"""The derived RUNS_ON resolution pass (gate controlm-hosts-topology, P3).

Resolves each :ControlMJob's polymorphic ``node_id`` against the host
topology loaded by :class:`~drydocs.loaders.controlm_hosts.ControlMHostsLoader`:

* ``node_id`` matches a ``ControlMHostGroup.name`` → ``RUNS_ON {role:
  host_group}`` (2-hop; Control-M load-balances across CONTAINS_HOST members);
* else it matches an ``ExecutionHost.nodeid`` → ``RUNS_ON {role: agent_host}``
  (1-hop hard-coded);
* else UNMATCHED — counted, never guessed; NULL ``node_id`` → no edge.

GROUP MATCH WINS (the signed §B precedence, mirroring Control-M's own
resolution). This is a derived pass in the WAS_INFORMED_BY sense: both
inputs are already in the graph, so it runs only AFTER the jobs pass and
the hosts pass, MATCHes endpoints, and MERGEs only edges.

Coverage follows the seal_attribution precedent: a dataclass with a
``reconciles()`` invariant, counts stamped onto the pass's own :JobRun,
and the CLI prints the dict — reported, never silent (the
STG_PARSE_QUALITY house rule). The P4 both-match collision census
(expected zero) and the multi-DC group ambiguity count ride along.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

LOGGER = logging.getLogger("drydocs.loaders.runs_on_resolution")

CYPHER_PATH = Path(__file__).resolve().parent / "cypher" / "runs_on_resolution.cypher"

_COVERAGE_QUERY = """
MATCH (j:ControlMJob)
WHERE NOT j:SchemaMeta
WITH j, (j.node_id IS NULL OR j.node_id = '') AS is_null
WITH j, is_null,
     (NOT is_null AND EXISTS { MATCH (g:ControlMHostGroup {name: j.node_id}) WHERE NOT g:SchemaMeta })   AS grp,
     (NOT is_null AND EXISTS { MATCH (h:ExecutionHost   {nodeid: j.node_id}) WHERE NOT h:SchemaMeta })   AS hst
RETURN count(j)                                                        AS total_jobs,
       sum(CASE WHEN is_null THEN 1 ELSE 0 END)                        AS null_node_id,
       sum(CASE WHEN grp THEN 1 ELSE 0 END)                            AS matched_host_group,
       sum(CASE WHEN NOT is_null AND NOT grp AND hst THEN 1 ELSE 0 END) AS matched_agent_host,
       sum(CASE WHEN NOT is_null AND NOT grp AND NOT hst THEN 1 ELSE 0 END) AS unmatched,
       sum(CASE WHEN grp AND hst THEN 1 ELSE 0 END)                    AS both_match
"""

_MULTI_DC_QUERY = """
MATCH (j:ControlMJob)
WHERE j.node_id IS NOT NULL AND j.node_id <> '' AND NOT j:SchemaMeta
MATCH (g:ControlMHostGroup {name: j.node_id})
WHERE NOT g:SchemaMeta
WITH j, count(g) AS gcount
WHERE gcount > 1
RETURN count(j) AS multi_dc_group_jobs
"""


@dataclass
class RunsOnCoverage:
    """Per-run resolution census (gate §B: reported as coverage, never guessed)."""

    total_jobs: int = 0
    null_node_id: int = 0
    matched_host_group: int = 0
    matched_agent_host: int = 0
    unmatched: int = 0
    # P4 census: NODE_ID matches BOTH a GRPNAME and a NODEID — expected zero;
    # such jobs are resolved as host_group (group wins) and counted here.
    both_match: int = 0
    # A group name held in >1 data center — the job edges to each (the DC
    # scoping join is blocked on the DEFINED_ON residuals); surfaced, not picked.
    multi_dc_group_jobs: int = 0
    notes: list[str] = field(default_factory=list)

    def reconciles(self) -> bool:
        """Every job is exactly one of: null, group-matched, host-matched, unmatched."""
        return (
            self.null_node_id
            + self.matched_host_group
            + self.matched_agent_host
            + self.unmatched
        ) == self.total_jobs

    def as_dict(self) -> dict:
        return {
            "total_jobs": self.total_jobs,
            "null_node_id": self.null_node_id,
            "matched_host_group": self.matched_host_group,
            "matched_agent_host": self.matched_agent_host,
            "unmatched": self.unmatched,
            "both_match": self.both_match,
            "multi_dc_group_jobs": self.multi_dc_group_jobs,
            "reconciles": self.reconciles(),
        }


class RunsOnResolutionPass:
    """Execute the derived pass and stamp its coverage onto a :JobRun."""

    name = "runs_on_resolution.v1"

    def __init__(self, client) -> None:
        self.client = client
        self.run_id = str(uuid.uuid4())
        self.resolved_at = (
            datetime.now(UTC).replace(microsecond=0, tzinfo=None).isoformat()
        )

    def run(self) -> RunsOnCoverage:
        params = {
            "run_id": self.run_id,
            "resolved_at": self.resolved_at,
            "loader": self.name,
        }
        self.client.run(
            "MERGE (r:JobRun {run_id: $run_id}) "
            "SET r.kind = 'derive', r.loader = $loader, "
            "    r.started_at = datetime($resolved_at)",
            **params,
        )
        self.client.run_script(CYPHER_PATH.read_text(encoding="utf-8"), params)
        coverage = self._census()
        self._stamp(coverage)
        if coverage.unmatched:
            LOGGER.warning(
                "runs_on_resolution: %d job(s) UNMATCHED (node_id resolves to "
                "neither a GRPNAME nor a NODEID) — coverage, not an error",
                coverage.unmatched,
            )
        if coverage.both_match:
            LOGGER.warning(
                "runs_on_resolution: %d job(s) matched BOTH a group and a host "
                "(P4 census expected zero) — resolved as host_group per the "
                "signed group-wins rule",
                coverage.both_match,
            )
        if not coverage.reconciles():
            LOGGER.warning(
                "runs_on_resolution: coverage does not reconcile: %s",
                coverage.as_dict(),
            )
        return coverage

    def _census(self) -> RunsOnCoverage:
        rows = self.client.run(_COVERAGE_QUERY)
        coverage = RunsOnCoverage(**{k: v for k, v in (rows[0] if rows else {}).items()})
        multi = self.client.run(_MULTI_DC_QUERY)
        if multi:
            coverage.multi_dc_group_jobs = multi[0].get("multi_dc_group_jobs", 0)
        return coverage

    def _stamp(self, coverage: RunsOnCoverage) -> None:
        self.client.run(
            """
            MATCH (run:JobRun {run_id: $run_id})
            OPTIONAL MATCH (:ControlMJob)-[r:RUNS_ON]->()
              WHERE r.last_run_id = $run_id
            WITH run, count(r) AS edges_written
            SET run.total_jobs          = $total_jobs,
                run.null_node_id        = $null_node_id,
                run.matched_host_group  = $matched_host_group,
                run.matched_agent_host  = $matched_agent_host,
                run.unmatched           = $unmatched,
                run.both_match          = $both_match,
                run.multi_dc_group_jobs = $multi_dc_group_jobs,
                run.edges_written       = edges_written,
                run.status              = 'OK',
                run.ended_at            = datetime($resolved_at)
            """,
            run_id=self.run_id,
            resolved_at=self.resolved_at,
            **{
                k: v
                for k, v in coverage.as_dict().items()
                if k != "reconciles"
            },
        )
