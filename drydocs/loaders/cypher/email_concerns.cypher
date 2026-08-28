// email_concerns.cypher — the ONE authorized CONCERNS writer (Q21; gate
// email-folder-assignment SIGNED 8/8, 2026-08-19).
//
//   (:Document)-[:CONCERNS {endpoint_class, assigned_by, evidence}]->(:ControlMFolder | :ETLProcess)
//
// THE FENCE THIS FILE IS THE EXEMPTION TO: the lexical email loader
// (email_extracts.cypher) may NEVER gain this write — its guard test forbids
// these tokens there BY NAME, and this file is the named exception, not a
// widening. The K7 §A1 fence rides every edge written here: CONCERNS says
// what an email is ABOUT; no derived attribution/ownership/routing edge may
// ever cite it as a basis (§C1).
//
// MATCH-only on BOTH endpoints (the folder_attribution discipline): this
// writer mints no Document, no folder, no process. An assignment whose
// endpoint the graph does not hold writes nothing — the caller's summary
// counts it, never silently. assigned_by + evidence arrive validated
// (drydocs/loaders/email_concerns.py refuses the batch before any write —
// §A3: no anonymous assignment). Endpoint class rides the edge (§A2, the
// rua-load-shapes §B2 union-endpoint convention). Idempotent: MERGE on the
// triple; re-assertion refreshes the properties.
UNWIND $rows AS row
MATCH (d:Document {doc_id: row.doc_id})
MATCH (t)
WHERE (row.endpoint_class = 'ControlMFolder' AND t:ControlMFolder AND t.folder_id = row.endpoint_key)
   OR (row.endpoint_class = 'ETLProcess' AND t:ETLProcess AND t.token = row.endpoint_key)
MERGE (d)-[r:CONCERNS]->(t)
SET r.endpoint_class = row.endpoint_class,
    r.assigned_by    = row.assigned_by,
    r.evidence       = row.evidence,
    r.assigned_at    = datetime($assigned_at),
    r.vocab_id       = 'docs_email_concerns'
RETURN count(r) AS written
