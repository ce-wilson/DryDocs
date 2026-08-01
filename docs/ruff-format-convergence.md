# Ruff formatter convergence — two-sided adoption plan (J10 amended scope)

**Status: PRODUCER SIDE COMPLETE (2026-08-01, laptop). Company side NOT STARTED.**
All six producer commits (stages 0–5) are on `main`; `poetry run ruff check .` and
`poetry run ruff format --check .` both exit 0 and CI blocks on both. The
**company-side instructions below are unchanged and now live** — they are the
next action for this stream, and nothing producer-side is waiting on them.
This doc remains the authority for the amended J10 scope; stage 0 added the
numbered step to [`docs/port-prompt.md`](port-prompt.md) pointing here. Decision
session: 2026-07-19 (measurements below are live from that session, producer tip
`83f97cb`); execution session 2026-08-01.

## Why this shape

The producer (`ce-wilson/DryDocs`) and company (`<company-org>/DryDocs`) repos
have **disjoint histories** ([`git-readme.md`](../git-readme.md)) — ports are
cherry-picks, not merges, so the classic mass-reformat objection (poisoned
merge-bases) does not apply. Instead of porting a ~6,800-line mechanical diff:

- **Each side formats its own reality.** The mechanical commits (lint autofix +
  `ruff format`) are marked **DO NOT PORT** and are *regenerated* company-side
  with the same pinned tool. Only the shared config and the small hand-authored
  fixes port as normal commits.
- Once both sides are formatted with the same tool + version + config, spurious
  style differences vanish from collision hand-reconciliation — future ports
  get *easier*.
