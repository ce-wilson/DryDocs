---
handoff: drydocs.lane-handoff.v1
lane: A
machine: desktop
generated: 2026-09-08
generated_at: 24076bc2 (main)
queue: [PORT6, PLAN5, PLAN6, J57, J75, N26]
pens: [backlog, port, adr, gates, snapshot]
---

# Lane A handoff — desktop, 2026-09-08

**From:** Lane A (desktop). **To:** the Lane A session on the desktop.
**Lifecycle:** a working handoff, not a durable record — the item files are. When
the queue below is empty, delete this file in the closing commit
(`python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` says when).

## Pens — declare them in your first commit (CLAUDE.md §0, one pen per surface)

Collisions come from two sessions writing the same surface, not from two sessions
existing. Your first commit message (or your `wip/` branch name) names what you hold:

```text
pen: backlog · port · adr · gates · snapshot
```

Lane B holds: `code:<module> per queued item`. Anything not declared by either lane
is off-limits to both until one asks. The item-file claim is the pen for ONE item; this
is the pen for a SURFACE.

## Start ritual — CLAUDE.md §0, cited, not restated

1. `git pull` (fast-forward), read CLAUDE.md, open the board's Ready-to-pull strip.
2. Claim ONE item at a time: push `status: in_progress` in that item file BEFORE work,
   no render (Y5). `git branch --show-current` before every commit (the branch
   guardrail). In-flight work pushes to `wip/<id>-desktop` at the first
   substantive edit (J31).
3. Ids come from the allocator, never from your tree (I6) — but a lane does not mint:
   ideas and groom requests go back to the sender (see the pens above).
4. Per-machine facts are yours to verify: `DRYDOCS_DATA_ROOT`, `DRYDOCS_LOGDIR`, the
   `.env`, and whether Neo4j is reachable here. Venue-stamp any live claim (J18).

## Your queue, in order (6 items) — claim one at a time

Every item below is `todo` with every dependency `done` at the generating commit — the
same rule the board's Ready strip uses (`derive_summary`). Re-check on pull: the other
lane may have moved something. The split is by MODULE (the id series is the module
since PLAN1), so two lanes minting in disjoint series cannot collide on a number.

| # | Id | Title | Type / prio | Module | Model | Notes from the check |
|---|---|---|---|---|---|---|
| 1 | **PORT6** | A roll close proves the clean-add class complete: a completeness check reads PORT-MANIFEST through the disposition classifier, lists every base-tag path absent from the consumer tree, and refuses COMPLETE unless the survivors are deferred by path | task / p1 | `drydocs-port` | sonnet | notes say machine-local |
| 2 | **PLAN5** | lane-handoff --suggest compares a lane's items against the other lane's pens and never against its queue - fold in the input-overlap check that found seven collisions | task / p2 | `drydocs-plan` | fable | clean |
| 3 | **PLAN6** | A venue wall written in acceptance prose is invisible to lane-handoff --suggest - give items a declared venue the check can read | task / p2 | `drydocs-plan` | sonnet | clean |
| 4 | **J57** | Acceptance that compares TOTALS lets two sessions agree on a number and both be wrong — the port and snapshot rituals record the failing-test ID SET, and a clean claim runs the repo-wide guard family | chore / p2 | `docs` | sonnet | clean |
| 5 | **J75** | A config surface, its renderer SURFACES row and the derived artifact it feeds are one coupling - a port slice that carries only part of the triple makes the derived file unproducible | chore / p2 | `docs` | sonnet | clean |
| 6 | **N26** | Nothing surfaces what the registry holds, so a wrong registration stays invisible until somebody trips over it - one view organized by class and one answer per loader, both from fields that already exist | task / p2 | `config` | sonnet | clean |

**Flags to rule before claiming** (the script flags; the author decides):

- PORT6: notes say machine-local — does the desktop have it? If not, this item belongs to the other lane or waits for the file to be copied over.

