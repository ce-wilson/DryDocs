"""Offline equivalence proof — greenfield must re-derive legacy's resolved behavior.

The proof reuses ``drydocs_core.controlm`` resolution (``resolve_job`` and the command
parser) on BOTH sides so the comparison is apples-to-apples: parse legacy and greenfield,
resolve each job's variables/commands, and diff the *resolved* outputs — cosmetic
definition differences are fine, behavioral differences fail the proof. A greenfield
artifact is trusted (and may enter the Jira handoff) only with a passing report.

Corroboration context (0002-B §2 step 5, read-only): the legacy side must also reconcile
with the Oracle ``psgmgr`` extract and the loaded graph snapshot via ``drydocs_core``
adapters + ``Neo4jClient(database="drydocs")`` — this component never writes either.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .formats import DefinitionSet


@dataclass
class EquivalenceReport:
    """Outcome of the offline proof; attach to the Jira handoff."""

    equivalent: bool
    compared_jobs: int = 0
    divergences: list[str] = field(default_factory=list)  # resolved-behavior diffs, mechanism-only


def prove_equivalence(
    legacy: DefinitionSet, greenfield: DefinitionSet
) -> EquivalenceReport:
    """Prove ``greenfield`` re-derives ``legacy``'s resolved behavior."""
    raise NotImplementedError("M0 PoC slice — resolved-behavior diff via drydocs_core.controlm")
