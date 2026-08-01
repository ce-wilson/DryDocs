"""render_board.py — render docs/restructure/backlog.yaml to docs/plan/board.html.

Thin CLI entry point beside ``knowledge/depgraph-snapshots/snapshot.ps1`` (see backlog
item I2 / CLAUDE.md §0 session ritual) until the ``drydocs/cli.py`` entrypoint-boundary
TODO (MODULE_MAP.md) is resolved. Stdlib + ``drydocs.plan_board`` only.

A default-paths run ALSO refreshes ``web/src/generated/gates.json`` (J17),
``web/src/generated/enforcement-matrix.json`` (J20),
``web/src/generated/load-map.json`` (N4) and
``web/src/generated/software-registry.json`` (+ its ``web/public/vendor-icons/``
assets — the software-registry <-> drydocs-icons soft link, 2026-07-31): all
read sources this ritual edits
(backlog item text; the gate-prompts tree; the source registry + N3 loader
declarations), so a groom, gate-prompt add or loader change would otherwise
silently drift them past their guards (``test_gates_json.py`` /
``test_enforcement_matrix.py`` / ``test_load_map_json.py`` — the J20
incident: a gate-prompt commit regenerated gates.json but not the matrix).
One command refreshes all four; an explicit ``--backlog``/``--out`` run
(tests, previews) renders the board only.

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

    if args.backlog == DEFAULT_BACKLOG_PATH and args.out == DEFAULT_BOARD_PATH:
        import render_enforcement_matrix
        import render_gates
        import render_load_map
        import render_software_registry

        render_gates.main()
        render_enforcement_matrix.main()
        render_load_map.main()
        render_software_registry.main()


if __name__ == "__main__":
    main()
