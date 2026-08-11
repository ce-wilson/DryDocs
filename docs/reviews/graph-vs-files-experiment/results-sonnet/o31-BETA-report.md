# O31 — BETA (files-only track) report

## Premise check (step 1)

The dispatch says: find the docmeta evaluation harness, confirm a real run's
output exists, and STOP if it doesn't rather than building a regeneration
step over invented numbers.

Searched the repo (Grep for `benchmarkData`, `docmeta`) and found:

- `knowledge/upgrade-plans/p0-benchmark/benchmark_p0.py` — the docmeta P0
  benchmark script. Its own docstring: "Throwaway spike script (Q3)."
  Connects to a live Neo4j `drydocs` DB, runs three retrieval arms
  (traversal / full-text / manifest-routed markdown) over 12 fixed support
  questions, and writes JSON results.
- `knowledge/upgrade-plans/p0-benchmark/benchmark_p0_results.json` — the
  **committed output of an actual run** (14,683 bytes, per-question
  chars/ms/rows/marker_found/sample-text for all three arms). This is real:
  the `sample` fields contain literal excerpts of the actual `controlm-*.md`
  corpus text and doc IDs, timings vary realistically per question, and the
  per-question figures match `docmeta-p0-verdict.md`'s Results table almost
  exactly (see the discrepancies below, which is itself evidence the JSON
  predates and fed the verdict's hand-typed table, not the reverse).
- `knowledge/upgrade-plans/docmeta-p0-verdict.md` — the write-up
  `benchmarkData.ts`'s header cites as its source ("verbatim transcription
  of the 2026-07-16 live benchmark verdict"). Its own text: "the loaders are
  committed, so the run can be recreated at P1 to baseline the **real
  harness**" — i.e. this P0 script is explicitly a spike, not (yet) the
  durable harness a future R8-style component would use.
- `docs/restructure/backlog.yaml`'s O31 entry carries a grooming note (dated
  2026-07-23) recording that no standalone "docmeta evaluation harness"
  backlog item exists, and that O31 was "in practice blocked on that harness
  existing." That note predates finding this file in a fresh search — it
  reads as the harness not having been located during that grooming pass,
  not as evidence it doesn't exist.

**Verdict: the premise holds.** A real evaluation-harness run's output is
committed in the repo. It is a one-off spike's output, not a reusable
harness component — worth being honest about, and I say so in the backlog
note and generator docstring rather than overclaiming a "harness" that
doesn't (yet) exist as a standing thing. But it is exactly what the O31
acceptance names: real numbers from a real run, as opposed to the
hand-carried transcription the old `benchmarkData.ts` header describes.
Proceeded to step 2.

## What was built (step 2)

`scripts/render_underhood_benchmark.py` — a new renderer, following the
`scripts/render_*.py` pattern already used for the board/gates/enforcement-
matrix/load-map/software-registry (chose a script over a manual-procedure
README because a script is regeneratable and diffable exactly the way those
renders are, and because a drift-guard test can enforce it, which a written
procedure can't).

What it reads and how it's real, not hand-carried:

- **Every per-question `chars`/`ms`/`rows` figure** comes straight out of
  `benchmark_p0_results.json` — never hand-typed.
- **Every Cypher/full-text snippet** shown in the UI is extracted via
  `ast.parse` over `benchmark_p0.py`'s `QUESTIONS` list (never executed — no
  DB connection, no network call from this script) — so the snippets shown
  to a viewer are the literal queries the harness ran, not a hand-retyped
  paraphrase (the OLD `benchmarkData.ts` snippets were paraphrased/
  simplified versions that didn't match the harness script verbatim — I
  checked; e.g. old EL1 traversal snippet omitted the `-[:PART_OF]->`
  hop the real query has).
- **CORPUS.tiers / chunkCount** are parsed from the SA2 question's real
  traversal sample (`GROUNDED`/`SYNTHESIZED`/`VERBATIM` chunk/char counts),
  not hand-typed.
- **CORPUS.docCount / totalChars** are the one deliberate exception,
  documented as such in the script: they're corpus-inventory metadata
  (26 docs, 313,350 chars) from `docmeta-p0-verdict.md`'s Setup table, which
  is *not* part of the per-question harness JSON (the JSON's own SA1 sample
  returns `docs: 27`, which counts the manifest's own Document node — a
  discrepancy I chose not to silently resolve by guessing).
- **TOTALS / EFFICIENCY** are computed (sum, median, ratio) from the real
  per-question data, not retyped from the verdict's rounded summary row.

