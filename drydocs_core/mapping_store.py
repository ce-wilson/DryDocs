"""SQLite materialization of the mapping layer (plan M0-M4) — CORE layer.

Plan: knowledge/upgrade-plans/mapping-store-plan-2026-07-17.md.

THE CONTRACT: the committed YAML/CSV in git remain the source of truth the
HITL gate reviews; the SQLite file built here is a *derived, rebuildable
materialization* — deletable at any moment without data loss, never the
artifact a gate reviews. It exists so the UI (O13 /mappings via drydocs-api),
agents (SQL/MCP), and analytics (DuckDB reads the same file) can QUERY the
mapping layer instead of parsing YAML.

Lives in drydocs_core because BOTH the load component (read seam,
drydocs.loaders.manual_loads) and the api component (drydocs_api.mappings)
consume it, and components never import each other (MODULE_MAP boundary).

Sources materialized (all read-only here):
- config/taxonomy-ontology-map.yaml          -> ontology_mapping (the quintuple)
- drydocs_core/ontology/relationship_vocabulary.yaml
                                             -> relationship_vocabulary,
                                                node_classification
- config/manual-loads/manifest.yaml + CSVs   -> manual_load_file, manual_mapping
- config/overrides/seal-contact-overrides.csv
                                             -> seal_contact_override (O24 —
                                                the ui-write-surface gate's M2
                                                origin-flagged store)
- config/overrides/app-code-mappings.csv     -> app_code_mapping (K9 — the K7
                                                defined-mapping store, gate
                                                seal-app-ref-edge-reshape
                                                §E1/§E2)

Manual CSV ingestion reuses the SAME validation chain as the tier-5 loader
(drydocs_core.manual_mappings — manifest gate, vocabulary check, supported
shape); the store can therefore never accept a row the loader would refuse.
Reads come back across the SQL boundary; the parity test
(tests/unit/test_mapping_store.py) guards round-trip fidelity.

Determinism: byte-identical dumps for identical sources — insertion order is
file order, dumps are ordered by primary key, and no wall-clock values are
stored (meta carries source content hashes, not timestamps).
"""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

import drydocs_core
from drydocs_core.manual_mappings import (
    DEFAULT_MANIFEST_PATH as MANIFEST_PATH,
)
from drydocs_core.manual_mappings import (
    VOCABULARY_PATH,
    ManualLoadError,
    parse_mapping_csv,
)
from drydocs_core.models import ManualMappingRow

