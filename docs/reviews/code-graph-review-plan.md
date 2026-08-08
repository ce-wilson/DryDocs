# DryDocs — Code-Graph Multi-Persona Review (plan)

> **STATUS: PLANNED (2026-07-27).** Written the day the G33 self-documentation
> loader went live. The graph facts quoted below were probed against the real
> `drydocs` database (snapshot `drydocs-20260727-1732.json`, commit `4417d02`)
> — this plan is grounded, not hypothetical. Successor of the 2026-06 persona
> review routine (`persona-review-plan.md`, superseded), reusing its
> checkpoint-per-unit protocol.

**What changed to make this possible:** the depgraph ritual's output is now a
queryable subgraph — `(:Project {project_id:'drydocs'})` → 183 `:CodeModule` →
98 `IMPORTS` — loaded by `drydocs load-code-snapshot` (G33, gate
`self-documentation-code-graph`). A code review can now START from graph
queries and spend reading time only where the graph points.

**The honest limits, up front (do not oversell):**
- `IMPORTS` cannot distinguish `import x` / `from x import y` /
  `TYPE_CHECKING`-only (gate §D2). Never read it as "breaks if removed".
- `IMPORTS` edges exist only between intra-repo Python files — entry points
  invoked by packaging (CLI scripts, API apps) can look like orphans. Orphan
  queries produce CANDIDATES for a human read, never verdicts. (Since U9,
  2026-08-02, the snapshot is the WHOLE repo tree, not six scan roots — see
  the scope rule below the seed queries.)
- The code↔operational join (module → the :ControlMJob its Cypher writes) does
  NOT exist (gate §H5) — it is a named future item, not something to fake with
  string matching.

## Preconditions (once per review run)

1. Neo4j up (`neo4jtest`), `.env` targeting `drydocs` (NOT the home db —
   dev-environment.yaml; drift found and fixed 2026-07-27).
2. Fresh graph: `snapshot.ps1` → `poetry run drydocs load-code-snapshot`
   (idempotent; picks the newest `drydocs-YYYYMMDD[-HHMM].json` by PARSED
   timestamp).
3. For Phase 3 only: `poetry run drydocs load-doc-traceability` — the
   DesignDoc/Requirement/Component subgraph is EMPTY in `drydocs` today
   (probed 2026-07-27); the writer persona joins against it.

## Execution protocol (from the persona-review routine, proven 2026-06)

Run as one session per phase, or as the hourly cron pattern if budget-limited.
Checkpoint file: `docs/reviews/CODE-GRAPH-CHECKPOINT.md` (create on first run:
phase / task / next_action / run log; append after EVERY unit). Findings go to
one file per persona: `persona-python-architect-2026-07.md`,
`persona-project-manager-2026-07.md`, `persona-tech-writer-2026-07.md`.
Anything actionable ends as an IDEAS inbox line (tagged) for the next groom —
findings never edit backlog.yaml directly.

## Phase 1 — Python architect (skills: `architecture`, `code-review`, `tech-debt`)

**Mandate.** Structural health of the six scan roots, graph-first: query,
rank, then read only the flagged files.

Seed queries. Two standing filters ride EVERY query since U13/U14
(2026-08-04); the canonical, fully-written forms live in the tech-debt
skill's A1–A6 pack — this table is the question-and-baseline view:

- **Tombstones out** (U13): the D7 sweep keeps removed modules as
  `removed_from_source_at IS NOT NULL` tombstones, so every query filters
  `removed_from_source_at IS NULL` unless its row says why the dead belong.
  Proof case: post-S2, the unfiltered A3 ranked the dead
  `drydocs_core/controlm/__init__.py` at #6, one slot below its live
  replacement.
