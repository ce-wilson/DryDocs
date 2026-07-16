// =============================================================================
// pat_product_mapping.cypher  —  PAT team-to-product relationships.
//
// For each row in the PAT product mapping CSV this loader:
//   1. Expands comma-separated seal_ids and writes
//      Product -[:HAS_APPLICATION]-> Application for each one.
//   2. Writes DevTeam -[:SUPPORTS {team_type, sponsored}]-> Product (home).
//   3. Optionally writes DevTeam -[:SUPPORTS]-> AreaProduct when
//      area_product_id is present.
//   4. Optionally writes DevTeam -[:SUPPORTS {sponsored:true}]-> <target>
//      when sponsored_product_id is present and differs from product_id.
//
// Prerequisites: Product, DevTeam, and Application nodes must already exist
// (written by products.cypher, dev_teams.cypher, seal_applications.cypher).
// AreaProduct nodes are written by area_products.cypher; this loader will
// MERGE them as a fallback if they haven't been loaded yet.
//
// Parameters: $batch (team_id, product_id, area_product_id?, seal_ids?,
//             team_type, sponsored, sponsored_product_id?),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

// ── 1. HAS_APPLICATION: Product → Application (per SEAL app_id) ─────────────
WITH row,
     [id IN split(coalesce(row.seal_ids, ''), ',') WHERE trim(id) <> ''] AS app_ids
UNWIND CASE WHEN size(app_ids) = 0 THEN [null] ELSE app_ids END AS raw_app_id
FOREACH (_ IN CASE WHEN raw_app_id IS NOT NULL THEN [1] ELSE [] END |
  MERGE (a:BusinessApplication {seal_id: trim(raw_app_id)})
  MERGE (p:Product {product_id: row.product_id})
  MERGE (p)-[r:HAS_APPLICATION]->(a)
    ON CREATE SET r.first_seen_at = datetime($loaded_at),
                  r.source        = 'pat',
                  r.loader        = $loader
  SET r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
)

// ── 2. SUPPORTS: DevTeam → Product (home relationship) ──────────────────────
WITH row
MATCH (dt:DevTeam {team_id: row.team_id})
MATCH (p:Product  {product_id: row.product_id})
MERGE (dt)-[r:SUPPORTS]->(p)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = 'pat',
                r.loader        = $loader
SET r.team_type     = row.team_type,
    r.sponsored     = coalesce(row.sponsored, false),
    r.last_seen_at  = datetime($loaded_at),
    r.last_run_id   = $run_id

// ── 3. SUPPORTS: DevTeam → AreaProduct (when present) ───────────────────────
WITH row, dt
FOREACH (_ IN CASE
                WHEN row.area_product_id IS NOT NULL
                  AND trim(row.area_product_id) <> ''
                THEN [1] ELSE [] END |
  MERGE (ap:AreaProduct {area_product_id: row.area_product_id})
  MERGE (dt)-[r:SUPPORTS]->(ap)
    ON CREATE SET r.first_seen_at = datetime($loaded_at),
                  r.source        = 'pat',
                  r.loader        = $loader
  SET r.team_type    = row.team_type,
      r.sponsored    = coalesce(row.sponsored, false),
      r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
)

// ── 4. SUPPORTS (sponsored): DevTeam → sponsored target (when differs) ──────
WITH row, dt
FOREACH (_ IN CASE
                WHEN row.sponsored_product_id IS NOT NULL
                  AND trim(row.sponsored_product_id) <> ''
                  AND row.sponsored_product_id <> row.product_id
                THEN [1] ELSE [] END |
  MERGE (sp:Product {product_id: row.sponsored_product_id})
  MERGE (dt)-[r:SUPPORTS]->(sp)
    ON CREATE SET r.first_seen_at = datetime($loaded_at),
                  r.source        = 'pat',
                  r.loader        = $loader
  SET r.team_type    = row.team_type,
      r.sponsored    = true,
      r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
);
