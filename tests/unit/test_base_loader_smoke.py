"""Smoke test for the BaseLoader runtime path.

Locks in the Neo4jClient API contract that BaseLoader depends on — namely
that ``run`` accepts bind values as keyword arguments and ``run_script``
accepts a ``params`` dict. A signature regression on either method (the
historic state where ``run`` was ``(cypher, params=None)`` and
``run_script`` was ``(script)``) would crash every loader at runtime; this
test forces that to surface in CI rather than in production.
"""
from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, ClassVar, Iterator

import pytest
from pydantic import BaseModel

from drydocs.loaders.base import BaseLoader
from drydocs.neo4j_client import Neo4jClient


# ---- in-memory fakes -------------------------------------------------------

class _FakeAdapter:
    """Minimal Adapter that yields a fixed list of dicts."""

    name = "fake:smoke"

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __enter__(self) -> "_FakeAdapter":
        return self

    def __exit__(self, *_: Any) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        yield from self._rows


class _FakeNeo4jClient:
    """Captures every call so the test can assert on bind values."""

    def __init__(self) -> None:
        self.run_calls: list[tuple[str, dict]] = []
        self.run_script_calls: list[tuple[str, dict]] = []

    def run(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict]:
        bind = {**(params or {}), **kwargs}
        self.run_calls.append((cypher, bind))
        return []

    def run_script(self, script: str, params: dict[str, Any] | None = None) -> None:
        self.run_script_calls.append((script, dict(params or {})))


class _SmokeRow(BaseModel):
    id: str
    value: int


class _SingleStatementLoader(BaseLoader):
    """Single-MERGE cypher → routes through ``run`` with kwarg binds."""

    name: ClassVar[str] = "smoke.single.v1"
    cypher_path: ClassVar[Path | None] = Path(__file__).parent / "_smoke_single.cypher"
    row_model: ClassVar[type[BaseModel]] = _SmokeRow
    source_label: ClassVar[str] = "csv"


class _MultiStatementLoader(BaseLoader):
    """Multi-statement cypher → routes through ``run_script``."""

    name: ClassVar[str] = "smoke.multi.v1"
    cypher_path: ClassVar[Path | None] = Path(__file__).parent / "_smoke_multi.cypher"
    row_model: ClassVar[type[BaseModel]] = _SmokeRow
    source_label: ClassVar[str] = "csv"


@pytest.fixture
def smoke_cypher_files(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Create the cypher template files the loaders point at."""
    single = _SingleStatementLoader.cypher_path
    multi = _MultiStatementLoader.cypher_path
    assert single is not None and multi is not None
    single.write_text("UNWIND $batch AS row MERGE (n:Smoke {id: row.id})", encoding="utf-8")
    multi.write_text(
        "UNWIND $batch AS row MERGE (n:Smoke {id: row.id});\n"
        "MATCH (n:Smoke) SET n.touched_by = $loader;",
        encoding="utf-8",
    )
    yield
    single.unlink(missing_ok=True)
    multi.unlink(missing_ok=True)


# ---- signature contract ----------------------------------------------------

def test_neo4j_client_run_accepts_kwargs() -> None:
    """BaseLoader._open_run / _close_run pass bind values as kwargs.

    If this contract regresses (``run`` reverts to ``(cypher, params=None)``
    with no kwargs), every loader call fails with ``TypeError``.
    """
    sig = inspect.signature(Neo4jClient.run)
    kinds = {p.kind for p in sig.parameters.values()}
    assert inspect.Parameter.VAR_KEYWORD in kinds, (
        "Neo4jClient.run must accept **kwargs for keyword-style bind values"
    )


def test_neo4j_client_run_script_accepts_params() -> None:
    """BaseLoader._flush calls ``run_script(cypher, params=...)`` for
    multi-statement templates; the method must accept that arg."""
    sig = inspect.signature(Neo4jClient.run_script)
    assert "params" in sig.parameters, (
        "Neo4jClient.run_script must accept a params kwarg"
    )


# ---- end-to-end smoke -------------------------------------------------------

def test_single_statement_loader_runs_end_to_end(smoke_cypher_files: None) -> None:
    client = _FakeNeo4jClient()
    adapter = _FakeAdapter([{"id": "a", "value": 1}, {"id": "b", "value": 2}])

    summary = _SingleStatementLoader(client, adapter, batch_size=10).load()

    assert summary.status == "OK"
    assert summary.rows_processed == 2
    assert summary.rows_rejected == 0

    # _open_run + _flush + _close_run = 3 calls minimum, all via run() because
    # the cypher has a single statement.
    assert len(client.run_calls) >= 3
    assert client.run_script_calls == []

    # _flush sent the batch + provenance kwargs through run()'s **kwargs path.
    flush_call = next(
        (cypher, bind) for cypher, bind in client.run_calls if "UNWIND $batch" in cypher
    )
    _, bind = flush_call
    assert bind["run_id"] == summary.run_id
    assert bind["loader"] == "smoke.single.v1"
    assert bind["source_label"] == "csv"
    assert [r["id"] for r in bind["batch"]] == ["a", "b"]


def test_multi_statement_loader_routes_to_run_script(smoke_cypher_files: None) -> None:
    client = _FakeNeo4jClient()
    adapter = _FakeAdapter([{"id": "a", "value": 1}])

    summary = _MultiStatementLoader(client, adapter).load()

    assert summary.status == "OK"
    assert summary.rows_processed == 1
    # Multi-statement template → _flush uses run_script with the params dict.
    assert len(client.run_script_calls) == 1
    _, params = client.run_script_calls[0]
    assert params["loader"] == "smoke.multi.v1"
    assert params["run_id"] == summary.run_id
    assert params["batch"] == [{"id": "a", "value": 1}]


def test_invalid_rows_are_rejected_not_raised(smoke_cypher_files: None) -> None:
    client = _FakeNeo4jClient()
    adapter = _FakeAdapter([
        {"id": "good", "value": 1},
        {"id": "bad", "value": "not-an-int"},
    ])

    summary = _SingleStatementLoader(client, adapter).load()

    assert summary.status == "OK"
    assert summary.rows_processed == 1
    assert summary.rows_rejected == 1
    assert summary.rejects[0]["row_index"] == 1
