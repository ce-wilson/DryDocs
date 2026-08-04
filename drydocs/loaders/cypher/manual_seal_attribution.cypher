// =============================================================================
// manual_seal_attribution.cypher  —  SME-authored manual mapping CSV rows ->
//   (:ControlMFolder)-[:BELONGS_TO_APPLICATION {role:'seal_app_ref'}]->(:Port)
//
// Tier 5 of the attribution policy (gate seal-attribution-match-policy §F,
// SME-confirmed 2026-07-14; rekeyed to the folder grain at K8 per gate
// seal-app-ref-edge-reshape §D2 — ONE shape everywhere). Rows arrive ONLY
// through manual_loads.py, which enforces the manifest gate
// (config/manual-loads/manifest.yaml: registered BEFORE load, replaces_with
// required) and the supported-shape check.
//
//   - Authoring is per APP CODE (§B1): a code-level row (folder_id null)
//     fans out over (:ControlMApplication)-[:CONTAINS_FOLDER]-> to every
//     folder under the code; a row with folder_id pins exactly one folder
//     (the per-folder resolution path for shared platform codes). Folders
//     must PRE-EXIST — a manual row never creates Control-M objects;
//     missing endpoints surface via the loader's written-vs-rows
//     reconciliation, never silently.
//   - The target Application (+ its BatchProcessing :Port) is created ONLY
//     when the SME set create_target_if_missing, stamped
//     manually_created: true + manual_load_file + authored_by (§F.4) —
//     counted separately, never blended into matched/unmatched.
//   - The edge carries origin 'manual-pin' + match_method 'manual' +
//     source 'manual-csv' + manual_load_file + authored_by. Once written it
//     PINS: the automated loader's resolver and cypher both skip pinned
//     folders; retirement (manifest -> superseded) is always a human act.
//
// Parameters: $batch (validated ManualMappingRow dicts),
//             $run_id, $loaded_at, $loader, $source_label,
//             $orchestrator_product_id (§G1 — the domain orchestrator's
//             software-registry ref; 'controlm' for this domain).
// =============================================================================

UNWIND $batch AS row

// §F.4 — SME-authorized node creation only, stamped as manual tech debt.
// IDENTITY KEY (gate business-application-identity §C1/§C2): app_id is the
// neutral canonical key; seal_id is dual-written as a deprecated alias.
FOREACH (_ IN CASE WHEN row.create_target_if_missing THEN [1] ELSE [] END |
  MERGE (n:BusinessApplication {app_id: row.app_id})
    ON CREATE SET n.seal_id           = row.app_id,   // deprecated alias — phase 3
                  n.manually_created  = true,
                  n.manual_load_file  = row.manual_load_file,
                  n.authored_by       = row.authored_by,
                  n.first_seen_at     = datetime($loaded_at),
                  n.source            = 'manual-csv'
)
WITH row
FOREACH (_ IN CASE WHEN row.create_target_if_missing THEN [1] ELSE [] END |
  MERGE (bp:Port:BatchProcessing {parent_app_id: row.app_id, kind: 'BatchProcessing'})
    ON CREATE SET bp.first_seen_at = datetime($loaded_at),
                  bp.active_state  = 'declared',
                  bp.declared_by   = 'manual-csv',
                  bp.declared_at   = datetime($loaded_at)
)

// Fan-out (§B1): a code-level row covers every folder under its app code;
// a folder-pinned row narrows to that one folder.
WITH row
MATCH (ca:ControlMApplication {name: row.app_code})-[:CONTAINS_FOLDER]->(f:ControlMFolder)
WHERE row.folder_id IS NULL OR f.folder_id = row.folder_id

WITH row, f
MATCH (p:Port:BatchProcessing {parent_app_id: row.app_id, kind: 'BatchProcessing'})

MERGE (f)-[r:BELONGS_TO_APPLICATION {role: 'seal_app_ref'}]->(p)
  ON CREATE SET r.first_seen_at    = datetime($loaded_at),
                r.source           = 'manual-csv',
                r.origin           = 'manual-pin',
                r.match_method     = 'manual',
                r.manual_load_file = row.manual_load_file,
                r.authored_by      = row.authored_by
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id

// K10 (§G4/§G5/§G7): a manual pin confirms the port like any other landing
// edge; the authoring steward IS the confirmer, first-confirmation stamps
// stable.
SET p.active_state     = 'confirmed',
    p.confirmed_by     = coalesce(p.confirmed_by, row.authored_by),
    p.confirmed_at     = coalesce(p.confirmed_at, datetime($loaded_at)),
    p.confirmed_run_id = coalesce(p.confirmed_run_id, $run_id)

// §G1 (K11): a manual pin is a confirmed mapping like any other — it authors
// the same app -> orchestrator USES_SOFTWARE edge, one mechanism (§G7).
// Same key + guard discipline as folder_attribution.cypher.
WITH row
MATCH (a:BusinessApplication {app_id: row.app_id})
OPTIONAL MATCH (sp:SoftwareProduct {product_id: $orchestrator_product_id})
FOREACH (_ IN CASE WHEN sp IS NOT NULL THEN [1] ELSE [] END |
  MERGE (a)-[u:USES_SOFTWARE {source: 'app-code-mapping'}]->(sp)
    ON CREATE SET u.first_seen_at = datetime($loaded_at),
                  u.origin        = 'confirmed',
                  u.status        = 'active',
                  u.loader        = $loader,
                  u.confirmed_by  = row.authored_by,
                  u.confirmed_at  = datetime($loaded_at)
  SET u.last_seen_at = datetime($loaded_at),
      u.last_run_id  = $run_id
);
