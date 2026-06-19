# Oracle Ingestion — Living SDLC Document

<!-- §META -->
```yaml
persona: oracle-dba
flow: oracle-ingestion
skill: db
status: DRAFT
version: 0.2
last_updated: 2026-06-18T18:00:00Z
populated_from: persona-oracle-dba.md §1.1–1.8
diagrams_status: TODO (cron task 1.1–1.4)
traceability_status: TODO (cron task 1.5)
```

## §META — Scope and conventions

**Flow:** Ingest Control-M job definitions from psgmgr (read-only) into DRYDOCS_STG
staging layer, then propagate to downstream Neo4j graph. Two modes: FULL REFRESH
(baseline) and INCREMENTAL (delta by VERSION_SERIAL watermark). Sample extraction
is a bounded variant of full refresh.

**Secrets discipline:** schema object names only; no real SIDs, data values,
credentials, org names, or server addresses.

**ID scheme:**
- Requirements: `FR-OI-NNN` (Functional Requirement, Oracle Ingestion)
- Use Cases: `UC-OI-NNN`
- Open questions: `OQ-OI-N` (also tracked in persona-oracle-dba.md)

**Status values per item:** `ACTIVE` | `PLANNED` | `PARTIAL` | `DEPRECATED`

**Cross-reference:** see `sdlc-neo4j-schema.md` for the downstream graph flow.

---

## §FR — Functional Requirements

| ID | Requirement | Priority | Status | Implementation Object | Notes |
|---|---|---|---|---|---|
| FR-OI-001 | System SHALL read Control-M job definitions from psgmgr exclusively via `CM_RO_USER` role (read-only) | P0 | ACTIVE | `drydocs/loaders/sql/controlm_jobs.sql` | Source of truth is immutable from DryDocs side |
| FR-OI-002 | System SHALL support FULL REFRESH mode: delete-by-run_id then bulk insert all current-version records | P0 | ACTIVE | `drydocs/loaders/controlm_jobs_loader.py` | Current production mode |
| FR-OI-003 | System SHALL filter source extracts to `IS_CURRENT_VERSION='1'` to load exactly one canonical record per logical job | P0 | ACTIVE | `controlm_jobs.sql` (WHERE clause) | Prevents version-history duplication |
| FR-OI-004 | System SHALL extract folder definitions from `CM_DEF_VTAB` per data center | P0 | ACTIVE | `controlm_folders.sql` | Not versioned; use LAST_UPDATED for change detection |
| FR-OI-005 | System SHALL extract job in-conditions from `CM_DEF_LNKI_P_VW` and out-conditions from `CM_DEF_LNKO_P_VW` | P0 | ACTIVE | `controlm_conditions_in.sql`, `controlm_conditions_out.sql` | Versioned; filter IS_CURRENT_VERSION |
| FR-OI-006 | System SHALL classify raw variables into semantic kinds: `SEMANTIC_FACT`, `FLOW_REF`, `INVOCATION`, `FILE_REF`, `FILE_OP`, `NOTIFICATION`, `UNPARSED_COMMAND` | P0 | ACTIVE | Python normalizer | Classification is Python-owned, not SQL-recursive |
| FR-OI-007 | System SHALL write classified variable rows to typed staging tables per kind | P0 | ACTIVE | `STG_VARIABLE`, `STG_APP_FACT`, `STG_INVOCATION`, `STG_FILE_REF`, `STG_FILE_OP`, `STG_NOTIFICATION`, `STG_UNPARSED_COMMAND` | Surrogate IDENTITY PKs; keyed `(run_id, data_center, folder_id, job_id)` |
| FR-OI-008 | System SHALL record each execution in `STG_RUN(run_id, loader, loaded_at, status)` | P0 | ACTIVE | `STG_RUN` | Provenance anchor for all staging rows |
| FR-OI-009 | System SHALL support INCREMENTAL mode driven by `VERSION_SERIAL` high-water mark per `(source_object, data_center)` | P1 | PLANNED | `STG_LOAD_CONTROL` + `drydocs/loaders/incremental_controlm.py` (new) | Primary watermark; CAPTURE_DATE as fallback if VERSION_SERIAL unreliable |
| FR-OI-010 | System SHALL persist the high-water mark in `STG_LOAD_CONTROL(source_object, data_center, hwm_version_serial, hwm_capture_date, load_mode, updated_at, rows_applied)` | P1 | PLANNED | `controlm_staging_supplement_ddl.sql` | New table; idempotent CREATE |
| FR-OI-011 | System SHALL detect changed jobs by querying `VERSION_SERIAL > hwm_version_serial` per data center | P1 | PLANNED | `drydocs/loaders/sql/incremental_changed_jobs.sql` (new) | Changed-job extract SQL |
| FR-OI-012 | System SHALL execute incremental batch loop: (1) cleanup stale staging rows for changed jobs, (2) insert normalized rows, (3) advance HWM; loop SHALL be restartable from last committed HWM on failure | P1 | PLANNED | `drydocs/loaders/incremental_controlm.py` | Per-job delete+insert is idempotent; HWM only advances after commit |
| FR-OI-013 | System SHALL support SAMPLE mode: scope-bounded extraction via binds `(:folder_filter, :run_as, :developer_sid, :row_cap)` | P1 | ACTIVE | `drydocs/loaders/sql/controlm_variables_scenarios.sql` | Row cap enforced via FETCH FIRST |
| FR-OI-014 | System SHALL persist sample provenance in `STG_SAMPLE_MANIFEST(run_id, scope_folder, developer_sid, row_cap, scenario_count, loaded_at)` | P2 | PLANNED | `controlm_staging_supplement_ddl.sql` | Enables downstream sample lineage queries |
| FR-OI-015 | System SHALL normalize developer SID attribution using `UPPER(REGEXP_REPLACE(sid,'p$',''))` to strip automation suffix | P2 | ACTIVE | `JOB_DETAILED_VIEW` inline expression | Automation accounts end in lowercase `p`; strip to get canonical employee SID |
| FR-OI-016 | System SHALL handle legitimate duplicate `(job, var)` definitions across data centers without collision | P1 | ACTIVE | `STG_VARIABLE` PK design; pre-flight TABLE_ID check | Defensive composite key; 0.1 pre-flight verifies no cross-DC TABLE_ID collision |
| FR-OI-017 | System SHALL support ~240K current-version jobs and ~1.1M variable rows across 4 data centers at full refresh | P0 | ACTIVE | Volume: <3M rows / <2GB; no partitioning needed currently | Volume baseline recorded here for capacity tracking |
| FR-OI-018 | System SHALL pilot incremental ingestion on data center P012 first | P1 | PLANNED | Pilot scope | Per `project_controlm_c3_normalization.md` |