- **Metrics scoped to `$packages`** (U14): the U9 whole-tree snapshot is
  the ruled artifact, but the METRIC queries bind
  `m.project IN ['drydocs','drydocs_core','drydocs_api',
  'drydocs_remediation','drydocs_lineage','drydocs_deepdoc','tests']` — the
  seven roots the pre-U9 baselines were measured on. Vendored
  `.claude/skills` scripts stay in the tree and out of the metrics (they
  were 54 of 77 raw orphan hits). First-party Python outside the packages
  (`agents/`, `scripts/`, `knowledge/`) is a separate labeled queue,
  reported beside the baseline, never folded in.

| # | Question | Query sketch | Baseline (scope written next to each number) |
|---|---|---|---|
| A1 | Layering: does `drydocs_core` import any app layer? | `MATCH (m:CodeModule {project:'drydocs_core'})-[:IMPORTS]->(t) WHERE t.project IN ['drydocs','drydocs_deepdoc','drydocs_remediation','drydocs_lineage'] ...` + both tombstone filters | **0 — clean** (2026-07-27 six-root scan; scope inherent in the projects named) |
| A2 | Circular imports | `MATCH (m:CodeModule {circular:true}) ...` + tombstone filter; cross-check with a live cycle query (`(m)-[:IMPORTS*2..6]->(m)`) — a disagreement between scanner verdict and graph is itself a finding (§C3) | scanner says 0 (2026-07-27, six-root; unchanged 2026-08-04 all-files) |
| A3 | Fan-in hotspots (change-risk ranking) | `MATCH (m)<-[:IMPORTS]-(x) WHERE ... m.project IN $packages RETURN m.file_id, count(x) ORDER BY count(x) DESC` — `x` unscoped (an `agents/` importer is real fan-in), both ends tombstone-filtered | `loaders/base.py` = 18 (2026-07-27, six-root) → **29** (2026-08-04, all-files scan, package scope) — read ITS diff history first in any review |
| A4 | Orphan candidates | no in- or out-IMPORTS, `extension = '.py'`, `project IN $packages`, project <> 'tests', name <> '__init__.py', tombstone-filtered | 24 candidates (2026-07-27, six-root) → **0 in-package** (2026-08-04, package scope; raw whole-repo `.py` reads 77, of which 54 vendored). The first-party non-package queue (`agents/` 15, `scripts/` 4, `knowledge/` 3) = **22 candidates** — separate queue, never in the 24 baseline |
| A5 | Test coverage shape | which non-test modules have NO tests-project importer — `MATCH (m) WHERE ... m.extension='.py' AND m.project IN $packages AND m.project<>'tests' AND NOT EXISTS {MATCH (t {project:'tests'})-[:IMPORTS]->(m)} RETURN m` + tombstone filter | **29** (2026-08-04, package scope; raw whole-repo `.py` reads 129 — vendored pollution, not test debt) |
| A6 | Cross-root coupling map | `MATCH (a)-[:IMPORTS]->(b) WHERE a.project<>b.project RETURN a.project,b.project,count(*)` + both tombstone filters — compare against MODULE_MAP's declared component boundaries | unprobed. Unscoped on purpose: `IMPORTS` edges only join Python files, and post-U9 rows involving `agents/`/`scripts/` are first-party coupling worth seeing |

Deliverable: findings ranked by the tech-debt skill's (Impact+Risk)×(6−Effort)
score, each with the query that found it and the file(s) read to confirm.

## Phase 2 — Project manager (skills: `groom-backlog`, `analyze`)

**Mandate.** Is `backlog.yaml` telling the truth about what is done and what
is left — audited against the code that actually exists?

