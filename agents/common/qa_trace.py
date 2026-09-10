"""The Ask decision trace — the `qa-debug` kind (R18, ADR 0007 §5 sink 4).

R3 built two sinks and R8 widened one of them, and between them they answer
"what did this run cost" and "what did it return". Neither answers **why**: the
router's reply is reduced to a `spec_id` and thrown away, the schema prompt
text2cypher was grounded on is never recorded, and the answer call's inputs
survive only as a row count. This module is the third question's sink.

TWO KINDS, TWO JOBS, and the split is the same one `api` / `api-debug` made:

- ``qa`` (llm_ledger.py) — the 90-day record. One line per LLM call, one per
  answered question, and its run line is the ONLY place a question hash turns
  back into the words a person typed. Lean on purpose.
- ``qa-debug`` (here) — the decision trace. Prompt and reply text, seven days,
  swept aggressively, and OFF unless the declaration says so. Burying the
  90-day record in prompt-sized debug noise would cost it the thing it exists
  for, which is exactly why api-debug is not `api` at DEBUG level.

ENABLEMENT IS SETTINGS-LEVEL, NEVER PER REQUEST, and the reason is inherited
rather than re-derived: an Ask question arrives as an HTTP request into the ADK
server, an HTTP request has no ``--verbose``, and a per-request flag would let
an untrusted caller turn on verbose capture of their own traffic. The gate is
the kind's own declared ``level: DEBUG`` in config/log-kinds.yaml — the same
line, read the same way, as ``drydocs_api.audit.ApiAuditLog``.

DEBUG ADDS A SINK AND CHANGES NOTHING ELSE. Same prompts, same temperature,
same call count, same answer whether this is on or off. A debug mode that
altered the pipeline would debug a pipeline nobody runs. The one thing R18 does
change — the router is now asked to state a reason — is changed in BOTH modes,
for that reason: see ``pipeline.ROUTER_SYSTEM``.

WHAT IT REFUSES TO CARRY. The answer call's user prompt IS the retrieved rows
JSON — folder names, host names, SEAL ids. R8 refused those values in the `qa`
ledger by explicit ruling, so the answer hop is recorded here as SHAPE (row
count, column keys, chars, truncation) and never as values; ``llm_shape`` is
the entry point that cannot carry them, and the pipeline calls it for that hop.
Caller identity is the same story one level down: nothing here takes a
``user_id``, only the envelope's already-hashed slot. Neither rule is a promise
in a comment: ``tests/unit/test_qa_trace.py`` MEASURES both, by planting a value
that exists in no prompt, schema or vocabulary — and a caller identity that
exists nowhere but the argument — and asserting neither reaches the file. That
is a behavioural check rather than a source scan on purpose; a scan would prove
this module contains no offending line, where what is worth proving is that no
path through it, or through the pipeline calling it, writes one.

Line shape (every record carries the correlation key and its ordinal):

    {"kind": "qa_trace", "ts", "run_id", "session_id", "seq", "hop", ...}

``hop`` is the discriminator: ``run_open`` | ``router`` | ``llm`` | ``step`` |
``run_close``. The reader is drydocs_api/qa_trace_read.py — deliberately on the
API side, because drydocs_api never imports the agents tree (a separate venv;
audit.py reimplements ``actor_hash`` for the same reason), and reading a
declared kind's day-files needs nothing from here.
"""

from __future__ import annotations

import itertools
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from drydocs_core.log_kinds import kind, log_filename
from drydocs_core.run_log import resolve_log_dir

TRACE_KIND = "qa-debug"
#: the free-form <name> segment, so qa.graph_qa.<day>.jsonl and
#: qa-debug.graph_qa.<day>.jsonl pair up in a directory listing.
TRACE_NAME = "graph_qa"

#: Prompt and reply text bound, stated here and in the kind's declared note.
#: The schema prompt is already capped at 12,000 chars by schema_context, so
#: this is headroom rather than a live constraint — a longer text is truncated
#: and FLAGGED, never dropped, because a silently shortened prompt is a
#: diagnostic that lies.
TRACE_TEXT_BOUND = 20_000

