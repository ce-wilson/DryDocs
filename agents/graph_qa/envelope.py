"""The response envelope — the contract the Ask spoke renders (ADR 0007 §5).

Every answer returns one envelope: the answer text, the per-step Cypher
record (what ran, where, how long, how many repairs), the sources, and the
metrics block (tokens / context size / memory size / timing). Question text
appears as sha256 + length only — full text belongs to the local ledger
(R3), never a payload that could be persisted in-graph.

Field shapes are documented in agents/graph_qa/README.md; changing them is a
contract change for the UI (R5) and the telemetry sinks (R3) — bump
deliberately, not incidentally.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def est_tokens(text: str) -> int:
    """Cheap, provider-neutral token estimate (~4 chars/token); labeled *_est everywhere."""
    return max(1, len(text) // 4) if text else 0


@dataclass
class StepRecord:
    i: int
    kind: str  # 'router' | 'spec' | 'text2cypher' | 'answer'
    ms: int = 0
    spec_id: str | None = None
    cypher: str | None = None
    database: str | None = None
    rows: int | None = None
    truncated: bool = False
    fix_retries: int = 0
    error: str | None = None
    # R4 ephemeral session spec ref (eph.<hash>) for /specs/{ref}/run|export;
    # None when the registration surface isn't configured (pre-R5 wiring).
    explore_ref: str | None = None


@dataclass
class SourceRecord:
    document: str
    trust: str  # 'CONFIRMED' | 'SYNTHESIZED' (watermarked DBs)
    fetched_at: str | None = None  # R7 freshness fields; None until then
    stale: bool | None = None


@dataclass
class TokenMetrics:
    prompt: int = 0
    completion: int = 0
    total: int = 0


@dataclass
class Metrics:
    iterations: int = 0
    llm_calls: int = 0
    tokens: TokenMetrics = field(default_factory=TokenMetrics)
    context: dict = field(default_factory=lambda: {"rows": 0, "chunks": 0, "tokens_est": 0})
    memory: dict = field(default_factory=lambda: {"events": 0, "tokens_est": 0})
    cost_est_usd: float | None = None  # priced in R3 (ledger owns the model->price map)
    response_ms: dict = field(
        default_factory=lambda: {"total": 0, "routing": 0, "retrieve": 0, "llm": 0}
    )


@dataclass
class Envelope:
    run_id: str
    session_id: str
    tier: str  # 'spec' | 'text2cypher' | 'unanswered'
    question_sha256: str
    question_chars: int
    answer: str
    model: str | None = None
    provider: str | None = None
    # R3 reserved caller-identity slot: sha256 + length ONLY (mirrors the
    # question-text rule; ADK 2.0 run_async takes user_id per call). Full
    # identity never lands in a payload or the graph.
    user_id_sha256: str | None = None
    user_id_chars: int | None = None
    steps: list[StepRecord] = field(default_factory=list)
    sources: list[SourceRecord] = field(default_factory=list)
    metrics: Metrics = field(default_factory=Metrics)

    def to_dict(self) -> dict:
        return asdict(self)
