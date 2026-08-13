"""xml_io test classes A (identity round-trip) and B (locator + projection).

Class A is the module's thesis: ``render(load_document(f))`` with no edits is
the original file, byte for byte, on every fixture — the test no
serializer-based design can pass (measured: ElementTree loses multi-line
attribute wrapping, DOCTYPE, comments, quote style, and literal ``>``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_remediation.xml_io import (
    AmbiguousLocatorError,
    Locator,
    LocatorNotFoundError,
    UnsupportedEncodingError,
    load_document,
    locate,
    render,
    to_definition_set,
)
from tests.unit.fixtures_controlm_xml import (
    F3_RESIDUE,
    F6_DUPLICATES,
    F8_NESTING,
    F10_UTF16,
    F11_MULTI_DC,
    ROUND_TRIP_FIXTURES,
)

# --------------------------------------------------------------------------- #
# A. Identity round-trip
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("name", sorted(ROUND_TRIP_FIXTURES))
def test_identity_round_trip_in_memory(name: str) -> None:
    """No edits -> the source, byte for byte. Every hazard fixture."""
    source = ROUND_TRIP_FIXTURES[name]
    assert render(load_document(source)) == source


@pytest.mark.parametrize("name", sorted(ROUND_TRIP_FIXTURES))
def test_identity_round_trip_file_to_file(name: str, tmp_path: Path) -> None:
    """Through real files in BINARY mode — BOM/newline/encoding bugs can't hide
    behind an in-memory comparison."""
    source = ROUND_TRIP_FIXTURES[name]
    src = tmp_path / f"{name}.xml"
    src.write_bytes(source)
    doc = load_document(src)
    out = tmp_path / f"{name}.out.xml"
    out.write_bytes(render(doc))
    assert out.read_bytes() == source
    assert doc.origin == src


def test_utf16_is_refused() -> None:
    """F10: byte-offset lexing is unsound for multi-byte-unit encodings."""
    with pytest.raises(UnsupportedEncodingError, match="utf-16"):
        load_document(F10_UTF16)


def test_crlf_and_bom_are_detected_not_normalized() -> None:
    doc = load_document(ROUND_TRIP_FIXTURES["F5_prolog"])
    assert doc.newline == b"\r\n"
    assert doc.bom == b"\xef\xbb\xbf"


def test_residue_elements_survive_verbatim() -> None:
    """The elements the curated model does not carry are still in the output —
    the capture-all requirement, proven on the bytes."""
    out = render(load_document(F3_RESIDUE))
    for tag in (
        b"<INCOND ",
        b"<OUTCOND ",
        b"<QUANTITATIVE ",
        b"<CONTROL ",
        b"<ON ",
        b"<DOACTION ",
        b"<DOMAIL ",
        b"<CAPTURE ",
        b"<RULE_BASED_CALENDARS ",
    ):
        assert tag in out, f"residue element {tag!r} lost"


# --------------------------------------------------------------------------- #
# B. Locator + position-faithful projection
# --------------------------------------------------------------------------- #


def test_locator_resolves_through_three_levels_of_nesting() -> None:
    doc = load_document(F8_NESTING)
    node = locate(doc, Locator(folder="PRXYZ8H", subfolder_path="A/B/C", job="PRXYZ8H301"))
    assert node.attr_value("CMDLINE") == "%%L0/%%L1/%%L2"


def test_locator_duplicate_variable_requires_ordinal() -> None:
    doc = load_document(F6_DUPLICATES)
    base = Locator(folder="PRXYZ6F", job="PRXYZ6F001", element="VARIABLE", name="%%DIR")
    with pytest.raises(AmbiguousLocatorError, match="§VARS|first-class|give ordinal"):
        locate(doc, base)
    first = locate(doc, Locator(**{**base.__dict__, "ordinal": 0}))
    second = locate(doc, Locator(**{**base.__dict__, "ordinal": 1}))
    assert first.attr_value("VALUE") == "/first"
    assert second.attr_value("VALUE") == "/second"


def test_locator_duplicate_job_requires_ordinal() -> None:
    doc = load_document(F6_DUPLICATES)
    with pytest.raises(AmbiguousLocatorError, match="give ordinal"):
        locate(doc, Locator(folder="PRXYZ6F", job="PRXYZ6F002"))
    second = locate(doc, Locator(folder="PRXYZ6F", job="PRXYZ6F002", ordinal=1))
    assert second.attr_value("CMDLINE") == "two.sh"


def test_locator_element_lookup_refuses_a_duplicated_job() -> None:
    """ordinal belongs to the innermost coordinate, so a duplicated job cannot
    be resolved PAST — that would silently pick which job's variable to edit."""
    doc = load_document(F6_DUPLICATES)
    with pytest.raises(AmbiguousLocatorError, match="unique job"):
        locate(doc, Locator(folder="PRXYZ6F", job="PRXYZ6F002", element="VARIABLE", name="%%X"))


def test_locator_misses_are_loud() -> None:
    doc = load_document(F6_DUPLICATES)
    with pytest.raises(LocatorNotFoundError):
        locate(doc, Locator(folder="NOPE"))
    with pytest.raises(LocatorNotFoundError):
        locate(doc, Locator(folder="PRXYZ6F", job="GHOST"))
    with pytest.raises(LocatorNotFoundError):
        locate(
            doc,
            Locator(
                folder="PRXYZ6F", job="PRXYZ6F001", element="VARIABLE", name="%%DIR", ordinal=9
            ),
        )


