"""J41 — guards for the port opening sequence.

Every assertion here is paired with its NEGATIVE case, because the whole item
exists because of checks that returned a plausible answer for the wrong reason
(J26 promise-vs-assertion). A coverage check that never reports an uncited commit
is indistinguishable from one that has nothing to report.
"""

from __future__ import annotations

import sys

import pytest

from drydocs.port import port_preflight as _pf
from drydocs.port.port_preflight import (
    ADVISORY_CHECKS,
    BASIS_TAGS,
    FOREIGN_PATHS,
    PLANNED_PATHS,
    RECORD_PREFIXES,
    REPO_ROOT,
    CheckResult,
    Commit,
    GitError,
    cited_paths,
    cited_shas,
    first_party_target,
    import_closure_outcome,
    import_edges,
    is_record_document,
    is_ritual,
    is_suite_guarded,
    next_base_tag,
    range_checks,
    relays_missing_basis,
    uncited_commits,
    unresolved_citations,
)

LEDGER = """\
STEP LEDGER — delta since `0d3761a9`.

116. O52 — THE ALWAYS-NULL COLUMN [TEST-PINNED] (`4ecfca0`).
    Some prose that mentions `0d3761a9` as the base.

117. EPIC U (`06c9f63` U15, `2d104ef` U17).

ACCEPTANCE GATE (behavior is the contract):
- a stray sha that must NOT count as a citation: `deadbee`
"""

RELAYS = """\
STANDING RELAYS (J38 — read this at EVERY port):

- **RELAY-1 (was R1) — AIS acronym expansion** [VERIFIED-PRODUCER] (standing
  since 2026-07-21). Producer's authoritative home is the software registry.
- ~~**RELAY-4 (was R4) — the J34 overlay migration**~~ — **STRUCK 2026-08-09.**
  Discharged; kept as an audit trail, not an instruction.
- **RELAY-5 (was R5) — DPL + Snowflake registry entries** (new 2026-08-09).
  You already pushed a software-registry change with the internal URL.

OWED COMPANY-SIDE:
"""


# ---- the ritual classifier ---------------------------------------------------


@pytest.mark.parametrize(
    "subject",
    [
        "chore(backlog): groom — 11 promoted, 3 merged",
        "chore(backlog): claim J41 in_progress (pushed before work)",
        "chore(depgraph): snapshot drydocs-20260809 @ 9270002",
        # Without these two the check cannot terminate — see below.
        "chore(port): roll the ledger through 0d3761a9",
        "chore(port): ledger step 122 — J41",
        # THE DRIFTED SPELLINGS (2026-08-29). The ledger header exempted claims,
        # renders and snapshots from the start; these are the subjects the repo
        # actually writes them as, and each one was reported UNCITED on the
        # port-base-20260826 range until the patterns learned them.
        "chore(snapshot): roll the depgraph snapshot for the batch-2 close",
        "chore(depgraph): session-close snapshot @062d71f6 (drydocs-20260829)",
        "chore(plan): render the board, roadmap and load runbook after batch 2",
        "chore(plan): re-render board and roadmap from committed sources only",
        "chore(Z5): claim — in_progress",
        "chore(O63): release claim — back to todo",
        "chore(backlog): O69 in_progress — refusal now cites ADR 0009",
        # THE THIRD DRIFT (2026-09-01), same three categories again: the
        # session-close snapshot under a `session` scope, a claim released with an
        # article in it, and a claim written as a `backlog(<ID>)` TYPE.
        "chore(session): depgraph snapshot at 02cadd7, taken after CI went green",
        "chore(session): depgraph snapshot 2026-08-31, and the board catches up",
        "chore(O26): release the claim - the SME HOLD is live",
        "backlog(G125): claim in_progress (desktop)",
        # THE EDITION SEGMENT (PLAN2, 2026-09-05): `[<EDITION>-]<MODULE><n>`. A claim
        # for an edition's item is still a claim; before the segment was admitted it
        # read as substantive and the coverage guard demanded a ledger step for it.
        "chore(backlog): XMPL-LOAD1 in_progress",
        "chore(XMPL-LOAD1): claim",
        "backlog(XMPL-LOAD1): release claim",
    ],
)
def test_ritual_subjects_need_no_ledger_step(subject: str) -> None:
    assert is_ritual(subject)


