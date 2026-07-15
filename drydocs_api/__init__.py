"""drydocs-api — the thin API over the knowledge graph (ADR 0005, backlog O5).

The deployment-shape access path for the web console: server-side Neo4j driver
(credentials from server env, never a browser), READ-ONLY enforcement and
per-view database routing at the endpoint layer, named queries shaped for the
console's views, and a session-auth stub (synthetic personas server-side;
enterprise OIDC is a company-side twin per the ADR's Evidence section).

Component rules (ADR 0002 components-on-core): imports ``drydocs_core`` only;
never another component. All handler logic is pure and framework-free
(``handlers.py``); FastAPI wiring lives in ``app.py`` behind an optional
dependency group (``poetry install --with api``).
"""

from drydocs_api.guard import WriteRejected, ensure_read_only
from drydocs_api.handlers import login, logout, run_named, run_raw
from drydocs_api.routing import database_for
from drydocs_api.sessions import InMemorySessionStore

__all__ = [
    "WriteRejected",
    "ensure_read_only",
    "login",
    "logout",
    "run_named",
    "run_raw",
    "database_for",
    "InMemorySessionStore",
]
