"""U12 — the ruled snapshot retention (SME 2026-08-02) is enforced, not hoped for.

The ruling: the newest all-files snapshot is the ONLY one in
knowledge/depgraph-snapshots/; git history is the archive. Before U12 the
ruling lived in prose and a human delete — a same-day rerun wrote a -HHmm
sibling beside the first (four occurrences in the two days after the ruling,
and a 101-file series once before it). These tests pin the committed state,
the script's enforcement, and the README's currency.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SNAP_DIR = REPO / "knowledge" / "depgraph-snapshots"

# The all-files ritual shape: <project>-<date>[-HHmm].json. The first hyphen
# group is followed by the date digits, so -CodeOnly files (drydocs-code-*)
# and the retired drydocs1-* names never match — both are exempt by design.
ALL_FILES_SHAPE = re.compile(r"^[a-z0-9_]+-\d{8}(-\d{4})?\.json$")


def _all_files_snapshots() -> list[str]:
    return sorted(p.name for p in SNAP_DIR.glob("*.json") if ALL_FILES_SHAPE.match(p.name))


def test_directory_holds_exactly_one_all_files_snapshot() -> None:
    """The ruled retention as a repo invariant: exactly one ritual snapshot is
    committed. Zero would mean the ritual never ran; two or more is the U12
    defect back again (the -HHmm sibling, or a stale prior day)."""
    snapshots = _all_files_snapshots()
    assert len(snapshots) == 1, (
        f"expected exactly ONE all-files snapshot (newest-only ruling, SME 2026-08-02), "
        f"found {len(snapshots)}: {snapshots} — snapshot.ps1's retention step should have "
        f"removed the others; older snapshots belong in git history, not the working tree"
    )


def test_script_enforces_the_retention_after_the_write() -> None:
    """snapshot.ps1 must (a) carry the retention step, keyed on the all-files
    pattern, and (b) run it AFTER the snapshot is written — so a failed run can
    never delete the only good snapshot."""
    script = (SNAP_DIR / "snapshot.ps1").read_text(encoding="utf-8")
    pattern_literal = r"'^{0}-\d{{8}}(-\d{{4}})?\.json$'"
    assert pattern_literal in script, (
        "snapshot.ps1 no longer carries the all-files retention pattern — the newest-only "
        "ruling (SME 2026-08-02) is unenforced again"
    )
    retention_at = script.index(pattern_literal)
    write_at = script.index("WriteAllText")
    assert retention_at > write_at, (
        "the retention step must run AFTER the new snapshot is written; deleting first "
        "risks a failed run leaving no snapshot at all"
    )
    assert "Remove-Item" in script[retention_at:], "the retention block matches but never deletes"


def test_readme_documents_what_the_script_does() -> None:
    """U12 acceptance (b)/(c): the README describes the current instrument —
    whole-repo default + -CodeOnly (the -Tree flag was removed), the ruled
    retention instead of 'keep the last ~10', the all-files instrument-change
    marker, and no markdown link to a snapshot file the directory no longer
    contains (history is cited as history, never linked as present)."""
    readme = (SNAP_DIR / "README.md").read_text(encoding="utf-8")
    assert "-CodeOnly" in readme
    assert (
        "snapshot.ps1 -Tree" not in readme
    ), "the -Tree flag was removed; the command block is stale"
    assert "last ~10" not in readme, "the pre-ruling prune guidance is back"
    assert "238 → 1457" in readme, "the all-files instrument-change marker (fourth) is missing"
    for target in re.findall(r"\]\(([^)]+\.json)\)", readme):
        assert (SNAP_DIR / target).is_file(), (
            f"README links {target} as a present file but the directory does not contain it — "
            f"restate it as history recoverable from git instead of linking it"
        )
