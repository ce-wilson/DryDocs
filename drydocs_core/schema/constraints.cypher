// =============================================================================
// constraints.cypher  —  M0
//
// Combined constraint + index DDL from v2 §5 and v3 §J. Idempotent; safe to
// re-run.  Neo4j 5.x syntax.
// =============================================================================

// --- Ontology backbone -------------------------------------------------------
CREATE CONSTRAINT ontology_iri        IF NOT EXISTS FOR (n:OntologyTerm)        REQUIRE n.iri IS UNIQUE;

// --- Generic asset / data product -------------------------------------------
CREATE CONSTRAINT asset_id            IF NOT EXISTS FOR (a:Asset)               REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT dataproduct_id      IF NOT EXISTS FOR (p:DataProduct)         REQUIRE p.id IS UNIQUE;

// --- DCAT --------------------------------------------------------------------
CREATE CONSTRAINT dataset_iri         IF NOT EXISTS FOR (d:Dataset)             REQUIRE d.iri IS UNIQUE;
CREATE CONSTRAINT distribution_id     IF NOT EXISTS FOR (x:Distribution)        REQUIRE x.id IS UNIQUE;

// --- Provenance / lineage ----------------------------------------------------
CREATE CONSTRAINT jobrun_id           IF NOT EXISTS FOR (r:JobRun)              REQUIRE r.run_id IS UNIQUE;
CREATE CONSTRAINT lineagerun_id       IF NOT EXISTS FOR (r:LineageRun)          REQUIRE r.run_id IS UNIQUE;

// --- DQV ---------------------------------------------------------------------
CREATE CONSTRAINT measurement_id      IF NOT EXISTS FOR (m:QualityMeasurement)  REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT metric_name         IF NOT EXISTS FOR (m:Metric)              REQUIRE m.name IS UNIQUE;
CREATE CONSTRAINT dimension_name      IF NOT EXISTS FOR (d:Dimension)           REQUIRE d.name IS UNIQUE;

// --- Corporate hierarchy -----------------------------------------------------
CREATE CONSTRAINT company_name        IF NOT EXISTS FOR (c:Company)             REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT business_segment    IF NOT EXISTS FOR (s:BusinessSegment)     REQUIRE s.code IS UNIQUE;
CREATE CONSTRAINT catalog_lob_id      IF NOT EXISTS FOR (l:CatalogLOB)          REQUIRE l.lob_id IS UNIQUE;
CREATE CONSTRAINT product_line_id     IF NOT EXISTS FOR (pl:ProductLine)        REQUIRE pl.product_line_id IS UNIQUE;
CREATE CONSTRAINT product_id          IF NOT EXISTS FOR (p:Product)             REQUIRE p.product_id IS UNIQUE;

// --- Application + ports -----------------------------------------------------
// IDENTITY (gate business-application-identity, 2026-07-27; ADR 0010): the canonical
// node's key is the NEUTRAL app_id. businessapplication_seal is RETAINED, not replaced —
// seal_id is still dual-written as a deprecated alias through phase 3, and its retirement
// is a separate later gate (§G3). The constraint NAME keeping "seal" is deliberate and
// listed at §F1(5) as one of the six legitimate homes for the registry name: it is a
// schema-object name, and it is the most operator-visible one (it prints in
// SHOW CONSTRAINTS and in the text of every uniqueness-violation error).
CREATE CONSTRAINT businessapplication_app_id  IF NOT EXISTS FOR (a:BusinessApplication)         REQUIRE a.app_id IS UNIQUE;
CREATE CONSTRAINT businessapplication_seal    IF NOT EXISTS FOR (a:BusinessApplication)         REQUIRE a.seal_id IS UNIQUE;
// G36 (2026-08-04): the former status/risk_level/name indexes are DROPPED, not just
// no longer created — a declared index reads as a claim the property is a predicate,
// and none of the three ever was (SET clauses and RETURN projections only; the one
// name-bind is the single-node SchemaMeta bootstrap MERGE). Every real bind goes
// through app_id/seal_id, already backed by the UNIQUE constraints above. The two
// genuine non-key predicates — manually_created (post-load count) and
// batch_orchestrator_last_run_id (per-run report) — stay UNindexed on purpose:
// registry cardinality makes a label scan sub-millisecond, and both run offline.
DROP INDEX businessapplication_status IF EXISTS;
DROP INDEX businessapplication_risk   IF EXISTS;
DROP INDEX businessapplication_name   IF EXISTS;

