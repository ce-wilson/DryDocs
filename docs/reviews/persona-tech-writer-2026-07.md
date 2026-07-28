# Persona review — Technical writer (code-graph Phase 3, U3)

> **Run: 2026-07-28.** Precondition executed and shown: `drydocs
> load-doc-traceability` against `drydocs` — pass 1 `doc_sections.v1`
> loaded 148 sections, pass 2 `doc_traceability.v1` loaded 51 matrix rows
> (the subgraph was EMPTY at plan time, as predicted). Pass 3
> `doc_feedback.v1` **refused, exit 2** — the L17 guard fired live: the
> feedback yamls carry authors and this database has no `:Employee`
> registry, so every attribution would have silently dropped. That refusal
> is the honest producer state (employees load from company-side seal
> contacts), and it is the first field confirmation the guard works.
> Code graph: snapshot `drydocs-20260728-0754.json`, commit `36866f9`.

## Doc-status board (every docs/design/*.md)

`Project.git_commit` = `36866f9`; repo total 302 commits since the
2026-07-20 history squash. "Behind" = `git rev-list --count <cite>..HEAD`;
**a value of 302 (= the whole post-squash history) means the cited hash is
PRE-SQUASH and unreachable from main** — on a fresh clone those citations
dangle (locally they resolve only via the `archive/old-history-2026-07-20`
tag).

| Doc | Rev | Cited commit | Behind | Cited components alive? | Verdict |
|---|---|---|---|---|---|
| controlm-ingestion-tdd | 5 | c1c3a0a | 106 | yes (all 9 rows verified) | **fresh** |
| drydocs-lineage-mac-runbook | 3 | 41c4879 | 101 | yes | **fresh** |
| drydocs-mapping-store-tdd | 1 | 22d1a39 | 147 | yes | fresh-ish |
| drydocs-mapping-store-runbook | 1 | 22d1a39 | 147 | yes | fresh-ish |
| drydocs-mapping-demo-runbook | 2 | **none** | — | yes | **no commit citation at all** — the only design doc without one |
| drydocs-startup-refresh-runbook | 3 | a135a6d | 275 | yes | **stale CITE, fresh content**: the file was edited TODAY (9a85fb9, the L16 container/port refresh) but still cites the 07-20 squash-day commit — the front-matter commit was not refreshed with the Rev bump |
| drydocs-web-console-runbook | 1 | 6766b4c | 230 | yes | stale-leaning |
| drydocs-web-console-tdd | 1 | 807e050 | **pre-squash** | yes | citation dangles off main |
| drydocs-project-tdd | 2 | ac2ea2e | **pre-squash** | yes | citation dangles |
| drydocs-project-review | 1 | 97ee81c | **pre-squash** | yes | citation dangles |
| drydocs-remediation-tdd | 1 | 24d6a4b | **pre-squash** | yes | citation dangles |
| graph-retrieval-benchmark-explainer | 2 | 0e036ff | **pre-squash** | yes | citation dangles |

Re-verify queue (staleness × traffic in the code they describe):
1. **drydocs-web-console-tdd** — pre-squash cite AND the web-console epic
   is the most active; 11 requirements ride on it.
2. **drydocs-project-tdd** — the umbrella doc, pre-squash cite.
3. **drydocs-remediation-tdd** — pre-squash cite, PRESCRIPTIVE status (the
   only prescriptive doc citing a dangling commit).
4. startup-refresh-runbook — content fresh; just re-cite.

## Component.ref ↔ CodeModule.file_id — both directions

**Direction 1 (refs → code): every path-like ref is alive.** All verified
on disk/graph: `drydocs_remediation/{detect,equivalence,jira,transform}.py`,
`drydocs_api/mappings.py`, `drydocs_core/adapters/oracle_adapter.py`,
`folder_name.py`, `controlm_{folders,jobs}.cypher`,
`controlm_dependencies_derived.cypher`, `controlm_dependencies_recursive.sql`,
`constraints.cypher`, `config/*` refs, `MODULE_MAP.md`,
`PORT-MANIFEST.yaml`. **Zero dead citations.** (Note: `drydocs_api/*` refs
verify on DISK only — that package is not a scan root; see the U2 census
finding.)

