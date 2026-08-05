// =============================================================================
// dev_teams.cypher  —  Catalog DevTeam metadata.
//
// This loader does NOT create the dev_team -> seal_id mapping (that's M2's
// pat_product_mapping). It only loads team metadata + an optional anchor
// to a Product.
//
// Parameters: $batch (team_id, name, jira_board_id, parent_product_id),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row
MERGE (dt:DevTeam {team_id: row.team_id})
  ON CREATE SET dt.first_seen_at = datetime($loaded_at),
                dt.source     = 'catalog'
// C24 (extends C22 §b to this loader): the unconditional `SET dt.name =
// row.name` blanked the stored name the first time an extract omitted the
// column. The model half moved with it — DevTeamRow.name was REQUIRED, which
// C22 ruled the WORSE failure: a sparse row then rejects wholesale, so
// last_seen_at never advances and the team looks retired rather than
// unrefreshed. name is now optional with ''-to-None normalization; team_id
// stays required, because optionality must not leak into keying.
SET dt.name         = coalesce(row.name, dt.name),
    dt.last_seen_at = datetime($loaded_at),
    dt.last_run_id  = $run_id

// Optional Jira board link.
WITH row, dt
FOREACH (_ IN CASE
                WHEN row.jira_board_id IS NOT NULL AND trim(row.jira_board_id) <> ''
                THEN [1] ELSE [] END |
  MERGE (jb:JiraBoard {board_id: row.jira_board_id})
    ON CREATE SET jb.first_seen_at = datetime($loaded_at)
  MERGE (dt)-[:HAS_JIRA_BOARD]->(jb)
)

// Optional Product anchor.
WITH row, dt
FOREACH (_ IN CASE
                WHEN row.parent_product_id IS NOT NULL
                  AND trim(row.parent_product_id) <> ''
                THEN [1] ELSE [] END |
  MERGE (p:Product {product_id: row.parent_product_id})
  MERGE (p)-[r:HAS_DEV_TEAM]->(dt)
    ON CREATE SET r.first_seen_at = datetime($loaded_at),
                  r.source        = 'catalog',
                  r.loader        = $loader
  SET r.last_seen_at = datetime($loaded_at),
      r.last_run_id  = $run_id
);