What is **not** mechanically derivable, and is instead a small, cited
`ADJUDICATION` overlay in the script: `docmeta-p0-verdict.md` itself
discloses that its marker-regex scorer is a crude pass/fail proxy and
records specific human corrections on top of it ("Two scoring artifacts
corrected during adjudication (recorded, not hidden)"). Every override in
the overlay cites the verdict.md line it encodes:

- MD1 and PV1 traversal: the verdict's own disclosed correction (raw
  `marker_found=false` for both, because the real answer is a doc-list/count
  that doesn't echo the marker literal — verdict.md lines 36-40).
- SA1/SA2/PV1 full-text and SA2/PV1 manifest: the marker regex
  (`r"controlm-"` / `r"SYNTHESIZED"`) matches incidentally inside a doc-id or
  tier-label string without the arm actually answering the aggregation/
  provenance question — verdict.md marks these `✗` / `~ rule only` even
  though the raw JSON says `marker_found=true`.
- PC1/PC2 traversal `qualifier: "informed"` and OS1's abstain
  `qualifier: "correct"` — verdict.md's `✔*` / `Ⓐ` annotations.

## Found while building this

Comparing the harness JSON against `docmeta-p0-verdict.md`'s own Results
table turned up two arithmetic errors in the hand-typed table that
`benchmarkData.ts` inherited by transcription — concrete evidence for this
item's own premise:

1. **Full-text recall.** The verdict table states `7/12`. Counting its own
   ✔ marks (EL1, EL3, PC2, PC3, MD1, MD2) gives `6/12`. The regenerated data
   computes `6/12` from the real per-question kinds — pinned by
   `tests/unit/test_underhood_benchmark.py::test_fulltext_recall_matches_the_real_per_question_data`.
2. **Per-arm totals.** The verdict's rounded totals (≈16,400 / ≈31,400 /
   ≈449,500 ch) don't equal the sum of its own per-question figures. Real
   sums from the JSON: traversal 15,354 / full-text 34,195 / manifest
   450,550 ch. Consequences that reach the UI:
   - `EFFICIENCY.headline`: **29.3×**, not the old 27.4×.
   - `EFFICIENCY.perQuestionRange`: **6×–1133×**, not the old, much
     narrower 28×–60× — the real range is wider because it covers all 10
     non-abstain questions (including the aggregation outliers SA1/SA2/PV1,
     where the manifest arm pays 75,940 ch to read-and-hand-count something
     traversal answers in under 200 ch) instead of a hand-picked "typical"
     subset.

Neither of these is a defect in this task's approach — they're exactly the
category of error the acceptance criterion exists to prevent, now visible
because the numbers are computed instead of retyped.

## Shape check — "the scoreboard renders unchanged in shape" (step 2, cont'd)

All exported symbols/types are unchanged: `StrategyId`, `StrategyInfo`,
`STRATEGIES`, `CORPUS`, `TOTALS`, `EFFICIENCY`, `ResultKind`,
`StrategyResult`, `QuestionClass`, `CLASS_TOKEN`, `CypherSnippet`,
`BenchmarkQuestion`, `QUESTIONS`, `PROVENANCE_LINE`. Every consumer
(`Scoreboard.tsx`, `StrategyCards.tsx`, `QuestionDetail.tsx`,
`TokenMemoryChart.tsx`, `HallucinationSpotlight.tsx`, `ResultChip.tsx`,
`TrustLegend.tsx`) imports the same names with the same field shapes.
`tsc -b && vite build` (below) type-checks every one of those consumers
against the regenerated file and passed clean — that is direct evidence the
shape didn't change, not an assumption. No browser was available on this
track to additionally screenshot `/under-the-hood`; the type-check is the
verification actually performed.

## Recording the change (step 3)

Found the convention by grepping for the existing `render_*.py` +
drift-guard pairing (`tests/unit/test_enforcement_matrix.py`,
`test_load_map_json.py` follow the identical shape: import the generator
via `importlib.util`, rebuild in memory, assert `committed == fresh`) and by
reading `tests/unit/test_render_determinism.py`, which keeps a
`COMMITTED_RENDERERS` allowlist of every renderer whose output is committed
and drift-checked (added specifically to catch OS-dependent `Path` sorting
after a real CI incident documented in that file's own docstring).

Applied both:
- `tests/unit/test_underhood_benchmark.py` — new drift guard, following the
  enforcement-matrix/load-map pattern (`committed == fresh regeneration`),
  plus tests that pin the two corrected numbers above so a future edit can't
  silently reintroduce the verdict's arithmetic slips, plus a
  `test_harness_output_exists` test that fails loudly (not silently) if the
  JSON this whole item rests on is ever removed.
- `tests/unit/test_render_determinism.py` — added
  `render_underhood_benchmark.py` to `COMMITTED_RENDERERS` (it has no bare
  `Path` sorts, so the platform-dependence check passes; registering it
  keeps the allowlist honest for any future renderer that does add one).

Also updated `docs/restructure/backlog.yaml`'s O31 entry: `status: done`
with a closing note (matching the style of neighboring closed items like
O30 — dated, findings-first, cites what changed) — found this is the
established convention by reading how O30's entry was closed. Regenerating
the item cascaded into two more places the repo tracks pinned counts, both
caught by the guard suite before I'd have otherwise noticed them:
`backlog.yaml`'s own `summary:` roll-up (`todo`/`done` counts, `next_ready`
list) and `docs/plan/roadmap.html` (rendered from the backlog, drift-checked
against it). Both regenerated and now consistent.

