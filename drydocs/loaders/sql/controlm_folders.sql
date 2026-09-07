-- =============================================================================
-- controlm_folders.sql
--
-- Source table : psgmgr.CM_DEF_VTAB  (replicated copy of dtsremgr.DEF_VTAB;
--                                     governed access via CM_RO_USER)
-- Projection   : columns the ControlMFolderRow model expects.
--
-- Key schema findings from the actual DDL:
--   * The folder NAME is SCHED_TABLE (NOT a "PARENT_TABLE" column — that
--     name lives only on the job side as a denormalized FK).
--   * There is NO IS_CURRENT_VERSION column on the folder table; versioning
--     applies only to jobs and conditions.
--   * There is NO VERSION_SERIAL on the folder table either.
--   * The only active-scheduling filter on folders is USER_DAILY IS NOT NULL.
--
-- The folder-level deletion columns (TBL_DELETION_*) are intentionally
-- omitted from the projection — soft-deletes are out of scope for M3.
--
-- APPLICATION (folder grain): CM_DEF_VTAB carries no APPLICATION column —
-- the folder-level value lives on the folder HEADER ROW in CM_DEF_VJOB
-- (JOB_ID = 1, the SMART-Table header per the controlm-q1q3-phase1 gate).
-- LEFT JOIN so folders without a header row still load (application NULL:
-- the cypher skips the :ControlMApplication merge for those rows).
--
-- Scope binds (optional, NULL = no filter): :folder_filter (T.SCHED_TABLE
-- LIKE), :developer_sid (last editor of the folder — T.LAST_UPDATED_USER),
-- LOAD2 (2026-09-04): this statement reads CM_DEF_VTAB, which carries the SHORT
-- Control-M server code, so it binds :data_center_code. CM_HOSTS and CM_AVG_RUN
-- carry the LONG-form name and bind :data_center_filter. The scope helper emits
-- BOTH from one --data-center value (drydocs/cli_shared.py _data_center_binds) and
-- python-oracledb drops the one this statement does not name. Before LOAD2 every
-- statement bound :data_center_filter and a long-form value here returned ZERO ROWS,
-- reading as an empty data center rather than as an error.
-- :row_cap (ROWNUM sample cap), :data_center_code (T.DATA_CENTER LIKE —
-- G115 the per-data-center run recipe, LOAD2 the SHORT-code domain: this
-- column is CM_DEF_VTAB's and carries the short server code, NOT the long
-- form the adhoc/profile_cm_avg_run.sql probe reported for CM_AVG_RUN).
-- :run_as does not apply at folder grain (no
-- job/owner on CM_DEF_VTAB) — use the job/variable extracts for run-as
-- scoping. (Operational who-ran-it identity is separate — CM_AUD_ACTS, later.)
-- =============================================================================

SELECT
    T.TABLE_ID       AS folder_id,
    T.SCHED_TABLE    AS sched_table,        -- folder name
    T.DATA_CENTER    AS data_center,        -- Control-M server (P12/P14/P32/P33)
    J.APPLICATION    AS application,        -- folder header row -> :ControlMApplication
    T.USER_DAILY     AS user_daily,
    T.TABLE_STATUS   AS table_status,
    T.TABLE_TYPE     AS table_type,
    T.INSTANCE_NAME  AS instance_name,
    T.LAST_UPDATED   AS last_updated,
    T.LAST_UPDATED_USER AS last_updated_user,
    T.CAPTURE_DATE   AS capture_date
FROM   psgmgr.CM_DEF_VTAB T
-- ALIAS NOTE (J39, 2026-08-26): the header-row join is aliased J (job table),
-- matching the company's copy — back-flowed mechanism-only so the two sides'
-- file stops carrying a permanent cosmetic diff. Was H.
LEFT JOIN psgmgr.CM_DEF_VJOB J
       ON  J.TABLE_ID = T.TABLE_ID
       AND J.JOB_ID   = 1                   -- folder header row (SMART Table)
       AND J.IS_CURRENT_VERSION = 'Y'       -- VARCHAR2(1): string literal; domain 'Y' (company TDD, 2026-07-15)
WHERE  T.USER_DAILY IS NOT NULL
  -- optional scope (any bind NULL = no filter on that dimension)
  AND  (:folder_filter      IS NULL OR T.SCHED_TABLE       LIKE :folder_filter)
  AND  (:developer_sid      IS NULL OR T.LAST_UPDATED_USER =    :developer_sid)
  AND  (:data_center_code IS NULL OR T.DATA_CENTER       LIKE :data_center_code)
  AND  (:row_cap            IS NULL OR ROWNUM             <=    :row_cap)
;
