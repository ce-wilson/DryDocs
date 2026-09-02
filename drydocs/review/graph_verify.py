"""Data-driven Cypher acceptance runner (``drydocs-review`` component).

Loads YAML ``TC-*`` suites from ``graph-tests/``, runs each case's Cypher against a
live graph, and asserts the result shape (``empty`` / ``nonempty`` / ``equals``).
A suite fails (non-zero exit) if any case fails.

The **loader** (``load_suite`` / ``load_suites``) and the **evaluator** (``evaluate``)
are pure and offline — unit-testable with no Neo4j. Only ``run_case`` / ``run_suite``
touch the graph, via any object exposing ``run(cypher, params) -> list[dict]`` (the
:class:`drydocs.neo4j_client.Neo4jClient` interface). The graph is only READ — this
component writes no meaning edges, so it needs no HITL gate to run.

classification: Internal-Public — the committed example suite is a vendor-BMC smoke
test. Real acceptance suites (internal counts/IDs) live in a gitignored twin.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import yaml

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
class Suite:
    name: str
    cases: tuple[Case, ...]
    description: str = ""
    targets: tuple[str, ...] = ()
    path: Path | None = None


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


def load_suite(path: str | Path) -> Suite:
    """Parse a single suite file. Pure — no graph access."""
    path = Path(path)
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_cases = doc.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise GraphVerifyError(f"{path}: must contain a non-empty `cases:` list")
    cases = tuple(_parse_case(c) for c in raw_cases)
    return Suite(
        name=str(doc.get("suite", path.stem)),
        cases=cases,
        description=str(doc.get("description", "")),
        targets=tuple(doc.get("targets") or ()),
        path=path,
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


def run_suite(client: GraphRunner, suite: Suite) -> list[CaseResult]:
    return [run_case(client, case) for case in suite.cases]


def exit_code(results: Iterable[CaseResult]) -> int:
    """0 if every case passed, 1 if any failed."""
    return 0 if all(r.passed for r in results) else 1
