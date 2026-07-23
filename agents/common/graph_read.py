"""Server-enforced read-only Cypher execution (ADR 0007 decision 2).

The token guards (``neo4j_tool._WRITE_TOKENS``, ``drydocs_api.guard``) are
fast pre-flights, NOT the boundary: both are evadable (e.g. ``CREATE(x)``
without a space slips the agents guard; ``CALL db.createLabel(...)`` slips
both). The boundary is here — every query runs inside a READ-access-mode
managed transaction, so the SERVER rejects any write that reaches it,
regardless of spelling. Row cap and a server-side transaction timeout apply
to every call (tests/integration/test_graph_qa_read_mode.py proves the
rejection against a live graph).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import neo4j

from common.neo4j_tool import get_driver

DEFAULT_ROW_CAP = 100
DEFAULT_TIMEOUT_S = 15.0


class CypherReadError(RuntimeError):
    """A query failed (syntax, semantics, or write-in-read-mode). Message feeds the fix loop."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class ReadResult:
    records: list[dict] = field(default_factory=list)
    keys: list[str] = field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    ms: int = 0


def run_read(
    cypher: str,
    params: dict | None = None,
    database: str | None = None,
    row_cap: int = DEFAULT_ROW_CAP,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> ReadResult:
    """Execute ``cypher`` in a READ-mode transaction; raise CypherReadError on failure."""
    db = database or os.getenv("NEO4J_DATABASE", "drydocs")
    started = time.perf_counter()

    @neo4j.unit_of_work(timeout=timeout_s)
    def _work(tx: neo4j.ManagedTransaction) -> tuple[list[dict], list[str], bool]:
        result = tx.run(cypher, **(params or {}))
        rows: list[dict] = []
        truncated = False
        for record in result:
            if len(rows) >= row_cap:
                truncated = True
                break
            rows.append(record.data())
        return rows, list(result.keys()), truncated

    try:
        with get_driver().session(
            database=db, default_access_mode=neo4j.READ_ACCESS
        ) as session:
            rows, keys, truncated = session.execute_read(_work)
    except neo4j.exceptions.Neo4jError as exc:
        raise CypherReadError(str(exc), code=getattr(exc, "code", None)) from exc
    except Exception as exc:  # driver/transport errors — same fix-loop path
        raise CypherReadError(f"{type(exc).__name__}: {exc}") from exc

    return ReadResult(
        records=rows,
        keys=keys,
        row_count=len(rows),
        truncated=truncated,
        ms=int((time.perf_counter() - started) * 1000),
    )
