# Runbook — DryDocs web console & API startup (UI server stack)

<!-- anchor: front-matter -->
- **Module:** drydocs-web — this runbook IS the module runbook for drydocs-web
  (V1 coverage rule, 2026-08-04). The `Module:` line is what
  `tests/unit/test_runbook_coverage.py` reads; coverage is a claim the document
  makes about itself, never inferred from the filename.
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 6, 2026-09-07
  audits the document against the shipped console (backlog V10, Epic V):** what you
  land on is described for the first time (the O35 category-first rebuild), the FB-03
  page designations are recorded where an operator can act on them, the standalone
  agent-test page gains the build and ship path its own header rules, and the build
  gate is corrected — it named one command while CI blocks on six. Three of those
  four were ABSENT rather than wrong, which is why the audit was worth running: a
  runbook is stale when it is silent about a surface, not only when it misdescribes
  one. **Rev 5, 2026-09-07
  adds the one-command stack (backlog O72):** Startup now offers two paths, and
  Path A is `docker compose up --wait` — Compose brings up the same processes with
  each service's health check set to that step's own success check, so a forgotten
  process is named at the shell instead of diagnosed in the browser. It is FIVE
  services, not four: ADR 0020's reverse proxy is a real process, played by Vite in
  the per-process path and by nginx in front of `dist/` here, which makes this stack
  the first place the production delivery shape actually runs. Path B, the
  per-process path, is unchanged and is kept — debugging one service is a real need.
  Not a deployment: no TLS, no Traefik. **Rev 4, 2026-09-06
  makes the console same-origin with its services (ADR 0020, backlog WEB10):** the
  browser calls the PATHS `/api` and `/agent` on the page's own origin and a reverse
  proxy forwards them — Vite's own dev and preview servers here, the Compose stack's
  proxy in production. There is no CORS allowlist, no `DRYDOCS_CORS_ORIGINS`, no
  `--allow_origins`, and no `VITE_API_URL` / `VITE_ADK_URL`: the bundle carries no
  service coordinate at all (`npm run dist:check` guards that), so one build promotes
  through every environment. Where the services live is a fact about the machine
  running Vite, read from `DRYDOCS_API_UPSTREAM` / `DRYDOCS_AGENT_UPSTREAM` with the
  ports below as defaults. The O39 deep-link template moved from a build-time variable
  to `GET /api/config`. The Rev 3 procedure is otherwise unchanged. **Rev 3, 2026-08-28
  adds the credential step (backlog O69 and O73):** sign-in proves a secret to
  drydocs-api, sessions expire, a fresh clone has no accounts until
  `scripts/set_console_credential.py` runs, and the API re-reads that file on change
  so a rotation needs no restart. `scripts/admin_demo_login.py` is the one-command
  demo path. The Rev 2 procedure is otherwise unchanged. **Rev 2, 2026-08-25**
  (Rev 1, 2026-07-21, reflected commit `6766b4c`: post-O9 shell + Explorer, post-O11
  QuerySpec registry/export, post-O22 glyph set; six Explorer frames incl. the SME
  Folders / App-codes mapping views. **Rev 2 adds the ADK agent server** — the fourth
  process, which only the Ask module talks to; it was missing from Rev 1 and its
  absence is what a 2026-08-20 session, and again a 2026-08-25 one, spent time
  diagnosing as a bare "Failed to fetch". Spec count refreshed 7 -> 35.)
- **Classification:** Internal-Public (localhost ports and synthetic persona ids only —
  all already present in committed public code; NO credentials — Neo4j settings live
  only in the repo-root `.env`, and console secrets only in a machine-local
  `console-credentials.json` under `internal-local/`; neither is ever quoted here)
- **Audience:** anyone bringing the DryDocs web console up locally — the UI stack is
  Neo4j (optional, for live frames), drydocs-api, the ADK agent server (only the Ask
  module needs it), and something serving the page and forwarding `/api` and `/agent`
  on its origin — the Vite dev server in the per-process path, a reverse proxy in
  front of `dist/` in the one-command stack
- **Companion:** `docs/design/drydocs-startup-refresh-runbook.md` (the graph itself —
  container, schema, ingest; explicitly out of scope here),
  `docs/design/drydocs-web-console-tdd.md` (architecture), `drydocs_api/README.md`,
  `docs/design/drydocs-mapping-demo-runbook.md` (the O13 `/demo` mapping page)

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Bring the DryDocs web console from OFF to VERIFIED in a local sandbox:
the thin API (`drydocs-api`, FastAPI/uvicorn on port 8001), the ADK agent server
(`agents/`, on port 8000) and the React console (`web/`, Vite on port 5173 in the
per-process path, the production build behind a proxy on 4173 in the one-command
stack), signed in and serving frames — live QuerySpec grids when the graph has data,
the SYNTHESIZED demo frames otherwise.

