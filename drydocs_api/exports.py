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
- ``internal`` exports carry a banner row and the ``INTERNAL__`` filename
  prefix (``internal-confidential`` retired into ``internal`` at J23)
- anything read by an uncertain-declared spec (G102: the :Uncertain realm) gains a
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
from datetime import UTC, datetime

from drydocs_api.ephemeral_specs import EphemeralSpecStore, is_ephemeral_ref
from drydocs_api.guard import ensure_read_only
from drydocs_api.handlers import GraphRunner, _authenticate
from drydocs_api.queries import validate_params
from drydocs_api.query_specs import (
    DISPLAY_LIMIT_PARAM,
    QuerySpec,
    UnknownSpecError,
    is_watermarked,
    query_spec,
)
from drydocs_api.sessions import InMemorySessionStore

WATERMARK_COLUMN = "trust_watermark"

#: API1 clause (c): the highest ``limit`` an export caller may ask for. The
#: display ceiling (500) bounds a GRID, which is a rendering decision; an export
#: is a governance artifact and should not inherit a rendering decision. So the
#: export path takes its own ceiling, raisable per call up to here.
#:
#: It is a CEILING and not "unbounded" on purpose. An unbounded export over a
#: result set nobody has counted is the failure the display limit was protecting
#: against, moved rather than fixed — and with `truncated` in the manifest, an
#: export that hits this ceiling now SAYS so, which is the property the item is
#: actually buying. Raising it is a one-line, reviewable edit.
EXPORT_LIMIT_CEILING = 50_000
# G102 / gate §B (B-DURABLE): the false per-database claim is gone. A spec-level
# watermark says UNCERTAIN (machine-derived realm, the :Uncertain label); a row
# whose corpus is known is stamped from the SOURCE's declared trust_default via
# corpus_trust_watermark() — honest per row, keyed on the registry, never on
# storage location. "SYNTHESIZED — unverified" was retired because two of the
# corpora it stamped were VERBATIM captures (the gate's strongest argument).
WATERMARK_VALUE = "UNCERTAIN — machine-derived, unverified"
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
    prefix = {"internal": "INTERNAL__"}.get(spec.classification, "")
    return f"{prefix}{spec.id}.{fmt}"


def banner_text(spec: QuerySpec) -> str | None:
    if spec.classification == "internal":
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


def corpus_trust_watermark(corpus_id: str) -> str | None:
    """B-DURABLE (gate document-content-topology §B): the per-row watermark for a
    doc-content row, keyed on the SOURCE's declared trust_default in
    config/doc-source-registry.yaml — never on where the row was stored.
    Returns None for an unknown corpus (the caller falls back to the spec-level
    value rather than inventing trust)."""
    from drydocs_core.source_registry import SourceRegistry

    try:
        src = SourceRegistry.from_yaml().get(corpus_id)
    except Exception:
        return None
    if src is None:
        return None
    trust = (src.data or {}).get("trust_default")
    if not isinstance(trust, str) or not trust:
        return None
    return f"{trust} — per the source's declared trust_default"


def _apply_watermark(spec: QuerySpec, keys: list[str], rows: Iterable[dict[str, object]]):
    if not is_watermarked(spec):
        return keys, rows
    keys = [*keys, WATERMARK_COLUMN]

    def gen() -> Iterator[dict[str, object]]:
        for row in rows:
            # per-row honesty first: a row that names its corpus is stamped from
            # the registry's declared trust, not the realm default (B-DURABLE)
            corpus = row.get("corpus_id")
            stamp = corpus_trust_watermark(corpus) if isinstance(corpus, str) else None
            yield {**row, WATERMARK_COLUMN: stamp or WATERMARK_VALUE}

    return keys, gen()


def _trust_tiers(spec: QuerySpec, seen: set[str]) -> list[str]:
    tiers = set(seen)
    if is_watermarked(spec):
        tiers.add("UNCERTAIN")  # G102: SYNTHESIZED retired — it falsely described verbatim captures
    return sorted(tiers)


def _collect_trust(row: Mapping[str, object], seen: set[str]) -> None:
    for key in _TRUST_KEYS & set(row):
        value = row[key]
        if isinstance(value, str) and value:
            seen.add(value.split(" ")[0].upper() if key == WATERMARK_COLUMN else value)


# ── result completeness (API1) ───────────────────────────────────────────────
#
# The mechanism, chosen and recorded as clause (a) asks: run the spec with
# ``limit + 1`` and report whether the extra row existed. The alternative — a
# pre-limit ``count()`` — costs a second traversal on every read of every frame
# and answers a question nobody asked (how many rows are there), where this
# answers the one that is asked (is what you are looking at all of it). One row
# over is the cheapest possible evidence, and it is exact.
#
# The probe row is DROPPED before the envelope is built. It is evidence, not
# data: emitting 501 rows for a limit of 500 would break the very contract the
# field exists to state.


