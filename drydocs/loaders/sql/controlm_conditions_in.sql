-- =============================================================================
-- controlm_conditions_in.sql
--
-- Source view : psgmgr.CM_DEF_LNKI_P_VW  (in-conditions)
--               Wraps dtsremgr.DEF_LNKI_P; governed access via CM_RO_USER.
--
-- Columns inferred by symmetry with the confirmed LNKO_P_VW. Re-upload
-- the actual DDL to validate before loading against production.
--
-- Each row is "job J consumes condition C with operator SIGN on ODATE".
-- =============================================================================

SELECT
    L.TABLE_ID           AS folder_id,
    L.JOB_ID             AS job_id,
    L.VERSION_SERIAL     AS version_serial,
    L.CONDITION          AS condition_name,
    L.ODATE              AS odate,
    L.SIGN               AS sign,
    L.ISN_               AS isn,
    L.IS_CURRENT_VERSION AS is_current_version,
    L.CAPTURE_DATE       AS capture_date
FROM   psgmgr.CM_DEF_LNKI_P_VW L
WHERE  L.IS_CURRENT_VERSION = 1
;