**Direction 2 (heavy code → docs): the two hottest modules are cited by
no Component.** `drydocs/loaders/base.py` (fan-in 19 — the loader
lifecycle every loader inherits) and `drydocs_lineage/model.py` (fan-in 9
— the lineage identity contract) appear in zero traceability-matrix
component cells. The matrix rows cite the loaders' *cypher* files but not
the base class that owns the JobRun envelope / D7 sweep / preflight
semantics they all share. → IDEAS line (doc tag).

**Data-quality finding on the join itself:** 8 of 56 `Component.ref`
values are damaged by the comma-split cell convention — refs holding
commas or semicolons inside parentheticals shear, e.g.
`K2 loader (`seal_attribution.cypher` (truncated mid-parenthetical) and
`DefinitionFormat` (transcript impl live; XML impl schema-blocked)` (a
prose fragment stored as a ref). The section-anchor cells already solve
this (`_PAREN_QUALIFIER_RE` strips trailing qualifiers); the component
cells don't. Either extend `_split_cell` for components the same way, or
tighten the authoring convention. → IDEAS line (bug tag; it corrupts
`(origin, ref)` node identity for those rows).

## Coverage gaps by subsystem

Modules per root (graph) vs dedicated design docs:

| Root | Modules | Dedicated doc(s) | Thinness |
|---|---|---|---|
| drydocs (loaders/CLI) | 43 | controlm-ingestion-tdd + runbooks | ok |
| drydocs_core | 36 | mapping-store-tdd (mapping_store only) — the controlm/ parser family (13 modules incl. commands.py, the G15/G16 contract) has NO doc of record beyond gate-log entries | **thinnest per-module** |
| drydocs_lineage | 13 | lineage-mac-runbook | ok |
| drydocs_remediation | 7 | remediation-tdd | ok |
| drydocs_deepdoc | 3 | none | thin, but 3 modules — accept |
| drydocs_api | ~10 (unscanned) | web-console-tdd (partial) | measured blind — fix the scan root first |

## §DEP regeneration check (sdlc-*.md)

Both SDLC docs' §DEP tables were written 2026-06 (pre-G2 core extraction,
pre-squash) and now contradict the tree in three places:

| Doc claim (§DEP) | Reality | Verdict |
|---|---|---|
| `neo4j_client.py` at `drydocs/neo4j_client.py` | `drydocs_core/neo4j_client.py` (G2 core extraction) | **stale path** |
| `relationship_vocabulary.yaml` in `drydocs/ontology/` | `drydocs_core/ontology/relationship_vocabulary.yaml` (G2 Phase B) | **stale path** |
| APOC availability "unconfirmed (OQ-NS-3)" | APOC is load-bearing: `run_script` uses `apoc.cypher.runMany`, the J9 e2e container installs it | **resolved OQ still listed open** |
| `drydocs/loaders/sql/` + `test_schema.py` + BaseLoader claims | all still true | ok |

→ IDEAS line (doc tag): refresh the two §DEP tables from the tree (and
note the docs live under `docs/reviews/`, outside the design-doc render
pipeline, so no outline sweep catches them drifting).

## IDEAS lines filed

- `[doc]` five design docs cite pre-squash commits that dangle off main;
  startup-refresh runbook edited today still cites 07-20; mapping-demo
  runbook has no commit citation — one re-cite sweep fixes all seven.
- `[bug]` component-cell comma-split shears 8 of 56 Component refs.
- `[doc]` base.py + lineage/model.py (the two fan-in hotspots) cited by no
  traceability component.
- `[doc]` sdlc-*.md §DEP tables contradict the post-G2 tree (3 rows).
