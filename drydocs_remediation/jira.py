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

G93 adds the RUN'S COUNTS. Before this, a finished batch reported findings with no
denominator: the reviewer could not tell whether the batch examined nine jobs or nine
hundred. :class:`RemediationCoverage` is recorded once, at batch time (by
:func:`run_remediation_batch`, wrapped in the shared ``batch_run_log`` context manager
G107 added — the fifth and last of the Idea-152 cadences), and carried on
``HandoffPackage.coverage`` as DATA. :func:`render_handoff` reads the recorded coverage;
it never re-derives a count from whatever findings survive filtering (the
extractors' ``ExtractCoverage.summary()`` pattern, ``drydocs_lineage/extractors/
controlm_inventory.py``, applied to this component's own accounting).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from drydocs_core.run_log import batch_run_log

from .detect import Finding
from .equivalence import EquivalenceReport
from .formats import DefinitionSet
from .transform import TransformResult


@dataclass(frozen=True)
class JiraRef:
    """The emitted ticket reference (the component's durable output)."""

    key: str


@dataclass
class RemediationCoverage:
    """Per-batch accounting for the Jira handoff (G93).

    Recorded ONCE, at batch time, from the objects and findings the run actually
    looked at — never recomputed from ``HandoffPackage.findings`` at render time,
    which may be a filtered subset. Mirrors the extractors' ``ExtractCoverage``
    shape: every count is a field, every skip is counted by reason, never dropped.

    ``findings_ratified`` / ``findings_unratified`` keep the WARN-only split visible
    on its own: a warn-only (unratified) finding must never read as a fix, so the
    ratified count is the only one that could ever back a "fixed" claim.
    """

    objects_examined: int = 0  # folders + jobs the run looked at
    objects_changed: int = 0  # definitions that differ, legacy vs greenfield
    findings_by_rule: dict[str, int] = field(default_factory=dict)
    findings_by_severity: dict[str, int] = field(default_factory=dict)
    findings_ratified: int = 0  # may back a "fixed" claim
    findings_unratified: int = 0  # WARN-only; must not inflate a fix count
    #: reason -> count. Nothing is skipped silently — an unratified Tier-1 rule
    #: lands here with its reason, the same house rule the extractors follow for
    #: unparseable rows.
    skipped: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def total_findings(self) -> int:
        return self.findings_ratified + self.findings_unratified

    def summary(self) -> str:
        return (
            f"objects: examined={self.objects_examined} changed={self.objects_changed} | "
            f"findings: {self.total_findings()} "
            f"(ratified={self.findings_ratified} unratified={self.findings_unratified}) "
            f"by rule={self.findings_by_rule} by severity={self.findings_by_severity} | "
            f"skipped={self.skipped}"
        )

    @classmethod
    def from_run(
        cls,
        definitions: DefinitionSet,
        findings: list[Finding],
        transform: TransformResult | None = None,
    ) -> RemediationCoverage:
        """Build the coverage from the artifacts a batch already produced.

        ``definitions`` is the legacy set the batch examined; ``transform`` (when a
        Tier-1 pass ran) supplies the greenfield set that ``objects_changed`` diffs
        against and the ``skipped_unratified`` rule ids that become the ``skipped``
        reason bucket — a governance skip is a skip, and it is counted, never
        dropped.
        """
        by_rule: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        ratified = 0
        unratified = 0
        for finding in findings:
            by_rule[finding.rule_id] = by_rule.get(finding.rule_id, 0) + 1
            by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
            if finding.ratified:
                ratified += 1
            else:
                unratified += 1
        skipped: dict[str, int] = {}
        objects_changed = 0
        if transform is not None:
            if transform.skipped_unratified:
                skipped["unratified (governance skip)"] = len(transform.skipped_unratified)
            objects_changed = _count_changed(definitions, transform.greenfield)
        return cls(
            objects_examined=len(definitions.folders) + len(definitions.jobs),
            objects_changed=objects_changed,
            findings_by_rule=by_rule,
            findings_by_severity=by_severity,
            findings_ratified=ratified,
            findings_unratified=unratified,
            skipped=skipped,
        )


def _count_changed(before: DefinitionSet, after: DefinitionSet) -> int:
    """Definitions whose value differs, ``before`` vs ``after``, paired by position
    (a Tier-1 rule preserves order — it maps each folder/job to its own rewrite)."""
    changed = 0
    for lf, gf in zip(before.folders, after.folders, strict=False):
        if lf != gf:
            changed += 1
    for lj, gj in zip(before.jobs, after.jobs, strict=False):
        if lj != gj:
            changed += 1
    return changed


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
    #: the run's recorded counts (G93). ``None`` means "assembled without a run
    #: summary" and renders as "not recorded" — a missing measurement must never
    #: read as a clean run.
    coverage: RemediationCoverage | None = None


class JiraSubmitter(ABC):
    """The wire boundary. Implementations live company-side (REST) or in tests (fakes)."""

    @abstractmethod
    def submit(self, title: str, body: str, attachments: list[Path]) -> JiraRef:
        """Create the ticket; return its reference."""


class UnprovenHandoffError(RuntimeError):
    """Raised when emitting a package whose equivalence proof is not passing."""


def _format_counts(counts: dict[str, int]) -> str:
    """``{"R1": 5, "R30": 3}`` -> ``"R1=5, R30=3"``, sorted for determinism."""
    if not counts:
        return "(none)"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


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
    lines.append("-- Coverage " + "-" * 40)
    # G93 (b): these numbers are RECORDED, not recomputed from `package.findings`
    # above -- which may be a filtered subset of what the run actually examined.
    if package.coverage is None:
        lines.append("not recorded")
    else:
        cov = package.coverage
        lines.append(f"Objects examined: {cov.objects_examined}")
        lines.append(f"Objects changed: {cov.objects_changed}")
        lines.append(
            f"Findings recorded: {cov.total_findings()} "
            f"(ratified={cov.findings_ratified}, unratified={cov.findings_unratified})"
        )
        lines.append(f"By rule: {_format_counts(cov.findings_by_rule)}")
        lines.append(f"By severity: {_format_counts(cov.findings_by_severity)}")
        lines.append(f"Skipped: {_format_counts(cov.skipped) if cov.skipped else '(none)'}")
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
    # three-valued verdict (defect B′): DIVERGED and NOT PROVEN are different
    # failures — one is evidence of breakage, the other is absence of evidence,
    # and the reviewer must see which they are looking at.
    if package.proof.equivalent:
        verdict = "PASS"
    elif package.proof.divergences:
        verdict = "DIVERGED"
    else:
        verdict = "NOT PROVEN"
    lines.append(
        f"Offline equivalence: {verdict} "
        f"({package.proof.proven_jobs}/{package.proof.compared_jobs} job(s) proven)"
    )
    for d in package.proof.divergences:
        lines.append(f"divergence: {d}")
    for np in package.proof.not_proven:
        lines.append(f"not proven: {np}")
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


def _assemble_handoff(
    definitions: DefinitionSet,
    findings: list[Finding],
    proof: EquivalenceReport,
    *,
    title: str,
    transform: TransformResult | None,
    greenfield_artifact: Path | None,
    owner: str | None,
    scope: str,
    change_summary: str,
    rollback: str,
    acceptance: list[str] | None,
) -> HandoffPackage:
    """The batch's real work: compute the run's coverage and package it. Kept
    apart from :func:`run_remediation_batch` the way ``lineage.writer`` keeps
    ``_write_curated`` apart from ``write_curated`` — the wrapper adds a record
    of the run, not behavior."""
    coverage = RemediationCoverage.from_run(definitions, findings, transform)
    return HandoffPackage(
        title=title,
        findings=findings,
        proof=proof,
        greenfield_artifact=greenfield_artifact,
        owner=owner,
        scope=scope,
        change_summary=change_summary,
        rollback=rollback,
        acceptance=acceptance or [],
        coverage=coverage,
    )


def run_remediation_batch(
    definitions: DefinitionSet,
    findings: list[Finding],
    proof: EquivalenceReport,
    *,
    title: str,
    transform: TransformResult | None = None,
    greenfield_artifact: Path | None = None,
    owner: str | None = None,
    scope: str = "",
    change_summary: str = "",
    rollback: str = "Restore prior version via Control-M Changes History.",
    acceptance: list[str] | None = None,
) -> HandoffPackage:
    """The remediation batch entry point (G93), wrapped in a run log.

    Detect, transform and prove already ran (their own units); this is the seam
    where the batch's counts are RECORDED — once, here — rather than left to be
    guessed at render time. Wrapped in ``batch_run_log`` (G107, the shared context
    manager every component batch now uses): it opens a run log, closes it on both
    the success and the failure path, re-raises the batch's own exception unchanged,
    and swallows an unwritable log directory so the log itself can never be the
    reason a batch fails.

    Returns the :class:`HandoffPackage` carrying the recorded
    :class:`RemediationCoverage` — :func:`render_handoff` reads it from there and
    never recomputes it from ``package.findings``.
    """
    with batch_run_log(
        "remediation.batch",
        target="jira",
        meta={"title": title},
    ) as summary:
        package = _assemble_handoff(
            definitions,
            findings,
            proof,
            title=title,
            transform=transform,
            greenfield_artifact=greenfield_artifact,
            owner=owner,
            scope=scope,
            change_summary=change_summary,
            rollback=rollback,
            acceptance=acceptance,
        )
        cov = package.coverage
        summary["objects examined"] = cov.objects_examined
        summary["objects changed"] = cov.objects_changed
        summary["findings recorded"] = cov.total_findings()
        summary["findings ratified"] = cov.findings_ratified
        summary["findings unratified"] = cov.findings_unratified
        summary["findings by rule"] = dict(cov.findings_by_rule)
        summary["findings by severity"] = dict(cov.findings_by_severity)
        summary["skipped"] = dict(cov.skipped)
        return package
