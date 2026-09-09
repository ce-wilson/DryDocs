"""Tests for drydocs.docgen.design_doc — the deterministic Markdown-subset renderer (Epic L / L3).

Unit tests exercise each block/inline construct on tiny fixtures; the final tests render the
REAL Control-M TDD and assert the anchors survive as element ids with no comment leakage.
"""

from __future__ import annotations

from pathlib import Path

from drydocs.docgen.design_doc import (
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
    assert render_doc(md) == render_doc(md)


def test_doc_title_from_h1() -> None:
    assert doc_title("# Technical Design — `x` chain\n\nbody") == "Technical Design — x chain"


# ── the real TDD ─────────────────────────────────────────────────────────────
def test_real_tdd_anchors_survive_no_leakage() -> None:
    md = CONTROLM_TDD.read_text(encoding="utf-8")
    html = render_doc(md)
    assert "<!-- anchor" not in html, "anchor comment leaked into the output"
    for anchor in ("front-matter", "traceability-matrix", "design-data-mapping", "hitl-gate"):
        assert f'id="{anchor}"' in html, f"missing id={anchor}"
    assert "<table>" in html and "<pre" in html  # the mapping tables + SQL blocks rendered


def test_feedback_layer_present_and_hidden_in_print() -> None:
    # L13: one surface — the annotate layer ships in the file but @media print hides it.
    md = "# Doc\n\n<!-- anchor: purpose-scope -->\n## Purpose\ntext"
    html = render_doc(md)
    for marker in ("drydocs-doc-feedback:", "Copy feedback", "dd-note-btn", "localStorage"):
        assert marker in html, f"missing {marker}"
    assert (
        "@media print { .dd-note-btn, .dd-note-box, .dd-fb-bar, .dd-toast, "
        ".dd-sme-feedback, .dd-sme-divider { display:none !important; } }"
    ) in html


def test_fb_bar_carries_prewritten_feedback_file_and_path() -> None:
    # The bottom-right toolbar bakes in the exact per-doc feedback filename (declared Rev
    # included) plus its docs/design/feedback/ path as click-to-copy lines, so the SME can
    # paste them straight into a create-file dialog.
    md = (
        "# Doc\n\n<!-- anchor: front-matter -->\n- **Status:** DRAFT **Rev 3, 2026-07-20**\n\n"
        "<!-- anchor: purpose-scope -->\n## Purpose\ntext"
    )
    html = render_doc(md)
    assert "__FBFILE__" not in html, "filename placeholder was not substituted"
    assert 'FILE="doc-rev3.yaml"' in html
    assert 'DIR="docs/design/feedback/"' in html
    assert "dd-fb-file" in html  # the two toolbar lines render from these constants


def test_feedback_yaml_format() -> None:
    out = feedback_yaml(
        "controlm-ingestion-tdd",
        {"traceability-matrix": "row FR-CMI-003 is wrong\ncheck stage 1", "hitl-gate": ""},
    )
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
    html_path = write_doc(src)
    # the doc id is embedded as the JS DOC constant (localStorage key is built from it at runtime)
    assert 'var DOC="runbook-startup"' in html_path.read_text(encoding="utf-8")


def test_write_doc_emits_single_surface(tmp_path) -> None:
    # L13: ONE file — the .print.html twin is retired and must never come back.
    src = tmp_path / "sample.md"
    src.write_text("# Sample\n\n<!-- anchor: purpose-scope -->\n## Purpose\ntext", encoding="utf-8")
    html_path = write_doc(src)
    assert html_path.name == "sample.html"
    assert not (tmp_path / "sample.print.html").exists()
    out = html_path.read_text(encoding="utf-8")
    assert 'id="purpose-scope"' in out
    assert "@page" in out and "@media print" in out  # the print sheet rides in the one file


# ── L6: print-margin anchors + Rev/commit footer ────────────────────────────
def test_margin_anchor_tag_in_gutter_hidden_on_screen() -> None:
    # L13: the tag ships in the one html; base CSS hides it, @media print positions it.
    md = "# Doc\n\n<!-- anchor: purpose-scope -->\n## Purpose\ntext"
    html = render_doc(md)
    assert (
        '<h2 id="purpose-scope"><span class="dd-margin-tag" aria-hidden="true">purpose-scope</span>Purpose</h2>'
        in html
    )
    assert ".dd-margin-tag, .dd-print-footer { display: none; }" in html  # screen default
    assert "@media print" in html  # the print block re-shows + positions the gutter tag


def test_margin_anchor_skips_hr() -> None:
    # hr is a void element (can't hold a child span) — no anchor in practice attaches to
    # one, but the injector must not choke or misplace a tag if it ever did.
    md = "<!-- anchor: mid-break -->\n---\n"
    html = render_doc(md)
    assert '<hr id="mid-break">' in html
    assert '<span class="dd-margin-tag"' not in html


def test_rev_footer_present_hidden_on_screen() -> None:
    md = "# Doc\n\ntext"
    html = render_doc(md)
    assert '<footer class="dd-print-footer">' in html
    assert ".dd-margin-tag, .dd-print-footer { display: none; }" in html


def test_rev_footer_reads_declared_rev_and_commit() -> None:
    md = "**Status:** DESCRIPTIVE — **Rev 7, 2026-01-01** (reflects commit `abc1234`)"
    assert doc_rev_footer(md) == "Rev 7 · commit abc1234"


def test_rev_footer_placeholder_when_undeclared() -> None:
    # a doc with no declared Rev/commit still gets a footer — the fixed placeholder,
    # never blank, and never derived from git state or a render timestamp.
    assert doc_rev_footer("# Doc\n\nno rev mentioned here") == "Rev — · commit —"


def test_rev_footer_matches_real_tdd() -> None:
    md = CONTROLM_TDD.read_text(encoding="utf-8")
    assert doc_rev_footer(md) == "Rev 5 · commit c1c3a0a"


def test_render_is_still_deterministic_with_margins_and_footer() -> None:
    md = CONTROLM_TDD.read_text(encoding="utf-8")
    assert render_doc(md) == render_doc(md)


# ── L10: the appendix "SME - Feedback" instruction panel ─────────────────────
def test_sme_feedback_panel_with_exact_filename() -> None:
    md = "# Doc\n\n**Rev 7, 2026-01-01**\n\n<!-- anchor: purpose-scope -->\n## Purpose\ntext"
    html = render_doc(md, doc_id="mydoc")
    assert "SME - Feedback" in html
    assert "<code>docs/design/feedback/</code>" in html
    assert "<code>mydoc-rev7.yaml</code>" in html  # exact per-doc filename, Rev baked in
    assert "not</em> markdown" in html  # the "is it markdown?" answer
    # print-hidden, not print-absent (L13 one-surface): the hide list covers the panel
    assert ".dd-sme-feedback, .dd-sme-divider { display:none !important; }" in html


def test_sme_feedback_filename_placeholder_without_rev() -> None:
    assert sme_feedback_filename("mydoc", "# Doc\n\nno rev here") == "mydoc-rev<N>.yaml"


def test_sme_panel_steps_carry_no_ids() -> None:
    # the panel's own <ol> must never grow annotate controls: no ids inside the section
    md = "# Doc\n\n<!-- anchor: purpose-scope -->\n## Purpose\ntext"
    html = render_doc(md, doc_id="mydoc")
    panel = html.split('<section class="dd-sme-feedback"', 1)[1].split("</section>", 1)[0]
    assert ' id="' not in panel


# ── L11: derived subsection anchors ──────────────────────────────────────────
def test_three_subheadings_get_derived_ids_no_gutter_tags() -> None:
    md = (
        "# Doc\n\n<!-- anchor: detailed-design -->\n## Design\n\n"
        "### Stage one parse\ntext\n\n### Stage two resolve\ntext\n\n### Stage three load\ntext"
    )
    html = render_doc(md, doc_id="d")
    for did in (
        "detailed-design--stage-one-parse",
        "detailed-design--stage-two-resolve",
        "detailed-design--stage-three-load",
    ):
        assert f'<h3 id="{did}">' in html, f"missing derived id {did}"
        # the printed gutter namespace stays authored-only: no margin tag on derived ids
        assert f'dd-margin-tag" aria-hidden="true">{did}</span>' not in html


def test_two_subheadings_stay_unanchored() -> None:
    md = (
        "# Doc\n\n<!-- anchor: detailed-design -->\n## Design\n\n"
        "### Stage one\ntext\n\n### Stage two\ntext"
    )
    assert "detailed-design--" not in render_doc(md, doc_id="d")


def test_numbered_steps_get_derived_ids() -> None:
    md = (
        "# Doc\n\n<!-- anchor: startup -->\n## Startup\n\n"
        "1. Pull the repo\n2. Start the container\n3. Run the loaders\n"
    )
    html = render_doc(md, doc_id="d")
    assert '<li id="startup--pull-the-repo">' in html
    assert '<li id="startup--start-the-container">' in html
    assert '<li id="startup--run-the-loaders">' in html
    assert 'dd-margin-tag" aria-hidden="true">startup--' not in html  # gutter stays authored-only


def test_two_step_list_stays_unanchored() -> None:
    md = "# Doc\n\n<!-- anchor: startup -->\n## Startup\n\n1. Pull\n2. Start\n"
    assert "startup--" not in render_doc(md, doc_id="d")


def test_duplicate_subsection_text_dedupes_deterministically() -> None:
    md = (
        "# Doc\n\n<!-- anchor: sec -->\n## Sec\n\n"
        "### Review\ntext\n\n### Review\ntext\n\n### Review\ntext"
    )
    html = render_doc(md, doc_id="d")
    for did in ("sec--review", "sec--review-2", "sec--review-3"):
        assert f'<h3 id="{did}">' in html
    assert render_doc(md, doc_id="d") == html  # still deterministic


def test_anchored_subheading_counts_toward_threshold_but_keeps_its_id() -> None:
    md = (
        "# Doc\n\n<!-- anchor: sec -->\n## Sec\n\n"
        "<!-- anchor: sec-own -->\n### Owned\ntext\n\n### Plain a\ntext\n\n### Plain b\ntext"
    )
    html = render_doc(md, doc_id="d")
    assert '<h3 id="sec-own">' in html  # authored id untouched
    assert '<h3 id="sec--plain-a">' in html  # 3 subsections total → derive the rest
    assert '<h3 id="sec--plain-b">' in html


def test_anchored_list_gets_gutter_tag_and_derived_li_ids() -> None:
    # L13 injection-order integration: margin tags land first (authored ol anchor), then
    # the L11 pass still finds the list and derives its top-level li ids.
    md = (
        "# Doc\n\n<!-- anchor: run-order -->\n"
        "1. Pull the repo\n2. Start the container\n3. Run the loaders\n"
    )
    html = render_doc(md, doc_id="d")
    assert (
        '<ol id="run-order"><span class="dd-margin-tag" aria-hidden="true">run-order</span>' in html
    )
    assert '<li id="run-order--start-the-container">' in html


# ---------------------------------------------------------------------------
# DOC9 — the committed pages, not only the renderer.
#
# Everything above this line pins render_doc's OUTPUT on fixtures. None of it
# opens a committed docs/design/*.html, so until now the only thing standing
# between an edited .md and a stale governed render was the session ritual in
# CLAUDE.md section 0 — a habit. Idea-111 records what a habit-only check is
# worth: CI ran red for a week while sessions pushed past it, because nothing
# local ever looked wrong. Lane B then committed four governed design renders on
# wip branches in 2026-09-07 and nothing in CI would have said either way. The
# board and the roadmap have had test_committed_roadmap_page_matches_its_sources
# since Y5; this is the same guard for the design docs.
# ---------------------------------------------------------------------------

DESIGN_DIR = REPO_ROOT / "docs" / "design"

#: The fix the assertion prints, verbatim from the session ritual (CLAUDE.md
#: section 0). The roadmap guard's shape: a drift guard names the command that
#: clears it, because the operator who hits it is usually not its author.
RENDER_COMMAND = "poetry run python scripts/render_design_doc.py docs/design/*.md"


def _fresh_page(md_path: Path) -> bytes:
    """The bytes write_doc would commit for ``md_path``, produced in memory.

    In memory, and safe to be in memory only because the next test pins it: this
    re-states write_doc's two choices — ``doc_id`` is the .md stem, and the file
    is written LF — so on its own it could drift from what the writer actually
    emits and this guard would happily compare against a shape nobody ships.
    ``test_the_in_memory_page_is_what_write_doc_commits`` holds the two to the
    same bytes, so the writer cannot move without breaking a test first.
    """
    return render_doc(md_path.read_text(encoding="utf-8"), doc_id=md_path.stem).encode("utf-8")


def _design_render_drift(directory: Path) -> list[str]:
    """Every stem in ``directory`` whose committed .html is not the current render.

    ALL of them, never just the first: a report that stops at the first stale doc
    sends the operator back for another round per document. A .md with no .html at
    all is drift too — the ritual renders ``docs/design/*.md`` as a set, so a
    missing page is a page nobody rendered, not a document that opted out.

    Sorted by ``p.name``, a str, and not by the Path: sorting Path objects is
    case-folded on Windows and case-sensitive on POSIX, which is the bug that held
    CI red for roughly 180 runs (test_render_determinism.py's opening note). A
    guard whose report order depends on the OS that ran it has no business
    reporting on cross-platform renders.
    """
    drift: list[str] = []
    for md in sorted(directory.glob("*.md"), key=lambda p: p.name):
        page = md.with_suffix(".html")
        expected = _fresh_page(md)
        if not page.exists():
            drift.append(f"{md.stem}: no committed .html beside the source")
        elif (committed := page.read_bytes()) == expected:
            continue
        elif committed.replace(b"\r\n", b"\n") == expected:
            drift.append(f"{md.stem}: CR bytes only — a writer added them after checkout")
        else:
            drift.append(f"{md.stem}: {len(committed)} committed bytes, {len(expected)} rendered")
    return drift


def test_committed_design_pages_match_their_sources() -> None:
    """The stale-render check from the session ritual, as a test — and STRICT.

    BYTES, never a normalized or whitespace-tolerant form (clause b). Governed
    renders publish VERBATIM (CLAUDE.md section 6) because the HITL loop
    re-attaches L5 digital and L6 paper feedback by anchor, so a restyled copy —
    exactly what a whitespace-tolerant compare waves through — breaks
    re-attachment silently. The one difference this does not own is the CR byte:
    test_render_determinism.py::test_committed_surfaces_carry_no_cr_byte already
    covers docs/design/*.html for that. The report NAMES that case so a CRLF
    checkout cannot read as a restyle, which is diagnosis; tolerating it would be
    the normalization the clause forbids.

    STRICT, with the tolerance question settled here rather than left to whoever
    hits it first (clause c). Y5 relaxed the roadmap guard for status-only drift
    because the claim protocol REQUIRES an un-rendered push: a claim is a one-key
    edit of one item file, pushed before work starts, and it is the only channel
    between the two machines. A design doc has no equivalent one-key edit and no
    protocol that forces one. The case worth checking before committing to strict
    was a .md that changes only its ``Rev N`` line — and it turns out to be the
    strongest argument FOR strictness, not against it. The rev feeds
    ``sme_feedback_filename`` and the printed footer, so a stale page at a rev
    bump hands the SME paper whose margin tags and feedback filename name the
    PREVIOUS revision. Feedback attributed to the wrong rev is the precise failure
    the L5/L6 loop exists to prevent, which makes a rev-only edit the worst case
    for tolerance rather than the candidate for it.
    """
    drift = _design_render_drift(DESIGN_DIR)
    assert not drift, (
        "committed design render(s) do not match their .md source:\n  "
        + "\n  ".join(drift)
        + f"\nRe-run `{RENDER_COMMAND}` and commit the refresh. The .md is the source "
        "of truth and the .html is a deterministic render of it (Epic L / L13), so a "
        "page that differs is a page the ritual skipped — or one somebody edited by "
        "hand, which governed surfaces never tolerate."
    )


def test_the_in_memory_page_is_what_write_doc_commits(tmp_path: Path) -> None:
    """The pin that makes the in-memory comparison above legitimate.

    ``_fresh_page`` re-states write_doc's doc_id and newline choices. If the
    writer ever changes either, this fails and the guard is fixed before it can
    start passing against bytes the ritual would never produce. Driven on the real
    Control-M TDD rather than a fixture, because the shape that matters is the one
    that ships.
    """
    written = write_doc(CONTROLM_TDD, tmp_path)
    assert written.read_bytes() == _fresh_page(CONTROLM_TDD), (
        "write_doc no longer emits what render_doc(md, doc_id=stem) produces — "
        "test_committed_design_pages_match_their_sources is comparing against the "
        "wrong bytes until _fresh_page is brought back into line with the writer"
    )


def _fixture_doc(directory: Path, stem: str, rev: int = 1) -> Path:
    """A minimal but real design doc: title, declared rev, one anchored section."""
    md = directory / f"{stem}.md"
    md.write_text(
        f"# {stem.replace('-', ' ').title()}\n\n"
        f"**Rev {rev}** · commit `abc123`\n\n"
        "<!-- anchor: a-section -->\n## A section\n\ntext\n",
        encoding="utf-8",
        newline="\n",
    )
    return md


def test_the_guard_passes_on_a_fresh_page_and_fails_on_a_hand_edit(tmp_path: Path) -> None:
    """J76: the instrument gets a fixture — and the fixture proves the STRICT half.

    The hand edit is ONE trailing newline, deliberately the smallest edit a
    whitespace-tolerant comparison would wave through. A restyled ``<style>``
    block would fail any comparison at all and so would prove nothing about clause
    (b); this one fails only because the comparison is on bytes.
    """
    md = _fixture_doc(tmp_path, "fixture-doc")
    page = write_doc(md)
    assert _design_render_drift(tmp_path) == [], "a freshly rendered page must pass"

    page.write_bytes(page.read_bytes() + b"\n")
    drift = _design_render_drift(tmp_path)
    assert len(drift) == 1 and drift[0].startswith("fixture-doc:"), drift


def test_a_source_with_no_committed_page_is_drift_not_a_crash(tmp_path: Path) -> None:
    """A .md nobody rendered is the commonest way this guard earns its keep —
    a new design doc committed without running the ritual."""
    _fixture_doc(tmp_path, "never-rendered")
    assert _design_render_drift(tmp_path) == [
        "never-rendered: no committed .html beside the source"
    ]


def test_every_stale_stem_is_reported_not_only_the_first(tmp_path: Path) -> None:
    """Clause (a): all of them. One round of re-rendering, not one per document."""
    for stem in ("alpha-doc", "beta-doc", "gamma-doc"):
        write_doc(_fixture_doc(tmp_path, stem))
    (tmp_path / "alpha-doc.html").write_bytes(b"<!doctype html>\n<html>hand-written</html>\n")
    (tmp_path / "gamma-doc.html").unlink()

    drift = _design_render_drift(tmp_path)
    assert [d.split(":")[0] for d in drift] == ["alpha-doc", "gamma-doc"], drift


def test_a_rev_bump_alone_is_drift_because_the_tolerance_is_strict(tmp_path: Path) -> None:
    """The clause (c) ruling, executable. Changing only ``Rev 1`` to ``Rev 2``
    moves the printed footer and the SME feedback filename, so the committed page
    genuinely no longer matches its source — and this is the case the item asked
    to settle before committing to strict. Settled: it fails."""
    md = _fixture_doc(tmp_path, "rev-doc", rev=1)
    write_doc(md)
    assert _design_render_drift(tmp_path) == []

    _fixture_doc(tmp_path, "rev-doc", rev=2)
    assert _design_render_drift(tmp_path), (
        "a rev-only edit left the committed page passing — the footer and "
        "sme_feedback_filename both key on the rev, so this must be drift"
    )
