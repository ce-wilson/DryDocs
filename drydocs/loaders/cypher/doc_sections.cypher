// =============================================================================
// doc_sections.cypher  —  docs/design/*.md -> :DesignDoc + :DocSection + PART_OF
// (L7 connector #1, pass 1 of 3; gate doc-traceability-feedback signed off
// 2026-07-20 — config/gate-log.md). One ROW = one AUTHORED anchor; the parent
// :DesignDoc's front-matter fields are denormalized onto every row so the
// DesignDoc MERGE is idempotent per row (the bmc_docs.cypher Document idiom).
//
// Keys are SOURCE-NAMESPACED (gate A2): DesignDoc (origin, doc_id);
// DocSection (origin, doc_id, anchor).
//
// Outputs:
//   (:DesignDoc:Entity {origin, doc_id, title, doc_type, rev, doc_status,
//     commit, path})
//   (:DocSection:Entity {origin, doc_id, anchor, heading, seq})
//     -[:PART_OF]->(doc)
//
// Parameters: $batch (origin, doc_id, title, doc_type, rev, doc_status,
//   commit, path, anchor, heading, seq, row_checksum),
//   $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

MERGE (doc:DesignDoc:Entity {origin: row.origin, doc_id: row.doc_id})
  ON CREATE SET doc.first_seen_at = datetime($loaded_at),
                doc.source     = $source_label
SET doc.title        = row.title,
    doc.doc_type     = row.doc_type,
    doc.rev          = row.rev,
    doc.doc_status   = row.doc_status,
    doc.commit       = row.commit,
    doc.path         = row.path,
    doc.last_seen_at = datetime($loaded_at),
    doc.last_run_id  = $run_id

MERGE (s:DocSection:Entity {origin: row.origin, doc_id: row.doc_id, anchor: row.anchor})
  ON CREATE SET s.first_seen_at = datetime($loaded_at),
                s.source     = $source_label
SET s.heading      = row.heading,
    s.seq          = row.seq,
    s.last_seen_at = datetime($loaded_at),
    s.last_run_id  = $run_id

MERGE (s)-[po:PART_OF]->(doc)
  ON CREATE SET po.first_seen_at = datetime($loaded_at),
                po.source        = $source_label,
                po.loader        = $loader
SET po.last_seen_at = datetime($loaded_at),
    po.last_run_id  = $run_id

// Provenance tail — doc 06 Phase 2 delta-only WAS_GENERATED_BY.
WITH row, s
MATCH (run:JobRun {run_id: $run_id})
WITH row, s, run, (s.row_checksum IS NULL OR s.row_checksum <> row.row_checksum) AS row_changed
FOREACH (_ IN CASE WHEN row_changed THEN [1] ELSE [] END |
    MERGE (s)-[r:WAS_GENERATED_BY {source: $source_label}]->(run)
      ON CREATE SET r.first_seen_at = datetime($loaded_at)
    SET r.last_seen_at = datetime($loaded_at)
)
SET s.row_checksum = row.row_checksum;
