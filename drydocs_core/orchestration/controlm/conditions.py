"""Condition-name scope: which data centers a Control-M condition resolves in.

A job's ``INCOND`` / ``OUTCOND`` names carry their own scope in a prefix. Per
the production support convention only two occur::

    PL-...    LOCAL   — resolves within the emitting folder's DATACENTER
    PG-...    GLOBAL  — resolves across data centers, by name alone

**The consequence is the reason this module exists.** Two LOCAL conditions
that share a name in different data centers are *different conditions*. So a
key derived from a condition name is incomplete without the data center, and
building one without it silently merges two unrelated dependencies into one
node — a wrong edge, not a missing one, which is the failure class that does
not announce itself.

:func:`condition_identity` exists so that rule is executable rather than
prose a caller has to remember.

An unrecognized prefix returns ``UNKNOWN`` rather than raising: a condition
name we do not recognize is a fact about the estate to report, not an error
that should stop a load. ``UNKNOWN`` is treated as data-center-scoped for
identity, because assuming the safer-looking global scope is what would merge
two distinct conditions.

Source: ``internal/controlm-config/reference/controlm-xml-processor-capture.md``
Part D. The two prefixes are a documented naming convention, not estate data.
"""

from __future__ import annotations

from typing import Literal

ConditionScope = Literal["LOCAL", "GLOBAL", "UNKNOWN"]

#: prefix -> scope. Ordered longest-first is unnecessary here (both are 3
#: chars and mutually exclusive), but the table is the extension point: a new
#: prefix is a data change, not a code change.
SCOPE_PREFIXES: dict[str, ConditionScope] = {
    "PL-": "LOCAL",
    "PG-": "GLOBAL",
}

__all__ = [
    "ConditionScope",
    "SCOPE_PREFIXES",
    "condition_scope",
    "condition_identity",
]


def condition_scope(name: str | None) -> ConditionScope:
    """Classify a condition name's scope from its prefix. Always returns."""
    if not name:
        return "UNKNOWN"
    stripped = name.strip()
    for prefix, scope in SCOPE_PREFIXES.items():
        if stripped.startswith(prefix):
            return scope
    return "UNKNOWN"


def condition_identity(name: str, data_center: str | None) -> tuple[str, str]:
    """The ``(name, qualifier)`` pair that uniquely identifies a condition.

    GLOBAL conditions resolve by name alone, so their qualifier is empty and
    the same name in two data centers is ONE condition. LOCAL and UNKNOWN
    conditions are qualified by the data center, so the same name in two data
    centers is TWO conditions.

    Use this to build a MERGE key. Keying on the name alone collapses distinct
    LOCAL conditions together and invents a dependency that does not exist.
    """
    scope = condition_scope(name)
    key = (name or "").strip()
    if scope == "GLOBAL":
        return (key, "")
    return (key, (data_center or "").strip())
