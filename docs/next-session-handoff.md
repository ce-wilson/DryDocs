# Next-session handoff

> **Rolling file — overwrite it, do not append.** One screen of "where things stand"
> for picking the work up on the other machine. Durable state lives in
> `docs/restructure/backlog.yaml` (the claim channel) and `docs/port-prompt.md`; this
> is the narrative that git alone does not carry.
>
> **Written 2026-08-01 (laptop), producer head `fb798c5`.**

## 1. Do this before you write any Python — two one-time local steps

**CI now BLOCKS on ruff.** `ruff check .` and `ruff format --check .` are both
gating as of J10 stage 5. An unformatted commit reds the build; it no longer
warns. `poetry run ruff format .` before committing, or expect the failure.

Two settings live in *git config / the working tree*, not in the repo, so each
clone needs them once. The desktop has had neither applied:

1. `git config blame.ignoreRevsFile .git-blame-ignore-revs` — worth setting, but
   **the earlier version of this line overstated it and was corrected by
   measurement** (desktop 2026-08-01, reproduced on the laptop). It claimed
   blame would otherwise land on the reformat. It mostly does not.

   On `drydocs/cli.py` — the most-reformatted file, untouched since stage 3 —
   only **41 of 2,055 lines (2%)** trace to the reformat at all, and the setting
   reattributes **zero** of them: identical counts with the config on and off,
   and with an explicit `--ignore-rev`. The reason is structural, not a
   misconfiguration: all 41 are lines the formatter *created* — 14 blank, 27
   lone `(`/`)` continuation lines from exploding calls across lines — and a
   line with no earlier version has nothing to reattribute to. The other 98%
   never pointed at the reformat, because `ruff format` re-wrapped and
   re-spaced far more than it rewrote.

   Keep the config: it is correct, costs nothing, GitHub's blame view honours
   the file, and a future reformat that genuinely rewrites lines will have
   something to reattribute. Just do not expect it to have rescued this one.
   General rule worth carrying: ignore-revs pays off in proportion to how many
   *existing* lines a mechanical commit modified, which for a formatter is
   usually far fewer than the diffstat suggests.
2. If `ruff format --check .` reports far more files than expected (~315 rather
   than 0), the working tree is CRLF while the index is LF. Fix once:
   `git add --renormalize .`, then delete and re-checkout the tracked `.py`
   files. No committed bytes change. This bit the laptop; the desktop measured
   clean, so it may already be fine.

## 2. J10 ruff — DONE producer-side, and it found three real defects

All six commits are on `main` (merged `--no-ff` as `fb798c5`; never rebase that
branch — `.git-blame-ignore-revs` records the stage-3 commit's own SHA).
**1,017 findings → 0**, 284 of 328 files reformatted, suite 1270 passed / 7
skipped unchanged at every stage.

The user ruled the two open calls: E501 ignored-with-reason; keeper set decided
**per-origin**, which the 2026-07-19 sizing could not have anticipated — **177
of the 362 post-format findings (49%) were vendored** Anthropic skill scripts
(`.claude/skills/{docx,pptx,xlsx,pdf,skill-creator}`, three near-identical copies
of the same office validators). Those became an `extend-exclude`;
`.claude/skills/groom-backlog` is ours and stays in scope. 30 findings in our own
code were **fixed rather than ignored**.

Worth knowing because each would have been buried by the cheaper option:

- **Ruff's F841 unsafe fix leaves dead code.** It strips the assignment target
  but keeps the call — `holdout = data.get(...)` becomes a bare `data.get(...)`.
  Six landed across three files. Diagnosis right every time, fix wrong every time.
- **A `pytest.raises(Exception)` never proved what its name claimed** — it passes
  on a typo'd attribute name too. Narrowed to `FrozenInstanceError`.
- **RUF003 was hiding an encoding bug**, not a style nit: `â†’` in
  `test_query_specs.py`, a double-encoded `->`. Tree sweep found no others.

Also: the plan doc's E402 premise was **wrong** (it assumed `sys.path` setup in
`scripts/`; all six hits are `pytest.importorskip` guards), and B008 had grown
14 → 26 while CI was advisory. Both corrected in
[`docs/ruff-format-convergence.md`](ruff-format-convergence.md).

**The live next action for this stream is the COMPANY side**, and nothing
producer-side is waiting on it. Instructions are unchanged and now current in
that doc: stages 1–3 regenerate locally, 0 and 4 port, 5 ports but only once
their own residuals hit zero.

## 3. Still open from the previous handoff — please confirm

`PORT-REPORT-57914bf4` merged company-side as `7b85a034` but, as of the desktop's
2026-08-01 note, **had not been pushed to company origin**. That is the user's
call and cannot be verified from the producer side. If it still has not happened,
the port exists in exactly one place.

## 4. Ritual state

- Depgraph snapshot **current**: `drydocs-20260801-1257.json` at `fb798c5`.
- Renders verified deterministic — re-rendering board + design docs after the
  commit produced zero drift.
- Producer CI green. Suite 1270 passed / 7 skipped / 10 deselected.
- Note the count differs from the desktop's 1272/5 on the same tree: two tests
  skip here because their machine-local psgmgr sample CSVs are gitignored. Same
  1277 total. Not a regression — do not chase it.

## 5. Board state

**73 todo · 1 in progress (E1, gate-deferred) · 197 done.** J10 was the second
in-progress item and is now closed.

Oldest genuinely-pullable: **O27**/**O28** (2026-07-22, p3, dependency-free) or
**Q7** (p2 — `docs-verify`: declared-vs-loaded per doc corpus, whose value rose
when Q13 registered a corpus at `confirmed: false` and N9 made
`doc-source-registry.yaml` the single home).

Still parked with reasons: **Q6** (needs `DryDocs-bkup`. The desktop reported it
absent; **searched the laptop this session and it is absent here too** — `C:` is
the only mounted drive, nothing matching `DryDocs-bkup*` to depth 4. So Q6 is
waiting on the *media*, not on being at the right machine — checking the other
box will not unblock it), **J13** (skip until the user supplies the term-list
confirmation).

## 6. The pattern from last session held, in a new form

The previous handoff named it: *a record that can only be checked against itself.*
J10 produced the inverse and it is worth carrying — **a check that fires
correctly but whose remedy is wrong**. Ruff was right about all six F841 sites and
right about RUF003; accepting its *fix* would have left dead code, and accepting
the cheap *ignore* would have preserved an encoding bug. The J16 port-manifest
guard was the good case: it caught `.git-blame-ignore-revs` having no
disposition, and the remedy it forced — decide, and write down why — was the
right one. Prefer guards that make you rule on something over guards that offer
to clear themselves.
