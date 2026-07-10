-- =============================================================================
-- controlm_variables_scenarios.sql  —  taxonomy scenario-coverage sampler
--
-- PURPOSE
--   Pull ONE representative row per classifier/resolver/staging scenario from
--   psgmgr, so a small, coverage-complete variable sample can be regenerated on
--   demand. Output columns match controlm_variables.sql exactly (plus a leading
--   `scenario` tag, which ControlMVariableRow ignores), so it drops straight
--   into `normalize-variables --csv` / `analyze-variables --csv` and the
--   sample-backed unit tests.
--
-- FUTURE TO-DO (why this file exists)
--   The 3 sample-backed tests (test_sample_*) currently skip when the gitignored
--   production CSV is absent (Track-1 = 86 passed / 3 skipped). Goal: build a
--   small, deterministic, full-coverage fixture from this sampler so those paths
--   run on ANY clone. Steps:
--     [ ] Verify each scenario predicate against real psgmgr (some are
--         approximations of the Python taxonomy — see ** REFINE ** markers).
--     [x] Source view name confirmed: psgmgr.CM_DEF_SETVAR_VW (verified
--         2026-07-10 against live psgmgr).
--     [ ] Run the consolidated query; SANITIZE values (paths, SIDs, SEAL ids,
--         emails) before committing — production data must not land in the repo
--         or the public producer mirror.
--     [ ] Commit the sanitized result as a fixture under tests/fixtures/ and
--         point test_sample_* at it (replacing skipif with a real assertion).
--     [ ] Add a scenario whenever a new VariableKind / launcher / edge case
--         appears (keep this file and the fixture in lockstep).
--
-- GOTCHA — matching literal '%' in LIKE
--   Control-M variable names/values contain '%%'. In LIKE, '%' is the wildcard,
--   so a literal percent must be escaped: `LIKE '\%\%FileWatch-%' ESCAPE '\'`.
--   For whole-name matches use `=` / `IN (...)` (no wildcard, no escape needed).
--
-- SCENARIOS INCLUDED  (scenario tag -> what it exercises -> probe SQL)
-- -----------------------------------------------------------------------------
-- Each probe below is the standalone "find me one real example" query. The
-- consolidated query at the bottom is the union of these, one row each.
--
--   LITERAL              plain value, no tokens
--     -- SELECT * FROM v WHERE v.var_value IS NOT NULL
--     --   AND v.var_value NOT LIKE '\%\%%' ESCAPE '\' FETCH FIRST 1 ROW ONLY;
--
--   VAR_REF              references another user %%var (Phase-B resolves)
--     -- SELECT * FROM v WHERE v.var_value LIKE '\%\%%' ESCAPE '\'
--     --   AND v.var_value NOT LIKE '\%\%$%' ESCAPE '\' FETCH FIRST 1 ROW ONLY;
--
--   SYSTEM_FUNC          system token only (CALCDATE/SUBSTR/ODATE...)   ** REFINE **
--     -- SELECT * FROM v WHERE v.var_value LIKE '\%\%$CALCDATE%' ESCAPE '\'
--     --   OR v.var_value LIKE '\%\%$ODATE%' ESCAPE '\' FETCH FIRST 1 ROW ONLY;
--
--   SEMANTIC_FACT        fact-registry name, plain value (SEAL/FID/DATAFLOW...)
--     -- SELECT * FROM v WHERE v.var_name IN ('%%SEAL','%%SEALID','%%DATAFLOW')
--     --   FETCH FIRST 1 ROW ONLY;
--
--   FLOW_REF             %%\global / %%\\pool\var cross-job shared state
--     -- SELECT * FROM v WHERE v.var_value LIKE '%\%\%\\%' ESCAPE '\'
--     --   FETCH FIRST 1 ROW ONLY;
--
--   DYNAMIC_NAME         adjacent %%refs compose a name (%%A%%B)          ** REFINE **
--     -- SELECT * FROM v WHERE v.var_value LIKE '\%\%%\%\%%' ESCAPE '\'
--     --   FETCH FIRST 1 ROW ONLY;
--
--   PLUGIN_NS_FILEWATCH  %%FileWatch-* (-> WATCH_INPUT file_ref)
--     -- SELECT * FROM v WHERE v.var_name LIKE '\%\%FileWatch-%' ESCAPE '\'
--     --   FETCH FIRST 1 ROW ONLY;
--
--   PLUGIN_NS_UCM        %%UCM-*CONTAINER_OVERRIDES (-> container command)
--     -- SELECT * FROM v WHERE v.var_name LIKE '\%\%UCM-%' ESCAPE '\'
--     --   AND UPPER(v.var_name) LIKE '%CONTAINER_OVERRIDES%' FETCH FIRST 1 ROW ONLY;
--
--   EMBEDDED_SHELL       PRECMD/POSTCMD shell text (-> invocation / file_op)
--     -- SELECT * FROM v WHERE v.var_name IN ('%%PRECMD','%%POSTCMD','%%POSCMD')
--     --   FETCH FIRST 1 ROW ONLY;
--
--   SHELL_ABINITIO       launcher: .m / dtlaunch / run_calp_temp.sh           ** REFINE **
--     -- SELECT * FROM v WHERE v.var_name IN ('%%PRECMD','%%POSTCMD')
--     --   AND (v.var_value LIKE '%.m %' OR v.var_value LIKE '%dtlaunch%')
--     --   FETCH FIRST 1 ROW ONLY;
--
--   SHELL_VALIDATION     launcher: run_data_validation.sh
--     -- SELECT * FROM v WHERE v.var_value LIKE '%run_data_validation.sh%'
--     --   FETCH FIRST 1 ROW ONLY;
--
--   NOTIFICATION         EMAIL/NOTIFY fact -> STG_NOTIFICATION (email split)
--     -- SELECT * FROM v WHERE v.var_name IN ('%%EMAIL','%%NOTIFY','%%EMAIL_LIST')
--     --   AND v.var_value LIKE '%@%' FETCH FIRST 1 ROW ONLY;
--
--   ENV_TRIPLET          _D/_Q/_P sibling (-> per-env variant expansion)     ** REFINE **
--     -- SELECT * FROM v WHERE REGEXP_LIKE(v.var_name, '_[DQP]$')
--     --   FETCH FIRST 1 ROW ONLY;   -- NB: triplet needs >=2 siblings on one job
--
--   CONCAT_DOT           %%A.%%B smuggled-dot concatenation                  ** REFINE **
--     -- SELECT * FROM v WHERE v.var_value LIKE '%.\%\%%' ESCAPE '\'
--     --   FETCH FIRST 1 ROW ONLY;
--
--   MALFORMED            empty / whitespace / invalid name token
--     -- SELECT * FROM v WHERE v.var_name IS NULL
--     --   OR NOT REGEXP_LIKE(v.var_name, '^\%\%[A-Za-z_]') FETCH FIRST 1 ROW ONLY;
--
--   FOLDER_SCOPE         smart-folder header row (folder-level inheritance)
--     -- SELECT * FROM v WHERE v.var_scope = 'FOLDER' FETCH FIRST 1 ROW ONLY;
-- =============================================================================


