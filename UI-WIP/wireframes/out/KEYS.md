# Wireframe keys — DryDocs console wireframes — SME review set

Spec v2 · 2026-08-13 · branch `main (O35-O41 shipped; landing/loads/underhood = as-built, dataflow = PROPOSED)`.
Convention: WF-<VIEW>-<NN>; SME feedback cites the key; keys map to label/data/react/graph in KEYS.md and re-attach through the L5/L6 loop

## Feedback addressed

- **FB-2026-08-13-01** — "Show a data flow as swimlanes: Control-M | Data Layer | File Server / Database (SME chat 2026-08-13, testing the feedback loop; the idea traces to the original Full Circle Docs document-portal concept, section 7 Business Flow Diagrams)" → new dataflow view added (WF-DFL-01..17) as PROPOSED — renderer gained lane + arrow primitives; React build not started (inboxed as Idea-116)
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

## Data Flow — swimlanes (PROPOSED, FB-2026-08-13-01; a lineage-module layout) (`/lineage · layout: swimlane (proposed)`)

| Key | Label / element | Data source | React component | Graph / Cypher |
|---|---|---|---|---|
| `WF-DFL-01` | Module toolbar: breadcrumb Home / Lineage · data-series picker · Layout: DAG \| Swimlane · Fit · Export | modules/registry.ts | `layout/ModuleToolbar.tsx (+ proposed layout toggle)` | `n/a` |
| `WF-DFL-02` | Control-M — scheduler lane (folders, jobs, conditions) | controlm inventory extract (jobs, conditions) | `lineage/SwimlaneView.tsx (proposed)` | `(:Job)-[:IN_FOLDER]->(:Folder); condition semantics per BMC baseline` |
| `WF-DFL-03` | Data Layer — pipeline lane (ETLProcess) | pipeline token from launcher CMDLINE (G15 contract) | `lineage/SwimlaneView.tsx (proposed)` | `:ETLProcess keyed by pipeline token` |
| `WF-DFL-04` | File Server / Database — asset lane (files, datasets) | registry v2 datasets + file assets from job command parse | `lineage/SwimlaneView.tsx (proposed)` | `:DataAsset / :Dataset (registry URN grammar origin@db.schema.table)` |
| `WF-DFL-05` | FileWatcher job — detects file arrival, posts the trigger condition | controlm inventory (FW role per C30 discriminators) | `SwimlaneNode (proposed)` | `:Job (FW role)` |
| `WF-DFL-06` | ETL launcher job — CMDLINE carries the pipeline token | launcher-registry classification + G15 arg contract | `SwimlaneNode (proposed)` | `:Job → :ETLProcess (token join)` |
| `WF-DFL-07` | Downstream load job — waits on the pipeline-complete condition | controlm inventory (in-conditions) | `SwimlaneNode (proposed)` | `:Job (condition wait, BMC baseline semantics)` |
| `WF-DFL-08` | ETLProcess (pipeline) — zone hops RAW → TRUSTED → REFINED | MAC set via dpl_mac.py seam (G17, ASSUMED contract) | `SwimlaneNode (proposed)` | `:ETLProcess {kind}` |
| `WF-DFL-09` | Source file on the file server (.dat + control token) | command parse + %%var resolution (G46/G92 feed) | `SwimlaneNode (proposed)` | `:DataAsset (file)` |
| `WF-DFL-10` | Target dataset — registry URN (origin@db.schema.table) | config source registry (N9 shape) | `SwimlaneNode + IdChip (proposed)` | `:Dataset (registry URN)` |
| `WF-DFL-11` | detected by | FW job watch target vs asset path | `SwimlaneEdge (proposed)` | `join, not an edge type` |
| `WF-DFL-12` | condition | controlm inventory out/in conditions | `SwimlaneEdge (proposed)` | `job→condition→job (BMC baseline)` |
| `WF-DFL-13` | launches | G15 launcher arg contract | `SwimlaneEdge (proposed)` | `token join Job→ETLProcess` |
| `WF-DFL-14` | READS (planned) | dataset_flow enrichment feed (DPL trace) | `SwimlaneEdge (proposed)` | `m3_reads_from — status: planned, gate pending` |
| `WF-DFL-15` | WRITES (planned) | dataset_flow enrichment feed (DPL trace) | `SwimlaneEdge (proposed)` | `m3_writes_to — status: planned, gate pending` |
| `WF-DFL-16` | pipeline-complete condition | controlm inventory out/in conditions | `SwimlaneEdge (proposed)` | `job→condition→job (BMC baseline)` |
| `WF-DFL-17` | Mode tag + provenance footer: EXAMPLE DATA · ILLUSTRATIVE until the lineage QuerySpec lands; READS/WRITES render dashed while status=planned | QuerySpec reachability + relationship-vocabulary status | `ModuleTemplate fallback banner idiom` | `n/a (transport + vocabulary state)` |

## Under the Hood — retrieval benchmark (as built) (`/under-the-hood`)

| Key | Label / element | Data source | React component | Graph / Cypher |
|---|---|---|---|---|
| `WF-UTH-01` | StatTiles headline row: 12/12 recall · 27.4× token efficiency · ~4.1k vs ~112.4k · 75ms · 374/26 · 3 strategies (tabular-nums, DL-1) | underhood/benchmarkData.ts (P0 fixture; regenerated by O31) | `components/StatTiles.tsx` | `docmeta P0 corpus (Document/Chunk graph) — fixture of committed verdict` |
| `WF-UTH-02` | Three strategy cards: Manifest-routed · Full-text (Lucene top-3) · Graph traversal — recall/tokens/latency + failure modes | underhood/benchmarkData.ts | `underhood/StrategyCards.tsx` | `traversal = Document→Chunk Cypher; fulltext = Neo4j Lucene index` |
| `WF-UTH-03` | Pass chips: 11 Traversal · 6 Full-text · 9 Manifest / 12 (DL-3) | QUESTIONS[].{traversal,fulltext,manifest}.kind | `components/ui/StatusChip.tsx in underhood/Scoreboard.tsx` | `n/a (fixture aggregate)` |
| `WF-UTH-04` | Scoreboard: 12 fixed support questions × 3 strategies; ResultChip pass/fail/partial/abstain/hallucination (fail = --status-fail-soft, DL-2) | underhood/benchmarkData.ts | `underhood/Scoreboard.tsx + underhood/ResultChip.tsx` | `per-question executed Cypher recorded in fixture` |
| `WF-UTH-05` | Question detail: per-strategy chars/ms + verdict prose for the selected row | underhood/benchmarkData.ts | `underhood/QuestionDetail.tsx` | `as above` |
