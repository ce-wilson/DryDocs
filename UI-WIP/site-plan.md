# DryDocs site plan — single-track ReUI build

> **Decision (2026-07-17, supersedes the two-track addendum in the IDEAS UI-stack entry):**
> ONE track. **ReUI free tier (reui.io) + shadcn on Vite + React + Tailwind**, React Flow
> for graph canvases, fronting an ADK 2.0 agent backend. **Salt DS is dropped** — no
> company-variant skin track. The shell stays library-agnostic per
> `layout-anatomy-checklist.md` (typed layout config, zone decomposition) as good
> architecture, not as a second-skin escape hatch.
>
> Base visuals: `Gemini_Generated_Landing-Favorite.png` (radial hub landing) +
> `Gemini-generated-subpage*.png` (module subpage pattern). Token source:
> `drydocs-landing-dark.html`. Open findings from `design-review.md` are folded in below.

---

## 1. Stack (locked)

| Layer | Choice | Notes |
|---|---|---|
| Build | Vite + React + TypeScript | |
| Styling | Tailwind + CSS custom properties | tokens are the theme API (§2) |
| Components | **ReUI free** (shadcn-style, copied into repo) | Data Grid, Filters, Tree, Timeline, Resizable, Sheet cover the shell + frames; enable ReUI MCP (`https://mcp.reui.io`) + `@reui/skills-claude` when build starts |
| Graph canvas | React Flow | lineage + explorer canvases; NVL is the fallback only if Neo4j-native rendering becomes a requirement |
| Routing | React Router (real routes, not display toggles) | fixes design-review 🔴 #1: every view deep-linkable + back-button safe |
| Backend | ADK 2.0 agent (`adk api_server`, REST/SSE; AG-UI optional later) → Neo4j MCP → graph | agent owns Cypher; UI never speaks Bolt directly |
| Fonts | IBM Plex Sans + IBM Plex Mono, **self-hosted woff2** | design-review: no Google Fonts CDN (intranet target) |

## 2. Theme system — system default, dark-first design

The user preference is dark; the *default* is the visitor's system, with a manual
three-state toggle (System / Dark / Light) in the header cluster.

- **Mechanism (shadcn convention):** `class` strategy — `dark` class on `<html>`;
  boot script reads `localStorage.theme` → falls back to `prefers-color-scheme`;
  listens to the media query while in System mode. No flash: the boot script is
  inline in `index.html` before paint.
- **Tokens:** everything routes through `:root` custom properties (already the
  discipline in `drydocs-landing-dark.html` — carry those values over as the dark set):
  - dark (canonical, designed first): bg `#0D1520`, panel `#111B29`, text `#E8EDF3`,
    muted `#8A97A8`, brand red `#D62828` (brand core ONLY), teal accent, green =
    healthy, amber = warning, red = alert. Fix carried over: `--faint` lightened to
    ≈`#71809A` (design-review WCAG fail).
  - light: derived second, same token names — schematic-on-paper look (light slate bg,
    same accent hues darkened one step for contrast). Every component consumes tokens,
    never raw hex, so light mode is a token sheet, not a redesign.
- **Graph canvases theme too:** React Flow node/edge styles read the same tokens
  (CSS vars work inside SVG); the animated "data packet" dots and neon node outlines
  get a light-mode equivalent (solid 2px outlines, no glow).
- **Brand rule (design-review):** red = brand core + alert only; document the dual role.

## 3. Information architecture — module menu + subpage landings

The landing keeps the mock's **radial hub**: red core sphere center, one spoke per
module. The left aside nav lists the same modules — spoke and nav item are the same
route. (The mock's towers — Auto / Home Lending / Cards — are NOT modules; they are
demo *content* inside Explorer, kept with their "EXAMPLE DATA · ILLUSTRATIVE" honesty
tags.)

### The module menu (aside nav, top→bottom)

