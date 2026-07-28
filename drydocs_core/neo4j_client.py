"""Neo4j driver wrapper.

Wraps the official ``neo4j`` driver with a thin context-manager interface.
All callers should use ``with Neo4jClient(...) as client:`` to ensure the
underlying driver is closed on exit.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase

LOGGER = logging.getLogger("drydocs.neo4j_client")


class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str, database: str | None = None) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._database = database
        self._driver = None

    def __enter__(self) -> "Neo4jClient":
        # liveness_check_timeout=0 forces the driver to re-validate pooled
        # connections before use, preventing SessionExpired on Aura.
        self._driver = GraphDatabase.driver(
            self._uri,
            auth=(self._user, self._password),
            liveness_check_timeout=0,
        )
        return self

    def __exit__(self, *_: Any) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def run(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Run a single Cypher statement and return rows as plain dicts.

        Bind values may be supplied as a ``params`` dict, as keyword
        arguments, or both; kwargs win on key collision (matches the
        underlying driver's ``tx.run`` behavior).
        """
        assert self._driver is not None, "Use Neo4jClient as a context manager"
        bind = {**(params or {}), **kwargs}
        with self._driver.session(database=self._database) as session:
            return session.execute_write(
                lambda tx: [dict(r) for r in tx.run(cypher, bind)]
            )

    def run_script(self, script: str, params: dict[str, Any] | None = None) -> None:
        """Run a multi-statement Cypher script, split CLIENT-SIDE (D5).

        Statements are separated on code semicolons only — the shared
        comment/string-aware scanner (``drydocs_core.cypher_split``) — so a
        ``;`` inside a ``//`` comment can never shear a statement, the
        apoc.cypher.runMany landmine that Cypher 25 turns into a hard error
        (it rejects the empty fragment). Each statement runs in its own
        auto-commit transaction, so DDL (CREATE CONSTRAINT) and DML (MERGE)
        can coexist in the same file, and comment-only fragments are dropped
        rather than sent to the server. The optional ``params`` dict is
        forwarded to every statement as the binding map.
        """
        assert self._driver is not None, "Use Neo4jClient as a context manager"
        from drydocs_core.cypher_split import split_statements

        with self._driver.session(database=self._database) as session:
            for statement in split_statements(script):
                session.run(statement, params or {}).consume()

    def execute_file(self, path: Path) -> None:
        """Read *path* and execute it via :meth:`run_script`."""
        script = path.read_text(encoding="utf-8")
        LOGGER.debug("Executing %s (%d chars)", path.name, len(script))
        self.run_script(script)

    def connection_info(self) -> dict[str, str]:
        """Return the URI, user, and database (no password)."""
        return {"uri": self._uri, "user": self._user, "database": self._database or "(home)"}

    def server_version(self) -> str:
        """Return the Neo4j kernel version string (e.g. ``'5.20.0'``)."""
        rows = self.run(
            "CALL dbms.components() YIELD name, versions "
            "WITH name, versions WHERE name = 'Neo4j Kernel' "
            "RETURN versions[0] AS v"
        )
        return rows[0]["v"] if rows else "unknown"

    def apoc_available(self) -> bool:
        """Return ``True`` if APOC procedures are reachable."""
        try:
            self.run("RETURN apoc.version() AS v")
            return True
        except Exception:
            return False

    def constraint_names(self) -> frozenset[str]:
        """Names from ``SHOW CONSTRAINTS`` — the D8 bootstrap guard keys on these."""
        return frozenset(r["name"] for r in self.run("SHOW CONSTRAINTS YIELD name RETURN name"))
