"""Read-only corroboration (0002-B §2 step 5; TDD Stage A, third row).

A legacy definition must *reconcile* with the corroborating sources of truth — the
Oracle ``psgmgr`` extract and the loaded ``drydocs`` graph — before any transform of it
is trusted. Both are READ-ONLY here: this component never writes a database, and the
mechanism enforces it rather than promising it —

- :func:`reconcile_variables` is pure comparison (transcript/definition vs extract rows).
- :class:`ReadOnlyGraph` is the ONLY path to the graph: it wraps
  ``drydocs_core.Neo4jClient`` exposing a single ``fetch`` that REFUSES any Cypher
  containing a write clause (raises :class:`GraphWriteAttemptError` before the driver is
  touched) and deliberately does not expose the client's script/file executors. The
  schema-specific corroboration queries are written company-side against the live graph
  (Track 2) — through this wrapper, so the read-only property survives them.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .formats import DefinitionSet, VariableDefs

if TYPE_CHECKING:  # driver type only; no runtime dependency on the driver here
    from drydocs_core.neo4j_client import Neo4jClient

#: Cypher clauses that write. Word-boundary, case-insensitive; queries here are
#: engine-authored, so a keyword scan is a sound guard (no user free-text).
_WRITE_CLAUSE = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|FOREACH)\b",
    re.IGNORECASE,
)


class GraphWriteAttemptError(RuntimeError):
    """A write clause reached the read-only corroboration boundary."""


class ReadOnlyGraph:
    """The component's sole graph access path — read queries only."""

    def __init__(self, client: "Neo4jClient") -> None:
        self._client = client

    def fetch(self, query: str, params: dict[str, Any] | None = None) -> list[Any]:
        clause = _WRITE_CLAUSE.search(query)
        if clause:
            raise GraphWriteAttemptError(
                f"write clause {clause.group(0)!r} in a corroboration query — "
                "this component never writes the graph (NFR-REM-1)"
            )
        return self._client.run(query, params)


def _as_map(defs: VariableDefs) -> dict[str, str | None]:
    return {(n[2:] if n.startswith("%%") else n): v for n, v in defs}


@dataclass
class CorroborationReport:
    """Outcome of reconciling definitions against a corroborating source."""

    consistent: bool
    checked_jobs: int = 0
    mismatches: list[str] = field(default_factory=list)


def reconcile_variables(
    definitions: DefinitionSet, extract: Mapping[str, VariableDefs]
) -> CorroborationReport:
    """Reconcile each job's variable definitions against ``extract`` (rows from the
    ``psgmgr`` staging extract or a graph fetch), keyed by job name. Name/value
    comparison; ordering differences are not mismatches."""
    mismatches: list[str] = []
    checked = 0
    for job in definitions.jobs:
        checked += 1
        source = extract.get(job.name)
        if source is None:
            mismatches.append(f"{job.name}: absent from the corroborating source")
            continue
        ours, theirs = _as_map(job.variables), _as_map(source)
        for name in sorted(set(ours) | set(theirs)):
            if name not in theirs:
                mismatches.append(f"{job.name}:{name}: only in the definition")
            elif name not in ours:
                mismatches.append(f"{job.name}:{name}: only in the corroborating source")
            elif ours[name] != theirs[name]:
                mismatches.append(
                    f"{job.name}:{name}: definition {ours[name]!r} != source {theirs[name]!r}"
                )
    return CorroborationReport(
        consistent=not mismatches, checked_jobs=checked, mismatches=mismatches
    )