---

## §UC — Use Cases

### UC-OI-001: Full Refresh Load

| Field | Value |
|---|---|
| Actor | Data Engineer / Scheduled job |
| Goal | Load all current-version Control-M jobs for one data center into DRYDOCS_STG |
| Preconditions | DRYDOCS_STG schema exists; CM_RO_USER has access to psgmgr objects; target data center is specified |
| FR linkage | FR-OI-001, FR-OI-002, FR-OI-003, FR-OI-004, FR-OI-005, FR-OI-006, FR-OI-007, FR-OI-008 |
| Status | ACTIVE |

**Steps:**
1. Open `STG_RUN` record (`status='RUNNING'`).
2. Query `CM_DEF_VTAB` for folders (data center filter).
3. Query `CM_DEF_VJOB WHERE IS_CURRENT_VERSION='1'` (data center filter).
4. Query `CM_DEF_LNKI_P_VW` / `CM_DEF_LNKO_P_VW` for conditions.
5. Run Python normalizer over raw job + variable rows.
6. DELETE old staging rows by `run_id` (or TRUNCATE for full replace).
7. Bulk INSERT to STG_ tables in batches of 1 000 rows.
8. Update `STG_RUN.status='SUCCEEDED'`, set `loaded_at`.

**Postconditions:** STG_ tables reflect complete current state for the data center; STG_RUN records the execution.

**Exceptions:**
- Source access denied → fail fast; `STG_RUN.status='FAILED'`.
- Normalizer error → partial insert may exist; mark run FAILED; re-run is safe (DELETE then re-insert).
- Duplicate TABLE_ID across DCs → pre-flight 0.1 check fails before any writes.

---

### UC-OI-002: Incremental Delta Load

| Field | Value |
|---|---|
| Actor | Scheduled job (daily / after-hours) |
| Goal | Load only jobs changed since the last high-water mark; avoid re-processing the full population |
| Preconditions | `STG_LOAD_CONTROL` has a prior HWM entry for `(source_object, data_center)`; a full refresh has established the baseline |
| FR linkage | FR-OI-009, FR-OI-010, FR-OI-011, FR-OI-012, FR-OI-018 |
| Status | PLANNED |