REPO_ROOT = Path(drydocs_core.__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "var" / "mapping.db"
ONTOLOGY_MAP_PATH = REPO_ROOT / "config" / "taxonomy-ontology-map.yaml"
SEAL_CONTACT_OVERRIDES_PATH = REPO_ROOT / "config" / "overrides" / "seal-contact-overrides.csv"
_OVERRIDES_META_KEY = "source:config/overrides/seal-contact-overrides.csv"
_OVERRIDE_STATUSES = ("active", "corrected-in-seal")
APP_CODE_MAPPINGS_PATH = REPO_ROOT / "config" / "overrides" / "app-code-mappings.csv"
_APP_CODE_META_KEY = "source:config/overrides/app-code-mappings.csv"
APP_CODE_TIERS = ("seal-born", "platform", "dual-coded")
# The full origin enum every surface discloses (K7 §B3). 'matched-fallback'
# is DERIVED by the K2 fallback at load time and disclosed on the edge — it
# is never authored, so the committed store admits only the other three.
APP_CODE_ORIGINS = ("defined", "matched-fallback", "override", "manual-pin")
APP_CODE_AUTHORED_ORIGINS = ("defined", "override", "manual-pin")

SCHEMA_VERSION = "drydocs.mapping-store.v1"

# Table DDL. Nullable columns mirror the YAML's reality (property supplements
# have no to_node, infrastructure edges have no prov term, etc.).
_DDL = """
CREATE TABLE meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE node_classification (
  label     TEXT PRIMARY KEY,
  class     TEXT,
  prov_type TEXT,
  note      TEXT
);

CREATE TABLE relationship_vocabulary (
  id           TEXT PRIMARY KEY,
  neo4j_label  TEXT NOT NULL,
  role         TEXT,
  from_node    TEXT,
  to_node      TEXT,
  prov_maps_to TEXT,
  sosa_maps_to TEXT,
  domain       TEXT,
  status       TEXT NOT NULL,
  note         TEXT
);

-- The mapping quintuple: (source label+key expr) -[relationship {role}]->
-- (target label+key expr), plus the HITL lifecycle. One row per
-- taxonomy-ontology-map.yaml entry, in file order (seq).
CREATE TABLE ontology_mapping (
  id                   TEXT PRIMARY KEY,
  seq                  INTEGER NOT NULL,
  taxonomy_source      TEXT,
  taxonomy_element     TEXT,
  source_label         TEXT,
  target_label         TEXT,
  relationship_type    TEXT,
  role                 TEXT,
  prov_maps_to         TEXT,
  matrix_row           TEXT,
  precedence_authority TEXT,
  vocab_id             TEXT,
  status               TEXT NOT NULL
      CHECK (status IN ('proposed','confirmed','applied','rejected')),
  confirmed_by         TEXT,
  confirmed_on         TEXT,
  applied_on           TEXT
);

CREATE TABLE manual_load_file (
  file          TEXT PRIMARY KEY,
  scope         TEXT,
  status        TEXT NOT NULL,
  replaces_with TEXT,
  authored_by   TEXT,
  notes         TEXT
);

-- Rekeyed at K8 (gate seal-app-ref-edge-reshape §B1/§D2): manual tier-5
-- rows are authored at the APP-CODE grain targeting app_id; folder_id NULL
-- = code-level row (the loader fans out over CONTAINS_FOLDER), folder_id
-- set = a per-folder pin on a shared platform code.
CREATE TABLE manual_mapping (
  file                     TEXT NOT NULL REFERENCES manual_load_file(file),
  line_no                  INTEGER NOT NULL,
  app_code                 TEXT NOT NULL,
  folder_id                TEXT,
  app_id                   TEXT NOT NULL,
  create_target_if_missing INTEGER NOT NULL,
  authored_by              TEXT NOT NULL,
  authored_on              TEXT,
  note                     TEXT,
  PRIMARY KEY (file, line_no)
);

-- ── M4 analytics views (DuckDB reads these through its sqlite extension) ──
CREATE VIEW v_mapping_quintuple AS
  SELECT id, source_label, relationship_type, role, target_label,
         prov_maps_to, status, vocab_id
  FROM ontology_mapping ORDER BY seq;

CREATE VIEW v_status_summary AS
  SELECT status, count(*) AS n FROM ontology_mapping
  GROUP BY status ORDER BY status;

CREATE VIEW v_vocab_active AS
  SELECT id, neo4j_label, role, from_node, to_node, domain
  FROM relationship_vocabulary WHERE status = 'active' ORDER BY id;

CREATE VIEW v_label_options AS
  SELECT label, class, prov_type FROM node_classification ORDER BY label;

-- Manual rows whose authoring key maps to more than one application — the
-- steward screen's conflict queue (within the manual tier itself). The key
-- is (app_code, folder_id): two code-level rows naming different apps
-- conflict, as do two pins on the same folder (folder→application is 1:1,
-- the K7 OWNER-NOT-USER ruling).
CREATE VIEW v_manual_conflicts AS
  SELECT app_code, folder_id, count(DISTINCT app_id) AS targets
  FROM manual_mapping GROUP BY app_code, folder_id
  HAVING count(DISTINCT app_id) > 1;

-- ── O24 SEAL-contact override list (ui-write-surface gate SME-3: the M2
-- origin-flagged store). Overrides NEVER write the graph and NEVER silently
-- replace the SEAL value — the captured seal_holder_sid keeps the source
-- value side by side with the correction.
CREATE TABLE seal_contact_override (
  line_no              INTEGER PRIMARY KEY,
  app_seal_id          TEXT NOT NULL,
  role_name            TEXT NOT NULL,
  seal_holder_sid      TEXT,
  override_holder_sid  TEXT NOT NULL,
  override_holder_name TEXT,
  rationale            TEXT NOT NULL,
  authored_by          TEXT NOT NULL,
  authored_on          TEXT,
  status               TEXT NOT NULL
      CHECK (status IN ('active','corrected-in-seal'))
);

-- The /mappings grid: every attribution ROW carries an origin flag — the
-- SEAL source value (as captured at authoring) and the user override render
-- as adjacent rows, source first, never merged into one.
CREATE VIEW v_seal_contact_grid AS
  SELECT app_seal_id, role_name, origin, holder_sid, holder_name,
         rationale, authored_by, authored_on, status
  FROM (
    SELECT app_seal_id, role_name, 'source' AS origin,
           seal_holder_sid AS holder_sid, NULL AS holder_name,
           NULL AS rationale, NULL AS authored_by, NULL AS authored_on,
           status, line_no
    FROM seal_contact_override WHERE seal_holder_sid IS NOT NULL
    UNION ALL
    SELECT app_seal_id, role_name, 'override' AS origin,
           override_holder_sid, override_holder_name,
           rationale, authored_by, authored_on, status, line_no
    FROM seal_contact_override
  )
  ORDER BY app_seal_id, role_name, line_no, origin DESC;

-- The source-corrections report feed: outstanding corrections only,
-- addressed to the application owners (AO privilege fixes SEAL itself).
CREATE VIEW v_source_corrections AS
  SELECT app_seal_id, role_name, seal_holder_sid, override_holder_sid,
         override_holder_name, rationale, authored_by, authored_on
  FROM seal_contact_override WHERE status = 'active'
  ORDER BY app_seal_id, role_name, line_no;

-- ── K9 defined-mapping store (K7 gate seal-app-ref-edge-reshape §E1/§E2):
-- the steward-DEFINED app-code → application domain. Unlike the contact
-- overrides above, these rows ARE a graph-loadable source of record — no
-- machine feed exists to defer to (§E2) — and override rows may be
-- PERMANENT (no corrected-in-source lifecycle, hence no status column).
-- Rows never write the graph directly; the loader (K8) stays the only
-- graph writer (§E3). folder_id empty = code-level row, fanned out to
-- folders by the loader via m3_contains_folder (§B1); folder_id set = a
-- tier-2 per-folder resolution.
CREATE TABLE app_code_mapping (
  line_no            INTEGER PRIMARY KEY,
  app_code           TEXT NOT NULL,
  folder_id          TEXT,
  tier               TEXT NOT NULL
      CHECK (tier IN ('seal-born','platform','dual-coded')),
  app_id             TEXT,
  declared_end_state TEXT,
  origin             TEXT NOT NULL
      CHECK (origin IN ('defined','matched-fallback','override','manual-pin')),
  rationale          TEXT,
  authored_by        TEXT NOT NULL,
  authored_on        TEXT
);

-- The /mappings grid: code-level rows before their per-folder resolutions;
-- a defined row and its override render adjacent, origin-flagged (§B3 —
-- attribution is never presented without its origin).
CREATE VIEW v_app_code_grid AS
  SELECT app_code, folder_id, tier, app_id, declared_end_state, origin,
         rationale, authored_by, authored_on
  FROM app_code_mapping
  ORDER BY app_code, folder_id IS NOT NULL, folder_id, line_no;

-- Tier-3 visibility (§B2): every dual-coded row with its DECLARED end
-- state — the surface a stalled migration cannot hide from.
CREATE VIEW v_dual_coded_migrations AS
  SELECT app_code, app_id, declared_end_state, authored_by, authored_on
  FROM app_code_mapping WHERE tier = 'dual-coded'
  ORDER BY app_code, line_no;
"""

_DUMP_ORDER = {
    "meta": "key",
    "node_classification": "label",
    "relationship_vocabulary": "id",
    "ontology_mapping": "seq",
    "manual_load_file": "file",
    "manual_mapping": "file, line_no",
    "seal_contact_override": "line_no",
    "app_code_mapping": "line_no",
}


class MappingStoreError(RuntimeError):
    """A source file is missing or malformed — the build refuses loudly."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise MappingStoreError(f"mapping-store source not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _text(value: Any) -> str | None:
    """Normalize YAML scalars to trimmed TEXT (None stays None)."""
    if value is None:
        return None
    if isinstance(value, dict | list):
        return json.dumps(value, sort_keys=True)
    return str(value).strip() or None


def build(
    db_path: str | Path = ":memory:",
    *,
    ontology_map_path: str | Path = ONTOLOGY_MAP_PATH,
    vocabulary_path: str | Path = VOCABULARY_PATH,
    manifest_path: str | Path = MANIFEST_PATH,
    overrides_path: str | Path | None = None,
    app_code_mappings_path: str | Path | None = None,
) -> sqlite3.Connection:
    """Build the materialization from the committed sources. Existing file at
    ``db_path`` is replaced (it is derived; the sources are the truth)."""
    if db_path != ":memory:":
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        if db_file.exists():
            db_file.unlink()
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_DDL)

    ontology_map_path = Path(ontology_map_path)
    vocabulary_path = Path(vocabulary_path)
    manifest_path = Path(manifest_path)
    # None resolves at CALL time (not def time) so tests can monkeypatch the
    # module constant to point the whole read chain at a fixture list.
    overrides_path = Path(overrides_path or SEAL_CONTACT_OVERRIDES_PATH)
    app_code_mappings_path = Path(app_code_mappings_path or APP_CODE_MAPPINGS_PATH)

    _ingest_vocabulary(conn, vocabulary_path)
    _ingest_ontology_map(conn, ontology_map_path)
    csv_hashes = _ingest_manual_loads(conn, manifest_path, vocabulary_path)
    _ingest_seal_overrides(conn, overrides_path)
    _ingest_app_code_mappings(conn, app_code_mappings_path)

    meta = {
        "schema_version": SCHEMA_VERSION,
        "source:taxonomy-ontology-map.yaml": _sha256(ontology_map_path),
        "source:relationship_vocabulary.yaml": _sha256(vocabulary_path),
        "source:manual-loads/manifest.yaml": _sha256(manifest_path),
        _OVERRIDES_META_KEY: _sha256(overrides_path),
        _APP_CODE_META_KEY: _sha256(app_code_mappings_path),
        **csv_hashes,
    }
    conn.executemany("INSERT INTO meta (key, value) VALUES (?, ?)", sorted(meta.items()))
    conn.commit()
    return conn


def _hash_source(path: Path) -> str:
    if not path.exists():
        raise MappingStoreError(f"mapping-store source not found: {path}")
    return _sha256(path)


def source_hashes(
    *,
    ontology_map_path: str | Path = ONTOLOGY_MAP_PATH,
    vocabulary_path: str | Path = VOCABULARY_PATH,
    manifest_path: str | Path = MANIFEST_PATH,
    overrides_path: str | Path | None = None,
    app_code_mappings_path: str | Path | None = None,
) -> dict[str, str]:
    """The meta rows a build() from these sources WOULD store, computed without
    building — staleness detection is then one dict comparison (is_current).
    Must stay key-for-key identical to build()'s meta insert."""
    ontology_map_path = Path(ontology_map_path)
    vocabulary_path = Path(vocabulary_path)
    manifest_path = Path(manifest_path)
    overrides_path = Path(overrides_path or SEAL_CONTACT_OVERRIDES_PATH)
    app_code_mappings_path = Path(app_code_mappings_path or APP_CODE_MAPPINGS_PATH)
    expected = {
        "schema_version": SCHEMA_VERSION,
        "source:taxonomy-ontology-map.yaml": _hash_source(ontology_map_path),
        "source:relationship_vocabulary.yaml": _hash_source(vocabulary_path),
        "source:manual-loads/manifest.yaml": _hash_source(manifest_path),
        _OVERRIDES_META_KEY: _hash_source(overrides_path),
        _APP_CODE_META_KEY: _hash_source(app_code_mappings_path),
    }
    manifest = _load_yaml(manifest_path)
    repo_root = manifest_path.resolve().parents[2]
    for entry in manifest.get("files") or []:
        file_rel = _text(entry.get("file"))
        if not file_rel or entry.get("status") not in ("pending-load", "loaded"):
            continue
        expected[f"source:{file_rel}"] = _hash_source((repo_root / file_rel).resolve())
    return expected


def is_current(
    db_path: str | Path,
    *,
    ontology_map_path: str | Path = ONTOLOGY_MAP_PATH,
    vocabulary_path: str | Path = VOCABULARY_PATH,
    manifest_path: str | Path = MANIFEST_PATH,
    overrides_path: str | Path | None = None,
    app_code_mappings_path: str | Path | None = None,
) -> bool:
    """Whether the materialization at ``db_path`` matches the committed sources
    EXACTLY: same schema version, same source set (added/removed manifest files
    count as drift), same content hashes. False for a missing, unreadable, or
    foreign file — the file is derived, so every False means "rebuild", never
    "investigate"."""
    db_file = Path(db_path)
    if not db_file.exists():
        return False
    try:
        conn = sqlite3.connect(f"file:{db_file.as_posix()}?mode=ro", uri=True)
        try:
            stored = dict(conn.execute("SELECT key, value FROM meta"))
        finally:
            conn.close()
    except sqlite3.Error:
        return False
    return stored == source_hashes(
        ontology_map_path=ontology_map_path,
        vocabulary_path=vocabulary_path,
        manifest_path=manifest_path,
        overrides_path=overrides_path,
        app_code_mappings_path=app_code_mappings_path,
    )


def _ingest_vocabulary(conn: sqlite3.Connection, path: Path) -> None:
    vocab = _load_yaml(path)
    for nc in vocab.get("node_classifications") or []:
        conn.execute(
            "INSERT OR REPLACE INTO node_classification (label, class, prov_type, note) "
            "VALUES (?, ?, ?, ?)",
            (
                _text(nc.get("label")),
                _text(nc.get("class")),
                _text(nc.get("prov_type")),
                _text(nc.get("note")),
            ),
        )
    for rel in vocab.get("local_relationships") or []:
        conn.execute(
            "INSERT INTO relationship_vocabulary "
            "(id, neo4j_label, role, from_node, to_node, prov_maps_to, sosa_maps_to, "
            " domain, status, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                _text(rel.get("id")),
                _text(rel.get("neo4j_label")),
                _text(rel.get("role")),
                _text(rel.get("from_node")),
                _text(rel.get("to_node")),
                _text(rel.get("prov_maps_to")),
                _text(rel.get("sosa_maps_to")),
                _text(rel.get("domain")),
                _text(rel.get("status")),
                _text(rel.get("note")),
            ),
        )


