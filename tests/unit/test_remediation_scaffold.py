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
from drydocs_remediation.formats import DefinitionFormat, DefinitionSet, XmlDefinitionFormat
from drydocs_remediation.jira import JiraRef


def test_package_surface() -> None:
    assert set(drydocs_remediation.__all__) == {
        "corroborate",
        "detect",
        "equivalence",
        "formats",
        "jira",
        "transform",
        # G67: adapts a staged definition export into DefinitionSet. Reading
        # was never the blocked half of the XML problem — dump() still raises.
        "xml_bridge",
    }


def test_definition_format_is_abstract() -> None:
    with pytest.raises(TypeError):
        DefinitionFormat()  # type: ignore[abstract]


def test_xml_load_works_and_dump_stays_a_deliberate_seam(tmp_path: Path) -> None:
    """``load`` reads real Control-M XML via xml_io (position-faithful
    projection). ``dump`` still raises — not schema-blocked anymore, but
    because a bare DefinitionSet cannot express the §XML splice contract:
    emission needs the original document + an attributed edit script
    (``xml_io.write``), never a regeneration from the model."""
    src = tmp_path / "legacy.xml"
    src.write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n<DEFTABLE>\n'
        b'  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRSCF1A">\n'
        b'    <JOB JOBNAME="PRSCF1A001" TASKTYPE="Command" CMDLINE="run.sh"/>\n'
        b"  </SMART_FOLDER>\n</DEFTABLE>\n"
    )
    xml = XmlDefinitionFormat()
    definitions = xml.load(src)
    assert [j.name for j in definitions.jobs] == ["PRSCF1A001"]
    with pytest.raises(NotImplementedError, match="rule 1"):
        xml.dump(DefinitionSet(), Path("greenfield.xml"))


def test_finding_and_refs_are_value_objects() -> None:
    f = Finding(rule_id="R1", severity="should-fix", ratified=False, target="job", message="m")
    assert f.ratified is False
    assert JiraRef(key="X-1").key == "X-1"