## Surfaces — who holds which pen this burst

The partition is by SURFACE, not only by item, because the collisions a burst
produces land on shared files rather than on claimed items: the inbox top, the
rendered pages, the snapshot. A lane touches the other lane's pens only by handing
the change back through the sender.

| Pen | Surface | Why |
|---|---|---|
| `backlog` | `docs/restructure/backlog/` | Lane A — items, epics, plan — the board's sources |
| `backlog` | `docs/restructure/IDEAS.md` | Lane A — the idea inbox — one file until R6 shards it |
| `backlog` | `docs/restructure/ideas/` | Lane A — the sharded inbox, once R6 lands (§0 names it already) |
| `backlog` | `docs/plan/` | Lane A — the plan renders: board, roadmap, ideas, load-map |
| `port` | `docs/port/` | Lane A — port prompt, relays, dossiers |
| `port` | `PORT-MANIFEST.yaml` | Lane A — port dispositions |
| `port` | `docs/company-prompts/` | Lane A — the company-facing prompts |
| `port` | `.claude/skills/reconcile-port/` | Lane A — the port skill |
| `adr` | `docs/decisions/` | Lane A — ADRs and their index |
| `gates` (this skill's addition to §0) | `config/gate-prompts/` | Lane A — gate prompts — SME sessions run from Lane A |
| `gates` (this skill's addition to §0) | `config/gate-log.md` | Lane A — the signed gate record |
| `gates` (this skill's addition to §0) | `config/crosswalks/` | Lane A — orchestrator crosswalks — gate-bound config |
| `snapshot` (this skill's addition to §0) | `knowledge/depgraph-snapshots/` | Lane A — the session snapshot — one writer per burst |
| Lane B's queue | the items R18, AGENT1, API4, WEB18, V9 and their inputs | do not claim or edit |
| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |
| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — Lane A regenerates once at close; nobody merges them by hand (J43) |

**About Lane B's queue, from the same check** (for the sender to rule — this lane
does nothing with these):

- R18: input `docs/decisions/0007-agentic-qa-architecture.md` — pen `adr` (ADRs and their index)
- AGENT1: input `docs/restructure/backlog/items/API4.yaml` — pen `backlog` (items, epics, plan — the board's sources)
- AGENT1: input `docs/restructure/backlog/items/O62.yaml` — pen `backlog` (items, epics, plan — the board's sources)
- API4: input `docs/restructure/backlog/items/O62.yaml` — pen `backlog` (items, epics, plan — the board's sources)
- WEB18: input `docs/restructure/backlog/items/R22.yaml` — pen `backlog` (items, epics, plan — the board's sources)

## Rules that have bitten — the durable ones live in CLAUDE.md

- Full suite before every push (`poetry run pytest -q`), plus `ruff check .` and a bare
  `ruff format --check .` — CI blocks on both and ran red for a week once while subsets
  passed locally (§0, Idea-111).
- A guard reads code, not prose (J66); never parse a render (J37); a review names its
  tree (J63). Read them in §6 — this file will not keep up with them.
- Item notes: no backslash escapes through a shell heredoc; write the note with the Write
  tool and run `tests/unit/test_backlog.py` before committing it.
- LANES ARE PRODUCER-SIDE ONLY. The company apply is a THIRD session in a different repo,
  never a lane: it ports methodically, one pen, accuracy over speed — this file never
  exists there. The `port` pen is producer-side and stays with Lane A; never run the port
  from the machine that holds it here.

## Close — in this order

1. Merge Lane B's `wip/<id>-*` branches `--no-ff` and delete them; then every item
   `done` and pushed.
2. Regenerate the renders ONCE (`render_board.py`, the design docs); `gh run list` at
   YOUR sha; then the depgraph snapshot — the `snapshot` pen is yours.
3. `python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` — when it
   reports the queue empty, delete this file in the same closing commit.
