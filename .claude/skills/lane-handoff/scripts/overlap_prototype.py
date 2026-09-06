"""Do Lane B's queued items share INPUT PATHS with Lane A's?

handoff.py --suggest flags an input under a Lane A PEN (backlog/port/adr/gates/
snapshot) and re-checks the other queue's ids for readiness. Neither of those
compares the two queues' input paths to each other, which is the collision the
fence is actually for.

A path matches another if either is a prefix of the other, so `drydocs_api/`
covers `drydocs_api/schemas.py`.

PRESERVED AS RUN, NOT AS A TOOL. Written on the laptop during the 2026-09-05 Lane B burst
while deciding which queued items were safe to take, left uncommitted, and recovered on
2026-09-06. The lane lists below are that burst's, hardcoded — generalizing them IS the fix
and belongs in `handoff.py`, not here. Idea-269 says to reproduce this check from its
description because the file was believed lost. It was not. This is it, byte for byte.

Two things the fold-in needs that Idea-269 does not yet carry, both found by re-running it:

1. A SHARED INPUT IS NOT A COLLISION UNLESS ONE SIDE WRITES IT. Run as written this reports
   SEVEN of the ten queued items, not the four the close report named. WEB2, WEB6 and WEB7
   are the extra three and every one of them collides on the same single path —
   docs/reviews/modules/web-2026-09-05.md, the review that spawned every WEB item on BOTH
   lanes. That is read-only provenance, not a write target, and 66 of the 663 item files
   name a docs/reviews/ path in `inputs`. A check that flags it fires on most WEB items in
   every future burst and gets ignored inside a week. The four in the close report are what
   is left after discounting it by hand.

   The catch, and the reason this file does not just fix itself: `inputs` is the only path
   field the v3 schema has. No item declares `outputs` and the validator does not know the
   word, so "one side writes it" is NOT expressible from the item files today. Either the
   schema grows the field, or the check excludes provenance by convention (paths under
   docs/reviews/). That is a ruling, and rulings are not a prototype's to make.

2. `--check` CANNOT DO THIS WITHOUT A FRONT-MATTER CHANGE. A generated handoff records
   `queue:` and `pens:` and not the other lane's ids; cmd_check matches the `queue:` line
   and reads nothing else. The other lane's ids survive only in a prose table row — "Lane
   A's queue | the items WEB9, WEB10, ..." — and parsing that is J37 exactly. So generate
   has to write an additive `other_queue:` line, and `--check` needs a graceful path for
   files that predate it. docs/lane-b-handoff.md is one such file.

A third, smaller one: the prefix rule is symmetric, so a COARSE input dominates the output.
O68 declares `web/src` and matches seven Lane A paths on its own. One row per collision is
right; the row ought to say which side was coarse.

Run from the repo root: `poetry run python .claude/skills/lane-handoff/scripts/overlap_prototype.py`
"""

from __future__ import annotations

from pathlib import Path

import yaml

ITEMS = Path("docs/restructure/backlog/items")
LANE_B = ["WEB2", "WEB6", "WEB8", "WEB7", "O63", "R12", "O43", "G131", "O89", "O68"]
LANE_A = ["WEB9", "WEB10", "R19", "R15", "R16", "P6", "N27"]


def inputs(item_id: str) -> list[str]:
    doc = yaml.safe_load((ITEMS / f"{item_id}.yaml").read_text(encoding="utf-8"))
    return [p.rstrip("/") for p in (doc.get("inputs") or [])]


def covers(a: str, b: str) -> bool:
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


a_inputs = {i: inputs(i) for i in LANE_A}
for b in LANE_B:
    hits: list[str] = []
    for p in inputs(b):
        for a, paths in a_inputs.items():
            for q in paths:
                if covers(p, q):
                    hits.append(f"{p}  <->  {a}:{q}")
    if hits:
        print(f"\n{b}:")
        for h in sorted(set(hits)):
            print(f"   {h}")
print("\n(no section above = no shared input path)")
