"""port_preflight.py — J41: certify a producer base before handing it to a company session.

The port has carried a mandatory CLOSING sequence since J35 and nothing at the front.
This is the opening sequence, executable: the producer runs it, and only a clean
result may be offered as a port base.

Usage:
    python scripts/port_preflight.py --base 6f03264
    python scripts/port_preflight.py --base 6f03264 --tag        # certify and push
    python scripts/port_preflight.py --base 6f03264 --skip-tests # report only, never certifies
"""

from __future__ import annotations

import argparse
import datetime as _dt
import subprocess
import sys

from drydocs.port_preflight import REPO_ROOT, next_base_tag, run_checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="last ported producer head")
    parser.add_argument("--tag", action="store_true", help="create and push port-base-<date>")
    parser.add_argument("--skip-tests", action="store_true", help="skip the suite (cannot certify)")
    parser.add_argument("--today", default=None, help="override the tag date (YYYYMMDD)")
    args = parser.parse_args()

    results = run_checks(args.base, skip_tests=args.skip_tests, will_tag=args.tag)

    print(f"PORT PREFLIGHT — base {args.base}\n")
    for result in results:
        print(f"  [{'PASS' if result.passed else 'FAIL'}] {result.name}")
        for line in result.detail.splitlines():
            print(f"        {line.strip()}" if not line.startswith("    ") else line)
    failed = [r for r in results if not r.passed]
    print()

    if failed:
        print(f"NOT CERTIFIED — {len(failed)} check(s) failed: {', '.join(r.name for r in failed)}")
        print("Do not offer this commit as a port base.")
        return 1

    print("CERTIFIED. This commit may be offered as a port base.")

    if args.tag:
        existing = subprocess.run(
            ["git", "tag"], cwd=str(REPO_ROOT), capture_output=True, text=True, check=False
        ).stdout.split()
        today = args.today or _dt.date.today().strftime("%Y%m%d")
        tag = next_base_tag(existing, today)
        subprocess.run(["git", "tag", tag], cwd=str(REPO_ROOT), check=True)
        subprocess.run(["git", "push", "origin", tag], cwd=str(REPO_ROOT), check=True)
        print(f"tagged and pushed {tag}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
