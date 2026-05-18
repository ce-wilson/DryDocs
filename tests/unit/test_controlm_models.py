"""Pydantic validation for the Control-M row models."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from drydocs.models import ControlMConditionRow, ControlMFolderRow, ControlMJobRow


# ---- ControlMFolderRow -----------------------------------------------------

def test_folder_basic() -> None:
    row = ControlMFolderRow.model_validate({
        "folder_id": "F00100",
        "parent_table": "CCB_AUTO_DAILY",
        "data_center": "P12",
        "user_daily": "Y",
        "is_current_version": "1",
        "version_serial": "4",
        "capture_date": "2026-04-29T03:00:00",
    })
    assert row.folder_id == "F00100"
    assert row.parent_table == "CCB_AUTO_DAILY"
    assert row.data_center == "P12"
    assert row.user_daily == "Y"
    assert row.is_current_version == "1"
    assert row.version_serial == 4
    assert row.active is True  # scheduled + current version


def test_folder_inactive_when_not_current_version() -> None:
    row = ControlMFolderRow.model_validate({
        "folder_id": "F00102",
        "parent_table": "CCB_AUTO_RETIRED",
        "data_center": "P14",
        "user_daily": "Y",
        "is_current_version": "0",  # old version
        "version_serial": "7",
        "capture_date": "2026-04-29T03:00:00",
    })
    assert row.active is False  # scheduled but old version


def test_folder_inactive_when_user_daily_blank() -> None:
    row = ControlMFolderRow.model_validate({
        "folder_id": "F00102",
        "parent_table": "CCB_AUTO_RETIRED",
        "data_center": "P14",
        "user_daily": "",  # blank -> None -> inactive
    })
    assert row.user_daily is None
    assert row.active is False


def test_folder_inactive_when_user_daily_missing() -> None:
    row = ControlMFolderRow.model_validate({
        "folder_id": "F00102",
        "parent_table": "CCB_AUTO_RETIRED",
        "data_center": "P14",
        # user_daily column not present at all in the dict
    })
    assert row.user_daily is None
    assert row.active is False


def test_folder_requires_folder_id() -> None:
    with pytest.raises(ValidationError):
        ControlMFolderRow.model_validate({
            "folder_id": "",
            "parent_table": "X",
            "data_center": "P12",
            "user_daily": "Y",
        })


def test_folder_requires_data_center() -> None:
    with pytest.raises(ValidationError):
        ControlMFolderRow.model_validate({
            "folder_id": "F1",
            "parent_table": "X",
            "data_center": "",
            "user_daily": "Y",
        })


# ---- ControlMJobRow --------------------------------------------------------

def test_job_basic() -> None:
    row = ControlMJobRow.model_validate({
        "job_id": "J100001",
        "version_serial": "3",
        "folder_id": "F00100",
        "job_name": "AUTO_FW_TRADES",
        "cyclic_type": "DAILY",
        "job_order": "1",
    })
    assert row.job_id == "J100001"
    assert row.version_serial == 3
    assert row.folder_id == "F00100"
    assert row.cyclic_type == "DAILY"
    assert row.job_order == 1


def test_job_optional_fields_nullable() -> None:
    row = ControlMJobRow.model_validate({
        "job_id": "J100001",
        "version_serial": "0",
        "folder_id": "F00100",
        "job_name": "X",
        "cyclic_type": "",  # blank -> None
        "job_order": "",    # blank -> None
    })
    assert row.cyclic_type is None
    assert row.job_order is None


def test_job_version_serial_must_parse() -> None:
    with pytest.raises(ValidationError):
        ControlMJobRow.model_validate({
            "job_id": "J100001",
            "version_serial": "not-a-number",
            "folder_id": "F00100",
            "job_name": "X",
            "cyclic_type": "DAILY",
            "job_order": "1",
        })


def test_job_version_serial_rejects_negative() -> None:
    with pytest.raises(ValidationError):
        ControlMJobRow.model_validate({
            "job_id": "J100001",
            "version_serial": "-1",
            "folder_id": "F00100",
            "job_name": "X",
            "cyclic_type": "DAILY",
            "job_order": "1",
        })


def test_job_requires_folder_id() -> None:
    with pytest.raises(ValidationError):
        ControlMJobRow.model_validate({
            "job_id": "J100001",
            "version_serial": "1",
            "folder_id": "",
            "job_name": "X",
            "cyclic_type": "DAILY",
            "job_order": "1",
        })


# ---- ControlMConditionRow --------------------------------------------------

def test_condition_basic() -> None:
    """Confirmed columns for LNKO_P_VW: CAPTURE_DATE, TABLE_ID, JOB_ID,
    CONDITION, ODATE, SIGN, ISN_, VERSION_OPCODE, IS_CURRENT_VERSION,
    VERSION_SERIAL.  Schema for LNKI_P_VW is inferred by symmetry."""
    row = ControlMConditionRow.model_validate({
        "folder_id": "F00100",
        "job_id": "J100002",
        "version_serial": "3",
        "condition_name": "TRADES_FILE_RECEIVED",
        "odate": "20260429",
        "sign": "+",
        "isn": "12345",
        "version_opcode": "I",
        "is_current_version": "1",
        "capture_date": "2026-04-29T03:00:00",
    })
    assert row.folder_id == "F00100"
    assert row.job_id == "J100002"
    assert row.version_serial == 3
    assert row.condition_name == "TRADES_FILE_RECEIVED"
    assert row.odate == "20260429"
    assert row.sign == "+"
    assert row.isn == 12345
    assert row.version_opcode == "I"


def test_condition_lnki_has_no_version_opcode() -> None:
    """LNKI_P_VW does NOT have VERSION_OPCODE (it's specific to out-conditions)."""
    row = ControlMConditionRow.model_validate({
        "folder_id": "F00100",
        "job_id": "J100002",
        "version_serial": "3",
        "condition_name": "TRADES_FILE_RECEIVED",
        "odate": "20260429",
        "sign": "+",
        "isn": "12345",
        # no version_opcode
        "is_current_version": "1",
        "capture_date": "2026-04-29T03:00:00",
    })
    assert row.version_opcode is None
