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
`drydocs_api` is scanned. Since U9 (2026-08-02) the snapshot is the WHOLE
repo tree — every region (`.claude`, `docs`, `web`, `agents`, `scripts`, …)
is in the graph, and `project` is the first path segment. The artifact being
whole-repo is the ruled shape; the METRICS are what get scoped (U14).

Four standing rules for every query and every conclusion:
- **Exclude schema exemplars** (O33): always guard node anchors with
  `WHERE NOT m:SchemaMeta`, or exemplar nodes/edges contaminate results.
- **Exclude tombstones** (U13): the D7 sweep keeps removed modules as
  tombstones (`removed_from_source_at IS NOT NULL`) so deletions are
  visible — which means every metric query must filter
  `m.removed_from_source_at IS NULL` or say in one line why the dead belong
  in that answer. Proof case: after S2's package move, the unfiltered A3
  ranking placed the dead `drydocs_core/controlm/__init__.py` at #6, one
  slot below its live replacement. (A freshly re-provisioned graph carries
  zero tombstones — the 2026-08-03 wipe did — but they re-accumulate with
  every load after a move or delete, so the filter is not optional.)
- **Scope metrics to the package allow-list** (U14; **eight roots since U18,
  2026-08-09**): architecture metrics (orphans, untested, fan-in baselines)
  bind `m.project IN $packages` with `$packages = ['drydocs','drydocs_core',
  'drydocs_api','drydocs_remediation','drydocs_lineage','drydocs_deepdoc',
  'drydocs_docmeta','tests']`. This is an allow-list IN THE QUERIES, never an
  exclude in the scanner: 54 of 77 raw orphan hits were Anthropic-vendored
  `.claude/skills` scripts, which pollutes the metric but belongs in the tree.
  First-party Python OUTSIDE the packages (`agents/`, `scripts/`,
  `knowledge/`) is a separate, labeled queue — report it beside the baseline
  number, never folded in (it was never in the pre-U9 baselines, so folding it
  breaks comparability in the other direction).

  **The list is hand-typed, so check it against `pyproject.toml` before
  trusting any number.** `$packages` is the seven distributable packages in
  `[tool.poetry] packages` plus `tests`, which is a scan root and not a
  package. `drydocs_docmeta` was born 2026-08-04 in `d647171` — the same
  commit added it to `pyproject.toml` and the same day U14 typed seven roots
  here, so the allow-list was wrong from the hour it was written and ten
  modules were invisible to A3/A4/A5 for five days. This is the second
  instance (`drydocs_api` was the first, found at the U2 census), which is why
  `tests/unit/test_code_graph_review_plan.py` now fails when the typed list
  and `pyproject.toml` disagree.
- **IMPORTS ≠ breaks-if-removed** (gate D2 caveat): an edge records that an
  import statement resolves, not that the dependency is load-bearing.
- **IMPORTS edges are DELETED, not tombstoned, when a snapshot stops asserting them
  (U21, 2026-08-21).** Only NODES carry `removed_from_source_at`; the A1–A6 queries need
  no edge-level tombstone filter, and a live edge means the newest loaded snapshot asserts
  it. Before U21 the import graph was append-only (a deleted import kept its edge through
  every re-run and inflated fan-in / under-reported A5), so any fan-in baseline recorded
  before that date was measured on a graph that could only grow. `edges_retracted` on the
  :JobRun says how many the last load removed.

