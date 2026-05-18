// =============================================================================
// seal_applications.cypher
//
// Loads SEAL Application Data into :Application + :EventProcessing +
// :BatchProcessing ports per v3 §C two-port pattern.
//
// Parameters (passed by BaseLoader._flush):
//   $batch        list of validated dicts (keys: seal_id, name,
//                                          deployment_module, data_retention,
//                                          risk_level, sox_governed, status)
//   $run_id       UUID of this loader's :JobRun
//   $loaded_at    ISO datetime string
//   $loader       loader version tag
//   $source_label 'csv' (phase 1) or 'oracle' (phase 2)
// =============================================================================

UNWIND $batch AS row

// Application upsert
MERGE (a:Application {seal_id: row.seal_id})
  ON CREATE SET a.created_at = datetime($loaded_at),
                a.source     = 'SEAL'
SET a.name              = row.name,
    a.deployment_module = row.deployment_module,
    a.data_retention    = row.data_retention,
    a.risk_level        = row.risk_level,
    a.sox_governed      = row.sox_governed,
    a.status            = row.status,
    a.last_seen_at      = datetime($loaded_at),
    a.last_run_id       = $run_id

// Two-port pattern (v3 §C): always create both, mark active=false until
// observed via downstream loaders (BMC for batch, future API loader for event).
MERGE (ep:Port:EventProcessing {parent_seal_id: row.seal_id, kind: 'EventProcessing'})
  ON CREATE SET ep.created_at = datetime($loaded_at),
                ep.active     = false
SET ep.last_seen_at = datetime($loaded_at)

MERGE (bp:Port:BatchProcessing {parent_seal_id: row.seal_id, kind: 'BatchProcessing'})
  ON CREATE SET bp.created_at = datetime($loaded_at),
                bp.active     = false
SET bp.last_seen_at = datetime($loaded_at)

MERGE (a)-[:HAS_PORT]->(ep)
MERGE (a)-[:HAS_PORT]->(bp)

// Provenance: this run touched this Application.
WITH a
MATCH (run:JobRun {run_id: $run_id})
MERGE (a)-[r:WAS_GENERATED_BY {source: 'SEAL'}]->(run)
  ON CREATE SET r.first_seen_at = datetime($loaded_at)
SET r.last_seen_at = datetime($loaded_at);