- The repo stays **PRIVATE**. Transfer to the company side goes via **git
  bundle** (see the bundle note in `git-readme.md` §"How the company side
  applies it") — never by making this repo public
  (`internal/**` is tracked here, and the pre-rewrite history retains the
  deleted seal-sample twins; both gates are recorded in
  [`config/classification.yaml`](../config/classification.yaml)).

## Stage 0 executed 2026-07-31 — one finding worth carrying

`line-ending` in `[tool.ruff.format]` is set to **`lf`, not `auto`**, and stage 0
therefore also adds `*.py text eol=lf` to `.gitattributes`. Reason, found by
running it: `auto` infers the ending per file, so the same source formats
differently on a CRLF working tree than on the Linux runner — the exact
OS-dependent-output class that kept CI red 2026-07-21..07-31. But pinning `lf`
without the `.gitattributes` rule makes a Windows checkout materialize CRLF,
which makes `ruff format --check` report EVERY file as needing reformat on line
endings alone (284 -> 314 in the live measurement) and stage 5's "exits 0"
acceptance unreachable on that machine while passing on the runner. Both halves
are needed; the rule ports with stage 0, so the company inherits it.

Git stores LF either way, so no committed bytes change — a one-time working-tree
renormalization (`git add --renormalize .`, then re-checkout the `.py` files) is
all it takes, and stage 3 rewrites every file anyway.

## Measured baseline (2026-07-19, ruff 0.5.7) — SUPERSEDED, see below

**Re-measured 2026-07-31 at producer head `7ccc655` (same ruff 0.5.7):**
`ruff check .` = **1,019 findings** (was 838), **404** safe fixes + **42**
unsafe; `ruff format --check .` = **284 of 328 files** would be reformatted
(was 203 of 237). Advisory CI means the debt grows ~180 findings per 10 days.
The 2026-07-19 figures below are kept as the decision-session record.

### The 2026-07-19 figures (decision session)

- `poetry run ruff check .`: **838 findings** (was ~757 at groom time
  2026-07-13 — CI is advisory, so the debt grows until this executes).
- **358** safe auto-fixes + **20** more behind `--unsafe-fixes`.
- `ruff format` trial (run and reverted): **203 of 237 files** reformatted,
  ~3,897 insertions / ~2,872 deletions.
- **E501 line-too-long: 337 → 206 after format** — the formatter clears
  code-shaped long lines but (by design, like Black) never wraps strings,
  comments, or docstrings. The residual is prose. Pre-format distribution:
  ~170 `.claude/` tooling, ~109 shipped packages, 45 `tests/`, 13 elsewhere.

## Producer stages — the commit-subject contract

Commit subjects are the contract: the company side locates the boundary **by
subject, never by SHA**. Use these verbatim (each contains its stage tag):

| Stage | Content | Subject contains | Ports? |
|---|---|---|---|
| 0 | pin `ruff = "0.5.7"` **exact** (caret removed deliberately) + settle `[tool.ruff]` / `[tool.ruff.lint]` / `[tool.ruff.format]`; add the port-prompt step | `J10 stage 0` | **PORTS** — the shared contract |
| 1 | `poetry run ruff check . --fix` | `J10 stage 1` | DO NOT PORT — regenerate |
| 2 | `poetry run ruff check . --fix --unsafe-fixes`, hand-reviewed | `J10 stage 2` | DO NOT PORT — regenerate + review |
| 3 | `poetry run ruff format .`; own SHA appended to `.git-blame-ignore-revs` + `git config blame.ignoreRevsFile .git-blame-ignore-revs` | `J10 stage 3` | DO NOT PORT — regenerate |
| 4 | remaining findings per-rule in batches; keepers get explicit pyproject `per-file-ignores` with reason comments | `J10 stage 4` | PORT normally |
| 5 | ci.yml ruff step drops `continue-on-error` AND gains `ruff format --check` | `J10 stage 5` | PORT — company applies only after its own residuals are zero |

End state (both sides): `poetry run ruff check .` exits 0, `poetry run ruff
format --check .` exits 0, CI blocks both. Full suite green at every stage.
The ruff version is load-bearing on both sides — formatter output varies across
versions; upgrade the pin deliberately, in lockstep, via a ported pyproject
commit.

## Open calls — ALL RULED 2026-08-01. Kept as the decision record.

1. **Timing** — ✅ user's go given 2026-08-01; stages 1–5 ran in one sitting on
   the laptop with a clean tree and no concurrent `.py` work.
2. **E501 residual policy** — ✅ **ignore with a reason comment**, as
   recommended. 241 hits survived the formatter. `ignore = ["E501"]` in
   `[tool.ruff.lint]`, reason inline.
3. **Keeper set** — ✅ ruled per-origin rather than per-rule, because the
   residual split cleanly along a line the 2026-07-19 sizing had not seen:
   **177 of 362 findings (49%) were vendored** Anthropic skill scripts under
   `.claude/skills/{docx,pptx,xlsx,pdf,skill-creator}` — three near-identical
   copies of the same office validators. Those are now an `extend-exclude`, not
   a per-file-ignore: we do not author them and re-vendoring reverts any fix.
   `.claude/skills/groom-backlog` is ours and stays in scope.

   Of the rest: **B008** (26 not 14 — it grew while CI was advisory) per-file-
   ignored in `drydocs/cli.py`; **N817** (11) globally ignored, every hit being
   `import xml.etree.ElementTree as ET`; **N818** (3) and **N812** (1) per-file-
   ignored with reasons; **RUF001/2/3** split — vendored copies excluded, all 3
   of ours fixed. **E402's premise was wrong**: the doc assumed deliberate
   `sys.path` setup in `scripts/`; all 6 hits are `pytest.importorskip` guards
   in two test modules, which must precede the imports they guard.

   Everything else was **fixed, not ignored** (30 findings): E741 ×14, B017 ×2,
   RUF012, RUF007 ×2, N806 ×3, N802.

### Three findings from execution worth carrying to the company side

- **B017 was a real test defect, not a style nit.** `pytest.raises(Exception)`
  in `test_plan_board.py` "proved" frozen dataclasses reject writes — but it
  passes just as happily on a typo'd attribute name or an unrelated `TypeError`.
  Narrowed to `dataclasses.FrozenInstanceError`. Expect the same class of thing
  in company-only tests; B017 hits are worth reading, not bulk-ignoring.
- **Ruff's F841 unsafe fix leaves dead code.** It strips the assignment target
  but KEEPS the call: `holdout = data.get("holdout", 0)` becomes a bare
  `data.get("holdout", 0)`. Six landed across three files in stage 2. The
  diagnosis was right every time; the fix was not. Read that diff — §3.2's
  hunk-by-hunk review is where this gets caught.
- **A latent encoding bug hid behind RUF003.** `tests/unit/test_query_specs.py`
  contained `â†’` — a double-encoded `->` whose third byte is the RIGHT SINGLE
  QUOTATION MARK ruff was flagging. Blanket-ignoring RUF001/2/3 would have
  preserved it. A tree sweep found no others.

   **B023 — RULED AND FIXED 2026-07-31, ahead of the sweep.** Reviewed
   individually as the plan required. Both findings were ONE site, not two:
   `knowledge/upgrade-plans/p0-benchmark/benchmark_p0.py:206`, same closure,
   same variable, flagged twice because `marker` appears twice on the line.
   Verdict: **not a live bug** — `score` is called on lines 216/218/222, all
   inside the iteration that defined it, and is never stored, returned, or
   deferred, so late binding cannot trigger. Fixed anyway with `marker=marker`
   (bind at definition time), because the failure mode under any future
   refactor — laziness, collection into a list, parallelising the loop — is
   silently scoring every question against the LAST marker and publishing
   plausible wrong benchmark numbers with no error. A per-file-ignore would
   have preserved exactly that trap. `ruff check` 1019 -> 1017; the fix PORTS
   normally (hand-authored code, not a mechanical stage-2 commit).

---

# Company-side instructions (for the Opus 4.8 maintainer agent)

You are the company-side maintainer agent for `<company-org>/DryDocs` on GitHub
Enterprise. The producer (`ce-wilson/DryDocs`) has adopted the ruff formatter
and lint autofixes. Because the two repos' histories are **disjoint** (no
merge-base — see `git-readme.md` in the fetched branch), the mechanical commits
are **not cherry-picked**: you regenerate them locally with the same pinned
tool. Only the shared config and the small hand-authored fixes port as normal
commits.

