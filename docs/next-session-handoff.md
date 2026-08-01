# Next-session handoff

> **Rolling file — overwrite it, do not append.** One screen of "where things stand"
> for picking the work up on the other machine. Durable state lives in
> `docs/restructure/backlog.yaml` (the claim channel) and `docs/port-prompt.md`; this
> is the narrative that git alone does not carry.
>
> **Written 2026-08-01 (desktop), producer head `3882db5`.**

## 1. The cross-repo port is COMPLETE — this is the big one

`PORT-REPORT-57914bf4` landed company-side as merge `7b85a034` (`--no-ff`, baseline
`7ffd430c` preserved as first parent). Range `e60822fc..57914bf4`, 55 commits.
Company acceptance: Track-1 `120/3/0`, full `1569/24/0`.

**Merged but NOT pushed to company origin as of this writing** — that push is the
user's call and had not been made. If it still has not, that is the first thing to
check; nothing producer-side depends on it, but the port exists in one place until
it happens.

Producer side is fully rolled (`3882db5`): `docs/port-prompt.md` is at **v3, 398
lines** (was 552), steps 50+51 collapsed, live ledger is **step 52 only**.

Two outcomes that changed the plan and are worth knowing before touching anything:

- **N9 registry v2 was FULL-ADOPTED company-side**, not deferred as recommended — all
  57 v1 sources migrated, 18 loaders rebound via `config/loader-source-overlay.yaml`.
  D2's overlay is what made that possible. **T19 now covers the N3–N6 load-map stream
  only**; the id-collision blocker is resolved by the v2 rename.
- **T11 was already discharged** (company ratified L7 on 2026-07-27) while the producer
  tracker still read `pending`. All 17 tracker rows now carry
  `pending (producer belief, as of <date>)` and a header saying status here is a
  producer *belief*, never company state.

## 2. J10 ruff — IN PROGRESS, blocked only on two answers

Stage 0 is done (`f18c88e`) and B023 is ruled + fixed (`b3b90dc`). The port boundary
is settled, so **stages 1–5 are unblocked** and want one clean sitting.

Live baseline at `3882db5`, ruff 0.5.7: **1,017 findings**, 404 safe + 42 unsafe,
**284 of 328 files** would reformat. Grows ~180 findings per 10 days while CI is
advisory.

**Two open calls, both the user's, neither needing any lull:**

1. **E501 residual policy** — recommendation: ignore with a reason comment ("formatter
   owns layout; residual is prose in strings/comments"). ~206 lines remain after
   formatting, nearly all prose.
2. **Keeper set** — B008 (14, Typer defaults), RUF001/2/3 (15, prose unicode), E402
   (6, deliberate `sys.path` in scripts) as reasoned `per-file-ignores`.

Then run stages 1→5 per `docs/ruff-format-convergence.md` (commit subjects are the
contract: `J10 stage <N>`). Preconditions: no other session holding uncommitted `.py`
work, and the stage-3 commit's own SHA goes into `.git-blame-ignore-revs`.

## 3. Ritual state

- Depgraph snapshot is **stale** — last one was `554a4e8`; run
  `knowledge\depgraph-snapshots\snapshot.ps1` at the next close-out.
- Producer CI is **green** (`7ccc655` fixed a 10-day red: renderers sorted `Path`
  objects, which is case-folded on Windows and case-sensitive on POSIX;
  `tests/unit/test_render_determinism.py` now pins the rule).
- Suite at 1272 passed / 5 skipped.

## 4. Board state

73 todo · 2 in progress (E1 gate-deferred, **J10**) · 196 done.

Oldest genuinely-pullable next_ready, if not doing J10: **O27**/**O28** (2026-07-22,
p3, dependency-free) or **Q7** (p2 — `docs-verify`: declared-vs-loaded per doc corpus,
whose value rose when Q13 registered a corpus at `confirmed: false` and N9 made
`doc-source-registry.yaml` the single home).

Still parked with reasons, not silently skipped: **Q6** (needs `DryDocs-bkup`, not on
the desktop — check the laptop), **J13** (its own notes say skip until the user
supplies the term-list confirmation).

## 5. One pattern worth carrying

Three defects this week shared a shape: **a record that can only be checked against
itself.** The enforcement-matrix drift guard compared a render to its own regeneration;
the T11 tracker row asserted company state the producer cannot see; the PORT-REPORT
asserted reversibility nothing had verified against git. Each fix put the check where
the evidence actually lives. Worth suspecting the shape rather than fixing instances.