| # | Module | Route | Graph pane (top) | Data frames (bottom tabs) | Backs onto | Phase |
|---|--------|-------|------------------|---------------------------|-----------|-------|
| 0 | **Overview** | `/` | radial hub (modules as spokes, health glyph per spoke) | — (benefit cards + onboarding checklist instead) | all | 1 |
| 1 | **Explorer** | `/explorer` | tower/app drill-down graph (mock subpage 1) | Applications · Jobs · Conditions · Servers | `drydocs` DB | 1 |
| 2 | **Lineage** | `/lineage` | React Flow source→target DAG (mock subpage 2) | Hops · Data assets · Schema definition · Row-level preview | `ddlineage` | 1 |
| 3 | **Ownership** | `/ownership` | SEAL→PAT→team rollup graph (My Apps SVG pattern) | Teams · Memberships · Escalation routing | seal-attribution | 2 |
| 4 | **Runbooks** | `/runbooks` | data-series provisioning chain (FileWatcher→RAW→ING→LD) | Series · Generated runbooks · Metadata completeness | runbook-automation | 2 |
| 5 | **Remediation** | `/remediation` | finding→fix-batch flow | Findings · Fix batches · Jira handoffs | drydocs_remediation | 2 |
| 6 | **Docs** | `/docs` | Document→Chunk corpus map | Documents · Chunks · Trust/provenance audit | docmeta | 3 |
| 7 | **Gates** | `/gates` | gate dependency graph | Open gates · Signed off · Gate log | HITL/review | 3 |
| 8 | **Loads** | `/loads` | loader→JobRun timeline (ReUI Timeline) | Runs · Rejects · Drift/coverage | BaseLoader `:JobRun`s | 2 |

Aside footer (pinned): Settings · Profile · Sign out. Header (64px): global search
("Search nodes, servers, jobs"), env toggle [Prod|UAT|Dev], theme toggle, avatar.

### Module subpage landing — one template, per the mocks

Every module (1–8) instantiates the SAME template (the mock subpage anatomy mapped
onto `layout-anatomy-checklist.md` zones):

```
TOOLBAR   breadcrumb (Home > <Module> > <selection>) · page actions:
          [layout picker] [zoom-to-fit] [refresh] [⬇ Export]      ← §4
CONTENT   ┌────────────────────────────────────────┬──────────────┐
          │ GRAPH PANE (React Flow)  ~55%          │ (right       │
          │  click node → inspector opens →        │  SIDEBAR:    │
          ├──── resizable divider (ReUI) ──────────┤  node        │
          │ DATA FRAMES ~45%: [Tab] [Tab] [Tab]    │  inspector,  │
          │  ReUI Data Grid + Filters              │  metadata    │
          │                                        │  panel as in │
          │                                        │  mock)       │
          └────────────────────────────────────────┴──────────────┘
```

- Graph pane and data frames are **linked selections**: click a node → its rows
  highlight/filter; select a row → node pulses. One shared selection store.
- Right sidebar = the mock's "Application Metadata" panel, content variants keyed by
  node type (job | folder | app | data-asset | team | document) — the checklist's
  aside≠sidebar rule.
- Deep links: `/explorer/tower/:key`, `/lineage/asset/:assetId`, `/gates/:gateId` — on
  route change, focus the view `h2` (design-review a11y finding).
- Landing CTA fix (design-review 🟡): "Explore the Graph" → `/explorer` generically,
  not a hard-coded tower.

## 4. The output function — Neo4j data-frame export

Every data frame on every module page is exportable, from the **[⬇ Export]** action in
the page toolbar (and per-frame in the Data Grid header). Design:

### QuerySpec registry (the contract that makes export possible)

Each data frame is declared, not ad hoc:

```ts
type QuerySpec = {
  id: string;               // "explorer.jobs.v1" — versioned like loaders
  database: "drydocs" | "ddlineage" | "ddcontext" | "ddall";
  cypher: string;           // parameterized, read-only
  params: Record<string, unknown>;
  columns: ColumnDef[];     // names, types, formatters
  classification: "external" | "internal-public" | "internal" | "internal-confidential";
};
```

The UI never invents Cypher; the frame renders whatever its QuerySpec returned via the
ADK backend. Export reuses the SAME spec — what you export is provably what you saw.

