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

## Persona sign-in (real, as of O69)

Signing in means proving a secret to `drydocs-api` and holding the opaque token it
returns (`src/lib/auth.ts`, session key `drydocs.session.v2`). The **client-side
picker this section used to describe is gone** — until 2026-08-28 any persona
could be chosen with nothing verifying it, and `?as=<persona>` gave a headless
sign-in for demos. Neither exists now: there is no `?as=`, and a browser that
edits its stored session buys nothing, because the role that gates anything is
re-derived from `PERSONAS` client-side and re-resolved from the token server-side
on every request (ADR 0005 decision 3).

Secrets are **machine-local and absent on a fresh clone**, so every login on a new
checkout is refused until one is set — the correct default for a proof of concept,
and the reason the refusal names its bootstrap command rather than reading as a
bug. Set one with `poetry run python scripts/set_console_credential.py <persona>`
(no-echo prompt; see `drydocs_api/credentials.py` for why the hash lives outside
both git and `var/`). Real enterprise authn/authz still replaces this layer
company-side per the ADR's Evidence.

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

## Tests (O80)

Two runners, both blocking in CI's `web` job the way `ruff` is in `gates`:

```powershell
npm test                 # vitest — pure modules, no browser, no servers
npm run test:watch       # the same, in watch mode
npm run test:e2e:install # once per machine: fetch the Chromium build
npm run test:e2e         # playwright — the browser path, against real servers
```

**What each is for.** `npm test` covers pure modules where a defect has already
escaped — `src/components/map/resolve.test.ts` is the seed case, because the Z5
map's synthetic cities could never resolve and no Python guard could see it, the
bug being in TypeScript. `npm run test:e2e` walks the path a person has had to
walk by hand after every auth change: sign in, reach a module through the nav,
assert a value the page rendered.

**The e2e suite starts its own servers and needs nothing running.** It boots
`drydocs-api` on **:8011** and Vite on **:5273**, mints a throwaway credential
into a temp directory, and tears it down after. It deliberately does not reuse a
server you already have: an API started against your real credential file cannot
verify its throwaway secret, which fails the run on a machine where nothing is
wrong. Your own `:8001` / `:5173` are never touched, adopted, or stopped.

**No Neo4j required.** The API's driver is created lazily and the module it
asserts against (`/gates`) renders from a committed generated artifact, so the
whole path runs with no graph — which is exactly the CI runner's condition.

**Ports are not freely chosen.** :5273 is a browser ORIGIN, and the API only
accepts origins it names; the harness passes its own via `DRYDOCS_CORS_ORIGINS`,
which *adds* to the built-in dev origins (5173, 4173) and never replaces them.
Changing the web port means changing that variable with it.

The case ledger is `config/taxonomy/ui-tests.yaml`: cases carrying `automated_by`
are run by these files, and the rest are still checklists a person works through.

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

**Which database the bolt panel talks to.** `VITE_NEO4J_DATABASE`, defaulting to
`drydocs` — the project database (`config/dev-environment.yaml` `ground_truth`,
the ADR 0002 topology), not the driver's home database. With no `.env.local` the
built-in default applies, so a fresh clone queries the right database rather than
returning zero rows from an empty one; the failure this replaced was silent,
because an empty result is not an error.

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

## Generated API client (O70)

The console's HTTP layer is generated from `drydocs-api`'s own OpenAPI schema,
not written by hand. Two committed artifacts, one chain, guarded at every link:

| Artifact | Written by | Guarded by |
|---|---|---|
| `src/generated/openapi.json` | `poetry run python scripts/dump_openapi.py` (repo root; reads `create_app().openapi()`, the importable object) | `tests/unit/test_openapi_client.py`, and `scripts/dump_openapi.py --check` in the CI `web` job |
| `src/generated/api.d.ts` | `npm run api:types` (`scripts/writeApiTypes.mjs` → `scripts/genApiTypes.ts`) | `src/generated/api.test.ts` regenerates in memory and compares |
| every call site | `src/lib/apiClient.ts` — `openapi-fetch` over the generated `paths` | `npm run build` (`tsc -b`), a CI step since O70 |

**After any `drydocs_api` change, regenerate in that order and commit both files**:

```sh
poetry run python scripts/dump_openapi.py && (cd web && npm run api:types)
```

What the generation buys: a path, path/query parameter or JSON body the schema
does not declare does not compile, and a response is typed wherever the server
declares one (`drydocs_api/schemas.py` — the routes `GraphAccess` and sign-in
read: `/login`, `/query/{id}`, `/raw-cypher`, `/specs`, `/specs/{id}/run`, and
the small ones). The `GraphAccess` seam in `src/lib/graph.ts` is unchanged —
components consume exactly what they did — and `src/lib/graphApi.ts` pins its
hand-owned result types to the generated ones at compile time.

What it does not buy yet: `/docs-verify`, `/mappings/*`, `/intake/*` and
`/specs/ephemeral` are still free objects server-side, so their wrappers go
through `unwrapAs<T>()` — a type the console CLAIMS, named as such at each call.
Declaring a model for one of them (a `drydocs_api.schemas` change plus the
regeneration above) turns that claim into a guard; the Python test lists them
so the promotion is a move between two lists, not a discovery.

`openapi-typescript` declares a `typescript@^5` peer while this package is on
TypeScript 6; the `overrides` block in `package.json` resolves the peer to the
project's own compiler rather than relaxing peer checks globally (`npm ci` honors
it). Regenerate and re-run `npm test` after bumping either.
