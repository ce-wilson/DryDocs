// =============================================================================
// patch_window.cypher — READ-ONLY queries behind `drydocs patch-window` (P5).
//
// Given a host (ExecutionHost.nodeid) or a host group (ControlMHostGroup.name),
// return every job that can land on it, per the signed controlm-hosts-topology
// resolution rules (config/gate-log.md 2026-07-09):
//   * 2-hop group path : (job)-[:RUNS_ON {role:'host_group'}]->(group)
//                        -[:CONTAINS_HOST]->(host) — Control-M load-balances
//                        across the group's members, so EVERY member host
//                        inherits every group-routed job.
//   * 1-hop hard-coded : (job)-[:RUNS_ON {role:'agent_host'}]->(host).
//
// This file is parsed by drydocs/loaders/patch_window.py: each `// >>> name`
// marker starts a named statement. Statements are READ ONLY — the pass that
// WRITES RUNS_ON is runs_on_resolution.cypher; this one only reads what it
// derived (tests/unit/test_patch_window.py asserts no write verbs here).
//
// Every anchor carries the O33 guard (NOT :SchemaMeta): the schema meta-graph
// MERGEs keyless exemplars under the REAL labels (including property-qualified
// RUNS_ON edges), so an unguarded name/key MATCH would return phantom rows.
//
// Timing properties (avg_start_time / start_next_day / avg_run_time on the
// job; window_start / window_end on the folder) are the P4 supplement
// contract (gate controlm-avg-run-supplement §A). The supplement loader is
// currently company-side only (backlog note 15043cd), so producer-side rows
// return null there — the utility reports those jobs as NO_TIMING_DATA
// findings (the remediation feeder), never guesses.
// =============================================================================

// >>> host_exists
MATCH (h:ExecutionHost {nodeid: $target})
WHERE NOT h:SchemaMeta
RETURN count(h) AS n;

// >>> group_exists
MATCH (g:ControlMHostGroup {name: $target})
WHERE NOT g:SchemaMeta
RETURN count(g) AS n;

// >>> group_dcs
MATCH (g:ControlMHostGroup {name: $target})
WHERE NOT g:SchemaMeta
RETURN g.data_center AS data_center
ORDER BY data_center;

// -- host mode ---------------------------------------------------------------

// >>> host_direct
MATCH (j:ControlMJob)-[:RUNS_ON {role: 'agent_host'}]->(h:ExecutionHost {nodeid: $target})
WHERE NOT j:SchemaMeta AND NOT h:SchemaMeta
OPTIONAL MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(j)
  WHERE NOT f:SchemaMeta
RETURN j.job_name        AS job_name,
       j.job_id          AS job_id,
       'agent_host'      AS path,
       null              AS group_name,
       null              AS pinned_host,
       f.sched_table     AS folder,
       j.node_id         AS node_id,
       j.avg_start_time  AS avg_start_time,
       j.start_next_day  AS start_next_day,
       j.avg_run_time    AS avg_run_time,
       f.window_start    AS window_start,
       f.window_end      AS window_end
ORDER BY job_name;

// >>> host_via_group
MATCH (g:ControlMHostGroup)-[:CONTAINS_HOST]->(h:ExecutionHost {nodeid: $target})
WHERE NOT g:SchemaMeta AND NOT h:SchemaMeta
MATCH (j:ControlMJob)-[:RUNS_ON {role: 'host_group'}]->(g)
WHERE NOT j:SchemaMeta
OPTIONAL MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(j)
  WHERE NOT f:SchemaMeta
RETURN j.job_name        AS job_name,
       j.job_id          AS job_id,
       'host_group'      AS path,
       g.name            AS group_name,
       null              AS pinned_host,
       f.sched_table     AS folder,
       j.node_id         AS node_id,
       j.avg_start_time  AS avg_start_time,
       j.start_next_day  AS start_next_day,
       j.avg_run_time    AS avg_run_time,
       f.window_start    AS window_start,
       f.window_end      AS window_end
ORDER BY job_name;

