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
// Parameters: $batch (SealContactRow dicts with app_id, role_name,
//             employee_sid, employee_name, employee_email),
//             $run_id, $loaded_at, $loader.
// =============================================================================

UNWIND $batch AS row

MATCH (a:Application {seal_id: row.app_id})
MATCH (r:Role {name: row.role_name})

MERGE (e:Employee {employee_id: row.employee_sid})
  ON CREATE SET e.created_at = datetime($loaded_at),
                e.source     = 'SEAL'
SET e.full_name    = coalesce(row.employee_name, e.full_name),
    e.email        = coalesce(row.employee_email, e.email),
    e.last_seen_at = datetime($loaded_at),
    e.last_run_id  = $run_id

MERGE (a)-[:HAS_MEMBERSHIP]->(m:Membership {
    membership_id: row.app_id + '|SEAL|' + row.role_name + '|' + row.employee_sid
})
  ON CREATE SET m.source     = 'SEAL',
                m.valid_from = date(),
                m.valid_to   = null,
                m.created_at = datetime($loaded_at)
SET m.last_seen_at = datetime($loaded_at),
    m.last_run_id  = $run_id

MERGE (m)-[r1:OF_ROLE]->(r)
  ON CREATE SET r1.first_seen_at = datetime($loaded_at), r1.source = 'SEAL'
SET r1.last_seen_at = datetime($loaded_at)

MERGE (m)-[r2:HELD_BY]->(e)
  ON CREATE SET r2.first_seen_at = datetime($loaded_at), r2.source = 'SEAL'
SET r2.last_seen_at = datetime($loaded_at)

WITH m
MATCH (run:JobRun {run_id: $run_id})
MERGE (m)-[r3:WAS_GENERATED_BY {source: 'SEAL'}]->(run)
  ON CREATE SET r3.first_seen_at = datetime($loaded_at)
SET r3.last_seen_at = datetime($loaded_at);
