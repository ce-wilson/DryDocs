"""The deepdoc write boundary — stamped findings → ``ddcontext`` only.

This is the ONLY module in the component that writes a database, and it writes only
:data:`drydocs_deepdoc.DATABASE`. Every written node/edge carries ``reliability`` and
``trust`` (a finding without stamps is a contract violation). Proxy nodes are MERGEd
on the URN business key only — ground-truth properties are never copied across the
boundary. Promotion to ``drydocs`` is NOT this module's job (HITL gate + loader path).
"""
from __future__ import annotations

from .investigate import ContextFinding


def write_findings(findings: list[ContextFinding]) -> int:
    """Write stamped findings to the context graph; returns the count written."""
    raise NotImplementedError("write mechanics land with the on-failure wiring (G4 notes)")
