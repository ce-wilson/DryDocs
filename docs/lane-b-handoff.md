---
handoff: drydocs.lane-handoff.v1
lane: B
machine: laptop
generated: 2026-09-07
generated_at: 78277d1c (main)
queue: [WEB17, O72, CORE3, I8, G127, V10]
pens: [code:drydocs-web, code:drydocs-core, code:drydocs-plan, code:docs]
---

# Lane B handoff — laptop, 2026-09-07

**From:** Lane A (desktop). **To:** the Lane B session on the laptop.
**Lifecycle:** a working handoff, not a durable record — the item files are. When
the queue below is empty, delete this file in the closing commit
(`python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` says when).

## Pens — declare them in your first commit (CLAUDE.md §0, one pen per surface)

Collisions come from two sessions writing the same surface, not from two sessions
existing. Your first commit message (or your `wip/` branch name) names what you hold:

```text
pen: code:drydocs-web · code:drydocs-core · code:drydocs-plan · code:docs
```

Lane A holds: `backlog · port · adr · gates · snapshot`. Anything not declared by either lane
is off-limits to both until one asks. The item-file claim is the pen for ONE item; this
is the pen for a SURFACE.

## Start ritual — CLAUDE.md §0, cited, not restated

1. `git pull` (fast-forward), read CLAUDE.md, open the board's Ready-to-pull strip.
2. Claim ONE item at a time: push `status: in_progress` in that item file BEFORE work,
   no render (Y5). `git branch --show-current` before every commit (the branch
   guardrail). In-flight work pushes to `wip/<id>-laptop` at the first
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
| 1 | **WEB17** | Two web build follow-ups - the strict tsconfig type-checks neither config file, and the coverage report needs a publishing decision | chore / p3 | `drydocs-web` | sonnet | input `docs/restructure/backlog/items/WEB4.yaml` — pen `backlog` (items, epics, plan — the board's sources); input `docs/restructure/backlog/items/WEB13.yaml` — pen `backlog` (items, epics, plan — the board's sources) |
| 2 | **O72** | One-command local stack: Compose the four processes the runbook starts by hand, with its success checks expressed as health checks | task / p3 | `drydocs-web` | sonnet | clean |
| 3 | **CORE3** | CI clones shallow, so the commit-message ceiling guard skips instead of measuring - decide fetch-depth and record the reason in the workflow | chore / p2 | `drydocs-core` | sonnet | input `docs/restructure/backlog/items/J74.yaml` — pen `backlog` (items, epics, plan — the board's sources) |
| 4 | **I8** | An item acceptance can be overtaken by its own dependency growing, and nothing notices - report dependency currency as a warning at groom time, never as a gate | chore / p2 | `drydocs-plan` | sonnet | clean |
| 5 | **G127** | Eighteen un-escaped historical database mentions survive in four operator docs, three of which are governed renders, and the guard does not scan them at all (after G114) | chore / p2 | `docs` | sonnet | clean |
| 6 | **V10** | SME runbook: drydocs-web — audit the existing web-console runbook current (post O35-O41, FB-03/FB-04 access model) (after V1) | chore / p2 | `docs` | sonnet | clean |

**Flags to rule before claiming** (the script flags; the author decides):

- WEB17: input `docs/restructure/backlog/items/WEB4.yaml` — pen `backlog` (items, epics, plan — the board's sources) — Lane A's pen; coordinate before editing.
- WEB17: input `docs/restructure/backlog/items/WEB13.yaml` — pen `backlog` (items, epics, plan — the board's sources) — Lane A's pen; coordinate before editing.
- CORE3: input `docs/restructure/backlog/items/J74.yaml` — pen `backlog` (items, epics, plan — the board's sources) — Lane A's pen; coordinate before editing.

**Sender's rulings on the flags and on the queue** (Lane A, desktop, 2026-09-07):

- The three flagged inputs (WEB4, WEB13, J74) are cited as HISTORY by WEB17 and CORE3 -
  read them, never edit them. The only item file each of you touches is the one you claim.
- O72's acceptance carries a stale sentence, and its own 2026-09-06 note says so: the
  CORS allow-list reason for the fixed ports is gone since WEB10 / ADR 0020, and the
  stack gains a fifth service (the reverse proxy reading `web/delivery.json`). Settle the
  acceptance against ADR 0020 in your claim commit - that edit is yours, it is the
  claimed item's file.
- G127 and V10 edit `docs/design/*.md`; their `.html` renders are Lane A's at close, so
  those two tips will be red on the render guard as well as the roadmap guard. Expected.
- Considered and NOT queued: S13 (already `done`, 2026-08-27, this lane's own build) and
  GN2 (ready, but its acceptance forbids overlapping an in-flight port and freezes other
  producer work - it is a solo whole-trunk item for after carve-out D and the seventh
  roll, and two of its inputs are the `port` pen). GN2 is fenced below as Lane A's.

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
| Lane A's queue | the items GN2, N23, C44, N19, K29, DOC2 and their inputs | do not claim or edit |
| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |
| `code:drydocs-web` | `config/taxonomy/ui-components.yaml` | this lane, with the module — the O42 ledger guard fails on any new .tsx, so every web item adds its row here (the 2026-09-05 Lane B close: five items touched it, none named it) |
| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — Lane A regenerates once at close; nobody merges them by hand (J43) |

**About Lane A's queue, from the same check** (for the sender to rule — this lane
does nothing with these):

- N23: gate-bound: registry-wiring-readiness (an SME session, not a build)
- C44: gate-bound: email-dl-contact-point (an SME session, not a build)
- N19: gate-bound: source-connection-and-run-identity (an SME session, not a build)
- K29: gate-bound: tech-partner-attach-level (an SME session, not a build)
- DOC2: gate-bound: ontology-domain-registry-and-edition-grain (an SME session, not a build)

**Lane B claims status-only and never renders.** A claim is one item file, pushed;
Y5 tolerates it un-rendered, and Lane A renders once at close. **Lane B does not
append to `IDEAS.md` while the inbox is one file** (until R6 shards it): even an
allocator-minted id conflicts at the inbox top when both machines insert there in
one burst (observed 2026-09-02, twice). Anything worth capturing goes back to the
sender in your close report.

**Three things the 2026-09-03 burst learned the hard way** (six items, one laptop):

- **Every Lane B CLOSE commit is red on the roadmap guard, and that is expected.** Y5
  tolerates status-only drift; a close writes notes, and Lane B does not render, so
  `test_committed_roadmap_page_matches_its_sources` fails on every `wip/` tip CI runs.
  Read CI for the OTHER jobs and say so in the close report; Lane A's render at merge
  is the fix.
- **A new tracked path that matches no `PORT-MANIFEST.yaml` row fails the fall-through
  guard, and the manifest is the `port` pen.** Hand the row back in the item's notes -
  path, disposition, the one-line reason - and leave the branch red on that guard;
  Lane A adds the row in the merge commit (J62, `.pre-commit-config.yaml`).
- **`render_board.py` refreshes only the plan renders and the generated files it owns.**
  An item that adds its own generated artifact with its own writer (O70's
  `openapi.json` / `api.d.ts` via `scripts/dump_openapi.py` and `npm run api:types`)
  names the writer in its close report, so Lane A runs it at merge if the source moved.

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

1. Every claimed item `done` and pushed; unfinished work on `wip/<id>-laptop`,
   pushed. No render, no snapshot — those are Lane A's pens.
2. `python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` — when it
   reports the queue empty, delete this file in the same closing commit.
3. Report back: what closed, what is on `wip/`, what you noticed (that is how ideas
   reach the inbox from Lane B). Lane A merges your `wip/` branches `--no-ff`, deletes
   them, renders once, snapshots once.
