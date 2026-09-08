"""port_completeness_check.py — the roll-close COMPLETENESS check (PORT6).

Run at a roll close, on the CONSUMER side, from the apply worktree:

    python scripts/port_completeness_check.py port-base-20260905 --prev port-base-20260902

It lists every path at the base tag that the working tree does not hold, bucketed by
the disposition `PORT-MANIFEST.yaml` resolves for it — through the same classifier the
disposition renderer uses, never a second one — plus every `## ` heading a union-append
markdown file has at the tag and lacks here. Exit 0 only when every survivor is named
in a `deferred-paths` row (the producer's, in `docs/port/port-prompt.md` at the tag, or
your own via `--deferrals FILE`) or falls in a ruling class (canonical-company: yours to
hold or take, never owed). Never-port paths are not listed at all.

WHY IT EXISTS. Two rolls closed COMPLETE (2026-09-01, 2026-09-05) with paths present at
the base tag and absent from the consumer tree; they surfaced as carve-outs afterwards
(the sixteenth and seventeenth reports; RELAY-35 is the by-hand recipe, the consumer's
correction 12 is its 113-survivor result). The attribution instrument the close used —
`git diff --numstat <base> <next> -- <path>`, empty means "not this roll" — prints empty
for a forgotten path exactly as for a deferred one. This is the second instrument: it
answers "ever applied or not", and the two run together at every close.

PRESENCE ONLY. A path present on both sides with different content does not show here;
that is the reconcile guards' subject (a before-dir) and `--numstat`'s.

Canonical-producer; ships to the consumer with the tree. Logic in
`drydocs/port/port_completeness.py`; this is the entry point only.
"""

from __future__ import annotations

import sys

from drydocs.port.port_completeness import main

if __name__ == "__main__":
    sys.exit(main())
