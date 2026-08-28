# Python 3.12 interpreter standard — DryDocs venv rebuild (SME note)

Status: SME direction, ready to apply. Record completion and the re-measured baseline in
your own upgrade ledger; nothing needs to flow back from this note.

## The direction

Every DryDocs virtual environment — the main checkout's and every worktree's — is built
with Python 3.12, never the box default 3.14. Rebuild any venv that was not built by the
worktree helper script, starting with the main checkout.

## Why — the mechanism, so nobody "upgrades" it back

- The box default interpreter is 3.14. `poetry install` on 3.14 cannot build
  `oracledb 2.5.1` (needs MSVC) or `tiktoken 0.7.0` (needs Rust) — neither ships a
  cp314 wheel. The install fails **late**, leaving a venv that looks fine and imports
  fine but is incomplete.
- The symptom is roughly 58 unit-test failures that are pure environment noise. That
  count currently matches the recorded known-red baseline digit for digit, which means
  an environment problem is indistinguishable from the recorded code baseline until the
  rebuild happens and the baseline is re-measured.
- Working around it by hand-installing a newer package trips the repo's environment-drift
  guard, which aborts pytest before collection — by design. The guard's message is
  correct: this is one wrong environment, not fifty-eight broken tests. The venv rebuild
  is the only sanctioned fix.
- The shell pre-sets `VIRTUAL_ENV` to the agents venv, which outranks the in-project venv
  and trips the same guard. Clear it first, every session.

## Steps — main checkout first, then repeat in any hand-built worktree

```powershell
$env:VIRTUAL_ENV = $null
poetry env use <path-to-highest-3.12>\python.exe   # deliberately 3.12, not newest
poetry install --sync
poetry env info -p                                  # confirm: a 3.12 venv path
poetry run python -c "import oracledb, tiktoken; print('deps ok')"
```

Worktrees created by the helper script already pin 3.12 and install from the lockfile;
rebuild only venvs that predate the helper or were built by hand. Treat any venv the
helper did not build as suspect until verified.

## After the rebuild — re-baseline, then update the working rule

1. Run the unit suite on main from a clean shell:
   `$env:VIRTUAL_ENV = $null; poetry run pytest tests/unit -q --tb=no -rf`
2. Whatever remains red after a **verified** 3.12 rebuild is real. Update the known-red
   working rule with the NEW count **and the failing-test list**, not the count alone —
   a list shrinks visibly as fixes merge; a bare count cannot tell "my change broke X"
   from "X was already red."
3. Expect part of any remainder to clear when the s8 company-split branch merges (it
   carries the traceability-chain restore). Anything still red after that merge is a
   backlog item, not an environment or baseline question.

## Durability — optional hardening, your call

- Tighten the pyproject python constraint to exclude 3.13+ until the wheel gap closes,
  so `poetry env use` on the wrong interpreter refuses up front instead of failing late.
- Extend the environment-drift guard to assert the interpreter version, so a
  wrong-python venv aborts collection with one clear message instead of dozens of
  misleading failures.
- Keep the worktree helper as the only venv builder.

Record the rebuild, the verification output, and the re-measured baseline in your
upgrade ledger.
