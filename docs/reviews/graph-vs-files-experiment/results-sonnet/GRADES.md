# Fable Review 2 — sonnet run, final grades, both tasks, both tracks (UNBLINDED)

**Reviewer:** Fable (unblinded: **ALPHA = GRAPH, BETA = FILES** — the reverse of 2026-08-10;
every cross-day comparison below is method-to-method, never label-to-label).
**Date:** 2026-08-11.
**Verification venue:** desktop working tree `C:\coding\projects\DryDocs`, `main` @ `6c24963`;
both experiment worktrees (`agent-aa168e5039f906d30` = ALPHA, `agent-a6fcf6daf8af92ce7` = BETA)
still exist and were inspected read-only. No repo edits beyond this file; no git-mutating
commands; the second live session's in-flight work untouched.

## Ground truth I established myself before scoring

- **The O31 premise HOLDS, verified against the tree, not either report.**
  `knowledge/upgrade-plans/p0-benchmark/benchmark_p0_results.json` exists on `main`: a
  12-question array, four arms per question (traversal / fulltext / manifest / a
  `traversal_naive` control), with realistic per-question `chars`/`ms` and `sample` fields
  containing literal corpus excerpts and doc ids — a real run's output, not a stub.
  `benchmark_p0.py` (the harness script) and `docmeta-p0-verdict.md` (the adjudicated
  write-up) sit beside it. So neither run faced the STOP branch; the cap question becomes
  "did they read the real source before building," answered per-run in §1.
- **The 7/12→6/12 recall bug is real, and both runs found it independently.** I counted the
  verdict.md fulltext column myself: six ✔ marks (EL1, EL3, PC2, PC3, MD1, MD2) against a
  hand-typed Recall row of `7/12` (line 62). The committed `benchmarkData.ts` carries the
  wrong `7/12` at lines 45/78. Two independent implementations converging on the same
  correction from the same source is strong evidence both regenerations are honest.
- **The per-arm sums are real.** My own sum over the JSON: traversal **15,354** ch,
  fulltext **34,195**, manifest **450,550** — against the committed file's hand-carried
  ≈16,400 / ≈31,400 / ≈449,500. Both regenerations emit 34,195 / 450,550 / 29.3× /
  6×–1133× / 6/12 identically; they differ only on traversal (ALPHA 15,352, BETA 15,354),
  and the 2-char gap is ALPHA's *documented* choice to credit 0 for the OS1 abstain's
  `"[]"` serialization artifact (`empty: true` → chars 0, stated in its script at the
  exact line). Neither number is fabricated; the SME should know the two diffs disagree on
  this one published figure and both are defensible.
- **Both worktrees verified directly.** BETA's two new files
  (`scripts/render_underhood_benchmark.py`, 634 lines; `tests/unit/test_underhood_benchmark.py`,
  103 lines) exist in its worktree even though its archived diff omits their content
  (see §1). ALPHA's diff embeds both of its new files verbatim under `=== NEW FILE ===`
  sections. All 8 archived scratch scripts (3 planning + 5 coding) open real Neo4j sessions
  against `drydocs` and together contain exactly the 28 Cypher MATCHes ALPHA's metrics claim
  — the evidence gap that capped o53-BETA yesterday is closed (fix 2 held).
