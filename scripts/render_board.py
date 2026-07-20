"""render_board.py — render docs/restructure/backlog.yaml to docs/plan/board.html.

Thin CLI entry point beside ``knowledge/depgraph-snapshots/snapshot.ps1`` (see backlog
item I2 / CLAUDE.md §0 session ritual) until the ``drydocs/cli.py`` entrypoint-boundary
TODO (MODULE_MAP.md) is resolved. Stdlib + ``drydocs.plan_board`` only.

Usage:
    python scripts/render_board.py
    python scripts/render_board.py --backlog path/to/backlog.yaml --out path/to/board.html
"""
from __future__ import annotations

import argparse
from pathlib import Path

from drydocs.plan_board import DEFAULT_BACKLOG_PATH, DEFAULT_BOARD_PATH, write_board


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backlog",
        type=Path,
        default=DEFAULT_BACKLOG_PATH,
        help="path to backlog.yaml (default: docs/restructure/backlog.yaml)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_BOARD_PATH,
        help="path to write the rendered board (default: docs/plan/board.html)",
    )
    args = parser.parse_args()

    out_path = write_board(args.backlog, args.out)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
