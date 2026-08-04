// =============================================================================
// product_lines.cypher  —  Product Lines under CatalogLOBs.
//
// :ProductLine is keyed on product_line_id and NOTHING here keys on name (C17
// §a): the name is written as an attribute only. This loader therefore requires
// an extract at the product-line grain that carries the id — the PAT team
// report, which projects the product line as a name, cannot feed it and is not
// meant to.
//
// The parent join takes the products.cypher shape (the C22 sweep — C17 fixed
// one loader and deliberately inboxed the rest): OPTIONAL MATCH, the `orphan`
// flag written on EVERY run so a parent that disappears is caught on the next
// load, and the unresolved id KEPT on the node as a queryable property. The
// name SET coalesces so a sparse refresh (ids without enrichment columns)
// updates last-seen bookkeeping without blanking the stored name.
//
// Parameters: $batch (product_line_id, name, parent_lob_id), $run_id,
//             $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row
MERGE (pl:ProductLine {product_line_id: row.product_line_id})
  ON CREATE SET pl.first_seen_at = datetime($loaded_at),
                pl.source     = 'catalog'
SET pl.name         = coalesce(row.name, pl.name),
    pl.last_seen_at = datetime($loaded_at),
    pl.last_run_id  = $run_id

WITH row, pl
OPTIONAL MATCH (l:CatalogLOB {lob_id: row.parent_lob_id})

// ── parent resolved: the hierarchy edge, and the orphan flag cleared ─────────
FOREACH (parent IN CASE WHEN l IS NULL THEN [] ELSE [l] END |
  SET pl.orphan               = false,
      pl.orphan_parent_lob_id = null
  MERGE (parent)-[r:HAS_PRODUCT_LINE]->(pl)
    ON CREATE SET r.first_seen_at = datetime($loaded_at),
                  r.source        = 'catalog',
                  r.loader        = $loader
  SET r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
)

// ── parent missing: keep the product line, KEEP THE UNRESOLVED ID ───────────
FOREACH (_ IN CASE WHEN l IS NULL THEN [1] ELSE [] END |
  SET pl.orphan               = true,
      pl.orphan_parent_lob_id = row.parent_lob_id
);