def test_the_ledger_roll_commit_is_ritual_or_the_check_cannot_terminate() -> None:
    """Found by running this module against its own repository.

    The commit that WRITES the citations can never be among them, so if a roll
    were substantive every roll would mint a fresh uncited commit and the next
    roll would too — an infinite regress that reads as a real coverage gap.
    """
    roll = Commit("cdc7a85", "chore(port): ledger step 122 — J41")
    assert uncited_commits([roll], LEDGER) == []


@pytest.mark.parametrize(
    "subject",
    [
        "fix(api): O52 — holder_sid reads the property the loader writes",
        "feat(taxonomy): register snowflake and dpl product rows",
        # The near-misses matter most: a substantive commit must not inherit the
        # exemption from a chore-shaped prefix.
        "chore(backlog): rewrite the pull rule",
        "chore(depgraph): bump the instrument pin to 6ee0af6",
        "chore(manifest): retire the three discharged packs",
        # The roll exemption is narrow ON PURPOSE: retiring manifest rows is also
        # a chore(port) and IS substantive work a consumer must be told about.
        "chore(port): retire the three discharged packs",
        "chore(port): stage five company packs above the never-port glob",
        # A CLOSE IS NOT RITUAL, and the boundary is deliberate: the ledger
        # header lists grooms, claims, renders and snapshots, never closes, and
        # close notes carry findings a consumer must read. Pinned so a later
        # widening cannot quietly swallow them.
        "chore(backlog): close G112 — the artifact pass resolves before counting",
        "chore(backlog): close J55 — the retired-acronym boundary guard is live",
        # Near-misses for the new patterns: the scope shape alone must not exempt.
        "chore(plan): the Lane B queue is empty — the handoff retires",
        "chore(snapshot): retire the newest-only retention ruling",
        # Near-misses for the 2026-09-01 patterns. A `session` scope alone is not
        # an exemption — the subject must say snapshot; a `backlog(<ID>)` type
        # alone is not one either — it must open with claim; and a MINT is
        # deliberately outside the ritual set, covered by footnote citation.
        "chore(session): the depgraph pin moves to the scrubbed archive tag",
        "backlog(O60): the BDAT layers become a second lane basis for the swimlane",
        "chore(Idea-233): mint the id and its final title, per the I6 rule",
        "chore(backlog): mint G132 + G133 (stubs) - home the folder-pull collector",
    ],
)
def test_substantive_subjects_are_never_ritual(subject: str) -> None:
    assert not is_ritual(subject)


# ---- citation parsing --------------------------------------------------------


def test_citations_are_read_from_the_ledger_section_only() -> None:
    found = cited_shas(LEDGER)
    assert {"4ecfca0", "06c9f63", "2d104ef"} <= found
    # Past the ACCEPTANCE GATE marker the section has ended — a sha quoted in the
    # acceptance prose is not a ledger citation.
    assert "deadbee" not in found


def test_a_missing_ledger_section_cites_nothing_rather_than_everything() -> None:
    """Failing OPEN here would reproduce the defect the module exists to catch.

    The input MUST contain a sha outside any ledger, or the test cannot tell
    fail-open from fail-closed — both return the empty set on sha-free text. The
    first draft of this test used sha-free text and passed against a deliberately
    fail-open ``_section``.
    """
    stray = "A document with no ledger at all, but it does quote `4ecfca0` in passing."
    assert cited_shas(stray) == set()


# ---- the coverage check ------------------------------------------------------


