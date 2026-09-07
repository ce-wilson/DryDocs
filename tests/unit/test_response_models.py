"""WEB8 — every modelled route is driven once, through the framework.

WHY THIS FILE EXISTS, AND WHY test_openapi_client.py IS NOT ENOUGH. That file
reads the committed SCHEMA: it proves each route DECLARES a model. It cannot
prove the handler still returns what the model says, because it never calls one.
And ``drydocs_api.schemas._Declared`` sets ``extra='forbid'``, which turns a
disagreement into a RESPONSE-VALIDATION 500 — a declaration and its handler
drifting apart is not a wrong field on the wire here, it is a dead route.

The gap was real when WEB8 opened. ``test_mapping_api.py`` — 48 tests over the
richest surface in the group, and the only one with WRITE routes — calls the
handler functions DIRECTLY. Nothing in the suite sent an HTTP request at
``/mappings/*`` or ``/intake/*``, so twenty freshly declared models would have
been guarded by the schema alone: exactly the "restatement of a declaration
with nothing guarding it" that O70 was written against.

So this tier is deliberately shallow and wide. It asserts almost nothing about
CONTENT — the handlers' own tests own that, in far more detail than a wiring
test should duplicate. It asserts that each route, driven through FastAPI with
its response model applied, answers 200. One request per modelled operation is
the whole idea: the failure this catches is a 500, and a 500 needs no assertion
beyond arriving.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi", reason="optional api group (poetry install --with api)")

from drydocs_api.audit import ApiAuditLog  # noqa: E402
from drydocs_api.intake import STATUSES  # noqa: E402

SECRET = "a-test-console-secret"


class FakeRunner:
    """Enough graph for the two routes that read one. ``/docs-verify`` sweeps
    databases through SHOW DATABASES; ``/mappings/pending/report`` counts email
    riders. Both must answer PLAUSIBLY rather than richly — a runner that raised
    would exercise each route's degraded path, which is a different test."""

    def run(self, cypher, params, database):
        if "SHOW DATABASES" in cypher:
            return ["name"], [{"name": "drydocs"}]
        return ["n"], [{"n": 0}]

    def stream(self, cypher, params, database):
        return ["n"], iter([{"n": 0}])


