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

// NOTE: a lineage database (`ddlineage`) was created here at G1 and RETIRED 2026-08-04
// (ADR 0002 X1 amendment). Nothing ever wrote it — ADR 0002 D1/D2 puts curated lineage
// writes in `drydocs` (asserted structurally by 0002-C §5), and the G30-repointed specs
// read `drydocs`. If lineage ever earns its own database (the ADR's named revisit
// trigger: a :ControlMJob proxy-node spine), recreate it here with its ddall alias —
// the design is the expensive part, the DDL is two lines.

// `ddcontext` RETIRED 2026-08-18 — gate document-content-topology (G32) §A, applied
// at G102. The content topology FOLDS TO ONE database: uncertain content lives in
// `drydocs` under the :Uncertain label, guarded by the three ADR 0011 clause-1
// guards (structural QuerySpec exclusion, the write-boundary allowlist, the live
// audit spec) — the same per-assertion discipline that always governed the manual
// pins. Existing per-machine ddcontext databases are left in place INERT (nothing
// reads or writes them); dropping them is per-machine cleanup, G50-class.

// Schema meta-graph (drydocs bootstrap-schema-graph) — G51, SME direction "2 different
// graphs" 2026-08-02. Exemplar nodes carry REAL labels beside :SchemaMeta, and drydocs'
// NODE KEYs enforce property EXISTENCE the exemplars don't have — so the meta-graph
// needs a database with no opinion about job rows. Its one constraint (schemameta_name)
// lives in schema_graph.cypher, NOT constraints.cypher. Deliberately NOT aliased into
// ddall: it describes the schema, not the estate — a support query federating exemplar
// nodes with real jobs would present labels as data.
CREATE DATABASE ddschema IF NOT EXISTS;

// `ddall` RETIRED 2026-08-18 with its second constituent (G32/G102): a composite
// over one database federates nothing. The G38 federated-read proof retires with
// it — post-fold every read is an ordinary single-database read.

// Verify (optional):
//   SHOW DATABASES YIELD name, type, currentStatus WHERE name STARTS WITH 'drydocs';
