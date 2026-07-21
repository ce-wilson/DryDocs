# Technical Design — DryDocs web console & thin API (the built UI: drydocs-web + drydocs-api)

<!-- anchor: front-matter -->
**Status:** DESCRIPTIVE — documents the built UI as of **Rev 1, 2026-07-18**, authored at
commit `807e050` (branch `feat/mapping-store`; Epic O items O1–O7 done, plus the O13
mapping-stewardship live demo). The O8–O12 site-plan rebuild (`UI-WIP/site-plan.md`) is the
PRESCRIPTIVE successor and is **not** this document. ·
**Classification:** Internal-Public — mechanism only; every persona, tower, app, and row
shown by the console is SYNTHESIZED; real SIDs/schemas live company-side. ·
**Audience:** engineers working on `web/` (drydocs-web) or `drydocs_api/` (drydocs-api),
and the SME reviewing the console's access-path and stewardship mechanics. ·
**Companion:** `docs/decisions/0005-browser-neo4j-access-path.md` (the governing ADR);
`docs/design/drydocs-project-tdd.md` (the platform frame); `UI-WIP/site-plan.md` (the
successor design); `docs/design/drydocs-mapping-demo-runbook.md` (start the demo);
`knowledge/upgrade-plans/mapping-store-plan-2026-07-17.md` (the M0–M4 store plan).

Worked example throughout: the admin persona `asmith7734` signs in and opens the Graph
view, which renders **live** `WAS_INFORMED_BY` edges from the `drydocs` EE database (9
jobs / 8 edges at the O6 verification); the steward persona `kchen2190` opens `/demo`,
drafts one job→application entry, and downloads the resulting gate-bound changeset CSV.

> **Read-me-first.** The console is a *read surface with one write-shaped exception, and
> even that exception writes no graph*. Every path from a browser to Neo4j crosses ONE
> seam (`GraphAccess`), lands in a server that holds the only credentials, is guarded
> read-only twice, and is routed to its database fail-closed. The mapping screen's
> "submit" returns a git artifact for the HITL gate — the loader remains the only writer.

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Specify the built web UI end-to-end: the React console and its mock-persona
gating, the `GraphAccess` seam and its two adapters, the thin read API (guard, named
queries, database routing, sessions), and the O13 mapping-stewardship surface (SQLite
materialization + changeset artifacts + the `/demo` page).

**In scope.**
- `web/src/` — shell, hash routing, view registry, mock auth, synthesized pages, the
  live Graph view, the admin Cypher/ADK console.
- `drydocs_api/` — FastAPI wiring, pure handlers, session store, personas, write guard,
  named-query registry, per-view database routing, `/mappings/*`, `/demo`.
- `drydocs_core/mapping_store.py` — the derived SQLite materialization the mapping
  endpoints read.

**Out of scope** (delegated): the O8–O12 ReUI/Tailwind rebuild, QuerySpec export, and
admin-config page (PRESCRIPTIVE — `UI-WIP/site-plan.md`); the ADK agent backend's
internals; ingestion (`controlm-ingestion-tdd.md`); enterprise SSO/OIDC and real rosters
(company-side twin per ADR 0005).

<!-- anchor: context-frame -->
## Where this sits — the four-layer frame

The console is a **layer-3 consumer**: it reads the populated knowledge graph and never
writes it. The mapping-stewardship surface is **layer-2 adjacent**: assigning a job to a
BusinessApplication is a *meaning* decision, so the UI only drafts gate-bound artifacts —
the meaning is assigned at the HITL gate, applied by the loader. Layer-4 context
projections are planned to land **server-side** (per ADR 0005 the thin API is where
task-scoped shaping belongs), not in the browser.

Upstream neighbours: the Neo4j EE container (`drydocs` DB, ground truth), and the config
ledgers (`config/taxonomy-ontology-map.yaml`, `config/manual-loads/`,
`drydocs_core/ontology/relationship_vocabulary.yaml`) via the mapping-store
materialization. Downstream: support/SME users in a browser; drafted changesets travel
git → K2 gate → `manual_loads` loader.

<!-- anchor: definitions -->
## Definitions, acronyms & references

