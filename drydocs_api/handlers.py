"""Pure, framework-free handlers — the graph_verify idiom (offline-testable).

Every handler takes an explicit session store and a duck-typed GraphRunner;
FastAPI (app.py) is a thin wiring layer over these. Auth, read-only
enforcement, param validation, and database routing all happen HERE so the
behavior is provable without a server or a driver.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from drydocs_api.credentials import BOOTSTRAP_HINT, CredentialChecker
from drydocs_api.guard import ensure_read_only
from drydocs_api.queries import named_query, validate_params
from drydocs_api.routing import database_for
from drydocs_api.sessions import InMemorySessionStore, Session


class GraphRunner(Protocol):
    """Duck-typed read executor; the live implementation pins READ routing."""

    def run(
        self, cypher: str, params: Mapping[str, object], database: str
    ) -> tuple[list[str], list[dict[str, object]]]: ...


def run_with_diagnostics(
    runner: GraphRunner, cypher: str, params: Mapping[str, object], database: str
) -> tuple[list[str], list[dict[str, object]], list[dict[str, object]]]:
    """R21: prefer a runner that carries the driver's notifications; a plain
    ``run`` runner (every duck-typed fake) yields an empty diagnostics list."""
    rich = getattr(runner, "run_with_diagnostics", None)
    if rich is not None:
        return rich(cypher, params, database)
    keys, rows = runner.run(cypher, params, database)
    return keys, rows, []


class Forbidden(PermissionError):
    """Raised when the session's role may not use the endpoint."""


class BadCredentialsError(PermissionError):
    """Raised when an identity or its secret does not check out.

    ONE error for both halves, deliberately. A caller must not be able to tell
    "no such account" from "wrong secret", because the difference is what turns
    a login endpoint into an account enumerator.
    """


class CredentialsNotConfiguredError(PermissionError):
    """Raised when this machine has no credential file yet — the fresh-clone
    state. Distinct from a bad secret because the fix is different: there is
    nothing to get right until somebody bootstraps an account."""


def login(
    persona_id: str,
    secret: str,
    store: InMemorySessionStore,
    credentials: CredentialChecker,
) -> dict[str, str]:
    """Exchange proof of a secret for a server session.

    The order matters. The secret is checked FIRST, against a store that pays
    the same derivation cost for an unknown id as for a real one, so neither
    the response nor its timing says whether the identity exists. Only then is
    the persona resolved and a token issued.

    Company-side this whole handler is replaced by the OIDC code-for-token
    exchange (ADR 0005 Evidence); everything above it — the session store, the
    role resolution, every route guard — is reused unchanged, which is the
    point of putting role resolution on the server in the first place.
    """
    if not credentials.is_bootstrapped:
        raise CredentialsNotConfiguredError(BOOTSTRAP_HINT)
    if not secret or not credentials.verify(persona_id, secret):
        raise BadCredentialsError("invalid credentials")
    session = store.issue(persona_id)
    return {
        "token": session.token,
        "persona_id": session.persona_id,
        "role": session.role,
        "expires_at": session.expires_at,
    }


def logout(token: str, store: InMemorySessionStore) -> None:
    store.revoke(token)


def authenticate(token: str, store: InMemorySessionStore) -> Session:
    """Resolve a bearer token to its session, or raise.

    The single authentication point for the whole API. ``store.resolve`` owns
    the expiry check, so no caller re-derives it and none can skip it; both
    unknown and expired raise ``InvalidTokenError`` (the expired case a
    subclass), which every route already maps to 401. This is the callable the
    FastAPI ``CurrentUser`` dependency wraps in ``app.py``.
    """
    return store.resolve(token)


#: Retained name for the handlers below, which read better with the private
#: spelling at the call site.
_authenticate = authenticate


def require_role(session: Session, *allowed: str) -> Session:
    """Assert the session holds one of ``allowed``; the basis of the admin-only
    and steward-or-admin route dependencies."""
    if session.role not in allowed:
        raise Forbidden(
            f"role '{session.role}' may not use this endpoint "
            f"(requires: {', '.join(sorted(allowed))})"
        )
    return session


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
    keys, rows, notes = run_with_diagnostics(runner, query.cypher, bound, database)
    return {
        "query_id": query_id,
        "database": database,
        "keys": keys,
        "rows": rows,
        "diagnostics": {"notifications": notes},
    }


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
    keys, rows, notes = run_with_diagnostics(runner, cypher, {}, database)
    return {
        "query_id": "raw-cypher",
        "database": database,
        "keys": keys,
        "rows": rows,
        "diagnostics": {"notifications": notes},
    }