**In scope.** The API server (auth stub, QuerySpec registry, two-path export, mapping
store); the ADK agent server behind the Ask module; the web dev server and its
production build/preview; the one-command Compose stack that starts all of them
(O72); the mock-persona sign-in; verification of the frame/export round-trip.

**Which process serves which module.** Every module except Ask reads through
drydocs-api, reached as `/api/*` on the console's own origin (the proxy forwards it to
:8001, prefix stripped). **Ask is the only module that calls `/agent/*`** — forwarded
to the ADK server on :8000 — where `AskRoute.tsx` posts the question to the `graph_qa`
app. That asymmetry is the single most useful fact in this runbook: a console where
every page works and only Ask fails is not a broken console, it is a missing fourth
process. Since Rev 4 the page tells you so itself: the proxy answers 502 for a dead
upstream and the console reads 502/503/504 as "the service behind this path is down,
not this page".

**Out of scope.** The graph itself — container startup, schema bootstrap, and ingest
belong to the companion startup-refresh runbook. The console runs WITHOUT a live graph
(every frame falls back to demo data with a visible notice), so that runbook is a
prerequisite only for live frames. Company-side deployment (OIDC, GHE) is not covered.

<!-- anchor: prerequisites -->
## Prerequisites

1. **Toolchain:** Node.js + npm on PATH; pipx-installed Poetry with the in-project
   `.venv` synced **including the api group** — `poetry install --with api` (FastAPI +
   uvicorn are an optional dependency group so the default install stays
   framework-free).
2. **Web dependencies present:** `web/node_modules` exists — first time (or after a
   `package.json` change): `npm install --prefix web`. Symptom of skipping this:
   `tsc` errors like `Cannot find module 'react-router-dom'`.
3. **Agent dependencies present (Ask only):** `agents/` carries its OWN virtualenv and
   `requirements.txt` — it is deliberately NOT part of the poetry package, so
   `poetry install` does nothing for it. First time:
   `cd agents; python -m venv .venv; .venv\Scripts\python -m pip install --only-binary :all: -r requirements.txt`.
   The `--only-binary` is not optional on Windows: recent `litellm` sdists need a Rust
   toolchain (`agents/README.md`). The packaging split was reviewed and deliberately
   KEPT — see Idea-141 in `docs/restructure/IDEAS.md`; the short version is that folding
   `agents/` into a poetry group would oblige the company side to resolve `google-adk`
   and `litellm` on its internal index at every port, and its `click 8.4.2` hard-conflicts
   with the repo's `click >=8.0,<8.2`.
4. **`agents/.env` (Ask only):** `cp agents/.env.example agents/.env`. It is a SECOND
   env file, not a duplicate of the repo root's — see Prerequisite 5 for the merge rule.
5. **`.env` at the repo root** with `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` —
   read server-side by drydocs-api only (credentials never reach the browser; ADR
   0005). Only needed for LIVE frames: the API's driver is lazy, so the server starts
   and serves `/mappings/*` and the sign-in flow with no Neo4j at all.

   **Two env files, and the rule between them.** The agent process reads BOTH, in a
   fixed precedence: `agents/common/neo4j_tool.py` calls `load_dotenv(agents/.env)`
   first, then merges the repo-root `.env` in as a FALLBACK — a root value is applied
   only when the name is still unset or empty. `agents/graph_qa/providers.py` does the
   same for the provider keys. So `agents/.env` is an OVERRIDE LAYER, not a copy: it
   carries what is true only for the agent runtime (`GRAPHQA_PROVIDER`, `GRAPHQA_MODEL`,
   `ADK_MODEL`, `GOOGLE_API_KEY`) and may leave `NEO4J_PASSWORD` blank on purpose,
   because the root `.env` supplies it. Two practical consequences: a shared value
   belongs in the root `.env` and should be set in ONE place, and a name set to a
   non-empty value in `agents/.env` WINS — so a stale override there is invisible from
   the root file and is worth checking first when the agent reaches the wrong database.