def test_a_cited_commit_is_covered_and_an_uncited_one_is_named() -> None:
    commits = [
        Commit("4ecfca0", "fix(api): O52 — holder_sid"),
        Commit("beefcaf", "feat(port): something nobody ledgered"),
    ]
    missing = uncited_commits(commits, LEDGER)
    assert [c.sha for c in missing] == ["beefcaf"]


def test_coverage_matches_on_prefix_in_both_directions() -> None:
    """The ledger abbreviates to 7 chars; git may hand back 40."""
    long_sha = "4ecfca0" + "a" * 33
    assert uncited_commits([Commit(long_sha, "fix(api): O52")], LEDGER) == []


def test_a_citation_buried_mid_sha_does_not_count_as_coverage() -> None:
    """PREFIX, not substring — and the distinction is load-bearing.

    Under substring matching an unrelated commit whose sha merely CONTAINS a cited
    one reads as covered, so the ledger silently gains coverage it never wrote.
    The prefix test above cannot catch that: a cited prefix is also a substring at
    position 0, so both implementations pass it. This case separates them.
    """
    buried = "aaa4ecfca0" + "b" * 30
    assert [c.sha for c in uncited_commits([Commit(buried, "feat(x): unledgered")], LEDGER)] == [
        buried
    ]


def test_ritual_commits_are_never_reported_as_uncited() -> None:
    commits = [Commit("f00dfee", "chore(backlog): claim J41 in_progress")]
    assert uncited_commits(commits, LEDGER) == []


def test_the_coverage_check_fires_on_a_ledger_that_stopped_early() -> None:
    """The exact 2026-08-09 state: the ledger ended at 115 with 38 commits past it."""
    stalled = "STEP LEDGER\n\n115. THE PORT-MACHINERY TRIO (`aaaaaaa`).\n\nACCEPTANCE GATE\n"
    commits = [Commit(f"{i:07x}", f"fix(x): real work {i}") for i in range(1, 39)]
    assert len(uncited_commits(commits, stalled)) == 38


# ---- relay basis tags --------------------------------------------------------


def test_a_live_relay_without_a_basis_tag_is_reported() -> None:
    """RELAY-5 as actually written: an SME report asserted as company state."""
    assert relays_missing_basis(RELAYS) == ["RELAY-5"]


def test_a_tagged_relay_passes_and_a_struck_one_is_exempt() -> None:
    missing = relays_missing_basis(RELAYS)
    assert "RELAY-1" not in missing, "a tagged relay must pass"
    assert "RELAY-4" not in missing, "a struck relay is an audit trail, not an instruction"


@pytest.mark.parametrize("tag", BASIS_TAGS)
def test_every_declared_basis_tag_actually_satisfies_the_check(tag: str) -> None:
    """A tag in BASIS_TAGS that the matcher does not honour would be a silent hole."""
    text = RELAYS.replace(
        "  You already pushed a software-registry change with the internal URL.",
        f"  {tag} You already pushed a software-registry change.",
    )
    assert relays_missing_basis(text) == []


def test_a_missing_relay_section_reports_nothing() -> None:
    assert relays_missing_basis("no relays here") == []


# ---- cited-path resolution ---------------------------------------------------

#: The Idea-110 document, reduced to the two lines that matter. `docs` is a real
#: top-level directory and the mark was really deleted, so this is the live case.
#: (The citations sat under `UI-WIP/` until S9 moved that workspace to
#: `docs/design/ui-exploration/`; the first path segment is what this fixture turns on.)
IDLE_DOC = """\
# Claude Design UI starting prompt

Approved / canonical: final mark `docs/design/ui-exploration/drydocs-mark.svg` + `drydocs-mark-mini.svg`,
brand sheet `docs/design/ui-exploration/kept-orbit-brand-sheet.png`.
"""

ROOTS = frozenset({"docs", "drydocs", "drydocs_core", "scripts", "tests", "web"})

#: Everything the idle doc names EXCEPT the deleted mark.
PRESENT = {"docs/design/ui-exploration/kept-orbit-brand-sheet.png"}


def _exists(rel: str) -> bool:
    return rel in PRESENT


