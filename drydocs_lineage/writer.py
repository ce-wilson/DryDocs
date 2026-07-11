"""The lineage write boundary — curated lineage → the ``drydocs`` ground truth.

This is the ONLY module in the component that writes a database, and it writes only
:data:`drydocs_lineage.DATABASE`. It accepts exclusively CONFIRMED candidates —
writing a proposed/rejected candidate is a contract violation, not a warning.
Write mechanics (cypher, loader pattern, provenance envelope) land with the
depgraph re-home; the acceptance gate then mirrors the load-side conventions
(WAS_GENERATED_BY delta-only, row checksums).
"""
from __future__ import annotations

from .extract import LineageCandidate


def write_curated(candidates: list[LineageCandidate]) -> int:
    """Write CONFIRMED candidates to ground truth; returns the count written."""
    raise NotImplementedError("write mechanics land with the depgraph re-home (G9/0002-C)")
