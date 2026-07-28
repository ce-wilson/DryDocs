// =============================================================================
// runs_on_resolution.cypher  —  the derived NODE_ID resolution pass
//
// Gate: controlm-hosts-topology SIGNED OFF 2026-07-09 (config/gate-log.md).
// The signed rule (verbatim in substance):
//   NODE_ID = GRPNAME  -> RUNS_ON {role: host_group}   (2-hop; Control-M
//                          load-balances across the group's CONTAINS_HOST
//                          members)
//   else NODE_ID = NODEID -> RUNS_ON {role: agent_host} (1-hop hard-coded)
//   else UNMATCHED — reported as coverage, NEVER guessed; NULL -> no edge.
//   GROUP MATCH WINS when both match (mirrors Control-M's own resolution;
//   probe P4 expects zero collisions — the census is reported either way).
//
// This is a DERIVED pass (the WAS_INFORMED_BY precedent): it reads nothing
// from staging — both inputs are already in the graph (ControlMJob.node_id
// from the jobs pass; ControlMHostGroup / ExecutionHost from the hosts
// pass) — so it must run only after BOTH passes have loaded. It MATCHes
// endpoints, never MERGEs them.
//
// Group names are matched by name across data centers: the DC-scoping join
// (which DC's group a job's folder belongs to) is blocked on the same DC
// residuals as DEFINED_ON, so a name held by groups in several DCs edges to
// each — counted in coverage as multi_dc_group_jobs, never silently picked.
//
// Rerun host affinity (a rerun sticks to the first attempt's host) is
// RUNTIME state — phase-2 ControlMJobRun/SOSA, never these definition edges.
//
// Parameters (RunsOnResolutionPass): $run_id, $resolved_at, $loader.
// Coverage counts are queried separately by the pass and stamped onto its
// :JobRun — see drydocs/loaders/runs_on_resolution.py.
// =============================================================================

// -- 1. The 2-hop case: NODE_ID names a host group (group match wins). -------
// NOT :SchemaMeta (O33): the meta-graph exemplar carries the real label with
// name = the label string — a name-keyed MATCH could otherwise attach a real
// job's edge to the schema exemplar.
MATCH (j:ControlMJob)
WHERE j.node_id IS NOT NULL AND j.node_id <> '' AND NOT j:SchemaMeta
MATCH (g:ControlMHostGroup {name: j.node_id})
WHERE NOT g:SchemaMeta
MERGE (j)-[r:RUNS_ON {role: 'host_group'}]->(g)
  ON CREATE SET r.first_seen_at = datetime($resolved_at),
                r.derived       = true,
                r.source        = 'CM_DEF_VJOB.NODE_ID x CM_HOSTS.GRPNAME',
                r.loader        = $loader
SET r.last_seen_at = datetime($resolved_at),
    r.last_run_id  = $run_id;

// -- 2. The 1-hop case: NODE_ID hard-codes a member host — only when NO group
//       carries that name (the signed group-wins precedence). ----------------
MATCH (j:ControlMJob)
WHERE j.node_id IS NOT NULL AND j.node_id <> '' AND NOT j:SchemaMeta
  AND NOT EXISTS { MATCH (g:ControlMHostGroup {name: j.node_id}) WHERE NOT g:SchemaMeta }
MATCH (h:ExecutionHost {nodeid: j.node_id})
WHERE NOT h:SchemaMeta
MERGE (j)-[r:RUNS_ON {role: 'agent_host'}]->(h)
  ON CREATE SET r.first_seen_at = datetime($resolved_at),
                r.derived       = true,
                r.source        = 'CM_DEF_VJOB.NODE_ID x CM_HOSTS.NODEID',
                r.loader        = $loader
SET r.last_seen_at = datetime($resolved_at),
    r.last_run_id  = $run_id;
