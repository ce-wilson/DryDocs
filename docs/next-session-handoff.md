# Next-session handoff

> **Rolling file — overwrite it, do not append.** One screen of "where things stand"
> for picking the work up on the other machine. Durable state lives in
> `docs/restructure/backlog/` (the claim channel — one file per item) and
> `docs/port/port-prompt.md`; this is the narrative that git alone does not carry.
>
> **Written 2026-08-24 (laptop `NewThinkpad`, session close), producer head `1cbacd7a`;
> certified base = tag `port-base-20260824` @ `68b53716` (commits after it ride the
> next port — normal, not a discrepancy).**

## 1. WAVE 2 IS CERTIFIED AND WAITING

**`port-base-20260824` @ `68b53716`**, preflight **7/7**, range
**`213e1d12..port-base-20260824`** — **182 commits**, ledger steps **178-213**.
Suite 2382 passed / 9 skipped (laptop `NewThinkpad`, samples-dir present,
`RECONCILE_BEFORE_DIR` unset — J18). CI green at the tagged commit.

**No hand prompt has been written for this range, deliberately.** Unlike the
`port-base-20260820` port, nothing here needs its own apply sequence — everything
applies by the manifest. What it DOES need is that the reader opens five steps first,
because they change behaviour or delete something the other side may hold:

| step | why it needs reading before the apply is planned |
|------|--------------------------------------------------|
| **195** | S8 splits `cli.py` (3184 lines) into a composition root + six domain modules. `drydocs/cli.py` is `evaluate` — biggest hand-merge in the range. |
| **209** | G79 removes `refresh-reference` **by name**; three subject commands replace it. Any runbook or schedule calling it breaks. |
| **210** | G81 makes `DRYDOCS_DATA_ROOT` **mandatory** — the first data-path command after the port exits 2 until it is exported. Also RELAY-12. |
| **188** | G87/G88/G101 migrate live vocabulary ids and ship two `.cypher` migrations that must run against the consumer's own graph. |
| **212** | the range **deletes** `docs/reviews/port-review-7c18ff4b-20260820.md` from the producer tree — an untracking (`103f240c`), not a retraction. |

**Also new this range and relevant AT the close:** step 208 — `scripts/port_backlog_union.py`
lands at `35e6d103`, which is INSIDE this range, so unlike the last port the company
now has it. Run it at close and paste the block into the PORT-REPORT.

## 2. TWO CLOSE-OUT GAPS, BOTH THE USER'S CALL

1. **The `port-base-20260820` port is REPORTED COMPLETE (user, 2026-08-24) but its four
   J35 fields have not reached this file.** The roll note records it as
   **USER-REPORTED**, not as the J35 record, and nothing was filled in from this side —
   no producer figure may stand in for a company acceptance number. If the company
   PORT-REPORT is available, the paragraph can be upgraded now instead of at the next
   port: applied RANGE + `rev-list --count`, PORT COMMIT(s), BACKUP TAG + its proof,
   ACCEPTANCE NUMBERS.
2. **The `caa0406` close-out is still unrecorded** — three fields, plus RELAY-7 owed
   company-side. Unchanged from the last two handoffs; the block above the
   "Last CONFIRMED-COMPLETE port" section in `port-prompt.md` says what rides on it.

## 3. What landed today (all pushed; CI green at HEAD)

- **`3f1cac70`** — the three cited paths that resolved nowhere, and **RELAY-12**. The
  G81 relay had been sitting OUTSIDE the numbered section while `relays_missing_basis()`
  parses only between `STANDING RELAYS` and `OWED COMPANY-SIDE:`, so check 5 was passing
  GREEN on a relay it structurally never inspected. Nothing was wrong with the relay —
  what was wrong is that the green meant nothing about it.
- **`9e621887`** — the roll: steps 178-213 plus the coverage footnote.
- **`3b4d8e76` + `68b53716`** — the CI failure and its repair (see §4), the tag point.
- **`1cbacd7a`** — the roll note's range count and tag location corrected, and the
  ACCEPTANCE GATE's stale full-suite reference refreshed.
- **`d222290e`** — Idea-161 closed into the audit trail.

## 4. THE ONE THING WORTH CARRYING TO THE OTHER MACHINE

**A guard can pass locally and fail in a fresh clone because of an UNTRACKED file that
is still on disk.** The roll went RED on CI while the same suite passed here: step 212
cites `docs/reviews/port-review-7c18ff4b-20260820.md`, which `103f240c` untracked but
which this laptop still holds. `test_runbook_currency.py` asks the **filesystem**, not
git. Any machine that ever held the file gets the same false pass; only a new checkout
sees the truth.

Fixed as a `HISTORICAL_PATHS` entry whose reason carries the trap, and **verified by
moving the file aside and re-running** — not by trusting the local green. This is the
Idea-111 class (an instrument whose failure mode is silence) and it is the reason the
session ritual's CI check is a numbered step rather than a habit.

## 5. Open and unchanged

- **Idea-162** — the company occupies `DD1`–`DD10` in the PRODUCER band. Capture-only;
  nothing to do until a producer `DD` series is proposed, which is the only way that
  decision would get made by accident.
- **Idea-160** — a SOURCE-mode `refresh-teams` needs `pat_team_roles.csv`, which nothing
  emits. Fails loud by name (G78), so it is a task, not a bug — but the first company-side
  real run meets it, and step 191 says so.
- **Idea-158** — `snapshot.ps1`'s board refresh can half-fail and report a traceback with
  no traceback in it. Root cause on this machine is `VIRTUAL_ENV` pre-set to `agents\.venv`
  in the agent shell, inherited by `poetry run`. Confirm all nine renders landed rather
  than trusting the warning line.
- **Idea-159 / S13** — four tests pass in the full suite and fail when their file runs
  alone (the `cli_*` circular import the S8 split exposed).
- Five items sit `in_progress` (E1, G62, K16, L19, MM7) and were NOT touched.
