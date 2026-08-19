"""The derived ExecutionHost -> Server identity pass (Z3; gate
server-location-ontology §C1, SIGNED OFF 12/12, 2026-08-19).

Joins Control-M's view of a host (:ExecutionHost, keyed on nodeid — often a
load-balancer alias) to the inventory spine (:Server, from
:class:`~drydocs.loaders.server_inventory.ServerInventoryLoader`) under the
signed match tiers, K2-style — declared tiers, recorded evidence, nothing
silent:

* **T1 exact** — ``nodeid == server name`` case-normalized →
  ``RESOLVES_TO_SERVER {match_tier: 'exact'}``;
* **T2 normalized** — the deterministic short-name/FQDN rule (strip the DNS
  suffix, nothing fuzzier), applied ONLY when exactly one candidate carries
  the short name — a collision is counted ``ambiguous_short_name`` and stays
  unmatched, never picked;
* **T3 dns-resolved** — NOT BUILT here: the Z4 nslookup collector feeds the
  same edge + evidence shape from its canned-transcript evidence file;
* else **UNMATCHED** — counted, never guessed; no edge.

An EDGE, never a merge (§A1): a tiered match can be wrong, and an edge with
``match_tier + match_evidence + resolved_at`` is reversible and auditable
where a MERGE is neither.

Derived pass in the WAS_INFORMED_BY sense (the runs_on_resolution precedent):
both inputs are already in the graph, so it runs only AFTER the hosts pass
and the server-inventory pass, MATCHes endpoints, and MERGEs only edges.
Coverage follows the same precedent: a dataclass with a ``reconciles()``
invariant, counts stamped onto the pass's own :JobRun, and the CLI prints
the dict — reported, never silent.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

LOGGER = logging.getLogger("drydocs.loaders.server_resolution")

CYPHER_PATH = Path(__file__).resolve().parent / "cypher" / "server_resolution.cypher"

_COVERAGE_QUERY = """
MATCH (h:ExecutionHost)
WHERE NOT h:SchemaMeta
WITH h, (h.nodeid IS NULL OR h.nodeid = '') AS is_null
OPTIONAL MATCH (h)-[r:RESOLVES_TO_SERVER]->()
WITH h, is_null, collect(r.match_tier) AS tiers
RETURN count(h)                                                          AS total_hosts,
       sum(CASE WHEN is_null THEN 1 ELSE 0 END)                          AS null_nodeid,
       sum(CASE WHEN 'exact' IN tiers THEN 1 ELSE 0 END)                 AS matched_exact,
       sum(CASE WHEN 'normalized' IN tiers THEN 1 ELSE 0 END)            AS matched_normalized,
       sum(CASE WHEN 'dns-resolved' IN tiers THEN 1 ELSE 0 END)          AS matched_dns_resolved,
       sum(CASE WHEN NOT is_null AND size(tiers) = 0 THEN 1 ELSE 0 END)  AS unmatched
"""

_AMBIGUOUS_QUERY = """
MATCH (h:ExecutionHost)
WHERE h.nodeid IS NOT NULL AND h.nodeid <> '' AND NOT h:SchemaMeta
  AND NOT EXISTS { MATCH (h)-[:RESOLVES_TO_SERVER]->() }
WITH h, split(toLower(h.nodeid), '.')[0] AS short
MATCH (s:Server)
WHERE NOT s:SchemaMeta AND split(toLower(s.name), '.')[0] = short
WITH h, count(s) AS candidates
WHERE candidates > 1
RETURN count(h) AS ambiguous_short_name
"""


@dataclass
class ServerResolutionCoverage:
    """Per-run resolution census (§C1: unmatched is visible, never dropped)."""

    total_hosts: int = 0
    null_nodeid: int = 0
    matched_exact: int = 0
    matched_normalized: int = 0
    matched_dns_resolved: int = 0
    unmatched: int = 0
    #: T2's ambiguity guard: hosts whose short name matched >1 Server — left
    #: unmatched by design (a collision is never picked); subset of unmatched.
    ambiguous_short_name: int = 0
    notes: list[str] = field(default_factory=list)

    def reconciles(self) -> bool:
        """Every host is exactly one of: null, matched (any tier), unmatched.

        A host carries at most one tier today (T1 wins before T2 runs; T3 may
        later add multi-server LB fan-out — the reconcile then counts hosts,
        not edges, which this query already does).
        """
        matched = self.matched_exact + self.matched_normalized + self.matched_dns_resolved
        return (self.null_nodeid + matched + self.unmatched) == self.total_hosts

    def as_dict(self) -> dict:
        return {
            "total_hosts": self.total_hosts,
            "null_nodeid": self.null_nodeid,
            "matched_exact": self.matched_exact,
            "matched_normalized": self.matched_normalized,
            "matched_dns_resolved": self.matched_dns_resolved,
            "unmatched": self.unmatched,
            "ambiguous_short_name": self.ambiguous_short_name,
            "reconciles": self.reconciles(),
        }


class ServerResolutionPass:
    """Execute the derived pass and stamp its coverage onto a :JobRun."""

    name = "server_resolution.v1"

    def __init__(self, client) -> None:
        self.client = client
        self.run_id = str(uuid.uuid4())
        self.resolved_at = datetime.now(UTC).replace(microsecond=0, tzinfo=None).isoformat()

    def run(self) -> ServerResolutionCoverage:
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
                "server_resolution: %d host(s) UNMATCHED (nodeid resolves to no "
                "inventory Server at T1/T2) — coverage, not an error; T3 (Z4 "
                "nslookup) may close some",
                coverage.unmatched,
            )
        if coverage.ambiguous_short_name:
            LOGGER.warning(
                "server_resolution: %d host(s) hit the T2 ambiguity guard "
                "(short name matches >1 Server) — left unmatched by design, "
                "never picked",
                coverage.ambiguous_short_name,
            )
        if not coverage.reconciles():
            LOGGER.warning(
                "server_resolution: coverage does not reconcile: %s",
                coverage.as_dict(),
            )
        return coverage

    def _census(self) -> ServerResolutionCoverage:
        rows = self.client.run(_COVERAGE_QUERY)
        coverage = ServerResolutionCoverage(**{k: v for k, v in (rows[0] if rows else {}).items()})
        ambiguous = self.client.run(_AMBIGUOUS_QUERY)
        if ambiguous:
            coverage.ambiguous_short_name = ambiguous[0].get("ambiguous_short_name", 0)
        return coverage

    def _stamp(self, coverage: ServerResolutionCoverage) -> None:
        self.client.run(
            """
            MATCH (run:JobRun {run_id: $run_id})
            OPTIONAL MATCH (:ExecutionHost)-[r:RESOLVES_TO_SERVER]->()
              WHERE r.last_run_id = $run_id
            WITH run, count(r) AS edges_written
            SET run.total_hosts          = $total_hosts,
                run.null_nodeid          = $null_nodeid,
                run.matched_exact        = $matched_exact,
                run.matched_normalized   = $matched_normalized,
                run.matched_dns_resolved = $matched_dns_resolved,
                run.unmatched            = $unmatched,
                run.ambiguous_short_name = $ambiguous_short_name,
                run.edges_written        = edges_written,
                run.status               = 'OK',
                run.ended_at             = datetime($resolved_at)
            """,
            run_id=self.run_id,
            resolved_at=self.resolved_at,
            **{k: v for k, v in coverage.as_dict().items() if k != "reconciles"},
        )
