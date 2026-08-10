"""J41 — guards for the port opening sequence.

Every assertion here is paired with its NEGATIVE case, because the whole item
exists because of checks that returned a plausible answer for the wrong reason
(J26 promise-vs-assertion). A coverage check that never reports an uncited commit
is indistinguishable from one that has nothing to report.
"""

from __future__ import annotations

import pytest

from drydocs.port_preflight import (
    BASIS_TAGS,
    Commit,
    cited_shas,
    is_ritual,
    next_base_tag,
    relays_missing_basis,
    uncited_commits,
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


def test_a_citation_buried_MID_sha_does_not_count_as_coverage() -> None:
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


# ---- tag naming --------------------------------------------------------------


def test_the_base_tag_takes_the_plain_date_when_free() -> None:
    assert next_base_tag([], "20260809") == "port-base-20260809"


def test_a_second_certification_on_one_day_suffixes_rather_than_collides() -> None:
    """Mirrors the company's own `-20260809b` backup-tag convention."""
    existing = ["port-base-20260809"]
    assert next_base_tag(existing, "20260809") == "port-base-20260809b"
    assert next_base_tag([*existing, "port-base-20260809b"], "20260809") == "port-base-20260809c"
