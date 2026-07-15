-- =============================================================================
-- preflight_open_questions.sql  —  run in SQL Developer against psgmgr
--
-- Answers the open questions gating feature/oracle-ingestion
-- (persona-oracle-dba.md §1.7 + controlm_staging_ddl.sql §0). Read-only probes.
-- Do NOT commit their result rows — record conclusions in the feature plan.
-- =============================================================================

-- Q1. [RESOLVED 2026-07-10] The variable object is psgmgr.CM_DEF_SETVAR_VW —
--     confirmed against live psgmgr: a valid view carrying TABLE_ID/JOB_ID/NAME/
--     VALUE plus its own IS_CURRENT_VERSION/VERSION_SERIAL. The probe below found
--     it by matching the delivered extract shape.
SELECT table_name, COUNT(*) AS matched_cols
FROM   all_tab_columns
WHERE  owner = 'PSGMGR'
  AND  column_name IN ('NAME','VALUE','JOB_ID','APPL_TYPE')
GROUP  BY table_name
HAVING COUNT(*) >= 4
ORDER  BY table_name;

-- Q2. Is CAPTURE_DATE a per-row change signal or one per-snapshot value? If
--     distinct_caps = 1 it is uniform (use VERSION_SERIAL / hash for change
--     detection instead).
SELECT COUNT(DISTINCT CAPTURE_DATE) AS distinct_caps,
       MIN(CAPTURE_DATE)            AS min_cap,
       MAX(CAPTURE_DATE)            AS max_cap
FROM   psgmgr.CM_DEF_VJOB;

-- Q3. Do the developer-SID columns exist on CM_DEF_VJOB?
SELECT column_name
FROM   all_tab_columns
WHERE  owner = 'PSGMGR' AND table_name = 'CM_DEF_VJOB'
  AND  column_name IN ('AUTHOR','CREATION_USER','CHANGE_USERID','VERSION_USER','OWNER')
ORDER  BY column_name;

-- Q0.1 (DDL pre-flight). Does TABLE_ID collide across data centers? Rows back =
--     (DATA_CENTER, TABLE_ID) is the true key (staging already assumes this).
SELECT TABLE_ID, COUNT(DISTINCT DATA_CENTER) AS dc_count
FROM   psgmgr.CM_DEF_VTAB
GROUP  BY TABLE_ID
HAVING COUNT(DISTINCT DATA_CENTER) > 1
FETCH  FIRST 20 ROWS ONLY;

-- Q0.2 (DDL pre-flight). Are MEMLIB / OVERLIB present (script-library paths)?
SELECT column_name
FROM   all_tab_columns
WHERE  owner = 'PSGMGR' AND table_name = 'CM_DEF_VJOB'
  AND  column_name IN ('MEMLIB','OVERLIB','APPL_TYPE')
ORDER  BY column_name;

-- Q4. Spot-check the developer-SID convention (lowercase initial; trailing 'p'
--     = automation release). Eyeball only — do NOT commit these values.
SELECT AUTHOR,
       CASE WHEN AUTHOR LIKE '%p' THEN 'Y' ELSE 'N' END AS looks_automation
FROM   psgmgr.CM_DEF_VJOB
WHERE  IS_CURRENT_VERSION = 'Y' AND AUTHOR IS NOT NULL
FETCH  FIRST 50 ROWS ONLY;
