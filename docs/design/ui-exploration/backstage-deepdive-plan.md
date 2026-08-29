# Backstage deep-dive comparison plan

> **DESCOPED 2026-07-22:** the internal Backstage site could not be located, so WP-7 and
> the distribution question are dropped. Executed scope = catalog structure & design only
> (WP-2) — findings in `backstage-catalog-assessment.md`. The rest of this plan is parked.

> **Posture (2026-07-22):** The DryDocs UI stack is **locked** (`site-plan.md`: ReUI free +
> shadcn on Vite/React/Tailwind, React Flow, drydocs-api — decided 2026-07-17 after the
> Keenthemes "Start React Free" comparison). This deep dive does **not** reopen that
> decision. It exists because an internal React site with a live Neo4j connection was
> observed running on Backstage — which raises three distinct questions:
>
> 1. **Validate** — does the locked stack hold up against a battle-tested internal-portal
>    framework, or does Backstage solve problems site-plan.md hasn't seen yet?
> 2. **Mine** — which Backstage patterns (catalog model, plugin architecture, graph card,
>    permission framework) are worth reproducing inside the ReUI build?
> 3. **Distribute** — if the company already runs Backstage internally, is
>    **DryDocs-as-a-Backstage-plugin** a viable company-side delivery channel — a lens onto
>    drydocs-api, not a replacement for the standalone console?

---

## 0. Ground facts (established at clone, 2026-07-22)

- Clone: `C:\coding\projects\backstage` (shallow, `--depth 1`, ~301 MB). **Out-of-repo on
  purpose** — never lands inside DryDocs; cite paths from here.
- Monorepo shape: `packages/` (~80 framework packages: app shell, backend system, CLI,
  catalog model/client, core components) + `plugins/` (**159 in-core plugins**) +
  `docs/`, `beps/` (design docs), `microsite/`.
- Second repo (NOT cloned yet): `backstage/community-plugins` — 109 workspaces.
  **Neither repo contains a Neo4j plugin.** Checked 2026-07-22 via GitHub API
  (`workspaces/` listing, 0 hits for `neo4j`).
  → **The internal site's Neo4j connection is custom, in-house code** — most plausibly a
  custom backend plugin holding the Bolt driver (Backstage's standard
  backend-for-frontend shape), or a catalog→Neo4j exporter. This is the single most
  important thing to confirm from the internal side (WP-7).
- UI layer is **mid-migration**: `packages/core-components` is still **Material-UI v4**
  (legacy); `@backstage/ui` (`packages/ui`, "BUI") is the new in-house design system.
  Any "should we use their components" question is dead on arrival — their own
  component story is in flux, and it's MUI-world, not Tailwind/shadcn-world.
- Catalog kinds (`packages/catalog-model/src/kinds/`): Component, System, Domain, API,
  Resource, Group, User, Location — plus new AiResource and McpServerApi kinds.
- Graph rendering: `plugins/catalog-graph` uses the **DependencyGraph inside
  core-components** (dagre/d3 lineage), **not React Flow** — no overlap with our canvas
  choice.

## 1. Comparison frame — Backstage concern → DryDocs counterpart

| # | Backstage | DryDocs (locked stack) | Question for the dive |
|---|-----------|------------------------|-----------------------|
| A | Catalog model (Component/System/Domain/API/Resource/Group/User + relations) | Neo4j ontology: SEAL Application, PAT Product/Team, Job/Folder, DataAsset | Is their entity+relation vocabulary a crosswalk target? (Their catalog IS a small knowledge graph with a fixed ontology.) |
| B | Plugin architecture (frontend + backend plugin pairs, extension points) | Module subpage template + QuerySpec registry | Do their extension seams suggest anything for our module template? And what would a "DryDocs plugin" have to implement? |
| C | Backend system (`backend-plugin-api`, service refs, proxy) | drydocs-api + O4 GraphAccess seam | How do they gate a frontend from a database? Compare to our "UI never speaks Bolt" rule (ADR 0005) — expect convergent design. |
| D | Permission framework + identity | Persona mock (`?as=` headless sign-in), O20-gated write surfaces | What does their read/write permission model look like at maturity? Inputs for the future real-auth pass. |
| E | catalog-graph / EntityRelationsGraph card | React Flow canvases, MiniDag | Interaction patterns only (hover/filter/depth limit) — not the rendering lib. |
| F | TechDocs (docs-like-code, MkDocs) | docs/design deterministic renders + governed-surface rule | Does docs-as-code-per-entity suggest anything for runbook publishing (module 4)? |
| G | Scaffolder (software templates) | Runbook generation, Jira fix packages | Their template→action pipeline vs our generate-runbook flow — pattern mining only. |
| H | Search platform (indexers + engines) | Global header search ("Search nodes, servers, jobs") | How they index heterogeneous entities for one search box. |
| I | App shell, routing, theming | Zone shell, React Router, token-sheet theming | Sanity check only — ours is decided; note anything they solved that layout-anatomy-checklist.md missed. |