def test_the_deleted_mark_is_reported_and_the_live_asset_is_not() -> None:
    """The exact 2026-08-12 failure: a merge validated text overlap, not the tree."""
    findings = unresolved_citations(
        {"docs/design/ui-exploration/claude-design-ui-prompt.md": IDLE_DOC},
        repo_roots=ROOTS,
        exists=_exists,
    )
    assert findings == [
        (
            "docs/design/ui-exploration/claude-design-ui-prompt.md",
            "docs/design/ui-exploration/drydocs-mark.svg",
        )
    ]


def test_a_document_whose_every_citation_resolves_reports_nothing() -> None:
    """The negative case, and it must not pass by finding nothing to look at.

    ``PRESENT`` covers the mark here, so the doc IS scanned and the scan comes back
    clean — distinguishable from a filter that silently dropped the document.
    """
    everything = PRESENT | {"docs/design/ui-exploration/drydocs-mark.svg"}
    assert cited_paths(IDLE_DOC, ROOTS) == everything, "the doc must actually be scanned"
    assert (
        unresolved_citations(
            {"docs/design/ui-exploration/claude-design-ui-prompt.md": IDLE_DOC},
            repo_roots=ROOTS,
            exists=lambda rel: rel in everything,
        )
        == []
    )


# ---- the two filters, each with the case that separates it from its absence ----


def test_a_bare_filename_is_a_mention_rather_than_a_path() -> None:
    """``drydocs-mark-mini.svg`` was deleted in the same commit as its sibling.

    It is deliberately NOT reported: with no directory there is nothing to resolve
    against, and the currency guard draws the line in the same place. Under-reach
    that is written down beats a guard that fires on every filename in prose.
    """
    assert "drydocs-mark-mini.svg" not in cited_paths(IDLE_DOC, ROOTS)


def test_a_path_relative_to_the_document_is_not_a_claim_about_this_tree() -> None:
    """``results/GRADES.md`` and ``jobs/base.py`` — 53 of the 59 findings on the
    live range, and not one of them a defect. ``results`` and ``jobs`` are not
    top-level entries here, so neither citation was ever about this repo."""
    text = "See `results/GRADES.md` and the foreign `jobs/base.py`."
    assert cited_paths(text, ROOTS) == set()


def test_the_root_filter_does_not_swallow_a_real_stale_path() -> None:
    """The filter above must discriminate, not just suppress.

    ``drydocs_core/controlm/paths.py`` has a genuine top-level root and genuinely
    does not exist — the same class as the PORT-MANIFEST row that pointed at
    ``drydocs_core/controlm/**``. A filter that also dropped this would be a hole.
    """
    text = "The resolver lives in `drydocs_core/controlm/paths.py`."
    assert cited_paths(text, ROOTS) == {"drydocs_core/controlm/paths.py"}
    assert unresolved_citations({"d.md": text}, repo_roots=ROOTS, exists=_exists) == [
        ("d.md", "drydocs_core/controlm/paths.py")
    ]


# ---- the exemptions ----------------------------------------------------------


def test_a_document_that_declares_itself_a_record_is_exempt() -> None:
    """How Idea-110 was actually closed: annotated as a record, not edited."""
    record = "# Prompt — RECORD\n\n```yaml\nstatus: DATED RECORD\n```\n\n" + IDLE_DOC
    assert is_record_document("docs/design/ui-exploration/claude-design-ui-prompt.md", record)
    assert (
        unresolved_citations(
            {"docs/design/ui-exploration/x.md": record}, repo_roots=ROOTS, exists=_exists
        )
        == []
    )


def test_the_marker_must_be_a_header_declaration_not_a_phrase_in_the_body() -> None:
    """Otherwise a document that merely DISCUSSES dated records silences itself."""
    buried = "\n".join(["filler"] * 40) + "\nstatus: DATED RECORD\n" + IDLE_DOC
    assert not is_record_document("docs/x.md", buried)


