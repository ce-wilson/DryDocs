"""Read-only corroboration (0002-B §2 step 5) — the reconcile logic and the RUNTIME
half of the no-graph-write gate (NFR-REM-1): write Cypher cannot reach the driver."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from drydocs_remediation.corroborate import (
    GraphWriteAttemptError,
    ReadOnlyGraph,
    reconcile_variables,
)
from drydocs_remediation.formats import TranscriptDefinitionFormat

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "remediation"


class SpyClient:
    """Stands in for drydocs_core.Neo4jClient; records every query that reaches it."""

    def __init__(self) -> None:
        self.queries: list[str] = []

    def run(self, query: str, params: dict[str, Any] | None = None) -> list[Any]:  # noqa: ARG002
        self.queries.append(query)
        return []


def _legacy():
    return TranscriptDefinitionFormat().load(FIXTURES / "synthetic-legacy-transcript.yaml")


def test_reconcile_consistent_source() -> None:
    ds = _legacy()
    extract = {ds.jobs[0].name: list(ds.jobs[0].variables)}
    report = reconcile_variables(ds, extract)
    assert report.consistent is True
    assert report.checked_jobs == 1


def test_reconcile_reports_value_and_presence_mismatches() -> None:
    ds = _legacy()
    rows = [(n, v) for n, v in ds.jobs[0].variables if n != "%%EXT"]
    rows[0] = ("%%DIR_A", "/data/other/")  # value drift
    report = reconcile_variables(ds, {ds.jobs[0].name: rows})
    assert report.consistent is False
    assert any("DIR_A" in m and "!=" in m for m in report.mismatches)
    assert any("EXT: only in the definition" in m for m in report.mismatches)


def test_reconcile_flags_missing_job() -> None:
    report = reconcile_variables(_legacy(), {})
    assert report.consistent is False
    assert report.mismatches == [
        "JOB0001_SAMPLE_DAILY_INDICATOR_TOK_FW: absent from the corroborating source"
    ]


def test_read_queries_pass_through() -> None:
    spy = SpyClient()
    ReadOnlyGraph(spy).fetch("MATCH (j:SyntheticLabel {name: $n}) RETURN j", {"n": "x"})
    assert len(spy.queries) == 1


@pytest.mark.parametrize("clause", ["MERGE", "CREATE", "SET", "DELETE", "REMOVE", "DROP"])
def test_write_cypher_never_reaches_the_driver(clause: str) -> None:
    spy = SpyClient()
    graph = ReadOnlyGraph(spy)
    with pytest.raises(GraphWriteAttemptError):
        graph.fetch(f"MATCH (n) {clause} n.x = 1 RETURN n")
    assert spy.queries == []  # nothing crossed the boundary


def test_wrapper_exposes_no_script_executors() -> None:
    graph = ReadOnlyGraph(SpyClient())
    for name in ("run", "run_script", "execute_file"):
        assert not hasattr(graph, name)
