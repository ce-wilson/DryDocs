---
handoff: drydocs.lane-handoff.v1
lane: A
machine: desktop
generated: 2026-09-08
generated_at: 2dc38863 (main)
queue: [PORT4, PORT3, PORT1, DOC2, PLAN9, J77, J64, J65, U27, I5, J54, N18, J70, Y3]
other_queue: [G90, J59, LOAD7, CORE9, J61, Y6, I7, DOC7, J60, S11]
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

## Your queue, in order (14 items) — claim one at a time

Every item below is `todo` with every dependency `done` at the generating commit — the
same rule the board's Ready strip uses (`derive_summary`). Re-check on pull: the other
lane may have moved something. The split is by MODULE (the id series is the module
since PLAN1), so two lanes minting in disjoint series cannot collide on a number.

| # | Id | Title | Type / prio | Module | Model | Notes from the check |
|---|---|---|---|---|---|---|
| 1 | **PORT4** | The port drop guard has no accepted-drop seam, so a retirement the port already ruled is reported as a finding at every chunk | task / p2 | `drydocs-port` | sonnet | overlap: PORT4 <-> J59: both name `PORT-MANIFEST.yaml`; overlap: PORT4 <-> S11: both name `PORT-MANIFEST.yaml`; overlap: PORT4 <-> S11: `scripts` (S11's input, coarse) covers `scripts/port_rename_check.py` |
| 2 | **PORT3** | A canonical-producer test that pins a never-port path fails on every consumer tree by construction, and nothing checks the join | task / p2 | `drydocs-port` | sonnet | overlap: PORT3 <-> J59: both name `PORT-MANIFEST.yaml`; overlap: PORT3 <-> S11: both name `PORT-MANIFEST.yaml` |
| 3 | **PORT1** | Three back-flow adoptions from the company's chunk-1 apply, plus the rule that a workplan naming a script names the commit it needs | task / p2 | `drydocs-port` | sonnet | overlap: PORT1 <-> S11: `scripts` (S11's input, coarse) covers `scripts/render_port_dispositions.py`; overlap: PORT1 <-> S11: `scripts` (S11's input, coarse) covers `scripts/port_rename_check.py` |
| 4 | **DOC2** | RELAY-23 - the frozen letters, mint by module code, the edition segment and the retired partition rules reach the company through the port-prompt (after PLAN2, PLAN3) | task / p1 | `docs` | fable | gate-bound: ontology-domain-registry-and-edition-grain (an SME session, not a build); overlap: DOC2 <-> J59: both name `PORT-MANIFEST.yaml`; overlap: DOC2 <-> S11: both name `docs/port/port-prompt.md`; overlap: DOC2 <-> S11: both name `PORT-MANIFEST.yaml` |
| 5 | **PLAN9** | Census pins are venue data: the coverage-census tuple in test_docs_coverage moves to a venue-owned config block the test reads, after a survey of the other pins of the same shape | task / p2 | `drydocs-plan` | sonnet | notes say machine-local; overlap: PLAN9 <-> J59: both name `PORT-MANIFEST.yaml`; overlap: PLAN9 <-> S11: both name `PORT-MANIFEST.yaml` |
| 6 | **J77** | A branch tip can be green while commits inside it were red at push, so a bisect through the range fails on a ledger guard rather than the defect - have the roll say which commits were red | chore / p3 | `docs` | haiku | overlap: J77 <-> J61: both name `CLAUDE.md`; overlap: J77 <-> Y6: both name `CLAUDE.md`; overlap: J77 <-> I7: both name `CLAUDE.md`; overlap: J77 <-> DOC7: both name `CLAUDE.md`; overlap: J77 <-> S11: both name `docs/port/port-prompt.md` |
| 7 | **J64** | A depgraph snapshot scanned before the commit it stamps is a claim about a tree that was never scanned - scan after, not before | bug / p2 | `graph-infra` | sonnet | clean |
| 8 | **J65** | The snapshot script's board refresh has been silently skipping on this desktop, and the warning prints the word Traceback instead of the module that is missing | bug / p2 | `graph-infra` | sonnet | overlap: J65 <-> J61: both name `scripts/render_board.py`; overlap: J65 <-> S11: `scripts` (S11's input, coarse) covers `scripts/render_load_map.py`; overlap: J65 <-> S11: `scripts` (S11's input, coarse) covers `scripts/render_board.py` |
| 9 | **U27** | snapshot.ps1's CI check asks `gh run list --branch main`, so from any branch HEAD can never appear and the verdict degrades to no-run-yet permanently — and the verdict function still has no tests | bug / p2 | `graph-infra` | sonnet | clean |
| 10 | **I5** | Two idea captures landed below the audit trail with a non-conforming header and were invisible to BOTH IDEAS.md guards | bug / p2 | `docs` | sonnet | overlap: I5 <-> I7: both name `.claude/skills/groom-backlog/SKILL.md` |
| 11 | **J54** | VERSIONING.md describes a backlog schema and a backlog file that no longer exist, so the release ritual instructs a reader to cite a tombstone | chore / p3 | `docs` | haiku | clean |
| 12 | **N18** | Run the registry-wiring-readiness gate (the wired/ready split, Idea-81 close) (after N10) | task / p2 | `config` | fable | gate-bound: registry-wiring-readiness (an SME session, not a build) |
| 13 | **J70** | Four registry-id rewrites were requested as a find-and-replace — two are id renames that owe a retired-id row, and one contradicts the signed J13 class-3 ruling | task / p2 | `config` | sonnet | gate-bound: schema-identifier-publish-ceiling-teams-edition (an SME session, not a build) |
| 14 | **Y3** | Backlog graph vocabulary via the gate: :BacklogItem + DEPENDS_ON registered planned, gate prompt drafted — projection semantics, git stays the claim channel (after Y2) | task / p3 | `ontology` | sonnet | overlap: Y3 <-> G90: `drydocs_core/ontology/relationship_vocabulary` (Y3's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary/20-property-terms.yaml`; overlap: Y3 <-> G90: `config/gate-prompts` (Y3's input, coarse) covers `config/gate-prompts/remediation-fix-tracking.yaml` |

**Flags to rule before claiming** (the script flags; the author decides):

- PLAN9: notes say machine-local — does the desktop have it? If not, this item belongs to the other lane or waits for the file to be copied over.

**Ruled by the sender (2026-09-08, this machine):** PLAN9's machine-local note is the
POINT of the item - the census tuple is venue data and this desktop is the venue that
pinned it - so it stays here. DOC2, N18 and J70 are gate work and the SME sits at this
machine; DOC2 is the RELAY (port pen) and reads the signed
`ontology-domain-registry-and-edition-grain` record, N18 RUNS its gate, J70 drafts under
a gate that is not yet signed. **This lane does not edit `CLAUDE.md` section 0 this
burst** - Lane B holds J61, Y6, I7 and DOC7 as one cluster on `wip/j61-laptop` - so J77's
sentence goes where a roll is authored (`.claude/skills/reconcile-port/SKILL.md` and the
roll shape in `docs/port/port-prompt.md`), and a section-0 pointer, if wanted, lands after
the merge. The `PORT-MANIFEST.yaml` overlaps with J59 and S11 are one-directional: Lane B
reads it, this lane writes it, and S11's three package rows arrive in its close notes for
the merge commit. The J64 / J65 / U27 trio is one sitting on `snapshot.ps1` - J65 first
(the refresh that silently skips), then J64 (scan after the commit), then U27 (the
branch-blind CI check plus the verdict tests) - and the ritual runs once after all three,
not after each. Y3's planned entry touches no term G90 binds. Not queued, and why: GN2 is
a wide rename that wants a single frozen unit and its own window; H8 needs the company
tree; CFG6 waits on the snapshot trio because its consumer is `snapshot.ps1`. Not an
item: the section-3 redaction ruling RELAY-47 is reserved for - it has no backlog item,
and the natural home is PORT4's accepted-drop seam, so PORT4 is queued first.

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
| Lane B's queue | the items G90, J59, LOAD7, CORE9, J61, Y6, I7, DOC7, J60, S11 and their inputs | do not claim or edit |
| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |
| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — Lane A regenerates once at close; nobody merges them by hand (J43) |

**About Lane B's queue, from the same check** (for the sender to rule — this lane
does nothing with these):

- G90: input `config/gate-prompts/remediation-fix-tracking.yaml` — pen `gates` (gate prompts — SME sessions run from Lane A)
- G90: gate-bound: remediation-fix-tracking (an SME session, not a build)
- J59: notes say machine-local
- J59: input `PORT-MANIFEST.yaml` — pen `port` (port dispositions)
- J61: input `docs/restructure/backlog/items/J48.yaml` — pen `backlog` (items, epics, plan — the board's sources)
- J61: input `docs/restructure/backlog/items/U27.yaml` — pen `backlog` (items, epics, plan — the board's sources)
- Y6: input `docs/restructure/backlog/items/Y5.yaml` — pen `backlog` (items, epics, plan — the board's sources)
- S11: input `PORT-MANIFEST.yaml` — pen `port` (port dispositions)
- S11: input `docs/port/port-prompt.md` — pen `port` (port prompt, relays, dossiers)

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
