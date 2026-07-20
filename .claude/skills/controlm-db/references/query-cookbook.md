# §QUERY — CM_ replica query cookbook

Vetted read patterns against the `psgmgr` CM_ replica. Provenance **SYNTHESIZED**
(DryDocs query patterns; column names grounded in the committed loaders + crosswalk).
All examples use placeholders — substitute real folder/SID values only at runtime,
never in a committed file. Every definition query filters current version +
scheduled folders.

## §CONV — conventions used below
- `:folder`, `:sid`, `:run_as` = bind placeholders. `LIKE 'ABC_%'` shown literal
  only as a pattern shape.
- Bind literals for `IS_CURRENT_VERSION` are **strings** (`'Y'`), the column is
  VARCHAR2(1). Domain value `'Y'` live-verified 2026-07-15 (D4; was assumed `'1'`).
- Prefer indexed predicates; the `CM_DEF_V*` views are moderate, `CM_HIST_VW` is
  expensive (see §HIST).

## §Q1 — jobs in a folder (with owner + author)
```sql
SELECT J.JOB_ID, J.JOB_NAME, J.APPLICATION, J.TASK_TYPE,
       J.OWNER AS run_as, J.AUTHOR, J.NODE_ID AS target_agent
FROM   psgmgr.CM_DEF_VJOB J
JOIN   psgmgr.CM_DEF_VTAB T ON J.TABLE_ID = T.TABLE_ID
WHERE  J.IS_CURRENT_VERSION = 'Y'
  AND  T.USER_DAILY IS NOT NULL
  AND  T.SCHED_TABLE LIKE :folder
ORDER  BY J.JOB_NAME;
```

## §Q2 — a job's variables (job-scope + inherited folder-scope)
```sql
SELECT CASE WHEN J.JOB_NAME = T.SCHED_TABLE THEN 'FOLDER' ELSE 'JOB' END AS scope,
       V.NAME AS var_name, V.VALUE AS var_value
FROM   psgmgr.CM_DEF_SETVAR_VW V
JOIN   psgmgr.CM_DEF_VJOB   J ON V.TABLE_ID = J.TABLE_ID AND V.JOB_ID = J.JOB_ID
JOIN   psgmgr.CM_DEF_VTAB   T ON J.TABLE_ID = T.TABLE_ID
WHERE  V.IS_CURRENT_VERSION = 'Y'   -- the view stores version history; filter or you get superseded rows
  AND  J.IS_CURRENT_VERSION = 'Y'
  AND  T.USER_DAILY IS NOT NULL
  AND  T.SCHED_TABLE = :folder
ORDER  BY scope DESC, var_name;   -- FOLDER rows first (inherited), then JOB rows
```
Folder-scope rows (`JOB_NAME = SCHED_TABLE`) are the smart-folder header variables
every job in the folder inherits. Duplicate names are legitimate — do not assume
uniqueness.

## §Q3 — what a job consumes / emits (its dependency surface)
```sql
-- IN: conditions this job waits for
SELECT I.CONDITION, I.ODATE, I.AND_OR, I.PARENTHESES, I.ORDER_
FROM   psgmgr.CM_DEF_LNKI_P_VW I
JOIN   psgmgr.CM_DEF_VTAB T ON I.TABLE_ID = T.TABLE_ID
WHERE  I.IS_CURRENT_VERSION = 'Y' AND T.USER_DAILY IS NOT NULL
  AND  I.TABLE_ID = :table_id AND I.JOB_ID = :job_id
ORDER  BY I.ORDER_;

-- OUT: conditions this job posts (SIGN '+' add / '-' remove)
SELECT O.CONDITION, O.ODATE, O.SIGN
FROM   psgmgr.CM_DEF_LNKO_P_VW O
JOIN   psgmgr.CM_DEF_VTAB T ON O.TABLE_ID = T.TABLE_ID
WHERE  O.IS_CURRENT_VERSION = 'Y' AND T.USER_DAILY IS NOT NULL
  AND  O.TABLE_ID = :table_id AND O.JOB_ID = :job_id;
```

