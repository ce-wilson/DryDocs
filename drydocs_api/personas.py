"""Server-side personas — the console's identity source, READ from the declaration.

The roster itself lives in ``config/console-personas.yaml`` and is read through
:mod:`drydocs_core.console_personas` (CFG14, 2026-09-10). It used to be declared
here AND in ``web/src/lib/auth.ts``, with a unit test parsing the TypeScript to
catch the drift two declarations guarantee; the duplication was the defect and
the regex was the symptom. This module keeps its CONTRACT — ``Persona``,
``PERSONAS``, ``persona()``, ``UnknownPersonaError`` — and loses the data.

Enterprise OIDC (SID + roles-from-claims) replaces this module company-side per
ADR 0005's Evidence — a gitignored twin, never here. The secrets that back these
ids are machine-local and never committed (``drydocs_api/credentials.py``); this
change moves no secret.

THE IDS ARE OBVIOUSLY FICTIONAL, and the reasoning now lives beside the roster in
the declaration rather than in this docstring, so it is read by whoever edits the
seats rather than by whoever imports them.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from drydocs_core.console_personas import ConsolePersonas

ROLES = ("user", "steward", "admin")


@dataclass(frozen=True)
class Persona:
    id: str
    role: str  # 'user' | 'steward' | 'admin'


class UnknownPersonaError(KeyError):
    """Raised when a login names a persona the server does not know."""


@lru_cache(maxsize=1)
def _roster() -> dict[str, Persona]:
    """The declared roster, read once.

    Cached because the declaration is a committed file that cannot change under a
    running server, and a per-login YAML parse would be a cost paid for nothing.
    Tests that write a different declaration clear it with ``_roster.cache_clear()``.
    """
    declared = ConsolePersonas.from_yaml()
    return {p.id: Persona(id=p.id, role=p.role) for p in declared.personas.values()}


def personas() -> dict[str, Persona]:
    """The roster as a mapping — the callable form, for anything that may run
    before or after a test swaps the declaration."""
    return dict(_roster())


def persona(persona_id: str) -> Persona:
    try:
        return _roster()[persona_id]
    except KeyError as exc:
        raise UnknownPersonaError(persona_id) from exc


def __getattr__(name: str) -> object:
    """``PERSONAS``, resolved on first access rather than at import.

    Callers and tests read ``PERSONAS`` directly and keep doing so - CFG14 moved
    where the data comes from, not the shape the server offers it in. What it
    must NOT do is turn importing this module into a filesystem read.

    ``drydocs_api.intake`` imports ``sessions``, which imports this module, so a
    module-level ``PERSONAS = _roster()`` would make an unreadable roster abort an
    import four modules away with a traceback naming neither the roster nor the
    caller. Measured, not supposed: the J48 worktree probe in
    ``tests/unit/test_repo_paths.py`` imports ``drydocs_api.intake`` and failed
    exactly that way while the declaration was still uncommitted.

    The refusal itself is right and is kept - a roster that cannot be read is not
    an empty roster. It now fires at whoever asked for the roster. PEP 562: this
    runs only for names the module does not define, so it costs nothing per access
    after the first, and ``_roster`` is cached besides.
    """
    if name == "PERSONAS":
        return _roster()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """``PERSONAS`` is reachable but not in the module dict, so name it here."""
    return sorted([*globals(), "PERSONAS"])
