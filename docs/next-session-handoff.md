# Next-session handoff

> **Rolling file — overwrite it, do not append.** One screen of "where things stand"
> for picking the work up on the other machine. Durable state lives in
> `docs/restructure/backlog/` (the claim channel — one file per item) and
> `docs/port/port-prompt.md`; this is the narrative that git alone does not carry.
>
> **Updated 2026-08-25 (desktop, at the 20260825 certification): certified base is now
> tag `port-base-20260825` — 230 commits, `213e1d12..port-base-20260825`, preflight 7/7,
> suite 2431/11 (desktop MSI), steps 178-227.** The 2026-08-24 series below is superseded
> by extension, not withdrawn: this tag is `...824c` plus steps 221-227 (ADR 0014 ruled
> with amendments, G105 log-kinds, G107 batch run logs, R23 CLOSED — the desktop store
> was purged 2026-08-25 and §5 below is DONE — the escalation-census relay, the alias
> sanitization + Scan D, and the C27 CatalogSubLOB ruling). Read steps 226 and 223
> before planning the apply; the range's hand prompt
> (`catalog-sublob-and-db-alias-company-prompt.md`) was delivered by hand and executed
> company-side 2026-08-25, then retired to internal-local/archive/ per the delivery-pack
> rule -- still IN the range at the tag, so the apply carries their copy. The rest of this
> file is the 2026-08-24 narrative and still reads correctly against the longer range.

## 1. WAVE 2 IS CERTIFIED AND WAITING — AND IT GREW

**`port-base-20260824c`**, preflight **7/7**, range
**`213e1d12..port-base-20260824c`** — **208 commits**, ledger steps **178-220**.
Suite **2385 passed / 9 skipped** (laptop `NewThinkpad`; 6 skips are reconcile guards
with `RECONCILE_BEFORE_DIR` unset, 3 are the production sample CSV being absent — J18).

**Why three tags carry the same date.** All three certified 7/7 against the same base
and each is the previous one plus commits, so take the longest. `port-base-20260824`
(`68b53716`, 182 commits) was the morning base; HEAD then moved 22 commits past it while
nobody applied it, so those were ledgered as **steps 214-220** and re-certified as
`...824b` (`68b1c03b`, 205); `...824c` is a ledger ACCURACY repair on top with no new
payload — step 219 had described a resolver change G109 does not contain and step 216
named the driver instead of the module. **Port the longest range in one apply.** If an
apply is already in flight against an earlier tag, finish it and take the remainder
next — do not re-target mid-apply.

**No hand prompt for this range, deliberately** — everything applies by the manifest.
What it needs is that the reader opens five steps first, because they change behaviour
or delete something the other side may hold. **Steps 214-220 add none of these:**

| step | why it needs reading before the apply is planned |
|------|--------------------------------------------------|
| **195** | S8 splits `cli.py` (3184 lines) into a composition root + six domain modules. `drydocs/cli.py` is `evaluate` — biggest hand-merge in the range. |
| **209** | G79 removes `refresh-reference` **by name**; three subject commands replace it. Any runbook or schedule calling it breaks. |
| **210** | G81 makes `DRYDOCS_DATA_ROOT` **mandatory** — the first data-path command after the port exits 2 until it is exported. Also RELAY-12. |
| **188** | G87/G88/G101 migrate live vocabulary ids and ship two `.cypher` migrations that must run against the consumer's own graph. |
| **212** | the range **deletes** `docs/reviews/port-review-7c18ff4b-20260820.md` from the producer tree — an untracking (`103f240c`), not a retraction. |

**Also new this range:** step 208 — `scripts/port_backlog_union.py` lands at `35e6d103`,
INSIDE this range, so the company now has it. Run it at close and paste the block into
the PORT-REPORT.

**Two NEW relays ride this extension** (RELAY-14, RELAY-15) — see §3.

## 2. TWO CLOSE-OUT GAPS, BOTH THE USER'S CALL

1. **The `port-base-20260820` port is REPORTED COMPLETE (user, 2026-08-24) but its four
   J35 fields have not reached this file.** The roll note records it as
   **USER-REPORTED**, not as the J35 record, and nothing was filled in from this side —
   no producer figure may stand in for a company acceptance number. If the company
   PORT-REPORT is available, the paragraph can be upgraded now instead of at the next
   port: applied RANGE + `rev-list --count`, PORT COMMIT(s), BACKUP TAG + its proof,
   ACCEPTANCE NUMBERS.
2. **The `caa0406` close-out is still unrecorded** — three fields, plus RELAY-7 owed
   company-side. Unchanged from the last three handoffs; the block above the
   "Last CONFIRMED-COMPLETE port" section in `port-prompt.md` says what rides on it.

