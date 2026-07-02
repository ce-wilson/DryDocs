"""Unit tests for the Phase-C command parser, path classifier, and fact
routing. Scenarios transcribed from real production rows.
"""
from __future__ import annotations

from drydocs.controlm.commands import (
    classify_executable,
    extract_container_command,
    parse_command,
    split_statements,
)
from drydocs.controlm.facts import route_fact
from drydocs.controlm.paths import build_file_ref, canonicalize_path, classify_role
from drydocs.controlm.variables import classify_variable

# --- statement splitting ------------------------------------------------------

def test_split_respects_quotes() -> None:
    stmts = split_statements("echo 'a;b'; mv x y; rm z")
    assert stmts == ["echo 'a;b'", "mv x y", "rm z"]


def test_split_on_pipe_and_andand() -> None:
    assert split_statements("a | b && c") == ["a", "b", "c"]


def test_strip_fully_enclosing_quotes_then_split() -> None:
    # real shape: folder 161947 wraps the whole shell string in double quotes
    stmts = split_statements('"cc /tmp/pp; sed s/x/y/ f > g; mv g f"')
    assert stmts == ["cc /tmp/pp", "sed s/x/y/ f > g", "mv g f"]


def test_inner_quotes_not_stripped() -> None:
    # two separate quoted spans must NOT be treated as one enclosure
    assert split_statements("'a;b' ; 'c'") == ["'a;b'", "'c'"]


# --- launcher registry --------------------------------------------------------

def test_classify_abinitio_graph() -> None:
    assert classify_executable("loan_trn_bur_misop.m") == (
        "ABINITIO", "abinitio.graph_or_plan")


def test_classify_validation_util() -> None:
    assert classify_executable("/home/b02supp/xmtr_scripts/run_data_validation.sh")[0] \
        == "VALIDATION_UTIL"


def test_classify_python_and_unknown() -> None:
    assert classify_executable("/apps/anaconda/4.6.14/3/bin/python3")[0] == "PYTHON"
    assert classify_executable("/some/weird/binary")[0] == "UNKNOWN"


# --- invocation parsing (real PRECMD/POSTCMD) ---------------------------------

def test_postcmd_validation_util_invocation() -> None:
    # real: folder 188252 job 2
    cmd = ("sh /home/b02supp/xmtr_scripts/run_calp_temp.sh "
           "bb_bureau_fsh_stg_experian_all_monthly_and.m {ODATE},2,Y,NO")
    parsed = parse_command(cmd)
    assert len(parsed.invocations) == 1
    inv = parsed.invocations[0]
    assert inv.invocation_type == "VALIDATION_UTIL"
    assert inv.script_path.endswith("run_calp_temp.sh")
    # the Ab Initio graph rides as an argument and is surfaced
    assert inv.args[0].endswith("_and.m")
    assert inv.is_classified


def test_precmd_mkdir_and_copy_file_ops() -> None:
    # real: folder 161947 job 12 (PRECMD pair)
    cmd = ("mkdir -p /apps/serial/VPC_P_VMSTR_BAL_{ODATE}/backup; "
           "cp /apps/serial/backup/* /apps/serial/VPC/; "
           "rm -f /home/optsld/p/VMSTR.rec")
    parsed = parse_command(cmd)
    ops = {op.op_type for op in parsed.file_ops}
    assert ops == {"MKDIR", "COPY", "DELETE"}
    cp = next(o for o in parsed.file_ops if o.op_type == "COPY")
    assert cp.src_pattern.endswith("/backup/*")
    assert cp.tgt_pattern.endswith("/VPC/")


def test_sed_pipeline_is_transform() -> None:
    # real: folder 161947 — sed cleanup pipeline
    cmd = "sed -e 's/ex/g' $ft_nm | sed 's/a0//g' > out; mv out in"
    parsed = parse_command(cmd)
    assert any(o.op_type == "TRANSFORM" for o in parsed.file_ops)
    assert any(o.op_type == "MOVE" for o in parsed.file_ops)


def test_assignment_and_noop_skipped() -> None:
    parsed = parse_command("ft_nm= ls -1rt FIRM_*.dat; cd /tmp; echo done")
    # ls after an assignment, cd, echo -> all no-ops, no invocations/ops
    assert parsed.invocations == []
    assert parsed.file_ops == []


# --- container override extraction (real UCM) ---------------------------------

def test_extract_container_command() -> None:
    # real: folder 185675
    value = ("containerOverrides:{ command: /bin/sh, -c, "
             "python /app/app.py --job_name SURVEY --order_id 123 }")
    inner = extract_container_command(value)
    assert inner is not None
    assert inner.startswith("python /app/app.py")
    parsed = parse_command(inner)
    assert parsed.invocations[0].invocation_type == "PYTHON"
    assert parsed.invocations[0].script_path == "/app/app.py"


def test_environment_only_override_has_no_command() -> None:
    # real: folder 179833 — environment array, no command
    value = ("containerOverrides:{environment:[{name:TABLE_NAME,value:custcore},"
             "{name:FRM_DT,value:{ODATE}}]}")
    assert extract_container_command(value) is None


# --- path canonicalization + role classification ------------------------------

