"""A result names what it did not check (ADR 0021, ACCEPTED 2026-09-09).

The module sweep's first cycle found ONE defect shape seven times - a result that
cannot tell *checked and clean* from *not checked* - and the correct answer
implemented six times over with no shared convention. This is the convention made
into a type, so the wrong version fails to type-check or fails the guard rather
than failing in a review two months later.

Three states, and only three (D1):

* ``CHECKED_CLEAN`` - the probe ran over its whole subject and found nothing. It
  carries the subject's ``size`` where one exists, so "clean over 0" is visible.
* ``FINDINGS`` - the probe ran and found something; the findings travel with it,
  and so does the size, because a findings list with no denominator hides itself.
* ``NOT_CHECKED`` - the probe did not run, or ran over less than its subject. It
  carries a written reason of at least :data:`REASON_MIN` characters, never empty
  (the SOURCELESS_LOADERS idiom applied to a result).

Two properties belong to the type and not to its callers. A :class:`CheckOutcome`
NEVER coerces to a boolean - ``bool(outcome)`` raises, so ``if outcome:`` cannot be
written and the only way to ask "is it clean" is :attr:`CheckOutcome.is_clean`,
true for ``CHECKED_CLEAN`` and false for BOTH other states. And every state
renders itself (:meth:`CheckOutcome.render`) as the operator line, so a surface
cannot show a not-checked result as ``0``, as an empty list, or as PASS (D5).

A PROBE is any function whose answer depends on something it had to go and look
at - a subprocess, a graph query, a tree scan, a network call. A probe returns
this type (D2). The probes that have adopted it are DECLARED in :data:`PROBES`,
and ``tests/unit/test_check_outcome.py`` imports each one and reads its return
annotation (D3): the registry is shrink-only in one direction - a name that no
longer resolves fails the guard - and it finds nothing that nobody registered,
exactly as an undeclared component import is invisible to the boundary test.

Pure data. Imports nothing but the stdlib - this is core, and core imports
nothing (drydocs_core/component_map.py).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

#: A NOT_CHECKED result carries a reason at least this long. Forty characters is
#: the length at which "skipped" has to become "skipped because ...", which is the
#: whole point: a bare skip is a fact with no owner, a reasoned one is a decision.
REASON_MIN = 40


class Outcome(str, Enum):
    """The three states. A fourth is the revisit trigger, not an addition (ADR 0021)."""

    CHECKED_CLEAN = "checked-clean"
    FINDINGS = "findings"
    NOT_CHECKED = "not-checked"


@dataclass(frozen=True)
class CheckOutcome:
    """One probe's answer. Build it through :func:`checked_clean`,
    :func:`findings` or :func:`not_checked`; the constructor validates the
    state's own invariants so a malformed answer fails where it is made."""

    state: Outcome
    #: What the probe found - empty except in FINDINGS, where it is never empty.
    findings: tuple = ()
    #: The size of the subject scanned (rows, files, commits), where one exists.
    size: int | None = None
    #: A short operator-facing description of the subject ("commit 0d3761a9",
    #: "1,204 rows of :Document"); rendered beside the state.
    subject: str | None = None
    #: NOT_CHECKED only: why the probe did not run, or ran over less than its subject.
    reason: str | None = None
    #: The J18 stamp, where the answer depends on the machine that produced it.
    venue: str | None = None

    def __post_init__(self) -> None:
        if self.state is Outcome.NOT_CHECKED:
            if not isinstance(self.reason, str) or len(self.reason.strip()) < REASON_MIN:
                raise ValueError(
                    f"a NOT_CHECKED outcome needs a reason of at least {REASON_MIN} "
                    f"characters - got {self.reason!r}"
                )
            if self.findings:
                raise ValueError("a NOT_CHECKED outcome carries no findings - it did not look")
        elif self.state is Outcome.FINDINGS:
            if not self.findings:
                raise ValueError(
                    "a FINDINGS outcome with nothing in it is CHECKED_CLEAN - say so; an empty "
                    "findings list is the seventh spelling of not-checked (ADR 0021 D2)"
                )
        elif self.state is Outcome.CHECKED_CLEAN:
            if self.findings:
                raise ValueError("a CHECKED_CLEAN outcome cannot carry findings")
        else:  # pragma: no cover - the enum is closed
            raise ValueError(f"unknown outcome state {self.state!r}")
        if self.size is not None and self.size < 0:
            raise ValueError(f"size cannot be negative: {self.size}")

    def __bool__(self) -> bool:
        """Refused, by design: ``if outcome:`` would read NOT_CHECKED as either
        clean or failed, and both are wrong. Ask :attr:`is_clean` or
        :attr:`is_not_checked` by name."""
        raise TypeError(
            "a CheckOutcome has three states and does not coerce to a boolean - "
            "ask outcome.is_clean (true only for CHECKED_CLEAN) or "
            "outcome.is_not_checked by name (ADR 0021 D1)"
        )

    @property
    def is_clean(self) -> bool:
        """True ONLY for CHECKED_CLEAN. FINDINGS and NOT_CHECKED are both false."""
        return self.state is Outcome.CHECKED_CLEAN

    @property
    def is_not_checked(self) -> bool:
        return self.state is Outcome.NOT_CHECKED

    @property
    def count(self) -> int:
        return len(self.findings)

    def render(self) -> str:
        """The operator line: one per state, never a number standing in for a state.

        ``checked, clean (1,204 rows)`` / ``3 findings over 45 rules`` /
        ``NOT CHECKED - <reason>``. The venue rides at the end when set.
        """
        if self.state is Outcome.NOT_CHECKED:
            line = f"NOT CHECKED - {self.reason.strip()}"  # type: ignore[union-attr]
        elif self.state is Outcome.FINDINGS:
            n = self.count
            line = f"{n} finding{'s' if n != 1 else ''}"
            if self.subject:
                line += f" over {self.subject}"
            elif self.size is not None:
                line += f" over {self.size:,} scanned"
        else:
            line = "checked, clean"
            if self.subject:
                line += f" ({self.subject})"
            elif self.size is not None:
                line += f" ({self.size:,} scanned)"
        if self.venue:
            line += f" [venue: {self.venue}]"
        return line