// Port pattern: each Application has exactly one port per KIND — EventProcessing
// and BatchProcessing (the SEAL data ports), plus Technology since the Z3 build
// (gate server-location-ontology §C2, 2026-08-19 — the infrastructure attachment
// surface, minted by the server-inventory loader for apps the export names). Composite uniqueness on (parent_app_id, kind) lets
// us enforce that without modeling the relationship inside the constraint.
//
// TRAP (gate §D1, and the reason the DROP below is not optional): `CREATE CONSTRAINT
// <name> IF NOT EXISTS` matches on the NAME, not the definition. Redefining port_unique
// under its own name would SUCCEED AND DO NOTHING, silently leaving the old
// (parent_seal_id, kind) key live while the loader writes parent_app_id — every Port
// then has a null in the old key, which a NODE KEY would reject on write but which an
// already-created constraint never re-validates. Belt and braces: DROP the old name AND
// create under a new one, so an operator reading SHOW CONSTRAINTS sees the change.
//
// Against a graph loaded BEFORE this change the CREATE fails loudly (a NODE KEY requires
// both properties to exist, and those Ports carry parent_seal_id only). That is the
// intended outcome, not a regression: §C4 ruled wipe-and-rebuild, so the fix is to
// rebuild — a bootstrap that quietly succeeded here would be the silent-double failure.
DROP CONSTRAINT port_unique IF EXISTS;
CREATE CONSTRAINT port_app_key        IF NOT EXISTS FOR (p:Port)                REQUIRE (p.parent_app_id, p.kind) IS NODE KEY;

// --- People / org chart ------------------------------------------------------
CREATE CONSTRAINT area_product_id     IF NOT EXISTS FOR (ap:AreaProduct)        REQUIRE ap.area_product_id IS UNIQUE;
CREATE CONSTRAINT devteam_id          IF NOT EXISTS FOR (d:DevTeam)             REQUIRE d.team_id IS UNIQUE;
CREATE CONSTRAINT employee_id         IF NOT EXISTS FOR (e:Employee)            REQUIRE e.employee_id IS UNIQUE;
CREATE CONSTRAINT sn_group_id         IF NOT EXISTS FOR (g:ServiceNowGroup)     REQUIRE g.group_id IS UNIQUE;
CREATE CONSTRAINT jira_board_id       IF NOT EXISTS FOR (b:JiraBoard)           REQUIRE b.board_id IS UNIQUE;

// Role / Membership keys — LIVE, with a scoped deprecation (C20, 2026-07-28).
// K4 (gate 2026-07-10 §B/§C) deprecated the reified Membership pattern (W3C
// ORG) in the SEAL ATTRIBUTION loaders specifically — qualified attribution
// replaced it there. These keys remain load-bearing for the catalog paths:
// catalog_ontology_supplement.cypher seeds the canonical :Role rows and
// pat_team_roles.cypher MERGEs :Membership on membership_id (PAT team roles).
// AMENDED AT G91 (2026-08-18) — that second clause is now HISTORY. The SME ruled the
// DevTeam leg onto qualified attribution, so catalog_dev_team_has_membership is deprecated
// and pat_team_roles.cypher is marked do-not-run until rewritten. :Membership therefore has
// NO live writer.
// :Role KEEPS its keys and gains a new purpose: the replacement
// catalog_dev_team_attribution_had_role targets Attribution -[:HAD_ROLE]-> :Role, so the
// canonical rows the catalog supplement seeds are still the register that leg resolves
// against. The membership_id key is left in place deliberately rather than dropped in the
// same change — the loader rewrite is the follow-up that decides whether :Membership
// survives at all, and dropping a constraint ahead of its loader is the S3 ordering trap
// run backwards.
// The earlier "kept for old graphs" phrase was void — graphs rebuild from
// bootstrap, they are never migrated (the C13 precedent).
CREATE CONSTRAINT role_name           IF NOT EXISTS FOR (r:Role)                REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT role_id             IF NOT EXISTS FOR (r:Role)                REQUIRE r.role_id IS UNIQUE;
// membership_id DROPPED at G99 (2026-08-18). pat_team_roles.cypher was the last
// writer of :Membership and it now writes the qualified-attribution shape instead;
// the two SEAL references that remain are comments. A uniqueness key on a label
// nothing writes is dead schema, and the estate is truncate-and-reload so there is
// no stored data to protect. Dropped WITH its last writer, never ahead of it — the
// ordering caution above, honoured. :Membership stays REGISTERED in the vocabulary
// because the deprecated entries still cite it as an endpoint; the label is history,
// not a live target.

