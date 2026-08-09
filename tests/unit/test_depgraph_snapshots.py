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


# --- instrument currency (2026-08-04) ----------------------------------------


def _script() -> str:
    return (SNAP_DIR / "snapshot.ps1").read_text(encoding="utf-8")


def test_script_compares_the_checkout_against_the_pin() -> None:
    """The check the capability probe cannot do.

    A depgraph revision can pass every behavioural probe and still be stale,
    because new commits often add edge TYPES rather than capabilities. On
    2026-08-04 the laptop scanned on 5006567 while the desktop was already on
    773fb1e and nothing said so, leaving two snapshots that were not comparable
    by construction. `expected_commit` is the only record of the intended
    revision, so the script must read it and compare.
    """
    script = _script()
    assert "expected_commit" in script, (
        "snapshot.ps1 no longer reads depgraph.expected_commit — instrument drift is "
        "invisible again (the 2026-08-04 two-machine divergence)"
    )
    assert "merge-base --is-ancestor" in script, (
        "the drift classification is gone; a bare mismatch cannot tell 'sibling ahead' "
        "(benign, bump the pin) from 'sibling behind' (this scan is stale)"
    )
    # It must reason about the revision it RECORDS, not a freshly-read HEAD —
    # they agree in a normal run, but the recorded one is what the snapshot is
    # attributed to. An early version compared against HEAD and misreported
    # 'behind' as 'ahead'.
    assert "--is-ancestor $expCommit $depFull" in script, (
        "the ancestry test must compare against $depFull (the captured, recorded "
        "instrument revision), not against a fresh HEAD"
    )


def test_instrument_drift_warns_and_never_refuses() -> None:
    """Ruled 2026-08-04: WARN, do not refuse.

    A sibling legitimately AHEAD of the pin is the normal way a bump starts, so
    a hard failure would block the very work that fixes the drift. The capability
    refusal above it is a different question and keeps its `throw`.
    """
    script = _script()
    start = script.index("--- instrument CURRENCY")
    end = script.index("--- git metadata")
    block = script[start:end]
    assert "Write-Warning" in block, "the currency block no longer warns at all"
    assert "throw" not in block, (
        "the currency check must not refuse — a sibling ahead of the pin is normal, "
        "and refusing would block the bump that resolves it"
    )


def test_capability_refusal_quotes_the_pin_rather_than_a_frozen_sha() -> None:
    """The refusal text hardcoded `depgraph 5006567` and went stale the moment
    the pin moved — found at the 2026-08-04 bump. It must quote the config."""
    script = _script()
    start = script.index("Refusing to scan")
    end = script.index("--- instrument CURRENCY")
    refusal = script[start:end]
    assert "$pinDesc" in refusal, "the refusal no longer quotes the configured pin"
    assert not re.search(
        r"depgraph [0-9a-f]{7}\b", refusal
    ), "the refusal hardcodes a commit SHA again; it goes stale at the next pin bump"


# --- worktree state: tracked vs untracked (U15, 2026-08-09) ------------------


def test_dirty_counts_tracked_changes_only() -> None:
    """`dirty` is a provenance claim, so untracked files must not set it.

    A bare `git status --porcelain` lists untracked paths, so one boolean over
    both said "dirty" when the only dirt was a scratch file. The 20260805
    snapshot recorded dirty=true at exactly the pinned commit with three
    untracked paths as the whole story -- a header that states the opposite of
    the truth, since a reader takes dirty=true to mean the named commit does not
    describe the scanned code.
    """
    script = _script()
    assert "--untracked-files=no" in script, (
        "the worktree-state helper no longer excludes untracked files from `dirty` -- "
        "a stray scratch file marks the snapshot as not matching its own commit (U15)"
    )
    # The defect shape itself, in either spelling. `git status --porcelain` with
    # no untracked flag is the exact call that conflated the two facts.
    offenders = [
        line.strip()
        for line in script.splitlines()
        if not line.strip().startswith("#")
        and re.search(r"git (?:-C \S+ )?status --porcelain(?!\s*--untracked-files)", line)
    ]
    assert not offenders, (
        "a bare `git status --porcelain` is back; it counts untracked paths as dirt:\n"
        + "\n".join(offenders)
    )


def test_untracked_presence_is_recorded_rather_than_discarded() -> None:
    """Narrowing `dirty` must not throw the other fact away.

    Both header blocks carry it. On the INSTRUMENT side it is close to
    provenance rather than housekeeping: depgraph runs out of that checkout, so
    an untracked module there can take part in the scan while belonging to no
    commit.
    """
    script = _script()
    assert "ls-files --others --exclude-standard" in script, (
        "nothing detects untracked paths any more -- the U15 split dropped the fact "
        "instead of separating it"
    )
    meta_start = script.index("$meta = [ordered]@{")
    meta_end = script.index("$metaJson =", meta_start)
    meta = script[meta_start:meta_end]
    for block in ("git", "depgraph"):
        line = next(ln for ln in meta.splitlines() if ln.strip().startswith(f"{block} "))
        assert "untracked_present=" in line, (
            f"meta.{block} records `dirty` but not `untracked_present`; the reader can no "
            f"longer tell a scratch file from a real divergence"
        )


def test_readme_documents_the_tracked_untracked_split() -> None:
    """The README is the contract for the header shape -- consumers read it
    rather than the PowerShell. U12 already pins its currency; this pins the
    field the U15 change added."""
    readme = (SNAP_DIR / "README.md").read_text(encoding="utf-8")
    assert readme.count('"untracked_present"') >= 2, (
        "the documented meta shape still shows only `dirty` on one or both blocks"
    )
    assert "TRACKED changes only" in readme, (
        "the README does not say what `dirty` now means, so a reader will keep the old "
        "reading of a field whose meaning changed"
    )


def test_powershell_keeps_non_ascii_out_of_quoted_strings() -> None:
    """PS 5.1 decodes a BOM-less .ps1 as the ANSI codepage.

    A UTF-8 em dash then arrives as three CP1252 characters, the last of which
    is a smart quote — and PowerShell honours smart quotes as string delimiters,
    so a one-line "..." containing one ends early and the WHOLE script fails to
    parse. This was hit for real while building the currency check above.

    Comments and here-strings are unaffected and this repo's .ps1 files use em
    dashes freely in both; only single-line quoted literals are the hazard.
    """
    offenders: list[str] = []
    for path in sorted(REPO.rglob("*.ps1")):
        if any(part in {".git", "node_modules", "worktrees", ".venv"} for part in path.parts):
            continue
        raw = path.read_bytes()
        if raw[:3] == b"\xef\xbb\xbf":
            continue  # BOM present: PS decodes it as UTF-8, no hazard
        in_here_string = False
        for lineno, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            stripped = line.strip()
            if in_here_string:
                if stripped.startswith('"@') or stripped.startswith("'@"):
                    in_here_string = False
                continue
            if '@"' in line or "@'" in line:
                in_here_string = True
                continue
            if stripped.startswith("#"):
                continue
            code = line.split("#", 1)[0]
            if '"' in code and any(ord(ch) > 127 for ch in code):
                rel = path.relative_to(REPO).as_posix()
                offenders.append(f"{rel}:{lineno}: {stripped[:90]}")
    assert not offenders, (
        "non-ASCII inside a single-line double-quoted string in a BOM-less .ps1 — "
        "PS 5.1 reads it as CP1252 and the smart quote ends the string early, failing "
        "the whole script's parse. Use ASCII there, or move the text into a here-string:\n"
        + "\n".join(offenders)
    )
