# Task (identical for both tracks): O31 — regenerate benchmarkData.ts from a real harness run

Backlog item O31 (module drydocs-web, epic web-console), verbatim acceptance:

> benchmarkData.ts is produced by a documented regeneration step (a script, or a recorded
> manual procedure in the file header/a sibling README) that reads a real evaluation-harness
> run rather than the hand-carried P0-verdict numbers; the /under-the-hood scoreboard renders
> unchanged in shape from the regenerated data; build + lint green.

Your job, in this order:

1. **Establish the premise before acting on it.** Find the docmeta evaluation harness and
   determine whether a real run's output actually exists and in what shape. **If it does
   not, STOP and report that** — a documented regeneration step over numbers you never
   sourced is exactly the failure this item exists to remove. A truthful "the harness output
   does not exist; here is what would have to produce it, and here is the shape it must
   emit" is a CORRECT and complete outcome, scored as such.
2. If the output does exist: build the regeneration step (a script alongside the other
   `scripts/render_*.py`, or a recorded manual procedure in the file header / a sibling
   README — the acceptance allows either; choose and say why), regenerate
   `web/src/underhood/benchmarkData.ts` from it, and confirm the `/under-the-hood`
   scoreboard renders **unchanged in shape** from the regenerated data.
3. Record the change the way this repo records changes of this kind. Do not assume where
   that convention lives — **find it**, and say how you found it. This repo keeps ledgers
   and pinned counts in more than one place, and a generated artifact usually acquires a
   drift guard.
4. Run the checks. **"Green" means the repo's own guard suite —
   `poetry run pytest tests/unit -q` — not only the checks the acceptance names.** The web
   build and lint (`npm run build` / `npm run lint`, whatever `package.json` defines) are
   necessary and not sufficient. Quote the actual output lines, do not assert a result.

You are in an ISOLATED WORKTREE. Commit NOTHING.

When done, write BOTH of these to the absolute results path given in your dispatch block
(they are in the MAIN tree, not your worktree):
- `<run>.diff` — `git diff` output with `git status --porcelain` appended;
- `<run>-report.md` — your full report AND the metrics block below. Your report is an
  artifact of the experiment, not just a message: if it is not written to that file, it does
  not exist for grading.

Metrics block, verbatim keys, at the end of the report file:

```
METRICS
files_read: <n>  [list every one]
searches_or_queries: <n>  [each one, verbatim]
tool_calls_total: <n>
blocked_on: <anything the track rules prevented, or "nothing">
```

**Do not report timestamps or durations** — the orchestrator stamps those. Report only what
you did.
