// =============================================================================
// pat_team_roles.cypher  —  PAT human role assignments on DevTeams.
//
// Writes the org:Membership n-ary pattern for PAT team staffing:
//
//   DevTeam -[:HAS_MEMBERSHIP]-> Membership -[:OF_ROLE]-> Role
//                                            -[:HELD_BY]-> Employee
//
// This mirrors the SEAL pattern (Application → Membership) but sourced from
// PAT data.  Role nodes must already exist (seeded by
// catalog_ontology_supplement.cypher).  Employee nodes must already exist
// (written by seal_applications.cypher).
//
// Parameters: $batch (team_id, employee_sid, role_id, valid_from?, valid_to?),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

MATCH (dt:DevTeam  {team_id:   row.team_id})
MATCH (r:Role      {role_id:   row.role_id})
MATCH (e:Employee  {employee_id: row.employee_sid})

MERGE (m:Membership {membership_id: row.team_id + '_' + row.employee_sid + '_' + row.role_id})
  ON CREATE SET m.first_seen_at = datetime($loaded_at),
                m.source     = 'pat'
SET m.valid_from   = row.valid_from,
    m.valid_to     = row.valid_to,
    m.last_seen_at = datetime($loaded_at),
    m.last_run_id  = $run_id

MERGE (dt)-[:HAS_MEMBERSHIP]->(m)
MERGE (m)-[:OF_ROLE]->(r)
MERGE (m)-[:HELD_BY]->(e);
