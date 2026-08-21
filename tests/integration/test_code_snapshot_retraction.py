"""U21 (d) — the two graph-side guards for per-source edge retraction.

Against a throwaway Neo4j EE (testcontainers, same image the e2e chain uses):

1. snapshot A asserts a -> base and c -> base; snapshot B still CONTAINS a but
   no longer asserts its import, and OMITS c entirely. After B: a -> base is
   gone (the sweep works) and c -> base survives (it cannot over-reach).
2. Re-loading A re-asserts a -> base by MERGE — retraction is reversible by
   the next snapshot, which is why it may delete instead of mark.

Opt-in like every integration test (``-m integration``).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.integration.test_e2e_load import NEO4J_IMAGE, _client

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(shutil.which("docker") is None, reason="docker not on PATH"),
]


def _docker_ok() -> bool:
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@pytest.fixture(scope="module")
def env():
    if not _docker_ok():
        pytest.skip("Docker daemon unavailable")
    from testcontainers.neo4j import Neo4jContainer

    container = (
        Neo4jContainer(NEO4J_IMAGE)
        .with_env("NEO4J_PLUGINS", '["apoc"]')
        .with_env("NEO4J_ACCEPT_LICENSE_AGREEMENT", "eval")
    )
    with container as neo4j:
        yield {
            "NEO4J_URI": neo4j.get_connection_url(),
            "NEO4J_USER": neo4j.username,
            "NEO4J_PASSWORD": neo4j.password,
            "NEO4J_DATABASE": "neo4j",
        }


def _node(file_id: str) -> dict:
    return {
        "file_id": file_id,
        "project": "drydocs",
        "rel_path": file_id.split("/", 1)[1],
        "name": file_id.rsplit("/", 1)[1],
        "extension": ".py",
        "kind": "file",
        "circular": False,
    }


def _write(tmp_path: Path, name: str, nodes: list[str], edges: list[list[str]]) -> Path:
    doc = {
        "schema": "depgraph-machine-first/v1",
        "projects": ["drydocs"],
        "meta": {
            "project": "drydocs",
            "captured_at": "2026-08-21T00:00:00",
            "tree": False,
            "git": {
                "commit": "abc1234",
                "full": "abc1234" + "0" * 33,
                "branch": "main",
                "dirty": False,
            },
        },
        "nodes": [_node(n) for n in nodes],
        "edges": edges,
    }
    path = tmp_path / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def _imports(cli) -> set[tuple[str, str]]:
    rows = cli.run(
        "MATCH (a:CodeModule)-[:IMPORTS]->(b:CodeModule) RETURN a.file_id AS a, b.file_id AS b"
    )
    return {(r["a"], r["b"]) for r in rows}


def test_snapshot_b_retracts_a_dropped_import_and_leaves_omitted_modules_alone(env, tmp_path):
    from drydocs.loaders.code_snapshot import CodeSnapshotAdapter, CodeSnapshotLoader

    snap_a = _write(
        tmp_path,
        "a.json",
        ["drydocs/a.py", "drydocs/c.py", "drydocs/base.py"],
        [["drydocs/a.py", "drydocs/base.py"], ["drydocs/c.py", "drydocs/base.py"]],
    )
    # B still contains a (import dropped) and base; c is not in B at all
    snap_b = _write(tmp_path, "b.json", ["drydocs/a.py", "drydocs/base.py"], [])

    with _client(env) as cli:
        cli.run("MATCH (n) DETACH DELETE n")
        s1 = CodeSnapshotLoader(cli, CodeSnapshotAdapter(snap_a), full_extract=True).load()
        assert s1.edges_retracted == 0
        assert _imports(cli) == {
            ("drydocs/a.py", "drydocs/base.py"),
            ("drydocs/c.py", "drydocs/base.py"),
        }

        s2 = CodeSnapshotLoader(cli, CodeSnapshotAdapter(snap_b), full_extract=True).load()
        # guard 1: the dropped import is gone — the sweep works
        # guard 2: c's edge survives — c was not in B, so B says nothing about it
        assert _imports(cli) == {("drydocs/c.py", "drydocs/base.py")}
        assert s2.edges_retracted == 1
        assert s2.nodes_marked_removed == 1  # c itself is tombstoned by the D7 node pass
        run = cli.run("MATCH (r:JobRun {run_id: $id}) RETURN r.edges_retracted AS n", id=s2.run_id)
        assert run[0]["n"] == 1

        # reversible: the next snapshot that asserts the import re-creates it by MERGE
        s3 = CodeSnapshotLoader(cli, CodeSnapshotAdapter(snap_a), full_extract=True).load()
        assert s3.edges_retracted == 0
        assert _imports(cli) == {
            ("drydocs/a.py", "drydocs/base.py"),
            ("drydocs/c.py", "drydocs/base.py"),
        }


def test_edges_from_other_loaders_are_never_candidates(env, tmp_path):
    """An IMPORTS edge without the snapshot source stamp — written by anything
    else — sits between two touched modules and survives a full re-load."""
    from drydocs.loaders.code_snapshot import CodeSnapshotAdapter, CodeSnapshotLoader

    snap_a = _write(tmp_path, "a2.json", ["drydocs/x.py", "drydocs/y.py"], [])
    with _client(env) as cli:
        cli.run("MATCH (n) DETACH DELETE n")
        CodeSnapshotLoader(cli, CodeSnapshotAdapter(snap_a), full_extract=True).load()
        cli.run(
            "MATCH (x:CodeModule {file_id:'drydocs/x.py'}), (y:CodeModule {file_id:'drydocs/y.py'}) "
            "MERGE (x)-[r:IMPORTS]->(y) SET r.source = 'hand-curated'"
        )
        s = CodeSnapshotLoader(cli, CodeSnapshotAdapter(snap_a), full_extract=True).load()
        assert s.edges_retracted == 0
        assert _imports(cli) == {("drydocs/x.py", "drydocs/y.py")}
