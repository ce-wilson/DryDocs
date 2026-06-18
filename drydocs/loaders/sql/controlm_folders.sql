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
-- Scope binds (optional, NULL = no filter): :folder_filter (T.SCHED_TABLE
-- LIKE), :developer_sid (last editor of the folder — T.LAST_UPDATED_USER),
-- :row_cap (ROWNUM sample cap). :run_as does not apply at folder grain (no
-- job/owner on CM_DEF_VTAB) — use the job/variable extracts for run-as
-- scoping. (Operational who-ran-it identity is separate — CM_AUD_ACTS, later.)
-- =============================================================================

SELECT
    T.TABLE_ID       AS folder_id,
    T.SCHED_TABLE    AS sched_table,        -- folder name
    T.DATA_CENTER    AS data_center,        -- Control-M server (P12/P14/P32/P33)
    T.USER_DAILY     AS user_daily,
    T.TABLE_STATUS   AS table_status,
    T.TABLE_TYPE     AS table_type,
    T.INSTANCE_NAME  AS instance_name,
    T.LAST_UPDATED   AS last_updated,
    T.LAST_UPDATED_USER AS last_updated_user,
    T.CAPTURE_DATE   AS capture_date
FROM   psgmgr.CM_DEF_VTAB T
WHERE  T.USER_DAILY IS NOT NULL
  -- optional scope (any bind NULL = no filter on that dimension)
  AND  (:folder_filter IS NULL OR T.SCHED_TABLE       LIKE :folder_filter)
  AND  (:developer_sid IS NULL OR T.LAST_UPDATED_USER =    :developer_sid)
  AND  (:row_cap       IS NULL OR ROWNUM             <=    :row_cap)
;
