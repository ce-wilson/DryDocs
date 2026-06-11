-- =============================================================================
-- controlm_variables.sql
--
-- Source table : psgmgr.CM_DEF_SETVAR (replicated copy of dtsremgr.DEF_SETVAR)
--                ** VERIFY NAME ** — this is the object behind the
--                (TABLE_NAME|JOB_NAME|JOB_ID|APPL_TYPE|NAME|VALUE) extract;
--                substitute the confirmed view name before production use.
--                Joined to CM_DEF_VJOB + CM_DEF_VTAB for context.
--
-- Projection   : one row per variable definition with job + folder context.
--                Matches the ControlMVariableRow model. Variable scope is
--                derived: smart-folder header rows carry the folder name as
--                their job name and hold folder-scope variables that all
--                jobs in the folder inherit.
--
-- Volumes      : ~1.1M rows across 4 data centers (job-level ~1.03M +
--                folder-level ~95K; max 67 per job). 59% of jobs define no
--                variables at all.
--
-- Filter rule  :
--   J.IS_CURRENT_VERSION = '1'  — current-version jobs only
--   T.USER_DAILY IS NOT NULL    — actively-scheduled folders only
--   (verify whether CM_DEF_SETVAR carries its own IS_CURRENT_VERSION /
--    VERSION_SERIAL like the LNKI/LNKO views; add the filter if so)
--
-- NOTE: duplicate (job, variable-name) definitions are legitimate in the
-- source (observed: %%FileWatch-TIME_LIMIT defined twice on one job with
-- different values). Do NOT dedupe here — definition order is preserved
-- by ROWNUM-free natural read order and disambiguated downstream.
-- =============================================================================

SELECT
    T.DATA_CENTER         AS data_center,
    V.TABLE_ID            AS folder_id,
    T.SCHED_TABLE         AS folder_name,
    V.JOB_ID              AS job_id,
    J.JOB_NAME            AS job_name,
    J.APPL_TYPE           AS appl_type,        -- OS / FileWatch / AIAWSWLK / ...
    CASE WHEN J.JOB_NAME = T.SCHED_TABLE
         THEN 'FOLDER' ELSE 'JOB' END
                          AS var_scope,
    V.NAME                AS var_name,
    V.VALUE               AS var_value
FROM   psgmgr.CM_DEF_SETVAR V                  -- ** VERIFY VIEW NAME **
JOIN   psgmgr.CM_DEF_VJOB  J  ON V.TABLE_ID = J.TABLE_ID
                             AND V.JOB_ID   = J.JOB_ID
JOIN   psgmgr.CM_DEF_VTAB  T  ON J.TABLE_ID = T.TABLE_ID
WHERE  J.IS_CURRENT_VERSION = '1'
  AND  T.USER_DAILY IS NOT NULL
;
