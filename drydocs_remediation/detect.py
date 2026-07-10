"""Failure-pattern / standards-finding detection (Gate 2 — validation).

Runs the machine-checkable rules against a loaded :class:`~drydocs_remediation.formats.
DefinitionSet`. The rule SOURCE is the R1–R29 registry
(``internal/remediation/standards-rules-registry.md``, Internal — never hardcode its
values here); each rule carries severity and ratification status. Detection may surface
findings for ANY rule, but ratification gates what downstream *transform* may act on.

Cadence note (0002-B §2 step 1): detection is failure-driven (small batches picked from
real failures), not cron.
"""
from __future__ import annotations

from dataclasses import dataclass

from .formats import DefinitionSet


@dataclass(frozen=True)
class Finding:
    """One rule hit on one definition object."""

    rule_id: str          # e.g. "R7" — key into the rules registry
    severity: str         # must-fix | should-fix | advisory (registry vocabulary)
    ratified: bool        # only ratified rules may drive greenfield changes
    target: str           # folder/job the finding is on (definition-set coordinates)
    message: str          # human-readable finding, mechanism-only


def detect_findings(definitions: DefinitionSet) -> list[Finding]:
    """Evaluate the rule set against ``definitions`` and return all findings."""
    raise NotImplementedError("M0 PoC slice — rules engine over the R-registry")
