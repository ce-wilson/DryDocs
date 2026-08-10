# Sonnet run — 2026-08-11, 03:05 (addendum to PROTOCOL.md)

Same experiment, **model pinned to `sonnet`** everywhere haiku was. Read
[`PROTOCOL.md`](PROTOCOL.md) first — everything there holds unless contradicted below.

**Two questions this run answers, and they are different questions:**
1. **Graph vs files at sonnet tier** — the same within-day comparison as 2026-08-10.
2. **Haiku vs sonnet** — cross-day, and ONLY on the planning leg, which is why the
   planning task is held **byte-identical** (Ideas 96–103, same prompt, same track blocks).
   The coding leg changes task (O53 is closed), so it is NOT cross-day comparable and the
   grading must not treat it as such.

| | Track A — GRAPH | Track B — FILES |
|---|---|---|
| **Planning** (Ideas 96–103 — UNCHANGED from 2026-08-10) | backlog-groomer, **sonnet** | backlog-groomer, **sonnet** |
| **Coding** (**O31**, not O53) | general-purpose, **sonnet**, worktree | general-purpose, **sonnet**, worktree |

**Track labels ROTATE:** on 2026-08-10 ALPHA=files / BETA=graph. Tomorrow
**ALPHA=graph, BETA=files** — so a reviewer who has read the earlier record cannot infer
the track from the label, and any label-order bias shows up as a reversal.

---

## Step 0 (new, and mandatory) — reload the graph before dispatch

The 2026-08-10 graph was loaded from `bd051ab`; the tree has since moved through O47, O53
and ADR 0011 — including **new code files** (`IntakeRoute.tsx`, `IntakeStepper.tsx`,
`intakeApi.ts`, `port_preflight.py`) and one **deletion** (`HeroArt.tsx`). Running the graph
track against that snapshot would handicap it far beyond yesterday's docs-only gap and
would measure staleness, not navigation.

    knowledge/depgraph-snapshots/snapshot.ps1      # if the tree moved since 0437
    poetry run drydocs load-code-snapshot

Record in RUN-LOG: the snapshot file, its commit, and the loaded `:CodeModule` total/live.
If the reload cannot run, **say so and abort the graph track** rather than running it stale.

## The five protocol fixes fable's grading earned

1. **Archive EVERY worker's full report + METRICS block** to
   `results/<run>-report.md`, not just its deliverable. On 2026-08-10 the coding runs'
   metrics were returned to the orchestrator but never archived — that gap is precisely what
   left o53-BETA's verification unprovable and capped its score at 4.
2. **The graph track archives its query scripts on the CODING run too** (`*-scratch.py` in
   `results/`). Planning-BETA did this faithfully; o53-BETA archived nothing, so there was no
   quotable evidence the orphan query it exists to demonstrate had ever run.
3. **Workers do not report timestamps.** Both 2026-08-10 planning runs fabricated theirs
   (one claimed a 90-minute span for a 306-second run). The orchestrator stamps dispatch and
   completion; workers report only tool counts and files read.
4. **Orchestrator-observed metrics are ground truth**, self-reports recorded beside them.
   All four haiku runs under-reported by 34–65%. **Whether sonnet self-reports more
   accurately is itself a graded finding** — fable computes the per-run discrepancy and
   compares it to haiku's 34–65% band.
5. **"Green" is defined once, for both tracks, in both prompts:** *"green means the repo's
   own guard suite (`poetry run pytest tests/unit -q`), not only the checks the acceptance
   names."* **This is a deliberate hint neither haiku run got**, and the reason is stated
   rather than hidden: both haiku coding runs left the Python guards red while correctly
   reporting npm build/lint green, so a re-run without the hint would most likely re-measure
   the same prompt gap instead of the model. Given equally to both tracks, it stays a fair
   comparison — and it makes the output potentially adoptable, which the haiku diffs were not.

Also corrected: the 2026-08-10 coding prompt pointed at "that file's neighbouring retired
rows" for a convention that **does not exist in that file** (fable found the yaml has no
retired rows). The new prompt never points at a specific location for a convention — it says
*find how this repo records the change* and leaves the finding to the worker.

## The coding task — O31

Chosen because its acceptance is premise-testing in the same way O53's was
verification-testing: it requires `benchmarkData.ts` to be produced from **a real
evaluation-harness run** rather than the hand-carried P0 numbers. **If no such harness output
exists, the correct outcome is to STOP and report that** — and a run that fabricates a
regeneration step over numbers it never sourced fails on accuracy regardless of how clean its
diff is. Same discipline dimension that separated the tracks yesterday, different mechanism.

O31 is `model: sonnet` in `backlog.yaml`, so this experiment runs it at exactly the tier it
was groomed for.

## Grading additions (fable, review 2)

Beyond PROTOCOL.md's five sections:
- **Cross-day planning comparison** — same task, same prompt, haiku vs sonnet: id-collision
  count, epic-name accuracy, whether the `port_preflight.py`-class find recurs, tool uses,
  duration, tokens. The 2026-08-10 numbers are in `GRADES.md` §2.
- **Self-report honesty delta** — per-run discrepancy vs haiku's 34–65% band.
- **Did the "green means the guard suite" hint land?** For each coding run: did it run the
  Python suite, and did it act on what it found.
- **Did the graph reload change the graph track's blind spots?** Fable's 2026-08-10
  improvement note was to extend the graph to acceptance-bearing non-code surfaces (taxonomy
  ledger rows, guard-test pins). That extension is NOT built, so the prediction to test is
  that the graph track again walks off the map wherever the acceptance lives in yaml or a
  test file — and whether sonnet *notices and says so* rather than silently working around it.

## Unchanged

Model pinned within the run; agent type varies by task, never by track; fable reviews the
plans blind before the coding dispatch and grades everything unblinded after; **commit
nothing, push nothing** — results are for the SME, who rules before anything lands.
