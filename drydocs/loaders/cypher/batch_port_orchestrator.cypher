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
// PREREQ (Q8 family, 2026-07-27). MATCH-only cuts both ways: an app registry
// that is absent ENTIRELY makes every row's MATCH fail, and a product registry
// that is absent entirely makes the FOREACH guard drop every edge — either way
// the run reported OK having written nothing. Both are now refused BEFORE the
// load in BatchPortOrchestratorLoader._assert_endpoint_registries_present, and
// the per-row survivors are reported after it. The check cannot live here: a
// template that runs per BATCH cannot tell "this row's id is wrong" from "the
// registry is not in this database". Read that method before re-pointing this
// loader at another database (a relationship cannot span databases).
//
// The unmapped flag is keyed on row.product_id — the CROSSWALK result — not on
// sp, the node lookup. Keyed on sp (as it was until 2026-07-27) an absent or
// incomplete registry silently relabelled correctly-mapped apps as "unmapped in
// platforms.yaml", contradicting the CLI coverage report on the same run. The
// registry-gap case is a LOAD problem, not a CONFIG problem, and is reported by
// the loader instead of being written into the graph as the wrong diagnosis.
//
// Parameters: $batch (seal_id, orchestrator_raw, product_id),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row
// IDENTITY KEY (gate business-application-identity §C1) — the canonical node is keyed
// on app_id; the batch-port row field keeps its own name.
MATCH (a:BusinessApplication {app_id: row.seal_id})
OPTIONAL MATCH (sp:SoftwareProduct {product_id: row.product_id})
FOREACH (_ IN CASE WHEN sp IS NOT NULL THEN [1] ELSE [] END |
  MERGE (a)-[u:USES_SOFTWARE {source: 'batch-port'}]->(sp)
    ON CREATE SET u.first_seen_at = datetime($loaded_at),
                  u.status        = 'active',
                  u.loader        = $loader
  // §G2 (gate seal-app-ref-edge-reshape, 2026-08-03): this edge is the SEAL
  // DECLARATION, kept origin=declared — a steward confirmation supersedes it
  // by authoring its own {source: 'app-code-mapping', origin: 'confirmed'}
  // edge (folder_attribution.cypher); no cleanup sweep, nothing overwritten.
  SET u.origin           = coalesce(u.origin, 'declared'),
      u.orchestrator_raw = row.orchestrator_raw,
      u.last_seen_at     = datetime($loaded_at),
      u.last_run_id      = $run_id
)
SET a.batch_orchestrator_raw          = row.orchestrator_raw,
    a.batch_orchestrator_unmapped     = CASE WHEN row.product_id IS NULL THEN true ELSE null END,
    a.batch_orchestrator_last_run_id  = $run_id;
