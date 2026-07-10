-- =============================================================================
-- controlm_variables.sql
--
-- Source view  : psgmgr.CM_DEF_SETVAR_VW (replicated copy of dtsremgr.DEF_SETVAR)
--                Confirmed 2026-07-10 against live psgmgr: this is the object
--                behind the (TABLE_NAME|JOB_NAME|JOB_ID|APPL_TYPE|NAME|VALUE)
--                extract — a view carrying its own IS_CURRENT_VERSION /
--                VERSION_SERIAL. Joined to CM_DEF_VJOB + CM_DEF_VTAB for context.
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
--   V.IS_CURRENT_VERSION = '1'  — current-version variable rows only
--   J.IS_CURRENT_VERSION = '1'  — current-version jobs only
--   T.USER_DAILY IS NOT NULL    — actively-scheduled folders only
--   (CM_DEF_SETVAR_VW carries its own IS_CURRENT_VERSION / VERSION_SERIAL like
--    the LNKI/LNKO views — confirmed 2026-07-10 — so the V-filter is applied;
--    without it the extract returns superseded variable rows.)
--
-- Scope binds  : optional, NULL = no filter on that dimension. Used for
--                sampling and targeted re-pulls (pass NULL for the full
--                population). The same binds appear on every psgmgr extract;
--                folder-grained extracts use only :folder_filter / :row_cap.
--   :folder_filter  folder-name LIKE pattern (e.g. 'CCB_AUTO_%')
--   :run_as         tenant FID (service) user the job runs as — J.OWNER, exact
--   :developer_sid  human developer who authored/changed the def — matched on
--                   J.AUTHOR / J.CREATION_USER / J.CHANGE_USERID. Control-M
--                   SIDs start with a lowercase letter; a SID ending in
--                   lowercase 'p' is the automation release process, not a
--                   person.
--   :row_cap        unordered sample cap (ROWNUM); NULL = unlimited
--   (Operational employee identity — who *ran* actions vs authored the def —
--    is separate: it lives in the action-audit table psgmgr.CM_AUD_ACTS; wire
--    it on a future audit extract, configure later.)
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
FROM   psgmgr.CM_DEF_SETVAR_VW V
JOIN   psgmgr.CM_DEF_VJOB  J  ON V.TABLE_ID = J.TABLE_ID
                             AND V.JOB_ID   = J.JOB_ID
JOIN   psgmgr.CM_DEF_VTAB  T  ON J.TABLE_ID = T.TABLE_ID
WHERE  V.IS_CURRENT_VERSION = '1'
  AND  J.IS_CURRENT_VERSION = '1'
  AND  T.USER_DAILY IS NOT NULL
  -- optional scope (any bind NULL = no filter on that dimension)
  AND  (:folder_filter IS NULL OR T.SCHED_TABLE LIKE :folder_filter)
  AND  (:run_as        IS NULL OR J.OWNER        =  :run_as)   -- tenant FID user
  AND  (:developer_sid IS NULL OR :developer_sid IN (J.AUTHOR, J.CREATION_USER, J.CHANGE_USERID))
  AND  (:row_cap       IS NULL OR ROWNUM        <=  :row_cap)
;
