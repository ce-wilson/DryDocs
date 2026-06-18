# DryDocs — Multi-Persona Project Review (resumable routine plan)

Autonomous, resumable review of DryDocs from two expert personas, run as a daily
routine **within usage limits**, checkpointing after every unit so it resumes
across days until complete.

## EXECUTION PROTOCOL — read this first, every run

1. Read `docs/reviews/CHECKPOINT.md`. Determine `current_phase`, `current_task`,
   and `next_action`. If `status: COMPLETE`, do nothing and exit.
2. Load the current persona's skill(s) for that phase (see below).
3. Do the **smallest next unit** of work (one numbered task, or part of one).
4. Append findings to that persona's output file.
5. **Update `CHECKPOINT.md`** (phase, task, next_action, ISO timestamp, +1 log line).
6. Repeat 2–5 until the run ends.

**Checkpoint after EVERY unit — never hold unsaved progress.** The latest
`CHECKPOINT.md` must always be a safe resume point; this is how progress is saved
before the usage limit. If usage looks near-limit, finish the current append +
checkpoint, then stop. When all phases are done, write the summary and set
`status: COMPLETE`.

**Variable reset / cadence.** The daily usage limit resets at a time that **varies
day to day**, so the routine fires **hourly** rather than at a fixed clock time —
most wakes may have no budget (cut off near-instantly, no harm) and the first wake
after the reset resumes. As the FIRST action of each wake, append
`- <ISO timestamp> wake` to `CHECKPOINT.md`'s `## Run log`; over days this run-log
**tracks** when the reset actually makes budget available (no hardcoded time).

**Secrets discipline:** keep all output architecture-level. Reference schema object
names only (already in the repo). NO real SIDs, data values, credentials, emails,
or the company GHE org. Save results **per persona** in the files below.

## Phase 1 — Oracle DBA  (skill: `db`)

**Mandate.** `psgmgr` is the **read-only source of truth**. Design a SUPPLEMENTAL
staging layer (extend `DRYDOCS_STG`) created via the DryDocs **Python framework**
(`drydocs/loaders/`, `drydocs/loaders/sql/`, `OracleAdapter`) using **existing
roles** — read via `CM_RO_USER`, write/own under `DRYDOCS_STG`. Tune the extracts
for (1) sampling [done] and (2) incremental ingestion.

Tasks (each a checkpointable unit):
- **1.1 Inventory.** psgmgr base objects the extracts use (`CM_DEF_VTAB`,
  `CM_DEF_VJOB`, `CM_DEF_LNKI_P_VW`, `CM_DEF_LNKO_P_VW`, `CM_DEF_SETVAR` — note the
  unverified flag) and the current `DRYDOCS_STG` DDL (8 STG_ tables + views from
  `controlm_staging_ddl.sql`). Record grain, keys, volumes (~1.1M vars / ~240K
  jobs / 4 DCs), and owning/reading roles.
- **1.2 Gap analysis.** What supplemental staging is needed for (a) developer-SID
  attribution, (b) scope/sample manifests, (c) incremental load control.
- **1.3 Supplemental DDL.** Propose new STG_ objects (e.g. `STG_LOAD_CONTROL`
  watermark table; a developer-SID dimension/view; a sample-manifest view over the
  scenario sampler) — DDL + rationale, owned by `DRYDOCS_STG`, granted to existing
  roles, idempotent/re-runnable. Created via the Python framework, not by hand.
- **1.4 Extract tuning — sampling.** Confirm `controlm_variables_scenarios.sql` +
  the scope binds (`:folder_filter/:run_as/:developer_sid/:row_cap`); note tuning
  (indexes/hints, `FETCH FIRST`, bind usage, the LIKE-ESCAPE gotcha).
- **1.5 Extract tuning — incremental ingestion.** Design the incremental strategy:
  watermark columns (`CAPTURE_DATE` / `VERSION_SERIAL` / `IS_CURRENT_VERSION`),
  change detection, MERGE/UPSERT into staging, a high-water-mark control table,
  restartability, handling of legitimate duplicate `(job, var)` defs, and
  array-size/batch tuning mapped to `OracleAdapter` + the loaders.
- **1.6 Roles & security.** Confirm `CM_RO_USER` read scope suffices for the new
  extracts; `DRYDOCS_STG` privileges for the new objects; least privilege.
- **1.7 Finalize** `docs/reviews/persona-oracle-dba.md`.

## Phase 2 — Neo4j Architect / Ontology  (skills: start `neo4j-getting-started-skill`, then `neo4j-modeling-skill`, `neo4j-cypher-skill`, `neo4j-import-skill`)

**Mandate.** Review the Phase-1 plan from a graph/ontology architecture standpoint,
including **first-time Neo4j setup**.

Tasks:
- **2.1 First-time setup** (`neo4j-getting-started-skill`). Walk the stages
  (prereqs → context → provision → model → load → explore → query → build) mapped
  to DryDocs; what already exists (constraints, ontology supplements, loaders) vs
  what's missing.
- **2.2 Ontology review** (`neo4j-modeling-skill`). The node/edge model: PROV
  `:JobRun`, `:ControlMJob:Activity`, `:JobFolder`, `:Condition`, `:Application`,
  `AreaProduct`, `Role`/`Employee`, developer-SID → Employee attribution. Check
  keys/constraints (the corrected node keys), supernodes, n-ary patterns,
  generic-label anti-patterns.
- **2.3 Staging → graph mapping.** Validate the `DRYDOCS_STG` (incl. Phase-1
  supplemental tables) → Cypher load mapping; ensure the incremental staging
  supports idempotent `MERGE`.
- **2.4 Incremental graph load** (`neo4j-import-skill` / `neo4j-cypher-skill`).
  Constraints-first, `UNWIND $batch` + `MERGE`, `CALL { } IN TRANSACTIONS`,
  change-only loads driven by the watermark staging.
- **2.5 Critique Phase 1.** Reconcile the DBA staging design with graph needs; flag
  mismatches; record adjustments as addenda to `persona-oracle-dba.md`.
- **2.6 Finalize** `docs/reviews/persona-neo4j-architect.md`.

## Phase 3 — Synthesis
- **3.1** Write `docs/reviews/persona-review-summary.md`: cross-persona
  reconciliation, prioritized recommendations, and open decisions for the user.

## Output files (saved per persona)
- `docs/reviews/persona-oracle-dba.md`
- `docs/reviews/persona-neo4j-architect.md`
- `docs/reviews/persona-review-summary.md`
- `docs/reviews/CHECKPOINT.md` — progress / resume state
