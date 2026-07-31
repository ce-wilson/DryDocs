"""Author-it webhelp HTML -> markdown, for the external-vendor doc captures (Q13).

Stage 2 of the standalone vendor-docs pipeline (capture -> **convert** -> load).
Pure and offline: no network, no filesystem, no graph — one HTML string in, one
:class:`ConvertedDoc` out — so the whole conversion contract is unit-testable.

WHAT COUNTS AS CHROME
---------------------
BMC's Author-it webhelp wraps every topic in navigation furniture that is not
content and must not become chunk text:

* ``table.relatedtopics aboveheading`` — the Previous/Next/Contents/Index icon
  strip at the top of the page (398 occurrences in the Utilities capture).
* ``table.relatedtopics belowtopictext`` + its ``h3.relatedheading`` — the
  "Related Topics" block at the foot (990). Its LINKS are kept as
  :attr:`ConvertedDoc.related` because they are the vendor's own cross-references
  and the natural evidence for a future SEE_ALSO edge — but they are DATA here,
  never an edge. Q14's gate decides whether a vendor cross-link is an assertion
  we carry.
* ``<script>`` / ``<style>``, and the ``isTOCLoaded()`` redirect shim every page
  carries.

HEADING LEVELS ARE NOT SEMANTIC
-------------------------------
Author-it renders a topic's own title at a level reflecting its DEPTH IN THE
TOC, not its importance: across the 1,016-page capture the title appears as
``h1.heading1`` once, ``h2.heading2`` 15 times, ``h3.heading3`` 120,
``h4.heading4`` 383, ``h5.heading5`` 379 and ``h6.heading6`` 97. Reading level
as meaning would produce nonsense chunking, so levels are NORMALIZED: the
topic's first content heading becomes ``#`` and every later one ``##``. That
also makes the established "split on H2" chunking contract behave uniformly
across a corpus where 993 of 1,016 pages carry exactly one heading.
"""
from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

#: Author-it class markers.
_CHROME_TABLE_MARKER = "relatedtopics"
_RELATED_FOOT_MARKER = "belowtopictext"
_HEADING_CLASS_RE = re.compile(r"heading[1-6]")

_BLOCK_TAGS = {"p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol", "pre"}


@dataclass
class RelatedLink:
    """A vendor cross-reference. Data for Q14's gate — never an edge here."""

    href: str
    text: str


@dataclass
class ConvertedDoc:
    title: str
    markdown: str
    related: list[RelatedLink] = field(default_factory=list)
    #: headings found, post-normalization, in document order
    headings: list[str] = field(default_factory=list)

    @property
    def abstract(self) -> str:
        """First real paragraph — the cheap triage signal for an agent.

        Deterministic by construction: the first non-empty line after the title
        that is not itself a heading, list item, or table row.
        """
        for line in self.markdown.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "-", "|", ">")):
                continue
            return stripped
        return ""


class _AuthorItParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._parts: list[str] = []
        self.related: list[RelatedLink] = []
        self.headings: list[str] = []

        self._skip_depth = 0          # inside script/style
        self._chrome_tables = 0       # nested depth inside a relatedtopics table
        self._in_foot_related = False # that table is the "Related Topics" block
        self._table_depth = 0
        self._in_title_tag = False

        self._heading: str | None = None   # normalized marker while inside a heading
        self._buf: list[str] = []
        self._href: str | None = None
        self._link_text: list[str] = []
        self._seen_heading = False

    # -- helpers ---------------------------------------------------------- #
    @property
    def _suppressed(self) -> bool:
        return self._skip_depth > 0 or self._chrome_tables > 0

    def _flush(self) -> None:
        text = re.sub(r"[ \t]+", " ", "".join(self._buf)).strip()
        self._buf.clear()
        if text:
            self._parts.append(text)

    # -- tags ------------------------------------------------------------- #
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k: (v or "") for k, v in attrs}
        cls = attr.get("class", "")

        if tag in ("script", "style"):
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title_tag = True
            return

        if tag == "table":
            self._table_depth += 1
            if _CHROME_TABLE_MARKER in cls or self._chrome_tables:
                self._chrome_tables += 1
                self._in_foot_related = self._in_foot_related or (_RELATED_FOOT_MARKER in cls)
                self._flush()
                return

        # Inside the foot "Related Topics" block we still want the links.
        if self._chrome_tables and tag == "a" and self._in_foot_related:
            self._href, self._link_text = attr.get("href"), []
            return
        if self._suppressed:
            return

        if tag in _BLOCK_TAGS:
            self._flush()

        if tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
            if _HEADING_CLASS_RE.fullmatch(cls):
                # Normalize: first content heading is the topic title (#),
                # every later one is a section (##).
                self._heading = "#" if not self._seen_heading else "##"
                self._seen_heading = True
        elif tag == "a":
            self._href, self._link_text = attr.get("href"), []
        elif tag == "li":
            self._buf.append("- ")
        elif tag == "br":
            self._buf.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag == "title":
            self._in_title_tag = False
            return

        if tag == "table":
            self._table_depth = max(0, self._table_depth - 1)
            if self._chrome_tables:
                self._chrome_tables -= 1
                if self._chrome_tables == 0:
                    self._in_foot_related = False
            return

        if tag == "a" and self._href is not None:
            text = "".join(self._link_text).strip()
            if self._chrome_tables and self._in_foot_related:
                if text:
                    self.related.append(RelatedLink(href=self._href, text=text))
            elif not self._suppressed and text:
                # Keep the href: it is the raw material for a future SEE_ALSO.
                self._buf.append(f"[{text}]({self._href})" if self._href else text)
            self._href, self._link_text = None, []
            return

        if self._suppressed:
            return

        if self._heading and tag.startswith("h") and len(tag) == 2:
            heading_text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            self._buf.clear()
            if heading_text:
                self._parts.append(f"{self._heading} {heading_text}")
                self.headings.append(heading_text)
            self._heading = None
            return

        if tag in _BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._in_title_tag:
            self.title += data
            return
        if self._href is not None and (not self._suppressed or self._in_foot_related):
            self._link_text.append(data)
            return
        if self._suppressed:
            return
        self._buf.append(data)

    # -- result ----------------------------------------------------------- #
    def result(self) -> str:
        self._flush()
        out: list[str] = []
        for part in self._parts:
            if out and out[-1] == part:
                continue  # Author-it repeats the title in the <title> and the heading
            out.append(part)
        return "\n\n".join(out).strip()


def html_to_markdown(raw: str | bytes) -> ConvertedDoc:
    """Convert one captured Author-it topic to markdown.

    Returns the normalized markdown, the topic title, and the vendor's own
    related-topic links (as data, not edges).
    """
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    raw = raw.lstrip("﻿")

    parser = _AuthorItParser()
    parser.feed(raw)
    parser.close()

    body = parser.result()
    title = _html.unescape(parser.title).strip()

    if parser.headings:
        title = title or parser.headings[0]
    if not body.startswith("#"):
        # 22 pages of the capture carry no content heading at all; give them
        # one so the chunker and the loader see a uniform shape.
        body = f"# {title}\n\n{body}".strip()

    return ConvertedDoc(
        title=title or "(untitled)",
        markdown=body,
        related=parser.related,
        headings=parser.headings,
    )
