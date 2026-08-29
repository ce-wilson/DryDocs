"""R23 — the session store is the last place a live credential should sit.

ADK persists the user message VERBATIM: ``Runner._append_user_event`` builds an
``Event`` whose ``content`` is the very object handed to ``run_async``, and the
session service writes every part as given. The R5 handshake sends the caller's
drydocs-api token as an in-band control part (``graph_qa.control``), so once per
turn that token landed in ``<app>/.adk/session.db`` in cleartext — with no
expiry, because ``InMemorySessionStore.issue`` mints a token that only ``revoke``
or an API restart ends. A copy taken from the file replays for the life of the
process.

This module is the single choke point that stops it: every session service
implementation persists through ``append_event``, so wrapping that one method
covers local SQLite, a database URI and the in-memory service identically,
without the caller knowing which one it got.

TWO PROPERTIES THIS FILE EXISTS TO KEEP, both load-bearing:

1. **The copy is a copy.** The persisted event and the agent's ``user_content``
   are the SAME ``Content`` object upstream, so redacting in place would take
   the token away from the turn that needs it. Nothing here mutates its input —
   an event with nothing to redact is returned unchanged and uncopied, and one
   with something to redact is replaced by a deep copy that is written instead.
2. **It is duck-typed, not subclassed.** Nothing here imports ADK, which is what
   lets the guard drive it with a stub store in the repo's own interpreter —
   ``agents/`` has its own venv, and a fix provable only inside that venv is a
   fix nothing in CI can hold onto.

The redaction RULE is not here on purpose: it belongs to the app that owns the
control shape (``graph_qa.control.redact_control_text``), and is passed in. A
second app with a different secret shape reuses this wrapper by handing it a
different rule rather than by teaching this file about its payload.
"""

from __future__ import annotations

import copy
from collections.abc import Callable

#: A redactor takes one part's text and returns its STORED form, or ``None``
#: when the part is already safe to store as sent.
Redactor = Callable[[object], object]


def _deep_copy(event: object) -> object:
    """A pydantic-aware deep copy, falling back to :mod:`copy` for stubs."""
    model_copy = getattr(event, "model_copy", None)
    if callable(model_copy):
        return model_copy(deep=True)
    return copy.deepcopy(event)


def redacted_event(event: object, redact_text: Redactor) -> object:
    """``event`` itself when nothing needs redacting, else a deep copy whose
    affected parts carry their stored form.

    Returning the ORIGINAL object in the common case is deliberate: it makes
    "this turn had no secret in it" observable by identity in a test, which is
    a stronger statement than an equality check on two copies.
    """
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None) or []
    replacements: dict[int, object] = {}
    for index, part in enumerate(parts):
        stored = redact_text(getattr(part, "text", None))
        if stored is not None:
            replacements[index] = stored
    if not replacements:
        return event
    clean = _deep_copy(event)
    for index, stored in replacements.items():
        clean.content.parts[index].text = stored
    return clean


class RedactingSessionService:
    """Delegating wrapper around a session service: everything is the inner
    service's behaviour, except that ``append_event`` persists a redacted copy.

    The wrapper returns what the inner service returned — which for ADK is the
    event it stored — so the SSE echo of the user message carries the redacted
    text. That is the intended shape: the browser already holds the token it
    just sent, and an echo is exactly the sort of place a credential leaks on
    to a screen or into a log.
    """

    def __init__(self, inner: object, redact_text: Redactor) -> None:
        self._inner = inner
        self._redact_text = redact_text

    def __getattr__(self, name: str) -> object:
        # Only reached for names this class does not define, so create_session,
        # get_session, list_sessions, delete_session and flush all pass through
        # untouched — this wrapper has one opinion and it is about writes.
        return getattr(self._inner, name)

    def __repr__(self) -> str:
        return f"RedactingSessionService({self._inner!r})"

    async def append_event(self, session: object, event: object) -> object:
        return await self._inner.append_event(
            session=session, event=redacted_event(event, self._redact_text)
        )