def _ingest_ontology_map(conn: sqlite3.Connection, path: Path) -> None:
    doc = _load_yaml(path)
    for seq, entry in enumerate(doc.get("mappings") or []):
        ont = entry.get("ontology") or {}
        tax = entry.get("taxonomy") or {}
        conn.execute(
            "INSERT INTO ontology_mapping "
            "(id, seq, taxonomy_source, taxonomy_element, source_label, target_label, "
            " relationship_type, role, prov_maps_to, matrix_row, precedence_authority, "
            " vocab_id, status, confirmed_by, confirmed_on, applied_on) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                _text(entry.get("id")),
                seq,
                _text(tax.get("source")),
                _text(tax.get("element")),
                _text(ont.get("from_node")),
                _text(ont.get("to_node")),
                _text(ont.get("neo4j_label")),
                _text(ont.get("role")),
                _text(ont.get("prov_maps_to")),
                _text(ont.get("matrix_row")),
                _text(entry.get("precedence_authority")),
                _text(entry.get("vocab_id")),
                _text(entry.get("status")),
                _text(entry.get("confirmed_by")),
                _text(entry.get("confirmed_on")),
                _text(entry.get("applied_on")),
            ),
        )


def _ingest_manual_loads(
    conn: sqlite3.Connection, manifest_path: Path, vocabulary_path: Path
) -> dict[str, str]:
    """Register manifest entries and ingest loadable CSVs through the SAME
    validation chain the tier-5 loader uses. Returns per-CSV content hashes."""
    manifest = _load_yaml(manifest_path)
    repo_root = manifest_path.resolve().parents[2]
    hashes: dict[str, str] = {}
    for entry in manifest.get("files") or []:
        file_rel = _text(entry.get("file"))
        if not file_rel:
            continue
        conn.execute(
            "INSERT INTO manual_load_file (file, scope, status, replaces_with, "
            "authored_by, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (
                file_rel,
                _text(entry.get("scope")),
                _text(entry.get("status")),
                _text(entry.get("replaces_with")),
                _text(entry.get("authored_by")),
                _text(entry.get("notes")),
            ),
        )
        if entry.get("status") not in ("pending-load", "loaded"):
            continue  # superseded files are registered (audit) but not materialized
        csv_path = (repo_root / file_rel).resolve()
        rows = parse_mapping_csv(
            csv_path, manifest_path=manifest_path, vocabulary_path=vocabulary_path
        )
        hashes[f"source:{file_rel}"] = _sha256(csv_path)
        for line_no, row in enumerate(rows, start=2):
            conn.execute(
                "INSERT INTO manual_mapping (file, line_no, app_code, folder_id, app_id, "
                "create_target_if_missing, authored_by, authored_on, note) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    file_rel,
                    line_no,
                    row.app_code,
                    row.folder_id,
                    row.app_id,
                    int(row.create_target_if_missing),
                    row.authored_by,
                    row.authored_on,
                    row.note,
                ),
            )
    return hashes


