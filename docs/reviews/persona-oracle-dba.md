# Persona Review — Oracle DBA (Phase 1)

Reviewer persona: **Oracle DBA** (via the `db` skill). Mandate: treat `psgmgr` as
the read-only source of truth; design a **supplemental** staging layer extending
`DRYDOCS_STG`, built through the DryDocs Python framework using **existing roles**;
tune the extracts for **sampling** (done) and **incremental ingestion**.

Architecture-level only — object/column names (already in the repo), no real data,
SIDs, or credentials.

---

## 1.1 Inventory (what exists today)

**psgmgr base (read-only source):**
- `CM_DEF_VTAB` — folders ("tables"), ~18.8K. Not versioned; `USER_DAILY IS NOT NULL`
  = active. Has `LAST_UPDATED`, `LAST_UPDATED_USER`, `CAPTURE_DATE`.
- `CM_DEF_VJOB` — jobs, ~240.6K, ~100 cols, version history (`VERSION_SERIAL`,
  `IS_CURRENT_VERSION`). Identity/owner cols: `OWNER`, `AUTHOR`, `VERSION_USER`,
  and (per the scope-bind work) `CREATION_USER`, `CHANGE_USERID`. `CAPTURE_DATE`.
- `CM_DEF_LNKI_P_VW` / `CM_DEF_LNKO_P_VW` — conditions (versioned).
- `CM_DEF_SETVAR` — variables, ~1.1M. **Name still unverified** (`** VERIFY **`).

**DRYDOCS_STG (owned, write-back):** base read views `JOB_DETAILED_VIEW` /
`JOB_VARIABLE_VIEW`; run control `STG_RUN`; 8 staging tables (`STG_VARIABLE`,
`STG_INVOCATION`, `STG_FILE_REF`, `STG_FILE_OP`, `STG_NOTIFICATION`,
`STG_APP_FACT`, `STG_PARSE_QUALITY`, `STG_UNPARSED_COMMAND`) with surrogate
IDENTITY PKs, all keyed `(run_id, data_center, folder_id, job_id)`; coverage view
`STG_COVERAGE_SUMMARY`. ~<3M rows / <2 GB; no partitioning needed.

**Current load pattern: FULL REFRESH.** The normalizer DELETEs by `RUN_ID` (or
truncates) and bulk-inserts ~1.1M variable rows **every run**. `STG_RUN` records
each execution. Composite key is defensively `(DATA_CENTER, TABLE_ID)` —
pre-flight 0.1 checks whether `TABLE_ID` collides across DCs.

**Roles:** `CM_RO_USER` reads psgmgr; `DRYDOCS_STG` owns staging; a Python
normalizer account gets `SELECT` on the views + `SELECT/INSERT/DELETE` on staging;
analysts read-only.

---

## 1.2 Gap analysis

| Need | Gap today |
|---|---|
| **Developer-SID attribution** | `JOB_DETAILED_VIEW` exposes `OWNER`/`AUTHOR`/`VERSION_USER` but **not** `CREATION_USER`/`CHANGE_USERID`. No dimension linking SID→employee. The SID convention (lowercase initial; trailing lowercase `p` = automation release, not a person) is not encoded anywhere. |
| **Scope / sample manifests** | The scenario sampler (`controlm_variables_scenarios.sql`) and scope binds exist, but nothing **persists what a sample covered** — which scope binds, which scenarios, how many rows. No sample provenance. |
| **Incremental ingestion** | Only full refresh exists. No watermark, no change detection, no incremental MERGE. Re-extracts the whole ~1.1M population every run — expensive and unnecessary once a baseline exists. `STG_RUN` records runs but no per-source high-water mark. |

---

## 1.3 Supplemental DDL design (built via the Python framework, idempotent)

All new objects owned by `DRYDOCS_STG`, created via a new framework DDL file
(e.g. `drydocs/loaders/sql/ddl/controlm_staging_supplement_ddl.sql`) run by the
loader. Idempotency per the `db` skill: `CREATE OR REPLACE` for views;
existence-checked `CREATE TABLE/INDEX` (catch ORA-00955 / check `ALL_TABLES`);
`GRANT` is idempotent (REVOKE needs a guard).

