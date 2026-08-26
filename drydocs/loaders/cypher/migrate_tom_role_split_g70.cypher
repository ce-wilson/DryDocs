// =============================================================================
// migrate_tom_role_split_g70.cypher — one-shot migration for graphs loaded
// BEFORE G70 (gate tom-roles-enumeration-and-cardinality, signed 2026-08-11).
//
// §H5 ASKED "MIGRATION OR REBUILD — SAY WHICH". The answer is: MIGRATION,
// and it is small because NO ATTRIBUTION RE-KEYS. attribution_id embeds the
// CANONICAL role spelling, and G70 froze every pre-G70 canonical spelling
// byte-identical (pinned by tests/unit/test_seal_roles.py), so the §H5
// orphaning hazard — a rename re-keying every contact-side Attribution —
// never arises. What DOES move is the concept side:
//
//   1. the §G9 Operate Manager split: L1/L2 Attributions re-point from the
//      old single operate_manager concept to operate_manager_l1/_l2, and the
//      level property retires (it now IS the concept);
//   2. three previously-UNMAPPED declared names gain their HAD_ROLE edge:
//      bare 'Operate Manager' (the old CASE had no branch for it),
//      'Risk Manager' (§A2: one class, two names -> technology_risk_controls),
//      and 'Chief Business Technologist' (the §G register made it a concept;
//      the 2026-08-06 "no crosswalk, in case it appears" was the pre-gate
//      interim);
//   3. the old scheme's c7.levels annotation retires with the split.
//
// The four classes the pre-G70 code REJECTED outright (Deployment Owner,
// Deployment Information Owner, Application Module Owner, Site Reliability
// Engineer) have NOTHING to migrate: their rows never loaded. They arrive on
// the next source load, which is not a migration.
//
// PRECONDITION: run the seal supplement first (drydocs apply-supplements) so
// the new concepts exist with their declared attributes — the MERGEs below
// create bare nodes only as a fallback.
// Idempotent: re-running finds nothing left to move.
// Venue note (J18): a run of this file names the machine/database it ran on.
// =============================================================================

// -- 1a. L1 re-points --------------------------------------------------------
MATCH (m:Attribution {role_source_name: 'L1 Operate Manager'})
OPTIONAL MATCH (m)-[old:HAD_ROLE]->(:TOMRole {id: 'operate_manager'})
MERGE (l1:TOMRole {id: 'operate_manager_l1'})
MERGE (m)-[new:HAD_ROLE]->(l1)
  ON CREATE SET new.first_seen_at = coalesce(old.first_seen_at, datetime()),
                new.source = 'SEAL'
SET new.last_seen_at = coalesce(old.last_seen_at, datetime()),
    m.unmapped_role = false
REMOVE m.level
DELETE old;

// -- 1b. L2 re-points --------------------------------------------------------
MATCH (m:Attribution {role_source_name: 'L2 Operate Manager'})
OPTIONAL MATCH (m)-[old:HAD_ROLE]->(:TOMRole {id: 'operate_manager'})
MERGE (l2:TOMRole {id: 'operate_manager_l2'})
MERGE (m)-[new:HAD_ROLE]->(l2)
  ON CREATE SET new.first_seen_at = coalesce(old.first_seen_at, datetime()),
                new.source = 'SEAL'
SET new.last_seen_at = coalesce(old.last_seen_at, datetime()),
    m.unmapped_role = false
REMOVE m.level
DELETE old;

// -- 2. previously-unmapped declared names gain their concept ----------------
// (role_source_name held the CANONICAL spelling pre-G70 — the §A4b raw-string
// fix applies to loads AFTER G70, so these literals match what is in the graph)
UNWIND [
  {name: 'Operate Manager',             concept: 'operate_manager'},
  {name: 'Risk Manager',                concept: 'technology_risk_controls'},
  {name: 'Chief Business Technologist', concept: 'chief_business_technologist'}
] AS fix
MATCH (m:Attribution {role_source_name: fix.name})
WHERE m.unmapped_role = true
MERGE (tr:TOMRole {id: fix.concept})
MERGE (m)-[r:HAD_ROLE]->(tr)
  ON CREATE SET r.first_seen_at = datetime(), r.source = 'SEAL'
SET r.last_seen_at = datetime(),
    m.unmapped_role = false
REMOVE m.level;

// -- 3. the old scheme annotation retires with the split ---------------------
MATCH (c:TOMRole {id: 'operate_manager'})
REMOVE c.levels;
