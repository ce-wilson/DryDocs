"""Unit tests for graph_verify (drydocs/graph_verify.py).

The loader + evaluator are pure/offline, so these run with no Neo4j. The graph
runner is exercised with a tiny fake that returns canned rows.
"""

from __future__ import annotations

from typing import Any

import pytest

from drydocs.graph_verify import (
    DEFAULT_GRAPH_TESTS_DIR,
    Assertion,
    GraphVerifyError,
    Suite,
    evaluate,
    exit_code,
    load_suite,
    load_suites,
    run_suite,
    unknown_targets,
)
from drydocs.review_labels import ReviewLabels


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
    suite = _mini_suite()
    graph = _FakeGraph({"ControlMFolder": [{"f": 1}], "orphan": []})  # folder exists, no orphans
    results = run_suite(graph, suite)
    assert exit_code(results) == 0
    assert all(r.passed for r in results)


def test_run_suite_failure_exit_one() -> None:
    suite = _mini_suite()
    graph = _FakeGraph({"ControlMFolder": [], "orphan": [{"orphan": "J1"}]})  # both fail
    results = run_suite(graph, suite)
    assert exit_code(results) == 1
    assert not any(r.passed for r in results)


def _mini_suite() -> Suite:
    from drydocs.graph_verify import Case

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
