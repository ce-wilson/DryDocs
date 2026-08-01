"""Guards for the doc-06 Phase 3 provenance diet (backlog M2, 2026-07-21).

Static file checks only — the graph-side invariants are verified live by
`drydocs m3-verify` (its three Phase-3 invariants). These tests pin the
non-graph half: loaders write the post-diet shape (first_seen_at bookkeeping,
no raw-named folder audit props). The one-time cleanup migration
(20260721_provenance_diet_cleanup.cypher) was removed 2026-07-23 after its
producer-side run — pre-diet graphs are rebuilt from bootstrap instead.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CYPHER_DIR = REPO / "drydocs" / "loaders" / "cypher"
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
    assert (
        "f.last_updated " not in text and "f.last_updated=" not in text
    ), "folders cypher still writes the raw-named last_updated node prop"
    assert (
        "f.last_updated_user" not in text
    ), "folders cypher still writes the raw-named last_updated_user node prop"


def test_manual_loads_reads_first_seen_at() -> None:
    text = (REPO / "drydocs" / "loaders" / "manual_loads.py").read_text(encoding="utf-8")
    assert "n.first_seen_at IS NOT NULL" in text
    assert "n.created_at" not in text
