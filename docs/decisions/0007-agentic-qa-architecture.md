# ADR 0007 — Agentic Q&A: a tiered read-only agent over the knowledge graph; deterministic QuerySpecs stay the data path; agent Cypher surfaces through ephemeral specs

```yaml
status: PROPOSED        # PROPOSED | ACCEPTED | SUPERSEDED — SME gate session = backlog R1
date: 2026-07-23
deciders: [chad.wilson]
layer: cross-cutting    # agents/ service + thin API + web console + docmeta; and the first real occupant of layer 4 (context graph)
affects:
  - agents/                            # new graph_qa ADK app; common/ grows a stats ledger + a QuerySpec client
  - drydocs_api/query_specs.py         # ephemeral session-scoped specs — the Cypher-exposure mechanism
  - drydocs_api/app.py                 # /specs run/export accept ephemeral ids; /raw-cypher gate UNCHANGED
  - web/src/lib/adk.ts                 # console → ADK client, promoted out of the admin bench
  - web/src/                           # the Ask spoke (new module route), under O20's zero-write rule
  - config/doc-source-registry.yaml    # refresh/sha256 policy becomes code-enforced (rescrape queue)
  - docs/restructure/backlog.yaml      # Epic R (R1–R8), phase 15
```

## Context

The console needs to answer **free-text questions**, not just render its named
views. The requirements as asked: deterministic Cypher stays behind the UI's
known views; a question triggers an agent shaped on the graph-of-thoughts
pattern; the UI **exposes the Cypher behind every answer** so the user can pick
it up and explore; every run captures **question, context size, memory size,
and agent/token metrics** for tracking; and when an unstructured source has
changed underneath its chunks, we detect it and **rescrape / update the
context** rather than answer from stale text.

Two reference architectures were analyzed side by side (2026-07-23, local
clones in the sandbox; full comparison with workflow diagrams in the analysis
artifact¹):

- **neo4j-labs/llm-graph-builder** — a single-pass RAG pipeline over a
  persistent KG. Six of seven chat modes run *deterministic* Cypher retrieval
  templates; only its "graph" mode lets the LLM write Cypher, and only that
  mode returns `cypher_query` to the UI. Strong: the per-answer info envelope
  (tokens, response time, mode, node details), the Document status lifecycle
  with explicit reprocess conditions, Neo4j-backed chat memory.
- **spcl/knowledge-graph-of-thoughts (KGoT)** — an iterative controller that
  builds a *task-scoped* KG per question: majority-vote INSERT (tools + LLM
  Cypher writes) vs RETRIEVE (query + parse), fix-Cypher repair loops on every
  failure, forced-solve fallbacks, and a per-LLM-call JSONL cost ledger
  (function, model, prompt/completion tokens, cost, duration).

What exists here already: the `agents/` ADK service with read-only graph tools
(`read_cypher` token-guard + READ routing); `drydocs_api` with ~22 versioned,
classification-aware QuerySpecs, provenance-stamped exports, and an
admin-gated `/raw-cypher` (ADR 0005); the `GraphAccess` seam in `web/src/lib/`;
the O20 standing ruling (**the UI performs zero graph writes**); the four-DB
topology (ADR 0002: `drydocs` truth / `ddcontext` uncertain / composite); the
doc-source registry's *policy* that a sha256 change on refetch re-queues
curation (ADR 0006 — not yet code-enforced); and the open LLM-key question in
IDEAS.md (2026-07-03).

The forces:

1. **Neither reference transfers wholesale.** llm-graph-builder's mode picker
   pushes retrieval strategy onto the user and cannot multi-hop; KGoT's loop
   assumes an ephemeral graph it may freely write and injects the *entire
   graph state* into every prompt — impossible against a persistent KG, and
   its INSERT branch collides head-on with O20.
2. **DryDocs already owns a better deterministic layer than either project** —
   the QuerySpec registry. An agent that bypasses it would fork the Cypher
   source of truth.
3. **The trust and publish boundaries apply to answers too**: which DB a
   question reads is a routing decision; answer text carries trust tier and
   classification; question text can contain Internal data and must not land
   in the repo or the graph.
4. **KGoT's task graph is our layer 4.** CLAUDE.md names the context graph
   ("what matters right now for this task") as future; the agent's working
   memory is exactly that object, so its residency must be decided, not
   improvised.

## Decision

**A tiered, read-only Q&A agent lives in `agents/` as an ADK app
(`graph_qa`), consumes the QuerySpec registry as its deterministic layer,
escalates through schema-grounded text2cypher to a bounded graph-of-thoughts
loop, exposes every executed Cypher via ephemeral session specs in
`drydocs_api`, and captures a per-run telemetry envelope plus a per-LLM-call
ledger.** Concretely:

