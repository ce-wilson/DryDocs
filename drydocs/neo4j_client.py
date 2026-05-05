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

    def run(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Run a single Cypher statement and return rows as plain dicts."""
        assert self._driver is not None, "Use Neo4jClient as a context manager"
        with self._driver.session(database=self._database) as session:
            return session.execute_write(
                lambda tx: [dict(r) for r in tx.run(cypher, params or {})]
            )

    def run_script(self, script: str) -> None:
        """Run a multi-statement Cypher script via ``apoc.cypher.runMany``.

        Each statement in *script* must be terminated by a semicolon.
        APOC runs each statement in its own transaction, so DDL (CREATE
        CONSTRAINT) and DML (MERGE) can coexist in the same file.
        """
        assert self._driver is not None, "Use Neo4jClient as a context manager"
        with self._driver.session(database=self._database) as session:
            session.execute_write(
                lambda tx: tx.run(
                    "CALL apoc.cypher.runMany($script, {}) YIELD row RETURN row",
                    {"script": script},
                ).consume()
            )

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