Principle: **each side formats its own reality.** Your company-only files (the
real `drydocs-review` wiring, connectors, anything Canonical-COMPANY) are
formatted by *your* run — never by taking producer copies.

## 0. Preconditions — verify ALL before changing anything

- Working tree clean (`git status --porcelain` empty); no other session or
  agent has uncommitted `.py` work in flight.
- Producer `main` available. The producer repo is private; the normal channel
  is a **git bundle** received through an approved internal transfer (verify
  its SHA-256 against the transfer note first):

  ```
  git bundle verify <path-to>/drydocs-<date>.bundle
  git remote add cewilson <path-to>/drydocs-<date>.bundle
  git fetch cewilson main
  ```

  (If your environment can reach github.com and policy allows an authenticated
  fetch, `git remote add cewilson https://github.com/ce-wilson/DryDocs.git`
  works identically — visibility of the repo does not change these
  instructions.)
- You have read `git-readme.md` and `PORT-MANIFEST.yaml` from the fetched
  branch. The manifest stays the authority on per-path collision dispositions;
  these instructions add to that flow, they do not replace it.
- Full test suite green on your `main`. Record the pass count — it is your
  baseline for every later stage.

## 1. Identify the boundary commits (by subject, never by SHA)

In `git log --oneline --reverse cewilson/main`, locate the `J10` stages — the
dispositions are the producer-stage table above (stage 0 ports; 1–3 do not
port; 4 ports; 5 ports but is gated on §6).

## 2. Port up to the boundary

On your port branch (`git switch -c drydocs-port main`), cherry-pick the
producer range **up to and including stage 0**, resolving collisions per
PORT-MANIFEST as usual. For the stage-0 `pyproject.toml` collision:

- TAKE the producer's `[tool.ruff]` / `[tool.ruff.lint]` / `[tool.ruff.format]`
  sections and the dev-dependency pin `ruff = "0.5.7"` (exact — the caret is
  gone deliberately; the pin IS the contract).
- KEEP your own `version` string (standing rule).
- NEVER cherry-pick producer `poetry.lock` hunks. Regenerate instead:
  `poetry lock` (or `poetry update ruff`), then `poetry install`.
- Gate: `poetry run ruff --version` must print exactly `ruff 0.5.7`. If it
  does not, stop and fix the environment before proceeding.

## 3. Regenerate the mechanical commits (in place of stages 1–3)

Each is its own commit; run the full suite after each; expect zero behavior
change — treat any test delta as a defect in the run, not in the tests.

1. `poetry run ruff check . --fix`
   → commit: `chore(lint): ruff mechanical autofixes (regenerated company-side; producer J10 stage 1 equivalent)`
