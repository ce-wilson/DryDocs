"""Spec run + two-path export handlers (O11 / site-plan §4) — pure, framework-free.

The server-side export path re-runs a QuerySpec's Cypher against the spec's
database and streams csv/jsonl chunk by chunk (driver streaming — NOT
``apoc.export.*``, which writes files on the DB server, the wrong side of the
boundary). Every export gets a provenance manifest; because ``row_count`` is
only known when the stream finishes, the manifest is registered in the
:class:`ExportLedger` as the final act of the chunk generator and served from
``GET /exports/{id}/manifest`` — the sidecar ``.manifest.json`` the UI saves
next to the data file.

Classification rules (PUBLISH-BOUNDARY.md wired in):
- ``internal`` / ``internal-confidential`` exports carry a banner row and the
  ``INTERNAL__`` / ``INTERNAL-CONFIDENTIAL__`` filename prefix
- anything read from a watermarked database (ddcontext/ddall) gains a
  grid-visible ``trust_watermark`` column and ``SYNTHESIZED`` in the
  manifest's trust tiers
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import secrets
from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from drydocs_api.guard import ensure_read_only
from drydocs_api.handlers import GraphRunner, _authenticate
from drydocs_api.queries import validate_params
from drydocs_api.query_specs import QuerySpec, is_watermarked, query_spec
from drydocs_api.sessions import InMemorySessionStore

WATERMARK_COLUMN = "trust_watermark"
WATERMARK_VALUE = "SYNTHESIZED — unverified"
_TRUST_KEYS = frozenset({"trust", "trust_tier", "trust_tiers", WATERMARK_COLUMN})

try:  # single source for the manifest's app_version
    from drydocs_api import __version__ as APP_VERSION  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    APP_VERSION = "dev"


class UnknownExportError(KeyError):
    """Raised when a manifest is requested for an unknown/incomplete export."""


class ExportLedger:
    """Bounded in-memory manifest store. A manifest appears only when its
    export stream COMPLETED — a partially-consumed stream never registers,
    so a served manifest always describes a full file."""

    def __init__(self, capacity: int = 100) -> None:
        self._manifests: OrderedDict[str, dict[str, object]] = OrderedDict()
        self._capacity = capacity

    def complete(self, export_id: str, manifest: dict[str, object]) -> None:
        self._manifests[export_id] = manifest
        while len(self._manifests) > self._capacity:
            self._manifests.popitem(last=False)

    def manifest(self, export_id: str) -> dict[str, object]:
        try:
            return self._manifests[export_id]
        except KeyError as exc:
            raise UnknownExportError(export_id) from exc


def filename_for(spec: QuerySpec, fmt: str) -> str:
    prefix = {
        "internal": "INTERNAL__",
        "internal-confidential": "INTERNAL-CONFIDENTIAL__",
    }.get(spec.classification, "")
    return f"{prefix}{spec.id}.{fmt}"


def banner_text(spec: QuerySpec) -> str | None:
    if spec.classification in ("internal", "internal-confidential"):
        return (
            f"CLASSIFICATION: {spec.classification.upper()} — not for redistribution "
            "(PUBLISH-BOUNDARY.md); exported from DryDocs with provenance manifest"
        )
    return None


def _rows_iter(
    runner: GraphRunner, spec: QuerySpec, bound: Mapping[str, object]
) -> tuple[list[str], Iterator[dict[str, object]]]:
    """Prefer a streaming runner (``stream`` yields rows lazily); fall back to
    the buffered ``run`` for runners that don't stream (tests, small results)."""
    stream = getattr(runner, "stream", None)
    if callable(stream):
        return stream(spec.cypher, dict(bound), spec.database)
    keys, rows = runner.run(spec.cypher, dict(bound), spec.database)
    return keys, iter(rows)


def _apply_watermark(spec: QuerySpec, keys: list[str], rows: Iterable[dict[str, object]]):
    if not is_watermarked(spec):
        return keys, rows
    keys = [*keys, WATERMARK_COLUMN]

    def gen() -> Iterator[dict[str, object]]:
        for row in rows:
            yield {**row, WATERMARK_COLUMN: WATERMARK_VALUE}

    return keys, gen()


def _trust_tiers(spec: QuerySpec, seen: set[str]) -> list[str]:
    tiers = set(seen)
    if is_watermarked(spec):
        tiers.add("SYNTHESIZED")
    return sorted(tiers)


def _collect_trust(row: Mapping[str, object], seen: set[str]) -> None:
    for key in _TRUST_KEYS & set(row):
        value = row[key]
        if isinstance(value, str) and value:
            seen.add(value.split(" ")[0].upper() if key == WATERMARK_COLUMN else value)


