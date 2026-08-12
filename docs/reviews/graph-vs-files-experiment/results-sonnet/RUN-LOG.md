# RUN LOG — sonnet run, 2026-08-11

Authority: [`PROTOCOL.md`](../PROTOCOL.md) + [`PROTOCOL-sonnet-20260811.md`](../PROTOCOL-sonnet-20260811.md).
Model pinned **sonnet** everywhere the 2026-08-10 run used haiku.
**Track labels ROTATE this run: ALPHA = GRAPH, BETA = FILES** (the reverse of 2026-08-10).
Fable is not told which is which until review 2.

Venue (J18): **desktop**, container `neo4jtest`, database `drydocs`.
All times local (EDT). Workers were told **not** to report timestamps — the orchestrator
stamps every one below.

---

## Step 0 — graph reload (mandatory, before any dispatch)

**03:07 — tree state on arrival.** `main` @ `a5319a3`. A second live session shares this
tree and holds uncommitted work in flight (C30/G67): modified
`drydocs_lineage/extractors/controlm_xml.py`, `drydocs_remediation/{__init__,detect,formats}.py`;
untracked `drydocs_remediation/xml_bridge.py`, `tests/unit/test_remediation_conformance.py`,
`tests/unit/test_remediation_xml_bridge.py`. Never touched, never staged.

**Snapshot decision — did NOT re-run `snapshot.ps1`; loaded the existing one. Reasoning
recorded because it is a deviation from the addendum's literal instruction.**

The addendum says re-snapshot "if the tree has moved since the drydocs-20260810-0437
snapshot." It has — but a **fresh snapshot already exists**, written 00:33 today:
`knowledge/depgraph-snapshots/drydocs-20260811.json` @ `5613ea0`, `dirty: false`,
`untracked_present: false`, depgraph instrument `main @ 6ee0af6` with
`multi_root`/`tree`/`ts_imports` all true. HEAD is **3 commits past** that snapshot and
`git diff --name-only 5613ea0..HEAD` is **docs-only** — `board.html`, `roadmap.html`,
`backlog.yaml`, the depgraph json itself, and two `.md` captures. **No code file moved.**

Re-running `snapshot.ps1` would have (a) embedded the other session's in-flight WIP into a
tracked artifact with `dirty: true`, and (b) deleted the clean committed snapshot under the
U12 newest-only retention rule — in a tree a second session may commit from at any moment.
That trades a real hazard for zero code-structure currency. The purpose of the addendum's
step 0 — *the graph track must not be measuring staleness* — is met by `5613ea0`.

**03:10 — `poetry run drydocs load-code-snapshot`.** Loaded
`drydocs-20260811.json`. Status `OK`, 0 rows rejected, 0 unresolved parents.

| | |
|---|---|
| snapshot | `knowledge/depgraph-snapshots/drydocs-20260811.json` |
| snapshot commit | `5613ea0` (branch `main`, clean, untracked absent) |
| `:CodeModule` total | **1480** |
| `:CodeModule` live (`removed_from_source_at IS NULL`) | **1465** |
| `:CodeDirectory` | 270 |
| `IMPORTS` edges | 891 |
| `(:Project)` `git_commit` / `git_dirty` | `5613ea0` / `false` |

**Currency spot-checks** (the exact files the addendum named as the 2026-08-10 gap):

- `web/src/routes/IntakeRoute.tsx` — present, live
- `drydocs/port_preflight.py`, `scripts/port_preflight.py`, `tests/unit/test_port_preflight.py` — present, live
- `web/src/components/HeroArt.tsx` — present and **soft-deleted** (`removed_from_source_at` set at load), which is the loader behaving correctly on the O53 deletion
- `web/src/underhood/benchmarkData.ts` — present, live (the O31 target)

The graph is current for code. **The graph track was NOT run stale; no abort.**

**Git changes produced by step 0: none.** The load writes only to Neo4j, and no snapshot
was rewritten. `docs/reviews/graph-vs-files-experiment/results-sonnet/` is the only new path.

---

## Phase 1 — planning (Ideas 96–103), both tracks in parallel

Prompt = `prompts/planning-shared.md` **verbatim, byte-identical to 2026-08-10** (the
cross-day haiku-vs-sonnet comparison depends on it) + the track block + a dispatch block.
Agent type `backlog-groomer` both sides, model `sonnet`, both backgrounded.

The dispatch block carries three things the prompt files do not: the results paths; a
**supersede line** for `track-graph.md`'s hardcoded `bd051ab` snapshot reference (now
`5613ea0`, with the reload counts); and the **no-timestamps** instruction that deletes the
`started/finished` line from the METRICS block (fix 3 — both 2026-08-10 planning runs
fabricated theirs). `track-graph.md` and `track-files.md` themselves are unedited.

