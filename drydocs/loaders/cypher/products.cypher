// =============================================================================
// products.cypher  —  Products under ProductLines.
//
// The product-line join is BY ID and never by name (C17 §a, gate
// `seal-app-ref-edge-reshape` §G6-RIDER): every catalog grain carries a numeric
// id at source, so an extract that projects the product line as a name only is
// an extract to fix, not a key to invent.
//
// Having ruled the join, the join must not fail SILENTLY either — otherwise the
// silence has just moved from "which key?" to "did it match?". This used to be
// a hard MATCH placed AFTER the Product MERGE, so a parent id with no loaded
// :ProductLine produced a real Product node with no parent edge and
// `orphan: false` still sitting on it from ON CREATE — an unparented product
// that reported itself as fine, and an `orphan` flag nothing could ever set
// true. Now the miss is recorded on the node: `orphan` is written on EVERY run
// (so a parent that disappears is caught on the next load, not only on create)
// and `orphan_parent_product_line_id` keeps the id that failed to resolve, so
// the gap is a query rather than a diff of expected-vs-actual counts.
//
// The name SET coalesces (C22 §b): a sparse refresh — ids without enrichment
// columns — updates last-seen bookkeeping without blanking the stored name.
//
// Parameters: $batch (product_id, name, parent_product_line_id), $run_id,
//             $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row
MERGE (p:Product {product_id: row.product_id})
  ON CREATE SET p.first_seen_at = datetime($loaded_at),
                p.source     = 'catalog'
SET p.name         = coalesce(row.name, p.name),
    p.last_seen_at = datetime($loaded_at),
    p.last_run_id  = $run_id

WITH row, p
OPTIONAL MATCH (pl:ProductLine {product_line_id: row.parent_product_line_id})

// ── parent resolved: the hierarchy edge, and the orphan flag cleared ─────────
FOREACH (parent IN CASE WHEN pl IS NULL THEN [] ELSE [pl] END |
  SET p.orphan                        = false,
      p.orphan_parent_product_line_id = null
  MERGE (parent)-[r:HAS_PRODUCT]->(p)
    ON CREATE SET r.first_seen_at = datetime($loaded_at),
                  r.source        = 'catalog',
                  r.loader        = $loader
  SET r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
)

// ── parent missing: keep the product, KEEP THE UNRESOLVED ID ────────────────
FOREACH (_ IN CASE WHEN pl IS NULL THEN [1] ELSE [] END |
  SET p.orphan                        = true,
      p.orphan_parent_product_line_id = row.parent_product_line_id
);
