# Fable Review 2 — Final grades, both tasks, both tracks (UNBLINDED)

**Reviewer:** Fable (unblinded: ALPHA = FILES, BETA = GRAPH).
**Date:** 2026-08-10.
**Verification venue:** desktop working tree at `C:\coding\projects\DryDocs`, current `main`
(the live tree still carries HeroArt — both coding runs worked in isolated worktrees, so
every acceptance check below was replayed against the diffs plus the pre-change tree).

Ground truth I established myself before scoring the coding runs:

- The **"coverage pin"** in O53's acceptance is the tuple
  `(29, 68)` in `tests/unit/test_ui_components.py::test_unbound_components_are_counted_not_hidden`
  (lines 264–269), and the **history-line convention** is that test's docstring ledger
  ("62 -> 63 at O28 … 66 -> 68 at Q16"). A correct O53 adds "68 -> 67 at O53: HeroArt
  deleted (unbound, so only the total moves)" and changes the pin to `(29, 67)`.
- The same test file also asserts **section-header counts match the rows** (line 165), so the
  yaml's `# --- component (15) ---` header must become `(14)`.
- `config/taxonomy/ui-components.yaml` has **no retired rows** — its full git history is
  additions only — so the coding prompt's pointer to "that file's neighboring retired rows"
  was itself a red herring; the convention lives in the guard test, not the yaml. Both
  workers faced the same misdirection, so it is scored evenly (as a shared handicap, not a
  per-run defect — but *finding* the real pin was still part of the acceptance, and neither did).

---

## 1. Accuracy (per run, 1–10)

### planning-ALPHA (files) — **3**
Carried forward from review 1 unchanged: grep line numbers replay to the digit
(C25 @ 14050, K17 @ 2479), but 5 of 6 drafted ids (J18/J19/J20/J21/U9) collide with existing
items, the "next free id" table is fabricated, and two of three epic names don't exist.
Unblinding makes this *worse*, not better: this was the track with unrestricted Grep over
backlog.yaml — one `grep "- id: J18"` (the exact operation it demonstrably knew how to run)
would have caught the collisions. The failure was diligence, not tooling.

### planning-BETA (graph) — **6**
Carried forward from review 1: files, epics, phases, and cross-item claims all verify;
one id collision (U19, present at its own claimed snapshot, so not staleness) and one wrong
package-root list in that same item. Unblinding adds one nuance in each direction: the id
collision is *not* excusable by the graph — backlog ids live in a yaml BETA read directly,
outside the graph's coverage — but the graph is what let BETA find the `port_preflight.py`
machinery (the single most consequential correct fact in either plan) that ALPHA's 11 Globs
never surfaced. Net: the review-1 score stands.

### o53-ALPHA (files) — **6**
Verified against the diff and the acceptance clause by clause:

| Acceptance element | Result |
|---|---|
| HeroArt.tsx deleted | **Yes** — but only via the appended `git status` (` D web/src/components/HeroArt.tsx`); the diff body has **no deletion hunk**, which an unstaged delete should produce. Artifact-capture defect (likely a path-filtered `git diff`), flagged; the status line is accepted as proof of deletion. |
| index.css hero-net rule removed | **Yes** — `@keyframes hero-net-pulse` + `.dark .hero-net` both gone, replaced by a "DELETED O53" tombstone comment (consistent with the O30 App.css precedent the groom notes cite). |
| ui-components.yaml row removed | **Yes.** |
| Section count 15→14 | **Yes** — header edited to `# --- component (14) ---`. |
| Coverage pin moved w/ history line | **NO** — `tests/unit/test_ui_components.py` untouched; the pinned `(29, 68)` now disagrees with the 67 remaining rows, so `poetry run pytest` fails on this worktree. |
| Orphan claim proven before delete | **Yes, on the orchestrator's record**: RUN-LOG line 14 — "verified-before-delete via grep". The worker's own report (with the quoted grep) is not among the archived artifacts, so the evidence is orchestrator-attested rather than quoted verbatim. |
| Build/lint quoted | **Asserted, not quoted** — RUN-LOG says "build PASS, lint PASS"; no command output survives in the artifacts. Same gap for both runs; scored evenly. |

Verified before deleting, honest ledger discipline on the yaml, but the acceptance's
explicit pin clause is unmet and leaves the Python guard suite red. 6.

### o53-BETA (graph) — **4** (capped)
Same clause-by-clause check:

