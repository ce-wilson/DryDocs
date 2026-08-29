# 09 — Functional-id (FID) identity and ingest scope

**Status: PLANNED — captured 2026-08-04, gate drafted, not started.** Rulings live in
`config/gate-prompts/fid-identity-and-scope.yaml`; this doc is the plan behind them.
Groom to `backlog.yaml` before building.

## Problem

A **functional id** is the service account a Control-M job runs as, that holds install
entitlements, and that carries an application (SEAL) assignment in the firm's ID
directory. DryDocs already models the account — `:AppUser`, `prov:SoftwareAgent`,
*"Service account / FID that jobs run as"* — and already **depends on the FID →
application join in a signed gate it cannot satisfy**:

> Reconciliation for the FID / APP_NAME / ALIAS tiers is an injected seam
> (`TierReconcilers`) … FID and ALIAS have no producer-side reconciliation source yet,
> so their facts stay unresolved (counted, never guessed) until a table is wired
> company-side.
> — [`drydocs/loaders/seal_attribution.py`](../../drydocs/loaders/seal_attribution.py)

The K2 match policy (signed 2026-07-14) ordered attribution **SEAL > FID > APP_NAME >
ALIAS**. Tier 1 works. **Tier 2 has been an empty dict since the build.** The ID
directory is the table that fills it.

Two properties of that directory make a naive join unsafe, and both were spotted
before any of this was written down:

1. **Ownership is current-state only.** Accounts transfer between owners and
   applications. The record shows where an account sits *today*; the originating
   application may never have been captured. The record's own audit columns say the
   record *changed* and when — never what it changed *from*. This is the same
   two-era capture problem ruled at `audit-envelope-phase4` for SEAL lifecycle dates.
2. **The key we join on is not the key the directory is built on.** Every source we
   hold speaks the account **name** (a job's run-as owner is a name; the `FID_D` /
   `FID_Q` / `FID_P` environment-suffix convention in
   [`variables.py`](../../drydocs_core/orchestration/controlm/variables.py) is a name
   convention). The directory is keyed on a short opaque **id**. One evidence email
   already labeled its column *FID* while populating it with names — a mislabel that
   is harmless while nobody joins on it and silently wrong the moment somebody does.

## Why the scope question is the hard part

One application can carry **roughly two hundred** functional accounts. Almost none of
them run batch: break-glass and privileged-access ids, identity-mapping ids,
verification-environment ids, component-typed ids. So:

- **Pull everything** → multiplies the confidential surface (employee SIDs, mailbox
  addresses, support-team names), the review burden, and the noise, to answer
  questions nobody asked.
- **Pull too little** → run-as owners stay unresolvable, and an under-scoped pull is
  indistinguishable from a defect when someone later asks why coverage is low.

Neither bound can be picked by judgment, because **DryDocs already knows which
accounts it needs** — they are exactly the ones it currently cannot resolve. The scope
is therefore *demand-driven and measured*, not estimated.

## The pull list — three demand sets, all computable today

| # | Demand set | Where it comes from | Why it is needed |
|---|-----------|---------------------|------------------|
| i | **Run-as owners** | distinct job owner (`run_as` / `J.OWNER`) in the Control-M extract | these are the accounts that appear in the graph as batch actors |
| ii | **Unresolved FID facts** | distinct `fact_value` on `STG_APP_FACT` rows with `fact_type='FID'` that the K2 resolver counts unresolved | the literal tier-2 backlog; each one is a fact we hold and cannot use |
| iii | **Evidence rows** | account names in registered adhoc evidence (corpus `adhoc-sme-email`) | the software-version batch that raised all of this |

The union is the pull list. No fourth set without a use case.

## Registration is not attribution (SME evidence, 2026-08-05)

A Control-M run-as account whose name encodes a data platform is **registered** to that
platform's application, while the **folder** whose jobs run as it is **attributed** to a
newer, product-aligned application. Neither source is wrong — they answer different
questions:

| Fact | Subject | Source of record |
|---|---|---|
| **Registration** — who owns the account | the account | ID directory |
| **Attribution** — whose work the folder is | the folder | app-code mapping (K8, confirmed) |