6. **A console credential on this machine** (O69). Sign-in proves a secret now, and a
   fresh clone has none, so the first attempt on a new machine is refused with
   `no console credentials are configured on this machine`:
   ```powershell
   poetry run python scripts/set_console_credential.py morpheus
   poetry run python scripts/set_console_credential.py --list
   ```
   The secret is prompted for with no echo, hashed with scrypt, and written to a
   `console-credentials.json` under `internal-local/` — gitignored, never committed,
   never ported, and NOT under `var/` (deleting `var/` is safe precisely because
   everything in it rebuilds from committed text; a credential has no committed
   source, so it would not). That file is absent on a fresh clone by design, which is
   why it is named this way rather than as a path: a runbook that spells out a path
   is asserting the path is there. Set one secret per persona you intend to sign in
   as. Nothing here reaches the browser: the browser only ever holds the opaque token
   the API returns.

   **No restart is needed** (O73). The API re-reads the credential file when it
   changes, so adding or rotating a secret takes effect on the next sign-in. It
   decides by a stat rather than a timer, so an unchanged file costs nothing. Two
   edge cases behave differently on purpose: a file that is unreadable — corrupt, or
   caught mid-write — keeps the credentials already loaded and logs why, because
   locking everybody out during a routine rotation would be a fault caused by the
   safety behaviour; a file that is DELETED empties the store, because that is
   unambiguous. The writer replaces the file atomically, so the mid-write case is
   rare rather than routine.

   **For a demo, one command does all of this** and says what is missing:
   ```powershell
   poetry run python scripts/admin_demo_login.py                # what can sign in, is the API up
   poetry run python scripts/admin_demo_login.py --ensure       # set every account that has none
   poetry run python scripts/admin_demo_login.py --rotate admin
   poetry run python scripts/admin_demo_login.py --check-login admin
   ```
   It takes role shorthands (`admin`, `steward`, `user`, `sme`) as well as the ids
   themselves; `--ensure` with no argument covers every account in the roster. `--check-login` performs the real HTTP login the browser performs and reports
   which of the three usual causes it is: no credential set, the API not running, or
   the secret itself. `--generate` invents a secret and prints it ONCE, which is the
   right trade for a synthetic account on localhost and the wrong one anywhere else.
   The script is deliberately disposable: it is the seam ADR 0005 hands to a company
   OIDC binding, and it gets deleted rather than adapted when SSO lands.
7. **Optional — a READY graph** per the companion startup-refresh runbook, if you want
   the Explorer frames to show live rows instead of the demo fallback.
8. **Optional — `.claude/launch.json`** carries the `drydocs-web` dev-server entry for
   the Claude Code browser preview; no action needed, it is committed.

<!-- anchor: startup -->
## Startup

From OFF to READY. Run from the repo root; each step states its success check.

**Two paths, and they are alternatives, not stages.** Path A below is one command
and is the right default. Path B is the per-process path, kept because debugging
one service — `uvicorn --reload`, a breakpoint, Vite's HMR — is a real need that a
container stack does not serve.

### Path A — the whole stack, one command (backlog O72)

```powershell
docker compose up --wait          # from the repo root
```

*Success:* the command EXITS 0. `--wait` blocks until every service reports
healthy and returns non-zero if one does not, and each service's health check is
the corresponding Path B success check below — `/health` answering `ok`, the agent
server listing exactly its four apps, the page serving its mount point. So the
process you forgot is named at the shell rather than diagnosed in the browser
three layers away, which is what this path exists to fix. Then open
**http://localhost:4173** and sign in (Path B step 5 — the credential step is the
same, and the file is bind-mounted read-only from `internal-local/`).

`docker compose ps` shows the health column; `docker compose logs -f <service>`
follows one; `docker compose down` stops the stack and `down -v` also discards
its volumes.

What it starts, and how it differs from Path B:

- **five services, not four** — Neo4j, `drydocs-api`, the ADK agent server, and a
  **reverse proxy serving the production build**. ADR 0020 made the console
  same-origin with its services, so something must serve the page and forward
  `/api` and `/agent` on that same origin; in Path B that something is Vite, and
  here it is nginx in front of `dist/`. This stack is where that production shape
  first runs.
- **the console is on 4173, not 5173** — the same port Path B step 6 uses for the
  production build, and it leaves 5173 free so `npm run dev` can run beside the
  stack against the published `:8001` / `:8000`.
- **its Neo4j is NOT `neo4jtest`** — the stack has its own volumes and publishes
  no Neo4j port, so it neither collides with the canonical container nor risks two
  servers on one store. It starts EMPTY with the ADR 0002 topology provisioned, so
  frames show the demo fallback until something loads it. To point the stack at
  the graph you already have, set `DRYDOCS_STACK_NEO4J_URI=bolt://host.docker.internal:7687`.
- **no secret is baked** — Compose reads the repo-root `.env` for
  `NEO4J_PASSWORD` and `ANTHROPIC_API_KEY`, and the console credential file is a
  read-only bind mount. `.dockerignore` keeps `internal-local/`, `internal/` and
  every `.env` out of the build context.

Not in scope, deliberately: TLS, Traefik, and anything else shaped like a
deployment. This is a local convenience.

### Path B — process by process

