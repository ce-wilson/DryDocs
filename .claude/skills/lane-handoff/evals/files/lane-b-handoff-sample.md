---
handoff: drydocs.lane-handoff.v1
lane: B
machine: laptop
generated: 2026-09-01
generated_at: 51336cff (main)
queue: [MM3, G79, G106]
---

# Lane B handoff — laptop, 2026-09-01

**From:** the desktop Lane A session. **To:** the Lane B session on the laptop.
**Lifecycle:** a working handoff, not a durable record — the item files are. When
the queue below is empty, delete this file in the closing commit
(`python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` says when).

## Your queue, in order (3 items) — claim one at a time

| # | Id | Title | Type / prio | Module | Model | Notes from the check |
|---|---|---|---|---|---|---|
| 1 | **MM3** | Mind-map state file + the shared entity/ID extractor + novelty and theme columns on the search log | task / p2 | `drydocs-deepdoc` | opus | clean |
| 2 | **G79** | Split refresh-reference by SOURCE — one command per subject | task / p1 | `drydocs-load` | opus | clean |
| 3 | **G106** | drydocs prune-logs: retention as a verb mirroring prune-snapshots | task / p2 | `drydocs-load` | sonnet | clean |

## Surfaces — who owns what this burst

| Surface | Owner | Why |
|---|---|---|
| `config/gate-prompts/` | Lane A | gate prompts (SME sessions run from Lane A) |
| `docs/restructure/IDEAS.md` | Lane A | the idea inbox, and all grooming |
| `knowledge/depgraph-snapshots/` | Lane A | the session snapshot — one writer per burst |

## Close

1. Every claimed item `done` and pushed; renders regenerated; `gh run list` at YOUR sha.
2. `python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` — when it
   reports the queue empty, delete this file in the same closing commit.