**Steps:**
1. Read `hwm_version_serial` from `STG_LOAD_CONTROL` for `(CM_DEF_VJOB, :data_center)`.
2. Query `CM_DEF_VJOB WHERE VERSION_SERIAL > hwm AND IS_CURRENT_VERSION='1'`.
3. If result is empty → log NO_CHANGES; stop.
4. For each batch of 1 000 changed jobs:
   a. DELETE existing staging rows for `(data_center, folder_id, job_id)`.
   b. INSERT normalized rows into STG_ tables.
   c. Advance `STG_LOAD_CONTROL.hwm_version_serial` to batch max; COMMIT.
5. (Downstream) trigger graph incremental sync (see `sdlc-neo4j-schema.md §UC-NS-002`).

**Postconditions:** Staging reflects the delta; `STG_LOAD_CONTROL.hwm_version_serial` advanced to latest processed version.

**Exceptions:**
- Mid-batch failure → HWM not advanced past failure point → safe restart from last committed HWM.
- HWM entry not found for this source/DC pair → fall through to full refresh (UC-OI-001).

---

### UC-OI-003: Sample Extraction

| Field | Value |
|---|---|
| Actor | Developer / Analyst |
| Goal | Extract a scope-bounded subset of jobs and variables for offline analysis or dev-environment testing |
| Preconditions | `controlm_variables_scenarios.sql` deployed; scope binds provided by caller |
| FR linkage | FR-OI-013, FR-OI-014 |
| Status | ACTIVE (sampling); PLANNED (manifest persistence) |

**Steps:**
1. Bind scope parameters: `:folder_filter`, `:run_as`, `:developer_sid`, `:row_cap`.
2. Execute `controlm_variables_scenarios.sql` (per-scenario probes + UNION-ALL).
3. Write rows to staging (same STG_ tables as full refresh, scoped run_id).
4. Write provenance row to `STG_SAMPLE_MANIFEST`.

**Postconditions:** Staging contains scoped sample; `STG_SAMPLE_MANIFEST` records what was loaded and at what scope.

**Exceptions:**
- Empty sample → warn; mark manifest with `scenario_count=0`.
- `row_cap` hit → `FETCH FIRST` enforces hard limit; manifest records actual vs. cap.

---

### UC-OI-004: Restart Failed Incremental Load

| Field | Value |
|---|---|
| Actor | Data Engineer |
| Goal | Resume a failed incremental run from the last safe checkpoint without data duplication |
| Preconditions | Prior incremental run failed mid-batch; `STG_LOAD_CONTROL` HWM was not advanced past the failure point |
| FR linkage | FR-OI-012 |
| Status | PLANNED |

**Steps:**
1. Identify last committed `hwm_version_serial` from `STG_LOAD_CONTROL` (unchanged by failed batches).
2. Re-run incremental load from that HWM (same as UC-OI-002).
3. Batches that were already fully committed = no-op (per-job DELETE+INSERT is idempotent).
4. Uncommitted batches are re-processed cleanly.

**Postconditions:** Full delta committed; no duplicates.

---

### UC-OI-005: Staging Provenance Audit

| Field | Value |
|---|---|
| Actor | Data Analyst / DBA |
| Goal | Determine what was loaded, when, with what scope, and from what HWM |
| Preconditions | Access to `STG_RUN`, `STG_LOAD_CONTROL`, `STG_SAMPLE_MANIFEST` |
| FR linkage | FR-OI-008, FR-OI-010, FR-OI-014 |
| Status | PLANNED (pending manifest table) |

**Steps (read-only):**
1. Query `STG_LOAD_CONTROL` for HWM history by `(source_object, data_center)`.
2. Query `STG_SAMPLE_MANIFEST` for sample scope by `run_id`.
3. Join `STG_RUN` for timing and status.

---

## §DEP — Dependencies