@pytest.mark.parametrize("prefix", sorted(RECORD_PREFIXES))
def test_every_record_prefix_actually_exempts_and_carries_a_reason(prefix: str) -> None:
    """A prefix the matcher does not honour would be a silent hole; a prefix
    without a reason is an exemption whose justification outlived its author."""
    assert len(RECORD_PREFIXES[prefix].strip()) >= 40
    assert is_record_document(f"{prefix}some-capture.md", IDLE_DOC)


def test_a_document_outside_every_record_prefix_is_still_checked() -> None:
    """The negative case for the table: near-misses must not inherit the exemption."""
    assert not is_record_document("docs/review-notes.md", IDLE_DOC)
    assert not is_record_document("internal/controlm-config/plan.md", IDLE_DOC)


# ---- the per-path tables, and the two ways each can rot ----------------------


def test_a_declared_foreign_or_planned_path_is_not_reported() -> None:
    """The positive control, written so it cannot pass by scanning nothing.

    The document names one exempt path from each table AND one ordinary missing
    path. Reporting exactly the ordinary one proves the document was scanned and
    the two skips are the tables' doing — a filter that dropped the document would
    report nothing and read identically.
    """
    foreign = next(iter(FOREIGN_PATHS))
    planned = next(iter(PLANNED_PATHS))
    text = (
        f"Edit your `{foreign}`, then unit 5.8 builds `{planned}`, "
        "and see `docs/design/ui-exploration/drydocs-mark.svg`."
    )
    roots = ROOTS | {foreign.split("/")[0], planned.split("/")[0]}
    assert {foreign, planned} <= cited_paths(text, roots), "the tables must be reached"
    assert unresolved_citations({"d.md": text}, repo_roots=roots, exists=_exists) == [
        ("d.md", "docs/design/ui-exploration/drydocs-mark.svg")
    ]


@pytest.mark.parametrize(
    ("label", "path"),
    [("FOREIGN_PATHS", p) for p in sorted(FOREIGN_PATHS)]
    + [("PLANNED_PATHS", p) for p in sorted(PLANNED_PATHS)],
)
def test_every_path_exemption_carries_a_reason(label: str, path: str) -> None:
    """An exemption without a reason outlives the person who knew why."""
    table = FOREIGN_PATHS if label == "FOREIGN_PATHS" else PLANNED_PATHS
    assert len(table[path].strip()) >= 40, f"{label}[{path!r}] needs a real reason"


@pytest.mark.parametrize("path", sorted(FOREIGN_PATHS))
def test_a_foreign_path_is_genuinely_absent_here(path: str) -> None:
    """The entry claims the path is ANOTHER tree's. If it turns up in this one the
    claim is false, and the check must go back to reading it."""
    assert not (
        REPO_ROOT / path
    ).exists(), (
        f"{path!r} exists in this tree, so it is not foreign — remove the FOREIGN_PATHS entry"
    )


@pytest.mark.parametrize("path", sorted(PLANNED_PATHS))
def test_a_planned_path_that_has_landed_leaves_the_table(path: str) -> None:
    """This table's whole difference from FOREIGN_PATHS is that it EXPIRES.

    A planned path resolves the moment its unit lands, and from then on the
    exemption is hiding a live citation from a live check. The condition is
    observable, so it is asserted rather than trusted to a future reader.
    """
    assert not (REPO_ROOT / path).exists(), (
        f"{path!r} has landed — delete its PLANNED_PATHS entry; the citation now resolves "
        "on its own and the exemption is suppressing a real check"
    )


def test_the_documents_the_suite_already_resolves_are_not_reported_twice() -> None:
    assert is_suite_guarded("docs/port/port-prompt.md")
    assert is_suite_guarded("docs/design/drydocs-core-runbook.md")
    assert (
        unresolved_citations(
            {"docs/port/port-prompt.md": IDLE_DOC}, repo_roots=ROOTS, exists=_exists
        )
        == []
    )


