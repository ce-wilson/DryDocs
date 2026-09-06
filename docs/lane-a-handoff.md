---
handoff: drydocs.lane-handoff.v1
lane: A
machine: desktop
generated: 2026-09-06
generated_at: 9841ac9b (main)
queue: [WEB9, R15, R16, WEB10, R19, P6, N27]
pens: [backlog, port, adr, gates, snapshot]
---

# Lane A handoff — desktop, 2026-09-06

**From:** Lane A close of the 2026-09-05 burst (desktop, 2026-09-06). **To:** the Lane A session on the desktop.
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

## Your queue, in order (7 items) — claim one at a time

Every item below is `todo` with every dependency `done` at the generating commit — the
same rule the board's Ready strip uses (`derive_summary`). Re-check on pull: the other
lane may have moved something. The split is by MODULE (the id series is the module
since PLAN1), so two lanes minting in disjoint series cannot collide on a number.

| # | Id | Title | Type / prio | Module | Model | Notes from the check |
|---|---|---|---|---|---|---|
| 1 | **WEB9** | Credential propagation to the agent tier - the drydocs-api bearer token leaves the Ask message body and rides a header, a short-TTL exchange token or a session id, so no credential lands in an agent transcript | task / p1 | `drydocs-web` | sonnet | clean |
| 2 | **R15** | Epistemic labeling on query answers: every lineage/impact-style answer declares exact vs lower-bound and names the causes that limited the walk | task / p2 | `drydocs-api` | sonnet | clean |
| 3 | **R16** | Named agent verbs over the reviewed QuerySpecs: impact, context and trace as purpose-built tools instead of raw Cypher against the generic MCP server | task / p2 | `drydocs-api` | sonnet | clean |
| 4 | **WEB10** | The console's delivery shape - same-origin behind the API or one reverse proxy, a runtime-configured API base instead of a build-time inlined VITE_API_URL, and a production build that fails rather than falling back to localhost | task / p2 | `drydocs-web` | sonnet | clean |
| 5 | **R19** | Ask clarification loop for unresolved acronyms and graph-label intent (after R2, R5) | requirement / p1 | `drydocs-agents` | sonnet | clean |
| 6 | **P6** | Run the data-center collision probe on live psgmgr before any multi-data-center load — one table id in two data centers silently merges two folders into one graph node | task / p1 | `config` | opus | clean |
| 7 | **N27** | Control-M cannot be the source of record for a relationship whose other end is unregistered - register the three file-transfer platforms as systems with a classification and an owner | task / p1 | `config` | sonnet | clean |

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
| Lane B's queue | the items WEB8, O63 and their inputs | do not claim or edit |
| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |
| `code:drydocs-web` | `config/taxonomy/ui-components.yaml` | this lane, with the module — the O42 ledger guard fails on any new .tsx, so every web item adds its row here (the 2026-09-05 Lane B close: five items touched it, none named it) |
| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — Lane A regenerates once at close; nobody merges them by hand (J43) |

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
