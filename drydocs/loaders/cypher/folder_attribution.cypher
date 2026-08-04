// =============================================================================
// folder_attribution.cypher  —  resolved folder-grain attributions ->
//   (:ControlMFolder)-[:BELONGS_TO_APPLICATION {role:'seal_app_ref'}]->(:Port)
//
// Backlog K8; shape ruled at gate seal-app-ref-edge-reshape (SIGNED OFF
// 2026-08-03, config/gate-log.md §C1/§D1/§D2):
//
//   - MATCH both endpoints — the automated path creates NO nodes. Folder
//     identity = folder_id (controlm-psgmgr); the target is the
//     application's BatchProcessing :Port, key (parent_app_id, kind) —
//     NOT :BusinessApplication (§C1: supernode avoidance). A row whose
//     endpoints are absent writes nothing here and is surfaced by the
//     loader as JobRun.dropped_in_graph (never a silent drop).
//   - PIN guard (§F, folder grain): a folder carrying a manually-asserted
//     edge (match_method = 'manual') is never touched by automation — the
//     Python resolver already excludes pinned folders (surfacing
//     PIN-CONFLICTs on the coverage report); this WHERE is the
//     belt-and-suspenders backstop.
//   - ON CREATE: first_seen_at / source / origin / match_method / tier
//     (set once). origin is the §B3 disclosure flag: defined | override |
//     manual-pin (authored) | matched-fallback (derived by the demoted K2
//     policy at load time — never presented as defined).
//   - SET every run: last_seen_at / last_run_id (re-confirmation
//     bookkeeping).
//
// Folder -> application is 1:1 (OWNER-NOT-USER): enforced by the resolver
// (one row per folder by construction) and by the graph-test suite
// graph-tests/folder-attribution-coverage.yaml — never by a constraint,
// because Neo4j cannot declare relationship cardinality.
//
// Parameters: $batch (validated FolderAttributionRow dicts),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

MATCH (f:ControlMFolder {folder_id: row.folder_id})
MATCH (p:Port:BatchProcessing {parent_app_id: row.app_id, kind: 'BatchProcessing'})
WHERE NOT EXISTS {
  MATCH (f)-[m:BELONGS_TO_APPLICATION {role: 'seal_app_ref'}]->(:Port)
  WHERE m.match_method = 'manual'
}

MERGE (f)-[r:BELONGS_TO_APPLICATION {role: 'seal_app_ref'}]->(p)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = row.source,
                r.origin        = row.origin,
                r.match_method  = row.match_method,
                r.tier          = row.tier
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id

// K10 (§G4/§G5): the edge landing on the port IS the confirmation — no
// separate trigger, which is what §C1(b) bought. First-confirmation stamps
// are stable (coalesce): a re-run re-confirms without rewriting who/when
// confirmed first. confirmed_by = the authoring steward when the row was
// authored, else the loader (a matched-fallback derivation).
SET p.active_state     = 'confirmed',
    p.confirmed_by     = coalesce(p.confirmed_by, coalesce(row.authored_by, $loader)),
    p.confirmed_at     = coalesce(p.confirmed_at, datetime($loaded_at)),
    p.confirmed_run_id = coalesce(p.confirmed_run_id, $run_id);
