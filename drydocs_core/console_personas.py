"""The console's demo roster, declared once — reader for ``config/console-personas.yaml``.

CFG14, 2026-09-10. The roster used to be written twice, in TypeScript and in
Python, with a unit test parsing the TypeScript to catch the drift that
duplication guarantees. Both sides now read this declaration: ``drydocs_api``
through this module, the console through the rendered
``web/src/generated/console-personas.json``.

WHAT THIS IS NOT. It is not an authorization source. The server re-resolves the
real role from the bearer token on every request (ADR 0005 decision 3), and the
role a browser holds decides which nav entries render and nothing else. This
module answers "who may sign in to a demo, and what does the nav look like" —
never "what may they do".

THE CLAIM BLOCK IS DECLARED AND DEFERRED, never absent (gate
``console-auth-boundary``, SIGNED 2026-09-10, §C P4). Its status and its contents
must agree: a deferred block with a mapping in it, or an adopted block with none,
is a declaration asserting something nobody checked, and both are refused here
rather than at whichever call site reads it first. That is the ``wired`` axis's
shape (CFG13) applied to entitlements.

Pure config reading: no graph, no database, no network, and nothing imported from
any component.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from drydocs_core.repo_paths import repo_root

REPO_ROOT = repo_root(Path(__file__).resolve().parents[1])
DEFAULT_PERSONAS_PATH = REPO_ROOT / "config" / "console-personas.yaml"

SCHEMA_ID = "drydocs.console-personas.v1"

#: A deferred claim block carries a written reason of at least this many
#: characters. The SOURCELESS_LOADERS idiom, and the same length the ``wired``
#: axis uses: forty characters is where "deferred" has to become "deferred
#: because ...", which is the difference between a fact and a decision.
CLAIM_REASON_MIN = 40

#: The two legal states of the claim block. ``deferred`` means the mapping is
#: empty and the reason says why; ``adopted`` means it is populated.
CLAIM_DEFERRED = "deferred"
CLAIM_ADOPTED = "adopted"
CLAIM_STATUSES = (CLAIM_DEFERRED, CLAIM_ADOPTED)


class ConsolePersonaError(ValueError):
    """A roster declaration that cannot be trusted — never a silent fallback."""


@dataclass(frozen=True)
class ConsolePersona:
    """One seat: an id, the role it maps to, and what the console shows for it."""

    id: str
    display_name: str
    role: str
    chip: str
    #: Scopes the area cascade's default for a user-tier seat. ``None`` above it:
    #: a steward or admin is not scoped to one tower, so a tower on such a seat
    #: is a declaration contradicting itself and is refused.
    tower_key: str | None = None


@dataclass(frozen=True)
class ClaimMapping:
    """The claim-to-role mapping — empty and deferred until the console onboards."""

    status: str
    reason: str
    mapping: dict[str, str]

    @property
    def is_deferred(self) -> bool:
        return self.status == CLAIM_DEFERRED


class ConsolePersonas:
    """The declared roster, validated at construction."""

    def __init__(self, config: dict[str, Any]) -> None:
        if config.get("schema") != SCHEMA_ID:
            raise ConsolePersonaError(f"unexpected schema {config.get('schema')!r}")

        roles = config.get("roles")
        if not isinstance(roles, list) or not roles:
            raise ConsolePersonaError("roles: must be a non-empty closed list")
        self.roles: tuple[str, ...] = tuple(str(r) for r in roles)

        rows = config.get("personas")
        if not isinstance(rows, dict) or not rows:
            raise ConsolePersonaError(
                "personas: missing or empty — an empty roster would make every "
                "sign-in fail and every guard over it vacuous"
            )

        personas: dict[str, ConsolePersona] = {}
        for pid, spec in rows.items():
            personas[str(pid)] = self._persona(str(pid), spec)
        self.personas: dict[str, ConsolePersona] = personas
        self.claims: ClaimMapping = self._claims(config.get("claims"))

    def _persona(self, pid: str, spec: Any) -> ConsolePersona:
        if not isinstance(spec, dict):
            raise ConsolePersonaError(f"{pid}: not a mapping")
        role = str(spec.get("role") or "").strip()
        if not role:
            raise ConsolePersonaError(f"{pid}: declares no role")
        if role not in self.roles:
            raise ConsolePersonaError(
                f"{pid}: role {role!r} is not on the closed list {list(self.roles)} — "
                "a new tier is an edit to the roles list and its guard, never a value "
                "that widens the set by arriving"
            )
        display_name = str(spec.get("display_name") or "").strip()
        if not display_name:
            raise ConsolePersonaError(f"{pid}: declares no display_name")
        tower = spec.get("tower_key")
        tower_key = str(tower).strip() if tower else None
        if tower_key and role != "user":
            raise ConsolePersonaError(
                f"{pid}: tower_key on a {role!r} seat — a tower scopes a user-tier "
                "drill, and a steward or admin is not scoped to one, so this "
                "declaration contradicts itself"
            )
        return ConsolePersona(
            id=pid,
            display_name=display_name,
            role=role,
            chip=str(spec.get("chip") or "").strip(),
            tower_key=tower_key,
        )

    def _claims(self, block: Any) -> ClaimMapping:
        """The claim block is DECLARED and its status must match its contents."""
        if not isinstance(block, dict):
            raise ConsolePersonaError(
                "claims: block missing or not a mapping — it is declared and deferred, "
                "never absent (gate console-auth-boundary, §C P4)"
            )
        status = str(block.get("status") or "").strip()
        if status not in CLAIM_STATUSES:
            raise ConsolePersonaError(
                f"claims.status {status!r} is not one of {list(CLAIM_STATUSES)}"
            )
        mapping = block.get("mapping")
        if not isinstance(mapping, dict):
            raise ConsolePersonaError("claims.mapping: must be a mapping, empty when deferred")
        reason = block.get("reason")
        if status == CLAIM_DEFERRED:
            if mapping:
                raise ConsolePersonaError(
                    "claims: status is deferred but the mapping is not empty — the status "
                    "and the contents disagree, so one of them is asserting something "
                    "nobody checked"
                )
            if not isinstance(reason, str) or len(reason.strip()) < CLAIM_REASON_MIN:
                raise ConsolePersonaError(
                    f"claims: a deferred block needs a reason of at least {CLAIM_REASON_MIN} "
                    "characters — a bare deferral is a fact with no owner, a reasoned one is "
                    "a decision someone can re-read and reverse"
                )
        elif not mapping:
            raise ConsolePersonaError(
                "claims: status is adopted but the mapping is empty — an adopted mapping "
                "that maps nothing grants nothing, and would read as working"
            )
        for group, role in mapping.items():
            if str(role) not in self.roles:
                raise ConsolePersonaError(
                    f"claims.mapping[{group!r}]: role {role!r} is not on the closed list"
                )
        return ClaimMapping(
            status=status,
            reason=str(reason or "").strip(),
            mapping={str(k): str(v) for k, v in mapping.items()},
        )

    # ---- construction ----------------------------------------------------
    @classmethod
    def from_yaml(cls, path: Path | None = None) -> ConsolePersonas:
        src = Path(path) if path is not None else DEFAULT_PERSONAS_PATH
        if not src.is_file():
            raise ConsolePersonaError(f"roster declaration missing: {src}")
        return cls(yaml.safe_load(src.read_text(encoding="utf-8")) or {})

    # ---- queries ---------------------------------------------------------
    def get(self, persona_id: str) -> ConsolePersona:
        try:
            return self.personas[persona_id]
        except KeyError:
            raise ConsolePersonaError(f"unknown persona {persona_id!r}") from None

    def ids(self) -> list[str]:
        return list(self.personas)

    def by_role(self, role: str) -> list[ConsolePersona]:
        return [p for p in self.personas.values() if p.role == role]

    def as_rows(self) -> list[dict[str, Any]]:
        """The roster as the console consumes it — the render's payload.

        Key names are the TypeScript ones (``displayName``, ``towerKey``), because
        the generated JSON is imported straight into a typed structure there and a
        rename here would be a silent break at a boundary no Python test crosses.
        ``towerKey`` is omitted rather than null when absent, matching the optional
        field the interface already declares.
        """
        rows: list[dict[str, Any]] = []
        for p in self.personas.values():
            row: dict[str, Any] = {
                "id": p.id,
                "displayName": p.display_name,
                "role": p.role,
                "chip": p.chip,
            }
            if p.tower_key:
                row["towerKey"] = p.tower_key
            rows.append(row)
        return rows
