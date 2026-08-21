"""U22 — the code-graph freshness comparison, over fixtures (no database).

The unit-testable half is the COMPARISON, not the freshness: each verdict is
driven from fixtures — fresh, stale, no snapshot on disk, empty graph, database
unreachable — so the mechanism is guarded on a machine with no database. Own
file rather than test_code_graph_review_plan.py (the offered home): that file
guards a DOCUMENT against pyproject; this guards a mechanism, and the two fail
for different reasons.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from drydocs.code_graph_freshness import Verdict, check, compare, newest_snapshot

CAPTURED = "2026-08-21T03:40:24"  # naive = LOCAL wall clock, as snapshot.ps1 stamps it


def _local(text: str) -> datetime:
    return datetime.fromisoformat(text).astimezone()


def test_fresh_when_the_graph_was_loaded_after_the_newest_snapshot() -> None:
    loaded = _local(CAPTURED) + timedelta(minutes=40)
    v = compare(loaded, "run-1", "drydocs-20260821-0340.json", CAPTURED)
    assert v.verdict is Verdict.FRESH and not v.is_warning
    assert v.snapshot_name == "drydocs-20260821-0340.json" and v.graph_run_id == "run-1"
    assert "FRESH" in v.message() and "run-1" in v.message() and "0340" in v.message()


def test_stale_names_the_drift_the_run_and_the_snapshot() -> None:
    loaded = datetime(2026, 8, 2, 23, 6, 42, tzinfo=UTC)  # the 08-13 incident's value
    v = compare(loaded, "run-aug2", "drydocs-20260813.json", "2026-08-13T10:00:00")
    assert v.verdict is Verdict.STALE and v.is_warning
    assert v.lag is not None and v.lag.days >= 10
    msg = v.message()
    assert "STALE by 10." in msg and "run-aug2" in msg and "drydocs-20260813.json" in msg
    assert "never refreshes" in msg  # reports, does not repair


def test_naive_snapshot_time_is_local_not_utc() -> None:
    """A naive captured_at read as UTC would shift the snapshot hours earlier
    and call a stale graph fresh. Proven on the ambiguous window."""
    captured_local = _local(CAPTURED)  # the true instant
    loaded_just_before = captured_local - timedelta(minutes=5)
    v = compare(loaded_just_before, "r", "snap.json", CAPTURED)
    assert v.verdict is Verdict.STALE


def test_no_snapshot_is_its_own_verdict() -> None:
    v = compare(datetime.now(UTC), "r", None, None)
    assert v.verdict is Verdict.NO_SNAPSHOT and v.is_warning
    assert "NO SNAPSHOT" in v.message()


def test_empty_graph_is_its_own_verdict() -> None:
    v = compare(None, None, "snap.json", CAPTURED)
    assert v.verdict is Verdict.EMPTY_GRAPH and v.is_warning
    assert "EMPTY" in v.message() and "snap.json" in v.message()


class _Boom:
    def __enter__(self):
        raise ConnectionRefusedError("bolt://nowhere:7687")

    def __exit__(self, *a):
        return False


def test_database_unreachable_is_never_fresh(tmp_path: Path) -> None:
    """The failure this item exists to stop: a check that reports green because
    it could not look."""
    _write_snapshot(tmp_path, "drydocs-20260821.json", CAPTURED)
    v = check(_Boom, tmp_path)
    assert v.verdict is Verdict.UNREACHABLE and v.is_warning
    assert "ConnectionRefusedError" in v.detail
    assert "UNKNOWN, not fresh" in v.message() and "drydocs-20260821.json" in v.message()


class _Client:
    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def run(self, cypher, **params):
        assert "CodeModule" in cypher and "last_seen_at" in cypher
        return self.rows


def test_check_wires_probe_and_snapshot_into_the_comparison(tmp_path: Path) -> None:
    _write_snapshot(tmp_path, "drydocs-20260820.json", "2026-08-20T01:00:00")
    _write_snapshot(tmp_path, "drydocs-20260821.json", CAPTURED)  # newest wins
    fresh = check(
        lambda: _Client([{"last_seen_at": _local(CAPTURED) + timedelta(hours=1), "run_id": "r9"}]),
        tmp_path,
    )
    assert fresh.verdict is Verdict.FRESH and fresh.snapshot_name == "drydocs-20260821.json"
    empty = check(lambda: _Client([]), tmp_path)
    assert empty.verdict is Verdict.EMPTY_GRAPH
    assert newest_snapshot(tmp_path)[0] == "drydocs-20260821.json"
    assert newest_snapshot(tmp_path / "nope") == (None, None)


def _write_snapshot(directory: Path, name: str, captured_at: str) -> None:
    doc = {
        "schema": "depgraph-machine-first/v1",
        "projects": ["drydocs"],
        "meta": {
            "project": "drydocs",
            "captured_at": captured_at,
            "tree": False,
            "git": {"commit": "abc1234"},
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
            }
        ],
        "edges": [],
    }
    (directory / name).write_text(json.dumps(doc), encoding="utf-8")
