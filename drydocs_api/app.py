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

from collections.abc import Mapping
from pathlib import Path

import neo4j
from pydantic import BaseModel

from drydocs_api.exports import (
    ExportLedger,
    UnknownExportError,
    export_manifest,
    export_spec,
    list_specs,
    run_spec,
)
from drydocs_api.guard import WriteRejected
from drydocs_api.handlers import Forbidden, login, logout, run_named, run_raw
from drydocs_api.query_specs import UnknownSpecError
from drydocs_api.mappings import (
    ChangesetValidationError,
    MappingStore,
    UnknownDomainError,
    draft_changeset,
    draft_override,
    list_domains,
    mapping_grid,
    mapping_options,
    source_corrections_report,
)
from drydocs_api.personas import UnknownPersonaError
from drydocs_api.queries import NAMED_QUERIES, ParamValidationError, UnknownQueryError
from drydocs_api.sessions import InMemorySessionStore, InvalidTokenError
from drydocs_core.config import Neo4jSettings


class LoginBody(BaseModel):
    persona_id: str


class QueryBody(BaseModel):
    params: dict = {}


class RawBody(BaseModel):
    cypher: str


class ChangesetBody(BaseModel):
    entries: list = []


class LiveRunner:
    """The real GraphRunner: one server-side driver, READ routing pinned —
    the second defense layer behind the endpoint guard. The driver is created
    LAZILY on first graph query so mapping-store-only sessions (O13 demo, no
    Neo4j configured) can still serve /mappings/*."""

    def __init__(self, settings: Neo4jSettings | None = None) -> None:
        self._settings = settings
        self._driver: neo4j.Driver | None = None

    @property
    def driver(self) -> neo4j.Driver:
        if self._driver is None:
            s = self._settings or Neo4jSettings()
            self._driver = neo4j.GraphDatabase.driver(
                s.uri, auth=(s.user, s.password.get_secret_value())
            )
        return self._driver

    def run(
        self, cypher: str, params: Mapping[str, object], database: str
    ) -> tuple[list[str], list[dict[str, object]]]:
        result = self.driver.execute_query(
            cypher,
            parameters_=dict(params),
            database_=database,
            routing_=neo4j.RoutingControl.READ,
        )
        return list(result.keys), [r.data() for r in result.records]

    def stream(self, cypher: str, params: Mapping[str, object], database: str):
        """Driver streaming for exports (O11): rows are yielded as the driver
        fetches them — NOT apoc.export (which writes on the DB server) and NOT
        a buffered execute_query. READ access is pinned at the session, which
        stays open for the generator's lifetime and closes when it finishes."""
        session = self.driver.session(database=database, default_access_mode=neo4j.READ_ACCESS)
        try:
            result = session.run(cypher, dict(params))
            keys = list(result.keys())
        except Exception:
            session.close()
            raise

        def rows():
            try:
                for record in result:
                    yield record.data()
            finally:
                session.close()

        return keys, rows()

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()


def create_app(runner=None, store: InMemorySessionStore | None = None):
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

    def _token(authorization: str | None) -> str:
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

    # ── O11 QuerySpec registry + two-path export (site-plan §4) ──────────────
    export_ledger = ExportLedger()

    @app.get("/specs")
    def get_specs() -> list[dict[str, object]]:
        return list_specs()

    @app.post("/specs/{spec_id}/run")
    def post_spec_run(
        spec_id: str, body: QueryBody, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        try:
            return run_spec(spec_id, body.params, _token(authorization), sessions, graph)
        except InvalidTokenError:
            raise HTTPException(401, "invalid session") from None
        except UnknownSpecError:
            raise HTTPException(404, f"unknown spec '{spec_id}'") from None
        except ParamValidationError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.post("/specs/{spec_id}/export")
    def post_spec_export(
        spec_id: str,
        body: QueryBody,
        format: str = "csv",
        authorization: str | None = Header(default=None),
    ):
        from fastapi.responses import StreamingResponse

        try:
            job = export_spec(
                spec_id, body.params, format, _token(authorization), sessions, graph, export_ledger
            )
        except InvalidTokenError:
            raise HTTPException(401, "invalid session") from None
        except UnknownSpecError:
            raise HTTPException(404, f"unknown spec '{spec_id}'") from None
        except ParamValidationError as exc:
            raise HTTPException(422, str(exc)) from None
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        return StreamingResponse(
            job.chunks,
            media_type=job.media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{job.filename}"',
                "X-DryDocs-Export-Id": job.export_id,
                "X-DryDocs-Manifest-Path": f"/exports/{job.export_id}/manifest",
                # the browser needs these readable cross-origin for the sidecar flow
                "Access-Control-Expose-Headers": "X-DryDocs-Export-Id, X-DryDocs-Manifest-Path, Content-Disposition",
            },
        )

    @app.get("/exports/{export_id}/manifest")
    def get_export_manifest(
        export_id: str, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        try:
            return export_manifest(export_id, _token(authorization), sessions, export_ledger)
        except InvalidTokenError:
            raise HTTPException(401, "invalid session") from None
        except UnknownExportError:
            raise HTTPException(
                404, "unknown export id (manifests register when the download completes)"
            ) from None

    # ── O13 mapping stewardship (plan M2) — reads from the mapping-store
    # materialization; the ONLY "write" is a returned change artifact. ──
    mapping_store = MappingStore()

    def _mapping_call(fn, *args):
        try:
            return fn(*args)
        except InvalidTokenError:
            raise HTTPException(401, "invalid session") from None
        except Forbidden as exc:
            raise HTTPException(403, str(exc)) from None
        except UnknownDomainError as exc:
            raise HTTPException(404, f"unknown mapping domain {exc}") from None
        except ChangesetValidationError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.get("/mappings/domains")
    def get_domains(authorization: str | None = Header(default=None)) -> dict[str, object]:
        return _mapping_call(list_domains, _token(authorization), sessions)

    @app.get("/mappings/grid/{domain_id}")
    def get_grid(
        domain_id: str, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        return _mapping_call(
            mapping_grid, domain_id, _token(authorization), sessions, mapping_store
        )

    @app.get("/mappings/options")
    def get_options(authorization: str | None = Header(default=None)) -> dict[str, object]:
        return _mapping_call(mapping_options, _token(authorization), sessions, mapping_store)

    @app.post("/mappings/changeset")
    def post_changeset(
        body: ChangesetBody, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        return _mapping_call(
            draft_changeset, body.entries, _token(authorization), sessions, mapping_store
        )

    # ── O24 SEAL-contact overrides (ui-write-surface gate SME-3, M2 tier):
    # drafting returns the UPDATED committed file; the report is the AO-facing
    # source-corrections artifact. The server still writes nothing. ──
    @app.post("/mappings/overrides/draft")
    def post_override_draft(
        body: ChangesetBody, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        return _mapping_call(
            draft_override, body.entries, _token(authorization), sessions, mapping_store
        )

    @app.get("/mappings/overrides/report")
    def get_override_report(
        authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        return _mapping_call(
            source_corrections_report, _token(authorization), sessions, mapping_store
        )

    # Dev-mode demo page (same-origin, so no CORS surface): the live-data twin
    # of UI-WIP/wf-mapping-01.html until the O8 React shell exists.
    @app.get("/demo")
    def get_demo():
        from fastapi.responses import HTMLResponse

        page = Path(__file__).resolve().parent / "static" / "mapping_demo.html"
        return HTMLResponse(page.read_text(encoding="utf-8"))

    return app