| # | Query (run against database `drydocs`) | Debt category it measures |
|---|---|---|
| A1 | `MATCH (m:CodeModule {project:'drydocs_core'})-[:IMPORTS]->(t:CodeModule) WHERE NOT m:SchemaMeta AND NOT t:SchemaMeta AND m.removed_from_source_at IS NULL AND t.removed_from_source_at IS NULL AND t.project IN ['drydocs','drydocs_api','drydocs_deepdoc','drydocs_remediation','drydocs_lineage','drydocs_docmeta'] RETURN m.file_id, t.file_id` | **Architecture debt** — layering violations: the core layer importing upward. Baseline 0; any row is a finding. Cross-check `tests/unit/test_module_boundary.py`. NOTE: this query carries its OWN hardcoded upward list, so it needed the U18 eighth root too — a core module importing `drydocs_docmeta` was unaskable before 2026-08-09. Re-probed at the widening: still **0**. |
| A2 | `MATCH (m:CodeModule {circular:true}) WHERE NOT m:SchemaMeta AND m.removed_from_source_at IS NULL RETURN m.file_id` plus live cross-check `MATCH (a:CodeModule)-[:IMPORTS*2..8]->(a) WHERE NOT a:SchemaMeta AND a.removed_from_source_at IS NULL RETURN count(DISTINCT a)` | **Code debt** — circular imports. Baseline 0 by both probes; scanner-vs-graph disagreement is itself a finding. |
| A3 | `MATCH (m:CodeModule)<-[:IMPORTS]-(x:CodeModule) WHERE NOT m:SchemaMeta AND NOT x:SchemaMeta AND m.removed_from_source_at IS NULL AND x.removed_from_source_at IS NULL AND m.project IN $packages RETURN m.file_id, count(x) AS fan_in ORDER BY fan_in DESC LIMIT 15` | **Code debt** — change-risk hotspots: high fan-in means a small edit ripples wide. Read the top entries' diff history first in any review. `x` is deliberately unscoped: an importer in `agents/` is real fan-in. Baselines, old beside new so runs compare like with like: `loaders/base.py` = 29 (seven roots, 2026-08-04) → **31** (eight roots, 2026-08-09 at `2d104ef`). **All of that movement is tree drift, none of it the eighth root** — measured both ways on the same graph and the top-15 is byte-identical, because `drydocs_docmeta`'s highest fan-in is `connectors/base.py` at 7, well under the list's 13 cutoff. |
| A4 | `MATCH (m:CodeModule) WHERE NOT m:SchemaMeta AND m.removed_from_source_at IS NULL AND m.extension = '.py' AND m.project IN $packages AND NOT ()-[:IMPORTS]->(m) AND NOT (m)-[:IMPORTS]->() AND m.project <> 'tests' AND NOT m.file_id CONTAINS '__init__' RETURN m.file_id` | **Code debt** — dead-code candidates (no imports either direction). Package scope: **0** at seven roots (2026-08-04) and **0** at eight (2026-08-09, `2d104ef`) — every `drydocs_docmeta` module has at least one importer, so the eighth root adds nothing here. Against the old 24 baseline. The separate first-party queue (swap the scope to `['agents','scripts','knowledge']`): 22 candidates → **4** after the U19 instrument fix (2026-08-09, depgraph `6ee0af6`), with `agents/` going 15 → **0**. Roughly four in five of that queue was a scanner artifact rather than dead code. All four survivors are subprocess-invoked entry points (`filter_ignored.py`, `probe_instrument.py`, `benchmark_p0.py`, `extract_office_text.py`), so the reading is zero first-party dead modules. Report it beside the baseline, never folded in. Every hit still needs a human disposition: entry point (CLI, script, pytest) vs genuinely dead. |
| A5 | `MATCH (m:CodeModule) WHERE NOT m:SchemaMeta AND m.removed_from_source_at IS NULL AND m.extension = '.py' AND m.project IN $packages AND m.project <> 'tests' AND NOT EXISTS { MATCH (t:CodeModule {project:'tests'})-[:IMPORTS]->(m) WHERE NOT t:SchemaMeta } RETURN m.file_id` | **Test debt** — modules no test imports (direct-import proxy only; fixtures and subprocess-level coverage won't show). Baselines: **29** (seven roots, 2026-08-04) → **27** (seven roots, 2026-08-09 at `2d104ef`) → **29** (eight roots, same graph). **Read those three numbers, not the first and last** — the eight-root figure lands back on 29 by coincidence: the tree lost two untested modules while the eighth root contributed exactly two, so quoting 29 → 29 would report "no change" across two real movements in opposite directions. The eighth root's two are `drydocs_docmeta/connectors/filedrop.py` and `drydocs_docmeta/connectors/web.py`, and they belong in the untested list rather than being absent from it. Raw whole-repo `.py` reads 129 — vendored pollution, not test debt. |
| A6 | `MATCH (a:CodeModule)-[:IMPORTS]->(b:CodeModule) WHERE NOT a:SchemaMeta AND NOT b:SchemaMeta AND a.removed_from_source_at IS NULL AND b.removed_from_source_at IS NULL AND a.project <> b.project RETURN a.project, b.project, count(*) ORDER BY count(*) DESC` | **Architecture debt** — cross-root coupling map; compare against MODULE_MAP.md's declared component boundaries. Unscoped on purpose: `IMPORTS` edges only exist between Python files, and post-U9 rows involving `agents/` or `scripts/` are first-party coupling worth seeing. |

**Step 0 — is the graph current? (U22)** Before reading any number off the
graph, run `poetry run drydocs code-graph-freshness`. It compares
`max(:CodeModule.last_seen_at)` against the newest `knowledge/depgraph-snapshots/
drydocs-*.json` `meta.captured_at` and prints ONE line naming the verdict
(FRESH / STALE by N days / EMPTY / NO SNAPSHOT / DATABASE UNREACHABLE), the run
id that last loaded and the snapshot it compared. Quote that line beside every
A1–A6 number. It is warn-only and never refreshes anything: a STALE verdict
means `drydocs load-code-snapshot` first — the 2026-08-13 reading of A3 = 28 was
an eleven-day-old graph that looked current, and UNREACHABLE is never "fresh".

**Step 0b — the delta, not the prose (U25).** `poetry run python
knowledge/depgraph-snapshots/metrics_ledger.py --delta` prints A3/A4/A5 and
live-vs-snapshot IMPORTS between the last two `debt-metrics.jsonl` rows (one
row per `snapshot.ps1` run). Report THAT delta in the A3/A4/A5 sections and
quote the row's commit; the hand-typed baselines in the table below are history
from before the ledger existed, not numbers to re-derive.

How to run: no CLI query command exists yet — use a short scratchpad script
with `Neo4jSettings` from `drydocs_core.config` (reads `.env`; raw
`os.environ` lacks the password) and `Neo4jClient` as a context manager.

### No-database fallback (offline)

The skill must never hard-depend on Neo4j (same decoupling rule as the
session ritual, gate H3). Without a running container, answer the same
questions from the newest snapshot JSON directly:

- `knowledge/depgraph-snapshots/drydocs-<latest>.json` — `nodes` (with
  `file_id`, `project`) and `edges` (`[src_file_id, dst_file_id]` pairs)
  support A1/A3/A4/A5/A6 with a few lines of Python (no SchemaMeta or
  tombstone guard needed — exemplars and tombstones exist only in the
  loaded graph; the snapshot is the live tree by construction); the
  package allow-list (U14) still applies, as a `file_id` first-segment
  filter. `circular_files` in the stats line covers A2.
- `knowledge/depgraph-snapshots/viewer.html` — visual inspection of the
  same snapshot, useful for the A6 coupling picture.

Findings feed the Prioritization Framework above (code debt: A2/A3/A4;
architecture debt: A1/A6; test debt: A5) and route through the IDEAS inbox,
never directly into `backlog.yaml` or the graph.
