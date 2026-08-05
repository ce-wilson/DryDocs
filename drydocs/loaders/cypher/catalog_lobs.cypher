// =============================================================================
// catalog_lobs.cypher  —  Internal product-catalog Lines of Business.
//
// Loads :CatalogLOB nodes and the optional :RECONCILES_TO -> :BusinessSegment
// edge per v3 §B (catalog LOBs may not 1:1 align with corporate segments —
// e.g. AWMCIB).
//
// The reconciliation target is resolved through the precedence chain
// (config/precedence.yaml) by CatalogLOBsLoader, NOT taken raw from the catalog
// column. The winning authority is recorded on the edge (r.authority) and any
// losing authorities are kept as aliases (r.aliases — skos:closeMatch, never
// dropped; see precedence.yaml#conflict_policy). See drydocs/precedence.py.
//
// Parameters:
//   $batch        list of validated dicts (lob_id, code, name,
//                                          reconciles_to_segment,   // resolved winner
//                                          reconcile_confidence,    // winner's confidence
//                                          reconcile_authority,     // winning authority id
//                                          reconcile_aliases)       // [str] losing claims
//   $run_id, $loaded_at, $loader, $source_label  — see BaseLoader.
// =============================================================================

UNWIND $batch AS row

MERGE (l:CatalogLOB {lob_id: row.lob_id})
  ON CREATE SET l.first_seen_at = datetime($loaded_at),
                l.source     = 'catalog'
// C24 (extends C22 §b to this loader): a SPARSE refresh must not blank what a
// full extract loaded. The pre-C24 form was `SET l.code = row.code, l.name =
// row.name` — and this file lost data TODAY rather than hypothetically, because
// CatalogLOBRow already declared both fields `str | None`: an extract carrying
// lob_id alone wrote null over a stored code and name on EVERY refresh.
SET l.code         = coalesce(row.code, l.code),
    l.name         = coalesce(row.name, l.name),
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
      r.authority    = row.reconcile_authority,   // winning precedence authority
      r.aliases      = row.reconcile_aliases,      // losing claims (skos:closeMatch)
      r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
);
