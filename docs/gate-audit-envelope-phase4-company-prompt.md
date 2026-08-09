# Company-side prompt — the `audit-envelope-phase4` gate: status, envelope profile, ratification

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> The producer gate signed 2026-08-04 (M3, 13/13) and rode to you in the a14a8028/
> 5417ef10 ports; the producer has NO RECORD of your side's status. The producer ruled
> FOUR sources; your audit-fields.yaml carries NINE company-only confirmed-source
> entries the producer cannot see — finishing this gate on your side means ruling
> those by the same method.

Venue: company `<org>/DryDocs`, current `main`. Name the venue in every claim (J18).

## Step 1 — STATUS FIRST (answer before touching anything else)

What is this gate's status on YOUR side? Search your `config/gate-log.md` for any
`audit-envelope-phase4` entry (heading-named — a body citation does not count, the J28
rule). Report ONE of:
- **RATIFIED** — quote the entry heading + date, report back, STOP.
- **NEVER RUN** — continue to step 2.
- **PARTIAL** — some envelope rulings exist under other headings: list them, then
  continue; this session consolidates rather than duplicates.

**BEFORE you may report RATIFIED, run the PROVENANCE CHECK. An entry existing is
NOT evidence that you ratified anything.** `config/gate-log.md` is `union-append`
in the port manifest, so producer entries land on your side BY DESIGN — and the
crosswalk yamls and `source-registry.yaml` `confirmed:` flags port too. All three
"corroborating signals" therefore corroborate each other and nothing else.

    git log --oneline -S "audit envelope" -- config/gate-log.md

- The introducing commit is a **PORT commit** (subject starts `port(...)`, or it
  sits on a port branch) -> the entry ARRIVED FROM THE PRODUCER. Report **NEVER
  RUN**, not RATIFIED, and continue to step 2.
- The introducing commit is **company-authored and unrelated to any port** ->
  genuinely RATIFIED. Quote that commit id; it is what gets ledgered.

Quote the command's OUTPUT, not your reading of it.

THIS IS NOT HYPOTHETICAL. On 2026-08-09 the `airflow-crosswalk` check reported
RATIFIED on exactly these three signals; the provenance command returned one
commit, `80d0fc0e`, subject `port(cewilson): apply eeaffa2..f7970e5 (step 31 —
web console O2 + 2026-07-14 gate session) onto branch`. The producer's own F2
sign-off had ported across and was being read back as company confirmation. Note
the tells that were visible without the command: the heading cites a PRODUCER
backlog id (F1/F2/M3/M4/O20), the signer and date match the producer's exactly,
and the producer's `confirmed:` comment string is byte-identical to yours.

The strongest POSITIVE evidence is content the producer has never seen: an entry
that rules company-only rows cannot be a ported artifact.

## Step 2 — profile the internal datasets used (agent; read-only, zero graph writes)

The envelope question is per-source: which REAL extract columns can honestly feed
`source_created_by / source_created_at / source_updated_by / source_updated_at`.
Profile — real values stay Internal, field NAMES and verdicts come back here:
1. **The four producer-ruled sources, on YOUR data:** seal:app-extract (verify the
   two-era lifecycle-date story holds on your live registry rows — current-era
   planned/actual pairs vs sparse legacy), the SEAL contact extract (5 fields, no
   audit columns), pat:product-catalog and pat:people-report (the report extracts
   project zero audit columns; `valid_from`/`valid_to` are role-validity, never
   authorship), repo:software-registry (git history IS the envelope).
2. **Your NINE company-only confirmed-source entries** in `config/audit-fields.yaml`
   (now a per-entry manifest row — they survive ports): per entry, the field census —
   does the real extract carry audit columns, lifecycle dates, or nothing?
3. **The revisit trigger, which only YOU can fire:** the SEAL registry UI exposes a
   per-application AUDIT DOWNLOAD — a true record-audit trail source-side. Profile
   whether that export is obtainable on your network; if one is ingested, IT is the
   envelope source and this gate re-runs against its columns.

## Step 3 — the producer rulings, crafted to finish yours

Ratify per-item, then extend the method to what only you hold. Union-append to YOUR
gate-log; edits that change meaning are registered divergences:
1. **A1 scope** — four sources; the controlm-family stubs (link views, setvar,
   cm_hosts, cm_avg_run, stg_app_fact) stay stubs pending their own census.
2. **B2 seal:app-extract = RULED STUB** on the two-era evidence: registry dates are
   onboarding-lifecycle milestones, NOT record audit; `creation_date` is a lifecycle
   fact with era-dependent capture and cannot honestly feed `source_created_at`.
   Confirm your step-2 profile shows the same story.
3. **B3** — `last_certified_by_sid`/`last_certified_date` EXCLUDED: certification is
   attestation, not modification. `capture_date` stays excluded (the standing rule).
4. **C1/C2** — both PAT sources ruled stub-until-projected (the C17 lesson: the
   backing store has more than the report projects); role-validity never maps onto
   the envelope.
5. **D1** — repo:software-registry ruled PERMANENT stub: git commit author/date IS
   the audit envelope (closes the repo-committed trio).
6. **E1–E3** — no cypher change; entries stay `status: stub` with the gate cited in
   their notes; Phase 4 recorded done for these sources.
7. **THE EXTENSION (yours alone):** rule each of your nine company-only entries by
   the same method — honest mapping, ruled stub with the why recorded, or ruled
   permanent stub. An unruled entry is a gap, not a default.
8. **The revisit trigger** — record the step-2(3) audit-download finding: obtainable
   (schedule its ingestion decision in words) or not (the trigger stands dormant).

## Rules in force

1. Per-item outcomes in your gate-log entry — ratified / edited / refused; edits are
   registered divergences. 2. Real SIDs, dates, and application identifiers stay
   Internal; report-back is mechanism-only (field names, verdicts, counts). 3. Venue
   every claim (J18). 4. One commit per concern. 5. Fix data, never test-edit — the
   envelope drift guards are the contract.

## Close-out

Report back: the step-1 status, the step-2 census (four ruled + nine yours + the
audit-download finding), per-item dispositions — then stop. Ingesting any audit
export is the SME's decision.
