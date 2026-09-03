---
name: run-drydocs-console
description: Start, stop, or troubleshoot the DryDocs web console (the React/Vite UI at localhost:5173 and the drydocs-api backend at localhost:8001). Use when asked to run/start/launch the UI, web console, or front end; when the console renders but shows "nothing answered at http://localhost:8001"; when sign-in fails; or when a console page loads with stale or empty generated data. The CLI-only paths (ingest-controlm, m3-verify, the model/adapter smoke) live in the sibling run-drydocs skill.
---

The DryDocs web console is **three tiers, started in order**. Each depends on the one
before it, and the console degrades differently depending on which is missing — so
diagnose by tier before touching anything.

| # | Tier | Address | Started by |
|---|------|---------|-----------|
| 1 | Neo4j | `bolt://localhost:7687`, db `drydocs` | Docker container (see `config/dev-environment.yaml`) |
| 2 | drydocs-api | `http://127.0.0.1:8001` | `uvicorn drydocs_api.app:create_app --factory` |
| 3 | web console | `http://localhost:5173` | `npm run dev` in `web/` |

**The sibling skill is stale on this point and should not be believed:** `run-drydocs`
says DryDocs is "pure CLI with no interactive TUI or GUI." That was true before the
`web/` app and `drydocs_api` package existed. It is the right skill for the ingest
pipeline and the offline model/adapter checks; it is the wrong skill for the console.

## Start the stack

```powershell
# TIER 1 — verify, do not assume. Container name is neo4jtest on the desktop.
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# TIER 2 — the API. Run from repo root.
poetry run uvicorn drydocs_api.app:create_app --factory --port 8001

# TIER 3 — the console. Separate shell, from web/.
npm run dev
```

Then confirm each tier ANSWERED rather than merely started — a listening port is not
a working service:

```powershell
curl http://localhost:8001/health     # {"status":"ok"}
curl -I http://localhost:5173/        # 200; title is "DryDocs Console"
```

## Which tier is broken — read the symptom

- **"nothing answered at http://localhost:8001"** in the console UI → tier 2 is down.
  This is the most common failure and the reason this skill exists. The console itself
  is fine; start the API.
- **Console loads, pages render, graph panels are empty** → tier 1. The API is up but
  has no graph behind it. Check the container and the `drydocs` database.
- **Browser cannot connect at all on 5173** → tier 3, or the IPv6 gotcha below.
- **Sign-in refuses every attempt** → the credentials store, not the servers. See below.

## Gotchas — each of these has actually bitten

**`VIRTUAL_ENV` leaks on this desktop.** The Claude Code shell pre-sets `VIRTUAL_ENV`
to `agents\.venv`, which makes `poetry run` resolve the wrong environment and
`drydocs_core` imports fail. Prefix the API command: `unset VIRTUAL_ENV; poetry run
uvicorn ...`. User terminals are unaffected — this is an agent-shell condition, so do
not "fix" it in project config.

**Vite binds IPv6 localhost only.** The dev server listens on `[::1]:5173`, so
`http://localhost:5173` works while a literal `http://127.0.0.1:5173` may refuse. Use
the hostname, not the v4 literal, before concluding the server is down.

**Never pipe a dev server into `head`.** `npm run dev | head -20` swallows the banner
and leaves an empty log — the server runs, but its address line and every later HMR or
compile error are invisible. Launch unpiped and read the log file.

