// =============================================================================
// provisioning/02_proxy_constraints.cypher  —  G1 (ADR 0002 D1, proxy-node keys)
//
// Run in EACH data database — BOTH drydocs AND ddcontext:
//   cypher-shell -d drydocs         -f 02_proxy_constraints.cypher
//   cypher-shell -d ddcontext -f 02_proxy_constraints.cypher
//
// The composite joins the two DBs by BUSINESS KEY (proxy-node pattern) — never by
// internal node id — so both DBs must carry the same uniqueness on the join keys, and
// `ddcontext` records survive every `drydocs` rebuild and re-link automatically.
//
// Identity is the EXISTING canonical business key (ADR 0001: "identity is always a
// business key"); no identity is invented here:
//   * DataAsset   -> assetId  (URN: urn:drydocs:dataasset:{platform}:{namespace}:{name})
//   * ControlMJob -> (folder_id, job_id)  (the canonical key from constraints.cypher)
//
// Idempotent; Neo4j 5.x. (A UNIQUE / NODE KEY constraint creates its own backing range
// index, so the join keys are indexed without separate CREATE INDEX statements.)
// =============================================================================

CREATE CONSTRAINT dataasset_id    IF NOT EXISTS FOR (a:DataAsset)   REQUIRE a.assetId IS UNIQUE;
CREATE CONSTRAINT controlmjob_key IF NOT EXISTS FOR (j:ControlMJob) REQUIRE (j.folder_id, j.job_id) IS NODE KEY;