1. **(Optional) the graph:** companion runbook Startup §1–3 (`docker start …`,
   `drydocs check`, bootstrap/supplements). Skip entirely for a demo-only console.
2. **drydocs-api:**
   ```powershell
   poetry run uvicorn drydocs_api.app:create_app --factory --port 8001
   ```
   *Success:* `Invoke-RestMethod http://localhost:8001/health` returns
   `{"status":"ok"}`; `Invoke-RestMethod http://localhost:8001/specs` lists the
   QuerySpec registry (35 specs as of Rev 2). Dev tip: add `--reload` while editing
   registry/handler code — without it the server keeps serving the import-time
   registry until restarted.
3. **ADK agent server (required for Ask, optional for everything else):**
   ```powershell
   cd agents
   .venv\Scripts\python serve.py
   ```
   *Success:* `Invoke-RestMethod http://localhost:8000/list-apps` returns exactly
   `controlm_fix, core_ingest, graph_qa, graph_query` — four apps, not five. A fifth
   entry named `common` means the launcher fell back to `adk api_server`'s flat loader;
   use `serve.py`, which hands ADK its `NestedAgentLoader` (R14). Swagger at `/docs`.
   Note the launcher is `serve.py`, NOT `adk api_server`, and the interpreter is the
   AGENTS venv — `poetry run` will not find `google-adk`.
   *Skip this step and every module still works except Ask*, which reports the server
   behind `/agent` as not answering (the proxy's 502) with nothing in the drydocs-api
   log, because the request never went to :8001. Before Rev 4 that was a bare `Failed
   to fetch`; backlog **O63** adds the page-side check.
4. **Web console (dev):**
   ```powershell
   npm run dev --prefix web
   ```
   *Success:* Vite prints `Local: http://localhost:5173/`; the sign-in screen renders
   at that URL. Any port works: the page calls `/api` and `/agent` on its own origin
   and Vite's proxy (`web/vite.config.ts`, routes from `web/delivery.json`) forwards
   them to the upstreams. If drydocs-api or the agent server is on a non-default port,
   set `DRYDOCS_API_UPSTREAM` / `DRYDOCS_AGENT_UPSTREAM` in the shell that runs `npm
   run dev` — these are read by the Vite PROCESS, never inlined into the bundle.
5. **Sign in:** choose an account, then enter its secret. The identities are synthetic
   and committed (`web/src/lib/auth.ts` / `drydocs_api/personas.py`): `morpheus` (admin
   — raw-Cypher console + `/admin` surfaces), `trinity` (steward — `/mappings`), `neo`
   (user, and the persona `/intake` opens for), and `mouse`, `tank`, `dozer` (three
   plain user-tier seats, alike in everything but identity, which is what makes
   per-persona isolation testable). The SECRETS are machine-local, from Prerequisite 6.
   *Success:* the shell renders with the aside nav; the header shows the persona chip.
   A refusal says only `invalid credentials` — the API deliberately does not say whether
   the account or the secret was wrong, because the difference is what turns a login
   route into an account enumerator.

   **What you land on (`/`, the Overview route) is CATEGORY-FIRST** since the O35
   rebuild (SME feedback FB-01/FB-02: the hub was too busy and the product name
   unreadable). Two explicit pick-lists, not a dashboard: **modules** — "what do you
   want to look at?", rendered from the same `web/src/modules/registry.ts` the aside
   nav reads, so the two cannot disagree — and **business area / tower**, which scopes
   Explorer and Lineage. The product name renders exactly once, in the nav wordmark;
   the h1 is the value proposition. Worth knowing at the console rather than in a
   design doc: a module MISSING from the landing pick-list is a registry entry
   missing, not a landing bug, and the pick-list is filtered by the signed-in
   persona's access, so two personas correctly see two different lists.

   **Which pages an SME reviews (FB-03).** The designation is `/software`, `/gates`
   and `/load-map`. They share one property that makes them the review set: each
   renders from a COMMITTED GENERATED ARTIFACT rather than from the graph, so they are
   reproducible on any machine with no Neo4j at all — which is also why the O88
   capture tool takes them as its default route set. Every other route is graph-backed
   and is only as good as the graph behind the API at that moment. Take that as the
   rule for demo and review sessions: the three designated pages are safe to show
   cold; anything else needs the graph checked first.

   **Headless verification (`?as=<personaId>`)** is a real sign-in now, so it needs a
   real secret: set `VITE_DEV_CONSOLE_SECRET` in the shell that runs `npm run dev` to
   the secret you stored for that account. There is no default and no fallback — a
   baked-in dev password is the exact thing a credential step exists to remove. Without
   it the affordance logs a warning to the browser console and shows the sign-in screen.
   It stays DEV-only, baked out of production bundles by `import.meta.env.DEV`.

   Sessions expire after 8 hours (`drydocs_api/sessions.DEFAULT_TTL`) and are held in
   memory, so an API restart also ends them. Either way the console returns to this
   screen by itself rather than rendering a shell whose every panel 401s.
6. **Production-build variant** (instead of step 4, when verifying the deployable
   bundle):
   ```powershell
   npm run build --prefix web
   npm run preview --prefix web        # serves dist/ on http://localhost:4173, same proxy
   ```
7. **The standalone agent-test page** (`/agent-test.html`) — NOT part of the console
   shell, and that is a ruling rather than an omission: the FB-04 harness was
   re-ruled an INDEPENDENT page at SME sign-off on 2026-07-29 (`config/gate-log.md`).
   No auth layer, dark view only, no shell — the minimal real-time twin of Under the
   Hood, built for the company port's live-data test, read-only throughout (O20).

   **Build and ship path, which is the part an operator needs:** it is a
   self-contained file in `web/public/`, so Vite passes it through VERBATIM — no
   build step transforms it, and it lands unchanged inside `web/dist`. It therefore
   ships with the console and needs no separate deploy. Reach it at
   `/agent-test.html` on whichever server is serving the page: `:5173` in dev,
   `:4173` for the preview or the one-command stack.

   **Open it over http, not `file://`.** The layout renders either way, so the
   distinction looks cosmetic and is not: the ADK fetch from a `file://` origin can
   be refused, and the symptom is a page that draws correctly and answers nothing.
   It also fetches no CDN, no framework and no remote fonts (the locked-down-intranet
   rule) — system and local IBM Plex only, with its token sheet hand-frozen and held
   to the console's by the WEB14 parity test.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

What "refresh" means for the UI stack — code and data reach the running servers
differently:

1. **Web code:** Vite hot-reloads on save — nothing to do. After dependency changes,
   re-run `npm install --prefix web` (Vite logs `Re-optimizing dependencies because
   lockfile has changed` on next start).
2. **API code (registry, handlers, exports):** uvicorn WITHOUT `--reload` serves the
   import-time state — restart it (or run with `--reload` in dev). A stale server is
   the classic "I added a spec but `/specs` doesn't list it" symptom.
3. **Agent code (`agents/**`):** `serve.py` runs uvicorn WITHOUT `--reload`, so the
   agent pipeline, provider adapter and prompt changes are import-time state — restart
   the process. Changing `agents/.env` ALSO needs a restart: both env readers run at
   module import, so an edited key is not picked up by a running server.
4. **Graph data:** the companion runbook's Refresh section (`refresh-reference`,
   `ingest-controlm`, corpora loads). The console needs no restart — the next frame
   fetch reads the new rows, and grids that showed the demo fallback switch to LIVE
   automatically.
