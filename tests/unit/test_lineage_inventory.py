"""G9 re-home oracle — the depgraph prototype's own tests, ported onto the re-homed
component (ADR 0002-C §5 "parser equivalence" + extractor behavior).

The fixture is the prototype's SYNTHETIC 5-row twin (shape-faithful, value-fake:
jdoe/svc.hldm/generic hosts+paths). The parser cases double as the §3/G8 fold
regression: the CORE parser must reproduce what depgraph's fork asserted —
.pset → ABINITIO and spark-submit skipping option values are the folded deltas.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_core.orchestration.controlm import parse_command
from drydocs_lineage.extractors import ControlMInventoryExtractor
from drydocs_lineage.model import REL_ALIASES, REL_TYPES, LineageGraph

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "lineage" / "jobs.csv"


# -- parser equivalence (0002-C §3/G8 — the core parser IS depgraph's, unified) ----


def test_plain_script_path() -> None:
    inv = parse_command("/opt/scripts/hldm/onpm_fw.ksh").invocations
    assert len(inv) == 1
    assert inv[0].invocation_type == "SHELL_SCRIPT"
    assert inv[0].target == "/opt/scripts/hldm/onpm_fw.ksh"


def test_pset_is_abinitio() -> None:
    inv = parse_command("/opt/scripts/hldm/trust.pset").invocations
    assert inv[0].invocation_type == "ABINITIO"


def test_spark_submit_skips_option_values() -> None:
    # the real script is the .py, NOT `yarn` (value of --master) — the G8 bug fix
    inv = parse_command(
        "spark-submit --master yarn /opt/spark/refine_loans.py --date {ODATE}"
    ).invocations
    assert inv[0].invocation_type == "PYSPARK"
    assert inv[0].target == "/opt/spark/refine_loans.py"


def test_python_dash_m_module() -> None:
    inv = parse_command("python -m mypkg.run").invocations
    assert inv[0].invocation_type == "PYTHON"
    assert inv[0].target == "mypkg.run"


# -- extractor behavior (ported expectations, verbatim semantics) ------------------


@pytest.fixture()
def graph() -> LineageGraph:
    g = LineageGraph()
    ControlMInventoryExtractor().extract(FIXTURE, g)
    return g


def test_counts(graph: LineageGraph) -> None:
    kinds = [p.kind for p in graph.processes.values()]
    # 4 current jobs (1 stale is_current_version=N skipped) + 3 children
    assert kinds.count("controlm_job") == 4
    assert len(graph.processes) == 7
    assert len(graph.rels) == 4


def test_stale_version_skipped(graph: LineageGraph) -> None:
    names = {p.name for p in graph.processes.values()}
    assert "old_fw.ksh" not in names  # is_current_version=N


def test_field_mapping(graph: LineageGraph) -> None:
    job = next(p for p in graph.processes.values() if p.name == "PEX_SPARK_REFINE")
    assert (
        job.node_target == "host-emr-01"
    )  # node_id -> node_target (host-or-group; gate controlm-hosts-topology)
    assert job.run_as == "svc.hldm"  # owner -> run_as
    assert job.application == "ARA"
    assert job.folder.startswith("PRARAG-HLDM-70014")


def test_shared_script_collapses(graph: LineageGraph) -> None:
    # onpm_fw.ksh is invoked by jobs in two folders -> one node, two INVOKES
    shell = [p for p in graph.processes.values() if p.name == "onpm_fw.ksh"]
    assert len(shell) == 1
    into_shell = [r for r in graph.rels if r[2] == shell[0].node_id]
    assert len(into_shell) == 2
    assert all(r[1] == "INVOKES" for r in into_shell)


# -- ontology reconcile (0002-C §4 identity/vocabulary rules) ----------------------


def test_rel_vocabulary_is_the_registered_set() -> None:
    # USES_ARTIFACT joined at G97 — gate cmdline-nfr-vetting SME-2 (2026-07-21)
    # registered it as a DISTINCT label rather than a role on INVOKES, and
    # rua-load-shapes §A4 activated it. REL_ALIASES is deliberately untouched:
    # the payload label is new vocabulary, not a prototype spelling.
    assert REL_TYPES == {"INVOKES", "TRIGGERS", "READS_FROM", "WRITES_TO", "USES_ARTIFACT"}
    # prototype spellings normalize on entry, never leak into the graph
    g = LineageGraph()
    g.processes  # noqa: B018
    g.add_rel("proc#a:1", "READS", "data#b:2")
    assert g.rels == {("proc#a:1", "READS_FROM", "data#b:2")}
    assert REL_ALIASES == {"READS": "READS_FROM", "WRITES": "WRITES_TO"}


def test_legacy_host_key_normalizes_to_node_target() -> None:
    """Prototype exports (and pre-rename v1 files) carry `host`; from_dict must
    normalize it to node_target — the polymorphic NODE_ID target (gate
    controlm-hosts-topology: host GROUP in the common case, not a server)."""
    from drydocs_lineage.model import LineageGraph

    g = LineageGraph.from_dict(
        {
            "schema": "depgraph-machine-first/v2",
            "processes": [
                {
                    "node_id": "proc#controlm_job:1.2",
                    "kind": "controlm_job",
                    "name": "J",
                    "host": "SOME-GROUP",
                    "project": "dropped",
                }
            ],
            "data_assets": [],
            "rels": [],
        }
    )
    job = g.processes["proc#controlm_job:1.2"]
    assert job.node_target == "SOME-GROUP"
    assert not hasattr(job, "host")


# -- coverage accounting (G11 — report every skip by reason, never drop silently) ---


def test_coverage_counts_pinned_on_fixture() -> None:
    g = LineageGraph()
    cov = ControlMInventoryExtractor().extract(FIXTURE, g)
    # 5 rows -> 4 current jobs + 1 stale skip; every current job has a parsed cmd
    assert cov.rows_read == 5
    assert cov.jobs_added == 4
    assert cov.skipped_stale_version == 1
    assert cov.skipped_nameless == 0
    assert cov.invocations_added == 4
    assert cov.invocations_unresolved == 0
    assert cov.invocations_no_target == 0
    assert cov.commands_empty == 0
    assert cov.commands_unparsed == 0


def test_coverage_reports_nameless_empty_and_unresolved(tmp_path) -> None:
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(
        "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"
        "1,10,JOB_EMPTY_CMD,F1,svc.x,h1,,Y\n"  # kept; empty command
        "2,10,,F1,svc.x,h1,/opt/x.sh,Y\n"  # nameless -> skipped
        "3,10,JOB_UNKNOWN,F1,svc.x,h1,mystery_bin,Y\n"  # UNKNOWN kind -> unresolved
        "4,10,JOB_STALE,F1,svc.x,h1,/opt/y.sh,N\n",  # stale -> skipped
        encoding="utf-8",
    )
    g = LineageGraph()
    cov = ControlMInventoryExtractor().extract(csv_path, g)
    assert cov.rows_read == 4
    assert cov.jobs_added == 2
    assert cov.skipped_nameless == 1
    assert cov.skipped_stale_version == 1
    assert cov.commands_empty == 1
    assert cov.invocations_added == 1
    assert cov.invocations_unresolved == 1  # mystery_bin classified UNKNOWN, still a candidate
    # the accounting is total: every row lands in exactly one row-level bucket
    assert cov.rows_read == (cov.jobs_added + cov.skipped_nameless + cov.skipped_stale_version)
    # dict view carries every counter (machine-readable for future STG_PARSE_QUALITY hookup)
    assert set(cov.as_dict()) >= {
        "rows_read",
        "jobs_added",
        "skipped_stale_version",
        "skipped_nameless",
        "commands_empty",
        "commands_unparsed",
        "invocations_added",
        "invocations_unresolved",
        "invocations_no_target",
    }
    assert "skipped: stale=1 nameless=1" in cov.summary()


def test_coverage_missing_source_is_all_zero(tmp_path) -> None:
    cov = ControlMInventoryExtractor().extract(tmp_path / "nope", LineageGraph())
    assert cov.rows_read == 0 and cov.jobs_added == 0


# -- file-ops candidates (G14 — the feed that activates G13's dormant resolution) --


def test_cmdline_move_gzip_emits_reads_writes_candidates(tmp_path) -> None:
    """The gate-caveat wrapper case (unix move/gzip, no ETL engine): CMD_LINE
    file ops become READS_FROM/WRITES_TO candidates with the JOB itself as the
    Activity (gate EDIT from_node: ControlMJob — no Script hop exists), and
    operand patterns become local_file DataAssets."""
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(
        "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"
        '22,161015,JOB_ARCHIVE,F1,svc.x,h1,"mv /data/out/loans.dat /data/arch/loans.dat; '
        'gzip /data/arch/loans.dat",Y\n',
        encoding="utf-8",
    )
    g = LineageGraph()
    cov = ControlMInventoryExtractor().extract(csv_path, g)
    jid = "proc#controlm_job:161015.22"
    # mv reads its src and writes its tgt; gzip reads the moved file and
    # writes the derived .gz twin
    assert (jid, "READS_FROM", "data#local_file:/data/out/loans.dat") in g.rels
    assert (jid, "WRITES_TO", "data#local_file:/data/arch/loans.dat") in g.rels
    assert (jid, "READS_FROM", "data#local_file:/data/arch/loans.dat") in g.rels
    assert (jid, "WRITES_TO", "data#local_file:/data/arch/loans.dat.gz") in g.rels
    assert cov.file_ops_added == 4
    # a pure file-op command line is PARSED, not "unparsed"
    assert cov.commands_unparsed == 0
    assert {a.location for a in g.data_assets.values()} == {
        "/data/out/loans.dat",
        "/data/arch/loans.dat",
        "/data/arch/loans.dat.gz",
    }
    assert all(a.kind == "local_file" for a in g.data_assets.values())


def test_non_dataflow_and_operandless_file_ops_are_counted_never_silent(tmp_path) -> None:
    """The coverage house rule on the file-ops pass: job mechanics (mkdir/rm)
    and malformed data-flow ops are skipped BY COUNTED REASON, never dropped
    silently — and none of them fabricate assets or rels."""
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(
        "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"
        '1,10,JOB_MECHANICS,F1,svc.x,h1,"mkdir -p /tmp/w; rm -f /tmp/w/x.log; '
        'mv /data/only_src.dat",Y\n',
        encoding="utf-8",
    )
    g = LineageGraph()
    cov = ControlMInventoryExtractor().extract(csv_path, g)
    assert cov.file_ops_added == 0
    assert cov.file_ops_skipped_non_dataflow == 2  # mkdir + rm: not lineage flow
    assert cov.file_ops_no_operand == 1  # mv with no target operand
    assert not g.data_assets
    assert not g.rels
    assert "file-ops: added=0 non_dataflow=2 no_operand=1" in cov.summary()


def test_no_parse_code_of_its_own() -> None:
    # 0002-C §5: lineage contains NO Control-M parse code (no LAUNCHER_REGISTRY,
    # no parse_command definition) — the parser is core's, full stop.
    import ast

    pkg = Path(__file__).resolve().parents[2] / "drydocs_lineage"
    offenders: list[str] = []
    for path in pkg.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "parse_command":
                offenders.append(f"{path.name}: defines parse_command")
            if isinstance(node, ast.Name) and node.id == "LAUNCHER_REGISTRY":
                offenders.append(f"{path.name}: LAUNCHER_REGISTRY")
    assert not offenders, offenders


def test_stable_invocation_keys_dpl_guid_and_pset_basename(tmp_path) -> None:
    """SME session 2026-07-16 (gate-log cmdline-lineage-review): process identity
    uses the env-stable token — DPL launches key by -pipeline GUID (the launcher
    jar is shared tooling), Ab Initio psets key by basename (the same graph sits
    at different sandbox mounts per env). Plain scripts stay PATH-keyed so
    multi-mount duplicates surface in review, never auto-merge."""
    csv_path = tmp_path / "jobs.csv"
    dpl_cmd = (
        "java -jar /apps/tenants/dpl_utils/dt-accelerators/dt-pipelines-launcher-current.jar"
        " -pipeline 00000000-0000-0000-0000-000000000000 -dataflow DS_NM -conf /cfg/c.json"
    )
    csv_path.write_text(
        "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"
        f'1,10,JOB_DPL,F1,svc.x,h1,"{dpl_cmd}",Y\n'
        '2,10,JOB_PSET_DEV,F1,svc.x,h1,"sh /apps/w/runScript.sh -g ""/dev/mnt/ing.pset -F 1""",Y\n'
        '3,10,JOB_PSET_PRD,F1,svc.x,h1,"sh /apps/w/runScript.sh -g ""/prd/mnt/ing.pset -F 1""",Y\n'
        "4,10,JOB_SH_A,F1,svc.x,h1,ksh /data/mnt/check.ksh,Y\n"
        "5,10,JOB_SH_B,F1,svc.x,h1,ksh /home/mnt/check.ksh,Y\n",
        encoding="utf-8",
    )
    g = LineageGraph()
    ControlMInventoryExtractor().extract(csv_path, g)
    child_ids = {pid for pid in g.processes if not pid.startswith("proc#controlm_job:")}
    assert child_ids == {
        "proc#dpl:00000000-0000-0000-0000-000000000000",  # GUID, not the jar path
        "proc#abinitio:ing.pset",  # basename: dev+prod converge
        "proc#shell_script:/data/mnt/check.ksh",  # scripts stay path-keyed:
        "proc#shell_script:/home/mnt/check.ksh",  # dupes surface for SME merge
    }
    # full paths retained as properties on the converged pset node
    assert g.processes["proc#abinitio:ing.pset"].path.endswith("ing.pset")


