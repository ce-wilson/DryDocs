// =============================================================================
// catalog_lobs.cypher  —  Internal product-catalog Lines of Business.
//
// Loads :CatalogLOB nodes and the optional :RECONCILES_TO -> :BusinessSegment
// edge per v3 §B (catalog LOBs may not 1:1 align with corporate segments —
// e.g. AWMCIB).
//
// Parameters:
//   $batch        list of validated dicts (lob_id, code, name,
//                                          reconciles_to_segment,
//                                          reconcile_confidence)
//   $run_id, $loaded_at, $loader, $source_label  — see BaseLoader.
// =============================================================================

UNWIND $batch AS row

MERGE (l:CatalogLOB {lob_id: row.lob_id})
  ON CREATE SET l.created_at = datetime($loaded_at),
                l.source     = 'catalog'
SET l.code         = row.code,
    l.name         = row.name,
    l.last_seen_at = datetime($loaded_at),
    l.last_run_id  = $run_id

// Reconciliation edge (optional — only when the catalog LOB maps to a
// canonical business segment with non-null confidence).
WITH row, l
FOREACH (_ IN CASE
                WHEN row.reconciles_to_segment IS NOT NULL
                  AND trim(row.reconciles_to_segment) <> ''
                THEN [1] ELSE [] END |
  MERGE (s:BusinessSegment {code: row.reconciles_to_segment})
  MERGE (l)-[r:RECONCILES_TO]->(s)
    ON CREATE SET r.first_seen_at = datetime($loaded_at),
                  r.source        = 'catalog',
                  r.loader        = $loader
  SET r.confidence   = row.reconcile_confidence,
      r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
);