| Acceptance element | Result |
|---|---|
| HeroArt.tsx deleted | **Yes** — full 133-line deletion hunk in the diff (the cleanest diff capture of the two). |
| index.css hero-net rule removed | **Yes** — clean removal, no tombstone. |
| ui-components.yaml row removed | **Yes.** |
| Section count 15→14 | **NO** — header still reads `# --- component (15) ---`; this breaks `test_ui_components.py`'s header-count check *in addition to* the pin. |
| Coverage pin moved w/ history line | **NO** — test file untouched, same as ALPHA. |
| Orphan claim proven before delete | **UNPROVEN.** This is the cap. The graph track's rules required query scripts written to the results directory; the directory contains five `explore-*.py` scripts, **all from planning-BETA — zero from the o53 run**. RUN-LOG line 15 records only "build PASS, lint PASS; diff 9,029 bytes" — no verification note, in pointed contrast to ALPHA's line. The only observed pre-delete tool uses relayed by the orchestrator are two PowerShell existence checks, which confirm the file *exists*, not that nothing *imports* it. There is no quotable evidence that the Cypher orphan query — the one thing this track exists to demonstrate — was ever run. |

Per the grading rule, a run that deleted without verified proof caps at 4 regardless of
diff quality. Uncapped it would have scored 5 (one below ALPHA: better diff capture, but
the missed 15→14 header breaks a second guard test). If the orchestrator holds BETA's
un-archived report and it quotes a pre-delete orphan query, the cap lifts and the score
becomes 5. **4.**

Shared finding, stated once: **both** coding runs failed the pin clause, so **neither**
worktree passes `pytest` — the acceptance's "build + lint green" (npm) is green for both,
but the repo's own drift guard, the thing the ledger header calls "the point", is red for
both. The web build cannot catch this; only the Python suite can, and neither run ran it.

---

## 2. Performance

| Run | Duration | Tool uses (orchestrator) | Tool uses (self-report) | Tokens | files_read (self-report) |
|---|---|---|---|---|---|
| planning-ALPHA (files) | 306.1s | 41 | **27** (11 Read + 11 Glob + 4 Grep + 1 Bash) | 72,605 | 11 |
| planning-BETA (graph) | 258.5s | 26 | **10** (yet lists 7 queries + "8 Neo4j query script runs" + Reads + a Write) | 81,671 | 3 |
| o53-ALPHA (files) | 408.7s | 47 | **28** | 77,594 | not in archived artifacts |
| o53-BETA (graph) | 265.5s | 31 | **11** (while listing 19 items) | 77,451 | not in archived artifacts |

**Self-report discrepancies — all four runs under-report, flagged explicitly:**

- Every run's self-count is 34–65% below the orchestrator's observation (27 vs 41; 10 vs 26;
  28 vs 47; 11 vs 31). The pattern is systematic across both tracks and both task types —
  haiku workers count "logical steps" and drop retries, failed calls, and report/diff writes
  — so tool-use comparisons between tracks are only valid on the orchestrator's numbers,
  which this table treats as ground truth.
- Two self-reports are **internally** inconsistent on their face: o53-BETA claims a total of
  11 while enumerating 19 items; planning-BETA claims 10 total while separately claiming
  "8 Neo4j query script runs" plus Reads plus the plan write.
- Both planning runs **fabricated their timestamps** and said so ("estimated"):
  planning-ALPHA claims a 90-minute 00:00–01:30Z span (actual: 306.1s, dispatched 03:05);
  planning-BETA claims 16:22–16:35Z (actual: 258.5s, dispatched 03:05). Neither timestamp
  pair is anywhere near the dispatch window.
- The coding runs' METRICS blocks (including their files_read lists) were returned to the
  orchestrator but are **not archived** in the results directory — a protocol gap that cost
  o53-BETA its verification evidence in §1.

Track pattern on the orchestrator's numbers: graph was faster on both tasks (−15.6%
planning, −35.0% coding) with fewer tool uses (26 vs 41; 31 vs 47), at a token cost on
planning (+12.5%) and token parity on coding (−0.2%).

---

## 3. Rule compliance

- **planning-ALPHA (files): COMPLIANT.** Glob/Grep/Read plus one disclosed `wc -l` — review
  1's "borderline deviation, not a violation" ruling stands. No Cypher anywhere.
