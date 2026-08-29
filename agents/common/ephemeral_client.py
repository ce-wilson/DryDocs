"""Ephemeral-spec registration client (R4 / ADR 0007 decision 4).

After the graph_qa pipeline executes a query, it registers that exact Cypher
with drydocs_api (``POST /specs/ephemeral``) and puts the returned
``explore_ref`` in the step record — Open-in-Explorer and Export in the Ask
spoke then reuse ``/specs/{ref}/run|export`` and the browser never submits
raw Cypher.

stdlib-only (urllib): the agents venv adds no HTTP dependency for this.
Configuration is server-side env, never a payload from the browser:

- ``DRYDOCS_API_URL``       — the thin API base (default http://localhost:8001)
- ``DRYDOCS_AGENT_REG_KEY`` — the trusted-caller key the endpoint requires

The *owner token* is the console user's drydocs_api session token, forwarded
by the Ask spoke with the question (R5 wiring). Without it there is no owner
to scope the ref to — ``make_register`` returns None and the envelope's
``explore_ref`` fields stay null, which is the honest pre-R5 state.
"""

from __future__ import annotations

import json
import os
import urllib.request
from collections.abc import Callable, Mapping

DEFAULT_API_URL = "http://localhost:8001"
TIMEOUT_S = 5.0


def make_register(
    owner_token: str | None,
    api_url: str | None = None,
    agent_key: str | None = None,
    run_id: str | None = None,
) -> Callable[..., str] | None:
    """Build the pipeline's ``register_cypher`` callable, or None when the
    registration surface isn't configured (no owner token / no agent key).

    ``run_id`` rides as ``X-DryDocs-Run-Id`` (G108 ruling D): it is the
    correlation key that joins the API's audit line to this run's ledger
    lines — closed over here rather than threaded through the pipeline, so
    ``register_cypher``'s call signature (and every fake of it) is unchanged."""
    api_url = (api_url or os.environ.get("DRYDOCS_API_URL") or DEFAULT_API_URL).rstrip("/")
    agent_key = agent_key or os.environ.get("DRYDOCS_AGENT_REG_KEY")
    if not owner_token or not agent_key:
        return None

    def register(
        cypher: str,
        database: str,
        params: Mapping[str, object] | None = None,
        description: str = "",
    ) -> str:
        body = json.dumps(
            {
                "owner_token": owner_token,
                "cypher": cypher,
                "database": database,
                "params": dict(params or {}),
                "description": description,
            }
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-DryDocs-Agent-Key": agent_key,
        }
        if run_id:
            headers["X-DryDocs-Run-Id"] = run_id
        request = urllib.request.Request(
            f"{api_url}/specs/ephemeral",
            data=body,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload["explore_ref"]

    return register