### Orchestrator-observed metrics (ground truth per fix 4)

| | dispatched | completed | duration | tool uses (observed) | tokens | tool uses (self-report) |
|---|---|---|---|---|---|---|
| ALPHA (GRAPH) | 03:12 | 03:21 | **563.0s** | **32** | 129,803 | 30 |
| BETA (FILES) | 03:12 | 03:21 | **530.0s** | **55** | 140,633 | 43 |

Self-report discrepancy: ALPHA **−6.3%** (30 vs 32), BETA **−21.8%** (43 vs 55). Both sit
well inside haiku's 34–65% under-report band; ALPHA is nearly exact. Neither reported a
timestamp — the fix-3 instruction held on both sides.

**Artifacts written** (both tracks wrote the deliverable AND the `-report.md` twin, so fix 1
held):

- `planning-ALPHA.md` / `planning-ALPHA-report.md` (28,384 bytes, byte-identical)
- `planning-ALPHA-scratch.py`, `-scratch2.py`, `-scratch3.py` — the graph track archived its
  query scripts (fix 2, planning half)
- `planning-BETA.md` / `planning-BETA-report.md` (23,448 bytes, byte-identical)

**Headline shape, before fable scores anything:** the graph track ran **42% fewer tool
uses** (32 vs 55) and **8% fewer tokens** for **6% more wall-clock**. That inverts the
2026-08-10 direction on time (graph was 15.6% *faster* at haiku) while widening the tool-use
gap (26 vs 41 = 37% at haiku).

**One thing for fable, not pre-judged here.** ALPHA's own METRICS block lists seven `Grep`
calls, every one scoped to `IDEAS.md` or `backlog.yaml`. Its rule block forbids Grep but
exempts those two files as task inputs that "may be read directly." Whether a scoped Grep of
an exempt file is permitted reading or a forbidden search is not settled by the rule text.
That is a compliance call and it belongs to the reviewer; the dispatch asked fable to state
its reading explicitly rather than resolve it by reflex.

---

## Phase 2 — fable review 1 (blind)

Dispatched **03:23**, model `fable`. Given both plan paths, the two rule sets as rule text
attached to labels but **not** to track identity, and an explicit warning not to infer the
label↔method mapping from the earlier run — the rotation exists precisely to catch that.
Writing to `results-sonnet/fable-review-1.md`. Completed **03:28**, 304.3s, 23 tool uses,
109,830 tokens.

| Dimension | ALPHA (graph) | BETA (files) |
|---|---|---|
| Accuracy | 6 | 9 |
| Completeness | 5 | 9 |
| Sizing | 6 | 9 |
| Convention fidelity | 7 | 9 |
| Compliance | VALID | VALID |

Fable hands **BETA** to the SME. The findings that decided it, both verifiable:

- **ALPHA's structural claims are the stronger evidence** where the graph applies. Its
  `manual_loads.py` fan-in of 5 is exactly right where a naive grep over-counts to 6 — the
  sixth hit references the module by path inside a `read_text`, not an import — and it caught
  two function-local imports besides. The thin-importer claim
  (`scripts/port_preflight.py` → `drydocs/port_preflight.py`) holds at line 21.
- **ALPHA made the one error that costs the SME real time.** It promoted Idea-99 as a new
  item requiring `port-prompt.md` to gain a DPL/Snowflake relay line — but that relay
  **already exists** as RELAY-5 at `docs/port-prompt.md:743`, dated 2026-08-09. ALPHA
  confirmed the file's *graph node* existed and never read its *content*. The drafted
  acceptance is already true in the tree: a no-op item.
- **ALPHA's drafts are missing `title`, `type` and `status` on every item** — three of the
  twelve `REQUIRED_FIELDS` in `test_backlog.py`. BETA's carry all twelve.

**Compliance call, reasoned rather than reflexed:** fable read ALPHA's seven exempt-file
Greps as permitted *reading*, on the ground that a file-pinned Grep can only surface content
a licensed full Read would surface and discovers no paths — the strict-literal reading would
make the exemption self-defeating. Both plans VALID; fable recorded that ALPHA flips to
INVALID under the strict reading, so the SME can overrule the call without re-running
anything.

## Phase 3 — coding (O31), both tracks in isolated worktrees

Dispatched **03:31**, both `general-purpose` / sonnet / `isolation: worktree`, run as a pair
(not concurrently with fable) so wall-clock stays comparable to the 2026-08-10 coding pair.
Prompt = `prompts/coding-shared-o31.md` + the same track block each side carried in phase 1 +
a dispatch block.

Three things the dispatch adds beyond the results paths:

1. **ALPHA must archive every query script** as `o31-ALPHA-<n>-scratch.py`, with the reason
   stated plainly — the 2026-08-10 graph coding run archived nothing, so nothing proved its
   Cypher had ever run, and fable capped it at 4 for lack of proof (fix 2).
