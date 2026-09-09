---
handoff: drydocs.lane-handoff.v1
lane: B
machine: laptop
generated: 2026-09-08
generated_at: 2dc38863 (main)
queue: [G90, J59, LOAD7, CORE9, J61, Y6, I7, DOC7, J60, S11]
other_queue: [PORT4, PORT3, PORT1, DOC2, PLAN9, J77, J64, J65, U27, I5, J54, N18, J70, Y3]
pens: [code:drydocs-load, code:config, code:drydocs-core, code:docs, code:drydocs-docgen]
---

# Lane B handoff — laptop, 2026-09-08

**From:** Lane A (desktop). **To:** the Lane B session on the laptop.
**Lifecycle:** a working handoff, not a durable record — the item files are. When
the queue below is empty, delete this file in the closing commit
(`python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` says when).

## Pens — declare them in your first commit (CLAUDE.md §0, one pen per surface)

Collisions come from two sessions writing the same surface, not from two sessions
existing. Your first commit message (or your `wip/` branch name) names what you hold:

```text
pen: code:drydocs-load · code:config · code:drydocs-core · code:docs · code:drydocs-docgen
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

## Your queue, in order (10 items) — claim one at a time

Every item below is `todo` with every dependency `done` at the generating commit — the
same rule the board's Ready strip uses (`derive_summary`). Re-check on pull: the other
lane may have moved something. The split is by MODULE (the id series is the module
since PLAN1), so two lanes minting in disjoint series cannot collide on a number.

| # | Id | Title | Type / prio | Module | Model | Notes from the check |
|---|---|---|---|---|---|---|
| 1 | **G90** | Build the fix-tracking loader the remediation-fix-tracking gate authorized (§C1) | requirement / p2 | `drydocs-load` | fable | input `config/gate-prompts/remediation-fix-tracking.yaml` — pen `gates` (gate prompts — SME sessions run from Lane A); gate-bound: remediation-fix-tracking (an SME session, not a build); overlap: G90 <-> Y3: `config/gate-prompts` (Y3's input, coarse) covers `config/gate-prompts/remediation-fix-tracking.yaml`; overlap: G90 <-> Y3: `drydocs_core/ontology/relationship_vocabulary` (Y3's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary/20-property-terms.yaml` |
| 2 | **J59** | The one freshness key the repo has LIES — 16 of 24 dated YAML headers are stale against git, so the `updated:` field needs a check that compares it to something, and that check cannot live in CI (after J58) | chore / p3 | `config` | sonnet | notes say machine-local; input `PORT-MANIFEST.yaml` — pen `port` (port dispositions); overlap: J59 <-> PORT4: both name `PORT-MANIFEST.yaml`; overlap: J59 <-> PORT3: both name `PORT-MANIFEST.yaml`; overlap: J59 <-> DOC2: both name `PORT-MANIFEST.yaml`; overlap: J59 <-> PLAN9: both name `PORT-MANIFEST.yaml` |
| 3 | **LOAD7** | test_pat_projection stops skipping on a tracked sample fixture - a missing PAT product-mapping sample fails the test loudly | bug / p3 | `drydocs-load` | sonnet | clean |
| 4 | **CORE9** | Delete the five skip guards the rewritten skip-guard policy no longer asks for, so every remaining skip is one the policy would refuse to drop (after CORE4) | chore / p3 | `drydocs-core` | sonnet | clean |
| 5 | **J61** | A shared checkout blocked by another live session's uncommitted file can neither pull nor push, and the branch guardrail returns EMPTY in the detached worktree that is the only way out — write the recovery down instead of improvising it once per session | chore / p2 | `docs` | sonnet | input `docs/restructure/backlog/items/J48.yaml` — pen `backlog` (items, epics, plan — the board's sources); input `docs/restructure/backlog/items/U27.yaml` — pen `backlog` (items, epics, plan — the board's sources); overlap: J61 <-> J77: both name `CLAUDE.md`; overlap: J61 <-> J65: both name `scripts/render_board.py` |
| 6 | **Y6** | The pull rule says a claim ships no render, which is true when you claim an existing item and false when you mint a new one — state the distinction in CLAUDE.md before it turns CI red again | chore / p2 | `docs` | sonnet | input `docs/restructure/backlog/items/Y5.yaml` — pen `backlog` (items, epics, plan — the board's sources); overlap: Y6 <-> J77: both name `CLAUDE.md` |
| 7 | **I7** | Fan-out orchestration puts several id allocators and several render writers inside one checkout - write the coordinator rule into the operating guide before a skill spawns workers | chore / p2 | `docs` | sonnet | overlap: I7 <-> J77: both name `CLAUDE.md`; overlap: I7 <-> I5: both name `.claude/skills/groom-backlog/SKILL.md` |
| 8 | **DOC7** | The J31 wip-branch rule says when the LOCAL branch is deleted, in CLAUDE.md and in the lane-handoff close | chore / p3 | `docs` | haiku | overlap: DOC7 <-> J77: both name `CLAUDE.md` |
| 9 | **J60** | Module and package docstrings are enforced by nothing — enable ruff's D100/D104 instead of writing a bespoke guard, and fill the modules that have no docstring at all | chore / p3 | `docs` | sonnet | clean |
| 10 | **S11** | Extract drydocs_plan/, drydocs_docgen/ and drydocs_port/ — the three declared components that never got a package (after S8) | chore / p3 | `drydocs-docgen` | sonnet | input `PORT-MANIFEST.yaml` — pen `port` (port dispositions); input `docs/port/port-prompt.md` — pen `port` (port prompt, relays, dossiers); overlap: S11 <-> PORT4: `scripts` (S11's input, coarse) covers `scripts/port_rename_check.py`; overlap: S11 <-> PORT4: both name `PORT-MANIFEST.yaml`; overlap: S11 <-> PORT3: both name `PORT-MANIFEST.yaml`; overlap: S11 <-> PORT1: `scripts` (S11's input, coarse) covers `scripts/render_port_dispositions.py`; overlap: S11 <-> PORT1: `scripts` (S11's input, coarse) covers `scripts/port_rename_check.py`; overlap: S11 <-> DOC2: both name `PORT-MANIFEST.yaml`; overlap: S11 <-> DOC2: both name `docs/port/port-prompt.md`; overlap: S11 <-> PLAN9: both name `PORT-MANIFEST.yaml`; overlap: S11 <-> J77: both name `docs/port/port-prompt.md`; overlap: S11 <-> J65: `scripts` (S11's input, coarse) covers `scripts/render_load_map.py`; overlap: S11 <-> J65: `scripts` (S11's input, coarse) covers `scripts/render_board.py` |

**Flags to rule before claiming** (the script flags; the author decides):

- G90: input `config/gate-prompts/remediation-fix-tracking.yaml` — pen `gates` (gate prompts — SME sessions run from Lane A) — Lane A's pen; coordinate before editing.
- J59: notes say machine-local — does the laptop have it? If not, this item belongs to the other lane or waits for the file to be copied over.
- J59: input `PORT-MANIFEST.yaml` — pen `port` (port dispositions) — Lane A's pen; coordinate before editing.
- J61: input `docs/restructure/backlog/items/J48.yaml` — pen `backlog` (items, epics, plan — the board's sources) — Lane A's pen; coordinate before editing.
- J61: input `docs/restructure/backlog/items/U27.yaml` — pen `backlog` (items, epics, plan — the board's sources) — Lane A's pen; coordinate before editing.
- Y6: input `docs/restructure/backlog/items/Y5.yaml` — pen `backlog` (items, epics, plan — the board's sources) — Lane A's pen; coordinate before editing.
- S11: input `PORT-MANIFEST.yaml` — pen `port` (port dispositions) — Lane A's pen; coordinate before editing.
- S11: input `docs/port/port-prompt.md` — pen `port` (port prompt, relays, dossiers) — Lane A's pen; coordinate before editing.

**Ruled by the sender (2026-09-08):** every pen flag above is a READ, and the overlaps
are sequencing, not blocks. **G90** reads the signed gate prompt as its spec and reads
`20-property-terms.yaml` for the terms it binds; it writes neither. "Gate-bound" here
means the gate is SIGNED (10/10, 2026-08-12) and the build is authorized, not that a
session is owed. Y3 adds a PLANNED vocabulary entry on Lane A and touches no term G90
uses. The acceptance is unit tests against the recorded-Cypher fake; a live run is a
bonus and is venue-stamped if made. **J59** is machine-local BY DESIGN - a local hook is
each machine's own install - so build it on the laptop and say so; `PORT-MANIFEST.yaml`
is one of the 24 dated headers it CHECKS and is never edited by it - a stale `updated:`
in a port-pen file goes in the close report, Lane A fixes it. **J61, Y6, I7, DOC7 are one
cluster on CLAUDE.md section 0**, so this burst fences `CLAUDE.md` section 0 to Lane B:
Lane A does not edit section 0 until the cluster merges, and J77's convention sentence
lands in the port-pen surfaces where a roll is authored, not in CLAUDE.md. Carry the four
on ONE branch, `wip/j61-laptop`, four claims and four commits in queue order - four
branches off one paragraph set would conflict with each other at merge, and one branch
is the exception to J31's per-id shape that the same-file case earns; name it in the
close report. The item files J48, U27 and Y5 are read as evidence and cited, never
edited; J61 reads `render_board.py` to re-verify clause (d) and does not change it. I7
edits section 0 only - if a groom-skill sentence is wanted, hand it back (I5 holds
`.claude/skills/groom-backlog/SKILL.md` this burst). **J60 runs after the cluster and
before S11**, from a fresh pull of `main`: the docstring commit is separate from the ruff
config commit, and a top-of-file docstring on a module Lane A also edited is a merge Lane
A resolves - expected, not a defect. **S11 is last and is the long tail**; if it does not
close this burst, that is fine and the branch stays on `wip/s11-laptop`. Its
`MODULE_MAP.md` rows land in the SAME commit as the move (the boundary guard is
default-deny); its `PORT-MANIFEST.yaml` rows for the three new packages are handed back
in the notes on the standing rule below (branch red on the fall-through guard, Lane A
adds the rows at merge); `docs/port/port-prompt.md` is read for the citations that name
`drydocs/port_preflight.py` and NOT edited - Lane A repoints them under the `port` pen at
merge. The `scripts/` overlaps are import lines that follow the move; if Lane A's PORT1 or
PORT4 touched the same script, the conflict is an import line and Lane A resolves it. The
laptop has its own Neo4j container and independent graph - verify before any live claim
and stamp the venue (J18). No flag blocks a claim.

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
| Lane A's queue | the items PORT4, PORT3, PORT1, DOC2, PLAN9, J77, J64, J65, U27, I5, J54, N18, J70, Y3 and their inputs | do not claim or edit |
| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |
| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — Lane A regenerates once at close; nobody merges them by hand (J43) |

**About Lane A's queue, from the same check** (for the sender to rule — this lane
does nothing with these):

- DOC2: gate-bound: ontology-domain-registry-and-edition-grain (an SME session, not a build)
- PLAN9: notes say machine-local
- N18: gate-bound: registry-wiring-readiness (an SME session, not a build)
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
