# wf-module-subpage-01 — shared module subpage template (rung 2, text wireframe)

> Spec source: `site-plan.md` §3 (one template × 9 modules) · backlog **O9** (template +
> Explorer instance), **O10** (Lineage instance), **O11** (export action) · visual base:
> `Gemini-generated-subpage.png` / `-2.png`. Zones per `layout-anatomy-checklist.md`.
> Explorer is the first instantiation; every other module reuses this file as its spec.

```
+---------------------------------------------------------------------------------+
| [logo]                  [ search.... ]        [Prod|UAT|Dev] [theme] [bell] [@] |  HEADER (global, unchanged)
+--------+------------------------------------------------------------------------+
| ASIDE  | TOOLBAR (page-owned):                                                  |
| (nav,  |  Home > Explorer > <selection>          [layout] [fit] [refresh]       |
| active |                                          [ v Export ]  (1)             |
| module |------------------------------------------------------------------------+
| hi-    |                                                          | RIGHT       |
| lit)   |   GRAPH PANE  (React Flow)                 ~55% height   | SIDEBAR (2) |
|        |                                                          | (inspector) |
|        |     [node]----[node]----[node]                           |             |
|        |        \         |                                       | metadata    |
|        |         \     [node]                                     | rows for    |
|        |          \       |                                       | selected    |
|        |           [node·selected (3)]                            | node:       |
|        |                                                          |  id         |
|        |  (empty state: "no selection — pick a <entity>") (4)     |  type       |
|        |                                                          |  props...   |
|        |========== resizable divider (5) =========================|  [open in   |
|        |                                                          |   module]   |
|        |   DATA FRAMES                              ~45% height   |             |
|        |   [ Tab A ]  [ Tab B ]  [ Tab C ]                        |             |
|        |   +--------------------------------------------------+  |             |
|        |   | filter row (ReUI Filters)                        |  |             |
|        |   | col | col | col | col | col          (ReUI Grid) |  |             |
|        |   | row·highlighted-by-graph-selection (3)           |  |             |
|        |   | row                                              |  |             |
|        |   +--------------------------------------------------+  |             |
+--------+----------------------------------------------------------+------------+
```

## Annotation key

1. **[Export] is a toolbar action AND repeated in each grid header** (O11): menu =
   `CSV (view)` · `JSON (view)` · `CSV (full, server)` · `JSONL (full, server)` ·
   `Copy as Cypher`. Server items disabled until the frame's QuerySpec is registered.
   Internal-classified specs render the classification chip NEXT TO the export button
   — the user sees what they're about to export before they export it.
2. Right sidebar = node inspector, content variant keyed by node type
   (job | folder | app | data-asset | team | document). Closed by default; opens on
   node click; `[open in module]` deep-links to the entity's home module. Reserve the
   grid column even when closed (layout-anatomy: aside ≠ sidebar).
3. **One selection store, two views**: graph node click → grid rows filter/highlight;
   grid row select → node highlights + centers. Selection also lands in the URL
   (`?sel=<elementId|business-key>`) so deep links restore it.
4. Every pane has explicit empty/loading/error states (slow Cypher = loading spinner
   in-pane, never a blank).
5. Divider: ReUI Resizable, persisted per-module in localStorage. Graph pane may
   collapse to 0 (table-only mode) — some modules (Gates, Loads) are table-first.
6. Breadcrumb trail is route-derived: `Home > <Module> > <selection label>`.
7. Per-module instantiation = { route, QuerySpecs per tab, graph query, node-type
   set for the inspector, toolbar extras }. NOTHING else may vary — template drift
   is a review flag.

## Per-module tab plan (from site-plan §3 table)

| Module | Tabs (data frames) |
|---|---|
| Explorer | Applications · Jobs · Conditions · Servers |
| Lineage | Hops · Data assets · Schema definition |
| Ownership | Teams · Memberships · Escalation routing |
| Runbooks | Series · Generated runbooks · Metadata completeness |
| Remediation | Findings · Fix batches · Jira handoffs |
| Docs | Documents · Chunks · Trust/provenance audit |
| Gates | Open gates · Signed off · Gate log |
| Loads | Runs · Rejects · Drift/coverage |

## Open items

- [ ] Inspector variant field lists per node type (draft from the mock's
      "Application Metadata" panel; confirm against live schema at build).
- [ ] Whether Gates module gets write actions (sign-off from the UI) — currently NO:
      site-plan keeps the UI read-only; gate actions stay in the existing gate flow.
