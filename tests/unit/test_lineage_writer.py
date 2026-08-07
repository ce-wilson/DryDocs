"""Fork-3 writer contract — the 0002-C §5 gates as tests.

Pins, in order of importance:

1. **Ground-truth-only (the remaining §5 gate, structural + runtime):** the
   component's ONLY database-writing module is writer.py; the string
   ``ddcontext`` appears nowhere in the package; a client bound to any
   database other than ``drydocs`` is refused (TrustBoundaryError).
   The scanned name is the DEPLOYED one (``ddcontext``) — it was
   ``drydocs_context`` until 2026-07-26, i.e. the guard had been scanning for a
   database name that no longer exists and would not have caught a constant
   naming the real one. Same class of bug as the one it guards against.
2. **Gate-bound vocabulary:** GATE STATE CHANGED AT G55 (rua-load-shapes §J,
   SIGNED OFF 2026-08-07, 28/28): m3_invokes / m3_reads_from / m3_writes_to
   are ``status: active`` in the real registry, so a live load of those labels
   proceeds; m3_triggers stays ``planned`` and still raises
   GateBoundVocabularyError — the gate check is per-label, and the terminus
   retires per-label as gates activate, never wholesale.
3. **Curated-only + identity:** confirmed rels must exist in the graph;
   ControlMJob endpoints must carry the NODE-KEY composite.
4. **Mechanics:** constraint-on-key MERGE, UNWIND batches, MATCH (never MERGE)
   for job endpoints, registered vocab_id stamped on every rel.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import drydocs_lineage
from drydocs_lineage.extractors import ControlMInventoryExtractor
from drydocs_lineage.model import (
    DataAssetNode,
    LineageGraph,
    ProcessNode,
    asset_id,
    process_id,
)
from drydocs_lineage.writer import (
    DATABASE,
    GateBoundVocabularyError,
    TrustBoundaryError,
    asset_urn,
    plan_curated,
    vocabulary_status,
    write_curated,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "lineage" / "jobs.csv"
PKG = REPO_ROOT / "drydocs_lineage"


def _fixture_graph() -> LineageGraph:
    g = LineageGraph()
    ControlMInventoryExtractor().extract(FIXTURE, g)
    return g


class _FakeClient:
    """Just enough Neo4jClient surface for the writer (connection_info + run)."""

    def __init__(self, database: str = "drydocs") -> None:
        self._database = database
        self.calls: list[tuple[str, dict]] = []

    def connection_info(self) -> dict:
        return {"uri": "bolt://synthetic", "user": "u", "database": self._database}

    def run(self, cypher: str, params: dict | None = None, **kwargs) -> list[dict]:
        merged = {**(params or {}), **kwargs}
        self.calls.append((cypher, merged))
        if "RETURN count(r) AS written" in cypher:
            return [{"written": len(merged["rows"])}]
        return []


ACTIVE_REGISTRY = """\
  - id:           m3_invokes
    status:       active
  - id:           m3_triggers
    status:       active
  - id:           m3_reads_from
    status:       active
  - id:           m3_writes_to
    status:       active
