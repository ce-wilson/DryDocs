# drydocs-api — thin read API over the knowledge graph

The deployment-shape access path decided by **ADR 0005**: the browser never
holds database credentials or picks a database; this component does.

- **Read-only by construction**: `guard.ensure_read_only` rejects write-shaped
  Cypher at the endpoint layer (comments/strings stripped first), and the live
  runner pins `RoutingControl.READ` behind it.
- **Per-view database routing** (`routing.py`): which database a view reads
  (`drydocs` vs `ddall`) is a server-side row, never a client string.
- **Named queries** (`queries.py`): overview-counts, folder-census,
  dependency-chain, c4-graph — params declared + validated, fail closed.
- **QuerySpec registry** (O11, `query_specs.py`): versioned module specs behind
  `GET /specs` + `POST /specs/{id}/run`, with two-path export
  (`POST /specs/{id}/export` → artifact + `GET /exports/{id}/manifest`
  provenance manifest).
- **Mappings surface** (O13/O24, read + draft only, zero graph writes):
  `/mappings/domains|grid/{domain}|options`, changeset drafting
  (`POST /mappings/changeset`), and the override-list draft/report pair
  (`POST /mappings/overrides/draft`, `GET /mappings/overrides/report`) over the
  origin-flagged mapping store. `GET /demo` serves the O13 demo page.
- **Auth stub** (`personas.py` + `sessions.py`): synthetic personas, opaque
  bearer tokens, role resolved server-side per request. Enterprise OIDC
  replaces the stub company-side (gitignored twin) per the ADR's Evidence.
- **Pure handlers** (`handlers.py`): framework-free; FastAPI (`app.py`) is an
  optional wiring layer.

## Run

```powershell
poetry install --with api          # fastapi + uvicorn (optional group)
$env:NEO4J_URI = "bolt://localhost:7687"   # config/dev-environment.yaml is the authority
$env:NEO4J_PASSWORD = "<server-side only>"
poetry run uvicorn drydocs_api.app:create_app --factory --port 8001
```

Smoke: `POST /login {"persona_id": "asmith7734"}` → bearer token →
`POST /query/overview-counts {}`. `POST /raw-cypher` is admin-only and
write-guarded. `GET /queries` lists the registry.

## Tests

Offline (`tests/unit/test_drydocs_api.py`): guard, sessions, routing, param
validation, handlers over a fake runner, persona drift vs `web/src/lib/auth.ts`.
No FastAPI import needed; the wiring test skips if the `api` group isn't installed.
