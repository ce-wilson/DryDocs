---
handoff: drydocs.lane-handoff.v1
lane: B
machine: laptop
generated: 2026-09-09
generated_at: 7ed742d2 (main)
queue: [LOAD13, LOAD14, DOC12, REV2, REM3, API5, LOAD8, LOAD9, LOAD10, LOAD12, LIN4, CORE13, CORE14, CORE15, CORE16, CORE17, GRAPH1, GRAPH4, META2, AGENT2, DEEP1, O48, Q28, N17, G86, G85]
other_queue: [PORT8, PLAN12, CFG7, CFG8, CORE10, GRAPH5, CORE18, PLAN13, MM13, WEB22, GRAPH2, GRAPH3, CORE11, CORE12, DOC10, DOC11, N23, J70, ONT5, GRAPH6, META1, MM7, Y3]
pens: [code:drydocs-load, code:docs, code:drydocs-review, code:drydocs-remediation, code:drydocs-api, code:drydocs-lineage, code:drydocs-core, code:graph-infra, code:drydocs-docmeta, code:drydocs-agents, code:drydocs-deepdoc, code:config, code:drydocs-web]
---

# Lane B handoff — laptop, 2026-09-09

**From:** Lane A (desktop). **To:** the Lane B session on the laptop.
**Lifecycle:** a working handoff, not a durable record — the item files are. When
the queue below is empty, delete this file in the closing commit
(`python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` says when).

## Pens — declare them in your first commit (CLAUDE.md §0, one pen per surface)

Collisions come from two sessions writing the same surface, not from two sessions
existing. Your first commit message (or your `wip/` branch name) names what you hold:

