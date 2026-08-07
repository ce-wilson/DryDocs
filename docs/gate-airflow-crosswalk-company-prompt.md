# Company-side prompt — the `airflow-crosswalk` gate: status, estate profile, ratification

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> The producer gate signed 2026-07-14 (F2, 17 confirmations, ACCEPTED IN FULL); the
> producer has NO RECORD of your side's status. Sibling of the autosys-crosswalk
> session — same three steps, different estate and different open questions.

Venue: company `<org>/DryDocs`, current `main`. Name the venue in every claim (J18).

## Step 1 — STATUS FIRST (answer before touching anything else)

What is this gate's status on YOUR side? Search your `config/gate-log.md` for any
`airflow-crosswalk` entry, check `config/crosswalks/airflow-to-bmc.yaml` row statuses
and the source-registry `airflow-mwaa` row. Report ONE of:
- **RATIFIED** — quote the entry heading + date, report back, STOP.
- **DIVERGED** — name the differing rows, stop at a divergence report.
- **NEVER RUN** — continue to step 2.
- **NOT APPLICABLE** — no Airflow/MWAA estate exists or is planned: record the dated
  disposition in your gate-log, report back, STOP.

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
