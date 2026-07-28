// =============================================================================
// code_snapshot.cypher  —  knowledge/depgraph-snapshots/drydocs-*.json ->
//                          :Project + :CodeModule + HAS_MODULE + IMPORTS +
//                          IS_ENCODED_IN
//
// Gate: self-documentation-code-graph SIGNED OFF 2026-07-27 (config/gate-log.md;
// spec config/gate-prompts/self-documentation-code-graph.yaml). Bindings:
//   * Project (prov:Collection) — ONE root, §B1(a); the six scan roots are the
//     CodeModule.project PROPERTY, never sibling nodes. §F2: nothing else in
//     the graph hangs off :Project — it is the "is this our own code?" anchor.
//   * CodeModule (prov:Entity) — one source FILE, keyed on file_id
//     (repo-relative path; §C1(a)/§C2). abs_path is DROPPED upstream (§H4).
//   * HAS_MODULE = prov:hadMember (u1_has_module) — single root to ALL modules.
//   * IMPORTS (u1_imports) — importer -> imported. §D2 accepted limit: cannot
//     distinguish `import x` / `from x import y` / TYPE_CHECKING-only. Do NOT
//     read an IMPORTS edge as "breaks if removed".
//   * IS_ENCODED_IN (u1_is_encoded_in) — FIRST USE of the SWO layer: targets
//     the ALREADY-SEEDED SwoClass term (§E1(b)); row.language_iri is derived
//     from node.extension by the adapter, null = no seeded term, edge skipped.
//     MATCH-only on the term: run `drydocs bootstrap` (ontology.cypher) first.
//
// §F1 (collision guard): no node may carry BOTH :CodeModule and
// :SoftwareProduct. Enforced as a GRAPH-TEST (m1-verify), not a constraint —
// Neo4j cannot declare label mutual-exclusion.
//
// Import targets are MERGEd as stubs so edge order within the batch cannot
// matter; every target is also a node row of the same snapshot, which then
// fills the stub in the same run.
//
// Parameters (passed by BaseLoader._flush):
//   $batch        list of dicts matching CodeModuleRow
//   $run_id       UUID of this loader's :JobRun
//   $loaded_at    ISO datetime string
//   $loader       loader version tag
//   $source_label 'snapshot'
// =============================================================================

UNWIND $batch AS row

// The single Project root (§B1(a)) — carries the snapshot's git provenance,
// so the graph can state exactly which commit it describes.
MERGE (p:Project:Collection {project_id: row.project_id})
  ON CREATE SET p.first_seen_at = datetime($loaded_at),
                p.source        = 'depgraph-snapshot'
SET p.captured_at  = datetime(row.captured_at),
    p.git_commit   = row.git_commit,
    p.git_full     = row.git_full,
    p.git_branch   = row.git_branch,
    p.git_dirty    = row.git_dirty,
    p.last_seen_at = datetime($loaded_at),
    p.last_run_id  = $run_id

// The module (file) node — key file_id, §C2.
MERGE (m:CodeModule:Entity {file_id: row.file_id})
  ON CREATE SET m.first_seen_at = datetime($loaded_at),
                m.source        = 'depgraph-snapshot'
SET m.project      = row.project,
    m.rel_path     = row.rel_path,
    m.name         = row.name,
    m.extension    = row.extension,
    m.circular     = row.circular,
    m.last_seen_at = datetime($loaded_at),
    m.last_run_id  = $run_id

// Containment (u1_has_module, prov:hadMember).
MERGE (p)-[hm:HAS_MODULE]->(m)
  ON CREATE SET hm.first_seen_at = datetime($loaded_at),
                hm.source        = 'depgraph-snapshot',
                hm.loader        = $loader
SET hm.last_seen_at = datetime($loaded_at),
    hm.last_run_id  = $run_id

// SWO language binding (u1_is_encoded_in) — only when the adapter mapped the
// extension to a seeded term. OPTIONAL MATCH + FOREACH because the term may
// legitimately be absent per row (null iri), but a MAPPED term missing from
// the graph means bootstrap has not run — m1-verify catches that as a count
// mismatch rather than this template guessing.
WITH row, p, m
OPTIONAL MATCH (lang:OntologyTerm:SwoClass {iri: row.language_iri})
FOREACH (l IN CASE WHEN lang IS NULL THEN [] ELSE [lang] END |
  MERGE (m)-[enc:IS_ENCODED_IN]->(l)
    ON CREATE SET enc.first_seen_at = datetime($loaded_at),
                  enc.source        = 'depgraph-snapshot',
                  enc.loader        = $loader
  SET enc.last_seen_at = datetime($loaded_at),
      enc.last_run_id  = $run_id
)

// Dependencies (u1_imports) — importer -> imported (§D1). Rows with no
// imports are eliminated by the UNWIND here, which is safe: this is the last
// clause chain and their node/containment writes above already happened.
WITH row, m
UNWIND row.imports AS target_id
MERGE (t:CodeModule:Entity {file_id: target_id})
  ON CREATE SET t.first_seen_at = datetime($loaded_at),
                t.source        = 'depgraph-snapshot'
SET t.last_seen_at = datetime($loaded_at),
    t.last_run_id  = $run_id
MERGE (m)-[imp:IMPORTS]->(t)
  ON CREATE SET imp.first_seen_at = datetime($loaded_at),
                imp.source        = 'depgraph-snapshot',
                imp.loader        = $loader
SET imp.last_seen_at = datetime($loaded_at),
    imp.last_run_id  = $run_id;