def test_a_new_design_doc_that_is_not_a_runbook_is_this_check_s_to_catch() -> None:
    """The skip is narrow on purpose — ``test_runbook_currency`` globs ``*-runbook.md``
    only, so anything else under ``docs/design/`` must fall INTO this check."""
    assert not is_suite_guarded("docs/design/drydocs-core-tdd.md")
    assert unresolved_citations(
        {"docs/design/drydocs-core-tdd.md": IDLE_DOC}, repo_roots=ROOTS, exists=_exists
    ) == [("docs/design/drydocs-core-tdd.md", "docs/design/ui-exploration/drydocs-mark.svg")]


# ---- tag naming --------------------------------------------------------------


def test_the_base_tag_takes_the_plain_date_when_free() -> None:
    assert next_base_tag([], "20260809") == "port-base-20260809"


def test_a_second_certification_on_one_day_suffixes_rather_than_collides() -> None:
    """Mirrors the company's own `-20260809b` backup-tag convention."""
    existing = ["port-base-20260809"]
    assert next_base_tag(existing, "20260809") == "port-base-20260809b"
    assert next_base_tag([*existing, "port-base-20260809b"], "20260809") == "port-base-20260809c"


# ---- PORT8: the preflight fails closed --------------------------------------
#
# Slot 7 of the module sweep demonstrated the defect: real base, 38 commits and
# 8 added documents; bogus base, 0 and 0; and `uncited_commits([], text)` is []
# so the certification passed. The worse the base, the greener the report. These
# pin the three facts that close it - a git failure is loud, an unresolvable base
# is NOT CHECKED (never clean), and an EMPTY range on a base that resolves is
# still a clean pass, because "no commits" and "could not look" are different
# answers.


def test_git_helper_raises_on_a_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    def fake_run(args, **kwargs):  # - subprocess.run's signature
        return subprocess.CompletedProcess(
            args, 128, stdout="", stderr="fatal: bad revision 'nosuchref'"
        )

    monkeypatch.setattr(_pf.subprocess, "run", fake_run)
    with pytest.raises(GitError) as err:
        _pf._git("log", "nosuchref..HEAD")
    assert err.value.returncode == 128
    assert "bad revision" in err.value.stderr


def test_a_not_checked_result_can_never_have_passed() -> None:
    """CORE10: the verdict is READ off the shared type (ADR 0021), so the impossible
    state - not checked, yet passed - is not representable rather than refused."""
    result = CheckResult.skipped(
        "ledger coverage", "the base did not resolve, so the range could not be read"
    )
    assert result.verdict == "NOT CHECKED" and not result.passed and result.not_checked
    assert result.detail.startswith("NOT CHECKED - ")
    assert CheckResult.ok("x", "fine").verdict == "PASS"
    assert CheckResult.failed("x", "one thing wrong").verdict == "FAIL"
    with pytest.raises(ValueError):  # a skip with no written reason is refused by the type
        CheckResult.skipped("x", "skipped")
    with pytest.raises(TypeError):  # and the outcome itself never reads as a boolean
        bool(result.outcome)


def test_an_unresolvable_base_is_not_checked_never_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_git(*args: str, cwd=None):
        raise GitError(args, 128, "fatal: Needed a single revision")

    monkeypatch.setattr(_pf, "_git", failing_git)
    results = range_checks("nosuchref", LEDGER)
    by_name = {r.name: r for r in results}
    assert set(by_name) == {
        "base resolves",
        "ledger coverage",
        "cited paths resolve",
        "range import closure",
    }
    for r in results:
        assert r.not_checked, r.name
        assert not r.passed, r.name
        assert "NOT CHECKED" in r.detail, r.name
        assert r.outcome.is_not_checked and r.outcome.reason, r.name


