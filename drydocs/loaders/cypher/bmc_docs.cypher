// =============================================================================
// bmc_docs.cypher  —  BMC Control-M documentation corpus -> :Document + :Chunk
// (lexical graph; manual chunking + MERGE, Neo4j llm-graph-builder pattern —
// chunk-only, NO LLM extraction, NO embeddings, fully deterministic).
//
// Source: external/orchestration/bmc-controlm/controlm-*.md (26 converted
// BMC docs; provenance model in SOURCE-MANIFEST.md). One ROW = one CHUNK,
// carrying its parent Document's header fields denormalized — the Document
// MERGE is idempotent per row (BmcDocsAdapter, drydocs/loaders/bmc_docs.py).
//
// Outputs:
//   (:Document:Entity {doc_id, title, source_url, source_page, scraped_on,
//     purpose, path, trust_default, target_version, classification,
//     subject_product_id})
//   (:Chunk:Entity {chunk_id, seq, heading, level, text, char_count,
//     provenance, tier_rule})
//     -[:PART_OF]->(doc)
//   (doc)-[:FIRST_CHUNK]->(chunk seq 0)
//   (prev chunk)-[:NEXT_CHUNK]->(this chunk) — ordering is computed in
//     Python (the adapter emits row.prev_chunk_id per row); this template
//     only MATCHes the previous chunk, never derives order itself.
//   (doc)-[:DESCRIBES {target_version}]->(sp:SoftwareProduct)
//
// PREREQ: `drydocs load-software-registry` must have already loaded
// :SoftwareProduct. This template MATCHes (NEVER MERGEs) the product — same
// convention as controlm_jobs.cypher's folder prereq — so a missing or
// misspelled subject_product_id silently drops the DESCRIBES edge for that
// row instead of creating a stub SoftwareProduct node.
//
// Parameters: $batch (doc_id, title, source_url, source_page, scraped_on,
//   purpose, path, trust_default, target_version, classification,
//   subject_product_id, chunk_id, seq, heading, level, text, char_count,
//   provenance, tier_rule, prev_chunk_id, row_checksum),
//   $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

// Document upsert — idempotent per row; every row of the same doc_id agrees
// on these fields (BmcDocsAdapter denormalizes them onto every chunk row).
MERGE (doc:Document:Entity {doc_id: row.doc_id})
  ON CREATE SET doc.first_seen_at = datetime($loaded_at),
                doc.source     = 'markdown'
SET doc.title              = row.title,
    doc.source_url         = row.source_url,
    doc.source_page        = row.source_page,
    doc.scraped_on         = row.scraped_on,
    doc.purpose            = row.purpose,
    doc.path               = row.path,
    doc.trust_default      = row.trust_default,
    doc.target_version     = row.target_version,
    doc.classification     = row.classification,
    doc.subject_product_id = row.subject_product_id,
    doc.last_seen_at       = datetime($loaded_at),
    doc.last_run_id        = $run_id

// Chunk upsert.
MERGE (c:Chunk:Entity {chunk_id: row.chunk_id})
  ON CREATE SET c.first_seen_at = datetime($loaded_at),
                c.source     = 'markdown'
SET c.seq          = row.seq,
    c.heading      = row.heading,
    c.level        = row.level,
    c.text         = row.text,
    c.char_count   = row.char_count,
    c.provenance   = row.provenance,
    c.tier_rule    = row.tier_rule,
    c.last_seen_at = datetime($loaded_at),
    c.last_run_id  = $run_id

// Chunk -> Document containment.
MERGE (c)-[po:PART_OF]->(doc)
  ON CREATE SET po.first_seen_at = datetime($loaded_at),
                po.source        = 'markdown',
                po.loader        = $loader
SET po.last_seen_at = datetime($loaded_at),
    po.last_run_id  = $run_id

// Previous chunk -> this chunk (NEXT_CHUNK). MATCH only — row.prev_chunk_id
// is null for every seq-0 row, and a Cypher property match against a null
// parameter value matches nothing, so the FOREACH guard below naturally
// no-ops for doc-start chunks without a separate null check.
WITH row, doc, c
OPTIONAL MATCH (prev:Chunk {chunk_id: row.prev_chunk_id})
FOREACH (_ IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
    MERGE (prev)-[nx:NEXT_CHUNK]->(c)
      ON CREATE SET nx.first_seen_at = datetime($loaded_at),
                    nx.source        = 'markdown',
                    nx.loader        = $loader
    SET nx.last_seen_at = datetime($loaded_at),
        nx.last_run_id  = $run_id
)

// Document -> SoftwareProduct (DESCRIBES). MATCH only, never MERGE — see
// prereq note above.
WITH row, doc, c
OPTIONAL MATCH (sp:SoftwareProduct {product_id: row.subject_product_id})
FOREACH (_ IN CASE WHEN sp IS NOT NULL THEN [1] ELSE [] END |
    MERGE (doc)-[d:DESCRIBES {target_version: row.target_version}]->(sp)
      ON CREATE SET d.first_seen_at = datetime($loaded_at),
                    d.source        = 'markdown',
                    d.loader        = $loader
    SET d.last_seen_at = datetime($loaded_at),
        d.last_run_id  = $run_id
)

// Provenance tail (doc 06 Phase 2 delta-only pattern, idiom copied from
// controlm_folders.cypher): WAS_GENERATED_BY fires only when this chunk was
// just created (no prior row_checksum) or the incoming checksum differs
// from the stored one. row_checksum is always refreshed so the next run
// compares against this run's content.
WITH row, doc, c
MATCH (run:JobRun {run_id: $run_id})
WITH row, doc, c, run, (c.row_checksum IS NULL OR c.row_checksum <> row.row_checksum) AS row_changed
FOREACH (_ IN CASE WHEN row_changed THEN [1] ELSE [] END |
    MERGE (c)-[r:WAS_GENERATED_BY {source: 'markdown'}]->(run)
      ON CREATE SET r.first_seen_at = datetime($loaded_at)
    SET r.last_seen_at = datetime($loaded_at)
)
SET c.row_checksum = row.row_checksum

// Document -> first chunk (seq 0, the preamble). Placed LAST: the WHERE
// below drops every non-zero-seq row from the remainder of the statement,
// so everything above (Chunk/PART_OF/NEXT_CHUNK/DESCRIBES/provenance tail)
// must already be written — same convention as controlm_folders.cypher's
// header-gated ControlMApplication block at its tail.
WITH row, doc, c
WHERE row.seq = 0
MERGE (doc)-[fc:FIRST_CHUNK]->(c)
  ON CREATE SET fc.first_seen_at = datetime($loaded_at),
                fc.source        = 'markdown',
                fc.loader        = $loader
SET fc.last_seen_at = datetime($loaded_at),
    fc.last_run_id  = $run_id;
