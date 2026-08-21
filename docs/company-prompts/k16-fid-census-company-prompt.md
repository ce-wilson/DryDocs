# Company-side prompt — run the FID directory census (K16, doc 09 phase 0)

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> The producer built the **method** and can never run it: this census measures a
> functional-id directory the producer repo does not hold and must not hold. What comes
> back here is **counts only** — never a row dump, never an account name.
>
> This runs **BEFORE** the `fid-identity-and-scope` gate, not after. That gate is drafted
> and unsigned, and §D2 says why: *"about two hundred accounts per application"* is an
> estimate it cannot rule on. The census turns it into *"N of ~200, and here is what the
> other rows are."* It also blocks **K17**, and K17 blocks the K2 tier-2 unblock.

> **RIDER 2026-08-19 — THE GATE HAS SIGNED (33/33) AND HALF THIS CENSUS ALREADY
> RAN. READ THIS BEFORE RUNNING ANYTHING.** The producer SME ran the Control-M
> half live on the replica (the S1-S5 session SQL in doc 09) and the gate walked
> from those numbers, so the paragraph above is now HISTORY: the gate no longer
> waits on this prompt. **What remains owed is the DIRECTORY half only** — the
> counts that need the id-owner/directory extract this repo and the producer
> machine do not hold: (a) total directory rows for the census application,
> (c) the remainder breakdown by the directory's own type/status columns, and
> the Q0 disagreement legs that need the directory's application assignment.
> Do NOT re-run the Control-M half; its numbers are in the gate record.
> Four corrections from the gate session bind your run: (1) there are TWO
> sources (doc 09 "Two sources, two grains") — the HR functional-type extract
> answers WHO OWNS and can never answer WHICH APPLICATION; the id-owner listing
> is the application side, and a by-application listing over-returns (all
> environments, all subtypes, ids connecting to OTHER applications). (2) §D2
> census classes: non-account owner values (null/inherited, folder-header rows,
> variable-deferred, template placeholders, connection-profile placeholders)
> are NAMED CLASSES counted OUTSIDE the join denominator — exclude them before
> any join or the rates are wrong. (3) `OWNER` is MIXED-CASE at rest — the old
> ALL-UPPER note recorded a normalization plan, not the data; normalize case on
> BOTH sides of the name join and report case-only mismatches, never fold them.
> (4) The 171-way name is the Control-M PLATFORM account (a run_as CLASS, not
> an anomaly) — classify run_as per JOB before joining; FileWatcher-type on the
> platform account is the designed pattern.

Venue: company `<org>/DryDocs`, current `main`. Name the venue in every claim (J18).

## Step 0 — the command

```
drydocs fid-census \
  --application <APP> \
  --directory <idowner-export.csv> \
  --map "account=<HEADER>,application=<HEADER>,type=<HEADER>,status=<HEADER>,owner=<HEADER>" \
  --run-as <controlm-jobs.csv> \
  --attribution <account-to-app.csv>
```

Optional: `--fid-facts <csv>` (demand set ii) and `--adhoc <csv>` (demand set iii),
each with a `--*-column` override. `--delimiter '|'` for raw SQL Developer exports.

**`--map` has NO DEFAULTS, deliberately.** The producer has never seen a
functional-id directory export, and `config/source-mappings/seal-extract.yaml`
records what happens when a loader's field names get mistaken for verified source
vocabulary — `SEALID` lived in the repo for months as a column name that appears
in no source. Name the real headers or the command refuses.