# -- DPL launcher argument contract (G15; gate cmdline-nfr-vetting evidence) -------

_GUID = "11111111-2222-3333-4444-555555555555"
_CSV_HEADER = "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"


def _extract(tmp_path, *rows: str):
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(_CSV_HEADER + "".join(rows), encoding="utf-8")
    g = LineageGraph()
    cov = ControlMInventoryExtractor().extract(csv_path, g)
    return g, cov


def test_onprem_launcher_and_both_guid_spellings_converge(tmp_path) -> None:
    """(a)+(b): the on-prem dpl_spark_processor spellings classify DPL alongside
    dt-launcher.sh, and BOTH pipeline-id flag spellings key the SAME ETLProcess
    identity — one workload node however it is launched."""
    g, _ = _extract(
        tmp_path,
        f'1,10,JOB_AWS,F1,svc.x,h1,"/apps/t/dt-accelerators/dt-launcher.sh -env D '
        f'-pipeline {_GUID} -i -conf /cfg/c.json",Y\n',
        f'2,10,JOB_ONPM,F1,svc.x,h1,"/apps/dpl/dpl_processor/bin/dpl_spark_processor '
        f'--pipeline-id {_GUID} --aws --queue-name q1",Y\n',
        f'3,10,JOB_ONPM_DYN,F1,svc.x,h1,"/apps/dpl/dpl_processor/bin/dpl_spark_processor_dynamic '
        f'--pipeline-id {_GUID} --spark-params x=y",Y\n',
    )
    children = {pid for pid in g.processes if not pid.startswith("proc#controlm_job:")}
    assert children == {f"proc#dpl:{_GUID}"}
    into_child = [r for r in g.rels if r[2] == f"proc#dpl:{_GUID}"]
    assert len(into_child) == 3
    assert g.processes[f"proc#dpl:{_GUID}"].kind == "dpl"


