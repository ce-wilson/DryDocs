"""Per-LLM-call JSONL ledger (R3 / ADR 0007 telemetry contract, sink 1).

KGoT's ``collect_stats`` pattern: every LLM call appends ONE line to a
day-file in ``DRYDOCS_LOGDIR`` (the drydocs_core.run_log log family — the
same configurable path, never the repo), and every answered question appends
one run-summary line. The run line is the ONLY place the full question text
lands — the :AgentRun graph node carries sha256 + length exclusively (the
question-text rule), so the local ledger is where an operator correlates a
hash back to the words.

The ledger also owns the model -> price map: ``cost_est_usd`` is computed
here from provider usage metadata (prices per MTok, Anthropic list prices as
of 2026-06; the company Azure models are deliberately absent — an unknown
model yields ``None``, never a guessed number). Writing is best-effort after
the first successful append — telemetry is an audit trail, never the reason
an answer fails.

Line shapes (both carry ``kind`` as the discriminator):

    {"kind": "llm_call", "ts", "run_id", "step", "iteration", "model",
     "provider", "prompt_tokens", "completion_tokens", "total_tokens",
     "cost_est_usd", "duration_ms"}
    {"kind": "run", "ts", "run_id", "session_id", "tier", "question",
     "question_sha256", "question_chars", "llm_calls", "tokens",
     "cost_est_usd", "response_ms", "iterations", "budget", "tier2",
     "answer", "context", "cypher_steps"}

R8 EXTENDS THE FULL-TEXT RULE FROM THE QUESTION TO THE TRIPLE, and that is a
ruling rather than a field addition, so it is written here beside the code that
acts on it and is handed back for confirmation.

The rule as R3 left it: full QUESTION text lives in this file and nowhere else;
the :AgentRun node carries sha256 + length. R8's evaluation clause needs the
question/context/answer TRIPLE to score anything at all, and a triple assembled
at answer time and thrown away cannot be scored on demand. So the run line now
also carries:

  * ``answer``       — the answer text as sent to the caller;
  * ``context``      — the retrieved-row COUNTS and the spec/step identities
                       that produced them, never the row VALUES;
  * ``cypher_steps`` — the Cypher each retrieval step actually ran, which is
                       also what the promotion feed ranks.

WHAT THIS DELIBERATELY DOES NOT DO. None of it reaches the :AgentRun node — the
graph side is unchanged, still sha256 + length, and agent_run_writer.py is not
touched. And ``context`` carries counts and identities, NOT retrieved values: a
retrieved row can hold folder names, host names and SEAL ids, and copying those
into a telemetry file would move real graph content into a log under a rule that
was written for a question a person typed. Counting rows answers "was the answer
grounded in something" without restating what that something was.

The judgement being handed back is whether the answer text itself belongs here.
It is the agent's own words rather than the graph's, and the file is already the
one place full text lands, so it is written here under that rule; but the rule
was ruled for a question, and extending it is not this build's call to make
silently. See the R8 close notes.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from drydocs_core.run_log import resolve_log_dir  # noqa: E402

LEDGER_BASENAME = "qa.graph_qa"

# USD per 1M tokens (input, output) — Anthropic list prices, cached 2026-06.
# Substring-matched against the provider-reported model id so date-suffixed
# and provider-prefixed ids ("anthropic/claude-sonnet-4-5-20250929") resolve.
PRICE_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-fable-5": (10.00, 50.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-opus-4-7": (5.00, 25.00),
    "claude-opus-4-6": (5.00, 25.00),
    "claude-opus-4-5": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}


def estimate_cost_usd(
    model: str | None, prompt_tokens: int, completion_tokens: int
) -> float | None:
    """Price one call, or None for a model not in the map (honest unknown)."""
    if not model:
        return None
    for key in sorted(PRICE_PER_MTOK, key=len, reverse=True):
        if key in model:
            in_rate, out_rate = PRICE_PER_MTOK[key]
            return round((prompt_tokens * in_rate + completion_tokens * out_rate) / 1_000_000, 6)
    return None


def _context_summary(envelope) -> dict:
    """What was retrieved, by SHAPE and never by VALUE.

    Counts and identities only. A retrieved row holds folder names, host names
    and SEAL ids; copying them into a telemetry file would move graph content
    into a log whose rule was written for a question a person typed. A grader
    asking "was this answer grounded in anything" is answered by the count; a
    grader asking "in WHAT" has to go back to the graph, which is the correct
    place to ask.
    """
    ctx = getattr(envelope.metrics, "context", {}) or {}
    return {
        "rows": ctx.get("rows", 0),
        "chunks": ctx.get("chunks", 0),
        "tokens_est": ctx.get("tokens_est", 0),
        "sources": len(getattr(envelope, "sources", []) or []),
        "steps": [
            {
                "i": s.i,
                "kind": s.kind,
                "spec_id": s.spec_id,
                "rows": s.rows,
                "truncated": s.truncated,
                "epistemic": s.epistemic,
            }
            for s in getattr(envelope, "steps", []) or []
        ],
    }


def _cypher_steps(envelope) -> list[dict]:
    """The Cypher each retrieval step actually ran.

    Kept SEPARATE from the context summary because it has a second consumer:
    the R8 promotion feed ranks recurring Tier-1 Cypher by frequency, and a
    query that only ever existed in an in-memory envelope cannot be counted
    across runs. Steps that ran no Cypher are omitted rather than recorded as
    nulls — a declared-answer run contributes nothing to a frequency ranking
    and should not look like it contributed an empty query.
    """
    return [
        {
            "i": s.i,
            "kind": s.kind,
            "spec_id": s.spec_id,
            "database": s.database,
            "cypher": s.cypher,
            "rows": s.rows,
            "fix_retries": s.fix_retries,
        }
        for s in getattr(envelope, "steps", []) or []
        if s.cypher
    ]


class LlmLedger:
    """Append-only JSONL day-file: ``qa.graph_qa.<YYYYmmdd>.jsonl`` in the
    run-log directory. Opened per append (two concurrent sessions on one
    machine interleave lines instead of clobbering a shared handle)."""

    def __init__(self, log_dir: Path | None = None) -> None:
        self._log_dir = log_dir

    def path(self) -> Path:
        log_dir = self._log_dir or resolve_log_dir()
        # G105: DERIVED from config/log-kinds.yaml rather than formatted here.
        # The `qa` kind declares rotation: per-day and format: jsonl, so this file
        # is CONFORMING under the one naming rule rather than the exception ADR
        # 0014 clause 3 originally called it. Falls back to the literal shape if
        # the declaration cannot be read -- telemetry never breaks an answer.
        try:
            from drydocs_core.log_kinds import log_filename

            return log_dir / log_filename("qa", "graph_qa")
        except Exception:
            stamp = datetime.now().strftime("%Y%m%d")
            return log_dir / f"{LEDGER_BASENAME}.{stamp}.jsonl"

    def _append(self, record: dict) -> None:
        try:
            path = self.path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, default=str) + "\n")
        except OSError:  # audit trail, never the reason an answer fails
            pass

    def call(
        self,
        run_id: str,
        step: str,
        model: str | None,
        provider: str | None,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: int,
        iteration: int = 1,
    ) -> float | None:
        """Record one LLM call; returns the cost estimate so the caller can
        accumulate it into the envelope's metrics."""
        cost = estimate_cost_usd(model, prompt_tokens, completion_tokens)
        self._append(
            {
                "kind": "llm_call",
                "ts": datetime.now(UTC).isoformat(timespec="seconds"),
                "run_id": run_id,
                "step": step,
                "iteration": iteration,
                "model": model,
                "provider": provider,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost_est_usd": cost,
                "duration_ms": duration_ms,
            }
        )
        return cost

    def run(self, envelope, question: str) -> None:
        """Record the per-question summary — full question text lives HERE
        and only here (the graph node carries sha256 + length).

        R8 adds the other two thirds of the evaluation triple. See the module
        docstring for what ``context`` carries and, more to the point, what it
        refuses to carry."""
        metrics = envelope.metrics
        self._append(
            {
                "kind": "run",
                "ts": datetime.now(UTC).isoformat(timespec="seconds"),
                "run_id": envelope.run_id,
                "session_id": envelope.session_id,
                "tier": envelope.tier,
                "question": question,
                "question_sha256": envelope.question_sha256,
                "question_chars": envelope.question_chars,
                "llm_calls": metrics.llm_calls,
                "tokens": {
                    "prompt": metrics.tokens.prompt,
                    "completion": metrics.tokens.completion,
                    "total": metrics.tokens.total,
                },
                "cost_est_usd": metrics.cost_est_usd,
                "response_ms": metrics.response_ms,
                # ── R8: the cap signals, so a bound can be tuned from what it
                # DID rather than from opinion. `iterations` is the Tier-2 loop
                # count; `exhausted` and `forced_solve` are the two signals R6
                # records precisely because a cap whose effect is invisible
                # cannot be tuned. They are pure metrics — no text, no values.
                "iterations": metrics.iterations,
                "budget": metrics.budget,
                "tier2": metrics.tier2,
                # ── R8: the evaluation triple ────────────────────────────────
                "answer": envelope.answer,
                "context": _context_summary(envelope),
                "cypher_steps": _cypher_steps(envelope),
            }
        )
