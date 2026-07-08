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
CREATE CONSTRAINT application_seal    IF NOT EXISTS FOR (a:Application)         REQUIRE a.seal_id IS UNIQUE;
CREATE INDEX      application_status  IF NOT EXISTS FOR (a:Application)         ON  (a.status);
CREATE INDEX      application_risk    IF NOT EXISTS FOR (a:Application)         ON  (a.risk_level);
CREATE INDEX      application_name    IF NOT EXISTS FOR (a:Application)         ON  (a.name);

// Two-port pattern: each Application has exactly one EventProcessing and one
// BatchProcessing child. Composite uniqueness on (parent_seal_id, kind) lets
// us enforce that without modeling the relationship inside the constraint.
CREATE CONSTRAINT port_unique         IF NOT EXISTS FOR (p:Port)                REQUIRE (p.parent_seal_id, p.kind) IS NODE KEY;

// --- People / org chart ------------------------------------------------------
CREATE CONSTRAINT area_product_id     IF NOT EXISTS FOR (ap:AreaProduct)        REQUIRE ap.area_product_id IS UNIQUE;
CREATE CONSTRAINT devteam_id          IF NOT EXISTS FOR (d:DevTeam)             REQUIRE d.team_id IS UNIQUE;
CREATE CONSTRAINT employee_id         IF NOT EXISTS FOR (e:Employee)            REQUIRE e.employee_id IS UNIQUE;
CREATE CONSTRAINT sn_group_id         IF NOT EXISTS FOR (g:ServiceNowGroup)     REQUIRE g.group_id IS UNIQUE;
CREATE CONSTRAINT jira_board_id       IF NOT EXISTS FOR (b:JiraBoard)           REQUIRE b.board_id IS UNIQUE;

// Reified Membership pattern (W3C ORG)
CREATE CONSTRAINT role_name           IF NOT EXISTS FOR (r:Role)                REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT role_id             IF NOT EXISTS FOR (r:Role)                REQUIRE r.role_id IS UNIQUE;
CREATE CONSTRAINT membership_id       IF NOT EXISTS FOR (m:Membership)          REQUIRE m.membership_id IS UNIQUE;

// --- Schedulers --------------------------------------------------------------
CREATE CONSTRAINT scheduler_kind      IF NOT EXISTS FOR (k:SchedulerKind)       REQUIRE k.name IS UNIQUE;

// --- Control-M / BMC ---------------------------------------------------------
// Node key uses natural identity (folder_id, job_id) without version_serial —
// loaders filter to IS_CURRENT_VERSION='1' so one canonical node per logical
// entity; version_serial stays as an audit property only.
CREATE CONSTRAINT controlm_server     IF NOT EXISTS FOR (s:ControlMServer)      REQUIRE s.name IS UNIQUE;
// Control-M APPLICATION grouping (folder header row; gate controlm-q1q3-phase1).
// NOT the SEAL business :Application — see ADR 0003 naming rules.
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
CREATE INDEX      job_name            IF NOT EXISTS FOR (j:ControlMJob)         ON  (j.job_name);

// --- Software registry (plan 07 / ADR 0004) ----------------------------------
CREATE CONSTRAINT vendor_id           IF NOT EXISTS FOR (v:Vendor)              REQUIRE v.vendor_id IS UNIQUE;
CREATE CONSTRAINT softwareproduct_id  IF NOT EXISTS FOR (p:SoftwareProduct)     REQUIRE p.product_id IS UNIQUE;

// --- Data assets / files / channels -----------------------------------------
CREATE CONSTRAINT table_qualified     IF NOT EXISTS FOR (t:Distribution)        REQUIRE (t.database_nm, t.schema_nm, t.table_nm) IS NODE KEY;
CREATE INDEX      file_arrival        IF NOT EXISTS FOR (f:File)                ON  (f.arrived_at);
CREATE CONSTRAINT channel_id          IF NOT EXISTS FOR (ch:Channel)            REQUIRE ch.id IS UNIQUE;

// --- Snapshots (versioning at/above Application) ----------------------------
CREATE CONSTRAINT app_snapshot_id     IF NOT EXISTS FOR (s:ApplicationSnapshot) REQUIRE s.snapshot_id IS UNIQUE;
CREATE CONSTRAINT product_snapshot_id IF NOT EXISTS FOR (s:ProductSnapshot)     REQUIRE s.snapshot_id IS UNIQUE;
CREATE CONSTRAINT lob_snapshot_id     IF NOT EXISTS FOR (s:CatalogLOBSnapshot)  REQUIRE s.snapshot_id IS UNIQUE;