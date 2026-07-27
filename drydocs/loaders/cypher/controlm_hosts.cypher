// =============================================================================
// controlm_hosts.cypher  —  psgmgr.CM_HOSTS -> :ControlMHostGroup +
//                           :ExecutionHost + CONTAINS_HOST
//
// Gate: controlm-hosts-topology SIGNED OFF 2026-07-09 (config/gate-log.md;
// spec config/gate-prompts/controlm-hosts-topology.yaml). Bindings:
//   * ControlMHostGroup (prov:Collection) — NOT "ControlMGroup", which would
//     collide with the CM_DEF_VJOB.GROUP_NAME application-group concept.
//   * Member hosts REUSE ExecutionHost (prov:SoftwareAgent), keyed on nodeid
//     alone (multi-group membership expected; probe P2c pending).
//   * CONTAINS_HOST = prov:hadMember (CONTAINS_JOB / CONTAINS_FOLDER family),
//     carries participation_type + last_capture_date.
//
// Group grain is (data_center, name) — the same GRPNAME can exist per DC
// (constraint controlmhostgroup_key). The object is NOT versioned; one row
// per (DATA_CENTER, GRPNAME, NODEID).
//
// DELIBERATELY NOT WRITTEN HERE: (:ControlMHostGroup)-[:DEFINED_ON]->
// (:ControlMServer). The DC key rule is signed (exact long-form match) but
// the CM_HOSTS-vs-CM_DEF_VTAB value-domain verification (probe P3) and the
// 22-DC-vs-production scope call are still open gate-log residuals — and the
// folder pass keys ControlMServer on the SHORT form today. The vocabulary
// term m3_host_group_defined_on stays status: planned until those close.
//
// The job wiring — RUNS_ON {role: host_group | agent_host} — is NOT this
// pass either: it is the derived resolution pass (runs_on_resolution.cypher)
// that runs only after BOTH the jobs pass and this pass have loaded.
//
// Parameters (passed by BaseLoader._flush):
//   $batch        list of dicts matching the projection columns
//   $run_id       UUID of this loader's :JobRun
//   $loaded_at    ISO datetime string
//   $loader       loader version tag
//   $source_label 'csv' (sample mode) or 'oracle' (production)
// =============================================================================

UNWIND $batch AS row

// Host group upsert — one node per (DATA_CENTER, GRPNAME).
MERGE (g:ControlMHostGroup:Collection {data_center: row.data_center, name: row.grpname})
  ON CREATE SET g.first_seen_at = datetime($loaded_at),
                g.source     = 'psgmgr.CM_HOSTS'
SET g.last_seen_at = datetime($loaded_at),
    g.last_run_id  = $run_id

// Member agent host upsert — one node per distinct NODEID (keyed on nodeid
// alone; the same host legitimately appears in many groups).
MERGE (h:ExecutionHost:Agent {nodeid: row.nodeid})
  ON CREATE SET h.first_seen_at = datetime($loaded_at),
                h.source     = 'psgmgr.CM_HOSTS'
SET h.last_seen_at = datetime($loaded_at),
    h.last_run_id  = $run_id

// Group membership (prov:hadMember; m3_host_group_contains_host).
MERGE (g)-[m:CONTAINS_HOST]->(h)
  ON CREATE SET m.first_seen_at = datetime($loaded_at),
                m.source        = 'psgmgr.CM_HOSTS',
                m.loader        = $loader
SET m.participation_type = row.participation_type,
    m.last_capture_date  = CASE WHEN row.capture_date IS NULL OR row.capture_date = '' THEN null
                                ELSE datetime(replace(row.capture_date, ' ', 'T')) END,
    m.last_seen_at       = datetime($loaded_at),
    m.last_run_id        = $run_id;