**A. `STG_LOAD_CONTROL` — incremental watermark (the keystone).**
```
(source_object   VARCHAR2,   -- 'CM_DEF_VJOB' | 'CM_DEF_VTAB' | 'CM_DEF_SETVAR' | ...
 data_center     VARCHAR2,
 load_mode       VARCHAR2,   -- FULL | INCREMENTAL
 hwm_capture_date  TIMESTAMP,  -- last CAPTURE_DATE applied
 hwm_version_serial NUMBER,    -- last VERSION_SERIAL applied (versioned sources)
 last_run_id     VARCHAR2 REFERENCES stg_run,
 last_status     VARCHAR2,   -- SUCCEEDED | FAILED | RUNNING
 rows_applied    NUMBER,
 updated_at      TIMESTAMP,
 PRIMARY KEY (source_object, data_center))
```
Advanced **only** after a committed batch — the restart point.

**B. `STG_DEV_SID` — developer-SID dimension + the convention, encoded.**
```
(sid            VARCHAR2 PRIMARY KEY,
 is_automation  CHAR(1),   -- 'Y' when REGEXP_LIKE(sid,'p$') AND lowercase-initial
 first_seen_run VARCHAR2, last_seen_run VARCHAR2,
 job_count      NUMBER)
```
Populated from `DISTINCT` of `AUTHOR/CREATION_USER/CHANGE_USERID` (jobs) +
`LAST_UPDATED_USER` (folders). `is_automation` derives the trailing-`p` rule so the
graph can separate human developers from the release process. (SIDs are mildly
sensitive identity data — keep in `DRYDOCS_STG`, analyst read-only, never in the
public producer repo.)

**C. `STG_SAMPLE_MANIFEST` — sample provenance.**
```
(run_id VARCHAR2 REFERENCES stg_run, scope_folder VARCHAR2, scope_run_as VARCHAR2,
 scope_developer_sid VARCHAR2, scope_row_cap NUMBER,
 scenario VARCHAR2, rows_pulled NUMBER, captured_at TIMESTAMP)
```
One row per (sample run × scenario) so every sample records the scope binds and
scenario coverage that produced it.

**D. Extend the base views (`CREATE OR REPLACE`, idempotent).**
Add `CREATION_USER`, `CHANGE_USERID` to `JOB_DETAILED_VIEW`; add a
`JOB_DEVELOPER_VIEW` that unions the four SID-bearing columns to one
`(data_center, folder_id, job_id, role, sid, is_automation)` shape for the
dev-SID scope + the dimension load.

---

## 1.4 Extract tuning — sampling (already in place; confirmed)

The scenario sampler + scope binds are sound. DBA notes:
- Bind variables (`:folder_filter` etc.) keep the cursor shareable — no literal
  churn in the shared pool. Good.
- `FETCH FIRST 1 ROW ONLY` per parenthesised scenario branch is correct; the
  `ROWNUM` cap is an **unordered** sample (fine for coverage, not pagination).
- The `LIKE '\%\%…' ESCAPE '\'` idiom for literal `%%` is correct and necessary.
- **Add:** write a `STG_SAMPLE_MANIFEST` row per sampler run so coverage is
  provable and reproducible. Sampling reads through `JOB_VARIABLE_VIEW` (or direct)
  and is lightweight — no tuning concern at sample volumes.

---

## 1.5 Extract tuning — incremental ingestion (the main design)

Move from full-refresh to a two-mode model; `STG_LOAD_CONTROL.load_mode` records
which ran.

**Change detection.** `CAPTURE_DATE` is a snapshot stamp (likely uniform per
extract) so it is a coarse high-water mark, not a per-row change signal. Use:
- **Jobs / conditions (versioned):** `VERSION_SERIAL` — a higher serial than the
  stored HWM = changed. Primary signal.
- **Folders / variables (not versioned):** a content **hash** per grain
  (`STANDARD_HASH` of the projected columns) compared to a stored hash, or fall
  back to `CAPTURE_DATE > hwm`.

