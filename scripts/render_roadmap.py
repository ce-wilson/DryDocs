"""render_roadmap.py — render roadmap.yaml + backlog.yaml to docs/plan/roadmap.html.

Sibling of ``render_board.py``; a default-paths ``render_board.py`` run calls this
too, so the ritual stays one command. Stdlib + ``drydocs.plan_roadmap`` only.

Usage:
    python scripts/render_roadmap.py
    python scripts/render_roadmap.py --roadmap path/to/roadmap.yaml --out path/to/roadmap.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

from drydocs.plan_roadmap import (
    DEFAULT_ROADMAP_BACKLOG_PATH,
    DEFAULT_ROADMAP_OUT_PATH,
    DEFAULT_ROADMAP_PATH,
    write_roadmap,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roadmap", type=Path, default=DEFAULT_ROADMAP_PATH)
    parser.add_argument("--backlog", type=Path, default=DEFAULT_ROADMAP_BACKLOG_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_ROADMAP_OUT_PATH)
    args = parser.parse_args()
    print(f"wrote {write_roadmap(args.roadmap, args.backlog, args.out)}")


if __name__ == "__main__":
    main()
