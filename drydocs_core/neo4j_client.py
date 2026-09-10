"""Neo4j driver wrapper.

Wraps the official ``neo4j`` driver with a thin context-manager interface.
All callers should use ``with Neo4jClient(...) as client:`` to ensure the
underlying driver is closed on exit.

CORE11 (2026-09-10) closed two of the three gaps the 2026-09-07 core report
named, and the ADR draft in the item file carries the third:

- **S2 — every read ran in a write transaction.** ``run`` was the only query
  method and it was unconditionally ``execute_write``, so a least-privilege
  read credential failed on ``RETURN apoc.version()`` and, in a cluster, every
  read routed to the leader. ``read`` is the second method; the four read
  helpers on this class use it.
- **S3 — the driver's own diagnostics were dropped.** ``run`` returned rows and
  discarded the result summary, so a query naming a mistyped label returned
  ``[]`` with no signal: empty-because-nothing-matched and
  empty-because-the-label-does-not-exist were the same value. The summary is
  now consumed on every path, converted through
  :mod:`drydocs_core.notifications` — the shape the API runner and the agents'
  read helper already share (R21) — logged at the driver's own severity, and
  kept on :attr:`last_notifications`.

Why ``run`` is still the WRITE path when the report suggested defaulting to
read: this method has some forty call sites across the loaders, most of them
writes, and a default flip would silently convert them. The migration of the
read-shaped call sites is an ADR action item, not this change.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase

from drydocs_core.notifications import Neo4jNotification, from_summary, to_payload

LOGGER = logging.getLogger("drydocs.neo4j_client")

#: Driver severity -> logger level. Kept EXPLICIT rather than flattened to one
#: level: an INFORMATION notification logged as a warning teaches readers that
#: this channel cries wolf, which is how the 2026-08-05 CI red went unread for a
#: week (Idea-111). An unknown severity logs as a warning — the safe direction.
_SEVERITY_LEVELS = {
    "WARNING": logging.WARNING,
    "INFORMATION": logging.INFO,
}


class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str, database: str | None = None) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._database = database
        self._driver = None
        #: The notifications the LAST statement carried (R21 shape). ``[]`` is a
        #: clean run, never a missing field. Reset at the start of every
        #: statement, so it always describes the most recent one.
        self.last_notifications: list[Neo4jNotification] = []

    def __enter__(self) -> Neo4jClient:
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

    def _record(self, summary: Any) -> list[Neo4jNotification]:
        """Convert, log and retain one statement's notifications.

        Never raises and never turns a non-fatal warning into a failure — that
        is R21's rule and it is not this method's to revisit. Logging is the
        channel that suits core's callers: a loader or a CLI verb has no
        response body to carry a payload in, so a dropped warning has nowhere
        else to surface.
        """
        notifications = from_summary(summary)
        self.last_notifications = notifications
        for note in notifications:
            LOGGER.log(
                _SEVERITY_LEVELS.get(note.severity.upper(), logging.WARNING),
                "neo4j %s %s: %s%s",
                note.severity or "notification",
                note.code,
                note.title or note.description,
                f" (at {note.position})" if note.position else "",
            )
        return notifications

    def _execute(self, cypher: str, bind: dict[str, Any], *, write: bool) -> list[dict[str, Any]]:
        assert self._driver is not None, "Use Neo4jClient as a context manager"
        self.last_notifications = []

        def work(tx: Any) -> list[dict[str, Any]]:
            result = tx.run(cypher, bind)
            rows = [dict(r) for r in result]
            # consume() AFTER the rows are drained: the summary is only complete
            # once the stream has been read to the end.
            self._record(result.consume())
            return rows

        with self._driver.session(database=self._database) as session:
            runner = session.execute_write if write else session.execute_read
            return runner(work)

    def run(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Run a single Cypher statement in a WRITE transaction, rows as dicts.

        Bind values may be supplied as a ``params`` dict, as keyword
        arguments, or both; kwargs win on key collision (matches the
        underlying driver's ``tx.run`` behavior).

        Use :meth:`read` for a query that only reads — this method demands write
        access, which a least-privilege credential will not have and which pins
        the query to the leader in a clustered topology.
        """
        return self._execute(cypher, {**(params or {}), **kwargs}, write=True)

    def read(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Run a single Cypher statement in a READ transaction, rows as dicts.

        The counterpart to :meth:`run`, with the same binding rules. CORE11/S2:
        before this existed, ``execute_read`` appeared nowhere in the first-party
        tree and every read in DryDocs ran inside a write transaction.
        """
        return self._execute(cypher, {**(params or {}), **kwargs}, write=False)

    def run_with_diagnostics(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
        *,
        write: bool = True,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Rows AND the driver's notifications, for a caller that wants them
        explicitly rather than off :attr:`last_notifications`.

        Named after ``LiveRunner.run_with_diagnostics`` in ``drydocs_api`` on
        purpose — same intent, and the ADR draft treats the pair as the seam's
        one convergence point. It differs in two ways, both stated rather than
        smoothed over: the API returns ``(keys, rows, notifications)`` because a
        JSON response needs the column order, and this takes binds through
        ``params`` only — ``run`` and ``read`` accept ``**kwargs`` as bind
        values, so any option keyword here would collide with a bind named after
        it.
        """
        rows = self._execute(cypher, dict(params or {}), write=write)
        return rows, to_payload(self.last_notifications)

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

        CORE11: the summary each ``consume()`` already returned was thrown away
        here too. It is now recorded, and because a script is many statements,
        :attr:`last_notifications` ends up holding the LAST statement's — the
        log carries all of them, which is the channel that matters for a
        bootstrap script nobody reads the return value of.
        """
        assert self._driver is not None, "Use Neo4jClient as a context manager"
        from drydocs_core.cypher_split import split_statements

        self.last_notifications = []
        with self._driver.session(database=self._database) as session:
            for statement in split_statements(script):
                self._record(session.run(statement, params or {}).consume())

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
        rows = self.read(
            "CALL dbms.components() YIELD name, versions "
            "WITH name, versions WHERE name = 'Neo4j Kernel' "
            "RETURN versions[0] AS v"
        )
        return rows[0]["v"] if rows else "unknown"

    def apoc_available(self) -> bool:
        """Return ``True`` if APOC procedures are reachable."""
        try:
            self.read("RETURN apoc.version() AS v")
            return True
        except Exception:
            return False

    def constraint_names(self) -> frozenset[str]:
        """Names from ``SHOW CONSTRAINTS`` — the D8 bootstrap guard keys on these."""
        return frozenset(r["name"] for r in self.read("SHOW CONSTRAINTS YIELD name RETURN name"))

    def constraints_detail(self) -> tuple[dict, ...]:
        """Name, kind, entity, labels and properties for every live constraint (G130).

        The INVERSE check needs more than names: a warning that says only
        "``membership_id`` is undeclared" sends the reader back to the database to
        find out what it enforces. The label and property are what let a human
        decide anything, and deciding is the only action this check ever asks for.
        """
        return tuple(
            dict(r)
            for r in self.read(
                "SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties "
                "RETURN name, type, entityType, labelsOrTypes, properties ORDER BY name"
            )
        )
