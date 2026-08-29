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
        header["rev"] == 13
    )  # Rev 13, 2026-08-24: PRESENTATION ONLY. Appendix B's fifteen bare command lines gain
    # a numbered `#` comment per step and blank-line phase grouping, and the four remaining
    # bare commands elsewhere pick up the aligned trailing comment the doc's other
    # multi-command blocks already had. THE RULE: a fenced block with two or more commands
    # annotates every line; a single-command block does not, its step title already being
    # the description. No command, order or success check changed. Appendix B stays
    # guard-clean because test_load_sequence_surfaces extracts verbs with
    # `poetry run drydocs (<verb>)` and never sees a comment — which is also why a
    # superseded step must never be left commented-out there: the regex would match it.
    # Rev 12, 2026-08-24: the rev11 SME feedback — provisioning moves out of Startup to the
    # end of Prerequisites (it is a precondition of every startup step, not one of them),
    # "Schema backbone" -> "Schema core", the per-file-verb scolding dropped. The same
    # feedback's "commands run together" note was a RENDERER defect, not prose: render_body
    # folded a fenced block inside a list item into the item's text.
    # Rev 11, 2026-08-24: the G102 catch-up. The doc had told readers for two weeks to
    # provision a four-database topology two of whose names retired at the 2026-08-18 fold,
    # and it ordered provisioning FOURTH — after the verbs that connect to the databases it
    # creates, so `drydocs check` raises DatabaseNotFound and the sequence could not be
    # followed on the fresh container it was written for. Provisioning is now step 2.
    # Rev 10, 2026-08-04 (N6: Appendix B becomes the `cold-start` PROFILE of
    # cli.CANONICAL_LOAD_SEQUENCE rather than a second sequence — it gains the standing
    # docs-verify step it was missing, and test_load_sequence_surfaces.py now fails on
    # any drift between the block and the declaration). Rev 9 same day was X2: ddlineage
    # retired — ADR 0002 X1 amendment; topology enumerations drop to four names and the
    # provisioning-never-drops asymmetry is written into startup step 4. Rev 8 same day
    # was G52: the rollback copy Appendix A promised no longer exists on the laptop;
    # venue-named per J18.
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
    """The rev1 file specifically — scoped by doc_rev, not just doc_id.

    The doc has more than one feedback file now (rev11 landed 2026-08-24), and a
    doc_id-only filter silently widened this from "the rev1 file" to "every note ever
    left on this doc" — which is a test that changes meaning every time a review
    happens. Filtering on the rev keeps it pinned to the file it names.
    """
    rows = [
        r
        for r in DesignDocFeedbackAdapter(FEEDBACK_DIR).rows()
        if r["doc_id"] == "drydocs-startup-refresh-runbook" and r["doc_rev"] == 1
    ]
    assert len(rows) == 2, f"the committed rev1 file carries 2 notes, got {len(rows)}"
    for r in rows:
        model = FeedbackNoteRow.model_validate(r)
        assert model.doc_rev == 1  # taken against Rev 1 (filename <N>)
        assert model.status == "applied"  # marked when Rev 2 landed
        assert model.author == "chad.wilson"  # file-level author field
        assert model.base_anchor == model.anchor  # authored anchors, not derived
    assert {r["anchor"] for r in rows} == {"front-matter", "purpose-scope"}


def test_feedback_adapter_reads_rev11_startup_review() -> None:
    """The rev11 file — the review that moved provisioning out of Startup (Rev 12).

    It carries the two rev1 notes forward alongside its own, which is deliberate: the
    reviewer re-sent the whole sheet, and dropping the already-applied ones would leave
    a reader chasing two of the notes they can see in the source.
    """
    rows = [
        r
        for r in DesignDocFeedbackAdapter(FEEDBACK_DIR).rows()
        if r["doc_id"] == "drydocs-startup-refresh-runbook" and r["doc_rev"] == 11
    ]
    assert len(rows) == 3
    assert {r["anchor"] for r in rows} == {"front-matter", "purpose-scope", "startup"}
    for r in rows:
        model = FeedbackNoteRow.model_validate(r)
        assert model.status == "applied"  # all three resolved at Rev 12
        assert model.author == "chad.wilson"


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
