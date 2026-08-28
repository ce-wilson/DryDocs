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
from typing import Annotated

import neo4j
from pydantic import BaseModel

from drydocs_api.credentials import CredentialStore
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
from drydocs_api.handlers import (
    BadCredentialsError,
    CredentialsNotConfiguredError,
    Forbidden,
    authenticate,
    login,
    logout,
    require_role,
    run_named,
    run_raw,
)
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
    promote_draft,
    source_corrections_report,
)
from drydocs_api.personas import UnknownPersonaError
from drydocs_api.queries import NAMED_QUERIES, ParamValidationError, UnknownQueryError
from drydocs_api.query_specs import UnknownSpecError
from drydocs_api.sessions import InMemorySessionStore, InvalidTokenError, Session
from drydocs_core.config import Neo4jSettings
from drydocs_core.notifications import from_summary, to_payload


class LoginBody(BaseModel):
    persona_id: str
    # O69: the thing being proved. Sent once, over the login call only; the
    # browser keeps the returned token and never the secret.
    secret: str


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
    credentials: CredentialStore | None = None,
):
    """App factory. ``runner``/``store``/``credentials`` are injectable for
    tests; the default is the live driver, a fresh in-memory session store, and
    the machine-local credential file (absent on a fresh clone, which yields an
    empty store in which every login is refused)."""
    from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile
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
    creds = credentials if credentials is not None else CredentialStore.load()

    def _token(authorization: str | None) -> str:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(401, "missing bearer token")
        return authorization.split(" ", 1)[1]

    # ── O69: authentication as a route signature ────────────────────────────
    # Every authenticated route declares ``user: CurrentUser`` (or ``AdminUser``)
    # instead of accepting a raw Authorization header and remembering to check
    # it. A route that forgets the parameter does not compile into an
    # authenticated route at all — it becomes an obviously public one, which is
    # the failure a reviewer can see. The handlers in handlers.py STILL run
    # their own ``authenticate`` call: they are the framework-free layer with
    # their own contract, provable offline without a server, and a second dict
    # lookup is not a cost worth trading that for.
    def _current_session(authorization: str | None = Header(default=None)) -> Session:
        try:
            return authenticate(_token(authorization), sessions)
        except InvalidTokenError:
            # Unknown and EXPIRED both land here; the client's answer to either
            # is the same, which is why sessions.ExpiredTokenError subclasses it.
            raise HTTPException(401, "invalid session") from None

    # N806: these are type ALIASES, not variables — PascalCase is the
    # convention FastAPI's own docs use for the annotated-dependency idiom.
    CurrentUser = Annotated[Session, Depends(_current_session)]  # noqa: N806

    def _current_admin(user: CurrentUser) -> Session:
        try:
            return require_role(user, "admin")
        except Forbidden as exc:
            raise HTTPException(403, str(exc)) from None

    AdminUser = Annotated[Session, Depends(_current_admin)]  # noqa: N806

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
            return login(body.persona_id, body.secret, sessions, creds)
        except CredentialsNotConfiguredError as exc:
            # Not a security leak worth hiding: an empty store has nothing to
            # enumerate, and the alternative is a fresh clone whose sign-in
            # screen refuses every attempt with no way to learn why.
            raise HTTPException(401, str(exc)) from None
        except (BadCredentialsError, UnknownPersonaError):
            # ONE message for both. Which of the two it was is precisely what
            # an account enumerator is trying to learn.
            raise HTTPException(401, "invalid credentials") from None

    @app.post("/logout")
    def post_logout(user: CurrentUser) -> dict[str, str]:
        logout(user.token, sessions)
        return {"status": "ok"}

    @app.post("/query/{query_id}")
    def post_query(query_id: str, body: QueryBody, user: CurrentUser) -> dict[str, object]:
        try:
            return run_named(query_id, body.params, user.token, sessions, graph)
        except InvalidTokenError:
            raise HTTPException(401, "invalid session") from None
        except UnknownQueryError:
            raise HTTPException(404, f"unknown query '{query_id}'") from None
        except ParamValidationError as exc:
            raise HTTPException(422, str(exc)) from None

    # The one route whose role requirement is visible in its signature: AdminUser
    # 403s a non-admin before the body is read. run_raw re-asserts it anyway —
    # the handler is what the offline suite tests, and it must fail closed on
    # its own.
    @app.post("/raw-cypher")
    def post_raw(body: RawBody, user: AdminUser) -> dict[str, object]:
        try:
            return run_raw(body.cypher, user.token, sessions, graph)
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
    ) -> dict[str, object]:
        try:
            return register_ephemeral(
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
        except Forbidden as exc:
            raise HTTPException(403, str(exc)) from None
        except InvalidTokenError:
            raise HTTPException(401, "unknown owner session") from None
        except WriteRejected as exc:
            raise HTTPException(400, str(exc)) from None
        except EphemeralValidationError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.post("/specs/{spec_id}/run")
    def post_spec_run(spec_id: str, body: QueryBody, user: CurrentUser) -> dict[str, object]:
        try:
            return run_spec(spec_id, body.params, user.token, sessions, graph, ephemerals)
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
        user: CurrentUser,
        format: str = "csv",
    ):
        from fastapi.responses import StreamingResponse

        try:
            job = export_spec(
                spec_id,
                body.params,
                format,
                user.token,
                sessions,
                graph,
                export_ledger,
                ephemerals=ephemerals,
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
    def get_export_manifest(export_id: str, user: CurrentUser) -> dict[str, object]:
        try:
            return export_manifest(export_id, user.token, sessions, export_ledger)
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

    def _intake_call(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
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
    def post_intake(body: IntakeCreateBody, user: CurrentUser) -> dict[str, object]:
        return _intake_call(
            create_intake,
            body.context_type,
            body.area,
            body.note,
            user.token,
            sessions,
            intake_store,
        )

    @app.get("/intake")
    def get_intakes(user: CurrentUser) -> dict[str, object]:
        return _intake_call(list_intakes, user.token, sessions, intake_store)

    @app.get("/intake/{intake_id}")
    def get_one_intake(intake_id: str, user: CurrentUser) -> dict[str, object]:
        return _intake_call(get_intake, intake_id, user.token, sessions, intake_store)

    @app.post("/intake/{intake_id}/evidence")
    async def post_intake_evidence(
        intake_id: str,
        files: list[UploadFile],
        user: CurrentUser,
    ) -> dict[str, object]:
        out: dict[str, object] = {}
        for f in files:
            data = await f.read()
            out = _intake_call(
                add_evidence,
                intake_id,
                f.filename or "unnamed",
                data,
                user.token,
                sessions,
                intake_store,
            )
        return out

    @app.post("/intake/{intake_id}/transition")
    def post_intake_transition(
        intake_id: str,
        body: IntakeTransitionBody,
        user: CurrentUser,
    ) -> dict[str, object]:
        return _intake_call(
            intake_transition,
            intake_id,
            body.to,
            body.note,
            user.token,
            sessions,
            intake_store,
        )

    @app.post("/intake/{intake_id}/thread-decision")
    def post_thread_decision(
        intake_id: str,
        body: ThreadDecisionBody,
        user: CurrentUser,
    ) -> dict[str, object]:
        return _intake_call(
            thread_decision,
            intake_id,
            body.decision,
            user.token,
            sessions,
            intake_store,
        )

    # ── O13 mapping stewardship (plan M2) — reads from the mapping-store
    # materialization; the ONLY "write" is a returned change artifact. ──
    mapping_store = MappingStore()

    def _mapping_call(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except InvalidTokenError:
            raise HTTPException(401, "invalid session") from None
        except Forbidden as exc:
            raise HTTPException(403, str(exc)) from None
        except UnknownDomainError as exc:
            raise HTTPException(404, f"unknown mapping domain {exc}") from None
        except ChangesetValidationError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.get("/mappings/domains")
    def get_domains(user: CurrentUser) -> dict[str, object]:
        return _mapping_call(list_domains, user.token, sessions)

    @app.get("/mappings/grid/{domain_id}")
    def get_grid(domain_id: str, user: CurrentUser) -> dict[str, object]:
        return _mapping_call(mapping_grid, domain_id, user.token, sessions, mapping_store)

    @app.get("/mappings/options")
    def get_options(user: CurrentUser) -> dict[str, object]:
        return _mapping_call(mapping_options, user.token, sessions, mapping_store)

    @app.post("/mappings/changeset")
    def post_changeset(body: ChangesetBody, user: CurrentUser) -> dict[str, object]:
        return _mapping_call(draft_changeset, body.entries, user.token, sessions, mapping_store)

    # ── O24 SEAL-contact overrides (ui-write-surface gate SME-3, M2 tier),
    # moved to the S4 draft buffer: drafting writes ROWS to var/mapping.db and
    # returns a receipt; promotion emits the diff to apply on a branch. The
    # server still writes no committed file — git is the only commit target. ──
    @app.post("/mappings/overrides/draft")
    def post_override_draft(body: ChangesetBody, user: CurrentUser) -> dict[str, object]:
        return _mapping_call(
            draft_override,
            body.entries,
            user.token,
            sessions,
            mapping_store,
            draft_id=body.draft_id,
        )

    @app.get("/mappings/drafts")
    def get_drafts(user: CurrentUser, domain: str | None = None) -> dict[str, object]:
        return _mapping_call(list_drafts, user.token, sessions, mapping_store, domain)

    @app.post("/mappings/drafts/{draft_id}/promote")
    def post_promote_draft(draft_id: str, user: CurrentUser) -> dict[str, object]:
        return _mapping_call(promote_draft, draft_id, user.token, sessions, mapping_store)

    @app.get("/mappings/overrides/report")
    def get_override_report(user: CurrentUser) -> dict[str, object]:
        return _mapping_call(source_corrections_report, user.token, sessions, mapping_store)

    # ── K9/K11 app-code defined-mapping drafting (gate seal-app-ref-edge-
    # reshape §E1/§E2/§G7): the steward cascade drafts store rows; the
    # artifact is the COMPLETE updated committed file. Server writes nothing;
    # the K8 loader stays the only graph writer (§E3). ──
    @app.post("/mappings/app-code/draft")
    def post_app_code_draft(body: ChangesetBody, user: CurrentUser) -> dict[str, object]:
        return _mapping_call(
            draft_app_code_mapping, body.entries, user.token, sessions, mapping_store
        )

    # K7 §B2 tier-3 readback (lifted from wip/k9-laptop at J30): dual-coded was
    # admitted only because the end state is DECLARED, so the declaration needs a
    # reader or the condition is decorative.
    @app.get("/mappings/app-code/migrations")
    def get_app_code_migrations(
        user: CurrentUser,
    ) -> dict[str, object]:
        return _mapping_call(app_code_migration_report, user.token, sessions, mapping_store)

    # Dev-mode demo page (same-origin, so no CORS surface): the live-data twin
    # of docs/design/ui-exploration/wf-mapping-01.html until the O8 React shell exists.
    @app.get("/demo")
    def get_demo():
        from fastapi.responses import HTMLResponse

        page = Path(__file__).resolve().parent / "static" / "mapping_demo.html"
        return HTMLResponse(page.read_text(encoding="utf-8"))

    return app
