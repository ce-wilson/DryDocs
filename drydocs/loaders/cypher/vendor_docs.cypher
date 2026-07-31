// =============================================================================
// vendor_docs.cypher — captured external-vendor documentation -> a NAVIGABLE
// :Document + :Chunk graph (backlog Q13; plan =
// knowledge/upgrade-plans/vendor-docs-agent-navigation.md).
//
// Source: DRYDOCS_DATA_ROOT/vendor-docs/<capture-id>/ — out-of-repo VERBATIM
// capture (scripts/external_vendor_scrape.py) converted to markdown by
// drydocs/loaders/vendor_docs.py. One ROW = one CHUNK, carrying its parent
// Document's fields denormalized so the Document MERGE is idempotent per row.
//
// TAXONOMY ONLY — this template writes structure the VENDOR ALREADY PUBLISHES
// (its table of contents) and nothing that asserts meaning:
//   * NO :ControlMUtility — whether a documented utility is a first-class node
//     is Q14's gate question, not this loader's to presume.
//   * NO DOCUMENTS / DESCRIBES edge to :SoftwareProduct. Deliberate, and not
//     merely deferred: a relationship CANNOT SPAN NEO4J DATABASES (the finding
//     behind Q8), and ADR 0006 re-targets doc corpora to `dddocs` while the
//     software registry keeps writing `drydocs`. Writing that edge here would
//     work today and silently vanish at the move. G32 owns the residency
//     ruling; Q16 carries the pointer once it lands.
//   * NO SEE_ALSO. The vendor's own related-topic links ARE carried through
//     conversion and sit in convert-manifest.json as evidence for Q14 — as
//     data, on disk, never as an edge.
//
// Outputs:
//   (:Document:Entity {doc_id, corpus_id, title, abstract, page_role,
//     breadcrumb, source_url, sha256, captured_at, doc_version,
//     version_verified, trust, classification})
//   (:Chunk:Entity {chunk_id, seq, heading, level, text, char_count})
//     -[:PART_OF]->(doc)
//   (doc)-[:FIRST_CHUNK]->(chunk seq 0)
//   (prev chunk)-[:NEXT_CHUNK]->(this chunk)   — order computed in Python
//   (:DocSection {section_id, title, corpus_id})   the TOC spine
//   (doc)-[:IN_SECTION]->(:DocSection)
//   (:DocSection)-[:SUBSECTION_OF]->(:DocSection)
//
// `version_verified` is written from the row and is ALWAYS false at load time:
// only a human confirming this capture against a runtime version may flip it
// (Q16). An agent answering from this corpus can therefore never claim more
// than "the <doc_version> documentation says X, unverified for your estate".
//
// Parameters: $batch (see VendorDocChunkRow), $run_id, $loaded_at, $loader,
//   $source_label.
// =============================================================================

UNWIND $batch AS row

// --- Document (idempotent per row) ------------------------------------------
MERGE (doc:Document:Entity {doc_id: row.doc_id})
  ON CREATE SET doc.first_seen_at = datetime($loaded_at),
                doc.source        = 'vendor-docs'
SET doc.corpus_id        = row.corpus_id,
    doc.title            = row.title,
    doc.abstract         = row.abstract,
    doc.page_role        = row.page_role,
    doc.breadcrumb       = row.breadcrumb,
    doc.source_url       = row.source_url,
    doc.sha256           = row.sha256,
    doc.captured_at      = row.captured_at,
    doc.doc_version      = row.doc_version,
    doc.version_verified = row.version_verified,
    doc.trust            = row.trust,
    doc.classification   = row.classification,
    doc.last_seen_at     = datetime($loaded_at)

// --- Chunk -------------------------------------------------------------------
MERGE (chunk:Chunk:Entity {chunk_id: row.chunk_id})
  ON CREATE SET chunk.first_seen_at = datetime($loaded_at)
SET chunk.seq          = row.seq,
    chunk.heading      = row.heading,
    chunk.level        = row.level,
    chunk.text         = row.text,
    chunk.char_count   = row.char_count,
    chunk.corpus_id    = row.corpus_id,
    chunk.last_seen_at = datetime($loaded_at)

MERGE (chunk)-[:PART_OF]->(doc)

FOREACH (_ IN CASE WHEN row.seq = 0 THEN [1] ELSE [] END |
  MERGE (doc)-[:FIRST_CHUNK]->(chunk)
)

// Ordering is computed in Python (the adapter emits row.prev_chunk_id); this
// template only MATCHes the predecessor and never derives sequence itself.
FOREACH (_ IN CASE WHEN row.prev_chunk_id IS NULL THEN [] ELSE [1] END |
  MERGE (prev:Chunk:Entity {chunk_id: row.prev_chunk_id})
  MERGE (prev)-[:NEXT_CHUNK]->(chunk)
)

// --- TOC spine ---------------------------------------------------------------
// The publisher's own hierarchy, transcribed. Section identity is the joined
// ancestry path scoped by corpus, so two corpora with a same-named book do not
// collide and a re-run is idempotent.
WITH doc, row, row.toc_path AS path
FOREACH (_ IN CASE WHEN size(path) = 0 THEN [] ELSE [1] END |
  MERGE (leaf:DocSection {section_id: row.corpus_id + '/' + apoc.text.join(path, '/')})
    ON CREATE SET leaf.first_seen_at = datetime($loaded_at)
  SET leaf.title     = last(path),
      leaf.corpus_id = row.corpus_id,
      leaf.depth     = size(path)
  MERGE (doc)-[:IN_SECTION]->(leaf)
)

WITH doc, row, row.toc_path AS path
UNWIND CASE WHEN size(path) > 1 THEN range(1, size(path) - 1) ELSE [] END AS i
MERGE (child:DocSection {section_id: row.corpus_id + '/' + apoc.text.join(path[0..i + 1], '/')})
  ON CREATE SET child.first_seen_at = datetime($loaded_at)
SET child.title     = path[i],
    child.corpus_id = row.corpus_id,
    child.depth     = i + 1
MERGE (parent:DocSection {section_id: row.corpus_id + '/' + apoc.text.join(path[0..i], '/')})
  ON CREATE SET parent.first_seen_at = datetime($loaded_at)
SET parent.title     = path[i - 1],
    parent.corpus_id = row.corpus_id,
    parent.depth     = i
MERGE (child)-[:SUBSECTION_OF]->(parent)