This is the K7 **OWNER-NOT-USER** ruling one grain down — *"a folder belongs to whoever
OWNS it, not whoever USES it — a platform team's all-tenants utility folder belongs to
the platform team"* — applied to an account instead of a folder. The account name
corroborates the *registration* and not the consumption, which is precisely why the
"never infer an application from a name prefix" rule has to hold: here the prefix
confidently yields the wrong application for the job.

**The two facts meet on the job, and nowhere else:**

```
(:ControlMJob)-[:EXECUTED_BY]->(:AppUser)-[:BELONGS_TO_APPLICATION {assignment_kind:'registration'}]->(app A)
(:ControlMFolder)-[:BELONGS_TO_APPLICATION]->(:Port)<-[:HAS_PORT]-(app B)
```

Registration **never propagates transitively onto the jobs**. A traversal that shortcuts
from job to app A is the defect the rule exists to forbid.

### What this costs the K2 FID tier

The signed match policy orders `SEAL > FID > APP_NAME > ALIAS` as evidence of *the job's*
application. The evidence above shows the FID tier carries **registration**, so filling
`TierReconcilers.fid` as originally specified would resolve a job to the account's owning
application and contradict a confirmed app-code mapping. **The tier is harmless today
only because the table is empty.** Proposed re-scope: FID evidence resolves only where no
confirmed folder attribution exists, never overrides one, and a disagreement is reported
rather than written. That is a change to a signed gate — it returns to HITL.

### The disagreement is a finding

*"Jobs attributed to application X running as accounts registered to application Y"* is a
first-class report, not a QA metric. Three readings, distinguished per case and never
globally: (a) different subjects, both correct — platform account serving a consumer app;
(b) **stale directory** — an application decomposition into product-aligned SEALs happened
and re-registration lagged, making this a remediation candidate; (c) wrong folder
attribution. No single source separates them; the graph does, one case at a time. Which is
the strongest argument for loading both and collapsing neither.

## Phase 0 — the census (do this first, it *is* the answer)

Before any bulk pull, run a one-time census **on a single application**:

```
total directory rows for that application      vs      |demand set ∩ that application|
```

broken down by the directory's own type/status columns **and by the registration-vs-
attribution disagreement breakdown above**. That converts *"about two hundred"* into
*"N of ~200, here is what the other rows are, and here is how often registration and
attribution disagree"* — which is the number the scoping decision actually needs.
Output is Internal and is reported as **counts, never a row dump**.

### The numbers (fills in from the company-side run — K16 phase 0-counts)

The method is built and tested; these cells stay empty on the producer side by design,
because this repo holds no directory extract. **An empty cell means "not measured yet,"
never "zero"** — the distinction the whole gate turns on.

| Measurement | Value | Source field on `FidCensus` |
|---|---|---|
| (a) total directory rows for the application | **measured for four applications: 555 · 500 · 209 · 59** (SME id-owner captures 2026-08-19; upper bounds — all environments and subtypes included). Per-census-application value still _pending_ the company run | `directory_rows_total` |
| (b) \|demand set ∩ that application\| | _pending_ | `demand_in_application` |
| — of which, per demand set (i / ii / iii) | _pending_ | `demand_by_source` |
| demanded but absent from the directory | _pending_ | `demand_not_in_directory` |
| (c) remainder (a) − (b), by type / by status | _pending_ | `remainder_by_type` · `remainder_by_status` |
| §Q5 — account types seen as run-as owners | _pending_ | `run_as_owner_types` |
| **Q0** — comparable / agree / disagree / undecidable | _pending_ | `comparable` · `agreements` · `disagreements` · `undecidable` |
| **Q0** — §G5 breakdown of the disagreements | _pending_ | `disagreements_by_reading` |
| spelling near-misses (reported, never folded) | _pending_ | `case_only_mismatches` |

The §G5 breakdown row is the one that **cannot be filled by running the method**. The
census parks every disagreement in `unruled` and waits: §G5 says the three readings are
*"distinguished per case and never globally… a human ruling each."* So that row fills as
the directory owner rules cases, and the count still sitting in `unruled` is itself a
reportable number rather than a gap.