"""


# --- 1. ground-truth-only (§5, structural + runtime) -------------------------------


def test_only_writer_touches_a_database_and_context_is_unnameable() -> None:
    offenders: list[str] = []
    for path in PKG.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        # docstrings may EXPLAIN the boundary; no other string constant may
        # carry the context DB's name (that's how a wrong write target is born)
        docstrings = {
            ast.get_docstring(n, clean=False)
            for n in ast.walk(tree)
            if isinstance(n, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        }
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and "ddcontext" in node.value
                and node.value not in docstrings
            ):
                offenders.append(f"{path.name}: string constant names ddcontext")
        if path.name == "writer.py":
            continue  # the one sanctioned writer; everything below is for the rest
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for name in names:
                if name == "neo4j" or "neo4j_client" in name:
                    offenders.append(f"{path.name}: imports {name}")
    assert not offenders, offenders


def test_write_target_is_ground_truth_and_single_sourced() -> None:
    assert DATABASE == "drydocs"
    assert drydocs_lineage.DATABASE is DATABASE  # __init__ re-exports the boundary's


def test_trust_boundary_refuses_other_databases() -> None:
    g = _fixture_graph()
    with pytest.raises(TrustBoundaryError, match="drydocs"):
        write_curated(g, set(g.rels), client=_FakeClient(database="ddcontext"))


# --- 2. the vocabulary gate ---------------------------------------------------------


def test_live_load_executes_for_the_gate_activated_labels() -> None:
    """THE gate, INVERTED DELIBERATELY at G55 (gate rua-load-shapes §J, SIGNED
    OFF 2026-08-07, 28/28): m3_invokes / m3_reads_from / m3_writes_to went
    planned → active, so the raises-check this test carried since the
    vocabulary was declared flips to the execution contract — updated
    deliberately, not silently, exactly as its old docstring promised. The
    terminus survives per-label on what stayed planned (the companion test
    below)."""
    g = _fixture_graph()
    client = _FakeClient()
    assert write_curated(g, set(g.rels), client=client) == 4


def test_live_load_still_gate_bound_on_the_planned_label() -> None:
    """m3_triggers was NOT among the six G22 activation candidates and stays
    status: planned — a plan carrying TRIGGERS still refuses against the real
    registry. The raises-check terminus retires per-label as gates activate,
    never wholesale."""
    g = LineageGraph()
    sid = process_id("shell_script", "/opt/scripts/wrap.ksh")
    did = process_id("dpl", "b6b6c1b2-guid")
    g.add_process(
        ProcessNode(node_id=sid, kind="shell_script", name="wrap.ksh", path="/opt/scripts/wrap.ksh")
    )
    g.add_process(
        ProcessNode(
            node_id=did,
            kind="dpl",
            name="dt-pipelines-launcher.jar",
            path="/apps/tenants/dpl_utils/dt-accelerators/dt-pipelines-launcher.jar",
        )
    )
    g.add_rel(sid, "TRIGGERS", did)
    with pytest.raises(GateBoundVocabularyError, match="m3_triggers"):
        write_curated(g, set(g.rels), client=_FakeClient())


def test_real_registry_statuses_are_readable() -> None:
    statuses = vocabulary_status({"m3_invokes", "m3_triggers", "m3_reads_from", "m3_writes_to"})
    assert set(statuses) == {"m3_invokes", "m3_triggers", "m3_reads_from", "m3_writes_to"}
    assert set(statuses.values()) <= {"planned", "active", "deprecated", "removed"}


def test_plan_is_always_allowed_while_gate_is_closed() -> None:
    g = _fixture_graph()
    plan = plan_curated(g, set(g.rels))  # no gate, no client — review material
    assert plan.rels == 4 and plan.rel_types == ("INVOKES",)


# --- 3. curated-only + identity ------------------------------------------------------


def test_refuses_confirmed_rel_not_in_graph() -> None:
    g = _fixture_graph()
    ghost = ("proc#controlm_job:9.9", "INVOKES", "proc#shell_script:/opt/ghost.sh")
    with pytest.raises(ValueError, match="curation out of sync"):
        plan_curated(g, {ghost})


def test_refuses_invented_job_identity() -> None:
    # hand-made-CSV fallback key (folder/job_name) is not the NODE-KEY composite
    g = LineageGraph()
    jid = process_id("controlm_job", "FOLDER-X/JOB_Y")
    cid = process_id("shell_script", "/opt/x.sh")
    g.add_process(ProcessNode(node_id=jid, kind="controlm_job", name="JOB_Y"))
    g.add_process(ProcessNode(node_id=cid, kind="shell_script", name="x.sh"))
    g.add_rel(jid, "INVOKES", cid)
    with pytest.raises(ValueError, match="NODE-KEY composite"):
        plan_curated(g, set(g.rels))


def test_empty_confirmed_is_a_noop() -> None:
    assert write_curated(LineageGraph(), set()) == 0


# --- 4. mechanics ---------------------------------------------------------------------


def test_plan_mechanics_constraint_on_key_merge_unwind() -> None:
    g = _fixture_graph()
    plan = plan_curated(g, set(g.rels))
    cyphers = [c for c, _ in plan.statements]
    assert any("CREATE CONSTRAINT script_path IF NOT EXISTS" in c for c in cyphers)
    merge = next(c for c in cyphers if "MERGE (s:Script {path: row.path})" in c)
    assert "UNWIND $rows AS row" in merge
    # the fixture's onpm_fw.ksh target is a real .ksh path (not abinitio/dpl) —
    # it stays :Script; disambiguate from the trust.pset :ETLProcess INVOKES
    # batch below (G12 split one INVOKES group into two dst-class groups).
    rel = next(
        c for c in cyphers if "MERGE (src)-[r:INVOKES]->(dst)" in c and "MATCH (dst:Script" in c
    )
    # job endpoints are MATCHed on the NODE KEY — the M3 load owns those nodes
    assert "MATCH (src:ControlMJob {folder_id: row.src_folder_id, job_id: row.src_job_id})" in rel
    assert "MERGE (src:ControlMJob" not in rel
    assert "r.vocab_id      = 'm3_invokes'" in rel
    assert "CYPHER 25" not in " ".join(cyphers)
    # the fixture's composite keys ride the rows
    rel_rows = next(
        p
        for c, p in plan.statements
        if "MERGE (src)-[r:INVOKES]->(dst)" in c and "MATCH (dst:Script" in c
    )["rows"]
    assert {
        "src_folder_id": "161015",
        "src_job_id": "22",
        "dst_key": "/opt/scripts/hldm/onpm_fw.ksh",
    } in rel_rows


# --- 5. ETLProcess endpoint mapping (G12) --------------------------------------------


def test_abinitio_invocation_maps_to_etlprocess_not_script() -> None:
    """The fixture's job 25 invokes trust.pset directly (no wrapper) — an
    ABINITIO-kind process. It must MERGE as :ETLProcess keyed on the SAME
    stable token the extractor already computed (basename, per
    controlm_inventory._stable_invocation_key), with the full path carried as
    a property (never identity), and NOT collapse onto the generic :Script
    path (the pre-G12 behavior, which also mis-keyed Script.path on a bare
    basename instead of a real path)."""
    g = _fixture_graph()
    plan = plan_curated(g, set(g.rels))
    cyphers = [c for c, _ in plan.statements]
    assert any("CREATE CONSTRAINT etlprocess_token IF NOT EXISTS" in c for c in cyphers)
    etl_merge = next(c for c in cyphers if "MERGE (e:ETLProcess {token: row.token})" in c)
    assert "UNWIND $rows AS row" in etl_merge
    etl_rows = next(p for c, p in plan.statements if "MERGE (e:ETLProcess" in c)["rows"]
    assert {
        "token": "trust.pset",
        "kind": "etl",
        "engine": "abinitio",
        "name": "trust.pset",
        "path": "/opt/scripts/hldm/trust.pset",
        "dataflow": "",
        "config_path": "",
    } in etl_rows
    # no Script row for trust.pset — it must not double-book under both classes
    script_rows = next(p for c, p in plan.statements if "MERGE (s:Script" in c)["rows"]
    assert not any(r["path"] == "trust.pset" for r in script_rows)
    assert plan.etl_processes == 1

    rel = next(
        c for c in cyphers if "MERGE (src)-[r:INVOKES]->(dst)" in c and "MATCH (dst:ETLProcess" in c
    )
    assert "MATCH (src:ControlMJob {folder_id: row.src_folder_id, job_id: row.src_job_id})" in rel
    assert "MATCH (dst:ETLProcess {token: row.dst_key})" in rel
    assert "r.vocab_id      = 'm3_invokes'" in rel


def test_triggers_targets_dpl_pipeline_as_etlprocess_with_properties() -> None:
    """A Script wrapper TRIGGERS a DPL pipeline: identity is the -pipeline GUID
    (kind-scoped stable token, gate-log cmdline-lineage-review §b), and the
    dataflow name + config JSON path ride as properties, never identity."""
    g = LineageGraph()
    sid = process_id("shell_script", "/opt/scripts/wrap.ksh")
    did = process_id("dpl", "b6b6c1b2-guid")
    g.add_process(
        ProcessNode(
            node_id=sid,
            kind="shell_script",
            name="wrap.ksh",
            path="/opt/scripts/wrap.ksh",
        )
    )
    g.add_process(
        ProcessNode(
            node_id=did,
            kind="dpl",
            name="dt-pipelines-launcher.jar",
            path="/apps/tenants/dpl_utils/dt-accelerators/dt-pipelines-launcher.jar",
            dataflow="orders_dataflow",
            config_path="/apps/tenants/dpl_utils/config/orders.json",
        )
    )
    g.add_rel(sid, "TRIGGERS", did)

    plan = plan_curated(g, set(g.rels))
    assert plan.rel_types == ("TRIGGERS",)
    assert plan.etl_processes == 1

    etl_rows = next(p for c, p in plan.statements if "MERGE (e:ETLProcess" in c)["rows"]
    assert etl_rows == [
        {
            "token": "b6b6c1b2-guid",
            "kind": "etl",
            "engine": "dpl",
            "name": "dt-pipelines-launcher.jar",
            "path": "/apps/tenants/dpl_utils/dt-accelerators/dt-pipelines-launcher.jar",
            "dataflow": "orders_dataflow",
            "config_path": "/apps/tenants/dpl_utils/config/orders.json",
        }
    ]

    trig = next(c for c, _ in plan.statements if "MERGE (src)-[r:TRIGGERS]->(dst)" in c)
    assert "MATCH (src:Script {path: row.src_key})" in trig
    assert "MATCH (dst:ETLProcess {token: row.dst_key})" in trig
    assert "r.vocab_id      = 'm3_triggers'" in trig


# --- 6. file-ops endpoint resolution (G13) ---------------------------------------------


def test_file_ops_reads_from_script_resolves_to_owning_job() -> None:
    """Gate-log 2026-07-15 EDIT: m3_reads_from's from_node is "ETLProcess |
    ControlMJob", never Script (a prov:Entity cannot carry prov:used). A
    script-level READS_FROM candidate must plan as the OWNING job reading the
    asset, resolved via the script's INVOKES edge — even though that INVOKES
    edge is not itself part of THIS confirmed batch (it is graph topology, a
    separate curation fact)."""
    g = LineageGraph()
    jid = process_id("controlm_job", "161015.22")
    sid = process_id("shell_script", "/opt/scripts/hldm/mover.ksh")
    aid = asset_id("local_file", "/data/landing/loans.csv")
    g.add_process(ProcessNode(node_id=jid, kind="controlm_job", name="JOB_MOVER"))
    g.add_process(
        ProcessNode(
            node_id=sid,
            kind="shell_script",
            name="mover.ksh",
            path="/opt/scripts/hldm/mover.ksh",
        )
    )
    g.add_data_asset(
        DataAssetNode(
            node_id=aid,
            kind="local_file",
            location="/data/landing/loans.csv",
        )
    )
    g.add_rel(jid, "INVOKES", sid)  # structural topology (not confirmed here)
    g.add_rel(sid, "READS_FROM", aid)  # the candidate under curation this batch

    plan = plan_curated(g, {(sid, "READS_FROM", aid)})
    assert plan.rel_types == ("READS_FROM",)
    assert plan.unresolved_file_ops == 0
    assert plan.scripts == 0  # sid resolved away — no bare :Script Activity row

    cyphers = [c for c, _ in plan.statements]
    rel = next(c for c in cyphers if "MERGE (src)-[r:READS_FROM]->(dst)" in c)
    assert "MATCH (src:ControlMJob {folder_id: row.src_folder_id, job_id: row.src_job_id})" in rel
    assert "MATCH (dst:DataAsset {assetId: row.dst_key})" in rel
    assert "r.vocab_id      = 'm3_reads_from'" in rel

    rows = next(p for c, p in plan.statements if "MERGE (src)-[r:READS_FROM]->(dst)" in c)["rows"]
    assert rows == [
        {
            "src_folder_id": "161015",
            "src_job_id": "22",
            "dst_key": "urn:drydocs:dataasset:local_file:/data/landing:loans.csv",
        }
    ]


def test_file_ops_etl_case_src_stays_etlprocess() -> None:
    """The OTHER case in the gate-log EDIT: an ETLProcess src (abinitio/dpl)
    keeps its own Activity — WRITES_TO is not resolved through any job."""
    g = LineageGraph()
    eid = process_id("abinitio", "trust.pset")
    aid = asset_id("hdfs", "/data/landing/loans")
    g.add_process(
        ProcessNode(
            node_id=eid,
            kind="abinitio",
            name="trust.pset",
            path="/opt/scripts/hldm/trust.pset",
        )
    )
    g.add_data_asset(DataAssetNode(node_id=aid, kind="hdfs", location="/data/landing/loans"))
    g.add_rel(eid, "WRITES_TO", aid)

    plan = plan_curated(g, set(g.rels))
    assert plan.rel_types == ("WRITES_TO",)
    assert plan.unresolved_file_ops == 0
    assert plan.etl_processes == 1

    cyphers = [c for c, _ in plan.statements]
    write_rel = next(c for c in cyphers if "MERGE (src)-[r:WRITES_TO]->(dst)" in c)
    assert "MATCH (src:ETLProcess {token: row.src_key})" in write_rel
    assert "MATCH (dst:DataAsset {assetId: row.dst_key})" in write_rel
    assert "r.vocab_id      = 'm3_writes_to'" in write_rel


def test_file_ops_script_invoked_by_multiple_jobs_fans_out() -> None:
    """AMBIGUITY CALL (G13): a script INVOKEd by more than one job fans the
    file-ops candidate out to EVERY owning job — each job-run performs the
    file operation, so each is a distinct Activity that used the asset."""
    g = LineageGraph()
    j1 = process_id("controlm_job", "161015.22")
    j2 = process_id("controlm_job", "161015.23")
    sid = process_id("shell_script", "/opt/scripts/hldm/mover.ksh")
    aid = asset_id("local_file", "/data/landing/loans.csv")
    g.add_process(ProcessNode(node_id=j1, kind="controlm_job", name="JOB_A"))
    g.add_process(ProcessNode(node_id=j2, kind="controlm_job", name="JOB_B"))
    g.add_process(
        ProcessNode(
            node_id=sid,
            kind="shell_script",
            name="mover.ksh",
            path="/opt/scripts/hldm/mover.ksh",
        )
    )
    g.add_data_asset(
        DataAssetNode(
            node_id=aid,
            kind="local_file",
            location="/data/landing/loans.csv",
        )
    )
    g.add_rel(j1, "INVOKES", sid)
    g.add_rel(j2, "INVOKES", sid)
    g.add_rel(sid, "READS_FROM", aid)

    plan = plan_curated(g, {(sid, "READS_FROM", aid)})
    assert plan.unresolved_file_ops == 0
    rows = next(p for c, p in plan.statements if "MERGE (src)-[r:READS_FROM]->(dst)" in c)["rows"]
    assert len(rows) == 2
    assert {
        "src_folder_id": "161015",
        "src_job_id": "22",
        "dst_key": "urn:drydocs:dataasset:local_file:/data/landing:loans.csv",
    } in rows
    assert {
        "src_folder_id": "161015",
        "src_job_id": "23",
        "dst_key": "urn:drydocs:dataasset:local_file:/data/landing:loans.csv",
    } in rows


def test_file_ops_script_with_no_owning_job_is_dropped_and_counted() -> None:
    """AMBIGUITY CALL (G13): the gate forbids a bare :Script Activity for file
    ops; a script with no INVOKES owner anywhere in the graph cannot be
    planned as-is. Dropped, never silently — plan.unresolved_file_ops
    surfaces the loss so review catches it."""
    g = LineageGraph()
    sid = process_id("shell_script", "/opt/scripts/hldm/orphan.ksh")
    aid = asset_id("local_file", "/data/landing/loans.csv")
    g.add_process(
        ProcessNode(
            node_id=sid,
            kind="shell_script",
            name="orphan.ksh",
            path="/opt/scripts/hldm/orphan.ksh",
        )
    )
    g.add_data_asset(
        DataAssetNode(
            node_id=aid,
            kind="local_file",
            location="/data/landing/loans.csv",
        )
    )
    g.add_rel(sid, "READS_FROM", aid)  # no job INVOKES sid anywhere in the graph

    plan = plan_curated(g, set(g.rels))
    assert plan.unresolved_file_ops == 1
    assert plan.rels == 1  # still the confirmed count (audit trail)
    assert plan.rel_types == ()  # nothing left to write for this candidate
    assert plan.statements == ()
    assert plan.scripts == 0


def test_file_ops_dst_must_be_a_data_asset() -> None:
    """The gate-log EDIT unifies to_node on DataAsset for BOTH cases; a
    candidate that disagrees is a curation error the writer flags rather than
    silently forcing into some other shape."""
    g = LineageGraph()
    jid = process_id("controlm_job", "161015.22")
    sid = process_id("shell_script", "/opt/scripts/hldm/mover.ksh")
    other = process_id("shell_script", "/opt/scripts/hldm/other.ksh")
    g.add_process(ProcessNode(node_id=jid, kind="controlm_job", name="JOB_A"))
    g.add_process(ProcessNode(node_id=sid, kind="shell_script", name="mover.ksh"))
    g.add_process(ProcessNode(node_id=other, kind="shell_script", name="other.ksh"))
    g.add_rel(jid, "INVOKES", sid)
    g.add_rel(sid, "READS_FROM", other)  # dst is a Script, not a DataAsset

    with pytest.raises(ValueError, match="DataAsset"):
        plan_curated(g, {(sid, "READS_FROM", other)})


def test_cmdline_file_op_feed_plans_job_to_asset_edges(tmp_path: Path) -> None:
    """G14 acceptance: a job whose CMD_LINE moves a file plans job->asset
    edges in plan_curated output. The extractor's file-ops feed arrives with
    the job itself as the Activity (the gate EDIT's file-ops case — no Script
    hop), so G13's resolution passes it straight through to the ControlMJob
    MATCH shape; refusal semantics stay untouched (m3_reads_from/m3_writes_to
    remain planned — this is plan material, not a write)."""
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(
        "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"
        '22,161015,JOB_ARCHIVE,F1,svc.x,h1,"mv /data/out/loans.dat /data/arch/loans.dat",Y\n',
        encoding="utf-8",
    )
    g = LineageGraph()
    ControlMInventoryExtractor().extract(csv_path, g)
    confirmed = {r for r in g.rels if r[1] in ("READS_FROM", "WRITES_TO")}
    assert confirmed  # the feed exists — G13's logic is no longer dormant

    plan = plan_curated(g, confirmed)
    assert plan.unresolved_file_ops == 0
    assert plan.rel_types == ("READS_FROM", "WRITES_TO")
    assert plan.assets == 2

    cyphers = [c for c, _ in plan.statements]
    reads = next(c for c in cyphers if "MERGE (src)-[r:READS_FROM]->(dst)" in c)
    assert "MATCH (src:ControlMJob {folder_id: row.src_folder_id, job_id: row.src_job_id})" in reads
    assert "MATCH (dst:DataAsset {assetId: row.dst_key})" in reads
    assert "r.vocab_id      = 'm3_reads_from'" in reads
    rows = next(p for c, p in plan.statements if "MERGE (src)-[r:READS_FROM]->(dst)" in c)["rows"]
    assert rows == [
        {
            "src_folder_id": "161015",
            "src_job_id": "22",
            "dst_key": "urn:drydocs:dataasset:local_file:/data/out:loans.dat",
        }
    ]
    writes = next(c for c in cyphers if "MERGE (src)-[r:WRITES_TO]->(dst)" in c)
    assert "r.vocab_id      = 'm3_writes_to'" in writes


def test_unresolved_file_op_candidates_mirrors_the_plan_drop() -> None:
    """G14: the review-surface helper lists exactly what plan_curated would
    drop — a script-src candidate with no owning job — and nothing else."""
    from drydocs_lineage.writer import unresolved_file_op_candidates

    g = LineageGraph()
    jid = process_id("controlm_job", "161015.22")
    owned = process_id("shell_script", "/opt/owned.ksh")
    orphan = process_id("shell_script", "/opt/orphan.ksh")
    aid = asset_id("local_file", "/data/x.dat")
    g.add_process(ProcessNode(node_id=jid, kind="controlm_job", name="J"))
    g.add_process(ProcessNode(node_id=owned, kind="shell_script", name="owned.ksh"))
    g.add_process(ProcessNode(node_id=orphan, kind="shell_script", name="orphan.ksh"))
    g.add_data_asset(DataAssetNode(node_id=aid, kind="local_file", location="/data/x.dat"))
    g.add_rel(jid, "INVOKES", owned)
    g.add_rel(owned, "READS_FROM", aid)  # resolves via the owning job
    g.add_rel(orphan, "WRITES_TO", aid)  # no owner — the would-be drop
    g.add_rel(jid, "READS_FROM", aid)  # already a job src — trivial

    assert unresolved_file_op_candidates(g) == [(orphan, "WRITES_TO", aid)]
    plan = plan_curated(g, {r for r in g.rels if r[1] != "INVOKES"})
    assert plan.unresolved_file_ops == 1  # the helper and the plan agree


def test_write_executes_when_gate_is_open(tmp_path: Path) -> None:
    registry = tmp_path / "vocab.yaml"
    registry.write_text(ACTIVE_REGISTRY, encoding="utf-8")
    g = _fixture_graph()
    client = _FakeClient()
    written = write_curated(g, set(g.rels), client=client, registry=registry)
    assert written == 4
    ran = [c for c, _ in client.calls]
    assert any("CREATE CONSTRAINT script_path" in c for c in ran)
    assert any("MERGE (s:Script" in c for c in ran)
    assert any("MERGE (src)-[r:INVOKES]->(dst)" in c for c in ran)
    # every data statement carries the run timestamp
    assert all("written_at" in p for _, p in client.calls)


def test_asset_urn_is_the_d1_proxy_shape() -> None:
    assert asset_urn("hdfs", "/data/landing/loans") == (
        "urn:drydocs:dataasset:hdfs:/data/landing:loans"
    )
    assert asset_urn("hive_table", "edw.loans") == ("urn:drydocs:dataasset:hive_table:-:edw.loans")
