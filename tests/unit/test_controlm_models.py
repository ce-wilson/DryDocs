"""Pydantic validation for the Control-M row models — schemas locked to
the actual psgmgr DDL.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from drydocs.models import (
    ControlMConditionInRow,
    ControlMConditionOutRow,
    ControlMDependencyRow,
    ControlMFolderRow,
    ControlMJobRow,
)


# ---- ControlMFolderRow -----------------------------------------------------

def test_folder_basic_real_columns() -> None:
    """psgmgr.CM_DEF_VTAB has SCHED_TABLE (not PARENT_TABLE) and NO
    IS_CURRENT_VERSION / VERSION_SERIAL columns."""
    row = ControlMFolderRow.model_validate({
        "folder_id": "100",
        "sched_table": "CCB_AUTO_DAILY",
        "data_center": "P12",
        "user_daily": "Y",
        "table_status": "A",
        "table_type": "2",
        "instance_name": "PROD-EAST",
        "last_updated": "2026-04-29 03:00:00",
        "last_updated_user": "svc.cmadmin",
        "capture_date": "2026-04-29 03:00:00",
    })
    assert row.folder_id == "100"
    assert row.sched_table == "CCB_AUTO_DAILY"
    assert row.table_type == 2
    assert row.active is True


def test_folder_inactive_when_user_daily_null() -> None:
    """User_daily is the ONLY active-scheduling filter on folders."""
    row = ControlMFolderRow.model_validate({
        "folder_id": "102",
        "sched_table": "CCB_AUTO_RETIRED",
        "data_center": "P14",
        "user_daily": "",
        "table_status": "R",
        "table_type": "2",
        "instance_name": "PROD-EAST",
        "last_updated": "2025-11-01 03:00:00",
        "last_updated_user": "svc.cmadmin",
        "capture_date": "2026-04-29 03:00:00",
    })
    assert row.active is False


def test_folder_requires_sched_table() -> None:
    with pytest.raises(ValidationError):
        ControlMFolderRow.model_validate({
            "folder_id": "1",
            "sched_table": "",
            "data_center": "P12",
            "user_daily": "Y",
        })


# ---- ControlMJobRow --------------------------------------------------------

def test_job_basic_real_columns() -> None:
    """psgmgr.CM_DEF_VJOB has the columns we project per controlm_jobs.sql.
    APPLICATION is a key business-app reconciliation column."""
    row = ControlMJobRow.model_validate({
        "job_id": "100002",
        "version_serial": "3",
        "folder_id": "100",
        "job_name": "AUTO_LOAD_TRADES",
        "parent_table": "CCB_AUTO_DAILY",
        "application": "CCB Auto Risk",
        "group_name": "AUTO_DAILY",
        "task_type": "Job",
        "cyclic": "N",
        "cyclic_type": "",
        "job_order": "2",
        "owner": "svc.autoetl",
        "author": "jdoe",
        "node_id": "host-auto-01",
        "cmd_line": "/opt/scripts/auto/trade_load.pset",
        "description": "Ab Initio graph load to trusted",
        "memname": "",
        "priority": "5",
        "critical": "Y",
        "active_from": "",
        "active_till": "",
        "end_folder": "N",
        "is_current_version": "1",
        "version_opcode": "U",
        "version_timestamp": "20260429030000",
        "version_user": "jdoe",
        "instance_name": "PROD-EAST",
        "capture_date": "2026-04-29 03:00:00",
    })
    assert row.job_id == "100002"
    assert row.version_serial == 3
    assert row.application == "CCB Auto Risk"
    assert row.parent_table == "CCB_AUTO_DAILY"
    assert row.is_current_version == "1"
    assert row.cmd_line.endswith(".pset")


def test_job_version_serial_must_parse() -> None:
    with pytest.raises(ValidationError):
        ControlMJobRow.model_validate({
            "job_id": "J1",
            "version_serial": "not-a-number",
            "folder_id": "100",
            "job_name": "X",
        })


# ---- ControlMConditionInRow -----------------------------------------------

def test_condition_in_has_boolean_expression_columns() -> None:
    """LNKI_P has AND_OR / PARENTHESES / ORDER_ (no SIGN)."""
    row = ControlMConditionInRow.model_validate({
        "folder_id": "100",
        "job_id": "100002",
        "version_serial": "3",
        "condition_name": "TRADES_FILE_ARRIVED",
        "odate": "20260429",
        "and_or": "AND",
        "parentheses": "",
        "order_": "1",
        "isn": "1",
        "version_opcode": "U",
        "is_current_version": "1",
        "capture_date": "2026-04-29 03:00:00",
    })
    assert row.condition_name == "TRADES_FILE_ARRIVED"
    assert row.and_or == "AND"
    assert row.order_ == 1
    # Confirm: LNKI does NOT have a SIGN attribute on the model.
    assert not hasattr(row, "sign")


# ---- ControlMConditionOutRow ----------------------------------------------

def test_condition_out_has_sign_no_boolean_expression() -> None:
    """LNKO_P has SIGN (no AND_OR / PARENTHESES / ORDER_)."""
    row = ControlMConditionOutRow.model_validate({
        "folder_id": "100",
        "job_id": "100001",
        "version_serial": "3",
        "condition_name": "TRADES_FILE_ARRIVED",
        "odate": "20260429",
        "sign": "+",
        "isn": "1",
        "version_opcode": "U",
        "is_current_version": "1",
        "capture_date": "2026-04-29 03:00:00",
    })
    assert row.sign == "+"
    assert not hasattr(row, "and_or")


# ---- ControlMDependencyRow ------------------------------------------------

def test_dependency_row_carries_path_and_level() -> None:
    """Output rows of the recursive predecessor SQL."""
    row = ControlMDependencyRow.model_validate({
        "in_parent_table": "CCB_AUTO_DAILY",
        "in_job_name": "AUTO_TDQ_TRADES",
        "in_parent_table_id": "100",
        "in_job_id": "100003",
        "in_table_job_id": "100.100003",
        "out_condition": "TRADES_LOAD_OK",
        "dependent_table": "CCB_AUTO_DAILY",
        "dependent_job": "AUTO_LOAD_TRADES",
        "dependent_table_id": "100",
        "dependent_job_id": "100002",
        "out_table_job_id": "100.100002",
        "recursion_level": "1",
        "dependency_path": "AUTO_TDQ_TRADES -> AUTO_LOAD_TRADES",
    })
    assert row.recursion_level == 1
    assert " -> " in row.dependency_path
    assert row.in_table_job_id == "100.100003"


def test_dependency_recursion_level_min() -> None:
    with pytest.raises(ValidationError):
        ControlMDependencyRow.model_validate({
            "in_parent_table": "F",
            "in_job_name": "X",
            "in_parent_table_id": "1",
            "in_job_id": "1",
            "in_table_job_id": "1.1",
            "out_condition": "C",
            "dependent_table": "F",
            "dependent_job": "Y",
            "dependent_table_id": "1",
            "dependent_job_id": "2",
            "out_table_job_id": "1.2",
            "recursion_level": "0",  # invalid — recursion levels start at 1
            "dependency_path": "X -> Y",
        })
