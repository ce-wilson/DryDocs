// =============================================================================
// pat_product_mapping.cypher  —  PAT team report: apps + alignment (C9 gate).
//
// Reshaped at the C9 gate (2026-07-18, config/gate-log.md "PAT reconcile"):
// the row subject is the TEAM (one row per team in the PAT team report), and
// every edge hangs off it — the C5 same-row rule (docs/RELATIONSHIP_GUIDE.md).
//
// For each row this loader writes:
//   1. APPS (always, when seal_ids present): the row's SEAL ids feed the
//      ACTIVE arch_develops edge —
//      (:BusinessApplication {seal_id})-[:WAS_ATTRIBUTED_TO {role:'developed_by'}]->(:DevTeam)
//      No new label: this is the catalog side of the catalog↔SEAL ownership
//      reconciliation the vocabulary already confirmed.
//   2. ALIGNMENT (fallback ladder): DevTeam-[:SUPPORTS]->AreaProduct when the
//      row carries area_product_id; ELSE DevTeam-[:SUPPORTS]->Product — the
//      home-product edge is written ONLY as the sole assertion (C5: when the
//      area-product chain exists, Product derives via HAS_AREA_PRODUCT, and a
//      direct edge would restate the row join). team_type (aligned|flex|
//      dedicated) + sponsored ride on the edge.
//   3. SPONSORED (independent facts, C5-fine — different target than the
//      alignment chain): DevTeam-[:SUPPORTS {sponsored:true}]->Product when
//      sponsored_product_id differs from product_id; same for
//      sponsored_area_product_id -> AreaProduct.
//   4. VOLATILE-ALIGNMENT SWEEP (per team, this run): alignment changes in
//      PAT, so each load DELETES this team's pat-sourced SUPPORTS /
//      developed_by edges not refreshed by this run — tracked, never frozen.
//      Scoped to teams in the batch (the D7 scoping philosophy).
//
// C17 (2026-08-01) — which report column is which, now that the source report
// structure has been reviewed. §2's row.area_product_id is the SUPPORTING area
// product; §3b's row.sponsored_area_product_id is the SPONSORING one. The two
// sponsoring columns are CO-POPULATED rather than mutually exclusive, so §3a
// and §3b firing independently is correct and intended, not a latent bug —
// that was the open question C17 closed, and the answer changed no write here.
// The report's THIRD sponsoring form, Sponsoring Product Line, is ruled OUT OF
// SCOPE: it is name-only, and modelling it would mean MERGEing a :ProductLine
// on a name, which §a forbids outright.
//
// Product→HAS_APPLICATION is NO LONGER written here (C9): the row's seal_ids
// are TEAM-scoped; attributing them to the Product conflated two PAT screens.
// catalog_has_application stays status: planned until a product-scoped
// extract is onboarded. One-time cleanup of previously written edges:
// migrate_pat_alignment_c9.cypher.
//
// Prerequisites: DevTeam nodes must exist (dev_teams.cypher). Product /
// AreaProduct / BusinessApplication are MERGEd as fallback anchors if their
// own loaders haven't run yet.
//
// Parameters: $batch (team_id, product_id, area_product_id?, seal_ids?,
//             team_type, sponsored, sponsored_product_id?,
//             sponsored_area_product_id?),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

// ── 0. The row subject ───────────────────────────────────────────────────────
MATCH (dt:DevTeam {team_id: row.team_id})

// ── 1. Apps: arch_develops per SEAL id (satellite → subject) ────────────────
WITH row, dt,
     [id IN split(coalesce(row.seal_ids, ''), ',') WHERE trim(id) <> ''] AS app_ids
FOREACH (raw_app_id IN app_ids |
  MERGE (a:BusinessApplication {seal_id: trim(raw_app_id)})
    ON CREATE SET a.first_seen_at = datetime($loaded_at),
                  a.source     = 'pat'
  MERGE (a)-[r:WAS_ATTRIBUTED_TO {role: 'developed_by'}]->(dt)
    ON CREATE SET r.first_seen_at = datetime($loaded_at),
                  r.source        = 'pat',
                  r.loader        = $loader
  SET r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
)

// ── 2. Alignment: AreaProduct preferred, Product only as sole assertion ─────
WITH row, dt,
     (row.area_product_id IS NOT NULL AND trim(row.area_product_id) <> '') AS has_area
FOREACH (_ IN CASE WHEN has_area THEN [1] ELSE [] END |
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
FOREACH (_ IN CASE WHEN NOT has_area THEN [1] ELSE [] END |
  MERGE (p:Product {product_id: row.product_id})
  MERGE (dt)-[r:SUPPORTS]->(p)
    ON CREATE SET r.first_seen_at = datetime($loaded_at),
                  r.source        = 'pat',
                  r.loader        = $loader
  SET r.team_type    = row.team_type,
      r.sponsored    = coalesce(row.sponsored, false),
      r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
)

// ── 3a. Sponsored product (when it differs from the home product) ───────────
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
)

// ── 3b. Sponsored area product (when it differs from the alignment target) ──
WITH row, dt
FOREACH (_ IN CASE
                WHEN row.sponsored_area_product_id IS NOT NULL
                  AND trim(row.sponsored_area_product_id) <> ''
                  AND row.sponsored_area_product_id <> coalesce(row.area_product_id, '')
                THEN [1] ELSE [] END |
  MERGE (sap:AreaProduct {area_product_id: row.sponsored_area_product_id})
  MERGE (dt)-[r:SUPPORTS]->(sap)
    ON CREATE SET r.first_seen_at = datetime($loaded_at),
                  r.source        = 'pat',
                  r.loader        = $loader
  SET r.team_type    = row.team_type,
      r.sponsored    = true,
      r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
)

// ── 4. Volatile-alignment sweep: this team's stale pat edges go ─────────────
WITH DISTINCT row, dt
OPTIONAL MATCH (dt)-[stale:SUPPORTS]->()
  WHERE stale.source = 'pat' AND stale.last_run_id <> $run_id
DELETE stale
WITH DISTINCT row, dt
OPTIONAL MATCH (:BusinessApplication)-[stale_dev:WAS_ATTRIBUTED_TO {role: 'developed_by'}]->(dt)
  WHERE stale_dev.source = 'pat' AND stale_dev.last_run_id <> $run_id
DELETE stale_dev;
