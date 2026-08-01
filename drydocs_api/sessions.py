"""In-memory session store — the auth stub's token half.

The server, not the browser, is the role authority on the api path (ADR 0005
decision 3): the client holds only an opaque token; role is resolved
server-side per request. In-memory is deliberate for the producer sandbox —
a durable store rides the company-side OIDC twin, not this stub.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from drydocs_api.personas import persona


@dataclass(frozen=True)
class Session:
    token: str
    persona_id: str
    role: str
    issued_at: str  # ISO-8601 UTC


class InvalidTokenError(KeyError):
    """Raised when a token is unknown (never issued, or revoked)."""


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def issue(self, persona_id: str) -> Session:
        """Issue a session for a known persona (raises UnknownPersonaError otherwise)."""
        p = persona(persona_id)
        session = Session(
            token=secrets.token_urlsafe(24),
            persona_id=p.id,
            role=p.role,
            issued_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        self._sessions[session.token] = session
        return session

    def resolve(self, token: str) -> Session:
        try:
            return self._sessions[token]
        except KeyError as exc:
            raise InvalidTokenError("unknown or revoked session token") from exc

    def revoke(self, token: str) -> None:
        self._sessions.pop(token, None)