def _ingest_seal_overrides(conn: sqlite3.Connection, path: Path) -> None:
    """Ingest the committed SEAL-contact override list (O24). Validation fails
    loudly per row: the file is steward-authored, so a bad row is a mistake to
    fix at the source, never something to guess around. Role names must
    canonicalize to the SEAL role vocabulary; an override that EQUALS the
    captured SEAL value is refused (it is not a correction)."""
    from drydocs_core.models.seal import canonicalize_role

    if not path.exists():
        raise MappingStoreError(f"mapping-store source not found: {path}")
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for line_no, raw in enumerate(reader, start=2):
            where = f"{path.name} line {line_no}"
            app = _text(raw.get("app_seal_id"))
            role = canonicalize_role(raw.get("role_name"))
            seal_sid = _text(raw.get("seal_holder_sid"))
            override_sid = _text(raw.get("override_holder_sid"))
            rationale = _text(raw.get("rationale"))
            authored_by = _text(raw.get("authored_by"))
            status = _text(raw.get("status")) or "active"
            if not app:
                raise MappingStoreError(f"{where}: app_seal_id is required")
            if role is None:
                raise MappingStoreError(
                    f"{where}: role_name {raw.get('role_name')!r} does not "
                    "canonicalize to a SEAL role"
                )
            if not override_sid:
                raise MappingStoreError(f"{where}: override_holder_sid is required")
            if seal_sid == override_sid:
                raise MappingStoreError(
                    f"{where}: override equals the captured SEAL value — not a correction"
                )
            if not rationale:
                raise MappingStoreError(
                    f"{where}: rationale is REQUIRED — it is the source-corrections "
                    "report's justification column"
                )
            if not authored_by:
                raise MappingStoreError(f"{where}: authored_by is required")
            if status not in _OVERRIDE_STATUSES:
                raise MappingStoreError(f"{where}: status {status!r} not in {_OVERRIDE_STATUSES}")
            conn.execute(
                "INSERT INTO seal_contact_override (line_no, app_seal_id, role_name, "
                "seal_holder_sid, override_holder_sid, override_holder_name, rationale, "
                "authored_by, authored_on, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    line_no,
                    app,
                    role,
                    seal_sid,
                    override_sid,
                    _text(raw.get("override_holder_name")),
                    rationale,
                    authored_by,
                    _text(raw.get("authored_on")),
                    status,
                ),
            )


