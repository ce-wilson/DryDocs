"""FastAPI wiring for drydocs-api — the ONLY module that touches a framework
or a live driver. Everything it exposes is a thin shell over handlers.py.

FastAPI/uvicorn are an OPTIONAL dependency group (``poetry install --with api``)
so the default install and the unit suite stay framework-free. Run it:

    poetry install --with api
    poetry run uvicorn drydocs_api.app:create_app --factory --port 8001

Credentials come from server env (NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD via
drydocs_core.config.Neo4jSettings) — never from a request, never in a browser.
"""

# NOTE: no `from __future__ import annotations` here — FastAPI resolves route
# annotations at runtime via get_type_hints, and PEP-563 string annotations
# break body-model detection (a body silently becomes a query param).

from typing import Mapping, Optional

import neo4j
from pydantic import BaseModel

from drydocs_core.config import Neo4jSettings

from drydocs_api.guard import WriteRejected
from drydocs_api.handlers import Forbidden, login, logout, run_named, run_raw
from drydocs_api.personas import UnknownPersonaError
from drydocs_api.queries import NAMED_QUERIES, ParamValidationError, UnknownQueryError
from drydocs_api.sessions import InMemorySessionStore, InvalidTokenError


class LoginBody(BaseModel):
    persona_id: str


class QueryBody(BaseModel):
    params: dict = {}


class RawBody(BaseModel):
    cypher: str


class LiveRunner:
    """The real GraphRunner: one server-side driver, READ routing pinned —
    the second defense layer behind the endpoint guard."""

    def __init__(self, settings: Optional[Neo4jSettings] = None) -> None:
        s = settings or Neo4jSettings()
        self._driver = neo4j.GraphDatabase.driver(
            s.uri, auth=(s.user, s.password.get_secret_value())
        )

    def run(
        self, cypher: str, params: Mapping[str, object], database: str
    ) -> tuple[list[str], list[dict[str, object]]]:
        result = self._driver.execute_query(
            cypher,
            parameters_=dict(params),
            database_=database,
            routing_=neo4j.RoutingControl.READ,
        )
        return list(result.keys), [r.data() for r in result.records]

    def close(self) -> None:
        self._driver.close()


def create_app(runner=None, store: Optional[InMemorySessionStore] = None):
    """App factory. ``runner``/``store`` are injectable for tests; the default
    is the live driver + a fresh in-memory session store."""
    from fastapi import FastAPI, Header, HTTPException
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="drydocs-api", description="Thin read API over the knowledge graph (ADR 0005)")
    # The web console dev server is the only expected browser origin today.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:4173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    sessions = store if store is not None else InMemorySessionStore()
    graph = runner if runner is not None else LiveRunner()

    def _token(authorization: Optional[str]) -> str:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(401, "missing bearer token")
        return authorization.split(" ", 1)[1]

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/queries")
    def queries() -> list[dict[str, object]]:
        return [
            {
                "id": q.id,
                "description": q.description,
                "params": [
                    {"name": p.name, "type": p.type, "required": p.required, "default": p.default}
                    for p in q.params
                ],
            }
            for q in NAMED_QUERIES.values()
        ]

    @app.post("/login")
    def post_login(body: LoginBody) -> dict[str, str]:
        try:
            return login(body.persona_id, sessions)
        except UnknownPersonaError:
            raise HTTPException(401, "unknown persona") from None

    @app.post("/logout")
    def post_logout(authorization: str | None = Header(default=None)) -> dict[str, str]:
        logout(_token(authorization), sessions)
        return {"status": "ok"}

    @app.post("/query/{query_id}")
    def post_query(
        query_id: str, body: QueryBody, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        try:
            return run_named(query_id, body.params, _token(authorization), sessions, graph)
        except InvalidTokenError:
            raise HTTPException(401, "invalid session") from None
        except UnknownQueryError:
            raise HTTPException(404, f"unknown query '{query_id}'") from None
        except ParamValidationError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.post("/raw-cypher")
    def post_raw(body: RawBody, authorization: str | None = Header(default=None)) -> dict[str, object]:
        try:
            return run_raw(body.cypher, _token(authorization), sessions, graph)
        except InvalidTokenError:
            raise HTTPException(401, "invalid session") from None
        except Forbidden as exc:
            raise HTTPException(403, str(exc)) from None
        except WriteRejected as exc:
            raise HTTPException(400, str(exc)) from None

    return app
