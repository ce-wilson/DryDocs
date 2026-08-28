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

import os
from collections.abc import Mapping
from pathlib import Path

import neo4j
from pydantic import BaseModel

from drydocs_api.audit import ApiAuditLog
from drydocs_api.ephemeral_specs import (
    EphemeralSpecStore,
    EphemeralValidationError,
    register_ephemeral,
)
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
from drydocs_api.intake import (
    IllegalTransitionError,
    IntakeStore,
    IntakeValidationError,
    UnknownIntakeError,
    add_evidence,
    create_intake,
    default_intake_root,
    get_intake,
    list_intakes,
    thread_decision,
)
from drydocs_api.intake import (
    transition as intake_transition,
)
from drydocs_api.mappings import (
    ChangesetValidationError,
    MappingStore,
    UnknownDomainError,
    app_code_migration_report,
    draft_app_code_mapping,
    draft_changeset,
    draft_override,
    list_domains,
    list_drafts,
    mapping_grid,
    mapping_options,
    pending_source_correction_report,
    promote_draft,
    source_corrections_report,
)
from drydocs_api.personas import UnknownPersonaError
from drydocs_api.queries import NAMED_QUERIES, ParamValidationError, UnknownQueryError
from drydocs_api.query_specs import UnknownSpecError
from drydocs_api.sessions import InMemorySessionStore, InvalidTokenError
from drydocs_core.config import Neo4jSettings
from drydocs_core.notifications import from_summary, to_payload


class LoginBody(BaseModel):
    persona_id: str


class QueryBody(BaseModel):
    params: dict = {}


class RawBody(BaseModel):
    cypher: str


class ChangesetBody(BaseModel):
    entries: list = []
    # S4: append to an existing draft instead of starting a new one, so a
    # multi-step edit stays one reviewable unit. Omitted = new draft.
    draft_id: str | None = None


class IntakeCreateBody(BaseModel):
    context_type: str
    area: dict = {}
    note: str = ""


class IntakeTransitionBody(BaseModel):
    to: str
    note: str = ""


class ThreadDecisionBody(BaseModel):
    decision: str  # 'adds-value' | 'no-new-value'


class EphemeralRegisterBody(BaseModel):
    owner_token: str
    cypher: str
    database: str
    params: dict = {}
    description: str = ""
    columns: list = []


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
        keys, rows, _ = self.run_with_diagnostics(cypher, params, database)
        return keys, rows

    def run_with_diagnostics(
        self, cypher: str, params: Mapping[str, object], database: str
    ) -> tuple[list[str], list[dict[str, object]], list[dict[str, object]]]:
        """R21: rows AND the driver's notifications. The summary used to be
        discarded here, which is how four unknown-label warnings presented as
        a clean empty answer on 2026-08-20. Non-fatal: never raised, always
        carried; ``[]`` is a clean run, not a missing field."""
        result = self.driver.execute_query(
            cypher,
            parameters_=dict(params),
            database_=database,
            routing_=neo4j.RoutingControl.READ,
        )
        notifications = to_payload(from_summary(result.summary))
        return list(result.keys), [r.data() for r in result.records], notifications

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


