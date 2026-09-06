"""Response models for the routes the console consumes (O70).

WHY THESE EXIST. Until O70 every handler in ``app.py`` returned
``dict[str, object]``, so the OpenAPI schema drydocs-api publishes described
each response as a free object, and the browser's response types were written
by hand against what the handlers happened to return. That is a restatement
of a declaration with nothing guarding it — the defect class this repo has a
rule about twice over (never parse a render, never hand-copy a declaration).
The console's TypeScript client is now GENERATED from the schema, so a
response type has to be declared HERE, by the server, or the generated client
carries ``Record<string, unknown>`` and the hand-written cast has merely moved.

WHY ``extra='forbid'``. Pydantic's default silently DROPS a returned key the
model does not name — a handler could add a field, the wire would lose it, and
nothing would say so. Forbidding extras makes that a response-validation
failure in the API test suite, which is where a declaration and its handler
should be caught disagreeing. Every key each handler returns today is named
below; add a key to the handler and you add it here in the same commit, then
regenerate (``scripts/dump_openapi.py`` and ``npm run api:types`` in ``web/``).

The export MANIFEST stays a free object on purpose: the ledger record is open
by design and the console types it ``Record<string, unknown>`` already.

WEB8 closed O70's named follow-up. Every route it listed — ``/docs-verify``,
``/intake/*``, ``/mappings/*``, ``/specs/ephemeral`` — is modelled below, along
with ``/admin/log-estate``, which arrived after O70 and left the same hole. The
console's response types are now the generated ones, and ``unwrapAs``, the
helper that marked each unmodelled route at its call site, is gone with the
last of them.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class _Declared(BaseModel):
    """A response shape the server stands behind: no undeclared keys pass."""

    model_config = ConfigDict(extra="forbid")


class HealthOut(_Declared):
    status: str


class ConfigOut(_Declared):
    """GET /config (ADR 0020): the non-secret, per-environment values the console
    reads at boot instead of having them inlined at build time. Nothing here may
    be a credential or a coordinate the page could not already reach."""

    runtime_view_url_template: str | None


class StatusOut(_Declared):
    status: str


class LoginOut(_Declared):
    """The session the browser holds. Never the secret (O69).

    ``session_id`` (ADR 0019) is the public handle: the console passes it to the
    graph_qa agent in the control part so the agent can register ephemeral specs
    for THIS session without ever holding the token. It authorizes nothing.
    """

    token: str
    session_id: str
    persona_id: str
    role: str
    expires_at: str


class ParamOut(_Declared):
    """One declared parameter of a named query or a QuerySpec."""

    name: str
    type: str
    required: bool
    default: Any = None


class NamedQueryOut(_Declared):
    id: str
    description: str
    params: list[ParamOut]


class NamedRunOut(_Declared):
    """``/query/{query_id}`` and ``/raw-cypher`` share this envelope — the
    database is named AFTER the fact because routing is a server decision
    (ADR 0002 / ADR 0005 decision 2)."""

    query_id: str
    database: str
    keys: list[str]
    rows: list[dict[str, Any]]
    diagnostics: dict[str, Any]


class ColumnOut(_Declared):
    name: str
    type: str
    label: str


class SpecOut(_Declared):
    """One registry row as ``/specs`` lists it — the declaration, never the
    database (G102: ``watermarked`` comes from the spec)."""

    id: str
    description: str
    database: str
    classification: str
    cypher: str
    columns: list[ColumnOut]
    params: list[ParamOut]
    watermarked: bool


class CauseOut(_Declared):
    """R15: one cause that limited a walk. `cause` is the DryDocs cause class
    (`unparsed-cmd-line` | `unresolved-invocation` | `gate-pending-edge`),
    `detail` names the concrete thing (the probe class, or the planned
    vocabulary entry id for a gate-pending edge), `count` is the measurement
    when one was taken and null when it could not be (a probe that returned no
    count) or does not apply (a gate-pending edge has no count until it exists)."""

    cause: str
    detail: str
    count: int | None = None


class SpecRunOut(_Declared):
    """A QuerySpec run (O11): the registry echoes the spec's contract back
    with the rows, so the UI renders the classification banner and the
    SYNTHESIZED watermark without holding its own query definitions. This is
    the server-side twin of the console's ``SpecResult`` seam type."""

    spec_id: str
    database: str
    classification: str
    columns: list[ColumnOut]
    cypher: str
    params: dict[str, Any]
    keys: list[str]
    rows: list[dict[str, Any]]
    watermarked: bool
    ephemeral: bool
    #: API1 (d): completeness, declared. `truncated` says the spec's ceiling cut
    #: the answer; `limit` is the ceiling that applied, or null for a spec that
    #: has none. Both are modelled HERE so the generated client carries them as
    #: typed fields and the console renders from the contract — not from
    #: `rows.length === limit`, which is a second expression of a fact the
    #: server already knows and is wrong precisely when the answer is exactly
    #: 500 rows.
    truncated: bool
    limit: int | None = None
    #: R15: the epistemic label on the ANSWER. `exact` means every cause the
    #: spec's walk declares measured zero; `lower-bound` means at least one
    #: fired and `causes` names it; null means the spec declares no walk and is
    #: ungraded — never read null as exact. Zero rows with `lower-bound` is a
    #: different answer from zero rows with `exact`, and the console renders
    #: the label as given rather than inventing its own wording for it.
    epistemic: Literal["exact", "lower-bound"] | None = None
    causes: list[CauseOut] = []


