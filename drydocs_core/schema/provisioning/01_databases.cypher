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

// PROVISIONED FOR LATER — nothing writes here today (backlog G30 ruling, 2026-07-26).
// Created at G1 as a home for cross-platform lineage, but ADR 0002 D1/D2 (accepted,
// never amended) puts drydocs-lineage's curated writes in `drydocs`, and 0002-C §5
// asserts that structurally. The blocking fact: the curated writer MATCHes
// :ControlMJob nodes the M3 load owns in `drydocs` and deliberately never MERGEs them
// — a transaction cannot span databases, so writing lineage here would silently drop
// every job-endpoint edge. Kept provisioned + composite-aliased so the choice stays
// cheap: it is empty, so moving lineage here later costs a design, not a migration.
CREATE DATABASE ddlineage IF NOT EXISTS;

// Isolated uncertain context (drydocs-deepdoc, on-demand). Trust: SYNTHESIZED/unverified.
// Its own transaction domain: a transaction cannot span databases, so uncertain data
// here can NEVER be written into `drydocs` by accident (the trust axis = the DB boundary).
CREATE DATABASE ddcontext IF NOT EXISTS;

// Schema meta-graph (drydocs bootstrap-schema-graph) — G51, SME direction "2 different
// graphs" 2026-08-02. Exemplar nodes carry REAL labels beside :SchemaMeta, and drydocs'
// NODE KEYs enforce property EXISTENCE the exemplars don't have — so the meta-graph
// needs a database with no opinion about job rows. Its one constraint (schemameta_name)
// lives in schema_graph.cypher, NOT constraints.cypher. Deliberately NOT aliased into
// ddall: it describes the schema, not the estate — a support query federating exemplar
// nodes with real jobs would present labels as data.
CREATE DATABASE ddschema IF NOT EXISTS;

// Composite — stores no data of its own; aliases all three constituents. The platform
// enforces read-from-many / write-to-one, so support queries read all while writes
// still land in exactly one constituent (no cross-DB writes).
CREATE COMPOSITE DATABASE ddall IF NOT EXISTS;
CREATE ALIAS ddall.drydocs    IF NOT EXISTS FOR DATABASE drydocs;
CREATE ALIAS ddall.ddlineage  IF NOT EXISTS FOR DATABASE ddlineage;
CREATE ALIAS ddall.ddcontext  IF NOT EXISTS FOR DATABASE ddcontext;

// Verify (optional):
//   SHOW DATABASES YIELD name, type, currentStatus WHERE name STARTS WITH 'drydocs';