2. **How to run those scripts at all.** A fresh worktree has no installed Python environment,
   which is the most likely mechanical explanation for yesterday's missing scripts. ALPHA is
   told it may run scratch scripts from the main repo root, since the code graph is external
   read-only infrastructure — read from there, never edit there.
3. **Dependency install is named as a shared, equal cost** to both tracks (`npm ci` /
   `poetry install`), to be reported rather than hidden. Both were told to quote command
   output and never assert an unobserved result.

| | dispatched | completed | duration | tool uses (observed) | tokens | self-report |
|---|---|---|---|---|---|---|
| ALPHA (GRAPH) | 03:31 | 04:02 | **1865.5s** | **107** | 309,849 | ~88 |
| BETA (FILES) | 03:31 | 04:03 | **1893.8s** | **117** | 261,340 | 74 |

Both wrote `.diff` + `-report.md` (fix 1). ALPHA archived **five** `o31-ALPHA-<n>-scratch.py`
files (fix 2 — the exact gap that capped the graph track at 4 yesterday; the evidence exists
this time). Neither reported a timestamp (fix 3).

### Two environmental events, both verified by the orchestrator rather than taken on report

**1. The main tree moved mid-experiment — not by any worker.** The second live session
committed and ran its own session-end ritual at ~03:22: HEAD `a5319a3` → `6c24963`, which
rewrote `drydocs-20260811.json` → `drydocs-20260811-0322.json` @ `e1d9ac0` under the U12
newest-only retention rule. The graph had already been loaded at 03:10, so no run was
affected. **This retroactively confirms the step-0 call**: had I run `snapshot.ps1` myself,
the two sessions would have collided on the same retention-governed filename inside twelve
minutes.

**2. Both coding runs accidentally wrote to the MAIN tree, and both caught and restored it.**
The mechanism is shared and environmental, not a defect in either run: `render_*.py` default
paths resolve through the **installed** `drydocs` package, which points at the main repo
regardless of the worktree's cwd. So a worktree agent running the documented one-command
session-ritual regen writes to the main tree.

I verified the restoration independently of both reports:

```
docs/plan/board.html    BYTE-IDENTICAL to HEAD
docs/plan/ideas.html    BYTE-IDENTICAL to HEAD
docs/plan/roadmap.html  BYTE-IDENTICAL to HEAD
git diff --quiet -- docs/plan/   exit=0
```

The lingering ` M` in `git status` is a **stale stat cache** — the rewrite changed mtime, not
content. **Both runs' self-reported recovery claims are CONFIRMED TRUE.** Nothing of the
other session's work was touched, and no experiment artifact leaked into the tree.

This hazard is worth keeping after the experiment ends, independent of who wins: it means
**any** worktree-isolated agent that runs this repo's render ritual silently edits the main
tree. Both tracks found it the hard way, within the same half hour, which is about as strong
a reproduction as one gets.

---

## Phase 4 — fable final grade (unblinded)

Dispatched **04:06**, model `fable`, writing `results-sonnet/GRADES.md`.

Given: the base grading prompt, the addendum's "Grading additions" section verbatim, every
artifact path, the **rotated** track identities with an explicit warning to compare
method-to-method and never label-to-label across days, the orchestrator metrics table as
ground truth, the haiku baseline table from `results/GRADES.md` §2, and the six
orchestrator-established facts above so it need not trust a worker's account of them.

Two corrections carried into the prompt: the coding task is **O31, not O53** (the prompt file
predates the change), and O53's cap rule translates to *"built a regeneration step without
establishing that a real harness run exists and reading it."* Both runs were told in
identical words that a truthful "the harness output does not exist" is a **correct and
complete** outcome, so the cap turns on premise-establishment, not on diff quality.

One open compliance question was handed to fable rather than settled here: o31-ALPHA's
METRICS block self-discloses four "non-graph content lookups" (three greps of `backlog.yaml`,
one `__file__` probe). Review 1 ruled scoped greps of *exempt task-input files* permissible —
but the coding prompt, unlike the planning prompt, names no exempt inputs at all. Fable was
asked to rule explicitly either way, on the stated ground that disclosure is not permission
and is also not nothing.

Completed **04:14**, 509.1s, 32 tool uses, 133,820 tokens. Wrote `GRADES.md` (291 lines).

| Run (method) | Accuracy | Compliance |
|---|---|---|
| planning-ALPHA (**graph**) | 6 | VALID (flips INVALID under the strict-literal Grep reading; condition recorded) |
| planning-BETA (**files**) | 9 | VALID |
| o31-ALPHA (**graph**) | **9** | VALID — explicit ruling on the 4 disclosed non-graph lookups |
| o31-BETA (**files**) | 8 | VALID |

