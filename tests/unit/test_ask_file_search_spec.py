"""The Ask report's spec must actually FILTER, and must not over-promise (O62).

THE EVIDENCE THIS EXISTS FOR is on the item. On 2026-08-21 a live Ask session
answered a file-name question correctly — and did it by routing to
``docs.documents.v1``, whose Cypher applies NO filter: it lists every
``:Document`` and the answer model picked the match out of 27 rows by title
similarity. Correct that day, degrading as the corpus grows, and — the sharper
problem — a full listing CANNOT render "not found", so O62's honest-absence
clause would have been unimplementable on top of it.

So the property worth guarding is not "the spec returns the right rows" (no
graph here, and the desktop's graph holds zero ``:DataAsset`` nodes anyway). It
is that the spec TAKES A TERM AND USES IT. A spec that accepted a term and
ignored it would pass every other check in the suite while reproducing exactly
the defect this item was written to fix.

WHAT IS DELIBERATELY NOT ASSERTED: that a repo leg exists. No ``:CodeRepo``
label is declared, the spec does not ask for one, and the surface says "not
modelled" rather than "not found" — a distinction this guard pins, because
collapsing the two would tell a reader a load might fix it.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi", reason="fastapi is an optional dep (the api group)")

from drydocs_api.query_specs import QUERY_SPECS  # noqa: E402

SPEC_ID = "ask.file-search.v1"


def _spec():
    assert SPEC_ID in QUERY_SPECS, f"{SPEC_ID} is not registered"
    return QUERY_SPECS[SPEC_ID]


def test_the_spec_accepts_a_required_search_term() -> None:
    """The prerequisite the item's own observation established."""
    params = {p.name: p for p in _spec().params}
    assert "term" in params, (
        "the Ask report's spec takes no search term — which is the defect O62 exists to "
        "fix: an unfiltered listing narrowed by the answer model cannot say 'not found'"
    )
    assert params["term"].required, "the term must be required; an optional filter is no filter"


def test_the_cypher_actually_uses_the_term() -> None:
    """A spec that accepts a term and ignores it is the same defect wearing a
    parameter. Assert the filter is applied, not merely declared."""
    cypher = _spec().cypher
    assert "$term" in cypher, f"{SPEC_ID} declares a term parameter its Cypher never reads"
    assert "CONTAINS" in cypher.upper(), (
        "the term is named but not used as a filter — the point is that the SERVER narrows "
        "the answer, not the model reading it"
    )


def test_the_filter_is_case_insensitive_on_both_sides() -> None:
    """A support engineer types a file name the way they remember it, not the way
    the graph stored it. Lower-casing only one side is the bug that makes a real
    match report 'not found' — the worst possible answer from this surface."""
    cypher = _spec().cypher
    assert cypher.count("toLower(") >= 2, (
        "only one side of the comparison is lower-cased, so a case difference reports a "
        "false 'not found'"
    )


def test_it_returns_the_legs_the_report_renders() -> None:
    """The report names an application, a process, a folder and a dev team; each
    has to be a column or the surface renders a permanent 'not found'."""
    columns = {c.name for c in _spec().columns}
    for needed in ("asset", "activity", "folder", "application", "dev_team"):
        assert needed in columns, f"{SPEC_ID} does not return '{needed}', which the report renders"


def test_it_does_not_claim_a_repo_leg() -> None:
    """No :CodeRepo label is declared, so the spec must not pretend otherwise.

    The surface says "not modelled" for this leg precisely because no load would
    supply it; a spec that asked for a repo would turn that honest statement into
    a misleading "not found".
    """
    spec = _spec()
    assert "CodeRepo" not in spec.cypher
    assert not any("repo" in c.name.lower() for c in spec.columns)


def test_it_is_a_read_and_carries_its_classification() -> None:
    cypher_upper = _spec().cypher.upper()
    for write_word in ("CREATE", "MERGE", "DELETE", "SET "):
        assert write_word not in cypher_upper, f"{SPEC_ID} is a READ spec and names {write_word}"
    # Rows carry application ids and team names; team rosters are confidential
    # material (J23) — the same call ownership.teams makes.
    assert _spec().classification == "internal"
