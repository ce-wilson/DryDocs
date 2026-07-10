"""drydocs-remediation scaffold guards (ADR 0002-B §2 step 1, G3).

The real verification gates (no-graph-write, Jira-only, equivalence proof — 0002-B §3)
land WITH the implementations. Here we pin the structural contract: the package imports
cleanly, the format seam is abstract, and the remaining stubs are honest about being
stubs (NotImplementedError, not silent no-ops). The implemented M0 behavior lives in
``test_remediation_m0.py``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import drydocs_remediation
from drydocs_remediation.detect import Finding
from drydocs_remediation.equivalence import EquivalenceReport
from drydocs_remediation.formats import DefinitionFormat, DefinitionSet, XmlDefinitionFormat
from drydocs_remediation.jira import JiraRef, emit_handoff
from drydocs_remediation.transform import propose_greenfield


def test_package_surface() -> None:
    assert set(drydocs_remediation.__all__) == {
        "detect", "equivalence", "formats", "jira", "transform",
    }


def test_definition_format_is_abstract() -> None:
    with pytest.raises(TypeError):
        DefinitionFormat()  # type: ignore[abstract]


def test_remaining_stubs_raise_not_implemented() -> None:
    """XML I/O is schema-acquisition-blocked; transform + jira are the M1 slice."""
    ds = DefinitionSet()
    xml = XmlDefinitionFormat()
    with pytest.raises(NotImplementedError):
        xml.load(Path("legacy.xml"))
    with pytest.raises(NotImplementedError):
        xml.dump(ds, Path("greenfield.xml"))
    with pytest.raises(NotImplementedError):
        propose_greenfield(ds, [])
    with pytest.raises(NotImplementedError):
        emit_handoff([], Path("greenfield.xml"), EquivalenceReport(equivalent=True))


def test_finding_and_refs_are_value_objects() -> None:
    f = Finding(rule_id="R1", severity="should-fix", ratified=False, target="job", message="m")
    assert f.ratified is False
    assert JiraRef(key="X-1").key == "X-1"
