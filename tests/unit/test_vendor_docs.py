"""Guards for the standalone vendor-docs pipeline (backlog Q13).

Offline throughout: the Author-it HTML is a fixture, the capture manifest is
written to tmp_path, and nothing touches Neo4j.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from drydocs.loaders.vendor_docs import (
    ROLE_FALLBACK,
    VendorDocsAdapter,
    VendorDocsLoader,
    convert_capture,
    derive_page_role,
    split_chunks,
)
from drydocs_core.docs.vendor_html import html_to_markdown

CYPHER = Path(__file__).resolve().parents[2] / "drydocs" / "loaders" / "cypher" / "vendor_docs.cypher"

# Trimmed from a real captured topic: the isTOCLoaded shim, the Previous/Next
# icon strip, the topic heading rendered at h4 (depth, not importance), and the
# foot "Related Topics" block.
FIXTURE_HTML = """﻿<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html><head><meta charset="UTF-8" /><title> defjob XML file rules </title>
<script type="text/javascript">function isTOCLoaded() { location.href = "x"; return false; }</script>
</head>
<body onload="if (isTOCLoaded()) {expand('1');highlight('2')}">
<table class="relatedtopics aboveheading"><tr><td>
<p class="bodytext"><a href="7345.htm"><img alt="Previous Topic"></a></p></td>
<td><p class="bodytext"><a href="89957.htm"><img alt="Next Topic"></a></p></td></tr></table>
<h4 id="t16200" class="heading4">defjob XML file rules</h4>
<p class="bodytext">The defjob utility reads an XML file. See
<a class="jumptemplate" href="17196.htm">defjob XML file example</a>.</p>
<ul class="listbullet"><li class="listbullet">Tags are case sensitive.</li>
<li class="listbullet">Values are quoted.</li></ul>
<h5 class="heading5">Advanced usage</h5>
<p class="bodytext">Only for batch definitions.</p>
<table class="relatedtopics belowtopictext"><tr><td>
<h3 class="relatedheading">Related Topics</h3>
<p class="relateditem"><a href="16201.htm">defjob XML file parameters</a></p>
<p class="relateditem"><a href="3930.htm">exportdefjob</a></p></td></tr></table>
</body></html>"""


# --------------------------------------------------------------------------- #
# conversion
# --------------------------------------------------------------------------- #
def test_navigation_chrome_never_reaches_the_body():
    doc = html_to_markdown(FIXTURE_HTML)
    for chrome in ("Previous Topic", "Next Topic", "isTOCLoaded", "Related Topics", "location.href"):
        assert chrome not in doc.markdown, f"chrome leaked into body: {chrome}"


def test_heading_levels_are_normalized_not_trusted():
    """Author-it renders the title at a level reflecting TOC DEPTH.

    In the real capture the topic title appears as h1 once, h2 15x, h3 120x,
    h4 383x, h5 379x and h6 97x — so level cannot be read as importance. The
    first content heading becomes '#' and later ones '##' regardless of source
    level, which is also what makes split-on-H2 behave uniformly.
    """
    doc = html_to_markdown(FIXTURE_HTML)  # title is h4, section is h5
    assert doc.markdown.startswith("# defjob XML file rules")
    assert "\n## Advanced usage" in doc.markdown
    assert doc.headings == ["defjob XML file rules", "Advanced usage"]


def test_related_links_are_captured_as_data_not_body_text():
    doc = html_to_markdown(FIXTURE_HTML)
    assert [(r.text, r.href) for r in doc.related] == [
        ("defjob XML file parameters", "16201.htm"),
        ("exportdefjob", "3930.htm"),
    ]
    # ...and the foot block's link text must not appear as prose
    assert "defjob XML file parameters" not in doc.markdown


def test_inline_links_survive_with_their_href():
    """The href is the raw material for a future SEE_ALSO (Q14's gate)."""
    doc = html_to_markdown(FIXTURE_HTML)
    assert "[defjob XML file example](17196.htm)" in doc.markdown


def test_list_items_and_abstract():
    doc = html_to_markdown(FIXTURE_HTML)
    assert "- Tags are case sensitive." in doc.markdown
    assert doc.abstract.startswith("The defjob utility reads an XML file")
    assert not doc.abstract.startswith("#")


def test_page_with_no_heading_still_gets_a_title():
    doc = html_to_markdown("<html><head><title>Bare</title></head><body>"
                           "<p class='bodytext'>Body only.</p></body></html>")
    assert doc.markdown.startswith("# Bare")
    assert doc.abstract == "Body only."


# --------------------------------------------------------------------------- #
# page_role — explicit rules, and a REPORTED fallback rather than a silent one
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "title,expected",
    [
        ("defjob XML file examples", "examples"),
        ("Copy jobs XML file example", "examples"),
        ("defjob XML file parameters", "parameters"),
        ("defjob XML file rules", "rules"),
        ("Introduction to Utilities", "overview"),
        ("Utility reference table", ROLE_FALLBACK),
        ("ctmorder", ROLE_FALLBACK),
    ],
)
def test_derive_page_role(title, expected):
    assert derive_page_role(title) == expected


def test_examples_wins_over_parameters_when_a_title_has_both():
    """Ordering is load-bearing: 'XML file parameters for folders examples'
    is an examples page, and rule order is what decides that."""
    assert derive_page_role("updatedef XML file parameters examples") == "examples"


