"""U17 — the code-graph review plan's staleness ranking is DEFINED, not implied.

The plan is the instrument spec for a recurring three-persona review. Phase 3
unit 2 used to name `DesignDoc.commit` and then describe it as "each doc's last
touch" in the same sentence. Those are two different facts about a document —
what its author asserts it reflects, and when the file was last edited — and on
the worked example they put the same runbook at opposite ends of the queue
(claim_lag 792 vs touch_lag 122 at 4ecfca0). An undefined ranking is not a small
gap: it means two runs of the same unit can disagree and both be "right".

These guards pin the ruling itself, not a number that moves with the repo.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLAN = REPO / "docs" / "reviews" / "code-graph-review-plan.md"

# The unit the ruling belongs to. Scoping every assertion to this slice keeps a
# stray mention elsewhere in the plan from satisfying a guard by accident.
UNIT_START = "2. **Staleness ranking.**"
UNIT_END = "3. **Coverage gaps by subsystem.**"


def _unit() -> str:
    plan = PLAN.read_text(encoding="utf-8")
    start = plan.index(UNIT_START)
    return plan[start : plan.index(UNIT_END, start)]


def test_the_three_measures_are_named_and_distinguished() -> None:
    """Naming is the fix. As long as one word ('staleness') covered two facts,
    every query author re-decided which one it meant."""
    unit = _unit()
    for measure in ("claim_lag", "touch_lag", "citation_lag"):
        assert measure in unit, (
            f"the staleness unit no longer names `{measure}` — the three measures were "
            f"separated precisely so no run has to guess which one it is ranking on"
        )


def test_the_ranking_key_is_stated_and_is_the_claim() -> None:
    """Ranking on touch_lag would hide this unit's own subject: a doc edited ten
    times without ever being re-checked against the code ranks as FRESH."""
    unit = _unit()
    assert re.search(r"[Rr]ank .{0,40}on `claim_lag`", unit), (
        "the unit no longer states that the re-verify queue ranks on `claim_lag` — "
        "without a named key the ranking is undefined again (U17)"
    )


def test_the_conflation_that_caused_this_does_not_return() -> None:
    """The original defect in one sentence: `DesignDoc.commit` introduced, then
    glossed as the doc's last touch. It is an author's assertion transcribed from
    prose; the last touch is a git fact."""
    # Not line-scoped: the original defect spanned a line break ("`DesignDoc.commit`
    # vs `Project.git_commit`" then "how many commits behind is each doc's last
    # touch"), so a per-line check would have passed the very text it exists to
    # catch. Quoted spans are stripped first -- the ruling has to be able to quote
    # the wording it replaced without tripping its own guard.
    unit = re.sub(r"\s+", " ", re.sub(r'"[^"]*"', "", _unit()))
    hit = re.search(r"DesignDoc\.commit.{0,200}?\blast touch\b", unit, re.I)
    # The message is only evaluated when the assertion fails, so hit is not None
    # wherever it is dereferenced.
    assert not hit, (
        "`DesignDoc.commit` is glossed as the doc's last touch again; it is the author's "
        f"CLAIM, and the two are what U17 exists to keep apart:\n  ...{hit.group(0) if hit else ''}..."
    )


def test_each_degenerate_case_is_ruled() -> None:
    """A rule that covers only the happy path leaves the query author deciding
    the interesting rows — which is the undefined state in a smaller box."""
    unit = _unit()
    assert "**unknown**" in unit, (
        "the no-citation case is unruled; the hazard is silently substituting touch_lag "
        "and reporting a doc that claims nothing as fresh"
    )
    assert "**maximum**" in unit, (
        "the unreachable-citation case is unruled; a claim that cannot be checked must "
        "outrank one measured as far behind"
    )


# --- U18: the $packages allow-list is typed by hand, so pin it to a fact -----

SKILL = REPO / ".claude" / "skills" / "tech-debt" / "SKILL.md"
PYPROJECT = REPO / "pyproject.toml"

# `tests` is a scan root and not a distributable package, so it is the one
# entry that legitimately has no counterpart in pyproject.
NON_PACKAGE_ROOTS = {"tests"}


def _declared_packages() -> set[str]:
    """The authoritative list: what the project actually ships."""
    import tomllib

    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return {entry["include"] for entry in data["tool"]["poetry"]["packages"]}


def _typed_allow_list(text: str, anchor: str) -> set[str]:
    start = text.index(anchor)
    return set(re.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'", text[start : text.index("]", start)]))


def test_the_typed_package_scope_matches_what_the_project_ships() -> None:
    """The failure this exists for, twice over.

    `drydocs_api` was invisible to every metric until the U2 census; then
    `drydocs_docmeta` was born on 2026-08-04 in d647171 — the commit that added
    it to pyproject.toml — on the same day U14 typed seven roots into the pack,
    so ten modules were outside A3/A4/A5 from the hour the list was written.
    Both times the authoritative answer was already sitting in pyproject.toml.
    A hand-maintained list makes a third instance a matter of time, so the list
    is now checked against the fact rather than trusted.
    """
    expected = _declared_packages() | NON_PACKAGE_ROOTS
    for path, anchor in ((SKILL, "$packages = ["), (PLAN, "`m.project IN [")):
        typed = _typed_allow_list(path.read_text(encoding="utf-8"), anchor)
        missing = expected - typed
        extra = typed - expected
        assert not missing and not extra, (
            f"{path.relative_to(REPO).as_posix()}: the metric scope disagrees with "
            f"pyproject.toml [tool.poetry] packages + {sorted(NON_PACKAGE_ROOTS)}.\n"
            f"  missing (modules invisible to every A3/A4/A5 number): {sorted(missing)}\n"
            f"  unexpected: {sorted(extra)}"
        )


def test_the_layering_query_carries_its_own_widened_list() -> None:
    """A1 does not use `$packages` — it hardcodes the upward targets, so it
    needed the U18 widening on its own. Before that, "does core import
    drydocs_docmeta?" was a question the pack could not ask, and a clean result
    would have meant nothing."""
    skill = SKILL.read_text(encoding="utf-8")
    a1 = skill[skill.index("| A1 |") : skill.index("| A2 |")]
    upward = set(re.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'", a1))
    missing = (_declared_packages() - {"drydocs_core"}) - upward
    assert not missing, (
        "the A1 layering query's hardcoded upward-target list is missing "
        f"{sorted(missing)} — a core module importing those is undetectable, and A1's "
        "baseline of 0 would be silence rather than evidence"
    )


def test_the_reachability_check_is_ancestry_not_object_existence() -> None:
    """Machine-dependent, and verified as such: the five pre-squash citations
    resolve as objects on the desktop (the local archive tag keeps them alive)
    and are ancestors of HEAD on no machine. `cat-file` passes them here and
    fails them on a fresh clone."""
    unit = _unit()
    assert "merge-base --is-ancestor" in unit, (
        "the citation check no longer names `git merge-base --is-ancestor` — object "
        "existence is not reachability, and the difference is machine-dependent"
    )
    assert "cat-file" in unit, (
        "the plan no longer warns against `git cat-file -t` as the reachability test; "
        "that is the check that silently passes on this desktop and fails elsewhere"
    )
