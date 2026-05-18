// =============================================================================
// seal_contacts.cypher
//
// Loads SEAL Contact Data into the W3C ORG Membership pattern (v3 §F.3):
//
//     (:Application)-[:HAS_MEMBERSHIP]->(:Membership)
//                                          -[:OF_ROLE]->(:Role)
//                                          -[:HELD_BY]->(:Employee)
//
// The membership_id is deterministic: seal_id|SEAL|role_name|employee_id.
// Re-running with the same row is a no-op (MERGE).
//
// Roles are constrained to the eight-role vocabulary seeded by M0;
// pydantic SealContactRow rejects rows whose role_name doesn't canonicalize
// to one of the SEAL five.
//
// Parameters (passed by BaseLoader._flush):
//   $batch       list of validated dicts (keys: seal_id, role_name,
//                                         employee_id, employee_name,
//                                         employee_email)
//   $run_id      UUID of this loader's :JobRun
//   $loaded_at   ISO datetime string
//   $loader      loader version tag
// =============================================================================

UNWIND $batch AS row

MATCH (a:Application {seal_id: row.seal_id})
MATCH (r:Role {name: row.role_name})

// Employee upsert (or create if PAT/SEAL referenced before HR feed lands)
MERGE (e:Employee {employee_id: row.employee_id})
  ON CREATE SET e.created_at = datetime($loaded_at),
                e.source     = 'SEAL'
SET e.full_name    = coalesce(row.employee_name, e.full_name),
    e.email        = coalesce(row.employee_email, e.email),
    e.last_seen_at = datetime($loaded_at),
    e.last_run_id  = $run_id

// Reified Membership: deterministic id keeps re-runs idempotent.
MERGE (a)-[:HAS_MEMBERSHIP]->(m:Membership {
    membership_id: row.seal_id + '|SEAL|' + row.role_name + '|' + row.employee_id
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

// Provenance: this run touched this Membership.
WITH m
MATCH (run:JobRun {run_id: $run_id})
MERGE (m)-[r3:WAS_GENERATED_BY {source: 'SEAL'}]->(run)
  ON CREATE SET r3.first_seen_at = datetime($loaded_at)
SET r3.last_seen_at = datetime($loaded_at);
