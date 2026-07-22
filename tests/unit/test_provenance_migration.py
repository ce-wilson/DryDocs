"""Guards for the doc-06 Phase 3 provenance cleanup (backlog M2, 2026-07-21).

Static file checks only — the migration's graph effects are verified live by
`drydocs m3-verify` (its three Phase-3 invariants) after the HITL-confirmed
run. These tests pin the non-graph half: loaders write the post-diet shape
(first_seen_at bookkeeping, no raw-named folder audit props) and the migration
file keeps its safety rails (pre-diet run filter, snapshot-label exclusions,
batched destructive steps).
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CYPHER_DIR = REPO / "drydocs" / "loaders" / "cypher"
MIGRATION_FILE = (
    REPO / "drydocs" / "migrations" / "20260721_provenance_diet_cleanup.cypher"
)
FOLDERS_CYPHER = CYPHER_DIR / "controlm_folders.cypher"


def test_no_loader_cypher_writes_created_at() -> None:
    """The pull-provenance naming standard is first_seen_at / last_seen_at /
    last_run_id — node bookkeeping created_at retired at M2. (The token
    source_created_at is the audit ENVELOPE and does not contain
    '.created_at', so an exact-token scan is safe.)"""
    offenders = []
    for path in sorted(CYPHER_DIR.glob("*.cypher")):
        if ".created_at" in path.read_text(encoding="utf-8"):
            offenders.append(path.name)
    assert not offenders, (
        f"loader cypher(s) still write node created_at: {offenders} — "
        "use first_seen_at (doc 06 Phase 3)"
    )


def test_folders_cypher_writes_envelope_not_raw_names() -> None:
    text = FOLDERS_CYPHER.read_text(encoding="utf-8")
    assert "f.source_updated_at" in text
    assert "f.source_updated_by" in text
    # The raw-named node props retired at M2; row.last_updated (the extract
    # column feeding the envelope) legitimately remains.
    assert "f.last_updated " not in text and "f.last_updated=" not in text, (
        "folders cypher still writes the raw-named last_updated node prop"
    )
    assert "f.last_updated_user" not in text, (
        "folders cypher still writes the raw-named last_updated_user node prop"
    )


def test_migration_file_safety_rails() -> None:
    text = MIGRATION_FILE.read_text(encoding="utf-8")
    # Deletion is scoped to pre-diet COMPLETED runs only — never a bare
    # WAS_GENERATED_BY sweep; ambiguous runs are surfaced, not deleted.
    assert "run.rows_changed IS NULL" in text
    assert "{kind: 'load', status: 'OK'}" in text
    # The snapshot writer's own created_at vocabulary is excluded from the
    # rename.
    for label in ("ApplicationSnapshot", "ProductSnapshot", "CatalogLOBSnapshot"):
        assert f"NOT n:{label}" in text, f"rename must exclude :{label}"
    # Destructive steps run batched.
    assert "IN TRANSACTIONS" in text
    # Backfill only fills gaps (idempotent re-run).
    assert "f.source_updated_at IS NULL" in text


def test_manual_loads_reads_first_seen_at() -> None:
    text = (REPO / "drydocs" / "loaders" / "manual_loads.py").read_text(
        encoding="utf-8"
    )
    assert "n.first_seen_at IS NOT NULL" in text
    assert "n.created_at" not in text
