""":AgentRun writer boundary (R3 / ADR 0007 telemetry contract, sink 2).

One :AgentRun node per answered question, mirroring the loader :JobRun
envelope (kind='qa' instead of kind='load') so agent telemetry is queryable
next to load telemetry. This module is the DEDICATED writer the R1 gate
ruling requires: the ONLY code path in the agent service that opens a WRITE
session, targeting the ruled database — ``ddcontext``, NEVER ``drydocs``
(refused here, not just documented; a revisit that moves telemetry to its
own dd* database is an ADR 0002 topology amendment, changed via env).

Privacy rules carried in the props, not the caller's discipline:

- question: sha256 + length ONLY (full text solely in the local JSONL
  ledger — agents/common/llm_ledger.py);
- caller identity: the RESERVED hashed slot — user_id sha256 + length,
  mirroring the question rule; ADK 2.0 run_async takes user_id per call and
  full identity never lands in the graph.
"""

from __future__ import annotations

import hashlib
import os

AGENT_RUN_DB_ENV = "DRYDOCS_AGENTRUN_DB"
DEFAULT_AGENT_RUN_DB = "ddcontext"  # R1 gate ruling 2026-07-23 (config/gate-log.md)

_MERGE_AGENT_RUN = (
    "MERGE (r:AgentRun {run_id: $run_id}) "
    "SET r += $props, r.recorded_at = datetime()"
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def agent_run_db() -> str:
    """The ruled target database; refuses ``drydocs`` no matter what the env says."""
    db = os.getenv(AGENT_RUN_DB_ENV, DEFAULT_AGENT_RUN_DB).strip() or DEFAULT_AGENT_RUN_DB
    if db == "drydocs":
        raise ValueError(
            ":AgentRun never lands in 'drydocs' (R1 gate ruling: ddcontext) — "
            f"fix {AGENT_RUN_DB_ENV}"
        )
    return db


def agent_run_props(envelope, user_id: str = "") -> dict:
    """Derive the flat :AgentRun property map from an answer envelope — pure,
    offline-testable. Everything the acceptance names, nothing free-text."""
    steps = envelope.steps
    executed = [s for s in steps if s.cypher and s.rows is not None]
    metrics = envelope.metrics
    props: dict = {
        "run_id": envelope.run_id,
        "kind": "qa",
        "session_id": envelope.session_id,
        "question_sha256": envelope.question_sha256,
        "question_chars": envelope.question_chars,
        "tier": envelope.tier,
        "model": envelope.model,
        "provider": envelope.provider,
        "iterations": metrics.iterations,
        "llm_calls": metrics.llm_calls,
        "tokens_prompt": metrics.tokens.prompt,
        "tokens_completion": metrics.tokens.completion,
        "tokens_total": metrics.tokens.total,
        "context_rows": metrics.context.get("rows", 0),
        "context_chunks": metrics.context.get("chunks", 0),
        "context_tokens_est": metrics.context.get("tokens_est", 0),
        "memory_events": metrics.memory.get("events", 0),
        "memory_tokens_est": metrics.memory.get("tokens_est", 0),
        "cypher_count": len(executed),
        "fix_retries": max((s.fix_retries for s in steps), default=0),
        "specs_used": sorted({s.spec_id for s in steps if s.kind == "spec" and s.spec_id}),
        "dbs_touched": sorted({s.database for s in executed if s.database}),
        "response_ms_total": metrics.response_ms.get("total", 0),
        "response_ms_routing": metrics.response_ms.get("routing", 0),
        "response_ms_retrieve": metrics.response_ms.get("retrieve", 0),
        "response_ms_llm": metrics.response_ms.get("llm", 0),
        # staleness flags: 0 until R7 fills SourceRecord.stale — an honest zero,
        # not a missing field, so the admin frame's column exists from day one.
        "stale_sources": sum(1 for src in envelope.sources if src.stale),
        "cost_est_usd": metrics.cost_est_usd,
        # reserved caller-identity slot (agent-runtime review, merged 2026-07-28):
        # the envelope's hashed slot wins when the pipeline already filled it.
        "user_id_sha256": getattr(envelope, "user_id_sha256", None)
        or (_sha256(user_id) if user_id else None),
        "user_id_chars": getattr(envelope, "user_id_chars", None)
        or (len(user_id) if user_id else None),
    }
    return props


def write_agent_run(envelope, user_id: str = "", database: str | None = None) -> None:
    """Write the :AgentRun node through a WRITE session on the ruled DB.

    Imports the shared driver lazily so this module stays importable (and
    ``agent_run_props`` testable) without the agents venv's live deps.
    """
    import neo4j

    from common.neo4j_tool import get_driver

    db = database or agent_run_db()
    if db == "drydocs":  # an explicit argument doesn't bypass the ruling either
        raise ValueError(":AgentRun never lands in 'drydocs' (R1 gate ruling: ddcontext)")
    props = agent_run_props(envelope, user_id=user_id)
    run_id = props.pop("run_id")
    props = {k: v for k, v in props.items() if v is not None}
    with get_driver().session(
        database=db, default_access_mode=neo4j.WRITE_ACCESS
    ) as session:
        session.execute_write(
            lambda tx: tx.run(_MERGE_AGENT_RUN, run_id=run_id, props=props).consume()
        )
