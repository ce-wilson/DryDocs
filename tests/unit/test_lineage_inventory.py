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

from drydocs_core.controlm import parse_command
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
    assert job.node_target == "host-emr-01"  # node_id -> node_target (host-or-group; gate controlm-hosts-topology)
    assert job.run_as == "svc.hldm"       # owner -> run_as
    assert job.application == "ARA"
    assert job.folder.startswith("PRARAG-HLDM-90001")


def test_shared_script_collapses(graph: LineageGraph) -> None:
    # onpm_fw.ksh is invoked by jobs in two folders -> one node, two INVOKES
    shell = [p for p in graph.processes.values() if p.name == "onpm_fw.ksh"]
    assert len(shell) == 1
    into_shell = [r for r in graph.rels if r[2] == shell[0].node_id]
    assert len(into_shell) == 2
    assert all(r[1] == "INVOKES" for r in into_shell)


# -- ontology reconcile (0002-C §4 identity/vocabulary rules) ----------------------

def test_rel_vocabulary_is_the_registered_set() -> None:
    assert REL_TYPES == {"INVOKES", "TRIGGERS", "READS_FROM", "WRITES_TO"}
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

    g = LineageGraph.from_dict({
        "schema": "depgraph-machine-first/v2",
        "processes": [{
            "node_id": "proc#controlm_job:1.2", "kind": "controlm_job",
            "name": "J", "host": "SOME-GROUP", "project": "dropped",
        }],
        "data_assets": [], "rels": [],
    })
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
        "1,10,JOB_EMPTY_CMD,F1,svc.x,h1,,Y\n"          # kept; empty command
        "2,10,,F1,svc.x,h1,/opt/x.sh,Y\n"              # nameless -> skipped
        "3,10,JOB_UNKNOWN,F1,svc.x,h1,mystery_bin,Y\n"  # UNKNOWN kind -> unresolved
        "4,10,JOB_STALE,F1,svc.x,h1,/opt/y.sh,N\n",     # stale -> skipped
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
    assert cov.rows_read == (
        cov.jobs_added + cov.skipped_nameless + cov.skipped_stale_version
    )
    # dict view carries every counter (machine-readable for future STG_PARSE_QUALITY hookup)
    assert set(cov.as_dict()) >= {
        "rows_read", "jobs_added", "skipped_stale_version", "skipped_nameless",
        "commands_empty", "commands_unparsed", "invocations_added",
        "invocations_unresolved", "invocations_no_target",
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
        "/data/out/loans.dat", "/data/arch/loans.dat", "/data/arch/loans.dat.gz",
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
    assert cov.file_ops_no_operand == 1            # mv with no target operand
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
        "proc#abinitio:ing.pset",                          # basename: dev+prod converge
        "proc#shell_script:/data/mnt/check.ksh",           # scripts stay path-keyed:
        "proc#shell_script:/home/mnt/check.ksh",           # dupes surface for SME merge
    }
    # full paths retained as properties on the converged pset node
    assert g.processes["proc#abinitio:ing.pset"].path.endswith("ing.pset")


# -- DPL launcher argument contract (G15; gate cmdline-nfr-vetting evidence) -------

_GUID = "11111111-2222-3333-4444-555555555555"
_CSV_HEADER = (
    "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"
)


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
    modes = {
        g.processes[f"proc#dpl:{guid}"].properties["launch_mode"] for guid in guids
    }
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
    assert node.dataflow == "DF1"           # dedicated G12 field
    assert node.config_path == "/cfg/c.json"
    assert node.properties == {
        "env": "D", "app_name": "APP1", "alias": "AL1", "seal": "99999",
        "fid": "FID1", "image": "img-repo/ing:1",
        "compute": "/cfg/compute_small.json", "launch_mode": "-i",
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
