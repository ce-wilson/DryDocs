// =============================================================================
// essential_graphrag.cypher  —  Essential GraphRAG ebook -> :Document + :Chunk
// (lexical graph; manual chunking + MERGE, same llm-graph-builder pattern the
// bmc-docs-lexical-load gate confirmed 2026-07-08 — chunk-only, NO LLM
// extraction, NO embeddings, fully deterministic). Q2 experiment corpus.
//
// Source: Essential-GraphRAG.pdf (repo root, gitignored local copy of the
// published Manning ebook — cite source_url). One ROW = one CHUNK carrying
// its parent Document's fields denormalized (EssentialGraphragAdapter,
// drydocs/loaders/essential_graphrag.py).
//
// Outputs (docs_* vocabulary REUSE — zero new relationship types):
//   (:Document:Entity {doc_id, title, authors, publisher, published,
//     source_url, path, trust_default, classification})
//   (:Chunk:Entity {chunk_id, seq, heading, level, text, char_count,
//     provenance, tier_rule, chapter, section, page_start})
//     -[:PART_OF]->(doc)
//   (doc)-[:FIRST_CHUNK]->(chunk seq 0)
//   (prev chunk)-[:NEXT_CHUNK]->(this chunk) — ordering computed in Python
//     (row.prev_chunk_id); this template only MATCHes, never derives order.
//
// DELIBERATELY NO DESCRIBES BLOCK: the bmc_docs template's
// (Document)-[:DESCRIBES]->(SoftwareProduct) hook is omitted — this book
// describes a methodology, not a software-registry product, and the target
// database (ddcontext) carries no :SoftwareProduct nodes to MATCH anyway.
//
// Parameters: $batch (doc_id, title, authors, publisher, published,
//   source_url, path, trust_default, classification, chunk_id, seq, heading,
//   level, text, char_count, provenance, tier_rule, prev_chunk_id, chapter,
//   section, page_start, row_checksum),
//   $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

// Document upsert — idempotent per row (every row of the doc agrees on these).
MERGE (doc:Document:Entity {doc_id: row.doc_id})
  ON CREATE SET doc.first_seen_at = datetime($loaded_at),
                doc.source     = 'pdf'
SET doc.title          = row.title,
    doc.authors        = row.authors,
    doc.publisher      = row.publisher,
    doc.published      = row.published,
    doc.source_url     = row.source_url,
    doc.path           = row.path,
    doc.trust_default  = row.trust_default,
    doc.classification = row.classification,
    doc.last_seen_at   = datetime($loaded_at),
    doc.last_run_id    = $run_id

// Chunk upsert.
MERGE (c:Chunk:Entity {chunk_id: row.chunk_id})
  ON CREATE SET c.first_seen_at = datetime($loaded_at),
                c.source     = 'pdf'
SET c.seq          = row.seq,
    c.heading      = row.heading,
    c.level        = row.level,
    c.text         = row.text,
    c.char_count   = row.char_count,
    c.provenance   = row.provenance,
    c.tier_rule    = row.tier_rule,
    c.chapter      = row.chapter,
    c.section      = row.section,
    c.page_start   = row.page_start,
    c.last_seen_at = datetime($loaded_at),
    c.last_run_id  = $run_id

// Chunk -> Document containment.
MERGE (c)-[po:PART_OF]->(doc)
  ON CREATE SET po.first_seen_at = datetime($loaded_at),
                po.source        = 'pdf',
                po.loader        = $loader
SET po.last_seen_at = datetime($loaded_at),
    po.last_run_id  = $run_id

// Previous chunk -> this chunk (NEXT_CHUNK). MATCH only — a null
// prev_chunk_id matches nothing, so the FOREACH guard naturally no-ops for
// the seq-0 chunk without a separate null check.
WITH row, doc, c
OPTIONAL MATCH (prev:Chunk {chunk_id: row.prev_chunk_id})
FOREACH (_ IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
    MERGE (prev)-[nx:NEXT_CHUNK]->(c)
      ON CREATE SET nx.first_seen_at = datetime($loaded_at),
                    nx.source        = 'pdf',
                    nx.loader        = $loader
    SET nx.last_seen_at = datetime($loaded_at),
        nx.last_run_id  = $run_id
)

// Provenance tail (doc 06 Phase 2 delta-only pattern): WAS_GENERATED_BY fires
// only on create or content change; row_checksum always refreshed.
WITH row, doc, c
MATCH (run:JobRun {run_id: $run_id})
WITH row, doc, c, run, (c.row_checksum IS NULL OR c.row_checksum <> row.row_checksum) AS row_changed
FOREACH (_ IN CASE WHEN row_changed THEN [1] ELSE [] END |
    MERGE (c)-[r:WAS_GENERATED_BY {source: 'pdf'}]->(run)
      ON CREATE SET r.first_seen_at = datetime($loaded_at)
    SET r.last_seen_at = datetime($loaded_at)
)
SET c.row_checksum = row.row_checksum

// Document -> first chunk (seq 0, front matter). Placed LAST — the WHERE
// drops every non-zero-seq row from the remainder of the statement, so
// everything above must already be written (the bmc_docs.cypher convention).
WITH row, doc, c
WHERE row.seq = 0
MERGE (doc)-[fc:FIRST_CHUNK]->(c)
  ON CREATE SET fc.first_seen_at = datetime($loaded_at),
                fc.source        = 'pdf',
                fc.loader        = $loader
SET fc.last_seen_at = datetime($loaded_at),
    fc.last_run_id  = $run_id;