-- =============================================================================
-- CONSOLIDATED QUERY  —  one representative row per scenario, in one pass.
-- Run this to regenerate the coverage sample. Each branch is parenthesised so
-- its FETCH FIRST applies per-scenario, not to the whole UNION.
-- (Predicates marked ** REFINE ** above are SQL approximations of the Python
--  taxonomy — Python re-classifies precisely on ingest; verify before trusting.)
-- =============================================================================

WITH v AS (
    SELECT
        T.DATA_CENTER  AS data_center,
        V.TABLE_ID     AS folder_id,
        T.SCHED_TABLE  AS folder_name,
        V.JOB_ID       AS job_id,
        J.JOB_NAME     AS job_name,
        J.APPL_TYPE    AS appl_type,
        CASE WHEN J.JOB_NAME = T.SCHED_TABLE THEN 'FOLDER' ELSE 'JOB' END AS var_scope,
        V.NAME         AS var_name,
        V.VALUE        AS var_value
    FROM   psgmgr.CM_DEF_SETVAR_VW V
    JOIN   psgmgr.CM_DEF_VJOB  J  ON V.TABLE_ID = J.TABLE_ID AND V.JOB_ID = J.JOB_ID
    JOIN   psgmgr.CM_DEF_VTAB  T  ON J.TABLE_ID = T.TABLE_ID
    WHERE  V.IS_CURRENT_VERSION = '1'
      AND  J.IS_CURRENT_VERSION = '1'
      AND  T.USER_DAILY IS NOT NULL
)
SELECT 'SEMANTIC_FACT'       AS scenario, s.* FROM (SELECT v.* FROM v WHERE v.var_name IN ('%%SEAL','%%SEALID','%%DATAFLOW') FETCH FIRST 1 ROW ONLY) s
UNION ALL
SELECT 'FLOW_REF',           s.* FROM (SELECT v.* FROM v WHERE v.var_value LIKE '%\%\%\\%' ESCAPE '\' FETCH FIRST 1 ROW ONLY) s
UNION ALL
SELECT 'PLUGIN_NS_FILEWATCH',s.* FROM (SELECT v.* FROM v WHERE v.var_name LIKE '\%\%FileWatch-%' ESCAPE '\' FETCH FIRST 1 ROW ONLY) s
UNION ALL
SELECT 'PLUGIN_NS_UCM',      s.* FROM (SELECT v.* FROM v WHERE v.var_name LIKE '\%\%UCM-%' ESCAPE '\' AND UPPER(v.var_name) LIKE '%CONTAINER_OVERRIDES%' FETCH FIRST 1 ROW ONLY) s
UNION ALL
SELECT 'EMBEDDED_SHELL',     s.* FROM (SELECT v.* FROM v WHERE v.var_name IN ('%%PRECMD','%%POSTCMD','%%POSCMD') FETCH FIRST 1 ROW ONLY) s
UNION ALL
SELECT 'SHELL_VALIDATION',   s.* FROM (SELECT v.* FROM v WHERE v.var_value LIKE '%run_data_validation.sh%' FETCH FIRST 1 ROW ONLY) s
UNION ALL
SELECT 'SYSTEM_FUNC',        s.* FROM (SELECT v.* FROM v WHERE v.var_value LIKE '\%\%$CALCDATE%' ESCAPE '\' OR v.var_value LIKE '\%\%$ODATE%' ESCAPE '\' FETCH FIRST 1 ROW ONLY) s    -- ** REFINE **
UNION ALL
SELECT 'VAR_REF',            s.* FROM (SELECT v.* FROM v WHERE v.var_value LIKE '\%\%%' ESCAPE '\' AND v.var_value NOT LIKE '\%\%$%' ESCAPE '\' FETCH FIRST 1 ROW ONLY) s            -- ** REFINE **
UNION ALL
SELECT 'NOTIFICATION',       s.* FROM (SELECT v.* FROM v WHERE v.var_name IN ('%%EMAIL','%%NOTIFY','%%EMAIL_LIST') AND v.var_value LIKE '%@%' FETCH FIRST 1 ROW ONLY) s
UNION ALL
SELECT 'ENV_TRIPLET',        s.* FROM (SELECT v.* FROM v WHERE REGEXP_LIKE(v.var_name, '_[DQP]$') FETCH FIRST 1 ROW ONLY) s                                                          -- ** REFINE: needs >=2 siblings/job **
UNION ALL
SELECT 'CONCAT_DOT',         s.* FROM (SELECT v.* FROM v WHERE v.var_value LIKE '%.\%\%%' ESCAPE '\' FETCH FIRST 1 ROW ONLY) s                                                       -- ** REFINE **
UNION ALL
SELECT 'FOLDER_SCOPE',       s.* FROM (SELECT v.* FROM v WHERE v.var_scope = 'FOLDER' FETCH FIRST 1 ROW ONLY) s
UNION ALL
SELECT 'MALFORMED',          s.* FROM (SELECT v.* FROM v WHERE v.var_name IS NULL OR NOT REGEXP_LIKE(v.var_name, '^\%\%[A-Za-z_]') FETCH FIRST 1 ROW ONLY) s
UNION ALL
SELECT 'LITERAL',            s.* FROM (SELECT v.* FROM v WHERE v.var_value IS NOT NULL AND v.var_value NOT LIKE '\%\%%' ESCAPE '\' FETCH FIRST 1 ROW ONLY) s
;
