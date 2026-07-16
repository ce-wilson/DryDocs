// =============================================================================
// seal_attribution.cypher  —  resolved STG_APP_FACT decisions ->
//                             (:ControlMJob)-[:WAS_ASSOCIATED_WITH {role:'seal_app_ref'}]->(:BusinessApplication)
//
// Backlog K2; edge shape SME-confirmed at gate seal-attribution-match-policy
// (config/gate-log.md, 2026-07-14, §D/§E):
//
//   - MATCH both endpoints — this loader creates NO nodes on the automated
//     path. Job identity = (folder_id, job_id) node key (controlm-psgmgr);
//     Application identity = seal_id (seal-extract). A decision whose
//     endpoints are absent writes nothing here and is surfaced by the
//     loader as JobRun.dropped_in_graph (never a silent drop, §B).
//   - PIN guard (§F): a job carrying a manually-asserted edge
//     (match_method = 'manual') is never touched by automation — the Python
//     resolver already excludes pinned jobs (surfacing PIN-CONFLICTs on the
//     coverage report); this WHERE is the belt-and-suspenders backstop.
//   - ON CREATE: first_seen_at / source / match_method (set once, §D).
//     source is the fixed loader-identity string so this edge's provenance
//     stays distinct from any future owner/author WAS_ASSOCIATED_WITH role.
//   - SET every run: last_seen_at / last_run_id (re-confirmation bookkeeping).
//
// K3 rider (gate log): this shape type-checks while :BusinessApplication is still
// prov:SoftwareAgent; the K4 reclass re-opens the edge SHAPE at its own gate.
//
// Parameters: $batch (validated SealAttributionRow dicts),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

MATCH (j:ControlMJob {folder_id: row.folder_id, job_id: row.job_id})
MATCH (a:BusinessApplication {seal_id: row.seal_id})
WHERE NOT EXISTS {
  MATCH (j)-[m:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]->(:BusinessApplication)
  WHERE m.match_method = 'manual'
}

MERGE (j)-[r:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]->(a)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = 'controlm-variable-normalization',
                r.match_method  = row.match_method
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id;