- **Persona / role** — synthetic identities with roles ordered **user < steward < admin**:
  `jdoe4821` (user), `kchen2190` (steward), `asmith7734` (admin). Client and server copies
  are drift-guarded by a test that parses the TS from Python.
- **GraphAccess seam** — the single TypeScript interface (`web/src/lib/graph.ts`) through
  which any console code reads the graph; view components never import `neo4j-driver`.
- **api / bolt adapters** — the seam's two implementations: `graphApi.ts` (HTTP to
  drydocs-api; the deployment path) and `neo4j.ts` (direct Bolt; dev-mode bench only).
- **Named query** — a server-registered, param-validated, read-only Cypher statement
  (`drydocs_api/queries.py`); the browser sends an id + params, never Cypher.
- **Mapping domain** — one stewarded mapping surface (`ontology-map`, `job-application`,
  and the not-yet-built `fid-seal`, `alias-seal`).
- **Changeset artifact** — the CSV + manifest snippet returned by
  `POST /mappings/changeset`; a *proposal* for the git/gate/loader chain, never a write.
- **MappingStore** — read-only accessor over the derived SQLite file (`var/mapping.db`),
  auto-built from committed sources; safe to delete, never committed.
- **ADK** — the agent backend (`api_server`, port 8000) reached only from the admin
  console's agent flow.
- **O1–O13** — Epic `web-console` backlog items (`docs/restructure/backlog.yaml`).
- **ADR 0005** — "Browser ↔ Neo4j access path", **ACCEPTED 2026-07-14**: thin API is the
  deployment shape; bolt-from-browser survives only as a dev-mode adapter. Builds on ADR
  0002 (database topology behind `routing.py`) and ADR 0003 (the scan-code-regions-only
  lesson reused by the write guard).

<!-- anchor: design-summary -->
## Design summary

```
 browser (React console, web/src)                  browser (mapping demo, /demo page)
   SignIn ── mock session (localStorage)              persona login → bearer token
   Shell/views.ts ── role-gated hash routes           │
   Landing/TowerDrill/MyApps ── SYNTHESIZED data      ▼
   GraphExplorer ──► GraphAccess seam           GET /mappings/domains|grid|options
   CypherConsole ──► (dev+admin: bolt bench)    POST /mappings/changeset
        │                                             │
        ▼ api adapter (bearer token)                  ▼
 drydocs-api (FastAPI, :8001) ── sessions ── personas (role authority server-side)
   /query/{id} ── validate params ── ensure_read_only ── route DB (fail-closed)
   /raw-cypher ── admin only ────────┘                       │
        │                                        MappingStore (SQLite, read-only,
        ▼ RoutingControl.READ                    auto-built from config ledgers)
   Neo4j EE  drydocs DB                                      │
        (the loader is the ONLY writer) ◄── K2 gate ◄── git ◄┘ changeset ARTIFACT
```

A browser holds no credentials and composes no Cypher (outside the dev bench): it logs a
persona in for an opaque token, asks for named queries or mapping grids, and gets rows
plus the server-chosen database back. The one "submit" in the system returns a CSV +
manifest artifact for the gate — the graph write stays with the loader.

<!-- anchor: detailed-design -->
## Detailed design

