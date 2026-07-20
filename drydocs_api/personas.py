"""Server-side synthetic personas — the session-auth STUB's identity source.

Mirrors ``web/src/lib/auth.ts`` (the O2 mock the API replaces as role
authority): same synthetic ids, same two roles. A unit test parses the TS file
and fails on drift. Enterprise OIDC (SID + roles-from-claims) replaces this
module company-side per ADR 0005's Evidence — a gitignored twin, never here.
Ids are synthetic; real SIDs never land in this repo (publish boundary).
"""

from __future__ import annotations

from dataclasses import dataclass

ROLES = ("user", "steward", "admin")


@dataclass(frozen=True)
class Persona:
    id: str
    role: str  # 'user' | 'steward' | 'admin'


PERSONAS: dict[str, Persona] = {
    "jdoe4821": Persona(id="jdoe4821", role="user"),
    "asmith7734": Persona(id="asmith7734", role="admin"),
    # steward = the O13 power-user tier (user < steward < admin): sees
    # /mappings, not /admin/config and not raw Cypher.
    "kchen2190": Persona(id="kchen2190", role="steward"),
}


class UnknownPersonaError(KeyError):
    """Raised when a login names a persona the stub does not know."""


def persona(persona_id: str) -> Persona:
    try:
        return PERSONAS[persona_id]
    except KeyError as exc:
        raise UnknownPersonaError(persona_id) from exc
