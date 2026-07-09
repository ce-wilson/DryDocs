"""Tests for drydocs.design_doc — the deterministic Markdown-subset renderer (Epic L / L3).

Unit tests exercise each block/inline construct on tiny fixtures; the final tests render the
REAL Control-M TDD and assert the anchors survive as element ids with no comment leakage.
"""
from __future__ import annotations

from pathlib import Path

from drydocs.design_doc import (
    doc_rev_footer,
    doc_title,
    feedback_yaml,
    render_body,
    render_doc,
    sme_feedback_filename,
    write_doc,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROLM_TDD = REPO_ROOT / "docs" / "design" / "controlm-ingestion-tdd.md"


def test_heading_with_anchor_becomes_id() -> None:
    html = render_body("<!-- anchor: traceability-matrix -->\n## Requirements traceability matrix")
    assert '<h2 id="traceability-matrix">Requirements traceability matrix</h2>' in html


def test_anchor_on_paragraph_when_no_heading() -> None:
    html = render_body("<!-- anchor: front-matter -->\n**Status:** DESCRIPTIVE")
    assert '<p id="front-matter"><strong>Status:</strong> DESCRIPTIVE</p>' in html


def test_inline_code_bold_link() -> None:
    html = render_body("Use `MERGE` and **bind** vars; see [oracle](oracle_adapter.py:61).")
    assert "<code>MERGE</code>" in html
    assert "<strong>bind</strong>" in html
    assert '<a href="oracle_adapter.py:61">oracle</a>' in html


def test_italic_and_not_over_matching() -> None:
    assert render_body("read it a *second* way") == "<p>read it a <em>second</em> way</p>"
    # spaces around a lone asterisk must NOT become italic
    assert "<em>" not in render_body("count a * b here")


def test_code_span_is_not_further_parsed() -> None:
    # ** inside a code span must stay literal, not become <strong>
    html = render_body("literal `a**b**c` here")
    assert "<code>a**b**c</code>" in html
    assert "<strong>" not in html


def test_table_renders() -> None:
    md = "| A | B |\n|---|---|\n| 1 | `x` |\n"
    html = render_body(md)
    assert "<table>" in html and "<th>A</th>" in html
    assert "<td>1</td>" in html and "<td><code>x</code></td>" in html


def test_fenced_code_escapes_and_keeps_lang() -> None:
    html = render_body("```sql\nSELECT * FROM t WHERE a < b;\n```")
    assert '<pre class="sql"><code>' in html
    assert "&lt; b" in html  # escaped, not raw <


def test_flat_and_nested_lists() -> None:
    flat = render_body("- one\n- two")
    assert flat == "<ul><li>one</li><li>two</li></ul>"
    nested = render_body("- a\n  - b\n- c")
    assert nested == "<ul><li>a<ul><li>b</li></ul></li><li>c</li></ul>"
    ordered = render_body("1. first\n2. second")
    assert ordered == "<ol><li>first</li><li>second</li></ol>"


def test_blockquote_recurses() -> None:
    html = render_body("> **Note.** it is\n> important")
    assert html.startswith("<blockquote>") and html.endswith("</blockquote>")
    assert "<strong>Note.</strong>" in html


def test_hr_and_comment_stripped() -> None:
    html = render_body("para\n\n---\n\n<!-- not an anchor -->\nmore")
    assert "<hr>" in html
    assert "<!--" not in html  # comments never leak into output


def test_rendering_is_deterministic() -> None:
    md = CONTROLM_TDD.read_text(encoding="utf-8")
    assert render_doc(md, "print") == render_doc(md, "print")
    assert render_doc(md, "screen") == render_doc(md, "screen")


def test_doc_title_from_h1() -> None:
    assert doc_title("# Technical Design — `x` chain\n\nbody") == "Technical Design — x chain"


# ── the real TDD ─────────────────────────────────────────────────────────────
def test_real_tdd_anchors_survive_no_leakage() -> None:
    md = CONTROLM_TDD.read_text(encoding="utf-8")
    for mode in ("screen", "print"):
        html = render_doc(md, mode)
        assert "<!-- anchor" not in html, f"anchor comment leaked into {mode} output"
        for anchor in ("front-matter", "traceability-matrix", "design-data-mapping", "hitl-gate"):
            assert f'id="{anchor}"' in html, f"missing id={anchor} in {mode}"
        assert "<table>" in html and "<pre" in html  # the mapping tables + SQL blocks rendered


def test_screen_has_feedback_layer_print_does_not() -> None:
    md = "# Doc\n\n<!-- anchor: purpose-scope -->\n## Purpose\ntext"
    screen = render_doc(md, "screen")
    printed = render_doc(md, "print")
    for marker in ("drydocs-doc-feedback:", "Copy feedback", "dd-note-btn", "localStorage"):
        assert marker in screen, f"screen missing {marker}"
        assert marker not in printed, f"print leaked {marker}"


def test_feedback_yaml_format() -> None:
    out = feedback_yaml("controlm-ingestion-tdd", {"traceability-matrix": "row FR-CMI-003 is wrong\ncheck stage 1", "hitl-gate": ""})
    assert out == (
        "# design-doc feedback — paste into docs/design/feedback/controlm-ingestion-tdd-rev<N>.yaml\n"
        "doc: controlm-ingestion-tdd\n"
        "notes:\n"
        "  - anchor: traceability-matrix\n"
        "    note: |\n"
        "      row FR-CMI-003 is wrong\n"
        "      check stage 1\n"
    )  # empty hitl-gate note is skipped


def test_write_doc_uses_stem_as_doc_id(tmp_path) -> None:
    src = tmp_path / "runbook-startup.md"
    src.write_text("# Runbook\n\n<!-- anchor: startup -->\n## Startup\ngo", encoding="utf-8")
    html_path, _ = write_doc(src)
    # the doc id is embedded as the JS DOC constant (localStorage key is built from it at runtime)
    assert 'var DOC="runbook-startup"' in html_path.read_text(encoding="utf-8")


def test_write_doc_emits_both_surfaces(tmp_path) -> None:
    src = tmp_path / "sample.md"
    src.write_text("# Sample\n\n<!-- anchor: purpose-scope -->\n## Purpose\ntext", encoding="utf-8")
    html_path, print_path = write_doc(src)
    assert html_path.name == "sample.html" and print_path.name == "sample.print.html"
    assert 'id="purpose-scope"' in html_path.read_text(encoding="utf-8")
    assert "@page" in print_path.read_text(encoding="utf-8")  # print CSS present


# ── L6: print-margin anchors + Rev/commit footer ────────────────────────────
def test_margin_anchor_tag_print_only() -> None:
    md = "# Doc\n\n<!-- anchor: purpose-scope -->\n## Purpose\ntext"
    printed = render_doc(md, "print")
    screen = render_doc(md, "screen")
    assert '<h2 id="purpose-scope"><span class="dd-margin-tag" aria-hidden="true">purpose-scope</span>Purpose</h2>' in printed
    assert "dd-margin-tag" not in screen  # the digital surface carries no gutter tags


def test_margin_anchor_skips_hr() -> None:
    # hr is a void element (can't hold a child span) — no anchor in practice attaches to
    # one, but the injector must not choke or misplace a tag if it ever did.
    md = "<!-- anchor: mid-break -->\n---\n"
    printed = render_doc(md, "print")
    assert '<hr id="mid-break">' in printed
    assert '<span class="dd-margin-tag"' not in printed


def test_rev_footer_print_only() -> None:
    md = "# Doc\n\ntext"
    printed = render_doc(md, "print")
    screen = render_doc(md, "screen")
    assert '<footer class="dd-print-footer">' in printed
    assert "dd-print-footer" not in screen


def test_rev_footer_reads_declared_rev_and_commit() -> None:
    md = "**Status:** DESCRIPTIVE — **Rev 7, 2026-01-01** (reflects commit `abc1234`)"
    assert doc_rev_footer(md) == "Rev 7 · commit abc1234"


def test_rev_footer_placeholder_when_undeclared() -> None:
    # a doc with no declared Rev/commit still gets a footer — the fixed placeholder,
    # never blank, and never derived from git state or a render timestamp.
    assert doc_rev_footer("# Doc\n\nno rev mentioned here") == "Rev — · commit —"


def test_rev_footer_matches_real_tdd() -> None:
    md = CONTROLM_TDD.read_text(encoding="utf-8")
    assert doc_rev_footer(md) == "Rev 3 · commit 107581d"


def test_print_render_is_still_deterministic_with_margins_and_footer() -> None:
    md = CONTROLM_TDD.read_text(encoding="utf-8")
    assert render_doc(md, "print") == render_doc(md, "print")


# ── L10: the appendix "SME - Feedback" instruction panel ─────────────────────
def test_sme_feedback_panel_screen_only_with_exact_filename() -> None:
    md = "# Doc\n\n**Rev 7, 2026-01-01**\n\n<!-- anchor: purpose-scope -->\n## Purpose\ntext"
    screen = render_doc(md, "screen", doc_id="mydoc")
    printed = render_doc(md, "print", doc_id="mydoc")
    assert "SME - Feedback" in screen
    assert "<code>docs/design/feedback/</code>" in screen
    assert "<code>mydoc-rev7.yaml</code>" in screen  # exact per-doc filename, Rev baked in
    assert "not</em> markdown" in screen             # the "is it markdown?" answer
    assert "SME - Feedback" not in printed
    assert "dd-sme-feedback" not in printed


def test_sme_feedback_filename_placeholder_without_rev() -> None:
    assert sme_feedback_filename("mydoc", "# Doc\n\nno rev here") == "mydoc-rev<N>.yaml"


def test_sme_panel_steps_carry_no_ids() -> None:
    # the panel's own <ol> must never grow annotate controls: no ids inside the section
    md = "# Doc\n\n<!-- anchor: purpose-scope -->\n## Purpose\ntext"
    screen = render_doc(md, "screen", doc_id="mydoc")
    panel = screen.split('<section class="dd-sme-feedback"', 1)[1].split("</section>", 1)[0]
    assert ' id="' not in panel


# ── L11: derived subsection anchors ──────────────────────────────────────────
def test_three_subheadings_get_derived_ids_screen_only() -> None:
    md = (
        "# Doc\n\n<!-- anchor: detailed-design -->\n## Design\n\n"
        "### Stage one parse\ntext\n\n### Stage two resolve\ntext\n\n### Stage three load\ntext"
    )
    screen = render_doc(md, "screen", doc_id="d")
    printed = render_doc(md, "print", doc_id="d")
    for did in (
        "detailed-design--stage-one-parse",
        "detailed-design--stage-two-resolve",
        "detailed-design--stage-three-load",
    ):
        assert f'<h3 id="{did}">' in screen, f"missing derived id {did}"
        assert did not in printed  # print namespace stays authored-only


def test_two_subheadings_stay_unanchored() -> None:
    md = (
        "# Doc\n\n<!-- anchor: detailed-design -->\n## Design\n\n"
        "### Stage one\ntext\n\n### Stage two\ntext"
    )
    screen = render_doc(md, "screen", doc_id="d")
    assert "detailed-design--" not in screen


def test_numbered_steps_get_derived_ids() -> None:
    md = (
        "# Doc\n\n<!-- anchor: startup -->\n## Startup\n\n"
        "1. Pull the repo\n2. Start the container\n3. Run the loaders\n"
    )
    screen = render_doc(md, "screen", doc_id="d")
    printed = render_doc(md, "print", doc_id="d")
    assert '<li id="startup--pull-the-repo">' in screen
    assert '<li id="startup--start-the-container">' in screen
    assert '<li id="startup--run-the-loaders">' in screen
    assert "startup--" not in printed


def test_two_step_list_stays_unanchored() -> None:
    md = "# Doc\n\n<!-- anchor: startup -->\n## Startup\n\n1. Pull\n2. Start\n"
    assert "startup--" not in render_doc(md, "screen", doc_id="d")


def test_duplicate_subsection_text_dedupes_deterministically() -> None:
    md = (
        "# Doc\n\n<!-- anchor: sec -->\n## Sec\n\n"
        "### Review\ntext\n\n### Review\ntext\n\n### Review\ntext"
    )
    screen = render_doc(md, "screen", doc_id="d")
    for did in ("sec--review", "sec--review-2", "sec--review-3"):
        assert f'<h3 id="{did}">' in screen
    assert render_doc(md, "screen", doc_id="d") == screen  # still deterministic


def test_anchored_subheading_counts_toward_threshold_but_keeps_its_id() -> None:
    md = (
        "# Doc\n\n<!-- anchor: sec -->\n## Sec\n\n"
        "<!-- anchor: sec-own -->\n### Owned\ntext\n\n### Plain a\ntext\n\n### Plain b\ntext"
    )
    screen = render_doc(md, "screen", doc_id="d")
    assert '<h3 id="sec-own">' in screen           # authored id untouched
    assert '<h3 id="sec--plain-a">' in screen      # 3 subsections total → derive the rest
    assert '<h3 id="sec--plain-b">' in screen