def test_unresolved_variable_launcher_still_yields_dpl_identity(tmp_path) -> None:
    """(c): an UNRESOLVED original whose executable is a folder variable
    (%%PY_LAUNCH / %%SCRIPT_PATH) still classifies DPL and keys on the
    -pipeline GUID — the only literal on the line — without crashing on the
    %%VAR tokens."""
    g, cov = _extract(
        tmp_path,
        f'1,10,JOB_UNRES,F1,svc.x,h1,"%%PY_LAUNCH -env %%ENV -pipeline {_GUID} '
        f'-appName %%APP_NAME -seal %%SEAL -i -conf %%CONF_PATH",Y\n',
    )
    node = g.processes[f"proc#dpl:{_GUID}"]
    assert node.kind == "dpl"
    assert cov.invocations_added == 1
    assert cov.invocations_unresolved == 0  # classified DPL, not UNKNOWN
    # unresolved %%VAR values are kept verbatim as candidate properties
    assert node.properties["app_name"] == "%%APP_NAME"
    assert node.properties["seal"] == "%%SEAL"


def test_mode_flags_are_a_property_never_a_kind(tmp_path) -> None:
    """(d): -i / -t / -py land as the launch_mode PROPERTY and all three stay
    kind=dpl — never a separate invocation_type."""
    guids = [f"00000000-0000-0000-0000-00000000000{n}" for n in (1, 2, 3)]
    g, _ = _extract(
        tmp_path,
        f'1,10,JOB_I,F1,svc.x,h1,"sh /a/dt-launcher.sh -pipeline {guids[0]} -i",Y\n',
        f'2,10,JOB_T,F1,svc.x,h1,"sh /a/dt-launcher.sh -pipeline {guids[1]} -t",Y\n',
        f'3,10,JOB_PY,F1,svc.x,h1,"sh /a/dt-launcher.sh -pipeline {guids[2]} -py",Y\n',
    )
    modes = {g.processes[f"proc#dpl:{guid}"].properties["launch_mode"] for guid in guids}
    assert modes == {"-i", "-t", "-py"}
    assert all(g.processes[f"proc#dpl:{guid}"].kind == "dpl" for guid in guids)


