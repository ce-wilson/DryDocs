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

Two things the census settles for free:

- whether non-application account types ever appear as run-as owners (gate §Q5) — if
  they do, type cannot be used even as an explanatory filter;
- the **disagreement rate** between the directory's application assignment and the
  Control-M-derived attribution where both exist (gate §Q4). That is the cheapest
  available measure of how far either source can be trusted.

## Phases

| Phase | Work | Gate state |
|-------|------|-----------|
| **0** | Census on one application (counts only); answer the six gate open questions with the directory owner | before sign-off |
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
