// =============================================================================
// code_tree.cypher  —  knowledge/depgraph-snapshots/drydocs-*.json (v2 rels) ->
//                      :CodeDirectory + CONTAINS_ENTRY
//
// The containment layer of the code snapshot (SME ruling 2026-08-05, admitting
// the tree the G33 gate deferred — ":Directory nodes and CONTAINS edges are a
// gate decision"). Runs AFTER code_snapshot.cypher in load-code-snapshot.
// Bindings (u2_contains_entry in the relationship vocabulary):
//   * CodeDirectory (prov:Collection) — one source-tree DIRECTORY, keyed on
//     file_id (repo-relative path; shares the CodeModule key space — a path
//     is a dir or a file, never both).
//   * CONTAINS_ENTRY = prov:hadMember — parent holds this entry. ONE label
//     for the whole tree (dir->dir and dir->file; :Project at the root) so
//     path traversal is a single -[:CONTAINS_ENTRY*]-> pattern.
//   * The repo-root directory is NOT a CodeDirectory: rows with is_root=true
//     author their edges from the single :Project node (gate §B1(a) holds —
//     one root, no duplicate; nothing else hangs off :Project, §F2, and this
//     stays true — the tree hangs off it THROUGH the ruled edge).
//
// Child endpoints are MERGEd as stubs (the imports-target precedent in
// code_snapshot.cypher) so statement order across batches cannot matter:
// every child dir is also a row of this batch stream and every child file is
// a node row of the module loader, which fills the stub.
//
// Parameters (passed by BaseLoader._flush):
//   $batch        list of dicts matching CodeDirectoryRow
//   $run_id       UUID of this loader's :JobRun
//   $loaded_at    ISO datetime string
//   $loader       loader version tag
//   $source_label 'snapshot'
// =============================================================================

// ---- 1. Directory nodes (non-root rows only) --------------------------------
UNWIND $batch AS row
WITH row WHERE row.is_root = false
MERGE (d:CodeDirectory:Collection {file_id: row.file_id})
  ON CREATE SET d.first_seen_at = datetime($loaded_at),
                d.source        = 'depgraph-snapshot'
SET d.name         = row.name,
    d.rel_path     = row.rel_path,
    d.project      = row.project,
    d.last_seen_at = datetime($loaded_at),
    d.last_run_id  = $run_id;

// ---- 2. Root: (:Project)-[:CONTAINS_ENTRY]->(top-level directories) --------
UNWIND $batch AS row
WITH row WHERE row.is_root = true
MERGE (p:Project:Collection {project_id: row.project_id})
WITH row, p
UNWIND row.child_dir_ids AS cid
MERGE (c:CodeDirectory:Collection {file_id: cid})
  ON CREATE SET c.first_seen_at = datetime($loaded_at),
                c.source        = 'depgraph-snapshot'
MERGE (p)-[e:CONTAINS_ENTRY]->(c)
  ON CREATE SET e.first_seen_at = datetime($loaded_at),
                e.source        = 'depgraph-snapshot',
                e.loader        = $loader
SET e.last_seen_at = datetime($loaded_at),
    e.last_run_id  = $run_id;

// ---- 3. Root: (:Project)-[:CONTAINS_ENTRY]->(top-level files) ---------------
UNWIND $batch AS row
WITH row WHERE row.is_root = true
MERGE (p:Project:Collection {project_id: row.project_id})
WITH row, p
UNWIND row.child_file_ids AS cid
MERGE (m:CodeModule:Entity {file_id: cid})
  ON CREATE SET m.first_seen_at = datetime($loaded_at),
                m.source        = 'depgraph-snapshot'
MERGE (p)-[e:CONTAINS_ENTRY]->(m)
  ON CREATE SET e.first_seen_at = datetime($loaded_at),
                e.source        = 'depgraph-snapshot',
                e.loader        = $loader
SET e.last_seen_at = datetime($loaded_at),
    e.last_run_id  = $run_id;

// ---- 4. (:CodeDirectory)-[:CONTAINS_ENTRY]->(child directories) -------------
UNWIND $batch AS row
WITH row WHERE row.is_root = false
MERGE (d:CodeDirectory:Collection {file_id: row.file_id})
WITH row, d
UNWIND row.child_dir_ids AS cid
MERGE (c:CodeDirectory:Collection {file_id: cid})
  ON CREATE SET c.first_seen_at = datetime($loaded_at),
                c.source        = 'depgraph-snapshot'
MERGE (d)-[e:CONTAINS_ENTRY]->(c)
  ON CREATE SET e.first_seen_at = datetime($loaded_at),
                e.source        = 'depgraph-snapshot',
                e.loader        = $loader
SET e.last_seen_at = datetime($loaded_at),
    e.last_run_id  = $run_id;

// ---- 5. (:CodeDirectory)-[:CONTAINS_ENTRY]->(child files) -------------------
UNWIND $batch AS row
WITH row WHERE row.is_root = false
MERGE (d:CodeDirectory:Collection {file_id: row.file_id})
WITH row, d
UNWIND row.child_file_ids AS cid
MERGE (m:CodeModule:Entity {file_id: cid})
  ON CREATE SET m.first_seen_at = datetime($loaded_at),
                m.source        = 'depgraph-snapshot'
MERGE (d)-[e:CONTAINS_ENTRY]->(m)
  ON CREATE SET e.first_seen_at = datetime($loaded_at),
                e.source        = 'depgraph-snapshot',
                e.loader        = $loader
SET e.last_seen_at = datetime($loaded_at),
    e.last_run_id  = $run_id;