# ── WEB8: the routes O70 left as free objects ────────────────────────────────
#
# O70 modelled the query/spec surface and named the rest as its own follow-up.
# Those routes kept hand-declared response types in the browser, and every one
# of them was marked at its call site by ``unwrapAs`` — a helper whose only job
# was to say "the schema has not modelled this route yet". WEB8 models them, so
# the helper has nothing left to mark and goes with the last call site.
#
# WHY MAPPINGS IS THE ONE THAT MATTERED. It is the only module in this group
# with WRITE surfaces (draft, promote), so a drifted route there writes wrong
# rather than renders wrong — the web review's T3, and the reason this item
# carries the priority it does.
#
# EACH MODEL IS DERIVED FROM BOTH ENDS: the handler's actual return, and the
# interface the console declared for it. The second end is not decoration — it
# is the spec of what the page reads, and two shapes below exist only because
# the two ends turned out to disagree (see ``IntakeListRowOut`` and
# ``IntakeEvidenceOut``).
#
# WHERE A FIELD STAYS OPEN, IT IS OPEN ON PURPOSE. A mapping grid's ``rows``,
# the label and relationship option lists, and a migration row are per-domain
# SELECTs — two of them ``SELECT *`` over a view — whose columns belong to the
# DOMAIN, not to the route. The console already types them
# ``Record<string, unknown>``. Naming today's columns here would be a second
# declaration of the view's shape, free to disagree with it; the ENVELOPE is
# what the route owes its client, and the envelope is what is modelled.


# ── /docs-verify (O58) ───────────────────────────────────────────────────────


class CorpusRowOut(_Declared):
    """One declared corpus, reconciled against the graph."""

    corpus_id: str
    target_db: str
    status: str
    documents: int
    chunks: int
    detail: str
    ok: bool


class CorpusStatusOut(_Declared):
    """GET /docs-verify. ``databases_queried`` is carried beside
    ``databases_swept`` because the surface's honesty rule turns on the
    difference: a database that was not queried renders "not queried", never 0
    (the O56 rule), and the rows alone cannot tell those apart. ``statuses`` is
    the whole vocabulary, sent with the payload so the page renders the real set
    instead of a hand-copied one."""

    classification: str
    databases_swept: list[str]
    databases_queried: list[str]
    statuses: list[str]
    rows: list[CorpusRowOut]


# ── /admin/log-estate (O68) ──────────────────────────────────────────────────


class LogKindOut(_Declared):
    """One declared log kind, beside what is actually on the host's disk.

    ``dir`` and ``oldest_days`` are nullable but always PRESENT: a kind with no
    files has no oldest file, and that is a different fact from a kind whose age
    was never measured."""

    id: str
    level: str
    retention_days: int
    rotation: str
    format: str
    status: str
    dir: str | None
    path: str
    exists: bool
    file_count: int
    total_bytes: int
    oldest_days: int | None
    over_retention: bool


