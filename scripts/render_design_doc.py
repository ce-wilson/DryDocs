"""render_design_doc.py — render a design doc .md to its single .html (Epic L / L3).

Thin CLI beside ``scripts/render_board.py`` (and wired into the session-end ritual next to
``snapshot.ps1``) until the ``drydocs/cli.py`` entrypoint-boundary TODO is resolved. Stdlib
+ ``drydocs.docgen.design_doc`` only — the doc .md is the single source of truth; the one HTML
surface (screen + @media print, L13) is a deterministic render of it.

Usage:
    python scripts/render_design_doc.py docs/design/controlm-ingestion-tdd.md
    python scripts/render_design_doc.py docs/design/*.md            # several docs
    python scripts/render_design_doc.py docs/design/foo.md --out-dir build/
"""

from __future__ import annotations

import argparse
from pathlib import Path

from drydocs.docgen.design_doc import write_doc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docs", nargs="+", type=Path, help="design-doc .md file(s) to render")
    parser.add_argument(
        "--out-dir", type=Path, default=None, help="output dir (default: beside each .md)"
    )
    args = parser.parse_args()

    for md in args.docs:
        html_path = write_doc(md, args.out_dir)
        print(f"wrote {html_path}")


if __name__ == "__main__":
    main()
