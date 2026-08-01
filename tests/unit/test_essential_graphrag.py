"""Tests for the Essential GraphRAG book-PDF lexical loader (Q2).

The splitter is exercised on SYNTHETIC page lists (the real PDF is
gitignored and machine-local); one live test runs against the real PDF when
present and skips otherwise.
"""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path

import pytest

from drydocs.loaders.base import _code_semicolons
from drydocs.loaders.essential_graphrag import (
    CHAPTER_TITLES,
    DEFAULT_PDF,
    EssentialGraphragAdapter,
    EssentialGraphragLoader,
    split_book,
)
from drydocs_core.models.docs import BookChunkRow

# --- synthetic mini-book -------------------------------------------------------
# Two chapters + appendix + index, with the three PDF-noise shapes the splitter
# must survive: a page-number-glued running head ("31.1 ..."), an in-prose
# decimal that looks like a heading ("2.4 GHz ..."), and a non-monotonic
# section number ("2.3 ..." where 2.2 is expected).

TITLES = {1: "Alpha", 2: "Beta"}
APPENDIX = "The Test environment"

PAGES = [
    "ESSENTIAL TESTBOOK\nby Nobody",  # p1  front matter
    "contents\n1.1 Alpha One 2\n2.1 Beta One 9",  # p2  TOC (never scanned)
    "1\nAlpha\nThis chapter covers\nintro line",  # p3  ch1 opener
    "31.1 Alpha One\n1.1 Alpha One\nbody a\n2.4 GHz clock",  # p4  running head + real 1.1 + decimal trap
    "1.2 Alpha Two\nbody b",  # p5
    "2\nBeta\nThis chapter covers\nbeta intro",  # p6  ch2 opener
    "2.1 Beta One\nbody c\n2.3 Skipped Nonmono\nmore c",  # p7  2.3 rejected (2.2 expected)
    "appendix\nThe Test environment\nA.1 Appx One\nappx body\nA.2.1 Nested stays\nA.2 Appx Two\nx",  # p8
    "index\nalpha 3\nbeta 7",  # p9  back matter
]


def _chunks():
    return split_book(PAGES, chapter_titles=TITLES, appendix_title=APPENDIX)


def test_chunk_sequence_headings_and_levels():
    got = [(c.heading, c.level, c.section, c.page_start) for c in _chunks()]
    assert got == [
        ("(front matter)", 0, None, 1),
        ("1 Alpha", 1, None, 3),
        ("1.1 Alpha One", 2, "1.1", 4),
        ("1.2 Alpha Two", 2, "1.2", 5),
        ("2 Beta", 1, None, 6),
        ("2.1 Beta One", 2, "2.1", 7),
        ("appendix The Test environment", 1, None, 8),
        ("A.1 Appx One", 2, "A.1", 8),
        ("A.2 Appx Two", 2, "A.2", 8),
        ("(back matter)", 0, None, 9),
    ]


def test_running_head_stays_in_chapter_preamble():
    ch1 = next(c for c in _chunks() if c.heading == "1 Alpha")
    assert "31.1 Alpha One" in ch1.text  # glued page number => not a boundary


def test_decimal_and_nonmonotonic_lines_are_not_boundaries():
    s11 = next(c for c in _chunks() if c.section == "1.1")
    assert "2.4 GHz clock" in s11.text  # wrong chapter for region 1
    s21 = next(c for c in _chunks() if c.section == "2.1")
    assert "2.3 Skipped Nonmono" in s21.text  # 2.2 expected => rejected


def test_appendix_subsection_stays_embedded():
    a1 = next(c for c in _chunks() if c.section == "A.1")
    assert "A.2.1 Nested stays" in a1.text


def test_chapter_count_mismatch_fails_loud():
    with pytest.raises(ValueError, match="expected 3"):
        split_book(PAGES, chapter_titles={**TITLES, 3: "Gamma"}, appendix_title=APPENDIX)


def test_adapter_rows_denormalize_and_chain():
    adapter = EssentialGraphragAdapter(
        Path("Essential-GraphRAG.pdf"),
        pages=PAGES,
        chapter_titles=TITLES,
        appendix_title=APPENDIX,
    )
    rows = list(adapter.rows())
    assert len(rows) == 10
    assert rows[0]["prev_chunk_id"] is None
    for prev, row in pairwise(rows):
        assert row["prev_chunk_id"] == prev["chunk_id"]
    seqs = [r["seq"] for r in rows]
    assert seqs == list(range(10))
    # every row validates through the loader's model
    for row in rows:
        model = BookChunkRow.model_validate(row)
        assert model.provenance == "GROUNDED"
        assert model.tier_rule == "pdf-extract-grounded-v1"
        assert model.doc_id == "essential-graphrag"


def test_loader_cypher_is_single_statement():
    cypher = EssentialGraphragLoader.cypher_path.read_text(encoding="utf-8")
    # single code ';' => BaseLoader dispatches plain run(), never runMany
    assert _code_semicolons(cypher) == 1
    # the DESCRIBES hook must not exist as a written edge (deliberately omitted)
    assert "MERGE (doc)-[d:DESCRIBES" not in cypher


@pytest.mark.skipif(not DEFAULT_PDF.exists(), reason="local gitignored PDF absent")
def test_real_pdf_splits_cleanly():
    from drydocs.loaders.essential_graphrag import extract_pages

    pages = extract_pages(DEFAULT_PDF)
    assert len(pages) == 179
    chunks = split_book(pages)
    headings = [c.heading for c in chunks]
    assert headings[0] == "(front matter)"
    assert headings[-1] == "(back matter)"
    # all 8 chapter preambles present, in order
    preambles = [c for c in chunks if c.level == 1 and c.chapter]
    assert [c.chapter for c in preambles] == list(range(1, 9))
    # every declared chapter got at least one section chunk
    for ch in CHAPTER_TITLES:
        assert any(c.chapter == ch and c.level == 2 for c in chunks), ch
    # appendix sections A.1..A.4 all found
    assert [c.section for c in chunks if c.section and c.section.startswith("A.")] == [
        "A.1",
        "A.2",
        "A.3",
        "A.4",
    ]
    # sections within each chapter are monotonic
    by_ch: dict[int, list[int]] = {}
    for c in chunks:
        if c.level == 2 and c.chapter and c.section:
            by_ch.setdefault(c.chapter, []).append(int(c.section.split(".")[1]))
    for ch, secs in by_ch.items():
        assert secs == list(range(1, len(secs) + 1)), (ch, secs)
