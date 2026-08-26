# Runbook — DryDocs web console & API startup (UI server stack)

<!-- anchor: front-matter -->
- **Module:** drydocs-web — this runbook IS the module runbook for drydocs-web
  (V1 coverage rule, 2026-08-04). The `Module:` line is what
  `tests/unit/test_runbook_coverage.py` reads; coverage is a claim the document
  makes about itself, never inferred from the filename.
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 2, 2026-08-25**
  (Rev 1, 2026-07-21, reflected commit `6766b4c`: post-O9 shell + Explorer, post-O11
  QuerySpec registry/export, post-O22 glyph set; six Explorer frames incl. the SME
  Folders / App-codes mapping views. **Rev 2 adds the ADK agent server** — the fourth
  process, which only the Ask module talks to; it was missing from Rev 1 and its
  absence is what a 2026-08-20 session, and again a 2026-08-25 one, spent time
  diagnosing as a bare "Failed to fetch". Spec count refreshed 7 -> 35.)
- **Classification:** Internal-Public (localhost ports and synthetic persona ids only —
  all already present in committed public code; NO credentials — Neo4j settings live
  only in the repo-root `.env`, never here)
- **Audience:** anyone bringing the DryDocs web console up locally — the UI stack is
  four processes: Neo4j (optional, for live frames), drydocs-api, the ADK agent server
  (only the Ask module needs it), and the Vite dev server
- **Companion:** `docs/design/drydocs-startup-refresh-runbook.md` (the graph itself —
  container, schema, ingest; explicitly out of scope here),
  `docs/design/drydocs-web-console-tdd.md` (architecture), `drydocs_api/README.md`,
  `docs/design/drydocs-mapping-demo-runbook.md` (the O13 `/demo` mapping page)

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Bring the DryDocs web console from OFF to VERIFIED in a local sandbox:
the thin API (`drydocs-api`, FastAPI/uvicorn on port 8001), the ADK agent server
(`agents/`, on port 8000) and the React console (`web/`, Vite on port 5173), signed in
and serving frames — live QuerySpec grids when the graph has data, the SYNTHESIZED demo
frames otherwise.

**In scope.** The API server (auth stub, QuerySpec registry, two-path export, mapping
store); the ADK agent server behind the Ask module; the web dev server and its
production build/preview; the mock-persona sign-in; verification of the frame/export
round-trip.

**Which process serves which module.** Every module except Ask reads through
drydocs-api on :8001. **Ask is the only module that dials :8000** — `AskRoute.tsx`
reads a second base URL (`VITE_ADK_URL`) and posts the question to the `graph_qa` ADK
app. That asymmetry is the single most useful fact in this runbook: a console where
every page works and only Ask fails is not a broken console, it is a missing fourth
process.

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
6. **Optional — a READY graph** per the companion startup-refresh runbook, if you want
   the Explorer frames to show live rows instead of the demo fallback.
7. **Optional — `.claude/launch.json`** carries the `drydocs-web` dev-server entry for
   the Claude Code browser preview; no action needed, it is committed.

<!-- anchor: startup -->
## Startup

From OFF to READY. Run from the repo root; each step states its success check.

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
   .venv\Scripts\python serve.py --allow_origins http://localhost:5173
   ```
   *Success:* `Invoke-RestMethod http://localhost:8000/list-apps` returns exactly
   `controlm_fix, core_ingest, graph_qa, graph_query` — four apps, not five. A fifth
   entry named `common` means the launcher fell back to `adk api_server`'s flat loader;
   use `serve.py`, which hands ADK its `NestedAgentLoader` (R14). Swagger at `/docs`.
   Note the launcher is `serve.py`, NOT `adk api_server`, and the interpreter is the
   AGENTS venv — `poetry run` will not find `google-adk`.
   *Skip this step and every module still works except Ask*, which fails with a bare
   `Failed to fetch` and nothing in the drydocs-api log, because the request never
   reached :8001. Backlog **O63** exists to make the page diagnose that itself.
4. **Web console (dev):**
   ```powershell
   npm run dev --prefix web
   ```
   *Success:* Vite prints `Local: http://localhost:5173/`; the sign-in screen renders
   at that URL. The API's CORS allow-list is exactly `localhost:5173` (dev) and
   `localhost:4173` (preview) — serve from those ports or frames will fail CORS.
5. **Sign in:** pick a mock persona (synthetic, committed in `web/src/lib/auth.ts` /
   `drydocs_api/personas.py`): `jdoe4821` (user), `asmith7734` (admin — raw-Cypher
   console + `/admin` surfaces), `kchen2190` (steward — `/mappings`). *Success:* the
   shell renders with the aside nav; the header shows the persona chip.
6. **Production-build variant** (instead of step 4, when verifying the deployable
   bundle):
   ```powershell
   npm run build --prefix web
   npm run preview --prefix web        # serves dist/ on http://localhost:4173
   ```

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

1. **API contract:**
   ```powershell
   Invoke-RestMethod http://localhost:8001/health          # {"status":"ok"}
   Invoke-RestMethod http://localhost:8001/specs | % id    # 35 spec ids, versioned .vN
   ```
