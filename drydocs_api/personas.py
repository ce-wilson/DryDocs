"""Server-side synthetic personas — the console's identity source.

Mirrors ``web/src/lib/auth.ts``: same ids, same roles. A unit test parses the
TS file and fails on drift. Enterprise OIDC (SID + roles-from-claims) replaces
this module company-side per ADR 0005's Evidence — a gitignored twin, never
here. The secrets that back these ids are machine-local and never committed
(``drydocs_api/credentials.py``).

THE IDS ARE OBVIOUSLY FICTIONAL, and that is the point rather than a joke. They
were SID-shaped until 2026-08-28 (``jdoe4821``, ``asmith7734``, ``kchen2190``),
which read as realistic in a demo and carried a standing risk with it: an id
that looks like a real corporate SID is an id somebody can mistake for one, in a
screenshot, a bug report, or a file that escapes the publish boundary. A name no
directory could ever issue cannot be mistaken that way. The one thing the rename
must not do is imply these are people — they are four access levels and three
seats at the lowest of them.

WHY THREE USER-TIER ACCOUNTS: several console behaviours are scoped PER PERSONA
rather than per role — the Ask panel's stored last turn is the case O64 tested —
and proving isolation needs two accounts that differ in nothing but identity.
"""

from __future__ import annotations

from dataclasses import dataclass

ROLES = ("user", "steward", "admin")


@dataclass(frozen=True)
class Persona:
    id: str
    role: str  # 'user' | 'steward' | 'admin'


PERSONAS: dict[str, Persona] = {
    "morpheus": Persona(id="morpheus", role="admin"),
    # steward = the O13 power-user tier (user < steward < admin): sees
    # /mappings, not /admin/config and not raw Cypher.
    "trinity": Persona(id="trinity", role="steward"),
    # O47: the intake persona. Role 'user' on purpose — SME is a persona, not
    # a fourth role tier; the /intake page gate is client-side (auth.ts
    # canAccessIntake) and the intake API's own transition map is role-based,
    # so an SME holds exactly the user-tier server rights.
    "neo": Persona(id="neo", role="user"),
    # Three plain user-tier seats, identical in rights and distinct only in
    # identity — which is what makes per-persona isolation testable at all.
    "mouse": Persona(id="mouse", role="user"),
    "tank": Persona(id="tank", role="user"),
    "dozer": Persona(id="dozer", role="user"),
}


class UnknownPersonaError(KeyError):
    """Raised when a login names a persona the server does not know."""


def persona(persona_id: str) -> Persona:
    try:
        return PERSONAS[persona_id]
    except KeyError as exc:
        raise UnknownPersonaError(persona_id) from exc
