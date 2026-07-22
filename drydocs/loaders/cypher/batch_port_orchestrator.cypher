// =============================================================================
// batch_port_orchestrator.cypher — declared batch-port orchestrator migration
// (backlog C14; executes the C12 platforms-taxonomy sign-off, 2026-07-21).
//
// MATCH-only on BOTH endpoints: apps come from seal_applications, products
// from load-software-registry — this pass creates neither; a row whose app or
// product is absent writes nothing (run those loaders first).
//
// The edge MERGE is KEYED on {source: 'batch-port'} so the declared-
// orchestrator edge coexists with (never collides with) the DRYDOCS-SELF
// stack edges (source: 'registry', software_registry.cypher) and the future
// plan-07 'controlm-cmdline' detections on the same USES_SOFTWARE type.
//
// Unmapped rows (product_id null — the platforms.yaml crosswalk had no
// software_registry_ref for the string): the raw string is preserved and
// flagged on the app node (the seal_contacts unmapped_role precedent) —
// surfaced for review, never guessed into a product. A later run that maps
// the string clears the flag (idempotent, re-run safe).
//
// Parameters: $batch (seal_id, orchestrator_raw, product_id),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row
MATCH (a:BusinessApplication {seal_id: row.seal_id})
OPTIONAL MATCH (sp:SoftwareProduct {product_id: row.product_id})
FOREACH (_ IN CASE WHEN sp IS NOT NULL THEN [1] ELSE [] END |
  MERGE (a)-[u:USES_SOFTWARE {source: 'batch-port'}]->(sp)
    ON CREATE SET u.first_seen_at = datetime($loaded_at),
                  u.status        = 'active',
                  u.loader        = $loader
  SET u.orchestrator_raw = row.orchestrator_raw,
      u.last_seen_at     = datetime($loaded_at),
      u.last_run_id      = $run_id
)
SET a.batch_orchestrator_raw          = row.orchestrator_raw,
    a.batch_orchestrator_unmapped     = CASE WHEN sp IS NULL THEN true ELSE null END,
    a.batch_orchestrator_last_run_id  = $run_id;
