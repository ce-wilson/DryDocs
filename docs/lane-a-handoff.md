---
handoff: drydocs.lane-handoff.v1
lane: A
machine: desktop
generated: 2026-09-09
generated_at: 7ed742d2 (main)
queue: [PORT8, PLAN12, CFG7, CFG8, CORE10, GRAPH5, CORE18, PLAN13, MM13, WEB22, GRAPH2, GRAPH3, CORE11, CORE12, DOC10, DOC11, N23, J70, ONT5, GRAPH6, META1, MM7, Y3]
other_queue: [LOAD13, LOAD14, DOC12, REV2, REM3, API5, LOAD8, LOAD9, LOAD10, LOAD12, LIN4, CORE13, CORE14, CORE15, CORE16, CORE17, GRAPH1, GRAPH4, META2, AGENT2, DEEP1, O48, Q28, N17, G86, G85]
pens: [backlog, port, adr, gates, snapshot]
---

# Lane A handoff — desktop, 2026-09-09

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

## Your queue, in order (23 items) — claim one at a time

Every item below is `todo` with every dependency `done` at the generating commit — the
same rule the board's Ready strip uses (`derive_summary`). Re-check on pull: the other
lane may have moved something. The split is by MODULE (the id series is the module
since PLAN1), so two lanes minting in disjoint series cannot collide on a number.

