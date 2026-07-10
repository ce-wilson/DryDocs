"""Legacy → greenfield definition transform (Gate 3 — generation).

Applies remediations for findings to produce the *greenfield* :class:`~drydocs_remediation.
formats.DefinitionSet`. HARD RULE (registry governance, recorded at the doc port): only
findings whose rule is ✅-ratified may change the definition; 🟡/❓ findings pass through
as WARN-only annotations. High-blast-radius actions (e.g. folder renames) are PROPOSED,
never auto-applied — per the registry's own greenfield columns.
"""
from __future__ import annotations

from .detect import Finding
from .formats import DefinitionSet


def propose_greenfield(
    definitions: DefinitionSet, findings: list[Finding]
) -> DefinitionSet:
    """Return the greenfield definition set for ``definitions`` given ``findings``."""
    raise NotImplementedError("M0 PoC slice — ratified-rule transforms only")