def checked_clean(
    *, size: int | None = None, subject: str | None = None, venue: str | None = None
) -> CheckOutcome:
    """The probe ran over its whole subject and found nothing."""
    return CheckOutcome(Outcome.CHECKED_CLEAN, size=size, subject=subject, venue=venue)


def findings(
    items: Iterable,
    *,
    size: int | None = None,
    subject: str | None = None,
    venue: str | None = None,
) -> CheckOutcome:
    """The probe ran and found ``items`` (never empty - that is :func:`checked_clean`)."""
    return CheckOutcome(
        Outcome.FINDINGS, findings=tuple(items), size=size, subject=subject, venue=venue
    )


def not_checked(reason: str, *, venue: str | None = None) -> CheckOutcome:
    """The probe did not run, or ran over less than its subject - with the reason."""
    return CheckOutcome(Outcome.NOT_CHECKED, reason=reason, venue=venue)


#: THE DECLARED PROBE REGISTRY (ADR 0021 D3). Dotted names, one per probe that
#: returns :class:`CheckOutcome`; the item that makes a function a probe adds its
#: line here. Declared, never inferred - a name heuristic (``check_*``) is the
#: guard-reads-prose class the sweep measured, and it would have missed ``_git``.
#: ``tests/unit/test_check_outcome.py`` imports each name (a name that no longer
#: resolves fails - shrink-only) and reads its return annotation through
#: ``tests/source_scan.py`` (J66): the annotation must be this type.
PROBES: tuple[str, ...] = (
    # CORE10, the first adopters (ADR 0021 D4, in order):
    "drydocs.port.port_preflight.base_resolves",  # is the base a commit git can see here
    "drydocs.docs_coverage.graph_probe",  # layer 2 of the coverage report
    # CORE14 (2026-09-10): the sweep's recurrence in core's own driver. Four
    # worlds - APOC absent, server unreachable, auth wrong, and an unexpected
    # fifth - all returned the same False, so `drydocs bootstrap` said "APOC
    # required" to people whose database was simply stopped.
    "drydocs_core.neo4j_client.Neo4jClient.apoc_available",
)
