"""Failure-pattern / standards-finding detection (Gate 2 — validation).

M0 scope: the ONE mechanized detector — **dot-smuggling** (a variable whose value is
pure punctuation, smuggled through Control-M's concatenation operator), rule id ``R1``
in the rules registry. Detection runs on the core classifier's ``value_is_delimiter``
feature so remediation and the loaders share one truth for the pattern.

The registry-driven rules ENGINE (R1-R29 from
``internal/remediation/standards-rules-registry.md``) is the M1 deliverable — per the
M0 scope doc, other standards are checked by hand in M0. Findings here are emitted
``ratified=False`` (WARN-only downstream) until the registry is machine-readable and
its per-rule ratification statuses drive this field; hardcoding those judgments in
public code would leak gate decisions.

Cadence note (0002-B §2 step 1): detection is failure-driven (small batches picked
from real failures), not cron.
"""

from __future__ import annotations

from dataclasses import dataclass

from drydocs_core.controlm import classify_job_variables

from .formats import DefinitionSet

#: The M0 detector: registry rule R1 ("No dot-smuggling").
DOT_SMUGGLING_RULE_ID = "R1"


@dataclass(frozen=True)
class Finding:
    """One rule hit on one definition object."""

    rule_id: str  # key into the rules registry (e.g. "R1")
    severity: str  # must-fix | should-fix | advisory (registry vocabulary)
    ratified: bool  # only ratified rules may drive greenfield changes
    target: str  # "<job>:<variable>" the finding is on
    message: str  # human-readable finding, mechanism-only


def detect_findings(definitions: DefinitionSet) -> list[Finding]:
    """Evaluate the M0 detector against every job in ``definitions``."""
    findings: list[Finding] = []
    for job in definitions.jobs:
        for cv in classify_job_variables(job.variables):
            if cv.value_is_delimiter:
                findings.append(
                    Finding(
                        rule_id=DOT_SMUGGLING_RULE_ID,
                        severity="should-fix",
                        ratified=False,  # registry ratification is gate territory (M1)
                        target=f"{job.name}:{cv.name}",
                        message=(
                            "variable value is pure punctuation smuggled through the "
                            "concatenation operator (dot-smuggling); resolve and inline "
                            "the literal instead"
                        ),
                    )
                )
    return findings
