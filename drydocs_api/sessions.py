"""In-memory session store — the token half of console authentication.

The server, not the browser, is the role authority on the api path (ADR 0005
decision 3): the client holds only an opaque token; role is resolved
server-side per request. In-memory is deliberate for the producer sandbox — a
durable store rides the company-side OIDC twin, not this one. A restart
therefore signs everybody out, which is a correct property here rather than a
gap: the console has no long-running state a session needs to survive.

O69 added the expiry. A token now stops working on its own, so an abandoned
browser tab cannot hold a live session indefinitely, and ``resolve`` is the one
place that decides it — no caller re-checks the clock, and no caller can forget
to. An expired token is a 401, exactly like an unknown one, and the client's
answer to both is the same: return to the sign-in screen.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from drydocs_api.personas import persona

#: How long a session lives. Short enough that a forgotten tab goes stale
#: within a working day, long enough that a console session is not interrupted
#: mid-task. A company binding its own OIDC replaces this with the token
#: lifetime its identity provider issues.
DEFAULT_TTL = timedelta(hours=8)


@dataclass(frozen=True)
class Session:
    token: str
    persona_id: str
    role: str
    issued_at: str  # ISO-8601 UTC
    expires_at: str  # ISO-8601 UTC

    def is_expired(self, now: datetime | None = None) -> bool:
        moment = now if now is not None else datetime.now(UTC)
        return moment >= datetime.fromisoformat(self.expires_at)


class InvalidTokenError(KeyError):
    """Raised when a token is unknown (never issued, or revoked)."""


class ExpiredTokenError(InvalidTokenError):
    """Raised when a token was valid but has passed its expiry.

    A subclass of :class:`InvalidTokenError` on purpose: every existing caller
    already maps that to 401, and expiry must not become a distinct status a
    handler could forget to handle.
    """


class InMemorySessionStore:
    def __init__(self, ttl: timedelta = DEFAULT_TTL) -> None:
        self._sessions: dict[str, Session] = {}
        self._ttl = ttl

    @property
    def ttl(self) -> timedelta:
        return self._ttl

    def issue(self, persona_id: str, *, now: datetime | None = None) -> Session:
        """Issue a session for a known persona (raises UnknownPersonaError otherwise).

        Authentication happens BEFORE this call: the store issues tokens, it
        does not decide who deserves one. See ``handlers.login``.
        """
        p = persona(persona_id)
        issued = now if now is not None else datetime.now(UTC)
        session = Session(
            token=secrets.token_urlsafe(24),
            persona_id=p.id,
            role=p.role,
            issued_at=issued.isoformat(timespec="seconds"),
            expires_at=(issued + self._ttl).isoformat(timespec="seconds"),
        )
        self._sessions[session.token] = session
        return session

    def resolve(self, token: str, *, now: datetime | None = None) -> Session:
        try:
            session = self._sessions[token]
        except KeyError as exc:
            raise InvalidTokenError("unknown or revoked session token") from exc
        if session.is_expired(now):
            # Drop it here rather than leaving it to a sweep: the store is
            # small, and an expired entry that lingers is one a later bug could
            # resurrect.
            del self._sessions[token]
            raise ExpiredTokenError("session expired; sign in again")
        return session

    def revoke(self, token: str) -> None:
        self._sessions.pop(token, None)

    def revoke_identity(self, persona_id: str) -> int:
        """Drop EVERY session held by one persona; returns how many went (O75).

        The explicit lever behind account withdrawal. It is not what makes
        withdrawal work -- ``handlers.authenticate`` refuses and drops a
        withdrawn account's session on its next request, so the common path
        needs no coordination at all -- but a caller that already knows an
        account is gone should not have to wait for each of its tokens to be
        presented before the store stops holding them.

        Named for the persona rather than the token because that is the unit a
        withdrawal is expressed in. This store never learns WHY: it is told an
        identity is finished, and the credential half is nowhere in scope here.
        """
        held = [t for t, s in self._sessions.items() if s.persona_id == persona_id]
        for token in held:
            del self._sessions[token]
        return len(held)

    def purge_expired(self, *, now: datetime | None = None) -> int:
        """Drop every expired session; returns how many went. Sessions whose
        tokens are never presented again would otherwise sit here for the life
        of the process."""
        moment = now if now is not None else datetime.now(UTC)
        stale = [t for t, s in self._sessions.items() if s.is_expired(moment)]
        for token in stale:
            del self._sessions[token]
        return len(stale)