# ── spec run (the UI's data-frame read path) ─────────────────────────────────


def run_spec(
    spec_id: str,
    params: dict[str, object],
    token: str,
    store: InMemorySessionStore,
    runner: GraphRunner,
) -> dict[str, object]:
    """Run a QuerySpec for a data frame: any authenticated role; params fail
    closed; database comes from the SPEC (a reviewed registry row); watermark
    column appended for ddcontext/ddall reads."""
    _authenticate(token, store)
    spec = query_spec(spec_id)
    bound = validate_params(spec, params)
    ensure_read_only(spec.cypher)  # defense in depth
    keys, rows = runner.run(spec.cypher, dict(bound), spec.database)
    keys, watermarked = _apply_watermark(spec, list(keys), rows)
    out_rows = list(watermarked)
    return {
        "spec_id": spec.id,
        "database": spec.database,
        "classification": spec.classification,
        "columns": [
            {"name": c.name, "type": c.type, "label": c.label or c.name} for c in spec.columns
        ],
        "cypher": spec.cypher,
        "params": dict(bound),
        "keys": keys,
        "rows": out_rows,
        "watermarked": is_watermarked(spec),
    }


# ── server-side export (path b) ──────────────────────────────────────────────


@dataclass(frozen=True)
class ExportJob:
    export_id: str
    filename: str
    media_type: str
    chunks: Iterator[str]


def _csv_line(values: list[object]) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow(values)
    return buf.getvalue()


def export_spec(
    spec_id: str,
    params: dict[str, object],
    fmt: str,
    token: str,
    store: InMemorySessionStore,
    runner: GraphRunner,
    ledger: ExportLedger,
    now: datetime | None = None,
) -> ExportJob:
    """Build a streaming export of a spec. The returned chunk generator yields
    the banner (classified specs), header, and rows; when it is EXHAUSTED it
    registers the provenance manifest in the ledger under ``export_id``."""
    if fmt not in ("csv", "jsonl"):
        raise ValueError(f"unsupported export format '{fmt}' (csv | jsonl)")
    session = _authenticate(token, store)
    spec = query_spec(spec_id)
    bound = validate_params(spec, params)
    ensure_read_only(spec.cypher)
    export_id = secrets.token_urlsafe(12)
    executed_at = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")

    def chunks() -> Iterator[str]:
        keys, rows = _rows_iter(runner, spec, bound)
        keys, watermarked = _apply_watermark(spec, list(keys), rows)
        banner = banner_text(spec)
        row_count = 0
        trust_seen: set[str] = set()

        if fmt == "csv":
            if banner:
                yield f"# {banner}\n"
            yield _csv_line(list(keys))
            for row in watermarked:
                _collect_trust(row, trust_seen)
                row_count += 1
                yield _csv_line([row.get(k) for k in keys])
        else:  # jsonl
            if banner:
                yield json.dumps({"_classification_banner": banner}) + "\n"
            for row in watermarked:
                _collect_trust(row, trust_seen)
                row_count += 1
                yield json.dumps(row, default=str) + "\n"

        ledger.complete(
            export_id,
            {
                "query_spec": spec.id,
                "cypher_sha256": hashlib.sha256(spec.cypher.encode("utf-8")).hexdigest(),
                "params": dict(bound),
                "database": spec.database,
                "executed_at": executed_at,
                "row_count": row_count,
                "classification": spec.classification,
                "trust_tiers_present": _trust_tiers(spec, trust_seen),
                "exported_by": session.persona_id,
                "format": fmt,
                "app_version": APP_VERSION,
            },
        )

    return ExportJob(
        export_id=export_id,
        filename=filename_for(spec, fmt),
        media_type="text/csv" if fmt == "csv" else "application/x-ndjson",
        chunks=chunks(),
    )


def export_manifest(
    export_id: str, token: str, store: InMemorySessionStore, ledger: ExportLedger
) -> dict[str, object]:
    _authenticate(token, store)
    return ledger.manifest(export_id)


def list_specs() -> list[dict[str, object]]:
    from drydocs_api.query_specs import QUERY_SPECS

    return [
        {
            "id": s.id,
            "description": s.description,
            "database": s.database,
            "classification": s.classification,
            "cypher": s.cypher,
            "columns": [{"name": c.name, "type": c.type, "label": c.label or c.name} for c in s.columns],
            "params": [
                {"name": p.name, "type": p.type, "required": p.required, "default": p.default}
                for p in s.params
            ],
            "watermarked": s.database in ("ddcontext", "ddall"),
        }
        for s in QUERY_SPECS.values()
    ]
