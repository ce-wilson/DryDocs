"""The lineage write boundary — curated lineage → the ``drydocs`` ground truth.

This is the ONLY module in the component that writes a database, and it writes only
:data:`drydocs_lineage.DATABASE`. It accepts exclusively rels whose curation status is
CONFIRMED — writing a proposed/rejected candidate is a contract violation, not a
warning. Write mechanics (the depgraph Fork-3 profile: constraint-on-key MERGE,
UNWIND batches) are the NEXT re-home slice; the four rel labels are gate-bound
vocabulary (``model.VOCAB_IDS``, all ``status: planned``) — no live load before the
HITL gate confirms them, per the standing edge-meaning rule.
"""
from __future__ import annotations

from .model import LineageGraph


def write_curated(graph: LineageGraph, confirmed: set[tuple[str, str, str]]) -> int:
    """Write the CONFIRMED subset of ``graph``'s rels (+ their endpoint nodes) to
    ground truth; returns the count written."""
    raise NotImplementedError(
        "Fork-3 write mechanics land in the next 0002-C slice; the rel vocabulary "
        "is gate-bound (planned) — no live load before the HITL gate"
    )
