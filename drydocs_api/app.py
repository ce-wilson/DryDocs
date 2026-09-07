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

from drydocs_api.audit import ApiAuditLog
from drydocs_api.corpus_status import DOC_REGISTRY_PATH, corpus_status
from drydocs_api.credentials import CredentialChecker, ReloadingCredentialStore
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
from drydocs_api.log_estate import log_estate
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
from drydocs_api.schemas import (
    AppCodeMigrationsOut,
    ChangesetArtifactOut,
    ConfigOut,
    CorpusStatusOut,
    CorrectionsReportOut,
    DataCenterOut,
    DataCentersOut,
    DraftReceiptOut,
    EphemeralRegisterOut,
    HealthOut,
    IntakeEvidenceOut,
    IntakeListOut,
    IntakeRecordOut,
    LogEstateOut,
    LoginOut,
    MappingDomainsOut,
    MappingGridOut,
    MappingOptionsOut,
    NamedQueryOut,
    NamedRunOut,
    OpenDraftsOut,
    PendingCorrectionsReportOut,
    PromotedDiffOut,
    SpecOut,
    SpecRunOut,
    StatusOut,
)
from drydocs_api.sessions import InMemorySessionStore, InvalidTokenError, Session
from drydocs_core.config import Neo4jSettings
from drydocs_core.data_centers import load_registry as load_data_center_registry
from drydocs_core.env_refs import resolve_optional
from drydocs_core.notifications import from_summary, to_payload


class LoginBody(BaseModel):
    persona_id: str
    # O69: the thing being proved. Sent once, over the login call only; the
    # browser keeps the returned token and never the secret.
    secret: str


class QueryBody(BaseModel):
    params: dict = {}


