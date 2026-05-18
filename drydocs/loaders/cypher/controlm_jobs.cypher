// =============================================================================
// controlm_jobs.cypher  —  psgmgr.CM_DEF_VJOB -> :ControlMJob
//
// Source: psgmgr.CM_DEF_VJOB (wraps dtsremgr.DEF_JOB)
//
// Outputs:
//   (:ControlMJob {job_id, version_serial, job_name, cyclic_type, job_order, active})
//     <-[:CONTAINS_JOB]- (:JobFolder)
//
// Composite NODE KEY: (job_id, version_serial). A new VERSION_SERIAL value
// creates a NEW :ControlMJob node so history is non-destructive (v3 §J).
// Re-loads with identical (job_id, version_serial) are no-ops via MERGE.
//
// Prereq: controlm_folders must have loaded so the parent :JobFolder
// exists. If a job references a folder we haven't loaded yet (race), the
// MATCH below quietly drops that job; rerun folders then jobs.
//
// Parameters (passed by BaseLoader._flush):
//   $batch        list of dicts (job_id, version_serial, folder_id,
//                                job_name, cyclic_type, job_order)
//   $run_id       UUID of this loader's :JobRun
//   $loaded_at    ISO datetime string
//   $loader       loader version tag
//   $source_label 'csv' (sample mode) or 'oracle' (production)
// =============================================================================

UNWIND $batch AS row

// Folder must exist (loaded by controlm_folders before this runs).
MATCH (f:JobFolder {folder_id: row.folder_id})

// Composite-key Job upsert.
MERGE (j:ControlMJob:Activity {
    job_id: row.job_id,
    version_serial: row.version_serial
})
  ON CREATE SET j.created_at = datetime($loaded_at),
                j.source     = 'psgmgr.CM_DEF_VJOB'
SET j.job_name           = row.job_name,
    j.cyclic_type        = row.cyclic_type,
    j.job_order          = row.job_order,
    j.is_current_version = row.is_current_version,
    j.capture_date       = row.capture_date,
    j.active             = row.is_current_version IN [1, '1', 'Y', true],
    j.last_seen_at       = datetime($loaded_at),
    j.last_run_id        = $run_id

// Folder -> Job containment.
MERGE (f)-[r:CONTAINS_JOB]->(j)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = 'psgmgr.DEF_JOB',
                r.loader        = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id

// Provenance attribution.
WITH j
MATCH (run:JobRun {run_id: $run_id})
MERGE (j)-[r:WAS_GENERATED_BY {source: 'BMC'}]->(run)
  ON CREATE SET r.first_seen_at = datetime($loaded_at)
SET r.last_seen_at = datetime($loaded_at);