**1. Shell & routing — state, not a router.** `App.tsx` holds `session`, `route`, `env`;
routing is `window.location.hash` + a `hashchange` listener (no react-router, by design —
revisited in O8). `lib/views.ts` is the single registry: each view carries its allowed
roles; `canSee` filters the nav, `parseRoute` fails safe (unauthorized or unknown deep
links normalize to the persona's default view via `history.replaceState`), `canDrill`
scopes tower drill-down (admin any tower; user only their own). Nav order is intentional:
Graph before Console (the wf-console-01 finding).

**2. Mock auth — client convenience, server authority.** `lib/auth.ts` persists a session
in localStorage (`drydocs.mock-session.v1`) with the role **always re-derived from
`PERSONAS`** — a forged blob degrades to sign-in. This is explicitly not security: picking
a card *is* the whole authentication, pending company-side OIDC. The server twin
(`drydocs_api/personas.py`) carries the same three ids, drift-guarded by a unit test that
parses the TS; `sessions.py` mints opaque `secrets.token_urlsafe(24)` bearer tokens bound
server-side to persona + role — the client never asserts its role to the API.

**3. Synthesized surfaces.** `Landing` (hero + tower cards), `TowerDrill` (illustrative
Cypher literal, `GraphSvg` render, schema table, anonymized preview, dependency matrix),
`MyApps` (per-persona app cards + rollup graph), `Governance` (inert placeholder) render
only in-repo SYNTHESIZED data (`data/towers.ts`, `data/myApps.ts`) and stay useful as the
no-backend demo. `GraphSvg` is a pure SVG renderer for static graph specs.

**4. The GraphAccess seam (ADR 0005).** `lib/graph.ts` defines `GraphAccess`
(`runRead`, `runNamed`) and `boltAllowed(role) = import.meta.env.DEV && role === 'admin'`
— production bundles compile the bolt path out by construction. `graphApi.ts` is the api
adapter: `POST /login` exchanges the persona id for a bearer token; `runNamed` →
`POST /query/{id}`; retries once on 401 (in-memory sessions die with the server); never
falls back to bolt, every failure is loud. `neo4j.ts` is the bolt adapter for the
dev bench: form-entered credentials (never `VITE_*`-seeded), sessions forced READ,
`runNamed` **throws** — the query registry lives server-side only, no browser fork.

**5. The live Graph view.** `GraphExplorer` (both roles) calls `runNamed('c4-graph')`
through the api adapter and lays the result out with **synchronous deterministic
d3-force** (300 ticks, fixed-seed LCG, rescaled into the viewBox) — no animation, so DOM
and screenshots are CDP-assertable. It renders real `:ControlMJob` nodes and
`WAS_INFORMED_BY` edges, a click-to-select inspector (upstream/downstream + via
condition), and the server-returned database name as the LIVE tag. No Cypher affordance
in this view. NVL was evaluated and deferred (proprietary, ~1.25 MB WebGL, opaque to DOM
assertions) — revisit at a C4 zoom ladder or >200-node scenes.

**6. The thin API.** `drydocs_api/app.py` is the only module touching FastAPI or a live
driver (optional `--with api` dependency group; CORS for the Vite origins 5173/4173);
everything else is pure and offline-testable. `LiveRunner` creates the driver lazily
(mapping-only sessions never need Neo4j) and pins `RoutingControl.READ` — the second
defense layer. `guard.ensure_read_only` is the first: it strips comments and string
literals (the ADR 0003 code-regions lesson), then rejects write clauses
(`create/merge/delete/detach/set/remove/drop/foreach`, `load csv`) with HTTP 400 before
any driver call; it runs on **both** raw Cypher (admin-only endpoint) and named queries
(defense in depth). `queries.py` registers four named queries — `overview-counts`,
`folder-census(sched_table)`, `dependency-chain(job_a, job_b)`, `c4-graph(limit=200)` —
with fail-closed param validation (unknown keys rejected, types checked, defaults
applied). `routing.py` maps every view id to its database (`drydocs`, ground truth)
fail-closed: a missing id is an error, never a default.

**7. Mapping stewardship (O13 live demo).** `mappings.py` gates `/mappings/*` to
steward-or-admin. Reads come from `MappingStore` — a read-only (`mode=ro`) SQLite
connection over `var/mapping.db`, auto-built on first use from the committed sources —
across four registered domains (two available: the ontology-map quintuple and the tier-5
job→application manual CSV; FID/ALIAS await their reconciler tables).
`draft_changeset` validates fail-closed (folder + job + seal ids required, **rationale
required**, the K2 shape `WAS_ASSOCIATED_WITH {role: seal_app_ref}` must be registered in
the vocabulary), stamps `authored_by` from the *session* persona, and returns a CSV in
the committed template column order plus a `manifest.yaml` snippet. The server writes
nothing. `static/mapping_demo.html` (served at `/demo`, same-origin, vanilla JS) is the
grayscale live-data twin of `UI-WIP/wf-mapping-01.html`: persona login → domain strip →
grid → draft tray → submitted changeset rendered back with a client-side CSV download.

<!-- anchor: design-data-mapping -->
### Source → column-level field mapping

The console ingests nothing — the one materialization it reads is built by
`drydocs_core.mapping_store.build()`: committed YAML/CSV sources
(`relationship_vocabulary.yaml`, `config/taxonomy-ontology-map.yaml`,
`config/manual-loads/*.csv` + manifest) → six SQLite tables + analytics views, with a
source-hash meta row and deterministic byte-identical rebuilds; `dump_csv` writes the
gate-reviewable text twin per table. Grid columns surfaced to the browser are the table
columns verbatim (e.g. `manual_mapping`: `file, folder_id, job_id, seal_id,
create_target_if_missing, authored_by, authored_on, note`). Otherwise: N/A — no
source→graph ingestion happens in this design.

<!-- anchor: classification-security -->
## Classification & security

This document and both components are **Internal-Public**: mechanism only. All personas,
towers, apps, and preview rows are SYNTHESIZED and banner-labeled MOCK in the UI; the
publish-boundary grep ran clean at O2/O4/O6. Security posture, by layer:

- **Credentials.** Neo4j credentials exist only in server env (`Neo4jSettings`); no
  `VITE_NEO4J_PASSWORD` in any committed env file (repo-checked at O4); the dev bolt
  bench takes localhost form-entry only.
- **AuthZ.** Roles live server-side against opaque bearer tokens; the client's
  localStorage session gates *rendering* only and degrades safely when forged.
- **Write protection.** Endpoint write-guard (HTTP 400) + `RoutingControl.READ` + the
  mapping surface's artifact-only "writes". The loader remains the only graph writer.
- **Blast radius.** Raw Cypher requires admin + (in the React app) a dev build;
  production bundles exclude the bolt path by construction.

<!-- anchor: qa-tests -->
## QA & tests

- **Offline unit suites** (pure handlers, duck-typed runner — the graph_verify idiom):
  `test_drydocs_api.py` (guard, params, routing, sessions, persona drift vs the TS, plus
  a TestClient smoke that caught a real PEP-563/FastAPI body bug),
  `test_mapping_api.py` (role gate incl. user→403, grid/options reads over a real
  materialization, artifact shape, rationale required, zero server writes),
  `test_mapping_store.py` (deterministic builds, six tables + views, source-hash meta,
  CSV read-path parity, manifest gate refusing unregistered CSVs).
- **Front-end gates:** `npm run build` (tsc) + `npm run lint` (oxlint) green; seam
  conformance is `satisfies GraphAccess` on both adapters (tsc-enforced).
- **Runtime drives (headless-Edge CDP):** 27/27 login/role regression (fresh-state
  sign-in only, hash-guard fallback, reload persistence, sign-out, admin views, corrupt
  blob degradation) and 16/16 against the full live stack at O6 — DOM node/edge counts
  asserted equal to the API payload, live job names asserted in the SVG DOM.
- **Graph invariants:** N/A — the surface is read-only; `m1/m3-verify` gate the loaders,
  not the console.

<!-- anchor: hitl-gate -->
## HITL gate & open questions

No ontology decision is made in the UI by construction: the job→application screen
*drafts* entries in the K2 shape (`WAS_ASSOCIATED_WITH {role: seal_app_ref}`, registered
in the vocabulary; manual = tier 5, never overriding SEAL evidence) and the artifact
travels git → K2 gate → loader. ADR 0005 itself passed SME review (accepted as written,
2026-07-14, recorded in the ADR + O3).

Open questions: (1) FID→seal and ALIAS→seal domains are registered but unavailable until
their reconciler tables exist (K6/T2, T3); (2) the in-memory session store resets on
restart — acceptable for the sandbox, replaced with the enterprise auth twin
company-side; (3) hash routing and the single dark theme are superseded by the O8 shell
(React Router, system-default theming) when that lands; (4) the `m3_seal_app_ref`
edge-shape follow-up gate remains open on the loader side.

<!-- anchor: traceability-matrix -->
## Requirements traceability matrix

| Requirement (source item) | Design section | Component | Test / verify | Status |
|---|---|---|---|---|
| Persona sign-in gates the console; user cannot reach the Cypher console even via URL hash (O2) | detailed-design | drydocs-web | CDP drive 27/27; `views.ts` gating under tsc | done |
| Unauthorized/unknown deep links normalize to the role default (O2) | detailed-design | drydocs-web | CDP hash-guard fallback checks | done |
| Browser never holds DB credentials; thin API is the deployment path (O3/ADR 0005) | classification-security | seam + drydocs-api | O4 repo grep: zero `VITE_NEO4J_PASSWORD`; prod-preview panel ABSENT 3/3 | done |
| Raw Cypher reachable only by admin, and in the React app only in a dev build (O4) | detailed-design | CypherConsole + handlers | CDP 3/3 + `test_drydocs_api.py` Forbidden tests | done |
| API rejects write Cypher before any driver call; READ routing pinned (O5) | detailed-design | drydocs_api/guard | `test_drydocs_api.py` guard cases | done |
| Per-view database routing decided server-side, fail-closed (O5) | detailed-design | drydocs_api/routing | `test_drydocs_api.py` routing cases | done |
| Live C4/graph view renders real edges; payload shaped server-side (O6) | detailed-design | GraphExplorer + queries.py | O6 CDP 16/16; DOM counts == API payload | done |
| Named queries param-validated fail-closed (O5/O7) | detailed-design | drydocs_api/queries | `test_drydocs_api.py` param cases | done |
| /mappings/* gated to steward/admin; user gets 403 (O13 demo) | detailed-design | drydocs_api/mappings | `test_mapping_api.py` role gate | done |
| Changeset submit writes nothing server-side; artifact in template column order with required rationale and session-stamped author (O13 demo) | detailed-design | drydocs_api/mappings | `test_mapping_api.py` artifact cases | done |
| Mapping materialization deterministic and parity-checked against the CSV parse (M0) | design-data-mapping | drydocs_core/mapping_store | `test_mapping_store.py` | done |

<!-- anchor: decisions-discussions -->
## Decisions & discussions

- **ADR 0005 (ACCEPTED)** — the load-bearing decision; every module in §Detailed design
  cites it. Company-side OIDC/SSO is its evidence-noted twin.
- **d3-force over NVL** (recorded on O6) — ISC, ~90 KB, layout-only, deterministic;
  revisit trigger: C4 zoom ladder or >200-node scenes.
- **No router / single dark theme / hash views** — deliberate O2-era scope guards, now
  explicitly superseded by `UI-WIP/site-plan.md` (O8: React Router, ReUI shell,
  system-default theming). This TDD stays DESCRIPTIVE of the built state.
- **FastAPI as an optional dependency group** — keeps the default install and the unit
  suite framework-free; the pure-handler split is what made the offline suites possible.
- **SQLite materialization is derived, never committed** — CSV/git stays gate truth
  (mapping-store plan, 2026-07-17).

<!-- anchor: appendices -->
## Appendices

**A. Endpoint inventory (drydocs-api, :8001).**

| Endpoint | Method | Role | Backing |
|---|---|---|---|
| `/health` | GET | — | static |
| `/queries` | GET | — | registry metadata |
| `/login`, `/logout` | POST | any persona | `sessions.py` |
| `/query/{id}` | POST | any authenticated | named query → Neo4j `drydocs` (READ) |
| `/raw-cypher` | POST | admin | guard → Neo4j `drydocs` (READ) |
| `/mappings/domains` · `/grid/{domain}` · `/options` | GET | steward, admin | MappingStore (SQLite ro) |
| `/mappings/changeset` | POST | steward, admin | validation only → artifact |
| `/demo` | GET | — (page logs in) | `static/mapping_demo.html` |

**B. Named-query registry.** `overview-counts` (no params) · `folder-census`
(`sched_table: string`) · `dependency-chain` (`job_a`, `job_b`: string) · `c4-graph`
(`limit: int = 200`). All read `ControlMJob`/`ControlMFolder` via
`WAS_INFORMED_BY`/`CONTAINS_JOB`; all route to `drydocs`.

**C. View registry (web console).** `landing` (admin) · `my-apps` (user, admin) ·
`graph` (both; live) · `console` (admin; bolt bench dev-only + ADK flow) · `governance`
(admin; placeholder). Default view: admin → landing, else my-apps.
