// =============================================================================
// controlm_folders.cypher  —  psgmgr.CM_DEF_VTAB -> :JobFolder + :ControlMServer
//
// Source: psgmgr.CM_DEF_VTAB (replicated copy of dtsremgr.DEF_VTAB).
// BMC calls folders "tables" — naming gotcha lives in
// docs/m3_controlm_concept_mapping.md.
//
// Outputs:
//   (:JobFolder {folder_id, sched_table, user_daily, table_status, ...})
//     -[:RUNS_ON {since}]-> (:ControlMServer:Platform {name})
//
// Each folder runs on exactly one server. The :RUNS_ON.since timestamp
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
MERGE (f:JobFolder:Collection {folder_id: row.folder_id})
  ON CREATE SET f.created_at = datetime($loaded_at),
                f.source     = 'psgmgr.CM_DEF_VTAB'
SET f.sched_table       = row.sched_table,
    f.user_daily        = row.user_daily,
    f.table_status      = row.table_status,
    f.table_type        = row.table_type,
    f.instance_name     = row.instance_name,
    f.last_updated      = row.last_updated,
    f.last_updated_user = row.last_updated_user,
    f.capture_date      = row.capture_date,
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

// Folder -> Server.
MERGE (f)-[r:RUNS_ON]->(srv)
  ON CREATE SET r.since        = datetime($loaded_at),
                r.source       = 'psgmgr.CM_DEF_VTAB',
                r.loader       = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id

// Provenance: this loader run touched this folder.
WITH f
MATCH (run:JobRun {run_id: $run_id})
MERGE (f)-[r:WAS_GENERATED_BY {source: 'BMC'}]->(run)
  ON CREATE SET r.first_seen_at = datetime($loaded_at)
SET r.last_seen_at = datetime($loaded_at);
