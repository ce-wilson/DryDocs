# §INGEST — pulling the CM_ replica into DryDocs

How the company `psgmgr` CM_ objects flow into the DryDocs staging/graph
pipeline. The existing loaders are the source of truth; this file is the map +
the rules for extending them.

## §FILES — what exists

Extract SQL (`drydocs/loaders/sql/`), one file per grain, each a plain projection
with optional scope binds:

| File | Source object | Model row |
|------|---------------|-----------|
| `controlm_folders.sql` | `CM_DEF_VTAB` | `ControlMFolderRow` |
| `controlm_jobs.sql` | `CM_DEF_VJOB` ⨝ `CM_DEF_VTAB` | `ControlMJobRow` |
| `controlm_variables.sql` | `CM_DEF_SETVAR` ⨝ VJOB ⨝ VTAB | `ControlMVariableRow` |
| `controlm_conditions_in.sql` | `CM_DEF_LNKI_P_VW` ⨝ VTAB | in-condition |
| `controlm_conditions_out.sql` | `CM_DEF_LNKO_P_VW` ⨝ VTAB | out-condition |
| `controlm_dependencies_recursive.sql` | derived from in/out | dependency edge |

DDL (`drydocs/loaders/sql/ddl/`): `controlm_staging_ddl.sql` (base staging
tables in `DRYDOCS_STG`), `controlm_staging_supplement_ddl.sql` (load-control +
manifest + `JOB_DEVELOPER_VIEW`). Ad-hoc probes: `sql/adhoc/`.

## §RULES — extending a loader (read before editing)

1. **Project, don't `SELECT *`.** `CM_DEF_VJOB` has 100+ columns; extract only
   what a model row needs. Add columns behind a stated use case, not speculatively.
2. **Always filter current + scheduled.** `J.IS_CURRENT_VERSION = '1'`
   (string literal) and `T.USER_DAILY IS NOT NULL`. Folder-grain files skip the
   version filter (folders aren't versioned).
3. **Keep the four scope binds** consistent across every extract (NULL = no
   filter): `:folder_filter` (`SCHED_TABLE LIKE`), `:run_as` (`OWNER`, the tenant
   FID), `:developer_sid` (`AUTHOR`/`CREATION_USER`/`CHANGE_USERID`), `:row_cap`
   (`ROWNUM`). Folder/condition grains use only `:folder_filter`/`:developer_sid`/
   `:row_cap` (no `OWNER` at that grain).
4. **Read-only.** Extracts touch `psgmgr` via `CM_RO_USER` only. Staging
   DML/DDL targets `DRYDOCS_STG`, never `psgmgr`.
5. **Don't dedupe in SQL.** Duplicate `(job, var-name)` SETVAR rows are legitimate
   (observed `%%FileWatch-TIME_LIMIT` twice on one job). Preserve read order;
   disambiguate downstream.
6. **`developer_sid` semantics.** Control-M SIDs start with a lowercase letter; a
   SID ending in lowercase `p` is the automation **release process**, not a person.
   `AUTHOR` on `CM_DEF_VJOB` is the Control-M team's Functional ID, not an
   individual editor (SME clarification, ADR-06 review).
7. **Audit columns are gated — don't project them ad hoc.**
   `CREATION_USER`/`CREATION_DATE`/`CHANGE_USERID`/`CHANGE_DATE` are deliberately
   filter-only in today's extracts. Promoting them to graph properties is the
   HITL-gated audit-envelope plan
   (`docs/restructure/06-provenance-source-audit-fields.md`, Phase 0/1) — the
   per-source column→envelope mapping needs the SME gate first, because the
   columns' semantics differ (author ≠ creator ≠ last editor).

## §INCREMENTAL — watermark load

The incremental strategy (feature `oracle-ingestion`): read a high-water mark from
`STG_LOAD_CONTROL`, extract only changed rows, apply per-job delete+insert in one
transaction (job grain `(DATA_CENTER, TABLE_ID, JOB_ID)`), commit per batch, then
advance the HWM. Add these predicates to the versioned extracts:

```sql
AND (:hwm_version_serial IS NULL OR VERSION_SERIAL > :hwm_version_serial)
AND (:hwm_capture_date   IS NULL OR CAPTURE_DATE   > :hwm_capture_date)
```

Change-detection depends on two open questions — resolve before trusting deltas:
- **Q2:** is `CAPTURE_DATE` per-row or uniform per snapshot? (picks the watermark
  column)
- **Q0.1:** does `TABLE_ID` collide across `DATA_CENTER`s? (composite-key grain)

## §PROBE — confirm an object exists before coding against it

The replica is a subset; do not assume a poster table was replicated. Cheap
data-dictionary check (does **not** hit the expensive views):

```sql
-- what CM_ objects exist and their type
SELECT object_name, object_type, status
FROM   all_objects
WHERE  owner = 'PSGMGR' AND object_name LIKE 'CM\_%' ESCAPE '\'
ORDER  BY object_name;

-- column-match probe to confirm a suspected object (e.g. the SETVAR view name)
SELECT table_name, COUNT(*) AS col_matches
FROM   all_tab_columns
WHERE  owner = 'PSGMGR'
  AND  column_name IN ('TABLE_ID','JOB_ID','NAME','VALUE')
GROUP  BY table_name
HAVING COUNT(*) >= 3;
```

Record findings as conclusions in the feature plan — **never commit real rows**.

## §CONNECT — how the extract actually runs

Connection is Kerberos external-auth (Thick mode) via `libs/oracle_kerberos/`
(`connect()` / `OracleAdapter(query, bind_params)`). No adapter changes needed for
new extracts. Do **not** touch `drydocs/adapters/oracle_adapter.py` (port-frozen).
For `CM_HIST_VW` and any runtime view, set a bounded `call_timeout` and an indexed
predicate — see the query cookbook's history note.

## §GRAPH — where rows land

Loaders map staging rows to the DryDocs ontology. Folders MERGE **two nodes**
per row: `:ControlMFolder` (renamed from `:JobFolder`, ADR 0003) plus a
`:ControlMServer` from `DATA_CENTER`, linked by `SCHEDULED_ON`. Jobs →
`:ControlMJob` under `CONTAINS_JOB`; in/out conditions → `:Condition` via
`REQUIRES_IN_CONDITION` / `EMITS_OUT_CONDITION`, and the derived
**`:WAS_INFORMED_BY`** edge (job B ⟶ job A on shared condition name; vocab
`m3_was_informed_by` — the older `DEPENDS_ON` name is retired). SETVAR is
**staging-only** today — its graph representation (nodes vs properties) is an
open design decision; don't assume a variable node exists. The extract-level ER
(tables, joins, audit columns, label map) is drawn in
`docs/restructure/06a-controlm-source-er-review.md`. New relationship types go
through `docs/RELATIONSHIP_GUIDE.md` + the HITL gate — never invent an edge type
inside a loader.
