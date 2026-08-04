"""Deterministic HTML -> plain text. Pure, offline, no heuristics that vary.

Determinism is the whole point: the cleaned text is what gets hashed, and a
cleaner whose output drifts with library versions or dict ordering would make
every freshness comparison (ADR 0006 §4 — a sha256 change re-queues curation)
report phantom changes. So: stdlib ``HTMLParser``, no third-party HTML stack,
no "smart" content extraction.

SIBLING, NOT DUPLICATE. ``drydocs_core.docs.vendor_html`` converts a captured
page to MARKDOWN, preserving heading structure and links, because the
vendor-docs loader chunks on structure. This produces flat TEXT for corpora
that carry no structure worth keeping, and for hashing. Reach for that one
when the structure matters and this one when it does not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser

#: Elements whose CONTENT is never document text — markup that happens to sit
#: in the body. Dropped wholesale rather than stripped tag-by-tag.
_NON_CONTENT = frozenset({"script", "style", "noscript", "template", "svg"})

#: Elements that end a line of prose. Without these, "one.Two" comes out of
#: adjacent block elements and every downstream sentence split is wrong.
_BLOCK = frozenset(
    {
        "p", "div", "br", "li", "tr", "td", "th", "section", "article",
        "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "table",
    }
)  # fmt: skip

_MULTI_BLANK = re.compile(r"\n{3,}")
_TRAILING_WS = re.compile(r"[ \t]+\n")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")


@dataclass(frozen=True)
class CleanedDoc:
    """Text plus the two facts a caller needs to judge the cleaning."""

    text: str
    title: str
    #: How many non-content elements were dropped. Reported rather than
    #: silent: a page that "cleaned" to nothing because it was all script is a
    #: capture problem, and a zero here next to an empty text says so.
    dropped_elements: int


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title = ""
        self.dropped = 0
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:  # - stdlib signature
        if tag in _NON_CONTENT:
            self._skip_depth += 1
            self.dropped += 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._in_title = True
        elif tag in _BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _NON_CONTENT:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._in_title = False
        elif tag in _BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self.title += data
        else:
            self.parts.append(data)


def clean_html(raw: str | bytes, *, encoding: str = "utf-8") -> CleanedDoc:
    """HTML bytes or text -> :class:`CleanedDoc`.

    Decoding is ``errors="replace"``: a capture is evidence, and refusing to
    read a page because three bytes are mis-encoded loses the other 6 KB. The
    replacement characters survive into the text where a reader can see them,
    which is the honest outcome — silently dropping them would not be.
    """
    text = raw.decode(encoding, "replace") if isinstance(raw, bytes) else raw
    parser = _TextExtractor()
    parser.feed(text)
    parser.close()
    return CleanedDoc(
        text=normalize_whitespace("".join(parser.parts)),
        title=" ".join(parser.title.split()),
        dropped_elements=parser.dropped,
    )


def normalize_whitespace(text: str) -> str:
    """Collapse runs of space and blank lines; strip trailing space per line.

    Applied to every corpus regardless of connector, so the same document
    fetched over the web and read from a filedrop hashes identically.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    text = _MULTI_SPACE.sub(" ", text)
    text = _TRAILING_WS.sub("\n", text)
    text = _MULTI_BLANK.sub("\n\n", text)
    return "\n".join(line.strip() for line in text.split("\n")).strip()
