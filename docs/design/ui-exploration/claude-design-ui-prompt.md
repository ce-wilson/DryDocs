# Claude Design UI starting prompt — RECORD of the 2026-07-21 issue

```yaml
status: DATED RECORD      # not a live prompt — do not paste as-is
captured: 2026-07-21      # authored at d9a2eac; describes the tree on that date
landed:   2026-08-12      # merged to main at 429d829, unchanged
```

> **This is a record of the prompt as issued on 2026-07-21, not current instructions.**
> It was written to be pasted into Claude Design UI against the repo root, and it is kept
> because it is the clearest single statement of the approved design direction — the Kept
> Orbit brand rules, the locked stack, the token palette, and the layout anatomy. Those
> hold. What does not automatically hold is every **path** it cites: the file was authored
> on a branch and merged three weeks later, so it describes the tree at capture date.
>
> **Reclassified 2026-08-12** (Idea-110). Reusing it means re-checking its references
> first. The known drift, recorded so the next reader does not chase it:
>
> - **`docs/design/ui-exploration/drydocs-mark.svg` and `drydocs-mark-mini.svg` no longer exist.** §2 and §6
>   list them as the "final vector marks" under *Approved / canonical*. Commit `d6022c3`
>   (2026-07-28) dropped them as rejected and nothing has replaced them, so the final mark
>   is **unsettled** — treat any mark reference below as a description of intent, not as a
>   pointer to an asset. `kept-orbit-brand-sheet.png` and `kept-orbit-philosophy.md` are
>   present and remain the brand authority.
> - Everything else it names resolved when this was checked (33 paths, 2026-08-12),
>   including the component inventory in §3, the icon registry in §4 and the connection
>   seams in §5. That check is a point-in-time result, not a guarantee.
>
> §7 ("What actually needs design work") is the part most likely to be stale — it is a
> 2026-07-21 to-do list, and some of it may since be done.

---

You are designing for **DryDocs Console** — an intranet React SPA that fronts a
production-support knowledge graph for D&A batch processing (Control-M jobs, data
lineage, ownership, runbooks). A working console already exists in `web/`; your job is
to **refine and extend the existing design system, not invent a new one**. The brand
direction, palette, typography, and layout anatomy are APPROVED and locked — work
within them.

## 1. Tech stack (locked — decision 2026-07-17, `docs/design/ui-exploration/site-plan.md` §1)

- **React 19 + TypeScript ~6 + Vite 8** (`web/package.json`), dev server :5173
- **Tailwind CSS 4** via `@tailwindcss/vite`, themed entirely through **CSS custom
  properties** in `web/src/styles/tokens.css` — tokens are the theme API
- **No component library package.** ReUI-free-tier convention: shadcn-style primitives
  copied into the repo (`web/src/components/ui/`), hand-owned
- **@xyflow/react 12 (React Flow)** for interactive graph canvases; **d3-force** for the
  deterministic live dependency layout; hand-rolled static SVG for the landing hub
- **react-router-dom 7** (real routes — the earlier hash-router is superseded)
- **IBM Plex Sans (400/500/600/700) + IBM Plex Mono (400/500/600)**, self-hosted via
  @fontsource — **no Google Fonts CDN, no external requests of any kind** (intranet target)
- Lint: oxlint. No CSS-in-JS. Salt DS was evaluated and **dropped** — single track.

## 2. Design system — current choices (APPROVED)

**Brand: "Kept Orbit"** (`docs/design/ui-exploration/kept-orbit-philosophy.md`, brand plate
`docs/design/ui-exploration/kept-orbit-brand-sheet.png`, final mark `docs/design/ui-exploration/drydocs-mark.svg` +
`drydocs-mark-mini.svg`). A small saturated **red core sphere** orbited by exact
elliptical-arc panel "staves" that never touch it. Hard rules: the core's red is used
for brand (and alert) ONLY — no decorative red anywhere else; panels are mathematical
arcs, never freehand; depth by occlusion order, no blur/shadow theatrics; must survive
flattening to flat inks; mono type "annotates, never competes."