**Neither coding run capped.** Fable verified the O31 premise itself rather than accepting
either account: `benchmark_p0_results.json` is a real 12-question harness run, and it
re-derived the corrected aggregates independently (traversal 15,354 / fulltext 34,195 /
manifest 450,550 chars; full-text recall genuinely **6/12** against the verdict's hand-typed
7/12). Both runs read the real source before building, and their two independent
regenerations converge on identical numbers but for one documented 2-character divergence.
The 2026-08-10 run had no equivalent — both haiku coding runs left the Python guards red.

**The compliance ruling on o31-ALPHA: COMPLIANT.** The three greps were within-file offset
lookups into a file its own archived query 27 had already graph-named, and the `__file__`
probe was forensics on the main-tree incident — outside the experiment's variable. The
strict-literal flip condition is recorded so the SME can overrule without a re-run.

---

## Result — the two headline comparisons

**1. Graph vs files at sonnet.** Planning: **graph HURT, 6 vs 9.** Coding: **a wash on the
deliverable**, decided 9 vs 8 by ledger diligence rather than navigation.

**2. Haiku vs sonnet, planning only** (the sole cross-day-comparable leg — its prompt was
held byte-identical; the coding task changed O53 → O31 and is not comparable):

| | haiku 2026-08-10 | sonnet 2026-08-11 |
|---|---|---|
| graph track accuracy | 6 | **6** |
| files track accuracy | 3 | **9** |
| winner | graph | **files** |

Sonnet eliminated id collisions on **both** tracks and made the `port_preflight.py`-class
structural find track-neutral — it was the graph's signature win at haiku. Cost roughly
doubled, and **the entire quality return went to the files track** (3→9 against the graph's
6→6). Self-report honesty improved across the board: **6.3–36.8%** under-report against
haiku's 34–65% band, with planning-ALPHA nearly exact at 30 vs 32.

**The cross-tier constant, and it is the finding worth keeping.** On both days the winning
track is the one that read the decisive artifact's *content*. Haiku-files never read
`backlog.yaml`'s id series and drafted five colliding ids; sonnet-graph never read
`port-prompt.md` and drafted a no-op item over a relay that already exists. The graph
carries structure; grooming decisions are content decisions.

**And the confound is now gone.** Yesterday's improvement note blamed snapshot staleness.
This run removed it — fresh `5613ea0` reload, verified current — and the same file boundary
still produced the graph track's only planning error and its only compliance strain. So the
limiting factor is **grain, not currency**. Fable's one improvement before a re-run is worth
quoting: push the graph *below file grain* on the acceptance-bearing surfaces — backlog ids
and rollup counts, port-prompt relay entries, guard-test pins as addressable nodes joined to
the modules they govern.

The guard-suite hint (fix 5) landed on both coding runs and changed both outcomes: each
caught and fixed a broken rollup guard of its own making. Both graph runs also *narrated*
their remaining blindness rather than silently working around it, which was the behaviour the
addendum predicted would separate sonnet from haiku.

---

## Close

**Nothing committed, nothing pushed** — per the SME's standing rule, the results are for
review first. Everything lives in
`docs/reviews/graph-vs-files-experiment/results-sonnet/` as untracked files; the sibling
`results/` (haiku) directory was never touched.

The 03:05 cron was one-shot and cleared itself on firing — `CronList` reports no scheduled
jobs, so there is nothing left running from this experiment.

Whatever the SME rules, **one finding is adoptable independent of the graph-vs-files
question**: this repo's `render_*.py` default paths resolve through the installed `drydocs`
package to the main tree, so any worktree-isolated agent running the session-end render
ritual silently writes to the main repo. Two independent tracks reproduced it within the same
half hour, and both recovered cleanly. That belongs in `IDEAS.md` regardless of which code
set is adopted.

> **Filed 2026-08-12 as `Idea-109`**, with the mechanism re-verified on this desktop: the
> editable `drydocs.pth` pins the package to the main tree and `plan_board.py`'s
> `_REPO_ROOT` is derived from `Path(__file__)`, so a `scripts/render_*.py` run — which
> puts `scripts/` on `sys.path[0]` and never the cwd — resolves both its input and its
> output paths to main no matter which worktree the caller stands in.
>
> **Capture correction, same date.** `o31-BETA.diff` as written was a plain `git diff`
> plus a porcelain listing, so it *named* BETA's two untracked files but carried none of
> their content — including `scripts/render_underhood_benchmark.py`, BETA's core
> deliverable. `o31-ALPHA.diff` had already embedded ALPHA's equivalents in full. BETA's
> capture has been brought up to ALPHA's format (744 insertions, 0 deletions; existing
> bytes unchanged), so the two tracks are now captured to the same standard and are
> comparable on the record rather than only in their dirty worktrees. See `Idea-108`.

## Phase 4 — fable final grade

_pending_
