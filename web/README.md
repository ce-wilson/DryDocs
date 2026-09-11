# DryDocs Console (web/)

## Site shell (O8) — zone layout, theming, 12 module routes

Post-sign-in, the app is a real `react-router` tree (deep-linkable, back-button
safe), not the old `#/...` hash router. `src/layout/Shell.tsx` renders the zone
shell — aside / header / page-owned toolbar (each route's own `ModuleToolbar`)
/ content / right-sidebar slot — driven by one typed config,
`src/layout/shellConfig.ts`. `src/modules/registry.ts` is the single array of
the 12 modules that drives both the aside nav and the Overview
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
could be chosen with nothing verifying it. A browser that edits its stored session
buys nothing, because the role that gates anything is re-derived from `PERSONAS`
client-side and re-resolved from the token server-side on every request
(ADR 0005 decision 3).

`?as=<persona>` STILL EXISTS, and this section used to say it did not. It is a
DEV-ONLY affordance (the headless-verification skill drives pages with it), baked
out of production bundles by the `import.meta.env.DEV` constant — the same
build-time construction that makes the bolt adapter unreachable in a production
build. It is a real sign-in, so it needs a real secret: `VITE_DEV_CONSOLE_SECRET`,
set in the dev shell beside the one `scripts/set_console_credential.py` stored.
There is no default and no fallback, because a baked-in dev password is the exact
thing a credential step exists to remove. A reader auditing authentication needs
to know it is there.

Secrets are **machine-local and absent on a fresh clone**, so every login on a new
checkout is refused until one is set — the correct default for a proof of concept,
and the reason the refusal names its bootstrap command rather than reading as a
bug. Set one with `poetry run python scripts/set_console_credential.py <persona>`
(no-echo prompt; see `drydocs_api/credentials.py` for why the hash lives outside
both git and `var/`). Real enterprise authn/authz still replaces this layer
company-side per the ADR's Evidence.

### The six synthetic personas

Never real SIDs — publish boundary. The three SID-shaped display names this table
carried until WEB15 were retired from `auth.ts` on 2026-08-28 and should not have
outlived it here.

| Persona | Role | Seat |
|---|---|---|
| `morpheus` | admin | platform admin · all towers |
| `trinity` | steward | mapping steward · manual tiers (O13) |
| `neo` | user | app-support SME · context intake — the persona `/intake` admits by ID |
| `mouse` | user | app access derived from ServiceNow |
| `tank` | user | app access derived from ServiceNow · second seat |
| `dozer` | user | app access derived from ServiceNow · third seat |

### What is gated, and where

Three tiers, one vocabulary. `canAccessModule(access, role)` in
`src/modules/registry.ts` is the ONLY check: `'all'` (the default) admits every
signed-in persona, `'sme'` admits steward and admin, `'admin'` admits admin.

**Five of the twelve modules are NOT open to a user-role persona**, which the
previous version of this section denied outright:

| Module | Path | Access |
|---|---|---|
| Remediation | `/remediation` | `sme` |
| Software | `/software` | `sme` |
| Gates | `/gates` | `sme` |
| Load map | `/load-map` | `sme` |
| Under the Hood | `/under-the-hood` | `sme` |

Four more surfaces are gated and are deliberately NOT nav modules
(`GATED_SURFACES` in the same file, same vocabulary): `/mappings` (`sme` — the
write surface), `/admin/config` (`admin`) and `/console` (`admin` — the
raw-Cypher sandbox, and steward does not get it), plus the Idea-192 research PoC
`/lab/salt-poc` (`sme`, the same access as the `/load-map` page it re-skins with Salt DS).

`/intake` is the one exception, and it is declared as one: it admits the SME
PERSONA by id as well as steward and admin, which a ROLE vocabulary cannot
express, so it keeps `canAccessIntake` in `src/lib/auth.ts` and is listed in
`PERSONA_SCOPED_PATHS`.

**All of it derives from the registry (WEB3).** One pathless `RouteAccessGate`
inside the shell asks `canAccessPath` what the current pathname requires. Before
WEB3, `App.tsx` restated `role === 'steward' || role === 'admin'` inline six
times — and that divergence had already shipped a bug: O59 set `/remediation` to
`sme`, which hid the nav entry and left the route reachable by typing the URL.
A source scan in `src/modules/routeAccess.test.ts` now fails on any new role or
persona predicate outside the registry.

The tower demo deep links (`/explorer/tower/:key`) keep their own per-persona
rule (`canDrill` in `src/lib/views.ts`) — a view filter, not a route gate. The
ADK agent flow uses the signed-in persona id as its `userId`.

Run it: `cp .env.example .env.local` (point `VITE_NEO4J_URI` at your local Neo4j —
canonical container/ports live in `config/dev-environment.yaml`; bolt is
`bolt://localhost:7687` on the `neo4jtest` EE container), then
`npm install && npm run dev`.

## The `js-cookie` override — do not remove it because it looks unnecessary

`package.json` pins `"overrides": { "js-cookie": "^3.0.8" }`. It has no direct
dependent here, so it reads as dead weight. It is not.

`@neo4j-nvl/react` -> `@neo4j-nvl/base` -> `@segment/analytics-next@1.81.1` ->
`js-cookie@3.0.1`, which is **GHSA-qjx8-664m-686j** (high; per-instance prototype
hijack in `assign()` enabling cookie-attribute injection). npm reports it five
times — once per link in the chain — but it is one defect. The override resolves
`js-cookie` to 3.0.8, which is fixed, and `npm run audit:high` (the CI gate) goes
from five high findings to zero.

Three things worth knowing before touching it:

- **`npm audit fix --force` is wrong here.** It proposes `@neo4j-nvl/base@1.0.0`,
  a DOWNGRADE from the 1.2.1 we run, and calls it a breaking change. It would cost
  the graph canvas. NVL 1.2.1 is already the latest published, and it pins Segment
  at an exact `1.81.1`, so there is no upstream release to move to instead.
- **The vulnerable code never shipped.** NVL gates Segment behind
  `init(apiKey)` and nothing here supplies a key; `AnalyticsBrowser` appears zero
  times in NVL's browser build; and a production `npm run build` contains no
  `js-cookie`, `withAttributes`, `analytics-next` or `cdn.segment` (NVL itself is
  present, so the check is not vacuous). Tree-shaking drops the chain. The override
  is hygiene and a green audit gate, not an incident fix.
- **Why the narrow pin.** `@segment/analytics-next@1.84.1` also clears the
  advisory (it covers `<=1.84.0`), but that is a three-minor jump in a package we
  never execute. Overriding the leaf is the smaller blast radius; 3.0.1 -> 3.0.8 is
  patch-level on a tiny stable API.

Retire the override when NVL ships a release that no longer depends on a
vulnerable `@segment/analytics-next` — check with
`npm view @neo4j-nvl/base@latest dependencies`.

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

**The browser never learns the API's port.** The page calls `/api/*` on its own
origin and Vite's proxy forwards it (ADR 0020), so the harness tells the Vite
PROCESS where its API is — `DRYDOCS_API_UPSTREAM=http://localhost:8011` — and
nothing on the API side names :5273. Changing either port means changing that
one variable with it. (Before WEB10 the API held a CORS allowlist the harness
had to extend with `DRYDOCS_CORS_ORIGINS`; that boundary is retired.)

The case ledger is `config/taxonomy/ui-tests.yaml`: cases carrying `automated_by`
are run by these files, and the rest are still checklists a person works through.

## Paper form (O88) — capture a route for pen-and-paper review

The console's paper form is the **executed DOM**, captured from the running console
through headless Edge and written as one self-contained `.html` per route — the L6
half of the Epic L feedback loop, for a React SPA over a live API. It is a capture,
never a re-render: a second renderer that reproduced console markup from JSON would
drift from the screen silently.

```powershell
npm run paper -- --persona mouse                                   # /gates, /software, /load-map
npm run paper -- --persona trinity --routes /gates,/remediation --verify-print
Get-Content .\secret.txt | npm run paper -- --persona mouse --secret-stdin   # non-interactive
```

- **What it needs**: the console and `drydocs-api` running (`--web`, default
  `http://localhost:5173`), a persona and its secret (prompted without echo, or
  `--secret-stdin` — never a flag, never the environment), `DRYDOCS_DATA_ROOT` set
  (captures land under `<data root>/console-captures/<utc-stamp>/`, or `--out`), and
  headless Edge (`--browser chromium` falls back to the O80 harness's build).
- **What each capture carries**: every stylesheet inlined (fonts fall back to system
  faces; `@font-face` is dropped rather than shipping font files), images and canvases
  as data URIs, no scripts, the `.dd-margin-tag` gutter tag on every heading, table and
  tab panel (`<route-slug>.<n>` in DOM order, also in `data-dd-anchor`), and a
  `.dd-print-footer` on every printed page: `route · commit (dirty?) · captured UTC ·
  api <origin the page itself read> · persona · browser`. A `capture-manifest.json`
  beside the files records the same plus each file's sha256 and whether it is
  self-contained (the script exits 1 if any capture still references an external
  resource).
- **The print sheet is `src/styles/print.css`** (imported by `index.css`, `@media
  print` only): the shell chrome goes, `main` gets the left gutter, and the
  `.dd-margin-tag` / `.dd-print-footer` rules are the design-doc renderer's, verbatim —
  `tests/unit/test_console_print_gutter.py` pins them equal. Printing a live route from
  the browser uses the same sheet, with no tags and no footer, because only the capture
  knows the commit and the moment.
- **The default set is the three SME surfaces** that render from committed generated
  artifacts (`/gates`, `/software`, `/load-map`): they need no graph, so a capture is
  reproducible anywhere, and they are exactly the pages FB-03 designates for review.
  Graph-backed routes are opt-in and only as good as the graph behind the API at that
  moment — which is what the footer is for.
- **Captures are not committed.** They can carry real graph values; they follow the
  vendor-scrape landing rule. Tracking a sanitized one is a decision with a
  classification on it, not a default.
- The transformation is pure (`src/lib/paperForm.ts`, tested under jsdom in
  `paperForm.test.ts`); `scripts/captureRoutes.mjs` is the driver around it. The `verify`
  skill's design-doc recipe (`drydocs.docgen.doc_pdf`) prints a capture to PDF unchanged.

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

The graph must be loaded first (repo README "Quick start"). The console calls
the API as `/api` on its own origin; if drydocs-api is not on `http://localhost:8001`,
set `DRYDOCS_API_UPSTREAM` in the shell that runs Vite (`DRYDOCS_AGENT_UPSTREAM`
for the ADK server behind `/agent`). Both are read by the Vite process and never
reach the bundle — `npm run dist:check` fails the build if any host:port does.

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
| `src/generated/openapi.json` | `poetry run python scripts/dump_openapi.py` (repo root; reads `create_app().openapi()`, the importable object) — **needs `DRYDOCS_DATA_ROOT` set**: `create_app()` resolves the data root at import and there is no default (G81) | `tests/unit/test_openapi_client.py`, and `scripts/dump_openapi.py --check` in the CI `web` job |
| `src/generated/api.d.ts` | `npm run api:types` (`scripts/writeApiTypes.ts` → `scripts/genApiTypes.ts`) | `src/generated/api.test.ts` regenerates in memory and compares |
| every call site | `src/lib/apiClient.ts` — `openapi-fetch` over the generated `paths` | `npm run build` (`tsc -b`), a CI step since O70 |

**After any `drydocs_api` change, regenerate in that order and commit both files**:

```sh
DRYDOCS_DATA_ROOT="$HOME/data/DryDocs" poetry run python scripts/dump_openapi.py   && (cd web && npm run api:types)
```

`DRYDOCS_DATA_ROOT` belongs to the FIRST command only — `npm run api:types` reads a
committed JSON file and needs nothing from the environment. Unset, the first command now
exits 1 naming the variable and leaves `openapi.json` untouched (API3); if you reach the
second command with a missing or empty schema anyway, it says so and points back here
rather than failing on a JSON parse error three layers from the cause (WEB16).

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
