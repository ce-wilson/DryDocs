# 06a — Control-M source ER review (for the audit-fields gate session)

**Status: FOR SME REVIEW — feeds Phase 0 of
[`06-provenance-source-audit-fields.md`](06-provenance-source-audit-fields.md).**
Everything below is transcribed from the committed extracts
(`drydocs/loaders/sql/controlm_*.sql` — the authoritative CM_ names) and the
cypher loaders. Mechanism only; no data values.

## ER diagram — the psgmgr CM_ objects we extract from

Only projected/filter columns are shown (CM_DEF_VJOB has 100+; we project ~26).
`AUDIT` marks authorship/change columns relevant to the audit-envelope decision.

```mermaid
erDiagram
    CM_DEF_VTAB {
        number  TABLE_ID PK "folder_id"
        varchar SCHED_TABLE "folder name (no PARENT_TABLE col here)"
        varchar DATA_CENTER "Control-M server code"
        varchar USER_DAILY "load filter: IS NOT NULL = actively scheduled"
        varchar TABLE_STATUS
        varchar TABLE_TYPE
        varchar INSTANCE_NAME
        date    LAST_UPDATED "AUDIT source-updated-at (projected)"
        varchar LAST_UPDATED_USER "AUDIT source-updated-by (projected)"
        date    CAPTURE_DATE "replication timestamp, not authorship"
    }

    CM_DEF_VJOB {
        number  JOB_ID PK "with TABLE_ID = job identity"
        number  TABLE_ID PK,FK "folder FK"
        varchar JOB_NAME
        varchar PARENT_TABLE "denormalized folder name on the job row"
        varchar APPLICATION "business app name (reconcile to seal_id)"
        varchar GROUP_NAME
        varchar TASK_TYPE
        varchar CYCLIC "Y/N + CYCLIC_TYPE"
        varchar OWNER "run-as tenant FID (service acct, not a person)"
        varchar AUTHOR "AUDIT authoring SID (projected)"
        varchar CREATION_USER "AUDIT created-by (FILTER-ONLY, not loaded)"
        date    CREATION_DATE "AUDIT created-at (NOT extracted at all)"
        varchar CHANGE_USERID "AUDIT changed-by (FILTER-ONLY, not loaded)"
        date    CHANGE_DATE "AUDIT changed-at (NOT extracted at all)"
        varchar NODE_ID "target host or agent"
        varchar CMD_LINE
        varchar MEMNAME
        varchar DESCRIPTION
        varchar IS_CURRENT_VERSION "load filter: must equal quoted '1'"
        number  VERSION_SERIAL "edit-history counter"
        varchar VERSION_OPCODE
        varchar VERSION_USER "AUDIT who made THIS version (projected)"
        date    VERSION_TIMESTAMP "AUDIT when THIS version (projected)"
        date    CAPTURE_DATE "replication timestamp"
    }

    CM_DEF_LNKI_P_VW {
        number  TABLE_ID PK,FK
        number  JOB_ID PK,FK
        varchar CONDITION PK "condition name (join key to LNKO)"
        varchar ODATE PK "operational date"
        varchar AND_OR "boolean expr glue"
        varchar PARENTHESES "expr grouping"
        number  ORDER_ "expr sequencing"
        number  ISN_
        varchar IS_CURRENT_VERSION "load filter '1'"
        number  VERSION_SERIAL
        date    CAPTURE_DATE
    }

    CM_DEF_LNKO_P_VW {
        number  TABLE_ID PK,FK
        number  JOB_ID PK,FK
        varchar CONDITION PK "condition name"
        varchar ODATE
        varchar SIGN PK "ADD or DELETE"
        number  ISN_
        varchar IS_CURRENT_VERSION "load filter '1'"
        number  VERSION_SERIAL
        date    CAPTURE_DATE
    }

    CM_DEF_SETVAR {
        number  TABLE_ID PK,FK "** object name to verify **"
        number  JOB_ID PK,FK
        varchar NAME PK "variable name (dupes legitimate)"
        varchar VALUE
    }

    CM_DEF_VTAB  ||--o{ CM_DEF_VJOB      : "TABLE_ID (extract JOIN)"
    CM_DEF_VTAB  ||--o{ CM_DEF_LNKI_P_VW : "TABLE_ID (extract JOIN, folder scope only)"
    CM_DEF_VTAB  ||--o{ CM_DEF_LNKO_P_VW : "TABLE_ID (extract JOIN, folder scope only)"
    CM_DEF_VJOB  ||--o{ CM_DEF_LNKI_P_VW : "TABLE_ID+JOB_ID (implied, resolved at graph load)"
    CM_DEF_VJOB  ||--o{ CM_DEF_LNKO_P_VW : "TABLE_ID+JOB_ID (implied, resolved at graph load)"
    CM_DEF_VJOB  ||--o{ CM_DEF_SETVAR    : "TABLE_ID+JOB_ID (extract JOIN)"
    CM_DEF_LNKO_P_VW }o--o{ CM_DEF_LNKI_P_VW : "CONDITION name match = derived dependency"
```

