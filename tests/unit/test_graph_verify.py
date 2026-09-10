"""Unit tests for graph_verify (drydocs/review/graph_verify.py).

The loader + evaluator are pure/offline, so these run with no Neo4j. The graph
runner is exercised with a tiny fake that returns canned rows.
"""

from __future__ import annotations

from typing import Any

import pytest

from drydocs.review.graph_verify import (
    DEFAULT_GRAPH_TESTS_DIR,
    Assertion,
    GraphVerifyError,
    Suite,
    evaluate,
    exit_code,
    load_suite,
    load_suites,
    run_case,
    run_suite,
    suite_verdict,
    unknown_targets,
)
from drydocs.review.review_labels import ReviewLabels


# ---- evaluator (pure) -----------------------------------------------------
@pytest.mark.parametrize(
    "assertion,rows,expected,ok",
    [
        (Assertion.EMPTY, [], None, True),
        (Assertion.EMPTY, [{"x": 1}], None, False),
        (Assertion.NONEMPTY, [{"x": 1}], None, True),
        (Assertion.NONEMPTY, [], None, False),
        (Assertion.EQUALS, [{"n": 3}], {"n": 3}, True),  # dict expected -> wrapped
        (Assertion.EQUALS, [{"n": 3}], [{"n": 3}], True),  # list expected
        (Assertion.EQUALS, [{"n": 2}], {"n": 3}, False),
        (Assertion.EQUALS, [], None, True),  # both empty
    ],
)
def test_evaluate(assertion: Assertion, rows: list, expected: Any, ok: bool) -> None:
    passed, detail = evaluate(assertion, rows, expected)
    assert passed is ok
    assert (detail == "") is ok


# ---- loader (pure) --------------------------------------------------------
def _write(tmp_path, text: str):
    p = tmp_path / "suite.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_load_suite_parses_cases(tmp_path) -> None:
    p = _write(
        tmp_path,
        """
        suite: demo
        description: a demo
        targets: [ControlMFolder]
        cases:
          - id: TC-01
            cypher: "MATCH (f:ControlMFolder) RETURN f"
            assert: nonempty
          - id: TC-02
            cypher: "RETURN 1 AS n"
            assert: equals
            expected: [{n: 1}]
        """,
    )
    suite = load_suite(p)
    assert suite.name == "demo"
    assert suite.targets == ("ControlMFolder",)
    assert [c.id for c in suite.cases] == ["TC-01", "TC-02"]
    assert suite.cases[1].assertion is Assertion.EQUALS


@pytest.mark.parametrize(
    "body",
    [
        "cases: []",  # empty cases
        "cases:\n  - cypher: x\n    assert: empty",  # missing id
        "cases:\n  - id: TC-1\n    assert: empty",  # missing cypher
        "cases:\n  - id: TC-1\n    cypher: x\n    assert: bogus",  # bad assertion
        "cases:\n  - id: TC-1\n    cypher: x\n    assert: equals",  # equals w/o expected
    ],
)
def test_load_suite_rejects_malformed(tmp_path, body: str) -> None:
    with pytest.raises(GraphVerifyError):
        load_suite(_write(tmp_path, body))


# ---- runner (fake graph) --------------------------------------------------
class _FakeGraph:
    """Returns canned rows keyed by a substring of the cypher."""

    def __init__(self, responses: dict[str, list[dict]]) -> None:
        self._responses = responses

    def run(self, cypher: str, params: dict | None = None) -> list[dict]:
        for needle, rows in self._responses.items():
            if needle in cypher:
                return rows
        return []


def test_run_suite_all_pass_exit_zero() -> None:
    """REV2 rewrote the runner's return: `_mini_suite` declares no anchor, so the
    case results are reached through `.results` and the verdict is NOT RUN. The
    pass/fail behaviour of the CASES is what this test still pins - the
    anchored equivalents live in the REV2 block below."""
    suite = _mini_suite()
    graph = _FakeGraph({"ControlMFolder": [{"f": 1}], "orphan": []})  # folder exists, no orphans
    results = [run_case(graph, c) for c in suite.cases]
    assert exit_code(results) == 0
    assert all(r.passed for r in results)


def test_run_suite_failure_exit_one() -> None:
    suite = _mini_suite()
    graph = _FakeGraph({"ControlMFolder": [], "orphan": [{"orphan": "J1"}]})  # both fail
    results = [run_case(graph, c) for c in suite.cases]
    assert exit_code(results) == 1
    assert not any(r.passed for r in results)


