// =============================================================================
// doc_feedback.cypher  —  docs/design/feedback/<doc>-rev<N>.yaml ->
// :FeedbackNote + ANNOTATES (+ WAS_ATTRIBUTED_TO {role: feedback_author}).
// L7 connector #1, pass 3 of 3 (gate doc-traceability-feedback signed off
// 2026-07-20 — config/gate-log.md). One ROW = one anchor-keyed note.
//
// Key (origin, doc_id, doc_rev, anchor) — one note per anchor per rev file;
// doc_rev is the rev the note was taken AGAINST (a property, not a Revision
// node — gate C2). Lifecycle status open|applied|rejected|superseded — gate C3.
//
// ANNOTATES targets the note's BASE authored anchor (an L11 derived id
// degrades to its parent section — the feedback_anchor_valid rule) and
// MATCHes only (pass 1 first): an unresolvable anchor drops the edge, never
// creates a stub section. WAS_ATTRIBUTED_TO MATCHes :Employee {employee_id}
// only — an unknown author drops the edge, provenance is never fabricated
// (gate C1). Correlation to :Requirement is the mixed-direction traversal
// ANNOTATES + reverse SPECIFIED_IN — deliberately NOT stored (gate C4).
// PREREQ ENFORCEMENT (L17, Q8 family): this template cannot check the
// whole-registry conditions (it runs per batch) — DocFeedbackLoader
// refuses up front via _assert_doc_sections_present (NO :DocSection
// reachable -> every ANNOTATES would drop; a relationship cannot span databases)
// and _assert_employees_present_if_authored (authored batch,
// EMPTY :Employee registry -> every attribution would drop); per-row
// misses are listed after the load by _report_unmatched_anchors /
// _report_unknown_authors, never silent.
//
// Parameters: $batch (origin, doc_id, doc_rev, anchor, base_anchor, note,
//   status, author, row_checksum), $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

MERGE (fn:FeedbackNote:Entity {origin: row.origin, doc_id: row.doc_id,
                               doc_rev: row.doc_rev, anchor: row.anchor})
  ON CREATE SET fn.first_seen_at = datetime($loaded_at),
                fn.source     = $source_label
SET fn.note         = row.note,
    fn.status       = row.status,
    fn.base_anchor  = row.base_anchor,
    fn.last_seen_at = datetime($loaded_at),
    fn.last_run_id  = $run_id

// Note -> the authored section it annotates (MATCH only).
WITH row, fn
OPTIONAL MATCH (ds:DocSection {origin: row.origin, doc_id: row.doc_id, anchor: row.base_anchor})
FOREACH (_ IN CASE WHEN ds IS NOT NULL THEN [1] ELSE [] END |
    MERGE (fn)-[an:ANNOTATES]->(ds)
      ON CREATE SET an.first_seen_at = datetime($loaded_at),
                    an.source        = $source_label,
                    an.loader        = $loader
    SET an.last_seen_at = datetime($loaded_at),
        an.last_run_id  = $run_id
)

// Note -> its reviewing Employee (MATCH only; null author matches nothing).
WITH row, fn
OPTIONAL MATCH (e:Employee {employee_id: row.author})
FOREACH (_ IN CASE WHEN e IS NOT NULL THEN [1] ELSE [] END |
    MERGE (fn)-[at:WAS_ATTRIBUTED_TO {role: 'feedback_author'}]->(e)
      ON CREATE SET at.first_seen_at = datetime($loaded_at),
                    at.source        = $source_label,
                    at.loader        = $loader
    SET at.last_seen_at = datetime($loaded_at),
        at.last_run_id  = $run_id
)

// Provenance tail — delta-only WAS_GENERATED_BY.
WITH row, fn
MATCH (run:JobRun {run_id: $run_id})
WITH row, fn, run, (fn.row_checksum IS NULL OR fn.row_checksum <> row.row_checksum) AS row_changed
FOREACH (_ IN CASE WHEN row_changed THEN [1] ELSE [] END |
    MERGE (fn)-[r:WAS_GENERATED_BY {source: $source_label}]->(run)
      ON CREATE SET r.first_seen_at = datetime($loaded_at)
    SET r.last_seen_at = datetime($loaded_at)
)
SET fn.row_checksum = row.row_checksum;
