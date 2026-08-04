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
// TWO IDS, AND THEY ARE NOT THE SAME THING (fixed at the Q13 close):
//   * `corpus_id` is the config/doc-source-registry.yaml entry — the id
//     `drydocs docs-verify` searches for, because that entry's graph_locator
//     says `match: corpus_id` (Q7). Keying the graph by the CAPTURE id instead
//     made the reconciliation check answer "missing" for a fully loaded
//     corpus: a false negative in the one check built to catch false claims.
//   * `capture_id` is one fetch of one tree at one version, and it SCOPES
//     `doc_id` and `section_id`. Author-it reuses topic ids across
//     publications, so a bare-stem MERGE would overwrite the 9.0.20 topic
//     with its 9.0.21 namesake and silently take the version distinction —
//     the thing this corpus exists to preserve — with it.
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
//   (:Document:Entity {doc_id, corpus_id, capture_id, title, abstract,
//     page_role, breadcrumb, source_url, sha256, captured_at, doc_version,
//     version_verified, trust, classification})
//   (:Chunk:Entity {chunk_id, seq, heading, level, text, char_count,
//     corpus_id, capture_id, doc_version, version_verified})
//     -[:PART_OF]->(doc)
//   (doc)-[:FIRST_CHUNK]->(chunk seq 0)
//   (prev chunk)-[:NEXT_CHUNK]->(this chunk)   — order computed in Python
//   (:DocSection {section_id, title, corpus_id, capture_id, doc_version,
//     version_verified})                          the TOC spine
//   (doc)-[:IN_SECTION]->(:DocSection)
//   (:DocSection)-[:SUBSECTION_OF]->(:DocSection)
//
// `version_verified` rides EVERY node, not just the Document, and is ALWAYS
// false at load time: only a human confirming this capture against a runtime
// version may flip it (Q16). A chunk that surfaces on its own in a retrieval
// result therefore still carries the version caveat — an agent answering from
// this corpus can never claim more than "the <doc_version> documentation says
// X, unverified for your estate".
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
    doc.capture_id       = row.capture_id,
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
SET chunk.seq              = row.seq,
    chunk.heading          = row.heading,
    chunk.level            = row.level,
    chunk.text             = row.text,
    chunk.char_count       = row.char_count,
    chunk.corpus_id        = row.corpus_id,
    chunk.capture_id       = row.capture_id,
    chunk.doc_version      = row.doc_version,
    chunk.version_verified = row.version_verified,
    chunk.last_seen_at     = datetime($loaded_at)

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
// ancestry path scoped by CAPTURE, so neither two corpora sharing a book name
// nor two versions of one book collide, and a re-run is idempotent.
WITH row, doc, chunk, row.toc_path AS path
FOREACH (_ IN CASE WHEN size(path) = 0 THEN [] ELSE [1] END |
  MERGE (leaf:DocSection {section_id: row.capture_id + '/' + apoc.text.join(path, '/')})
    ON CREATE SET leaf.first_seen_at = datetime($loaded_at)
  SET leaf.title            = last(path),
      leaf.corpus_id        = row.corpus_id,
      leaf.capture_id       = row.capture_id,
      leaf.doc_version      = row.doc_version,
      leaf.version_verified = row.version_verified,
      leaf.depth            = size(path)
  MERGE (doc)-[:IN_SECTION]->(leaf)
)

// --- Provenance tail (doc 06 Phase 2 delta-only pattern, idiom copied from
// bmc_docs.cypher / controlm_folders.cypher) ---------------------------------
// WAS_GENERATED_BY fires only when this chunk was just created (no prior
// row_checksum) or the incoming checksum differs from the stored one.
// row_checksum is always refreshed so the next run compares against this
// run's content.
//
// WITHOUT THIS the loader could not report a change AT ALL: BaseLoader derives
// `rows_changed` by counting the WAS_GENERATED_BY edges a run attached, so a
// template that writes none reports rows_changed=0 on the FIRST load as
// readily as on a no-op re-run. That makes the Q13 acceptance's own idempotence
// evidence ("a second full run reports zero net change") unfalsifiable — the
// "succeeds loudly, does nothing" reporting class this epic hit three times
// (G29, G30, Q8). `to_params` computed row_checksum all along; nothing read it.
//
// PLACEMENT IS LOAD-BEARING: it must sit ABOVE the SUBSECTION_OF block, whose
// UNWIND of an empty list drops every row at TOC depth <= 1 from the remainder
// of the statement — the same tail-ordering trap bmc_docs.cypher documents.
WITH row, doc, chunk
MATCH (run:JobRun {run_id: $run_id})
WITH row, doc, chunk, run,
     (chunk.row_checksum IS NULL OR chunk.row_checksum <> row.row_checksum) AS row_changed
FOREACH (_ IN CASE WHEN row_changed THEN [1] ELSE [] END |
  MERGE (chunk)-[r:WAS_GENERATED_BY {source: 'vendor-docs'}]->(run)
    ON CREATE SET r.first_seen_at = datetime($loaded_at)
  SET r.last_seen_at = datetime($loaded_at)
)
SET chunk.row_checksum = row.row_checksum

// --- TOC ancestry chain (LAST — see the placement note above) ----------------
WITH row, doc, row.toc_path AS path
UNWIND CASE WHEN size(path) > 1 THEN range(1, size(path) - 1) ELSE [] END AS i
MERGE (child:DocSection {section_id: row.capture_id + '/' + apoc.text.join(path[0..i + 1], '/')})
  ON CREATE SET child.first_seen_at = datetime($loaded_at)
SET child.title            = path[i],
    child.corpus_id        = row.corpus_id,
    child.capture_id       = row.capture_id,
    child.doc_version      = row.doc_version,
    child.version_verified = row.version_verified,
    child.depth            = i + 1
MERGE (parent:DocSection {section_id: row.capture_id + '/' + apoc.text.join(path[0..i], '/')})
  ON CREATE SET parent.first_seen_at = datetime($loaded_at)
SET parent.title            = path[i - 1],
    parent.corpus_id        = row.corpus_id,
    parent.capture_id       = row.capture_id,
    parent.doc_version      = row.doc_version,
    parent.version_verified = row.version_verified,
    parent.depth            = i
MERGE (child)-[:SUBSECTION_OF]->(parent)
