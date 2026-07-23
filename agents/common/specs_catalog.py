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

from drydocs_api.guard import WriteRejected, ensure_read_only  # noqa: E402,F401
from drydocs_api.query_specs import (  # noqa: E402
    QUERY_SPECS,
    WATERMARKED_DATABASES,
    QuerySpec,
)

__all__ = [
    "QUERY_SPECS",
    "WATERMARKED_DATABASES",
    "QuerySpec",
    "WriteRejected",
    "ensure_read_only",
    "catalog_lines",
    "get_spec",
    "resolve_params",
]


def get_spec(spec_id: str) -> QuerySpec | None:
    return QUERY_SPECS.get(spec_id)


def catalog_lines() -> list[str]:
    """One line per spec for the router prompt: id, database, params, description."""
    lines = []
    for spec in QUERY_SPECS.values():
        params = ", ".join(
            f"{p.name}:{p.type}" + ("" if p.required else f"={p.default}")
            for p in spec.params
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
