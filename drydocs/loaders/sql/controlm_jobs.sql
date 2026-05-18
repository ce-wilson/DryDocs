-- =============================================================================
-- controlm_jobs.sql
--
-- Source view : psgmgr.CM_DEF_VJOB joined to psgmgr.CM_DEF_VTAB for the
--               active-folder filter. Both wrap dtsremgr.DEF_* base tables;
--               read-only access via CM_RO_USER.
-- Projection  : columns the ControlMJobRow model expects.
--
-- TODO — column-name confirmation:
--   The exact column names below are based on the BMC DEF_JOB canonical
--   schema. Confirm against psgmgr.CM_DEF_VJOB once the SQL re-upload
--   completes; rename aliases here if anything differs.
--
-- Filter rule:
--   J.IS_CURRENT_VERSION = 1   — only current-version jobs
--   T.IS_CURRENT_VERSION = 1   — only current-version folders
--   T.USER_DAILY IS NOT NULL   — only actively-scheduled folders
-- =============================================================================

SELECT
    J.JOB_ID            AS job_id,
    J.VERSION_SERIAL    AS version_serial,
    J.TABLE_ID          AS folder_id,
    J.JOB_NAME          AS job_name,
    J.CYCLIC_TYPE       AS cyclic_type,
    J.JOB_ORDER         AS job_order,
    J.IS_CURRENT_VERSION AS is_current_version,
    J.CAPTURE_DATE      AS capture_date
FROM   psgmgr.CM_DEF_VJOB J
JOIN   psgmgr.CM_DEF_VTAB T   ON J.TABLE_ID = T.TABLE_ID
                              AND T.IS_CURRENT_VERSION = 1
WHERE  J.IS_CURRENT_VERSION = 1
  AND  T.USER_DAILY IS NOT NULL
;