## Source → Neo4j label mapping (as the loaders write today)

| Extract | Source object(s) | Node label(s) MERGEd | Edges written |
|---|---|---|---|
| `controlm_folders` | `CM_DEF_VTAB` | **two nodes per row**: `:ControlMFolder:Collection {folder_id}` **and** `:ControlMServer:Platform {name: DATA_CENTER}` | `(folder)-[:SCHEDULED_ON]->(server)` |
| `controlm_jobs` | `CM_DEF_VJOB ⋈ CM_DEF_VTAB` | `:ControlMJob:Activity {folder_id, job_id}` | `(folder)-[:CONTAINS_JOB]->(job)` |
| `controlm_conditions_in` | `CM_DEF_LNKI_P_VW ⋈ CM_DEF_VTAB` | `:Condition:Entity` | `(job)-[:REQUIRES_IN_CONDITION]->(cond)` |
| `controlm_conditions_out` | `CM_DEF_LNKO_P_VW ⋈ CM_DEF_VTAB` | `:Condition:Entity` | `(job)-[:EMITS_OUT_CONDITION]->(cond)` |
| `controlm_dependencies` (derived) | LNKO ⋈ LNKI on `CONDITION` | none (matches existing jobs) | `(consumer)-[:WAS_INFORMED_BY {via_condition}]->(producer)` |
| `controlm_variables` | `CM_DEF_SETVAR ⋈ VJOB ⋈ VTAB` | **staging only — no graph node yet** (design decision open) | — |

(Every loader also writes `WAS_GENERATED_BY → :JobRun` per touched node — the
supernode pattern doc 06 proposes to retire. Second labels are the ontology
layer: `Collection`/`Activity`/`Entity`/`Platform` are the PROV/DPROD terms.)

## Audit-column inventory (the Phase-0 decision table)

| Object | Created by | Created at | Last changed by | Last changed at | Today |
|---|---|---|---|---|---|
| `CM_DEF_VTAB` (folder) | — (none on folder) | — | `LAST_UPDATED_USER` | `LAST_UPDATED` | **projected**, loaded to staging; not yet an envelope property |
| `CM_DEF_VJOB` (job) | `CREATION_USER` | `CREATION_DATE` | `CHANGE_USERID` | `CHANGE_DATE` | **filter-only / not extracted** — the doc-06 gap |
| `CM_DEF_VJOB` per-version | — | — | `VERSION_USER` | `VERSION_TIMESTAMP` | projected (this version's editor — differs from CHANGE_*?) |
| conditions / variables | — | — | inherit job/folder? | — | only `CAPTURE_DATE` |

Distinct people, not interchangeable: `OWNER` = run-as service FID;
`AUTHOR` = authoring SID; `CREATION_USER` = original creator;
`CHANGE_USERID`/`VERSION_USER` = last/this editor. `CAPTURE_DATE` is
replication time — never authorship.

## Questions for your feedback

- **Q1 — joins.** Conditions extracts join only `VTAB` (folder scope); the job
  link is resolved at graph-load by `(TABLE_ID, JOB_ID)` MATCH. Should they join
  `VJOB` in SQL instead (guaranteeing the job is current-version *in the same
  extract*)? Also: is `SETVAR → VJOB` on `(TABLE_ID, JOB_ID)` correct for
  folder-scope variables (header rows where `JOB_NAME = SCHED_TABLE`)?
- **Q2 — audit columns.** Confirm the envelope mapping per object (the table
  above), especially: does `CHANGE_USERID/CHANGE_DATE` duplicate
  `VERSION_USER/VERSION_TIMESTAMP` on the current version, or do they diverge
  (e.g. bulk migrations)? Exact `CREATION_DATE`/`CHANGE_DATE` column names need
  a data-dictionary probe — they're inferred from the `*_USER` twins.
- **Q3 — labels.** Confirm the two-labels-per-folder-row pattern
  (`ControlMFolder` + `ControlMServer` from `DATA_CENTER`) and whether
  variables should become nodes or stay properties/staging.
