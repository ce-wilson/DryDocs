"""EssentialGraphragAdapter / EssentialGraphragLoader — book-PDF lexical loader (Q2).

Loads the *Essential GraphRAG* ebook (Bratanič & Hane, Manning 2025 — the
local PDF is gitignored; cite ``source_url``) as a Document -> Chunk lexical
graph, reusing the ACTIVE ``docs_*`` vocabulary the ``bmc-docs-lexical-load``
gate confirmed (2026-07-08). Chunk-only, NO LLM extraction, NO embeddings,
fully deterministic — the Q2 experiment corpus for agent-traversal testing.

Chunking rule (``pdf-lexical-v1``), driven by the book's own structure:

- seq 0 ``(front matter)`` — everything before chapter 1's opening page.
- A chapter starts at the PAGE containing the Manning opener phrase
  ``"This chapter covers"`` (exactly one per chapter — the count is asserted).
  The chapter-opening text up to its first section heading is a level-1
  preamble chunk headed ``"<n> <chapter title>"``.
- Section chunks (level 2) split at heading lines matching ``<c>.<s> Title``
  accepted ONLY in monotonic order (chapter must match the current chapter,
  section must be the next expected number). This rejects the two PDF-noise
  shapes: running heads (the page number is glued to the section number, e.g.
  ``"373.2 Parent document retriever"``) and in-prose decimals (``"2.4 GHz"``
  fails the monotonic check; TOC lines live in the front matter, which is
  never scanned).
- The appendix starts at the page whose stripped line is exactly
  ``"appendix"``; its ``A.<n>`` sections split the same way (``A.2.1``-style
  sub-sections stay embedded, like H3s in the bmc-docs loader).
- ``(back matter)`` starts at the page whose stripped line is exactly
  ``"index"`` (after the appendix) and runs to EOF.

Every chunk is tier GROUNDED (``pdf-extract-grounded-v1``): pypdf extraction
is mechanical but lossy (ligature drops, intra-word splits), so the text is a
faithful derivation of the published book, not byte-VERBATIM.
"""
from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

from drydocs_core.models.docs import BookChunkRow

from .base import BaseLoader, compute_row_checksum

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

REPO_ROOT = Path(__file__).resolve().parents[2]
CYPHER_DIR = Path(__file__).resolve().parent / "cypher"
DEFAULT_PDF = REPO_ROOT / "Essential-GraphRAG.pdf"

DOC_ID = "essential-graphrag"
TITLE = "Essential GraphRAG: Knowledge Graph-Enhanced RAG"
AUTHORS = "Tomaž Bratanič, Oskar Hane"
PUBLISHER = "Manning"
PUBLISHED = "2025-07"
SOURCE_URL = "https://www.manning.com/books/essential-graphrag"
CLASSIFICATION = "External"
TRUST_DEFAULT = "GROUNDED"
TIER_RULE_ID = "pdf-extract-grounded-v1"

CHAPTER_TITLES: dict[int, str] = {
    1: "Improving LLM accuracy",
    2: "Vector similarity search and hybrid search",
    3: "Advanced vector retrieval strategies",
    4: "Generating Cypher queries from natural language questions",
    5: "Agentic RAG",
    6: "Constructing knowledge graphs with LLMs",
    7: "Microsoft's GraphRAG implementation",
    8: "RAG application evaluation",
}
APPENDIX_TITLE = "The Neo4j environment"

_CHAPTER_OPENER = "This chapter covers"
_APPENDIX_LINE = "appendix"
_INDEX_LINE = "index"

# Chapter is a SINGLE digit — a running head glues the page number onto the
# section number ("373.2 ..."), so its first two chars are never "<digit>.".
_SECTION_RE = re.compile(r"^([1-9])\.(\d{1,2})\s+[A-Z(]")
_APPENDIX_SECTION_RE = re.compile(r"^A\.(\d)\s+[A-Z(]")


