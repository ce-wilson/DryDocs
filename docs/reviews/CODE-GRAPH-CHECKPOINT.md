# Code-graph review — checkpoint

Protocol: checkpoint-per-unit (persona-review routine, proven 2026-06).
Plan: [`code-graph-review-plan.md`](code-graph-review-plan.md).

## State

- phase: ALL THREE COMPLETE (run 1)
- next_action: none — next run only worth a session after the scanner fix
  (see run log 2026-07-28); U4 (tech-debt query pack) should wait on the
  same fix or it enshrines vacuous queries.

## Run log

- 2026-07-28 — **Run 1 complete, single session (U1+U2+U3).**
  Preconditions: snapshot `drydocs-20260728-0754.json` (commit `36866f9`)
  → `load-code-snapshot` (194 modules, 105 IMPORTS) →
  `load-doc-traceability` (sections 148, matrix 51; feedback pass REFUSED
  by the L17 :Employee guard — first live firing, recorded as evidence in
  U3, not an error).
  - U1 → `persona-python-architect-2026-07.md`. Headline: the snapshot
    records ZERO cross-root (and no function-level) IMPORTS edges, so
    A1/A5/A6 are vacuous and A4's 24 orphans were 24 false positives
    (all dispositioned with grep evidence). A2 healthy (scanner and live
    graph agree: 0 cycles). A3: base.py fan-in 18→19; lineage/model.py 9
    is the new second hotspot.
  - U2 → `persona-project-manager-2026-07.md`. 80 recent done items /
    91 path claims: ZERO false done-claims; 30/30 next_ready inputs
    alive; census found `drydocs_api` is not a scan root (a whole
    package invisible to every Phase-1 metric).
  - U3 → `persona-tech-writer-2026-07.md`. Doc board: 5 design docs cite
    PRE-SQUASH commits (dangle off main), startup-refresh runbook edited
    same day still cites 07-20, mapping-demo runbook has no cite; zero
    dead component citations; 8/56 Component refs sheared by the
    comma-split cell convention; base.py + lineage/model.py cited by no
    component; sdlc-*.md §DEP stale in 3 rows (pre-G2 paths).
  - 5 IDEAS lines filed (see inbox, 2026-07-28); zero backlog/graph
    edits from within the reviews themselves.
