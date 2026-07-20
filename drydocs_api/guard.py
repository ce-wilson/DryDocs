"""Read-only Cypher guard — the endpoint-layer half of NFR "no interactive writes".

Generalizes the ``agents/common/neo4j_tool.py`` write-token precedent (graph
writes go through the DryDocs loaders + HITL gate, never through an
interactive surface). Two layers of defense:

1. THIS guard fails fast on write-shaped Cypher before anything reaches a
   driver — comments and string literals are stripped first so ``'set'``
   inside emitted data never false-positives (the ADR 0003 bind-renderer
   lesson: scan code regions only).
2. The live runner additionally pins ``RoutingControl.READ``, so even a guard
   miss cannot reach a write-capable connection.
"""

from __future__ import annotations

import re

# Cypher clauses that mutate the graph or schema. Word-boundary matched on a
# comment/string-stripped, lowercased copy of the query.
WRITE_CLAUSES: frozenset[str] = frozenset(
    {
        "create",
        "merge",
        "delete",
        "detach",
        "set",
        "remove",
        "drop",
        "foreach",
    }
)
# Multi-word forms that need phrase matching.
WRITE_PHRASES: tuple[str, ...] = ("load csv",)

_STRIP_PATTERNS = (
    re.compile(r"/\*.*?\*/", re.DOTALL),  # /* block comments */
    re.compile(r"//[^\n]*"),  # // line comments
    re.compile(r"'(?:[^'\\]|\\.)*'"),  # 'string literals'
    re.compile(r'"(?:[^"\\]|\\.)*"'),  # "quoted identifiers/strings"
)


class WriteRejected(ValueError):
    """Raised when a query contains a write clause — the caller gets a 4xx, never the driver."""


def _code_regions(cypher: str) -> str:
    text = cypher
    for pattern in _STRIP_PATTERNS:
        text = pattern.sub(" ", text)
    return text.lower()


def is_write_cypher(cypher: str) -> str | None:
    """Return the offending clause if ``cypher`` is write-shaped, else None."""
    code = _code_regions(cypher)
    for phrase in WRITE_PHRASES:
        if phrase in code:
            return phrase
    for token in re.findall(r"[a-z_]+", code):
        if token in WRITE_CLAUSES:
            return token
    return None


def ensure_read_only(cypher: str) -> None:
    """Raise :class:`WriteRejected` for write-shaped Cypher; no-op for reads."""
    clause = is_write_cypher(cypher)
    if clause is not None:
        raise WriteRejected(
            f"write clause '{clause}' rejected: graph writes go through the DryDocs "
            "loaders + HITL gate, never through the API (ADR 0005 / the loaders-only rule)"
        )