def test_definition_properties_captured_runtime_values_excluded(tmp_path) -> None:
    """(e): the observed definition-level params land as PROPERTIES (never
    identity — the node still keys on the GUID); runtime values (-bd/-od
    partition values, -proId per-run GUID, -timeout/-sleep tuning) are
    deliberately excluded."""
    g, _ = _extract(
        tmp_path,
        f'1,10,JOB_FULL,F1,svc.x,h1,"/a/dt-launcher.sh -env D -pipeline {_GUID} '
        f"-appName APP1 -alias AL1 -seal 99999 -dataflow DF1 -img img-repo/ing:1 "
        f"-bd 20260101 -od 20260101 -fid FID1 -proId RUN-GUID -timeout 60 -sleep 30 "
        f'-i -conf /cfg/c.json -compute /cfg/compute_small.json",Y\n',
    )
    node = g.processes[f"proc#dpl:{_GUID}"]
    assert node.dataflow == "DF1"  # dedicated G12 field
    assert node.config_path == "/cfg/c.json"
    assert node.properties == {
        "env": "D",
        "app_name": "APP1",
        "alias": "AL1",
        "seal": "99999",
        "fid": "FID1",
        "image": "img-repo/ing:1",
        "compute": "/cfg/compute_small.json",
        "launch_mode": "-i",
    }
    # identity is the GUID, properties never leak into the key
    assert node.node_id == f"proc#dpl:{_GUID}"


def test_onprem_argument_contract_properties(tmp_path) -> None:
    """(e) on-prem half: the dpl_spark_processor argument-contract params land
    as properties (dataset id, aws flag, jar path, hdfs location, token/manifest
    paths, queue name)."""
    g, _ = _extract(
        tmp_path,
        f'1,10,JOB_ONPM,F1,svc.x,h1,"/bin/dpl_spark_processor --pipeline-id {_GUID} '
        f"--aws --dataset-id DS-1 --user-jar-path /jars/u.jar --hdfs-location /hdfs/z "
        f'--token-file-path /tok/t.tok --manifest-file-path /m/m.json --queue-name q1",Y\n',
    )
    props = g.processes[f"proc#dpl:{_GUID}"].properties
    assert props["aws"] == "true"
    assert props["dataset_id"] == "DS-1"
    assert props["user_jar_path"] == "/jars/u.jar"
    assert props["hdfs_location"] == "/hdfs/z"
    assert props["token_file_path"] == "/tok/t.tok"
    assert props["manifest_file_path"] == "/m/m.json"
    assert props["queue_name"] == "q1"


# -- pre/post-execution shell text (G60 — the PRECMD/POSTCMD feed into G14) --------


def test_postcmd_move_joins_the_candidate_stream(tmp_path) -> None:
    """The G60 case: a job whose POSTCMD moves a file yields READS_FROM /
    WRITES_TO candidates with the SAME endpoints as a CMD_LINE file op — the
    job is the Activity, the operands are local_file assets, and no new
    relationship type appears. The counters keep the two sources apart so the
    pre/post yield is measurable."""
    jobs = tmp_path / "jobs.csv"
    jobs.write_text(
        "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"
        "9,161947,JOB_MERGE,F1,svc.x,h1,/opt/scripts/merge.ksh,Y\n",
        encoding="utf-8",
    )
    variables = tmp_path / "vars.csv"
    variables.write_text(
        "folder_id,job_id,job_name,var_name,var_value,appl_type\n"
        '161947,9,JOB_MERGE,%%POSTCMD,"mv /data/out/items.dat /data/backup/items.dat",OS\n',
        encoding="utf-8",
    )
    g = LineageGraph()
    cov = ControlMInventoryExtractor().extract(jobs, g, variables_csv=variables)
    jid = "proc#controlm_job:161947.9"
    assert (jid, "READS_FROM", "data#local_file:/data/out/items.dat") in g.rels
    assert (jid, "WRITES_TO", "data#local_file:/data/backup/items.dat") in g.rels
    assert cov.prepost_rows_read == 1
    assert cov.prepost_file_ops_added == 2
    # the CMD_LINE counter is untouched — the yield is measurable BY SOURCE
    assert cov.file_ops_added == 0
    assert cov.prepost_jobs_unmatched == 0 and cov.prepost_commands_unparsed == 0


def test_prepost_pass_discovers_the_raw_variables_export(tmp_path) -> None:
    """Directory mode with the bundled-sample header shape
    (TABLE_NAME/NAME/VALUE): the POSCMD typo spelling still counts as shell
    text (core's SHELL_VAR_NAMES), the triple-quoted CSV value is unwrapped by
    the core parser's outer-quote strip, an unmatched job and an unparseable
    value are counted rather than dropped, and a non-shell variable row never
    enters the pass."""
    (tmp_path / "controlm_jobs__sample.csv").write_text(
        "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"
        "9,161947,JOB_A,F1,svc.x,h1,/opt/scripts/a.ksh,Y\n",
        encoding="utf-8",
    )
    (tmp_path / "controlm_variables__sample.csv").write_text(
        "TABLE_NAME,JOB_NAME,JOB_ID,APPL_TYPE,NAME,VALUE\n"
        # the observed POSCMD typo, sample-shaped triple quoting, a backup mv
        '161947,JOB_A,9,OS,%%POSCMD,"""cc /apps/pre; mv /data/a.parquet /data/backup/a.parquet;"""\n'
        "161947,JOB_A,9,OS,%%PRECMD,echo starting\n"  # noop-only -> unparsed, counted
        "161947,JOB_GONE,99,OS,%%POSTCMD,mv /a /b\n"  # no such job -> unmatched, counted
        "161947,JOB_A,9,OS,%%TOK_FILE,/data/a.tok\n",  # not shell text -> not in the pass
        encoding="utf-8",
    )
    g = LineageGraph()
    cov = ControlMInventoryExtractor().extract(tmp_path, g)
    jid = "proc#controlm_job:161947.9"
    assert (jid, "READS_FROM", "data#local_file:/data/a.parquet") in g.rels
    assert (jid, "WRITES_TO", "data#local_file:/data/backup/a.parquet") in g.rels
    assert cov.prepost_rows_read == 3
    assert cov.prepost_file_ops_added == 2
    assert cov.prepost_commands_unparsed == 1
    assert cov.prepost_jobs_unmatched == 1
    assert "prepost: rows=3 unmatched=1 empty=0 unparsed=1 added=2" in cov.summary()
    # no new relationship types — the G14 endpoints are the whole story
    assert {r[1] for r in g.rels if r[0] == jid} <= {"INVOKES", "READS_FROM", "WRITES_TO"}


