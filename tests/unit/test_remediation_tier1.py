"""Tier-1 transform engine (TDD Stage C/D, FR-REM-3).

Per-rule contract: pure, idempotent, ratified-only application, behavior-preserving
(the equivalence proof passes across the transform). Rule VALUES here are synthetic —
real maps/ids are company-side.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_remediation.equivalence import prove_equivalence, resolved_watch
from drydocs_remediation.formats import TranscriptDefinitionFormat
from drydocs_remediation.transform import canonical_variable_rename, propose_greenfield

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "remediation"


def _legacy():
    return TranscriptDefinitionFormat().load(FIXTURES / "synthetic-legacy-transcript.yaml")


def _rename_rule(ratified: bool = True):
    return canonical_variable_rename(
        {"DIR_A": "DIR_CANON", "PFX": "FILE_PREFIX"},
        rule_id="SYN-1",
        ratified=ratified,
    )


def test_ratified_rule_applies_and_rewrites_references() -> None:
    ds = _legacy()
    result = propose_greenfield(ds, [_rename_rule()])
    assert result.applied == ["SYN-1"]
    assert result.skipped_unratified == []
    job = result.greenfield.jobs[0]
    names = [n for n, _ in job.variables]
    assert "%%DIR_CANON" in names and "%%FILE_PREFIX" in names
    assert "%%DIR_A" not in names and "%%PFX" not in names
    assert job.watch_template.startswith("%%DIR_CANON.%%FILE_PREFIX.")
    # the input set is untouched (pure transform)
    assert ds.jobs[0].variables[0][0] == "%%DIR_A"


def test_transform_preserves_resolved_behavior() -> None:
    ds = _legacy()
    result = propose_greenfield(ds, [_rename_rule()])
    report = prove_equivalence(ds, result.greenfield)
    assert report.equivalent is True
    assert (
        resolved_watch(result.greenfield.folder_variables(), result.greenfield.jobs[0])
        == "/data/sample/in/Sample_File_{ODATE}.tok"
    )


def test_rule_is_idempotent() -> None:
    rule = _rename_rule()
    once = rule.apply(_legacy())
    twice = rule.apply(once)
    assert twice.jobs[0].variables == once.jobs[0].variables
    assert twice.jobs[0].watch_template == once.jobs[0].watch_template


def test_unratified_rule_is_skipped_loudly() -> None:
    ds = _legacy()
    result = propose_greenfield(ds, [_rename_rule(ratified=False)])
    assert result.applied == []
    assert result.skipped_unratified == ["SYN-1"]
    assert result.greenfield.jobs[0].variables == ds.jobs[0].variables


def test_rename_does_not_touch_longer_names() -> None:
    # "DIR" is a prefix of "DIR_A" — the rename must not rewrite inside it
    rule = canonical_variable_rename({"DIR": "X"}, rule_id="SYN-2", ratified=True)
    out = rule.apply(_legacy())
    assert out.jobs[0].watch_template == _legacy().jobs[0].watch_template
    assert [n for n, _ in out.jobs[0].variables] == [n for n, _ in _legacy().jobs[0].variables]


def test_conflicting_rename_raises() -> None:
    # renaming PFX onto the already-existing EXT is Tier-2 judgment, not Tier-1
    rule = canonical_variable_rename({"PFX": "EXT"}, rule_id="SYN-3", ratified=True)
    with pytest.raises(ValueError, match="SYN-3"):
        rule.apply(_legacy())
