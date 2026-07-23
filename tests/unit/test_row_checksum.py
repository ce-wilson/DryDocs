"""Unit tests for the delta-detection row checksum (doc 06 Phase 2 —
provenance-edge diet). Offline — no Neo4j.

Covers the shared helper (:func:`drydocs.loaders.base.compute_row_checksum`)
in isolation, then each Control-M loader's ``to_params`` wiring that feeds
``row_checksum`` into the batch the Cypher template consumes.
"""
from __future__ import annotations

from drydocs.loaders.base import compute_row_checksum
from drydocs.loaders.controlm_conditions_in import ControlMConditionsInLoader
from drydocs.loaders.controlm_conditions_out import ControlMConditionsOutLoader
from drydocs.loaders.controlm_folders import ControlMFoldersLoader
from drydocs.loaders.controlm_jobs import ControlMJobsLoader
from drydocs_core.models import (
    ControlMConditionInRow,
    ControlMConditionOutRow,
    ControlMFolderRow,
    ControlMJobRow,
)


# ---- compute_row_checksum, in isolation ------------------------------------

def test_same_row_same_hash() -> None:
    row = {"a": 1, "b": "x", "c": None}
    assert compute_row_checksum(row) == compute_row_checksum(dict(row))


def test_field_change_changes_hash() -> None:
    row1 = {"a": 1, "b": "x"}
    row2 = {"a": 2, "b": "x"}
    assert compute_row_checksum(row1) != compute_row_checksum(row2)


def test_key_order_is_irrelevant() -> None:
    row1 = {"a": 1, "b": 2, "c": 3}
    row2 = {"c": 3, "a": 1, "b": 2}
    assert compute_row_checksum(row1) == compute_row_checksum(row2)


def test_capture_date_excluded_by_default() -> None:
    """capture_date is the ETL/replication pull timestamp, not a source-record
    value — it must NOT affect the hash, or every row would look 'changed' on
    every run regardless of actual content."""
    row1 = {"job_id": "1", "capture_date": "2026-01-01"}
    row2 = {"job_id": "1", "capture_date": "2027-06-06"}
    assert compute_row_checksum(row1) == compute_row_checksum(row2)


def test_batch_level_params_excluded_defensively() -> None:
    """run_id/loaded_at are BaseLoader._flush batch params, not row content —
    excluded even though today's to_params dicts never carry them, so a
    future refactor can't silently poison every hash."""
    row1 = {"job_id": "1", "run_id": "run-a", "loaded_at": "t1"}
    row2 = {"job_id": "1", "run_id": "run-b", "loaded_at": "t2"}
    assert compute_row_checksum(row1) == compute_row_checksum(row2)


def test_custom_exclude_set_widens_default() -> None:
    row1 = {"a": 1, "noisy": "x"}
    row2 = {"a": 1, "noisy": "y"}
    assert compute_row_checksum(
        row1, exclude=frozenset({"noisy"})
    ) == compute_row_checksum(row2, exclude=frozenset({"noisy"}))


def test_checksum_is_a_stable_hex_digest() -> None:
    checksum = compute_row_checksum({"a": 1})
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # sha256 hex digest
    int(checksum, 16)  # raises if not valid hex


# ---- loader.to_params wiring ------------------------------------------------
# Loaders' to_params only touches the row model / dict, not self — safe to
# build via __new__ and skip BaseLoader.__init__ (no client/adapter needed).

_JOB_ROW = {
    "job_id": "J1",
    "version_serial": "3",
    "folder_id": "F1",
    "job_name": "JOBX",
}


def test_jobs_to_params_adds_row_checksum() -> None:
    loader = ControlMJobsLoader.__new__(ControlMJobsLoader)
    params = loader.to_params(ControlMJobRow.model_validate(_JOB_ROW))
    assert "row_checksum" in params
    assert len(params["row_checksum"]) == 64


def test_jobs_to_params_checksum_stable_ignoring_capture_date() -> None:
    loader = ControlMJobsLoader.__new__(ControlMJobsLoader)
    model1 = ControlMJobRow.model_validate({**_JOB_ROW, "capture_date": "2026-01-01 00:00:00"})
    model2 = ControlMJobRow.model_validate({**_JOB_ROW, "capture_date": "2027-06-06 00:00:00"})
    assert loader.to_params(model1)["row_checksum"] == loader.to_params(model2)["row_checksum"]