def validate_app_code_row(
    row: dict[str, Any], *, where: str, seen: set[tuple[str, str, str]]
) -> dict[str, str | None]:
    """Validate ONE defined-mapping row against the K7 tier rules (§B1/§B2)
    and return it normalized. Shared by the CSV ingestion below and the API
    draft endpoint, so a drafted artifact can never be refused at
    materialization. ``seen`` accumulates (app_code, folder_id, origin) keys
    across the file for the duplicate check — folder → application is 1:1
    (OWNER-NOT-USER), so a duplicate authoring row is a defect, not a state.
    """
    app_code = _text(row.get("app_code"))
    folder_id = _text(row.get("folder_id"))
    tier = _text(row.get("tier"))
    app_id = _text(row.get("app_id"))
    end_state = _text(row.get("declared_end_state"))
    origin = _text(row.get("origin"))
    rationale = _text(row.get("rationale"))
    authored_by = _text(row.get("authored_by"))

    if not app_code:
        raise MappingStoreError(f"{where}: app_code is required")
    if tier not in APP_CODE_TIERS:
        raise MappingStoreError(f"{where}: tier {tier!r} not in {APP_CODE_TIERS}")
    if origin == "matched-fallback":
        raise MappingStoreError(
            f"{where}: origin 'matched-fallback' is derived by the K2 fallback at "
            "load time and disclosed on the edge (§B3) — it is never authored "
            "into the committed store"
        )
    if origin not in APP_CODE_AUTHORED_ORIGINS:
        raise MappingStoreError(f"{where}: origin {origin!r} not in {APP_CODE_AUTHORED_ORIGINS}")
    if tier == "seal-born":
        if folder_id:
            raise MappingStoreError(
                f"{where}: a seal-born row is code-level 1:1 — fan-out covers its "
                "folders (§B1); a per-folder row contradicts tier 1"
            )
        if not app_id:
            raise MappingStoreError(f"{where}: a seal-born row requires app_id (1:1)")
    elif tier == "platform":
        if folder_id and not app_id:
            raise MappingStoreError(
                f"{where}: a platform per-folder resolution row requires app_id"
            )
        if not folder_id and app_id:
            raise MappingStoreError(
                f"{where}: a shared platform code has no single application — "
                "resolution is per folder (§B2); leave app_id empty on the "
                "code-level row"
            )
    else:  # dual-coded
        if folder_id:
            raise MappingStoreError(
                f"{where}: a dual-coded row is code-level — the platform-code side "
                "of the migration resolves per folder under the PLATFORM code's rows"
            )
        if not app_id:
            raise MappingStoreError(f"{where}: a dual-coded row requires app_id")
        if not end_state:
            raise MappingStoreError(
                f"{where}: a dual-coded row requires declared_end_state (§B2 — a "
                "stalled migration must be visible, never silently permanent)"
            )
    if end_state and tier != "dual-coded":
        raise MappingStoreError(
            f"{where}: declared_end_state belongs to dual-coded rows only (§B2)"
        )
    if origin != "defined" and not rationale:
        raise MappingStoreError(
            f"{where}: rationale is REQUIRED on {origin} rows — an override may be "
            "PERMANENT in this domain (§E2), so the why must travel with it"
        )
    if not authored_by:
        raise MappingStoreError(f"{where}: authored_by is required")

    key = (app_code, folder_id or "", origin or "")
    if key in seen:
        raise MappingStoreError(
            f"{where}: duplicate {origin} row for app_code={app_code}"
            + (f" folder_id={folder_id}" if folder_id else "")
            + " — folder → application is 1:1 (OWNER-NOT-USER); author one row"
        )
    seen.add(key)
    return {
        "app_code": app_code,
        "folder_id": folder_id,
        "tier": tier,
        "app_id": app_id,
        "declared_end_state": end_state,
        "origin": origin,
        "rationale": rationale,
        "authored_by": authored_by,
        "authored_on": _text(row.get("authored_on")),
    }