def applied_limit(spec: QuerySpec, bound: Mapping[str, object]) -> int | None:
    """The ceiling that governs this run, or None when there is none.

    Keyed on the CYPHER binding ``$limit`` and a bound integer for it — not on
    the spec DECLARING a ``limit`` parameter. The distinction is the ephemeral
    case and it is not hypothetical: an R4 ephemeral spec is built with
    ``params=()`` (user params fail closed) while its ceiling arrives in
    ``bound_params``, frozen at registration. Keyed on the declaration, every
    capped Ask-path answer would report ``truncated: false, limit: null`` — the
    exact false-completeness claim this item exists to abolish, on the surface
    most likely to produce it.

    The conjunction is still what makes the probe safe: if the Cypher binds
    ``$limit`` then the driver really applies it, so more rows than the ceiling
    can only mean the ceiling bit. A spec that declared the parameter without
    binding it would have had a cap invented for it; that cannot happen here.
    """
    if ("$" + DISPLAY_LIMIT_PARAM) not in spec.cypher:
        return None
    value = bound.get(DISPLAY_LIMIT_PARAM)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _probe_params(bound: Mapping[str, object], limit: int | None) -> dict[str, object]:
    """The params the DRIVER receives — one row past the ceiling. Never the
    params echoed back to the caller: those must stay the ceiling that applied,
    because the console feeds them straight back into the export path."""
    if limit is None:
        return dict(bound)
    return {**bound, DISPLAY_LIMIT_PARAM: limit + 1}


def resolve_export_limit(
    spec: QuerySpec, bound: Mapping[str, object], requested: int | None
) -> int | None:
    """API1 (c): the export's ceiling — the display one, or a caller-raised one.

    Raises ``ValueError`` (which the route maps to 422) rather than silently
    clamping. A caller who asked for 200,000 rows and received 50,000 with no
    error would be handed exactly the kind of quietly-capped artifact this item
    exists to abolish.
    """
    display = applied_limit(spec, bound)
    if requested is None:
        return display
    if is_ephemeral_ref(spec.id):
        # R4: an ephemeral spec's params are FROZEN at registration and replayed
        # verbatim — that is what makes an agent-registered query reproducible.
        # Reporting its completeness is free; rewriting its bound limit is not.
        raise ValueError(
            f"'{spec.id}' is an ephemeral spec: its params are frozen at registration (R4), "
            "so its export ceiling cannot be raised"
        )
    if display is None:
        raise ValueError(
            f"spec '{spec.id}' declares no '{DISPLAY_LIMIT_PARAM}' parameter, so there is "
            "no export ceiling to raise"
        )
    if not isinstance(requested, int) or isinstance(requested, bool) or requested < 1:
        raise ValueError(f"export limit must be a positive integer (got {requested!r})")
    if requested > EXPORT_LIMIT_CEILING:
        raise ValueError(
            f"export limit {requested} exceeds the server ceiling {EXPORT_LIMIT_CEILING}"
        )
    return requested


# ── spec resolution: permanent registry row, or the session's ephemeral ──────


def _resolve_spec(
    spec_id: str, session_id: str, ephemerals: EphemeralSpecStore | None
) -> tuple[QuerySpec, dict[str, object]]:
    """Resolve a spec id for run/export. ``eph.`` refs resolve ONLY through the
    owning session's store entry (R4: foreign/expired/unknown all 404) and
    carry their params frozen at registration; registry ids resolve as before
    with no fixed params. ``session_id`` is the AUTHENTICATED caller's public
    handle (ADR 0019) — the bearer was already resolved, so the lookup keys on
    the same value the agent registered under."""
    if is_ephemeral_ref(spec_id):
        if ephemerals is None:
            raise UnknownSpecError(spec_id)
        eph = ephemerals.resolve(session_id, spec_id)
        return eph.as_query_spec(), dict(eph.bound_params)
    return query_spec(spec_id), {}


# ── spec run (the UI's data-frame read path) ─────────────────────────────────


def run_spec(
    spec_id: str,
    params: dict[str, object],
    token: str,
    store: InMemorySessionStore,
    runner: GraphRunner,
    ephemerals: EphemeralSpecStore | None = None,
) -> dict[str, object]:
    """Run a QuerySpec for a data frame: any authenticated role; params fail
    closed; database comes from the SPEC (a reviewed registry row, or the
    session's own ephemeral registration); watermark column appended for
    specs that declare uncertain=True (pre-fold this keyed on the
    retired ddcontext/ddall database names — ADR 0011 §117)."""
    session = _authenticate(token, store)
    spec, fixed = _resolve_spec(spec_id, session.session_id, ephemerals)
    bound = {**fixed, **validate_params(spec, params)}
    return execute_spec(spec, bound, runner)


