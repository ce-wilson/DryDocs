// =============================================================================
// controlm_conditions_out.cypher  —  psgmgr.CM_DEF_LNKO_P_VW -> :Condition
//                                     + :EMITS_OUT_CONDITION edge
//
// Each row is "job J (in folder F, version_serial V) EMITS condition C with
// operator SIGN."  SIGN = '+' adds; SIGN = '-' removes.
//
// Condition is keyed identically to controlm_conditions_in.cypher so the
// same :Condition node is shared between IN and OUT references when
// (folder_id, name) matches.
//
// Parameters: $batch, $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

// Job must exist (loaded by controlm_jobs first). MATCH on (folder_id, job_id).
MATCH (j:ControlMJob {
    folder_id: row.folder_id,
    job_id: row.job_id
})

MERGE (c:Condition:Entity {
    folder_id: row.folder_id,
    name: row.condition_name
})
  ON CREATE SET c.created_at = datetime($loaded_at),
                c.source     = 'psgmgr.CM_DEF_LNKO_P_VW'
SET c.version_serial    = row.version_serial,
    c.last_seen_at      = datetime($loaded_at),
    c.last_run_id       = $run_id,
    c.last_capture_date = row.capture_date

MERGE (j)-[r:EMITS_OUT_CONDITION]->(c)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = 'psgmgr.CM_DEF_LNKO_P_VW',
                r.loader        = $loader
SET r.odate          = row.odate,
    r.sign           = row.sign,
    r.isn            = row.isn,
    r.version_opcode = row.version_opcode,
    r.last_seen_at   = datetime($loaded_at),
    r.last_run_id    = $run_id

WITH c
MATCH (run:JobRun {run_id: $run_id})
MERGE (c)-[r:WAS_GENERATED_BY {source: 'BMC'}]->(run)
  ON CREATE SET r.first_seen_at = datetime($loaded_at)
SET r.last_seen_at = datetime($loaded_at);