// K4 (gate 2026-07-10 §B/§C): qualified-attribution replaces Membership/Role in
// the SEAL loaders. These MERGE keys MUST be indexed — without them every
// MERGE (:Attribution {attribution_id}) / (:TOMRole {id}) is a full label scan,
// O(n²) over the growing set (company live-DB: 826s → 29s on seal_applications).
CREATE CONSTRAINT attribution_id      IF NOT EXISTS FOR (m:Attribution)         REQUIRE m.attribution_id IS UNIQUE;
CREATE CONSTRAINT tomrole_id          IF NOT EXISTS FOR (t:TOMRole)             REQUIRE t.id IS UNIQUE;

// --- Control-M / BMC ---------------------------------------------------------
// Node key uses natural identity (folder_id, job_id) without version_serial —
// loaders filter to IS_CURRENT_VERSION='Y' so one canonical node per logical
// entity; version_serial stays as an audit property only.
CREATE CONSTRAINT controlm_server     IF NOT EXISTS FOR (s:ControlMServer)      REQUIRE s.name IS UNIQUE;
// Control-M APPLICATION grouping (folder header row; gate controlm-q1q3-phase1).
// NOT the SEAL business :BusinessApplication — see ADR 0003 naming rules.
CREATE CONSTRAINT controlmapplication_name IF NOT EXISTS FOR (a:ControlMApplication) REQUIRE a.name IS UNIQUE;
// Drop the JobFolder-era constraint name, then create against the renamed
// label (ADR 0003: BMC labels take the ControlM prefix). Both idempotent.
DROP CONSTRAINT folder_id IF EXISTS;
CREATE CONSTRAINT controlmfolder_id   IF NOT EXISTS FOR (f:ControlMFolder)      REQUIRE f.folder_id IS UNIQUE;

// Drop old versioned key (included version_serial in earlier M3 drafts) then
// create the correct natural key. Both statements are idempotent.
DROP CONSTRAINT controlmjob_key IF EXISTS;
CREATE CONSTRAINT controlmjob_key     IF NOT EXISTS FOR (j:ControlMJob)         REQUIRE (j.folder_id, j.job_id) IS NODE KEY;

DROP CONSTRAINT condition_key IF EXISTS;
CREATE CONSTRAINT condition_key       IF NOT EXISTS FOR (c:Condition)           REQUIRE (c.folder_id, c.name) IS NODE KEY;

// The D1 business-key backbone (G31, 2026-08-18). Moved here from
// provisioning/02_proxy_constraints.cypher when the G102 fold retired that
// file's charter (cross-database joins need matching keys in BOTH databases;
// there is one database now). The DISCIPLINE it carried survives intact:
// identity is always a BUSINESS key (ADR 0001), never an internal node id —
// it is what lets a corpus rebuild and re-link (truncate-and-reload), and what
// deepdoc's graph-seeded retrieval cites back to. The URN grammar:
// urn:drydocs:dataasset:{platform}:{namespace}:{name}.
CREATE CONSTRAINT dataasset_id        IF NOT EXISTS FOR (a:DataAsset)           REQUIRE a.assetId IS UNIQUE;
CREATE INDEX      job_name            IF NOT EXISTS FOR (j:ControlMJob)         ON  (j.job_name);

// Host topology (P3; gate controlm-hosts-topology 2026-07-09). Group grain is
// per data center — the same GRPNAME can exist in several DCs; member hosts
// are keyed on nodeid ALONE (multi-group membership is expected).
CREATE CONSTRAINT controlmhostgroup_key IF NOT EXISTS FOR (g:ControlMHostGroup) REQUIRE (g.data_center, g.name) IS NODE KEY;
CREATE CONSTRAINT executionhost_nodeid  IF NOT EXISTS FOR (h:ExecutionHost)     REQUIRE h.nodeid IS UNIQUE;

// --- Software registry (plan 07 / ADR 0004) ----------------------------------
CREATE CONSTRAINT vendor_id           IF NOT EXISTS FOR (v:Vendor)              REQUIRE v.vendor_id IS UNIQUE;
CREATE CONSTRAINT softwareproduct_id  IF NOT EXISTS FOR (p:SoftwareProduct)     REQUIRE p.product_id IS UNIQUE;

// --- Docs corpus lexical graph (bmc-docs; gate bmc-docs-lexical-load) --------
CREATE CONSTRAINT document_id         IF NOT EXISTS FOR (d:Document)            REQUIRE d.doc_id IS UNIQUE;
CREATE CONSTRAINT chunk_id            IF NOT EXISTS FOR (c:Chunk)               REQUIRE c.chunk_id IS UNIQUE;