class LogZoneOut(_Declared):
    """One declared data zone (G109), inventoried the same way."""

    id: str
    path: str
    mode: str | None
    exists: bool
    file_count: int
    total_bytes: int
    empty: bool


class LogEstateOut(_Declared):
    """GET /admin/log-estate. Both halves ride in one payload because the SME's
    question spans them. Note what is absent and stays absent: a kind's
    CONTENTS. ADR 0014 clause 6 rules that the verbose debug tier is captured;
    SURFACING it is a different risk and is not ruled, so there is no field here
    through which a log line could travel."""

    kinds: list[LogKindOut]
    zones: list[LogZoneOut]


# ── /intake/* (O46 store, O47 client) ────────────────────────────────────────


class EvidenceOut(_Declared):
    """One uploaded evidence file. ``kind`` is the extension with its dot
    stripped, and the upload path admits exactly three (``ALLOWED_EXTENSIONS``),
    so the wire declares the three rather than a bare string."""

    evidence_id: str
    intake_id: str
    filename: str
    rel_key: str
    sha256: str
    size: int
    kind: Literal["msg", "json", "txt"]
    pair_key: str
    preview: dict[str, Any] | None
    uploaded_at: str
    superseded: bool


class LegalTransitionOut(_Declared):
    to: str
    action: str


class LegalTransitionsOut(_Declared):
    """The per-record, per-ROLE transition map the UI renders its buttons from —
    the server owns the machine (the IntakeStepper decision, 2026-08-06), so the
    button set is a server answer and never a client rule.

    The two thread fields carry defaults where nothing else here does, because
    the handler only attaches them to a flagged draft that still owes its
    decision. A default keeps them out of the schema's ``required`` list, which
    is what makes the generated client declare them optional — matching the
    handler instead of over-promising for it."""

    status: str
    transitions: list[LegalTransitionOut]
    waiting_on_gate: bool
    terminal: bool
    thread_decision_required: bool = False
    thread_decisions: list[str] = []


class IntakeListRowOut(_Declared):
    """An intake as the QUEUE lists it.

    NO ``evidence`` FIELD — and that is the list's real shape, not an omission
    here. ``list_intakes`` serializes each record and attaches its legal
    transitions; it never reads the evidence table, which is one query for the
    page instead of one per row. The console declared the list as
    ``IntakeRecord[]`` — the same type it uses for a single record — so it has
    been claiming an always-present ``evidence: EvidenceRow[]`` that the list
    endpoint has never sent. Modelling the two shapes apart is what surfaced
    that, and keeping them apart is what stops it coming back."""

    intake_id: str
    created_at: str
    created_by: str
    origin: str
    classification: str
    context_type: str
    note: str
    status: str
    review_payload: str | None
    area: dict[str, str | None]
    thread_of: list[str]
    thread_flagged: bool
    thread_decision: Literal["adds-value", "no-new-value"] | None
    legal_transitions: LegalTransitionsOut


class IntakeRecordOut(IntakeListRowOut):
    """One intake read whole: the list row, plus the evidence ``get_intake``
    attaches. Every single-record route on this surface returns this shape,
    because create, transition and thread-decision all end by re-reading the
    record through ``get_intake``."""

    evidence: list[EvidenceOut]


class IntakeEvidenceOut(IntakeRecordOut):
    """POST /intake/{intake_id}/evidence: the whole record, plus the id of the
    file just stored. ``_evidence_out`` adds that one key to what ``get_intake``
    returns, which makes it a THIRD shape on this surface — and under
    ``extra='forbid'`` a model that overlooked it would turn every SUCCESSFUL
    upload into a response-validation 500."""

    evidence_id: str


class IntakeListOut(_Declared):
    intakes: list[IntakeListRowOut]


# ── /mappings/* (O13, O24, S4, K9/K11, N14) ──────────────────────────────────


