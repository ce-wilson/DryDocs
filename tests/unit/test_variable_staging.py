"""Unit tests for the STG_* staging-row builder (Phase A output side)."""
from __future__ import annotations

from pathlib import Path

import pytest

from drydocs.adapters.csv_adapter import CsvAdapter
from drydocs.controlm.staging import (
    build_staging_bundle,
    build_staging_rows,
    collect_jobs,
)
from drydocs.models import ControlMVariableRow

SAMPLE = (
    Path(__file__).resolve().parents[2]
    / "drydocs" / "data" / "samples" / "controlm_variables__sample.csv"
)

# Gitignored production extract — skip (don't fail) the sample-backed tests
# where it is absent, so the suite is green on any clone. Inline cases above
# cover staging routing deterministically without it.
requires_sample = pytest.mark.skipif(
    not SAMPLE.exists(),
    reason="production sample CSV absent (gitignored); regenerate locally via psgmgr",
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


# every column of the Phase-C tables, in DDL order (minus identity PK)
STG_INVOCATION_COLUMNS = [
    "run_id", "data_center", "folder_id", "job_id", "seq",
    "invocation_source", "invocation_type", "executable_path",
    "script_path", "config_path", "args_json", "raw_command",
    "is_classified", "classifier_rule",
]
STG_FILE_OP_COLUMNS = [
    "run_id", "data_center", "folder_id", "job_id", "seq", "op_type",
    "src_pattern", "tgt_pattern", "source_field", "raw_statement",
]
STG_APP_FACT_COLUMNS = [
    "run_id", "data_center", "folder_id", "job_id", "fact_type",
    "fact_value", "environment", "source_var",
]


def test_bundle_routes_shell_to_invocation_and_file_ops() -> None:
    jobs = collect_jobs([
        _row("100", "2", "%%POSTCMD",
             "sh /x/run_data_validation.sh TBL,{ODATE},YES; mv a b"),
    ])
    bundle = build_staging_bundle(jobs, "run-1")
    assert list(bundle.invocation[0].keys()) == STG_INVOCATION_COLUMNS
    assert bundle.invocation[0]["invocation_type"] == "VALIDATION_UTIL"
    assert list(bundle.file_op[0].keys()) == STG_FILE_OP_COLUMNS
    assert bundle.file_op[0]["op_type"] == "MOVE"
    q = bundle.parse_quality[0]
    assert q["cmd_present"] == "Y" and q["cmd_classified"] == "Y"


def test_bundle_routes_facts_and_notifications() -> None:
    jobs = collect_jobs([
        _row("100", "2", "%%SEAL", "34544"),
        _row("100", "2", "%%NOTIFY", "a@x.com;b@x.com"),
    ])
    bundle = build_staging_bundle(jobs, "run-1")
    assert list(bundle.app_fact[0].keys()) == STG_APP_FACT_COLUMNS
    assert bundle.app_fact[0]["fact_type"] == "SEAL"
    assert len(bundle.notification) == 2


def test_bundle_routes_filewatch_path() -> None:
    jobs = collect_jobs([
        _row("100", "2", "%%FileWatch-FILE_PATH",
             "/data/dropbox/RPM/tbl_{ODATE}.dat"),
    ])
    bundle = build_staging_bundle(jobs, "run-1")
    assert bundle.file_ref[0]["ref_role"] == "WATCH_INPUT"
    assert bundle.file_ref[0]["date_token"] == "{ODATE}"


@requires_sample
def test_sample_bundle_smoke() -> None:
    with CsvAdapter(SAMPLE) as adapter:
        rows = [ControlMVariableRow.model_validate(r) for r in adapter.rows()]
    bundle = build_staging_bundle(collect_jobs(rows), "run-sample")
    # all invocations classified or routed (no UNKNOWN leakage from the sample)
    assert all(i["invocation_type"] != "UNKNOWN" for i in bundle.invocation)
    # facts + notifications + file refs all present
    assert bundle.app_fact and bundle.notification and bundle.file_ref
    assert any(i["invocation_type"] == "VALIDATION_UTIL" for i in bundle.invocation)
    assert any(i["invocation_type"] == "PYTHON" for i in bundle.invocation)


@requires_sample
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
