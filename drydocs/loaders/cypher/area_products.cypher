// =============================================================================
// area_products.cypher  —  Area Product Groups (Team of Teams).
//
// Creates AreaProduct nodes and wires them under their parent Product via
// HAS_AREA_PRODUCT.  Optionally anchors DevTeams under their AreaProduct
// via HAS_DEV_TEAM when area_product_id is present on DevTeamRow (written
// by this loader on a second pass, or via pat_product_mapping).
//
// Parameters: $batch (area_product_id, name, parent_product_id),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row
MERGE (ap:AreaProduct {area_product_id: row.area_product_id})
  ON CREATE SET ap.first_seen_at = datetime($loaded_at),
                ap.source     = 'catalog'
SET ap.name         = row.name,
    ap.last_seen_at = datetime($loaded_at),
    ap.last_run_id  = $run_id

WITH row, ap
MATCH (p:Product {product_id: row.parent_product_id})
MERGE (p)-[r:HAS_AREA_PRODUCT]->(ap)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = 'catalog',
                r.loader        = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id;
