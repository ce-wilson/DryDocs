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
     "cost_est_usd", "response_ms"}
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


class LlmLedger:
    """Append-only JSONL day-file: ``qa.graph_qa.<YYYYmmdd>.jsonl`` in the
    run-log directory. Opened per append (two concurrent sessions on one
    machine interleave lines instead of clobbering a shared handle)."""

    def __init__(self, log_dir: Path | None = None) -> None:
        self._log_dir = log_dir

    def path(self) -> Path:
        log_dir = self._log_dir or resolve_log_dir()
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
        and only here (the graph node carries sha256 + length)."""
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
            }
        )
