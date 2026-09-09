---
handoff: drydocs.lane-handoff.v1
lane: B
machine: laptop
generated: 2026-09-09
generated_at: 7daa2804 (main)
queue: [DOC9, REM2, MM12, V6, V4, V5, DOC8, S11]
other_queue: [N18, J70, Y3]
pens: [code:docs, code:drydocs-remediation, code:drydocs-deepdoc, code:drydocs-docgen]
---

# Lane B handoff — laptop, 2026-09-09

**From:** the Lane A session. **To:** the Lane B session on the laptop.
**Lifecycle:** a working handoff, not a durable record — the item files are. When
the queue below is empty, delete this file in the closing commit
(`python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` says when).

## Pens — declare them in your first commit (CLAUDE.md §0, one pen per surface)

Collisions come from two sessions writing the same surface, not from two sessions
existing. Your first commit message (or your `wip/` branch name) names what you hold:

```text
pen: code:docs · code:drydocs-remediation · code:drydocs-deepdoc · code:drydocs-docgen
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
| 1 | **DOC9** | The committed docs/design/*.html renders get a committed-vs-source guard on the roadmap guard's shape, comparing renderer bytes rather than a normalized form | task / p2 | `docs` | sonnet | clean |
| 2 | **REM2** | A synthetic Control-M folder-set export ships beside the other samples so the remediation runbook's one verb can be demonstrated in a clone (after V7) | task / p2 | `drydocs-remediation` | sonnet | clean |
| 3 | **MM12** | Acronyms are the one thing every corpus in the deepdoc investigation is dense with and the extractor has no class for them — add acronym candidates, with the sentence they were found in, to the mind-map state file (after MM3) | task / p2 | `drydocs-deepdoc` | sonnet | overlap: MM12 <-> J70: `drydocs_core` (MM12's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary/41-local-business-application.yaml`; overlap: MM12 <-> Y3: `drydocs_core` (MM12's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary` |
| 4 | **V6** | SME runbook: drydocs-lineage — module-wide operate surface; index or absorb the chain-scoped lineage-mac and cmdline-resolution runbooks (after V1) | task / p2 | `docs` | sonnet | clean |
| 5 | **V4** | SME runbook: drydocs-review — gate pages, graph verify, review labels, publishing flow (after V1) | task / p2 | `docs` | sonnet | clean |
| 6 | **V5** | SME runbook: drydocs-docgen — design-doc render chain, outline validation, the L5/L6 feedback loop (after V1) | task / p2 | `docs` | sonnet | clean |
| 7 | **DOC8** | The 3.14 advisory leg's warnings are read once: each class is fixed or filtered by name with its reason, and the 3.12 baseline with it (after J67) | chore / p3 | `docs` | sonnet | clean |
| 8 | **S11** | Extract drydocs_plan/, drydocs_docgen/ and drydocs_port/ — the three declared components that never got a package (after S8) | chore / p3 | `drydocs-docgen` | sonnet | input `PORT-MANIFEST.yaml` — pen `port` (port dispositions); input `docs/port/port-prompt.md` — pen `port` (port prompt, relays, dossiers) |

**Flags to rule before claiming** (the script flags; the author decides):

- S11: input `PORT-MANIFEST.yaml` — pen `port` (port dispositions) — Lane A's pen; coordinate before editing.
- S11: input `docs/port/port-prompt.md` — pen `port` (port prompt, relays, dossiers) — Lane A's pen; coordinate before editing.

**Sender rulings on the flags and the order** (Lane A, desktop, 2026-09-09):

- **S11 and the `port` pen: one-directional, as ruled for the last queue.** Read
  `PORT-MANIFEST.yaml` and `docs/port/port-prompt.md` freely; write neither. A row the
  extraction needs (a new package path, a moved one) goes in S11's notes as path,
  disposition, one-line reason, and Lane A pastes it at the merge - the J59 clause (c)
  hand-back is the worked example (`7daa2804`). `MODULE_MAP.md` and `pyproject.toml` are
  yours for S11 (both auto-merged cleanly last burst).
- **MM12's coarse `drydocs_core` input does not reach `relationship_vocabulary/`.** The
  script flags an overlap with J70 and Y3 on that directory; MM12's build is the deepdoc
  extractor, and a new acronym class proposes into the state file, never into a vocabulary
  fragment (that is an ontology decision, Lane A's `gates` pen). Stay out of it.
- **V5 before S11, on purpose.** V5 documents the docgen render chain at its current
  paths; S11 moves that code into `drydocs_docgen/`. Write the runbook first, then let the
  extraction update its paths in the same S11 commit.
- **MM14 is deliberately not here.** It needs a throwaway Neo4j database and the laptop's
  venue for that is unruled; it goes to whichever machine the user says.
- **Run the whole J57 family before every push, and two more.** CORE9 verified 103
  targeted tests and its branch failed `tests/unit/test_never_port_citations.py` at the
  merge (fixed in `97e2d5d3`; Idea-308 carries the policy question). CLAUDE.md section 6's
  list does not yet name `test_skip_guard_policy.py` or `test_never_port_citations.py` -
  both read EVERY test file, so a change anywhere can fail them. Run them.

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
| Lane A's queue | the items N18, J70, Y3 and their inputs | do not claim or edit |
| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |
| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — Lane A regenerates once at close; nobody merges them by hand (J43) |

**About Lane A's queue, from the same check** (for the sender to rule — this lane
does nothing with these):

- N18: status is 'in_progress', a queue lists todo items only
- J70: gate-bound: schema-identifier-publish-ceiling-teams-edition (an SME session, not a build)

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