- **A differentiator neither report states: BETA's worktree `docs/plan/board.html` is STALE.**
  I checked both boards for the O31 card: ALPHA's reads `data-status="done"`, BETA's still
  reads `data-status="todo"` against its own backlog edit. CLAUDE.md §0's stale-render check
  names board.html explicitly; no unit test pins it (which is why BETA's suite stayed green),
  but it is exactly the "ledgers and pinned counts in more than one place" the prompt warned
  about, and BETA neither regenerated it (with the safe explicit-args form it had already
  found for roadmap) nor flagged the staleness.
- **Convention symmetry, verified:** `CHANGELOG.md` is a real Keep-a-Changelog ledger with
  bracketed backlog ids (ALPHA added `[O31]`; BETA did not), and
  `test_render_determinism.py`'s `COMMITTED_RENDERERS` is a manual allowlist, not
  auto-discovered (BETA registered its renderer; ALPHA did not — and no test fails on the
  omission). Each track found one ledger surface the other missed.

---

## 1. Accuracy (per run, 1–10)

### planning-ALPHA (graph) — **6**
Carried from review 1, and unblinding does not move it. The structural claims remain the
best-evidenced statements in either plan (the `manual_loads.py` fan-in of 5 where a naive
grep over-counts to 6; the two function-local imports; the thin-importer edge at
`scripts/port_preflight.py:21`) — that is genuine graph value. But the decisive error is now
legible as the graph track's characteristic failure mode: Idea-99 was promoted as a new item
whose acceptance is *already satisfied* by RELAY-5 at `docs/port-prompt.md:743`, because
ALPHA confirmed the file's **node** existed and never read its **content**. The graph
licensed the read; skipping it was diligence, not tooling. Add the three missing
`REQUIRED_FIELDS` (`title`, `type`, `status`) on every draft, and 6 is the ceiling.

### planning-BETA (files) — **9**
Carried from review 1: all three spot-checks verified to the cited line (including the
RELAY-5 merge→satisfied call, the single most consequential correct disposition in either
plan), all twelve schema fields on every draft, id allocation from a full series scan,
sizes anchored in opened files. Only trivial slips. Unblinding adds nothing to change.

### o31-ALPHA (graph) — **9**
Clause-by-clause against the acceptance, verified against the diff and its worktree:

| Acceptance element | Result |
|---|---|
| Premise established before building | **Yes, proven.** Graph queries surfaced `benchmark_p0.py` / `benchmark_p0_results.json` / the verdict; all three are in its files_read; the report correctly re-reads O31's "blocked on the harness existing" note as a missing *backlog id*, not a missing artifact. **No cap.** |
| Documented regeneration step | **Yes** — `scripts/render_benchmark_data.py`, modeled explicitly on the `render_software_registry.py` + drift-guard pairing, with the kind-adjudication table cited to the verdict rather than fabricated (and the marker-regex untrustworthiness *proven* by the SA1/SA2-vs-MD1/PV1 counterexamples, which I confirmed in the raw JSON: `marker_found` is True/True/False/False exactly as claimed). |
| Reads a real harness run | **Yes** — every aggregate computed from the JSON; the 7/12→6/12, 29.3×, 6×–1133× corrections all replay against my own sums. |
| Scoreboard unchanged in shape | **Yes** — same exported names/types; `tsc -b` clean quoted; plus an in-scope fix to `TokenMemoryChart.tsx`'s now-false scaling comment, with the reasoning stated. |
| Change recorded per repo convention | **Yes, four surfaces:** drift guard (`test_benchmark_data_ts.py`, 5 tests, quoted passing), `CHANGELOG.md` `[O31]`, backlog `done` + summary rollup + `next_ready`, board+roadmap re-rendered in the worktree. Explicitly checked `ui-components.yaml` and correctly ruled it out (.ts excluded by the ledger's own SCOPE CAVEAT). **Miss: did not register the new renderer in `COMMITTED_RENDERERS`** (no test enforces it; its sibling found it). |
| Checks quoted, not asserted | **Yes** — npm build (`✓ built in 460ms`), lint (3 pre-existing warnings), and the guard suite **run twice with a `git stash` zero-diff baseline proving the 3 remaining failures pre-existing** — the strongest verification discipline in any run across both days. |

The diff artifact is fully self-contained (tracked hunks + both new files' full text + status).
Deductions: the missed allowlist registration, and that its within-file navigation had to
step outside the sanctioned channel at all (ruled compliant in §3, but the strain is real). **9.**

### o31-BETA (files) — **8**
Same clause-by-clause:

| Acceptance element | Result |
|---|---|
| Premise established before building | **Yes, proven** — same three artifacts found by Grep, read, and honestly characterized ("a one-off spike's output, not a reusable harness component — worth being honest about"), which is the most truthful framing of the premise either run produced. **No cap.** |
| Documented regeneration step | **Yes** — `scripts/render_underhood_benchmark.py`, with one genuinely superior element: the UI's Cypher snippets are **ast-extracted from the harness script itself** (never executed), which exposed that the old file's snippets were hand-paraphrased (EL1's missing `-[:PART_OF]->` hop — I confirmed the old file's provenance header claims "verbatim transcription," so this is a real fidelity catch ALPHA didn't make). |
| Reads a real harness run | **Yes** — same computed aggregates, matching my sums exactly (15,354 raw); the one documented exception (CORPUS docCount/totalChars from the verdict's Setup table, with the 26-vs-27 discrepancy disclosed rather than guessed) is the right call. |
| Scoreboard unchanged in shape | **Yes** — same export surface, `tsc -b` quoted clean; honestly notes the type-check is the verification actually performed. |
| Change recorded per repo convention | **Partial.** Drift guard + `test_harness_output_exists` + **`COMMITTED_RENDERERS` registration** (found via `test_render_determinism.py`, which ALPHA missed) + backlog `done`/rollup/`next_ready` + roadmap re-render. **Two misses:** no `CHANGELOG.md` entry, and the worktree `board.html` left stale against its own backlog edit, unflagged (§ Ground truth). |
| Checks quoted, not asserted | **Yes** — build/lint/pytest all quoted; its root-cause work on the pre-existing failures is actually *deeper* than ALPHA's (`FORCE_COLOR=3` found in the shell env vs "ANSI artifacts"; the `sys.path[0]` script-vs-`-c` analysis of the render hazard is the best diagnosis of that incident either run produced). |

Deductions, stated: two unnoticed ledger misses (stale board, no changelog) against ALPHA's
one; and the archived diff omits the contents of the two new files that *are* the
deliverable — the prompt's literal spec ("git diff output") permits it, and I verified the
files in the worktree so no cap applies, but the artifact is not self-contained the way
ALPHA's is, and yesterday's grading already established why that matters. Its fidelity wins
(ast snippets, harness-existence guard, deeper root-causing) pull it back to within one
point. **8.**

**Cap rule:** applied to neither. Both runs read the real JSON and the verdict *before*
building, both proved (not asserted) that the raw `marker_found` cannot be trusted in either
direction, and neither fabricated a number — I re-derived every changed aggregate myself.

**Shared environmental incident, scored evenly:** both runs tripped the
`render_*.py`-defaults-resolve-to-main-tree hazard, both detected it themselves, both
verified/restored the main tree (orchestrator-confirmed byte-identical to HEAD), and both
reported it as a finding rather than burying it. That is the correct behavior twice; the
hazard itself is charged to the environment, not to either track.

---

## 2. Performance

Orchestrator-observed numbers are ground truth (fix 4); self-reports beside them.

| Run (method) | Duration | Tool uses (obs.) | Tool uses (self) | Self-report delta | Tokens | files_read (self) |
|---|---|---|---|---|---|---|
| planning-ALPHA (**graph**) | 563.0s | 32 | 30 | **−6.3%** | 129,803 | 4 |
| planning-BETA (**files**) | 530.0s | 55 | 43 | **−21.8%** | 140,633 | 9 |
| o31-ALPHA (**graph**) | 1865.5s | 107 | ~88 | **−17.8%** (self-hedged "~") | 309,849 | 23 |
| o31-BETA (**files**) | 1893.8s | 117 | 74 | **−36.8%** | 261,340 | 16 |

**Self-report honesty delta vs haiku's 34–65% band:** three of four sonnet runs sit *below*
the band (6.3 / 17.8 / 21.8); only o31-BETA's 36.8% touches its low edge. Sonnet
self-reporting is materially more honest, and o31-ALPHA flagged its own count as approximate
— the first run in either day to hedge rather than assert a wrong number.

**Metrics blocks that look self-reported wrong — flagged:**
- **o31-BETA:** its shape-check narrative names all 7 consumer files
  (`Scoreboard.tsx` … `TrustLegend.tsx`) but none appears in `files_read: 16`. The report
  itself supplies the explanation (a repo-wide Grep surfaced the import lines; `tsc` did the
  shape verification), so this is consistent-but-thin rather than false — flagged, not
  condemned. Its 74-vs-117 gap is also the largest of the day.
- **o31-ALPHA:** `tool_calls_total: ~88` vs 107 observed — under, but disclosed as a tally
  estimate. Its files_read list (23, full paths, worktree-vs-main annotated) is the most
  auditable metrics block any run has produced in this experiment.
- Neither planning block shows narrative/list mismatches; neither run reported a timestamp
  (fix 3 held, 4-for-4).

Within-day shape: on planning, graph used **42% fewer tool calls** (32 vs 55) and **7.7%
fewer tokens** for **6.2% more wall-clock**. On coding, duration is a wash (−1.5%), tool
calls near-wash (107 vs 117), and graph cost **+18.6% tokens** (309,849 vs 261,340 —
largely the Cypher round-trips and the 5 scratch scripts).

---

## 3. Rule compliance

- **planning-ALPHA (graph): COMPLIANT** — review 1's ruling stands: all seven Greps were
  pinned to the two prompt-exempt task inputs (IDEAS.md, backlog.yaml); an indexed read of a
  file you are licensed to read end-to-end discovers nothing outside the exemption. Recorded
  again: under the strict-literal "Forbidden: Grep" reading this flips to NON-COMPLIANT; the
  SME can overrule without a re-run.
- **planning-BETA (files): COMPLIANT** — Grep/Glob/Read only; no graph access anywhere.
- **o31-BETA (files): COMPLIANT** — no Cypher, no Neo4j; its own `blocked_on` correctly
  notes the track rule never even bound, since the harness output was read from the
  committed JSON.
- **o31-ALPHA (graph): COMPLIANT — explicit ruling on the self-disclosed matter, as asked.**
  The coding prompt names no exempt inputs, so review 1's exemption ground does not carry
  over. I rule the four disclosed lookups permitted on a different and narrower ground:
  1. The three `grep -n` calls against `backlog.yaml` were **within-file offset lookups in a
     file the graph itself had already named** (its archived query 27 —
     `m.file_id CONTAINS 'backlog.yaml'` — returned the node before any grep ran). The track
     rule licenses `Read` of any graph-named path; a line-number lookup inside a 16,368-line
     file it could lawfully Read end-to-end discovers no path and no code context the
     licensed Read wouldn't. Same mechanism-and-purpose test as review 1, different license.
  2. The Python `__file__` probe was **incident forensics on the installed venv during the
     main-tree-write recovery**, not code-context discovery over the tree — outside the
     variable this experiment controls. Refusing it would have meant not diagnosing an
     active cross-tree hazard.
  Disclosure is not permission — but the run also *earned* the ruling by routing every
  discovery question through Cypher first (28 archived queries) and stepping outside only
  where the graph's own file-grain boundary made the sanctioned channel structurally silent.
  Under the strict-literal reading, o31-ALPHA flips to NON-COMPLIANT; stated so the SME can
  overrule on the record. All four runs: **VALID.**

---

## 4. The verdict paragraph

**Planning: graph navigation HURT at sonnet, and the hurt is the same seam as its haiku-day
win.** The files run beat the graph run 9-to-6 on accuracy (review 1, blind), with the
hand-off decided by one fact — RELAY-5 at `docs/port-prompt.md:743` already satisfies
Idea-99 — that the files track found by reading the file and the graph track missed by
confirming the file's *node* and never opening its *content*; the graph run's only
efficiency edge (32 vs 55 tool calls, −7.7% tokens) bought nothing because it was also 6.2%
*slower* (563.0s vs 530.0s). This inverts 2026-08-10, where graph won planning 6-to-3 —
but the cross-tier constant is exact: on both days, the winning track was the one that read
the decisive artifact's content (haiku files never read backlog.yaml's id series and drafted
5 colliding ids; sonnet graph never read port-prompt.md and drafted a no-op item). The
graph carries structure, and grooming decisions are content decisions. **Coding: a wash on
the deliverable, a slight graph edge on the ledger (9 vs 8), and the method mattered less
than the model.** Both runs independently proved the premise (the committed
`benchmark_p0_results.json` — I verified it exists and is real), both computed identical
corrected aggregates (29.3×, 6/12, 450,550 — my own sums agree), both quoted green builds
and both ran the full guard suite; duration was a wash (1865.5s vs 1893.8s) and the graph
paid +18.6% tokens. The one-point gap is ledger diligence, not navigation: the files run
left its worktree board.html stale against its own backlog edit (verified:
`data-status="todo"` on the O31 card) and skipped the CHANGELOG, against the graph run's
single missed allowlist registration. **The one improvement before this is worth
re-running: push the graph below file grain on the acceptance-bearing surfaces** — backlog
item ids and rollup counts, port-prompt relay entries, guard-test pins as addressable
nodes/properties joined to the modules they govern. Yesterday's version of this note blamed
snapshot staleness as a confound; today staleness was removed (fresh `5613ea0` reload,
verified current) and the same boundary still produced the graph track's only planning
error and its only compliance strain — the file boundary, not currency, is the limiting
factor, and both failures on both days sit exactly on it.

---

## 5. Stale-graph handling

One line each, as required: **o31-ALPHA** noticed where it mattered — its report states the
tree is 3 commits past `5613ea0`, confirms per the dispatch note that all are docs-only, and
says why that could not affect the task (every graph-named path verified present);
**planning-ALPHA** disclosed the graph's scope limits honestly (the admitted un-run J44
query, the "graph indexes files, not file-internal offsets" caveat) but its RELAY-5 miss
was the file-content boundary, not snapshot drift — with the reload in place, no run on
either track was bitten by staleness, which is itself the day's cleanest protocol result.

---

## 6. Cross-day planning comparison (haiku 2026-08-10 vs sonnet 2026-08-11, method-to-method)

Byte-identical prompt, same track rules; the only cross-day-comparable leg.

| Metric | haiku FILES | haiku GRAPH | sonnet FILES (BETA) | sonnet GRAPH (ALPHA) |
|---|---|---|---|---|
| Accuracy (review-1 scale) | 3 | 6 | **9** | 6 |
| Drafted-id collisions | **5 of 6** | 1 (U19) | **0** | **0** |
| Epic-name accuracy | 2 of 3 nonexistent | correct | correct (named siblings) | correct (C31 mirrors C25) |
| `port_preflight.py`-class find | **missed** (11 Globs) | **found** | **found** (read the 63-line script) | found (verified the import edge) |
| Duration | 306.1s | 258.5s | 530.0s | 563.0s |
| Tool uses (obs.) | 41 | 26 | 55 | 32 |
| Tokens | 72,605 | 81,671 | 140,633 | 129,803 |
| Self-report delta | −34% | −62% | −21.8% | −6.3% |

Readings, each grounded above: (1) **sonnet eliminated the id-collision failure class on
both tracks** — haiku's 5-of-6 catastrophe and even graph-haiku's single U19 collision are
gone; both sonnet runs computed next-free ids correctly. (2) **The `port_preflight` find is
no longer track-separating** — at haiku only the graph surfaced it; at sonnet both tracks
found it, so the differentiator moved up a level, to content-reading depth (RELAY-5), where
files won. (3) **Sonnet costs ~1.8–2.1× the wall-clock and ~1.6–1.9× the tokens** of haiku
on the identical prompt, and the quality return is asymmetric: files went 3→9 while graph
stayed 6→6 (different failure each day — ids/roots at haiku, content currency and schema
fields at sonnet). The model upgrade bought the files track far more than it bought the
graph track, which is itself evidence the graph's ceiling here is the data it holds, not
the model reading it. (4) Self-report honesty improved on both tracks (§2).

## 7. Did the "green means the guard suite" hint land?

**Yes, on both runs, and it changed both outcomes.** Both ran
`poetry run pytest tests/unit -q`; both discovered their backlog status edit had broken the
rollup/roadmap guards (`test_summary_rollup_matches_items`, `test_next_ready_is_computed`,
`test_committed_roadmap_page_matches_its_sources`) and fixed all three before finishing —
without the hint, both would have shipped exactly the red-guard state both haiku runs
shipped. Both then handled the 3 remaining failures correctly by *diagnosing* rather than
ignoring or "fixing" them: ALPHA proved them pre-existing with a `git stash` zero-diff
baseline (quoted); BETA root-caused them further (`FORCE_COLOR=3` in the shell env; the
editable-install path hazard) and correctly declined to fix environment state from a
commit-nothing worktree. The hint's cost is visible in §2's coding durations (~31 min per
run, both including two full suite runs); its value is that today's diffs are adoptable and
yesterday's were not.

## 8. Did the graph reload change the graph track's blind spots?

**Half the prediction failed, and the half that held was narrated, not silent.** The
prediction was that the graph track would again walk off the map wherever the acceptance
lives in yaml or a test file. In fact the reloaded snapshot indexes yaml/md surfaces as
nodes — o31-ALPHA reached `backlog.yaml`, `MODULE_MAP.md`, `CHANGELOG.md`, and
`ui-components.yaml` through Cypher (archived queries 24–27) and never needed yesterday's
PowerShell locate-the-file workaround; it even ruled `ui-components.yaml` *out* correctly by
reading it. What remains blind is **within-file structure**: the graph could name
backlog.yaml but not find the O31 entry or the summary block inside its 16,368 lines (the
three disclosed greps, §3), and on the planning side could name port-prompt.md but not see
that RELAY-5 already exists inside it (the Idea-99 miss). Sonnet noticed and said so both
times — o31-ALPHA's report flags the greps "rather than asserting it was clearly in-bounds,"
and planning-ALPHA disclosed what it could not see — so the 2026-08-10 failure mode of
*silently* working around the map's edge did not recur. The blind spot moved from "which
file" to "what's inside the file," which is precisely the §4 improvement.
