"""extract_office_text.py — readable-text twins for binary office docs (C10).

Converts .pdf / .docx / .pptx files to plain .txt so agents can grep and read
them without binary parsing. Deterministic and offline: docx/pptx are zip+XML
(stdlib only); pdf goes through pypdf (already a project dependency).

The OUTPUT sits beside the binaries (default: an extracted/ sibling directory)
and inherits their classification — for gitignored vendor corpora the text
twins stay local too (the BMC poster rule: "the summaries are ours, the vendor
binary is not"; a verbatim text dump is the vendor's words, not a summary).

Usage:
    poetry run python scripts/extract_office_text.py external/ServiceNow
    poetry run python scripts/extract_office_text.py <dir> --out-dir <dir>/extracted
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def docx_text(path: Path) -> str:
    """Paragraph text from word/document.xml (w:p → w:t runs)."""
    with zipfile.ZipFile(path) as zf:
        root = ElementTree.fromstring(zf.read("word/document.xml"))
    paras: list[str] = []
    for p in root.iter(f"{_W}p"):
        text = "".join(t.text or "" for t in p.iter(f"{_W}t"))
        paras.append(text)
    return "\n".join(paras)


def pptx_text(path: Path) -> str:
    """Slide-by-slide text (a:t runs), slides in numeric order, notes included."""
    out: list[str] = []
    with zipfile.ZipFile(path) as zf:

        def num(name: str) -> int:
            m = re.search(r"(\d+)\.xml$", name)
            return int(m.group(1)) if m else 0

        slides = sorted(
            (n for n in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)), key=num
        )
        notes = {
            num(n): n
            for n in zf.namelist()
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)
        }
        for name in slides:
            n = num(name)
            root = ElementTree.fromstring(zf.read(name))
            lines = [t.text for t in root.iter(f"{_A}t") if t.text and t.text.strip()]
            out.append(f"===== slide {n} =====")
            out.extend(lines)
            if n in notes:
                nroot = ElementTree.fromstring(zf.read(notes[n]))
                nlines = [t.text for t in nroot.iter(f"{_A}t") if t.text and t.text.strip()]
                if nlines:
                    out.append(f"----- notes {n} -----")
                    out.extend(nlines)
    return "\n".join(out)


def pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    out: list[str] = []
    for i, page in enumerate(reader.pages, start=1):
        out.append(f"===== page {i} =====")
        out.append(page.extract_text() or "")
    return "\n".join(out)


_EXTRACTORS = {".docx": docx_text, ".pptx": pptx_text, ".pdf": pdf_text}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Extract text twins from pdf/docx/pptx files.")
    ap.add_argument("src_dir", type=Path)
    ap.add_argument("--out-dir", type=Path, default=None, help="default: <src_dir>/extracted")
    args = ap.parse_args(argv)

    out_dir = args.out_dir or (args.src_dir / "extracted")
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        p for p in args.src_dir.iterdir() if p.is_file() and p.suffix.lower() in _EXTRACTORS
    )
    if not files:
        print(f"no extractable files in {args.src_dir}")
        return 1
    for f in files:
        text = _EXTRACTORS[f.suffix.lower()](f)
        target = out_dir / (f.name + ".txt")
        # J49: LF — extracted text is diffed against re-extractions; the tracked
        # SDLC-Docs/extracted/*.md predate this script and are not its output.
        target.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {target}  ({len(text):,} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
