"""Oracle adapter.

BMC Control-M and HR org-hierarchy load from Oracle in phase 1 (psgmgr
schema). Catalog tables (LOB, ProductLine, Product, DevTeam) and SEAL/PAT
in phase 2 use the same adapter — only the SQL changes.

Connection is established per-context; the cursor streams via ``arraysize``
so very large result sets don't blow memory.

Every run writes a per-run SQL log (header -> handshake -> rendered SQL ->
CSV result) under ``SPIDERP_LOGDIR`` so the HITL can verify exactly what was
extracted — see :mod:`drydocs_core.adapters.sql_run_log`.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from .sql_run_log import SqlRunLog, render_sql

LOGGER = logging.getLogger(__name__)


class OracleAdapter:
    """Run a SQL query against Oracle and yield result rows as dicts.

    Parameters
    ----------
    user, password, dsn:
        Oracle connection coordinates.
    query:
        Parameterized SQL. Use ``:bind_name`` placeholders.
    bind_params:
        Mapping of bind names to values.
    arraysize:
        Cursor fetch size. 1000 is a good default for batch loads.
    name:
        Statement-batch name; becomes the run-log file base
        (``<name>.<yyyyMMdd-HHmmss>.log``).
    run_log:
        Write the per-run SQL log (default True). Execution is identical
        either way — the log is display-only.
    """

    def __init__(
        self,
        *,
        user: str,
        password: str,
        dsn: str,
        query: str,
        bind_params: dict[str, Any] | None = None,
        arraysize: int = 1000,
        name: str | None = None,
        run_log: bool = True,
    ) -> None:
        self.user = user
        self.password = password
        self.dsn = dsn
        self.query = query
        self.bind_params = bind_params or {}
        self.arraysize = arraysize
        self.name = name or "oracle"
        self.run_log = run_log
        self._conn = None  # type: ignore[assignment]
        self._cursor = None  # type: ignore[assignment]
        self._log: SqlRunLog | None = None

    def __enter__(self) -> OracleAdapter:
        # Lazy import so we don't require oracledb just to import the module.
        import oracledb

        if self.run_log:
            self._log = SqlRunLog(self.name, target=self.dsn, user=self.user)
            LOGGER.info("[sql-log] log: %s", self._log.open())
        try:
            self._conn = oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)
            if self._log is not None:
                self._log.handshake(f"Oracle Database {getattr(self._conn, 'version', '?')}")
            self._cursor = self._conn.cursor()
            self._cursor.arraysize = self.arraysize
            # Log the statement BEFORE executing so a failed extract still
            # leaves the attempted SQL on record for the HITL.
            if self._log is not None:
                self._log.statement(render_sql(self.query, self.bind_params), self.bind_params)
            self._cursor.execute(self.query, self.bind_params)
        except BaseException as exc:
            if self._log is not None:
                self._log.close(error=exc)
                self._log = None
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._log is not None:
            self._log.close(error=exc_val)
            self._log = None
        if self._cursor is not None:
            self._cursor.close()
            self._cursor = None
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def rows(self) -> Iterator[dict]:
        if self._cursor is None:
            raise RuntimeError("OracleAdapter must be used as a context manager")
        columns = [desc[0] for desc in self._cursor.description]
        cols = [c.lower() for c in columns]
        if self._log is not None:
            self._log.result_header(columns)
        for row in self._cursor:
            if self._log is not None:
                self._log.result_row(row)
            yield dict(zip(cols, row, strict=False))
