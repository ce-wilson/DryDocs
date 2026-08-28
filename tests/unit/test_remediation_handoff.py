"""Jira handoff boundary (TDD Stage E, FR-REM-6): deterministic render, the
Jira-only side-effect boundary, ownership surfaced-not-guessed, and the
no-unproven-submit rule."""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_remediation.detect import Finding
from drydocs_remediation.equivalence import EquivalenceReport
from drydocs_remediation.formats import DefinitionSet, JobDefinition
from drydocs_remediation.jira import (
    HandoffPackage,
    JiraRef,
    JiraSubmitter,
    RemediationCoverage,
    UnprovenHandoffError,
    emit_handoff,
    render_handoff,
    run_remediation_batch,
)


class RecordingSubmitter(JiraSubmitter):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, list[Path]]] = []

    def submit(self, title: str, body: str, attachments: list[Path]) -> JiraRef:
        self.calls.append((title, body, attachments))
        return JiraRef(key="SYN-100")


def _package(equivalent: bool = True, owner: str | None = "Synthetic Dev Team"):
    return HandoffPackage(
        title="[Remediation] JOB0001_SAMPLE_FW - remove dot-smuggling",
        findings=[
            Finding(
                rule_id="R1",
                severity="should-fix",
                ratified=False,
                target="JOB0001_SAMPLE_FW:SUFX",
                message="dot-smuggling",
            )
        ],
        proof=EquivalenceReport(equivalent=equivalent, compared_jobs=1, proven_jobs=1),
        greenfield_artifact=Path("greenfield-sample.yaml"),
        owner=owner,
        scope="Folder: FOLDER-SYNTH-SAMPLE-DLY  Job: JOB0001_SAMPLE_FW",
        acceptance=["Greenfield resolves to the baseline filename"],
    )


def test_render_is_pure_and_deterministic() -> None:
    pkg = _package()
    body1, body2 = render_handoff(pkg), render_handoff(pkg)
    assert body1 == body2
    assert "[R1] should-fix" in body1
    assert "UNRATIFIED (warn-only)" in body1
    assert "Offline equivalence: PASS (1/1 job(s) proven)" in body1
    assert "[ ] Greenfield resolves to the baseline filename" in body1


def test_unresolved_ownership_is_surfaced_not_guessed() -> None:
    body = render_handoff(_package(owner=None))
    assert "Owner: UNRESOLVED" in body
    assert "defect" in body


def test_emit_goes_only_through_the_submitter_boundary() -> None:
    submitter = RecordingSubmitter()
    ref = emit_handoff(_package(), submitter)
    assert ref == JiraRef(key="SYN-100")
    assert len(submitter.calls) == 1
    title, body, attachments = submitter.calls[0]
    assert title.startswith("[Remediation]")
    assert body == render_handoff(_package())
    assert attachments == [Path("greenfield-sample.yaml")]


def test_emit_refuses_an_unproven_package() -> None:
    submitter = RecordingSubmitter()
    with pytest.raises(UnprovenHandoffError):
        emit_handoff(_package(equivalent=False), submitter)
    assert submitter.calls == []  # nothing crossed the boundary


# --------------------------------------------------------------------------
# G93 — the run's counts ride the run log, not the console.
# --------------------------------------------------------------------------


@pytest.fixture
def logdir(tmp_path, monkeypatch):
    """Hermetic log directory (run_remediation_batch opens a real run log)."""
    d = tmp_path / "logs"
    d.mkdir()
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(d))
    return d


def test_coverage_absent_reads_not_recorded_not_omitted() -> None:
    """(d) A package assembled WITHOUT a run summary renders the section as
    "not recorded" -- a missing measurement must never read as a clean run."""
    body = render_handoff(_package())
    assert "-- Coverage " in body
    assert "not recorded" in body


