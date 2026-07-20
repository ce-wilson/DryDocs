// =============================================================================
// products.cypher  —  Products under ProductLines.
// Parameters: $batch (product_id, name, parent_product_line_id), $run_id,
//             $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row
MERGE (p:Product {product_id: row.product_id})
  ON CREATE SET p.created_at = datetime($loaded_at),
                p.source     = 'catalog',
                p.orphan     = false
SET p.name         = row.name,
    p.last_seen_at = datetime($loaded_at),
    p.last_run_id  = $run_id

WITH row, p
MATCH (pl:ProductLine {product_line_id: row.parent_product_line_id})
MERGE (pl)-[r:HAS_PRODUCT]->(p)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = 'catalog',
                r.loader        = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id;