class ExportBody(QueryBody):
    """The export request: a spec run's params, plus API1 (c)'s raisable ceiling.

    A separate model from ``QueryBody`` because the ceiling is an EXPORT
    decision. Raising the limit on a grid read would change what is on screen;
    raising it here changes what lands in a file that carries a manifest, and
    those are different permissions to grant. Omitted (the default) keeps
    today's behaviour exactly — the display limit the console echoes back — so
    a caller that has not been updated is unaffected.
    """

    limit: int | None = None


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
    # ADR 0019: the owning session's PUBLIC handle, never its token. The agent
    # authenticates itself with X-DryDocs-Agent-Key; this field only scopes.
    owner_session: str
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
    credentials: CredentialChecker | None = None,
    audit: ApiAuditLog | None = None,
):
    """App factory. ``runner``/``store``/``credentials``/``audit`` are injectable
    for tests; the default is the live driver, a fresh in-memory session store,
    the machine-local credential file (absent on a fresh clone, which yields an
    empty store in which every login is refused), and the declared api/api-debug
    audit sinks (G108 — see drydocs_api.audit for which routes are audited).

    The default credential store RE-READS its file when it changes (O73), so
    adding or rotating a secret takes effect without restarting the server."""
    from fastapi import Depends, FastAPI, Header, HTTPException, Request, UploadFile

    app = FastAPI(
        title="drydocs-api", description="Thin read API over the knowledge graph (ADR 0005)"
    )
    # NO CORS MIDDLEWARE, on purpose (ADR 0020, WEB10). The console is same-origin
    # with this API in every environment: a reverse proxy -- Vite's own in dev and
    # preview, O72's in the Compose stack -- serves the page and forwards `/api/*`
    # here with the prefix stripped, so no browser ever sends a cross-origin request
    # and there is no allowlist to keep current. The allowlist that stood here from
    # O69 drifted unobserved until 2026-08-30 (a documented verification port it
    # never named); an allowlist that cannot drift is one that does not exist.
    # DRYDOCS_CORS_ORIGINS is retired with it. A cross-origin caller is a deployment
    # defect this API refuses by default rather than a case to configure for.

    sessions = store if store is not None else InMemorySessionStore()
    graph = runner if runner is not None else LiveRunner()
    creds = credentials if credentials is not None else ReloadingCredentialStore()
    audit = audit if audit is not None else ApiAuditLog()

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
            # ``creds`` is passed so a withdrawn account's token stops working on
            # its NEXT request rather than at the end of its term (O75). This is
            # the one caller that supplies it: every authenticated route enters
            # through this dependency, so the check runs exactly once per
            # request, at the door.
            return authenticate(_token(authorization), sessions, creds)
        except InvalidTokenError:
            # Unknown and EXPIRED both land here; the client's answer to either
            # is the same, which is why sessions.ExpiredTokenError subclasses it.
            raise HTTPException(401, "invalid session") from None

    # N806: these are type ALIASES, not variables — PascalCase is the
    # convention FastAPI's own docs use for the annotated-dependency idiom.
    CurrentUser = Annotated[Session, Depends(_current_session)]  # noqa: N806

    def _current_admin(request: Request, user: CurrentUser) -> Session:
        try:
            return require_role(user, "admin")
        except Forbidden as exc:
            # G108 x O69, reconciled at the merge. Moving the role check to the
            # door put it OUTSIDE every route's audit block, so a REFUSED admin
            # request stopped being recorded at all -- and an unauthorized
            # attempt is precisely what an audit log exists to capture. The
            # rejection is therefore recorded here, carrying the original
            # Forbidden class rather than the 403 it is mapped to.
            #
            # FAILURE PATH ONLY: a request that passes is audited by the route
            # itself, and a line here as well would double-count it. The inner
            # re-raise exists so ``observe`` sees the exception and stamps
            # error_class; it is caught immediately because the caller's answer
            # is the HTTP 403, not the internal class.
            route = request.scope.get("route")
            path = getattr(route, "path", request.url.path)
            try:
                with audit.observe(
                    path, token=user.session_id, run_id=request.headers.get("x-drydocs-run-id")
                ):
                    raise exc
            except Forbidden:
                pass
            raise HTTPException(403, str(exc)) from None

    AdminUser = Annotated[Session, Depends(_current_admin)]  # noqa: N806

    # O70: the return annotation IS the response_model — FastAPI publishes it in
    # the OpenAPI schema the console's TypeScript client is generated from, and
    # validates the handler's dict against it (extra keys forbidden; see
    # drydocs_api.schemas). Every route the console reads through GraphAccess
    # or the sign-in flow is declared this way.
    @app.get("/health")
    def health() -> HealthOut:
        return HealthOut(status="ok")

    # ADR 0020: the per-environment values the console needs at RUNTIME, served
    # unauthenticated because none is a secret and the page has to read them
    # before anyone signs in. This route is the only place a deployment fact
    # reaches the bundle -- the build inlines none (the dist guard checks).
    @app.get("/config")
    def config() -> ConfigOut:
        template, _ = resolve_optional("DRYDOCS_RUNTIME_VIEW_URL_TEMPLATE", where="GET /config")
        return ConfigOut(runtime_view_url_template=template or None)

    # Z6 — the data-center spelling registry, read as CONFIG.
    #
    # AUTHENTICATED, unlike /config above, and the difference is the file: this
    # reader prefers the machine-local internal twin when it is present (J13), so
    # the rows can be the real inventory. /config serves values that are not
    # secrets and must be readable before sign-in; this one is neither.
    #
    # It is not a QuerySpec and cannot be: the pairing is a DECLARED fact in
    # config/taxonomy/data-centers.yaml, not a graph edge, and the reason it is
    # declared rather than derived is the vendor baseline — BMC defines no format
    # for the data-center name, so nothing in a short code determines a long one.
    # The console needs it because the E#### default-time seed for a folder with
    # no explicit time is reachable only through the short -> long pairing.
    @app.get("/data-centers")
    def get_data_centers(user: CurrentUser) -> DataCentersOut:
        _ = user  # any authenticated persona; the registry is not role-scoped
        registry = load_data_center_registry()
        return DataCentersOut(
            data_centers=[
                DataCenterOut(
                    code=d.code,
                    name=d.name,
                    default_time=d.default_time,
                    suffix=d.suffix,
                    sample=d.sample,
                    note=d.note,
                )
                for d in registry.data_centers
            ],
            source=registry.source,
            updated=registry.updated,
        )

    # O58 — the doc-corpus reconciliation, as a NAMED SERVER-SIDE READ.
    #
    # Not a QuerySpec, and it cannot be one: the sweep visits MORE THAN ONE
    # database on purpose (that is the only way a corpus sitting where it did not
    # declare becomes visible), while a spec carries exactly one `database:` and
    # SPEC_DATABASES is {"drydocs"} since the G102 fold. It also needs
    # SHOW DATABASES, a server-level query no spec expresses, which is where
    # `db-absent` comes from.
    #
    # THE ADR 0005 POSITION, stated because O58 required the cost recorded: this
    # takes NO parameters, and every Cypher string is chosen server-side by
    # drydocs_core.docs_verify. The browser cannot influence which query runs,
    # which is the property the ADR protects; decision 2 provides for named
    # server-side queries, and /query/{id} is the existing precedent. What it
    # genuinely gives up is the spec REGISTRY's review — so the payload carries
    # its own classification and its own status vocabulary.
    #
    # Steward+admin, matching the /gates and /software audience: every row here
    # is a delta against a declaration, and an end user reads "wrong-db" as
    # breakage rather than as the governance signal it is.
    @app.get("/docs-verify")
    def get_docs_verify(user: CurrentUser) -> CorpusStatusOut:
        # BOTH roles, because require_role is an exact membership test, not a
        # ranking — `require_role(user, "steward")` refuses an ADMIN, which is
        # never what an SME-surface gate means here. This is the server-side
        # twin of canAccessModule's 'sme' designation (steward OR admin), and
        # the console's /gates and /software pages read the same way.
        try:
            require_role(user, "steward", "admin")
        except Forbidden as exc:
            raise HTTPException(403, str(exc)) from None
        import yaml

        registry = yaml.safe_load(DOC_REGISTRY_PATH.read_text(encoding="utf-8"))
        return corpus_status(registry.get("sources", []), graph)

    @app.get("/queries")
    def queries() -> list[NamedQueryOut]:
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
    def post_login(body: LoginBody) -> LoginOut:
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
    def post_logout(user: CurrentUser) -> StatusOut:
        logout(user.token, sessions)
        return StatusOut(status="ok")

    @app.post("/query/{query_id}")
    def post_query(
        query_id: str,
        body: QueryBody,
        user: CurrentUser,
        x_drydocs_run_id: str | None = Header(default=None),
    ) -> NamedRunOut:
        try:
            with audit.observe(
                "/query/{query_id}", token=user.session_id, run_id=x_drydocs_run_id
            ) as rec:
                rec.query_id = query_id
                rec.params = body.params
                out = run_named(query_id, body.params, user.token, sessions, graph)
                rec.database = str(out["database"])
                rec.rows = len(out["rows"])
            return out
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
    def post_raw(
        body: RawBody,
        user: AdminUser,
        x_drydocs_run_id: str | None = Header(default=None),
    ) -> NamedRunOut:
        try:
            with audit.observe(
                "/raw-cypher", token=user.session_id, run_id=x_drydocs_run_id
            ) as rec:
                rec.cypher = body.cypher  # debug tier only; the api line cannot carry it
                out = run_raw(body.cypher, user.token, sessions, graph)
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
    def get_specs() -> list[SpecOut]:
        return list_specs()

    @app.post("/specs/ephemeral")
    def post_ephemeral_register(
        body: EphemeralRegisterBody,
        x_drydocs_agent_key: str | None = Header(default=None),
        x_drydocs_run_id: str | None = Header(default=None),
    ) -> EphemeralRegisterOut:
        # Audited even though it executes nothing: the Cypher ENTERS the system
        # here, and it is the route the QA agent's run_id arrives on (ruling D).
        # The actor is the OWNER session the ref is scoped to -- its handle,
        # which is what every other route records too (ADR 0019), so the
        # registration and the later run/export join on one actor value.
        try:
            with audit.observe(
                "/specs/ephemeral", token=body.owner_session, run_id=x_drydocs_run_id
            ) as rec:
                rec.cypher = body.cypher
                rec.params = body.params
                rec.database = body.database
                out = register_ephemeral(
                    x_drydocs_agent_key,
                    os.environ.get("DRYDOCS_AGENT_REG_KEY"),
                    body.owner_session,
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
        user: CurrentUser,
        x_drydocs_run_id: str | None = Header(default=None),
    ) -> SpecRunOut:
        try:
            with audit.observe(
                "/specs/{spec_id}/run", token=user.session_id, run_id=x_drydocs_run_id
            ) as rec:
                rec.spec_id = spec_id
                rec.params = body.params
                out = run_spec(spec_id, body.params, user.token, sessions, graph, ephemerals)
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
        body: ExportBody,
        user: CurrentUser,
        format: str = "csv",
        x_drydocs_run_id: str | None = Header(default=None),
    ):
        from fastapi.responses import StreamingResponse

        try:
            # The audit line lands at job creation with rows null: the rows are
            # streamed after this returns, and their count is the export
            # MANIFEST's fact (it registers when the download completes). A
            # failure after streaming starts is the manifest's to reveal.
            with audit.observe(
                "/specs/{spec_id}/export", token=user.session_id, run_id=x_drydocs_run_id
            ) as rec:
                rec.spec_id = spec_id
                rec.params = body.params
                job = export_spec(
                    spec_id,
                    body.params,
                    format,
                    user.token,
                    sessions,
                    graph,
                    export_ledger,
                    ephemerals=ephemerals,
                    limit=body.limit,
                )
                rec.detail["export_id"] = job.export_id
                rec.detail["format"] = format
                if body.limit is not None:
                    # A raised ceiling is a deliberate act on a governed
                    # artifact; the audit line is where that belongs.
                    rec.detail["limit"] = body.limit
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
    def post_intake(body: IntakeCreateBody, user: CurrentUser) -> IntakeRecordOut:
        return _intake_call(
            create_intake,
            body.context_type,
            body.area,
            body.note,
            user.token,
            sessions,
            intake_store,
            audit_route="/intake",
            audit_token=user.session_id,
        )

    @app.get("/intake")
    def get_intakes(user: CurrentUser) -> IntakeListOut:
        return _intake_call(list_intakes, user.token, sessions, intake_store)

    @app.get("/intake/{intake_id}")
    def get_one_intake(intake_id: str, user: CurrentUser) -> IntakeRecordOut:
        return _intake_call(get_intake, intake_id, user.token, sessions, intake_store)

    @app.post("/intake/{intake_id}/evidence")
    async def post_intake_evidence(
        intake_id: str,
        files: list[UploadFile],
        user: CurrentUser,
    ) -> IntakeEvidenceOut:
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
                audit_route="/intake/{intake_id}/evidence",
                audit_token=user.session_id,
            )
        return out

    @app.post("/intake/{intake_id}/transition")
    def post_intake_transition(
        intake_id: str,
        body: IntakeTransitionBody,
        user: CurrentUser,
    ) -> IntakeRecordOut:
        return _intake_call(
            intake_transition,
            intake_id,
            body.to,
            body.note,
            user.token,
            sessions,
            intake_store,
            audit_route="/intake/{intake_id}/transition",
            audit_token=user.session_id,
        )

    @app.post("/intake/{intake_id}/thread-decision")
    def post_thread_decision(
        intake_id: str,
        body: ThreadDecisionBody,
        user: CurrentUser,
    ) -> IntakeRecordOut:
        return _intake_call(
            thread_decision,
            intake_id,
            body.decision,
            user.token,
            sessions,
            intake_store,
            audit_route="/intake/{intake_id}/thread-decision",
            audit_token=user.session_id,
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
    def get_domains(user: CurrentUser) -> MappingDomainsOut:
        return _mapping_call(list_domains, user.token, sessions)

    @app.get("/mappings/grid/{domain_id}")
    def get_grid(domain_id: str, user: CurrentUser) -> MappingGridOut:
        return _mapping_call(mapping_grid, domain_id, user.token, sessions, mapping_store)

    @app.get("/mappings/options")
    def get_options(user: CurrentUser) -> MappingOptionsOut:
        return _mapping_call(mapping_options, user.token, sessions, mapping_store)

    @app.post("/mappings/changeset")
    def post_changeset(body: ChangesetBody, user: CurrentUser) -> ChangesetArtifactOut:
        return _mapping_call(draft_changeset, body.entries, user.token, sessions, mapping_store)

    # ── O24 SEAL-contact overrides (ui-write-surface gate SME-3, M2 tier),
    # moved to the S4 draft buffer: drafting writes ROWS to var/mapping.db and
    # returns a receipt; promotion emits the diff to apply on a branch. The
    # server still writes no committed file — git is the only commit target. ──
    @app.post("/mappings/overrides/draft")
    def post_override_draft(body: ChangesetBody, user: CurrentUser) -> DraftReceiptOut:
        return _mapping_call(
            draft_override,
            body.entries,
            user.token,
            sessions,
            mapping_store,
            draft_id=body.draft_id,
            audit_route="/mappings/overrides/draft",
            audit_token=user.session_id,
        )

    @app.get("/mappings/drafts")
    def get_drafts(user: CurrentUser, domain: str | None = None) -> OpenDraftsOut:
        return _mapping_call(list_drafts, user.token, sessions, mapping_store, domain)

    @app.post("/mappings/drafts/{draft_id}/promote")
    def post_promote_draft(draft_id: str, user: CurrentUser) -> PromotedDiffOut:
        return _mapping_call(
            promote_draft,
            draft_id,
            user.token,
            sessions,
            mapping_store,
            audit_route="/mappings/drafts/{draft_id}/promote",
            audit_token=user.session_id,
        )

    @app.get("/mappings/overrides/report")
    def get_override_report(user: CurrentUser) -> CorrectionsReportOut:
        return _mapping_call(source_corrections_report, user.token, sessions, mapping_store)

    @app.get("/mappings/pending/report")
    def get_pending_report(user: CurrentUser) -> PendingCorrectionsReportOut:
        # N14: the union report. The email rider count is a GRAPH read
        # (docs.email-unassigned.v1, Q21); the report itself must render with
        # no graph in reach, so an unreachable graph degrades to the explicit
        # "read it at the spec" line — never an error, never a silent zero.
        #
        # O69 at the merge: this route arrived on main AFTER the branch converted
        # every other route to the declared-user signature, so it was the one
        # raw-Authorization holdout the guard caught. Converted here rather than
        # exempted — the guard's whole point is that it has no exceptions.
        email: int | None = None
        try:
            out = run_named("docs.email-unassigned.v1", {}, user.token, sessions, graph)
            rows = out.get("rows") or []
            email = int(next(iter(rows[0].values()))) if rows else 0
        except Exception:  # — graph-unavailable is a rendered state here
            email = None
        return _mapping_call(
            pending_source_correction_report,
            user.token,
            sessions,
            mapping_store,
            email_unassigned=email,
        )

    # ── K9/K11 app-code defined-mapping drafting (gate seal-app-ref-edge-
    # reshape §E1/§E2/§G7): the steward cascade drafts store rows; the
    # artifact is the COMPLETE updated committed file. Server writes nothing;
    # the K8 loader stays the only graph writer (§E3). ──
    @app.post("/mappings/app-code/draft")
    def post_app_code_draft(body: ChangesetBody, user: CurrentUser) -> DraftReceiptOut:
        return _mapping_call(
            draft_app_code_mapping,
            body.entries,
            user.token,
            sessions,
            mapping_store,
            audit_route="/mappings/app-code/draft",
            audit_token=user.session_id,
        )

    # K7 §B2 tier-3 readback (lifted from wip/k9-laptop at J30): dual-coded was
    # admitted only because the end state is DECLARED, so the declaration needs a
    # reader or the condition is decorative.
    @app.get("/mappings/app-code/migrations")
    def get_app_code_migrations(
        user: CurrentUser,
    ) -> AppCodeMigrationsOut:
        return _mapping_call(app_code_migration_report, user.token, sessions, mapping_store)

    # O68: the log estate — per declared kind and zone, the directory, the file
    # count, the size and the declared retention. ADMIN ONLY: it names real
    # paths on the host's disk, which is operational detail and not something a
    # user-tier persona is asking for. The payload is shaped in
    # drydocs_api/log_estate.py and COMPUTED in drydocs_core — clause (b) puts
    # the byte sum in core so a second walker cannot disagree with the first.
    #
    # It reports the api-debug kind's size and retention like any other kind's
    # and cannot return its CONTENTS: there is no parameter here that names a
    # file, because capturing Cypher text is ruled (ADR 0014 clause 6) and
    # surfacing it is not (clause c).
    @app.get("/admin/log-estate")
    def get_log_estate(user: AdminUser) -> LogEstateOut:
        return log_estate()

    # Dev-mode demo page (same-origin, so no CORS surface): the live-data twin
    # of docs/design/ui-exploration/wf-mapping-01.html until the O8 React shell exists.
    @app.get("/demo")
    def get_demo():
        from fastapi.responses import HTMLResponse

        page = Path(__file__).resolve().parent / "static" / "mapping_demo.html"
        return HTMLResponse(page.read_text(encoding="utf-8"))

    return app