def _mini_suite() -> Suite:
    from drydocs.review.graph_verify import Case

    return Suite(
        name="mini",
        cases=(
            Case(
                id="TC-a", cypher="MATCH (f:ControlMFolder) RETURN f", assertion=Assertion.NONEMPTY
            ),
            Case(id="TC-b", cypher="RETURN orphan", assertion=Assertion.EMPTY),
        ),
    )


# ---- committed example suite + backbone integration --------------------------
def test_committed_bmc_docs_suite_loads() -> None:
    suites = load_suites(DEFAULT_GRAPH_TESTS_DIR)
    names = {s.name for s in suites}
    assert "bmc-docs-smoke" in names


def test_suite_targets_are_known_to_the_backbone() -> None:
    """The committed suite's targets must all be declared in the review backbone."""
    suite = next(s for s in load_suites(DEFAULT_GRAPH_TESTS_DIR) if s.name == "bmc-docs-smoke")
    backbone = ReviewLabels.load()
    assert unknown_targets(suite, backbone) == []


# ---- REV2: the anchor — a suite cannot certify an empty graph ---------------
#
# The defect: most cases in graph-tests/ assert `empty` ("no orphan jobs", "no
# folder without attribution"). On an unloaded graph every one of them passes,
# because zero rows is what they want to see. The 2026-09-08 review measured 28
# of 30 negative assertions with nothing establishing the graph could have
# produced a row at all — so the runner reported PASS over a database that had
# never been loaded, which is the exact shape ADR 0021 names.


def _anchored_suite(min_count: int = 1) -> Suite:
    from drydocs.review.graph_verify import Anchor, Case

    return Suite(
        name="anchored",
        anchor=Anchor(
            cypher=f"MATCH (n:ControlMFolder) RETURN n LIMIT {min_count}",
            min_rows=min_count,
            label="ControlMFolder",
        ),
        cases=(
            Case(
                id="TC-01",
                cypher="MATCH (j:Job) WHERE j.orphan RETURN j",
                assertion=Assertion.EMPTY,
            ),
        ),
    )


def test_an_empty_graph_is_not_run_rather_than_passing() -> None:
    """The item in one test. The case below asserts `empty`; on an empty graph
    it is satisfied, and before REV2 that was reported as a pass."""
    graph = _FakeGraph({})  # nothing matches: every query returns []
    result = run_suite(graph, _anchored_suite())
    assert result.outcome.is_not_checked
    assert "did not run" in result.outcome.reason
    assert "ControlMFolder" in result.outcome.reason
    assert result.results == (), "the cases must not run once the anchor has failed"
    assert exit_code(result) == 2


def test_the_same_suite_passes_once_the_anchor_finds_data() -> None:
    """The control: the mechanism must not turn a real pass into a NOT RUN."""
    graph = _FakeGraph({"ControlMFolder": [{"n": 1}], "orphan": []})
    result = run_suite(graph, _anchored_suite())
    assert result.outcome.is_clean
    assert len(result.results) == 1 and result.results[0].passed
    assert exit_code(result) == 0


def test_a_real_violation_is_findings_not_not_run() -> None:
    """Three states, three answers: the anchor holds AND a case fails."""
    graph = _FakeGraph({"ControlMFolder": [{"n": 1}], "orphan": [{"j": "J1"}]})
    result = run_suite(graph, _anchored_suite())
    assert not result.outcome.is_clean
    assert not result.outcome.is_not_checked
    assert result.outcome.count == 1
    assert "TC-01" in result.outcome.findings[0]
    assert exit_code(result) == 1


def test_a_suite_with_no_anchor_is_not_run() -> None:
    """Default-deny. The mechanism is worth nothing if a suite can opt out by
    omission, which is exactly how the four unanchored suites came to be."""
    result = run_suite(_FakeGraph({"ControlMFolder": [{"n": 1}]}), _mini_suite())
    assert result.outcome.is_not_checked
    assert "declares no anchor" in result.outcome.reason
    assert exit_code(result) == 2


def test_an_anchor_below_its_minimum_does_not_run_the_suite() -> None:
    """A `min_count` above 1 is for a suite whose invariants need a population,
    not merely one node."""
    graph = _FakeGraph({"ControlMFolder": [{"n": 1}], "orphan": []})
    result = run_suite(graph, _anchored_suite(min_count=5))
    assert result.outcome.is_not_checked
    assert "1 of the 5" in result.outcome.reason


