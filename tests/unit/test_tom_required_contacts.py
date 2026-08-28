"""G71 — the required-contact completeness surfaces (gate tom-roles-
enumeration-and-cardinality, signed 2026-08-11).

Offline by design (J18: no live-graph claim is made here): the suite loader
and evaluator are pure, and the presence check's mechanics are proven with a
duck-typed runner — the graph_verify idiom. What a live run adds is FINDINGS,
not validity.

Three properties pinned:
* the suite and both ownership specs DEFER TO THE DECLARATION — no vocabulary
  class id is written literally anywhere in them (the G70 discipline; a
  register change must never edit these surfaces);
* the presence case reports (app, role) rows and fails on a violation, passes
  on none (SS-C4's form, SS-B5's flag-never-refuse);
* the two sign-off caveats ride the operator-facing outputs (the sign-off:
  the report "should say so rather than imply DryDocs found them").
"""

from __future__ import annotations

from pathlib import Path

from drydocs.graph_verify import Assertion, load_suite, run_case
from drydocs_api.query_specs import QUERY_SPECS
from drydocs_core.ontology.tom_role_vocabulary import load_vocabulary

REPO_ROOT = Path(__file__).resolve().parents[2]
SUITE_PATH = REPO_ROOT / "graph-tests" / "tom-required-contacts.yaml"

GAPS_SPEC = "ownership.required-contact-gaps.v1"
CAPTURE_SPEC = "ownership.capture-gaps.v1"


class _Runner:
    """Duck-typed GraphRunner returning canned rows."""

    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def run(self, cypher: str, params: dict | None = None) -> list[dict]:
        return self.rows


def _suite():
    return load_suite(SUITE_PATH)


def _case(case_id: str):
    suite = _suite()
    by_id = {c.id: c for c in suite.cases}
    assert case_id in by_id, f"{case_id} missing — cases: {sorted(by_id)}"
    return by_id[case_id]


# -- shape: the suite is the SS-C4 mechanism -----------------------------------


def test_suite_loads_with_the_three_ruled_cases() -> None:
    suite = _suite()
    assert suite.name == "tom-required-contacts"
    assert [c.id for c in suite.cases] == ["TC-01", "TC-02", "TC-03"]
    assert _case("TC-01").assertion is Assertion.NONEMPTY  # vacuity guard
    assert _case("TC-02").assertion is Assertion.EMPTY  # G16: never required+derived
    assert _case("TC-03").assertion is Assertion.EMPTY  # the presence check


def test_presence_case_reports_app_role_rows_with_the_ruled_denominator() -> None:
    cypher = _case("TC-03").cypher
    # SS-C6: the denominator is applications a feed covered — the positive
    # QUALIFIED_ATTRIBUTION predicate must precede the missing-holder one.
    assert "(a)-[:QUALIFIED_ATTRIBUTION]->(:Attribution)" in cypher
    assert "NOT (a)-[:QUALIFIED_ATTRIBUTION]->(:Attribution)-[:HAD_ROLE]->(r)" in cypher
    # SS-C4: the offending (app, role) row is the report's shape.
    assert "AS app_id" in cypher and "AS missing_required_class" in cypher
    # the required set comes from the graph's own declared vocabulary
    assert "r.required = true" in cypher


def test_presence_case_fails_on_a_violation_and_passes_on_none() -> None:
    case = _case("TC-03")
    violation = run_case(_Runner([{"app_id": "APP-1", "missing_required_class": "x"}]), case)
    assert violation.passed is False
    assert violation.rows == [{"app_id": "APP-1", "missing_required_class": "x"}]
    clean = run_case(_Runner([]), case)
    assert clean.passed is True


def test_vacuity_guard_fails_on_an_unseeded_graph() -> None:
    case = _case("TC-01")
    unseeded = run_case(_Runner([]), case)
    assert unseeded.passed is False, "an unseeded vocabulary must FAIL, not pass vacuously"
    seeded = run_case(_Runner([{"required_class": "x"}]), case)
    assert seeded.passed is True


# -- G70 discipline: every surface defers to the declaration -------------------


def test_no_vocabulary_class_id_is_written_literally() -> None:
    """A register change (a class added, renamed, re-flagged) must never edit
    the suite or the specs — they join `required`/`active` on the graph's own
    TOMRole nodes. A literal id here is the §A1b drift seam reopening."""
    surfaces = {
        "graph-tests/tom-required-contacts.yaml": SUITE_PATH.read_text(encoding="utf-8"),
        GAPS_SPEC: QUERY_SPECS[GAPS_SPEC].cypher,
        CAPTURE_SPEC: QUERY_SPECS[CAPTURE_SPEC].cypher,
    }
    offenders = [
        f"{where}: {cls.id}"
        for cls in load_vocabulary().classes
        for where, text in surfaces.items()
        if cls.id in text
    ]
    assert not offenders, offenders


# -- SS-C5/SS-C6: the report joins the ownership surface, split as ruled -------


def test_specs_join_the_ownership_family_with_matching_columns() -> None:
    gaps = QUERY_SPECS[GAPS_SPEC]
    capture = QUERY_SPECS[CAPTURE_SPEC]
    for spec in (gaps, capture):
        assert spec.database == "drydocs"
        assert spec.classification == "internal"
        # O52 discipline: every RETURN alias is a declared column
        for col in spec.columns:
            assert f"AS {col.name}" in spec.cypher, f"{spec.id}: {col.name}"
    # the two findings stay two listings (SS-C6): the capture spec must not
    # join roles at all, and the gaps spec must not include uncovered apps
    assert "TOMRole" not in capture.cypher
    assert "NOT (a)-[:QUALIFIED_ATTRIBUTION]->(:Attribution)" in capture.cypher


def test_both_signoff_caveats_ride_the_operator_facing_outputs() -> None:
    """The sign-off: findings in the Operate Manager family are real defects
    being fixed elsewhere (mid-correction at source), and a count-to-one check
    cannot see geography/coverage-window gaps (residual 4). The report must
    say so in ITS OWN output — not in a gate log nobody reads at the page."""
    gaps_desc = QUERY_SPECS[GAPS_SPEC].description
    suite_text = SUITE_PATH.read_text(encoding="utf-8")
    for output in (gaps_desc, suite_text):
        assert "mid-correction" in output.lower()
        assert "geography" in output.lower()
