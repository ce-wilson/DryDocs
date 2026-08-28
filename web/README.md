# DryDocs Console (web/)

## Site shell (O8) — zone layout, theming, 9 module routes

Post-sign-in, the app is a real `react-router` tree (deep-linkable, back-button
safe), not the old `#/...` hash router. `src/layout/Shell.tsx` renders the zone
shell — aside / header / page-owned toolbar (each route's own `ModuleToolbar`)
/ content / right-sidebar slot — driven by one typed config,
`src/layout/shellConfig.ts`. `src/modules/registry.ts` is the single array of
the 9 site-plan §3 modules that drives both the aside nav and the Overview
radial hub (`src/routes/OverviewRoute.tsx`); every module route renders the
shared skeleton in `src/routes/ModuleTemplate.tsx` (graph pane + resizable
divider + data-frame tabs — populated per module by the O10–O19 builds:
lineage DAG, mappings stewardship, ownership rollup, loads timeline,
runbooks/remediation, docs corpus map, gates record, admin config lens, all
driven by server-side QuerySpecs with two-path export + provenance manifests,
O11). Explorer is the exception: its graph
pane hosts the O2 tower-demo cards, and the O6 live dependency view + tower
drill-downs stay reachable at `/explorer/live` and `/explorer/tower/:key`.
Theming is a dark (canonical) + light (derived) token pair in
`src/styles/tokens.css`, toggled via a `dark` class stamped by an inline
pre-paint boot script in `index.html` (System/Dark/Light — see
`src/lib/theme.ts` and `src/components/ThemeToggle.tsx`); IBM Plex is
self-hosted via `@fontsource` (no Google Fonts CDN).

## Mock persona sign-in (SYNTHESIZED)

The console is gated by a **mock** persona sign-in — a client-side picker with a
localStorage session (`drydocs.mock-session.v1`) and **zero real security**: anyone
can pick any persona; nothing is verified anywhere. It exists so role-gated views
can be built and demoed now. **This is not an architecture decision** — the real
access path is decided (**ADR 0005**: thin API; see "Graph access" below), but
real authn/authz still replaces `src/lib/auth.ts` company-side (enterprise OIDC
per the ADR's Evidence). `?as=<persona>` gives a headless sign-in for demos.

Three synthetic personas (never real SIDs — publish boundary):

| Persona | Role | Sees |
|---|---|---|
| `mouse` (J. Doe) | user | all 9 modules; Ownership is their own My Apps rollup (read-only, ServiceNow-derived, synthesized) |
| `morpheus` (A. Smith) | admin | everything above, plus Console (dev) — the bolt/ADK sandbox — and the cosmetic Prod\|UAT\|Dev env toggle |
| `trinity` (K. Chen) | steward | mapping stewardship (`/mappings`, O13): manual-tier grids, changeset drafts, override-list drafting (O24) — zero graph writes |

All 9 site-plan modules are open to every signed-in persona (post-O8); only
`/console` is role-gated (admin, checked in `src/App.tsx`) and the tower demo
deep links (`/explorer/tower/:key`) keep the old per-persona rule
(`canDrill` in `src/lib/views.ts`). The ADK agent flow uses the signed-in
persona id as its `userId`.

Run it: `cp .env.example .env.local` (point `VITE_NEO4J_URI` at your local Neo4j —
canonical container/ports live in `config/dev-environment.yaml`; bolt is
`bolt://localhost:7687` on the `neo4jtest` EE container), then
`npm install && npm run dev`.

## Graph access (ADR 0005) — the GraphAccess seam

Console code reads the graph ONLY through the `GraphAccess` interface
(`src/lib/graph.ts`); view components never import `neo4j-driver`. Two adapters:

- **`api`** (`src/lib/graphApi.ts`) — the deployment path (the `drydocs-api`
  thin API): exchanges the signed-in persona id for a server session token,
  then runs **named view queries** (`runNamed`) whose Cypher lives server-side
  in `drydocs_api/queries.py` — payload shaping is never duplicated in the
  browser. Fails loud when the API is down; never silently falls back to bolt.
- **`bolt`** (`src/lib/neo4j.ts`) — a **dev-mode tool only**: reachable only in
  dev builds (`import.meta.env.DEV`) AND for the admin role (`boltAllowed()`);
  production bundles have the path compiled out. It has no named-query
  registry (`runNamed` throws) — it is the raw-Cypher bench, nothing more.

## Graph view (live, backlog O6)

**`/explorer/live`** renders real `WAS_INFORMED_BY` dependency edges from the
knowledge graph through the api adapter (both roles; read-only). Rendering is
d3-force layout (deterministic) + the in-repo SVG idiom — the NVL decision is
recorded on backlog item O6. The synthesized tower drill-downs
(`/explorer/tower/:key`) stay as the no-backend demo. To run the full live path:

```powershell
docker start neo4jtest                        # Neo4j EE (bolt on :7687 — config/dev-environment.yaml)
poetry install --with api                     # once
poetry run uvicorn drydocs_api.app:create_app --factory --port 8001
npm run dev                                   # in web/
```

The full stack walkthrough is the governed runbook
`docs/design/drydocs-web-console-runbook.md`.

The graph must be loaded first (repo README "Quick start"). Point
`VITE_API_URL` at the API if it is not on `http://localhost:8001`.

**Dev-mode credential rule:** the Neo4j password is form-entered at runtime,
localhost targets only. Never define `VITE_NEO4J_PASSWORD` in any env file or
CI — Vite inlines `VITE_*` values into the built bundle, so a committed or
injected password becomes a secret inside a publishable artifact.

---

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