**CORS is an ADD-ON list, not a replacement.** `create_app()` ships an allowlist of
`http://localhost:5173` (vite dev), `4173` (vite preview) and `5199` (the ui-tests
ledger's documented verification port). `DRYDOCS_CORS_ORIGINS` ADDS to that list and
never replaces it, so a console served on any other port needs that env var rather than
an edit to the allowlist.

**Sign-in reads a machine-local credentials store.** `internal-local/console-credentials.json`
by default, overridden by `DRYDOCS_CONSOLE_CREDENTIALS`. It is gitignored and per-machine,
so a fresh clone has no personas and `/login` returns 401 for every attempt. `/login` also
returns ONE message for bad-secret and unknown-persona on purpose (enumeration), so a 401
does not tell you which it was — check the store exists before debugging the request.

## Paper form — capture a route for pen-and-paper review (O88)

With tiers 2 and 3 answering, `npm run paper -- --persona <id>` (in `web/`) signs in
through headless Edge and writes self-contained printable captures of `/gates`,
`/software` and `/load-map` (artifact-backed, no graph needed; `--routes` for others)
under `<DRYDOCS_DATA_ROOT>/console-captures/<stamp>/`, each with the L6 gutter tags and
a route/commit/time/API/persona footer. The secret is prompted, never a flag. See
`web/README.md`, "Paper form (O88)".

## Step 4 — test persona credentials (only if sign-in refuses)

The console signs in against a MACHINE-LOCAL store, so this step is per-desktop and is
not part of a normal start. Six Matrix-named personas share one dev-only secret
convention; the values live in a machine-local README under `internal-local/` (gitignored; the file name is in that directory's index), which is
gitignored, alongside the persona/role table. They are deliberately NOT written here —
this skill is tracked, and CLAUDE.md section 3 keeps credentials out of tracked surfaces.

```powershell
poetry run python scripts/set_console_credential.py --list        # which ids have one
poetry run python scripts/set_console_credential.py <persona-id>  # create or rotate
poetry run python scripts/set_console_credential.py --remove <id>
```

**Rotating while the stack is running is safe and needs no restart.** The API reads the
store at request time, so a new secret takes effect on the next sign-in; sessions already
open keep working until their token expires.

The script prompts via `getpass` and has NO `--secret-from-env` flag. That is O76's
ruling: a prompted secret was never rendered where a screen share could catch it, while a
generated one was printed once and is flagged for rotation. Do not add such a flag to feed
values in non-interactively — the e2e suite has its own entry point
(`web/e2e/bootstrap_credential.py`), which refuses to write to the real store's location.

## What the console reads

Two different sources, and confusing them wastes time:

- **Live graph data** — through tier 2 (`/demo`, `/graph/{specId}`, `/docs-verify`,
  `/intake`, 29 routes in all; `GET /openapi.json` enumerates them, `/docs` renders them).
- **Committed generated artifacts** — `web/src/generated/*.json` (gates, enforcement-matrix,
  load-map, software-registry, gazetteer, remediation-diff, remediation-profile,
  context-types, world-map.ts). These are RENDERER OUTPUT, refreshed by a default-paths
  `poetry run python scripts/render_board.py` and guarded against drift.

So a console page showing stale content is usually a stale ARTIFACT, not a stale server:
re-render, then `git status` — any diff means a committed render did not match its source.
Restarting the dev server will not fix it.

## Tests

```powershell
cd web
npm run test          # vitest unit
npm run lint          # oxlint
npm run build         # tsc -b && vite build — catches type errors the dev server tolerates
npm run test:e2e      # playwright; needs test:e2e:install once
```

The e2e suite (`web/e2e/console.spec.ts`) drives a real browser and bootstraps its own
credential (`web/e2e/bootstrap_credential.py`) — it does not reuse your machine-local
store. Python-side console guards live in `tests/unit/test_console_auth.py`,
`test_console_origins.py`, `test_load_map_console.py`, `test_world_map_generated.py`.

## Routes worth knowing

`/explorer` (+ `/explorer/live`, `/explorer/tower/:towerKey`), `/ask`, `/lineage`,
`/ownership`, `/runbooks`, `/remediation`, `/graph/:specId`, `/docs`, `/software`,
`/gates`, `/loads`, `/load-map`, `/under-the-hood`, `/intake`.

`/intake` is persona-gated — SME persona or any non-`user` role (`canAccessIntake` in
`web/src/lib/auth.ts`); the rest are open once signed in.

## Pointing the console elsewhere

`VITE_API_URL` overrides the API base. It is read in exactly two places
(`web/src/lib/auth.ts` for auth calls, `web/src/components/GraphExplorer.tsx` for graph
calls), both defaulting to `http://localhost:8001`. If you change it, add the console's
origin to `DRYDOCS_CORS_ORIGINS` on the API side or the browser will block the calls.
