"""A stub ADK api_server: the Ask spoke's wiring, verifiable with no LLM key (R12).

WHAT THIS IS FOR. The console's Ask spoke crosses three processes — browser →
ADK agent server (port 8000) → drydocs-api (port 8001) — and the middle one
needs an ``ANTHROPIC_API_KEY`` and its own venv. So the WIRING (the SSE frame
shape, the R4 control-part handshake, the ephemeral-spec round trip) could only
be checked by standing up an LLM, which meant in practice it was checked by
hand, once, per session. The R5 session wrote a throwaway stub in a scratchpad
to do exactly this and it was thrown away; this is that stub, owned.

WHAT IT IS NOT. It is not an agent and does not pretend to be one. It answers a
FIXED envelope. Nothing here evaluates a question, chooses a spec, or writes
Cypher — that is the real agent's job and stubbing it would produce a test that
passes while the agent is broken. What it reproduces is exactly the contract the
BROWSER depends on:

  GET  /list-apps                                   -> the app list
  POST /apps/{app}/users/{user}/sessions/{session}  -> session create
  POST /run_sse                                     -> SSE step frames + envelope
  POST /run                                         -> the same events, buffered

...and the one thing in that contract with real consequences: the control part
carries this browser session's drydocs-api token, and the stub uses it to
register a REAL ephemeral spec against a REAL drydocs-api, so the ``explore_ref``
in the step it emits is one the console can actually run. A stub that invented a
ref would verify nothing about the half of R4 that matters.

PLACEMENT, decided and recorded (the acceptance asks for the decision, not just
the file). It sits at the tests root beside ``source_scan.py``, which is the
same shape: importable helper code that is not itself a test. That buys three
things a ``tests/integration/`` module would not:

  * an integration test imports ``create_stub_adk`` and drives it through an
    in-process ASGI transport — no ports, no sleep-and-poll, no flake;
  * a developer runs ``python -m tests.stub_adk`` for a real browser check
    against a real drydocs-api, same code, and so cannot verify a stub that has
    drifted from the tested one;
  * it is under ``tests/``, so it is outside every package the app ships and
    outside the Vite root entirely — ``web/dist`` could not contain it if
    someone tried.

FastAPI is an optional dependency here (the ``api`` group), so the import is
deferred into the factory and the integration test skips when it is absent —
the same posture ``tests/unit/test_session_redaction.py`` takes for google-adk.
"""

# NO `from __future__ import annotations` HERE, deliberately, and it is not an
# oversight to be tidied away. FastAPI resolves a route handler's annotations at
# decoration time; with the future import they are strings, and `Request` is
# imported INSIDE the factory (fastapi is an optional dependency), so FastAPI
# cannot resolve it — it falls back to treating `request` as a query parameter
# and every /run_sse call answers 422 "Field required". Python 3.12 evaluates
# `str | None` and `dict[str, Any]` natively, so nothing here needs the import.
import json
from collections.abc import Iterator
from typing import Any

#: The app name the console asks for. graph_qa is the real agent's name; the
#: stub answers to it so the browser needs no configuration change to point at
#: this instead of the real server.
STUB_APP = "graph_qa"

#: The database a stubbed answer claims to have read. `drydocs` is the ground-
#: truth database (ADR 0002), which is what a spec-path answer would use.
STUB_DATABASE = "drydocs"

#: The Cypher the stub registers as an ephemeral spec. Deliberately trivial and
#: deliberately READ-ONLY: ``ensure_read_only`` runs at registration, so a write
#: here would fail the round trip rather than exercise it.
STUB_CYPHER = "MATCH (a:BusinessApplication) RETURN a.app_id AS app_id LIMIT 5"
STUB_COLUMNS = ["app_id"]


