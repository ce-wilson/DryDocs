// =============================================================================
// controlm_folders.cypher  —  psgmgr.CM_DEF_VTAB -> :JobFolder + :ControlMServer
//
// Source: psgmgr.CM_DEF_VTAB (wraps dtsremgr.DEF_TAB; BMC calls folders
//                              "tables" — see naming gotcha in
//                              docs/m3_controlm_concept_mapping.md)
//
// Outputs:
//   (:JobFolder {folder_id, parent_table, user_daily, active})
//     -[:RUNS_ON {since}]-> (:ControlMServer {name})
//
// Each folder runs on exactly one server. The ``since`` timestamp on
// :RUNS_ON lets server migrations be auditable.
//
// Parameters (passed by BaseLoader._flush):
//   $batch        list of dicts (folder_id, parent_table, data_center,
//                                user_daily)
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

// Folder upsert.
MERGE (f:JobFolder:Collection {folder_id: row.folder_id})
  ON CREATE SET f.created_at = datetime($loaded_at),
                f.source     = 'psgmgr.CM_DEF_VTAB'
SET f.parent_table       = row.parent_table,
    f.user_daily         = row.user_daily,
    f.is_current_version = row.is_current_version,
    f.version_serial     = row.version_serial,
    f.capture_date       = row.capture_date,
    f.active             = (row.user_daily IS NOT NULL AND row.user_daily <> '' AND
                            row.is_current_version IN [1, '1', 'Y', true]),
    f.last_seen_at       = datetime($loaded_at),
    f.last_run_id        = $run_id

// Folder -> Server. The 'since' marker on :RUNS_ON only updates on create;
// subsequent refreshes touch last_seen_at so we can prove the folder still
// runs on this server today.
MERGE (f)-[r:RUNS_ON]->(srv)
  ON CREATE SET r.since        = datetime($loaded_at),
                r.source       = 'psgmgr.CM_DEF_VTAB',
                r.loader       = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id

// Provenance attribution: this loader run touched this folder.
WITH f
MATCH (run:JobRun {run_id: $run_id})
MERGE (f)-[r:WAS_GENERATED_BY {source: 'BMC'}]->(run)
  ON CREATE SET r.first_seen_at = datetime($loaded_at)
SET r.last_seen_at = datetime($loaded_at);
