"""Corpus-driven retrieval seeded from the grounded graph — THE CHARTER IS IN
:mod:`drydocs_deepdoc`, and this module does not restate it (G32 2026-08-18, MM1 2026-08-21).

Analysis runs on the shared core parser (``drydocs_core.orchestration.controlm``); every finding
carries an explicit reliability/trust stamp because NOTHING here is verified — that
verification happens later, at the HITL promotion gate, if ever.
"""

from __future__ import annotations

from dataclasses import dataclass

# The shared parser surface. NOT re-exported for "the on-failure analysis
# bodies" any more - that model retired at G32. It is the evidence for ADR 0002
# D2, "they share the command-line/lineage parser in drydocs-core": the charter
# calls the parser an INPUT to an investigation rather than a rival to it, and
# these names being the CORE objects is what makes that checkable. Pinned by
# tests/unit/test_lineage_deepdoc_scaffold.py::test_both_components_share_the_core_parser.
from drydocs_core.orchestration.controlm import (  # noqa: F401
    extract_container_command,
    parse_command,
)


@dataclass(frozen=True)
class ContextFinding:
    """One uncertain finding, ready for the :Uncertain-labeled write."""

    subject_urn: str  # proxy-node business key (shared DryDocs URN)
    predicate: str  # the proposed relationship/observation, mechanism vocabulary
    object_urn: str  # proxy-node business key of the other end (or a literal ref)
    reliability: float  # 0.0-1.0 — derived confidence, never omitted
    trust: str  # SYNTHESIZED | GROUNDED (VERBATIM never originates here)
    evidence: str  # what the parser/analysis saw (mechanism-only text)


def investigate_failure(job_name: str, folder_name: str) -> list[ContextFinding]:
    """Deep-dive one failed job under its folder; return stamped findings."""
    # ADR 0021 precedent 6: the scaffold NAMES which of its own bodies raise. Name only.
    raise NotImplementedError("on-failure trigger + analysis land after the scaffold (G4 notes)")
