---
handoff: drydocs.lane-handoff.v1
lane: C
machine: desktop-ui
generated: 2026-09-11
generated_at: 4cee1bf7 (main)
queue: [WEB24]
other_queue: [C44, D11, K23, CFG4, API6, LOAD16, H8, L19, META1]
pens: [code:drydocs-web]
---

# Lane C handoff — desktop-ui, 2026-09-11

**From:** the Lane A session (desktop). **To:** the Lane C session on the desktop-ui.
**Lifecycle:** a working handoff, not a durable record — the item files are. When
the queue below is empty, delete this file in the closing commit
(`python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` says when).

## Pens — declare them in your first commit (CLAUDE.md §0, one pen per surface)

Collisions come from two sessions writing the same surface, not from two sessions
existing. Your first commit message (or your `wip/` branch name) names what you hold:

```text
pen: code:drydocs-web
```

Lane A holds: `backlog · port · adr · gates · snapshot`. Anything not declared by either lane
is off-limits to both until one asks. The item-file claim is the pen for ONE item; this
is the pen for a SURFACE.

## Start ritual — CLAUDE.md §0, cited, not restated

1. `git pull` (fast-forward), read CLAUDE.md, open the board's Ready-to-pull strip.
2. Claim ONE item at a time: push `status: in_progress` in that item file BEFORE work,
   no render (Y5). `git branch --show-current` before every commit (the branch
   guardrail). In-flight work pushes to `wip/<id>-desktop-ui` at the first
   substantive edit (J31).
3. Ids come from the allocator, never from your tree (I6) — but a lane does not mint:
   ideas and groom requests go back to the sender (see the pens above).
4. Per-machine facts are yours to verify: `DRYDOCS_DATA_ROOT`, `DRYDOCS_LOGDIR`, the
   `.env`, and whether Neo4j is reachable here. Venue-stamp any live claim (J18).

## Your queue, in order (1 item) — claim one at a time

Every item below is `todo` with every dependency `done` at the generating commit — the
same rule the board's Ready strip uses (`derive_summary`). Re-check on pull: the other
lane may have moved something. The split is by MODULE (the id series is the module
since PLAN1), so two lanes minting in disjoint series cannot collide on a number.

