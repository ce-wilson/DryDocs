"""The tiered answer pipeline (ADR 0007 decision 1) — pure orchestration.

Tier 0: the router matches the question onto a registered QuerySpec; the
spec's Cypher runs VERBATIM (deterministic, provenance-clean). Tier 1:
schema-grounded text2cypher with the fix loop (<= MAX_FIX_RETRIES) — the
read-only guard is a pre-flight, READ access mode in the executor is the
boundary. Tier 2 (the bounded enhance/solve loop) is R6, not here: when
Tier 1 cannot answer, the envelope says so honestly (tier='unanswered').

Everything is dependency-injected (provider, executor, schema sources,
clock) so the poetry unit suite tests the full control flow with fakes —
no litellm, no driver, no ADK.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable

from common import specs_catalog
from common.specs_catalog import ensure_read_only

from graph_qa.envelope import (
    Envelope,
    Metrics,
    SourceRecord,
    StepRecord,
    est_tokens,
    sha256_text,
)
from graph_qa.schema_context import build_schema_prompt, load_vocabulary

MAX_FIX_RETRIES = 2  # R2 acceptance: fix loop capped at 2
ROW_CAP = 100
ANSWER_CONTEXT_CHARS = 6_000  # rows JSON offered to the answer call, bounded

ROUTER_SYSTEM = (
    "You route a user question about the DryDocs knowledge graph onto ONE "
    "registered query spec, or none. Only pick a spec that clearly answers "
    "the question; never force a fit. Use only params the spec declares.\n"
    'Reply with JSON only: {"spec_id": "<id>" | null, "params": {}}'
)

TEXT2CYPHER_USER = (
    "Question: {question}\n\n"
    "Write ONE read-only Cypher query that answers it. Rules: no write "
    "clauses or write procedures of any kind; alias every returned value; "
    "add LIMIT {row_cap} unless the query aggregates to a few rows. The "
    "property keys list is graph-wide, not per-label — when an example query "
    "reads a property off a label, prefer the example's property over a "
    "plausible-sounding one.\n"
    'Reply with JSON only: {{"cypher": "..."}}'
)

FIX_USER = (
    "The previous Cypher failed.\n\nQuery:\n{cypher}\n\nError:\n{error}\n\n"
    "Return a corrected READ-ONLY query answering the original question: "
    "{question}\n"
    'Reply with JSON only: {{"cypher": "..."}}'
)

ANSWER_SYSTEM = (
    "You answer questions about the DryDocs knowledge graph from query "
    "results ONLY. Be concise and concrete; cite counts and names from the "
    "rows. If the rows cannot answer the question, say exactly what is "
    "missing — never invent data."
)


def _extract_json(text: str) -> dict:
    """Defensive JSON extraction — models wrap JSON in prose/fences often enough."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object in model reply: {text[:200]!r}")
    return json.loads(match.group(0))


