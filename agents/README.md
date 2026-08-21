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
| `graph_qa` | custom `BaseAgent` + provider adapter | **the Epic R / ADR 0007 Q&A agent**: free-text question → tiered answer envelope (QuerySpec router, then schema-grounded text2cypher; per-step Cypher + metrics). Provider is env-split per the R1 ruling (local=anthropic, company=azure). See [`graph_qa/README.md`](graph_qa/README.md). |
| `core_ingest` | `LlmAgent` (Gemini, legacy demo) | core-module ingestion flow: inspects the graph, advises taxonomy-first ingestion. Read-only. |
| `controlm_fix` | `LlmAgent` (Gemini, legacy demo) | "fix Control-M" flow: walks job/dependency/owner subgraph, proposes remediation plan. Read-only. |

`common/neo4j_tool.py` holds the shared singleton Neo4j driver + `read_cypher` /
`graph_schema` tools (write-token pre-flight). `common/graph_read.py` is the graph_qa
executor — READ-access-mode transactions make the **server** the write boundary (row cap +
tx timeout; proven by `tests/integration/test_graph_qa_read_mode.py`).
`common/specs_catalog.py` imports the `drydocs_api` QuerySpec registry by path — one
Cypher source of truth, no HTTP dependency.

> **Install gotcha (2026-07-23):** recent `litellm` sdists need a Rust toolchain on
> Windows; install wheels only — `pip install --only-binary :all: litellm` (1.91.4 known
> good in this venv).

## Run

```powershell
cd agents
.venv\Scripts\Activate.ps1          # first time: python -m venv .venv; pip install -r requirements.txt
Copy-Item .env.example .env          # fill NEO4J_PASSWORD (+ GOOGLE_API_KEY for the LLM apps)
.venv\Scripts\python serve.py --allow_origins http://localhost:5173
```

Serves http://localhost:8000 — `GET /list-apps`, `POST /apps/{app}/users/{u}/sessions/{s}`,
`POST /run`. Swagger at `/docs`. (`adk web` gives the ADK dev UI instead.)

**Why `serve.py` and not `adk api_server` (R14, 2026-08-21).** `adk api_server` uses ADK's flat
`AgentLoader`, whose `/list-apps` returns every non-hidden subdirectory — so the shared-tools
package `common/` was listed as a fifth app. `serve.py` builds the identical FastAPI app but hands
it ADK's own `NestedAgentLoader` (the loader `adk web` uses), which lists a directory only when it
holds an `agent.py` or `root_agent.yaml`. Nothing moved: `common` stays importable as `common`.
**Convention:** an APP is a directory with an `agent.py`; a SHARED package has none and is therefore
never an app — put new shared tooling in `common/` (or another `agent.py`-less package), never in a
directory with an `agent.py`. `tests/unit/test_agents_app_discovery.py` holds the app list to the
four real apps.

## Memory-leak testing notes

- Three separate processes by design → leaks are attributable: **ADK service** =
  `memray run -m google.adk.cli api_server` or attach tracemalloc; **React page** = Chrome
  DevTools heap-snapshot diff (watch for leaked bolt WebSockets/sessions); **Neo4j** =
  `docker stats neo4j`.
- Known growth vector: the default `InMemorySessionService` keeps every session/event in
  process memory forever — expected growth under load, not a leak; swap for a DB-backed
  session service before any long soak test.