5. **Mapping store (`var/mapping.db`):** self-refreshing — the O14 staleness guard
   hash-checks the committed sources on every connect and auto-rebuilds when they
   drifted. Deleting the file is also safe (rebuilds on next read).
6. **Derived artifacts:** none owned by the UI stack — renders/snapshots belong to
   the session ritual (`knowledge/depgraph-snapshots/snapshot.ps1`).

<!-- anchor: verify -->
## Verify

1. **API contract** — direct, then through the proxy (the second is what the browser
   does; a pass on the first and a fail on the second is a proxy or upstream setting,
   not the API):
   ```powershell
   Invoke-RestMethod http://localhost:8001/health          # {"status":"ok"}
   Invoke-RestMethod http://localhost:8001/specs | % id    # 35 spec ids, versioned .vN
   Invoke-RestMethod http://localhost:5173/api/health      # same body, via Vite's proxy
   Invoke-RestMethod http://localhost:5173/api/config      # {"runtime_view_url_template": ...}
   ```
2. **Agent contract (Ask only):**
   ```powershell
   Invoke-RestMethod http://localhost:8000/list-apps       # controlm_fix core_ingest graph_qa graph_query
   Invoke-RestMethod http://localhost:5173/agent/list-apps # same list, via Vite's proxy
   ```
   `graph_qa` present is the check that matters — a server that is up but does not serve
   that app is not a green for the Ask page.
