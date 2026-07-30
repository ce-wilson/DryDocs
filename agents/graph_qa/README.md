# graph_qa — tiered read-only Q&A over the knowledge graph (Epic R / ADR 0007)

Free-text question in, a stream of `{"kind": "step", "step": {...}}` events
while the pipeline works (R5 — the Ask spoke renders them live over the ADK
`/run_sse` transport), then **one JSON envelope** out: the answer, every
piece of Cypher that ran (and where, and how long, and how many repairs),
the sources, and the metrics block. R2 ships Tiers 0–1; the bounded
graph-of-thoughts loop (Tier 2) is R6.

**Message parts (R5):** part 0 is the question; an optional later part is
the `drydocs_control` JSON (`control.py`) carrying the console session's
drydocs-api token + url — the R4 owner-token handshake that lets the agent
register ephemeral specs the ASKING session can run/export. Control parts
never reach the LLM.

## The tiers

| Tier | What runs | Cypher shown |
|---|---|---|
| 0 | Router matches the question onto a registered QuerySpec (`drydocs_api/query_specs.py`, imported — the agent defines **no named Cypher of its own**) | the spec's Cypher, **verbatim** |
| 1 | Schema-grounded text2cypher: prompt = active `relationship_vocabulary.yaml` rows + live `graph_schema()` + few-shot spec examples (**never whole-graph state**); fix loop ≤ 2 | the generated Cypher + fix history |
| — | Neither worked → `tier: "unanswered"`, attempted Cypher + errors in `steps` | everything attempted |

**Read-only enforcement:** `drydocs_api.guard.ensure_read_only` is a
pre-flight only. The boundary is `common/graph_read.py` — every query executes
in a READ-access-mode transaction, so the **server** rejects writes the token
guards miss (`CREATE(x)`, `CALL db.createLabel(...)`).
`tests/integration/test_graph_qa_read_mode.py` proves it live. Row cap 100,
transaction timeout 15 s.

## The envelope (the contract R5 renders and R3 logs)

```json
{
  "status": "success",
  "run_id": "qa-20260723-104512-3f9c2a",
  "session_id": "…", "tier": "spec | text2cypher | unanswered",
  "question_sha256": "…", "question_chars": 42,
  "answer": "…",
  "model": "…", "provider": "anthropic | azure",
  "steps": [
    { "i": 1, "kind": "router", "spec_id": "explorer.jobs.v2", "ms": 480 },
    { "i": 2, "kind": "spec", "spec_id": "explorer.jobs.v2",
      "cypher": "MATCH …", "database": "drydocs", "rows": 42,
      "truncated": false, "fix_retries": 0, "error": null, "explore_ref": null },
    { "i": 3, "kind": "answer", "ms": 1210 }
  ],
  "sources": [ { "document": "spec:explorer.jobs.v2", "trust": "CONFIRMED",
                 "fetched_at": null, "stale": null } ],
  "metrics": {
    "iterations": 1, "llm_calls": 2,
    "tokens": { "prompt": 3100, "completion": 240, "total": 3340 },
    "context": { "rows": 42, "chunks": 0, "tokens_est": 890 },
    "memory": { "events": 6, "tokens_est": 410 },
    "cost_est_usd": null,
    "response_ms": { "total": 2400, "routing": 480, "retrieve": 130, "llm": 2210 }
  }
}
```

Notes on honesty markers: `question_sha256`/`question_chars` only — full
question text belongs to the local ledger (R3), never a persistable payload.
`*_est` token fields are ~4-chars/token estimates; exact prompt/completion
tokens come from the provider usage metadata via the extractor seam.
`explore_ref` (R4) is the ephemeral session-spec ref (`eph.<hash>`) of the
step's EXECUTED Cypher: the pipeline registers it via
`common/ephemeral_client.make_register` (needs `DRYDOCS_AGENT_REG_KEY` +
the console session's owner token, forwarded by R5 wiring) and the UI
re-runs/exports it through `/specs/{ref}/run|export`; `null` when the
registration surface isn't configured, and a registration failure never
kills an answer. `cost_est_usd` (R3) is the sum of per-call estimates from
the ledger's model→price map (`common/llm_ledger.py`); null when no ledger
is wired or the model is unpriced. R3 also adds the reserved caller-identity
slot `user_id_sha256`/`user_id_chars` (hash + length only, mirroring the
question-text rule) and two sinks beside the envelope: a per-LLM-call JSONL
ledger in DRYDOCS_LOGDIR (the ONLY home of full question text) and one
`:AgentRun` node per question in `ddcontext` via
`common/agent_run_writer.py` (surfaced by the `console.agent-runs.v1` spec).
`fetched_at`/`stale` are declared now and filled by R7. `chunks` stays 0
until doc-corpus retrieval (R7) wires in.

## Provider config (R1 axis-C ruling, gate-log 2026-07-23)

Environment-split, all ids from env — never code:

```
GRAPHQA_PROVIDER=anthropic      # local/producer (company runtime: azure)
GRAPHQA_MODEL=<model or azure deployment name>
ANTHROPIC_API_KEY=…             # provider=anthropic
AZURE_API_KEY=… AZURE_API_BASE=… AZURE_API_VERSION=…   # provider=azure
```

Both bind through `providers.LiteLlmProvider`; `extract_usage()` normalizes
Anthropic and Azure/OpenAI token metadata into one shape.

## Run

```
cd agents && adk api_server --allow_origins http://localhost:5173
# POST /apps/graph_qa/users/<u>/sessions/<s>  then  POST /run
```

Unit tests (fakes, no venv deps): `poetry run pytest tests/unit/test_graph_qa.py -q`.
Live READ-mode proof: `poetry run pytest tests/integration/test_graph_qa_read_mode.py -m integration -q`.