2. `poetry run ruff check . --fix --unsafe-fixes`
   → **review this diff hunk-by-hunk before committing** — unsafe fixes can
   change semantics (e.g. deleting an "unused" variable a company-only caller
   inspects). Commit with the stage-2-equivalent label.
3. `poetry run ruff format .`
   → commit: `chore(fmt): adopt ruff format (regenerated company-side; producer J10 stage 3 equivalent)`
4. Append the stage-3 commit's SHA (**yours**, not the producer's) to
   `.git-blame-ignore-revs` (create if absent), run
   `git config blame.ignoreRevsFile .git-blame-ignore-revs`, commit.

## 4. Continue the port

Cherry-pick the remaining producer range (stage 4 onward), skipping stages 1–3
you just regenerated. Post-format producer commits were authored under the same
tool + config, so their patch context matches your formatted files — collisions
on the integration files should now be content-only.

## 5. Company-only residuals — your own cleanup

After §3–4, `poetry run ruff check .` will still report findings the producer
never saw: they live in company-only code the producer cannot touch. Resolve
them yourself under the same policy the ported config encodes — fix per-rule in
small commits, or add `per-file-ignores` entries in pyproject with a reason
comment for rules deliberately kept in specific company-only paths. Do NOT
weaken the shared `select` list; scope any relief to per-file-ignores.

## 6. Only then: flip CI to blocking

Apply the producer's stage-5 commit (or make the equivalent edit) only when
BOTH hold on your branch:

- `poetry run ruff check .` exits 0
- `poetry run ruff format --check .` exits 0

## 7. Verification oracle — end state

- `poetry run ruff --version` = 0.5.7, matching the exact pyproject pin
- `poetry run ruff check .` and `poetry run ruff format --check .` both exit 0
- full suite ≥ baseline pass count, zero failures
- history shows the regenerated mechanical commits labeled company-side;
  `.git-blame-ignore-revs` carries your format SHA
- the CI ruff step no longer has `continue-on-error`

## Stop conditions — halt and report to your operator; do not improvise

- `ruff --version` cannot be made to match the pin.
- Any test that passed at baseline fails after a mechanical stage.
- The unsafe-fixes diff touches behavior you cannot verify locally.
- A post-stage-3 producer commit conflicts in a way PORT-MANIFEST doesn't cover.
- Any step would require committing real identifiers (SIDs, server names, org
  rosters) — never; see PUBLISH-BOUNDARY.md.

---

# Transfer without visibility change (repo stays private)

Producer side — create and fingerprint the bundle (agent-side creation is
permission-gated; run in a regular terminal if the session classifier blocks it):

```
git -C C:\coding\projects\sandbox\DryDocs bundle create C:\coding\projects\sandbox\drydocs-<date>.bundle main
git bundle verify C:\coding\projects\sandbox\drydocs-<date>.bundle
powershell -c "(Get-FileHash C:\coding\projects\sandbox\drydocs-<date>.bundle -Algorithm SHA256).Hash"
```

Email/transfer notes:

- **Approved internal channel only, to the company mailbox** — the bundle
  carries the full history, including the deleted seal-sample twins and
  `internal/`. Inside the company that is their own data coming home; anywhere
  else it is the exposure the publish boundary exists to prevent.
- Include the **SHA-256 in the message body** so the receiving side verifies
  integrity after transit.
- Mail filters often strip unknown extensions: if `.bundle` bounces, zip it or
  rename (e.g. `drydocs-<date>.bundle.zip.remove`) and say so in the body.
- Size limit trouble (>~25 MB): prefer an approved file-transfer service over
  split archives; ask the producer session for a split/rejoin recipe only as a
  last resort.
- Later transfers get smaller — incremental bundle from the last ported
  commit: `git bundle create drydocs-inc.bundle <last-ported>..main`.
- **Blocked-attachment fallback — base64 text (CHANNEL USED 2026-07-19;
  GitHub auth is blocked from company machines, binary attachments filtered):**
  `certutil -encode <bundle> <bundle>.b64.txt` producer-side (~+37% size; the
  BEGIN/END CERTIFICATE markers are normal), email the `.txt`, then
  `certutil -decode` company-side and verify SHA-256 + `git bundle verify`
  before fetching. If the inbound size limit bites, split the text file on
  line boundaries and rejoin with `copy /y part1.txt+part2.txt` — the decoder
  ignores whitespace seams.
