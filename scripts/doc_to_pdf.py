"""doc_to_pdf.py — render a design doc's .print.html to .pdf (Epic L / L4).

Thin CLI over ``drydocs.doc_pdf``. Uses a headless Chromium-family browser (Brave first,
then Chrome / Edge) with fixed flags, and normalizes the PDF dates so re-runs are
structurally identical. The blank PDF is build-on-demand (PUBLISH-BOUNDARY) — regenerate
before printing for the pen/paper loop.

Usage:
    python scripts/doc_to_pdf.py docs/design/controlm-ingestion-tdd.print.html
    python scripts/doc_to_pdf.py docs/design/foo.print.html --out build/foo.pdf --browser "C:/.../brave.exe"
"""
from __future__ import annotations

import argparse
from pathlib import Path

from drydocs.doc_pdf import find_browser, html_to_pdf


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", type=Path, help="the .print.html to convert")
    ap.add_argument("--out", type=Path, default=None, help="output .pdf (default: <stem>.pdf)")
    ap.add_argument("--browser", type=Path, default=None, help="browser exe (default: Brave/Chrome/Edge)")
    args = ap.parse_args()

    if args.browser is None and find_browser() is None:
        print("no headless Chromium-family browser found (Brave / Chrome / Edge); "
              "install one or pass --browser")
        return 2
    pdf = html_to_pdf(args.html, args.out, args.browser)
    print(f"wrote {pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
