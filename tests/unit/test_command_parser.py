"""Unit tests for the Phase-C command parser, path classifier, and fact
routing. Scenarios transcribed from real production rows.
"""

from __future__ import annotations

from drydocs_core.orchestration.controlm.facts import route_fact

# S2 (ADR 0008): the parser is neutral (orchestration.shell); the UCM container
# override is a Control-M FIELD shape, so it moved to controlm.fields with the
# rest of the vendor half. The path functions here are the neutral ones bound to
# the Control-M PathDialect — same behavior, vendor knowledge in the vendor dir.
from drydocs_core.orchestration.controlm.fields import extract_container_command
from drydocs_core.orchestration.controlm.paths import (
    build_file_ref,
    canonicalize_path,
    classify_role,
)
from drydocs_core.orchestration.controlm.variables import classify_variable
from drydocs_core.orchestration.shell import (
    classify_executable,
    parse_command,
    split_statements,
)

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
    assert classify_executable("loan_trn_bur_misop.m") == ("ABINITIO", "abinitio.graph_or_plan")


def test_classify_validation_util() -> None:
    assert (
        classify_executable("/home/b02supp/xmtr_scripts/run_data_validation.sh")[0]
        == "VALIDATION_UTIL"
    )


def test_classify_python_and_unknown() -> None:
    assert classify_executable("/apps/anaconda/4.6.14/3/bin/python3")[0] == "PYTHON"
    assert classify_executable("/some/weird/binary")[0] == "UNKNOWN"


# --- invocation parsing (real PRECMD/POSTCMD) ---------------------------------


def test_postcmd_validation_util_invocation() -> None:
    # real: folder 188252 job 2
    cmd = (
        "sh /home/b02supp/xmtr_scripts/run_calp_temp.sh "
        "bb_bureau_fsh_stg_experian_all_monthly_and.m {ODATE},2,Y,NO"
    )
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
    cmd = (
        "mkdir -p /apps/serial/VPC_P_VMSTR_BAL_{ODATE}/backup; "
        "cp /apps/serial/backup/* /apps/serial/VPC/; "
        "rm -f /home/optsld/p/VMSTR.rec"
    )
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


def test_gzip_is_compress_with_derived_twin() -> None:
    # the 2026-07-15 gate-caveat form: pure unix file ops (move, gzip), no ETL
    # engine involved (G14)
    parsed = parse_command("mv /data/out/loans.dat /data/arch/loans.dat; gzip /data/arch/loans.dat")
    mv = next(o for o in parsed.file_ops if o.op_type == "MOVE")
    assert (mv.src_pattern, mv.tgt_pattern) == (
        "/data/out/loans.dat",
        "/data/arch/loans.dat",
    )
    gz = next(o for o in parsed.file_ops if o.op_type == "COMPRESS")
    assert gz.src_pattern == "/data/arch/loans.dat"
    # gzip rewrites in place on a deterministic name contract — the .gz twin
    # is derived so lineage sees both sides of the flow
    assert gz.tgt_pattern == "/data/arch/loans.dat.gz"


def test_gunzip_strips_the_gz_twin() -> None:
    gz = parse_command("gunzip /data/in/feed.csv.gz").file_ops[0]
    assert gz.op_type == "COMPRESS"
    assert gz.src_pattern == "/data/in/feed.csv.gz"
    assert gz.tgt_pattern == "/data/in/feed.csv"


def test_gzip_to_stdout_has_no_derived_target() -> None:
    # -c streams to stdout — no in-place twin exists, so no target is invented
    gz = parse_command("gzip -c /data/x.dat").file_ops[0]
    assert gz.op_type == "COMPRESS"
    assert gz.src_pattern == "/data/x.dat"
    assert gz.tgt_pattern is None


def test_assignment_and_noop_skipped() -> None:
    parsed = parse_command("ft_nm= ls -1rt FIRM_*.dat; cd /tmp; echo done")
    # ls after an assignment, cd, echo -> all no-ops, no invocations/ops
    assert parsed.invocations == []
    assert parsed.file_ops == []


# --- container override extraction (real UCM) ---------------------------------


