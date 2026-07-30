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
"""

from __future__ import annotations

import json

CONTROL_KEY = "drydocs_control"


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
