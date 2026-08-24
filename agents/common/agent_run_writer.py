""":AgentRun writer boundary (R3 / ADR 0007 telemetry contract, sink 2).

One :AgentRun node per answered question, mirroring the loader :JobRun
envelope (kind='qa' instead of kind='load') so agent telemetry is queryable
next to load telemetry. This module is the DEDICATED writer the R1 gate
ruling requires: the ONLY code path in the agent service that opens a WRITE
session, targeting the ruled database — ``drydocs``, and nothing else
(refused here, not just documented: see ``agent_run_db`` below).

THE RULING INVERTED AT THE G102 FOLD (2026-08-18) and this docstring is the
correction. It read ``ddcontext``, NEVER ``drydocs`` — the pre-fold rule —
while ``DEFAULT_AGENT_RUN_DB`` twenty lines below already said ``drydocs``.
The defect to refuse is now a STALE env var still pointing at the retired
``ddcontext``, which would write telemetry into a database nothing reads.

Privacy rules carried in the props, not the caller's discipline:

- question: sha256 + length ONLY (full text solely in the local JSONL
  ledger — agents/common/llm_ledger.py);
- caller identity: the RESERVED hashed slot — user_id sha256 + length,
  mirroring the question rule; ADK 2.0 run_async takes user_id per call and
  full identity never lands in the graph.
"""

from __future__ import annotations

import hashlib
import json
import os

AGENT_RUN_DB_ENV = "DRYDOCS_AGENTRUN_DB"
DEFAULT_AGENT_RUN_DB = "drydocs"  # G102 (2026-08-18): the fold. The R1 ruling's SUBSTANCE (":AgentRun lands never-in-ground-truth") survives as the :Uncertain label per ADR 0011 §118 — this module is the second entry on the uncertain-writer allowlist

_MERGE_AGENT_RUN = (
    "MERGE (r:AgentRun:Uncertain {run_id: $run_id}) " "SET r += $props, r.recorded_at = datetime()"
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def agent_run_db() -> str:
    """The ruled target database; refuses anything else no matter what the env says.

    THE REFUSAL INVERTED AT G102 (2026-08-18). Pre-fold this function refused
    `drydocs` (the R1 ruling: :AgentRun never in ground truth). Post-fold the
    R1 substance survives as the :Uncertain label on the MERGE, and the ruled
    database IS `drydocs` — so the defect to refuse is now a STALE env var
    still pointing at the retired `ddcontext`, which would write telemetry
    into a database nothing reads.
    """
    db = os.getenv(AGENT_RUN_DB_ENV, DEFAULT_AGENT_RUN_DB).strip() or DEFAULT_AGENT_RUN_DB
    if db != DEFAULT_AGENT_RUN_DB:
        raise ValueError(
            f":AgentRun lands ONLY in '{DEFAULT_AGENT_RUN_DB}' carrying :Uncertain "
            f"(G102 fold; R1's never-in-ground-truth survives as the label) — "
            f"'{db}' is stale, fix {AGENT_RUN_DB_ENV}"
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
        # R21: the notifications Neo4j raised on any executed step, one JSON
        # string each (a Neo4j list property must be homogeneous) tagged with
        # the step index; and their count. A clean run carries [] and 0 — an
        # empty payload, never a missing field.
        "warnings": [
            json.dumps({"step": s.i, **n}, sort_keys=True, separators=(",", ":"))
            for s in steps
            for n in (getattr(s, "notifications", None) or [])
        ],
        "warning_count": sum(len(getattr(s, "notifications", None) or []) for s in steps),
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
    if db != DEFAULT_AGENT_RUN_DB:  # an explicit argument doesn't bypass the ruling either
        raise ValueError(
            f":AgentRun lands ONLY in '{DEFAULT_AGENT_RUN_DB}' (G102 fold; the "
            ":Uncertain label carries the R1 ruling) — got " + repr(db)
        )
    props = agent_run_props(envelope, user_id=user_id)
    run_id = props.pop("run_id")
    props = {k: v for k, v in props.items() if v is not None}
    with get_driver().session(database=db, default_access_mode=neo4j.WRITE_ACCESS) as session:
        session.execute_write(
            lambda tx: tx.run(_MERGE_AGENT_RUN, run_id=run_id, props=props).consume()
        )