Units:
1. **Done-claims spot check.** For every item closed in the last ~30 days
   whose close_note names modules/files, confirm each named `file_id` exists
   in the graph (`MATCH (m:CodeModule {file_id:$f})`) — and RETURN
   `removed_from_source_at`, because tombstones belong in this answer: a hit
   that is a tombstone means the file existed and was since removed, a
   different disposition than never-existed (typo'd claim).
2. **Module-registry census.** backlog `modules:` registry vs the graph's
   `project` regions + top-level `file_id` prefixes: every graph region should
   be claimable by some module; every module should still have files. (The
   D7 sweep makes deletions visible — this unit queries
   `removed_from_source_at IS NOT NULL` deliberately; the dead ARE the
   answer here.)
3. **Todo reality check.** For `next_ready` items, do their `inputs:` paths
   still exist (graph for .py, filesystem for the rest)? Stale inputs = the
   item needs a re-groom before an agent burns a session on it.
4. **Epic coverage view.** Per epic, which scan roots its items touched
   (close_note file mentions × graph) — surfaces epics whose code footprint
   is drifting from their charter.

Deliverable: a drift table (item → claim → graph verdict) + IDEAS lines for
every mismatch; NO direct backlog edits (groom owns those).

## Phase 3 — Technical writer (skill: `documentation`)

**Mandate.** Status of the current documents, joined to the code they claim
to describe. Precondition: `load-doc-traceability` (subgraph empty today).
All prose this persona writes — and any staleness verdict on existing prose —
follows [`docs/style/us-business-english.md`](../style/us-business-english.md)
(U.S. business-technical English, never UK/EU idiom; mechanism names are never
renamed by a style judgment — that scope fence is in the guide).

Units:
1. **Component↔module join.** `:Component.ref` values (traceability matrix
   citations) vs `:CodeModule.file_id` — matrix rows citing files that moved
   or died; modules with heavy fan-in (A3 list) that NO doc component cites.
2. **Staleness ranking.** `DesignDoc.commit` vs `Project.git_commit`
   (`4417d02` today): how many commits behind is each doc's last touch, and
   does its cited component list still exist? Rank the re-verify queue.
3. **Coverage gaps by subsystem.** Six scan roots × DesignDoc coverage —
   which root has the thinnest doc coverage relative to its module count
   (baseline: tests 85, drydocs 41, drydocs_core 35, lineage 12,
   remediation 7, deepdoc 3).
4. **The §DEP sections of the SDLC docs** (`sdlc-*.md`) — regenerate their
   dependency claims FROM the graph instead of prose memory; any
   contradiction is a doc bug to log.

Deliverable: a doc-status board (doc → last commit → cited components alive?
→ verdict fresh/stale/orphaned) + IDEAS lines.

## Skill-integration verdicts (the "can they use it?" question — answered by inspection 2026-07-27)

**`tech-debt` skill — YES, as an evidence source, no skill edit required.**
The skill is a generic categorize-and-prioritize framework; nothing in it
reads files or graphs itself — the session running it gathers evidence. The
graph upgrades that evidence from anecdote to measurement for two of its six
categories (code debt: A2/A3/A4; architecture debt: A1/A6). OPTIONAL
follow-up: add a "DryDocs graph evidence" section to the skill with the Phase
1 query pack, so every future tech-debt run starts from the same queries.
Caveat that must ride any such edit: the skill must degrade gracefully with
NO database running (the snapshot JSON + viewer.html remain the fallback —
same decoupling rule as the session ritual, §H3).

**`groom-backlog` skill — YES for validation, NO for the groom itself.**
Grooming is a yaml-transcription task and must keep working offline; the
graph adds a VALIDATION pass, not a dependency: (a) an item's `module:` field
can be sanity-checked against the graph census (Phase 2 unit 2); (b)
close_note file claims can be verified before flipping `done` (unit 1).
OPTIONAL follow-up: a short "graph cross-check (optional, needs Neo4j)"
subsection in the skill's mechanics — explicitly optional, never a groom
blocker.

Both verdicts fold into this plan's phases rather than requiring skill edits
up front; promote the two OPTIONAL follow-ups via IDEAS if the first review
run proves the queries earn their keep.

## Backlog hook

This plan is the artifact; the work items (one per phase, plus the two
optional skill-edit follow-ups) go through the normal groom — an IDEAS inbox
line points here. Phase 1 has no dependencies; Phase 2/3 are independent of
each other; none is HITL (read-only analysis, findings routed through IDEAS).
