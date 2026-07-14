"""Manual mapping CSV loads — tier 5 of the K2 SEAL attribution policy.

Gate seal-attribution-match-policy §F (SME-confirmed 2026-07-14,
config/gate-log.md): when no fact tier resolves a job — or multi-hit triage
cannot — the SME may author a CSV row (template
config/manual-loads/TEMPLATE-node-mapping.csv) mapping a source node key to a
PRE-EXISTING relationship to a target node key. THE RULES, all enforced here:

- **Manifest gate.** A CSV is loadable ONLY if registered in
  config/manual-loads/manifest.yaml first, its entry names a ``replaces_with``
  automation path (visible, named, closable debt), and its status is
  ``pending-load`` or ``loaded`` (idempotent re-run). ``superseded`` refuses.
- **No new relationship types.** The CSV's relationship column must name an
  entry that already exists in relationship_vocabulary.yaml (label + role) —
  a CSV can never mint a relationship type (that is ontology-mapper + a gate).
- **Supported shape.** The writer currently supports exactly the K2 shape:
  ControlMJob -[WAS_ASSOCIATED_WITH {role: seal_app_ref}]-> Application.
  Any other labels/relationship refuse loudly — extending the writer is a
  deliberate future change, not a silent fallback.
- **PIN semantics.** Edges written here carry match_method 'manual' +
  source 'manual-csv' + manual_load_file + authored_by; the automated loader
  (seal_attribution.py) excludes pinned jobs and surfaces PIN-CONFLICTs.
  Retirement (manifest -> superseded) is always a human act.

Parsing + validation are pure (offline-testable); only the loader touches
the graph, through the standard BaseLoader lifecycle (:JobRun provenance).
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, ClassVar, Iterator

import yaml

import drydocs_core
from drydocs_core.models import ManualMappingRow

from .base import BaseLoader

LOGGER = logging.getLogger(__name__)

_REPO_ROOT = Path(drydocs_core.__file__).resolve().parent.parent
DEFAULT_MANIFEST_PATH = _REPO_ROOT / "config" / "manual-loads" / "manifest.yaml"
VOCABULARY_PATH = (
    Path(drydocs_core.__file__).resolve().parent
    / "ontology" / "relationship_vocabulary.yaml"
)

# The one shape the manual writer supports today (K2). Extending this map is
# a deliberate code change reviewed against the vocabulary — never dynamic.
SUPPORTED_SHAPE = {
    "source_label": "ControlMJob",
    "relationship": "WAS_ASSOCIATED_WITH",
    "role": "seal_app_ref",
    "target_label": "Application",
}
LOADABLE_STATUSES = ("pending-load", "loaded")


class ManualLoadError(RuntimeError):
    """A manual CSV failed the manifest gate, shape check, or vocabulary check."""


# ---------------------------------------------------------------------------
# Pure validation
# ---------------------------------------------------------------------------

def load_manifest(path: str | Path = DEFAULT_MANIFEST_PATH) -> dict:
    path = Path(path)
    if not path.exists():
        raise ManualLoadError(f"manual-loads manifest not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def require_registered(
    csv_path: str | Path,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
) -> dict:
    """The manifest gate (§F.5): return the CSV's manifest entry or refuse.

    Registration happens BEFORE load; every entry must name its automated
    replacement. Returns the matched entry dict.
    """
    csv_path = Path(csv_path).resolve()
    manifest_path = Path(manifest_path).resolve()
    manifest = load_manifest(manifest_path)
    if manifest.get("status") != "confirmed":
        raise ManualLoadError(
            "config/manual-loads/manifest.yaml is not status: confirmed — the "
            "manual-loads mechanism is gate-bound (seal-attribution-match-policy)."
        )
    repo_root = manifest_path.parents[2]
    for entry in manifest.get("files") or []:
        entry_file = entry.get("file")
        if not entry_file:
            continue
        if (repo_root / entry_file).resolve() != csv_path:
            continue
        status = entry.get("status")
        if status not in LOADABLE_STATUSES:
            raise ManualLoadError(
                f"{entry_file}: manifest status '{status}' is not loadable "
                f"(expected one of {LOADABLE_STATUSES}); a superseded file's "
                "mappings belong to its replaces_with automation."
            )
        if not (entry.get("replaces_with") or "").strip():
            raise ManualLoadError(
                f"{entry_file}: manifest entry has no replaces_with — a manual "
                "load with no named automation path is not accepted (§F.5)."
            )
        return entry
    raise ManualLoadError(
        f"{csv_path} is not registered in {manifest_path} — register the CSV "
        "in config/manual-loads/manifest.yaml BEFORE loading (§F.5)."
    )


def relationship_registered(
    neo4j_label: str,
    role: str | None,
    vocabulary_path: str | Path = VOCABULARY_PATH,
) -> bool:
    """True iff (label, role) names an existing relationship_vocabulary.yaml
    entry — the 'a CSV can never mint a relationship type' rule (§F.1)."""
    vocab = yaml.safe_load(Path(vocabulary_path).read_text(encoding="utf-8")) or {}
    for rel in vocab.get("local_relationships") or []:
        if rel.get("neo4j_label") != neo4j_label:
            continue
        rel_role = rel.get("role")
        if (rel_role or None) == (role or None):
            return True
    return False


def _parse_key(raw: str, column: str, line_no: int) -> dict[str, str]:
    """Parse 'k=v;k=v' key columns from the template CSV."""
    pairs: dict[str, str] = {}
    for part in (raw or "").split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ManualLoadError(
                f"row {line_no}: {column} segment '{part}' is not k=v"
            )
        k, v = part.split("=", 1)
        pairs[k.strip()] = v.strip()
    if not pairs:
        raise ManualLoadError(f"row {line_no}: {column} is empty")
    return pairs


def parse_mapping_csv(
    csv_path: str | Path,
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    vocabulary_path: str | Path = VOCABULARY_PATH,
) -> list[ManualMappingRow]:
    """Manifest-gate, shape-check, and parse one manual mapping CSV.

    Raises :class:`ManualLoadError` on the first violation — a manual load
    is small and human-authored; partial acceptance would hide authoring
    mistakes rather than surface them.
    """
    csv_path = Path(csv_path)
    entry = require_registered(csv_path, manifest_path)
    manifest_file = str(entry.get("file"))

    rows: list[ManualMappingRow] = []
    with csv_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for line_no, raw in enumerate(reader, start=2):
            src_label = (raw.get("source_label") or "").strip()
            relationship = (raw.get("relationship") or "").strip()
            tgt_label = (raw.get("target_label") or "").strip()
            rel_props = _parse_key(raw.get("rel_props") or "", "rel_props", line_no)
            role = rel_props.get("role")

            if not relationship_registered(relationship, role, vocabulary_path):
                raise ManualLoadError(
                    f"row {line_no}: relationship {relationship} (role={role}) is "
                    "not registered in relationship_vocabulary.yaml — a manual CSV "
                    "can never mint a relationship type (§F.1; ontology-mapper + "
                    "a gate own that decision)."
                )
            shape = {
                "source_label": src_label,
                "relationship": relationship,
                "role": role,
                "target_label": tgt_label,
            }
            if shape != SUPPORTED_SHAPE:
                raise ManualLoadError(
                    f"row {line_no}: unsupported shape {shape} — the manual writer "
                    f"currently supports exactly {SUPPORTED_SHAPE}; extending it "
                    "is a deliberate code change."
                )

            source_key = _parse_key(raw.get("source_key") or "", "source_key", line_no)
            target_key = _parse_key(raw.get("target_key") or "", "target_key", line_no)
            missing = {"folder_id", "job_id"} - source_key.keys()
            if missing:
                raise ManualLoadError(
                    f"row {line_no}: source_key missing {sorted(missing)} "
                    "(ControlMJob node key is (folder_id, job_id))"
                )
            if "seal_id" not in target_key:
                raise ManualLoadError(
                    f"row {line_no}: target_key missing seal_id "
                    "(Application node key)"
                )

            rows.append(ManualMappingRow(
                folder_id=source_key["folder_id"],
                job_id=source_key["job_id"],
                seal_id=target_key["seal_id"],
                create_target_if_missing=raw.get("create_target_if_missing", "false"),
                manual_load_file=manifest_file,
                authored_by=raw.get("authored_by") or "",
                authored_on=raw.get("authored_on"),
                note=raw.get("note"),
            ))
    if not rows:
        raise ManualLoadError(f"{csv_path}: no mapping rows found")
    return rows


# ---------------------------------------------------------------------------
# Adapter + loader
# ---------------------------------------------------------------------------

class ManualMappingAdapter:
    """Yields pre-validated manual mapping rows to BaseLoader."""

    def __init__(self, rows: list[ManualMappingRow]) -> None:
        self._rows = rows

    def __enter__(self) -> "ManualMappingAdapter":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        for row in self._rows:
            yield row.model_dump(mode="json")


class ManualSealAttributionLoader(BaseLoader):
    """Writes SME-authored seal_app_ref edges (match_method 'manual').

    After the write it reconciles edges-touched against rows loaded and
    stamps the shortfall (rows whose ControlMJob was absent) on the :JobRun
    as dropped_in_graph — reported, never silent.
    """

    name: ClassVar[str] = "manual_seal_attribution.v1"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "manual_seal_attribution.cypher"
    )
    row_model: ClassVar[type] = ManualMappingRow
    source_label: ClassVar[str] = "human"

    def load(self):
        summary = super().load()
        result = self.client.run(
            """
            MATCH (run:JobRun {run_id: $run_id})
            OPTIONAL MATCH (:ControlMJob)-[r:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]->(:Application)
              WHERE r.last_run_id = $run_id AND r.match_method = 'manual'
            WITH run, count(r) AS edges_written
            OPTIONAL MATCH (n:Application {manually_created: true})
              WHERE n.created_at IS NOT NULL AND n.source = 'manual-csv'
            WITH run, edges_written, count(n) AS manually_created_total
            SET run.edges_written          = edges_written,
                run.dropped_in_graph       = $rows - edges_written,
                run.manually_created_total = manually_created_total
            RETURN edges_written
            """,
            run_id=self.run_id,
            rows=summary.rows_processed,
        )
        if result:
            dropped = summary.rows_processed - result[0].get("edges_written", 0)
            if dropped:
                LOGGER.warning(
                    "manual_seal_attribution: %d row(s) found no ControlMJob "
                    "endpoint — surfaced as JobRun.dropped_in_graph.", dropped
                )
        return summary