def execute_spec(
    spec: QuerySpec, bound: Mapping[str, object], runner: GraphRunner
) -> dict[str, object]:
    """Run an already-resolved, already-validated spec and shape THE envelope.

    R9: this is the one dict both ``POST /specs/{id}/run`` and the agent query
    command (``drydocs_api.agent_query``) return, so an agent reading the CLI
    and a console reading the API see the same twelve keys — ``truncated`` and
    ``limit`` joined the envelope at API1, and they joined it HERE rather than
    at the route precisely so the agent tier inherits completeness too: an agent
    that files a 500-row answer as the answer is the same defect as a console
    that does. Exactly these keys:
    the API's declared response model (O70, ``drydocs_api.schemas.SpecRunOut``)
    forbids extras, so a CLI-only field belongs on the CLI's side, never here.
    Authentication and spec RESOLUTION (registry row vs. a session's ephemeral
    registration) stay with the callers — this takes a spec and bound params.
    """
    ensure_read_only(spec.cypher)  # defense in depth — ephemeral specs re-validate here
    limit = applied_limit(spec, bound)
    keys, rows = runner.run(spec.cypher, _probe_params(bound, limit), spec.database)
    rows = list(rows)
    truncated = limit is not None and len(rows) > limit
    if truncated:
        rows = rows[:limit]  # the probe row is evidence, never payload
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
        "ephemeral": is_ephemeral_ref(spec.id),
        # API1 (a): completeness is part of the READ CONTRACT, so it is a
        # declared field and not something a consumer infers from
        # `len(rows) == limit` — a heuristic that is wrong exactly when the
        # answer happens to be 500 rows, and that would be a second expression
        # of a fact the server already knows.
        "truncated": truncated,
        "limit": limit,
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
    ephemerals: EphemeralSpecStore | None = None,
    limit: int | None = None,
) -> ExportJob:
    """Build a streaming export of a spec — permanent or ephemeral: the
    manifest fields (cypher_sha256, params, database, classification, trust
    tiers) are produced by the SAME code either way. The returned chunk
    generator yields the banner (classified specs), header, and rows; when it
    is EXHAUSTED it registers the provenance manifest in the ledger under
    ``export_id``.

    ``limit`` is API1 (c): the caller-raised export ceiling, up to
    ``EXPORT_LIMIT_CEILING``. ``None`` keeps today's behaviour — the display
    limit the console echoed back — so an un-updated caller is unaffected. Either
    way the manifest records the ceiling that applied and whether it bit.
    """
    if fmt not in ("csv", "jsonl"):
        raise ValueError(f"unsupported export format '{fmt}' (csv | jsonl)")
    session = _authenticate(token, store)
    spec, fixed = _resolve_spec(spec_id, session.session_id, ephemerals)
    bound = {**fixed, **validate_params(spec, params)}
    ensure_read_only(spec.cypher)
    ceiling = resolve_export_limit(spec, bound, limit)
    if ceiling is not None:
        # The manifest's `params` must describe the run that happened, so the
        # raised ceiling replaces the echoed display limit here and not later.
        bound = {**bound, DISPLAY_LIMIT_PARAM: ceiling}
    export_id = secrets.token_urlsafe(12)
    executed_at = (now or datetime.now(UTC)).isoformat(timespec="seconds")

    def chunks() -> Iterator[str]:
        keys, rows = _rows_iter(runner, spec, _probe_params(bound, ceiling))
        keys, watermarked = _apply_watermark(spec, list(keys), rows)
        banner = banner_text(spec)
        row_count = 0
        truncated = False
        trust_seen: set[str] = set()

        def bounded() -> Iterator[dict[str, object]]:
            """Emit at most `ceiling` rows; the row past it sets the flag.

            Written as a wrapper rather than as two copies of the same break so
            the csv and jsonl branches below cannot drift on the one thing that
            has to be identical: which rows leave the building.
            """
            nonlocal truncated
            for emitted, row in enumerate(watermarked):
                if ceiling is not None and emitted >= ceiling:
                    truncated = True
                    return
                yield row

        if fmt == "csv":
            if banner:
                yield f"# {banner}\n"
            yield _csv_line(list(keys))
            for row in bounded():
                _collect_trust(row, trust_seen)
                row_count += 1
                yield _csv_line([row.get(k) for k in keys])
        else:  # jsonl
            if banner:
                yield json.dumps({"_classification_banner": banner}) + "\n"
            for row in bounded():
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
                # API1 (b): row_count alone cannot distinguish "the answer was
                # 500 rows" from "the answer was cut at 500". The manifest is
                # the governance record and outlives the screen that produced
                # it, so the distinction is recorded IN the artifact.
                "truncated": truncated,
                "limit": ceiling,
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
            "columns": [
                {"name": c.name, "type": c.type, "label": c.label or c.name} for c in s.columns
            ],
            "params": [
                {"name": p.name, "type": p.type, "required": p.required, "default": p.default}
                for p in s.params
            ],
            "watermarked": is_watermarked(s),  # G102: the declaration, never the database
        }
        for s in QUERY_SPECS.values()
    ]
