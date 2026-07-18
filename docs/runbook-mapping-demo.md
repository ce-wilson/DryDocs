# Runbook — start the mapping-store demo site (O13)

The demo site is the live-data twin of `UI-WIP/wf-mapping-01.html`: a FastAPI server
(`drydocs_api`) serving a single-page mapping-stewardship demo at `/demo`, backed by the
SQLite mapping-store materialization (`var/mapping.db`). **Neo4j is NOT required** — the
graph driver is lazy and only `/query/*` / `/raw-cypher` touch it; all `/mappings/*`
endpoints read the SQLite store, which auto-builds from the committed YAML/CSV sources
on first use.

## Prerequisites (one-time)

```powershell
# From repo root, on the feat/mapping-store branch
poetry install --with api      # fastapi + uvicorn are an optional dependency group
```

## Start

```powershell
poetry run uvicorn drydocs_api.app:create_app --factory --port 8001
```

Then open **http://localhost:8001/demo** in a browser.

Stop with `Ctrl+C` in the terminal.

## Log in (demo personas)

The page asks for a persona id (no password — sessions are in-memory, reset on restart):

| Persona | Role | Sees |
|---------|------|------|
| `kchen2190` | steward | `/mappings/*` — **use this one for the demo** |
| `jdoe4821` | user | basic tier, no mapping stewardship |
| `asmith7734` | admin | everything incl. raw Cypher (needs Neo4j for graph queries) |

## Verify it's up

```powershell
Invoke-RestMethod http://localhost:8001/health          # -> {"status":"ok"}
```

In the demo page, after logging in as `kchen2190`, the domain list should show four
domains — `ontology-map` and `job-application` available, `fid-seal` and `alias-seal`
greyed out (reconciler tables not built yet, expected).

## Optional — pre-build / rebuild the mapping DB

The store builds itself when absent, but you can build explicitly (e.g. after editing
`config/taxonomy-ontology-map.yaml` or `config/manual-loads/`, since the running server
does not watch the sources — delete or rebuild, then restart):

```powershell
poetry run python scripts/build_mapping_db.py                       # writes var/mapping.db
poetry run python scripts/build_mapping_db.py --dump-dir var/dumps  # + gate-reviewable CSVs
```

`var/mapping.db` is DERIVED — never commit it; the committed YAML/CSV sources are truth.

## Troubleshooting

- **`ModuleNotFoundError: fastapi`** → the api group isn't installed: `poetry install --with api`.
- **Port already in use** → pick another port (`--port 8002`); the demo page is same-origin so any port works.
- **Domain grid empty / stale after config edits** → delete `var/mapping.db` and restart (or rerun the build script).
- **Graph queries fail as admin** → expected without Neo4j; only `/mappings/*` and `/demo` are offline-capable. For graph queries, configure `.env` per `.claude/skills/run-drydocs/SKILL.md`.
