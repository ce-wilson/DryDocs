"""Fork-3 writer contract — the 0002-C §5 gates as tests.

Pins, in order of importance:

1. **Ground-truth-only (the remaining §5 gate, structural + runtime):** the
   component's ONLY database-writing module is writer.py; the string
   ``drydocs_context`` appears nowhere in the package; a client bound to any
   database other than ``drydocs`` is refused (TrustBoundaryError).
2. **Gate-bound vocabulary:** the four rel labels are ``status: planned`` in
   relationship_vocabulary.yaml — a live load against the REAL registry raises
   GateBoundVocabularyError today, by design. Execution mechanics are testable
   only against a synthetic registry flipped to ``active``.
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
from drydocs_lineage.model import LineageGraph, ProcessNode, process_id
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
            if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and "drydocs_context" in node.value
                and node.value not in docstrings
            ):
                offenders.append(f"{path.name}: string constant names drydocs_context")
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
        write_curated(g, set(g.rels), client=_FakeClient(database="drydocs_context"))


# --- 2. the vocabulary gate ---------------------------------------------------------

def test_live_load_is_gate_bound_against_the_real_registry() -> None:
    """THE gate: all four labels are status: planned today — a live load must
    refuse. When the HITL gate flips them active, this test flips to the
    execution contract (and gets updated deliberately, not silently)."""
    g = _fixture_graph()
    with pytest.raises(GateBoundVocabularyError, match="m3_invokes"):
        write_curated(g, set(g.rels), client=_FakeClient())


def test_real_registry_statuses_are_readable() -> None:
    statuses = vocabulary_status(
        {"m3_invokes", "m3_triggers", "m3_reads_from", "m3_writes_to"}
    )
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
    rel = next(c for c in cyphers if "MERGE (src)-[r:INVOKES]->(dst)" in c)
    # job endpoints are MATCHed on the NODE KEY — the M3 load owns those nodes
    assert "MATCH (src:ControlMJob {folder_id: row.src_folder_id, job_id: row.src_job_id})" in rel
    assert "MERGE (src:ControlMJob" not in rel
    assert "r.vocab_id      = 'm3_invokes'" in rel
    assert "CYPHER 25" not in " ".join(cyphers)
    # the fixture's composite keys ride the rows
    rel_rows = next(p for c, p in plan.statements if "INVOKES" in c)["rows"]
    assert {"src_folder_id": "161015", "src_job_id": "22",
            "dst_key": "/opt/scripts/hldm/onpm_fw.ksh"} in rel_rows


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
    assert asset_urn("hive_table", "edw.loans") == (
        "urn:drydocs:dataasset:hive_table:-:edw.loans"
    )
