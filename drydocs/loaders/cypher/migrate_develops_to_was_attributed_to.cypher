// ============================================================================
// migrate_develops_to_was_attributed_to.cypher — K4 clause 5 (gate 2026-07-10 §E)
//
// Flips the pre-K4 (:DevTeam)-[:DEVELOPS]->(:BusinessApplication) edges to the
// PROV-valid inverse (:BusinessApplication)-[:WAS_ATTRIBUTED_TO {role:
// developed_by}]->(:DevTeam). Idempotent — re-running MERGEs the same edges
// and finds no remaining DEVELOPS to delete. Follows the D1 precedent
// (migrate_runs_on_to_scheduled_on.cypher).
// Note: matches the OLD :Application label too, for graphs bootstrapped
// before the K4 label normalization.
// ============================================================================

MATCH (d:DevTeam)-[old:DEVELOPS]->(a)
WHERE a:BusinessApplication OR a:Application
MERGE (a)-[n:WAS_ATTRIBUTED_TO {role: 'developed_by'}]->(d)
  ON CREATE SET n = properties(old), n.role = 'developed_by',
                n.migrated_from = 'DEVELOPS', n.migrated_at = datetime()
DELETE old;