Two things the census settles for free:

- whether non-application account types ever appear as run-as owners (gate §Q5) — if
  they do, type cannot be used even as an explanatory filter;
- the **disagreement rate** between the directory's application assignment and the
  Control-M-derived attribution where both exist (gate §Q4). That is the cheapest
  available measure of how far either source can be trusted.

## Two sources, two grains (SME evidence, 2026-08-19)

The plan above was written against ONE source — the id-owner directory. The SME's
2026-08-19 direction and captures establish there are **two pull surfaces**, different
in grain, key, and blind spots. Venue (J18): every number below was read off SME
captures made on the SME's machine; the captures live outside the tree under the data
root (`fid/screenshots/`), and no extract is in this repo. Shapes and counts only.

**Source A — the HR employee-data custom solution.** FIDs are carried IN the HR
employee record system as functional-type entries:

- The FID **name** (no application id anywhere in the row) sits in the employee
  name field; the **type** column marks the row functional; the **manager** field
  is repurposed to hold the standard id of the employee who **owns or manages the
  account**. LOB, department, and cost-center columns come along for free.
- Measured shape of the profiled extract: 227 rows, 23 columns, every row
  functional-type and active, every employee-id value unique — while the NAME
  column holds only 54 distinct values. **One name is registered 171 separate
  times (75% of the extract), each to a different manager and cost center — and
  the SME identifies it (2026-08-19) as the Control-M PLATFORM user: the account
  jobs run as when they run as Control-M itself, not as any business
  application's FID.** 50 names are 1:1 with their id; 3 more names carry small
  duplicates.

  That identification names a **run_as class this plan had not separated: the
  platform-user account.** A job whose run_as is the platform's own account
  carries no application signal in its run_as at all — resolving it through any
  FID -> application join would attribute the job to the PLATFORM, which is the
  §G registration-vs-attribution counterexample generalized from one account to
  a whole class. And the class is cross-platform, per the SME: **Informatica
  carries several platform accounts under which business-application jobs run.**
  Consequence for the census and the K2 tier alike: run_as must be CLASSIFIED
  (application FID vs platform-user account vs unresolvable) before any join is
  attempted, and the platform-user bucket is resolved by the platform's own
  attribution chain (folder/workflow ownership), never by the directory. K25
  carries the detection; which classes exist and how a platform account is
  recognized (a curated list? the directory's own type/purpose columns?) is a
  K17 §D/§G question.

  **Worked example (SME captures, 2026-08-19 — a live folder from a legacy
  line-of-business estate; captures in the data root, values stay there).** One
  folder, two run_as classes, split BY JOB: the FileWatcher job runs as the
  Control-M platform account, while the folder's default run_as — what the next
  job in the chain uses — is the application's own account. Three consequences:
  (1) **run_as class is JOB-grain.** A folder-level read reports the
  application account and misses the platform-run watcher entirely; any census
  or detector must classify per job. (2) **Job TYPE co-varies with the class.**
  File watching is a platform service, so FileWatcher × platform-account is the
  designed pattern, not an anomaly — the countable anomaly class is a PAYLOAD
  job running as the platform. (3) **The application identity lives in the
  folder's variables, not in the platform-run job's identity.** The watcher's
  watch-path is composed from folder variables, and the folder carries the
  application-specific parametrization (environment paths, an
  interface/source-system code, database users, notification groups) — which is
  also where the estate's Informatica feed shows up: the archive path points
  into an Informatica staging area, connecting this pattern to the
  platform-account class on that platform too.
- Consequences: the grain is **(account id, owner)** — exactly the multi-owner
  scenario `fid_census.py` was built for; the name is the Control-M `run_as` join
  key but is NOT unique; and **this source cannot answer "which application"** —
  no application id exists in the row. It answers *who owns this account*.

**Source B — the id-owner application, searched by application id.** The read
surface over the directory proper:

- Returns, per application: record id, FID, functional **type**, functional
  **purpose** (free text), **name**, description. The name column joins to Source
  A's name and to Control-M `run_as`.
- **Measured by-application totals from four captures:** 555, 500, 209, and 59
  FIDs for four different applications. "About two hundred per application" was
  the estimate; the real spread is roughly an order of magnitude.
- **The SME's caveat, verbatim in substance:** a by-application listing contains
  ALL FIDs for that application for ALL environments — including ids used to
  connect to OTHER applications, app-to-app connection ids, and human shared
  accounts. So (a) in the census is an upper bound by construction, and the §D
  scope ruling (which subtypes count) decides how far above the demand set it
  sits.

**How the two map — proposal for the K17 gate, deciding nothing here:**

| Question | Source | Join |
|---|---|---|
| Who owns/manages this run-as account? | A (HR) | `run_as` name -> A.name -> A.manager (owner's standard id) — at (account id, owner) grain |
| Which application is this FID assigned to? | B (id-owner) | `run_as` name -> B.name -> the search's application id; B is the K2 tier-2 candidate |
| Identity core | B's ids | the FID/record id keys the `:AppUser` node (the doc's standing rule); A's employee-id is a per-row key of the HR carrier, not the identity |
| Census (a) | B | by-application total (over-broad; §D filters rule what counts) |
| Census owner-side counts | A | owner fan-out, name collisions, LOB/cost-center distribution |

Neither source alone is sufficient: A has owners but no applications; B has
applications but its owner columns are role-derived views (see the concepts doc
`knowledge/standards/technology/functional-id-concepts.md` §6 — a listing does not
say whether ownership is individual or catalog-role). The join between them is the
NAME — the key §A of the gate already rules is unsafe as identity. That is not a
contradiction: the name is the *join*, the id is the *identity*, and the census can
measure how lossy the join is (the platform-user account alone is measured at 171-way for
one value).

**What this changes in the plan:** the census gains an owner-side half from Source A
(no new questions — it answers the §Q0 "who owns it" leg the demand-set intersection
needed anyway), and (a) is now measured for four applications instead of estimated
for one. The §G registration-vs-attribution machinery is unchanged. Cross-application
run-as — a job whose run-as account belongs to a DIFFERENT application than the
folder's — is now a first-class census output rather than a footnote: K25 carries it.

## Session SQL — the psgmgr queries that put numbers in front of the gate

Generic samples for the K17 session, written against the columns the committed
extract already projects (`drydocs/loaders/sql/controlm_jobs.sql`:
`psgmgr.CM_DEF_VJOB J` joined to `CM_DEF_VTAB T`, filtered
`J.IS_CURRENT_VERSION = 'Y' AND T.USER_DAILY IS NOT NULL` — current-version jobs
in actively-scheduled folders, the same population every other number in this
plan uses). **Counts only, run where the replica lives; no output row carries a
name that leaves that machine.** Each query names the gate question it feeds.

**S1 — the run-as demand set, weighted (§D, census leg i).** Every distinct
run-as owner with its footprint — the list the directory join starts from:

```sql
SELECT   J.OWNER,
         COUNT(*)                    AS jobs,
         COUNT(DISTINCT J.TABLE_ID)  AS folders,
         COUNT(DISTINCT J.APPLICATION) AS app_codes
FROM     psgmgr.CM_DEF_VJOB J
JOIN     psgmgr.CM_DEF_VTAB T ON J.TABLE_ID = T.TABLE_ID
WHERE    J.IS_CURRENT_VERSION = 'Y' AND T.USER_DAILY IS NOT NULL
GROUP BY J.OWNER
ORDER BY jobs DESC;
```

**S2 — run-as class × job type (§G's job-type dimension; K25's first cut).**
The worked example predicts FileWatcher-type jobs on the platform account beside
payload jobs on application accounts — this shows whether that pattern holds
estate-wide, per owner:

```sql
SELECT   J.OWNER, J.TASK_TYPE, COUNT(*) AS jobs
FROM     psgmgr.CM_DEF_VJOB J
JOIN     psgmgr.CM_DEF_VTAB T ON J.TABLE_ID = T.TABLE_ID
WHERE    J.IS_CURRENT_VERSION = 'Y' AND T.USER_DAILY IS NOT NULL
GROUP BY J.OWNER, J.TASK_TYPE
ORDER BY J.OWNER, jobs DESC;
```

**S3 — the platform-account signature (§D/§G: how is a platform account
RECOGNIZED?).** A platform account's shape is breadth: one owner spanning many
folders and application codes. Owners ranked by spread — the top of this list is
the candidate platform-account set the SME confirms or corrects, which is
cheaper and more honest than any name heuristic:

```sql
SELECT   J.OWNER,
         COUNT(DISTINCT J.APPLICATION)     AS app_codes,
         COUNT(DISTINCT T.SCHED_TABLE)     AS folder_names,
         COUNT(*)                          AS jobs
FROM     psgmgr.CM_DEF_VJOB J
JOIN     psgmgr.CM_DEF_VTAB T ON J.TABLE_ID = T.TABLE_ID
WHERE    J.IS_CURRENT_VERSION = 'Y' AND T.USER_DAILY IS NOT NULL
GROUP BY J.OWNER
HAVING   COUNT(DISTINCT J.APPLICATION) > 1
ORDER BY app_codes DESC, folder_names DESC;
```

**S4 — the cross-application seam, per owner (§Q0/§G5 feed; K25's join).** For
each owner, the distinct folder-derived application codes it runs under — the
Control-M half of the disagreement census. The directory half (the owner's
assigned application) comes from the id-owner export, and the join key is the
NAME, exactly as the two-source section warns:

```sql
SELECT   J.OWNER, J.APPLICATION, COUNT(*) AS jobs
FROM     psgmgr.CM_DEF_VJOB J
JOIN     psgmgr.CM_DEF_VTAB T ON J.TABLE_ID = T.TABLE_ID
WHERE    J.IS_CURRENT_VERSION = 'Y' AND T.USER_DAILY IS NOT NULL
GROUP BY J.OWNER, J.APPLICATION
ORDER BY J.OWNER, jobs DESC;
```

**S5 — owner-shape split (§Q5: do PERSONAL ids ever run jobs?).** The repo's own
extract notes that developer SIDs are lowercase-initial letter-plus-digits; a
service/tenant name is anything else. This is a SHAPE heuristic for triage only
— §Q5's real answer joins the directory's type column — but it flags candidates
for the SME in one pass:

```sql
SELECT   CASE WHEN REGEXP_LIKE(J.OWNER, '^[A-Za-z][0-9]{6}$')
              THEN 'personal-id-shaped' ELSE 'service-shaped' END AS owner_shape,
         COUNT(DISTINCT J.OWNER) AS owners, COUNT(*) AS jobs
FROM     psgmgr.CM_DEF_VJOB J
JOIN     psgmgr.CM_DEF_VTAB T ON J.TABLE_ID = T.TABLE_ID
WHERE    J.IS_CURRENT_VERSION = 'Y' AND T.USER_DAILY IS NOT NULL
GROUP BY CASE WHEN REGEXP_LIKE(J.OWNER, '^[A-Za-z][0-9]{6}$')
              THEN 'personal-id-shaped' ELSE 'service-shaped' END;
```

Two fences. **Definition grain only** — these read what jobs are CONFIGURED to
run as; what a run ACTUALLY executed as is the run-grain question
(`scheduler_executed_by`), needs the history feed, and none of this SQL answers
it. And **OWNER is stored MIXED CASE at rest** (corrected 2026-08-19, K17 session
round 2 — the earlier ALL-UPPER note recorded the normalization plan, not the
storage state; the committed extract's `--run-as` bind upper-cases
unconditionally and is therefore a K16 FIX ITEM, not a feature: it silently
returns zero rows for every lower-stored owner) — any join against the
directory's name column must normalize case on BOTH sides, and the census
reports case-only mismatches rather than folding them.

## Phases

| Phase | Work | Gate state |
|-------|------|-----------|
| **0** | Census on one application (counts only); answer the six gate open questions with the directory owner | before sign-off |
| **0-method** | ✅ **METHOD DELIVERED 2026-08-07 (K16, producer side)** — `drydocs/fid_census.py`, guarded by `tests/unit/test_fid_census.py`. Pure: no file, no database, no writes; every input injected. Run it with [`docs/company-prompts/k16-fid-census-company-prompt.md`](../k16-fid-census-company-prompt.md) | before sign-off |
| **0-K25** | ✅ **DETECTION METHOD DELIVERED 2026-08-26 (K25, producer side)** — `drydocs/run_as_detect.py`, guarded by `tests/unit/test_run_as_detect.py`: the cross-application run_as class detector over the S1-S4 join (per-JOB class platform_user / application_fid / unresolvable; class × job type; the §G5 split parked until ruled). Same discipline as the census row above — pure, injected, counts-only by return type. Run it with [`docs/company-prompts/k25-run-as-detection-company-prompt.md`](../k25-run-as-detection-company-prompt.md); its numbers land in the same company-side event the 0-counts row awaits | evidence for K17 |
| **0-counts** | ⬜ **AWAITING THE COMPANY-SIDE RUN** — the numbers are Internal and cannot be produced in this repo, which holds no directory extract. The table below fills in from that run | before sign-off |
| **1** | Register the system + dataset (`config/source-registry.yaml` v2, `confirmed: false`); register the audit-envelope entry as `stub` | at sign-off |
| **2** | Demand-set extract → dated retained snapshot under `internal/` company-side | after sign-off |
| **3** | `name → fid` crosswalk + `:AppUser` load, keyed on the directory id; miss rate reported as a first-class number | after sign-off |
| **4** | `(:AppUser)-[:BELONGS_TO_APPLICATION {role:'service_account', as_of}]->(:BusinessApplication)` | after sign-off |
| **5** | Feed `TierReconcilers.fid` from the same crosswalk — **the K2 tier-2 unblock**, no second mapping table | after phase 3 |
| **6** | Snapshot diffing → transfer observations | after two snapshots exist |

## Standing rules (the ones that survive the build)

- **`as_of` on every edge**, carrying the extract date, never the load date. Anything
  derived through this join inherits it — including the software-version rollup
  (`software-version-context` §F2). A derived fact that loses its `as_of` cannot have
  it restored later.
- **A later extract that disagrees is a transfer, not drift.** The directory is
  working as designed; the loader reports the move.
- **Transfer detection requires diffing**, so extracts are retained as dated
  snapshots (the depgraph-snapshot precedent, retention rule included). Without
  retained snapshots, transfers are permanently invisible and any `as_of` we stamp is
  decoration.
- **The originating application is UNKNOWN, never inferred.** No back-dating today's
  assignment onto historical jobs, no inferring origin from a name prefix. *"Not
  captured"* is a true answer and is what keeps the graph usable for audit questions.
- **Retired accounts are in scope.** Status is a property, not a pull filter —
  historical jobs reference accounts that are no longer active, and filtering them out
  looks identical to a coverage gap.
- **No fuzzy name matching.** Names in this family differ by an environment suffix or
  a single token, which is exactly where approximate matching is most confident and
  most wrong. Unresolved rows are reported, never guessed.
- **Minimal columns.** *"The export has it"* is not a reason to keep a column. Contact
  columns (support owners, teams, mailboxes) defer to `email-dl-contact-point` rather
  than being absorbed here — one contact model, not two.
- **Refresh is on-demand.** The event that invalidates this data is a transfer, which
  no schedule anticipates.

## Related

- Gate: [`config/gate-prompts/fid-identity-and-scope.yaml`](../../config/gate-prompts/fid-identity-and-scope.yaml)
- Gate: [`config/gate-prompts/software-version-context.yaml`](../../config/gate-prompts/software-version-context.yaml) — the evidence batch that raised this; its §F rollup is blocked here
- Signed, unchanged, cited: `seal-attribution-match-policy` (K2 precedence + `match_method` vocabulary), `business-application-identity` (`app_id` is the neutral key), `seal-app-ref-edge-reshape` §C1 (app node stays a record)
- Doc 06 [`06-provenance-source-audit-fields.md`](06-provenance-source-audit-fields.md) — the envelope this source registers a `stub` against