**Incremental extract** = base view filtered `IS_CURRENT_VERSION='1'` **AND**
(`VERSION_SERIAL > :hwm_version_serial` OR `CAPTURE_DATE > :hwm_capture_date`),
scoped by the same `:folder_filter/:run_as/:developer_sid` binds.

**Idempotent apply — replace per JOB, not per row.** The skill warns delete+insert
isn't idempotent and MERGE needs a natural key — but staging has IDENTITY PKs and
legitimate duplicate `(job, var)` rows, so there is no row-level natural key. The
safe unit is the **job**: for each changed `(data_center, folder_id, job_id)`,
`DELETE` its staging rows and re-insert the freshly derived set **in one
transaction**. That is idempotent at job grain (a job's rows are always replaced as
a whole, dupes preserved) and restart-safe.

**Restartability.** Batch changed jobs in `arraysize` chunks (the `OracleAdapter`
already streams at 1000); per batch: derive → delete-by-job → insert → advance
`STG_LOAD_CONTROL` HWM → `COMMIT`. A failure resumes from the last committed HWM;
no orphans because delete+insert for a job is one transaction. `STG_RUN` status
tracks the overall run.

**Batch / load tuning.**
- Full-refresh baseline may use `/*+ APPEND */` direct-path insert (and optionally
  drop/rebuild the `STG_*_job_ix` indexes around the bulk load).
- Incremental deltas are small — keep indexes live; **do not** use APPEND with the
  per-job delete/insert.
- Commit per batch (not per row, not once at end) for restartability + undo size.

---

## 1.6 Roles & security (existing roles suffice, with two deltas)

- **`CM_RO_USER` (read):** the new dev-SID columns (`CREATION_USER`,
  `CHANGE_USERID`, etc.) are **columns on already-granted tables** — `SELECT` on
  `CM_DEF_VJOB`/`VTAB` already covers them, so **no new psgmgr grant** is needed.
  Only open item: confirm `SELECT` on the real `CM_DEF_SETVAR` object (the
  unverified name).
- **`DRYDOCS_STG` (owner):** creates the 3 new objects in its own schema — no extra
  system privilege.
- **Python normalizer account — two new grants:**
  1. `SELECT, INSERT, UPDATE, DELETE ON STG_LOAD_CONTROL` (needs **UPDATE** to
     advance the HWM), and `SELECT, INSERT, DELETE` on `STG_DEV_SID` /
     `STG_SAMPLE_MANIFEST`.
  2. **`UPDATE` on the existing staging tables** — incremental's per-job replace is
     delete+insert, so INSERT/DELETE still suffice there; **but** if any table moves
     to true row-level MERGE later, add `UPDATE`. Flag for the grant script.
- `GRANT` is idempotent; wrap any `REVOKE` to swallow ORA-01927.

---

## 1.7 Summary & open decisions (for the user)

**Recommended:** add `STG_LOAD_CONTROL`, `STG_DEV_SID`, `STG_SAMPLE_MANIFEST` and
the view extensions as a new framework DDL file; implement incremental as
**watermark (VERSION_SERIAL / hash) → changed-job extract → per-job delete+insert →
commit+advance HWM**, keeping full-refresh as the baseline/rebuild path.

Open questions:
1. **Confirm `CM_DEF_SETVAR`** (still unverified) — blocks the variable extract and
   any incremental hash on variables.
2. **Is `CAPTURE_DATE` per-extract-uniform or per-row?** Decides whether it can be a
   change signal or only a coarse HWM (defaulting to VERSION_SERIAL/hash).
3. **Do `CREATION_USER` / `CHANGE_USERID` exist on `CM_DEF_VJOB`** as the
   scope-bind work assumes? (Pre-flight `ALL_TAB_COLUMNS` check — same pattern as
   the DDL's section 0.2 for MEMLIB/OVERLIB.)
4. Incremental cadence + retention: keep N runs of staging, or replace-in-place?

→ Handed to Phase 2 (Neo4j architect) for graph/ontology review of this staging
design and the incremental→idempotent-MERGE-into-graph path.
