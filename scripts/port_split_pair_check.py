"""port_split_pair_check.py — a commit split across two dispositions ports as a broken half (PORT12).

Run at a roll close, on the PRODUCER side, before certifying:

    python scripts/port_split_pair_check.py port-base-20260909
    python scripts/port_split_pair_check.py port-base-20260909 --head HEAD

It names every SPLIT PAIR in the range: a definition the range ADDS to a file the
consumer reconciles by hand, and a reference the same range adds to it from a file that
crosses to the consumer unattended. Each pair is a line the roll owes its relay - not a
refusal, and not a defect in anyone's work.

WHY IT EXISTS. G130 (`01761011`, 2026-08-30) added `constraints_detail` to
`drydocs_core/neo4j_client.py` and a call to it in `drydocs/cli_schema.py` in one
commit. The caller's path is canonical-producer and crossed wholesale; the method's
path falls to the manifest default, which is evaluate-on-collision for a file both
sides authored, so it waited on a hand-merge. The consumer took the caller, the sixteen
lines did not arrive, and `drydocs bootstrap` raised
`AttributeError: 'Neo4jClient' object has no attribute 'constraints_detail'` ten days
later - because an uncalled missing method raises nothing until it is called. There was
no earlier signal available, which is why this runs at the close rather than waiting for
someone to notice.

WHAT IT IS NOT. It is not a gate: the dispositions are right, `drydocs_core/**` is
evaluate-on-collision for a reason the manifest states, and a split commit is a normal
thing to write. It is not PORT6's completeness check either - that answers whether a
PATH ever arrived, and would never have seen this, because every path in the G130 case
is present on both sides. This is about what is INSIDE two files that arrived by
different routes.

THREE OUTCOMES, NEVER SILENCE (ADR 0021). Pairs found, checked-clean over a named
range, or NOT CHECKED with the revision that would not resolve. A range that could not
be compared is not a range with no findings.

Canonical-producer; the logic is in `drydocs/port/split_pairs.py` and this is the entry
point only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from drydocs.port.split_pairs import check_range  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("base", help="the previous roll's base tag")
    ap.add_argument(
        "--head", default="HEAD", help="the tag or revision being rolled (default HEAD)"
    )
    args = ap.parse_args(argv)

    outcome = check_range(args.base, args.head, repo=REPO)
    print(f"SPLIT-PAIR CHECK (PORT12): {outcome.render()}")

    if outcome.is_not_checked:
        # Not a pass and not a failure: nothing was compared, and the roll's report
        # says so in the same words rather than printing a reassuring zero.
        return 2

    if outcome.is_clean:
        print("No definition added on a hand-merge path is newly used from one that crosses whole.")
        return 0

    print()
    print("Each line is a RELAY LINE this roll owes - the consumer's hand-merge of the")
    print("defining file has to carry the definition, or the using file breaks on their")
    print("tree with no signal until it runs.")
    print()
    by_definer: dict[str, list] = {}
    for f in outcome.findings:
        by_definer.setdefault(f.defined_in, []).append(f)
    for definer in sorted(by_definer):
        rows = by_definer[definer]
        print(f"  {definer}  [{rows[0].defined_disposition}]")
        for f in sorted(rows, key=lambda x: (x.name, x.used_in)):
            print(f"      {f.name}  <- used from {f.used_in} ({f.used_disposition})")
    print()
    print(f"{len(outcome.findings)} split pair(s). Reported, never gated: exit 0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
