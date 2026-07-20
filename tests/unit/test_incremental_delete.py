"""D7 — incremental-delete path: soft-delete mark + retention sweep.

Duck-typed client (the graph_verify idiom, no live DB): the tests assert the
queries BaseLoader._mark_removed and sweep_removed() actually issue — scope
binding, mark/reactivate shapes, count reporting — since the graph-side
semantics are plain Cypher over the run bookkeeping every template writes
(last_run_id / last_seen_at).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Iterator

import pytest
from pydantic import BaseModel

from drydocs.loaders.base import BaseLoader, sweep_removed


class _FakeAdapter:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __enter__(self) -> "_FakeAdapter":
        return self

    def __exit__(self, *_: Any) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        yield from self._rows


class _FakeClient:
    """Answers the mark/reactivate/sweep count queries; records every call."""

    def __init__(self, *, marked: int = 0, reactivated: int = 0, swept: int = 0,
                 retained: int = 0) -> None:
        self.marked = marked
        self.reactivated = reactivated
        self.swept = swept
        self.retained = retained
        self.run_calls: list[tuple[str, dict]] = []
        self.run_script_calls: list[tuple[str, dict]] = []

    def run(self, cypher: str, params: dict[str, Any] | None = None,
            **kwargs: Any) -> list[dict]:
        bind = {**(params or {}), **kwargs}
        self.run_calls.append((cypher, bind))
        if "AS marked" in cypher:
            return [{"marked": self.marked}]
        if "AS reactivated" in cypher:
            return [{"reactivated": self.reactivated}]
        if "AS swept" in cypher:
            return [{"swept": self.swept}]
        if "AS retained" in cypher:
            return [{"retained": self.retained}]
        return []

    def run_script(self, script: str, params: dict[str, Any] | None = None) -> None:
        self.run_script_calls.append((script, dict(params or {})))

    def mark_calls(self) -> list[tuple[str, dict]]:
        return [(c, b) for c, b in self.run_calls if "removed_from_source_at = datetime" in c]

    def reactivate_calls(self) -> list[tuple[str, dict]]:
        return [(c, b) for c, b in self.run_calls if "removed_from_source_at = null" in c]


class _Row(BaseModel):
    folder_id: str
    job_id: str


_CYPHER = Path(__file__).parent / "_sweep_smoke.cypher"


class _ScopedLoader(BaseLoader):
    """Jobs-style: extract declares coverage per folder_id."""

    name: ClassVar[str] = "sweep.scoped.v1"
    cypher_path: ClassVar[Path | None] = _CYPHER
    row_model: ClassVar[type[BaseModel]] = _Row
    sweep_label: ClassVar[str | None] = "SweepJob"
    sweep_scope_property: ClassVar[str | None] = "folder_id"


class _UnscopedLoader(BaseLoader):
    """Folders-style: no scope property — marks only under full_extract."""

    name: ClassVar[str] = "sweep.unscoped.v1"
    cypher_path: ClassVar[Path | None] = _CYPHER
    row_model: ClassVar[type[BaseModel]] = _Row
    sweep_label: ClassVar[str | None] = "SweepJob"


@pytest.fixture(autouse=True)
def sweep_cypher_file():
    _CYPHER.write_text(
        "UNWIND $batch AS row MERGE (n:SweepJob {folder_id: row.folder_id, job_id: row.job_id})",
        encoding="utf-8",
    )
    yield
    _CYPHER.unlink(missing_ok=True)


ROWS = [
    {"folder_id": "F1", "job_id": "J1"},
    {"folder_id": "F1", "job_id": "J2"},
    {"folder_id": "F2", "job_id": "J9"},
]


def test_mark_pass_runs_scoped_to_the_extracts_folders() -> None:
    """Graph-minus-extract via last_run_id, bounded to the folders the extract
    actually carried — a filtered extract can never mark out-of-scope nodes."""
    client = _FakeClient(marked=2)
    summary = _ScopedLoader(client, _FakeAdapter(ROWS)).load()

    (cypher, bind), = client.mark_calls()
    assert "MATCH (n:SweepJob)" in cypher
    assert "n.last_run_id IS NULL OR n.last_run_id <> $run_id" in cypher
    assert "n.folder_id IN $scope_values" in cypher  # the scoping clause
    assert bind["scope_values"] == ["F1", "F2"]      # exactly the extract's folders
    assert "removed_by_run_id" in cypher             # mark = property + run id
    assert summary.nodes_marked_removed == 2         # reported, never silent


def test_reappeared_nodes_get_their_mark_cleared() -> None:
    client = _FakeClient(reactivated=1)
    summary = _ScopedLoader(client, _FakeAdapter(ROWS)).load()

    (cypher, bind), = client.reactivate_calls()
    assert "n.last_run_id = $run_id" in cypher            # only nodes seen THIS run
    assert "removed_from_source_at = null" in cypher      # the mark is cleared
    assert bind["run_id"] == summary.run_id
    assert summary.nodes_reactivated == 1


def test_counts_land_on_the_jobrun_envelope() -> None:
    client = _FakeClient(marked=3, reactivated=1)
    _ScopedLoader(client, _FakeAdapter(ROWS)).load()

    close_call = next(b for c, b in client.run_calls if "nodes_marked_removed" in c)
    assert close_call["nodes_marked_removed"] == 3
    assert close_call["nodes_reactivated"] == 1


def test_unscoped_loader_marks_nothing_without_full_extract_declaration() -> None:
    """A filtered extract must not mark: without a scope property, only the
    caller knows coverage — no full_extract, no mark pass."""
    client = _FakeClient(marked=99)
    summary = _UnscopedLoader(client, _FakeAdapter(ROWS)).load()

    assert client.mark_calls() == []
    assert client.reactivate_calls() == []
    assert summary.nodes_marked_removed == 0


def test_unscoped_loader_marks_globally_under_full_extract() -> None:
    client = _FakeClient(marked=1)
    summary = _UnscopedLoader(client, _FakeAdapter(ROWS), full_extract=True).load()

    (cypher, bind), = client.mark_calls()
    assert "IN $scope_values" not in cypher  # full population, no scope clause
    assert "scope_values" not in bind
    assert summary.nodes_marked_removed == 1


def test_empty_extract_declares_nothing_and_marks_nothing() -> None:
    """An empty extract is indistinguishable from a broken one — never treat
    it as 'everything was removed'."""
    client = _FakeClient(marked=99)
    summary = _ScopedLoader(client, _FakeAdapter([])).load()

    assert client.mark_calls() == []
    assert summary.nodes_marked_removed == 0


def test_loader_without_sweep_label_is_untouched_by_d7() -> None:
    class _Plain(BaseLoader):
        name: ClassVar[str] = "sweep.plain.v1"
        cypher_path: ClassVar[Path | None] = _CYPHER
        row_model: ClassVar[type[BaseModel]] = _Row

    client = _FakeClient()
    _Plain(client, _FakeAdapter(ROWS), full_extract=True).load()
    assert client.mark_calls() == []


# ---------------------------------------------------------------------------
# retention sweep
# ---------------------------------------------------------------------------

def test_sweep_deletes_only_past_retention_and_reports_counts() -> None:
    client = _FakeClient(swept=4, retained=2)
    counts = sweep_removed(client, "SweepJob", older_than_days=30)

    (cypher, bind), = [(c, b) for c, b in client.run_calls if "DETACH DELETE" in c]
    assert "removed_from_source_at < datetime() - duration({days: $days})" in cypher
    assert bind["days"] == 30
    assert counts == {"swept": 4, "retained": 2}


def test_sweep_dry_run_deletes_nothing() -> None:
    client = _FakeClient(swept=4, retained=6)
    counts = sweep_removed(client, "SweepJob", older_than_days=7, dry_run=True)

    assert all("DETACH DELETE" not in c for c, _ in client.run_calls)
    assert counts == {"swept": 4, "retained": 6}