1. **Tiering.** Tier 0: a router maps the question onto a registered QuerySpec
   when one fits — deterministic answer, spec Cypher shown verbatim. Tier 1:
   schema-grounded text2cypher — the prompt is assembled from the ontology
   vocabulary (`relationship_vocabulary.yaml`), live `graph_schema` output,
   and few-shot spec examples, **never** whole-graph state — with a
   fix-Cypher loop (≤2) on execution error. Tier 2: only when Tier 1's
   context is insufficient — a bounded enhance/solve loop (iterations ≤2,
   vote ×3, forced-solve fallback, per-question token budget).
2. **Read-only is enforced server-side.** Agent queries execute in READ
   access mode so the server rejects writes (the `_WRITE_TOKENS` string guard
   remains only as a fast pre-flight — it is not a security boundary; it
   misses `CALL apoc.*` writes). Row caps and query timeouts apply. O20
   stands: nothing in this path writes ground truth.
3. **The enhance branch writes only the task-scoped context graph.** Default
   residency proposal: **in-process task graph** (KGoT's NetworkX shape) —
   zero persistence risk, dies with the run. Escalation residency — persisting
   task graphs to `ddcontext` as SYNTHESIZED, session-tagged, TTL-swept — is a
   **gate decision at R1**, not a default.
4. **Cypher exposure via ephemeral specs.** Every executed query (all tiers)
   is registered server-side as an ephemeral, session-scoped spec
   (hash-addressed id, read-only re-validated, TTL-bounded). The response
   carries the display text plus the `explore_ref`; Open-in-Explorer and
   Export reuse the existing `/specs/{id}/run|export` paths — provenance
   manifest, classification stamping, and DB routing come for free, and the
   browser still never submits raw Cypher. `/raw-cypher` stays admin+dev
   gated exactly per ADR 0005. Recurring Tier-1 Cypher becomes a *promotion
   feed* of candidates for permanent, reviewed specs — gate-bound, never
   auto-registered.
5. **Telemetry contract** (the asked-for metrics, three sinks):
   - *per-LLM-call JSONL ledger* in `DRYDOCS_LOGDIR` (never the repo):
     run_id, step, model, prompt/completion tokens, cost estimate,
     duration, iteration — KGoT's `collect_stats` pattern;
   - *per-question `:AgentRun` envelope* mirroring `:JobRun` (kind `qa`):
     question **sha256 + length only** (full text lives solely in the local
     ledger), tier reached, iterations, LLM calls, token totals, context size
     (tokens + chunks/rows), memory size (session events + tokens), Cypher
     count, fix retries, specs used, DBs touched, timing breakdown,
     staleness flags. Residency: **never `drydocs`** — target DB is part of
     the R1 gate (proposal: `ddcontext`), written through a dedicated writer
     boundary in the agent service, not from the UI;
   - *the UI info payload* — the same envelope rendered as a "How I got
     this" panel (answer, steps with Cypher/database/rows/ms, sources with
     trust tier, metrics chip).