// -- group mode ----------------------------------------------------------------

// >>> group_jobs
MATCH (j:ControlMJob)-[:RUNS_ON {role: 'host_group'}]->(g:ControlMHostGroup {name: $target})
WHERE NOT j:SchemaMeta AND NOT g:SchemaMeta
OPTIONAL MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(j)
  WHERE NOT f:SchemaMeta
RETURN j.job_name        AS job_name,
       j.job_id          AS job_id,
       'host_group'      AS path,
       g.name            AS group_name,
       null              AS pinned_host,
       f.sched_table     AS folder,
       j.node_id         AS node_id,
       j.avg_start_time  AS avg_start_time,
       j.start_next_day  AS start_next_day,
       j.avg_run_time    AS avg_run_time,
       f.window_start    AS window_start,
       f.window_end      AS window_end
ORDER BY job_name;

// >>> group_hardcoded
// Jobs PINNED to a member host of the group: patching those hosts affects
// these jobs too, and the pin itself bypasses the group's load balancing —
// each row doubles as a HARDCODED_BYPASS metadata finding.
MATCH (g:ControlMHostGroup {name: $target})-[:CONTAINS_HOST]->(h:ExecutionHost)
WHERE NOT g:SchemaMeta AND NOT h:SchemaMeta
MATCH (j:ControlMJob)-[:RUNS_ON {role: 'agent_host'}]->(h)
WHERE NOT j:SchemaMeta
OPTIONAL MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(j)
  WHERE NOT f:SchemaMeta
RETURN j.job_name        AS job_name,
       j.job_id          AS job_id,
       'agent_host'      AS path,
       g.name            AS group_name,
       h.nodeid          AS pinned_host,
       f.sched_table     AS folder,
       j.node_id         AS node_id,
       j.avg_start_time  AS avg_start_time,
       j.start_next_day  AS start_next_day,
       j.avg_run_time    AS avg_run_time,
       f.window_start    AS window_start,
       f.window_end      AS window_end
ORDER BY job_name;

// -- NODE_GROUP <-> RUNS_ON cross-validation (metadata findings) ---------------

// >>> xval_intent_without_edge
// A job whose raw node_id NAMES the target but that carries NO RUNS_ON edge
// to it: the declared intent and the derived topology disagree (resolution
// pass not rerun since the job landed, or the target was missing from the
// CM_HOSTS capture at resolution time).
MATCH (j:ControlMJob {node_id: $target})
WHERE NOT j:SchemaMeta
  AND NOT EXISTS {
    MATCH (j)-[:RUNS_ON]->(g:ControlMHostGroup {name: $target})
    WHERE NOT g:SchemaMeta
  }
  AND NOT EXISTS {
    MATCH (j)-[:RUNS_ON]->(h:ExecutionHost {nodeid: $target})
    WHERE NOT h:SchemaMeta
  }
RETURN j.job_name AS job_name, j.job_id AS job_id, j.node_id AS node_id
ORDER BY job_name;

// >>> xval_stale_edge_host
// The inverse drift: a RUNS_ON edge into the target host whose job's node_id
// has since CHANGED — the edge outlived the intent that created it.
MATCH (j:ControlMJob)-[:RUNS_ON {role: 'agent_host'}]->(h:ExecutionHost {nodeid: $target})
WHERE NOT j:SchemaMeta AND NOT h:SchemaMeta
  AND (j.node_id IS NULL OR j.node_id <> $target)
RETURN j.job_name AS job_name, j.job_id AS job_id, j.node_id AS node_id
ORDER BY job_name;

// >>> xval_stale_edge_group
MATCH (j:ControlMJob)-[:RUNS_ON {role: 'host_group'}]->(g:ControlMHostGroup {name: $target})
WHERE NOT j:SchemaMeta AND NOT g:SchemaMeta
  AND (j.node_id IS NULL OR j.node_id <> $target)
RETURN j.job_name AS job_name, j.job_id AS job_id, j.node_id AS node_id
ORDER BY job_name;
