// =============================================================================
// provisioning/smoke_drydocs_all.cypher  —  G1 acceptance smoke (read-only)
//
//   cypher-shell -d ddall -f smoke_drydocs_all.cypher
//
// Reads ALL THREE constituents through the composite and writes NONE. On a freshly
// provisioned (empty) topology this returns 0 / 0 / 0 — success is that the federated
// query RUNS AT ALL: both aliases resolve and no write occurs. While `drydocs` is
// mid-rebuild a constituent may be temporarily absent; treat that as "target not
// currently present", not a failure (ADR 0002 rollout state).
// =============================================================================

CALL { USE ddall.drydocs   MATCH (n) RETURN count(n) AS c }
WITH c AS drydocs_nodes
CALL { USE ddall.ddlineage MATCH (n) RETURN count(n) AS c }
WITH drydocs_nodes, c AS ddlineage_nodes
CALL { USE ddall.ddcontext MATCH (n) RETURN count(n) AS c }
RETURN drydocs_nodes, ddlineage_nodes, c AS ddcontext_nodes;