def test_prepost_pass_never_mistakes_the_jobs_csv_for_variables(tmp_path) -> None:
    """A jobs-CSV-only run (file OR directory) must not feed job rows through
    the shell-variable pass: the variables CSV is header-verified in both
    call shapes."""
    jobs = tmp_path / "jobs.csv"
    jobs.write_text(
        "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"
        "9,161947,JOB_A,F1,svc.x,h1,/opt/scripts/a.ksh,Y\n",
        encoding="utf-8",
    )
    for source in (jobs, tmp_path):
        cov = ControlMInventoryExtractor().extract(source, LineageGraph())
        assert cov.prepost_rows_read == 0
        assert cov.prepost_file_ops_added == 0


# =============================================================================
# G97 - the launcher/payload split (USES_ARTIFACT)
#
# Two signed gates rule this and neither is reopened here: cmdline-nfr-vetting
# 2026-07-21 (SME-2 the DISTINCT label, ControlMJob->Script{payload}; SME-3
# the :Script refinements) and rua-load-shapes 2026-08-07 (B2 the union
# endpoint that keeps INVOKES on :ETLProcess, B3 verbatim evidence, A4 the
# activation). Fixtures are synthetic throughout.
# =============================================================================

_G97_HEADER = "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"
_VARS_HEADER = "folder_id,job_id,job_name,var_name,var_value,appl_type\n"
_JID = "proc#controlm_job:161947.9"

# a REGISTERED launcher (informatica.icdw_run_interface, named_launcher: true)
_G97_JOBS = _G97_HEADER + (
    "9,161947,JOB_SPARK,F1,svc.x,h1,"
    "/apps/icdw/ICDW_etl_run_interface.ksh /apps/app/conform.jar,Y\n"
)


def _g97_extract(tmp_path, vars_csv: str, jobs_csv: str = _G97_JOBS):
    jobs = tmp_path / "jobs.csv"
    jobs.write_text(jobs_csv, encoding="utf-8")
    variables = tmp_path / "vars.csv"
    variables.write_text(vars_csv, encoding="utf-8")
    graph = LineageGraph()
    coverage = ControlMInventoryExtractor().extract(jobs, graph, variables_csv=variables)
    return graph, coverage


def _rels_of(graph, label):
    return sorted(r for r in graph.rels if r[1] == label)


def test_launcher_and_payload_yield_exactly_one_edge_each(tmp_path) -> None:
    """The acceptance's headline case. One command line carrying a REGISTERED
    launcher, plus the variable feed naming the payload it dispatches, yields
    exactly one INVOKES (to the launcher) and one USES_ARTIFACT (to the
    payload), with script_role stamped on both endpoints."""
    graph, coverage = _g97_extract(
        tmp_path,
        _VARS_HEADER
        + "161947,9,JOB_SPARK,%%ETL_ARTIFACT_URI,s3://synth/app/conform.jar,OS\n"
        + "161947,9,JOB_SPARK,%%ETL_PLATFORM,emr,OS\n"
        + "161947,9,JOB_SPARK,%%ETL_ARTIFACT_KIND,jar,OS\n"
        + "161947,9,JOB_SPARK,%%ETL_PLATFORM_FLAGS,-py,OS\n",
    )
    launcher = "proc#informatica:/apps/icdw/ICDW_etl_run_interface.ksh"
    payload = "proc#etl_artifact:s3://synth/app/conform.jar"

    assert _rels_of(graph, "INVOKES") == [(_JID, "INVOKES", launcher)]
    assert _rels_of(graph, "USES_ARTIFACT") == [(_JID, "USES_ARTIFACT", payload)]
    assert graph.processes[launcher].properties["script_role"] == "launcher"

    props = graph.processes[payload].properties
    assert props["script_role"] == "payload"
    assert props["artifact_uri"] == "s3://synth/app/conform.jar"
    assert props["platform"] == "emr"  # the SME-3 adopted property set
    assert props["artifact_kind"] == "jar"
    assert props["platform_flags"] == "-py"
    # B3: the derivation stays re-checkable, verbatim
    assert "%%ETL_ARTIFACT_URI=s3://synth/app/conform.jar" in props["evidence"]

    assert coverage.launchers_classified == 1
    assert coverage.payloads_classified == 1
    assert coverage.invocations_unclassified == 0


def test_payload_less_command_line_yields_no_uses_artifact_edge(tmp_path) -> None:
    """The acceptance's negative case: no artifact variable, no USES_ARTIFACT.
    The launcher keeps its INVOKES and nothing is invented beside it."""
    graph, coverage = _g97_extract(
        tmp_path, _VARS_HEADER + "161947,9,JOB_SPARK,%%SOME_OTHER,value,OS\n"
    )
    assert _rels_of(graph, "USES_ARTIFACT") == []
    assert len(_rels_of(graph, "INVOKES")) == 1
    assert coverage.payloads_classified == 0
    assert coverage.launchers_classified == 1


