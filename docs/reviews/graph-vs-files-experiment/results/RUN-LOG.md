# Experiment run log — 2026-08-10, 03:05 cron

Orchestrator: main session (opus). Track identities: ALPHA = files, BETA = graph
(known here and in phase 4; withheld from fable in review 1).

## Dispatch order

| # | When (local) | What | Model / agent | Status |
|---|---|---|---|---|
| 1 | 03:05 | planning-ALPHA (files) | haiku / backlog-groomer | **done 03:10** — 306.1s, 41 tool uses, 72,605 subagent tokens |
| 2 | 03:05 | planning-BETA (graph) | haiku / backlog-groomer | **done 03:09** — 258.5s, 26 tool uses, 81,671 subagent tokens |

| 3 | 03:11 | fable-review-1 (blind) | fable / general-purpose | **done 03:16** — 288.9s, 18 tool uses, 113,237 subagent tokens |
| 4 | 03:17 | o53-ALPHA (files) | haiku / general-purpose / worktree | **done 03:24** — 408.7s, 47 tool uses, 77,594 subagent tokens; build PASS, lint PASS; verified-before-delete via grep |
| 5 | 03:17 | o53-BETA (graph) | haiku / general-purpose / worktree | **done 03:28** — 265.5s, 31 tool uses, 77,451 subagent tokens; build PASS, lint PASS; diff 9,029 bytes |

| 6 | 03:30 | fable-grade-final (unblinded) | fable / general-purpose | **done 03:35** — 312.0s, 20 tool uses, 97,154 subagent tokens |

## Final scores (GRADES.md is authoritative)

planning: ALPHA 3, BETA 6 · coding: ALPHA 6, BETA 4 (capped — no archived
pre-delete verification evidence). Fable's replay found BOTH coding runs missed
the coverage pin (29, 68) in test_ui_components.py — both worktrees fail the
repo's own guard suite; NEITHER diff is adoptable as-is. All four runs
under-reported tool uses by 34-65%; both planning runs fabricated timestamps.

## Anomalies

- Review 1 headline: ALPHA drafted 5/6 ids that COLLIDE with existing backlog
  items (fabricated "next free" table); BETA had 1 collision (U19 — existed at
  its own snapshot commit, so not staleness). Both runs VALID on rule
  compliance. Fable would hand BETA to the SME.
