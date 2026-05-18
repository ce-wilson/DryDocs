"""Folder name parser — verifies the production naming convention."""
from __future__ import annotations

from drydocs.controlm import parse_folder_name


def test_real_folder_name_from_recursive_sample() -> None:
    """PRARAG-HLDM-111027-PEX-RFND-DLY:
       P=Prod, R=Retail, ARA=appcode, G=Smart folder, then domain segments."""
    p = parse_folder_name("PRARAG-HLDM-111027-PEX-RFND-DLY")
    assert p.prefix_recognized is True
    assert p.prefix == "PRARAG"
    assert p.environment_code == "P"
    assert p.environment == "Production"
    assert p.lob_code == "R"
    assert p.lob == "Retail"
    assert p.app_code == "ARA"
    assert p.folder_type_code == "G"
    assert p.folder_type == "Smart folder"
    assert p.segments == ("HLDM", "111027", "PEX", "RFND", "DLY")


def test_dev_environment() -> None:
    p = parse_folder_name("DRARAG-HLDM-111027-DEV")
    assert p.environment == "Development"
    assert p.environment_code == "D"
    assert p.app_code == "ARA"


def test_auto_appcode() -> None:
    p = parse_folder_name("PRAUTG-AUTO-15001-AUT-RFND-DLY")
    assert p.app_code == "AUT"
    assert p.lob == "Retail"
    assert p.folder_type == "Smart folder"


def test_no_segments_after_prefix() -> None:
    p = parse_folder_name("PRARAG")
    assert p.prefix == "PRARAG"
    assert p.segments == ()
    assert p.prefix_recognized is True


def test_unrecognised_prefix_keeps_raw() -> None:
    """Garbage in → still produces a result, just not recognised."""
    p = parse_folder_name("XX")
    assert p.prefix_recognized is False
    assert p.prefix == "XX"
    assert p.app_code is None


def test_empty_input() -> None:
    p = parse_folder_name("")
    assert p.prefix_recognized is False
    assert p.prefix == ""
    assert p.segments == ()


def test_unknown_folder_type_letter_preserved_as_code() -> None:
    """If position 6 is a letter we don't recognise, keep the code but
    leave folder_type as None."""
    p = parse_folder_name("PRARAX-HLDM-DLY")
    assert p.app_code == "ARA"
    assert p.folder_type_code == "X"
    assert p.folder_type is None