def test_an_empty_range_on_a_real_base_is_still_a_clean_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def resolving_git(*args: str, cwd=None):
        calls.append(args)
        if args[0] == "rev-parse":
            return "0d3761a9deadbeef"
        return ""  # an empty log and an empty diff: nothing in the range

    monkeypatch.setattr(_pf, "_git", resolving_git)
    results = range_checks("0d3761a9", LEDGER)
    by_name = {r.name: r for r in results}
    assert by_name["base resolves"].passed and not by_name["base resolves"].not_checked
    assert by_name["ledger coverage"].passed and not by_name["ledger coverage"].not_checked
    assert "all 0 commits" in by_name["ledger coverage"].detail
    # clean over ZERO is visible on the type, never hidden behind "clean" (ADR 0021 D1)
    assert by_name["ledger coverage"].outcome.size == 0
    assert by_name["cited paths resolve"].passed
    assert calls[0][0] == "rev-parse", "the base is resolved before the range is read"


# ── PORT9: the range's import closure ────────────────────────────────────────
# Slice I, 2026-09-11: the consumer took drydocs_api/app.py (in range, default_ok)
# and it imported drydocs_api/corpus_status.py, which no roll's range had ever
# carried - so the take could not import. PORT12's cli_schema break was the same
# shape a roll earlier. Both were found by ModuleNotFoundError AFTER the take;
# this computes the list BEFORE it, for the consumer to intersect against its tree.

_TRACKED = {
    "drydocs_api/app.py",
    "drydocs_api/corpus_status.py",
    "drydocs_api/intake.py",
    "drydocs_core/repo_paths.py",
}


def _reader(sources: dict[str, str]):
    return lambda rel: sources.get(rel)


def test_a_dotted_name_is_ours_exactly_when_it_resolves_to_a_tracked_file() -> None:
    tracked = {"drydocs_api/app.py", "drydocs_core/orchestration/__init__.py"}
    assert first_party_target("drydocs_api.app", tracked) == "drydocs_api/app.py"
    # a package resolves through its __init__
    assert (
        first_party_target("drydocs_core.orchestration", tracked)
        == "drydocs_core/orchestration/__init__.py"
    )
    # third-party and stdlib resolve to nothing, with no prefix list to maintain
    assert first_party_target("pytest", tracked) is None
    assert first_party_target("ast", tracked) is None


def test_an_out_of_range_import_is_reported_and_an_in_range_one_is_not() -> None:
    in_range = {"drydocs_api/app.py", "drydocs_api/intake.py"}
    sources = {
        "drydocs_api/app.py": (
            "import ast\n"
            "from drydocs_api.corpus_status import corpus_status\n"  # OUT of range
            "from drydocs_api.intake import block_history\n"  # IN range
        ),
        "drydocs_api/intake.py": "from drydocs_core import repo_paths\n",  # OUT of range
    }
    edges = import_edges(in_range, _TRACKED, _reader(sources))
    assert [(e.importer, e.target) for e in edges] == [
        ("drydocs_api/app.py", "drydocs_api/corpus_status.py"),
        ("drydocs_api/intake.py", "drydocs_core/repo_paths.py"),
    ]
    # `ast` is stdlib and `intake` is in range - neither is a closure gap
    assert not any(e.module == "ast" for e in edges)
    assert not any(e.target == "drydocs_api/intake.py" for e in edges)


def test_a_relative_import_is_not_counted_because_its_module_reports_its_own_gaps() -> None:
    in_range = {"drydocs_api/app.py"}
    sources = {"drydocs_api/app.py": "from . import corpus_status\nfrom .intake import x\n"}
    assert import_edges(in_range, _TRACKED, _reader(sources)) == []


def test_a_file_deleted_in_the_range_or_unparseable_is_skipped_rather_than_raising() -> None:
    in_range = {"drydocs_api/app.py", "drydocs_api/gone.py", "drydocs_api/broken.py"}
    sources = {
        "drydocs_api/app.py": "from drydocs_core import repo_paths\n",
        "drydocs_api/broken.py": "def (:\n",  # a syntax error is not a closure verdict
        # "gone.py" is absent from the reader entirely - deleted in the range
    }
    edges = import_edges(in_range, _TRACKED, _reader(sources))
    assert [e.target for e in edges] == ["drydocs_core/repo_paths.py"]