| # | Id | Title | Type / prio | Module | Model | Notes from the check |
|---|---|---|---|---|---|---|
| 1 | **WEB24** | Rule the five open Salt DS second-track questions at a HITL gate, and land the PoC findings on main first so the gate cites the tree rather than a branch | task / p2 | `drydocs-web` | fable | input `docs/restructure/IDEAS.md` — pen `backlog` (the idea inbox — one file until R6 shards it); overlap: WEB24 <-> C44: both name `docs/restructure/03-hitl-sme-flow.md`; overlap: WEB24 <-> CFG4: both name `config/taxonomy/software-registry.yaml`; overlap: WEB24 <-> L19: `docs/design` (L19's input, coarse) covers `docs/design/ui-exploration/site-plan.md`; overlap: WEB24 <-> L19: `docs/design` (L19's input, coarse) covers `docs/design/ui-exploration/ui-conventions.md`; overlap: WEB24 <-> L19: `docs/design` (L19's input, coarse) covers `docs/design/ui-exploration/kept-orbit-philosophy.md` |

**Flags to rule before claiming** (the script flags; the author decides):

- WEB24: input `docs/restructure/IDEAS.md` — pen `backlog` (the idea inbox — one file until R6 shards it) — Lane A's pen; coordinate before editing.

## Branching and merge — WEB24's is not the lane default

Read this before the queue. The lane's standing merge rule does not apply to the branch
this item is about.

**The PoC branch does not merge.** `wip/idea-192-desktop` carries twelve paths and WEB24
clause (f) keeps eleven of them off `main`: the `/lab/salt-poc` route, the five npm pins,
the `config/taxonomy/ui-components.yaml` ledger row and the load-map render refresh that
rides it. A `--no-ff` merge would put a second component library in the console for an
option nobody has ruled on, which is the gate being pre-empted by its own preparation. So
rule 3 — Lane A merges your `wip/` branches at close — is SUSPENDED for that one branch.
It is not yours to merge and it is not Lane A's either. Clause (c) is what releases it.

**Lift ONE PATH, never the commit.** The findings doc reached the branch in `3c17ddf0`,
which also carries `web/src/routes/SaltPocRoute.tsx` and `SaltPocRoute.css`. So
`git cherry-pick 3c17ddf0` brings the route with it and breaks clause (f). The operation is
a path-scoped take:

```bash
git fetch origin
git switch -c wip/web24-desktop-ui origin/main
git checkout origin/wip/idea-192-desktop -- docs/design/ui-exploration/salt-ds-poc.md
git status --short                      # expect exactly one added path, and only one
```

**Why the whole-file take is right HERE and wrong as a habit.** `git checkout <ref> -- <path>`
writes the file as that ref holds it — the CUMULATIVE state, not the change. That is the
defect PORT14 recorded from the consumer's apply and PORT9 corrected producer-side, and it
bites whenever the receiving side already holds the path. Here it does not:
`salt-ds-poc.md` is status `A` against `main`, so the whole file IS the change. That is the
clean-add half of PORT9's corrected rule and it is the only half that licenses this
command. Do not carry it to a path `main` already has.

**The two render files are the trap, and they look harmless.** `docs/plan/load-map.html`
and `web/src/generated/load-map.json` differ from `main` only by the
`config/taxonomy/ui-components.yaml` blob id and the inputs digest that follows from it.
Landed on their own they are stale against `main`'s ledger and the session ritual's
stale-render check fails; landed WITH their source they breach clause (f). Both stay on the
branch. The same goes for `tests/unit/test_ui_components.py`, `web/README.md`,
`web/src/App.tsx` and `web/src/modules/registry.ts` — eleven of the branch's twelve paths
stay put, and exactly one moves.

**Do NOT restamp the doc's provenance bullet when it lands.** Its `Reviewed at:` line names
`2883fc61` on the branch, and rewriting it to a `main` sha would stamp a present-day commit
on a document read against a tree that never held the PoC code.
`docs/style/review-provenance.md` forbids that sweep by name — back-filling a sha is the
exact failure the convention exists to prevent, applied to itself.

**Do NOT add the doc to WEB24's `inputs:`.** The item's own notes forbid it by name: it is
an OUTPUT of clause (a), not an input, and the PLAN12 guard checks open items' inputs
against the tracked tree, which is why it was left off at the mint. At close it goes in
`outputs:` instead — and never `WEB24.yaml` itself, which claiming and closing both edit, so
the guard refuses it (ADR 0013 clause 3b). Compute the list rather than typing it:
`git diff --name-only <merge>^1 <merge>`.

**No render rides with it.** `docs/design/ui-exploration/*.md` sits outside the
`render_design_doc.py docs/design/*.md` set — `*` does not span separators — and no
`salt-ds-poc.html` exists on either side. Landing the doc alone leaves no stale render and
trips no determinism guard. Do not generate one.

**What the doc says about its own home is correct; leave it.** Its provenance block names
`2883fc61` on `wip/idea-192-desktop` and its section 6 lists the code by branch. That is
J63 working as designed: the doc asserts where the code lives, it does not assert that the
code is on `main`. A reader at the sitting can open the doc, which is the whole point of
clause (a).

**Your own branch is ordinary.** `wip/web24-desktop-ui` off `origin/main`, pushed at the
first substantive edit (J31), merged `--no-ff` by Lane A at close and deleted there. The
PoC branch is the exception; yours is not. If you are a second session in the desktop's
own working tree, take the §0 detached-worktree recipe rather than sharing the checkout —
a pull that aborts on another session's dirty file blocks the whole tree, not just the
file.

**What retires `wip/idea-192-desktop`.** Clause (c)'s answer, and nothing before it. A
second track opens, and a follow-up item lands the route on its own terms; it does not, and
the branch is deleted with the item's close recording that the PoC was costed and declined.
Either way the deletion is Lane A's, with `git branch -d` and never `-D` — the refusal on
an unmerged branch IS the check.

**One cosmetic thing, deliberately not fixed.** `2883fc61`'s subject begins with a UTF-8
BOM (`EF BB BF`). It is pushed, it sits on a branch nothing merges, and rewriting a pushed
commit to remove a leading invisible character costs more than it buys. If clause (c) ever
sends that branch toward `main`, squash or reword it then.

## The `gates` pen, on loan for one slug

WEB24 clause (b) writes `config/gate-prompts/salt-ds-second-track.yaml` and clause (d)
records an outcome in `config/gate-log.md`. Both are Lane A's `gates` pen, so the loan is
stated here rather than assumed:

- **Yours:** `config/gate-prompts/salt-ds-second-track.yaml`. A NEW file on a slug no other
  lane is writing, so there is nothing to collide with.
- **Not yours:** `config/gate-log.md`. It is append-only and every burst in which two lanes
  touched it produced a conflict at its tail. Draft the record, hand it to Lane A in your
  close report, and Lane A appends it in the same commit as the render.
- The item's `gates:` field gains the slug only AFTER the prompt file is on disk.
  `test_declared_gates_are_lists_of_known_prompt_slugs` reads the disk, and WEB24's own
  notes say so — adding the slug at claim time turns the board red for the whole window.

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
| Lane A's queue | the items C44, D11, K23, CFG4, API6, LOAD16, H8, L19, META1 and their inputs | do not claim or edit |
| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |
| `code:drydocs-web` | `config/taxonomy/ui-components.yaml` | this lane, with the module — the O42 ledger guard fails on any new .tsx, so every web item adds its row here (the 2026-09-05 Lane B close: five items touched it, none named it) |
| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — Lane A regenerates once at close; nobody merges them by hand (J43) |

**About Lane A's queue, from the same check** (for the sender to rule — this lane
does nothing with these):

- C44: gate-bound: email-dl-contact-point (an SME session, not a build)
- D11: gate-bound: controlm-definition-precedence (an SME session, not a build)
- K23: gate-bound: document-supersession (an SME session, not a build)

**Lane C claims status-only and never renders.** A claim is one item file, pushed;
Y5 tolerates it un-rendered, and Lane A renders once at close. **Lane C does not
append to `IDEAS.md` while the inbox is one file** (until R6 shards it): even an
allocator-minted id conflicts at the inbox top when both machines insert there in
one burst (observed 2026-09-02, twice). Anything worth capturing goes back to the
sender in your close report.

**Three things the 2026-09-03 burst learned the hard way** (six items, one laptop):

- **Every Lane C CLOSE commit is red on the roadmap guard, and that is expected.** Y5
  tolerates status-only drift; a close writes notes, and Lane C does not render, so
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

1. Every claimed item `done` and pushed; unfinished work on `wip/<id>-desktop-ui`,
   pushed. No render, no snapshot — those are Lane A's pens.
2. `python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` — when it
   reports the queue empty, delete this file in the same closing commit.
3. Report back: what closed, what is on `wip/`, what you noticed (that is how ideas
   reach the inbox from Lane C). Lane A merges your `wip/` branches `--no-ff`, deletes
   them, renders once, snapshots once.