@dataclass
class _RawChunk:
    heading: str
    level: int
    chapter: int | None
    section: str | None
    page_start: int
    lines: list[str]

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def split_book(
    pages: Sequence[str],
    *,
    chapter_titles: Mapping[int, str] = CHAPTER_TITLES,
    appendix_title: str | None = APPENDIX_TITLE,
) -> list[_RawChunk]:
    """Deterministically split per-page extracted text into lexical chunks.

    ``pages`` is the 0-indexed list of per-PDF-page texts (page 1 first).
    Raises ``ValueError`` if the chapter-opener count does not match
    ``chapter_titles`` — fail loud, never mis-chunk silently.
    """
    n_chapters = len(chapter_titles)
    chapter_start_pages = [
        i for i, text in enumerate(pages) if _CHAPTER_OPENER in text
    ]
    if len(chapter_start_pages) != n_chapters:
        raise ValueError(
            f"expected {n_chapters} '{_CHAPTER_OPENER}' pages, "
            f"found {len(chapter_start_pages)} — chunking rule pdf-lexical-v1 "
            "does not fit this PDF"
        )

    def _page_with_line(needle: str, from_page: int) -> int | None:
        for i in range(from_page, len(pages)):
            if any(ln.strip() == needle for ln in pages[i].splitlines()):
                return i
        return None

    appendix_page = (
        _page_with_line(_APPENDIX_LINE, chapter_start_pages[-1] + 1)
        if appendix_title is not None
        else None
    )
    index_page = _page_with_line(
        _INDEX_LINE,
        (appendix_page if appendix_page is not None else chapter_start_pages[-1]) + 1,
    )

    chunks: list[_RawChunk] = []

    def _flat(lo_page: int, hi_page: int) -> list[tuple[int, str]]:
        """(1-based page number, line) pairs for pages[lo_page:hi_page]."""
        out: list[tuple[int, str]] = []
        for p in range(lo_page, hi_page):
            out.extend((p + 1, ln) for ln in pages[p].splitlines())
        return out

    # -- front matter ---------------------------------------------------------
    if chapter_start_pages[0] > 0:
        chunks.append(
            _RawChunk(
                heading="(front matter)", level=0, chapter=None, section=None,
                page_start=1,
                lines=[ln for _, ln in _flat(0, chapter_start_pages[0])],
            )
        )

    # -- chapters + numbered sections (monotonic scan) ------------------------
    def _split_region(
        flat: list[tuple[int, str]],
        preamble: _RawChunk,
        boundary: re.Pattern[str],
        accept: callable,
        section_of: callable,
    ) -> None:
        current = preamble
        expected = 1
        for page_no, line in flat:
            m = boundary.match(line)
            if m and accept(m, expected):
                chunks.append(current)
                current = _RawChunk(
                    heading=line.strip(), level=2,
                    chapter=preamble.chapter, section=section_of(m),
                    page_start=page_no, lines=[line],
                )
                expected += 1
                continue
            current.lines.append(line)
        chunks.append(current)

    region_ends = chapter_start_pages[1:] + [
        appendix_page if appendix_page is not None
        else (index_page if index_page is not None else len(pages))
    ]
    for c, (start, end) in enumerate(zip(chapter_start_pages, region_ends, strict=False), 1):
        flat = _flat(start, end)
        preamble = _RawChunk(
            heading=f"{c} {chapter_titles[c]}", level=1, chapter=c,
            section=None, page_start=start + 1, lines=[],
        )
        _split_region(
            flat, preamble, _SECTION_RE,
            accept=lambda m, exp, _c=c: int(m.group(1)) == _c and int(m.group(2)) == exp,
            section_of=lambda m: f"{m.group(1)}.{m.group(2)}",
        )

    # -- appendix -------------------------------------------------------------
    if appendix_page is not None:
        app_end = index_page if index_page is not None else len(pages)
        flat = _flat(appendix_page, app_end)
        preamble = _RawChunk(
            heading=f"appendix {appendix_title}", level=1, chapter=None,
            section=None, page_start=appendix_page + 1, lines=[],
        )
        _split_region(
            flat, preamble, _APPENDIX_SECTION_RE,
            accept=lambda m, exp: int(m.group(1)) == exp,
            section_of=lambda m: f"A.{m.group(1)}",
        )

    # -- back matter -----------------------------------------------------------
    if index_page is not None:
        chunks.append(
            _RawChunk(
                heading="(back matter)", level=0, chapter=None, section=None,
                page_start=index_page + 1,
                lines=[ln for _, ln in _flat(index_page, len(pages))],
            )
        )

    return [c for c in chunks if c.text.strip()]


def extract_pages(pdf_path: Path) -> list[str]:
    """Per-page text via pypdf (an existing project dependency)."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    return [page.extract_text() or "" for page in reader.pages]


class EssentialGraphragAdapter:
    """Yield one row per chunk of the book, doc fields denormalized.

    ``pages`` is injectable so unit tests exercise the splitter on synthetic
    page lists — the real (gitignored) PDF is only touched when ``pages`` is
    None, at ``rows()`` time.
    """

    name = "essential-graphrag"

    def __init__(
        self,
        pdf_path: Path | str = DEFAULT_PDF,
        *,
        pages: Sequence[str] | None = None,
        chapter_titles: Mapping[int, str] = CHAPTER_TITLES,
        appendix_title: str | None = APPENDIX_TITLE,
    ) -> None:
        self.pdf_path = Path(pdf_path)
        self._pages = pages
        self._chapter_titles = chapter_titles
        self._appendix_title = appendix_title

    def __enter__(self) -> EssentialGraphragAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        pages = self._pages if self._pages is not None else extract_pages(self.pdf_path)
        try:
            rel_path = self.pdf_path.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel_path = self.pdf_path.name
        prev_chunk_id: str | None = None
        raw_chunks = split_book(
            pages,
            chapter_titles=self._chapter_titles,
            appendix_title=self._appendix_title,
        )
        for seq, chunk in enumerate(raw_chunks):
            chunk_id = f"{DOC_ID}#{seq:03d}"
            yield {
                "doc_id": DOC_ID,
                "title": TITLE,
                "authors": AUTHORS,
                "publisher": PUBLISHER,
                "published": PUBLISHED,
                "source_url": SOURCE_URL,
                "path": rel_path,
                "trust_default": TRUST_DEFAULT,
                "classification": CLASSIFICATION,
                "chunk_id": chunk_id,
                "seq": seq,
                "heading": chunk.heading,
                "level": chunk.level,
                "text": chunk.text,
                "char_count": len(chunk.text),
                "provenance": TRUST_DEFAULT,
                "tier_rule": TIER_RULE_ID,
                "prev_chunk_id": prev_chunk_id,
                "chapter": chunk.chapter,
                "section": chunk.section,
                "page_start": chunk.page_start,
            }
            prev_chunk_id = chunk_id


class EssentialGraphragLoader(BaseLoader):
    name: ClassVar[str] = "essential_graphrag.v1"
    source_id: ClassVar[str | None] = "essential-graphrag"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "essential_graphrag.cypher"
    row_model: ClassVar[type] = BookChunkRow
    source_label: ClassVar[str] = "pdf"

    def to_params(self, model: BaseModel) -> dict:
        """Delta checksum over the full chunk row (the bmc_docs idiom)."""
        params = model.model_dump(mode="json")
        params["row_checksum"] = compute_row_checksum(params)
        return params