def test_recorded_numbers_survive_a_filtered_findings_list() -> None:
    """(b) NUMBERS ARE RECORDED, NOT RECOMPUTED AT RENDER TIME. The coverage was
    recorded against the FULL run (12 findings); the package below hands the
    renderer only 2 of them (e.g. the caller filtered to must-fix for display).
    The rendered Coverage section must still report the recorded 12 -- a
    denominator silently re-derived from `len(package.findings)` would report 2.
    """
    coverage = RemediationCoverage(
        objects_examined=9,
        objects_changed=3,
        findings_by_rule={"R1": 5, "R30": 3, "R41": 4},
        findings_by_severity={"must-fix": 4, "should-fix": 6, "advisory": 2},
        findings_ratified=0,
        findings_unratified=12,
        skipped={"unratified (governance skip)": 2},
    )
    subset = [
        Finding(rule_id="R30", severity="must-fix", ratified=False, target="a", message="m"),
        Finding(rule_id="R30", severity="must-fix", ratified=False, target="b", message="m"),
    ]
    pkg = HandoffPackage(
        title="[Remediation] synthetic batch",
        findings=subset,  # a SUBSET of what the run examined
        proof=EquivalenceReport(equivalent=True, compared_jobs=1, proven_jobs=1),
        coverage=coverage,
    )

    body = render_handoff(pkg)

    assert len(pkg.findings) == 2, "the fixture must actually be a subset"
    assert "Findings recorded: 12 (ratified=0, unratified=12)" in body
    assert "Objects examined: 9" in body
    assert "Objects changed: 3" in body
    assert "R1=5" in body and "R30=3" in body and "R41=4" in body
    assert "must-fix=4" in body and "should-fix=6" in body and "advisory=2" in body
    assert "unratified (governance skip)=2" in body


def test_coverage_minimum_content_ratified_split_never_inflates_fix_count() -> None:
    """(c) The ratified/unratified split: a warn-only finding must not inflate a
    fix count."""
    coverage = RemediationCoverage(
        objects_examined=1,
        findings_by_rule={"R1": 1},
        findings_by_severity={"should-fix": 1},
        findings_ratified=0,
        findings_unratified=1,
    )
    pkg = HandoffPackage(
        title="t",
        findings=[
            Finding(rule_id="R1", severity="should-fix", ratified=False, target="x", message="m")
        ],
        proof=EquivalenceReport(equivalent=True, compared_jobs=0, proven_jobs=0),
        coverage=coverage,
    )
    body = render_handoff(pkg)
    assert "ratified=0, unratified=1" in body


def test_coverage_does_not_restate_the_equivalence_proof() -> None:
    """(e) Coverage counts what the run LOOKED AT; the proof states what it
    DEMONSTRATED. The two denominators legitimately differ (nine objects
    examined, one job pair proven) and the Coverage section must not repeat or
    fold in the PASS/DIVERGED/NOT PROVEN verdict or its job counts."""
    coverage = RemediationCoverage(objects_examined=9, findings_unratified=1)
    pkg = HandoffPackage(
        title="t",
        findings=[
            Finding(rule_id="R1", severity="should-fix", ratified=False, target="x", message="m")
        ],
        proof=EquivalenceReport(equivalent=True, compared_jobs=1, proven_jobs=1),
        coverage=coverage,
    )
    body = render_handoff(pkg)
    coverage_section, _, rest = body.partition("-- Equivalence evidence")
    assert "Objects examined: 9" in coverage_section
    assert "PASS" not in coverage_section
    assert "proven" not in coverage_section
    assert "Offline equivalence: PASS (1/1 job(s) proven)" in rest


def test_run_remediation_batch_is_the_batch_entry_point(logdir) -> None:
    """The batch entry point assembles a HandoffPackage whose coverage matches
    what the run actually examined, via a real run (not a hand-built fixture)."""
    definitions = DefinitionSet(
        jobs=[
            JobDefinition(name="JOB0001_SAMPLE_FW"),
            JobDefinition(name="JOB0002_SAMPLE_FW"),
        ]
    )
    findings = [
        Finding(rule_id="R1", severity="should-fix", ratified=False, target="a", message="m"),
        Finding(rule_id="R30", severity="must-fix", ratified=False, target="b", message="m"),
    ]
    proof = EquivalenceReport(equivalent=True, compared_jobs=2, proven_jobs=2)

    package = run_remediation_batch(
        definitions,
        findings,
        proof,
        title="[Remediation] two-job batch",
        owner="Synthetic Dev Team",
    )

    assert package.coverage is not None
    assert package.coverage.objects_examined == 2
    assert package.coverage.findings_by_rule == {"R1": 1, "R30": 1}
    body = render_handoff(package)
    assert "Objects examined: 2" in body
    assert "Findings recorded: 2 (ratified=0, unratified=2)" in body
