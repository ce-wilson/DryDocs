// =============================================================================
// migrate_runs_on_to_scheduled_on.cypher  —  (D1 / consolidated-plan B.1)
//
// ONE-TIME, IDEMPOTENT migration. Renames the folder->server edge RUNS_ON to
// SCHEDULED_ON on any pre-existing graph (controlm_folders.cypher now writes
// SCHEDULED_ON directly). Safe to re-run: if no RUNS_ON edges remain it is a no-op,
// and re-running over already-migrated edges just re-MERGEs SCHEDULED_ON.
//
// Run once per environment after deploying the loader change.
// (RUNS_ON is reassigned to execution-host placement with a role property — see
// relationship_vocabulary.yaml scheduler_runs_on_agent_host / m3_runs_on_etl_host — so
// this only touches ControlMFolder->ControlMServer edges.)
// =============================================================================

MATCH (f:ControlMFolder)-[r:RUNS_ON]->(srv:ControlMServer)
MERGE (f)-[s:SCHEDULED_ON]->(srv)
  ON CREATE SET s.since  = r.since,
                s.source = r.source,
                s.loader = r.loader
SET s.last_seen_at = r.last_seen_at,
    s.last_run_id  = r.last_run_id
DELETE r;