@pytest.fixture()
def api(tmp_path, monkeypatch):
    """An app whose every store roots in tmp. The data root is set here rather
    than inherited: it is a per-machine fact (G81 removed the default), and a
    test that depended on the developer's own root would pass or fail by
    accident of whose laptop it ran on."""
    from fastapi.testclient import TestClient

    from drydocs_api.app import create_app
    from drydocs_api.credentials import CredentialStore
    from drydocs_api.sessions import InMemorySessionStore

    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("DRYDOCS_MAPPING_DB", str(tmp_path / "mapping.db"))
    monkeypatch.setenv("DRYDOCS_AGENT_REG_KEY", "reg-key")

    creds = CredentialStore()
    creds.set("morpheus", SECRET)  # admin

    app = create_app(
        runner=FakeRunner(),
        store=InMemorySessionStore(),
        credentials=creds,
        audit=ApiAuditLog(log_dir=tmp_path / "audit"),
    )
    client = TestClient(app)
    login = client.post("/login", json={"persona_id": "morpheus", "secret": SECRET}).json()
    return client, login["token"], login["session_id"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _ok(response, what):
    """A 200, or the failure with the body attached.

    The body matters on this tier: a response-validation failure names the field
    and the model it broke, and that message is the entire diagnostic value of
    the test."""
    assert response.status_code == 200, f"{what} -> {response.status_code}: {response.text[:600]}"
    return response.json()


# ── the single-payload reads ─────────────────────────────────────────────────


def test_docs_verify_validates_against_its_model(api):
    client, token, _ = api
    body = _ok(client.get("/docs-verify", headers=_auth(token)), "GET /docs-verify")
    assert body["databases_queried"] == ["drydocs"], "the fake server has exactly this one"
    assert "statuses" in body and body["classification"]


def test_log_estate_validates_against_its_model(api):
    client, token, _ = api
    body = _ok(client.get("/admin/log-estate", headers=_auth(token)), "GET /admin/log-estate")
    assert isinstance(body["kinds"], list) and isinstance(body["zones"], list)


def test_ephemeral_registration_validates_against_its_model(api):
    client, token, session_id = api
    body = _ok(
        client.post(
            "/specs/ephemeral",
            json={
                "owner_session": session_id,
                "cypher": "MATCH (n) RETURN count(n) AS n",
                "database": "drydocs",
            },
            headers={"X-DryDocs-Agent-Key": "reg-key"},
        ),
        "POST /specs/ephemeral",
    )
    assert body["explore_ref"] and body["expires_at"]


# ── mappings: the group with write surfaces ──────────────────────────────────


def test_mappings_read_routes_validate(api):
    client, token, _ = api
    domains = _ok(client.get("/mappings/domains", headers=_auth(token)), "GET /mappings/domains")
    assert domains["domains"], "the domain list is declared in code and never empty"

    _ok(client.get("/mappings/options", headers=_auth(token)), "GET /mappings/options")
    _ok(client.get("/mappings/drafts", headers=_auth(token)), "GET /mappings/drafts")
    _ok(client.get("/mappings/overrides/report", headers=_auth(token)), "GET overrides/report")
    _ok(client.get("/mappings/pending/report", headers=_auth(token)), "GET pending/report")
    _ok(client.get("/mappings/app-code/migrations", headers=_auth(token)), "GET migrations")

    # Every domain the server says is available — a grid's rows are the DOMAIN's
    # columns, so one domain passing says nothing about the next.
    for domain in domains["domains"]:
        if not domain["available"]:
            continue
        _ok(
            client.get(f"/mappings/grid/{domain['id']}", headers=_auth(token)),
            f"GET /mappings/grid/{domain['id']}",
        )


def test_mappings_pending_report_validates_with_no_graph_in_reach(api, monkeypatch):
    """The N14 degraded path: ``email_unassigned`` goes null rather than zero,
    and null is a DIFFERENT answer. Worth its own request because the model
    declares that field nullable and nothing else here exercises it."""
    client, token, _ = api

    def explode(*a, **k):
        raise ConnectionError("neo4j went away")

    monkeypatch.setattr("drydocs_api.app.run_named", explode)
    body = _ok(client.get("/mappings/pending/report", headers=_auth(token)), "pending/report")
    assert body["counts"]["email_unassigned"] is None


def test_mappings_write_routes_validate(api):
    """The draft/promote surface. T3's whole point: these WRITE, so a route that
    500s on its own response is a lost edit and not a blank panel."""
    client, token, _ = api

    # Per APP CODE, not per job: the job-grain changeset was retired at K7 §A1.
    # The console's hand-declared `DraftEntry` still describes the retired shape
    # (folder_id/job_id) — recorded in the WEB8 close notes, and not fixable
    # from the response side, because ChangesetBody.entries is a free `list`.
    _ok(
        client.post(
            "/mappings/changeset",
            json={
                "entries": [
                    {
                        "app_code": "WEB8",
                        "app_id": "70001",
                        "rationale": "web8 wiring test",
                    }
                ]
            },
            headers=_auth(token),
        ),
        "POST /mappings/changeset",
    )

    receipt = _ok(
        client.post(
            "/mappings/overrides/draft",
            json={
                "entries": [
                    {
                        "app_id": "70001",
                        "role_name": "L2 Manager",
                        "override_holder_sid": "70002",
                        "rationale": "web8 wiring test",
                    }
                ]
            },
            headers=_auth(token),
        ),
        "POST /mappings/overrides/draft",
    )
    assert receipt["draft_id"]

    _ok(
        client.post(
            f"/mappings/drafts/{receipt['draft_id']}/promote",
            headers=_auth(token),
        ),
        "POST /mappings/drafts/{id}/promote",
    )

    _ok(
        client.post(
            "/mappings/app-code/draft",
            json={
                "entries": [
                    {
                        "app_code": "WEB8",
                        "row_kind": "seal-born",
                        "app_id": "70001",
                        "rationale": "web8 wiring test",
                    }
                ]
            },
            headers=_auth(token),
        ),
        "POST /mappings/app-code/draft",
    )


# ── intake: three shapes on one surface ──────────────────────────────────────


def test_intake_lifecycle_validates_every_shape(api, tmp_path):
    """One pass through the surface, because the three shapes are only
    distinguishable in sequence: the LIST row (no evidence), the RECORD
    (evidence), and the upload response (record + evidence_id)."""
    client, token, _ = api

    created = _ok(
        client.post(
            "/intake",
            json={"context_type": "other", "area": {}, "note": "web8 wiring test"},
            headers=_auth(token),
        ),
        "POST /intake",
    )
    intake_id = created["intake_id"]
    assert created["evidence"] == [], "a fresh record carries the key, empty"

    # A WIRE CHANGE WEB8 MADE, pinned here rather than discovered later. The
    # handler attaches the two thread fields only to a flagged draft; a response
    # model serializes its DEFAULTS, so they are now present on every record.
    # Harmless — both console consumers test truthiness — but it is a change,
    # and openapi-typescript types a defaulted field as REQUIRED for exactly
    # this reason, so the generated type and the wire agree only while this holds.
    assert created["legal_transitions"]["thread_decision_required"] is False
    assert created["legal_transitions"]["thread_decisions"] == []

    listed = _ok(client.get("/intake", headers=_auth(token)), "GET /intake")
    assert listed["intakes"], "the record just created is in the queue"
    assert "evidence" not in listed["intakes"][0], (
        "IntakeListRowOut declares no evidence field — the list endpoint has never "
        "sent one, and modelling it would put a key on the wire the handler does "
        "not produce"
    )

    fetched = _ok(client.get(f"/intake/{intake_id}", headers=_auth(token)), "GET /intake/{id}")
    assert "evidence" in fetched, "the single-record read DOES carry it"

    uploaded = _ok(
        client.post(
            f"/intake/{intake_id}/evidence",
            files={"files": ("note.txt", b"a line of evidence", "text/plain")},
            headers=_auth(token),
        ),
        "POST /intake/{id}/evidence",
    )
    assert uploaded["evidence_id"], (
        "the upload response is the record PLUS this key — under extra='forbid' a "
        "model without it turns every successful upload into a 500"
    )
    assert uploaded["evidence"], "and the uploaded file is in the record it returns"

    # The one transition a draft has (TRANSITIONS['draft']). Read off the record
    # the server just sent rather than hard-coded, because the legal set is the
    # SERVER's to own — a test that spelled it out would be a second copy of the
    # machine, free to disagree with the first.
    to = fetched["legal_transitions"]["transitions"][0]["to"]
    assert to == "ontology-reviewed", "the draft's one exit, pinned so a silent re-route shows"
    _ok(
        client.post(
            f"/intake/{intake_id}/transition",
            json={"to": to, "note": "web8 wiring test"},
            headers=_auth(token),
        ),
        "POST /intake/{id}/transition",
    )


def test_thread_decision_validates_and_carries_the_optional_transition_fields(api):
    """The last intake route, and the only one that reaches
    ``LegalTransitionsOut``'s two OPTIONAL fields.

    They are optional because the handler attaches them to a flagged draft and
    to nothing else, so a model that made them required would be wrong on every
    other record and a model that omitted them would drop the UI's only signal
    that a decision is owed. Reaching them takes two intakes carrying the same
    evidence text: the second trips quoted-content-overlap against the first."""
    client, token, _ = api
    text = b"\n".join(f"a distinctive line of evidence number {i}".encode() for i in range(12))

    ids = []
    for n in (1, 2):
        record = _ok(
            client.post(
                "/intake",
                json={"context_type": "other", "area": {}, "note": f"web8 thread {n}"},
                headers=_auth(token),
            ),
            "POST /intake",
        )
        ids.append(record["intake_id"])
        _ok(
            client.post(
                f"/intake/{record['intake_id']}/evidence",
                files={"files": (f"thread-{n}.txt", text, "text/plain")},
                headers=_auth(token),
            ),
            "POST /intake/{id}/evidence",
        )

    flagged = _ok(client.get(f"/intake/{ids[1]}", headers=_auth(token)), "GET /intake/{id}")
    assert flagged["thread_flagged"], "the same evidence in two intakes is a thread"
    assert flagged["legal_transitions"]["thread_decision_required"] is True
    assert flagged["legal_transitions"]["thread_decisions"] == ["adds-value", "no-new-value"]

    decided = _ok(
        client.post(
            f"/intake/{ids[1]}/thread-decision",
            json={"decision": "adds-value"},
            headers=_auth(token),
        ),
        "POST /intake/{id}/thread-decision",
    )
    assert decided["thread_decision"] == "adds-value"


def test_a_blank_return_note_is_a_422_and_the_reason_reaches_the_caller(api):
    """O50: the admin queue's Send-back button is convenience; THIS is the rule.

    ``test_intake_api.test_return_requires_a_note`` already pins the store's
    refusal, and pinning it again would be a second copy. What is new here is
    the WIRE: the console disables the button until a note is typed, and if that
    client check ever diverges from the server's, the admin has to read the
    SERVER's sentence — so the status code and the message both have to survive
    the HTTP boundary. A 500, or a 422 with FastAPI's generic body, would leave
    the queue printing a shrug.
    """
    client, token, _ = api
    created = _ok(
        client.post(
            "/intake",
            json={"context_type": "other", "area": {}, "note": "o50 return-note test"},
            headers=_auth(token),
        ),
        "POST /intake",
    )
    intake_id = created["intake_id"]
    # Walk to sme-confirmed by following the server's own map at each hop —
    # never a hard-coded path, which would be the machine written down twice.
    for _ in range(len(STATUSES)):
        record = _ok(client.get(f"/intake/{intake_id}", headers=_auth(token)), "GET /intake/{id}")
        if record["status"] == "sme-confirmed":
            break
        forward = record["legal_transitions"]["transitions"][0]["to"]
        _ok(
            client.post(
                f"/intake/{intake_id}/transition",
                json={"to": forward, "note": ""},
                headers=_auth(token),
            ),
            "POST /intake/{id}/transition",
        )
    else:  # pragma: no cover - only reachable if the machine grows a cycle
        raise AssertionError("never reached sme-confirmed following the legal map")

    refused = client.post(
        f"/intake/{intake_id}/transition",
        json={"to": "admin-returned", "note": "   "},
        headers=_auth(token),
    )
    assert refused.status_code == 422, refused.text
    assert refused.json()["detail"] == (
        "a return goes back with a note — the SME needs the why"
    ), "the console prints this verbatim; a paraphrase here is a second copy of the rule"

    accepted = _ok(
        client.post(
            f"/intake/{intake_id}/transition",
            json={"to": "admin-returned", "note": "bindings look wrong"},
            headers=_auth(token),
        ),
        "POST /intake/{id}/transition",
    )
    assert accepted["status"] == "admin-returned"


def test_every_console_route_in_the_schema_guard_was_driven_here() -> None:
    """The two guards are kept in step by name.

    test_openapi_client.CONSOLE_ROUTES is the DECLARED set; this file is the
    DRIVEN set. A route added to the first and forgotten here would be schema-
    guarded and never called, which is the state WEB8 found the mappings surface
    in. Routes are listed by hand rather than derived — deriving them from the
    schema would make this test agree with itself."""
    from tests.unit.test_openapi_client import CONSOLE_ROUTES

    driven = {
        ("/health", "get"),  # the audit tier drives these two
        ("/login", "post"),
        ("/logout", "post"),
        ("/queries", "get"),
        ("/query/{query_id}", "post"),
        ("/raw-cypher", "post"),
        ("/specs", "get"),
        ("/specs/{spec_id}/run", "post"),
        ("/docs-verify", "get"),
        ("/admin/log-estate", "get"),
        ("/specs/ephemeral", "post"),
        ("/intake", "get"),
        ("/intake", "post"),
        ("/intake/{intake_id}", "get"),
        ("/intake/{intake_id}/evidence", "post"),
        ("/intake/{intake_id}/transition", "post"),
        ("/intake/{intake_id}/thread-decision", "post"),
        ("/mappings/domains", "get"),
        ("/mappings/grid/{domain_id}", "get"),
        ("/mappings/options", "get"),
        ("/mappings/changeset", "post"),
        ("/mappings/overrides/draft", "post"),
        ("/mappings/overrides/report", "get"),
        ("/mappings/pending/report", "get"),
        ("/mappings/drafts", "get"),
        ("/mappings/drafts/{draft_id}/promote", "post"),
        ("/mappings/app-code/draft", "post"),
        ("/mappings/app-code/migrations", "get"),
    }
    missing = set(CONSOLE_ROUTES) - driven
    assert not missing, f"declared but never driven through the framework: {sorted(missing)}"
    stale = driven - set(CONSOLE_ROUTES)
    assert not stale, f"driven but no longer declared — drop from this list: {sorted(stale)}"