### A hazard found and worked around (not an O31 defect, disclosed for the record)

Running `scripts/render_board.py` with its default arguments from inside
this worktree wrote `docs/plan/board.html`, `docs/plan/ideas.html`, and
`docs/plan/roadmap.html` to the **main tree** (`C:\coding\projects\DryDocs\docs\plan\...`),
not the worktree — a real violation of "commit nothing, touch nothing
outside your worktree except the two result files," caught and fixed
immediately, not swept under the rug.

Root cause, confirmed by direct testing: `scripts/render_board.py` imports
its default output paths from the installed `drydocs` package
(`drydocs.plan_board.DEFAULT_BOARD_PATH`, similarly `plan_roadmap`,
`plan_ideas`). When Python runs a *script* (`poetry run python
scripts/render_board.py`), `sys.path[0]` is the script's own directory
(`scripts/`), so `import drydocs` falls through to the venv's editable
install — and that install's `__file__` metadata points at the main tree
checkout (`C:\coding\projects\DryDocs\.venv`, confirmed via `poetry env
info`), because that's where `poetry install` originally ran, before this
worktree existed. Scripts that compute their own paths via
`Path(__file__).resolve().parent.parent` inside the script itself (e.g.
`render_gates.py`, `render_enforcement_matrix.py`) are unaffected and
correctly wrote into the worktree; only the two board-ritual scripts that
default through `drydocs.plan_board` / `drydocs.plan_roadmap` are affected.
(For what it's worth: `poetry run python -c "..."` does NOT reproduce this,
because `-c` mode puts the cwd on `sys.path[0]`, which shadows the editable
install with the worktree's own local `drydocs/` package — the bug is
specific to `python script.py` invocation.)

Impact assessment (verified, not assumed): the three main-tree files
written were byte-for-byte identical, before and after, to their committed
`HEAD` blobs (confirmed via `git show HEAD:<path>` diffed against the
on-disk files — both attempts, the initial no-op discovery and a follow-up
CRLF-normalized re-check, came back with zero differences and identical
byte counts). The accidental write regenerated content that was already
current, so no data was lost or altered in the main tree. I did not rely on
this assumption — I verified it before moving on.

Fix applied for the actual regeneration this item needed:
`scripts/render_roadmap.py --roadmap docs/restructure/roadmap.yaml --backlog
docs/restructure/backlog.yaml --out docs/plan/roadmap.html` with explicit,
worktree-relative arguments, which resolves entirely by argparse defaults
override and never touches the `drydocs.plan_roadmap` module's own default
constants. Confirmed landing in the worktree via `git status` immediately
after. I did not re-run `render_board.py`'s default (unsafe) path again.

This is a pre-existing environment/worktree-setup issue, not something
introduced by or in scope for O31 — flagged here because it's exactly the
kind of thing "commit nothing" exists to catch, and because any other
worktree session running the bare `render_board.py`/`render_roadmap.py`
default command will hit the same thing.

## Checks (step 4)

**`npm ci`** (web/): cost ~5s, 82 packages, clean — needed since
`node_modules` didn't exist in this worktree.

**`npm run build`** (`tsc -b && vite build`):
```
✓ built in 463ms
```
No TypeScript errors. (One pre-existing warning about a large JS chunk,
unrelated to this change.)

**`npm run lint`** (`oxlint`):
```
src/layout/rightSidebarContext.tsx:37:17: warning react(only-export-components)...
src/components/TrustLegend.tsx:11:14: warning react(only-export-components)...
src/components/icons/HubGlyphs.tsx:186:14: warning react(only-export-components)...
```
Three pre-existing warnings (not errors, not in files this change touched).
No new lint findings from `benchmarkData.ts` or the new script.

