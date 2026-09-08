# graph_qa — tiered read-only Q&A over the knowledge graph (Epic R / ADR 0007)

Free-text question in, a stream of `{"kind": "step", "step": {...}}` events
while the pipeline works (R5 — the Ask spoke renders them live over the ADK
`/run_sse` transport), then **one JSON envelope** out: the answer, every
piece of Cypher that ran (and where, and how long, and how many repairs),
the sources, and the metrics block. R2 shipped Tiers 0–1; R6 added Tier 2,
the bounded graph-of-thoughts loop.

**Message parts (R5):** part 0 is the question; an optional later part is
the `drydocs_control` JSON (`control.py`) carrying the console session's
drydocs-api session by its PUBLIC handle (`session_id`, ADR 0019) — the R4
handshake that lets the agent register ephemeral specs the ASKING session
can run/export. The bearer token never rides in a part (ADR 0019) and
neither does the api url (ADR 0020 — the agent's own deployment fact).
Control parts never reach the LLM, with **one documented exception (R19):
`clarifications`**, a list of `{term, resolution, declined}` the person
supplied after a turn came back as a clarification request — their own
words about their own terms, appended to the question as a clause for the
router and text2cypher prompts, and deliberately NOT a secret (a stored
trace should show what the person said a term meant). The R23 seam stays as
defence in depth: ADK persists every part of the user message as given, so
the launcher (`serve.py`) wraps the session service and writes a redacted
copy in which any `api_token` a stale console still sends is stored as a
fixed placeholder. A resumed invocation, which recovers its content from
stored history, degrades to "no control" exactly as a malformed part does.

## The tiers

| Tier | What runs | Cypher shown |
|---|---|---|
| — | **Clarification (R19), before anything routes:** an acronym or label-shaped
term in the question that resolves to no registered QuerySpec, no active
vocabulary row, no live label/property and no approved glossary sense
(`term_resolution.py`; `drydocs_core/glossary.py`) stops the run at
`tier: "clarification"` with a structured request — the term, its candidate
senses/labels, and the choices — instead of a silently chosen near match. The
next turn carries the person's answer in the control part and is never
re-asked; a declined term is stated on the answer, so a zero-row near match is
never presented as a finding. A lower-case question detects nothing and pays
nothing — the single pass is unchanged | none — nothing ran |
| 0 | Router matches the question onto a registered QuerySpec (`drydocs_api/query_specs.py`, imported — the agent defines **no named Cypher of its own**) | the spec's Cypher, **verbatim** |
| 1 | Schema-grounded text2cypher: prompt = active `relationship_vocabulary.yaml` rows + live `graph_schema()` + few-shot spec examples (**never whole-graph state**); fix loop ≤ 2 | the generated Cypher + fix history |
| 2 | **Only when Tier 1's context is insufficient** (`tier2.py`): a bounded enhance/solve loop — iterations ≤ 2, next-step decision by majority of 3 independent votes, Tier-1's ≤ 2 fix loop inherited, and a per-question token budget that stops exploration. Always terminates | every sub-question's Cypher, same as Tier 1 |
| — | Even Tier 2 gathered nothing → `tier: "unanswered"`, attempted Cypher + errors in `steps` | everything attempted |

**Tier-2 bounding, stated because the caps alone do not imply it:** a tied or
unparseable vote counts as **solve** (the failure mode of voting is a loop that
will not stop, so ambiguity resolves toward terminating); and the token budget
bounds **exploration**, not the whole run — once spent the loop stops enhancing,
but evidence already gathered still gets one final answer call, recorded as
`budget.exhausted`. The task graph it builds is **in-process only** (R1 gate
ruling A, 2026-07-23): it dies with the run, `task_graph.py` has no driver or
Cypher in it at all, and `tests/unit/test_tier2.py` fails if any appears.

**Read-only enforcement:** `drydocs_api.guard.ensure_read_only` is a
pre-flight only. The boundary is `common/graph_read.py` — every query executes
in a READ-access-mode transaction, so the **server** rejects writes the token
guards miss (`CREATE(x)`, `CALL db.createLabel(...)`).
`tests/integration/test_graph_qa_read_mode.py` proves it live. Row cap 100,
transaction timeout 15 s.

## The envelope (the contract R5 renders and R3 logs)

```json
{
  "status": "success | clarification",
  "run_id": "qa-20260723-104512-3f9c2a",
  "session_id": "…",
  "tier": "declared | clarification | spec | text2cypher | tier2 | unanswered",
  "question_sha256": "…", "question_chars": 42,
  "answer": "…",
  "model": "…", "provider": "anthropic | azure",
  "steps": [
    { "i": 1, "kind": "router", "spec_id": "explorer.jobs.v2", "ms": 480,
      "rationale": "the question names a folder and asks what runs in it" },
    { "i": 2, "kind": "spec", "spec_id": "explorer.jobs.v2",
      "cypher": "MATCH …", "database": "drydocs", "rows": 42,
      "truncated": false, "fix_retries": 0, "error": null, "explore_ref": null,
      "epistemic": null, "causes": [], "note": null, "rationale": null },
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
    "response_ms": { "total": 2400, "routing": 480, "retrieve": 130, "llm": 2210 },
    "budget": { "tokens_limit": 12000, "tokens_used": 3340, "exhausted": false },
    "tier2": { "engaged": false, "votes": [], "forced_solve": false }
  },
  "task_graph": [],
  "clarification": null,
  "debug_trace": false,
  "scope": null,
  "scope_note": null
}
```

R19 adds two fields. `steps[].note` is free text a step wants the trace to
show — the clarification prompt on a `clarify` step, the person's own
resolution (or `declined: ...`) on a `clarified` step; `null` on every other
kind. `clarification` is set ONLY at `tier: "clarification"` (and
`status: "clarification"`), shaped `{terms: [{term, kind, candidates,
choices}], prompt}`, with `answer` carrying the same prompt as text so a
consumer that knows nothing of R19 still shows a sentence. The two fixed
choice ids are `__free_text__` and `__proceed__` (answer anyway).

R18 adds two more, and the first is a CONTRACT CHANGE rather than a new
capture. `steps[].rationale` is the router's own one-sentence reason for the
spec it picked, on the `router` step and nowhere else — it exists because
`ROUTER_SYSTEM` now asks for a `reason` alongside `spec_id` and `params`.
Nothing generated one before, so no amount of extra logging could have
produced it; `null` means the reply carried none (a pre-R18 build, or a model
that ignored the instruction), never an empty stated reason. It is a statement
about an observable choice — an auditable decision trace — and not hidden
chain-of-thought, which this pipeline neither requests nor would receive
(`providers.py` passes no thinking parameter and reads only the message
content).

`debug_trace` says whether the `qa-debug` decision trace recorded this run. A
FLAG, never the trace: the trace text stays in `DRYDOCS_LOGDIR` under the same
sink boundary that keeps full question text out of this payload, and an admin
retrieves it from `GET /admin/qa-trace?run_id=…`. It is `false` on every server
whose `config/log-kinds.yaml` does not declare the `qa-debug` kind at
`level: DEBUG` — which is the shipped default — and an explicit `false` rather
than an absent field, so a consumer can tell "no trace was recorded" from "this
agent predates R18". Enablement is settings-level and never per request, for
the reason `api-debug` gives: an Ask question arrives as an HTTP request, and a
per-request switch would belong to whoever sent the request.

AGENT1 adds `scope` and `scope_note`. A scope is a ROUTER HINT and nothing
else: it SHORTENS the spec catalog joined into `ROUTER_SYSTEM`, so a spec
outside it is never offered and, if the router names one anyway out of another
spec's description, it is dropped exactly like a hallucinated id and Tier 1
takes over. No new tier, no second backend, no separate index. The control part
carries it (`{"drydocs_control": {"scope": "knowledge-graph"}}`); unlike
`clarifications` it never reaches a prompt as text.

`scope` reports what RAN, which is `null` on every unscoped run — and that is
every run today, because no console control sets one yet (the item's clause (d)
split: the filter and the envelope land first). `scope_note` is why a REQUESTED
scope was not honoured, because readiness is per option and only one is ready:
`knowledge-graph` is live; `vendor-corpus` is declared and refused until a spec
searches chunk text (API4) — a control over a title-and-abstract search would
claim the documents had been searched; `general-knowledge` is declared and
refused because answers here come from query results only, so it needs a
different answer contract and a ruling rather than an epistemic label. An
unknown or unready scope answers UNSCOPED and says so; it never errors, and it
never empties the catalog.

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
`:AgentRun` node per question in `drydocs` (the G102 fold, 2026-08-18) via
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

## The Tier-2 task graph (R6)

`task_graph` carries one **cumulative** snapshot per phase — `start`, one per
`iteration`, then `final` — so any single frame renders alone rather than
needing its predecessors replayed:

```json
"task_graph": [
  { "iteration": 1, "phase": "iteration",
    "nodes": [ { "id": "question-1", "kind": "question", "label": "…",
                 "iteration": 0, "rows": null },
               { "id": "evidence-3", "kind": "evidence", "label": "…",
                 "iteration": 1, "rows": 7 } ],
    "edges": [ { "source": "question-1", "target": "subquestion-2",
                 "via": "decomposes_to" } ] }
]
```

Node kinds are closed (`question | subquestion | evidence | answer`) and so are
edge verbs (`decomposes_to | evidence_for | answers`) — an open vocabulary here
would drift into an unreviewed parallel ontology sitting beside the real one.

Edges are deliberately `{source, target, via}`: exactly the record
`web/src/lib/forceLayout.ts` lays out, so the console's `TaskGraphPane` renders
a frame with no adapter between them. That pane keeps its own visual language
even though it shares the placement engine with the live job-dependency graph —
someone who mistakes a synthesized sub-question for a real graph node has been
actively misled, so the two must not look alike.
