# SME — UI Launch Guide

> 2026-07-28 · branch `feat/datalens-quickwins`. How to run the DryDocs console for an
> SME review session — in today's **fixture mode** (no graph needed) or **live mode**
> (Neo4j + API). Written now so it's ready the moment the live wiring (Track-2 T2-1)
> lands; every step below already works against the producer stack. Ungoverned WIP doc —
> enters the Epic L render pipeline when the live wiring is real.

## TL;DR — fixture mode (works today, 2 commands)

```powershell
cd C:\coding\projects\DryDocs\web
npm install          # first time only
npm run dev          # → http://localhost:5173
```

Open http://localhost:5173, pick a persona (see §Personas), review. Every synthetic
surface is tagged `EXAMPLE DATA · ILLUSTRATIVE` — that tag is the honesty convention,
not an error.

## Live mode (adds the graph + API under the same UI)

Run each in its own terminal, in this order:

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
3. **Web** (same as fixture mode):
   ```powershell
   cd web; npm run dev                     # → http://localhost:5173
   ```
   If the API is not on `http://localhost:8001`, set `VITE_API_URL` in `web/.env`
   (see `web/.env.example`).

**How you know you're live:** module headers switch from the yellow
`EXAMPLE DATA · ILLUSTRATIVE` tag to `LIVE — …` (e.g. `LIVE — :JobRun envelope` on
Loads). If a QuerySpec is unreachable you get the explicit fallback banner
("Live QuerySpec loads.runs.v1 unavailable … showing the SYNTHESIZED demo frame
instead") and the view stays usable on fixtures — a dead API never blanks a page.

## Personas (mock auth — real SSO arrives with the O1 access-path ADR)

| Persona | Role | Use for |
|---|---|---|
| A. Smith (`asmith7734`) | admin | full review — all towers, all modules |
| J. Doe (`jdoe4821`) | user | the scoped experience (own tower only) |
| K. Chen (`kchen2190`) | steward | mapping-steward surfaces (manual tiers) |

Sign-out is in the header. The mock-auth banner across the top is intentional.

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
| Under the Hood | `/under-the-hood` | docmeta P0 benchmark | fixture by design (O31 refresh path) |

## Running an SME feedback pass

1. Open the wireframes for the session: `UI-WIP/wireframes/out/*.svg` (regenerate any
   time with the command below — no repo deps, no graph needed):
   ```powershell
   python UI-WIP\wireframes\render_wireframes.py
   ```
2. Every wireframe element carries a **key** (`WF-LND-05`, `WF-LDS-02`, …). Give feedback
   against keys — "WF-LND-04 still too busy" — the way gate pages key confirmations.
   `UI-WIP/wireframes/out/KEYS.md` resolves every key to its **label source, data
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
- **Neo4j auth/connection** → the API reads the standard env (`.env`); verify bolt 7687
  is reachable before suspecting the UI.
- **Blank page after pulling** → `npm install` (deps moved), then hard-refresh.
