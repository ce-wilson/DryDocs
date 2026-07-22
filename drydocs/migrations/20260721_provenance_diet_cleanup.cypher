// Migration: provenance diet cleanup (doc 06 Phase 3 / backlog M2, 2026-07-21).
// Target: EXISTING graphs loaded before the M1 provenance-edge diet (2026-07-08)
// and/or before the Phase 1 audit envelope (2026-07-07). Run once. Idempotent.
// New graphs need none of this — loaders already write the post-diet shape.
//
// DESTRUCTIVE (step 1 deletes edges; step 3 removes properties) — HITL-confirm
// before running, per the M2 acceptance. Sequence producer-first, then the
// company runs its own copy against its graph (doc 06 risk note; T9: graph
// writes are always theirs).
//
// RUN MODE: steps use CALL { ... } IN TRANSACTIONS — execute in implicit/auto-
// commit mode (cypher-shell default, Neo4j Browser :auto, or the drydocs
// client's session.run), NOT inside an explicit transaction.
//
// What each step does and why it is safe:
//   1) Pre-diet runs are identifiable structurally: JobRun.rows_changed was
//      introduced by M1's _close_run — a run that completed OK WITHOUT it
//      predates the diet, so its WAS_GENERATED_BY edges are blanket full-
//      refresh membership ("we pulled it"), not change records. Post-M1 edges
//      (create/actual-change only) all point at runs WITH rows_changed: never
//      touched. Runs with rows_changed NULL and status <> 'OK' are AMBIGUOUS
//      (failed/unclosed, either era) — reported by the sanity query below,
//      never auto-deleted (the coverage-policy rule: surfaced, not guessed).
//   2) Folder audit envelope backfill where recoverable: pre-Phase-1 graphs
//      carry the raw-named pair (last_updated / last_updated_user) but not the
//      envelope (source_updated_at / source_updated_by). Pre-Phase-1 loaders
//      stored last_updated as a STRING — normalized to datetime() here.
//      (Jobs have nothing to backfill from: their source audit columns were
//      filter-only pre-Phase-1 and never landed in the graph; a re-load
//      populates their envelope.)
//   3) The raw-named folder pair retires (the envelope is the record now).
//   4) Pull-provenance naming standardization (deferred from Phase 1): node
//      bookkeeping created_at -> first_seen_at, matching the edge vocabulary
//      (first_seen_at / last_seen_at / last_run_id). The three snapshot
//      version labels are EXCLUDED — their created_at belongs to the snapshot
//      writer's own vocabulary (valid_from / valid_to / created_at), not
//      loader bookkeeping.

// 1) Delete blanket WAS_GENERATED_BY edges (pre-diet completed runs only).
MATCH (run:JobRun {kind: 'load', status: 'OK'})
WHERE run.rows_changed IS NULL
MATCH (n)-[r:WAS_GENERATED_BY]->(run)
CALL {
  WITH r
  DELETE r
} IN TRANSACTIONS OF 10000 ROWS;

// 2) Backfill the folder envelope where recoverable (pre-Phase-1 graphs;
//    string dates normalized).
MATCH (f:ControlMFolder)
WHERE f.last_updated IS NOT NULL AND f.source_updated_at IS NULL
SET f.source_updated_at = CASE
      WHEN valueType(f.last_updated) STARTS WITH 'STRING'
      THEN datetime(replace(f.last_updated, ' ', 'T'))
      ELSE f.last_updated END,
    f.source_updated_by = coalesce(f.source_updated_by, f.last_updated_user);

// 3) Retire the raw-named folder pair (loaders stopped writing them at M2).
MATCH (f:ControlMFolder)
WHERE f.last_updated IS NOT NULL OR f.last_updated_user IS NOT NULL
REMOVE f.last_updated, f.last_updated_user;

// 4) Rename loader bookkeeping created_at -> first_seen_at (snapshot version
//    labels excluded — see header).
MATCH (n)
WHERE n.created_at IS NOT NULL
  AND NOT n:ApplicationSnapshot AND NOT n:ProductSnapshot AND NOT n:CatalogLOBSnapshot
CALL {
  WITH n
  SET n.first_seen_at = coalesce(n.first_seen_at, n.created_at)
  REMOVE n.created_at
} IN TRANSACTIONS OF 10000 ROWS;

// 5) Sanity checks (run manually; expectations in comments):
// // AMBIGUOUS runs — review by hand before deciding anything about them:
// MATCH (run:JobRun {kind:'load'}) WHERE run.rows_changed IS NULL AND run.status <> 'OK'
// OPTIONAL MATCH (n)-[r:WAS_GENERATED_BY]->(run)
// RETURN run.run_id, run.loader, run.status, count(r) AS edges;
// // Expect 0 after step 1:
// MATCH (run:JobRun {kind:'load', status:'OK'}) WHERE run.rows_changed IS NULL
// MATCH ()-[r:WAS_GENERATED_BY]->(run) RETURN count(r) AS blanket_remaining;
// // Expect 0 after step 3:
// MATCH (f:ControlMFolder) WHERE f.last_updated IS NOT NULL OR f.last_updated_user IS NOT NULL
// RETURN count(f) AS raw_props_remaining;
// // Expect 0 after step 4 (snapshot labels keep created_at by design):
// MATCH (n) WHERE n.created_at IS NOT NULL
//   AND NOT n:ApplicationSnapshot AND NOT n:ProductSnapshot AND NOT n:CatalogLOBSnapshot
// RETURN count(n) AS created_at_remaining;
