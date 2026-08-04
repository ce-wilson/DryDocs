"""Adapter-level tests for the L7 doc-traceability loaders (no DB needed).

Fixtures are the REAL committed artifacts — docs/design/*.md and
docs/design/feedback/*.yaml — so these tests double as a conformance guard:
if a doc edit breaks the deterministic parse (matrix cell contract, anchor
convention, feedback format), it fails here before any graph load.
Gate: doc-traceability-feedback (signed off 2026-07-20, config/gate-log.md).
"""

from __future__ import annotations

from pathlib import Path

from drydocs.loaders.doc_traceability import (
    DesignDocFeedbackAdapter,
    DesignDocSectionsAdapter,
    TraceabilityMatrixAdapter,
    classify_test_kind,
    doc_type_for_stem,
    parse_doc_header,
    parse_matrix_rows,
)
from drydocs_core.models.doc_traceability import (
    DESIGN_DOCS_ORIGIN,
    DocSectionRow,
    FeedbackNoteRow,
    TraceabilityRow,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DIR = REPO_ROOT / "docs" / "design"
FEEDBACK_DIR = DESIGN_DIR / "feedback"
CONTROLM_TDD = DESIGN_DIR / "controlm-ingestion-tdd.md"
RUNBOOK = DESIGN_DIR / "drydocs-startup-refresh-runbook.md"


# ---- header / doc_type ------------------------------------------------------


def test_doc_type_suffix_rule() -> None:
    assert doc_type_for_stem("controlm-ingestion-tdd") == "TDD"
    assert doc_type_for_stem("drydocs-startup-refresh-runbook") == "Runbook"
    assert doc_type_for_stem("drydocs-project-review") == "Review"
    assert doc_type_for_stem("graph-retrieval-benchmark-explainer") == "Explainer"
    assert doc_type_for_stem("something-else") == "DesignDoc"


def test_runbook_header_carries_rev_and_commit() -> None:
    header = parse_doc_header(RUNBOOK)
    assert header["origin"] == DESIGN_DOCS_ORIGIN
    assert header["doc_id"] == "drydocs-startup-refresh-runbook"
    assert header["doc_type"] == "Runbook"
    assert (
        header["rev"] == 8
    )  # Rev 8, 2026-08-04 (G52: the rollback copy Appendix A promised no longer exists on
    # the laptop — container gone, its orphaned data volume deleted; the claim is now
    # venue-named per J18 rather than stated flat, since the desktop may still hold one)
    assert header["doc_status"] == "DESCRIPTIVE"
    assert header["commit"], "front-matter commit citation should parse"
    assert header["path"] == "docs/design/drydocs-startup-refresh-runbook.md"


# ---- sections stream --------------------------------------------------------


def test_sections_adapter_covers_every_committed_doc() -> None:
    rows = list(DesignDocSectionsAdapter(DESIGN_DIR).rows())
    assert rows, "no section rows parsed"
    doc_ids = {r["doc_id"] for r in rows}
    assert "controlm-ingestion-tdd" in doc_ids
    assert "drydocs-startup-refresh-runbook" in doc_ids
    # every row validates against the pydantic model (what BaseLoader enforces)
    for r in rows:
        DocSectionRow.model_validate(r)
    # the runbook's authored outline anchors are all present
    runbook_anchors = {
        r["anchor"] for r in rows if r["doc_id"] == "drydocs-startup-refresh-runbook"
    }
    assert {"front-matter", "purpose-scope", "startup", "verify", "rollback"} <= runbook_anchors


# ---- traceability matrix stream ---------------------------------------------


def test_controlm_matrix_parses_all_rows() -> None:
    rows = parse_matrix_rows(CONTROLM_TDD.read_text(encoding="utf-8"), "controlm-ingestion-tdd")
    ids = [r["requirement_id"] for r in rows]
    assert len(ids) == 9, f"expected the 9 committed matrix rows, got {ids}"
    assert "FR-CMI-003" in ids and "NFR-CMI-001" in ids
    by_id = {r["requirement_id"]: r for r in rows}
    # kind from the id prefix (gate A3)
    assert by_id["FR-CMI-001"]["kind"] == "FR"
    assert by_id["NFR-CMI-001"]["kind"] == "NFR"
    # comma-split components, backticks stripped
    assert by_id["FR-CMI-003"]["components"] == ["controlm_folders.cypher", "folder_name.py"]
    # section anchor cell resolves to the authored anchor id
    assert by_id["FR-CMI-003"]["section_anchors"] == ["design-data-mapping"]
    for r in rows:
        TraceabilityRow.model_validate(r)


def test_fr_cmi_007_test_cell_splits_and_classifies() -> None:
    rows = parse_matrix_rows(CONTROLM_TDD.read_text(encoding="utf-8"), "controlm-ingestion-tdd")
    tests = {
        t["ref"]: t["kind"] for r in rows if r["requirement_id"] == "FR-CMI-007" for t in r["tests"]
    }
    assert len(tests) == 2, f"the ';'-split should yield 2 citations, got {tests}"
    kinds = set(tests.values())
    assert kinds == {"gate", "graph-test"}, f"kind-rule-v1 misclassified: {tests}"


def test_kind_rule_v1() -> None:
    assert classify_test_kind("graph-tests/seal-attribution-coverage.yaml") == "graph-test"
    assert classify_test_kind("gate `seal-attribution-match-policy` (2026-07-14)") == "gate"
    assert classify_test_kind("m3-verify dependency check") == "verify"
    assert classify_test_kind("test_ingest_chain_order_is_enforced") == "unit"


def test_five_column_matrix_maps_by_header_not_position() -> None:
    # The web-console TDD's matrix has NO Description column and a prose
    # requirement identity — the header-driven map must land every cell in
    # the right field (a fixed-position parse shifted all of them).
    md = (DESIGN_DIR / "drydocs-web-console-tdd.md").read_text(encoding="utf-8")
    rows = parse_matrix_rows(md, "drydocs-web-console-tdd")
    assert len(rows) >= 10
    first = rows[0]
    assert first["kind"] == "other"  # prose identity, loose mode (gate D5)
    assert first["section_anchors"] == ["detailed-design"]
    assert first["components"] == ["drydocs-web"]
    assert all(
        t["ref"] != "done" for r in rows for t in r["tests"]
    ), "a Status cell leaked into the tests field — column mapping regressed"
    for r in rows:
        TraceabilityRow.model_validate(r)


def test_section_cell_qualifiers_and_semicolons_normalize() -> None:
    # The remediation TDD cites `design-summary; detailed-design (Stage A)` —
    # ';'-separated anchors with a parenthetical sub-locator; both must
    # normalize to bare authored anchor ids or SPECIFIED_IN silently drops.
    md = (DESIGN_DIR / "drydocs-remediation-tdd.md").read_text(encoding="utf-8")
    rows = parse_matrix_rows(md, "drydocs-remediation-tdd")
    by_id = {r["requirement_id"].split(" ")[0]: r for r in rows}
    fr1 = next(v for k, v in by_id.items() if k.startswith("FR-REM-1"))
    assert fr1["section_anchors"] == ["design-summary", "detailed-design"]
    fr2 = next(v for k, v in by_id.items() if k.startswith("FR-REM-2"))
    assert fr2["section_anchors"] == ["detailed-design"]


def test_matrix_adapter_only_yields_docs_with_a_matrix() -> None:
    rows = list(TraceabilityMatrixAdapter(DESIGN_DIR).rows())
    assert rows
    # the runbook outline has NO traceability block (documented L8 decision)
    assert all(r["doc_id"] != "drydocs-startup-refresh-runbook" for r in rows)


# ---- L18: separators inside parentheticals never shear a ref -------------------


def test_split_cell_keeps_parenthetical_separators_whole() -> None:
    # The committed shear case: FR-CMI-007's component cell held
    # `K2 loader (`seal_attribution.cypher`, `load-seal-attribution`)` and the
    # naive comma split stored two corrupt (origin, ref) identities.
    from drydocs.loaders.doc_traceability import _split_cell

    assert _split_cell("K2 loader (`a.cypher`, `load-x`), drydocs/cli.py", ",") == [
        "K2 loader (`a.cypher`, `load-x`)",
        "drydocs/cli.py",
    ]
    # Test cells split on ';' — same rule.
    assert _split_cell("t.py (a; b); u.py", ";") == ["t.py (a; b)", "u.py"]
    # Plain cells are unchanged by the depth-aware split.
    assert _split_cell("a.py, b.py", ",") == ["a.py", "b.py"]
    # An unbalanced cell still terminates (no separator ever closes it).
    assert _split_cell("broken (x, y", ",") == ["broken (x, y"]


def test_no_committed_ref_is_sheared_mid_parenthetical() -> None:
    """Conformance guard over the real docs: a ref with unbalanced parens is
    the shear signature (or an authoring typo) — either way it corrupts
    (origin, ref) identity and must fail here before any load."""
    for row in TraceabilityMatrixAdapter(DESIGN_DIR).rows():
        for ref in row["components"]:
            assert ref.count("(") == ref.count(
                ")"
            ), f"{row['doc_id']} {row['requirement_id']}: sheared component ref {ref!r}"
        for t in row["tests"]:
            assert t["ref"].count("(") == t["ref"].count(
                ")"
            ), f"{row['doc_id']} {row['requirement_id']}: sheared test ref {t['ref']!r}"


# ---- feedback stream ----------------------------------------------------------


def test_feedback_adapter_reads_rev1_with_lifecycle_and_author() -> None:
    rows = [
        r
        for r in DesignDocFeedbackAdapter(FEEDBACK_DIR).rows()
        if r["doc_id"] == "drydocs-startup-refresh-runbook"
    ]
    assert len(rows) == 2, f"the committed rev1 file carries 2 notes, got {len(rows)}"
    for r in rows:
        model = FeedbackNoteRow.model_validate(r)
        assert model.doc_rev == 1  # taken against Rev 1 (filename <N>)
        assert model.status == "applied"  # marked when Rev 2 landed
        assert model.author == "chad.wilson"  # file-level author field
        assert model.base_anchor == model.anchor  # authored anchors, not derived
    assert {r["anchor"] for r in rows} == {"front-matter", "purpose-scope"}


def test_feedback_derived_anchor_degrades_to_base(tmp_path: Path) -> None:
    (tmp_path / "some-doc-rev3.yaml").write_text(
        "doc: some-doc\nnotes:\n"
        "  - anchor: detailed-design--stage-2-variable-pass\n"
        "    note: |\n      check the bind order\n",
        encoding="utf-8",
    )
    rows = list(DesignDocFeedbackAdapter(tmp_path).rows())
    assert len(rows) == 1
    assert rows[0]["anchor"] == "detailed-design--stage-2-variable-pass"
    assert rows[0]["base_anchor"] == "detailed-design"  # L11 degrade rule, graph-side
    assert rows[0]["doc_rev"] == 3
    assert rows[0]["status"] == "open"  # default when the yaml carries none
    assert rows[0]["author"] is None


def test_feedback_stray_files_are_findings(tmp_path: Path) -> None:
    """L20 — the misnamed Copy-feedback export (2026-07-28) must be visible."""
    (tmp_path / "some-doc-rev1.yaml").write_text(
        "doc: some-doc\nnotes:\n  - anchor: design\n    note: fine\n", encoding="utf-8"
    )
    (tmp_path / "README.md").write_text("expected extra\n", encoding="utf-8")
    (tmp_path / "scans").mkdir()  # the L6 paper archive — a dir, never a finding
    (tmp_path / "scans" / "page1.png").write_bytes(b"\x89PNG")
    (tmp_path / "some-doc-rev1 - Copy.yaml").write_text("doc: some-doc\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("loose notes\n", encoding="utf-8")

    adapter = DesignDocFeedbackAdapter(tmp_path)
    assert adapter.stray_files() == ["notes.txt", "some-doc-rev1 - Copy.yaml"]
    # the stray yaml is a finding, not a row — rows() still loads only the
    # well-named export
    assert {r["doc_id"] for r in adapter.rows()} == {"some-doc"}


def test_feedback_stray_files_empty_cases(tmp_path: Path) -> None:
    assert DesignDocFeedbackAdapter(tmp_path / "absent").stray_files() == []
    assert DesignDocFeedbackAdapter(FEEDBACK_DIR).stray_files() == [], (
        "the committed feedback/ directory carries a file matching no "
        "<doc>-rev<N>.yaml pattern — rename it so its notes load, move it "
        "under scans/, or add it to expected_extra_names with a reason"
    )
