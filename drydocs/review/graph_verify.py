"""Data-driven Cypher acceptance runner (``drydocs-review`` component).

Loads YAML ``TC-*`` suites from ``graph-tests/``, runs each case's Cypher against a
live graph, and asserts the result shape (``empty`` / ``nonempty`` / ``equals``).
A suite fails (non-zero exit) if any case fails.

REV2 (2026-09-10) — THE ANCHOR. Most cases here assert ``empty``: "no orphan jobs",
"no folder without attribution". On an EMPTY graph every one of them passes, because
zero rows is what they want to see — so the suite reported PASS over a database that
had never been loaded. The 2026-09-08 review measured it: 28 of 30 negative
assertions had nothing establishing that the graph could have produced a row at all.

A suite therefore declares an ``anchor``: a positive control that must find data
before any negative assertion means anything. :func:`run_suite` evaluates it FIRST
and, when it fails, reports NOT RUN — never PASS, and the cases are not run, because
their answers would be about an absent graph rather than about the invariants. The
verdict is :class:`drydocs_core.check_outcome.CheckOutcome` (ADR 0021), whose three
states are exactly what this distinction needs and which cannot be coerced to a bool.

A suite with NO anchor is also NOT RUN, with that as its reason. Default-deny: the
mechanism is worth nothing if a suite can opt out of it by omission, which is how
the four unanchored suites came to be unanchored.

The **loader** (``load_suite`` / ``load_suites``) and the **evaluator** (``evaluate``)
are pure and offline — unit-testable with no Neo4j. Only ``run_case`` / ``run_suite``
touch the graph, via any object exposing ``run(cypher, params) -> list[dict]`` (the
:class:`drydocs.neo4j_client.Neo4jClient` interface). The graph is only READ — this
component writes no meaning edges, so it needs no HITL gate to run.

classification: Internal-Public — the committed example suite is a vendor-BMC smoke
test. Real acceptance suites (internal counts/IDs) live in a gitignored twin.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import yaml

from drydocs_core.check_outcome import CheckOutcome, checked_clean, findings, not_checked
from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)
DEFAULT_GRAPH_TESTS_DIR = _REPO_ROOT / "graph-tests"


class GraphVerifyError(RuntimeError):
    """A suite file is malformed or declares an unknown assertion."""


class Assertion(str, Enum):
    EMPTY = "empty"
    NONEMPTY = "nonempty"
    EQUALS = "equals"


@dataclass(frozen=True)
class Case:
    id: str
    cypher: str
    assertion: Assertion
    description: str = ""
    expected: Any = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Anchor:
    """A suite's positive control: proof the graph could answer at all (REV2).

    Two declaration forms, because the suites need both:

    * ``label:`` + ``min_count:`` — "there are at least N :ControlMFolder". The
      common case, and the safer one to write: the Cypher is generated, so a
      suite author cannot accidentally write an anchor that asserts nothing.
    * ``cypher:`` + ``min_rows:`` — an arbitrary read for an anchor a label
      count cannot express (a relationship, a property being populated).

    ``min_count``/``min_rows`` default to 1 and must be >= 1: an anchor of zero
    is not an anchor, it is the thing this mechanism exists to prevent.
    """

    cypher: str
    min_rows: int = 1
    description: str = ""
    label: str | None = None


@dataclass(frozen=True)
class Suite:
    name: str
    cases: tuple[Case, ...]
    description: str = ""
    targets: tuple[str, ...] = ()
    path: Path | None = None
    #: REV2. ``None`` means the suite declares no positive control, which
    #: :func:`run_suite` reports as NOT RUN rather than running it anyway.
    anchor: Anchor | None = None


@dataclass(frozen=True)
class SuiteResult:
    """One suite's answer: the verdict, and the detail behind it.

    ``outcome`` is the three-state verdict (ADR 0021). ``results`` is empty when
    the anchor failed or was absent — the cases were not run, deliberately, so
    nothing downstream can mistake an unrun case for a passing one.
    """

    suite: Suite
    outcome: CheckOutcome
    results: tuple[CaseResult, ...] = ()
    anchor_rows: int | None = None


@dataclass(frozen=True)
class CaseResult:
    case: Case
    passed: bool
    rows: list[dict[str, Any]]
    detail: str = ""


# ---------------------------------------------------------------------------
# Loading (pure / offline)
# ---------------------------------------------------------------------------
def _parse_case(raw: dict[str, Any]) -> Case:
    cid = raw.get("id")
    if not cid:
        raise GraphVerifyError(f"case missing `id`: {raw!r}")
    cypher = raw.get("cypher")
    if not cypher:
        raise GraphVerifyError(f"[{cid}] missing `cypher`")
    raw_assert = raw.get("assert")
    try:
        assertion = Assertion(raw_assert)
    except ValueError as exc:
        raise GraphVerifyError(
            f"[{cid}] unknown assert '{raw_assert}'; expected one of "
            f"{[a.value for a in Assertion]}"
        ) from exc
    if assertion is Assertion.EQUALS and "expected" not in raw:
        raise GraphVerifyError(f"[{cid}] assert 'equals' requires an `expected` block")
    return Case(
        id=cid,
        cypher=str(cypher),
        assertion=assertion,
        description=str(raw.get("description", "")),
        expected=raw.get("expected"),
        params=dict(raw.get("params") or {}),
    )


_LABEL_OK = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _parse_anchor(raw: Any, suite_name: str) -> Anchor | None:
    """Parse a suite's ``anchor:`` block. Absent -> ``None`` (reported NOT RUN)."""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise GraphVerifyError(
            f"{suite_name}: `anchor` must be a mapping, got {type(raw).__name__}"
        )
    label = raw.get("label")
    cypher = raw.get("cypher")
    if bool(label) == bool(cypher):
        raise GraphVerifyError(
            f"{suite_name}: an anchor declares EXACTLY ONE of `label:` or `cypher:` "
            "(label + min_count for a row count, cypher + min_rows for anything else)"
        )
    minimum = raw.get("min_count" if label else "min_rows", 1)
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
        raise GraphVerifyError(
            f"{suite_name}: anchor minimum must be an integer >= 1, got {minimum!r} - "
            "an anchor of zero is satisfied by an empty graph, which is what an anchor is for"
        )
    if label:
        if not _LABEL_OK.match(str(label)):
            raise GraphVerifyError(
                f"{suite_name}: anchor label {label!r} is not a plain label name; use the "
                "`cypher:` form for anything the generated count cannot express"
            )
        cypher = f"MATCH (n:{label}) RETURN n LIMIT {minimum}"
    return Anchor(
        cypher=str(cypher),
        min_rows=minimum,
        description=str(raw.get("description", "")),
        label=str(label) if label else None,
    )


