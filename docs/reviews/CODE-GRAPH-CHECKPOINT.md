# Code-graph review — checkpoint

Protocol: checkpoint-per-unit (persona-review routine, proven 2026-06).
Plan: [`code-graph-review-plan.md`](code-graph-review-plan.md).

## State

- phase: RUN 2 IN PROGRESS (2026-08-08, scheduled 2am session) — U-arch
  and U-pm complete; next unit U-tw (tech writer).
- next_action: U-tw — doc-status board + re-check of Run 1 staleness
  findings (pre-squash cites, sdlc §DEP paths).

## Run log

- 2026-08-08 — **Run 2, U-arch complete.**
  Preconditions: snapshot `drydocs-20260808.json` (commit `f156cc7`) →
  `load-code-snapshot` (whole-tree per U9: 391 live `.py` / 830 IMPORTS;
  273 `.py` at U14 package scope; the prompt's 205/370 baseline is pre-U9
  scope — deviation explained, not drift) → `load-doc-traceability`
  (DocSection 188, DesignDoc 16, Requirement 51, Component 55; the
  doc_feedback pass REFUSED again on the L17 :Employee guard — same
  expected firing as Run 1, not a blocker).
  - U-arch → `persona-python-architect-2026-08.md`. A1 clean AND finally
    falsifiable; A2 0/0 agree; A3 base.py 29→31, lineage/model.py 24
    (confirmed #2, G22-reshape budget flag); A4 package-scope 0 holds;
    A5 29→27. Two instrument findings: `drydocs_docmeta` (born 08-04,
    10 modules) missing from the U14 $packages allow-list (score 30);
    residual scanner blind spot — imports rooted off the repo root
    (`scripts/` bare siblings, `agents/` common./graph_qa.) record zero
    in-region edges, so the 23-item A4b queue is mostly false orphans
    (score 20). Tombstones: 7, all non-.py — D7 healthy.
  - U-pm → `persona-project-manager-2026-08.md`. Done ledger TRUE again
    (271 claims, 37 flags all dispositioned — incl. the first tombstone
    disposition class, the S5 yaml→fragment-directory splits). Census gap
    class CLOSED (docmeta visible). The finding moved to grooming: 9 of
    62 next_ready items carry stale inputs — 5-item cluster from S5's
    08-06 re-home, 3× `web/src/routes/ask/`, a retention-deleted dated
    snapshot cite (structural: cite the dir, not a dated file), R9
    filename typo, V4 `drydocs/review/`. E1 wears in_progress while
    actually waiting on gate scheduling. One IDEAS line covers all.

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
- 2026-07-28 (same day) — **Scanner fix built (U6).** Root cause was one
  defect: `scan()` ran each root in isolation, so absolute imports naming a
  sibling root OR the file's own package dir never resolved (`ast.walk`
  always covered function bodies). Fix = shared-namespace `extract_many`
  in the depgraph repo + `drydocs_api` added to snapshot.ps1 targets.
  Post-fix graph: 205 modules / 370 IMPORTS (was 194/105), 0 cycles,
  drydocs→drydocs_core probe matches grep ground truth module-for-module
  (24), orphan signal reduced to genuine pytest entry points only.
