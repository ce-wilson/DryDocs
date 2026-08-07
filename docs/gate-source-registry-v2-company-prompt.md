# Company-side prompt — the `source-registry-v2` T19 review + overlay rebind

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> The producer sign-off entry (N7, 2026-07-31) closes with: "Output feeds the
> company T19 review, not a port." **This session IS that review**, plus the one
> build the design reserved for your side: the D2 overlay rebind.

Venue: company `<org>/DryDocs`, current `main` (registry v2 + the N9 migration
ported with the a14a8028 range — verify `config/source-registry.yaml` is
schema v2 with the retired-id refusal list before starting). Name the venue in
every claim (J18).

## What this session is (and is not)

The producer gate `source-registry-v2` was SIGNED OFF 2026-07-31 (N7; 10 rulings,
2 amendments, 1 residual; SME chad.wilson) and BUILT the same day (N9). Under the
two-tier doctrine that is NOT your sign-off. This session: ratify the shape
rulings, run YOUR T19 naming review, and build YOUR overlay. Union-append the
entry to YOUR `config/gate-log.md`; an edit that changes meaning is a
**registered divergence**.

## The producer ruling you are ratifying (summary — the gate-log entry is authority)

- **D1** — two-level identity: SYSTEM rows (connection/locator/classification/
  SDLC) split from DATASET rows (gate/crosswalk/feeds_taxonomy/authority, each
  with its OWN `confirmed`); loaders bind to the DATASET. **Amendment:**
  `seal_id` is a standing PLACEHOLDER on every committed producer system row —
  the REAL value lives on your side (the ccb-twin convention: your rows carry it
  first-class at rest; sanitization applies only at the export crossing).
- **D2** — per-side loader→source_id **overlay**: per-repo config wins over
  class defaults, guarded to resolve to registered dataset ids (extends J21).
  **This is your T19 rebind seam — config, not code.**
- **D3** — URN handle `urn:drydocs:dataset:({carrier-or-origin},{artifact},prod)`,
  lowercase, derived deterministically — a render, never hand-maintained.
- **D4** — reconcile guard: renamed rows carry `replaces:`; retired ids land in
  a refusal list; `SourceRegistry.from_yaml` AND the overlay guard refuse any
  retired id. Same-string-different-meaning (the T19 failure) becomes
  structurally impossible.
- **Q1** — id grammar `{origin}@{db}.{schema}.{table}`, lowercase; the
  qualified segment is the ACTUAL carrier locator. Producer commits
  `[db].[schema]` placeholders; **your rows carry the real coordinates.**
- **Q2** env segment always `prod` · **Q3** derived stores = @ grammar +
  `derived: true`, authority omitted · **Q4** `snow` registered as a SaaS
  system (first dataset `snow:cmdb-ci-classes`, doubles as the cmdb_ci
  crosswalk source) · **Q5** design-docs one home, pipeline-side · **Q6**
  signed gates TRANSFER across renames (identity refactoring, not meaning
  change); the amendment entry maps every old→new id.
- **T19 naming ruling:** the catalog feed's replacement is
  **`pat:product-catalog`** (+ `pat:people-report` split out) — deliberately
  matching NEITHER legacy string, so neither repo's wrong value survives. Both
  legacy strings are in the retired-id refusal list.

## What the producer could NOT decide for you — rule these yourself

1. **The T19 review proper.** Adopt `pat:product-catalog` / `pat:people-report`
   or register a divergence with your reason. Verify BOTH of your legacy id
   strings are refused by YOUR copy of the D4 list (run the refusal, quote it).
2. **Build YOUR D2 overlay** — bind your loaders to registered dataset ids with
   the REAL `{db}.{schema}` coordinates (first-class at rest on your side).
   The overlay guard must pass against your registry; quote the run.
3. **Per-row confirmation sweep, your side.** Q6 transfers YOUR previously
   signed rows only; everything else lands `confirmed: false` until your own
   gates. Do not inherit producer per-row confirms.
4. **The cm_hosts rider.** Your Q1-B pinned divergence
   (`cm_hosts confirmed: false` + the namespace floor) is a REGISTERED standing
   divergence — the registry migration must NOT flip it. Same for the pinned
   `controlm:deftable-xml-export` divergence. Verify both guards survive.
5. **`confirmed`-flag semantics.** Producer `confirmed` = semantic confirmation;
   your side has additionally encoded wiring readiness (the Idea-81 overload).
   State which reading your rows use until the `wired`/`ready` split lands.

## Rules in force

1. Per-item outcomes in your gate-log entry (D1–D4, Q1–Q6, T19) — ratified /
   edited / refused, edits registered as divergences.
2. Fix data/code, never test-edit; producer guards are the contract.
3. Real db/schema/seal values stay Internal on your side; anything reported
   back to the producer is mechanism-only (placeholder spellings).
4. Venue every claim (J18).
5. One commit per concern; quote the suite delta in each report-back message.

## Close-out

- Gate-log entry appended; T19 naming adopted-or-diverged; overlay built and
  guard-verified; pinned divergences confirmed intact.
- Report back: per-item edits/divergences, the T19 outcome, overlay guard
  evidence, and anything the producer should ledger — mechanism-only.
- Then stop.
