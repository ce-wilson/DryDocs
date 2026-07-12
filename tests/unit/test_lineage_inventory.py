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
    # 4 current jobs (1 stale is_current_version=0 skipped) + 3 children
    assert kinds.count("controlm_job") == 4
    assert len(graph.processes) == 7
    assert len(graph.rels) == 4


def test_stale_version_skipped(graph: LineageGraph) -> None:
    names = {p.name for p in graph.processes.values()}
    assert "old_fw.ksh" not in names  # is_current_version=0


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
        "1,10,JOB_EMPTY_CMD,F1,svc.x,h1,,1\n"          # kept; empty command
        "2,10,,F1,svc.x,h1,/opt/x.sh,1\n"              # nameless -> skipped
        "3,10,JOB_UNKNOWN,F1,svc.x,h1,mystery_bin,1\n"  # UNKNOWN kind -> unresolved
        "4,10,JOB_STALE,F1,svc.x,h1,/opt/y.sh,0\n",     # stale -> skipped
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