class GraphQaPipeline:
    def __init__(
        self,
        provider,
        run_read: Callable,
        graph_schema: Callable[[], dict],
        default_db: str = "drydocs",
        clock: Callable[[], float] = time.perf_counter,
        vocabulary_loader: Callable[[], list[dict]] = load_vocabulary,
        register_cypher: Callable | None = None,
        ledger=None,
        on_step: Callable | None = None,
    ) -> None:
        self.provider = provider
        self.run_read = run_read
        self.graph_schema = graph_schema
        self.default_db = default_db
        self.clock = clock
        self.vocabulary_loader = vocabulary_loader
        # R4: registers executed Cypher as an ephemeral session spec and
        # returns the explore_ref (agents/common/ephemeral_client.make_register).
        # None = registration surface not configured; explore_ref stays null.
        self.register_cypher = register_cypher
        # R3: per-LLM-call JSONL ledger (agents/common/llm_ledger.LlmLedger).
        # Duck-typed: .call(...) records one line and returns the cost estimate.
        # None = no ledger; cost_est_usd stays None (the ledger owns the price map).
        self.ledger = ledger
        # R5: step observer — called with each StepRecord the moment it lands
        # in the envelope, so the ADK wrapper can stream steps to the Ask
        # spoke while the answer is still being produced. Observer failures
        # never affect the answer.
        self.on_step = on_step

    def _push_step(self, envelope: Envelope, step: StepRecord) -> None:
        envelope.steps.append(step)
        if self.on_step is not None:
            try:
                self.on_step(step)
            except Exception:
                pass

    def _explore_ref(self, cypher: str, database: str, params: dict) -> str | None:
        """Register one EXECUTED query; a registration failure never kills an
        answer — the step just carries no explore_ref (honest degradation)."""
        if self.register_cypher is None:
            return None
        try:
            return self.register_cypher(cypher=cypher, database=database, params=params)
        except Exception:
            return None

    # -- envelope bookkeeping -------------------------------------------------
    def _llm(
        self, envelope: Envelope, system: str, user: str, timings: dict,
        step: str = "llm",
    ) -> str:
        reply = self.provider.complete(system, user)
        envelope.metrics.llm_calls += 1
        envelope.metrics.tokens.prompt += reply.usage.prompt_tokens
        envelope.metrics.tokens.completion += reply.usage.completion_tokens
        envelope.metrics.tokens.total += reply.usage.total_tokens
        envelope.model = reply.model
        timings["llm"] += reply.ms
        if self.ledger is not None:
            try:  # telemetry is best-effort — never the reason an answer fails
                cost = self.ledger.call(
                    run_id=envelope.run_id,
                    step=step,
                    model=reply.model,
                    provider=getattr(self.provider, "provider", None),
                    prompt_tokens=reply.usage.prompt_tokens,
                    completion_tokens=reply.usage.completion_tokens,
                    duration_ms=reply.ms,
                    iteration=max(envelope.metrics.iterations, 1),
                )
                if cost is not None:
                    envelope.metrics.cost_est_usd = (
                        envelope.metrics.cost_est_usd or 0.0
                    ) + cost
            except Exception:
                pass
        return reply.text

    # -- tiers ----------------------------------------------------------------
    def _route(self, envelope: Envelope, question: str, timings: dict) -> tuple:
        started = self.clock()
        catalog = "\n".join(specs_catalog.catalog_lines())
        raw = self._llm(
            envelope, ROUTER_SYSTEM, f"Specs:\n{catalog}\n\nQuestion: {question}", timings,
            step="router",
        )
        spec_id, params = None, {}
        try:
            decision = _extract_json(raw)
            spec_id = decision.get("spec_id") or None
            params = decision.get("params") or {}
        except (ValueError, json.JSONDecodeError):
            spec_id = None  # router noise never kills the question — fall through to Tier 1
        timings["routing"] += int((self.clock() - started) * 1000)
        self._push_step(
            envelope,
            StepRecord(i=len(envelope.steps) + 1, kind="router", spec_id=spec_id,
                       ms=timings["routing"]),
        )
        return spec_id, params

    def _run_spec(self, envelope: Envelope, spec_id: str, params: dict, timings: dict):
        spec = specs_catalog.get_spec(spec_id)
        if spec is None:
            return None  # router hallucinated an id — Tier 1 takes over
        try:
            resolved = specs_catalog.resolve_params(spec, params)
        except ValueError:
            resolved = specs_catalog.resolve_params(spec, {})  # defaults over router noise
        started = self.clock()
        step = StepRecord(
            i=len(envelope.steps) + 1, kind="spec", spec_id=spec.id,
            cypher=spec.cypher, database=spec.database,
        )
        try:
            result = self.run_read(
                spec.cypher, params=resolved, database=spec.database, row_cap=ROW_CAP
            )
        except Exception as exc:  # a registered spec failing is exceptional — record, fall through
            step.error = str(exc)
            step.ms = int((self.clock() - started) * 1000)
            self._push_step(envelope, step)
            return None
        step.rows, step.truncated, step.ms = result.row_count, result.truncated, result.ms
        step.explore_ref = self._explore_ref(spec.cypher, spec.database, resolved)
        self._push_step(envelope, step)
        timings["retrieve"] += step.ms
        trust = "SYNTHESIZED" if spec.database in specs_catalog.WATERMARKED_DATABASES else "CONFIRMED"
        envelope.sources.append(SourceRecord(document=f"spec:{spec.id}", trust=trust))
        return result

    def _run_text2cypher(self, envelope: Envelope, question: str, timings: dict):
        schema_prompt = build_schema_prompt(
            self.vocabulary_loader(),
            self.graph_schema(),
            [(s.id, s.description, s.cypher) for s in specs_catalog.QUERY_SPECS.values()],
        )
        raw = self._llm(
            envelope, schema_prompt,
            TEXT2CYPHER_USER.format(question=question, row_cap=ROW_CAP), timings,
            step="text2cypher",
        )
        cypher = None
        for attempt in range(MAX_FIX_RETRIES + 1):
            step = StepRecord(
                i=len(envelope.steps) + 1, kind="text2cypher",
                database=self.default_db, fix_retries=attempt,
            )
            try:
                cypher = _extract_json(raw).get("cypher", "").strip()
                step.cypher = cypher
                if not cypher:
                    raise ValueError("model returned empty cypher")
                ensure_read_only(cypher)  # pre-flight; READ mode in run_read is the boundary
                result = self.run_read(cypher, database=self.default_db, row_cap=ROW_CAP)
                step.rows, step.truncated, step.ms = (
                    result.row_count, result.truncated, result.ms,
                )
                step.explore_ref = self._explore_ref(cypher, self.default_db, {})
                self._push_step(envelope, step)
                timings["retrieve"] += step.ms
                envelope.sources.append(
                    SourceRecord(document=f"text2cypher:{self.default_db}", trust="CONFIRMED")
                )
                return result
            except Exception as exc:  # WriteRejected, JSON/parse noise, CypherReadError alike
                step.error = str(exc)
                self._push_step(envelope, step)
                if attempt == MAX_FIX_RETRIES:
                    return None
                raw = self._llm(
                    envelope, schema_prompt,
                    FIX_USER.format(cypher=cypher or raw[:500], error=exc, question=question),
                    timings, step="fix",
                )
        return None

    # -- entry point ----------------------------------------------------------
    def answer(
        self,
        question: str,
        run_id: str,
        session_id: str = "",
        memory_events: int = 0,
        memory_chars: int = 0,
        user_id: str = "",
    ) -> Envelope:
        total_started = self.clock()
        timings = {"routing": 0, "retrieve": 0, "llm": 0}
        envelope = Envelope(
            run_id=run_id,
            session_id=session_id,
            tier="unanswered",
            question_sha256=sha256_text(question),
            question_chars=len(question),
            answer="",
            provider=getattr(self.provider, "provider", None),
            metrics=Metrics(),
        )
        envelope.metrics.memory = {
            "events": memory_events,
            "tokens_est": memory_chars // 4,
        }
        if user_id:  # R3 reserved slot: hash + length only, never the identity
            envelope.user_id_sha256 = sha256_text(user_id)
            envelope.user_id_chars = len(user_id)

        spec_id, params = self._route(envelope, question, timings)
        result = self._run_spec(envelope, spec_id, params, timings) if spec_id else None
        if result is not None:
            envelope.tier = "spec"
        if result is None or result.row_count == 0:
            # Zero rows from a routed spec is "insufficient context" (ADR 0007
            # tiering) — a mis-routed or not-yet-loaded spec must not become an
            # empty answer when text2cypher can ground one. The spec step stays
            # in the envelope either way; tier reports what actually answered.
            t2c_result = self._run_text2cypher(envelope, question, timings)
            if t2c_result is not None and (result is None or t2c_result.row_count > 0):
                result = t2c_result
                envelope.tier = "text2cypher"

        if result is not None:
            rows_json = json.dumps(result.records, default=str)[:ANSWER_CONTEXT_CHARS]
            envelope.metrics.context = {
                "rows": result.row_count,
                "chunks": 0,  # doc-chunk retrieval arrives with R7 corpora wiring
                "tokens_est": est_tokens(rows_json),
            }
            envelope.answer = self._llm(
                envelope, ANSWER_SYSTEM,
                f"Question: {question}\n\nRows ({result.row_count}"
                f"{', truncated' if result.truncated else ''}):\n{rows_json}",
                timings, step="answer",
            )
            self._push_step(
                envelope,
                StepRecord(i=len(envelope.steps) + 1, kind="answer", ms=timings["llm"]),
            )
        else:
            envelope.answer = (
                "I could not produce a valid read-only query for this question. "
                "The attempted Cypher and errors are in the steps — try rephrasing, "
                "or run one of the registered explorer views."
            )

        envelope.metrics.iterations = 1  # Tier-2 (R6) will count real loop iterations
        envelope.metrics.response_ms = {
            "total": int((self.clock() - total_started) * 1000),
            **timings,
        }
        return envelope