def test_unregistered_interpreter_is_unclassified_never_promoted(tmp_path) -> None:
    """Clause (e). spark-submit is a GENERIC interpreter rule, deliberately not
    `named_launcher` in the registry - an arbitrary interpreter is not launcher
    evidence. It stays exactly where it is today, on INVOKES with no role, and
    it is COUNTED. Promoting it would be the guess the clause forbids."""
    jobs = _G97_HEADER + (
        "9,161947,JOB_SPARK,F1,svc.x,h1," "spark-submit --master yarn /apps/app/refine.py,Y\n"
    )
    graph, coverage = _g97_extract(tmp_path, _VARS_HEADER, jobs_csv=jobs)
    node = graph.processes["proc#pyspark:/apps/app/refine.py"]
    assert "script_role" not in node.properties
    assert (_JID, "INVOKES", node.node_id) in graph.rels
    assert coverage.invocations_unclassified == 1
    assert coverage.launchers_classified == 0


def test_payload_named_in_both_feeds_is_migrated_never_double_represented(tmp_path) -> None:
    """Clause (d) - the outcome that must be IMPOSSIBLE. The same jar is named
    on the command line (so the CMD_LINE pass staged it WITH an INVOKES edge)
    and in the artifact variable. It must end as ONE node on ONE label: in the
    writer both stagings MERGE onto the same :Script {path}, so a jar carrying
    INVOKES and USES_ARTIFACT at once is exactly the double representation the
    clause rules out. The edge is MOVED, not added beside."""
    jobs = _G97_HEADER + (
        "9,161947,JOB_JAVA,F1,svc.x,h1," "java -jar /apps/app/conform.jar --date 20260101,Y\n"
    )
    graph, coverage = _g97_extract(
        tmp_path,
        _VARS_HEADER + "161947,9,JOB_JAVA,%%ETL_ARTIFACT_URI,/apps/app/conform.jar,OS\n",
        jobs_csv=jobs,
    )
    jar = "proc#java:/apps/app/conform.jar"
    assert jar in graph.processes
    assert "proc#etl_artifact:/apps/app/conform.jar" not in graph.processes  # ONE node
    assert (_JID, "USES_ARTIFACT", jar) in graph.rels
    assert (_JID, "INVOKES", jar) not in graph.rels
    assert graph.processes[jar].properties["script_role"] == "payload"
    assert coverage.payloads_migrated_off_invokes == 1


def test_etl_process_payload_stays_on_invokes_per_b2(tmp_path) -> None:
    """B2 in code. scheduler_uses_artifact's to_node is `Script` (SME-2), and
    B2 chose the union endpoint precisely so INVOKES could keep landing on
    :ETLProcess without re-modelling G12's working wrapper-payload expansion.
    So an Ab Initio pset STAYS on INVOKES. That is not an unmigrated leftover,
    and it is counted apart from `unclassified` because the reason is a RULING
    rather than an absence of evidence."""
    jobs = _G97_HEADER + (
        # the abioncloud wrapper, whose -g payload IS expanded to the pset — so
        # the node really is an :ETLProcess (G12) and not the wrapper script
        "9,161947,JOB_AI,F1,svc.x,h1,/apps/ab/runscript.sh -g /sandbox/ing.pset,Y\n"
    )
    graph, coverage = _g97_extract(
        tmp_path,
        _VARS_HEADER + "161947,9,JOB_AI,%%ETL_ARTIFACT_URI,ing.pset,OS\n",
        jobs_csv=jobs,
    )
    pset = "proc#abinitio:ing.pset"
    assert (_JID, "INVOKES", pset) in graph.rels
    assert _rels_of(graph, "USES_ARTIFACT") == []
    assert "script_role" not in graph.processes[pset].properties  # not a :Script
    assert coverage.payloads_kept_on_invokes_etl == 1
    assert coverage.invocations_etl_process == 1


def test_unresolved_artifact_value_is_counted_never_staged(tmp_path) -> None:
    """SME-1's own caveat honoured: "payloads are often variable-held/
    unresolvable". A value that is still a %%reference names no artifact, and
    staging it would put a node called %%JAR_HOME/conform.jar in the graph that
    reads as a real artifact forever after. Counted, not dropped, not invented."""
    graph, coverage = _g97_extract(
        tmp_path,
        _VARS_HEADER + "161947,9,JOB_SPARK,%%ETL_ARTIFACT_URI,%%JAR_HOME/conform.jar,OS\n",
    )
    assert _rels_of(graph, "USES_ARTIFACT") == []
    assert not [n for n in graph.processes if n.startswith("proc#etl_artifact:")]
    assert coverage.artifact_values_unresolved == 1
    assert coverage.payloads_classified == 0


def test_values_decide_a_launcher_valued_artifact_variable_is_not_a_payload(tmp_path) -> None:
    """The G16 value contract's load-bearing case, and the 2,384-variable gap
    analysis' one durable finding: NAMES LIE. %%JAR_PATH holding dt-launcher.sh
    is a LAUNCHER reference, not an artifact - classify_variable resolves it by
    VALUE, so no payload stages and no USES_ARTIFACT edge appears."""
    graph, coverage = _g97_extract(
        tmp_path, _VARS_HEADER + "161947,9,JOB_SPARK,%%JAR_PATH,dt-launcher.sh,OS\n"
    )
    assert _rels_of(graph, "USES_ARTIFACT") == []
    assert coverage.payloads_classified == 0
    assert coverage.artifact_rows_read == 1  # it WAS read - it just is not a payload


def test_artifact_row_for_an_unknown_job_is_counted(tmp_path) -> None:
    """The house rule applied to the new pass: a fact whose job is not in this
    extract is counted, never dropped."""
    _, coverage = _g97_extract(
        tmp_path,
        _VARS_HEADER + "999999,1,JOB_ELSEWHERE,%%ETL_ARTIFACT_URI,s3://synth/x.jar,OS\n",
    )
    assert coverage.artifact_jobs_unmatched == 1
    assert coverage.payloads_classified == 0