def _ingest_app_code_mappings(conn: sqlite3.Connection, path: Path) -> None:
    """Ingest the committed defined-mapping list (K9). Validation fails loudly
    per row — the file is steward-authored and IS the source of record for
    this domain (§E2), so a bad row is a mistake to fix at the source."""
    if not path.exists():
        raise MappingStoreError(f"mapping-store source not found: {path}")
    seen: set[tuple[str, str, str]] = set()
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for line_no, raw in enumerate(reader, start=2):
            row = validate_app_code_row(raw, where=f"{path.name} line {line_no}", seen=seen)
            conn.execute(
                "INSERT INTO app_code_mapping (line_no, app_code, folder_id, tier, "
                "app_id, declared_end_state, origin, rationale, authored_by, "
                "authored_on) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    line_no,
                    row["app_code"],
                    row["folder_id"],
                    row["tier"],
                    row["app_id"],
                    row["declared_end_state"],
                    row["origin"],
                    row["rationale"],
                    row["authored_by"],
                    row["authored_on"],
                ),
            )


# ---------------------------------------------------------------------------
# Deterministic dumps — the gate-reviewable text twin of the binary DB.
# ---------------------------------------------------------------------------


def dump_csv(conn: sqlite3.Connection, out_dir: str | Path) -> list[Path]:
    """Write one sorted CSV per table. Byte-identical for identical sources —
    the drift/round-trip guarantee the unit test asserts."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for table, order in _DUMP_ORDER.items():
        cur = conn.execute(f"SELECT * FROM {table} ORDER BY {order}")  # — fixed registry
        cols = [d[0] for d in cur.description]
        path = out_dir / f"{table}.csv"
        with path.open("w", encoding="utf-8", newline="\n") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(cols)
            for row in cur:
                writer.writerow(["" if v is None else v for v in row])
        written.append(path)
    return written


# ---------------------------------------------------------------------------
# M1/M3 read seam — manual mapping rows served FROM the materialization.
# ---------------------------------------------------------------------------


def manual_mapping_rows_from_store(
    csv_path: str | Path,
    *,
    manifest_path: str | Path = MANIFEST_PATH,
    vocabulary_path: str | Path = VOCABULARY_PATH,
) -> list[ManualMappingRow]:
    """Return the ManualMappingRow list for one registered CSV, read back
    across the SQL boundary of an in-memory build (the M3 read path).

    Validation is identical to the legacy path by construction (build()
    ingests via parse_mapping_csv); what this adds is the DB round-trip,
    guarded by the parity test.
    """
    manifest_path = Path(manifest_path)
    repo_root = manifest_path.resolve().parents[2]
    file_rel = Path(csv_path).resolve().relative_to(repo_root).as_posix()

    conn = build(
        ":memory:",
        manifest_path=manifest_path,
        vocabulary_path=vocabulary_path,
    )
    try:
        cur = conn.execute(
            "SELECT app_code, folder_id, app_id, create_target_if_missing, "
            "file, authored_by, authored_on, note "
            "FROM manual_mapping WHERE file = ? ORDER BY line_no",
            (file_rel,),
        )
        rows = [
            ManualMappingRow(
                app_code=r[0],
                folder_id=r[1],
                app_id=r[2],
                create_target_if_missing=bool(r[3]),
                manual_load_file=r[4],
                authored_by=r[5],
                authored_on=r[6],
                note=r[7],
            )
            for r in cur
        ]
    finally:
        conn.close()
    if not rows:
        raise ManualLoadError(
            f"{csv_path}: no rows materialized — is the CSV registered and loadable "
            "in config/manual-loads/manifest.yaml?"
        )
    return rows


def app_code_rows_from_store(
    *,
    app_code_mappings_path: str | Path | None = None,
) -> list[dict]:
    """Authored app-code mapping rows (K9 store; gate §E2: the store IS the
    source of record for this domain), read back across the SQL boundary of
    an in-memory build — the K8 folder-attribution loader's input.

    Every returned row is AUTHORED (origin defined | override | manual-pin):
    matched-fallback is refused at authoring and exists only as a load-time
    derivation the loader discloses on the edge (§B3).
    """
    conn = build(":memory:", app_code_mappings_path=app_code_mappings_path)
    try:
        cur = conn.execute(
            "SELECT app_code, folder_id, tier, app_id, declared_end_state, "
            "origin, rationale, authored_by, authored_on "
            "FROM app_code_mapping ORDER BY line_no"
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r, strict=True)) for r in cur]
    finally:
        conn.close()


def tables(conn: sqlite3.Connection) -> Iterable[str]:
    return [
        r[0]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
    ]