def test_jobs_to_params_checksum_changes_on_content_change() -> None:
    loader = ControlMJobsLoader.__new__(ControlMJobsLoader)
    model1 = ControlMJobRow.model_validate(_JOB_ROW)
    model2 = ControlMJobRow.model_validate({**_JOB_ROW, "job_name": "JOBY"})
    assert loader.to_params(model1)["row_checksum"] != loader.to_params(model2)["row_checksum"]


_FOLDER_ROW = {
    "folder_id": "100",
    "sched_table": "CCB_AUTO_DAILY",
    "data_center": "P12",
    "user_daily": "Y",
}


def test_folders_to_params_adds_row_checksum_alongside_parsed_fields() -> None:
    loader = ControlMFoldersLoader.__new__(ControlMFoldersLoader)
    params = loader.to_params(ControlMFolderRow.model_validate(_FOLDER_ROW))
    assert "row_checksum" in params
    assert "app_code" in params  # the one surviving parsed field (join key)
    # folder property diet (SME ruling 2026-07-23): the expanded
    # naming-convention decode never reaches the batch params
    for retired in ("environment_code", "environment", "lob_code", "lob",
                    "folder_type_code", "folder_type"):
        assert retired not in params


def test_folders_to_params_checksum_stable_ignoring_capture_date() -> None:
    loader = ControlMFoldersLoader.__new__(ControlMFoldersLoader)
    model1 = ControlMFolderRow.model_validate({**_FOLDER_ROW, "capture_date": "2026-01-01"})
    model2 = ControlMFolderRow.model_validate({**_FOLDER_ROW, "capture_date": "2027-01-01"})
    assert loader.to_params(model1)["row_checksum"] == loader.to_params(model2)["row_checksum"]


def test_folders_to_params_checksum_changes_on_content_change() -> None:
    loader = ControlMFoldersLoader.__new__(ControlMFoldersLoader)
    model1 = ControlMFolderRow.model_validate(_FOLDER_ROW)
    model2 = ControlMFolderRow.model_validate({**_FOLDER_ROW, "user_daily": ""})
    assert loader.to_params(model1)["row_checksum"] != loader.to_params(model2)["row_checksum"]


_COND_ROW = {
    "folder_id": "100",
    "job_id": "J1",
    "version_serial": "1",
    "condition_name": "C-OK",
}


def test_conditions_in_to_params_adds_row_checksum() -> None:
    loader = ControlMConditionsInLoader.__new__(ControlMConditionsInLoader)
    params = loader.to_params(ControlMConditionInRow.model_validate(_COND_ROW))
    assert "row_checksum" in params


def test_conditions_in_to_params_checksum_stable_ignoring_capture_date() -> None:
    loader = ControlMConditionsInLoader.__new__(ControlMConditionsInLoader)
    model1 = ControlMConditionInRow.model_validate({**_COND_ROW, "capture_date": "2026-01-01"})
    model2 = ControlMConditionInRow.model_validate({**_COND_ROW, "capture_date": "2027-01-01"})
    assert loader.to_params(model1)["row_checksum"] == loader.to_params(model2)["row_checksum"]


def test_conditions_out_to_params_adds_row_checksum() -> None:
    loader = ControlMConditionsOutLoader.__new__(ControlMConditionsOutLoader)
    params = loader.to_params(ControlMConditionOutRow.model_validate(_COND_ROW))
    assert "row_checksum" in params


def test_conditions_out_to_params_checksum_stable_ignoring_capture_date() -> None:
    loader = ControlMConditionsOutLoader.__new__(ControlMConditionsOutLoader)
    model1 = ControlMConditionOutRow.model_validate({**_COND_ROW, "capture_date": "2026-01-01"})
    model2 = ControlMConditionOutRow.model_validate({**_COND_ROW, "capture_date": "2027-01-01"})
    assert loader.to_params(model1)["row_checksum"] == loader.to_params(model2)["row_checksum"]