3. **Frame round-trip (browser):** sign in → Explorer → each tab (Applications ·
   Folders · App codes · Jobs · Conditions · Servers) shows EITHER a LIVE grid
   (`n/m · <database> · LIVE` in the frame header) OR the demo fallback with its
   explicit notice ("QuerySpec … returned no rows … showing the SYNTHESIZED demo
   frame"). A silent empty pane is a bug, not a state.
4. **Export round-trip (proves the O11 chain):** on any LIVE frame, `⬇ CSV (full)`
   downloads the data file (internal specs: `INTERNAL__…csv` with the banner first
   line) plus the `.manifest.json` sidecar — manifest `row_count` matches the file,
   `cypher_sha256` present. Headless equivalent: POST
   `/specs/explorer.jobs.v2/export?format=csv` with a bearer token, then GET the
   `X-DryDocs-Manifest-Path` header's URL.
5. **Ask round-trip (proves the fourth process):** sign in, go to `/ask`, ask a question
   the registry can answer (`which Control-M jobs exist?`). *Success:* the turn shows the
   tier-0 router picking a named spec, the row count, and a `SOURCES ... CONFIRMED` chip
   naming the spec. A failure here is diagnosed by WHICH of the two it is: the server
   behind `/agent` not answering (nothing listening on :8000 — the service was never
   started) versus the service up and its provider key unset (`ANTHROPIC_API_KEY` in
   `agents/.env`). They are different problems
   with different fixes and only the second is fixable by editing a file.

   Note the page restores the LAST COMPLETED TURN from browser storage (O64), so an
   answer on screen after a reload is not evidence the agent is reachable — check the
   run id's date, or ask something new.
6. **Both themes:** header toggle System / Dark / Light — tokens flip everywhere
   including the React Flow canvas (no hard-coded colors).
7. **Build gate — SIX WEB COMMANDS, not one.** This step named `npm run build` alone
   until Rev 6, while CI had grown five more BLOCKING web checks around it. A local
   "green" that ran one of six is the shape of the failure Idea-111 records: the unit
   suite passed for a week while CI ran red, because nothing local resembled what CI
   was doing. The list below is read off `.github/workflows/ci.yml`, not off
   `package.json` — the scripts block holds several things CI does not gate on, and
   which ones it gates on is the only question this step answers. From `web/`:
   ```powershell
   npm run build          # tsc -b + vite build — a type error fails here
   npm run lint           # oxlint, --max-warnings 0 (the flag lives in the script, so
                          # a local run and a CI run gate identically)
   npm run bundle:check   # initial-chunk size ceiling
   npm run dist:check     # no deployment coordinate reached the bundle (ADR 0020)
   npm run test:coverage  # vitest AND the WEB13 statements floor — a ratchet that
                          # only goes up; it subsumes a bare `npm test`
   npm run test:e2e       # playwright, and it is BLOCKING, not optional
   ```
   Plus, from the repo root, `poetry run pytest -q` (the API layer is fully covered
   offline — no server or driver needed) and `poetry run python scripts/dump_openapi.py
   --check`, the other half of the O70 pair; it runs in CI's `web` job because that is
   the one venue with the `api` group installed.

   Two commands people reach for here that are NOT gates, so that a red one is priced
   correctly: `npm run audit:high` is WARN-ONLY in CI by decision (WEB13 (d) — the
   finding it closed was that nobody was looking, not the advisories themselves), and
   `npm run api:types` REGENERATES the client rather than checking it. Run the latter
   when the schema moved; `dump_openapi.py --check` is what fails if you forget.

   *Local-only caveat, and it is a machine fact rather than a defect:* `dist:check`
   fails on a machine that has a `web/.env.local`, because Vite inlines its `VITE_*`
   values into the bundle and the check exists to refuse exactly that. Move the file
   aside and rebuild to check; do not edit `src/` to satisfy it.

<!-- anchor: rollback -->
## Rollback

The console is read-only against the graph (the loaders-only rule, ADR 0005), so
rollback is process hygiene, not data recovery:

1. **Anything misbehaving:** stop the process and restart per Startup — both servers
   are stateless apart from the two items below.
2. **API sessions are in-memory:** a restart drops them; the web adapter retries once
   on 401 and re-logs-in transparently. If the UI wedges mid-retry, sign out/in.
3. **`var/mapping.db`** is a derived artifact: delete freely; it rebuilds on next read
   (O14 guard).
4. **No destructive last resort exists on this stack** — nothing the UI or API does
   writes the graph; the only write-shaped output anywhere is the O13 steward
   changeset ARTIFACT (a downloaded file that travels git + gate review).

<!-- anchor: troubleshooting -->
## Troubleshooting

Symptom → diagnosis → fix; each grounded in a real incident this stack has produced.

| Symptom | Diagnosis | Fix |
|---|---|---|
| `docker compose up --wait` exits non-zero with `container drydocs-<x>-1 is unhealthy` | Path A working as designed: the named service failed ITS success check. This is the whole point — the answer is in the message, not in the browser | `docker compose logs <x>`, then `docker inspect drydocs-<x>-1 --format '{{json .State.Health}}'` for what the probe itself printed |
| Path A: `Error ... port is already allocated` on 8000, 8001 or 4173 | Path B's processes are still running, or another stack holds the port. The two paths are alternatives | Stop the host processes, or `docker compose down`. Nothing here conflicts with `neo4jtest`: the stack publishes no Neo4j port |
| Path A: sign-in says "no console credentials are configured on this machine" | Correct on a fresh clone, and stack-independent. The credential file is bind-mounted from `internal-local/`, so the API sees exactly what the host has | Prerequisite 6, on the HOST, then `docker compose restart api` is not even needed — the API re-reads the file on change |
| Frames show "the server behind /api is not answering (the page's own server returned 502 for it)" | drydocs-api not running behind the proxy (the adapter fails loud by design — no silent bolt fallback). The page's own server IS up — it wrote the 502 | Startup step 2; if the API is up on a non-default port, set `DRYDOCS_API_UPSTREAM` for the Vite shell |
| Frames show "nothing answered at /api on this page's own origin" | The server that serves the PAGE is gone (Vite or the production proxy), so the fetch threw. Not an API fault | Restart Vite (step 4) or the proxy; a dead API never produces this message since Rev 4 |
| `ModuleNotFoundError: fastapi` / `uvicorn not found` | api dependency group not installed | `poetry install --with api` |
| `tsc: Cannot find module 'react-router-dom'` (or any dep) on build | `web/node_modules` missing/stale on this machine | `npm install --prefix web` |
| Browser console CORS errors on frame fetch | Should not occur since Rev 4 — every call is same-origin. If it does, something is fetching an absolute `http://host:port` URL instead of the `/api` path | `npm run dist:check --prefix web` names the bundle chunk carrying the coordinate; fix the call site to use `apiBaseUrl()` / `agentBaseUrl()` |
| `/specs` missing a spec you just added | uvicorn serving the import-time registry (no `--reload`) | Restart uvicorn, or dev with `--reload` (2026-07-21 incident, twice) |
| Sign-in refused with `no console credentials are configured on this machine` | Fresh clone or a new machine: the credential file does not exist yet, so there are no accounts | Prerequisite 6 — `poetry run python scripts/set_console_credential.py <persona-id>` |
| Sign-in refused with `invalid credentials` | Wrong secret, or no secret stored for that account. The message is the same either way ON PURPOSE | `scripts/admin_demo_login.py` shows which accounts are ready and whether the API is up; `--check-login <account>` says which of the three layers is actually failing |
| A freshly-set secret is still refused | Since O73 the API re-reads the file on change, so this is no longer the restart case it was on the day O69 shipped. Check you set it against the SAME checkout the API is running from — a git worktree has its own `internal-local/` | `scripts/admin_demo_login.py` prints the credential file path the API resolves; compare it with where you wrote |
| Signed out mid-session, back at the sign-in screen | The session expired (8h) or the API restarted and dropped the in-memory store. Since O69 the client no longer logs itself back in — it cannot, without the secret — so a 401 ends the session instead of being papered over | Sign in again. This is the designed behaviour, not a fault |
| `?as=<persona>` shows the sign-in screen instead of signing in | `VITE_DEV_CONSOLE_SECRET` is unset in the Vite shell, or does not match that account's stored secret | Set it in the shell running `npm run dev` and restart Vite (env is inlined at startup); the browser console carries the reason |
| Tabs all show demo fallback despite a running graph | Graph is up but EMPTY (specs ran, 0 rows), or `.env` points at the wrong Bolt port | Companion runbook Refresh section; check `.env` `NEO4J_URI` against `docker port` |
| Export downloads but manifest fetch 404s | Manifests register only when the stream COMPLETES; a cancelled download never registers | Re-export; a served manifest always describes a full file (by design) |
| Port 8001/5173/8000 already in use | Orphaned server from a previous session — a killed `npm`/shell parent leaves the `node`/`python` CHILD listening, so the port looks taken by nothing | `Get-CimInstance Win32_Process -Filter "ProcessId=<pid from netstat -ano>" | Select CommandLine` to identify it, `Stop-Process -Id <pid> -Force`, then restart. Start Vite with `--strictPort` if a fixed port matters to you (the ui-tests ledger records the port a case ran on); since Rev 4 a drifted port still works, because nothing on the API side names it |
| **Ask says the server behind `/agent` is not answering; every other module works; the drydocs-api log shows no error at all** | The ADK agent server on :8000 is not running. Ask is the ONLY module that calls `/agent`, so the request never went to :8001 and :8001 cannot log what it never received. Before Rev 4 this surfaced as a bare "Failed to fetch" | Startup step 3. Confirm first with `netstat -ano | findstr :8000` — no LISTENING row is the diagnosis (2026-08-20 and 2026-08-25 incidents; backlog **O63** makes the page do this itself) |
| Ask reaches the agent but errors with `ANTHROPIC_API_KEY is not set (agents/.env)` | Transport is fine; the graph_qa provider is unconfigured. This is a DIFFERENT failure from the row above and has a different fix | Set `ANTHROPIC_API_KEY` in `agents/.env` (never the root `.env` if the agent should differ), then RESTART the agent server — env is read at import |
| `/list-apps` returns five apps including `common` | Started with `adk api_server` (flat `AgentLoader`) instead of `serve.py` | Use `serve.py` (R14); `tests/unit/test_agents_app_discovery.py` pins the list to four |
| Agent server: `ModuleNotFoundError: google.adk` | Ran under the poetry venv, not the agents venv — `agents/` is not part of the poetry package | `agents\.venv\Scripts\python serve.py ...` (Prerequisite 3) |
| Agent reaches the wrong Neo4j database, and the root `.env` looks right | A non-empty override in `agents/.env` WINS over the root file (Prerequisite 5) | Check `agents/.env` first; blank it to fall back to the root value |

<!-- anchor: contacts-escalation -->
## Contacts & escalation

- **Owner / SME:** the repo owner (sign-offs in `config/gate-log.md`); single-operator
  sandbox — no on-call rotation.
- **Ambiguity rule:** anything touching relationship/edge meaning or a new UI WRITE
  surface is NEVER decided from a runbook — write surfaces route through the O20 gate
  (backlog) and the HITL flow (`docs/restructure/03-hitl-sme-flow.md`); everything
  else ambiguous goes to `docs/restructure/IDEAS.md` for the next groom.
- **Company-side deployment questions** (OIDC, GHE hosting): out of scope — tracked in
  the port/consumer stream, not this local procedure.

<!-- anchor: appendices -->
## Appendices

**A. Ports & URLs (local defaults — all committed in code, none secret; the BROWSER
sees only the two paths, never the ports):**

| Surface | URL | Source of the value |
|---|---|---|
| Web console (dev) | `http://localhost:5173` | Vite default; any port works (same-origin, ADR 0020) |
| Web console (preview) | `http://localhost:4173` | `vite preview` default; same proxy as dev |
| drydocs-api, as the browser calls it | `/api/*` on the page's origin | `web/delivery.json` → `apiBaseUrl()`; the proxy strips the prefix |
| drydocs-api, the process | `http://localhost:8001` | `DRYDOCS_API_UPSTREAM` default in `web/vite.config.ts`; `uvicorn --port` |
| ADK agent server, as the browser calls it (Ask only) | `/agent/*` on the page's origin | `web/delivery.json` → `agentBaseUrl()` |
| ADK agent server, the process | `http://localhost:8000` | `DRYDOCS_AGENT_UPSTREAM` default in `web/vite.config.ts`; `serve.py --port` default |
| Runtime, non-secret config | `/api/config` | `drydocs_api/app.py`; serves `DRYDOCS_RUNTIME_VIEW_URL_TEMPLATE` (O39) |
| Agent liveness / app list | `/list-apps` · `/docs` | `agents/serve.py` (ADK `get_fast_api_app`) |
| API health / specs | `/health` · `/specs` | `drydocs_api/app.py` |
| O13 mapping demo page | `http://localhost:8001/demo` | same-origin static page (pre-O13-screen) |

**B. Full cold-start sequence** (demo-only console; prepend the companion runbook's
Appendix B for a live graph):

```powershell
poetry install --with api                                        # first time
npm install --prefix web                                         # first time
poetry run uvicorn drydocs_api.app:create_app --factory --port 8001
npm run dev --prefix web                                         # proxies /api → :8001, /agent → :8000
# browse http://localhost:5173 → sign in (morpheus / trinity / mouse)
```

**B2. The Ask module additionally needs the agent server** (its own venv — see
Prerequisite 3; `poetry run` cannot start it):

```powershell
cd agents
python -m venv .venv                                             # first time
.venv\Scripts\python -m pip install --only-binary :all: -r requirements.txt   # first time
Copy-Item .env.example .env                                      # first time, then fill keys
.venv\Scripts\python serve.py
# check: Invoke-RestMethod http://localhost:8000/list-apps   → four apps incl. graph_qa
# (no --allow_origins since Rev 4: the console reaches it as /agent on its own origin)
```

**C. Console personas** (synthetic — `drydocs_api/personas.py`): `morpheus` admin ·
`trinity` steward · `neo`, `mouse`, `tank`, `dozer` user. Since O69 signing in proves
a secret and the server issues an expiring token; that credential half is what a
company replaces with OIDC at its seam (ADR 0005), keeping every route above it.
