// =============================================================================
// email_extracts.cypher  —  Q10: failure/activity emails as the lexical graph.
//
// One row = one chunk (the bmc_docs / essential_graphrag contract): the
// :Document MERGE is idempotent per row, the :Chunk chain rides PART_OF +
// FIRST_CHUNK/NEXT_CHUNK — pure reuse of the ACTIVE docs_* vocabulary (the Q2
// covering-gate precedent; no new edge types).
//
// WHAT THIS FILE MUST NEVER GAIN: an assignment write. The email → folder /
// process edge (docs_email_concerns, CONCERNS) is status: planned behind gate
// email-folder-assignment — an email with no extractable subject loads
// UNASSIGNED, which is a valid resting state. Guarded by
// tests/unit/test_email_extracts.py (no CONCERNS / ControlMFolder / ETLProcess
// token may appear here) and by the uncertain/vocabulary boundary suites.
//
// msg_path / extract_path are CITATIONS: file-server coordinates of the
// preserved pair (the only copy after the Outlook purge). The loader never
// opens the .msg.
//
// Parameters: $batch (EmailExtractRow dicts),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

MERGE (doc:Document {doc_id: row.doc_id})
  ON CREATE SET doc.first_seen_at = datetime($loaded_at),
                doc.source        = 'email-extract'
SET doc.subject        = row.subject,
    doc.title          = row.subject,
    doc.sent_at        = row.sent_at,
    doc.msg_path       = row.msg_path,
    doc.extract_path   = row.extract_path,
    doc.corpus_id      = 'ops-email-extracts',
    doc.trust_default  = row.trust_default,
    doc.classification = row.classification,
    doc.last_seen_at   = datetime($loaded_at),
    doc.last_run_id    = $run_id

MERGE (c:Chunk {chunk_id: row.chunk_id})
  ON CREATE SET c.first_seen_at = datetime($loaded_at),
                c.source        = 'email-extract'
SET c.seq          = row.seq,
    c.text         = row.text,
    c.char_count   = row.char_count,
    c.corpus_id    = 'ops-email-extracts',
    c.last_seen_at = datetime($loaded_at),
    c.last_run_id  = $run_id

MERGE (c)-[po:PART_OF]->(doc)
  ON CREATE SET po.first_seen_at = datetime($loaded_at),
                po.source        = 'email-extract',
                po.loader        = $loader
SET po.last_seen_at = datetime($loaded_at),
    po.last_run_id  = $run_id

// chunk ordering — the adapter computes prev_chunk_id; this MATCHes, never derives
WITH row, doc, c
OPTIONAL MATCH (prev:Chunk {chunk_id: row.prev_chunk_id})
FOREACH (_ IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
    MERGE (prev)-[nc:NEXT_CHUNK]->(c)
      ON CREATE SET nc.first_seen_at = datetime($loaded_at),
                    nc.source        = 'email-extract',
                    nc.loader        = $loader
    SET nc.last_seen_at = datetime($loaded_at),
        nc.last_run_id  = $run_id
)

// Document -> first chunk. Placed LAST — the WHERE drops non-zero-seq rows
// from the remainder of the statement (the bmc_docs.cypher convention).
WITH row, doc, c
WHERE row.seq = 0
MERGE (doc)-[fc:FIRST_CHUNK]->(c)
  ON CREATE SET fc.first_seen_at = datetime($loaded_at),
                fc.source        = 'email-extract',
                fc.loader        = $loader
SET fc.last_seen_at = datetime($loaded_at),
    fc.last_run_id  = $run_id;
