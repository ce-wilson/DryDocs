-- =============================================================================
-- controlm_conditions_out.sql
--
-- Source view : psgmgr.CM_DEF_LNKO_P_VW  (wraps dtsremgr.DEF_LNKO_P)
--
-- Schema confirmed from the actual DDL — ten columns:
--   CAPTURE_DATE, TABLE_ID, JOB_ID, CONDITION, ODATE, SIGN, ISN_,
--   VERSION_OPCODE, IS_CURRENT_VERSION, VERSION_SERIAL
--
-- Each row is "job J (in folder F) EMITS condition C with operator SIGN
--               on operational date ODATE, in this VERSION_SERIAL of the
--               definition."
--   SIGN = '+'  -> add the condition (success)
--   SIGN = '-'  -> remove the condition (cleanup)
--
-- Filter:
--   L.IS_CURRENT_VERSION = '1'  — only current versions
--   T.USER_DAILY IS NOT NULL    — only actively-scheduled folders
-- =============================================================================

SELECT
    L.TABLE_ID           AS folder_id,
    L.JOB_ID             AS job_id,
    L.VERSION_SERIAL     AS version_serial,
    L.CONDITION          AS condition_name,
    L.ODATE              AS odate,
    L.SIGN               AS sign,
    L.ISN_               AS isn,
    L.VERSION_OPCODE     AS version_opcode,
    L.IS_CURRENT_VERSION AS is_current_version,
    L.CAPTURE_DATE       AS capture_date
FROM   psgmgr.CM_DEF_LNKO_P_VW L
JOIN   psgmgr.CM_DEF_VTAB     T   ON L.TABLE_ID = T.TABLE_ID
WHERE  L.IS_CURRENT_VERSION = '1'
  AND  T.USER_DAILY IS NOT NULL
;
