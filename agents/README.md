# drydocs-agents — Google ADK agent service (sandbox)

Agent flows for the DryDocs web front end, built on
[Google ADK 2.0](https://adk.dev/2.0/) (`pip install google-adk` — the OSS base of the
company-internal Fusion SmartSDK). Sibling component to [`web/`](../web/); it is **not**
part of the poetry package (`drydocs`/`drydocs_core`) — it has its own venv so the agent
runtime can be profiled/leak-tested in isolation.

## Apps (one folder = one ADK app)

| App | Kind | Purpose |
|---|---|---|
| `graph_query` | custom `BaseAgent`, **no LLM/key needed** | user message = read-only Cypher (empty = default C4 component query); returns rows as JSON. Deterministic smoke/leak-test target for React → ADK → Neo4j. |
| `core_ingest` | `LlmAgent` (Gemini) | core-module ingestion flow: inspects the graph, advises taxonomy-first ingestion. Read-only. |
| `controlm_fix` | `LlmAgent` (Gemini) | "fix Control-M" flow: walks job/dependency/owner subgraph, proposes remediation plan. Read-only. |

`common/neo4j_tool.py` holds the shared singleton Neo4j driver + `read_cypher` /
`graph_schema` tools (write clauses rejected — graph writes stay with the loaders + HITL gate).

## Run

```powershell
cd agents
.venv\Scripts\Activate.ps1          # first time: python -m venv .venv; pip install -r requirements.txt
Copy-Item .env.example .env          # fill NEO4J_PASSWORD (+ GOOGLE_API_KEY for the LLM apps)
adk api_server --allow_origins http://localhost:5173
```

Serves http://localhost:8000 — `GET /list-apps`, `POST /apps/{app}/users/{u}/sessions/{s}`,
`POST /run`. Swagger at `/docs`. (`adk web` gives the ADK dev UI instead.)

## Memory-leak testing notes

- Three separate processes by design → leaks are attributable: **ADK service** =
  `memray run -m google.adk.cli api_server` or attach tracemalloc; **React page** = Chrome
  DevTools heap-snapshot diff (watch for leaked bolt WebSockets/sessions); **Neo4j** =
  `docker stats neo4j`.
- Known growth vector: the default `InMemorySessionService` keeps every session/event in
  process memory forever — expected growth under load, not a leak; swap for a DB-backed
  session service before any long soak test.
