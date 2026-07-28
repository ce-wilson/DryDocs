---
name: tech-debt
description: Identify, categorize, and prioritize technical debt. Trigger with "tech debt", "technical debt audit", "what should we refactor", "code health", or when the user asks about code quality, refactoring priorities, or maintenance backlog.
---

# Tech Debt Management

Systematically identify, categorize, and prioritize technical debt.

## Categories

| Type | Examples | Risk |
|------|----------|------|
| **Code debt** | Duplicated logic, poor abstractions, magic numbers | Bugs, slow development |
| **Architecture debt** | Monolith that should be split, wrong data store | Scaling limits |
| **Test debt** | Low coverage, flaky tests, missing integration tests | Regressions ship |
| **Dependency debt** | Outdated libraries, unmaintained dependencies | Security vulns |
| **Documentation debt** | Missing runbooks, outdated READMEs, tribal knowledge | Onboarding pain |
| **Infrastructure debt** | Manual deploys, no monitoring, no IaC | Incidents, slow recovery |

## Prioritization Framework

Score each item on:
- **Impact**: How much does it slow the team down? (1-5)
- **Risk**: What happens if we don't fix it? (1-5)
- **Effort**: How hard is the fix? (1-5, inverted — lower effort = higher priority)

Priority = (Impact + Risk) x (6 - Effort)

## Output

Produce a prioritized list with estimated effort, business justification for each item, and a phased remediation plan that can be done alongside feature work.

## DryDocs graph evidence (query pack A1–A6)

This repo self-documents: the `drydocs` Neo4j database carries a code graph
(`:CodeModule` + `IMPORTS`, loaded by `drydocs load-code-snapshot` from the
newest `knowledge/depgraph-snapshots/drydocs-*.json`). Use it to ground debt
claims in evidence instead of impressions. Trustworthy since the U6 scanner
fix (2026-07-28): cross-root and function-level imports are recorded and
`drydocs_api` is scanned (baseline 205 modules / 370 edges). `scripts/` is
still NOT a scan root — treat "imported only by scripts/" modules accordingly.

Two standing rules for every query and every conclusion:
- **Exclude schema exemplars** (O33): always guard node anchors with
  `WHERE NOT m:SchemaMeta`, or exemplar nodes/edges contaminate results.
- **IMPORTS ≠ breaks-if-removed** (gate D2 caveat): an edge records that an
  import statement resolves, not that the dependency is load-bearing.

| # | Query (run against database `drydocs`) | Debt category it measures |
|---|---|---|
| A1 | `MATCH (m:CodeModule {project:'drydocs_core'})-[:IMPORTS]->(t:CodeModule) WHERE NOT m:SchemaMeta AND NOT t:SchemaMeta AND t.project IN ['drydocs','drydocs_api','drydocs_deepdoc','drydocs_remediation','drydocs_lineage'] RETURN m.file_id, t.file_id` | **Architecture debt** — layering violations: the core layer importing upward. Baseline 0; any row is a finding. Cross-check `tests/unit/test_module_boundary.py`. |
| A2 | `MATCH (m:CodeModule {circular:true}) WHERE NOT m:SchemaMeta RETURN m.file_id` plus live cross-check `MATCH (a:CodeModule)-[:IMPORTS*2..8]->(a) WHERE NOT a:SchemaMeta RETURN count(DISTINCT a)` | **Code debt** — circular imports. Baseline 0 by both probes; scanner-vs-graph disagreement is itself a finding. |
| A3 | `MATCH (m:CodeModule)<-[:IMPORTS]-(x:CodeModule) WHERE NOT m:SchemaMeta AND NOT x:SchemaMeta RETURN m.file_id, count(x) AS fan_in ORDER BY fan_in DESC LIMIT 15` | **Code debt** — change-risk hotspots: high fan-in means a small edit ripples wide. Read the top entries' diff history first in any review. |
| A4 | `MATCH (m:CodeModule) WHERE NOT m:SchemaMeta AND m.removed_from_source_at IS NULL AND NOT ()-[:IMPORTS]->(m) AND m.project <> 'tests' AND NOT m.file_id CONTAINS '__init__' RETURN m.file_id` | **Code debt** — dead-code candidates. Post-U6 the signal is real, but every hit still needs a human disposition: entry point (CLI, script, pytest) vs genuinely dead. |
| A5 | `MATCH (m:CodeModule) WHERE NOT m:SchemaMeta AND m.project <> 'tests' AND NOT EXISTS { MATCH (t:CodeModule {project:'tests'})-[:IMPORTS]->(m) WHERE NOT t:SchemaMeta } RETURN m.file_id` | **Test debt** — modules no test imports (direct-import proxy only; fixtures and subprocess-level coverage won't show). |
| A6 | `MATCH (a:CodeModule)-[:IMPORTS]->(b:CodeModule) WHERE NOT a:SchemaMeta AND NOT b:SchemaMeta AND a.project <> b.project RETURN a.project, b.project, count(*) ORDER BY count(*) DESC` | **Architecture debt** — cross-root coupling map; compare against MODULE_MAP.md's declared component boundaries. |

How to run: no CLI query command exists yet — use a short scratchpad script
with `Neo4jSettings` from `drydocs_core.config` (reads `.env`; raw
`os.environ` lacks the password) and `Neo4jClient` as a context manager.

### No-database fallback (offline)

The skill must never hard-depend on Neo4j (same decoupling rule as the
session ritual, gate H3). Without a running container, answer the same
questions from the newest snapshot JSON directly:

- `knowledge/depgraph-snapshots/drydocs-<latest>.json` — `nodes` (with
  `file_id`, `project`) and `edges` (`[src_file_id, dst_file_id]` pairs)
  support A1/A3/A4/A5/A6 with a few lines of Python (no SchemaMeta guard
  needed — exemplars exist only in the loaded graph); `circular_files`
  in the stats line covers A2.
- `knowledge/depgraph-snapshots/viewer.html` — visual inspection of the
  same snapshot, useful for the A6 coupling picture.

Findings feed the Prioritization Framework above (code debt: A2/A3/A4;
architecture debt: A1/A6; test debt: A5) and route through the IDEAS inbox,
never directly into `backlog.yaml` or the graph.
