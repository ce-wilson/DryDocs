// =============================================================================
// doc_traceability.cypher  —  traceability-matrix rows -> :Requirement +
// :Component + :TestCase + the star (SPECIFIED_IN / IMPLEMENTED_BY /
// VERIFIED_BY). L7 connector #1, pass 2 of 3 (gate doc-traceability-feedback
// signed off 2026-07-20 — config/gate-log.md). One ROW = one matrix table row,
// fanned out per gate B4 (star off :Requirement, mirroring the table shape).
//
// PREREQ: doc_sections.cypher ran first — SPECIFIED_IN MATCHes (NEVER MERGEs)
// its :DocSection target, so a mis-cited anchor silently drops that edge
// instead of creating a stub section (the bmc_docs DESCRIBES convention).
// PREREQ ENFORCEMENT (L17, Q8 family): this template cannot check the
// whole-registry condition (it runs per batch) —
// DocTraceabilityLoader._assert_doc_sections_present refuses the load up
// front when NO :DocSection is reachable (a relationship cannot span databases
// — point at the DB that holds the doc_sections.v1 output), and
// _report_unmatched_anchors lists every per-row MATCH miss after the load.
// :Component / :TestCase ARE MERGEd here — this loader is their source of
// record, keys (origin, ref) per gate A2 (same-basename-within-origin stays
// an SME-merge case, gate D1 — never auto-merged here).
//
// Parameters: $batch (origin, doc_id, requirement_id, kind, description,
//   matrix_status, section_anchors [list], components [list],
//   tests [list of {kind, ref}], row_checksum),
//   $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

MERGE (req:Requirement:Entity {origin: row.origin, requirement_id: row.requirement_id})
  ON CREATE SET req.first_seen_at = datetime($loaded_at),
                req.source     = $source_label
SET req.kind          = row.kind,
    req.description   = row.description,
    req.matrix_status = row.matrix_status,
    req.doc_id        = row.doc_id,
    req.last_seen_at  = datetime($loaded_at),
    req.last_run_id   = $run_id

// Components — MERGEd here (source of record), edge in the same FOREACH.
FOREACH (ref IN row.components |
    MERGE (comp:Component:Entity {origin: row.origin, ref: ref})
      ON CREATE SET comp.first_seen_at = datetime($loaded_at),
                    comp.source     = $source_label
    SET comp.last_seen_at = datetime($loaded_at),
        comp.last_run_id  = $run_id
    MERGE (req)-[ib:IMPLEMENTED_BY]->(comp)
      ON CREATE SET ib.first_seen_at = datetime($loaded_at),
                    ib.source        = $source_label,
                    ib.loader        = $loader
    SET ib.last_seen_at = datetime($loaded_at),
        ib.last_run_id  = $run_id
)

// Test/verify citations — MERGEd here, kind is the OPEN enum (gate A7/D2).
FOREACH (t IN row.tests |
    MERGE (tc:TestCase:Entity {origin: row.origin, ref: t.ref})
      ON CREATE SET tc.first_seen_at = datetime($loaded_at),
                    tc.source     = $source_label
    SET tc.kind         = t.kind,
        tc.last_seen_at = datetime($loaded_at),
        tc.last_run_id  = $run_id
    MERGE (req)-[vb:VERIFIED_BY]->(tc)
      ON CREATE SET vb.first_seen_at = datetime($loaded_at),
                    vb.source        = $source_label,
                    vb.loader        = $loader
    SET vb.last_seen_at = datetime($loaded_at),
        vb.last_run_id  = $run_id
)

// SPECIFIED_IN — MATCH only (prereq above). UNWIND the cited anchors; the
// CASE wrapper keeps zero-anchor rows alive through the UNWIND (null anchor
// matches nothing, FOREACH guard no-ops — the bmc_docs prev-chunk idiom).
WITH row, req
UNWIND (CASE WHEN size(row.section_anchors) = 0 THEN [null] ELSE row.section_anchors END) AS sa
OPTIONAL MATCH (ds:DocSection {origin: row.origin, doc_id: row.doc_id, anchor: sa})
FOREACH (_ IN CASE WHEN ds IS NOT NULL THEN [1] ELSE [] END |
    MERGE (req)-[si:SPECIFIED_IN]->(ds)
      ON CREATE SET si.first_seen_at = datetime($loaded_at),
                    si.source        = $source_label,
                    si.loader        = $loader
    SET si.last_seen_at = datetime($loaded_at),
        si.last_run_id  = $run_id
)

// Provenance tail — delta-only WAS_GENERATED_BY on the Requirement. The
// DISTINCT collapses the section-anchor fan-out back to one row per
// requirement before the checksum compare.
WITH DISTINCT row, req
MATCH (run:JobRun {run_id: $run_id})
WITH row, req, run, (req.row_checksum IS NULL OR req.row_checksum <> row.row_checksum) AS row_changed
FOREACH (_ IN CASE WHEN row_changed THEN [1] ELSE [] END |
    MERGE (req)-[r:WAS_GENERATED_BY {source: $source_label}]->(run)
      ON CREATE SET r.first_seen_at = datetime($loaded_at)
    SET r.last_seen_at = datetime($loaded_at)
)
SET req.row_checksum = row.row_checksum;
