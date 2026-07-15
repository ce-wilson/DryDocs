---
name: controlm-db
description: "Ingest and query the BMC Control-M database tables (the CM_ replica in the psgmgr Oracle schema). Use when: (1) writing or reviewing SQL against the company's psgmgr CM_DEF_V* / CM_HIST / CM_AUD / CM_ESCALATION objects (job/folder/variable/condition/audit extracts), (2) mapping a Control-M concept (job, folder, On-Do, prerequisite condition, quantitative/control resource, SETVAR) to the physical table+column that carries it, (3) adding or changing a controlm_*.sql loader or its staging DDL, or (4) answering 'which table holds X' from the BMC physical data model. Grounded in the BMC 6.4.01 physical-model poster (entity/relationship ground truth), the vendor docs in external/orchestration/bmc-controlm/, and the company CM_ SQL loaders. For the runbook-automation workflow built on these tables, use the controlm-runbook-automation skill instead. Mechanism-only: never emit real SIDs, server names, folder names, or data values."
---

# Control-M DB — ingest & query the CM_ tables

The company replicates a **subset** of the BMC Control-M/Server database from the
vendor's runtime schema (`dtsremgr`) into the Oracle **`psgmgr`** schema under a
**`CM_`** naming convention, read-only via **`CM_RO_USER`**. This skill is the
routing brain for working against that copy: it maps every Control-M concept to
the physical table/column that carries it, and gives the vetted ingest + query
patterns.

**Two things this skill does. Pick one:**

1. **INGEST** — pull CM_ objects into the DryDocs staging/graph pipeline
   (`controlm_*.sql` loaders → staging DDL → incremental watermark). Read
   [`references/ingest.md`](references/ingest.md).
