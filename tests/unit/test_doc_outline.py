"""Tests for drydocs.doc_outline — the canonical-outline completeness + traceability guard.

Unit tests run on tiny in-memory fixtures; the final test asserts the REAL Control-M TDD
conforms to the REAL tdd.outline.yaml, so the exemplar can never silently drift from the
contract (Epic L / L1).
"""
from __future__ import annotations

from pathlib import Path

from drydocs.doc_outline import Outline, check, load_outline, validate_paths

REPO_ROOT = Path(__file__).resolve().parents[2]
TDD_OUTLINE = REPO_ROOT / "docs" / "design" / "templates" / "tdd.outline.yaml"
CONTROLM_TDD = REPO_ROOT / "docs" / "design" / "controlm-ingestion-tdd.md"


def _outline(mode: str = "strict") -> Outline:
    """A minimal outline: required sections + a traceability contract at `mode`."""
    return Outline(
        schema="drydocs.doc-outline.v1",
        doc_type="TEST",
        sections=[
            {"anchor": "purpose", "heading": "Purpose", "required": True},
            {"anchor": "detailed-design", "heading": "Design", "required": True},
            {"anchor": "traceability-matrix", "heading": "Traceability", "required": True},
            {"anchor": "appendix", "heading": "Appendix", "required": False},
        ],
        traceability={
            "mode": mode,
            "requirement_id_pattern": r"^(FR|NFR)-[A-Z0-9]+-\d+$",
            "matrix_section": "traceability-matrix",
        },
        raw={},
    )


GOOD_MATRIX = """
| Requirement | Description | Design section | Test / verify | Status |
|---|---|---|---|---|
| FR-T-001 | does a thing | detailed-design | test_thing | done |
"""


def _good_doc(matrix: str = GOOD_MATRIX) -> str:
    return f"""<!-- anchor: purpose -->
## Purpose
Covers FR-T-001.

<!-- anchor: detailed-design -->
## Design
The design.

<!-- anchor: traceability-matrix -->
## Traceability
{matrix}
<!-- anchor: appendix -->
## Appendix
"""


def test_good_doc_conforms() -> None:
    assert check(_outline(), _good_doc()) == []


def test_missing_required_anchor_fails() -> None:
    doc = _good_doc().replace("<!-- anchor: detailed-design -->\n", "")
    problems = check(_outline(), doc)
    assert any("detailed-design" in p for p in problems), problems


def test_orphan_requirement_id_fails_in_strict() -> None:
    # id referenced in the body but NOT present as a matrix row
    doc = _good_doc().replace("Covers FR-T-001.", "Covers FR-T-001 and FR-T-999.")
    problems = check(_outline("strict"), doc)
    assert any("FR-T-999" in p for p in problems), problems


def test_loose_mode_skips_id_format_and_orphans() -> None:
    """loose mode: free-form ids + body-orphan ids are fine, as long as each matrix row
    still cites a valid design-section anchor and a test."""
    loose_matrix = (
        "| Requirement | Design section | Test / verify |\n"
        "|---|---|---|\n"
        "| some free-form capability | detailed-design | test_x |\n"
    )
    doc = _good_doc(loose_matrix).replace("Covers FR-T-001.", "Covers FR-T-999 (not in matrix).")
    assert check(_outline("loose"), doc) == []


def test_loose_mode_still_requires_design_anchor_and_test() -> None:
    bad = (
        "| Requirement | Design section | Test / verify |\n"
        "|---|---|---|\n"
        "| cap | nowhere-section |  |\n"
    )
    problems = check(_outline("loose"), _good_doc(bad))
    assert any("cites no known outline anchor" in p for p in problems), problems
    assert any("empty test/verify" in p for p in problems), problems


def test_matrix_row_with_unknown_anchor_fails() -> None:
    bad = GOOD_MATRIX.replace("| detailed-design |", "| nowhere-section |")
    problems = check(_outline(), _good_doc(bad))
    assert any("cites no known outline anchor" in p for p in problems), problems


def test_matrix_row_with_empty_test_fails() -> None:
    bad = GOOD_MATRIX.replace("| test_thing |", "|  |")
    problems = check(_outline(), _good_doc(bad))
    assert any("empty test/verify" in p for p in problems), problems


def test_duplicate_matrix_row_fails() -> None:
    dup = GOOD_MATRIX + "| FR-T-001 | again | detailed-design | test_thing | done |\n"
    problems = check(_outline(), _good_doc(dup))
    assert any("more than one matrix row" in p for p in problems), problems


# ── the exemplar: real outline + real doc must conform ────────────────────────
def test_real_tdd_outline_loads() -> None:
    outline = load_outline(TDD_OUTLINE)
    assert outline.doc_type == "TDD"
    assert "traceability-matrix" in outline.required_anchors()


def test_controlm_tdd_conforms_to_outline() -> None:
    problems = validate_paths(TDD_OUTLINE, CONTROLM_TDD)
    assert problems == [], "Control-M TDD drifted from tdd.outline.yaml:\n  " + "\n  ".join(problems)


def test_every_committed_tdd_conforms_to_outline() -> None:
    """Every docs/design/*-tdd.md validates — new TDDs are auto-covered, no enumeration."""
    tdds = sorted((REPO_ROOT / "docs" / "design").glob("*-tdd.md"))
    assert tdds, "no committed TDDs found"
    for tdd in tdds:
        problems = validate_paths(TDD_OUTLINE, tdd)
        assert problems == [], f"{tdd.name} drifted from tdd.outline.yaml:\n  " + "\n  ".join(problems)