def control_from_parts(parts: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The R4 control part, or None.

    Mirrors ``askApi.controlPart``: one part whose text is JSON carrying a
    ``drydocs_control`` object. Read from the parts rather than assumed to be at
    a fixed index, because the console sends [question, control] and a future
    caller may not.
    """
    for part in parts:
        text = part.get("text")
        if not isinstance(text, str):
            continue
        try:
            payload = json.loads(text)
        except (TypeError, ValueError):
            continue
        if isinstance(payload, dict) and isinstance(payload.get("drydocs_control"), dict):
            return payload["drydocs_control"]
    return None


def _event(payload: dict[str, Any]) -> dict[str, Any]:
    """One ADK event as the browser's ``parseAdkEvent`` expects to find it:
    the JSON payload lives in ``content.parts[0].text``, as a STRING."""
    return {
        "author": STUB_APP,
        "content": {"role": "model", "parts": [{"text": json.dumps(payload)}]},
    }


def _step(i: int, kind: str, ms: int, **extra: Any) -> dict[str, Any]:
    step: dict[str, Any] = {"i": i, "kind": kind, "ms": ms}
    step.update(extra)
    return {"kind": "step", "step": step}


def _envelope(explore_ref: str | None, run_id: str) -> dict[str, Any]:
    """The final answer envelope (ADR 0007). ``status`` is what makes the
    browser treat it as final rather than as a step, so it is never omitted."""
    return {
        "status": "ok",
        "run_id": run_id,
        "tier": "1",
        "answer": "Stub answer. No model was called and nothing was reasoned about.",
        "model": None,
        "steps": [
            {"i": 1, "kind": "router", "ms": 1},
            {
                "i": 2,
                "kind": "spec",
                "ms": 2,
                "database": STUB_DATABASE,
                "cypher": STUB_CYPHER,
                "rows": 0,
                "explore_ref": explore_ref,
            },
        ],
        "sources": [{"document": "spec:stub", "trust": "SYNTHESIZED"}],
        "metrics": {
            "iterations": 1,
            "llm_calls": 0,
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "context": {},
            "memory": {},
            "response_ms": {"total": 3},
        },
    }


class EphemeralRegistrar:
    """Registers one ephemeral spec against a real drydocs-api.

    Takes an httpx-shaped client so the caller decides the transport: an
    ASGI transport over ``create_app()`` in a test (no ports), or a plain
    ``httpx.Client(base_url=...)`` against a running server for a browser check.
    The stub itself knows neither.

    A registration FAILURE is recorded and surfaced in the step, never swallowed.
    A stub that quietly emitted ``explore_ref: null`` when the handshake broke
    would make the one thing this fixture exists to verify invisible.
    """

    def __init__(self, client: Any, agent_key: str | None = None) -> None:
        self.client = client
        self.agent_key = agent_key
        self.errors: list[str] = []

    def register(self, control: dict[str, Any]) -> str | None:
        token = control.get("api_token")
        if not isinstance(token, str) or not token:
            self.errors.append("control part carried no api_token")
            return None
        headers = {"X-DryDocs-Agent-Key": self.agent_key} if self.agent_key else {}
        res = self.client.post(
            "/specs/ephemeral",
            json={
                "owner_token": token,
                "cypher": STUB_CYPHER,
                "database": STUB_DATABASE,
                "params": {},
                "description": "R12 stub-ADK fixture registration",
                "columns": STUB_COLUMNS,
            },
            headers=headers,
        )
        if res.status_code != 200:
            self.errors.append(f"/specs/ephemeral returned {res.status_code}: {res.text[:200]}")
            return None
        ref = res.json().get("explore_ref")
        return ref if isinstance(ref, str) else None


def events_for(parts: list[dict[str, Any]], registrar: EphemeralRegistrar | None) -> list[dict]:
    """The full event sequence for one run — the single source of both the SSE
    stream and the buffered ``/run`` reply, so the two cannot disagree about
    what a turn looks like."""
    control = control_from_parts(parts)
    explore_ref: str | None = None
    error: str | None = None
    if control is not None and registrar is not None:
        explore_ref = registrar.register(control)
        if explore_ref is None and registrar.errors:
            error = registrar.errors[-1]

    return [
        _event(_step(1, "router", 1)),
        _event(
            _step(
                2,
                "spec",
                2,
                database=STUB_DATABASE,
                cypher=STUB_CYPHER,
                rows=0,
                explore_ref=explore_ref,
                error=error,
            )
        ),
        _event(_envelope(explore_ref, run_id="stub-run")),
    ]


def sse_body(events: list[dict[str, Any]]) -> str:
    """The exact wire format ``lib/adk.ts`` parses: ``data: <json>`` frames
    separated by a blank line."""
    return "".join(f"data: {json.dumps(e)}\n\n" for e in events)


def create_stub_adk(registrar: EphemeralRegistrar | None = None):
    """The stub app. Import is deferred so this module is importable without
    the optional ``api`` dependency group installed."""
    from fastapi import FastAPI, Request
    from fastapi.responses import StreamingResponse

    app = FastAPI(title="stub-adk", description="R12 fixture — not an agent")

    @app.get("/list-apps")
    def list_apps() -> list[str]:
        return [STUB_APP]

    @app.post("/apps/{app_name}/users/{user_id}/sessions/{session_id}")
    def create_session(app_name: str, user_id: str, session_id: str) -> dict[str, Any]:
        return {"id": session_id, "appName": app_name, "userId": user_id, "state": {}}

    def _parts(body: dict[str, Any]) -> list[dict[str, Any]]:
        message = body.get("newMessage") or {}
        parts = message.get("parts") or []
        return [p for p in parts if isinstance(p, dict)]

    @app.post("/run_sse")
    async def run_sse(request: Request) -> StreamingResponse:
        events = events_for(_parts(await request.json()), registrar)

        def frames() -> Iterator[bytes]:
            for event in events:
                yield f"data: {json.dumps(event)}\n\n".encode()

        return StreamingResponse(frames(), media_type="text/event-stream")

    @app.post("/run")
    async def run(request: Request) -> list[dict[str, Any]]:
        return events_for(_parts(await request.json()), registrar)

    return app


def main() -> None:  # pragma: no cover - the developer entry point
    """``python -m tests.stub_adk`` — serve the stub for a real browser check.

    Point the console at it with ``VITE_ADK_URL=http://localhost:8000``; it needs
    drydocs-api running for the ephemeral registration leg, and no LLM key for
    anything.
    """
    import os

    import httpx
    import uvicorn

    api_url = os.environ.get("DRYDOCS_API_URL", "http://localhost:8001")
    registrar = EphemeralRegistrar(
        httpx.Client(base_url=api_url, timeout=10.0),
        agent_key=os.environ.get("DRYDOCS_AGENT_REG_KEY"),
    )
    print(f"stub-adk on :8000 — registering ephemeral specs against {api_url}")
    uvicorn.run(create_stub_adk(registrar), host="127.0.0.1", port=8000)


if __name__ == "__main__":  # pragma: no cover
    main()