def test_extract_container_command() -> None:
    # real: folder 185675
    value = (
        "containerOverrides:{ command: /bin/sh, -c, "
        "python /app/app.py --job_name SURVEY --order_id 123 }"
    )
    inner = extract_container_command(value)
    assert inner is not None
    assert inner.startswith("python /app/app.py")
    parsed = parse_command(inner)
    assert parsed.invocations[0].invocation_type == "PYTHON"
    assert parsed.invocations[0].script_path == "/app/app.py"


def test_environment_only_override_has_no_command() -> None:
    # real: folder 179833 — environment array, no command
    value = (
        "containerOverrides:{environment:[{name:TABLE_NAME,value:custcore},"
        "{name:FRM_DT,value:{ODATE}}]}"
    )
    assert extract_container_command(value) is None


# --- path canonicalization + role classification ------------------------------


def test_canonicalize_timestamp_wildcard() -> None:
    assert (
        canonicalize_path("/apps/dropbox/CMS_IDW_SCRA_Reporting_????????????????.dat")
        == "/apps/dropbox/CMS_IDW_SCRA_Reporting_{TS16}.dat"
    )


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
    cv = classify_variable("%%SEAL", "70004")
    facts, notes = route_fact(cv, "70004")
    assert notes == []
    assert facts[0].fact_type == "SEAL"
    assert facts[0].fact_value == "70004"


def test_route_notification_splits_addresses() -> None:
    cv = classify_variable(
        "%%NOTIFY",
        "APP_L2_Production_Support@example.com;Team_Night_Herons@example.com",
    )
    facts, notes = route_fact(cv, cv.raw_value)
    assert facts == []
    assert len(notes) == 2
    assert all(n.channel == "EMAIL" for n in notes)


def test_fid_env_triplet_carries_environment() -> None:
    from drydocs_core.orchestration.controlm.variables import classify_job_variables

    out = {
        cv.name: cv
        for cv in classify_job_variables(
            [("%%FID_D", "B0001"), ("%%FID_Q", "H0002"), ("%%FID_P", "K0003")]
        )
    }
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
    """Equivalence with depgraph's test_controlm.py on the depgraph-era 13-job
    sample, extended by the four D6 rows (2026-07-18: folders 161020/160501
    gained jobs so the m3-verify empty-folder invariant passes on samples):
    17 INVOKES; 10 abinitio .pset + 7 shell .ksh (6 distinct) -> 16 distinct
    children + 17 jobs = 33 processes."""
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
    assert len(invocations) == 17  # 17 INVOKES
    assert all(inv.is_classified for inv in invocations)  # no UNKNOWN left
    by_type: dict[str, int] = {}
    for inv in invocations:
        by_type[inv.invocation_type] = by_type.get(inv.invocation_type, 0) + 1
    assert by_type == {"ABINITIO": 10, "SHELL_SCRIPT": 7}
    distinct_children = {inv.script_path for inv in invocations}
    assert len(distinct_children) == 16  # + 17 jobs = 33 processes


def test_invocation_target_prefers_script_then_executable() -> None:
    """`target` (folded from the depgraph prototype, ADR 0002-C §3) keys lineage
    child nodes: script wins, executable is the fallback, raw statement last."""
    from drydocs_core.orchestration.controlm import parse_command

    spark = parse_command(
        "spark-submit --master yarn /opt/spark/refine_loans.py --date {ODATE}"
    ).invocations[0]
    assert spark.target == "/opt/spark/refine_loans.py"  # script wins over exe
    mod = parse_command("python -m mypkg.run").invocations[0]
    assert mod.target == "mypkg.run"


# --- live-pattern coverage (SME session 2026-07-16, gate-log cmdline-lineage- --
# review). Sanitized mechanism-twins of three production command shapes: the
# abioncloud wrapper, the DPL java launcher, and a compound if/else command.


