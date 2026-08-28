# Runbook — start the mapping-store demo site (O13 `/demo`)

<!-- anchor: front-matter -->
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 3, 2026-08-04** (S5: the ontology-map source is a fragment DIRECTORY, not a
  monolith file — currency audit; on top of Rev 2, 2026-07-21)
  (L14 refit onto `runbook.outline.yaml`; relocated from `docs/runbook-mapping-demo.md`
  to `docs/design/` — the D6 either/or decided at execution: this doc now validates and
  renders through the Epic L pipeline. Content reflects the post-O24 five-domain state.)
- **Classification:** Internal-Public (mechanism only — localhost ports and the three
  synthetic demo personas; no credentials, no company values)
- **Audience:** anyone demoing the mapping-stewardship flow without a graph, or
  developing against the `/mappings/*` API offline
- **Companion:** `docs/design/drydocs-web-console-runbook.md` (the full React console —
  this demo page is its single-page predecessor), `docs/design/drydocs-startup-refresh-runbook.md`
  (the graph-backed startup this one deliberately avoids needing),
  `docs/design/ui-exploration/wf-mapping-01.html` (the wireframe this demo is the live-data twin of)

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Bring up the single-page mapping-stewardship demo: a FastAPI server
(`drydocs_api`) serving `/demo`, backed by the SQLite mapping-store materialization
(`var/mapping.db`). **Neo4j is NOT required** — the graph driver is lazy and only
`/query/*` / `/raw-cypher` touch it; every `/mappings/*` endpoint reads the SQLite
store, which auto-builds from the committed YAML/CSV sources on first use.

**In scope.** The `/demo` page and the `/mappings/*` API it exercises, offline.

**Out of scope.** The React web console on port 5173 (its own runbook, above); graph
queries (need Neo4j per the startup/refresh runbook); anything that writes — the demo
drafts artifacts only, the loader stays the only graph writer.

<!-- anchor: prerequisites -->
## Prerequisites

```powershell
# From the repo root, on main
poetry install --with api      # fastapi + uvicorn are an optional dependency group
```

Nothing else: no container, no `.env`, no credentials (demo sessions are in-memory
persona logins, no passwords).

<!-- anchor: startup -->
## Startup

1. **Start the server:**
   ```powershell
   poetry run uvicorn drydocs_api.app:create_app --factory --port 8001
   ```
   *Success:* uvicorn reports `Application startup complete.`
2. **Open the page:** http://localhost:8001/demo
   *Success:* the persona login prompt renders.
3. **Log in (demo personas** — no password; sessions are in-memory, reset on restart):

   | Persona | Role | Sees |
   |---------|------|------|
   | `trinity` | steward | `/mappings/*` — **use this one for the demo** |
   | `mouse` | user | basic tier, no mapping stewardship |
   | `morpheus` | admin | everything incl. raw Cypher (needs Neo4j for graph queries) |

   *Success:* logged in as `trinity`, the domain strip renders (see Verify).

Stop with `Ctrl+C` in the terminal.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

The store is self-refreshing: it builds itself when absent **and rebuilds itself when
the committed sources drift** (source-hash check on every read — the O14 guard), so
edits to `config/taxonomy-ontology-map/`, `config/manual-loads/`, or
`config/overrides/seal-contact-overrides.csv` are picked up on the next request
without a restart. Explicit builds remain available (e.g. for the CSV dumps):

```powershell
poetry run python scripts/build_mapping_db.py                       # writes var/mapping.db
poetry run python scripts/build_mapping_db.py --dump-dir var/dumps  # + gate-reviewable CSVs
```

`var/mapping.db` is DERIVED — never commit it; the committed YAML/CSV sources are truth.

<!-- anchor: verify -->
## Verify

```powershell
Invoke-RestMethod http://localhost:8001/health          # -> {"status":"ok"}
```

In the demo page, after logging in as `trinity`, the domain list should show **five
domains** — `ontology-map`, `seal-contact-override` and `app-code-mapping` available;
`fid-seal` and `alias-seal` greyed out (reconciler tables not built yet, expected).
(`job-application` was the third available domain until K15 retired it, and it left the
registry entirely on 2026-08-26.)
The canonical domain registry is `DOMAINS` in `drydocs_api/mappings.py` — if the page
and the registry disagree, the page is stale, not the registry.

<!-- anchor: rollback -->
## Rollback

Everything here is derived or in-memory — rollback is cheap by construction:

- **Server state:** `Ctrl+C` and restart; sessions are in-memory and reset.
- **Store state:** deleting `var/mapping.db` is always safe — the file is derived and
  rebuilds from the committed sources on the next read. There is no destructive step
  in this runbook; the demo never writes git, graph, or committed config.

<!-- anchor: troubleshooting -->
## Troubleshooting

- **`ModuleNotFoundError: fastapi`** → the api group isn't installed: `poetry install --with api`.
- **Port already in use** → pick another port (`--port 8002`); the demo page is
  same-origin so any port works. (The React console's CORS allowlist does NOT apply
  here — that constraint is the console's, not `/demo`'s.)
- **Domain grid stale after config edits** → shouldn't happen (the O14 staleness guard
  rebuilds on drift); if it somehow does, deleting `var/mapping.db` remains safe — the
  file is derived.
- **Graph queries fail as admin** → expected without Neo4j; only `/mappings/*` and
  `/demo` are offline-capable. For graph queries, configure `.env` per
  `.claude/skills/run-drydocs/SKILL.md`.

<!-- anchor: contacts-escalation -->
## Contacts & escalation

Role-based, per the repo's standing flow: the repo owner/SME owns this procedure;
anything touching **edge meaning or mapping semantics** routes to the HITL gate
(`docs/restructure/03-hitl-sme-flow.md`) — the demo's drafted change artifacts travel
git → the K2 match-policy gate → the loader, never a direct write. Steward-flow design
questions belong to `docs/design/ui-exploration/wf-mapping-01.md`; escalation beyond the repo is not
applicable (local demo, no shared infrastructure).