**`poetry run pytest tests/unit -q`** (the repo's own guard suite, not just
the acceptance-named checks) — final run:
```
FAILED tests/unit/test_schema_graph.py::test_default_paths_point_into_the_repo
FAILED tests/unit/test_supplements.py::test_chain_applies_in_registry_order
FAILED tests/unit/test_supplements.py::test_unknown_only_name_exits_2_without_touching_the_graph
3 failed, 1880 passed, 9 skipped in 63.54s (0:01:03)
```

All 9 of my own new/modified tests pass
(`tests/unit/test_underhood_benchmark.py` ×6, plus the
`test_render_determinism.py` additions run clean). The `test_backlog.py`
(`test_summary_rollup_matches_items`, `test_next_ready_is_computed`) and
`test_plan_roadmap.py::test_committed_roadmap_page_matches_its_sources`
failures caused by my `backlog.yaml` status edit were found, diagnosed, and
fixed (summary counts + `next_ready` list + roadmap re-render) — final run
is clean on all three.

The remaining 3 failures are **pre-existing and unrelated to O31** — none
touch `backlog.yaml`, `benchmarkData.ts`, or any file in this diff.
Diagnosed, not just asserted:
- `test_schema_graph.py::test_default_paths_point_into_the_repo` — the
  identical main-tree-vs-worktree editable-install path hazard described
  above, this time inside `drydocs_core/schema/schema_graph.cypher`'s own
  default-path test. Would fail in any worktree session regardless of what
  else changed.
- `test_supplements.py` (×2) — `result.output` contains raw ANSI escape
  codes (`\x1b[3m`, `\x1b[1;31m`, box-drawing characters) instead of plain
  text, breaking a substring assertion. Root cause confirmed: this shell has
  `FORCE_COLOR=3` set in its environment (checked via `env`), which forces
  `rich`'s color detection on regardless of the `CliRunner`'s non-tty
  capture — a shell-environment artifact, not a code or data issue.

I did not attempt to fix these two pre-existing failures: neither is in
scope for O31, and "fixing" an environment variable or a shared venv's
install location from inside an isolated, commit-nothing worktree run
carries more risk than value here.

## Files changed (this diff)

- `scripts/render_underhood_benchmark.py` — new, the regeneration step.
- `web/src/underhood/benchmarkData.ts` — regenerated output.
- `tests/unit/test_underhood_benchmark.py` — new, drift guard + findings
  pinned as tests.
- `tests/unit/test_render_determinism.py` — added the new renderer to
  `COMMITTED_RENDERERS`.
- `docs/restructure/backlog.yaml` — O31 `status: done` + closing note;
  `summary:` roll-up counts and `next_ready` list updated to match.
- `docs/plan/roadmap.html` — re-rendered to match the backlog change
  (worktree copy only; the main-tree copy was verified unaffected, see
  above).

Nothing was committed or pushed, per the dispatch instructions.

```
METRICS
files_read: 16  [web/src/underhood/benchmarkData.ts, knowledge/upgrade-plans/p0-benchmark/benchmark_p0.py, knowledge/upgrade-plans/p0-benchmark/benchmark_p0_results.json, knowledge/upgrade-plans/docmeta-p0-verdict.md, docs/reviews/graph-vs-files-experiment/prompts/coding-shared-o31.md, docs/restructure/backlog.yaml (multiple offsets, O31 entry + summary block), scripts/render_enforcement_matrix.py, tests/unit/test_enforcement_matrix.py, tests/unit/test_load_map_json.py, tests/unit/test_render_determinism.py, web/package.json, config/taxonomy/ui-components.yaml (grep context), MODULE_MAP.md (grep context), scripts/render_board.py, scripts/render_roadmap.py, docs/plan/board.html]
searches_or_queries: 9  [Grep "benchmarkData" (repo-wide), Grep "docmeta" -i (repo-wide), Bash grep "O31" backlog.yaml, Bash grep "drift" MODULE_MAP.md, Bash grep "drydocs-web|web-console" MODULE_MAP.md, Grep "benchmarkData|underhood" config/taxonomy/ui-components.yaml, Bash grep -rln "render_enforcement_matrix|render_load_map|render_gates" config/ docs/ MODULE_MAP.md, Bash grep -n "REPO=|BOARD_OUT|Path(__file__)|def main" scripts/render_board.py, Bash grep -n "def render_roadmap|DEFAULT_ROADMAP" scripts/render_roadmap.py]
tool_calls_total: 74
blocked_on: nothing — the FILES track's only rule (no Neo4j/Cypher/graph access) was never needed since the harness output was read from its committed JSON file, never from a live database
```
