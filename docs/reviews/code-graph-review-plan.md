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
- The snapshot sees only intra-repo Python imports of the six scan roots —
  entry points invoked by packaging (CLI scripts, API apps) can look like
  orphans. Orphan queries produce CANDIDATES for a human read, never verdicts.
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

Seed queries (all probed live 2026-07-27; baseline answers recorded so drift
is visible next run):

| # | Question | Query sketch | Baseline |
|---|---|---|---|
| A1 | Layering: does `drydocs_core` import any app layer? | `MATCH (m:CodeModule {project:'drydocs_core'})-[:IMPORTS]->(t) WHERE t.project IN ['drydocs','drydocs_deepdoc','drydocs_remediation','drydocs_lineage'] RETURN m,t` | **0 — clean** |
| A2 | Circular imports | `MATCH (m:CodeModule {circular:true}) RETURN m` + cross-check with a live cycle query (`(m)-[:IMPORTS*2..6]->(m)`) — a disagreement between scanner verdict and graph is itself a finding (§C3) | scanner says 0 |
| A3 | Fan-in hotspots (change-risk ranking) | `MATCH (m)<-[:IMPORTS]-(x) RETURN m.file_id, count(x) ORDER BY count(x) DESC` | `loaders/base.py` = 18 — read ITS diff history first in any review |
| A4 | Orphan candidates | no in- or out-IMPORTS, project <> 'tests', name <> '__init__.py' | **24 candidates** — human-read each: entry point, dead code, or scanner blind spot? |
| A5 | Test coverage shape | which non-test modules have NO tests-project importer — `MATCH (m) WHERE m.project<>'tests' AND NOT EXISTS {MATCH (t {project:'tests'})-[:IMPORTS]->(m)} RETURN m` | unprobed |
| A6 | Cross-root coupling map | `MATCH (a)-[:IMPORTS]->(b) WHERE a.project<>b.project RETURN a.project,b.project,count(*)` — compare against MODULE_MAP's declared component boundaries | unprobed |

Deliverable: findings ranked by the tech-debt skill's (Impact+Risk)×(6−Effort)
score, each with the query that found it and the file(s) read to confirm.

## Phase 2 — Project manager (skills: `groom-backlog`, `analyze`)

**Mandate.** Is `backlog.yaml` telling the truth about what is done and what
is left — audited against the code that actually exists?

Units:
1. **Done-claims spot check.** For every item closed in the last ~30 days
   whose close_note names modules/files, confirm each named `file_id` exists
   in the graph (`MATCH (m:CodeModule {file_id:$f})`). A done item naming a
   file the tree no longer has = drift finding (rename or sweep).
2. **Module-registry census.** backlog `modules:` registry vs the graph's six
   `project` values + top-level `file_id` prefixes: every graph region should
   be claimable by some module; every module should still have files. (The
   D7 sweep makes deletions visible: `removed_from_source_at IS NOT NULL`.)
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
