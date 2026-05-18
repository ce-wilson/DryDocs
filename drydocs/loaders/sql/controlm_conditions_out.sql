-- =============================================================================
-- controlm_conditions_out.sql
--
-- Source view : psgmgr.CM_DEF_LNKO_P_VW  (out-conditions)
--               Wraps dtsremgr.DEF_LNKO_P; governed access via CM_RO_USER.
--
-- Columns confirmed from the actual DDL of psgmgr.CM_DEF_LNKO_P_VW:
--   CAPTURE_DATE, TABLE_ID, JOB_ID, CONDITION, ODATE, SIGN, ISN_,
--   VERSION_OPCODE, IS_CURRENT_VERSION, VERSION_SERIAL
--
-- Each row is "job J emits condition C with operator SIGN on ODATE".
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
WHERE  L.IS_CURRENT_VERSION = 1
;
