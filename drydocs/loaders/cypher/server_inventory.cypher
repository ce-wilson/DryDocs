// =============================================================================
// server_inventory.cypher  —  infra:server-export -> :Server + :DataCenter +
//                             LOCATED_IN + the technology-port leg
//
// Gate: server-location-ontology SIGNED OFF 12/12, 2026-08-19
// (config/gate-log.md; spec config/gate-prompts/server-location-ontology.yaml).
// Bindings:
//   * Server (dd:Server) — the INVENTORY spine (§A1), keyed on name.
//     Deliberately NOT ExecutionHost (Control-M's view — often an LB alias),
//     NOT ControlMServer (a scheduler instance), NOT ControlMHostGroup (an
//     LB set). The ExecutionHost join is the SEPARATE derived resolution pass
//     (server_resolution.cypher) with tiers + evidence — never a merge here.
//   * DataCenter (dd:DataCenter, functions as prov:Location) — PHYSICAL
//     building, keyed on name; carries building/city/state/country props +
//     location_grain (the Idea-90 declaration, computed loader-side — §B2).
//     NEVER the Control-M "data center" (§B4 — the scheduling concept whose
//     name encodes a default run time; the two never join by field name).
//   * LOCATED_IN = prov:atLocation (infra_located_in); rack rides the edge.
//   * The §C2 technology port (the SME reshape): (:BusinessApplication)
//     -[:HAS_PORT]->(:Port:Technology {kind:'Technology'})-[:RUNS_ON
//     {role:'technology_port'}]->(:Server). MATCH-only on the app — a row
//     whose app is absent loads its Server/DataCenter half and the gap is
//     counted by the loader's coverage query (reported, never minted).
//
// designation (PROD | DR) is a :Server property (§A3) — both designations
// get the port leg; queries filter the property.
//
// Parameters (passed by BaseLoader._flush):
//   $batch        list of dicts (ServerInventoryRow projections + location_grain)
//   $run_id       UUID of this loader's :JobRun
//   $loaded_at    ISO datetime string
//   $loader       loader version tag
//   $source_label 'csv'
// =============================================================================

// ---- Pass 1: every row lands its Server (+ DataCenter + LOCATED_IN) --------
UNWIND $batch AS row

MERGE (s:Server {name: row.server_name})
  ON CREATE SET s.first_seen_at = datetime($loaded_at),
                s.source        = 'infra:server-export'
SET s.os_product    = row.os_product,
    s.os_version    = row.os_version,
    s.designation   = row.designation,
    s.owning_app_id = row.business_application,
    s.last_seen_at  = datetime($loaded_at),
    s.last_run_id   = $run_id

// DataCenter + placement only when the row supplied a building (grain rule:
// absent levels stay absent — a row with city-only geography still records
// its grain on the Server for the coverage view, but mints no half-known
// DataCenter node; the finest-supplied-level declaration lives where the
// node is real).
SET s.location_grain = row.location_grain

WITH row, s
WHERE row.data_center IS NOT NULL AND row.data_center <> ''
MERGE (dc:DataCenter {name: row.data_center})
  ON CREATE SET dc.first_seen_at = datetime($loaded_at),
                dc.source        = 'infra:server-export'
SET dc.city           = row.city,
    dc.state          = row.state,
    dc.country        = row.country,
    dc.location_grain = row.location_grain,
    dc.last_seen_at   = datetime($loaded_at),
    dc.last_run_id    = $run_id

MERGE (s)-[loc:LOCATED_IN]->(dc)
  ON CREATE SET loc.first_seen_at = datetime($loaded_at),
                loc.source        = 'infra:server-export',
                loc.loader        = $loader
SET loc.rack         = row.rack,
    loc.last_seen_at = datetime($loaded_at),
    loc.last_run_id  = $run_id;

// ---- Pass 2: the §C2 technology-port leg (MATCH-only on the app) -----------
UNWIND $batch AS row

MATCH (a:BusinessApplication {app_id: row.business_application})
WHERE NOT a:SchemaMeta
MATCH (s:Server {name: row.server_name})

MERGE (a)-[hp:HAS_PORT]->(p:Port:Technology {parent_app_id: row.business_application, kind: 'Technology'})
  ON CREATE SET p.first_seen_at  = datetime($loaded_at),
                p.source         = 'infra:server-export',
                hp.first_seen_at = datetime($loaded_at),
                hp.source        = 'infra:server-export'
SET p.last_seen_at  = datetime($loaded_at),
    p.last_run_id   = $run_id

MERGE (p)-[r:RUNS_ON {role: 'technology_port'}]->(s)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = 'infra:server-export',
                r.loader        = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id;