| System | Role | Interface | Access Pattern | Notes |
|---|---|---|---|---|
| **PSGMGR** | Source of truth for Control-M job definitions | Oracle JDBC via `CM_RO_USER` role | Read-only; no DML | External; read grants must be in place |
| **DRYDOCS_STG** | Owned staging schema | Oracle DDL + DML; same DB connection | Write/own; STG_ tables + views | DryDocs owns this schema |
| **SEAL** | Application metadata registry | Application API or flat extract | Enriches `STG_APP_FACT` with application identity (seal_id) | External; see `project_controlm_escalation_governance.md` |
| **PAT** | Product/Application/Team org hierarchy | API or flat extract | Enriches org attribution in staging | External; see `project_pat_ontology_analysis.md` |
| **OracleAdapter** | Python connector to Oracle | `drydocs/loaders/sql/` + cx_Oracle | Batched SELECT + batch INSERT | Internal; part of DryDocs framework |
| **Python normalizer** | Variable classification + staging writer | `drydocs/loaders/` Python framework | Reads raw extract; writes STG_ tables | Internal |
| **Neo4j** | Downstream graph consumer | Python neo4j driver (separate flow) | Reads `JOB_DETAILED_VIEW`, `STG_APP_FACT` after staging complete | See `sdlc-neo4j-schema.md §DEP` |
| **STG_LOAD_CONTROL** | Watermark table (new, PLANNED) | Oracle table in DRYDOCS_STG | Read HWM before extract; write after commit | Keystone for incremental mode |
| **CM_RO_USER** | Oracle role | Grant on psgmgr objects | SELECT only | Must include `CM_DEF_SETVAR` when name confirmed (OQ-OI-1) |

---

## §C1 — C1 Context Diagram

<!-- TODO: cron task 1.1 — generate Mermaid flowchart diagram -->
<!-- Diagram should show: PSGMGR / SEAL / PAT (external) → OracleAdapter →
     Normalizer/Loader → DRYDOCS_STG → Neo4j (downstream).
     Verify file paths against drydocs/loaders/sql/ before drawing. -->

```
[DIAGRAM PENDING — cron task 1.1]

Actors / external systems:
  - PSGMGR (Control-M Production DB) [read-only via CM_RO_USER]
  - SEAL (Application Registry) [enrichment source]
  - PAT (Org Hierarchy) [enrichment source]

System boundary: DryDocs Oracle Ingestion
  - OracleAdapter (drydocs/loaders/sql/)
  - Normalizer / Loader (drydocs/loaders/)
  - DRYDOCS_STG (Oracle schema: STG_ tables + views)

Downstream:
  - Neo4j Graph (reads JOB_DETAILED_VIEW + STG_APP_FACT via Python loaders)
```

---

## §DES — Design Diagrams

### §DES/full-refresh — Full-Refresh Load Sequence

<!-- TODO: cron task 1.2 — Mermaid sequenceDiagram for full refresh -->
```
[DIAGRAM PENDING — cron task 1.2]

Participants: Actor, STG_RUN, psgmgr (CM_DEF_VJOB etc.), Normalizer, DRYDOCS_STG
Sequence: open run → query source → normalize → delete old → batch insert → close run
```

### §DES/incremental — Incremental Load Sequence

<!-- TODO: cron task 1.3 — Mermaid sequenceDiagram for incremental load -->
```
[DIAGRAM PENDING — cron task 1.3]

Participants: STG_LOAD_CONTROL, psgmgr, IncrementalControlMLoader, DRYDOCS_STG, Neo4j
Sequence: read HWM → changed-job extract → per-batch loop (cleanup → insert → advance HWM) → graph sync
Reference files: incremental_controlm.py (planned), incremental_changed_jobs.sql (planned)
```

### §DES/er — STG_ Tables Entity-Relationship

<!-- TODO: cron task 1.4 — Mermaid erDiagram for DRYDOCS_STG staging tables -->
```
[DIAGRAM PENDING — cron task 1.4]

Tables to include: STG_RUN, STG_LOAD_CONTROL (new), STG_SAMPLE_MANIFEST (new),
STG_VARIABLE, STG_APP_FACT, STG_INVOCATION, STG_FILE_REF, STG_FILE_OP,
STG_NOTIFICATION, STG_PARSE_QUALITY, STG_UNPARSED_COMMAND
Key relationships: all tables keyed (run_id, data_center, folder_id, job_id);
STG_RUN is the provenance anchor; STG_LOAD_CONTROL has (source_object, data_center) PK
```

---

## §TM — Traceability Matrix

<!-- TODO: cron task 1.5 — generate FR→UC→implementation file mapping -->
```
[TRACEABILITY PENDING — cron task 1.5]

For each FR-OI-*: map to UC-OI-*, implementation file, status, blocking OQ
```

---

## §SRC — Source Views and Objects

### psgmgr read objects (via CM_RO_USER, read-only)

