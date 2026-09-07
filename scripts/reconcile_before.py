"""reconcile_before.py — reconcile-port step 1 as ONE call, stamped with the sha it describes.

Run this from the CONSUMER (company) repo, on a clean checkout, BEFORE applying the
port range. It writes every before-snapshot the per-entry guards read
(``tests/unit/test_port_reconcile_guards.py``) into one directory, plus ``BASE.sha``
— the commit the tree was at — which those guards then refuse to run without.

    poetry run python scripts/reconcile_before.py "$env:TEMP/reconcile-before"

    # the line the PORT-REPORT carries — sha, date, commits behind HEAD:
    poetry run python scripts/reconcile_before.py --describe "$env:TEMP/reconcile-before"

Exit 0 = written (or described). Exit 2 = refused — a source has uncommitted
changes, or the directory is not inside a git checkout — and NOTHING was written:
a stamp over an uncommitted edit would name a commit the snapshot is not.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from drydocs.port.port_preflight import REPO_ROOT
from drydocs.port.reconcile_before import (
    ReconcileBeforeError,
    describe,
    write_snapshot,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before_dir", help="the RECONCILE_BEFORE_DIR to write (or describe)")
    parser.add_argument(
        "--describe",
        action="store_true",
        help="print the one-line PORT-REPORT description of an existing before-dir",
    )
    parser.add_argument(
        "--repo",
        default=str(REPO_ROOT),
        help="the consumer checkout to snapshot (default: the checkout containing the cwd)",
    )
    args = parser.parse_args()
    before_dir = Path(args.before_dir)
    repo = Path(args.repo)
    if args.describe:
        print(describe(before_dir, repo))
        return 0
    try:
        report = write_snapshot(before_dir, repo)
    except ReconcileBeforeError as exc:
        print(f"reconcile_before: REFUSED - {exc}", file=sys.stderr)
        return 2
    print("\n".join(report.lines()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