### Two export paths

1. **Client-side (view export):** current grid state — visible columns, applied
   filters/sort — to **CSV** or **JSON**, straight from the ReUI Data Grid model.
   Instant, capped at the rows already loaded (~10k guard).
2. **Server-side (full export):** POST `/export` to the ADK backend with
   `{querySpecId, params, format}`; the agent re-runs the spec's Cypher against the
   spec's database and **streams** the full result as `CSV`, `JSON Lines`, or
   `Parquet` (phase 2 format). Batched driver streaming — NOT `apoc.export.*` (which
   writes files on the DB server; wrong side of the boundary).

### The provenance envelope (every export, both paths)

Each export ships with a manifest — sidecar `.manifest.json` for CSV/JSONL, embedded
metadata for Parquet:

```json
{
  "query_spec": "explorer.jobs.v1",
  "cypher_sha256": "…",
  "params": { "tower": "…" },
  "database": "drydocs",
  "executed_at": "2026-07-17T…Z",
  "row_count": 1234,
  "classification": "internal",
  "trust_tiers_present": ["VERBATIM", "GROUNDED"],
  "exported_by": "<user>",
  "app_version": "…"
}
```

Rules wired to the repo's classification model (`PUBLISH-BOUNDARY.md`):
- Classification comes from the QuerySpec; **`internal`/`internal-confidential`
  exports get a banner row + filename prefix** (`INTERNAL__…csv`).
- Anything touching `ddcontext` (or `ddall`, which can read it) is watermarked
  `SYNTHESIZED — unverified` in the manifest AND as a grid-visible column.
- A "Copy as Cypher" action alongside export (the spec's query + params) — reproduces
  the mockups' Cypher-panel-as-documentation idea and gives SMEs the exact provenance.

### Backend note

The export endpoint is the first concrete consumer for the **drydocs-api** seam
(backlog O5, gated on ADR-0005/O3). Until that gate resolves, the ADK agent's tool
layer IS the API: `run_query_spec(spec_id, params)` + `export_query_spec(...)` as agent
tools. No new HITL gate needed for the UI itself — it is read-only against the graph;
anything write-shaped (annotations, gate actions in module 7) goes through the existing
gate flow, not the UI directly.

## 5. Phasing

- **P0 — shell + theme:** Vite scaffold, zone shell from `layout-anatomy-checklist.md`
  (aside/header/toolbar/content/right-sidebar, typed layout config), token sheets dark +
  light + system boot script, routing skeleton with all 9 routes stubbed, self-hosted
  Plex. Acceptance: theme toggle 3-state works, every route deep-links, back button safe.
- **P1 — landing + Explorer:** radial hub with live module spokes; Explorer module page
  on the shared template with demo (tower) data via QuerySpec registry + ADK stub;
  linked selection graph↔grid. Acceptance: mock parity screenshots dark AND light.
- **P2 — Lineage + export:** React Flow lineage canvas; both export paths + manifest;
  "Copy as Cypher". Acceptance: exported CSV+manifest round-trips a QuerySpec exactly;
  classification banner renders on internal specs.
- **P3 — remaining modules** in menu order (Ownership, Runbooks, Remediation, Loads,
  then Docs, Gates), each = template instantiation + its QuerySpecs.
- Wireframe workflow per `wireframe-guide.md`: rung-2 text wireframe per module page
  before build; annotated-scan loop for revisions; each accepted change → backlog item.

## 6. Follow-ups this plan creates

- [ ] Groom P0–P2 into `backlog.yaml` (new module id suggestion: `drydocs-ui`).
- [ ] LFS the 19 MB `start-react-free-reference.fig` before UI-WIP is committed wholesale.
- [ ] Retire the Salt two-track language from the IDEAS entry at next groom (decision
      note added to IDEAS now).
- [ ] Light-mode token sheet needs a design pass (dark is designed; light is derived).
- [ ] Landing radial hub needs a rung-3 wireframe (the mock is raster; rebuild as SVG).
