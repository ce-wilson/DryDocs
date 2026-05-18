-- =============================================================================
-- controlm_folders.sql
--
-- Source view : psgmgr.CM_DEF_VTAB
--               (wraps dtsremgr.DEF_TAB; governed access via CM_RO_USER)
-- Projection  : columns the ControlMFolderRow model expects.
--
-- TODO — column-name confirmation:
--   The exact column names below are based on the BMC DEF_TAB canonical
--   schema. Confirm against psgmgr.CM_DEF_VTAB after the SQL re-upload
--   completes; rename aliases here if anything differs.
--
-- Filter rule:
--   IS_CURRENT_VERSION = 1   — only current-version definitions (replaces
--                              the earlier USER_DAILY filter; LNKO_P
--                              confirms this column exists on the family).
--   USER_DAILY IS NOT NULL   — kept ANDed in case both filters apply on
--                              the folder side; remove if it doesn't.
-- =============================================================================

SELECT
    T.TABLE_ID         AS folder_id,
    T.PARENT_TABLE     AS parent_table,   -- TODO confirm: maybe TABLE_NAME
    T.DATA_CENTER      AS data_center,
    T.USER_DAILY       AS user_daily,
    T.IS_CURRENT_VERSION AS is_current_version,
    T.VERSION_SERIAL   AS version_serial,
    T.CAPTURE_DATE     AS capture_date
FROM   psgmgr.CM_DEF_VTAB T
WHERE  T.IS_CURRENT_VERSION = 1
  AND  T.USER_DAILY IS NOT NULL
;