# --------------------------------------------------------------------------- #
# chunking
# --------------------------------------------------------------------------- #
def test_single_topic_page_is_one_chunk():
    seq = split_chunks("# Title\n\nbody text\n")
    assert len(seq) == 1
    assert seq[0][0] == 0 and seq[0][1] == "(topic)"


def test_section_heading_splits_into_a_second_chunk():
    seq = split_chunks("# Title\n\nintro\n\n## Section\n\nmore\n")
    assert [(s[0], s[1], s[2]) for s in seq] == [(0, "(topic)", 0), (1, "Section", 2)]
    assert "intro" in seq[0][3] and "more" in seq[1][3]


# --------------------------------------------------------------------------- #
# convert stage + adapter, end to end on a fake capture
# --------------------------------------------------------------------------- #
@pytest.fixture()
def fake_capture(tmp_path: Path) -> Path:
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "16200.htm").write_text(FIXTURE_HTML, encoding="utf-8")
    manifest = {
        "vendor": "BMC", "product": "Control-M", "version": "9.0.20",
        "book": "Utilities", "captured_at": "2026-07-31T14:43:32Z",
        "base_url": "https://example.invalid/",
        "pages": [
            {
                "url": "16200.htm", "page": "16200.htm", "anchor": None,
                "source_url": "https://example.invalid/16200.htm",
                "title": "defjob XML file rules",
                "breadcrumb": "Utilities > emdef utility for jobs",
                "toc_path": ["Utilities", "emdef utility for jobs"],
                "bytes": 10, "sha256": "abc123",
            },
            {  # a fragment node: same document, a section within it
                "url": "16200.htm#adv", "page": "16200.htm", "anchor": "adv",
                "source_url": "https://example.invalid/16200.htm#adv",
                "title": "Advanced usage",
                "breadcrumb": "Utilities > emdef utility for jobs > Advanced usage",
                "toc_path": ["Utilities", "emdef utility for jobs", "defjob XML file rules"],
                "bytes": 10, "sha256": "abc123",
            },
        ],
    }
    (tmp_path / "capture-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path


def test_convert_writes_markdown_and_manifest(fake_capture: Path):
    summary = convert_capture("fake", root=fake_capture)

    assert summary.documents == 1, "the fragment node must not create a second document"
    assert summary.toc_nodes == 2
    assert summary.roles == {"rules": 1}
    assert summary.related_links == 2

    manifest = json.loads((fake_capture / "convert-manifest.json").read_text(encoding="utf-8"))
    doc = manifest["documents"][0]
    assert doc["doc_id"] == "16200"
    assert doc["page_role"] == "rules"
    assert doc["source_url"] == "https://example.invalid/16200.htm", "fragment stripped"
    assert doc["sections"] == [
        {"anchor": "adv", "title": "Advanced usage",
         "breadcrumb": "Utilities > emdef utility for jobs > Advanced usage"}
    ]
    assert (fake_capture / "markdown" / "16200.md").exists()


def test_convert_is_idempotent(fake_capture: Path):
    first = convert_capture("fake", root=fake_capture)
    before = (fake_capture / "convert-manifest.json").read_text(encoding="utf-8")
    second = convert_capture("fake", root=fake_capture)
    assert (fake_capture / "convert-manifest.json").read_text(encoding="utf-8") == before
    assert (first.documents, first.roles) == (second.documents, second.roles)


def test_adapter_rows_validate_and_chain_chunks(fake_capture: Path):
    convert_capture("fake", root=fake_capture)
    with VendorDocsAdapter("fake", root=fake_capture) as adapter:
        rows = list(adapter.rows())

    assert len(rows) == 2, "one topic chunk + one section chunk"
    models = [VendorDocsLoader.row_model.model_validate(r) for r in rows]

    assert models[0].seq == 0 and models[0].prev_chunk_id is None
    assert models[1].prev_chunk_id == models[0].chunk_id, "NEXT_CHUNK order comes from Python"
    for m in models:
        assert m.trust == "VERBATIM"
        assert m.doc_version == "9.0.20"
        assert m.version_verified is False, "only a human may flip this (Q16)"
        assert m.toc_path[0] == "Utilities"


# --------------------------------------------------------------------------- #
# the taxonomy-only boundary
# --------------------------------------------------------------------------- #
def test_loader_wiring():
    assert VendorDocsLoader.cypher_path == CYPHER and CYPHER.exists()
    assert VendorDocsLoader.source_id == "bmc-controlm-utilities"
    assert VendorDocsLoader.source_label == "vendor-docs"


def test_cypher_writes_the_spine():
    cypher = CYPHER.read_text(encoding="utf-8")
    for token in (":Document", ":Chunk", ":DocSection", "PART_OF",
                  "FIRST_CHUNK", "NEXT_CHUNK", "IN_SECTION", "SUBSECTION_OF"):
        assert token in cypher, f"missing {token}"


def test_cypher_writes_NO_meaning_edges():
    """Q13 is taxonomy only. These belong to Q14's gate (and G32 for the
    estate join, since a relationship cannot span Neo4j databases)."""
    body = "\n".join(
        line for line in CYPHER.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("//")
    )
    for forbidden in (":ControlMUtility", "DESCRIBES", "SEE_ALSO", "DOCUMENTS", ":SoftwareProduct"):
        assert forbidden not in body, (
            f"{forbidden} is gate-bound and must not appear in the executable template"
        )
