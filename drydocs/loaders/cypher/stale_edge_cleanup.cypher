// =============================================================================
// stale_edge_cleanup.cypher  —  (D1 / consolidated-plan B.2)
//
// Delete condition edges for CHANGED jobs before re-asserting them, so an
// incremental refresh doesn't leave orphaned REQUIRES_IN/EMITS_OUT edges when a
// job's conditions change between versions.
//
// MUST run BEFORE controlm_conditions_in.cypher / controlm_conditions_out.cypher
// in each incremental batch (IncrementalControlMLoader, Stream A.4).
//
// Parameters:
//   $changed_keys  list of {folder_id, job_id} for jobs whose version advanced
// =============================================================================

UNWIND $changed_keys AS key
MATCH (j:ControlMJob {folder_id: key.folder_id, job_id: key.job_id})
OPTIONAL MATCH (j)-[r:REQUIRES_IN_CONDITION|EMITS_OUT_CONDITION]->()
DELETE r;