`--run-as` reads the Control-M extract's `owner` column by default
(`CM_DEF_VJOB.OWNER`, aliased `owner` in `controlm_jobs.sql`, which the psgmgr
ledger records as *"run-as tenant Functional ID (service identity, not a person);
also the `:run_as` scope-bind (exact match)"*). Override with `--run-as-column`.

## Step 0b — the tool, and what it refuses to do

`drydocs/fid_census.py` — pure. It opens no file, contacts no database, and writes
nothing; the CLI above is a thin adapter that injects every input.
`tests/unit/test_fid_census.py` guards it (17 tests, all synthetic).

**THE EXPORT'S GRAIN IS HANDLED EITHER WAY, and you do not need to determine it
first.** An "idowner search" may return one row per ACCOUNT (filtered by owner) or
one row per (ACCOUNT, OWNER) pair — and under the SME rule that every FID carries
**at least two human owners**, the second shape means a two-owner account
legitimately contributes two rows. So the census reports `directory_rows_total`
and `directory_accounts_total` SEPARATELY, counts a differing-owner repeat as
`multi_owner_rows` rather than a duplicate, and reserves `duplicate_directory_rows`
for a true repeat of the same (account, owner). Report both numbers.

Two refusals are deliberate, and you will hit both:

- **It returns counts and nothing else.** `FidCensus` holds `int` and `dict[str, int]`
  fields only, so a row dump is not merely discouraged — it is unexpressible in the
  return type, and a test pins that structurally. This is what lets the result travel
  back to the producer repo at all.
- **It will not guess a §G5 reading.** Every disagreement lands in `unruled` until a
  human rules it. See step 3.

## Step 1 — pick ONE application, and say which kind it is

The census is scoped to a single application **on purpose** (§D2: a one-time census
before any bulk pull). Pick one you can also get a Control-M-derived folder attribution
for — without that, the Q0 half is undecidable and the gate still cannot sign.

Report which application you chose **by kind, not by name**: is it a product-aligned
SEAL, a platform application, or one that has been through a decomposition? The §G5(b)
"stale directory" reading is far likelier in the third case, and the producer needs to
know whether the measured rate generalizes or reflects a special case.

## Step 2 — assemble the four inputs (read-only, zero graph writes)

1. **`directory_rows`** — the directory extract, filtered to that application. Map its
   real columns onto `DirectoryRow(account, application, account_type, status)`. The
   producer field names are mechanism roles; your real column spellings stay on your
   side. `application` is the directory's **own** assignment — the registration fact.
2. **`run_as_owners`** (demand set i) — distinct `run_as` / `J.OWNER` in the Control-M
   extract.
3. **`unresolved_fid_facts`** (demand set ii) — distinct `fact_value` on `STG_APP_FACT`
   rows with `fact_type='FID'` that the K2 resolver counts unresolved. That is
   `AttributionCoverage.unresolved_facts_by_tier['FID']`'s underlying values, from
   `drydocs/loaders/seal_attribution.py`.
4. **`adhoc_accounts`** (demand set iii) — account names in registered adhoc evidence
   (corpus `adhoc-sme-email`).
5. **`attribution_by_account`** — account → the application its Control-M-derived FOLDER
   attribution names (K8's confirmed app-code mapping). Accounts you cannot resolve go
   in as **absent**, not as a guess; they land in `undecidable`.

**No fourth demand set** without a use case (§D5: widening is a decision, not a drift).

## Step 3 — run it, then rule the disagreements one at a time

Run the census. Then look at `disagreements` and `disagreements_by_reading` — every
disagreement will be sitting in `unruled`, and that is the tool working correctly.

§G5 gives three readings, **distinguished per case and never globally**:

- `different_subjects` — both correct: a platform account serving a consumer application.
- `stale_directory` — an application decomposition into product-aligned SEALs happened
  and re-registration lagged. **This one is a remediation candidate**, not a modeling
  problem.
- `wrong_attribution` — the folder attribution is wrong.

Rule them **with the directory owner**, one case at a time, and pass the rulings back in
as `rulings={account: reading}`. Whatever stays `unruled` is reported as its own number.
Do not batch-assign a reading to clear the bucket: the ratio between (a) and (b) is the
entire point of Q0, and a batch assignment destroys it.

**Remember what a disagreement is NOT.** Registration and attribution answer different
questions — the directory records who *owns the account*, the app-code mapping records
whose work the *folder* is. Neither source corrects the other, and the census resolves
nothing.

## Step 4 — what comes back to the producer

Send back `census.as_dict()` — counts only. Specifically:

- (a) `directory_rows_total` **and** `directory_accounts_total` — both, since the
  grain determines which one "total directory rows" means
- (b) `demand_in_application`, `demand_by_source`, `demand_not_in_directory`
- (c) `remainder_by_type`, `remainder_by_status`
- **Q0**: `comparable`, `agreements`, `disagreements`, `undecidable`,
  `disagreements_by_reading`
- **The two-owners rule**: `accounts_below_owner_minimum`,
  `accounts_with_no_owner_recorded`, `owner_rule_measurable`
- `run_as_owner_types` (gate §Q5), `case_only_mismatches`, `multi_owner_rows`,
  `duplicate_directory_rows`, `reconciles`

Plus three sentences of prose the numbers cannot carry: the application **kind** from
step 1, whether the extract was a targeted query or a full extract filtered on your side
(that is gate **§Q3**, and it changes the confidential surface even when the loaded scope
is identical), and anything the directory owner said while ruling that the buckets do not
capture.

Those land in doc 09's *"The numbers"* table, which is already built and waiting with
every cell marked _pending_.

## Step 5 — three things to report even if they look like non-answers

1. **`case_only_mismatches` > 0 — BUT NORMALIZE BOTH SIDES FIRST (corrected 2026-08-19).**
   `CM_DEF_VJOB.OWNER` is **mixed case at rest** — the earlier all-upper note recorded
   the normalization PLAN, not the storage state (K17 session round 2, replica
   evidence) — and the SME has ruled the two are the SAME account
   (`UPPER(EMP_LAST_NAME) = UPPER(OWNER)`, gate §Q6). **So `UPPER()` BOTH sides
   in your extract query before feeding the census.** If you do not, essentially every
   real match lands in `case_only_mismatches` instead of `demand_in_application`, and the
   headline number reads as "the directory barely covers the estate" when it may cover it
   completely. The arithmetic still recovers the truth —
   `demand_in_application + case_only_mismatches` — but the honest fix is to normalize on
   the way in.
   **Once normalized, the counter regains its meaning: a non-zero value is then a REAL
   spelling difference beyond case**, which is an identity question for the gate and not
   a bug to paper over on your side. That is the number worth reporting.
   The census tool itself deliberately does NOT fold case (`fid_census._normalize` trims
   only) — a census that folds silently cannot report how much it folded. Normalizing is
   your extract's job, not the tool's.
2. **A non-application `account_type` in `run_as_owner_types`.** That answers gate §Q5 in
   the negative: if non-application types really do appear as run-as owners, type cannot
   be used even as an explanatory filter.
3. **`reconciles == False`.** The invariant is that every distinct ACCOUNT lands in
   exactly one of (b) or the remainder, and that the disagreement split is complete. A
   false here means an input assumption is wrong — report it as a finding rather than
   adjusting the inputs until it balances.
4. **`owner_rule_measurable == False`.** The export carried no owner column, so
   `accounts_below_owner_minimum: 0` means **unmeasured, not compliant**. Say which it
   was; the two are different answers and the census refuses to conflate them.
5. **`accounts_below_owner_minimum` > 0.** Accounts carrying fewer than two human
   owners violate the SME rule stated 2026-08-07. Report the count — the RULE itself
   becomes a graph test once an account→owner edge exists, which doc 09's phase list
   does not yet model (it goes account→APPLICATION and never account→PERSON).

## Step 6 — what this does NOT authorize

- **No bulk pull.** The demand set is the pull list; this census is the measurement that
  decides whether it is the right one (§D2/§D5).
- **No load.** Nothing goes in the graph. The `:AppUser` load is doc 09 phase 3, after
  the gate signs.
- **No K2 tier fill.** `TierReconcilers.fid` stays empty. §G3 says filling it as
  originally specified would resolve a job to the account's *owning* application and
  contradict a confirmed app-code mapping — **the tier is harmless today only because
  the table is empty.** That re-scope is K17's ruling, and it is a change to a signed
  gate (`seal-attribution-match-policy`).

When the counts come back, K16 closes and **K17 — the gate session — becomes ready.**
