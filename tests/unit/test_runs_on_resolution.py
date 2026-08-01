"""Unit tests for the derived RUNS_ON resolution pass (P3).

Static + fake-client only — no Neo4j. The live behavior (edges actually
written against the sample corpus) is exercised by the ingest-controlm
smoke run; these tests pin the coverage contract: every job is exactly one
of null / group-matched / host-matched / unmatched, counts are stamped on
the pass's :JobRun, and the resolution script runs between the run-open
and the census.
"""

from __future__ import annotations

from drydocs.loaders.runs_on_resolution import (
    CYPHER_PATH,
    RunsOnCoverage,
    RunsOnResolutionPass,
)


def test_coverage_reconciles_partitions_the_job_population() -> None:
    ok = RunsOnCoverage(
        total_jobs=17,
        null_node_id=0,
        matched_host_group=9,
        matched_agent_host=7,
        unmatched=1,
    )
    assert ok.reconciles()
    assert ok.as_dict()["reconciles"] is True

    drifted = RunsOnCoverage(
        total_jobs=17,
        null_node_id=0,
        matched_host_group=9,
        matched_agent_host=7,
        unmatched=2,
    )
    assert not drifted.reconciles()
    assert drifted.as_dict()["reconciles"] is False


def test_coverage_dict_reports_the_p4_census_fields() -> None:
    d = RunsOnCoverage().as_dict()
    # both_match (P4 collision census, expected zero) and the multi-DC
    # ambiguity count must always be REPORTED — never silent.
    assert "both_match" in d
    assert "multi_dc_group_jobs" in d
    assert "unmatched" in d
    assert "null_node_id" in d


class FakeClient:
    """Records calls; answers the census queries with a fixed population."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []  # (kind, text)

    def run(self, cypher, params=None, **kwargs):
        self.calls.append(("run", cypher))
        if "AS total_jobs" in cypher:
            return [
                {
                    "total_jobs": 17,
                    "null_node_id": 0,
                    "matched_host_group": 9,
                    "matched_agent_host": 7,
                    "unmatched": 1,
                    "both_match": 0,
                }
            ]
        if "multi_dc_group_jobs" in cypher:
            return [{"multi_dc_group_jobs": 0}]
        return []

    def run_script(self, script, params=None):
        self.calls.append(("run_script", script))


def test_pass_runs_script_then_censuses_then_stamps() -> None:
    client = FakeClient()
    coverage = RunsOnResolutionPass(client).run()

    assert coverage.total_jobs == 17
    assert coverage.matched_host_group == 9
    assert coverage.matched_agent_host == 7
    assert coverage.unmatched == 1
    assert coverage.reconciles()

    kinds = [k for k, _ in client.calls]
    # open run -> resolution script -> census x2 -> stamp
    assert kinds[0] == "run" and "JobRun" in client.calls[0][1]
    assert kinds[1] == "run_script"
    assert client.calls[1][1] == CYPHER_PATH.read_text(encoding="utf-8")
    stamp = client.calls[-1][1]
    assert "run.unmatched" in stamp and "edges_written" in stamp
