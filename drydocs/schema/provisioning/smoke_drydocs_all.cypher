// =============================================================================
// provisioning/smoke_drydocs_all.cypher  —  G1 acceptance smoke (read-only)
//
//   cypher-shell -d drydocs_all -f smoke_drydocs_all.cypher
//
// Reads BOTH constituents through the composite and writes NEITHER. On a freshly
// provisioned (empty) topology this returns 0 / 0 — success is that the federated
// query RUNS AT ALL: both aliases resolve and no write occurs. While `drydocs` is
// mid-rebuild a constituent may be temporarily absent; treat that as "target not
// currently present", not a failure (ADR 0002 rollout state).
// =============================================================================

CALL { USE drydocs_all.drydocs         MATCH (n) RETURN count(n) AS c }
WITH c AS drydocs_nodes
CALL { USE drydocs_all.drydocs_context MATCH (n) RETURN count(n) AS c }
RETURN drydocs_nodes, c AS drydocs_context_nodes;
