-- =============================================================================
-- controlm_conditions_in.sql
--
-- Source view : psgmgr.CM_DEF_LNKI_P_VW  (wraps dtsremgr.DEF_LNKI_P)
--
-- Schema confirmed from the actual DDL — twelve columns:
--   CAPTURE_DATE, TABLE_ID, JOB_ID, CONDITION, ODATE, AND_OR, PARENTHESES,
--   ORDER_, ISN_, VERSION_OPCODE, IS_CURRENT_VERSION, VERSION_SERIAL
--
-- Each row is "job J (in folder F) CONSUMES condition C, evaluated in
--               a boolean expression of multiple IN conditions joined by
--               AND_OR with PARENTHESES grouping and ORDER_ sequencing,
--               on operational date ODATE, in this VERSION_SERIAL of the
--               definition."
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
    L.AND_OR             AS and_or,
    L.PARENTHESES        AS parentheses,
    L.ORDER_             AS order_,
    L.ISN_               AS isn,
    L.VERSION_OPCODE     AS version_opcode,
    L.IS_CURRENT_VERSION AS is_current_version,
    L.CAPTURE_DATE       AS capture_date
FROM   psgmgr.CM_DEF_LNKI_P_VW L
JOIN   psgmgr.CM_DEF_VTAB     T   ON L.TABLE_ID = T.TABLE_ID
WHERE  L.IS_CURRENT_VERSION = '1'
  AND  T.USER_DAILY IS NOT NULL
;