// --- Data assets / files / channels -----------------------------------------
CREATE CONSTRAINT table_qualified     IF NOT EXISTS FOR (t:Distribution)        REQUIRE (t.database_nm, t.schema_nm, t.table_nm) IS NODE KEY;
CREATE INDEX      file_arrival        IF NOT EXISTS FOR (f:File)                ON  (f.arrived_at);
CREATE CONSTRAINT channel_id          IF NOT EXISTS FOR (ch:Channel)            REQUIRE ch.id IS UNIQUE;

// --- Snapshots (versioning at/above Application) ----------------------------
CREATE CONSTRAINT app_snapshot_id     IF NOT EXISTS FOR (s:ApplicationSnapshot) REQUIRE s.snapshot_id IS UNIQUE;
CREATE CONSTRAINT product_snapshot_id IF NOT EXISTS FOR (s:ProductSnapshot)     REQUIRE s.snapshot_id IS UNIQUE;
CREATE CONSTRAINT lob_snapshot_id     IF NOT EXISTS FOR (s:CatalogLOBSnapshot)  REQUIRE s.snapshot_id IS UNIQUE;

// --- Documentation traceability + review feedback (L7; gate
// doc-traceability-feedback signed off 2026-07-20). SOURCE-NAMESPACED keys
// (gate A2) — origin is part of every identity, never a bare stem/path. -----
CREATE CONSTRAINT design_doc_key      IF NOT EXISTS FOR (d:DesignDoc)           REQUIRE (d.origin, d.doc_id) IS NODE KEY;
CREATE CONSTRAINT doc_section_key     IF NOT EXISTS FOR (s:DocSection)          REQUIRE (s.origin, s.doc_id, s.anchor) IS NODE KEY;
CREATE CONSTRAINT requirement_key     IF NOT EXISTS FOR (r:Requirement)         REQUIRE (r.origin, r.requirement_id) IS NODE KEY;
CREATE CONSTRAINT component_key       IF NOT EXISTS FOR (c:Component)           REQUIRE (c.origin, c.ref) IS NODE KEY;
CREATE CONSTRAINT test_case_key       IF NOT EXISTS FOR (t:TestCase)            REQUIRE (t.origin, t.ref) IS NODE KEY;
CREATE CONSTRAINT feedback_note_key   IF NOT EXISTS FOR (f:FeedbackNote)        REQUIRE (f.origin, f.doc_id, f.doc_rev, f.anchor) IS NODE KEY;

// --- Self-documentation code graph (G33 / Epic U; gate
// self-documentation-code-graph signed off 2026-07-27). ONE :Project root
// (§B1(a)); :CodeModule keyed on file_id — the only non-colliding key (§C2).
// The :CodeModule/:SoftwareProduct mutual-exclusion is a GRAPH-TEST in
// m1-verify, NOT a constraint — Neo4j cannot declare label exclusion (§F1).
CREATE CONSTRAINT project_id          IF NOT EXISTS FOR (p:Project)             REQUIRE p.project_id IS UNIQUE;
CREATE CONSTRAINT codemodule_file_id  IF NOT EXISTS FOR (m:CodeModule)          REQUIRE m.file_id IS UNIQUE;
// :CodeDirectory shares the file_id key space with :CodeModule (both are
// repo-relative paths; a path is a dir or a file, never both — SME ruling
// 2026-08-05, admitting the containment tree the G33 gate deferred).
CREATE CONSTRAINT codedirectory_file_id IF NOT EXISTS FOR (d:CodeDirectory)     REQUIRE d.file_id IS UNIQUE;
// --- Infrastructure / server location (Z3; gate server-location-ontology
// SIGNED OFF 12/12, 2026-08-19). :Server is the INVENTORY backbone (§A1), keyed
// on name — the Z2 join key; deliberately NOT ExecutionHost's nodeid key
// (identity joins are the RESOLVES_TO_SERVER evidence edge, never a shared
// key). :DataCenter is the PHYSICAL building (§B1) — never the Control-M
// scheduling DC (§B4; the two never join by field name). The technology
// port (§C2) needs no new constraint: port_app_key's (parent_app_id, kind)
// composite already admits kind='Technology' — the two-port comment above
// predates the third kind.
CREATE CONSTRAINT server_name         IF NOT EXISTS FOR (s:Server)              REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT datacenter_name     IF NOT EXISTS FOR (d:DataCenter)          REQUIRE d.name IS UNIQUE;
