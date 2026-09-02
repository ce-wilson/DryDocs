"""port_backlog_union.py — J42: fail the port report when a port dropped a backlog item.

Run this from the CONSUMER (company) repo, AFTER applying the port range and
BEFORE writing the port report. It reads the producer's backlog at the recorded
port base (a git ref — the ``port-base-YYYYMMDD`` tag, never ``HEAD``) and diffs
its item-id set against the tree the apply actually produced.

Usage, from the company checkout with the producer remote fetched:

    poetry run python scripts/port_backlog_union.py --producer-ref port-base-20260820

    # the producer ref lives on a remote that is not `origin` here:
    poetry run python scripts/port_backlog_union.py --producer-ref cewilson/main

Exit 0 = union holds (any ruled omissions are printed WITH their reasons, so an
accepted difference never reads like no difference at all). Exit 1 = the port
under-delivered, naming every missing id — paste the block into the port report.
Exit 2 = a side could not be read, which is a failure and never an empty set.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from drydocs.port.port_backlog_union import (
    BACKLOG_PATH,
    BacklogUnionError,
    run_union_check,
)
from drydocs.port.port_preflight import REPO_ROOT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--producer-ref",
        required=True,
        help="the RECORDED PORT BASE (a port-base-YYYYMMDD tag), never HEAD",
    )
    parser.add_argument(
        "--consumer-dir",
        default=None,
        help=f"the applied backlog tree (default: {BACKLOG_PATH} in this repo)",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="repo the producer ref is reachable from (default: this checkout)",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else REPO_ROOT
    consumer_dir = (
        Path(args.consumer_dir).resolve() if args.consumer_dir else REPO_ROOT / BACKLOG_PATH
    )

    with tempfile.TemporaryDirectory(prefix="drydocs-port-union-") as tmp:
        try:
            report = run_union_check(
                producer_ref=args.producer_ref,
                consumer_dir=consumer_dir,
                workdir=Path(tmp),
                repo=repo,
            )
        except BacklogUnionError as exc:
            print(f"BACKLOG UNION CHECK (J42) — COULD NOT RUN\n  {exc}", file=sys.stderr)
            return 2

    print(report.render())
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
