"""U25 — the debt-metrics ledger: one row per run, LF, no half rows, a delta reader."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODULE = REPO / "knowledge" / "depgraph-snapshots" / "metrics_ledger.py"


def _load():
    spec = importlib.util.spec_from_file_location("metrics_ledger", MODULE)
    mod = importlib.util.module_from_spec(spec)
    # a dataclass under `from __future__ import annotations` resolves its field
    # types through sys.modules[cls.__module__] — register before exec
    sys.modules["metrics_ledger"] = mod
    spec.loader.exec_module(mod)
    return mod


class _Client:
    """Answers the A3/A4/A5/IMPORTS queries from a scripted table."""

    def __init__(self, table):
        self.table = table

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def run(self, cypher, **params):
        if "count(r) AS n" in cypher:
            return [{"n": self.table["live_imports"]}]
        if "fan_in" in cypher:
            return [{"module": "drydocs/loaders/base.py", "fan_in": self.table["a3"]}]
        if "NOT ()-[:IMPORTS]->(m)" in cypher:
            key = "a4_fp" if "agents" in params.get("packages", []) else "a4_pkg"
            return [{"n": self.table[key]}]
        if "NOT EXISTS" in cypher:
            return [{"n": self.table["a5"]}]
        if "last_seen_at" in cypher:  # the freshness rider's probe
            return [{"last_seen_at": datetime(2026, 8, 21, 10, 0, tzinfo=UTC), "run_id": "r1"}]
        raise AssertionError(cypher)


def _snapshot(directory: Path, name: str = "drydocs-20260821.json", edges: int = 3) -> Path:
    doc = {
        "schema": "depgraph-machine-first/v1",
        "projects": ["drydocs"],
        "meta": {
            "project": "drydocs",
            "captured_at": "2026-08-21T03:40:24",
            "tree": False,
            "git": {"commit": "abc"},
        },
        "nodes": [
            {
                "file_id": f"drydocs/{i}.py",
                "project": "drydocs",
                "rel_path": f"{i}.py",
                "name": f"{i}.py",
                "extension": ".py",
                "kind": "file",
                "circular": False,
            }
            for i in range(edges + 1)
        ],
        "edges": [[f"drydocs/{i}.py", f"drydocs/{i+1}.py"] for i in range(edges)],
    }
    path = directory / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def test_row_carries_every_required_field_and_is_born_lf(tmp_path: Path) -> None:
    m = _load()
    snap = _snapshot(tmp_path)
    row = m.compute_row(
        _Client({"live_imports": 1032, "a3": 34, "a4_pkg": 0, "a4_fp": 4, "a5": 29}),
        snap,
        commit="0123456789abcdef",
        venue="bolt://x/drydocs",
        now=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
    )
    assert row.snapshot_imports == 3 and row.live_imports == 1032
    assert row.a3_top_module == "drydocs/loaders/base.py" and row.a3_fan_in == 34
    assert (row.a4_package_orphans, row.a4_first_party_orphans, row.a5_untested) == (0, 4, 29)
    assert row.freshness == "fresh" and row.date == "2026-08-21T12:00:00Z"
    ledger = tmp_path / "debt-metrics.jsonl"
    m.append_row(row, ledger)
    m.append_row(row, ledger)
    raw = ledger.read_bytes()
    assert b"\r" not in raw and raw.endswith(b"\n") and raw.count(b"\n") == 2
    rows = m.read_rows(ledger)
    assert len(rows) == 2 and set(rows[0]) >= {
        "date",
        "commit",
        "snapshot",
        "a3_top_module",
        "a3_fan_in",
        "a4_package_orphans",
        "a4_first_party_orphans",
        "a5_untested",
        "live_imports",
    }


def test_delta_reads_the_last_two_rows() -> None:
    m = _load()
    a = {
        "date": "2026-08-20T00:00:00Z",
        "commit": "aaaaaaa1",
        "a3_top_module": "x",
        "a3_fan_in": 31,
        "a4_package_orphans": 0,
        "a4_first_party_orphans": 4,
        "a5_untested": 29,
        "live_imports": 891,
        "snapshot_imports": 1032,
        "freshness": "stale",
    }
    b = {
        **a,
        "date": "2026-08-21T00:00:00Z",
        "commit": "bbbbbbb2",
        "a3_fan_in": 34,
        "live_imports": 1032,
        "a5_untested": 31,
        "freshness": "fresh",
    }
    text = m.delta([a, b])
    assert "A3 x=31 -> x=34" in text
    assert "A5 29 -> 31 (+2)" in text
    assert "live IMPORTS 891 -> 1032 (+141)" in text
    assert "freshness stale -> fresh" in text
    assert "no delta yet" in m.delta([a]) and "no rows" in m.delta([])


def test_no_database_means_no_row_not_a_half_row(tmp_path: Path, monkeypatch, capsys) -> None:
    m = _load()
    snap = _snapshot(tmp_path)
    monkeypatch.setattr(m, "LEDGER", tmp_path / "debt-metrics.jsonl")
    monkeypatch.setenv("NEO4J_URI", "bolt://nowhere.invalid:1")
    monkeypatch.setenv("NEO4J_PASSWORD", "x")
    rc = m.main([str(snap)])
    assert rc == 0  # warn-only: never blocks the snapshot
    assert not (tmp_path / "debt-metrics.jsonl").exists()
    assert "no row written" in capsys.readouterr().err


def test_ledger_is_declared_merge_union_and_exempt_from_retention() -> None:
    attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
    assert "debt-metrics.jsonl merge=union" in attrs
    readme = (REPO / "knowledge" / "depgraph-snapshots" / "README.md").read_text(encoding="utf-8")
    assert (
        "debt-metrics.jsonl" in readme and "never" in readme.split("debt-metrics.jsonl", 1)[1][:400]
    )
    script = (REPO / "knowledge" / "depgraph-snapshots" / "snapshot.ps1").read_text(
        encoding="utf-8"
    )
    assert "metrics_ledger.py" in script
