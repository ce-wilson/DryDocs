"""G4 scaffold guards — drydocs_lineage (C2) + drydocs_deepdoc (C3), ADR 0002 D2.

Pins the structural contract: both packages import cleanly, SHARE the core parser
(the literal D2 requirement — asserted via their module surfaces), declare opposite
write targets across the trust boundary, and are honest stubs. The D2 separation
("neither imports the other") is enforced by test_module_boundary's
components-don't-import-each-other rule over the new `lineage`/`deepdoc` groups.
"""
from __future__ import annotations

import pytest

import drydocs_deepdoc
import drydocs_lineage
from drydocs_deepdoc.investigate import ContextFinding, investigate_failure
from drydocs_deepdoc.writer import write_findings
from drydocs_lineage.curation import CurationStatus, curate
from drydocs_lineage.model import LineageGraph
from drydocs_lineage.writer import write_curated


def test_package_surfaces() -> None:
    assert set(drydocs_lineage.__all__) == {
        "DATABASE", "curation", "extractors", "model", "writer",
    }
    assert set(drydocs_deepdoc.__all__) == {"DATABASE", "investigate", "writer"}


def test_write_targets_sit_on_opposite_sides_of_the_trust_boundary() -> None:
    assert drydocs_lineage.DATABASE == "drydocs"           # ground truth (curated)
    assert drydocs_deepdoc.DATABASE == "drydocs_context"   # isolated uncertain
    assert drydocs_lineage.DATABASE != drydocs_deepdoc.DATABASE


def test_both_components_share_the_core_parser() -> None:
    # D2: "they share the command-line/lineage parser in drydocs-core"
    import drydocs_core.controlm as core_parser

    from drydocs_deepdoc import investigate
    from drydocs_lineage.extractors import controlm_inventory

    assert controlm_inventory.parse_command is core_parser.parse_command
    assert investigate.parse_command is core_parser.parse_command
    assert investigate.extract_container_command is core_parser.extract_container_command


def test_stubs_raise_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        curate([], {})
    with pytest.raises(NotImplementedError):
        write_curated(LineageGraph(), set())
    with pytest.raises(NotImplementedError):
        investigate_failure("JOB0001_SAMPLE", "FOLDER-SYNTH")
    with pytest.raises(NotImplementedError):
        write_findings([])


def test_value_objects_carry_the_trust_contract() -> None:
    assert CurationStatus.PROPOSED.value == "proposed"  # candidates never born confirmed
    finding = ContextFinding(
        subject_urn="urn:sample:job", predicate="observed_reads",
        object_urn="urn:sample:asset", reliability=0.4,
        trust="SYNTHESIZED", evidence="synthetic",
    )
    assert 0.0 <= finding.reliability <= 1.0
    assert finding.trust == "SYNTHESIZED"  # VERBATIM never originates in deepdoc
