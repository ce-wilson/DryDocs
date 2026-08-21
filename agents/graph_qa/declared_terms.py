"""Tier 0 for DECLARED non-graph terms (R22, 2026-08-21).

A console term whose authority is an in-repo definition — Tower first
(``config/taxonomy/ui-concepts.yaml``) — is answered from that declaration,
with provenance, before the router or text2cypher can reach for a graph label
that merely shares a word. No Cypher runs, no LLM is called: the step records
the term, the source and the deterministic answer, and the envelope's tier is
``declared``. Only ``graph_binding: none`` rows short-circuit; once the HITL
gate binds a term to the graph, the graph path owns it again.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path

from graph_qa.envelope import Envelope, SourceRecord, StepRecord

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from drydocs_core.ui_concepts import answer_for, match  # noqa: E402


def answer_declared(
    envelope: Envelope,
    question: str,
    timings: dict,
    *,
    clock: Callable[[], float] = time.perf_counter,
    push: Callable[[StepRecord], None] | None = None,
) -> bool:
    """True when the question named a declared non-graph term and was answered
    from its declaration; the envelope is then complete (tier ``declared``)."""
    concept = match(question)
    if concept is None:
        return False
    started = clock()
    envelope.answer = answer_for(question, concept)
    envelope.tier = "declared"
    step = StepRecord(
        i=len(envelope.steps) + 1,
        kind="declared",
        spec_id=f"declared:{concept.term}",
        # no cypher on purpose: the whole point is that none runs
        cypher=None,
        database=None,
        rows=concept.cardinality,
        ms=int((clock() - started) * 1000),
    )
    if push is not None:
        push(step)
    else:
        envelope.steps.append(step)
    envelope.sources.append(SourceRecord(document=concept.provenance, trust="CONFIRMED"))
    envelope.metrics.context = {"rows": concept.cardinality, "chunks": 0, "tokens_est": 0}
    timings["routing"] += step.ms
    return True
