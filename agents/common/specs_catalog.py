"""QuerySpec catalog access for the ADK agents — one Cypher source of truth.

The agents venv is separate from the poetry env, so the registry is imported
by path: the repo root goes on ``sys.path`` and ``drydocs_api.query_specs``
loads directly (that module and its two imports are framework-free by
design). No HTTP dependency on the thin API being up, and no second set of
named Cypher can drift into existence here — R2's acceptance says the agent
defines none of its own.

This module owns the path bootstrap; the guard re-exports below let the rest
of graph_qa use the API-grade read-only pre-flight without repeating it.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from common.scopes import in_scope  # noqa: E402
from drydocs_api.epistemics import grade  # noqa: E402
from drydocs_api.guard import WriteRejected, ensure_read_only  # noqa: E402
from drydocs_api.query_specs import (  # noqa: E402
    QUERY_SPECS,
    QuerySpec,
    is_watermarked,
)

__all__ = [
    "QUERY_SPECS",
    "is_watermarked",
    "QuerySpec",
    "WriteRejected",
    "ensure_read_only",
    "catalog_lines",
    "in_scope",
    "get_spec",
    "grade",
    "resolve_params",
]


def get_spec(spec_id: str) -> QuerySpec | None:
    return QUERY_SPECS.get(spec_id)


def catalog_lines(scope: str | None = None) -> list[str]:
    """One line per spec for the router prompt: id, database, params, description.

    AGENT1: ``scope`` is a ROUTER HINT and this is the only place it acts. A
    scoped catalog is a SHORTER catalog — the specs outside the scope are absent
    from the router system prompt, so the router cannot choose one, rather than
    being told not to. No tier, index or executor changes; the same router, the
    same text2cypher fallback, a different menu.

    ``None`` is UNSCOPED and returns every spec, which is what every caller did
    before this parameter existed and what the pipeline still does when no scope
    is asked for. The scope is RESOLVED before it arrives (``scopes.resolve``):
    an unknown or not-yet-ready scope degrades to ``None`` up there, so nothing
    here can produce an empty catalog.
    """
    lines = []
    for spec in QUERY_SPECS.values():
        if not in_scope(spec.id, scope):
            continue
        params = ", ".join(
            f"{p.name}:{p.type}" + ("" if p.required else f"={p.default}") for p in spec.params
        )
        lines.append(
            f"- {spec.id} [{spec.database}]"
            + (f" params({params})" if params else "")
            + f" — {spec.description}"
        )
    return lines


def resolve_params(spec: QuerySpec, provided: dict | None) -> dict:
    """Apply declared defaults and fail closed on unknown/missing params."""
    provided = dict(provided or {})
    resolved: dict = {}
    declared = {p.name: p for p in spec.params}
    unknown = set(provided) - set(declared)
    if unknown:
        raise ValueError(f"unknown params for {spec.id}: {sorted(unknown)}")
    for name, p in declared.items():
        if name in provided:
            value = provided[name]
            resolved[name] = int(value) if p.type == "int" else str(value)
        elif p.default is not None:
            resolved[name] = p.default
        elif p.required:
            raise ValueError(f"missing required param '{name}' for {spec.id}")
    return resolved
