# SME — UI Launch Guide

> 2026-07-28, revised 2026-08-20 · branch `feat/ui-workstream`. How to run the DryDocs
> console for an SME review session — in today's **fixture mode** (no graph needed) or
> **live mode** (Neo4j + API + the agent server). Ungoverned WIP doc — enters the Epic L
> render pipeline when the live wiring is real.
>
> **2026-08-20 revision, and why it is not a tidy-up:** live mode ran green here on
> Neo4j, drydocs-api and Vite with every view reading the graph — and `/ask` still
> failed, because the guide listed **three** services and the stack has **four**. The
> agent server was missing from this page entirely, so the console that this document
> called "live" was one silent step short of it. Step 3 below is that step. Verified end
> to end on the desktop against container `neo4jtest` / database `drydocs`: Loads shows
> `LIVE — :JobRun envelope`, and Ask answers from a registered QuerySpec with its source
> cited.

## TL;DR — fixture mode (works today, 2 commands)

```powershell
cd C:\coding\projects\DryDocs\web
npm install          # first time only
npm run dev          # → http://localhost:5173
```

Open http://localhost:5173, sign in as a persona (see §Personas), review. Every synthetic
surface is tagged `EXAMPLE DATA · ILLUSTRATIVE` — that tag is the honesty convention,
not an error.

## Live mode (adds the graph + API + agent under the same UI)

**Four services, each in its own terminal, in this order.** Three of them serve every
view; the fourth serves exactly one. Missing the fourth does not look like breakage
anywhere except `/ask`.

1. **Neo4j** (the local Docker EE container):
   ```powershell
   docker start <your-neo4j-container>     # bolt on 7687
   ```
   Fresh database? Run the pipeline first — `drydocs bootstrap` + loaders per
   `internal/repo-README.md`. (Bootstrap now verifies constraints loudly — see the
   D5 note there.)
2. **API** (FastAPI QuerySpec layer, port 8001):
   ```powershell
   poetry install --with api               # first time only
   poetry run uvicorn drydocs_api.app:create_app --factory --port 8001
   ```
3. **ADK agent server** (port 8000) — **only needed for the Ask spoke**, and easy to
   forget precisely because nothing else uses it. Every other view reaches the graph
   through drydocs-api; `/ask` is the one page that talks to the `graph_qa` agent
   instead, so skipping this step leaves a console that looks entirely healthy until
   someone asks a question:
   ```powershell
   cd agents
   .venv\Scripts\Activate.ps1              # first time: python -m venv .venv; pip install -r requirements.txt
   adk api_server --allow_origins http://localhost:5173
   ```
   Two things here are deliberately unlike the rest of the repo, and both bite once:
   - **Its own venv, not the poetry env** (`agents/README.md`) — `poetry run adk` will
     not find it. Whether that separation is worth keeping is open as Idea-141.
   - **Its own `agents/.env`**, separate from the repo-root `.env`: `NEO4J_*` plus
     `GRAPHQA_PROVIDER` / `GRAPHQA_MODEL` / `ANTHROPIC_API_KEY`. Both files are
     gitignored, so **a fresh clone or a new git worktree has neither** and each needs
     its own — the venv and the key do not travel with the branch.

   Confirm it before opening the page: `curl http://localhost:8000/list-apps` should
   list `graph_qa`. An unset provider key does not stop the server — it starts fine and
   fails at the first question with `ANTHROPIC_API_KEY is not set (agents/.env)`.
4. **Web** (same as fixture mode):
   ```powershell
   cd web; npm run dev                     # → http://localhost:5173
   ```
   If the API is not on `http://localhost:8001`, set `VITE_API_URL` in `web/.env`
   (see `web/.env.example`). Same for the agent server and `VITE_ADK_URL` (default
   `http://localhost:8000`).

