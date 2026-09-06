"""R15 — epistemic labeling on query answers: EXACT or LOWER-BOUND, with causes.

A lineage or impact answer is a walk over edges, and the walk can only see
edges that exist. In DryDocs three things keep an edge from existing without
anything in the row set saying so: a job whose ``cmd_line`` the extractor
could not parse (no INVOKES / USES_ARTIFACT / READS_FROM / WRITES_TO left
that job at all), an invocation that resolved to nothing recognizable (the
INVOKES target is a ProcessNode of ``kind = 'unknown'``), and a relationship
type the vocabulary registers as PLANNED with no loader behind it yet. Each
of those is a hop the answer does not contain and cannot mention. The
GitNexus comparison (docs/reviews/gitnexus-depgraph-comparison.md) is the
cautionary case: a tool that reports impact from a dependency graph it knows
to be partial, as if the graph were whole. The defect is not the partial
graph — every extractor has one — it is presenting the result as complete.

So the label is a property of the ANSWER, never of the graph: nothing here
adds a node, a property or an edge, and nothing here needs a gate. A spec
DECLARES what its walk can fail to see (:class:`WalkDeclaration`), and
:func:`grade` turns that declaration into a verdict at run time — ``exact``
when every declared cause measures zero, ``lower-bound`` otherwise, with the
causes that fired named machine-readably beside it. A spec that declares no
walk (an inventory list, a schema dump, an agent's ephemeral registration) is
UNGRADED and answers ``None``: the honest default for "nobody has said what
this walk can miss" is silence, not ``exact``.

The doctrine this puts into the contract: zero rows with ``lower-bound`` is a
different answer from zero rows with ``exact``. The first says "nothing found,
and here is why the walk could not have found it"; the second says "there is
nothing". A consumer that renders ``rows.length === 0`` as "no lineage" has
collapsed the two, which is the GitNexus failure in a different coat.

This module is framework-free on purpose: the agents import it by sys.path
(``agents/common/specs_catalog.py``) the same way they import the registry,
so it may not pull FastAPI or the driver in behind it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol

EXACT = "exact"
LOWER_BOUND = "lower-bound"
EPISTEMIC_VALUES: frozenset[str] = frozenset({EXACT, LOWER_BOUND})

#: A job with a command line the extractor left unparsed: no INVOKES,
#: USES_ARTIFACT, READS_FROM or WRITES_TO leaves it, so every hop that command
#: would have contributed is missing (the extractor's ``commands_unparsed``
#: counter, controlm_inventory.py).
CAUSE_UNPARSED_CMD_LINE = "unparsed-cmd-line"
#: An INVOKES edge whose target ProcessNode has ``kind = 'unknown'``: the job
#: invokes SOMETHING, and the walk has no idea what it reads or writes.
CAUSE_UNRESOLVED_INVOCATION = "unresolved-invocation"
#: A relationship type the vocabulary registers as ``status: planned`` and no
#: loader writes yet — a whole class of hop the graph cannot carry until its
#: gate flips. Keyed by vocabulary ENTRY id, never by Neo4j label: INVOKES is
#: both the active ``scheduler_invokes`` and the planned
#: ``scheduler_invokes_utility``, and the label alone cannot tell them apart.
CAUSE_GATE_PENDING_EDGE = "gate-pending-edge"

CAUSE_CLASSES: frozenset[str] = frozenset(
    {CAUSE_UNPARSED_CMD_LINE, CAUSE_UNRESOLVED_INVOCATION, CAUSE_GATE_PENDING_EDGE}
)

#: The run-time probes, one read-only count per measurable cause class. Each
#: returns a single row with one integer column ``n``. They read the ground
#: truth realm only — the :SchemaMeta exemplars (C8) and the :Uncertain realm
#: (ADR 0011) are excluded by hand here because these strings never pass
#: through the registry's ``_with_ground_truth_exclusion`` rewrite.
CAUSE_PROBES: Mapping[str, str] = {
    CAUSE_UNPARSED_CMD_LINE: (
        "MATCH (j:ControlMJob) "
        "WHERE NOT j:SchemaMeta AND NOT j:Uncertain "
        "AND j.cmd_line IS NOT NULL AND trim(j.cmd_line) <> '' "
        "AND NOT (j)-[:INVOKES|USES_ARTIFACT|READS_FROM|WRITES_TO]->() "
        "RETURN count(j) AS n"
    ),
    CAUSE_UNRESOLVED_INVOCATION: (
        "MATCH (j:ControlMJob)-[:INVOKES]->(p:ProcessNode) "
        "WHERE NOT j:SchemaMeta AND NOT j:Uncertain "
        "AND NOT p:SchemaMeta AND NOT p:Uncertain "
        "AND p.kind = 'unknown' "
        "RETURN count(DISTINCT p) AS n"
    ),
}


@dataclass(frozen=True)
class WalkDeclaration:
    """What a spec's walk can fail to see — declared on the spec, graded per run.

    ``probes`` names the run-time cause classes to measure (keys of
    :data:`CAUSE_PROBES`); ``gate_pending`` names vocabulary ENTRY ids that are
    ``status: planned`` and whose edges this walk would traverse if they
    existed. The static guard in tests/unit/test_epistemics.py fails when a
    listed entry is no longer planned-only — the list must SHRINK when the
    loader lands, exactly as ``planned_terms`` (R20) must.
    """

    probes: tuple[str, ...] = ()
    gate_pending: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        unknown = sorted(set(self.probes) - set(CAUSE_PROBES))
        if unknown:
            raise ValueError(f"unknown epistemic probe class(es): {unknown}")


#: The walk every READS_FROM / WRITES_TO lineage spec shares: both measurable
#: causes, plus the two planned scheduler edges that would carry data hops the
#: current graph cannot — a job waiting on a delivered file
#: (``scheduler_depends_on_file``, USED) and a job invoking a Control-M utility
#: (``scheduler_invokes_utility``, INVOKES). Named once so the two specs cannot
#: declare different blind spots for the same edges.
LINEAGE_WALK = WalkDeclaration(
    probes=(CAUSE_UNPARSED_CMD_LINE, CAUSE_UNRESOLVED_INVOCATION),
    gate_pending=("scheduler_depends_on_file", "scheduler_invokes_utility"),
)


class _Declares(Protocol):
    database: str
    walk: WalkDeclaration | None


#: ``run(cypher, params, database) -> rows`` — the shape both callers adapt to
#: in one line: the API's GraphRunner returns ``(keys, rows)`` and the agent's
#: ``run_read`` returns a ReadResult with ``.records``.
RunRows = Callable[[str, Mapping[str, object], str], Iterable[Mapping[str, object]]]


def _count(rows: Iterable[Mapping[str, object]]) -> int | None:
    """The probe's ``n``, or None when the runner gave back nothing usable.

    None is a MEASUREMENT FAILURE and grades as a cause, not as zero: a probe
    that could not run cannot rule its cause out, and "could not measure"
    presented as "measured zero" is the instrument failing INTO clean (J76).
    """
    for row in rows:
        value = row.get("n") if isinstance(row, Mapping) else None
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        return None
    return None


def grade(spec: _Declares, run: RunRows) -> tuple[str | None, list[dict[str, object]]]:
    """Grade one run of ``spec``: ``(epistemic, causes)``.

    ``epistemic`` is ``None`` for a spec with no walk declaration (ungraded),
    ``"exact"`` when every declared cause measures zero, ``"lower-bound"``
    otherwise. ``causes`` lists what fired, each as
    ``{"cause": <class>, "detail": <what>, "count": <int | None>}`` —
    ``count`` is the probe's measurement (None when it could not be taken), and
    ``detail`` is the vocabulary entry id for a gate-pending cause or the probe
    class for a measured one. A cause that measures zero is DROPPED: the list
    names what limited THIS answer, not everything the walk could in principle
    miss. Ordering is stable — probes in declaration order, then gate-pending
    entries in declaration order — so two runs against the same graph grade
    identically and a test can compare lists.
    """
    walk = spec.walk
    if walk is None:
        return None, []
    causes: list[dict[str, object]] = []
    for cls in walk.probes:
        n = _count(run(CAUSE_PROBES[cls], {}, spec.database))
        if n is None:
            causes.append(
                {"cause": cls, "detail": f"{cls}: probe returned no count", "count": None}
            )
        elif n > 0:
            causes.append({"cause": cls, "detail": cls, "count": n})
    for entry_id in walk.gate_pending:
        causes.append({"cause": CAUSE_GATE_PENDING_EDGE, "detail": entry_id, "count": None})
    return (LOWER_BOUND if causes else EXACT), causes
