// =============================================================================
// controlm_dependencies_derived.cypher  —  materialize :WAS_INFORMED_BY edges
//
// Consumes the output rows of controlm_dependencies_recursive.sql. Each
// input row is (successor job, matching condition, predecessor job) plus
// recursion_level and dependency_path.
//
// Materializes:
//   (:ControlMJob {successor}) -[:WAS_INFORMED_BY {derived:true,
//                                                   via_condition,
//                                                   recursion_level,
//                                                   dependency_path}]-> (:ControlMJob {predecessor})
//
// Relationship maps to prov:wasInformedBy — both endpoints are prov:Activity
// subclasses. Direction: (successor)→(predecessor).
//
// Match strategy:
//   * JOB_ID is folder-scoped in BMC — same JOB_ID appears across
//     different folders for the same logical job promoted to daily/cyclic
//     variants.  We match on (folder_id, job_id), which is the NODE KEY
//     after the m3_constraints_upgrade — guaranteed unique.
//   * version_serial is a property, not part of identity; current-version
//     filtering happened at SQL ingest, so no Cypher-side filter needed.
//
// Shortest-path preservation:
//   * recursion_level + dependency_path are written ONLY ON CREATE.
//   * The SQL outputs ``ORDER BY in_job_name, recursion_level`` so the
//     shortest path arrives first per (successor, predecessor, condition)
//     triple. The first MERGE wins, and subsequent encounters via longer
//     paths don't overwrite.
//
// Parameters: $batch, $run_id, $loaded_at, $loader.
// =============================================================================

UNWIND $batch AS row

MATCH (j:ControlMJob {
    folder_id: row.in_parent_table_id,
    job_id:    row.in_job_id
})

MATCH (p:ControlMJob {
    folder_id: row.dependent_table_id,
    job_id:    row.dependent_job_id
})

MERGE (j)-[r:WAS_INFORMED_BY {via_condition: row.out_condition}]->(p)
  ON CREATE SET r.derived         = true,
                r.recursion_level = row.recursion_level,
                r.dependency_path = row.dependency_path,
                r.first_seen_at   = datetime($loaded_at),
                r.source          = 'psgmgr.recursive_predecessor',
                r.loader          = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id;
