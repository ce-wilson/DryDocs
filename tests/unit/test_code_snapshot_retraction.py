"""U21 — IMPORTS edges are retracted per source, never globally, and counted.

Duck-typed client (the D7 test idiom): these cases pin the QUERY the loader
issues — its scope keys, its source fence, its count — and the summary / status
envelope plumbing. The graph-side guards (snapshot A then B leaves no live
edge; a module B omits keeps its edges) run against a real Neo4j in
tests/integration/test_code_snapshot_retraction.py.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from drydocs.loaders.base import LoadSummary, status_items_for
from drydocs.loaders.code_snapshot import (
    SNAPSHOT_EDGE_SOURCE,
    SNAPSHOT_EDGE_TYPES,
    CodeSnapshotAdapter,
    CodeSnapshotLoader,
)

REPO = Path(__file__).resolve().parents[2]


class _FakeClient:
    def __init__(self, *, retracted: int = 0) -> None:
        self.retracted = retracted
        self.run_calls: list[tuple[str, dict]] = []
        self.run_script_calls: list[tuple[str, dict]] = []

    def run(self, cypher: str, params: dict[str, Any] | None = None, **kwargs: Any) -> list[dict]:
        self.run_calls.append((cypher, {**(params or {}), **kwargs}))
        if "AS retracted" in cypher:
            return [{"retracted": self.retracted}]
        if "AS marked" in cypher:
            return [{"marked": 0}]
        if "AS reactivated" in cypher:
            return [{"reactivated": 0}]
        return []

    def run_script(self, script: str, params: dict[str, Any] | None = None) -> None:
        self.run_script_calls.append((script, dict(params or {})))

    def retraction_calls(self) -> list[tuple[str, dict]]:
        return [(c, b) for c, b in self.run_calls if "AS retracted" in c]


def _snapshot(tmp_path: Path) -> Path:
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
        "nodes": [
            {
                "file_id": "drydocs/a.py",
                "project": "drydocs",
                "rel_path": "a.py",
                "name": "a.py",
                "extension": ".py",
                "kind": "file",
                "circular": False,
            },
            {
                "file_id": "drydocs/b.py",
                "project": "drydocs",
                "rel_path": "b.py",
                "name": "b.py",
                "extension": ".py",
                "kind": "file",
                "circular": False,
            },
        ],
        "edges": [["drydocs/a.py", "drydocs/b.py"]],
    }
    path = tmp_path / "drydocs-20260821.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def test_retraction_is_scoped_to_touched_modules_and_snapshot_source_only(tmp_path: Path) -> None:
    """(a) per-source, never global: the query binds the run id on the MODULE
    (this run's coverage) and on the EDGE (what this run re-asserted), fences
    on the loader's own source stamp, and names only the types it writes."""
    client = _FakeClient(retracted=3)
    loader = CodeSnapshotLoader(client, CodeSnapshotAdapter(_snapshot(tmp_path)), full_extract=True)
    summary = loader.load()
    ((cypher, bind),) = client.retraction_calls()
    assert "m.last_run_id = $run_id" in cypher
    assert "r.last_run_id <> $run_id" in cypher
    assert "r.source = $edge_source" in cypher and bind["edge_source"] == SNAPSHOT_EDGE_SOURCE
    assert bind["run_id"] == loader.run_id
    assert f"[r:{'|'.join(SNAPSHOT_EDGE_TYPES)}]" in cypher
    # no unscoped pattern anywhere in the statement
    assert re.search(r"MATCH \(\)-\[", cypher) is None
    assert "DETACH" not in cypher
    # (c) the count is reported, never silent — summary, as_dict, envelope
    assert summary.edges_retracted == 3
    assert summary.as_dict()["edges_retracted"] == 3
    assert any(i["type"].endswith("/edges-retracted") for i in status_items_for(summary))
    # and stamped on the :JobRun beside nodes_marked_removed
    close = next(c for c, _ in client.run_calls if "run.edges_retracted" in c)
    assert "run.nodes_marked_removed" in close


def test_retraction_runs_after_the_node_mark_pass(tmp_path: Path) -> None:
    client = _FakeClient()
    CodeSnapshotLoader(client, CodeSnapshotAdapter(_snapshot(tmp_path)), full_extract=True).load()
    order = [c for c, _ in client.run_calls if "AS marked" in c or "AS retracted" in c]
    assert [("marked" in c) for c in order] == [True, False]


def test_retraction_refuses_without_full_extract_like_the_mark_pass(tmp_path: Path, caplog) -> None:
    """The D7 discipline applied to relationships: a filtered run must not retract."""
    client = _FakeClient(retracted=99)
    with caplog.at_level("INFO"):
        summary = CodeSnapshotLoader(client, CodeSnapshotAdapter(_snapshot(tmp_path))).load()
    assert client.retraction_calls() == []
    assert summary.edges_retracted == 0
    assert "edge retraction skipped" in caplog.text


def test_zero_retractions_emit_no_status_item() -> None:
    """A clean run stays clean: no all-clear item (O28 rule)."""
    summary = LoadSummary(loader="x", run_id="r", started_at="t", status="OK")
    assert status_items_for(summary) == []


def test_cypher_template_stamps_the_scope_keys_on_every_snapshot_edge() -> None:
    """The retraction keys on r.source + r.last_run_id; the template must write
    both on each of the three edge types, or the sweep would delete edges the
    run just re-asserted (or never see stale ones)."""
    text = (REPO / "drydocs" / "loaders" / "cypher" / "code_snapshot.cypher").read_text(
        encoding="utf-8"
    )
    for label, var in (("IMPORTS", "imp"), ("IS_ENCODED_IN", "enc"), ("HAS_MEDIA_TYPE", "hmt")):
        assert f"[{var}:{label}]" in text
        assert f"{var}.source        = 'depgraph-snapshot'" in text
        assert f"{var}.last_run_id  = $run_id" in text
