# Wireframe keys — DryDocs console wireframes — SME review set

Spec v1 · 2026-07-29 · branch `main (O35-O41 shipped; wireframes = as-built state)`.
Convention: WF-<VIEW>-<NN>; SME feedback cites the key; keys map to label/data/react/graph in KEYS.md and re-attach through the L5/L6 loop

## Feedback addressed

- **FB-2026-07-28-01** — "Landing hub image has too many items in it" → hub art demoted to a small decorative mark; navigation moves to explicit category pick-lists (WF-LND-05/06) — IMPLEMENTED (O35, 2026-07-29)
- **FB-2026-07-28-02** — "Display name is cluttered, not readable" → product name appears ONCE (nav wordmark); hero h1 becomes the value proposition (design-review rec #2) — IMPLEMENTED (O35, 2026-07-29)

## Landing / Overview — category-first (AS BUILT, O35) (`/`)

| Key | Label / element | Data source | React component | Graph / Cypher |
|---|---|---|---|---|
| `WF-LND-01` | Header: wordmark (only place the product name renders) · search · env pills · theme toggle · persona | lib/auth.ts PERSONAS (mock) | `layout/Header.tsx + components/BrandMark.tsx` | `n/a (auth pending O1 ADR)` |
| `WF-LND-02` | H1 (value prop, NOT the product name): 'A Don’t-Repeat-Yourself Knowledge Graph' | static | `routes/OverviewRoute.tsx hero copy` | `n/a` |
| `WF-LND-03` | Subline: 'Pick an area below to start — every view is backed by the graph.' | static | `routes/OverviewRoute.tsx` | `n/a` |
| `WF-LND-04` | Kept Orbit mark — small, decorative only (BrandMark size=120; hub art demoted per FB-01) | static SVG | `components/BrandMark.tsx (HeroArt demoted, no longer on landing)` | `n/a` |
| `WF-LND-05` | PICK-LIST A — 'What do you want to look at?' (modules; tagline + phase badge per row) | modules/registry.ts (static registry) | `routes/OverviewRoute.tsx → new CategoryList; rows link MODULES[].path` | `per-module backsOnto: drydocs / seal-attribution / docmeta / … (registry backsOnto field)` |
| `WF-LND-06` | PICK-LIST B — 'Business area / tower' (SME picks a target; scopes Explorer + Lineage) | data/towers.ts (SYNTHESIZED fixture); live target = LOB→Product→Team taxonomy | `components/TowerDrill.tsx entry cards` | `MATCH (t:Tower {name: $title}) — fixture cypherHtml; live: org taxonomy rollup` |
| `WF-LND-07` | Getting-started checklist (existing 0/5 list, unchanged) | static | `routes/OverviewRoute.tsx` | `n/a` |
| `WF-LND-09` | Benefit strip (kept from the previous landing): Automated Discovery · Impact Analysis · Governance & Posture · Change Management | static | `routes/OverviewRoute.tsx BenefitCard` | `n/a` |
| `WF-LND-08` | Provenance footer: 'Signed in as … · demo/synthetic content tagged EXAMPLE DATA · ILLUSTRATIVE' | lib/auth.ts session | `routes/OverviewRoute.tsx footer` | `n/a` |

## Loads — run timeline (AS BUILT: O36/O38/O40/O41 on top of the DL quick wins) (`/loads`)

| Key | Label / element | Data source | React component | Graph / Cypher |
|---|---|---|---|---|
| `WF-LDS-01` | Module toolbar: breadcrumb Home / Loads · Layout · Fit · Refresh · Export | modules/registry.ts | `layout/ModuleToolbar.tsx` | `n/a` |
| `WF-LDS-08` | Filter tiles (O40, DSI idiom): All runs · Completed · Failed · Running — click scopes the timeline below (aria-pressed) | demoLoads fixture → loads.runs.v1 | `components/StatTiles.tsx (interactive mode) in routes/LoadsRoute.tsx` | `count(:JobRun) by status` |
| `WF-LDS-02` | StatusChips: ✔ 3 completed · ✗ 1 failed · ~ running (DL-3) | loads/demoLoads.ts fixture → live QuerySpec loads.runs.v1 | `components/ui/StatusChip.tsx in loads/LoadsTimeline.tsx` | `:JobRun.status ∈ {COMPLETED, FAILED, …}` |
| `WF-LDS-03` | Completion meter 75% — green only at threshold (DL-4) | derived from runs[] | `components/ui/Meter.tsx` | `count(:JobRun {status:'COMPLETED'}) / count(:JobRun)` |
| `WF-LDS-04` | Mode tag: 'LIVE — :JobRun envelope' vs 'EXAMPLE DATA · ILLUSTRATIVE' | QuerySpec reachability | `loads/LoadsTimeline.tsx header tag` | `n/a (transport state)` |
| `WF-LDS-05` | Run timeline (dot-and-rail; O36 spacing fixed) — row anatomy: loader · source IdChip · status chip (O41 map: COMPLETED green / FAILED fail-rose / STARTED teal) · start→end · row counts · run_id IdChip (O39 runtime-view link slot) | loads/demoLoads.ts → live loads.runs.v1 | `loads/LoadsTimeline.tsx + components/ui/IdChip.tsx (statusToken per ui-conventions.md §1)` | `:JobRun {run_id, loader, source, status, started_at, completed_at, rows_processed, rows_changed, rows_rejected, nodes_marked_removed, nodes_reactivated}` |
| `WF-LDS-06` | Data-frame tabs: Runs · Rejects · Drift/coverage | modules/registry.ts | `explorer/DataFrame.tsx via ModuleTemplate` | `per-tab QuerySpecs` |
| `WF-LDS-07` | Fallback banner: 'Live QuerySpec loads.runs.v1 unavailable … showing the SYNTHESIZED demo frame instead.' | QuerySpec error state | `ModuleTemplate fallback banner` | `n/a` |

## Under the Hood — retrieval benchmark (as built) (`/under-the-hood`)

| Key | Label / element | Data source | React component | Graph / Cypher |
|---|---|---|---|---|
| `WF-UTH-01` | StatTiles headline row: 12/12 recall · 27.4× token efficiency · ~4.1k vs ~112.4k · 75ms · 374/26 · 3 strategies (tabular-nums, DL-1) | underhood/benchmarkData.ts (P0 fixture; regenerated by O31) | `components/StatTiles.tsx` | `docmeta P0 corpus (Document/Chunk graph) — fixture of committed verdict` |
| `WF-UTH-02` | Three strategy cards: Manifest-routed · Full-text (Lucene top-3) · Graph traversal — recall/tokens/latency + failure modes | underhood/benchmarkData.ts | `underhood/StrategyCards.tsx` | `traversal = Document→Chunk Cypher; fulltext = Neo4j Lucene index` |
| `WF-UTH-03` | Pass chips: 11 Traversal · 6 Full-text · 9 Manifest / 12 (DL-3) | QUESTIONS[].{traversal,fulltext,manifest}.kind | `components/ui/StatusChip.tsx in underhood/Scoreboard.tsx` | `n/a (fixture aggregate)` |
| `WF-UTH-04` | Scoreboard: 12 fixed support questions × 3 strategies; ResultChip pass/fail/partial/abstain/hallucination (fail = --status-fail-soft, DL-2) | underhood/benchmarkData.ts | `underhood/Scoreboard.tsx + underhood/ResultChip.tsx` | `per-question executed Cypher recorded in fixture` |
| `WF-UTH-05` | Question detail: per-strategy chars/ms + verdict prose for the selected row | underhood/benchmarkData.ts | `underhood/QuestionDetail.tsx` | `as above` |
