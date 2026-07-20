// ============================================================================
// migrate_pat_alignment_c9.cypher — C9 gate (2026-07-18, "PAT reconcile").
//
// One-time cleanup after the pat_product_mapping.cypher reshape. Idempotent —
// re-running finds nothing left to delete. Follows the D1/K4 precedent
// (migrate_runs_on_to_scheduled_on.cypher / migrate_develops_to_was_attributed_to.cypher).
//
// 1. The pre-C9 loader wrote DevTeam-[:SUPPORTS]->Product unconditionally
//    (the 2026-06-21-deprecated catalog_supports shape). Under the C9 ladder
//    the home-product edge survives ONLY as the sole assertion — so drop the
//    unsponsored team->Product edge wherever the team also carries an
//    unsponsored team->AreaProduct alignment (the C5 join-restatement case).
// 2. The pre-C9 loader also wrote Product-[:HAS_APPLICATION]->App from the
//    TEAM row's seal_ids (mis-attribution; catalog_has_application stays
//    status: planned until a product-scoped extract exists). Drop the
//    pat-sourced ones; a product-scoped loader re-creates them properly later.
// ============================================================================

MATCH (dt:DevTeam)-[r:SUPPORTS]->(:Product)
WHERE r.source = 'pat'
  AND coalesce(r.sponsored, false) = false
  AND EXISTS {
    MATCH (dt)-[r2:SUPPORTS]->(:AreaProduct)
    WHERE coalesce(r2.sponsored, false) = false
  }
DELETE r;

MATCH (:Product)-[r:HAS_APPLICATION]->(:BusinessApplication)
WHERE r.source = 'pat'
DELETE r;
