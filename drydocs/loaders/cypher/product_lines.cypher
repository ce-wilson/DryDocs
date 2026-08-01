// =============================================================================
// product_lines.cypher  —  Product Lines under CatalogLOBs.
//
// :ProductLine is keyed on product_line_id and NOTHING here keys on name (C17
// §a): the name is written as an attribute only. This loader therefore requires
// an extract at the product-line grain that carries the id — the PAT team
// report, which projects the product line as a name, cannot feed it and is not
// meant to.
//
// The parent MATCH below is the same silent-miss shape products.cypher just
// fixed; sweeping the remaining hierarchy joins is inboxed rather than done
// here, so one item's authority does not quietly change four loaders.
//
// Parameters: $batch (product_line_id, name, parent_lob_id), $run_id,
//             $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row
MERGE (pl:ProductLine {product_line_id: row.product_line_id})
  ON CREATE SET pl.first_seen_at = datetime($loaded_at),
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