| # | Id | Title | Type / prio | Module | Model | Notes from the check |
|---|---|---|---|---|---|---|
| 1 | **PORT8** | The port preflight certifies a base it could not read - _git discards the exit code, an unresolvable base yields an empty range, and both range checks pass on emptiness - so the preflight fails closed and reports NOT CHECKED | bug / p1 | `drydocs-port` | sonnet | clean |
| 2 | **PLAN12** | An inputs: existence guard in tests/unit/test_backlog.py - non-done items only, against git ls-files, gitignore-aware, byte-safe - landing green with the five stale item files fixed in the same commit | task / p1 | `drydocs-plan` | sonnet | clean |
| 3 | **CFG7** | One-off sweep, not a guard - the nineteen gate prompts and two sweepable items still citing the S5-retired file names get the current directory paths with dated AMENDED markers | chore / p2 | `config` | haiku | clean |
| 4 | **CFG8** | Draft the source-descriptor-axes gate prompt - are the five axes the right five, where does wired live and how is it derived, do axis values reach the graph - as its own short page held in the same sitting as registry-wiring-readiness | task / p1 | `config` | fable | overlap: CFG8 <-> LOAD14: both name `config/source-descriptors.yaml` |
| 5 | **CORE10** | ADR 0021 instrument: one three-outcome type in drydocs_core (checked-clean, findings, not-checked-with-reason), a declared probe registry, and a guard that reads code - the preflight and the doc-coverage report adopt it first | task / p1 | `drydocs-core` | sonnet | overlap: CORE10 <-> LOAD14: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/docs_verify.py`; overlap: CORE10 <-> LOAD14: both name `drydocs/docs_coverage.py`; overlap: CORE10 <-> LOAD9: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/run_log.py`; overlap: CORE10 <-> CORE13: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/neo4j_client.py`; overlap: CORE10 <-> CORE14: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/neo4j_client.py`; overlap: CORE10 <-> CORE15: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/run_log.py`; overlap: CORE10 <-> CORE16: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/adapters/csv_adapter.py`; overlap: CORE10 <-> CORE16: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/adapters/oracle_adapter.py`; overlap: CORE10 <-> CORE17: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/neo4j_client.py`; overlap: CORE10 <-> GRAPH1: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/component_map.py`; overlap: CORE10 <-> GRAPH4: both name `tests/source_scan.py`; overlap: CORE10 <-> O48: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary` |
| 6 | **GRAPH5** | Remove the eighteen ADR 0018 re-export shims in one item - the 'roll after next' trigger fired on 2026-09-08 and action item 6 is still unchecked - with the citation sweep and the relay line the company needs | task / p2 | `graph-infra` | sonnet | overlap: GRAPH5 <-> REV2: `drydocs/review` (GRAPH5's input, coarse) covers `drydocs/review/graph_verify.py`; overlap: GRAPH5 <-> GRAPH1: `drydocs/port` (GRAPH5's input, coarse) covers `drydocs/port/reconcile_before.py`; overlap: GRAPH5 <-> META2: `drydocs/review` (GRAPH5's input, coarse) covers `drydocs/review/sme_notes.py` |
| 7 | **CORE18** | The data root's layout is declared in three places and only two are cross-checked - internal/server-inventory/ leaves the repo tree, bundle.py's hardcoded repo/ prefix moves into config/data-zones.yaml, and the non-overlap invariant covers all three | task / p2 | `drydocs-core` | sonnet | overlap: CORE18 <-> LOAD13: both name `drydocs/source_registration/bundle.py`; overlap: CORE18 <-> LOAD14: both name `config/source-registry.yaml`; overlap: CORE18 <-> LOAD14: both name `config/source-descriptors.yaml`; overlap: CORE18 <-> N17: both name `config/source-registry.yaml` |
| 8 | **PLAN13** | lane-handoff learns three things - a pending-<branch>.md capture path carved out of the backlog pen, --mint-pending at Lane A's close, and a remote-ref pass so --suggest and --check see done-on-branch items and dead claims | task / p2 | `drydocs-plan` | sonnet | clean |
| 9 | **MM13** | The data-flow-overview gate prompt names MM3 nine times for work that is MM7 - the item numbers moved at a groom after the prompt was drafted and nothing re-pointed it | chore / p2 | `config` | sonnet | gate-bound: data-flow-overview (an SME session, not a build) |
| 10 | **WEB22** | Run the console-auth-boundary gate - the one drafted-unsigned prompt with no item owning its session - to a recorded outcome | task / p2 | `drydocs-web` | fable | gate-bound: console-auth-boundary (an SME session, not a build) |
| 11 | **GRAPH2** | reconcile_before reaches into tests.unit.test_runbook_currency for three exemption tables - decide whether the tables move to a non-test home rather than declaring the crossing | task / p3 | `graph-infra` | sonnet | overlap: GRAPH2 <-> GRAPH1: both name `drydocs/port/reconcile_before.py` |
| 12 | **GRAPH3** | No Python coverage threshold exists at all - test:coverage is declared only for the web console - decide whether one exists and what it is before any Python slot runs the tool | task / p3 | `graph-infra` | sonnet | clean |
| 13 | **CORE11** | Raise drydocs_core.Neo4jClient to the level of its two younger siblings - a read access mode, captured driver notifications - and record in an ADR whether drydocs_api and the agents adopt it or stay separate | task / p2 | `drydocs-core` | fable | overlap: CORE11 <-> API5: both name `drydocs_api/app.py`; overlap: CORE11 <-> CORE13: both name `drydocs_core/neo4j_client.py`; overlap: CORE11 <-> CORE14: both name `drydocs_core/neo4j_client.py`; overlap: CORE11 <-> CORE17: both name `drydocs_core/neo4j_client.py`; overlap: CORE11 <-> AGENT2: `agents` (AGENT2's input, coarse) covers `agents/common/neo4j_tool.py`; overlap: CORE11 <-> AGENT2: `agents/common` (AGENT2's input, coarse) covers `agents/common/neo4j_tool.py`; overlap: CORE11 <-> O48: `drydocs_api` (O48's input, coarse) covers `drydocs_api/app.py` |
| 14 | **CORE12** | Declare drydocs_core's public surface once - grow __all__ to match reality, mark internals by convention, or give the boundary test a second axis - so 22 of 34 core modules stop being imported outside any declared contract | task / p3 | `drydocs-core` | fable | overlap: CORE12 <-> GRAPH1: both name `tests/unit/test_module_boundary.py` |
| 15 | **DOC10** | The review sweep's plan needs a declared environment step - poetry install and a drydocs_core.__file__ venue assertion before any measurement is trusted - closing the firing that measured another worktree's tree | chore / p3 | `docs` | haiku | clean |
| 16 | **DOC11** | Regenerate the module-sweep plan's size column at cycle 2's open - six of seven measured slots moved from the 2026-09-05 snapshot, drydocs-web by 55 percent | chore / p3 | `docs` | haiku | clean |
| 17 | **N23** | One SME gate for the whole id grammar - un-redact the database and schema, correct the carrier slot the derived URN builds from, and add the subset qualifier, because the four findings cannot be ruled apart | task / p1 | `config` | fable | gate-bound: registry-wiring-readiness (an SME session, not a build); overlap: N23 <-> LOAD14: both name `config/source-registry.yaml`; overlap: N23 <-> N17: both name `config/source-registry.yaml` |
| 18 | **J70** | Four registry-id rewrites were requested as a find-and-replace — two are id renames that owe a retired-id row, and one contradicts the signed J13 class-3 ruling | task / p2 | `config` | sonnet | gate-bound: schema-identifier-publish-ceiling-teams-edition (an SME session, not a build); overlap: J70 <-> LOAD14: both name `config/source-registry.yaml`; overlap: J70 <-> O48: `drydocs_core/ontology/relationship_vocabulary` (O48's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary/41-local-business-application.yaml`; overlap: J70 <-> N17: both name `config/source-registry.yaml` |
| 19 | **ONT5** | Reserve the physical half of the G34 pattern - :CatalogField keyed field_id and one planned edge DataAsset-[:HAS_FIELD]->CatalogField - in the base, with the flip to confirmed riding ONT3's Logical Container prompt, never an edit to a deferred page | task / p2 | `ontology` | fable | overlap: ONT5 <-> O48: `drydocs_core/ontology/relationship_vocabulary` (O48's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary/10-node-classifications.yaml`; overlap: ONT5 <-> O48: `drydocs_core/ontology/relationship_vocabulary` (O48's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary/42-local-catalog.yaml` |
| 20 | **GRAPH6** | duckdb is imported lazily and declared nowhere, and openpyxl sits in the dev group - declare the optional dependency group and decide openpyxl's group before a generator ships in-product | chore / p3 | `graph-infra` | haiku | clean |
| 21 | **META1** | drydocs_docmeta has had no design-lens read - slot 7 confirmed hygiene only - so cycle 2 of the sweep gives it one rather than assuming it covered | task / p3 | `drydocs-docmeta` | sonnet | clean |
| 22 | **MM7** | Control-M Output-tab log extractor — launcher job KIND, resolved arguments, placement handoff pair, landing prefix, compute target — joined onto :ETLProcess by pipeline GUID, dpl_mac-shaped, every skip counted (after G17) | task / p1 | `drydocs-lineage` | opus | input `internal-local/deepdoc/2026-08-20-session-1/transcripts/controlm-evidence-capture.md` is machine-local; notes say machine-local |
| 23 | **Y3** | Backlog graph vocabulary via the gate: :BacklogItem + DEPENDS_ON registered planned, gate prompt drafted — projection semantics, git stays the claim channel (after Y2) | task / p3 | `ontology` | sonnet | overlap: Y3 <-> O48: both name `drydocs_core/ontology/relationship_vocabulary` |

**Flags to rule before claiming** (the script flags; the author decides):

- MM7: input `internal-local/deepdoc/2026-08-20-session-1/transcripts/controlm-evidence-capture.md` is machine-local — does the desktop have it? If not, this item belongs to the other lane or waits for the file to be copied over.
- MM7: notes say machine-local — does the desktop have it? If not, this item belongs to the other lane or waits for the file to be copied over.

**Ruled by the sender (2026-09-09, this machine, at the mint-pass tip `7ed742d2`):** MM7's
machine-local inputs are the reason it is HERE - the captured logs sit on this desktop, so the
item never goes to the laptop. The order is the plan's: PORT8, PLAN12 and CFG7 first (the three
build-now fixes), then the eighth port roll, then CFG8 (the descriptor-axes draft) and the
stale-premise sweep of registry-wiring-readiness as N18's BEFORE clause, then sitting 1 (N18 and
CFG9 in one session, with ADR 0021's acceptance and the deferral rulings in the same message);
the wired BUILD is minted from that record and lands next, then CORE10 and CORE18. GRAPH5 waits
for the eighth roll and for Lane B's REV2, META2 and GRAPH1 to merge. MM13 then ONT4 prepare
sitting 3; N23 and J70 are sitting 2 and N23's draft waits for sitting 1 to sign (its own gate
binding). CORE11, CORE12, GRAPH2, GRAPH3, DOC10, DOC11, GRAPH6, META1 and Y3 fill the gaps between
sittings. The CORE10 overlaps with Lane B's core items are not collisions (CORE10 adds a module,
it edits none of theirs); CFG8 and CORE18 both name config/source-descriptors.yaml and are
sequenced draft-then-build on purpose.

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
| Lane B's queue | the items LOAD13, LOAD14, DOC12, REV2, REM3, API5, LOAD8, LOAD9, LOAD10, LOAD12, LIN4, CORE13, CORE14, CORE15, CORE16, CORE17, GRAPH1, GRAPH4, META2, AGENT2, DEEP1, O48, Q28, N17, G86, G85 and their inputs | do not claim or edit |
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
