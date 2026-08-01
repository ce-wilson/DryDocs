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

It also carries the O27 rule-3 guard (``ensure_no_element_ids``): Cypher whose
results reach an external surface may not return a graph-internal element id.
Same shape as the write guard — refuse at the door, on code regions only — and
it lives here rather than in ``query_specs`` so BOTH spec paths (the reviewed
registry and the LLM-authored ephemeral registrations) call one implementation.
See ``drydocs_api/AUTHORING.md``.
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


# O27 rule 3. Matched on the comment/string-stripped, LOWERCASED copy, so the
# case-insensitivity of Cypher function names (`ElementId(` == `elementId(`)
# and the `RETURN 'id('` false-positive are both handled by _code_regions.
# The word boundary is what spares the legitimate source-system ids: `j.job_id`
# and `f.folder_id` have a word character before `id`, so they never match,
# while `id(`, `.id(` and `elementid(` do.
_ELEMENT_ID_RE = re.compile(r"\b(?:element)?id\s*\(")


class WriteRejected(ValueError):
    """Raised when a query contains a write clause — the caller gets a 4xx, never the driver."""


class ElementIdRejected(ValueError):
    """Raised when a query returns a graph-internal element id (O27 rule 3)."""


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


def returns_element_id(cypher: str) -> str | None:
    """Return the offending call if ``cypher`` yields a graph-internal element
    id, else None."""
    match = _ELEMENT_ID_RE.search(_code_regions(cypher))
    return match.group(0) if match else None


def ensure_no_element_ids(cypher: str, context: str) -> None:
    """Raise :class:`ElementIdRejected` for Cypher returning an element id.

    Element ids are Neo4j-internal pointers, not stable identifiers: they change
    on restore-from-backup, on re-load into a fresh database, and across store
    migrations. A deep link or export manifest built on one does not break
    loudly — it later resolves to a DIFFERENT node, which is worse. Applied to
    the permanent registry at import AND to ephemeral (agent-authored)
    registrations, which is where the real exposure is.
    """
    call = returns_element_id(cypher)
    if call is not None:
        raise ElementIdRejected(
            f"{context}: returns a graph-internal element id via '{call}' — element ids "
            "are unstable across restore/re-load and must never reach a URL, export or "
            "provenance manifest. Return the node's declared key instead "
            "(see drydocs_api/AUTHORING.md rule 3)."
        )