**Palette — "a working harbor at dusk."** Dark is canonical; light is derived.
Tokens live in `web/src/styles/tokens.css` (`:root` = light, `:root.dark` = dark):

| Token | Dark | Light | Role |
|---|---|---|---|
| `--bg` / `--bg2` | `#0d1520` / `#0f1b29` | `#f4f6f9` / `#eaeef4` | canvas |
| `--panel` / `--panel2` | `#121e2e` / `#152335` | `#ffffff` / `#eef2f7` | surfaces |
| `--edge` / `--edge-soft` | `#203045` / `#1a2739` | `#d3dce6` / `#e3e9f0` | borders |
| `--text` / `--muted` / `--faint` | `#e8edf3` / `#8a97a8` / `#71809a` | `#111a26` / `#48566c` / `#64728a` | type (faint was raised for WCAG AA) |
| `--blue` / `--blue-br` | `#2e6bc4` / `#4d8be0` | `#2e6bc4` / `#1d4f93` | water blue accent |
| `--teal` / `--green` / `--yellow` | `#2ab3a6` / `#3aae6b` / `#d9b831` | `#167f73` / `#1f7a46` / `#8a6a0c` | status accents |
| `--red` | `#c8202e` both themes | | **brand core + alert only** |
| `--brand-navy` / `--brand-green` | `#1e3a5c` / `#2bb673` both themes | | Kept Orbit stave identity colors |

Graph node kinds map to tokens, never raw hex (e.g. ControlMJob `--blue-br`, Dataset
`--blue`, EtlJob `--yellow`, Warehouse `--teal`, CatalogLOB `--red`).

**Theming:** dark-first, 3-state System/Dark/Light toggle, `.dark` class on `<html>`,
pre-paint boot script in `web/index.html` (localStorage `drydocs.theme.v1`), all React
Flow chrome routed through tokens. Dark-mode-only icon glow via `.glyph-accent`
drop-shadow; light mode gets solid outlines. `prefers-reduced-motion` kills animation.

**Layout anatomy** (`docs/design/ui-exploration/layout-anatomy-checklist.md`, implemented in
`web/src/layout/Shell.tsx` + `shellConfig.ts`): banner (yellow MOCK AUTH · SYNTHESIZED
strip) → **header 64px** (logo, global search, env toggle Prod|UAT|Dev, theme toggle,
persona chip) → three columns: **aside 240px** (collapsible to 64px, module nav) ·
**main** (page-owned toolbar 56px with breadcrumbs, then content) · **right sidebar
340px** (node inspector, collapses to 0). Two load-bearing rules: *Toolbar ≠ Header*
(breadcrumbs live in the toolbar) and *Aside ≠ Sidebar* (left nav vs right inspector).
Module pages split ~55% graph pane / ~45% data-frame tabs with a resizable divider.

**Product principles the design must honor:**
- **Read-only console.** Views have zero action controls; edits travel through the repo
  + HITL gate flow. The single write-shaped surface (`/mappings`, steward role) drafts
  downloadable CSV artifacts — it never writes the graph.
- **Provenance honesty.** Every data surface is badged: monospace yellow
  `SYNTHESIZED` / `EXAMPLE DATA · ILLUSTRATIVE` chips on demo data, `LIVE` +
  `n/m · <database>` headers on real frames, classification banners on exports. Never
  present demo data as real; never a silent fallback.
- Every pane has explicit empty/loading/error states (`ui/EmptyState.tsx`) — no blanks.

## 3. React components to use (build on these, don't fork new ones)

**Primitives** (`web/src/components/ui/`): `Tabs` (ARIA tablist), `EmptyState`,
`ResizableSplit` (persisted divider %).

