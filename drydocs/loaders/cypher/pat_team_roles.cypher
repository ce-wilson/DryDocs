// =============================================================================
// pat_team_roles.cypher  —  PAT human role assignments on DevTeams.
//
// Writes the QUALIFIED-ATTRIBUTION shape (G91, 2026-08-18):
//
//   DevTeam -[:QUALIFIED_ATTRIBUTION]-> Attribution -[:HAD_ROLE]->  Role
//                                                   -[:HAS_AGENT]-> Employee
//
// RE-SHAPED FROM the reified org:Membership pattern this file used to write
// (DevTeam -[:HAS_MEMBERSHIP]-> Membership -[:OF_ROLE|:HELD_BY]->). That shape
// was the LAST HOLDOUT: SEAL moved at K4 (2026-07-10) and the PAT product /
// area-product side at K5 (2026-07-20), so one employee was reaching the graph
// by two different routes. Now all four families -- SEAL applications, PAT
// products, PAT dev teams and ITSM support groups -- hang people off ONE
// Attribution -[:HAS_AGENT]-> Employee hop.
//
// HAS_AGENT IS REUSED, NOT TWINNED: that triple is identical to the SEAL one and
// the C8 meta-graph refuses ambiguous duplicate (from, label, to) triples, so the
// vocabulary registers only the two legs that DIFFER
// (catalog_dev_team_qualified_attribution, catalog_dev_team_attribution_had_role).
//
// attribution_id FOLLOWS THE SEAL IDIOM -- subject|FAMILY|role|person -- and is
// derived entirely from the row, never from a counter. That is what makes a
// re-run idempotent, and it matters here because the estate is TRUNCATE-AND-RELOAD:
// the key has to be reproducible from the source, not from load order.
//
// Role nodes must already exist (seeded by catalog_ontology_supplement.cypher).
// Employee nodes must already exist (written by seal_applications.cypher) -- the
// MATCH is strict on purpose, so a role assignment for an unknown SID is dropped
// loudly rather than minting a stub person.
//
// Parameters: $batch (team_id, employee_sid, role_id, valid_from?, valid_to?),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

MATCH (dt:DevTeam  {team_id:     row.team_id})
MATCH (r:Role      {role_id:     row.role_id})
MATCH (e:Employee  {employee_id: row.employee_sid})

MERGE (att:Attribution {
    attribution_id: row.team_id + '|PAT|' + row.role_id + '|' + row.employee_sid
})
  ON CREATE SET att.source        = 'pat',
                att.first_seen_at = datetime($loaded_at)
SET att.valid_from   = row.valid_from,
    att.valid_to     = row.valid_to,
    att.last_seen_at = datetime($loaded_at),
    att.last_run_id  = $run_id

MERGE (dt)-[:QUALIFIED_ATTRIBUTION]->(att)
MERGE (att)-[:HAD_ROLE]->(r)
MERGE (att)-[:HAS_AGENT]->(e);
