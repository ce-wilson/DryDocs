# Company-side prompt — the `airflow-crosswalk` gate: status, estate profile, ratification

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> The producer gate signed 2026-07-14 (F2, 17 confirmations, ACCEPTED IN FULL); the
> producer has NO RECORD of your side's status. Sibling of the autosys-crosswalk
> session — same three steps, different estate and different open questions.

> **DEFERRED 2026-08-09 (SME) — DO NOT RUN THIS SESSION ON SIGHT.** Neither
> orchestrator is ingested on either side, so ratifying today buys nothing
> operationally and spends a company session that P8, T22/DD6 and the T23 graph
> legs have better claim to. **Run this when, and only when, the first Airflow/MWAA
> source is about to be registered for ingestion — BEFORE the registration, not
> at the ingestion review.**
> WHY THE ORDER MATTERS, and it is the whole reason this is a hold rather than a
> shrug: `drydocs_core/orchestration/crosswalk.py` gates `resolve()` on
> `require_confirmed=True`, and `config/crosswalks/airflow-to-bmc.yaml` carries
> `status: confirmed` — which PORTED to you. So the only runtime gate protecting
> these mappings is ALREADY SATISFIED on your side by an artifact you never
> ratified. Nothing calls `resolve()` today (verified producer-side: no caller
> outside the module and its own tests), so the open gate leads nowhere. The
> first ingestion wires a caller and `resolve()` succeeds SILENTLY — there is no
> second checkpoint where the missing ratification would surface.
> **AND DO NOT ANSWER `NOT APPLICABLE`.** That branch below is for an
> orchestrator you will never ingest. These crosswalks are a deliberate
> forward-looking placeholder (`external/orchestration/airflow/README.md` says
> exactly that), so NOT APPLICABLE would foreclose it as a decision when the truth
> is a hold. If you must record something today, record **DEFERRED** with this
> trigger — see the added branch in step 1.

Venue: company `<org>/DryDocs`, current `main`. Name the venue in every claim (J18).

## Step 1 — STATUS FIRST (answer before touching anything else)

What is this gate's status on YOUR side? Search your `config/gate-log.md` for any
`airflow-crosswalk` entry — **heading-named only; a body citation does not count
(J28)** — check `config/crosswalks/airflow-to-bmc.yaml` row statuses
and the source-registry `airflow-mwaa` row. Report ONE of:
- **RATIFIED** — quote the entry heading + date, report back, STOP.
- **DIVERGED** — name the differing rows, stop at a divergence report.
- **NEVER RUN** — continue to step 2.
- **DEFERRED** — the SME hold above is still in force and no Airflow/MWAA source is
  being registered: report DEFERRED, quote the trigger, and STOP. This is NOT
  the same answer as NOT APPLICABLE, and the difference is load-bearing —
  DEFERRED keeps the ratification owed, NOT APPLICABLE retires it.
- **NOT APPLICABLE** — no Airflow/MWAA estate exists or is planned: record the dated
  disposition in your gate-log, report back, STOP.

**BEFORE you may report RATIFIED, run the PROVENANCE CHECK. An entry existing is
NOT evidence that you ratified anything.** `config/gate-log.md` is `union-append`
in the port manifest, so producer entries land on your side BY DESIGN — and the
crosswalk yamls and `source-registry.yaml` `confirmed:` flags port too. All three
"corroborating signals" therefore corroborate each other and nothing else.

    git log --oneline -S "airflow-crosswalk" -- config/gate-log.md

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

**READ THE COMMIT SUBJECT — your two kinds of gate-log commit are visibly
different, and that is the fastest discriminator.** Evidenced from your own
history:

    port(cewilson): apply eeaffa2..f7970e5 ...        <- PORTED. not your ratification.
    gate(ratify): seal-app-ref-edge-reshape company ratification ...   <- YOURS.
    platforms: SME gate CONFIRMED (Wilson, ...) ...                    <- YOURS.

Use a GATE ID as the search string, never a prose word. `-S "AutoSys"` returned
six commits because the word appears throughout the log; `-S "autosys-crosswalk"`
matches the entry that names the gate file and nothing else.

The strongest POSITIVE evidence is content the producer has never seen: an entry
that rules company-only rows cannot be a ported artifact.

## Step 2 — profile the internal datasets used (agent; read-only, zero graph writes)

Only your side can see the estate. Real values stay Internal; counts and shapes come
back here. NOTE the DPL context your side already traced (2026-07-21): the AWS Glue
leg sits BEHIND the launcher spine — this profile is about ORCHESTRATOR-level
Airflow/MWAA use, not the Glue jobs the DPL pipelines wrap:
1. **Estate census:** MWAA environments / self-managed Airflow instances in scope —
   DAG repo availability, DAG counts, schedule coverage.
2. **Row-6 evidence (per-operator INVOKES):** operator census across the DAG repos —
   which operators appear, with counts. The producer deferred the per-operator
   INVOKES crosswalk table to loader design; the census is what that table is built
   from.
3. **Row-5 evidence (dataset conditions):** Airflow Datasets / dataset-triggered
   scheduling usage — does the estate use them enough that the Condition property set
   needs enriching?
4. **Row-8c evidence (Connections):** Connection definitions census (target-system
   kinds, counts) — the deferred landing question is DataAsset reference vs job
   properties, and the answer depends on what Connections actually name.

## Step 3 — the producer rulings, crafted to finish yours

Ratify per-item against the step-2 profile; union-append to YOUR gate-log; edits that
change meaning are registered divergences:
1. **§A registration:** SoftwareProduct `airflow` MADE_BY `apache` (ADR 0004); **MWAA
   is NOT a separate product** — stock Airflow object model, AWS-managed deployment.
   Crosswalk-only scope, public concepts, bmc-baseline stays authority 1.
2. **§B the 14 rows:** rows 2/3 exact; 1/4/5/6/8a/8c/9/10 approximate with accepted
   caveats. Row 8a cardinality is 1-to-many: queue → `ControlMHostGroup
   -[:CONTAINS_HOST]-> ExecutionHost` (the controlm-hosts-topology pattern);
   hard-pinned worker = the 1-hop `RUNS_ON {role: agent_host}` case; NEVER queue →
   single ExecutionHost. If your cm_hosts divergence (Q1-B) touches this pattern,
   say how it lands here.
3. **The three deferred loader-design questions** — rule them FROM your profile or
   leave them open with the missing evidence named: row 5 (Condition property set for
   datasets), row 6 (per-operator INVOKES table), row 8c (Connection landing).
4. **§C no-equivalents stay unmapped:** row 7 (trigger-rule vocabulary), row 11
   (XCom — never modeled), row 12 (dynamic task mapping — the flagged drift risk),
   row 8b (Pool → Quantitative Resource, never folded into ExecutionHost). Nothing
   silently approximated.
5. **Loader discipline restated:** `confirmed: true` is crosswalk authority ONLY — a
   loader must be implemented and separately gated before any load.

## Rules in force

1. Per-item outcomes in your gate-log entry — ratified / edited / refused; edits are
   registered divergences. 2. Real environment names, repo names, connection strings
   stay Internal; report-back is mechanism-only. 3. Venue every claim (J18). 4. One
   commit per concern. 5. A ratified crosswalk is not a performed load.

## Close-out

Report back: the step-1 status, the step-2 profile counts, per-item dispositions, and
anything the producer should ledger — then stop. Loader builds and ingestion
scheduling are the SME's decisions.