**Shared:** `BrandMark` (Kept Orbit glyph), `ModuleIcon` (one geometric SVG glyph per
module id, currentColor), `icons/HubGlyphs` (120×120 hub glyphs, ~2.2px stroke),
`ThemeToggle`, `MiniDag` (the shared React Flow mini-DAG pane — token-colored nodes,
flag ribbons, linked selection; used by Gates/Runbooks/Remediation/Docs),
`LinkedDemoFrame` (demo table with row↔node selection linking), `SignIn` (persona
picker), `CypherConsole` (admin dev bench).

**Layout:** `Shell`, `Header`, `Aside`, `ModuleToolbar`, `RightSidebarSlot` (+
`rightSidebarContext`), `useRouteA11y` (focus/scroll on navigation).

**The one page template:** `routes/ModuleTemplate.tsx` — toolbar → graph pane →
resizable divider → data-frame tabs → right inspector. All eight modules instantiate
it; per-module variation is limited to route, queries, node-type set, and toolbar
extras. **Template drift is a review flag.**

**Feature panes to reference:** `explorer/ExplorerGraphPane` + `DataFrame` + `SpecGrid`
(the live QuerySpec grid with export + Copy-as-Cypher) + `NodeInspector`;
`ownership/OwnershipGraphPane` + `AssetSearchPanel`; `lineage/LineageGraphPane`;
`loads/LoadsTimeline`; `routes/OverviewRoute` (the radial-hub landing).

**Module registry** (`web/src/modules/registry.ts` — drives both nav and hub spokes):
Overview `/` (hub core), Explorer `/explorer`, Lineage `/lineage`, Ownership
`/ownership`, Runbooks `/runbooks`, Remediation `/remediation`, Docs `/docs`, Gates
`/gates`, Loads `/loads`; plus non-spoke gated routes `/mappings` (steward/admin),
`/admin/config` and `/console` (admin). Personas: user < steward < admin (mock auth,
three synthesized personas).

## 4. Vendor logos & icons

`drydocs-icons/` is the internal vendor icon registry — `manifest.json` is the source
of truth, `index.html` is the rendered contact sheet.

- `drydocs-icons/vendors/packaged/` (safe, regenerable SVGs): **BMC** `#FE5000`,
  **Neo4j** `#4581C3`, GitHub, Jira/Atlassian/Confluence/Bitbucket `#0052CC`,
  AWS S3/Glue/Lambda, Snowflake `#29B5E8`, Teradata, Splunk, Red Hat.
- `drydocs-icons/vendors/external/` (self-supplied, trademark-sensitive): **Oracle**,
  Informatica, Ab Initio, Alteryx, Salesforce, SQL Server, Experian (placeholder only).
- `drydocs-icons/vendors/generic/` (Material Design Icons, neutral `#475569`): server,
  database, storage, cloud, network, warehouse + persona icons (admin/analyst/dev/…).
- `drydocs-icons/png/` — 128/256/512 raster exports.

Trademark note: the registry is **internal-only**; package licenses cover icon files,
not trademarks. Do not restyle or recolor vendor marks.

## 5. Connection points — API and Neo4j

The browser never holds credentials or composes Cypher (ADR 0005). One `GraphAccess`
seam (`web/src/lib/graph.ts`) with two adapters:

- **drydocs-api (the deployment path)** — FastAPI on **:8001**, client
  `web/src/lib/graphApi.ts`, base URL `VITE_API_URL` (default `http://localhost:8001`).
  Start: `poetry run uvicorn drydocs_api.app:create_app --factory --port 8001`.
  Endpoints the UI uses: `POST /login` (persona → bearer token), `POST /query/{queryId}`
  (named views: overview-counts, folder-census, dependency-chain, c4-graph),
  `GET /specs` + `POST /specs/{specId}/run` (QuerySpec data frames, 7 registered),
  `POST /specs/{specId}/export?format=csv|jsonl` (+ provenance manifest sidecar),
  `POST /raw-cypher` (admin only), and the `/mappings/*` steward surface (domains,
  grid, options, changeset, overrides). All Cypher passes a read-only guard;
  CORS allows :5173/:4173 only.
