// =============================================================================
// controlm_jobs.cypher  —  psgmgr.CM_DEF_VJOB -> :ControlMJob
//
// Source: psgmgr.CM_DEF_VJOB (replicated copy of dtsremgr.DEF_VJOB)
//
// Composite NODE KEY: (folder_id, job_id). JOB_ID is folder-scoped in
// BMC — the same JOB_ID appears in multiple folders (e.g., a job
// promoted to both _DLY and _CYC variants). VERSION_SERIAL is captured
// as a PROPERTY for audit / freshness, not part of identity — re-loads
// with a newer VERSION_SERIAL update the same node in place.  Run
// m3_constraints_upgrade.cypher to lock this on existing graphs.
//
// Prereq: controlm_folders must have loaded so the parent :JobFolder
// exists. If a job references a folder we haven't loaded yet, the MATCH
// silently drops that job; rerun folders then jobs.
//
// PARENT_TABLE (folder name denormalized on the job) is kept as a property
// for query convenience but is NOT used as a relationship key — the FK is
// TABLE_ID via :CONTAINS_JOB to the :JobFolder.
//
// APPLICATION is the **Control-M app code**, NOT the SEAL business-app
// name.  Different teams use it differently: some put a Platform name
// here, others put their 3-char appcode. It does NOT reconcile cleanly to
// :Application.seal_id — the folder-name 3-char appcode (positions 3-5,
// e.g. 'ARA' in 'PRARAG-HLDM-...') is the canonical mechanism for that
// linkage. See docs/m3_controlm_concept_mapping.md.
//
// Parameters:
//   $batch        list of dicts matching the projection in controlm_jobs.sql
//   $run_id, $loaded_at, $loader, $source_label  — BaseLoader defaults.
// =============================================================================

UNWIND $batch AS row

// Folder must exist (loaded by controlm_folders before this runs).
MATCH (f:JobFolder {folder_id: row.folder_id})

// Composite-key Job upsert. (folder_id, job_id) is the natural identity;
// version_serial flows through as a property.
MERGE (j:ControlMJob:Activity {
    folder_id: row.folder_id,
    job_id: row.job_id
})
  ON CREATE SET j.created_at = datetime($loaded_at),
                j.source     = 'psgmgr.CM_DEF_VJOB'
SET j.version_serial     = row.version_serial,
    j.job_name           = row.job_name,
    j.parent_table       = row.parent_table,
    j.application        = row.application,
    j.group_name         = row.group_name,
    j.task_type          = row.task_type,
    j.cyclic             = row.cyclic,
    j.cyclic_type        = row.cyclic_type,
    j.job_order          = row.job_order,
    j.owner              = row.owner,
    j.author             = row.author,
    j.node_id            = row.node_id,
    j.cmd_line           = row.cmd_line,
    j.description        = row.description,
    j.memname            = row.memname,
    j.priority           = row.priority,
    j.critical           = row.critical,
    j.active_from        = row.active_from,
    j.active_till        = row.active_till,
    j.end_folder         = row.end_folder,
    j.is_current_version = row.is_current_version,
    j.version_opcode     = row.version_opcode,
    j.version_timestamp  = row.version_timestamp,
    j.version_user       = row.version_user,
    j.instance_name      = row.instance_name,
    j.capture_date       = row.capture_date,
    j.active             = row.is_current_version = '1',
    j.last_seen_at       = datetime($loaded_at),
    j.last_run_id        = $run_id

// Folder -> Job containment.
MERGE (f)-[r:CONTAINS_JOB]->(j)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = 'psgmgr.CM_DEF_VJOB',
                r.loader        = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id

// Provenance attribution.
WITH j
MATCH (run:JobRun {run_id: $run_id})
MERGE (j)-[r:WAS_GENERATED_BY {source: 'BMC'}]->(run)
  ON CREATE SET r.first_seen_at = datetime($loaded_at)
SET r.last_seen_at = datetime($loaded_at);