def test_writer_plans_uses_artifact_and_counts_the_roles(tmp_path) -> None:
    """The writer half: the split reaches the plan. USES_ARTIFACT gets its own
    MATCH/MERGE batch with the scheduler_uses_artifact vocab id, the :Script
    rows carry the SME-3 refinements, and WritePlan reports the clause-(e)
    counts off the planned rows."""
    from drydocs_lineage.writer import plan_curated

    graph, _ = _g97_extract(
        tmp_path,
        _VARS_HEADER
        + "161947,9,JOB_SPARK,%%ETL_ARTIFACT_URI,s3://synth/app/conform.jar,OS\n"
        + "161947,9,JOB_SPARK,%%ETL_PLATFORM,emr,OS\n",
    )
    plan = plan_curated(graph, set(graph.rels))
    assert "USES_ARTIFACT" in plan.rel_types
    assert plan.uses_artifact_rels == 1
    assert plan.launchers == 1 and plan.payloads == 1 and plan.scripts_unroled == 0

    cypher = "\n".join(c for c, _ in plan.statements)
    assert "MERGE (src)-[r:USES_ARTIFACT]->(dst)" in cypher
    assert "scheduler_uses_artifact" in cypher
    assert "s.script_role    = coalesce(row.script_role, s.script_role)" in cypher

    payload_row = next(
        r
        for _, params in plan.statements
        for r in params.get("rows", [])
        if isinstance(r, dict) and r.get("script_role") == "payload"
    )
    assert payload_row["platform"] == "emr"
    assert payload_row["artifact_uri"] == "s3://synth/app/conform.jar"


def test_payload_migration_cypher_moves_the_edge_and_spares_etlprocess() -> None:
    """Clause (d)'s written-down position, pinned so it cannot quietly drift.
    A MERGE-only re-load cannot retract an edge an earlier load asserted, so the
    named migration step is what makes double representation impossible on an
    EXISTING graph - and it must leave :ETLProcess alone, because B2 puts those
    on INVOKES deliberately."""
    from pathlib import Path as _Path

    repo = _Path(__file__).resolve().parents[2]
    script = (
        repo
        / "drydocs"
        / "loaders"
        / "cypher"
        / "migrate_payload_invokes_to_uses_artifact_g97.cypher"
    )
    text = script.read_text(encoding="utf-8")
    assert "MATCH (j:ControlMJob)-[old:INVOKES]->(s:Script)" in text  # :Script ONLY
    assert "s.script_role = 'payload'" in text  # evidence, never a path guess
    assert "MERGE (j)-[new:USES_ARTIFACT]->(s)" in text
    assert "DELETE old" in text  # MOVED, not copied
    assert "ETLProcess" in text  # the exclusion is stated, not silent


# =============================================================================
# G92 - resolve the job's scope chain BEFORE the file-op parse
#
# The defect: _file_op keyed the DataAsset off the VERBATIM operand, so a job
# whose POSTCMD moves %%R_PATH/out.dat and a job whose CMD_LINE moves
# /data/r/out.dat planned edges to TWO nodes for ONE file. Endpoints and meaning
# are unchanged (same READS_FROM / WRITES_TO, same ControlMJob -> DataAsset);
# only the operand the asset is keyed on changes. Synthetic fixtures, no
# database (J18).
# =============================================================================

_G92_JOBS = _G97_HEADER + (
    # job 9 spells the path LITERALLY on its command line
    "9,161947,JOB_LITERAL,F1,svc.x,h1,cp /data/r/out.dat /data/backup/out.dat,Y\n"
    # job 8 reaches the same file through a FOLDER variable, in POSTCMD
    "8,161947,JOB_VARIABLE,F1,svc.x,h1,/opt/scripts/noop.ksh,Y\n"
)

_G92_VARS = _VARS_HEADER + (
    # job_id 1 = the smart-folder header row (staging.py's raw-export rule)
    "161947,1,FOLDER_HDR,%%R_PATH,/data/r,OS\n"
    "161947,8,JOB_VARIABLE,%%POSTCMD,mv %%R_PATH/out.dat /data/archive/out.dat,OS\n"
)


def test_variable_and_literal_spellings_converge_on_one_asset(tmp_path) -> None:
    """The acceptance's named test. Two jobs, one file, ONE DataAsset id - and
    the %%-spelling never becomes a node of its own."""
    graph, coverage = _g97_extract(tmp_path, _G92_VARS, jobs_csv=_G92_JOBS)

    resolved = "data#local_file:/data/r/out.dat"
    assert resolved in graph.data_assets
    assert "data#local_file:%%R_PATH/out.dat" not in graph.data_assets
    # both jobs reach the SAME node - that is the whole point
    assert ("proc#controlm_job:161947.9", "READS_FROM", resolved) in graph.rels
    assert ("proc#controlm_job:161947.8", "READS_FROM", resolved) in graph.rels

    # clause (b): raw stays BESIDE resolved, so a wrong binding is auditable
    assert graph.data_assets[resolved].properties["raw_operands"] == "%%R_PATH/out.dat"
    # the literal job contributed no raw twin - its operand already WAS resolved
    backup = graph.data_assets["data#local_file:/data/backup/out.dat"]
    assert "raw_operands" not in backup.properties

    assert coverage.resolve_no_scope_chain == 0
    assert coverage.resolve_substitutions >= 1


def test_canonical_residue_is_expected_not_a_miss(tmp_path) -> None:
    """Clause (c). {ODATE}-class tokens only exist at execution time, so they
    survive resolution BY DESIGN and stay symbolic in the operand. They are
    counted as EXPECTED residue - distinct from an unresolved user variable,
    which is a real miss - and neither is dropped."""
    jobs = _G97_HEADER + (
        "9,161947,JOB_ODATE,F1,svc.x,h1,cp %%R_PATH/in_{{ODATE}}.dat /data/w/o.dat,Y\n"
    )
    vars_csv = _VARS_HEADER + "161947,1,FOLDER_HDR,%%R_PATH,/data/r,OS\n"
    graph, coverage = _g97_extract(tmp_path, vars_csv, jobs_csv=jobs)

    # the variable resolved; the runtime token did not, and should not have
    asset = "data#local_file:/data/r/in_{{ODATE}}.dat"
    assert asset in graph.data_assets
    assert coverage.resolve_residue == 1
    assert coverage.resolve_unresolved == 0  # residue is NOT a miss


