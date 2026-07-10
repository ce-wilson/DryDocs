"""Oracle adapter.

BMC Control-M and HR org-hierarchy load from Oracle in phase 1 (psgmgr
schema). Catalog tables (LOB, ProductLine, Product, DevTeam) and SEAL/PAT
in phase 2 use the same adapter — only the SQL changes.

Connection is established per-context; the cursor streams via ``arraysize``
so very large result sets don't blow memory.
"""
from __future__ import annotations

import logging
from typing import Any, Iterator

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
    ) -> None:
        self.user = user
        self.password = password
        self.dsn = dsn
        self.query = query
        self.bind_params = bind_params or {}
        self.arraysize = arraysize
        self.name = name or "oracle"
        self._conn = None  # type: ignore[assignment]
        self._cursor = None  # type: ignore[assignment]

    def __enter__(self) -> "OracleAdapter":
        # Lazy import so we don't require oracledb just to import the module.
        import oracledb  # noqa: PLC0415

        self._conn = oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)
        self._cursor = self._conn.cursor()
        self._cursor.arraysize = self.arraysize
        self._cursor.execute(self.query, self.bind_params)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        if self._cursor is not None:
            self._cursor.close()
            self._cursor = None
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def rows(self) -> Iterator[dict]:
        if self._cursor is None:
            raise RuntimeError("OracleAdapter must be used as a context manager")
        cols = [desc[0].lower() for desc in self._cursor.description]
        for row in self._cursor:
            yield dict(zip(cols, row))
