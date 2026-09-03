# drydocs-api — thin read API over the knowledge graph

The deployment-shape access path decided by **ADR 0005**: the browser never
holds database credentials or picks a database; this component does.

- **Read-only by construction**: `guard.ensure_read_only` rejects write-shaped
  Cypher at the endpoint layer (comments/strings stripped first), and the live
  runner pins `RoutingControl.READ` behind it.
- **Per-view database routing** (`routing.py`): which database a view reads is a
  server-side row, never a client string. Since the G102 fold (2026-08-18) every
  content spec routes to `drydocs` — the row survives because server-side routing was
  never only about having a choice, and `SPEC_DATABASES` still refuses anything else.
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
- **Draft buffer + promote** (S4, ADR 0009 rule 5): override and defined-mapping
  drafting writes ROWS to the `draft` table in `var/mapping.db` and returns a
  receipt; `GET /mappings/drafts` lists what is pending per editing session and
  `POST /mappings/drafts/{draft_id}/promote` emits a unified diff to apply on a
  branch. This replaced commit-by-replace, where drafting returned the complete
  updated file — correct for one editor, and unable to survive a second, since
  two stewards each built a whole file from the same base and the later commit
  erased the earlier. **Git is still the only commit target**: the service
  writes nothing tracked, and `tests/unit/test_mapping_api.py` enforces that
  statically rather than trusting it.
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

Smoke: `POST /login {"persona_id": "morpheus"}` → bearer token →
`POST /query/overview-counts {}`. `POST /raw-cypher` is admin-only and
write-guarded. `GET /queries` lists the registry.

## Tests

Offline (`tests/unit/test_drydocs_api.py`): guard, sessions, routing, param
validation, handlers over a fake runner, persona drift vs `web/src/lib/auth.ts`.
No FastAPI import needed; the wiring test skips if the `api` group isn't installed.

## Agent query command (R9) — the graph-navigation surface for agents

`drydocs_api.agent_query` is the read-only, deterministic way an agent (or a
person at a shell) navigates the graph: the QuerySpec registry and nothing else.
There is no Cypher input on it — the only things it can be handed are a spec id
and that spec's declared params — which is the difference between it and the
`graph_query` ADK agent (`agents/README.md`), which takes raw Cypher.

```powershell
poetry run python -m drydocs_api.agent_query list                    # every spec: id, params, columns, database
poetry run python -m drydocs_api.agent_query describe <spec-id>      # one spec's contract, Cypher included
poetry run python -m drydocs_api.agent_query run <spec-id> -p limit=20   # execute; -p KEY=VALUE repeatable
```

- **One envelope.** `run` prints exactly what `POST /specs/{id}/run` returns
  (`exports.execute_spec` — the ten-key `SpecRunOut` shape), so an agent reading
  the CLI and the console reading the API see the same thing. `list` and
  `describe` print the `GET /specs` rows. No third shape.
- **Typed params from strings.** `-p` values are converted to the declared
  type before validation (`limit=20` reaches the driver as an int); an unknown
  name, a missing required param or a value that cannot take its type is refused
  BY NAME, on stdout, and the runner never runs.
- **Exit contract**: `0` ran · `1` the runner raised (driver, connection, query —
  stdout carries the class and message) · `2` usage (unknown spec, bad param,
  an ephemeral `eph.` id — those are session-scoped and this command has none).
  One JSON document on stdout for every outcome, keys sorted, ASCII-safe; a
  success IS the envelope, every failure carries `"ok": false` and `"error"`.
- **Framework-free on import**: importing the module pulls the registry, the
  guard and the validator — never fastapi, never the driver, which is built
  lazily from the server environment (`NEO4J_*`, READ routing pinned) only when
  `run` executes. The unit suite injects a fake runner through `main(argv,
  runner=...)`; `tests/unit/test_agent_query.py` pins the envelope, the
  refusals, the exit codes and the import property.
- **MCP** (`mcp-neo4j-cypher`) is the richer later option and is deliberately
  out of scope: it adds a config surface and a write-risk surface this command
  does not have. Recorded on backlog item R9.
