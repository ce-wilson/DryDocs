---
handoff: drydocs.lane-handoff.v1
lane: B
machine: laptop
generated: 2026-09-10
generated_at: 7ba7e2b8 (main)
queue: [API7, CORE11, CORE13, CORE14, CORE17, CORE15, CORE16, CORE12, REV2, REM3, API5, LOAD8, LOAD9, LOAD10, LOAD12, LIN4, GRAPH1, GRAPH4, GRAPH7, META2, AGENT2, DEEP1, Q28]
other_queue: [CFG14, PORT11, PLAN13, MM13, ONT4, N23, J70, ONT5, GRAPH2, GRAPH3, GRAPH5, GRAPH6, DOC10, DOC11, META1, MM7, Y3, O48, N17, G86, G85]
pens: [code:drydocs-api, code:drydocs-core, code:drydocs-review, code:drydocs-remediation, code:drydocs-load, code:drydocs-lineage, code:graph-infra, code:drydocs-docmeta, code:drydocs-agents, code:drydocs-deepdoc, code:config]
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
pen: code:drydocs-api · code:drydocs-core · code:drydocs-review · code:drydocs-remediation · code:drydocs-load · code:drydocs-lineage · code:graph-infra · code:drydocs-docmeta · code:drydocs-agents · code:drydocs-deepdoc · code:config
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

## Your queue, in order (23 items) — claim one at a time

Every item below is `todo` with every dependency `done` at the generating commit — the
same rule the board's Ready strip uses (`derive_summary`). Re-check on pull: the other
lane may have moved something. The split is by MODULE (the id series is the module
since PLAN1), so two lanes minting in disjoint series cannot collide on a number.

