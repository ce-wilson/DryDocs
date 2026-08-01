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
from collections.abc import Iterator
from pathlib import Path
from typing import Any, ClassVar

import pytest
from pydantic import BaseModel

from drydocs.loaders.base import BaseLoader
from drydocs_core.neo4j_client import Neo4jClient

# ---- in-memory fakes -------------------------------------------------------


class _FakeAdapter:
    """Minimal Adapter that yields a fixed list of dicts."""

    name = "fake:smoke"

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __enter__(self) -> _FakeAdapter:
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
    assert (
        inspect.Parameter.VAR_KEYWORD in kinds
    ), "Neo4jClient.run must accept **kwargs for keyword-style bind values"


def test_neo4j_client_run_script_accepts_params() -> None:
    """BaseLoader._flush calls ``run_script(cypher, params=...)`` for
    multi-statement templates; the method must accept that arg."""
    sig = inspect.signature(Neo4jClient.run_script)
    assert "params" in sig.parameters, "Neo4jClient.run_script must accept a params kwarg"


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


def test_close_run_records_rows_changed_from_edge_count(smoke_cypher_files: None) -> None:
    """_close_run counts WAS_GENERATED_BY edges attached to this run's
    :JobRun and records the total as rows_changed on both the node and the
    LoadSummary (doc 06 Phase 2 — provenance-edge diet full-refresh
    accounting). Since Cypher templates now write the edge only on
    create/change, this count IS the changed-row total for the run."""

    class _ChangeCountingClient(_FakeNeo4jClient):
        def run(
            self, cypher: str, params: dict[str, Any] | None = None, **kwargs: Any
        ) -> list[dict]:
            bind = {**(params or {}), **kwargs}
            self.run_calls.append((cypher, bind))
            if "rows_changed" in cypher:
                return [{"rows_changed": 1}]
            return []

    client = _ChangeCountingClient()
    adapter = _FakeAdapter([{"id": "a", "value": 1}, {"id": "b", "value": 2}])

    summary = _SingleStatementLoader(client, adapter, batch_size=10).load()

    assert summary.rows_changed == 1
    assert summary.as_dict()["rows_changed"] == 1
    close_call = next(
        (cypher, bind) for cypher, bind in client.run_calls if "rows_changed" in cypher
    )
    _, bind = close_call
    assert bind["run_id"] == summary.run_id
    assert "WAS_GENERATED_BY" in close_call[0]


def test_close_run_rows_changed_defaults_to_zero_with_no_result(smoke_cypher_files: None) -> None:
    """If the client returns no rows for the close-run query (e.g. the fake
    client's default), rows_changed stays at its LoadSummary default rather
    than raising."""
    client = _FakeNeo4jClient()
    adapter = _FakeAdapter([{"id": "a", "value": 1}])

    summary = _SingleStatementLoader(client, adapter).load()

    assert summary.rows_changed == 0


def test_preflight_runs_show_indexes_before_any_write(smoke_cypher_files: None) -> None:
    """The index preflight (advisor-confirmation §2c) is the FIRST client call
    — before _open_run — so a refused load leaves the graph untouched."""
    client = _FakeNeo4jClient()
    adapter = _FakeAdapter([{"id": "a", "value": 1}])

    _SingleStatementLoader(client, adapter).load()

    first_cypher, _ = client.run_calls[0]
    assert "SHOW INDEXES" in first_cypher


def test_preflight_raises_on_failed_index(smoke_cypher_files: None) -> None:
    """A FAILED index aborts the load with nothing written — no :JobRun,
    no batch flush."""

    class _FailedIndexClient(_FakeNeo4jClient):
        def run(
            self, cypher: str, params: dict[str, Any] | None = None, **kwargs: Any
        ) -> list[dict]:
            bind = {**(params or {}), **kwargs}
            self.run_calls.append((cypher, bind))
            if "SHOW INDEXES" in cypher:
                return [{"name": "job_name", "state": "FAILED", "labelsOrTypes": ["ControlMJob"]}]
            return []

    client = _FailedIndexClient()
    adapter = _FakeAdapter([{"id": "a", "value": 1}])

    with pytest.raises(RuntimeError, match="FAILED index"):
        _SingleStatementLoader(client, adapter).load()

    # Only the SHOW INDEXES probe ran — the graph was never written.
    assert len(client.run_calls) == 1
    assert client.run_script_calls == []


def test_preflight_awaits_populating_index_then_loads(smoke_cypher_files: None) -> None:
    """A POPULATING index blocks via db.awaitIndexes instead of racing it;
    the load then proceeds normally."""

    class _PopulatingIndexClient(_FakeNeo4jClient):
        def run(
            self, cypher: str, params: dict[str, Any] | None = None, **kwargs: Any
        ) -> list[dict]:
            bind = {**(params or {}), **kwargs}
            self.run_calls.append((cypher, bind))
            if "SHOW INDEXES" in cypher:
                return [
                    {"name": "job_name", "state": "POPULATING", "labelsOrTypes": ["ControlMJob"]}
                ]
            return []

    client = _PopulatingIndexClient()
    adapter = _FakeAdapter([{"id": "a", "value": 1}])

    summary = _SingleStatementLoader(client, adapter, index_wait_seconds=42).load()

    assert summary.status == "OK"
    await_call = next(
        (cypher, bind) for cypher, bind in client.run_calls if "db.awaitIndexes" in cypher
    )
    assert await_call[1]["seconds"] == 42


def test_invalid_rows_are_rejected_not_raised(smoke_cypher_files: None) -> None:
    client = _FakeNeo4jClient()
    adapter = _FakeAdapter(
        [
            {"id": "good", "value": 1},
            {"id": "bad", "value": "not-an-int"},
        ]
    )

    summary = _SingleStatementLoader(client, adapter).load()

    assert summary.status == "OK"
    assert summary.rows_processed == 1
    assert summary.rows_rejected == 1
    assert summary.rejects[0]["row_index"] == 1


def test_code_semicolons_ignores_comments_and_strings() -> None:
    """runMany dispatch (J9 e2e finding): a ';' inside a // comment routed a
    single-statement template to apoc.cypher.runMany, which split it mid-comment."""
    from drydocs.loaders.base import _code_semicolons

    single = (
        "UNWIND $batch AS row\n"
        "// kept alongside the raw-named props above; retires in doc-06 Phase 3\n"
        "MERGE (f:Thing {id: row.id})\n"
        "SET f.note = 'a ; in a string', f.other = \"another ; here\"\n"
        "/* block comment; with a semicolon */\n"
        ";\n"
    )
    assert _code_semicolons(single) == 1  # only the terminator counts

    multi = "CREATE CONSTRAINT x IF NOT EXISTS FOR (n:A) REQUIRE n.id IS UNIQUE;\nMERGE (n:A {id: 1});\n"
    assert _code_semicolons(multi) == 2

    # the real template that broke: single statement despite its comment ';'
    from pathlib import Path

    folders = (
        Path(__file__).resolve().parents[2]
        / "drydocs"
        / "loaders"
        / "cypher"
        / "controlm_folders.cypher"
    )
    assert _code_semicolons(folders.read_text(encoding="utf-8")) <= 1
