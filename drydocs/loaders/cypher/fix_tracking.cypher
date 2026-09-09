// =============================================================================
// fix_tracking.cypher  —  drydocs.remediation.fix-tracking.v1 change-sets ->
//   the three ruled remediation_* properties on :ControlMJob / :ControlMFolder
//
// Gate remediation-fix-tracking, SIGNED OFF 2026-08-12 (config/gate-log.md).
// §C1 ruled a DEDICATED drydocs-load loader over C2's "a pass inside an
// existing Control-M loader", because a fix must be markable the hour its
// package ships and C2 would have coupled fix cadence to ingest cadence.
//
// MATCH, NEVER MERGE (§C1). A fix target that does not exist is an ERROR, not
// a node to invent — the fix package cites the graph's own keys, so a MERGE
// here would answer "which node did we fix?" by creating one. Note that MATCH
// alone does not RAISE on a miss, it silently writes nothing: the all-or-
// nothing preflight in fix_tracking.py is what turns a missing target into a
// refusal, and this template is only ever reached once every target resolved.
//
// FIX TRACKING IS A FOURTH AXIS (§A1). It never reuses the envelope names —
// source_created_by/at and source_updated_by/at stay source-system authorship
// (fence ratified at controlm-q1q3-phase1 / envelope-property-terms) — and it
// is not pull tracking (*_seen_at) or load provenance (WAS_GENERATED_BY). The
// remediation_ prefix is what keeps the four readable apart on a node
// inspector (§B1).
//
// TWO MODES, ONE TEMPLATE. $mode = 'apply' SETs the three properties;
// $mode = 'reject' REMOVEs them. The ruled enum has no 'rejected' member
// (§B2) — rejection is the caller's intent, not artifact content, so the same
// v1 change-set that applied a fix is what un-applies it. The reject branch is
// FENCED on remediation_fix_id: a stale rejection must never strip a NEWER
// fix's marks off the node, which is the one way this loader could destroy a
// fact it did not write.
//
// ONE DATE, THE LAST TRANSITION (§B3). remediation_status_date is overwritten
// on every transition; the full history lives in the fix package, which is
// where the alternative (per-status dates) was ruled out to avoid drift.
//
// Parameters: $batch (validated FixTrackingRow dicts — kind, label, folder_id,
//             job_id, display_name, and the three ruled properties),
//             $run_id, $loaded_at, $loader, $source_label, $mode.
// =============================================================================

UNWIND $batch AS row

// Resolve each row to its node, keyed on that label's NODE KEY verbatim
// (constraints.cypher), and drop anything that resolved to nothing so the write
// clauses below can never run against a null.
//
// THE SAME IDIOM THE PREFLIGHT USES, deliberately. _RESOLVE_TARGETS in
// fix_tracking.py resolves targets exactly this way, so "what the preflight
// checked" and "what the write touches" cannot be two different questions — a
// preflight that resolved by one rule while the write resolved by another would
// pass its check and still miss, which is the failure the preflight exists to
// prevent. Neither OPTIONAL MATCH can multiply rows: both patterns are NODE
// KEYs, so each matches at most one node, and the job pattern matches nothing
// for a folder row because its job_id is null and a property comparison against
// null never matches.
OPTIONAL MATCH (j:ControlMJob {folder_id: row.folder_id, job_id: row.job_id})
OPTIONAL MATCH (f:ControlMFolder {folder_id: row.folder_id})
WITH row, CASE row.kind WHEN 'job' THEN j WHEN 'folder' THEN f END AS n
WHERE n IS NOT NULL

// §B1 — the three ruled names, applied together. A partial application would
// leave a node claiming a status with no fix id to trace it to.
//
// THREE, AND ONLY THREE. No run id or timestamp rides along beside them: the
// gate ruled three property names, and "which run marked this fix, and when"
// is what the :JobRun edge below already answers. A fourth remediation_*
// property would be an unruled name in a ruled namespace, and §D1 gives
// property_terms entries to the ruled names — a property with no entry is
// exactly the drift that section exists to prevent.
FOREACH (_ IN CASE WHEN $mode = 'apply' THEN [1] ELSE [] END |
  SET n.remediation_fix_id      = row.remediation_fix_id,
      n.remediation_status      = row.remediation_status,
      n.remediation_status_date = date(row.remediation_status_date)
)

// Rejection removes the axis (§B2). Fenced on the fix id: the node keeps
// whatever a LATER fix wrote, and a rejection for a fix this node no longer
// carries is a no-op rather than a silent erasure.
FOREACH (_ IN CASE
           WHEN $mode = 'reject' AND n.remediation_fix_id = row.remediation_fix_id
           THEN [1] ELSE [] END |
  REMOVE n.remediation_fix_id,
         n.remediation_status,
         n.remediation_status_date
)

// Standard :JobRun provenance (§C1). Unconditional, unlike the delta-only
// WAS_GENERATED_BY the ingest loaders write (doc 06 Phase 2, provenance-edge
// diet): a fix-tracking run is a HUMAN INTERVENTION on a handful of nodes, not
// a nightly sweep over thousands, so there is no edge-count pressure to
// diet against — and "which run marked this fix, and when" is the question
// the axis exists to answer. It stays true for a rejection too, which is the
// run that removed the properties and would otherwise leave no trace at all.
WITH row, n
MATCH (run:JobRun {run_id: $run_id})
MERGE (n)-[r:WAS_GENERATED_BY {source: 'fix-tracking'}]->(run)
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.loader        = $loader,
                r.mode          = $mode
SET r.last_seen_at = datetime($loaded_at);
