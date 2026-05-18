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
;