def load_suite(path: str | Path) -> Suite:
    """Parse a single suite file. Pure — no graph access."""
    path = Path(path)
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_cases = doc.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise GraphVerifyError(f"{path}: must contain a non-empty `cases:` list")
    cases = tuple(_parse_case(c) for c in raw_cases)
    name = str(doc.get("suite", path.stem))
    return Suite(
        name=name,
        cases=cases,
        description=str(doc.get("description", "")),
        targets=tuple(doc.get("targets") or ()),
        path=path,
        anchor=_parse_anchor(doc.get("anchor"), name),
    )


def load_suites(directory: str | Path = DEFAULT_GRAPH_TESTS_DIR) -> list[Suite]:
    """Load every ``*.yaml`` suite in a directory, sorted by filename. Pure."""
    directory = Path(directory)
    return [load_suite(p) for p in sorted(directory.glob("*.yaml"))]


# ---------------------------------------------------------------------------
# Evaluation (pure / offline)
# ---------------------------------------------------------------------------
def _as_row_list(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return list(value)
    raise GraphVerifyError(f"expected a row dict or list of row dicts, got {type(value).__name__}")


def evaluate(
    assertion: Assertion, rows: list[dict[str, Any]], expected: Any = None
) -> tuple[bool, str]:
    """Return ``(passed, detail)`` for a set of result rows. Pure — no graph access."""
    if assertion is Assertion.EMPTY:
        return (len(rows) == 0, "" if len(rows) == 0 else f"expected 0 rows, got {len(rows)}")
    if assertion is Assertion.NONEMPTY:
        return (len(rows) > 0, "" if len(rows) > 0 else "expected >=1 row, got 0")
    if assertion is Assertion.EQUALS:
        want = _as_row_list(expected)
        ok = rows == want
        return (ok, "" if ok else f"expected rows {want!r}, got {rows!r}")
    raise GraphVerifyError(f"unhandled assertion: {assertion!r}")  # pragma: no cover


def unknown_targets(suite: Suite, review_labels: Any) -> list[str]:
    """Labels a suite targets that the review backbone doesn't know about.

    Optional cross-check that ties graph-verify to the ``review_labels`` backbone (both
    in the ``drydocs-review`` component). ``review_labels`` is a
    :class:`drydocs.review.review_labels.ReviewLabels`; passed in to keep this pure.
    """
    known = set(review_labels.all_labels())
    return [t for t in suite.targets if t not in known]


# ---------------------------------------------------------------------------
# Running (touches the graph — READ ONLY)
# ---------------------------------------------------------------------------
@runtime_checkable
class GraphRunner(Protocol):
    def run(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]: ...


def run_case(client: GraphRunner, case: Case) -> CaseResult:
    rows = client.run(case.cypher, case.params)
    passed, detail = evaluate(case.assertion, rows, case.expected)
    return CaseResult(case=case, passed=passed, rows=rows, detail=detail)


def run_suite(client: GraphRunner, suite: Suite) -> SuiteResult:
    """Run one suite, ANCHOR FIRST (REV2).

    Three outcomes, and the middle one is the whole item: no anchor declared, or
    an anchor that finds nothing, is NOT_CHECKED — the cases are not run at all,
    because an ``empty`` assertion over an absent graph answers a question
    nobody asked. Only once the anchor holds do the cases decide the verdict.
    """
    if suite.anchor is None:
        return SuiteResult(
            suite=suite,
            outcome=not_checked(
                f"suite {suite.name!r} declares no anchor, so a passing negative assertion "
                "cannot be told from an empty graph - add an `anchor:` block (REV2)",
            ),
        )
    anchor_rows = client.run(suite.anchor.cypher, {})
    if len(anchor_rows) < suite.anchor.min_rows:
        subject = suite.anchor.label or "the declared anchor query"
        return SuiteResult(
            suite=suite,
            outcome=not_checked(
                f"suite {suite.name!r} did not run: its anchor ({subject}) found "
                f"{len(anchor_rows)} of the {suite.anchor.min_rows} row(s) it requires, so this "
                "graph cannot answer the suite's questions and a PASS would mean nothing",
            ),
            anchor_rows=len(anchor_rows),
        )
    results = tuple(run_case(client, case) for case in suite.cases)
    failed = tuple(r for r in results if not r.passed)
    subject = f"{len(results)} case(s) of {suite.name}"
    if failed:
        return SuiteResult(
            suite=suite,
            outcome=findings(
                tuple(f"{r.case.id}: {r.detail}" for r in failed),
                size=len(results),
                subject=subject,
            ),
            results=results,
            anchor_rows=len(anchor_rows),
        )
    return SuiteResult(
        suite=suite,
        outcome=checked_clean(size=len(results), subject=subject),
        results=results,
        anchor_rows=len(anchor_rows),
    )


def suite_verdict(client: GraphRunner, suite: Suite) -> CheckOutcome:
    """The suite's three-state verdict alone — the registered probe (ADR 0021 D3).

    :func:`run_suite` carries the same verdict plus the case detail; this is the
    name the probe registry declares, because the registry's guard reads a return
    annotation and the answer to "did this suite pass" is the outcome, not the rows.
    """
    return run_suite(client, suite).outcome


def exit_code(result: SuiteResult | Iterable[CaseResult]) -> int:
    """0 clean, 1 findings, 2 NOT RUN — three codes for three states (REV2).

    NOT RUN gets its own code rather than sharing 0 or 1: sharing 0 is the bug
    this item fixes, and sharing 1 would tell an operator the invariants were
    violated when in fact nothing was checked. J78 made the same distinction for
    a CI verdict, and for the same reason.

    Still accepts a bare iterable of :class:`CaseResult` — the pre-REV2 shape —
    so a caller holding case results can ask the old question. That path has no
    anchor to consult and therefore cannot return 2.
    """
    if isinstance(result, SuiteResult):
        if result.outcome.is_not_checked:
            return 2
        return 0 if result.outcome.is_clean else 1
    return 0 if all(r.passed for r in result) else 1