_LOGGER = logging.getLogger(__name__)

#: Process-wide ordinal. Records carry run_id AND seq, so concurrent sessions
#: interleave in one day-file and still read back in order per run.
_SEQ = itertools.count(1)


def _bounded(payload: dict, key: str, text: str | None) -> None:
    """Set ``key`` bounded, plus ``<key>_truncated`` — always both, so absent
    never has to be read as "short enough"."""
    if text is None:
        return
    payload[key] = text[:TRACE_TEXT_BOUND]
    payload[f"{key}_truncated"] = len(text) > TRACE_TEXT_BOUND


def _row_shape(rows) -> dict:
    """The answer call's input, by SHAPE. Column KEYS are schema; the values
    under them are the graph's content, and this function has no branch that
    can reach one."""
    rows = rows or []
    keys: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            for k in row:
                if k not in keys:
                    keys.append(str(k))
    return {"rows": len(rows), "columns": sorted(keys)}


class QaTrace:
    """Append-only JSONL writer for the ``qa-debug`` kind.

    Opened per append like the ledger and the API audit (concurrent turns
    interleave lines instead of clobbering a handle). ``log_dir`` /
    ``kinds_path`` are injectable for tests; the defaults are the resolved log
    root and the repo declaration. Disabled is the DEFAULT and the FALLBACK: an
    unreadable declaration disables the trace rather than guessing at it.
    """

    def __init__(self, log_dir: Path | None = None, kinds_path: Path | None = None) -> None:
        self._log_dir = log_dir
        self._kinds_path = kinds_path
        self._warned = False
        self._enabled = False
        try:
            self._enabled = kind(TRACE_KIND, kinds_path).level == "DEBUG"
        except Exception:
            _LOGGER.warning("qa-debug kind unreadable; the Ask trace stays off", exc_info=True)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def path(self) -> Path:
        log_dir = self._log_dir or resolve_log_dir()
        return log_dir / log_filename(TRACE_KIND, TRACE_NAME, path=self._kinds_path)

    # ── hops ─────────────────────────────────────────────────────────────────

    def run_open(self, run_id: str, session_id: str, question: str, normalized: str) -> None:
        """The question as typed and as the prompts will carry it (R19 appends
        the person's own clarifications to it). Both, because a trace that
        showed only the normalized form would hide the one transformation the
        pipeline performs on a question before routing it."""
        payload: dict = {}
        _bounded(payload, "question", question)
        _bounded(payload, "normalized_question", normalized)
        payload["question_chars"] = len(question)
        self.record("run_open", run_id, session_id, **payload)

    def router(
        self,
        run_id: str,
        session_id: str,
        *,
        candidates: list[str],
        spec_id: str | None,
        params: dict | None,
        rationale: str | None,
        parse_error: str | None = None,
    ) -> None:
        """The decision itself: what was on offer, what was chosen, why the
        model said it chose it, and — when the reply would not parse — that the
        fall-through to Tier 1 was noise rather than a judgement. The three
        runs in R18's notes are indistinguishable in today's telemetry
        precisely because ``candidates`` and ``rationale`` had nowhere to go."""
        self.record(
            "router",
            run_id,
            session_id,
            candidates=candidates,
            spec_id=spec_id,
            params=params or {},
            rationale=rationale,
            parse_error=parse_error,
        )

    def llm(
        self,
        run_id: str,
        session_id: str,
        *,
        step: str,
        system: str,
        user: str,
        reply: str,
        model: str | None,
        provider: str | None,
        prompt_tokens: int,
        completion_tokens: int,
        ms: int,
    ) -> None:
        """One LLM call WITH ITS TEXT. Legitimate for every hop whose inputs are
        repo-authored (the spec catalog, the schema/vocabulary prompt, a fix
        error) plus the question, which the `qa` ledger already stores in full.
        The answer hop is the exception and uses ``llm_shape`` instead."""
        payload: dict = {
            "step": step,
            "model": model,
            "provider": provider,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "ms": ms,
        }
        _bounded(payload, "system", system)
        _bounded(payload, "user", user)
        _bounded(payload, "reply", reply)
        self.record("llm", run_id, session_id, **payload)

    def llm_shape(
        self,
        run_id: str,
        session_id: str,
        *,
        step: str,
        system: str,
        rows,
        row_count: int,
        truncated: bool,
        user_chars: int,
        reply_chars: int,
        model: str | None,
        provider: str | None,
        prompt_tokens: int,
        completion_tokens: int,
        ms: int,
    ) -> None:
        """The answer hop, recorded as shape. ``system`` is repo-authored
        (``pipeline.ANSWER_SYSTEM``) and is kept in full; the user prompt is the
        rows JSON and is reduced to counts, column keys and sizes. The reply is
        the answer text, which the `qa` ledger already holds under R8 — it is
        sized here rather than copied, so the trace adds no second home for it."""
        payload: dict = {
            "step": step,
            "input": {**_row_shape(rows), "row_count": row_count, "truncated": truncated},
            "user_chars": user_chars,
            "reply_chars": reply_chars,
            "model": model,
            "provider": provider,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "ms": ms,
        }
        _bounded(payload, "system", system)
        self.record("llm", run_id, session_id, **payload)

    def step(self, run_id: str, session_id: str, step) -> None:
        """One StepRecord as it lands in the envelope — the generated Cypher,
        the validation/fix attempt that produced it, its error, its row count,
        Neo4j's notifications. These fields already exist and already ship to
        the console; recording them HERE is what puts them on the same ordered
        timeline as the prompts that caused them."""
        self.record(
            "step",
            run_id,
            session_id,
            i=getattr(step, "i", None),
            step_kind=getattr(step, "kind", None),
            spec_id=getattr(step, "spec_id", None),
            cypher=getattr(step, "cypher", None),
            database=getattr(step, "database", None),
            rows=getattr(step, "rows", None),
            truncated=getattr(step, "truncated", None),
            fix_retries=getattr(step, "fix_retries", None),
            error=getattr(step, "error", None),
            rationale=getattr(step, "rationale", None),
            notifications=list(getattr(step, "notifications", None) or []),
            ms=getattr(step, "ms", None),
        )

    def run_close(self, envelope) -> None:
        """The closing record: what tier answered, what it cost, how long it
        took — and caller identity ONLY as the envelope's already-hashed slot.
        Nothing in this module takes a raw ``user_id``; the hash is the only
        shape available to it."""
        metrics = envelope.metrics
        self.record(
            "run_close",
            envelope.run_id,
            envelope.session_id,
            tier=envelope.tier,
            question_sha256=envelope.question_sha256,
            user_id_sha256=getattr(envelope, "user_id_sha256", None),
            model=envelope.model,
            provider=envelope.provider,
            answer_chars=len(envelope.answer or ""),
            llm_calls=metrics.llm_calls,
            iterations=metrics.iterations,
            tokens=metrics.tokens.total,
            cost_est_usd=metrics.cost_est_usd,
            response_ms=metrics.response_ms,
            context=metrics.context,
            budget=metrics.budget,
            tier2=metrics.tier2,
            steps=len(envelope.steps),
        )

    # ── mechanics ────────────────────────────────────────────────────────────

    def record(self, hop: str, run_id: str, session_id: str, **fields) -> None:
        """Append one correlated line, or do nothing at all when the trace is
        off. Best-effort after the G105 idiom: a diagnostic is never the reason
        an answer fails, and a permanently broken sink warns once rather than
        passing silently forever."""
        if not self._enabled:
            return
        line = {
            "kind": "qa_trace",
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "run_id": run_id,
            "session_id": session_id,
            "seq": next(_SEQ),
            "hop": hop,
            **fields,
        }
        try:
            path = self.path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(line, default=str) + "\n")
        except Exception:
            if not self._warned:
                self._warned = True
                _LOGGER.warning("qa trace write failed; answers continue", exc_info=True)