def test_compound_if_else_surfaces_all_invocations() -> None:
    """`ksh check; if…else sh wrapper…;fi` — the else-prefixed statement carries
    the MAIN invocation; control keywords must not swallow it, and the wrapper's
    -g pset payload (plus its nested -run_prog_command_line script) must surface."""
    cmd = (
        "ksh /data/sandboxes/app/bin/etl_ctl_file_check.ksh 20260101 team@example.com ; "
        "if [[ $? > 0 ]]; then exit 1;"
        "else sh /apps/wrapper/script/runScript.sh -c /cfg/app-unld-config.json "
        "-f F000000 -e prod -a img -p TAG "
        '-g "/home/svc/pset/ctl_script_exec_send_email.pset -KSH_EXEC_FLAG Y '
        "-run_prog_command_line /home/svc/bin/etl_ctl_file_check.ksh "
        '-TO_MAIL team@example.com" -s 30 -t 3600 -r large;fi'
    )
    parsed = parse_command(cmd)
    assert parsed.unparsed == []  # nothing UNKNOWN
    got = [(i.invocation_type, i.script_path) for i in parsed.invocations]
    assert got == [
        ("SHELL_SCRIPT", "/data/sandboxes/app/bin/etl_ctl_file_check.ksh"),
        ("ABINITIO", "/home/svc/pset/ctl_script_exec_send_email.pset"),
        ("SHELL_SCRIPT", "/home/svc/bin/etl_ctl_file_check.ksh"),
    ]
    # the wrapper stays visible as the executable behind the pset invocation
    wrapper = parsed.invocations[1]
    assert wrapper.executable_path.endswith("runScript.sh")
    assert wrapper.classifier_rule == "abioncloud.runscript_wrapper.pset_payload"
    assert wrapper.config_path == "/cfg/app-unld-config.json"


def test_wrapper_pset_payload_standard_shape() -> None:
    """The standard team pattern: runScript.sh (case-insensitive match) with the
    pset in -g. Without payload expansion every wrapper job collapses onto the
    same wrapper node."""
    cmd = (
        "sh /apps/wrapper/script/runScript.sh -c /cfg/app-config.json -f F000000 "
        '-e prod -a img -p TAG -g "/home/svc/pset/table_ingestion_sf.pset '
        '-AB_EXPECTED_RECORD_MBYTES 70" -s 30 -t 3600 -r large'
    )
    (inv,) = parse_command(cmd).invocations
    assert inv.invocation_type == "ABINITIO"
    assert inv.script_path == "/home/svc/pset/table_ingestion_sf.pset"
    assert inv.target == "/home/svc/pset/table_ingestion_sf.pset"


def test_dpl_pipelines_launcher_jar_classifies_dpl() -> None:
    """java -jar dt-pipelines-launcher…jar re-classifies from generic JAVA to DPL
    (DPL is NOT Ab Initio — SME 2026-07-16); config JSON captured."""
    cmd = (
        "java -Djava.io.tmpdir=/tmp/svc -jar -Dspring.profiles.active=prod "
        "/apps/tenants/dpl_utils/dt-accelerators/dt-pipelines-launcher-current.jar "
        "-pipeline 00000000-0000-0000-0000-000000000000 -appName app-prod "
        "-dataflow DATASET_NM -conf /cfg/epv-conf.json"
    )
    (inv,) = parse_command(cmd).invocations
    assert inv.invocation_type == "DPL"
    assert inv.classifier_rule == "dpl.pipelines_launcher_jar"
    assert inv.script_path.endswith("dt-pipelines-launcher-current.jar")
    assert inv.config_path == "/cfg/epv-conf.json"


def test_dt_launcher_sh_classifies_dpl_both_spellings() -> None:
    for launcher in ("dt-launcher.sh", "dtlaunch.sh"):
        (inv,) = parse_command(
            f"sh /apps/tenants/dpl_utils/dt-accelerators/{launcher} -py job_conf"
        ).invocations
        assert inv.invocation_type == "DPL", launcher
        assert inv.classifier_rule == "dpl.dt_launcher_accelerator"


def test_generic_java_jar_stays_java() -> None:
    (inv,) = parse_command("java -jar /apps/thing/tool.jar -x 1").invocations
    assert inv.invocation_type == "JAVA"
    assert inv.script_path == "/apps/thing/tool.jar"
    assert inv.target == "/apps/thing/tool.jar"


def test_air_sandbox_run_classifies_abinitio() -> None:
    (inv,) = parse_command("air sandbox run /sandbox/project/mygraph.pset").invocations
    assert inv.invocation_type == "ABINITIO"
    assert inv.classifier_rule == "abinitio.air_cli"
    assert inv.script_path == "/sandbox/project/mygraph.pset"