## 2. Work packages

Each WP names its target paths in the clone, its output, and a rough size. Order matters:
WP-1/WP-2 feed everything else; WP-7 is external and can run in parallel.

- **WP-1 — Architecture backbone read** (½ session). `docs/overview/architecture-overview/`,
  `docs/frontend-system/`, `docs/backend-system/`, `beps/`. Output: 1-page map of
  app-shell → plugin → backend-plugin → datastore flow, annotated with the DryDocs
  counterpart per layer (frame rows B, C, I).
- **WP-2 — Catalog model vs DryDocs ontology** (1 session, the deep one).
  `packages/catalog-model/src/kinds/*.ts` + `docs/features/software-catalog/` (esp.
  well-known relations). Output: crosswalk table entity-kind ↔ DryDocs node label,
  relation ↔ our relationship vocabulary — same shape as the orchestrator crosswalks in
  `config/`. This is also the input for the DryDocs-as-plugin question: our graph would
  surface INTO their catalog vocabulary. Flag anything that would be a new relationship
  type (→ ontology-mapper + HITL gate, per repo rules; expect `status: planned` entries,
  no graph writes from this dive).
- **WP-3 — Backend-for-frontend teardown** (½ session). `packages/backend-plugin-api`,
  `packages/backend-defaults`, one exemplar plugin's `-backend` pair, the proxy plugin.
  Output: sequence sketch of how a Backstage frontend reaches an external DB, side-by-side
  with drydocs-api/QuerySpec; verdict on whether their service-ref/DI pattern earns a
  place in drydocs-api.
- **WP-4 — catalog-graph interaction mining** (½ session). `plugins/catalog-graph/src/`.
  Output: list of interaction behaviors (depth limiting, relation filtering, click-through
  navigation) worth porting to the React Flow canvases; explicitly NOT a rendering-lib
  re-evaluation.
- **WP-5 — Permissions + identity skim** (½ session). `plugins/permission-*`,
  `docs/permissions/`. Output: notes feeding the eventual real-auth replacement for the
  `?as=` mock; no action now.
- **WP-6 — Scaffolder/TechDocs/search pattern skim** (½ session, timeboxed). Frame rows
  F, G, H. Output: at most 5 "steal this" bullets total; resist depth here.
- **WP-7 — Internal-site forensics** (external, parallel; company-side task). Identify
  the internal Backstage site's repo/owners; confirm HOW Neo4j is wired (custom backend
  plugin w/ Bolt driver? proxy to a graph API? catalog export?), which Backstage version,
  and whether the company runs a central Backstage instance accepting plugin
  contributions. **This determines whether question 3 (distribution) is real.**
  Mechanism-only notes come back to producer per the sanitization rules; real names/URLs
  stay in `internal-local/`.
- **WP-8 — Synthesis memo** (½ session). Output: `docs/design/ui-exploration/backstage-comparison.md` with
  three verdict sections matching the three questions (validate / mine / distribute), plus
  groomable backlog candidates. Distribution verdict is explicitly conditional on WP-7.

## 3. Decision outputs & kill criteria

- **Question 1 (validate):** default answer is "stack holds." Only a concrete,
  named problem Backstage solves that site-plan.md cannot absorb reopens anything — and
  that would be a new gate-worthy decision, not a quiet edit.
- **Question 2 (mine):** every mined pattern becomes an IDEAS.md inbox line or a backlog
  candidate attached to its module (Epic O), never an unplanned scope add.
- **Question 3 (distribute):** dead unless WP-7 confirms (a) a company Backstage instance
  exists, (b) it accepts internal plugin contributions, (c) a custom plugin can reach
  drydocs-api network-wise. If all three hold → propose a spike: thin Backstage frontend
  plugin rendering 1–2 QuerySpec-backed frames against drydocs-api (read-only, same
  classification banners). The standalone ReUI console remains the primary surface either
  way — the plugin would be a company-side lens, aligned with the standalone-template goal
  (one API, many skins).

## 4. Logistics

- Clone stays at `C:\coding\projects\backstage`, shallow; refresh with
  `git -C C:\coding\projects\backstage pull --depth 1` at dive start. If WP-2/WP-4 need
  it, shallow-clone `backstage/community-plugins` alongside (graphiql/graphql-voyager
  workspaces are the closest graph-adjacent prior art there).
- Dives run read-only against the clone; all outputs land in `docs/design/ui-exploration/` (this file's
  sibling notes) and IDEAS.md inbox lines — commit under the normal docs/design/ui-exploration flow (O21
  boundary check applies before any wholesale commit).
- Suggested sequencing: WP-1 → WP-2 in one sitting; kick off WP-7 the same day (it has
  external latency); WP-3–WP-6 as one follow-up session; WP-8 after WP-7 answers.