- **planning-BETA (graph): COMPLIANT.** Neo4j query scripts (archived as `explore-*.py`)
  plus 3 targeted Reads of task-named files; no Glob/Grep/sweeps in its METRICS or the
  orchestrator's observation.
- **o53-ALPHA (files): COMPLIANT.** Verification via grep is exactly the files-track method;
  no graph access observed or claimed.
- **o53-BETA (graph): COMPLIANT, with two flagged PowerShell calls.** Ruling and reasoning:
  - `PowerShell: Check if HeroArt.tsx exists` — **acceptable existence check.** The path was
    named by the task input; a `Test-Path` of a named file discovers no code context the
    task hadn't already handed over. It is actually the run's stale-graph diligence (§5):
    confirming the snapshot-era file still exists in the live tree before deleting it.
  - `PowerShell: Find ui-components.yaml` — **acceptable, but only just.** Mechanically a
    filename search is a tree sweep, and the track rule says "any tree sweep" is forbidden.
    Three things keep it on the right side of the line: (1) the filename was named verbatim
    in the task's acceptance text — the search could only return a path the task had already
    identified, i.e. zero discovery value beyond directory location; (2) the graph
    structurally cannot answer it — the code graph indexes code modules and import edges,
    not config yaml, so the track's sanctioned channel was blind here by design, not by the
    worker's choice; (3) it is the same class as planning-ALPHA's `wc -l`, which review 1
    ruled a disclosed borderline deviation — identical standard, identical ruling. A
    *content* search (`Select-String` for importers, say) by the same mechanism would have
    been NON-COMPLIANT; locating one task-named file is not.
  - The flag worth keeping: both PowerShell calls mark exactly where the graph's coverage
    ends. The worker didn't break the rules so much as walk off the edge of the map the
    rules assumed was complete.

No Cypher was found or reported in either files-track run. All four runs: **VALID.**

---

## 4. The verdict paragraph

**Planning: graph navigation helped, decisively on the dimension that matters.** BETA
(graph) beat ALPHA (files) 6-to-3 on accuracy and 8-to-3 on convention fidelity (review 1,
confirmed here), with 1 drafted-id collision against ALPHA's 5-of-6, while also being 15.6%
faster (258.5s vs 306.1s) on 37% fewer tool uses (26 vs 41) — its only costs were +12.5%
tokens and thin file grounding (3 files read vs 11), which produced its one real content
error (U19's wrong package-root list). The graph's concrete win: it surfaced the existing
`port_preflight.py` machinery that re-homes Idea-96, which ALPHA's 11 Globs never found.
**Coding: a wash on the diff, a hurt on the discipline.** Both tracks converged on the same
incomplete result — 3 files touched, and *both* missed the acceptance's coverage-pin clause
(`(29, 68)` in test_ui_components.py), leaving both worktrees red on the repo's own guard
suite — but BETA additionally missed the 15→14 header (a second guard-test failure), and,
decisively, left zero archived evidence of a pre-delete orphan query (no o53 scratch
scripts in a results directory that faithfully preserved planning-BETA's five), against
ALPHA's on-record "verified-before-delete via grep"; BETA's 35% speed edge (265.5s vs
408.7s) is worth nothing on a deletion task where the verification *is* the deliverable
(accuracy 6 vs 4, cap applied). **The one improvement before a re-run:** extend the graph's
coverage to the acceptance-bearing non-code surfaces — config/taxonomy ledger rows and
guard-test pins as graph nodes joined to the code modules they inventory — because every
BETA miss (PowerShell-locating ui-components.yaml, the unnoticed header count, the
unnoticed pin) happened precisely where the graph went blind, and O53-shaped chores live
mostly in that blind zone.

---

## 5. Stale-graph handling

- **planning-BETA: noticed, where it mattered.** Its report explicitly discloses that
  `test_markdown_fences.py` is absent from its CodeModule scan and reasons around the gap
  via J41's notes instead of papering over it ("Graph snapshot limitations" section) —
  exactly the behavior the track rules said would be graded.
- **o53-BETA: handled implicitly, never narrated.** Its `Test-Path` on HeroArt.tsx before
  deleting is a live-tree cross-check of a snapshot-era fact — the right instinct — but no
  surviving artifact states the snapshot-vs-tree gap or notes that the post-bd051ab commits
  were docs-only and therefore harmless to O53; the noticing, if it happened, went
  unrecorded in an un-archived report.
