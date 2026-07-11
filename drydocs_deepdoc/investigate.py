"""On-demand deep dive — a failure names the job/folder; this derives context.

Analysis runs on the shared core parser (``drydocs_core.controlm``); every finding
carries an explicit reliability/trust stamp because NOTHING here is verified — that
verification happens later, at the HITL promotion gate, if ever.
"""
from __future__ import annotations

from dataclasses import dataclass

from drydocs_core.controlm import extract_container_command, parse_command  # noqa: F401  (the shared parser surface)


@dataclass(frozen=True)
class ContextFinding:
    """One uncertain finding, ready for the drydocs_context write."""

    subject_urn: str      # proxy-node business key (shared DryDocs URN)
    predicate: str        # the proposed relationship/observation, mechanism vocabulary
    object_urn: str       # proxy-node business key of the other end (or a literal ref)
    reliability: float    # 0.0–1.0 — derived confidence, never omitted
    trust: str            # SYNTHESIZED | GROUNDED (VERBATIM never originates here)
    evidence: str         # what the parser/analysis saw (mechanism-only text)


def investigate_failure(job_name: str, folder_name: str) -> list[ContextFinding]:
    """Deep-dive one failed job under its folder; return stamped findings."""
    raise NotImplementedError("on-failure trigger + analysis land after the scaffold (G4 notes)")