def test_not_run_gets_its_own_exit_code() -> None:
    """0/1/2, not 0/1. Sharing 0 is the bug; sharing 1 would tell an operator the
    invariants were violated when nothing was checked (the J78 distinction)."""
    codes = {
        exit_code(run_suite(_FakeGraph({}), _anchored_suite())),
        exit_code(
            run_suite(_FakeGraph({"ControlMFolder": [{"n": 1}], "orphan": []}), _anchored_suite())
        ),
        exit_code(
            run_suite(
                _FakeGraph({"ControlMFolder": [{"n": 1}], "orphan": [{"j": "J1"}]}),
                _anchored_suite(),
            )
        ),
    }
    assert codes == {0, 1, 2}


def test_the_verdict_cannot_be_read_as_a_boolean() -> None:
    """ADR 0021 D1 — `if run_suite(...).outcome:` must not be writable, because
    it would read NOT RUN as either clean or failed and both are wrong."""
    outcome = suite_verdict(_FakeGraph({}), _anchored_suite())
    with pytest.raises(TypeError, match="three states"):
        bool(outcome)


# ---- the anchor declaration itself -----------------------------------------


@pytest.mark.parametrize(
    "block, needle",
    [
        ("anchor: {}", "EXACTLY ONE"),
        ("anchor:\n  label: A\n  cypher: MATCH (n) RETURN n", "EXACTLY ONE"),
        ("anchor:\n  label: A\n  min_count: 0", "anchor of zero"),
        ("anchor:\n  label: A\n  min_count: -1", "anchor of zero"),
        ("anchor:\n  label: A\n  min_count: true", "anchor of zero"),
        ("anchor:\n  label: 'A B'", "not a plain label name"),
        ("anchor: [1, 2]", "must be a mapping"),
    ],
)
def test_a_malformed_anchor_is_refused_at_load(tmp_path, block: str, needle: str) -> None:
    """An anchor that asserts nothing is worse than none: it looks like a
    positive control while being satisfied by an empty graph."""
    f = tmp_path / "s.yaml"
    f.write_text(
        f"suite: probe\n{block}\ncases:\n  - id: TC-01\n    cypher: MATCH (n) RETURN n\n"
        "    assert: empty\n",
        encoding="utf-8",
    )
    with pytest.raises(GraphVerifyError, match=needle):
        load_suite(f)


def test_the_cypher_form_is_accepted_for_what_a_label_count_cannot_say(tmp_path) -> None:
    f = tmp_path / "s.yaml"
    f.write_text(
        "suite: probe\n"
        "anchor:\n"
        "  cypher: MATCH (:A)-[r:OWNS]->(:B) RETURN r\n"
        "  min_rows: 3\n"
        "cases:\n  - id: TC-01\n    cypher: MATCH (n) RETURN n\n    assert: empty\n",
        encoding="utf-8",
    )
    suite = load_suite(f)
    assert suite.anchor.min_rows == 3 and suite.anchor.label is None
    assert "OWNS" in suite.anchor.cypher


def test_every_committed_suite_declares_an_anchor() -> None:
    """Acceptance (c). Four suites were entirely `empty` assertions with no
    positive control at all; all six now declare one, so none of them can
    certify an unloaded graph."""
    suites = load_suites()
    assert suites, "no committed suites were found - this guard would be vacuous"
    unanchored = [s.name for s in suites if s.anchor is None]
    assert not unanchored, f"suites with no positive control: {unanchored}"


def test_every_committed_suite_is_not_run_against_an_empty_graph() -> None:
    """The end-to-end version of the item, over the REAL committed suites: an
    empty database must produce six NOT RUNs and zero passes.

    MEASURED the other way on the laptop, 2026-09-10, by driving the pre-REV2
    runner over these same six suites against an empty graph:

        bmc-docs-lexical                5 cases   PASS (exit 0)
        bmc-docs-smoke                  3 cases   fail
        business-application-identity   5 cases   PASS (exit 0)
        folder-attribution-coverage    12 cases   PASS (exit 0)
        provenance-diet                 2 cases   PASS (exit 0)
        tom-required-contacts           3 cases   fail

    FOUR OF SIX certified an empty database, over 24 of the 30 cases - which is
    the item's title, confirmed rather than repeated. The two that failed did so
    only because they happened to carry a `nonempty` case; neither had DECLARED
    it as a positive control, so neither was protected on purpose.
    """
    graph = _FakeGraph({})
    verdicts = [run_suite(graph, s).outcome for s in load_suites()]
    assert verdicts, "no suites were run - this guard would be vacuous"
    assert all(v.is_not_checked for v in verdicts)
    assert not any(v.is_clean for v in verdicts)
