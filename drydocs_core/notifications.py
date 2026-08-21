"""Neo4j notifications as a plain, serialisable payload (R21, 2026-08-21).

WHY A CORE MODULE. A Neo4j query can succeed AND carry notifications — the
driver's non-fatal diagnostics: an unknown label, an unknown relationship type,
a missing property, a cartesian product. On 2026-08-20 a question that
escalated to schema-grounded Cypher produced FOUR such warnings (the graph had
never loaded the labels the query named) and the console showed a clean empty
answer: the API runner discarded the summary, the agent's read helper returned
rows only, and the :AgentRun record had no field for them. Three drops, one
shape — so the shape lives once, here, and every runner converts to it.

WHAT IT IS NOT. A notification is Neo4j's own statement about the query. It is
not a model prompt, not chain-of-thought, not an error: a non-fatal warning
never turns an answer into a failure. It sits on the safe side of the console's
exposure line (router decision, generated Cypher, rows, timings, source), and
this payload carries exactly the fields an admin needs to diagnose — code,
title, severity, position, description — nothing free-text from the caller.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Neo4jNotification:
    code: str
    title: str
    severity: str = ""
    description: str = ""
    #: ``"line:column"`` when the driver supplied a position, else ``""``
    position: str = ""
    category: str = ""

    def as_json(self) -> str:
        """One homogeneous string per notification — the form a Neo4j list
        property can hold (:AgentRun.warnings)."""
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> Neo4jNotification:
        return cls(**json.loads(text))


def _position(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, Mapping):
        line, col = raw.get("line"), raw.get("column")
    else:
        line, col = getattr(raw, "line", None), getattr(raw, "column", None)
    if line is None and col is None:
        return ""
    return f"{line}:{col}"


def from_summary(summary: Any) -> list[Neo4jNotification]:
    """Normalise a driver ``ResultSummary`` (or anything with a ``notifications``
    list of dicts, the neo4j 5.x shape) into :class:`Neo4jNotification` rows. Never
    raises: a summary without notifications yields ``[]``, and an empty list is
    the honest record of a clean run — not a missing field."""
    raw: Iterable[Any] = getattr(summary, "notifications", None) or []
    out: list[Neo4jNotification] = []
    for item in raw:
        get = item.get if isinstance(item, Mapping) else (lambda k, _i=item: getattr(_i, k, None))
        out.append(
            Neo4jNotification(
                code=str(get("code") or ""),
                title=str(get("title") or ""),
                severity=str(get("severity") or get("severity_level") or ""),
                description=str(get("description") or ""),
                position=_position(get("position")),
                category=str(get("category") or ""),
            )
        )
    return out


def to_payload(notifications: Iterable[Neo4jNotification]) -> list[dict[str, Any]]:
    return [asdict(n) for n in notifications]