2. **Agent contract (Ask only):**
   ```powershell
   Invoke-RestMethod http://localhost:8000/list-apps       # controlm_fix core_ingest graph_qa graph_query
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
   naming the spec. A failure here is diagnosed by WHICH of the two it is: nothing
   listening on :8000 (the service was never started) versus the service up and its
   provider key unset (`ANTHROPIC_API_KEY` in `agents/.env`). They are different problems
   with different fixes and only the second is fixable by editing a file.

   Note the page restores the LAST COMPLETED TURN from browser storage (O64), so an
   answer on screen after a reload is not evidence the agent is reachable — check the
   run id's date, or ask something new.
6. **Both themes:** header toggle System / Dark / Light — tokens flip everywhere
   including the React Flow canvas (no hard-coded colors).
7. **Build gate:** `npm run build --prefix web` exits 0 (tsc + vite);
   `poetry run pytest -q` green (the API layer is fully covered offline — no server
   or driver needed).

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
| Frames show "drydocs-api unreachable at http://localhost:8001" | API not running (the adapter fails loud by design — no silent bolt fallback) | Startup step 2 |
| `ModuleNotFoundError: fastapi` / `uvicorn not found` | api dependency group not installed | `poetry install --with api` |
| `tsc: Cannot find module 'react-router-dom'` (or any dep) on build | `web/node_modules` missing/stale on this machine | `npm install --prefix web` |
| Browser console CORS errors on frame fetch | Console served from a port outside the API allow-list | Use 5173 (dev) or 4173 (preview); other origins need an `app.py` CORS row (reviewed change) |
| `/specs` missing a spec you just added | uvicorn serving the import-time registry (no `--reload`) | Restart uvicorn, or dev with `--reload` (2026-07-21 incident, twice) |
| Every request 401 after an API restart | In-memory session store dropped; stale token | Expected — the adapter retries once automatically; persistent 401 → sign out/in |
| Tabs all show demo fallback despite a running graph | Graph is up but EMPTY (specs ran, 0 rows), or `.env` points at the wrong Bolt port | Companion runbook Refresh section; check `.env` `NEO4J_URI` against `docker port` |
| Export downloads but manifest fetch 404s | Manifests register only when the stream COMPLETES; a cancelled download never registers | Re-export; a served manifest always describes a full file (by design) |
| Port 8001/5173/8000 already in use | Orphaned server from a previous session — a killed `npm`/shell parent leaves the `node`/`python` CHILD listening, so the port looks taken by nothing | `Get-CimInstance Win32_Process -Filter "ProcessId=<pid from netstat -ano>" | Select CommandLine` to identify it, `Stop-Process -Id <pid> -Force`, then restart. Start Vite with `--strictPort` so it fails loudly instead of drifting to 5174, which is OUTSIDE the API's CORS allow-list |
| **Ask says only "Failed to fetch"; every other module works; the drydocs-api log shows no error at all** | The ADK agent server on :8000 is not running. Ask is the ONLY module that dials :8000, so the request never reached :8001 and :8001 cannot log what it never received. The browser reports a refused TCP connection as this generic string | Startup step 3. Confirm first with `netstat -ano | findstr :8000` — no LISTENING row is the diagnosis (2026-08-20 and 2026-08-25 incidents; backlog **O63** makes the page do this itself) |
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

**A. Ports & URLs (local defaults — all committed in code, none secret):**

| Surface | URL | Source of the value |
|---|---|---|
| Web console (dev) | `http://localhost:5173` | Vite default; CORS row in `drydocs_api/app.py` |
| Web console (preview) | `http://localhost:4173` | `vite preview` default; second CORS row |
| drydocs-api | `http://localhost:8001` | `VITE_API_URL` fallback in the web adapters |
| ADK agent server (Ask only) | `http://localhost:8000` | `VITE_ADK_URL` fallback in `AskRoute.tsx`; `serve.py --port` default |
| Agent liveness / app list | `/list-apps` · `/docs` | `agents/serve.py` (ADK `get_fast_api_app`) |
| API health / specs | `/health` · `/specs` | `drydocs_api/app.py` |
| O13 mapping demo page | `http://localhost:8001/demo` | same-origin static page (pre-O13-screen) |

**B. Full cold-start sequence** (demo-only console; prepend the companion runbook's
Appendix B for a live graph):

```powershell
poetry install --with api                                        # first time
npm install --prefix web                                         # first time
poetry run uvicorn drydocs_api.app:create_app --factory --port 8001
npm run dev --prefix web
# browse http://localhost:5173 → sign in (jdoe4821 / asmith7734 / kchen2190)
```

**B2. The Ask module additionally needs the agent server** (its own venv — see
Prerequisite 3; `poetry run` cannot start it):

```powershell
cd agents
python -m venv .venv                                             # first time
.venv\Scripts\python -m pip install --only-binary :all: -r requirements.txt   # first time
Copy-Item .env.example .env                                      # first time, then fill keys
.venv\Scripts\python serve.py --allow_origins http://localhost:5173
# check: Invoke-RestMethod http://localhost:8000/list-apps   → four apps incl. graph_qa
```

**C. Mock personas** (synthetic — `drydocs_api/personas.py`): `jdoe4821` user ·
`asmith7734` admin · `kchen2190` steward. No credentials exist; the "auth" is a
persona-id-for-token exchange stub replaced company-side by OIDC (ADR 0005).
