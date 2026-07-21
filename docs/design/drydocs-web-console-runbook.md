# Runbook — DryDocs web console & API startup (UI server stack)

<!-- anchor: front-matter -->
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 1, 2026-07-21**
  (content reflects commit `6766b4c`: post-O9 shell + Explorer, post-O11 QuerySpec
  registry/export, post-O22 glyph set; six Explorer frames incl. the SME
  Folders / App-codes mapping views)
- **Classification:** Internal-Public (localhost ports and synthetic persona ids only —
  all already present in committed public code; NO credentials — Neo4j settings live
  only in the repo-root `.env`, never here)
- **Audience:** anyone bringing the DryDocs web console up locally — the UI stack is
  three processes: Neo4j (optional, for live frames), drydocs-api, and the Vite dev
  server
- **Companion:** `docs/design/drydocs-startup-refresh-runbook.md` (the graph itself —
  container, schema, ingest; explicitly out of scope here),
  `docs/design/drydocs-web-console-tdd.md` (architecture), `drydocs_api/README.md`,
  `docs/design/drydocs-mapping-demo-runbook.md` (the O13 `/demo` mapping page)

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Bring the DryDocs web console from OFF to VERIFIED in a local sandbox:
the thin API (`drydocs-api`, FastAPI/uvicorn on port 8001) and the React console
(`web/`, Vite on port 5173), signed in and serving frames — live QuerySpec grids when
the graph has data, the SYNTHESIZED demo frames otherwise.

**In scope.** The API server (auth stub, QuerySpec registry, two-path export, mapping
store); the web dev server and its production build/preview; the mock-persona sign-in;
verification of the frame/export round-trip.

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
3. **`.env` at the repo root** with `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` —
   read server-side by drydocs-api only (credentials never reach the browser; ADR
   0005). Only needed for LIVE frames: the API's driver is lazy, so the server starts
   and serves `/mappings/*` and the sign-in flow with no Neo4j at all.
4. **Optional — a READY graph** per the companion startup-refresh runbook, if you want
   the Explorer frames to show live rows instead of the demo fallback.
5. **Optional — `.claude/launch.json`** carries the `drydocs-web` dev-server entry for
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
   QuerySpec registry (7 specs as of Rev 1). Dev tip: add `--reload` while editing
   registry/handler code — without it the server keeps serving the import-time
   registry until restarted.
3. **Web console (dev):**
   ```powershell
   npm run dev --prefix web
   ```
   *Success:* Vite prints `Local: http://localhost:5173/`; the sign-in screen renders
   at that URL. The API's CORS allow-list is exactly `localhost:5173` (dev) and
   `localhost:4173` (preview) — serve from those ports or frames will fail CORS.
4. **Sign in:** pick a mock persona (synthetic, committed in `web/src/lib/auth.ts` /
   `drydocs_api/personas.py`): `jdoe4821` (user), `asmith7734` (admin — raw-Cypher
   console + `/admin` surfaces), `kchen2190` (steward — `/mappings`). *Success:* the
   shell renders with the aside nav; the header shows the persona chip.
5. **Production-build variant** (instead of step 3, when verifying the deployable
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
3. **Graph data:** the companion runbook's Refresh section (`refresh-reference`,
   `ingest-controlm`, corpora loads). The console needs no restart — the next frame
   fetch reads the new rows, and grids that showed the demo fallback switch to LIVE
   automatically.
4. **Mapping store (`var/mapping.db`):** self-refreshing — the O14 staleness guard
   hash-checks the committed sources on every connect and auto-rebuilds when they
   drifted. Deleting the file is also safe (rebuilds on next read).
5. **Derived artifacts:** none owned by the UI stack — renders/snapshots belong to
   the session ritual (`knowledge/depgraph-snapshots/snapshot.ps1`).

<!-- anchor: verify -->
## Verify

1. **API contract:**
   ```powershell
   Invoke-RestMethod http://localhost:8001/health          # {"status":"ok"}
   Invoke-RestMethod http://localhost:8001/specs | % id    # 7 spec ids, versioned .vN
   ```
2. **Frame round-trip (browser):** sign in → Explorer → each tab (Applications ·
   Folders · App codes · Jobs · Conditions · Servers) shows EITHER a LIVE grid
   (`n/m · <database> · LIVE` in the frame header) OR the demo fallback with its
   explicit notice ("QuerySpec … returned no rows … showing the SYNTHESIZED demo
   frame"). A silent empty pane is a bug, not a state.
3. **Export round-trip (proves the O11 chain):** on any LIVE frame, `⬇ CSV (full)`
   downloads the data file (internal specs: `INTERNAL__…csv` with the banner first
   line) plus the `.manifest.json` sidecar — manifest `row_count` matches the file,
   `cypher_sha256` present. Headless equivalent: POST
   `/specs/explorer.jobs.v2/export?format=csv` with a bearer token, then GET the
   `X-DryDocs-Manifest-Path` header's URL.
4. **Both themes:** header toggle System / Dark / Light — tokens flip everywhere
   including the React Flow canvas (no hard-coded colors).
5. **Build gate:** `npm run build --prefix web` exits 0 (tsc + vite);
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
| Port 8001/5173 already in use | Orphaned server from a previous session | Find and stop it (e.g. `Get-CimInstance Win32_Process | ? CommandLine -like '*uvicorn*'`), then restart |

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

**C. Mock personas** (synthetic — `drydocs_api/personas.py`): `jdoe4821` user ·
`asmith7734` admin · `kchen2190` steward. No credentials exist; the "auth" is a
persona-id-for-token exchange stub replaced company-side by OIDC (ADR 0005).