```text
pen: code:drydocs-load · code:docs · code:drydocs-review · code:drydocs-remediation · code:drydocs-api · code:drydocs-lineage · code:drydocs-core · code:graph-infra · code:drydocs-docmeta · code:drydocs-agents · code:drydocs-deepdoc · code:config · code:drydocs-web
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

## Your queue, in order (26 items) — claim one at a time

Every item below is `todo` with every dependency `done` at the generating commit — the
same rule the board's Ready strip uses (`derive_summary`). Re-check on pull: the other
lane may have moved something. The split is by MODULE (the id series is the module
since PLAN1), so two lanes minting in disjoint series cannot collide on a number.

| # | Id | Title | Type / prio | Module | Model | Notes from the check |
|---|---|---|---|---|---|---|
| 1 | **LOAD13** | The base's finish line, as a test - from a clean clone, extract the synthetic stand-ins, bootstrap, ingest, verify, report coverage and generate both runbooks, every step green or skipped with its reason | task / p1 | `drydocs-load` | sonnet | overlap: LOAD13 <-> CORE18: both name `drydocs/source_registration/bundle.py` |
| 2 | **LOAD14** | A coverage report over the stand-ins' object classes - folders, jobs, datasets, docs - so the base says which classes it reached and why the rest did not, with not-probed never rendered as zero | task / p2 | `drydocs-load` | sonnet | overlap: LOAD14 <-> CFG8: both name `config/source-descriptors.yaml`; overlap: LOAD14 <-> CORE10: both name `drydocs/docs_coverage.py`; overlap: LOAD14 <-> CORE10: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/docs_verify.py`; overlap: LOAD14 <-> CORE18: both name `config/source-registry.yaml`; overlap: LOAD14 <-> CORE18: both name `config/source-descriptors.yaml`; overlap: LOAD14 <-> N23: both name `config/source-registry.yaml`; overlap: LOAD14 <-> J70: both name `config/source-registry.yaml` |
| 3 | **DOC12** | Generate the two-tab Excel Application Run Book FROM THE GRAPH - the sibling L23's long-form generator implies - filling the 31 graph-derivable columns from the runbooks QuerySpecs and marking every manual cell as needing capture | task / p2 | `docs` | sonnet | clean |
| 4 | **REV2** | graph_verify's acceptance runner cannot fail on an empty graph in four of six suites - every suite declares an anchor, the runner evaluates it first, and a suite whose anchor fails reports NOT RUN instead of PASS | bug / p1 | `drydocs-review` | sonnet | overlap: REV2 <-> GRAPH5: `drydocs/review` (GRAPH5's input, coarse) covers `drydocs/review/graph_verify.py` |
| 5 | **REM3** | detect_all() returns findings with no rule denominator, so an empty list reads as 'conforms' when it means 'no violations among the 17 of 45 rules implemented' - return the evaluated rule ids beside the findings and carry them into the profile | task / p2 | `drydocs-remediation` | sonnet | clean |
| 6 | **API5** | A graph outage answers 500, which the console reads as a bug rather than 'service down' - one exception handler maps Neo4j driver failures to 503 and passes the exception class only, never its message | bug / p2 | `drydocs-api` | sonnet | overlap: API5 <-> CORE11: both name `drydocs_api/app.py` |
| 7 | **LOAD8** | A scoped or sampled load writes a :JobRun indistinguishable from a full one - the run node records its scope binds and row cap, never the raw argv, so a sample cannot pass for the population | task / p2 | `drydocs-load` | sonnet | clean |
| 8 | **LOAD9** | An absent run log is silent - keep a load non-fatal when DRYDOCS_LOGDIR is unwritable, but say so in the end-of-run summary the operator reads | task / p3 | `drydocs-load` | sonnet | overlap: LOAD9 <-> CORE10: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/run_log.py` |
| 9 | **LOAD10** | Collapse catalog.py's eleven duplicated field-validator wrappers into shared Annotated aliases so a model that diverges from the helper becomes inexpressible | chore / p3 | `drydocs-load` | sonnet | clean |
| 10 | **LOAD12** | The resolution summary reports matched_dns_resolved: 0 for a tier that has no writer - distinguish 'no writer' from 'no matches' so the zero stops asserting a false claim | bug / p3 | `drydocs-load` | sonnet | clean |
| 11 | **LIN4** | rua_inventory reads a bundle envelope without checking its collector version, so a newer bundle parses silently at full apparent confidence - validate it the way lb_resolution.py already does | bug / p3 | `drydocs-lineage` | sonnet | clean |
| 12 | **CORE13** | Give core's Neo4j client a timeout and retry policy - nothing in drydocs_core sets a transaction timeout, a retry ceiling or an acquisition timeout, so an unreachable server hangs the caller | task / p2 | `drydocs-core` | sonnet | overlap: CORE13 <-> CORE10: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/neo4j_client.py`; overlap: CORE13 <-> CORE11: both name `drydocs_core/neo4j_client.py` |
| 13 | **CORE14** | apoc_available() collapses every failure to False - it must tell 'cannot reach the server' from 'APOC not installed' instead of catching bare Exception | bug / p3 | `drydocs-core` | sonnet | overlap: CORE14 <-> CORE10: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/neo4j_client.py`; overlap: CORE14 <-> CORE11: both name `drydocs_core/neo4j_client.py` |
| 14 | **CORE15** | run_log's four silent-degradation handlers log nothing - each except-Exception path names what degraded, and the four untested branches gain tests | bug / p3 | `drydocs-core` | sonnet | overlap: CORE15 <-> CORE10: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/run_log.py` |
| 15 | **CORE16** | Remove the three type-ignore[assignment] escapes in the adapters by typing the handles Optional and narrowing after connect() | chore / p3 | `drydocs-core` | haiku | overlap: CORE16 <-> CORE10: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/adapters/csv_adapter.py`; overlap: CORE16 <-> CORE10: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/adapters/oracle_adapter.py` |
| 16 | **CORE17** | The liveness_check_timeout=0 comment in neo4j_client.py justifies the setting by naming Aura, a platform retired 2026-07-06 - rewrite it against the platform we run | chore / p3 | `drydocs-core` | haiku | overlap: CORE17 <-> CORE10: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/neo4j_client.py`; overlap: CORE17 <-> CORE11: both name `drydocs_core/neo4j_client.py` |
| 17 | **GRAPH1** | The module-boundary guard sees static imports only - teach it importlib.import_module and __import__ with a string constant, and declare the drydocs.port.reconcile_before to drydocs_remediation crossing | bug / p1 | `graph-infra` | sonnet | overlap: GRAPH1 <-> CORE10: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/component_map.py`; overlap: GRAPH1 <-> GRAPH5: `drydocs/port` (GRAPH5's input, coarse) covers `drydocs/port/reconcile_before.py`; overlap: GRAPH1 <-> GRAPH2: both name `drydocs/port/reconcile_before.py`; overlap: GRAPH1 <-> CORE12: both name `tests/unit/test_module_boundary.py` |
| 18 | **GRAPH4** | Triage the eighteen test guards that read raw source against J66's exception, convert the code-subject ones to tests/source_scan.py, fold in test_remediation_changes.py's open instance, and decide whether source_scan becomes mandatory | task / p2 | `graph-infra` | sonnet | overlap: GRAPH4 <-> CORE10: both name `tests/source_scan.py` |
| 19 | **META2** | Use case 3's gate-free half - register the legacy-capture corpus as a doc-source-registry row (the producer ships the SHAPE as a synthetic row) so a legacy process can be captured as documents and SME notes before it is lost | task / p2 | `drydocs-docmeta` | sonnet | overlap: META2 <-> GRAPH5: `drydocs/review` (GRAPH5's input, coarse) covers `drydocs/review/sme_notes.py` |
| 20 | **AGENT2** | Retire the nine-copy sys.path preamble in agents/ - a hard-coded parents[2] plus thirteen E402 suppressions - by installing the repo into agents/.venv as a path dependency, or hoisting one bootstrap module | chore / p3 | `drydocs-agents` | sonnet | overlap: AGENT2 <-> CORE11: `agents` (AGENT2's input, coarse) covers `agents/common/neo4j_tool.py`; overlap: AGENT2 <-> CORE11: `agents/common` (AGENT2's input, coarse) covers `agents/common/neo4j_tool.py` |
| 21 | **DEEP1** | investigate.py's opening docstring still describes the reactive on-failure model retired at G32 - restate the corpus-driven-retriever charter or point at __init__ | chore / p3 | `drydocs-deepdoc` | haiku | clean |
| 22 | **O48** | Review-for-ontology pass: extraction over uploaded evidence → proposed-bindings panel the SME confirms (the CDO-style review) (after O47) | requirement / p2 | `drydocs-api` | sonnet | overlap: O48 <-> CORE10: `drydocs_core` (CORE10's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary`; overlap: O48 <-> CORE11: `drydocs_api` (O48's input, coarse) covers `drydocs_api/app.py`; overlap: O48 <-> J70: `drydocs_core/ontology/relationship_vocabulary` (O48's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary/41-local-business-application.yaml`; overlap: O48 <-> ONT5: `drydocs_core/ontology/relationship_vocabulary` (O48's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary/10-node-classifications.yaml`; overlap: O48 <-> ONT5: `drydocs_core/ontology/relationship_vocabulary` (O48's input, coarse) covers `drydocs_core/ontology/relationship_vocabulary/42-local-catalog.yaml`; overlap: O48 <-> Y3: both name `drydocs_core/ontology/relationship_vocabulary` |
| 23 | **Q28** | Register the BMC Control-M 9.0.21 Parameters tree as a doc corpus — the scraper can capture it, but corpus_id None makes conversion refuse rather than guess | task / p2 | `config` | sonnet | clean |
| 24 | **N17** | The derived join key ripple sweep is now desk work — say which psgmgr objects carry it, and record the answer in the column ledger rather than a new document | chore / p2 | `config` | sonnet | overlap: N17 <-> CORE18: both name `config/source-registry.yaml`; overlap: N17 <-> N23: both name `config/source-registry.yaml`; overlap: N17 <-> J70: both name `config/source-registry.yaml` |
| 25 | **G86** | Calendars: can a RULE_BASED_CALENDAR be validated, and can it render as an actual calendar in the console? | task / p3 | `drydocs-web` | sonnet | clean |
| 26 | **G85** | Agent lookup beside the fix diff — cite the vendor→standards→team chain from the verified BMC corpus | requirement / p3 | `drydocs-web` | opus | clean |

**Sender rulings on the flags and the order** (Lane A, desktop, 2026-09-09 - third issue of this
file, at the mint-pass tip `7ed742d2`; the first two issues closed at the Lane A close `1bd22b50`,
where seven of your items merged `--no-ff`):

- **Order.** LOAD13 first - it is the base's finish line and every later item is judged against
  it. Then LOAD14 and DOC12 (use case 1's two deliverables), then the p1 guard REV2, then the
  module-local items grouped one branch per module (REM3; API5; LOAD8, LOAD9, LOAD10, LOAD12;
  LIN4; CORE13 to CORE17; GRAPH1 then GRAPH4; META2; AGENT2; DEEP1), then the carried tail
  (O48, Q28, N17, G86, G85 - the 2026-09-09 rulings on those five stand unchanged).
- **The `drydocs_core` overlaps with CORE10 are not collisions.** CORE10 adds ONE new module and
  a registry to core and adopts the type in the preflight and the coverage report; it edits
  neither neo4j_client.py, run_log.py, the adapters, component_map.py nor tests/source_scan.py.
  Your CORE13 to CORE17, LOAD9, GRAPH1 and GRAPH4 proceed. CORE10 itself waits for ADR 0021's
  acceptance at sitting 1, so it lands after yours in any case.
- **LOAD14 before CORE10 on drydocs/docs_coverage.py.** LOAD14 extends the report's existing
  shape and READS config/source-registry.yaml and config/source-descriptors.yaml, never writes
  them; CORE10 then expresses None-for-not-probed through the type once it exists. Build LOAD14
  on today's shape.
- **LOAD13 reads drydocs/source_registration/bundle.py; CORE18 moves its repo/ prefix later.**
  If the extraction needs a change for the test to run, write it in LOAD13's notes for Lane A
  rather than editing bundle.py; CORE18 lands after the wired build.
- **CORE11 is an ADR first.** Your CORE13, CORE14, CORE17 and API5 touch neo4j_client.py and
  drydocs_api/app.py before CORE11 rules anything; CORE11's draft reads the tree as it then is,
  and no API or agents code moves until that ADR is accepted. AGENT2 touches import preambles
  only. CORE13's timeout values are recorded in its notes so API6 (Lane A) can read them.
- **GRAPH1 waits for PORT8 on origin, and GRAPH5 waits for you.** GRAPH1 edits
  drydocs/port/reconcile_before.py, the one drydocs/port file you touch this burst; PORT8 (the
  preflight fix) is the first thing Lane A lands, so pull before you claim GRAPH1. GRAPH5 (the
  shim removal) touches drydocs/review and drydocs/port and is sequenced after the eighth roll
  AND after your REV2, META2 and GRAPH1 branches merge - Lane A holds it until then.
- **No web items in this queue.** WEB19, WEB20 and WEB21 belong to the UI-testing session's
  code:drydocs-web pen by user ruling; G86 and G85 stay yours as before.
- **L23 stays in flight on `wip/l23-laptop`** and is not re-queued; close it as you would have.
- **Ideas from this burst.** Until PLAN13 lands the capture path is still the close report; once
  it lands, `docs/restructure/ideas/pending-<branch>.md` on your branch (PLAN4 d) and Lane A
  mints at the merge.
- **Every close runs the J57 family plus `test_skip_guard_policy.py` and
  `test_never_port_citations.py`**, as the previous issue said; a clean targeted run is not a
  clean claim.

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
| Lane A's queue | the items PORT8, PLAN12, CFG7, CFG8, CORE10, GRAPH5, CORE18, PLAN13, MM13, WEB22, GRAPH2, GRAPH3, CORE11, CORE12, DOC10, DOC11, N23, J70, ONT5, GRAPH6, META1, MM7, Y3 and their inputs | do not claim or edit |
| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |
| `code:drydocs-web` | `config/taxonomy/ui-components.yaml` | this lane, with the module — the O42 ledger guard fails on any new .tsx, so every web item adds its row here (the 2026-09-05 Lane B close: five items touched it, none named it) |
| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — Lane A regenerates once at close; nobody merges them by hand (J43) |

**About Lane A's queue, from the same check** (for the sender to rule — this lane
does nothing with these):

- MM13: gate-bound: data-flow-overview (an SME session, not a build)
- WEB22: gate-bound: console-auth-boundary (an SME session, not a build)
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