def test_unresolved_user_variable_is_a_counted_miss_never_dropped(tmp_path) -> None:
    """Clause (c), the other half. A user %%ref with no binding IS a miss - it
    is counted, and the candidate still stages on the raw spelling rather than
    disappearing, because a dropped operand is invisible and a raw one is not."""
    jobs = _G97_HEADER + ("9,161947,JOB_MISS,F1,svc.x,h1,cp %%NO_SUCH/in.dat /data/w/o.dat,Y\n")
    vars_csv = _VARS_HEADER + "161947,1,FOLDER_HDR,%%R_PATH,/data/r,OS\n"
    graph, coverage = _g97_extract(tmp_path, vars_csv, jobs_csv=jobs)

    assert coverage.resolve_unresolved == 1
    assert coverage.resolve_residue == 0
    assert "data#local_file:%%NO_SUCH/in.dat" in graph.data_assets  # counted, not dropped
    assert coverage.file_ops_added == 2


def test_no_scope_chain_is_counted_and_parses_raw(tmp_path) -> None:
    """Clause (e)'s floor: a job with NO resolvable chain is counted, never
    silently parsed raw as though it had been resolved. Behaviour is exactly
    what it was before this item - which is the point of counting it."""
    jobs = _G97_HEADER + ("9,161947,JOB_NOVARS,F1,svc.x,h1,cp /data/r/a.dat /data/w/a.dat,Y\n")
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(jobs, encoding="utf-8")
    graph = LineageGraph()
    coverage = ControlMInventoryExtractor().extract(csv_path, graph)  # no variables CSV
    assert coverage.resolve_no_scope_chain == 1
    assert coverage.file_ops_added == 2
    assert "data#local_file:/data/r/a.dat" in graph.data_assets


def test_scope_chain_reads_the_aliased_var_scope_column(tmp_path) -> None:
    """Clause (e), the formal projection. When var_scope is present it is
    AUTHORITATIVE - the folder row here carries neither job_id 1 nor a job_name
    matching the folder, so only the declared column can identify it."""
    jobs = _G97_HEADER + ("9,161947,JOB_A,F1,svc.x,h1,cp %%R_PATH/a.dat /data/w/a.dat,Y\n")
    vars_csv = (
        "folder_id,job_id,job_name,var_scope,var_name,var_value\n"
        "161947,77,SOME_OTHER_NAME,FOLDER,%%R_PATH,/data/r\n"
    )
    graph, coverage = _g97_extract(tmp_path, vars_csv, jobs_csv=jobs)
    assert "data#local_file:/data/r/a.dat" in graph.data_assets
    assert coverage.resolve_no_scope_chain == 0


def test_scope_chain_reads_the_raw_export_folder_header(tmp_path) -> None:
    """Clause (e), the raw export. No var_scope column exists there, so the
    folder row is identified by the repo's own two spellings of the same fact:
    the SQL projection derives FOLDER from JOB_NAME = SCHED_TABLE, and
    staging.py falls back to the JOB_ID = 1 smart-folder heuristic."""
    (tmp_path / "controlm_jobs__sample.csv").write_text(
        _G97_HEADER + "9,161947,JOB_A,F1,svc.x,h1,cp %%R_PATH/a.dat /data/w/a.dat,Y\n",
        encoding="utf-8",
    )
    (tmp_path / "controlm_variables__sample.csv").write_text(
        "TABLE_NAME,JOB_NAME,JOB_ID,APPL_TYPE,NAME,VALUE\n"
        # JOB_NAME == TABLE_NAME: the SQL projection's own definition of FOLDER
        "161947,161947,77,OS,%%R_PATH,/data/r\n",
        encoding="utf-8",
    )
    graph = LineageGraph()
    coverage = ControlMInventoryExtractor().extract(tmp_path, graph)
    assert "data#local_file:/data/r/a.dat" in graph.data_assets
    assert coverage.resolve_no_scope_chain == 0


def test_job_scope_overrides_folder_scope(tmp_path) -> None:
    """Vendor priority order, which is the resolver's own contract rather than
    anything this extractor decides: the JOB binding wins over the folder one.
    Pinned because assembling the chain in the wrong order would still resolve
    - just to the wrong file, silently."""
    jobs = _G97_HEADER + ("9,161947,JOB_A,F1,svc.x,h1,cp %%R_PATH/a.dat /data/w/a.dat,Y\n")
    vars_csv = _VARS_HEADER + (
        "161947,1,FOLDER_HDR,%%R_PATH,/data/folder,OS\n" "161947,9,JOB_A,%%R_PATH,/data/job,OS\n"
    )
    graph, _ = _g97_extract(tmp_path, vars_csv, jobs_csv=jobs)
    assert "data#local_file:/data/job/a.dat" in graph.data_assets
    assert "data#local_file:/data/folder/a.dat" not in graph.data_assets


def test_the_extractor_has_no_second_substitution_engine() -> None:
    """Clause (a) as a guard, not a promise. The resolver's stated guardrail is
    that no caller may re-implement substitution, and this item fails outright
    if a regex twin or a local %%-stripping engine appears in this module.

    The check that actually holds: this module calls the ONE resolver, and it
    does not import `re` at all — a substitution engine needs one, so the
    import is the honest tripwire. (The `removeprefix("%%")` already in the
    pre/post pass is NOT a smell: it normalises a variable NAME to match it
    against SHELL_VAR_NAMES, and never touches a value.)"""
    import drydocs_lineage.extractors.controlm_inventory as mod

    text = Path(mod.__file__).read_text(encoding="utf-8")
    assert "resolve_command_line(layers, text)" in text  # the ONE resolver, called
    code = [
        line
        for line in text.splitlines()
        if not line.lstrip().startswith("#") and not line.lstrip().startswith("#:")
    ]
    assert not any(line.strip() in ("import re", "import regex") for line in code), (
        "the extractor imported a regex module — a second substitution path is "
        "exactly what G92 clause (a) forbids"
    )
    assert not hasattr(mod, "re")
