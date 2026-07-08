"""Tests for drydocs.design_doc — the deterministic Markdown-subset renderer (Epic L / L3).

Unit tests exercise each block/inline construct on tiny fixtures; the final tests render the
REAL Control-M TDD and assert the anchors survive as element ids with no comment leakage.
"""
from __future__ import annotations

from pathlib import Path

from drydocs.design_doc import doc_title, render_body, render_doc, write_doc

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


def test_write_doc_emits_both_surfaces(tmp_path) -> None:
    src = tmp_path / "sample.md"
    src.write_text("# Sample\n\n<!-- anchor: purpose-scope -->\n## Purpose\ntext", encoding="utf-8")
    html_path, print_path = write_doc(src)
    assert html_path.name == "sample.html" and print_path.name == "sample.print.html"
    assert 'id="purpose-scope"' in html_path.read_text(encoding="utf-8")
    assert "@page" in print_path.read_text(encoding="utf-8")  # print CSS present