**How you know you're live:** module headers switch from the yellow
`EXAMPLE DATA · ILLUSTRATIVE` tag to `LIVE — …` (e.g. `LIVE — :JobRun envelope` on
Loads). If a QuerySpec is unreachable you get the explicit fallback banner
("Live QuerySpec loads.runs.v1 unavailable … showing the SYNTHESIZED demo frame
instead") and the view stays usable on fixtures — a dead API never blanks a page.

## Personas (mock auth — real SSO arrives with the O1 access-path ADR)

| Persona | Role | Use for |
|---|---|---|
| Morpheus (`morpheus`) | admin | full review — all towers, all modules |
| Trinity (`trinity`) | steward | mapping-steward surfaces (manual tiers) |
| Neo (`neo`) | user | the scoped experience, plus `/intake` |
| Mouse / Tank / Dozer | user | the scoped experience (own tower only) |

Sign-out is in the header. Each account needs a secret on this machine first —
`poetry run python scripts/admin_demo_login.py --ensure` sets any that are missing.
The band across the top is a statement, not a warning: the accounts are synthetic
and their secrets are machine-local rather than issued by a directory.

## What each view backs onto (live-readiness map)

| View | Route | Backs onto | Live today? |
|---|---|---|---|
| Overview | `/` | module registry + fixtures | fixture by design |
| Explorer | `/explorer` | `drydocs` | QuerySpec-ready |
| Lineage | `/lineage` | `drydocs` (G30 ruling) | QuerySpec-ready |
| Ownership | `/ownership` | seal-attribution | QuerySpec-ready |
| Runbooks | `/runbooks` | runbook-automation | partial |
| Remediation | `/remediation` | `drydocs_remediation` | partial |
| Docs | `/docs` | docmeta | partial |
| Gates | `/gates` | HITL/review | fixture |
| Loads | `/loads` | BaseLoader `:JobRun`s | QuerySpec-ready (`loads.runs.v1`) |
| Ask | `/ask` | `graph_qa` (ADK) → drydocs | live — **needs step 3**, the only view that does |
| Software | `/software` | generated JSON + one spec | live (SME/admin only) |
| Load map | `/load-map` | `load-map.json` (generated) | live, declaration-only (SME/admin only; O57) |
| Under the Hood | `/under-the-hood` | docmeta P0 benchmark | fixture by design (O31 refresh path) |

## Running an SME feedback pass

1. Open the wireframes for the session: `docs/design/ui-exploration/wireframes/out/*.svg` (regenerate any
   time with the command below — no repo deps, no graph needed):
   ```powershell
   python docs/design/ui-exploration\wireframes\render_wireframes.py
   ```
2. Every wireframe element carries a **key** (`WF-LND-05`, `WF-LDS-02`, …). Give feedback
   against keys — "WF-LND-04 still too busy" — the way gate pages key confirmations.
   `docs/design/ui-exploration/wireframes/out/KEYS.md` resolves every key to its **label source, data
   source, React component, and graph/Cypher property**, so each comment re-attaches
   to exactly one buildable thing (the L5/L6 re-attachment idiom).
3. Where feedback lands: UI look/behavior → `docs/restructure/IDEAS.md` inbox line citing
   the key → groom. Anything about *meaning* (a label, a relationship, what an edge
   implies) → the HITL gate (`docs/restructure/03-hitl-sme-flow.md`), never decided in
   the UI session.
4. Theme note for sessions: dark is canonical; light is functional but pre-O32. Use the
   header System/Dark/Light toggle; screenshots for feedback should say which theme.

## Troubleshooting

- **Port 5173 busy** → `npm run dev -- --port 5174`.
- **API up but views stay EXAMPLE DATA** → check `VITE_API_URL`, then the API log; the
  fallback banner names the exact QuerySpec id that failed.
- **Ask says `Failed to fetch`, every other page is fine** → step 3 is not running.
  That string is the browser's generic network error, so it means "nothing answered at
  `VITE_ADK_URL`" and nothing more; check `curl http://localhost:8000/list-apps` first.
  Once the server is up the same question returns a *different* error if the provider
  key is unset — `ANTHROPIC_API_KEY is not set (agents/.env)`, which is a config
  problem, not a transport one. Backlog **O63** makes the page run this ladder itself
  instead of leaving it to a reader.
- **Neo4j auth/connection** → the API reads the standard env (`.env`); verify bolt 7687
  is reachable before suspecting the UI.
- **Blank page after pulling** → `npm install` (deps moved), then hard-refresh.
