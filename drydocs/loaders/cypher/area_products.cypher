// =============================================================================
// area_products.cypher  —  Area Product Groups (Team of Teams).
//
// Creates AreaProduct nodes and wires them under their parent Product via
// HAS_AREA_PRODUCT.  That is ALL it writes.
//
// It does NOT anchor DevTeams under their AreaProduct. This header claimed it
// did ("optionally anchors DevTeams ... via HAS_DEV_TEAM") and the body never
// has; the only HAS_DEV_TEAM writer is dev_teams.cypher, parented on :Product.
// Corrected at G91 (2026-08-18), which deprecated catalog_area_product_has_dev_team
// as redundant — DevTeam<->AreaProduct is already carried by the ACTIVE
// catalog_supports_area_product (DevTeam -[:SUPPORTS]-> AreaProduct, written by
// pat_product_mapping.cypher). Do not add the second hop back here without a new
// proposal through docs/RELATIONSHIP_GUIDE.md.
//
// The parent join takes the products.cypher shape (the C22 sweep): OPTIONAL
// MATCH, the `orphan` flag written on EVERY run so a parent that disappears is
// caught on the next load, and the unresolved id KEPT on the node. The name
// SET coalesces so a sparse refresh does not blank the stored name.
//
// Parameters: $batch (area_product_id, name, parent_product_id),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row
MERGE (ap:AreaProduct {area_product_id: row.area_product_id})
  ON CREATE SET ap.first_seen_at = datetime($loaded_at),
                ap.source     = 'catalog'
SET ap.name         = coalesce(row.name, ap.name),
    ap.last_seen_at = datetime($loaded_at),
    ap.last_run_id  = $run_id

WITH row, ap
OPTIONAL MATCH (p:Product {product_id: row.parent_product_id})

// ── parent resolved: the hierarchy edge, and the orphan flag cleared ─────────
FOREACH (parent IN CASE WHEN p IS NULL THEN [] ELSE [p] END |
  SET ap.orphan                   = false,
      ap.orphan_parent_product_id = null
  MERGE (parent)-[r:HAS_AREA_PRODUCT]->(ap)
    ON CREATE SET r.first_seen_at = datetime($loaded_at),
                  r.source        = 'catalog',
                  r.loader        = $loader
  SET r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
)

// ── parent missing: keep the area product, KEEP THE UNRESOLVED ID ───────────
FOREACH (_ IN CASE WHEN p IS NULL THEN [1] ELSE [] END |
  SET ap.orphan                   = true,
      ap.orphan_parent_product_id = row.parent_product_id
);
