// =============================================================================
// seal_contacts.cypher
//
// Loads SEAL Contact extract (long format) for the roles NOT embedded in
// DECO_SEAL_APP_INFO: Backup Information Owner, Design Authority, Chief
// Business Technologist, L1 / L2 Operate Manager, Backup Application
// Owner, Risk Manager.
//
// The three contacts embedded in DECO (App Owner, CTO, PIO) are loaded
// by seal_applications.cypher directly from the application row — this
// loader is for everything else.
//
// K4 (gate 2026-07-10 §B/§C): writes the qualified-attribution shape
// (Attribution + HAD_ROLE → TOMRole) instead of the deprecated
// Membership/Role triple. Role names outside the fixed 7-concept tom_roles
// scheme are LOADED but flagged unmapped_role=true with role_source_name
// preserved — surfaced for review, never guessed into a concept. L1/L2
// Operate Manager both map to operate_manager with level on the Attribution.
//
// Parameters: $batch (SealContactRow dicts with app_id, role_name,
//             employee_sid, employee_name, employee_email),
//             $run_id, $loaded_at, $loader.
// =============================================================================

UNWIND $batch AS row

MATCH (a:BusinessApplication {seal_id: row.app_id})

MERGE (e:Employee {employee_id: row.employee_sid})
  ON CREATE SET e.created_at = datetime($loaded_at),
                e.source     = 'SEAL'
SET e.full_name    = coalesce(row.employee_name, e.full_name),
    e.email        = coalesce(row.employee_email, e.email),
    e.last_seen_at = datetime($loaded_at),
    e.last_run_id  = $run_id

// ---- role-name -> tom_roles concept crosswalk (gate §B fixed set) ----------
WITH a, e, row,
     CASE row.role_name
       WHEN 'Backup Information Owner' THEN 'backup_information_owner'
       WHEN 'Design Authority'         THEN 'design_authority'
       WHEN 'L1 Operate Manager'       THEN 'operate_manager'
       WHEN 'L2 Operate Manager'       THEN 'operate_manager'
       ELSE null
     END AS tom_role_id,
     CASE row.role_name
       WHEN 'L1 Operate Manager' THEN 'L1'
       WHEN 'L2 Operate Manager' THEN 'L2'
       ELSE null
     END AS om_level

MERGE (m:Attribution {
    attribution_id: row.app_id + '|SEAL|' + row.role_name + '|' + row.employee_sid
})
  ON CREATE SET m.source     = 'SEAL',
                m.valid_from = date(),
                m.valid_to   = null,
                m.created_at = datetime($loaded_at)
SET m.last_seen_at     = datetime($loaded_at),
    m.last_run_id      = $run_id,
    m.role_source_name = row.role_name,
    m.level            = om_level,
    m.unmapped_role    = tom_role_id IS NULL

MERGE (a)-[q:QUALIFIED_ATTRIBUTION]->(m)
  ON CREATE SET q.first_seen_at = datetime($loaded_at), q.source = 'SEAL'
SET q.last_seen_at = datetime($loaded_at)

MERGE (m)-[r2:HAS_AGENT]->(e)
  ON CREATE SET r2.first_seen_at = datetime($loaded_at), r2.source = 'SEAL'
SET r2.last_seen_at = datetime($loaded_at)

// HAD_ROLE only for names inside the fixed scheme — never mint concepts here
FOREACH (rid IN CASE WHEN tom_role_id IS NOT NULL THEN [tom_role_id] ELSE [] END |
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
