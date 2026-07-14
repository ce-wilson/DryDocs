// =============================================================================
// manual_seal_attribution.cypher  —  SME-authored manual mapping CSV rows ->
//                                    the same WAS_ASSOCIATED_WITH edge shape
//
// Tier 5 of the K2 match policy (gate seal-attribution-match-policy §F,
// SME-confirmed 2026-07-14). Rows arrive ONLY through manual_loads.py, which
// enforces the manifest gate (config/manual-loads/manifest.yaml: registered
// BEFORE load, replaces_with required) and the supported-shape check.
//
//   - The source job must PRE-EXIST (MATCH) — a manual row never creates a
//     ControlMJob; missing jobs surface via the loader's written-vs-rows
//     reconciliation, never silently.
//   - The target Application is created ONLY when the SME set
//     create_target_if_missing, stamped manually_created: true +
//     manual_load_file + authored_by (§F.4) — counted separately, never
//     blended into matched/unmatched.
//   - The edge carries match_method 'manual' + source 'manual-csv' +
//     manual_load_file + authored_by. Once written it PINS: the automated
//     loader's resolver and cypher both skip pinned jobs; retirement
//     (manifest -> superseded) is always a human act.
//
// Parameters: $batch (validated ManualMappingRow dicts),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

MATCH (j:ControlMJob {folder_id: row.folder_id, job_id: row.job_id})

// §F.4 — SME-authorized node creation only, stamped as manual tech debt.
FOREACH (_ IN CASE WHEN row.create_target_if_missing THEN [1] ELSE [] END |
  MERGE (n:Application {seal_id: row.seal_id})
    ON CREATE SET n.manually_created  = true,
                  n.manual_load_file  = row.manual_load_file,
                  n.authored_by       = row.authored_by,
                  n.created_at        = datetime($loaded_at),
                  n.source            = 'manual-csv'
)

WITH j, row
MATCH (a:Application {seal_id: row.seal_id})

MERGE (j)-[r:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]->(a)
  ON CREATE SET r.first_seen_at    = datetime($loaded_at),
                r.source           = 'manual-csv',
                r.match_method     = 'manual',
                r.manual_load_file = row.manual_load_file,
                r.authored_by      = row.authored_by
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id;