| Object | Grain | Key columns | Est. volume | Notes |
|---|---|---|---|---|
| `CM_DEF_VJOB` | Job version | `folder_id`, `job_id`, `version_serial`, `is_current_version` | ~240K current-version rows | Primary job source; ~100 cols; filter `IS_CURRENT_VERSION='1'` |
| `CM_DEF_VTAB` | Folder | `folder_id`, `data_center` | ~18.8K | Not versioned; `LAST_UPDATED` / `CAPTURE_DATE` for change detection |
| `CM_DEF_LNKI_P_VW` | In-condition per job | `folder_id`, `job_id`, `condition_name` | Varies | Prerequisites / in-conditions; versioned |
| `CM_DEF_LNKO_P_VW` | Out-condition per job | `folder_id`, `job_id`, `condition_name` | Varies | Postconditions / out-conditions; versioned |
| `CM_DEF_SETVAR` | Variable per job | `folder_id`, `job_id`, `var_name`, `var_value` | ~1.1M | **Name unverified — OQ-OI-1** |

### DRYDOCS_STG read views (for downstream consumers)

| View / Table | Purpose | Consumers |
|---|---|---|
| `JOB_DETAILED_VIEW` | Denormalized job record; inline developer SID normalization expression | Neo4j jobs loader; analysts |
| `JOB_VARIABLE_VIEW` | Variables joined to job for classification input | Python normalizer |
| `STG_COVERAGE_SUMMARY` | Cross-DC coverage metrics | Monitoring; QA |
| `STG_APP_FACT` | SEAL application-attributed semantic variable facts | Neo4j SEAL attribution loader |
| `STG_LOAD_CONTROL` | High-water mark per `(source_object, data_center)` — **PLANNED** | IncrementalControlMLoader; graph provenance |
| `STG_SAMPLE_MANIFEST` | Sample run provenance — **PLANNED** | Audit; graph :JobRun annotation |

### DryDocs Python + SQL loader files

| File | Role |
|---|---|
| `drydocs/loaders/sql/controlm_jobs.sql` | Full-refresh job extract |
| `drydocs/loaders/sql/controlm_folders.sql` | Folder extract |
| `drydocs/loaders/sql/controlm_conditions_in.sql` | In-condition extract |
| `drydocs/loaders/sql/controlm_conditions_out.sql` | Out-condition extract |
| `drydocs/loaders/sql/controlm_variables_scenarios.sql` | Sample-mode scoped variable extract |
| `drydocs/loaders/sql/ddl/controlm_staging_ddl.sql` | Base STG_ DDL |
| `drydocs/loaders/sql/ddl/controlm_staging_supplement_ddl.sql` | Phase-1 additions: STG_LOAD_CONTROL, STG_SAMPLE_MANIFEST |
| `drydocs/loaders/sql/incremental_changed_jobs.sql` | **PLANNED** — changed-job delta extract |
| `drydocs/loaders/incremental_controlm.py` | **PLANNED** — IncrementalControlMLoader orchestrator |

---

## §OQ — Open Questions

| ID | Question | Blocks | Source |
|---|---|---|---|
| OQ-OI-1 | What is the exact name of the variable source object? (`CM_DEF_SETVAR` is unverified) | FR-OI-006, FR-OI-007, all variable extracts | persona-oracle-dba.md §1.1 |
| OQ-OI-2 | Is `CAPTURE_DATE` set per-row at insert time, or is it uniform per extract batch? | HWM strategy selection (FR-OI-009); if uniform, VERSION_SERIAL must be primary watermark | persona-oracle-dba.md §1.5 |
| OQ-OI-3 | Do `CREATION_USER` and `CHANGE_USERID` exist on `CM_DEF_VJOB`? | FR-OI-015 (developer SID attribution graph edge); `JOB_DEVELOPER_VIEW` design | persona-oracle-dba.md §1.2 |
| OQ-OI-4 | What incremental cadence is required, and how many runs of staging should be retained? | `STG_LOAD_CONTROL` rollback window; full-refresh schedule; `STG_SAMPLE_MANIFEST` retention | persona-oracle-dba.md §1.5 |

---

## §LOG — Change Log (newest at bottom)

- 2026-06-18T18:00:00Z v0.1 scaffold: §META, §FR (FR-OI-001 to FR-OI-018), §UC (UC-OI-001 to UC-OI-005), §DEP, §SRC populated from persona-oracle-dba.md. Diagram/TM sections are stubs for cron task 1.1–1.5.
- 2026-06-18T18:00:00Z v0.2 §OQ section added; §SRC loader file table added.
