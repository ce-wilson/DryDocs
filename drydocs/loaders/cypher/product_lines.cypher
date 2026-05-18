// =============================================================================
// product_lines.cypher  —  Product Lines under CatalogLOBs.
// Parameters: $batch (product_line_id, name, parent_lob_id), $run_id,
//             $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row
MERGE (pl:ProductLine {product_line_id: row.product_line_id})
  ON CREATE SET pl.created_at = datetime($loaded_at),
                pl.source     = 'catalog'
SET pl.name         = row.name,
    pl.last_seen_at = datetime($loaded_at),
    pl.last_run_id  = $run_id

WITH row, pl
MATCH (l:CatalogLOB {lob_id: row.parent_lob_id})
MERGE (l)-[r:HAS_PRODUCT_LINE]->(pl)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = 'catalog',
                r.loader        = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id;