| # | Id | Title | Type / prio | Module | Model | Notes from the check |
|---|---|---|---|---|---|---|
| 1 | **API7** | The intake write handlers commit before the only ownership check, so a cross-persona mutation lands and the 403 the caller receives is cosmetic - move the check to before the write, not to the return value | task / p1 | `drydocs-api` | sonnet | notes say machine-local; overlap: API7 <-> O48: `drydocs_api` (O48's input, coarse) covers `drydocs_api/intake.py` |
| 2 | **CORE11** | Raise drydocs_core.Neo4jClient to the level of its two younger siblings - a read access mode, captured driver notifications - and record in an ADR whether drydocs_api and the agents adopt it or stay separate | task / p2 | `drydocs-core` | fable | input `docs/decisions/README.md` — pen `adr` (ADRs and their index); overlap: CORE11 <-> O48: `drydocs_api` (O48's input, coarse) covers `drydocs_api/app.py` |
| 3 | **CORE13** | Give core's Neo4j client a timeout and retry policy - nothing in drydocs_core sets a transaction timeout, a retry ceiling or an acquisition timeout, so an unreachable server hangs the caller | task / p2 | `drydocs-core` | sonnet | clean |
| 4 | **CORE14** | apoc_available() collapses every failure to False - it must tell 'cannot reach the server' from 'APOC not installed' instead of catching bare Exception | bug / p3 | `drydocs-core` | sonnet | clean |
| 5 | **CORE17** | The liveness_check_timeout=0 comment in neo4j_client.py justifies the setting by naming Aura, a platform retired 2026-07-06 - rewrite it against the platform we run | chore / p3 | `drydocs-core` | haiku | clean |
| 6 | **CORE15** | run_log's four silent-degradation handlers log nothing - each except-Exception path names what degraded, and the four untested branches gain tests | bug / p3 | `drydocs-core` | sonnet | clean |
| 7 | **CORE16** | Remove the three type-ignore[assignment] escapes in the adapters by typing the handles Optional and narrowing after connect() | chore / p3 | `drydocs-core` | haiku | clean |
| 8 | **CORE12** | Declare drydocs_core's public surface once - grow __all__ to match reality, mark internals by convention, or give the boundary test a second axis - so 22 of 34 core modules stop being imported outside any declared contract | task / p3 | `drydocs-core` | fable | clean |
| 9 | **REV2** | graph_verify's acceptance runner cannot fail on an empty graph in four of six suites - every suite declares an anchor, the runner evaluates it first, and a suite whose anchor fails reports NOT RUN instead of PASS | bug / p1 | `drydocs-review` | sonnet | overlap: REV2 <-> GRAPH5: `drydocs/review` (GRAPH5's input, coarse) covers `drydocs/review/graph_verify.py` |
| 10 | **REM3** | detect_all() returns findings with no rule denominator, so an empty list reads as 'conforms' when it means 'no violations among the 17 of 45 rules implemented' - return the evaluated rule ids beside the findings and carry them into the profile | task / p2 | `drydocs-remediation` | sonnet | clean |
| 11 | **API5** | A graph outage answers 500, which the console reads as a bug rather than 'service down' - one exception handler maps Neo4j driver failures to 503 and passes the exception class only, never its message | bug / p2 | `drydocs-api` | sonnet | overlap: API5 <-> O48: `drydocs_api` (O48's input, coarse) covers `drydocs_api/app.py` |
| 12 | **LOAD8** | A scoped or sampled load writes a :JobRun indistinguishable from a full one - the run node records its scope binds and row cap, never the raw argv, so a sample cannot pass for the population | task / p2 | `drydocs-load` | sonnet | clean |
| 13 | **LOAD9** | An absent run log is silent - keep a load non-fatal when DRYDOCS_LOGDIR is unwritable, but say so in the end-of-run summary the operator reads | task / p3 | `drydocs-load` | sonnet | clean |
| 14 | **LOAD10** | Collapse catalog.py's eleven duplicated field-validator wrappers into shared Annotated aliases so a model that diverges from the helper becomes inexpressible | chore / p3 | `drydocs-load` | sonnet | clean |
| 15 | **LOAD12** | The resolution summary reports matched_dns_resolved: 0 for a tier that has no writer - distinguish 'no writer' from 'no matches' so the zero stops asserting a false claim | bug / p3 | `drydocs-load` | sonnet | clean |
| 16 | **LIN4** | rua_inventory reads a bundle envelope without checking its collector version, so a newer bundle parses silently at full apparent confidence - validate it the way lb_resolution.py already does | bug / p3 | `drydocs-lineage` | sonnet | clean |
| 17 | **GRAPH1** | The module-boundary guard sees static imports only - teach it importlib.import_module and __import__ with a string constant, and declare the drydocs.port.reconcile_before to drydocs_remediation crossing | bug / p1 | `graph-infra` | sonnet | overlap: GRAPH1 <-> GRAPH2: both name `drydocs/port/reconcile_before.py`; overlap: GRAPH1 <-> GRAPH5: `drydocs/port` (GRAPH5's input, coarse) covers `drydocs/port/reconcile_before.py` |
| 18 | **GRAPH4** | Triage the eighteen test guards that read raw source against J66's exception, convert the code-subject ones to tests/source_scan.py, fold in test_remediation_changes.py's open instance, and decide whether source_scan becomes mandatory | task / p2 | `graph-infra` | sonnet | clean |
| 19 | **GRAPH7** | Retire the AIS typo-label guard - it asserts a fact about the company's tree from the producer's, passes vacuously here because the labels never existed, and has had no subject on either side since the company removed them | task / p2 | `graph-infra` | sonnet | clean |
| 20 | **META2** | Use case 3's gate-free half - register the legacy-capture corpus as a doc-source-registry row (the producer ships the SHAPE as a synthetic row) so a legacy process can be captured as documents and SME notes before it is lost | task / p2 | `drydocs-docmeta` | sonnet | overlap: META2 <-> GRAPH5: `drydocs/review` (GRAPH5's input, coarse) covers `drydocs/review/sme_notes.py` |
| 21 | **AGENT2** | Retire the nine-copy sys.path preamble in agents/ - a hard-coded parents[2] plus thirteen E402 suppressions - by installing the repo into agents/.venv as a path dependency, or hoisting one bootstrap module | chore / p3 | `drydocs-agents` | sonnet | clean |
| 22 | **DEEP1** | investigate.py's opening docstring still describes the reactive on-failure model retired at G32 - restate the corpus-driven-retriever charter or point at __init__ | chore / p3 | `drydocs-deepdoc` | haiku | clean |
| 23 | **Q28** | Register the BMC Control-M 9.0.21 Parameters tree as a doc corpus — the scraper can capture it, but corpus_id None makes conversion refuse rather than guess | task / p2 | `config` | sonnet | clean |

**Flags to rule before claiming** (the script flags; the author decides):

- API7: notes say machine-local — does the laptop have it? If not, this item belongs to the other lane or waits for the file to be copied over.
- CORE11: input `docs/decisions/README.md` — pen `adr` (ADRs and their index) — Lane A's pen; coordinate before editing.

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
| Lane A's queue | the items CFG14, PORT11, PLAN13, MM13, ONT4, N23, J70, ONT5, GRAPH2, GRAPH3, GRAPH5, GRAPH6, DOC10, DOC11, META1, MM7, Y3, O48, N17, G86, G85 and their inputs | do not claim or edit |
| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |
| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — Lane A regenerates once at close; nobody merges them by hand (J43) |

**About Lane A's queue, from the same check** (for the sender to rule — this lane
does nothing with these):

- ONT4: not ready — depends on ['MM13'] (not all done)
- MM13: gate-bound: data-flow-overview (an SME session, not a build)
- N23: gate-bound: registry-wiring-readiness (an SME session, not a build)
- J70: gate-bound: schema-identifier-publish-ceiling-teams-edition (an SME session, not a build)
- MM7: input `internal-local/deepdoc/2026-08-20-session-1/transcripts/controlm-evidence-capture.md` is machine-local
- MM7: notes say machine-local

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

## Sender's rulings — read these before the queue

Lane A ruled each flag the check raised rather than passing them through. Nothing below is a
guess; where a flag is a false positive it says so and why.

**Three items are already yours and IN FLIGHT — they are not in the queue above because the
generator refuses a claimed item, not because they are gone.** `LOAD13` (the base's finish line
as a test), `LOAD14` (the stand-ins coverage report) and `DOC12` (the two-tab Excel run book from
the graph) are all `in_progress` on your claims. They are the highest-value work on either lane —
Phase 2's exit criterion is that finish line — so finish them before pulling anything new.

**`API7` is new, it is p1, and it is the one to take first after the three above.** It came out of
the console-auth-boundary gate on 2026-09-10: the intake write handlers authorize by ROLE only,
and the sole per-record ownership test runs inside `get_intake`, which they call as their RETURN
VALUE — after the commit. A cross-persona write lands and the caller gets a 403 over the top of
it. Read its acceptance carefully: the test must assert the record is UNCHANGED after the
refusal, because asserting only that `Forbidden` was raised passes today, against the bug.

**`CORE11` is SPLIT, and this is the one ruling that changes how you work an item.** It moved to
your lane because five of your items touch `drydocs_core/neo4j_client.py` and it was sitting in
Lane A's queue causing six collisions. But its acceptance MINTS AN ADR, and `docs/decisions/**`
plus the ADR index are Lane A's `adr` pen. So: **you build the code and draft the ADR body; Lane A
mints the number and commits the index row.** That is the protocol CLAUDE.md already describes for
ADR numbering — a pushed index line reserves a number for a draft that does not exist yet — and it
maps onto the pen split without inventing anything. Put the draft and the title you want in the
item's notes; do not add a row to `docs/decisions/README.md`.

**`GRAPH1` and Lane A's `GRAPH2` both write `drydocs/port/reconcile_before.py`.** Ordering ruled:
**you take GRAPH1, and Lane A does not start GRAPH2 until GRAPH1 has merged.** That one file is
the single `drydocs/port` surface this lane touches — the carve-out the plan made once PORT8
landed — and it stays a carve-out, not an opening of the port pen.

**Flags that are false positives, ruled and taken knowingly:**

- `API7: notes say machine-local` — the phrase appears in the item's PROSE ("secrets are
  machine-local"), not in a declared `venue:`. Both of its inputs are tracked files and it builds
  anywhere. This is the exact defect the declared `venue:` field was added to end (PLAN6), showing
  up on a fresh item; PLAN13 is where the check gets fixed, and it is Lane A's.
- `REV2`, `META2`, `GRAPH1` overlapping `GRAPH5` — every one is `GRAPH5`'s coarse inputs
  (`drydocs/review`, `drydocs/port`) matching a specific file. GRAPH5 is the ADR 0018 shim removal:
  it is Phase 7, it is scheduled AFTER the ninth roll, and Lane A has not started it. Take all
  three.
- `API7`, `CORE11`, `API5` overlapping `O48` — all three are `O48`'s coarse `drydocs_api` input.
  O48 is parked on Lane A's list and not started. Take all three.

**Two items left your queue, and neither is dropped work.** `G86` and `G85` are `drydocs-web` and
they moved off this lane so that ONE session holds the web pen — see the fence below. `O48` and
`N17` are parked on Lane A's side: O48 collided six ways with Lane A's ontology work, and N17
writes `config/source-registry.yaml`, which N23 and J70 are about to move for sitting 2.

## The fence has a third session in it now

There are **three** sessions on this trunk, not two, and the new one is on the SAME MACHINE as
Lane A.

| Session | Where | Holds |
|---|---|---|
| Lane A | desktop, `main` | `backlog`, `port`, `adr`, `gates`, `snapshot` |
| **you**, Lane B | laptop, `wip/<id>-laptop` | the code pens listed above |
| UI workstream | desktop, worktree, branch `feat/web-completeness` | **`code:drydocs-web`** and `config/taxonomy/ui-components.yaml` |

**`code:drydocs-web` is NOT yours this burst.** The previous issue of this file gave it to you and
also fenced `config/taxonomy/ui-components.yaml` here; both moved on 2026-09-10, because the items
that write them (WEB19, WEB20, WEB21, WEB23) are the UI session's under the SME's ruling. If a
queued item of yours needs a `.tsx` change or an O42 row, put it in the item's notes and Lane A
carries it across — do not edit `web/src/**` or that ledger.

Its handoff is `docs/lane-ui-handoff.md` if you want to see what it holds.

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
