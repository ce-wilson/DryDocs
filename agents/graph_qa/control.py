"""Ask-spoke control channel (R5) — pure, offline-testable.

The console sends the user's question as message part 0 and an OPTIONAL
control part after it: a JSON object under the ``drydocs_control`` key
carrying what the agent needs to act on the caller's behalf —

    {"drydocs_control": {"api_token": "<drydocs-api session token>",
                         "api_url": "http://localhost:8001"}}

The token is the browser's own drydocs-api session (the R4 owner token):
with it, the agent registers each executed Cypher as an ephemeral spec owned
by THAT session, so Open-in-Explorer/Export work for the asking user and
nobody else. Control parts never reach the LLM — the pipeline only ever sees
part 0 — and an in-band part was chosen over ADK session state deliberately:
the shape is fully owned by this repo on both ends, testable without an ADK
runtime, and carries no assumption about ADK's request schema. Company-side
OIDC replaces the whole handshake (ADR 0005 Evidence).

PERSISTENCE (R23) — the property this docstring used to leave unstated, which
is how a live credential shipped to disk. Control parts never reach the LLM AND
the secret ones never reach the session store: ADK persists every part of the
user message as given, so ``redact_control_text`` below defines the STORED form
of a part and ``common.session_redaction`` applies it on the way to the store.
The live token is held only in the invocation's in-memory ``user_content`` for
the turn. Two consequences worth stating rather than discovering: the SSE echo
of the user event carries the redacted text (harmless — the browser sent it),
and a RESUMED invocation, which recovers its user content from stored history,
sees the placeholder rather than the token, so it degrades to "no control"
exactly as a malformed part does (``explore_refs`` stay null, never an error).
"""

from __future__ import annotations

import json

CONTROL_KEY = "drydocs_control"

#: Control fields whose VALUE is a credential. ``api_url`` is deliberately not
#: here: it is configuration, it is useful in a stored trace, and redacting it
#: would make the persisted event harder to read for no security gain.
SECRET_CONTROL_FIELDS = frozenset({"api_token"})

#: What a redacted value reads as. A fixed marker rather than a deletion, so a
#: stored event still shows that a handshake HAPPENED — the field is what the
#: R5 trail is read for, the value is what must not be there.
REDACTED_VALUE = "[redacted-by-drydocs]"


def split_question_and_control(texts: list[str]) -> tuple[str, dict]:
    """Part 0 is the question; any later part that parses as a JSON object
    with a ``drydocs_control`` dict contributes control fields. Anything
    else is ignored — a malformed control part degrades to 'no control'
    (explore_refs stay null), never to an error."""
    question = (texts[0] if texts else "").strip()
    control: dict = {}
    for text in texts[1:]:
        try:
            payload = json.loads(text or "")
        except (ValueError, TypeError):
            continue
        if isinstance(payload, dict) and isinstance(payload.get(CONTROL_KEY), dict):
            control.update(payload[CONTROL_KEY])
    return question, control


def redact_control_text(text: str | None) -> str | None:
    """The STORED form of one message part, or ``None`` when the part carries
    nothing secret and may be persisted exactly as sent.

    Returning ``None`` for "unchanged" rather than echoing the input is what
    lets the caller keep the original object when nothing needs replacing, so
    a turn with no control part costs no copy and no equality check.

    Parses by the same rule as :func:`split_question_and_control` on purpose:
    if a part is not control to the reader, it is not control to the redactor
    either, and the two can never disagree about which part holds the token.
    """
    try:
        payload = json.loads(text or "")
    except (ValueError, TypeError):
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get(CONTROL_KEY), dict):
        return None
    control = payload[CONTROL_KEY]
    if not any(field in SECRET_CONTROL_FIELDS for field in control):
        return None
    stored = dict(payload)
    stored[CONTROL_KEY] = {
        field: (REDACTED_VALUE if field in SECRET_CONTROL_FIELDS else value)
        for field, value in control.items()
    }
    return json.dumps(stored)
