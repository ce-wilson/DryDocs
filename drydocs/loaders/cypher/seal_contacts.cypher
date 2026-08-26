// =============================================================================
// seal_contacts.cypher
//
// Loads SEAL Contact extract (long format) for the roles NOT embedded in
// DECO_SEAL_APP_INFO. The three contacts embedded in DECO (App Owner, CTO,
// PIO) are loaded by seal_applications.cypher directly from the application
// row — this loader is for everything else.
//
// K4 (gate 2026-07-10 §B/§C): writes the qualified-attribution shape
// (Attribution + HAD_ROLE → TOMRole) instead of the deprecated
// Membership/Role triple.
//
// G70 (gate tom-roles-enumeration-and-cardinality, signed 2026-08-11): the
// role-name -> concept crosswalk that lived here as a 4-branch CASE — surface
// (iii) of §A8's four hardcoded lists — is GONE. The model computes
// row.tom_role_id from the DECLARED vocabulary
// (config/taxonomy/tom-role-vocabulary.yaml via
// drydocs_core.ontology.tom_role_vocabulary), so this file no longer holds a
// role list at all. An UNDECLARED name still loads, flagged
// unmapped_role=true — surfaced for review, never guessed into a concept —
// and row.role_source_name preserves the source's RAW spelling verbatim
// (§A4b) while row.role_name (the canonical spelling) keys the
// attribution_id exactly as before (§H5: no re-key; the identity gate's §D2
// 4-part shape is untouched). The pre-G70 level property retired with the
// Operate Manager split (§G9) — see migrate_tom_role_split_g70.cypher for
// already-loaded graphs.
//
// Parameters: $batch (SealContactRow dicts with app_id, role_name,
//             role_source_name, tom_role_id, employee_sid, employee_name,
//             employee_email),
//             $run_id, $loaded_at, $loader.
// =============================================================================

UNWIND $batch AS row

// IDENTITY KEY (gate business-application-identity §C1) — the canonical node is keyed
// on app_id, which is what the contact-extract row already called it.
MATCH (a:BusinessApplication {app_id: row.app_id})

MERGE (e:Employee {employee_id: row.employee_sid})
  ON CREATE SET e.first_seen_at = datetime($loaded_at),
                e.source     = 'SEAL'
SET e.full_name    = coalesce(row.employee_name, e.full_name),
    e.email        = coalesce(row.employee_email, e.email),
    e.last_seen_at = datetime($loaded_at),
    e.last_run_id  = $run_id

// ---- role-name -> concept: DECLARED, computed by the model (G70 §A8) -------
MERGE (m:Attribution {
    attribution_id: row.app_id + '|SEAL|' + row.role_name + '|' + row.employee_sid
})
  ON CREATE SET m.source     = 'SEAL',
                m.valid_from = date(),
                m.valid_to   = null,
                m.first_seen_at = datetime($loaded_at)
SET m.last_seen_at     = datetime($loaded_at),
    m.last_run_id      = $run_id,
    // the RAW source spelling, verbatim (§A4b) — the canonical spelling lives
    // in the attribution_id segment and on the HAD_ROLE concept
    m.role_source_name = row.role_source_name,
    m.unmapped_role    = row.tom_role_id IS NULL

MERGE (a)-[q:QUALIFIED_ATTRIBUTION]->(m)
  ON CREATE SET q.first_seen_at = datetime($loaded_at), q.source = 'SEAL'
SET q.last_seen_at = datetime($loaded_at)

MERGE (m)-[r2:HAS_AGENT]->(e)
  ON CREATE SET r2.first_seen_at = datetime($loaded_at), r2.source = 'SEAL'
SET r2.last_seen_at = datetime($loaded_at)

// HAD_ROLE only for DECLARED names — never mint concepts here
FOREACH (rid IN CASE WHEN row.tom_role_id IS NOT NULL THEN [row.tom_role_id] ELSE [] END |
  MERGE (tr:TOMRole {id: rid})
  MERGE (m)-[r1:HAD_ROLE]->(tr)
    ON CREATE SET r1.first_seen_at = datetime($loaded_at), r1.source = 'SEAL'
  SET r1.last_seen_at = datetime($loaded_at)
)

WITH m
MATCH (run:JobRun {run_id: $run_id})
MERGE (m)-[r3:WAS_GENERATED_BY {source: 'SEAL'}]->(run)
  ON CREATE SET r3.first_seen_at = datetime($loaded_at)
SET r3.last_seen_at = datetime($loaded_at);
