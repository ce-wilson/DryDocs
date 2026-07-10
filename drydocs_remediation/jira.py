"""Jira handoff emitter — the component's ONLY side-effect boundary (0002-B §3).

Jira is the system of record for the support→dev handoff: the ticket carries the
greenfield artifact and the equivalence report; the application dev team holds deploy
rights (separation of duties). Everything else in this package is pure computation —
the no-graph-write and Jira-only-output tests assert against THIS boundary, so keep
every external call inside this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .detect import Finding
from .equivalence import EquivalenceReport


@dataclass(frozen=True)
class JiraRef:
    """The emitted ticket reference (the component's durable output)."""

    key: str  # e.g. project ticket key returned by the Jira API


def emit_handoff(
    findings: list[Finding],
    greenfield_artifact: Path,
    proof: EquivalenceReport,
) -> JiraRef:
    """Open the handoff ticket; requires a PASSING equivalence proof."""
    raise NotImplementedError("M1 slice — Jira emitter behind this boundary")