## §Q4 — the dependency edge (job B depends on job A)
Job B depends on job A when B consumes a condition A emits. Derived, not stored:
```sql
SELECT ao.TABLE_ID AS a_table, ao.JOB_ID AS a_job,     -- producer
       bi.TABLE_ID AS b_table, bi.JOB_ID AS b_job,     -- consumer
       bi.CONDITION AS on_condition
FROM   psgmgr.CM_DEF_LNKO_P_VW ao                       -- A emits
JOIN   psgmgr.CM_DEF_LNKI_P_VW bi                       -- B consumes
       ON  bi.CONDITION = ao.CONDITION
       AND bi.ODATE     = ao.ODATE                      -- same date-reference semantics
      AND (ao.TABLE_ID <> bi.TABLE_ID OR ao.JOB_ID <> bi.JOB_ID)
WHERE  ao.IS_CURRENT_VERSION = 'Y' AND bi.IS_CURRENT_VERSION = 'Y'
  AND  ao.SIGN = '+';                                   -- only "add" edges are real deps
```
This is the shape `controlm_dependencies_recursive.sql` generalizes (recursive
closure for upstream/downstream chains). `SIGN = '-'` rows are cleanup, not deps.

## §Q5 — who authored vs who ran
- **Authored / changed** (definition-time): `CM_DEF_VJOB.AUTHOR`,
  `CREATION_USER`, `CHANGE_USERID`. Use `:developer_sid IN (...)`.
- **Ran** (operational): NOT in the definition views — that identity lives in the
  action-audit object `CM_AUD_ACTS` (future extract). Do not infer "who ran it"
  from `AUTHOR`.
- **Ownership/escalation routing:** `CM_ESCALATION_DB` (join on `EJOBNAME`,
  filter `ECOMPONENT = 'SEAL'`, gate on the `EAPPLICATION` column) maps a job to
  its SEAL app / support team.

## §Q6 — scope by tenant (run-as FID) or developer
```sql
-- everything a service FID owns
... WHERE J.IS_CURRENT_VERSION='Y' AND T.USER_DAILY IS NOT NULL
    AND J.OWNER = :run_as;
-- everything a developer authored or last changed
... AND :sid IN (J.AUTHOR, J.CREATION_USER, J.CHANGE_USERID);
```

## §HIST — runtime history (handle with care)
`CM_HIST_VW` (and any `CM_*` runtime view) **materializes before applying
`ROWNUM`** — an unbounded probe, even `ROWNUM <= 1`, times out (ORA-03156 /
DPY-4024). This is a workload problem, not connectivity.
- Always bound with an **indexed** predicate (e.g. `JOB_MEM_NAME`, a bounded
  `ORDER_DATE`/`ODATE` range) and raise `call_timeout` for the session.
- To smoke-test *access* cheaply, query the data dictionary instead:
  `SELECT owner, object_type, status FROM all_objects
   WHERE owner='PSGMGR' AND object_name='CM_HIST_VW';`
- Map history back to definitions via `JOBNO`/job name + `ODATE`; expect the
  runtime column names to follow the `CMR_AJF` shape (`ORDERNO`, `STATUS`,
  `STARTRUN`/`ENDRUN`, `OSCOMPSTAT`) — confirm against the actual view DDL.

## §PITFALLS
- Forgetting `IS_CURRENT_VERSION = 'Y'` → every historical edit returned.
- Filtering the version column as a **number** → no rows (it's VARCHAR2(1)).
- Trusting `CM_DEF_VJOB.PARENT_TABLE` for the folder name → use
  `CM_DEF_VTAB.SCHED_TABLE` (join on `TABLE_ID`).
- Assuming `TABLE_ID` is globally unique → it may collide across `DATA_CENTER`;
  key on `(DATA_CENTER, TABLE_ID, JOB_ID)` until Q0.1 is settled.
- Querying a poster table that was never replicated (On-Do, resources, security,
  agents) → confirm with the §PROBE dictionary query in `ingest.md` first.
- Running a bare `SELECT *` on `CM_HIST_VW` → timeout; bound it.
