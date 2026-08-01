"""Jira handoff — the component's ONLY side-effect boundary (TDD Stage E, FR-REM-6).

Jira is the system of record for the support→dev handoff (SoD: we author + validate,
the owning application team deploys). Everything else in this package is pure
computation; the no-graph-write and Jira-only-output guards assert against THIS module,
so every external call stays inside :class:`JiraSubmitter` implementations.

- :func:`render_handoff` is PURE and deterministic: same package → same markdown, no
  I/O, no timestamps. Mechanism-only template; the real values (job names, owners,
  project keys) flow in via the package at runtime and are Internal by content.
- :class:`JiraSubmitter` is the wire boundary. The REST implementation is company-side
  configuration (credentials never live in the engine — PUBLISH-BOUNDARY.md); the
  producer ships only the interface + test fakes.
- Ownership is resolved by the caller (escalation-DB rule, company-side). Unresolvable
  ownership is ITSELF a defect — surfaced in the ticket, never guessed (Stage E).
- A handoff without a PASSING equivalence proof cannot be emitted (M0 Gate 5:
  "do not submit until equivalence is proven") — render a draft instead.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from .detect import Finding
from .equivalence import EquivalenceReport


@dataclass(frozen=True)
class JiraRef:
    """The emitted ticket reference (the component's durable output)."""

    key: str


@dataclass
class HandoffPackage:
    """Everything a dev-ready ticket carries (TDD Stage E)."""

    title: str
    findings: list[Finding]
    proof: EquivalenceReport
    greenfield_artifact: Path | None = None  # the authored definition artifact
    owner: str | None = None  # resolved owning team; None = defect
    scope: str = ""  # folder/job/DC coordinates (caller data)
    change_summary: str = ""  # BEFORE -> AFTER, caller-authored
    rollback: str = "Restore prior version via Control-M Changes History."
    acceptance: list[str] = field(default_factory=list)


class JiraSubmitter(ABC):
    """The wire boundary. Implementations live company-side (REST) or in tests (fakes)."""

    @abstractmethod
    def submit(self, title: str, body: str, attachments: list[Path]) -> JiraRef:
        """Create the ticket; return its reference."""


class UnprovenHandoffError(RuntimeError):
    """Raised when emitting a package whose equivalence proof is not passing."""


def render_handoff(package: HandoffPackage) -> str:
    """Render the ticket body — pure, deterministic, mechanism-only template."""
    lines: list[str] = []
    lines.append(f"Title: {package.title}")
    if package.owner:
        lines.append(f"Owner: {package.owner}")
    else:
        lines.append(
            "Owner: UNRESOLVED — ownership could not be resolved; this is itself a "
            "defect (surfaced, not guessed)"
        )
    lines.append("Requested by: Production Support (analysis pre-validated; implementation only)")
    lines.append("")
    lines.append("-- Findings " + "-" * 40)
    if package.findings:
        for f in package.findings:
            ratify = "ratified" if f.ratified else "UNRATIFIED (warn-only)"
            lines.append(f"[{f.rule_id}] {f.severity} · {ratify} · {f.target}: {f.message}")
    else:
        lines.append("(none recorded)")
    lines.append("")
    if package.scope:
        lines.append("-- Scope " + "-" * 43)
        lines.append(package.scope)
        lines.append("")
    if package.change_summary:
        lines.append("-- Change (BEFORE -> AFTER) " + "-" * 24)
        lines.append(package.change_summary)
        lines.append("")
    lines.append("-- Equivalence evidence " + "-" * 28)
    verdict = "PASS" if package.proof.equivalent else "NOT PROVEN"
    lines.append(f"Offline equivalence: {verdict} ({package.proof.compared_jobs} job(s) compared)")
    for d in package.proof.divergences:
        lines.append(f"divergence: {d}")
    lines.append("")
    if package.acceptance:
        lines.append("-- Acceptance criteria " + "-" * 29)
        lines.extend(f"[ ] {item}" for item in package.acceptance)
        lines.append("")
    lines.append("-- Rollback " + "-" * 40)
    lines.append(package.rollback)
    return "\n".join(lines) + "\n"


def emit_handoff(package: HandoffPackage, submitter: JiraSubmitter) -> JiraRef:
    """Open the handoff ticket. Refuses without a passing equivalence proof."""
    if not package.proof.equivalent:
        raise UnprovenHandoffError(
            "equivalence proof is not passing — render a draft, do not submit " "(M0 Gate 5 rule)"
        )
    body = render_handoff(package)
    attachments = [package.greenfield_artifact] if package.greenfield_artifact else []
    return submitter.submit(package.title, body, attachments)
