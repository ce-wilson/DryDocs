// =============================================================================
// provisioning/01_databases.cypher  —  G1 (ADR 0002 D1)
//
// Run against the **system** database on a Neo4j ENTERPRISE DBMS (multi-database +
// composite databases are Enterprise-only). Idempotent (IF NOT EXISTS).
//
//   cypher-shell -d system -f 01_databases.cypher
//
// Creates the ground-truth DB, the isolated uncertain-context DB, and the read-only
// composite that federates both for support queries.
// =============================================================================

// Ground truth — structured KG (main load + drydocs-lineage). Trust: VERBATIM/GROUNDED.
CREATE DATABASE drydocs IF NOT EXISTS;

// Isolated uncertain context (drydocs-deepdoc, on-demand). Trust: SYNTHESIZED/unverified.
// Its own transaction domain: a transaction cannot span databases, so uncertain data
// here can NEVER be written into `drydocs` by accident (the trust axis = the DB boundary).
CREATE DATABASE drydocs_context IF NOT EXISTS;

// Composite — stores no data of its own; aliases the two constituents. The platform
// enforces read-from-many / write-to-one, so support queries read both while writes
// still land in exactly one constituent (no cross-DB writes).
CREATE COMPOSITE DATABASE drydocs_all IF NOT EXISTS;
CREATE ALIAS drydocs_all.drydocs         IF NOT EXISTS FOR DATABASE drydocs;
CREATE ALIAS drydocs_all.drydocs_context IF NOT EXISTS FOR DATABASE drydocs_context;

// Verify (optional):
//   SHOW DATABASES YIELD name, type, currentStatus WHERE name STARTS WITH 'drydocs';
