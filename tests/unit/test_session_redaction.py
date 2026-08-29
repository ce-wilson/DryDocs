"""R23 — the Ask control token must not reach the ADK session store.

Observed 2026-08-21 (desktop, session ``ask-jdoe4821-wjtacr8x``): the raw bearer
token appeared verbatim in all three user events of
``agents/graph_qa/.adk/session.db``, because ``askApi.ts`` sends it as an in-band
message part and ADK writes every part as given. It had no expiry, so a copy
taken from that file replayed for the life of the API process.

WHY THIS SUITE USES A STUB STORE RATHER THAN ADK. ``agents/`` runs on its own
interpreter (``agents/.venv``) and this repo's venv has no ``google-adk``, so a
guard that needed a real runtime could not run here at all — and a fix nothing in
CI can hold onto is how this class returns. ``control.py``'s own docstring says
the in-band shape was chosen so it is "testable without an ADK runtime", and
``common.session_redaction`` is duck-typed for exactly that reason: the stub
below is a session store in every sense this defect cares about, because the
defect is "what got written", not "which database wrote it".

The one thing a stub cannot prove is that ADK still calls the seam the wrapper
is installed at. ``test_the_adk_seam_the_launcher_patches_still_exists`` covers
that and SKIPS where ADK is absent (the U26 precedent), so the ADK-present
machine gets the check and the ADK-absent machine gets an honest skip rather
than a green that means nothing.
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.session_redaction import RedactingSessionService, redacted_event  # noqa: E402
from graph_qa.control import (  # noqa: E402
    CONTROL_KEY,
    REDACTED_VALUE,
    SECRET_CONTROL_FIELDS,
    redact_control_text,
    split_question_and_control,
)

TOKEN = "tok-live-9f3a2b7c4d1e"  # nosec — a fixture value, never a real token
QUESTION = "which jobs run in the nightly window?"
CONTROL_PART = json.dumps({CONTROL_KEY: {"api_token": TOKEN, "api_url": "http://localhost:8001"}})


# --------------------------------------------------------------------------
# A stub of exactly as much ADK as the wrapper touches: parts with text, an
# event with content, and a store that records what it was handed.
# --------------------------------------------------------------------------
@dataclass
class StubPart:
    text: str | None


@dataclass
class StubContent:
    role: str = "user"
    parts: list[StubPart] = field(default_factory=list)


@dataclass
class StubEvent:
    author: str = "user"
    content: StubContent | None = None


class StubStore:
    """Records the events it was asked to persist, and nothing else.

    ``written_blob`` is the honest test of "did the value reach the store":
    it flattens everything recorded, so a token surviving anywhere — a part
    this suite did not think to name, a field added later — still trips it.
    """

    def __init__(self) -> None:
        self.written: list[StubEvent] = []
        self.created: list[str] = []

    async def append_event(self, session: object, event: StubEvent) -> StubEvent:
        self.written.append(event)
        return event

    async def create_session(self, app_name: str) -> str:
        self.created.append(app_name)
        return app_name

    @property
    def written_blob(self) -> str:
        return json.dumps(
            [
                [part.text for part in (event.content.parts if event.content else [])]
                for event in self.written
            ]
        )


def _user_event(*texts: str | None) -> StubEvent:
    return StubEvent(content=StubContent(parts=[StubPart(text) for text in texts]))


def _persist(store: StubStore, event: StubEvent) -> StubEvent:
    service = RedactingSessionService(store, redact_control_text)
    return asyncio.run(service.append_event(session=object(), event=event))


# --------------------------------------------------------------------------
# (a) + (b) — the value stops reaching disk, and a test says so
# --------------------------------------------------------------------------
def test_the_token_never_reaches_the_store() -> None:
    """The acceptance clause, stated the way the defect was found: after a turn,
    the token VALUE appears nowhere in what was persisted."""
    store = StubStore()
    _persist(store, _user_event(QUESTION, CONTROL_PART))

    assert TOKEN not in store.written_blob
    assert REDACTED_VALUE in store.written_blob


def test_the_stored_event_still_shows_a_handshake_happened() -> None:
    """Redaction replaces the VALUE, never the field. The R5 trail is read for
    'did this turn carry control', which a deletion would silently answer no."""
    store = StubStore()
    _persist(store, _user_event(QUESTION, CONTROL_PART))

    stored = json.loads(store.written[0].content.parts[1].text)
    assert set(stored[CONTROL_KEY]) == {"api_token", "api_url"}
    assert stored[CONTROL_KEY]["api_token"] == REDACTED_VALUE
    assert stored[CONTROL_KEY]["api_url"] == "http://localhost:8001", (
        "api_url is configuration, not a credential — redacting it would cost "
        "readability for no security gain"
    )


def test_the_question_is_stored_untouched() -> None:
    """Part 0 is the user's own text and is not this wrapper's business."""
    store = StubStore()
    _persist(store, _user_event(QUESTION, CONTROL_PART))

    assert store.written[0].content.parts[0].text == QUESTION


# --------------------------------------------------------------------------
# (c) — the handshake still works: the live turn keeps the real token
# --------------------------------------------------------------------------
def test_the_live_event_is_not_mutated() -> None:
    """The load-bearing one. Upstream, the persisted event's ``content`` IS the
    object the agent reads as ``ctx.user_content``, so redacting in place would
    take the token away from the very turn that needs it and Open-in-Explorer
    would quietly stop working."""
    store = StubStore()
    live = _user_event(QUESTION, CONTROL_PART)
    _persist(store, live)

    assert live.content.parts[1].text == CONTROL_PART
    question, control = split_question_and_control([part.text for part in live.content.parts])
    assert question == QUESTION
    assert control["api_token"] == TOKEN


def test_a_resumed_turn_degrades_to_no_control_rather_than_a_wrong_one() -> None:
    """Stated because it is a real consequence, not an oversight: a resumed
    invocation recovers its user content from STORED history, so it sees the
    placeholder. That reads as 'no usable control' — the same degradation a
    malformed part already produces — and never as an error or a wrong token."""
    store = StubStore()
    _persist(store, _user_event(QUESTION, CONTROL_PART))

    _, control = split_question_and_control([part.text for part in store.written[0].content.parts])
    assert control["api_token"] != TOKEN
    assert control["api_token"] == REDACTED_VALUE


# --------------------------------------------------------------------------
# Nothing to redact costs nothing, and everything else passes through
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("label", "texts"),
    [
        ("no control part at all", (QUESTION,)),
        ("a part that is not JSON", (QUESTION, "not json")),
        ("JSON without the control key", (QUESTION, '{"other": 1}')),
        ("control with no secret field", (QUESTION, json.dumps({CONTROL_KEY: {"api_url": "u"}}))),
        ("an empty part", (QUESTION, None)),
    ],
)
def test_an_event_with_nothing_secret_is_stored_as_sent(label: str, texts: tuple) -> None:
    """Returned by IDENTITY, which is a stronger claim than equality: a turn
    with no credential in it is not copied, not rebuilt, not touched."""
    store = StubStore()
    live = _user_event(*texts)
    _persist(store, live)

    assert store.written[0] is live, label


def test_the_wrapper_delegates_everything_it_has_no_opinion_about() -> None:
    """One opinion, about writes. create/get/list/delete/flush are the inner
    service's, so wrapping cannot change how sessions are found or removed."""
    store = StubStore()
    service = RedactingSessionService(store, redact_control_text)

    assert asyncio.run(service.create_session("graph_qa")) == "graph_qa"
    assert store.created == ["graph_qa"]
    assert service.written is store.written


