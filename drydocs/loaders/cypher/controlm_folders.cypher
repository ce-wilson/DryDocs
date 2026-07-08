// =============================================================================
// controlm_folders.cypher  —  psgmgr.CM_DEF_VTAB -> :ControlMFolder + :ControlMServer
//
// Source: psgmgr.CM_DEF_VTAB (replicated copy of dtsremgr.DEF_VTAB).
// BMC calls folders "tables" — naming gotcha lives in
// docs/m3_controlm_concept_mapping.md.
//
// Outputs:
//   (:ControlMFolder {folder_id, sched_table, user_daily, table_status, ...})
//     -[:SCHEDULED_ON {since}]-> (:ControlMServer:Platform {name})
//   (:ControlMApplication:Collection {name}) -[:CONTAINS_FOLDER]-> (folder)
//     when the folder header row carries an APPLICATION value
//     (gate controlm-q1q3-phase1; vocabulary m3_contains_folder)
//
// TWO fields become labels in this pass: DATA_CENTER -> :ControlMServer and
// the header-row APPLICATION -> :ControlMApplication. Both grouping nodes
// therefore exist BEFORE the jobs pass runs (nodes-before-relationships).
//
// Each folder is scheduled on exactly one server. The :SCHEDULED_ON.since timestamp
// (set on create) plus last_seen_at (updated each refresh) make folder
// migrations between servers auditable.
//
// Active-folder filter (USER_DAILY IS NOT NULL) is applied in the SQL
// projection upstream. Folders that leak through with a NULL USER_DAILY
// would still merge here with active = false.
//
// Parameters (passed by BaseLoader._flush):
//   $batch        list of dicts matching the projection columns
//   $run_id       UUID of this loader's :JobRun
//   $loaded_at    ISO datetime string
//   $loader       loader version tag
//   $source_label 'csv' (sample mode) or 'oracle' (production)
// =============================================================================

UNWIND $batch AS row

// Control-M server upsert (one node per unique DATA_CENTER value).
MERGE (srv:ControlMServer:Platform {name: row.data_center})
  ON CREATE SET srv.created_at = datetime($loaded_at),
                srv.source     = 'psgmgr.CM_DEF_VTAB'
SET srv.last_seen_at = datetime($loaded_at),
    srv.last_run_id  = $run_id

// Folder upsert — name from SCHED_TABLE per the real DDL.
// The loader pre-parses SCHED_TABLE into structured properties
// (environment, lob_code, app_code, folder_type_code) via
// drydocs.controlm.folder_name.parse_folder_name before sending the
// batch — those parsed properties arrive as row fields.
MERGE (f:ControlMFolder:Collection {folder_id: row.folder_id})
  ON CREATE SET f.created_at = datetime($loaded_at),
                f.source     = 'psgmgr.CM_DEF_VTAB'
SET f.sched_table       = row.sched_table,
    f.user_daily        = row.user_daily,
    f.table_status      = row.table_status,
    f.table_type        = row.table_type,
    f.instance_name     = row.instance_name,
    f.last_updated      = CASE WHEN row.last_updated IS NULL OR row.last_updated = '' THEN null
                               ELSE datetime(replace(row.last_updated, ' ', 'T')) END,
    f.last_updated_user = row.last_updated_user,
    // source audit envelope (audit-fields.yaml): CM_DEF_VTAB has no creation
    // columns — updated-side only. Kept alongside the raw-named props above;
    // the raw pair retires in the doc-06 Phase 3 migration.
    f.source_updated_by = row.last_updated_user,
    f.source_updated_at = CASE WHEN row.last_updated IS NULL OR row.last_updated = '' THEN null
                               ELSE datetime(replace(row.last_updated, ' ', 'T')) END,
    f.capture_date      = CASE WHEN row.capture_date IS NULL OR row.capture_date = '' THEN null
                               ELSE datetime(replace(row.capture_date, ' ', 'T')) END,
    f.environment_code  = row.environment_code,
    f.environment       = row.environment,
    f.lob_code          = row.lob_code,
    f.lob               = row.lob,
    f.app_code          = row.app_code,
    f.folder_type_code  = row.folder_type_code,
    f.folder_type       = row.folder_type,
    f.active            = (row.user_daily IS NOT NULL AND row.user_daily <> ''),
    f.last_seen_at      = datetime($loaded_at),
    f.last_run_id       = $run_id

// Folder -> Server.  (B.1: renamed RUNS_ON -> SCHEDULED_ON per the vocabulary;
// run migrate_runs_on_to_scheduled_on.cypher once on any existing graph.)
MERGE (f)-[r:SCHEDULED_ON]->(srv)
  ON CREATE SET r.since        = datetime($loaded_at),
                r.source       = 'psgmgr.CM_DEF_VTAB',
                r.loader       = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id

// Provenance: this loader run touched this folder.
WITH f, row
MATCH (run:JobRun {run_id: $run_id})
MERGE (f)-[r:WAS_GENERATED_BY {source: 'BMC'}]->(run)
  ON CREATE SET r.first_seen_at = datetime($loaded_at)
SET r.last_seen_at = datetime($loaded_at)

// Control-M application grouping (second field-derived label of this pass).
// Placed AFTER the provenance tail: the WHERE below drops header-less rows
// from the remainder of the statement, so everything above must already be
// written. Constraint controlmapplication_name backs the MERGE.
WITH f, row
WHERE row.application IS NOT NULL AND row.application <> ''
MERGE (app:ControlMApplication:Collection {name: row.application})
  ON CREATE SET app.created_at = datetime($loaded_at),
                app.source     = 'psgmgr.CM_DEF_VJOB (folder header row)'
SET app.last_seen_at = datetime($loaded_at),
    app.last_run_id  = $run_id

// Application -> Folder containment (prov:hadMember; m3_contains_folder).
MERGE (app)-[cf:CONTAINS_FOLDER]->(f)
  ON CREATE SET cf.first_seen_at = datetime($loaded_at),
                cf.source        = 'psgmgr.CM_DEF_VJOB (folder header row)',
                cf.loader        = $loader
SET cf.last_seen_at = datetime($loaded_at),
    cf.last_run_id  = $run_id;
