"""Tests for drydocs.doc_outline — the canonical-outline completeness + traceability guard.

Unit tests run on tiny in-memory fixtures; the final test asserts the REAL Control-M TDD
conforms to the REAL tdd.outline.yaml, so the exemplar can never silently drift from the
contract (Epic L / L1).
"""

from __future__ import annotations

from pathlib import Path

from drydocs.doc_outline import Outline, check, feedback_anchor_valid, load_outline, validate_paths

REPO_ROOT = Path(__file__).resolve().parents[2]
TDD_OUTLINE = REPO_ROOT / "docs" / "design" / "templates" / "tdd.outline.yaml"
CONTROLM_TDD = REPO_ROOT / "docs" / "design" / "controlm-ingestion-tdd.md"
RUNBOOK_OUTLINE = REPO_ROOT / "docs" / "design" / "templates" / "runbook.outline.yaml"
STARTUP_RUNBOOK = REPO_ROOT / "docs" / "design" / "drydocs-startup-refresh-runbook.md"


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
    assert problems == [], "Control-M TDD drifted from tdd.outline.yaml:\n  " + "\n  ".join(
        problems
    )


def test_every_committed_tdd_conforms_to_outline() -> None:
    """Every docs/design/*-tdd.md validates — new TDDs are auto-covered, no enumeration."""
    tdds = sorted((REPO_ROOT / "docs" / "design").glob("*-tdd.md"))
    assert tdds, "no committed TDDs found"
    for tdd in tdds:
        problems = validate_paths(TDD_OUTLINE, tdd)
        assert problems == [], f"{tdd.name} drifted from tdd.outline.yaml:\n  " + "\n  ".join(
            problems
        )


# ── L8: the Runbook — the second doc type through the same contract ───────────
def test_real_runbook_outline_loads() -> None:
    outline = load_outline(RUNBOOK_OUTLINE)
    assert outline.doc_type == "Runbook"
    # the runbook's proof surface is its verify section, not a traceability matrix
    assert "verify" in outline.required_anchors()
    assert not outline.traceability.get("matrix_section")


def test_startup_refresh_runbook_conforms_to_outline() -> None:
    problems = validate_paths(RUNBOOK_OUTLINE, STARTUP_RUNBOOK)
    assert problems == [], (
        "startup/refresh runbook drifted from runbook.outline.yaml:\n  " + "\n  ".join(problems)
    )


def test_every_committed_runbook_conforms_to_outline() -> None:
    """Every docs/design/*-runbook.md validates — new runbooks are auto-covered."""
    runbooks = sorted((REPO_ROOT / "docs" / "design").glob("*-runbook.md"))
    assert runbooks, "no committed runbooks found"
    for rb in runbooks:
        problems = validate_paths(RUNBOOK_OUTLINE, rb)
        assert problems == [], f"{rb.name} drifted from runbook.outline.yaml:\n  " + "\n  ".join(
            problems
        )


# ── L15: the Review — the third doc type through the same contract ────────────
REVIEW_OUTLINE = REPO_ROOT / "docs" / "design" / "templates" / "review.outline.yaml"
PROJECT_REVIEW = REPO_ROOT / "docs" / "design" / "drydocs-project-review.md"


def test_real_review_outline_loads() -> None:
    outline = load_outline(REVIEW_OUTLINE)
    assert outline.doc_type == "Review"
    # the review narrates — no traceability spine (that's the TDDs' job)
    assert not outline.traceability.get("matrix_section")
    # the status section is the reason the Rev-per-epic-close cadence exists
    assert "status" in outline.required_anchors()


def test_project_review_conforms_to_outline() -> None:
    problems = validate_paths(REVIEW_OUTLINE, PROJECT_REVIEW)
    assert problems == [], "project review drifted from review.outline.yaml:\n  " + "\n  ".join(
        problems
    )


# ── the SDLC Run Book: the fourth doc type — support reference for an ─────────
#    Informatica-ETL business application (structure transcribed verbatim from a
#    reviewed enterprise example; all values in the exemplar are synthesized)
SDLC_RUNBOOK_OUTLINE = REPO_ROOT / "docs" / "design" / "templates" / "sdlc-app-runbook.outline.yaml"
SDLC_RUNBOOK_EXAMPLE = REPO_ROOT / "docs" / "design" / "templates" / "sdlc-app-runbook.example.md"


def test_real_sdlc_runbook_outline_loads() -> None:
    outline = load_outline(SDLC_RUNBOOK_OUTLINE)
    assert outline.doc_type == "SDLC-Runbook"
    # a support run book has inventories and procedures, not requirements
    assert not outline.traceability.get("matrix_section")
    # the sections the shape exists for: per-workflow blocks, script inventory,
    # directory map, recovery, escalation
    for anchor in (
        "etl-jobs",
        "unix-shell-scripts",
        "directory-configuration",
        "recovery-procedures",
        "tier2-escalation",
    ):
        assert anchor in outline.required_anchors(), anchor


def test_sdlc_runbook_example_conforms_to_outline() -> None:
    problems = validate_paths(SDLC_RUNBOOK_OUTLINE, SDLC_RUNBOOK_EXAMPLE)
    assert problems == [], (
        "sdlc-app-runbook.example.md drifted from sdlc-app-runbook.outline.yaml:\n  "
        + "\n  ".join(problems)
    )


# ── L11: derived subsection anchors in the feedback namespace ─────────────────
FB_DOC = "<!-- anchor: purpose -->\n## Purpose\n\n<!-- anchor: detailed-design -->\n## Design\n"


def test_feedback_anchor_valid_authored() -> None:
    assert feedback_anchor_valid("detailed-design", FB_DOC)


def test_feedback_anchor_valid_derived_from_authored_base() -> None:
    assert feedback_anchor_valid("detailed-design--stage-two-resolve", FB_DOC)


def test_feedback_anchor_invalid_unknown_base() -> None:
    assert not feedback_anchor_valid("nonexistent", FB_DOC)
    assert not feedback_anchor_valid("nonexistent--stage-one", FB_DOC)
