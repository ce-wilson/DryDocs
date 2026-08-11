"""Classify a Control-M Quantitative Resource pool name into a category.

A ``<QUANTITATIVE NAME="..." QUANT="n">`` element on a ``<JOB>`` declares that
the job consumes *n* slots from a named pool. Pool names follow a loose
positional convention::

    <APP_CODE>-<SUBSYSTEM>[-<MODIFIER>]*-<KIND>

This module parses that into a :class:`PoolClassification` with **no I/O**.

Why it is worth having before anything loads it
-----------------------------------------------
A pool names the **target platform independently of the job name**, so the two
cross-check: a job whose name says one platform and whose pool says another is
a finding neither source could raise alone. That is the standing use, and it
does not need the graph edge to exist first.

Mechanism here, vocabulary elsewhere
-------------------------------------
The pool vocabulary is estate data — the real category tokens and the real
app-code prefix are Internal and are **not** in this repo. What lives here is
the grammar, the classification contract, and an ordered rule table supplied by
the caller. :data:`DEFAULT_RULES` is empty, so an un-configured deployment
classifies everything ``unknown`` — the honest answer for a repo that does not
hold the vocabulary, and one that shows up as WARN volume rather than as
confident mislabelling.

**Rule order is correctness, not style.** Rules are first-match-wins and a real
table contains at least one broad rule that matches its token anywhere in the
name; it must be evaluated after the narrower ones or it steals their pools.
That is why :class:`PoolRule` tables are an ordered *sequence*. A mapping keyed
by category would drop the ordering, and the loss would be invisible until a
misclassified pool reached the graph.

Source: ``internal/controlm-config/reference/controlm-xml-processor-capture.md``
Part F, which carries the company implementation verbatim and F1's rationale.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

PoolCategory = Literal[
    "target_database",
    "etl_platform",
    "source_platform",
    "host_node",
    "business_app",
    "unknown",
]

#: Secondary Neo4j label per category. ``unknown`` adds no secondary label.
#:
#: NOTE: these names are the *proposed* label vocabulary, not a ratified one.
#: Nothing in this module writes a graph, and minting these labels on a node is
#: an ontology decision that goes through the HITL gate — see
#: docs/RELATIONSHIP_GUIDE.md. Carried here so a caller has one place to read
#: the intended mapping, never as authority to apply it.
CATEGORY_LABEL: dict[PoolCategory, str | None] = {
    "target_database": "TargetDatabase",
    "etl_platform": "EtlPlatform",
    "source_platform": "SourcePlatform",
    "host_node": "HostNode",
    "business_app": "BusinessApplication",
    "unknown": None,
}


@dataclass(frozen=True)
class PoolRule:
    """One ordered match rule: a category and the pattern that selects it."""

    category: PoolCategory
    pattern: re.Pattern[str]


#: The producer default is EMPTY on purpose. The real table is estate
#: vocabulary and is supplied by the caller (its values twin lives under
#: ``internal/``). Empty means every pool classifies ``unknown``, which is
#: accurate here rather than merely safe.
DEFAULT_RULES: tuple[PoolRule, ...] = ()

#: The app-code prefix shape. The real prefix is estate data, so the default
#: matches nothing and ``app_code`` stays ``None`` until a caller supplies one.
DEFAULT_APP_CODE_RE: re.Pattern[str] | None = None


@dataclass(frozen=True)
class PoolClassification:
    """Structured view of a parsed Quantitative Resource pool name."""

    name: str
    category: PoolCategory
    app_code: str | None  # parsed head token, when it matches the app-code shape
    subsystem: str | None  # second positional token
    kind_suffix: str | None  # terminal positional token
    secondary_label: str | None  # proposed label for the category (see above)


__all__ = [
    "PoolCategory",
    "PoolRule",
    "PoolClassification",
    "CATEGORY_LABEL",
    "DEFAULT_RULES",
    "DEFAULT_APP_CODE_RE",
    "classify",
]

_UNCLASSIFIED = PoolClassification(
    name="",
    category="unknown",
    app_code=None,
    subsystem=None,
    kind_suffix=None,
    secondary_label=None,
)


def classify(
    pool_name: str | None,
    rules: tuple[PoolRule, ...] = DEFAULT_RULES,
    app_code_re: re.Pattern[str] | None = DEFAULT_APP_CODE_RE,
) -> PoolClassification:
    """Classify a pool name. **Always returns** — never raises.

    An unrecognized name lands in ``unknown`` with no secondary label; the
    caller logs a WARN for those so misses surface in CI rather than becoming
    a silently absent edge. That is the aliases-suggest / values-decide
    discipline the FACT_REGISTRY next door already follows: a name we do not
    know is reported, not guessed at.
    """
    raw = (pool_name or "").strip()
    if not raw:
        return _UNCLASSIFIED

    tokens = raw.split("-")
    app_match = app_code_re.match(raw) if app_code_re else None
    app_code = app_match.group(1) if app_match else None

    # Positional tokens. A two-token name makes these the SAME token, and that
    # is intended rather than inherited: with <APP>-<KIND> there genuinely is
    # one token playing both the second-position and terminal roles, and
    # blanking one of them would lose information the name carries. Callers
    # comparing the two fields must expect equality on short names.
    subsystem = tokens[1] if len(tokens) >= 2 else None
    kind_suffix = tokens[-1] if len(tokens) >= 2 else None

    category: PoolCategory = "unknown"
    for rule in rules:  # ORDERED: first match wins — see the module docstring
        if rule.pattern.search(raw):
            category = rule.category
            break

    # `business_app` fallback: a pure <APP_CODE>-<SUBSYSTEM> name with no
    # recognized suffix. NEVER OBSERVED in the captured estate — the company
    # original says so outright and reserves the slot to complete the contract.
    # Kept WITH that caveat: dropping the comment would ship a never-seen
    # category as though it were evidence.
    if category == "unknown" and app_code and len(tokens) == 2:
        category = "business_app"

    return PoolClassification(
        name=raw,
        category=category,
        app_code=app_code,
        subsystem=subsystem,
        kind_suffix=kind_suffix,
        secondary_label=CATEGORY_LABEL[category],
    )
