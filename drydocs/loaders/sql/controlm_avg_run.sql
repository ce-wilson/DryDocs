-- =============================================================================
-- controlm_avg_run.sql
--
-- Source table : psgmgr.CM_AVG_RUN  (runtime statistics per job; name
--                verified live 2026-07-07/09; governed access via CM_RO_USER)
-- Projection   : all 14 observed columns — the supplement use case consumes
--                the aggregates AND the raw sample arrays (day-of-week
--                medians are computed from SAMPLES_* in Python, no CM_HIST
--                scan needed).
--
-- GATE-BOUND: the graph landing (avg/median timing PROPERTIES onto existing
-- :ControlMJob nodes + derived folder-level windows — NO new labels/edges)
-- is proposed only — see config/gate-prompts/controlm-avg-run-supplement.yaml.
-- Until the SME confirms, rows are staging-only (CM_DEF_SETVAR_VW precedent).
--
-- Known semantics (SME 2026-07-07; verify via adhoc/profile_cm_avg_run.sql):
--   * Join to jobs: (SCHED_TABLE, JOB_MEM_NAME) = (folder name,
--     CM_DEF_VJOB.JOB_NAME) — MEMNAME is never the key. Weaker than the
--     (TABLE_ID, JOB_ID) node key; -CYC/-DLY twin folders each carry rows.
--   * AVG_START_TIME uses the Control-M >24h post-midnight clock
--     (293502 ≈ 05:35:02 next day) — Python normalizes; never in SQL.
--   * Run times in seconds; FileWatcher rows measure watch/wait (~240s
--     cycles), not processing — the supplement flags them via APPL_TYPE.
--   * Data TYPES unknown until probe P0 (result grid only) — staging DDL
--     waits on it (SAMPLES_* may need CLOB).
--
-- Load order: supplement pass — runs AFTER the jobs pass (MATCHes existing
-- :ControlMJob nodes, never MERGEs them; the software-registry DESCRIBES
-- precedent). Unmatched stats rows are a coverage metric, never node-creating.
--
-- Scope binds (optional, NULL = no filter): :folder_filter (A.SCHED_TABLE
-- LIKE — same bind the other five extracts use), :row_cap (ROWNUM cap),
-- LOAD2 (2026-09-04): this column carries the LONG-form data-center name, so
-- this statement binds :data_center_filter. The CM_DEF_VTAB family (folders,
-- jobs, variables) carries the SHORT server code and binds :data_center_code;
-- one --data-center value emits both binds and each statement uses its own.
-- :data_center_filter (A.DATA_CENTER LIKE — G115; long-form, and the DC
-- value-domain probe in adhoc/profile_cm_avg_run.sql, answered 2026-07-22,
-- confirmed the long-form value domain matches CM_DEF_VTAB, so one pattern
-- scopes the whole extract family).
-- :run_as / :developer_sid do not apply (no owner/author at this grain).
-- =============================================================================

SELECT
    A.DATA_CENTER         AS data_center,        -- long-form DC name
    A.INSTANCE_NAME       AS instance_name,      -- relation to DC = probe P2b
    A.SCHED_TABLE         AS sched_table,        -- folder name (join key part)
    A.JOB_MEM_NAME        AS job_mem_name,       -- = CM_DEF_VJOB.JOB_NAME (join key part)
    A.NODE_GROUP          AS node_group,         -- runtime host-group placement (cross-validates RUNS_ON)
    A.DSN                 AS dsn,                -- null in all sampled rows (probe P3b; drop if always null)
    A.AVG_START_TIME      AS avg_start_time,     -- >24h clock — normalize in Python
    A.AVG_RUN_TIME        AS avg_run_time,       -- seconds
    A.MIN_RUN_TIME        AS min_run_time,       -- seconds
    A.MAX_RUN_TIME        AS max_run_time,       -- seconds
    A.STD_DEV             AS std_dev,
    A.SAMPLES_RUN_TIME    AS samples_run_time,   -- raw per-run seconds array (~20)
    A.SAMPLES_START_TIME  AS samples_start_time, -- raw <ts>:<odate> pairs — day-of-week medians
    A.CAPTURE_DATE        AS capture_date        -- replication timestamp — never authorship
FROM   psgmgr.CM_AVG_RUN A
WHERE  (:folder_filter      IS NULL OR A.SCHED_TABLE LIKE :folder_filter)
  AND  (:data_center_filter IS NULL OR A.DATA_CENTER LIKE :data_center_filter)
  AND  (:row_cap            IS NULL OR ROWNUM        <=   :row_cap)
;
