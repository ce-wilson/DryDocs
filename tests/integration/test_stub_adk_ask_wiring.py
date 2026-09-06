"""R12: the Ask spoke's wiring, end to end, with no LLM key and no ports.

Three processes stand between a question and an answer — browser, ADK agent
server, drydocs-api — and the middle one needs a model key and its own venv. So
the WIRING was only ever checked by hand: the SSE frame shape, the R4 control
handshake, and whether the ``explore_ref`` the console shows is a ref that
actually resolves.

This drives the stub (``tests/stub_adk.py``) against a REAL drydocs-api over an
in-process ASGI transport. No LLM, no ports, no sleep-and-poll. What it cannot
check is whether the AGENT is right; that is the real agent's own tests. What it
checks is that the console's contract with whatever sits at port 8000 holds.

VENUE (J18): no machine-specific state. drydocs-api runs on an in-memory session
store with a fake graph runner, so this is reproducible on any checkout with the
``api`` group installed.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from tests.stub_adk import (
    STUB_APP,
    EphemeralRegistrar,
    control_from_parts,
    create_stub_adk,
    events_for,
    sse_body,
)

pytest.importorskip("fastapi", reason="fastapi lives in the optional 'api' group")
# starlette's TestClient rides on httpx2 (>=1.3) or httpx; the api group ships
# httpx2, so requiring httpx here skipped this test on every current venv.
if not any(importlib.util.find_spec(name) for name in ("httpx2", "httpx")):
    pytest.skip("httpx2/httpx live in the optional 'api' group", allow_module_level=True)

# starlette's TestClient, not httpx.ASGITransport: as of httpx 0.28 that
# transport is async-only, and everything here is a synchronous test. TestClient
# is httpx-shaped (.post/.get returning a Response with .status_code/.json/.text),
# which is exactly the duck type EphemeralRegistrar takes — so the stub is handed
# the same interface here that a live httpx.Client gives it in `python -m
# tests.stub_adk`, and the two paths cannot diverge in what the stub sees.
from fastapi.testclient import TestClient  # noqa: E402

from drydocs_api.app import create_app  # noqa: E402
from drydocs_api.sessions import InMemorySessionStore  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
#: The recorded stream the browser-side guard parses. Written by hand, asserted
#: byte-for-byte below, so the two ends cannot drift: if the stub's frames
#: change, THIS test fails and the fixture must be regenerated deliberately.
SSE_FIXTURE = REPO / "tests" / "fixtures" / "adk" / "stub-run-sse.txt"

AGENT_KEY = "r12-stub-agent-key"


class AcceptingCredentials:
    """A CredentialChecker that knows the persona this test signs in as.

    Needed because O75 made ``authenticate`` re-check that the session's account
    still EXISTS on every request, and the default store is a machine-local file
    that a fresh clone (and this laptop) does not have — so every bearer token
    would be "invalid session" here for a reason that has nothing to do with the
    Ask wiring. Injecting the checker keeps this test venue-independent (J18),
    which is the whole reason create_app takes one.
    """

    is_bootstrapped = True

    def verify(self, identity: str, secret: str) -> bool:
        return False  # nothing here logs in; sessions are issued directly

    def has_identity(self, identity: str) -> bool:
        return identity == PERSONA


#: The persona whose sessions this test issues.
PERSONA = "mouse"


class FakeRunner:
    """A graph that answers one row. The spec path is not under test here."""

    def run(self, cypher, params, database):
        return ["app_id"], [{"app_id": "APP-1"}]


@pytest.fixture()
def sessions() -> InMemorySessionStore:
    return InMemorySessionStore()


@pytest.fixture()
def api(monkeypatch, tmp_path, sessions):
    """drydocs-api, in process, with the agent-registration key configured.

    G81: ``create_app()`` builds the intake store at import and the data root
    has NO default, so this must say where — the same reason the web CI job
    points it at a runner-temp path. A per-test tmp_path keeps the fixture from
    touching a developer's real data root, which is precisely the accident G81
    removed the default to prevent.
    """
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DRYDOCS_AGENT_REG_KEY", AGENT_KEY)
    app = create_app(runner=FakeRunner(), store=sessions, credentials=AcceptingCredentials())
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def stub(api):
    """The stub ADK server, registering against that drydocs-api."""
    registrar = EphemeralRegistrar(api, agent_key=AGENT_KEY)
    with TestClient(create_stub_adk(registrar)) as client:
        client.registrar = registrar  # type: ignore[attr-defined]
        yield client


def _run_body(parts: list[dict], session_id: str = "s-1") -> dict:
    """Exactly what ``lib/adk.ts`` ``runBody`` sends."""
    return {
        "appName": STUB_APP,
        "userId": "u-1",
        "sessionId": session_id,
        "newMessage": {"role": "user", "parts": parts},
        "streaming": False,
    }


def _control(session_id: str) -> dict:
    """Exactly what ``askApi.controlPart`` builds (ADR 0019: the handle, never
    the token)."""
    return {
        "text": json.dumps(
            {"drydocs_control": {"session_id": session_id, "api_url": "http://api.test"}}
        )
    }


def _parse_sse(body: str) -> list[dict]:
    """The browser's frame parser, in Python — split on the blank line, take the
    ``data:`` line of each frame. Deliberately re-implemented rather than
    imported: the point is that a SECOND independent reader of the same wire
    format agrees, and importing the console's parser is not possible from here
    anyway."""
    out = []
    for frame in body.split("\n\n"):
        for line in frame.split("\n"):
            if line.startswith("data:"):
                out.append(json.loads(line[5:].strip()))
    return out


def _payloads(events: list[dict]) -> list[dict]:
    """The JSON the console reads out of ``content.parts[0].text``."""
    return [json.loads(e["content"]["parts"][0]["text"]) for e in events]


# ── the endpoints the console calls ─────────────────────────────────────────


def test_the_three_endpoints_the_console_calls_all_answer(stub):
    assert stub.get("/list-apps").json() == [STUB_APP]
    created = stub.post(f"/apps/{STUB_APP}/users/u-1/sessions/s-1")
    assert created.status_code == 200
    assert created.json()["id"] == "s-1"


def test_run_sse_streams_frames_in_the_shape_lib_adk_parses(stub):
    res = stub.post("/run_sse", json=_run_body([{"text": "how many apps?"}]))
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse(res.text)
    assert len(events) == 3
    payloads = _payloads(events)
    # two steps then one envelope — `status` is what makes the last one final
    assert [p.get("kind") for p in payloads[:2]] == ["step", "step"]
    assert payloads[2]["status"] == "ok"
    assert "answer" in payloads[2]


def test_run_and_run_sse_describe_the_same_turn(stub):
    # The fallback path must not be a different conversation. askApi falls back
    # to /run when SSE is unavailable, and a stub whose two endpoints disagreed
    # would hide a real drift between them.
    body = _run_body([{"text": "q"}])
    buffered = _payloads(stub.post("/run", json=body).json())
    streamed = _payloads(_parse_sse(stub.post("/run_sse", json=body).text))
    assert buffered == streamed


# ── the R4 handshake, which is the half that matters ────────────────────────


def test_the_control_part_is_found_wherever_it_sits(stub):
    token_part = _control("sid")
    assert control_from_parts([{"text": "q"}, token_part])["session_id"] == "sid"
    assert control_from_parts([token_part, {"text": "q"}])["session_id"] == "sid"
    assert control_from_parts([{"text": "q"}]) is None
    # a part that is JSON but not a control part is not one
    assert control_from_parts([{"text": '{"something": 1}'}]) is None


def test_the_explore_ref_resolves_for_the_owning_session(api, stub, sessions):
    session = sessions.issue(PERSONA)
    token = session.token
    # ADR 0019: what crosses to the agent is the handle; the bearer stays here.
    res = stub.post("/run_sse", json=_run_body([{"text": "q"}, _control(session.session_id)]))
    payloads = _payloads(_parse_sse(res.text))
    ref = payloads[1]["step"]["explore_ref"]
    assert ref, f"no explore_ref; registrar errors: {stub.registrar.errors}"  # type: ignore[attr-defined]
    assert ref.startswith("eph.")

    # THE POINT OF THE WHOLE FIXTURE: the ref the console would render is a ref
    # the console can actually run. A stub that invented one would pass every
    # test above and verify nothing.
    run = api.post(
        f"/specs/{ref}/run", json={"params": {}}, headers={"Authorization": f"Bearer {token}"}
    )
    assert run.status_code == 200, run.text
    assert run.json()["rows"] == [{"app_id": "APP-1"}]
    assert run.json()["ephemeral"] is True


def test_another_session_cannot_run_this_sessions_ref(api, stub, sessions):
    owner = sessions.issue(PERSONA)
    other = sessions.issue(PERSONA).token
    res = stub.post("/run_sse", json=_run_body([{"text": "q"}, _control(owner.session_id)]))
    ref = _payloads(_parse_sse(res.text))[1]["step"]["explore_ref"]
    assert ref
    denied = api.post(
        f"/specs/{ref}/run", json={"params": {}}, headers={"Authorization": f"Bearer {other}"}
    )
    # R4: a foreign ref 404s rather than 403 — no existence leak.
    assert denied.status_code == 404


def test_a_failed_registration_is_surfaced_and_not_swallowed(api, stub, sessions):
    # The one failure mode that would make this fixture worthless is a stub that
    # emits `explore_ref: null` and says nothing when the handshake breaks.
    res = stub.post("/run_sse", json=_run_body([{"text": "q"}, _control("not-a-live-session")]))
    step = _payloads(_parse_sse(res.text))[1]["step"]
    assert step["explore_ref"] is None
    assert step["error"], "a failed registration must reach the step, not vanish"
    assert "/specs/ephemeral" in step["error"]


def test_without_a_control_part_the_turn_still_answers(stub):
    # askApi makes the control part optional ("agent still answers"), so the
    # stub must too — otherwise the fixture would only cover the signed-in path.
    payloads = _payloads(_parse_sse(stub.post("/run_sse", json=_run_body([{"text": "q"}])).text))
    assert payloads[2]["status"] == "ok"
    assert payloads[1]["step"]["explore_ref"] is None
    assert payloads[1]["step"]["error"] is None


# ── the recorded stream the browser-side guard reads ────────────────────────


def test_the_committed_sse_fixture_still_matches_what_the_stub_emits():
    """The drift guard between the two ends.

    ``web/src/ask/stubStream.test.ts`` parses this file with the console's REAL
    parseAdkEvent. That is only worth anything while the file is what the stub
    actually produces, so this asserts it byte for byte — and names how to
    regenerate it, because a fixture nobody can rebuild gets deleted instead of
    updated.
    """
    expected = sse_body(events_for([{"text": "q"}], registrar=None))
    # read_BYTES, not read_text: text mode translates CRLF to LF on the way
    # in, so a fixture that had been eol-normalised would compare equal here
    # while the vitest read different bytes off the same file. The blank line
    # between frames IS the SSE delimiter, so "byte for byte" has to mean it.
    actual = SSE_FIXTURE.read_bytes().decode("utf-8")
    assert actual == expected, (
        "tests/fixtures/adk/stub-run-sse.txt is stale. Regenerate it with: "
        "poetry run python scripts/regen_stub_sse_fixture.py "
        "(it writes BYTES, so the frame delimiters stay LF on every platform)"
    )
