"""Pure manual-mapping validation + parsing (tier 5, K2 gate §F) — CORE layer.

Extracted from drydocs.loaders.manual_loads (mapping-store plan M2): the
manifest gate, vocabulary check, supported-shape check and CSV parse are
parse/config-layer logic with no graph side effects, needed by BOTH the
tier-5 loader (drydocs.loaders.manual_loads) and the mapping-store
materialization (drydocs_core.mapping_store) that drydocs-api serves — and
components may not import each other, so the shared half lives here.

THE RULES enforced (unchanged from the loader docstring):
- Manifest gate: a CSV is loadable ONLY if registered in
  config/manual-loads/manifest.yaml with a named replaces_with automation path
  and a loadable status.
- No new relationship types: the relationship column must name an existing
  relationship_vocabulary.yaml entry (label + role).
- Supported shape: exactly the K7-ruled folder-grain shape (K8 flip;
  gate seal-app-ref-edge-reshape §D2 — ONE shape everywhere):
  ControlMFolder -[BELONGS_TO_APPLICATION {role: seal_app_ref}]-> Port,
  authored at the APP-CODE grain (§B1) with an optional per-folder narrowing.
"""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

import drydocs_core
from drydocs_core import yaml_fragments
from drydocs_core.models import ManualMappingRow
from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(drydocs_core.__file__).resolve().parent.parent)
DEFAULT_MANIFEST_PATH = _REPO_ROOT / "config" / "manual-loads" / "manifest.yaml"
VOCABULARY_PATH = (
    Path(drydocs_core.__file__).resolve().parent / "ontology" / "relationship_vocabulary"
)

# The one shape the manual writer supports today — the K7-ruled folder-grain
# edge (flipped from the K2 job-grain shape at K8, matching K2_SHAPE in
# drydocs_api/mappings.py per gate §D2). Extending this map is a deliberate
# code change reviewed against the vocabulary — never dynamic.
SUPPORTED_SHAPE = {
    "source_label": "ControlMFolder",
    "relationship": "BELONGS_TO_APPLICATION",
    "role": "seal_app_ref",
    "target_label": "Port",
}
LOADABLE_STATUSES = ("pending-load", "loaded")


class ManualLoadError(RuntimeError):
    """A manual CSV failed the manifest gate, shape check, or vocabulary check."""


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
    vocab = yaml_fragments.load_yaml_source(vocabulary_path) or {}
    for rel in vocab.get("local_relationships") or []:
        if rel.get("neo4j_label") != neo4j_label:
            continue
        rel_role = rel.get("role")
        if (rel_role or None) == (role or None):
            return True
    return False


def _parse_key(raw: str, column: str, line_no: int) -> dict[str, str]:
    """Parse 'k=v:k=v' key columns from the template CSV.

    Separator ruled by the SME 2026-08-03 (composite-key serialization
    standard, knowledge/standards/technology/composite-key-serialization.md):
    pairs join with ':' — NOT ';', which is the SQL statement terminator and
    these cells travel beside SQL. Constraint that makes it safe: key VALUES
    are identifiers and never contain ':'; the dot-composite ctlm_id form
    (folder_id.job_id) is compatible by design."""
    pairs: dict[str, str] = {}
    for part in (raw or "").split(":"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ManualLoadError(f"row {line_no}: {column} segment '{part}' is not k=v")
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
                    "not registered in the relationship vocabulary — a manual CSV "
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
            if "app_code" not in source_key:
                raise ManualLoadError(
                    f"row {line_no}: source_key missing app_code — authoring is "
                    "per Control-M app code (gate seal-app-ref-edge-reshape §B1); "
                    "add folder_id=<id> alongside it only to pin ONE folder of a "
                    "shared platform code."
                )
            if "app_id" not in target_key:
                raise ManualLoadError(
                    f"row {line_no}: target_key missing app_id (the Port key is "
                    "(parent_app_id, kind); the loader targets the application's "
                    "BatchProcessing :Port per gate §C1)"
                )

            rows.append(
                ManualMappingRow(
                    app_code=source_key["app_code"],
                    folder_id=source_key.get("folder_id"),
                    app_id=target_key["app_id"],
                    create_target_if_missing=raw.get("create_target_if_missing", "false"),
                    manual_load_file=manifest_file,
                    authored_by=raw.get("authored_by") or "",
                    authored_on=raw.get("authored_on"),
                    note=raw.get("note"),
                )
            )
    if not rows:
        raise ManualLoadError(f"{csv_path}: no mapping rows found")
    return rows
