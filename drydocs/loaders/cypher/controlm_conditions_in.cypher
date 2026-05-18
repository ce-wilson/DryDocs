// =============================================================================
// controlm_conditions_in.cypher  —  psgmgr.CM_DEF_LNKI_P_VW -> :Condition
//                                    + :REQUIRES_IN_CONDITION edge
//
// Each row is "job J (in folder F, version_serial V) CONSUMES condition C,
// possibly combined with other IN conditions via AND_OR/PARENTHESES/ORDER_."
//
// Condition NODE KEY: (folder_id, name). Conditions are namespaced by
// folder; version_serial is captured as a property (current-version
// filter is applied at SQL ingest, so the loaded value is always the
// current version of the definition).
//
// Parameters: $batch, $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

// Job must exist (loaded by controlm_jobs first). MATCH on (folder_id, job_id) —
// JOB_ID is folder-scoped in BMC.
MATCH (j:ControlMJob {
    folder_id: row.folder_id,
    job_id: row.job_id
})

// Condition upsert. (folder_id, name) is the natural identity; the same
// condition reused across job versions resolves to one node.
// ":Entity" anchors the PROV vocabulary.
MERGE (c:Condition:Entity {
    folder_id: row.folder_id,
    name: row.condition_name
})
  ON CREATE SET c.created_at = datetime($loaded_at),
                c.source     = 'psgmgr.CM_DEF_LNKI_P_VW'
SET c.version_serial    = row.version_serial,
    c.last_seen_at      = datetime($loaded_at),
    c.last_run_id       = $run_id,
    c.last_capture_date = row.capture_date

// REQUIRES_IN_CONDITION edge carries the boolean-expression metadata so
// downstream queries can reconstruct the IN-condition tree if needed.
MERGE (j)-[r:REQUIRES_IN_CONDITION]->(c)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = 'psgmgr.CM_DEF_LNKI_P_VW',
                r.loader        = $loader
SET r.odate          = row.odate,
    r.and_or         = row.and_or,
    r.parentheses    = row.parentheses,
    r.order_         = row.order_,
    r.isn            = row.isn,
    r.version_opcode = row.version_opcode,
    r.last_seen_at   = datetime($loaded_at),
    r.last_run_id    = $run_id

// Provenance.
WITH c
MATCH (run:JobRun {run_id: $run_id})
MERGE (c)-[r:WAS_GENERATED_BY {source: 'BMC'}]->(run)
  ON CREATE SET r.first_seen_at = datetime($loaded_at)
SET r.last_seen_at = datetime($loaded_at);
