"""Jira handoff boundary (TDD Stage E, FR-REM-6): deterministic render, the
Jira-only side-effect boundary, ownership surfaced-not-guessed, and the
no-unproven-submit rule."""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_remediation.detect import Finding
from drydocs_remediation.equivalence import EquivalenceReport
from drydocs_remediation.jira import (
    HandoffPackage,
    JiraRef,
    JiraSubmitter,
    UnprovenHandoffError,
    emit_handoff,
    render_handoff,
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
        proof=EquivalenceReport(equivalent=equivalent, compared_jobs=1),
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
    assert "Offline equivalence: PASS (1 job(s) compared)" in body1
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