class MappingDomainOut(_Declared):
    """One mapping domain the console can offer. ``available`` is false for a
    domain whose reconciler table is not built yet — declared so the page can
    render it greyed rather than omit it."""

    id: str
    title: str
    kind: Literal["quintuple", "manual", "override", "defined"]
    source: str
    tier: int | None
    available: bool


class MappingDomainsOut(_Declared):
    domains: list[MappingDomainOut]


class MappingGridOut(_Declared):
    """GET /mappings/grid/{domain_id}. ``keys`` names the columns for THIS
    domain and ``rows`` carries them — see the note above on why the row shape
    stays open."""

    domain: str
    keys: list[str]
    rows: list[dict[str, Any]]


class StatusSummaryOut(_Declared):
    status: str
    n: int


class MappingOptionsOut(_Declared):
    """GET /mappings/options — the vocabulary the authoring cascade offers."""

    labels: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    status_summary: list[StatusSummaryOut]


class ChangesetArtifactOut(_Declared):
    """POST /mappings/changeset. An ARTIFACT, not a write: the server produces
    CSV text and a manifest snippet and writes nothing at all — the loader stays
    the only graph writer (wf-mapping-01's one rule). ``lifecycle`` and ``note``
    carry that instruction to the operator, which is why they are on the wire
    and not in the page."""

    filename: str
    csv: str
    manifest_snippet: str
    entries: int
    lifecycle: str
    note: str


class DraftReceiptOut(_Declared):
    """POST /mappings/overrides/draft and /mappings/app-code/draft (S4, ADR 0009
    rule 5). Drafting writes ROWS to the mapping.db buffer and hands back this
    receipt. The shape it replaced returned a whole replacement file, which
    could not survive two editors: each held a full file built from the same
    base, so whichever was committed last erased the other."""

    draft_id: str
    domain: str
    entries: int
    pending: int
    committed_rows: int
    note: str


class OpenDraftOut(_Declared):
    draft_id: str
    domain: str
    entries: int
    authored_by: str
    authored_on: str


class OpenDraftsOut(_Declared):
    drafts: list[OpenDraftOut]


class PromotedDiffOut(_Declared):
    """POST /mappings/drafts/{draft_id}/promote — the unified diff to apply on a
    branch. The server still writes nothing; git is the only commit target."""

    draft_id: str
    domain: str
    path: str
    filename: str
    diff: str
    entries: int
    note: str


class CorrectionsReportOut(_Declared):
    """GET /mappings/overrides/report — the AO-facing source-corrections
    artifact, rendered as markdown the steward can send on."""

    filename: str
    markdown: str
    count: int
    generated_on: str
    generated_by: str


class PendingCountsOut(_Declared):
    """N14 §D2. ``email_unassigned`` is null when the graph could not be reached
    — a rendered state ("read it at the spec"), never an error and never a
    silent zero."""

    overrides: int
    manual_sources: int
    email_unassigned: int | None


class PendingCorrectionsReportOut(CorrectionsReportOut):
    """GET /mappings/pending/report — the N14 union report, which is the
    corrections report plus the per-domain counts behind its total."""

    counts: PendingCountsOut


class AppCodeMigrationsOut(_Declared):
    """GET /mappings/app-code/migrations — the K7 §B2 tier-3 readback, so a
    declared end state has a reader and "temporarily dual-coded" cannot quietly
    become the permanent state nobody re-opens. A row is ``SELECT *`` over
    ``v_dual_coded_migrations``, so the row shape is the view's."""

    migrations: list[dict[str, Any]]
    count: int


# ── /specs/ephemeral (the agent tier's registration receipt) ─────────────────


class EphemeralRegisterOut(_Declared):
    """POST /specs/ephemeral. The console never calls this one — the QA agent
    registers Cypher here and receives a REF, then runs and exports through the
    same reviewed seam every other caller uses, so the Cypher itself is never a
    query parameter. Modelled with the rest because O70 named it in the same
    list, and because the agent tier is a client with the same claim on a
    declared response as the browser has."""

    explore_ref: str
    database: str
    classification: str
    watermarked: bool
    expires_at: str
