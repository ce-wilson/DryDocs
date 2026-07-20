"""Pure, framework-free handlers — the graph_verify idiom (offline-testable).

Every handler takes an explicit session store and a duck-typed GraphRunner;
FastAPI (app.py) is a thin wiring layer over these. Auth, read-only
enforcement, param validation, and database routing all happen HERE so the
behavior is provable without a server or a driver.
"""

from __future__ import annotations

from typing import Mapping, Protocol

from drydocs_api.guard import ensure_read_only
from drydocs_api.queries import named_query, validate_params
from drydocs_api.routing import database_for
from drydocs_api.sessions import InMemorySessionStore, Session


class GraphRunner(Protocol):
    """Duck-typed read executor; the live implementation pins READ routing."""

    def run(
        self, cypher: str, params: Mapping[str, object], database: str
    ) -> tuple[list[str], list[dict[str, object]]]: ...


class Forbidden(PermissionError):
    """Raised when the session's role may not use the endpoint."""


def login(persona_id: str, store: InMemorySessionStore) -> dict[str, str]:
    """Auth stub: exchange a synthetic persona id for a server session.
    (Company-side this whole handler is replaced by the OIDC code-for-token
    exchange — ADR 0005 Evidence.)"""
    session = store.issue(persona_id)
    return {"token": session.token, "persona_id": session.persona_id, "role": session.role}


def logout(token: str, store: InMemorySessionStore) -> None:
    store.revoke(token)


def _authenticate(token: str, store: InMemorySessionStore) -> Session:
    return store.resolve(token)  # raises InvalidTokenError


def run_named(
    query_id: str,
    params: dict[str, object],
    token: str,
    store: InMemorySessionStore,
    runner: GraphRunner,
) -> dict[str, object]:
    """Run a named view query: any authenticated role; params fail closed;
    database routed server-side; read-only asserted in depth."""
    _authenticate(token, store)
    query = named_query(query_id)
    bound = validate_params(query, params)
    ensure_read_only(query.cypher)  # defense in depth — named queries are ours, assert anyway
    database = database_for(query_id)
    keys, rows = runner.run(query.cypher, bound, database)
    return {"query_id": query_id, "database": database, "keys": keys, "rows": rows}


def run_raw(
    cypher: str,
    token: str,
    store: InMemorySessionStore,
    runner: GraphRunner,
) -> dict[str, object]:
    """Raw Cypher — ADMIN ONLY (the console's gated dev affordance, ADR 0005),
    write-guarded, database still routed server-side (never client-chosen)."""
    session = _authenticate(token, store)
    if session.role != "admin":
        raise Forbidden("raw Cypher is admin-only")
    ensure_read_only(cypher)
    database = database_for("raw-cypher")
    keys, rows = runner.run(cypher, {}, database)
    return {"query_id": "raw-cypher", "database": database, "keys": keys, "rows": rows}
