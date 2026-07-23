// =============================================================================
// controlm_dependencies_derived.cypher  —  materialize :WAS_INFORMED_BY edges
//
// Consumes the output rows of controlm_dependencies_recursive.sql — DIRECT
// predecessor pairs only (phased-loader change, ported from the company repo
// 2026-07-23). Each row is (in_table_job_id, out_condition, out_table_job_id):
// pure ctlm_id composites (folder_id.job_id — the (folder_id, job_id) NODE
// KEY in composite form; P2 gate §B) between independently-loaded jobs.
//
// Materializes:
//   (:ControlMJob {successor}) -[:WAS_INFORMED_BY {via_condition,
//                                                  derived:true}]-> (:ControlMJob {predecessor})
//
// Relationship maps to prov:wasInformedBy — both endpoints are prov:Activity
// subclasses. Direction: (successor)→(predecessor).
//
// The stored-closure properties (level, path) are GONE with the recursive
// CTE: transitive reach is a graph traversal (variable-length
// :WAS_INFORMED_BY patterns), not a stored closure. m3-verify now checks
// via_condition on each edge instead.
//
// Match strategy:
//   * Split each composite on '.' → (folder_id, job_id), the NODE KEY after
//     the m3_constraints_upgrade — guaranteed unique. JOB_ID alone is
//     folder-scoped in BMC (DLY/CYC promoted twins share it).
//   * Both endpoints must ALREADY exist — this loader runs in the deferred
//     `ingest-controlm --phase relationships` pass: once, UNSCOPED, after
//     all nodes are loaded. Cross-folder edges silently never got created
//     when folders loaded one at a time (the second endpoint's MATCH
//     missed) — the reason --phase exists.
//
// Parameters: $batch, $run_id, $loaded_at, $loader.
// =============================================================================

UNWIND $batch AS row

MATCH (j:ControlMJob {
    folder_id: split(row.in_table_job_id, '.')[0],
    job_id:    split(row.in_table_job_id, '.')[1]
})

MATCH (p:ControlMJob {
    folder_id: split(row.out_table_job_id, '.')[0],
    job_id:    split(row.out_table_job_id, '.')[1]
})

MERGE (j)-[r:WAS_INFORMED_BY {via_condition: row.out_condition}]->(p)
  ON CREATE SET r.derived       = true,
                r.first_seen_at = datetime($loaded_at),
                r.source        = 'psgmgr.recursive_predecessor',
                r.loader        = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id;