## 3. What landed in this session

- **Steps 214-220** — the `neo4j-skills` trim-note correction (214), the G102 fold's
  prose tail incl. the `data-context-extractor` skill that was still routing agents at
  two dead databases (215), the design-doc renderer's nested-fence fix (216), runbook
  block annotation (217), ADR 0014 / G104 (218), G109 making `landing-zones --check`
  see both zone declarations instead of half of them and ruling the Confluence capture
  out of the tree (219), and doc 08 Phase 2 — psgmgr censused 7/7 with `CM_DEF_VJOB`
  corrected to a TABLE (220).
- **RELAY-14 — the id-space partition is still one-sided, and it has now cost a
  capture.** A company session captured an inbox entry with **no id at all**. Step 160
  predicted exactly this. The relay separates the two halves: the header and uniqueness
  guards in `test_plan_ideas.py` carry NO band assumption and port as-is (they make that
  failure impossible today), while the `n >= 10000` mirror assertion stays a company
  decision. It also corrects two claims that session made about the producer tree.
- **RELAY-15 — Control-M extraction is internal-only work.** Profiling is theirs by
  design and four baked-in expectations are producer guesses; neither extract has a
  data-center bind and one was deliberately not built; and the DBA staging ask is
  already written as `controlm_staging_ddl.sql` — what is missing is a per-DC run
  recipe, not a schema. Scope is three DCs with the fourth a deliberate cut (SME).
- **Idea-168/169/170** captured and the internal DC inventory updated (real identifiers
  stay in `internal/`).

## 4. THE ONE THING WORTH CARRYING TO THE OTHER MACHINE

**An idea capture that carries a COMPANY action is on a dead channel until it becomes a
relay.** `docs/restructure/IDEAS.md` is `union-append`, so the TEXT does reach the other
side — which is exactly what makes this easy to get wrong. But the port prompt's own
relay section says it plainly: the relays exist "replacing the idea inbox, which your
repo never reads." Three entries written this session (168, 169, 170) each ended in a
company action, and all three would have shipped as inbox prose nobody opens. They are
now RELAY-14 and RELAY-15.

This is the RELAY-12 failure from `3f1cac70` in a different costume: there, a live relay
sat OUTSIDE the parsed section and check 5 passed green on something it structurally
never inspected. Here the obligation sits outside the *read* section. **Test: if a
capture ends with "they need to…", it is a relay, not an idea.**

## 5. OWED ON THE DESKTOP — one action, and only that machine can do it

**R23 clause (d): purge `agents/graph_qa/.adk/session.db` on the DESKTOP.** The fix
landed 2026-08-25 (laptop) and no new turn can write a token, but the stores already on
disk are unaffected by it. The 2026-08-21 observation was made on the desktop —
session `ask-jdoe4821-wjtacr8x`, the raw bearer token verbatim in all three user events
— and those tokens stay REPLAYABLE for the life of the API process, because
`InMemorySessionStore.issue` mints with no expiry and only `revoke` or a restart ends
one. **The laptop was checked and is clean** (4 events, zero `api_token` mentions, file
dated 2026-07-23, i.e. it predates R5), so this is one machine's action, not both.
Disk hygiene only, not history rewriting: `.adk/` is gitignored, so nothing reached the
repo. Record the purge in R23's close note with the machine named (J18).

## 6. Open and unchanged

- **Idea-162** — the company occupies `DD1`–`DD10` in the PRODUCER band. Capture-only.
  A 2026-08-24 report describes that series as `DD10001`, which would put it in the
  company band; the producer cannot read their letter series, and the hazard is
  unchanged either way because `DD1`–`DD9` stay in the producer band regardless.
- **Idea-160** — a SOURCE-mode `refresh-teams` needs `pat_team_roles.csv`, which nothing
  emits. Fails loud by name (G78), so it is a task, not a bug — but the first company-side
  real run meets it, and step 191 says so.
- **Idea-158** — `snapshot.ps1`'s board refresh can half-fail and report a traceback with
  no traceback in it. Root cause on this machine is `VIRTUAL_ENV` pre-set to `agents\.venv`
  in the agent shell, inherited by `poetry run`. Confirm all nine renders landed rather
  than trusting the warning line.
- **Idea-159 / S13** — four tests pass in the full suite and fail when their file runs
  alone (the `cli_*` circular import the S8 split exposed).
- **The `controlm-hosts-topology` DC scope call** (22 data centers vs 4 production) is
  still SME-owned and OPEN. The three-DC extraction cut does NOT rule it — different
  question, same word.
- Five items sit `in_progress` (E1, G62, K16, L19, MM7) and were NOT touched.
