"""Unit tests for the STG_* staging-row builder (Phase A output side)."""
from __future__ import annotations

from pathlib import Path

from drydocs.adapters.csv_adapter import CsvAdapter
from drydocs.controlm.staging import build_staging_rows, collect_jobs
from drydocs.models import ControlMVariableRow

SAMPLE = (
    Path(__file__).resolve().parents[2]
    / "drydocs" / "data" / "samples" / "controlm_variables__sample.csv"
)

# every column of STG_VARIABLE except the identity PK, in DDL order
STG_VARIABLE_COLUMNS = [
    "run_id", "data_center", "folder_id", "job_id", "src_ordinal",
    "var_scope", "var_name", "raw_value", "resolved_value", "var_kind",
    "env_tag", "is_fully_resolved", "resolution_depth", "unresolved_tokens",
]
STG_QUALITY_COLUMNS = [
    "run_id", "data_center", "folder_id", "job_id", "var_total",
    "var_resolved", "cmd_present", "cmd_classified", "invocation_count",
    "file_ref_count", "unresolved_tokens", "notes",
]


def _row(folder: str, job: str, name: str, value: str, scope: str | None = None):
    return ControlMVariableRow.model_validate(
        {"table_name": folder, "job_id": job, "name": name, "value": value,
         **({"var_scope": scope} if scope else {})}
    )


def test_collect_jobs_header_heuristic_and_order() -> None:
    rows = [
        _row("100", "1", "%%DROPBOX", "/d"),
        _row("100", "2", "%%A", "1"),
        _row("100", "2", "%%A", "2"),  # duplicate preserved, in order
    ]
    jobs = collect_jobs(rows)
    header = jobs[("UNKNOWN", "100", "1")]
    assert header.is_folder_header
    job = jobs[("UNKNOWN", "100", "2")]
    assert not job.is_folder_header
    assert job.defs == [("%%A", "1"), ("%%A", "2")]


def test_var_scope_column_overrides_heuristic() -> None:
    rows = [_row("100", "5", "%%X", "1", scope="FOLDER")]
    jobs = collect_jobs(rows)
    assert jobs[("UNKNOWN", "100", "5")].is_folder_header


def test_staging_rows_match_ddl_columns() -> None:
    jobs = collect_jobs([
        _row("100", "1", "%%DROPBOX", "/d"),
        _row("100", "2", "%%PATH", "%%DROPBOX/f_%%$ODATE.dat"),
    ])
    var_rows, q_rows = build_staging_rows(jobs, "run-1")
    assert all(list(r.keys()) == STG_VARIABLE_COLUMNS for r in var_rows)
    assert all(list(r.keys()) == STG_QUALITY_COLUMNS for r in q_rows)


def test_job_resolves_under_folder_scope() -> None:
    jobs = collect_jobs([
        _row("100", "1", "%%DROPBOX", "/d"),
        _row("100", "2", "%%PATH", "%%DROPBOX/f_%%$ODATE.dat"),
    ])
    var_rows, q_rows = build_staging_rows(jobs, "run-1")
    by_job = {(r["job_id"], r["var_name"]): r for r in var_rows}
    path = by_job[("2", "%%PATH")]
    assert path["resolved_value"] == "/d/f_{ODATE}.dat"
    assert path["is_fully_resolved"] == "Y"
    assert path["var_scope"] == "JOB"
    assert by_job[("1", "%%DROPBOX")]["var_scope"] == "FOLDER"
    q = {r["job_id"]: r for r in q_rows}
    assert q["2"]["var_total"] == 1
    assert q["2"]["var_resolved"] == 1


def test_unresolved_tokens_and_quality_rollup() -> None:
    jobs = collect_jobs([_row("100", "3", "%%X", "%%RUNTIME_ONLY")])
    var_rows, q_rows = build_staging_rows(jobs, "run-1")
    assert var_rows[0]["is_fully_resolved"] == "N"
    assert var_rows[0]["unresolved_tokens"] == "RUNTIME_ONLY"
    assert q_rows[0]["var_resolved"] == 0
    assert q_rows[0]["unresolved_tokens"] == "RUNTIME_ONLY"


def test_env_variant_extra_rows() -> None:
    jobs = collect_jobs([
        _row("100", "1", "%%SCRIPT_PATH_D", "/apps/dev"),
        _row("100", "1", "%%SCRIPT_PATH_Q", "/apps/qa"),
        _row("100", "1", "%%SCRIPT_PATH_P", "/apps/prod"),
        _row("100", "4", "%%SCRIPT_PATH", "%%SCRIPT_PATH_%%HOSTNM"),
    ])
    var_rows, _ = build_staging_rows(jobs, "run-1")
    script = [r for r in var_rows if r["var_name"] == "%%SCRIPT_PATH"]
    base = [r for r in script if r["env_tag"] is None]
    variants = {r["env_tag"]: r for r in script if r["env_tag"]}
    assert len(base) == 1 and base[0]["is_fully_resolved"] == "N"
    assert variants["D"]["resolved_value"] == "/apps/dev"
    assert variants["P"]["resolved_value"] == "/apps/prod"
    assert variants["D"]["is_fully_resolved"] == "Y"
    # variant rows share the base row's ordinal (same source definition)
    assert {r["src_ordinal"] for r in script} == {base[0]["src_ordinal"]}


def test_sample_end_to_end_counts() -> None:
    with CsvAdapter(SAMPLE) as adapter:
        rows = [ControlMVariableRow.model_validate(r) for r in adapter.rows()]
    jobs = collect_jobs(rows)
    var_rows, q_rows = build_staging_rows(jobs, "run-sample")
    # one quality row per job; >= one stg row per definition (variants add more)
    assert len(q_rows) == len(jobs) == 82
    assert sum(r["var_total"] for r in q_rows) == 323
    assert len(var_rows) >= 323
    # invariant: every fully-resolved row has no %% left
    for r in var_rows:
        assert (("%%" not in (r["resolved_value"] or ""))
                == (r["is_fully_resolved"] == "Y"))