6. **Freshness & rescrape.** `:Document` nodes carry `source_url`,
   `source_sha256`, `fetched_at`, refresh policy, and a status lifecycle
   (llm-graph-builder's shape). At answer time cited chunks are checked
   against policy; stale citations are flagged in the answer. Rescrape is a
   **queued refresh artifact**, never an inline write: auto-runnable for
   SYNTHESIZED corpora, re-queues HITL curation for CONFIRMED (the registry's
   sha256 rule, now code-enforced). A changed sha means **full re-chunk** —
   llm-graph-builder's resume-from-position path is explicitly not adopted
   for changed content (it reuses chunk nodes by position and corrupts
   context). The Ask spoke offers "rescrape & re-answer", keeping both
   envelopes for comparison.
7. **Left open for the R1 gate** (with the ADR review): context-graph
   escalation residency (3), `:AgentRun` target DB (5), and the **LLM key
   strategy** — Gemini (`GOOGLE_API_KEY`, the Fusion-SmartSDK-shaped default)
   vs Anthropic via LiteLLM; either way one usage-extractor seam normalizes
   provider token metadata (llm-graph-builder's `get_total_tokens` is the
   template), and every model id stays in config (KGoT hardcodes a tool
   model in code — a known trap in their repo).

## Options considered

### A — llm-graph-builder pattern wholesale (mode-picker RAG)

| Dimension | Assessment |
|---|---|
| Complexity | Low-medium — proven single-pass pipeline |
| Answer quality | Good for lookup/summary; cannot multi-hop or decompose |
| Fit to existing seams | Poor — parallel retrieval stack beside the QuerySpec registry |
| Cost/question | Low (~2–3 LLM calls) |

**Rejected as the shape**: the mode picker externalizes retrieval strategy to
the user, the pipeline cannot reason across hops the way support questions
need, and its per-mode retrieval templates would duplicate what QuerySpecs
already are. **Adopted from it**: the info envelope, the Document status
lifecycle + reprocess semantics, token-cutoff discipline, and the
usage-extractor seam.

### B — KGoT pattern wholesale (full iterative controller)

| Dimension | Assessment |
|---|---|
| Complexity | High — controller, dual LLM roles, tool fleet |
| Answer quality | Strongest on hard multi-hop reasoning |
| Fit to existing seams | Collides — INSERT branch vs O20; whole-graph prompts vs a persistent KG |
| Cost/question | Dozens of LLM calls, minutes of latency |

**Rejected as the shape**: unbounded cost/latency for console use, prompts
that cannot scale past a toy graph, no UI contract, and a write model our
standing rulings forbid. **Adopted from it**: the tiered escalation *into* a
bounded loop, the fix-Cypher discipline, majority voting, forced-solve
fallbacks, the per-call cost ledger, and per-iteration snapshots.

### C — Tiered hybrid on existing seams (**chosen**)

| Dimension | Assessment |
|---|---|
| Complexity | Medium — one new ADK app + one thin-API extension + one UI spoke |
| Answer quality | Deterministic where possible; reasoning only where needed |
| Fit to existing seams | Native — QuerySpecs, GraphAccess, O20, doc-source registry all load-bearing |
| Cost/question | Scales with difficulty; capped by budget + forced-solve |

Also considered under C: **hosting the agent inside `drydocs_api`** instead of
ADK. Rejected — the company shape is Fusion SmartSDK on ADK, the ADK service
already exists with read-only graph tools, and ADR 0005 deliberately kept the
thin API small. The drift risk (two Cypher homes) is closed by the agent
*consuming* the QuerySpec registry rather than growing its own named queries.

## Trade-off analysis

The deciding structure mirrors ADR 0005: **every governance force — read-only
enforcement, DB routing, classification stamping, provenance, Cypher
exposure — already has a server-side home in `drydocs_api`; every reasoning
force belongs in the agent tier.** The tiering keeps the expensive machinery
(Tier 2) off the hot path: most console questions should terminate at Tier 0/1
in seconds, and the ledger exists precisely so the caps (iterations, votes,
budget) are tuned from measured cost rather than guessed. The ephemeral-spec
mechanism spends a small amount of server state to avoid loosening the
raw-Cypher gate — the alternative (letting the browser re-submit agent Cypher)
would re-open the boundary ADR 0005 closed.

## Consequences

- **Easier:** free-text answers with every Cypher inspectable and re-runnable;
  one Cypher source of truth (specs) with a measured promotion path;
  layer 4 gets a concrete, bounded first occupant; run telemetry becomes
  queryable next to load telemetry (`:JobRun` / `:AgentRun`); stale-source
  policy stops being prose and starts being code.
- **Harder:** three moving parts to keep honest (agent app, ephemeral-spec
  registry, Ask spoke) — the envelope contract needs a conformance test;
  the ADK in-memory session store must be swapped for a DB-backed one before
  any soak (memory-size telemetry doubles as the verification); composite-DB
  (`ddall`) questions need explicit routing (default: single routed DB per
  question, multi-DB as multi-step plans).
- **Revisit if:** the company Fusion SmartSDK diverges from OSS ADK in a way
  that breaks the app shape; or Tier-2 usage data shows the loop is either
  never reached (delete it) or dominates cost (raise Tier-1 quality instead);
  or per-user Neo4j entitlements ever arrive (reopens parts of ADR 0005, not
  this ADR).

## Action items

1. [ ] SME gate session (backlog **R1**): review this ADR → ACCEPTED; rule the
       three open axes (context-graph escalation residency, `:AgentRun` target
       DB, LLM key strategy); close the 2026-07-03 IDEAS.md key question.
2. [ ] **R2** graph_qa app: Tier-0 router + Tier-1 text2cypher + envelope.
3. [ ] **R3** telemetry: JSONL ledger + `:AgentRun` + `console.agent-runs.v1`.
4. [ ] **R4** ephemeral session specs in `drydocs_api`.
5. [ ] **R5** Ask spoke in the console (streamed steps, Cypher panel, metrics).
6. [ ] **R6** Tier-2 bounded loop + task-scoped context graph + snapshots.
7. [ ] **R7** freshness fields + rescrape queue (code-enforce the registry).
8. [ ] **R8** evaluation metrics + promotion feed + cap tuning from the ledger.

---
¹ Analysis provenance: 2026-07-23 comparative session (three parallel repo
surveys → synthesis). Rendered dossier with both workflow diagrams:
https://claude.ai/code/artifact/47aac12b-5800-433c-8400-c883e4f7111c
(access-gated; the substance is restated above — the ADR stands alone).
