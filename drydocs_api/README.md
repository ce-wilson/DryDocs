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
  (`exports.execute_spec` — the fourteen-key `SpecRunOut` shape, `truncated`/`limit`
  joined at API1 and `epistemic`/`causes` at R15), so an agent reading
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
- **MCP.** The generic `neo4j-drydocs` MCP server (free Cypher) sits beside this
  command, unchanged. Exposing the R16 verbs below as MCP tools is configuration
  that calls `main(["verb", ...])`, not a component of this package.

### Agent verbs (R16) — impact, context, trace

Three named tools over REVIEWED specs, for the questions an agent asks at the
estate's grain. Each verb IS one registry row — `verb.impact.v1`,
`verb.context.v1`, `verb.trace.v1` — and `drydocs_api/verbs.py` binds the name
to the row; `verb <name>` then takes exactly the `run` path (same validation,
`execute_spec`, envelope), so read-only, exposed Cypher and the R15 epistemic
label are inherited, not re-implemented. There is still no Cypher operand. R4's
ephemeral specs remain the escape hatch for a question no verb asks.

```powershell
poetry run python -m drydocs_api.agent_query verbs                                   # the three: params, row shape, spec
poetry run python -m drydocs_api.agent_query verb impact  -p job=<JOB_NAME>          # blast radius over the WAS_INFORMED_BY chain
poetry run python -m drydocs_api.agent_query verb context -p job=<JOB_NAME>          # folder, data center, app, team, flags, neighbors
poetry run python -m drydocs_api.agent_query verb trace   -p from_job=<A> -p to_job=<B>   # shortest chain path, one row per hop
```

| Verb | Asks about | Rows | Grain notes |
|---|---|---|---|
| `impact` | one job (`job`) | every downstream job within `VERB_CHAIN_HOPS` (12) hops: folder, distance, gating condition, shortest chain as text | downstream = informed by the seed, directly or transitively, over the derived `WAS_INFORMED_BY` edge (condition pairs only) |
| `context` | one job (`job`) | one row per folder defining that name: data center, application and developing team (through the `seal_app_ref` attribution), cyclic/critical/active, direct upstream/downstream, IN/OUT conditions | `job_name` is indexed, not unique — two rows means two folders |
| `trace` | two jobs (`from_job`, `to_job`) | one row per hop of the shortest path in either direction: step, endpoints, direction, condition | folders on both ends; no rows = no condition-derived path within the ceiling |

All three declare `CHAIN_WALK` (`epistemics.py`): the chain is blind to a
hand-off that is not a condition (a delivered file — `scheduler_depends_on_file`,
planned, no loader) and to jobs whose command line went unparsed or unresolved,
so the label is `lower-bound` while those causes stand, with the causes listed.
The API reaches the same rows at `POST /specs/verb.<name>.v1/run`; no route was
added. `tests/unit/test_agent_verbs.py` pins the binding, the inherited guards,
the envelope, the grade and the no-Cypher property.