def create_app(
    runner=None,
    store: InMemorySessionStore | None = None,
    audit: ApiAuditLog | None = None,
):
    """App factory. ``runner``/``store``/``audit`` are injectable for tests; the
    default is the live driver + a fresh in-memory session store + the declared
    api/api-debug audit sinks (G108 — see drydocs_api.audit's enumeration of
    which routes are audited and why)."""
    from fastapi import FastAPI, Header, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="drydocs-api", description="Thin read API over the knowledge graph (ADR 0005)"
    )
    # The web console dev server is the only expected browser origin today.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:4173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    sessions = store if store is not None else InMemorySessionStore()
    graph = runner if runner is not None else LiveRunner()
    audit = audit if audit is not None else ApiAuditLog()

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
        query_id: str,
        body: QueryBody,
        authorization: str | None = Header(default=None),
        x_drydocs_run_id: str | None = Header(default=None),
    ) -> dict[str, object]:
        token = _token(authorization)
        try:
            with audit.observe("/query/{query_id}", token=token, run_id=x_drydocs_run_id) as rec:
                rec.query_id = query_id
                rec.params = body.params
                out = run_named(query_id, body.params, token, sessions, graph)
                rec.database = str(out["database"])
                rec.rows = len(out["rows"])
            return out
        except InvalidTokenError:
            raise HTTPException(401, "invalid session") from None
        except UnknownQueryError:
            raise HTTPException(404, f"unknown query '{query_id}'") from None
        except ParamValidationError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.post("/raw-cypher")
    def post_raw(
        body: RawBody,
        authorization: str | None = Header(default=None),
        x_drydocs_run_id: str | None = Header(default=None),
    ) -> dict[str, object]:
        token = _token(authorization)
        try:
            with audit.observe("/raw-cypher", token=token, run_id=x_drydocs_run_id) as rec:
                rec.cypher = body.cypher  # debug tier only; the api line cannot carry it
                out = run_raw(body.cypher, token, sessions, graph)
                rec.database = str(out["database"])
                rec.rows = len(out["rows"])
            return out
        except InvalidTokenError:
            raise HTTPException(401, "invalid session") from None
        except Forbidden as exc:
            raise HTTPException(403, str(exc)) from None
        except WriteRejected as exc:
            raise HTTPException(400, str(exc)) from None

    # ── O11 QuerySpec registry + two-path export (site-plan §4) ──────────────
    export_ledger = ExportLedger()
    # R4: ephemeral session-scoped specs (ADR 0007 decision 4). Registration is
    # agent-key gated — a browser bearer token can never register Cypher, so
    # /raw-cypher stays the ONLY interactive Cypher surface (admin-gated, ADR 0005).
    ephemerals = EphemeralSpecStore()

    @app.get("/specs")
    def get_specs() -> list[dict[str, object]]:
        return list_specs()

    @app.post("/specs/ephemeral")
    def post_ephemeral_register(
        body: EphemeralRegisterBody,
        x_drydocs_agent_key: str | None = Header(default=None),
        x_drydocs_run_id: str | None = Header(default=None),
    ) -> dict[str, object]:
        # Audited even though it executes nothing: the Cypher ENTERS the system
        # here, and it is the route the QA agent's run_id arrives on (ruling D).
        # The actor is the OWNER session the ref is scoped to.
        try:
            with audit.observe(
                "/specs/ephemeral", token=body.owner_token, run_id=x_drydocs_run_id
            ) as rec:
                rec.cypher = body.cypher
                rec.params = body.params
                rec.database = body.database
                out = register_ephemeral(
                    x_drydocs_agent_key,
                    os.environ.get("DRYDOCS_AGENT_REG_KEY"),
                    body.owner_token,
                    body.cypher,
                    body.database,
                    body.params,
                    body.description,
                    body.columns,
                    sessions,
                    ephemerals,
                )
                rec.spec_id = str(out.get("explore_ref") or "") or None
            return out
        except Forbidden as exc:
            raise HTTPException(403, str(exc)) from None
        except InvalidTokenError:
            raise HTTPException(401, "unknown owner session") from None
        except WriteRejected as exc:
            raise HTTPException(400, str(exc)) from None
        except EphemeralValidationError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.post("/specs/{spec_id}/run")
    def post_spec_run(
        spec_id: str,
        body: QueryBody,
        authorization: str | None = Header(default=None),
        x_drydocs_run_id: str | None = Header(default=None),
    ) -> dict[str, object]:
        token = _token(authorization)
        try:
            with audit.observe("/specs/{spec_id}/run", token=token, run_id=x_drydocs_run_id) as rec:
                rec.spec_id = spec_id
                rec.params = body.params
                out = run_spec(spec_id, body.params, token, sessions, graph, ephemerals)
                rec.database = str(out.get("database") or "") or None
                rec.rows = len(out["rows"])
            return out
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
        x_drydocs_run_id: str | None = Header(default=None),
    ):
        from fastapi.responses import StreamingResponse

        token = _token(authorization)
        try:
            # The audit line lands at job creation with rows null: the rows are
            # streamed after this returns, and their count is the export
            # MANIFEST's fact (it registers when the download completes). A
            # failure after streaming starts is the manifest's to reveal.
            with audit.observe(
                "/specs/{spec_id}/export", token=token, run_id=x_drydocs_run_id
            ) as rec:
                rec.spec_id = spec_id
                rec.params = body.params
                job = export_spec(
                    spec_id,
                    body.params,
                    format,
                    token,
                    sessions,
                    graph,
                    export_ledger,
                    ephemerals=ephemerals,
                )
                rec.detail["export_id"] = job.export_id
                rec.detail["format"] = format
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

    # ── O46 SME context-intake — evidence + records land under the data root
    # (never the repo tree, never the graph); the server owns the status
    # machine and returns the legal-transitions map per record. ──
    intake_store = IntakeStore(default_intake_root())

    def _intake_call(fn, *args, audit_route=None, audit_token=None, **kwargs):
        # audit_route set = one of the four WRITE routes (G108); the GET reads
        # pass neither and stay unaudited.
        try:
            if audit_route is None:
                return fn(*args, **kwargs)
            with audit.observe(audit_route, token=audit_token) as rec:
                out = fn(*args, **kwargs)
                if isinstance(out, dict):
                    for key in ("intake_id", "id"):
                        if key in out:
                            rec.detail["intake_id"] = out[key]
                            break
            return out
        except InvalidTokenError:
            raise HTTPException(401, "invalid session") from None
        except Forbidden as exc:
            raise HTTPException(403, str(exc)) from None
        except UnknownIntakeError as exc:
            raise HTTPException(404, f"unknown intake {exc}") from None
        except IntakeValidationError as exc:
            raise HTTPException(422, str(exc)) from None
        except IllegalTransitionError as exc:
            raise HTTPException(409, str(exc)) from None

    @app.post("/intake")
    def post_intake(
        body: IntakeCreateBody, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        token = _token(authorization)
        return _intake_call(
            create_intake,
            body.context_type,
            body.area,
            body.note,
            token,
            sessions,
            intake_store,
            audit_route="/intake",
            audit_token=token,
        )

    @app.get("/intake")
    def get_intakes(authorization: str | None = Header(default=None)) -> dict[str, object]:
        return _intake_call(list_intakes, _token(authorization), sessions, intake_store)

    @app.get("/intake/{intake_id}")
    def get_one_intake(
        intake_id: str, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        return _intake_call(get_intake, intake_id, _token(authorization), sessions, intake_store)

    @app.post("/intake/{intake_id}/evidence")
    async def post_intake_evidence(
        intake_id: str,
        files: list[UploadFile],
        authorization: str | None = Header(default=None),
    ) -> dict[str, object]:
        token = _token(authorization)
        out: dict[str, object] = {}
        for f in files:
            data = await f.read()
            out = _intake_call(
                add_evidence,
                intake_id,
                f.filename or "unnamed",
                data,
                token,
                sessions,
                intake_store,
                audit_route="/intake/{intake_id}/evidence",
                audit_token=token,
            )
        return out

    @app.post("/intake/{intake_id}/transition")
    def post_intake_transition(
        intake_id: str,
        body: IntakeTransitionBody,
        authorization: str | None = Header(default=None),
    ) -> dict[str, object]:
        token = _token(authorization)
        return _intake_call(
            intake_transition,
            intake_id,
            body.to,
            body.note,
            token,
            sessions,
            intake_store,
            audit_route="/intake/{intake_id}/transition",
            audit_token=token,
        )

    @app.post("/intake/{intake_id}/thread-decision")
    def post_thread_decision(
        intake_id: str,
        body: ThreadDecisionBody,
        authorization: str | None = Header(default=None),
    ) -> dict[str, object]:
        token = _token(authorization)
        return _intake_call(
            thread_decision,
            intake_id,
            body.decision,
            token,
            sessions,
            intake_store,
            audit_route="/intake/{intake_id}/thread-decision",
            audit_token=token,
        )

    # ── O13 mapping stewardship (plan M2) — reads from the mapping-store
    # materialization; the ONLY "write" is a returned change artifact. ──
    mapping_store = MappingStore()

    def _mapping_call(fn, *args, audit_route=None, audit_token=None, **kwargs):
        # audit_route set = one of the three var/mapping.db WRITE routes (G108).
        # /mappings/changeset stays unaudited on purpose: it returns a change
        # artifact and persists nothing server-side (the O13 contract).
        try:
            if audit_route is None:
                return fn(*args, **kwargs)
            with audit.observe(audit_route, token=audit_token) as rec:
                out = fn(*args, **kwargs)
                if isinstance(out, dict) and "draft_id" in out:
                    rec.detail["draft_id"] = out["draft_id"]
            return out
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

    # ── O24 SEAL-contact overrides (ui-write-surface gate SME-3, M2 tier),
    # moved to the S4 draft buffer: drafting writes ROWS to var/mapping.db and
    # returns a receipt; promotion emits the diff to apply on a branch. The
    # server still writes no committed file — git is the only commit target. ──
    @app.post("/mappings/overrides/draft")
    def post_override_draft(
        body: ChangesetBody, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        token = _token(authorization)
        return _mapping_call(
            draft_override,
            body.entries,
            token,
            sessions,
            mapping_store,
            draft_id=body.draft_id,
            audit_route="/mappings/overrides/draft",
            audit_token=token,
        )

    @app.get("/mappings/drafts")
    def get_drafts(
        domain: str | None = None, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        return _mapping_call(list_drafts, _token(authorization), sessions, mapping_store, domain)

    @app.post("/mappings/drafts/{draft_id}/promote")
    def post_promote_draft(
        draft_id: str, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        token = _token(authorization)
        return _mapping_call(
            promote_draft,
            draft_id,
            token,
            sessions,
            mapping_store,
            audit_route="/mappings/drafts/{draft_id}/promote",
            audit_token=token,
        )

    @app.get("/mappings/overrides/report")
    def get_override_report(authorization: str | None = Header(default=None)) -> dict[str, object]:
        return _mapping_call(
            source_corrections_report, _token(authorization), sessions, mapping_store
        )

    @app.get("/mappings/pending/report")
    def get_pending_report(authorization: str | None = Header(default=None)) -> dict[str, object]:
        # N14: the union report. The email rider count is a GRAPH read
        # (docs.email-unassigned.v1, Q21); the report itself must render with
        # no graph in reach, so an unreachable graph degrades to the explicit
        # "read it at the spec" line — never an error, never a silent zero.
        token = _token(authorization)
        email: int | None = None
        try:
            out = run_named("docs.email-unassigned.v1", {}, token, sessions, graph)
            rows = out.get("rows") or []
            email = int(next(iter(rows[0].values()))) if rows else 0
        except Exception:  # — graph-unavailable is a rendered state here
            email = None
        return _mapping_call(
            pending_source_correction_report,
            token,
            sessions,
            mapping_store,
            email_unassigned=email,
        )

    # ── K9/K11 app-code defined-mapping drafting (gate seal-app-ref-edge-
    # reshape §E1/§E2/§G7): the steward cascade drafts store rows; the
    # artifact is the COMPLETE updated committed file. Server writes nothing;
    # the K8 loader stays the only graph writer (§E3). ──
    @app.post("/mappings/app-code/draft")
    def post_app_code_draft(
        body: ChangesetBody, authorization: str | None = Header(default=None)
    ) -> dict[str, object]:
        token = _token(authorization)
        return _mapping_call(
            draft_app_code_mapping,
            body.entries,
            token,
            sessions,
            mapping_store,
            audit_route="/mappings/app-code/draft",
            audit_token=token,
        )

    # K7 §B2 tier-3 readback (lifted from wip/k9-laptop at J30): dual-coded was
    # admitted only because the end state is DECLARED, so the declaration needs a
    # reader or the condition is decorative.
    @app.get("/mappings/app-code/migrations")
    def get_app_code_migrations(
        authorization: str | None = Header(default=None),
    ) -> dict[str, object]:
        return _mapping_call(
            app_code_migration_report, _token(authorization), sessions, mapping_store
        )

    # Dev-mode demo page (same-origin, so no CORS surface): the live-data twin
    # of docs/design/ui-exploration/wf-mapping-01.html until the O8 React shell exists.
    @app.get("/demo")
    def get_demo():
        from fastapi.responses import HTMLResponse

        page = Path(__file__).resolve().parent / "static" / "mapping_demo.html"
        return HTMLResponse(page.read_text(encoding="utf-8"))

    return app