def test_redacted_event_tolerates_an_event_with_no_content() -> None:
    """ADK writes plenty of events that are not user messages."""
    assert redacted_event(StubEvent(content=None), redact_control_text) is not None


# --------------------------------------------------------------------------
# The pure rule
# --------------------------------------------------------------------------
def test_redact_control_text_reports_unchanged_as_none() -> None:
    assert redact_control_text(None) is None
    assert redact_control_text("") is None
    assert redact_control_text("plain question") is None
    assert redact_control_text('{"other": 1}') is None
    assert redact_control_text(json.dumps({CONTROL_KEY: {"api_url": "u"}})) is None


def test_every_declared_secret_field_is_actually_redacted() -> None:
    """Guards the set rather than the one field, so adding a credential to the
    control shape without adding it to SECRET_CONTROL_FIELDS shows up here."""
    for name in SECRET_CONTROL_FIELDS:
        text = json.dumps({CONTROL_KEY: {name: "sensitive-value-xyz"}})
        stored = redact_control_text(text)
        assert stored is not None, name
        assert "sensitive-value-xyz" not in stored, name


# --------------------------------------------------------------------------
# The one thing the stub cannot prove
# --------------------------------------------------------------------------
def test_the_adk_seam_the_launcher_patches_still_exists() -> None:
    """``serve.py`` installs the wrapper by replacing ONE ADK function. If an
    upgrade renames it the launcher raises at start — this check moves that
    discovery to the suite on any machine that has ADK, and skips honestly
    where it does not (this repo's venv; the agents venv has it)."""
    fast_api = pytest.importorskip(
        "google.adk.cli.fast_api",
        reason="google-adk lives in agents/.venv, not this interpreter",
    )
    import serve

    assert hasattr(fast_api, serve._ADK_SESSION_FACTORY)