2. **QUERY** — answer a support/lineage question directly against the CM_ tables
   (what runs, what it depends on, who authored it, what a job's variables are).
   Read [`references/query-cookbook.md`](references/query-cookbook.md).

Either way, **first** resolve the concept → table using the schema map.

> The runbook-automation workflow (generate runbooks from the graph, fix
> metadata in failure-driven batches) is deliberately **not** part of this
> skill — it is company-specific and lives in `controlm-runbook-automation`,
> which builds on this one.

---

## The one thing to get right: three schemas, not one

The poster and the company copy do **not** use the same names. Keep these layers
distinct or every query is wrong:

| Layer | Owner | Example object | What it is |
|-------|-------|----------------|------------|
| **Vendor physical model** | BMC (poster) | `CMS_JOBDEF`, `CMR_AJF` | the 6.4.01 physical data model — **entity/relationship ground truth** |
| **Control-M runtime DB** | `dtsremgr` | `DEF_VJOB`, `DEF_VTAB`, `DEF_SETVAR`, `DEF_LNKI_P` | the live Control-M schema (9.0.21.300) the company replicates FROM |
| **Company replica** | `psgmgr` | `CM_DEF_VJOB`, `CM_DEF_VTAB`, `CM_DEF_SETVAR_VW`, `CM_DEF_LNKI_P_VW`, `CM_HIST_VW`, `CM_AUD_ACTS`, `CM_ESCALATION_DB` | the read-only `CM_`-prefixed copy we actually query |

**Version caveat (load-bearing):** the poster is **6.4.01**; the company runs
**9.0.21.300**. Use the poster for *entity relationships and column semantics*
(job → On-Do → action; job → prerequisite condition; job → SETVAR; folder → jobs)
— **not** for exact object/column names in `psgmgr`. The authoritative names for
the replica come from the committed loaders in `drydocs/loaders/sql/controlm_*.sql`
and the crosswalk. Two structural differences the newer version introduces:

- **Combined → split conditions.** 6.4.01 keeps in/out conditions in one
  `CMS_CON_J` (discriminated by `ROWTYPE`). 9.0.x splits them into
  **`DEF_LNKI_P`** (in / consumed) and **`DEF_LNKO_P`** (out / emitted) →
  `CM_DEF_LNKI_P_VW` / `CM_DEF_LNKO_P_VW`.
- **Versioned view layer.** The `CM_DEF_V*` views add `IS_CURRENT_VERSION`,
  `VERSION_SERIAL`, `VERSION_OPCODE`, `VERSION_TIMESTAMP`, `VERSION_USER`,
  `CAPTURE_DATE` — columns absent from the flat 6.4.01 tables. **Always filter
  `IS_CURRENT_VERSION = 'Y'`** (VARCHAR2(1) — quote the literal) or you read
  every historical edit.

Full mapping + column crosswalk: [`references/schema-crosswalk.md`](references/schema-crosswalk.md).
The vendor entity model (groups, PKs, key columns, relationships): [`references/er-model.md`](references/er-model.md).

---

## Concept → table quick index

| You want… | Vendor entity | Company object | Grain (key) |
|-----------|---------------|----------------|-------------|
| A job definition | `CMS_JOBDEF` | `CM_DEF_VJOB` | `(TABLE_ID, JOB_ID)` current version |
| A folder / schedule table | `CMS_SCHEDT` | `CM_DEF_VTAB` | `TABLE_ID`; name = `SCHED_TABLE` |
| A job's variables (SETVAR) | `CMS_SETVAR` | `CM_DEF_SETVAR_VW` | `(TABLE_ID, JOB_ID, NAME)` |
| Conditions a job **consumes** (in) | `CMS_CON_J` (ROWTYPE=in) | `CM_DEF_LNKI_P_VW` | `(TABLE_ID, JOB_ID, CONDITION, ODATE)` |
| Conditions a job **emits** (out) | `CMS_CON_J` (ROWTYPE=out) | `CM_DEF_LNKO_P_VW` | `(TABLE_ID, JOB_ID, CONDITION, SIGN)` |
| On-Do action blocks | `CMS_ONSTMT` + `CMS_DO` | (not yet replicated) | `(JOB_ID, IF_NO, DO_NO)` |
| Quantitative / control resources | `CMS_QR_J` / `CMS_CTL_J` | (not yet replicated) | `(resource, JOB_ID)` |
| Which hosts a node/host group balances across (job `NODE_ID` target) | `CMS_NODGRP` | `CM_HOSTS` | `(DATA_CENTER, GRPNAME, NODEID)` — gate `controlm-hosts-topology` pending |
| Agent/node identity + versions | `CMS_NODID` / `CMR_NODES` | (not replicated) | `NODEID` |
| Runtime / history of runs | `CMR_AJF`, `CMR_RUNINF`, `CMR_IOALOG` | `CM_HIST_VW` (expensive) | `ORDERNO` |
| Who **ran** an action (audit) | — | `CM_AUD_ACTS` | action-time identity |
| Escalation / SCIM routing | — | `CM_ESCALATION_DB` | `EJOBNAME` join, `ECOMPONENT='SEAL'` |

Blank "company object" = present in the vendor model but **not in the current
psgmgr replica** — do not assume it exists; confirm with the data-dictionary
probe in `ingest.md` before writing a loader against it.

---

## Guardrails (publish boundary + Control-M safety)

- **Mechanism, not instance.** Object/column names (`psgmgr`, `CM_DEF_VJOB`,
  `CM_RO_USER`, `SCHED_TABLE`) are established public vocabulary — fine to use.
  **Never** emit a real SID, server/host name, real folder name, tenant FID, or
  any data *value* in a committed file. Those live only in gitignored
  `internal-local/` or `drydocs/data/` (see `PUBLISH-BOUNDARY.md`).
- **Read-only.** The replica is a read copy via `CM_RO_USER`; this skill never
  issues DML/DDL against `psgmgr`. Staging DDL targets the DryDocs staging schema
  (`DRYDOCS_STG`), never `psgmgr`.
- **Current version only.** Every definition query filters
  `IS_CURRENT_VERSION = 'Y'` and actively-scheduled folders `USER_DAILY IS NOT NULL`.
- **`CM_HIST_VW` is expensive.** It materializes before applying `ROWNUM`; even
  `ROWNUM <= 1` probes time out (ORA-03156 / DPY-4024). Bound history queries with
  indexed predicates (e.g. `JOB_MEM_NAME`, a date range) and raise `call_timeout`
  — a slow history query is a workload problem, not a connectivity one.
- **Provenance tiers** (per the BMC `SOURCE-MANIFEST.md`): poster column/PK facts
  are **GROUNDED** to BMC; the vendor→company crosswalk and all query recipes are
  **SYNTHESIZED** (DryDocs inference). Do not load synthesized shapes as vendor
  ground truth.
- **Connection.** Queries run through the Kerberos login in
  `libs/oracle_kerberos/` (Thick mode, external auth). See that module's README;
  do not hand-build a DSN.

---

## Provenance

- **BMC 6.4.01 physical-model poster** —
  `external/orchestration/bmc-controlm/BMC_ControlM_SVR_v6.4.01_DB_Poster.pdf`
  (© BMC; internal-operation layouts, provided as-is, not a sanctioned API).
  **Local reference only — gitignored** (copyrighted vendor binary; this repo is
  sometimes published). Its factual schema is transcribed in
  [`references/er-model.md`](references/er-model.md), so the skill is complete
  without the PDF present.
- **Vendor concept docs** — `external/orchestration/bmc-controlm/controlm-*.md`
  (see that folder's `SOURCE-MANIFEST.md` for per-file trust tiers; the JSON
  `controlm-api-*.md` files are conceptual-only for our 9.0.21.300 XML env).
- **Company replica shape** — `drydocs/loaders/sql/controlm_*.sql` +
  `drydocs/loaders/sql/ddl/controlm_staging*_ddl.sql` (the authoritative CM_ names).
