"""render_ideas.py — render docs/restructure/IDEAS.md to docs/plan/ideas.html.

Sibling of ``render_board.py``; a default-paths ``render_board.py`` run calls this
too, so the ritual stays one command. Stdlib + ``drydocs.docgen.plan_ideas`` only.

Usage:
    python scripts/render_ideas.py
    python scripts/render_ideas.py --ideas path/to/IDEAS.md --out path/to/ideas.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

from drydocs.docgen.plan_ideas import DEFAULT_IDEAS_OUT_PATH, DEFAULT_IDEAS_PATH, write_ideas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ideas", type=Path, default=DEFAULT_IDEAS_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_IDEAS_OUT_PATH)
    args = parser.parse_args()
    print(f"wrote {write_ideas(args.ideas, args.out)}")


if __name__ == "__main__":
    main()
