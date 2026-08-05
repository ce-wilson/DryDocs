# Runbook — run and operate `drydocs-api` (the thin read API, ADR 0005)

<!-- anchor: front-matter -->
- **Module:** drydocs-api — this runbook IS the module runbook for drydocs-api
  (V1 coverage rule; V8 ruled AUTHOR-DISTINCT rather than extending the mapping-store
  runbook, see Purpose & scope).
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 1, 2026-08-04**,
  authored at commit `c28a4d1` (post-S4: the draft/promote write surfaces are live and
  the `/mappings/*/draft` endpoints return receipts rather than whole files).
- **Classification:** Internal-Public (mechanism only — localhost ports, synthetic
  persona ids already present in committed public code; NO credentials — Neo4j settings
  live only in the repo-root `.env`, never here)
- **Audience:** anyone running the API — locally for the console or the demo, or
  operating it as the console's backend — and anyone diagnosing a refused request
- **Companion:** `drydocs_api/README.md` (the component's own surface list),
  `docs/design/drydocs-mapping-demo-runbook.md` (the `/demo` page this serves),
  `docs/design/drydocs-web-console-runbook.md` (the React console that consumes it),
  `docs/design/drydocs-mapping-store-runbook.md` (the SQLite store it reads),
  `docs/design/drydocs-startup-refresh-runbook.md` (the graph the query routes need)

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Start `drydocs-api`, understand which of its surfaces read and which write,
and diagnose a refusal. It is the server the web console and the `/demo` page talk to,
and the only component that turns an HTTP request into a graph query.

**Why this is its own document rather than a chapter of another one (V8's ruling).**
Two existing runbooks touch this component and neither can absorb it:

- the **mapping-store** runbook operates `var/mapping.db` and scopes HTTP serving OUT in
  its own words — extending it would mean reversing its stated scope;
- the **mapping-demo** runbook covers the `/demo` page, which is one route of twenty-two.

Extending either would have produced a document whose title no longer described it. So
`drydocs-api` is authored distinct, and the two siblings stay narrower than it on purpose.

**THE OPERATING RULE, and everything else here is downstream of it: the loader is the
only graph writer.** This service never writes the graph. Not "should not" — three
independent layers stop it, and they are listed in Verify because an operator's job is
to confirm they are still in place, not to trust that they are.

**In scope.** Starting the server; the read surfaces (`/query/*`, `/raw-cypher`,
`/specs/*`, `/exports/*`, `/mappings/*` reads); the one thing it DOES write — the S4
draft buffer in `var/mapping.db`; the persona/role gate; and the refusals.

**Out of scope.** The React console itself (its own runbook); building or repairing
`var/mapping.db` (the mapping-store runbook); the graph, its schema and its loaders (the
startup/refresh runbook) — this service reads the graph and never loads it.

<!-- anchor: prerequisites -->
## Prerequisites

- **The API dependency group installed.** FastAPI and uvicorn are OPTIONAL
  (`[tool.poetry.group.api]`) so the default install and the unit suite stay
  framework-free:
  ```powershell
  poetry install --with api
  ```
  Without it the import fails at `create_app`, not at startup — the failure names FastAPI.
- **`var/mapping.db`** — nothing to do. It auto-builds from the committed YAML/CSV on
  first use and rebuilds whenever those sources drift (O14). Absent, stale, corrupt and
  foreign all mean the same thing: rebuild.
- **Neo4j — ONLY for the graph routes.** The driver is LAZY, so `/mappings/*`, `/demo`
  and `/health` all work with no graph at all. `/query/*`, `/raw-cypher` and
  `/specs/*/run` need one per the startup/refresh runbook.
- **`.env` at the repo root** for the graph routes: `NEO4J_URI`, `NEO4J_USER`,
  `NEO4J_PASSWORD`, `NEO4J_DATABASE`. Names only here; the values live in that file and
  are read server-side. A credential never arrives in a request and never reaches a
  browser (ADR 0005).

<!-- anchor: startup -->
## Startup

1. **Install the API group** (once per environment):
   ```powershell
   poetry install --with api
   ```
   Success: `poetry run python -c "import fastapi, uvicorn"` prints nothing.

2. **Start the server:**
   ```powershell
   poetry run uvicorn drydocs_api.app:create_app --factory --port 8001
   ```
   Success: uvicorn logs `Application startup complete` on `http://127.0.0.1:8001`. The
   `--factory` flag is required — `create_app` is a factory, not a module-level app.

3. **Confirm it is up** (no auth needed):
   ```powershell
   curl http://localhost:8001/health
   ```
   Success: `{"status":"ok"}`. This route touches neither the graph nor the store, so a
   healthy answer here proves the process only.

4. **Get a session token.** Every other route needs one; roles are resolved server-side
   per request and never sent by the client:
   ```powershell
   curl -X POST http://localhost:8001/login -H "Content-Type: application/json" `
        -d '{\"persona_id\":\"kchen2190\"}'
   ```
   Success: a token. The synthetic personas are `jdoe4821` (user), `kchen2190` (steward)
   and `asmith7734` (admin) — `user` is deliberately refused by every `/mappings/*` route,
   which is a working gate rather than a broken install.

5. **Point a consumer at it.** The console reads `VITE_API_URL` (`web/.env.example`); the
   `/demo` page is same-origin and needs no CORS. Only `localhost:5173` and `:4173` are
   allowed origins.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

**This service has no ingest.** That is the design, not an omission: it reads what the
loaders wrote, and the CLI chain in the startup/refresh runbook is what refreshes the
graph. The two things that DO change underneath a running server:

- **The mapping store.** Edit any committed source (`config/taxonomy-ontology-map/`,
  `drydocs_core/ontology/relationship_vocabulary/`, `config/overrides/*.csv`,
  `config/manual-loads/`) and the next read rebuilds `var/mapping.db` automatically —
  source-hash comparison against the build-time `meta` rows. No restart, no manual build.
- **The graph.** Run the load chain per the startup/refresh runbook. The API needs no
  restart; it holds one lazy driver and queries per request.

**The one write this service performs**, added at S4 (ADR 0009 rule 5): console edits
land as ROWS in the `draft` table of `var/mapping.db`, and `promote` turns a draft into a
unified diff for a branch. Committed files are never touched. Full sequence:

```
POST /mappings/overrides/draft      -> {draft_id, entries, pending, committed_rows}
GET  /mappings/drafts               -> what is pending, per editing session
POST /mappings/drafts/{id}/promote  -> {diff}  ->  git apply on a branch  ->  gate
```

Two properties worth knowing when operating it: drafts survive a store REBUILD (carried
across deliberately — a rebuild is routine), and they do NOT survive DELETING
`var/mapping.db`. Check `SELECT * FROM v_open_drafts;` before removing that file.

<!-- anchor: verify -->
## Verify

**1. The service answers and the store is readable** (no graph needed):
```powershell
curl http://localhost:8001/health
curl http://localhost:8001/mappings/domains -H "Authorization: Bearer <token>"
```
Expect `status: ok`, then the domain registry with `ontology-map`, `job-application`,
`seal-contact-override` and `app-code-mapping` marked `available: true`.

**2. The role gate holds.** Log in as `jdoe4821` (role `user`) and call any
`/mappings/*` route: expect **403**. A 200 here means the gate is gone.

**3. The write guard holds — this is the check that matters.** Post a write query to
`/raw-cypher` and expect it REFUSED:
```
CREATE (n:Probe) RETURN n     ->  rejected, never executed
```
Three layers enforce it and all three should be present:
- `drydocs_api/guard.py` rejects write clauses (`CREATE`, `MERGE`, `DELETE`, `SET`, …
  plus `LOAD CSV`) by parsing the Cypher, with string and comment regions excluded so a
  literal cannot smuggle one in;
- the live runner pins `neo4j.RoutingControl.READ`, so even a guard miss cannot write;
- the graph credentials are server-side and read-only by intent.

Canonical expected values live in `tests/unit/test_guard.py` and
`tests/unit/test_mapping_api.py` — the suite is the oracle, and
`test_no_endpoint_writes_a_tracked_file` additionally proves this service writes no file
git tracks.

**4. Nothing in the API writes a committed file:**
```powershell
poetry run pytest tests/unit/test_mapping_api.py -q
```

<!-- anchor: rollback -->
## Rollback

**The server is stateless — stop it and start it again.** There is no migration to undo
and no state in the process; every route recomputes from the store or the graph.

- **A bad `var/mapping.db`:** delete it and let the next read rebuild it — BUT check
  `v_open_drafts` first (S4). Unpromoted drafts are the one thing in that file not
  derived from git, and deleting it discards them.
- **A draft you do not want:** it is a row, not a file. Mark it discarded, or promote and
  simply not apply the diff. Nothing committed has changed either way.
- **A promoted diff already applied:** it is a normal git commit on a branch — revert it
  like any other. This is the entire point of promote-emits-a-diff rather than
  server-writes-a-file.
- **The graph:** not this runbook's to roll back. See the startup/refresh runbook; this
  service cannot have damaged it.

<!-- anchor: troubleshooting -->
## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| `ModuleNotFoundError: fastapi` at startup | the API group is optional and not installed | `poetry install --with api` |
| uvicorn: "Factory has not returned an app" / app not found | `--factory` omitted; `create_app` is a factory | add `--factory` |
| **401** on every route | no token, or the header is not `Authorization: Bearer <token>` | `POST /login` and send the bearer header |
| **403** on `/mappings/*` | logged in as `jdoe4821`, role `user` | log in as `kchen2190` (steward) or `asmith7734` (admin) — the refusal is correct |
| **404 `unknown mapping domain`** | domain registered but `available: false` (`fid-seal`, `alias-seal` — their reconciler tables are not built) | expected; not a fault |
| **422** on a draft | fail-closed validation mirroring the store's own rules (missing rationale, un-canonicalizable role, override equal to the SEAL value, duplicate defined-mapping key) | the message names the entry and the rule |
| `/query/*` or `/raw-cypher` fails while `/mappings/*` works | the driver is LAZY — only graph routes need Neo4j | start the container per the startup/refresh runbook |
| A write query is refused | working as designed — the guard, then READ routing | if you need to write, use the loader; that is the rule, not a limitation |
| Browser blocked by CORS | only `localhost:5173` and `:4173` are allowed origins | serve the console from one of them, or use `/demo` (same-origin) |
| Grid shows stale mappings | it should not — O14 rebuilds on source drift | confirm the committed source actually changed; the store keys on content hashes |

<!-- anchor: contacts-escalation -->
## Contacts & escalation

The component is owned by whoever is operating the console stack; this runbook documents
mechanism only and carries no on-call rota. **Anything touching mapping SEMANTICS — a
quintuple entry, a vocabulary term, an override, a defined mapping — is HITL-gated
(`docs/restructure/03-hitl-sme-flow.md`) and is not an operational decision.** The
governing sign-offs are `ui-write-surface` SME-3 (2026-07-21) for the override surface and
`seal-app-ref-edge-reshape` (2026-08-03) for the defined-mapping domain. A draft is a
proposal; the gate reviews the promoted diff. Escalation beyond the repo does not apply —
this is a local read service over local artifacts.

<!-- anchor: appendices -->
## Appendices

**A. Route inventory** (22 routes; `drydocs_api/README.md` carries the component-level
description of each group):

| Group | Routes | Needs Neo4j |
|---|---|---|
| Health | `GET /health` | no |
| Auth | `POST /login`, `POST /logout` | no |
| Named queries | `GET /queries`, `POST /query/{id}` | **yes** |
| Ad-hoc | `POST /raw-cypher` (guarded read-only) | **yes** |
| QuerySpecs | `GET /specs`, `POST /specs/ephemeral`, `POST /specs/{id}/run`, `POST /specs/{id}/export` | **yes** |
| Exports | `GET /exports/{id}/manifest` | no |
| Mappings (read) | `GET /mappings/domains|grid/{domain}|options`, `GET /mappings/overrides/report`, `GET /mappings/app-code/migrations` | no |
| Mappings (draft) | `POST /mappings/changeset`, `POST /mappings/overrides/draft`, `POST /mappings/app-code/draft` | no |
| Drafts (S4) | `GET /mappings/drafts`, `POST /mappings/drafts/{id}/promote` | no |
| Demo | `GET /demo` | no |

Re-derive this list rather than trusting it — if the table and the code disagree, the code
wins and the table is the defect:

```powershell
Select-String -Path drydocs_api\app.py -Pattern '@app\.(get|post)\("' | ForEach-Object { $_.Line.Trim() }
```

**B. Personas** (synthetic, committed in `drydocs_api/personas.py`): `jdoe4821` = user,
`kchen2190` = steward, `asmith7734` = admin. Enterprise OIDC replaces the stub
company-side per ADR 0005; the role model does not change with it.
