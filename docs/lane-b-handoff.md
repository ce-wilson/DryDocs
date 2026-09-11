---
handoff: drydocs.lane-handoff.v1
lane: B
machine: laptop
generated: 2026-09-10
generated_at: ce495fa2 (main)
queue: [GRAPH6, GRAPH2, GRAPH3, API6, LOAD16, H8, L19, META1]
other_queue: []
pens: [code:graph-infra, code:drydocs-api, code:drydocs-load, code:docs, code:drydocs-docmeta]
---

# Lane B handoff — laptop, 2026-09-10

**From:** the Lane A session. **To:** the Lane B session on the laptop.
**Lifecycle:** a working handoff, not a durable record — the item files are. When
the queue below is empty, delete this file in the closing commit
(`python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` says when).

## Pens — declare them in your first commit (CLAUDE.md §0, one pen per surface)

Collisions come from two sessions writing the same surface, not from two sessions
existing. Your first commit message (or your `wip/` branch name) names what you hold:

```text
pen: code:graph-infra · code:drydocs-api · code:drydocs-load · code:docs · code:drydocs-docmeta
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

## Your queue, in order (8 items) — claim one at a time

Every item below is `todo` with every dependency `done` at the generating commit — the
same rule the board's Ready strip uses (`derive_summary`). Re-check on pull: the other
lane may have moved something. The split is by MODULE (the id series is the module
since PLAN1), so two lanes minting in disjoint series cannot collide on a number.

| # | Id | Title | Type / prio | Module | Model | Notes from the check |
|---|---|---|---|---|---|---|
| 1 | **GRAPH6** | duckdb is imported lazily and declared nowhere, and openpyxl sits in the dev group - declare the optional dependency group and decide openpyxl's group before a generator ships in-product | chore / p3 | `graph-infra` | haiku | clean |
| 2 | **GRAPH2** | reconcile_before reaches into tests.unit.test_runbook_currency for three exemption tables - decide whether the tables move to a non-test home rather than declaring the crossing | task / p3 | `graph-infra` | sonnet | clean |
| 3 | **GRAPH3** | No Python coverage threshold exists at all - test:coverage is declared only for the web console - decide whether one exists and what it is before any Python slot runs the tool | task / p3 | `graph-infra` | sonnet | clean |
| 4 | **API6** | No route, spec or runner in drydocs-api sets a query timeout, so a hung query and a slow one look alike and the proxy's eventual 504 reads as a dead service - decide the bound before any build | task / p3 | `drydocs-api` | sonnet | clean |
| 5 | **LOAD16** | Team Edition Phase 4 - the coverage ledger generalized per application and per object class (repos, jobs, folders, tables, datasets, docs) on the ADR 0021 type, with wired: false rows counted as a named blocker class (after LOAD14, CORE10) | task / p2 | `drydocs-load` | sonnet | clean |
| 6 | **H8** | The company tree registers 67 CLI commands to producer main's 50 - turn the measured back-flow inventory into a per-command disposition the user can rule on | task / p2 | `docs` | sonnet | clean |
| 7 | **L19** | Post-census doc-drift sweep: re-cite pre-squash commit hashes, fix sdlc DEP tables to the post-G2 tree, cite the two fan-in hotspot contracts in the traceability matrix | chore / p2 | `docs` | sonnet | clean |
| 8 | **META1** | drydocs_docmeta has had no design-lens read - slot 7 confirmed hygiene only - so cycle 2 of the sweep gives it one rather than assuming it covered | task / p3 | `drydocs-docmeta` | sonnet | clean |

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
| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |
| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — Lane A regenerates once at close; nobody merges them by hand (J43) |

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

## What landed TODAY that changes three of these — read before you claim

The generator reads the item files; it cannot read `main` since they were written. Four
things landed 2026-09-10 that bear directly on this queue.

**GRAPH6 is plan unit 4.4, and it CLOSES PHASE 4.** `docs/restructure/EndGoalTeamsEdition.md`
names it as the last item of that phase (the duckdb / openpyxl dependency groups plus the
base-finish tag). It is first in the queue for that reason and it is `haiku`-tier — mechanical
with a stated acceptance. Nothing else in the plan waits on it, so if it is quick, take it and
the phase is done.

**GRAPH2 GOT BIGGER TODAY, and the item's own text now undercounts it.** It says
`reconcile_before` reaches into `tests.unit.test_runbook_currency` for THREE exemption tables.
As of `9e69e809` there are two more of exactly the same shape:
`.claude/skills/groom-backlog/validate.py` reads `INPUT_EXEMPTIONS` and `OUTPUT_EXEMPTIONS`
out of `tests/unit/test_backlog.py` via `importlib.util.spec_from_file_location`. Five tables
across two readers, so the item's question — *should these move to a non-test home?* — has
more evidence behind it than when it was written.

Two facts to carry into that decision, both measured today rather than argued:

- Those tables are **PER-SIDE VALUES**, not per-side code. A per-side banner went into
  `tests/unit/test_backlog.py` and the rule into `PORT-MANIFEST.yaml` at `ce495fa2`: each is
  guarded by "every row must still be cited by an item on THIS tree", so taking one whole
  strands the other side's rows, and unioning them gives each side rows nothing cites. **Any
  non-test home you choose has to keep that split**, or the port breaks in both directions.
- The consumer's apply of `port-base-20260910b` hit this live: PLAN12's guard arrived and
  reported **75 unresolved item inputs** against zero producer rows.

**A LANDMINE THAT IS NOT IN THIS QUEUE, so nobody trips it by accident.** PLAN14 added
`PLANNED_PATHS` to `drydocs/port/port_preflight.py`, naming `drydocs/loaders/field_map_xlsx.py`
and `tests/unit/test_field_map_xlsx.py` — files plan unit **5.8** will create. The guard
`test_a_planned_path_that_has_landed_leaves_the_table` **FAILS when either file appears**, by
design, so the exemption cannot outlive the work it waits on. If anything you do creates them,
delete the two rows in the same commit; the failure message says so.

**AND ONE MEASUREMENT RULE CHANGED.** J57 gained a third clause at `b484afc3`: same venue,
same invocation, THEN compare the failing set. `poetry run pytest -q` and
`python -m pytest tests/unit` collect differently — measured at 18 deselected and a different
skip count — so two runs that cross invocations cannot be compared even as sets. Use one
command for your before and your after.

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