- **Direct Bolt (dev-admin only)** — `web/src/lib/neo4j.ts`, `neo4j-driver` 6, gated to
  dev builds + admin role, password form-entered only (never env — Vite would inline it).
- **ADK agent server** — `web/src/lib/adk.ts`, `VITE_ADK_URL` default
  `http://localhost:8000` (used only by the admin CypherConsole).

**Neo4j:** local Docker **Neo4j 5 Enterprise** (Bolt 7687 / HTTP 7474; host-remapped
to 7689/7476 on this machine — see `web/.env.example`). Server-side settings via
`NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` / `NEO4J_DATABASE` env vars. Multi-DB
topology (ADR 0002): `drydocs` (ground truth), `ddlineage` (lineage), `ddcontext`
(synthesized, watermarked), `ddall` (composite). **Which database a view reads is a
server-side routing decision — never surfaced as a client choice.** The console runs
fully without a live graph: every frame falls back to visibly-badged SYNTHESIZED demo
data (`web/src/**/demo*.ts`, `web/src/data/*`).

## 6. References & screenshots (all in `docs/design/ui-exploration/` unless noted)

**Approved / canonical:**
- `kept-orbit-brand-sheet.png` — the brand plate (mark geometry, stave table, palette)
- `drydocs-mark.svg`, `drydocs-mark-mini.svg` — final vector marks
- `Gemini_Generated_Landing-Favorite.png` — the chosen radial-hub landing geometry
  (raster concept; the build recreates it as SVG)
- `codeflow-ui-reference.png` — external anatomy reference for the shell (aside stats ·
  center graph · right inspector · view-switcher toolbar)
- `dd-verify-top.png` — screenshot of the built console as it stands
- `site-plan.md`, `layout-anatomy-checklist.md`, `wireframe-guide.md`, and the
  wireframes `wf-landing-01`, `wf-module-subpage-01`, `wf-mapping-01`,
  `wf-runbook-path-01`, `wf-admin-config-01` (.md + .html/.pdf companions)
- `docs/design/drydocs-web-console-tdd.md` + `drydocs-web-console-runbook.md` —
  descriptive record of the built console

**Exploratory / superseded (context only — do not follow):** `WEBSITE-IDEAS.MD`,
`gemini-wire-frame.md`, `DryDocs_UI_Development_Specs.md` (the old `#0f172a`
cyber-teal/neon/glassmorphism direction), Inter/Fira fonts, Salt DS two-track,
the hash-router era in the TDD. Other `Gemini_*`/`Copilot_*` PNGs are concept variants.

## 7. What actually needs design work (start here)

1. **Light-mode design pass** — the light token sheet is mechanically derived from
   dark and has never had a real pass. Dark stays canonical.
2. **Landing radial hub** — rebuild the raster concept (`Landing-Favorite`) as a
   proper responsive SVG: red core + one spoke per module, clockwise from 12 o'clock,
   card-grid fallback on mobile, static-neutral health dots (no fake green).
3. **Hardcoded-hex cleanup** — legacy surfaces (`web/src/data/towers.ts`,
   `components/GraphSvg.tsx`, `GraphExplorer.tsx`, `App.css` cypher syntax colors)
   still carry raw hex; reconcile them into the token system.
4. **Onboarding checklist content** on the landing page (currently placeholder).
5. Empty/loading/error state polish across module panes; inspector density review.

**Constraints recap:** self-contained (no CDN/external assets), both themes must pass
WCAG AA, respect reduced motion, no red outside brand/alert, no new component library,
no action controls on read-only views, provenance badges never removed, and all data
in mocks must stay synthesized — never real job names, SIDs, server names, or schemas.