def test_canonicalize_timestamp_wildcard() -> None:
    assert canonicalize_path(
        "/apps/dropbox/CMS_IDW_SCRA_Reporting_????????????????.dat"
    ) == "/apps/dropbox/CMS_IDW_SCRA_Reporting_{TS16}.dat"


def test_role_classification() -> None:
    assert classify_role("DROPBOX") == "DROPBOX"
    assert classify_role("BACKUP_DIR") == "BACKUP"
    assert classify_role("CONFIG_JSON") == "CONFIG"
    assert classify_role("APPL_LOG") == "LOG"
    assert classify_role("SOME_INPUT_FILE") in {"INPUT", "OUTPUT"}


def test_build_file_ref_from_dropbox_path() -> None:
    ref = build_file_ref(
        "DROPBOX",
        "/apps/dropbox_cards/cdw_non-core_interfaces/dropbox/PTRX/MANTAS/",
        source_field="%%DROPBOX",
    )
    assert ref is not None
    assert ref.ref_role == "DROPBOX"
    assert ref.directory_path is not None


def test_build_file_ref_rejects_non_path() -> None:
    assert build_file_ref("X", "prod", source_field="%%X") is None
    assert build_file_ref("X", "a@b.com", source_field="%%X") is None


def test_filewatch_path_gets_watch_role_and_date_token() -> None:
    ref = build_file_ref(
        "FileWatch-FILE_PATH",
        "/data/uds/dropbox/RPM/tbl_options_{ODATE}.dat",
        source_field="%%FileWatch-FILE_PATH",
        role="WATCH_INPUT",
    )
    assert ref.ref_role == "WATCH_INPUT"
    assert ref.date_token == "{ODATE}"


# --- fact / notification routing ----------------------------------------------

def test_route_semantic_fact() -> None:
    cv = classify_variable("%%SEAL", "34544")
    facts, notes = route_fact(cv, "34544")
    assert notes == []
    assert facts[0].fact_type == "SEAL"
    assert facts[0].fact_value == "34544"


def test_route_notification_splits_addresses() -> None:
    cv = classify_variable(
        "%%NOTIFY",
        "CDW_L2_Production_Support@restricted.chase.com;Team_Data_Pirates@restricted.chase.com",
    )
    facts, notes = route_fact(cv, cv.raw_value)
    assert facts == []
    assert len(notes) == 2
    assert all(n.channel == "EMAIL" for n in notes)


def test_fid_env_triplet_carries_environment() -> None:
    from drydocs.controlm.variables import classify_job_variables
    out = {cv.name: cv for cv in classify_job_variables(
        [("%%FID_D", "B0001"), ("%%FID_Q", "H0002"), ("%%FID_P", "K0003")]
    )}
    facts, _ = route_fact(out["FID_P"], "K0003")
    assert facts[0].fact_type == "FID"
    assert facts[0].environment == "P"


# --- G8: depgraph parser-delta fold (ADR 0002-C §3) -----------------------------

def test_pset_classified_abinitio() -> None:
    itype, rule = classify_executable("/opt/scripts/hldm/trust.pset")
    assert itype == "ABINITIO"
    assert rule == "abinitio.pset"


def test_pset_direct_script_path() -> None:
    inv = parse_command("/opt/scripts/hldm/trust.pset").invocations
    assert len(inv) == 1
    assert inv[0].invocation_type == "ABINITIO"
    assert inv[0].script_path == "/opt/scripts/hldm/trust.pset"


def test_spark_submit_skips_option_values() -> None:
    # regression: the real script is the .py, NOT `yarn` (value of --master)
    inv = parse_command(
        "spark-submit --master yarn /opt/spark/refine_loans.py --date {ODATE}"
    ).invocations
    assert inv[0].invocation_type == "PYSPARK"
    assert inv[0].script_path == "/opt/spark/refine_loans.py"


def test_python_dash_m_module_falls_back_to_bare_arg() -> None:
    inv = parse_command("python -m mypkg.run").invocations
    assert inv[0].invocation_type == "PYTHON"
    assert inv[0].script_path == "mypkg.run"


def test_sample_reproduces_depgraph_oracle() -> None:
    """Equivalence with depgraph's test_controlm.py on the 13-job sample:
    13 INVOKES; 8 abinitio .pset + 5 shell .ksh (4 distinct) -> 12 distinct
    children + 13 jobs = 25 processes."""
    import csv
    from pathlib import Path

    import pytest

    sample = Path("drydocs/data/samples/controlm_jobs__sample.csv")
    if not sample.exists():
        pytest.skip("gitignored production sample not present")
    rows = list(csv.DictReader(sample.open(encoding="utf-8-sig")))
    invocations = []
    for row in rows:
        parsed = parse_command(row["cmd_line"])
        assert len(parsed.invocations) == 1, row["cmd_line"]
        invocations.append(parsed.invocations[0])
    assert len(invocations) == 13  # 13 INVOKES
    assert all(inv.is_classified for inv in invocations)  # no UNKNOWN left
    by_type: dict[str, int] = {}
    for inv in invocations:
        by_type[inv.invocation_type] = by_type.get(inv.invocation_type, 0) + 1
    assert by_type == {"ABINITIO": 8, "SHELL_SCRIPT": 5}
    distinct_children = {inv.script_path for inv in invocations}
    assert len(distinct_children) == 12  # + 13 jobs = 25 processes