def test_a_closed_range_is_clean_and_says_how_much_it_read() -> None:
    outcome = import_closure_outcome([], in_range_count=7)
    assert outcome.is_clean and not outcome.is_not_checked
    # clean over a KNOWN size, never a bare pass (ADR 0021 D1)
    assert outcome.size == 7


def test_the_closure_check_can_actually_fail() -> None:
    """The anti-vacuity control (J26), and it is load-bearing here.

    This check is ADVISORY - it never blocks certification - so nothing else in
    the suite would notice if it silently stopped reporting. A guard that cannot
    fail is not a guard, and an advisory that cannot fire is worse: it reads as
    "closure is fine" forever.
    """
    in_range = {"drydocs_api/app.py"}
    sources = {"drydocs_api/app.py": "from drydocs_api.corpus_status import corpus_status\n"}
    edges = import_edges(in_range, _TRACKED, _reader(sources))
    assert edges, "the positive case must produce an edge or this control proves nothing"
    outcome = import_closure_outcome(edges, in_range_count=1)
    assert not outcome.is_clean and not outcome.is_not_checked
    rendered = "\n".join(outcome.findings)
    assert "drydocs_api/corpus_status.py" in rendered
    assert "BEFORE taking the importers" in rendered


def test_findings_are_grouped_by_target_because_that_is_the_consumers_question() -> None:
    in_range = {"drydocs_api/app.py", "drydocs_api/intake.py"}
    sources = dict.fromkeys(in_range, "from drydocs_core import repo_paths\n")
    outcome = import_closure_outcome(
        import_edges(in_range, _TRACKED, _reader(sources)), in_range_count=2
    )
    target_lines = [ln for ln in outcome.findings if "OUT-OF-RANGE" in ln]
    assert len(target_lines) == 1, "one line per MODULE, not one per importing file"
    assert "2 in-range importer(s)" in target_lines[0]


def test_the_closure_check_is_declared_advisory_and_is_the_only_one() -> None:
    """The declaration half. If another check is ever added here, that is a decision
    to stop gating on it, and it should be hard to make by accident."""
    assert ADVISORY_CHECKS == frozenset({"range import closure"})


def test_an_advisory_finding_reports_without_blocking_certification() -> None:
    """The WIRING half, asserted on BEHAVIOUR rather than on the CLI's source text.

    The first draft of this grepped scripts/port_preflight.py for the split
    expression and was caught by test_source_scan's raw-read guard - correctly, and
    the behavioural version is the better test anyway: it would survive the line
    being rewritten and would fail if the split were removed, which a substring
    match has backwards.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "port_preflight_cli", REPO_ROOT / "scripts" / "port_preflight.py"
    )
    assert spec and spec.loader
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)

    advisory_finding = CheckResult.failed("range import closure", "    OUT-OF-RANGE a/b.py <- 1")
    blocking_pass = CheckResult.ok("tree clean", "nothing staged or modified")

    def fake_run_checks(base: str, *, skip_tests: bool = False, will_tag: bool = False):
        return [blocking_pass, advisory_finding]

    cli.run_checks = fake_run_checks
    sys.argv = ["port_preflight.py", "--base", "deadbee"]
    assert cli.main() == 0, "an advisory FINDINGS must not block certification"

    # ...and the probe still told the truth about what it found (ADR 0021): the
    # outcome is findings, not a pass dressed up as one to get past the gate.
    assert not advisory_finding.passed
    assert advisory_finding.verdict == "FAIL"

    # the NEGATIVE control: the same finding on a NON-advisory name does block.
    blocking_finding = CheckResult.failed("tree clean", "one modified file")

    def fake_run_checks_blocking(base: str, *, skip_tests: bool = False, will_tag: bool = False):
        return [blocking_finding]

    cli.run_checks = fake_run_checks_blocking
    assert cli.main() == 1, "a non-advisory finding must still refuse to certify"