def test_projection_is_position_faithful() -> None:
    """The nameless VARIABLE stays in the list at its document ordinal — the
    lineage extractor skips-and-counts it; an editor's index must not drift."""
    definitions = to_definition_set(load_document(F6_DUPLICATES))
    job = definitions.jobs[0]
    assert [n for n, _ in job.variables] == ["%%DIR", "", "%%DIR"]
    assert job.variables[1] == ("", "orphan-value-no-name")


def test_projection_carries_the_curated_fields() -> None:
    definitions = to_definition_set(load_document(F3_RESIDUE))
    folder = definitions.folders[0]
    assert (folder.name, folder.scope) == ("PRXYZ3C", "FOLDER")
    assert folder.variables == [("%%SCRIPT_PATH", "/opt/dpl")]
    sub = [f for f in definitions.folders if f.scope == "SUBFOLDER"]
    assert [f.name for f in sub] == ["PRXYZ3C/NESTED"]
    job = definitions.jobs[0]
    assert job.name == "PRXYZ3C001"
    assert job.command_line == "%%SCRIPT_PATH/run.sh -env %%ENV"
    assert job.post_command == "cat %%SCRIPT_PATH/out.tok"
    assert job.description == "runs %%SCRIPT_PATH nightly"
    # DOMAIL sits inside ON, which is not a scan-stop tag (only nested jobs /
    # sub-folders are) — so the notification scan finds it, as the extractor's does.
    assert job.notification_tags == ("DOMAIL",)
    nested = definitions.jobs[1]
    assert nested.subfolder_path == "NESTED"
    assert nested.scope_chain[0][0] == "FOLDER"
    assert nested.scope_chain[1] == ("SUBFOLDER", "NESTED", [("%%SCRIPT_PATH", "/opt/dpl/nested")])
    assert nested.scope_chain[2][0] == "JOB"


def test_projection_scope_chain_three_levels() -> None:
    definitions = to_definition_set(load_document(F8_NESTING))
    job = definitions.jobs[0]
    assert [layer[0] for layer in job.scope_chain] == [
        "FOLDER",
        "SUBFOLDER",
        "SUBFOLDER",
        "SUBFOLDER",
        "JOB",
    ]
    assert job.subfolder_path == "A/B/C"
    assert job.scope_chain[3][1] == "A/B/C"


def test_entity_values_decode_correctly() -> None:
    doc = load_document(ROUND_TRIP_FIXTURES["F4_entities"])
    job = locate(doc, Locator(folder="PRXYZ4D", job="PRXYZ4D001"))
    assert job.attr_value("NOTE") == "gt > literal"
    assert job.attr_value("TAB") == "a\tb"
    assert job.attr_value("ALPHA") == "Alpha"
    assert job.attr_value("HEXA") == "Alpha"
    assert job.attr_value("CMDLINE") == 'run.sh --flag="x"'
    folder = locate(doc, Locator(folder="PRXYZ4D"))
    assert folder.attr_value("DESCRIPTION") == "café & bar <ETL> \"quoted\" 'single'"


def test_latin1_high_byte_decodes() -> None:
    doc = load_document(ROUND_TRIP_FIXTURES["F9_latin1"])
    assert locate(doc, Locator(folder="PRXYZ9I")).attr_value("DESCRIPTION") == "café"


# --------------------------------------------------------------------------- #
# data_center — the other half of the folder's identity (2026-08-12 check:
# the bytes always carried it; the MODEL dropped it)
# --------------------------------------------------------------------------- #


def test_projection_carries_data_center() -> None:
    """Folder names repeat across data centers, so a projection without the DC
    collapses same-named folders into indistinguishable entries."""
    definitions = to_definition_set(load_document(F11_MULTI_DC))
    assert [(f.name, f.data_center) for f in definitions.folders] == [
        ("PRXYZ1A", "DC1"),
        ("PRXYZ1A", "DC2"),
    ]
    assert [(j.name, j.data_center, j.command_line) for j in definitions.jobs] == [
        ("PRXYZ1A001", "DC1", "dc1.sh"),
        ("PRXYZ1A001", "DC2", "dc2.sh"),
    ]


def test_projection_data_center_reaches_subfolders_and_nested_jobs() -> None:
    definitions = to_definition_set(load_document(F3_RESIDUE))
    assert all(f.data_center == "DC1" for f in definitions.folders)
    assert all(j.data_center == "DC1" for j in definitions.jobs)


def test_locator_disambiguates_same_named_folders_by_data_center() -> None:
    doc = load_document(F11_MULTI_DC)
    with pytest.raises(AmbiguousLocatorError, match="data_center"):
        locate(doc, Locator(folder="PRXYZ1A"))
    dc2_job = locate(doc, Locator(folder="PRXYZ1A", data_center="DC2", job="PRXYZ1A001"))
    assert dc2_job.attr_value("CMDLINE") == "dc2.sh"
    with pytest.raises(LocatorNotFoundError, match="DC9"):
        locate(doc, Locator(folder="PRXYZ1A", data_center="DC9"))
