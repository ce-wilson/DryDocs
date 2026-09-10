"""API5 — a graph outage answers 503, not 500.

WHAT WAS WRONG. Every route that touches the graph let a driver failure escape
as an unhandled exception, and FastAPI renders that as 500. But 500 means "this
service has a bug", and the console reads it exactly that way: `isUpstreamDown`
in ``web/src/lib/reachability.ts`` treats 502/503/504 as "the service is down,
not this page" and deliberately does not include 500. So a stopped Neo4j
container presented to the operator as a console defect — sending them to read
our code instead of starting their database.

THE LINE IS DriverError, NOT Neo4jError, and the two mean opposite things:

* ``DriverError`` — the driver could not get an answer at all (unreachable,
  session expired, misconfigured, a CORE13 timeout tripping). Not our bug: 503.
* ``Neo4jError`` — the SERVER answered with an error. For a query this service
  wrote, that IS our bug, and it must stay a 500. A test below pins that, because
  widening the handler to Neo4jError is the obvious "improvement" that would
  hide real defects behind "service down".

THE CLASS, NEVER THE MESSAGE (ADR 0020): a driver's message quotes the URI it
dialled, and the console must carry no host or port.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

import neo4j  # noqa: E402

from drydocs_api.audit import ApiAuditLog  # noqa: E402

SECRET = "a-test-console-secret"

#: The URI a driver error's message would quote. The point of the message rule
#: is that NONE of this reaches the response, so the test asserts on the parts.
LEAKY = "bolt://neo4j-prod-db-07.internal.example.test:7687"


class _Raising:
    """A GraphRunner that fails the way the real driver fails."""

    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def run(self, cypher, params, database):
        raise self._exc

    def run_with_diagnostics(self, cypher, params, database):
        raise self._exc

    def stream(self, cypher, params, database):
        raise self._exc


def _client(exc: Exception, tmp_path):
    from fastapi.testclient import TestClient

    from drydocs_api.app import create_app
    from drydocs_api.credentials import CredentialStore
    from drydocs_api.sessions import InMemorySessionStore

    creds = CredentialStore()
    creds.set("morpheus", SECRET)
    app = create_app(
        runner=_Raising(exc),
        store=InMemorySessionStore(),
        credentials=creds,
        audit=ApiAuditLog(log_dir=tmp_path / "audit"),
    )
    # raise_server_exceptions=False so a 500 comes back AS a 500 rather than
    # being re-raised into the test — otherwise the failing case cannot be
    # observed at all, which would make the 500 assertions vacuous.
    client = TestClient(app, raise_server_exceptions=False)
    token = client.post("/login", json={"persona_id": "morpheus", "secret": SECRET}).json()["token"]
    return client, {"Authorization": f"Bearer {token}"}


#: Every driver-side failure class the API can meet. `ServiceUnavailable` is the
#: stopped container, `SessionExpired` a mid-query loss, `ConfigurationError` a
#: bad NEO4J_URI — LiveRunner is lazy, so that one surfaces on the first query
#: rather than at server start.
DRIVER_FAILURES = [
    neo4j.exceptions.ServiceUnavailable(f"Couldn't connect to {LEAKY}"),
    neo4j.exceptions.SessionExpired(f"Failed to read from defunct connection {LEAKY}"),
    neo4j.exceptions.ConfigurationError(f"URI scheme not supported: {LEAKY}"),
]


@pytest.mark.parametrize("exc", DRIVER_FAILURES, ids=lambda e: type(e).__name__)
def test_a_driver_failure_answers_503(exc, tmp_path) -> None:
    client, auth = _client(exc, tmp_path)
    response = client.post("/raw-cypher", json={"cypher": "MATCH (n) RETURN n"}, headers=auth)
    assert response.status_code == 503, response.text


@pytest.mark.parametrize("exc", DRIVER_FAILURES, ids=lambda e: type(e).__name__)
def test_the_response_carries_the_class_and_not_the_message(exc, tmp_path) -> None:
    """ADR 0020: no host, no port, nothing the driver quoted."""
    client, auth = _client(exc, tmp_path)
    body = client.post("/raw-cypher", json={"cypher": "MATCH (n) RETURN n"}, headers=auth)
    assert body.json() == {"detail": type(exc).__name__}
    text = body.text
    assert "neo4j-prod-db-07" not in text
    assert "7687" not in text
    assert "bolt://" not in text
    assert str(exc) not in text


def test_a_server_side_error_is_still_a_500(tmp_path) -> None:
    """The line that makes the handler safe. A Neo4jError means the server
    ANSWERED with an error — for a query this service wrote, that is our bug,
    and calling it 'service down' would hide it. Widening the handler to
    Neo4jError is the obvious wrong 'improvement'; this is what refuses it."""
    server_said = type(
        "_ServerSaid",
        (neo4j.exceptions.ClientError,),
        {"code": "Neo.ClientError.Statement.SyntaxError"},
    )("Invalid input 'MTCH'")
    client, auth = _client(server_said, tmp_path)
    response = client.post("/raw-cypher", json={"cypher": "MTCH (n) RETURN n"}, headers=auth)
    assert response.status_code == 500, "a server-side error is a defect here, not an outage"


def test_a_non_driver_exception_is_still_a_500(tmp_path) -> None:
    """A bare ConnectionError is not a driver class and stays a 500 — the
    handler is registered on the driver's own hierarchy, not on 'anything that
    smells like a network problem'."""
    client, auth = _client(ConnectionError("neo4j went away mid-query"), tmp_path)
    response = client.post("/raw-cypher", json={"cypher": "MATCH (n) RETURN n"}, headers=auth)
    assert response.status_code == 500


def test_the_console_already_reads_503_as_down() -> None:
    """The acceptance's "the console needs no change", verified against the
    console's own source rather than asserted. `web/src/**` is not this lane's
    pen this burst, and this is why it did not need to be."""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    source = (repo / "web" / "src" / "lib" / "reachability.ts").read_text(encoding="utf-8")
    body = source.split("export function isUpstreamDown", 1)[1].split("}", 1)[0]
    assert "503" in body
    assert "500" not in body, "500 must NOT be read as down — it is the bug signal"


@pytest.mark.parametrize(
    "path, payload",
    [
        ("/raw-cypher", {"cypher": "MATCH (n) RETURN n"}),
        ("/queries/folder-count/run", {"params": {}}),
    ],
)
def test_the_handler_covers_the_routes_not_just_one(path, payload, tmp_path) -> None:
    """One handler over the app, not a try/except per route — so a route added
    tomorrow is covered without anyone remembering."""
    client, auth = _client(
        neo4j.exceptions.ServiceUnavailable(f"Couldn't connect to {LEAKY}"), tmp_path
    )
    response = client.post(path, json=payload, headers=auth)
    assert response.status_code in (404, 503), response.text
    if response.status_code == 503:
        assert response.json() == {"detail": "ServiceUnavailable"}
