-- =============================================================================
-- profile_cm_avg_run.sql  —  run internally in SQL Developer against psgmgr
--
-- Profiles psgmgr.CM_AVG_RUN — the runtime-statistics table feeding the
-- planned temporal runtime supplement (avg/median start+run times onto
-- ControlMJob properties; folder-level windows derived). Name VERIFIED live
-- (SME query 2026-07-07 / 2026-07-09). 14 columns observed in the result
-- grid — data TYPES are unknown (no DDL seen yet; P0 fixes that):
--   CAPTURE_DATE · INSTANCE_NAME · DATA_CENTER · SCHED_TABLE · DSN
--   · JOB_MEM_NAME · NODE_GROUP · AVG_START_TIME · AVG_RUN_TIME
--   · MIN_RUN_TIME · MAX_RUN_TIME · STD_DEV · SAMPLES_RUN_TIME
--   · SAMPLES_START_TIME
--
-- Known semantics going in (SME, 2026-07-07):
--   * JOB_MEM_NAME = CM_DEF_VJOB.JOB_NAME (join SCHED_TABLE + JOB_NAME);
--     MEMNAME is never a join key.
--   * AVG_START_TIME uses the Control-M >24h post-midnight clock
--     (e.g. 293502 ≈ 05:35:02 next day) — needs normalization.
--   * Run times in seconds; FileWatcher "run time" = watch/wait duration
--     (~240s cycles), not processing time.
--   * SAMPLES_* are raw per-run arrays (~20 runs; start samples carry :odate)
--     — day-of-week medians computable without CM_HIST.
--
-- Probes feed the controlm-avg-run-supplement gate
-- (config/gate-prompts/controlm-avg-run-supplement.yaml). Read-only. Do NOT
-- commit result rows (real folder/job/group names) — conclusions only.
-- =============================================================================

-- P0. Object type + authoritative column census (the missing DDL: types,
--     lengths, nullability — decides staging column types and whether the
--     SAMPLES_* columns are VARCHAR2(4000) or CLOB).
SELECT object_name, object_type, status
FROM   all_objects
WHERE  owner = 'PSGMGR' AND object_name = 'CM_AVG_RUN';

SELECT column_id, column_name,
       data_type ||
         CASE WHEN data_type IN ('VARCHAR2','NVARCHAR2','CHAR')
              THEN '(' || data_length || ')'
              WHEN data_type = 'NUMBER' AND data_precision IS NOT NULL
              THEN '(' || data_precision ||
                   CASE WHEN data_scale > 0 THEN ',' || data_scale END || ')'
              END AS full_type,
       nullable
FROM   all_tab_columns
WHERE  owner = 'PSGMGR' AND table_name = 'CM_AVG_RUN'
ORDER  BY column_id;

-- P1. Volume + basic cardinalities.
SELECT COUNT(*)                        AS row_count,
       COUNT(DISTINCT DATA_CENTER)     AS dc_count,
       COUNT(DISTINCT INSTANCE_NAME)   AS instance_count,
       COUNT(DISTINCT SCHED_TABLE)     AS folder_count,
       COUNT(DISTINCT NODE_GROUP)      AS node_group_count
FROM   psgmgr.CM_AVG_RUN;

-- P2. GRAIN CHECK — is (DATA_CENTER, SCHED_TABLE, JOB_MEM_NAME) unique?
--     -CYC/-DLY twin folders each carry rows for the same job name, so
--     SCHED_TABLE must be part of the key. Rows back = a further
--     discriminator exists (INSTANCE_NAME? CAPTURE_DATE history?).
SELECT DATA_CENTER, SCHED_TABLE, JOB_MEM_NAME, COUNT(*) AS dup_count
FROM   psgmgr.CM_AVG_RUN
GROUP  BY DATA_CENTER, SCHED_TABLE, JOB_MEM_NAME
HAVING COUNT(*) > 1
FETCH  FIRST 20 ROWS ONLY;

-- P2b. INSTANCE_NAME ↔ DATA_CENTER relation (sample showed instance P013CONT
--      under DATA_CENTER P032-… — clarify what INSTANCE_NAME identifies).
SELECT INSTANCE_NAME, COUNT(DISTINCT DATA_CENTER) AS dcs, COUNT(*) AS rows_
FROM   psgmgr.CM_AVG_RUN
GROUP  BY INSTANCE_NAME
ORDER  BY rows_ DESC;

-- P3. Value domains.
-- P3a. AVG_START_TIME >24h clock: how far past 240000 do values run, and are
--      they zero-padded HHMISS? (Decides the normalization rule + next-day flag.)
SELECT MIN(AVG_START_TIME) AS min_start, MAX(AVG_START_TIME) AS max_start,
       SUM(CASE WHEN AVG_START_TIME >= 240000 THEN 1 ELSE 0 END) AS post_midnight_rows,
       COUNT(*) AS total_rows
FROM   psgmgr.CM_AVG_RUN;

-- P3b. DSN population (null in every sampled row — confirm; if always null,
--      disposition = excluded).
SELECT COUNT(*) AS total, COUNT(DSN) AS dsn_not_null
FROM   psgmgr.CM_AVG_RUN;

-- P3c. Run-time sanity (seconds): range + the FileWatcher ~240s signature.
SELECT MIN(AVG_RUN_TIME) AS min_avg, MEDIAN(AVG_RUN_TIME) AS median_avg,
       MAX(AVG_RUN_TIME) AS max_avg
FROM   psgmgr.CM_AVG_RUN;

-- P4. JOIN COVERAGE — the supplement's landing join: (SCHED_TABLE,
--     JOB_MEM_NAME) → current-version active jobs (SCHED_TABLE + JOB_NAME).
--     Measures what fraction of stats rows land on a job node, and what
--     fraction of active jobs get stats (both directions matter for the
--     gate's coverage expectations).
--
--     PERFORMANCE NOTE: this is the ONLY Oracle join in the CM_AVG_RUN
--     package (the extract is a plain projection; the loader's job match
--     runs graph-side). The VJOB⨝VTAB subquery walks ~240K+ current-version
--     rows on a versioned view — CM_HIST_VW caution applies. Run P4s (the
--     scoped smoke test) FIRST; check the plan (EXPLAIN PLAN / autotrace)
--     and set a bounded call timeout before the estate-wide P4a/P4b. If
--     estate-wide is slow, run per DATA_CENTER instead.

-- P4s. Scoped smoke test — one folder family first (substitute a real
--      prefix locally; do not commit it). Cheap on both sides.
-- SELECT COUNT(*) AS stats_rows,
--        SUM(CASE WHEN j.JOB_NAME IS NOT NULL THEN 1 ELSE 0 END) AS matched_to_job
-- FROM   psgmgr.CM_AVG_RUN a
-- LEFT JOIN (SELECT DISTINCT t.SCHED_TABLE, v.JOB_NAME
--            FROM   psgmgr.CM_DEF_VJOB v
--            JOIN   psgmgr.CM_DEF_VTAB t ON t.TABLE_ID = v.TABLE_ID
--            WHERE  v.IS_CURRENT_VERSION = '1'
--              AND  t.USER_DAILY IS NOT NULL
--              AND  t.SCHED_TABLE LIKE '<FOLDER-PREFIX>%') j
--        ON  j.SCHED_TABLE = a.SCHED_TABLE
--        AND j.JOB_NAME    = a.JOB_MEM_NAME
-- WHERE  a.SCHED_TABLE LIKE '<FOLDER-PREFIX>%';

-- P4a. Estate-wide, stats → jobs direction.
SELECT COUNT(*) AS stats_rows,
       SUM(CASE WHEN j.JOB_NAME IS NOT NULL THEN 1 ELSE 0 END) AS matched_to_job
FROM   psgmgr.CM_AVG_RUN a
LEFT JOIN (SELECT DISTINCT t.SCHED_TABLE, v.JOB_NAME
           FROM   psgmgr.CM_DEF_VJOB v
           JOIN   psgmgr.CM_DEF_VTAB t ON t.TABLE_ID = v.TABLE_ID
           WHERE  v.IS_CURRENT_VERSION = '1'
             AND  t.USER_DAILY IS NOT NULL) j
       ON  j.SCHED_TABLE = a.SCHED_TABLE
       AND j.JOB_NAME    = a.JOB_MEM_NAME;

-- P4b. Estate-wide, jobs → stats direction.
SELECT COUNT(*) AS active_jobs,
       SUM(CASE WHEN a.JOB_MEM_NAME IS NOT NULL THEN 1 ELSE 0 END) AS jobs_with_stats
FROM  (SELECT DISTINCT t.SCHED_TABLE, v.JOB_NAME
       FROM   psgmgr.CM_DEF_VJOB v
       JOIN   psgmgr.CM_DEF_VTAB t ON t.TABLE_ID = v.TABLE_ID
       WHERE  v.IS_CURRENT_VERSION = '1'
         AND  t.USER_DAILY IS NOT NULL) j
LEFT JOIN (SELECT DISTINCT SCHED_TABLE, JOB_MEM_NAME FROM psgmgr.CM_AVG_RUN) a
       ON  a.SCHED_TABLE  = j.SCHED_TABLE
       AND a.JOB_MEM_NAME = j.JOB_NAME;

-- P5. NODE_GROUP cross-validation vs CM_HOSTS (the topology gate's runtime
--     counterpart): does every NODE_GROUP value match a GRPNAME, a NODEID
--     (hard-coded host case), or neither?
SELECT CASE
         WHEN a.NODE_GROUP IS NULL THEN 'NULL'
         WHEN g.GRPNAME IS NOT NULL THEN 'GROUP'
         WHEN n.NODEID  IS NOT NULL THEN 'DIRECT_HOST'
         ELSE 'UNMATCHED'
       END      AS node_group_resolution,
       COUNT(*) AS rows_
FROM   psgmgr.CM_AVG_RUN a
LEFT JOIN (SELECT DISTINCT GRPNAME FROM psgmgr.CM_HOSTS) g ON g.GRPNAME = a.NODE_GROUP
LEFT JOIN (SELECT DISTINCT NODEID  FROM psgmgr.CM_HOSTS) n ON n.NODEID  = a.NODE_GROUP
GROUP  BY CASE
            WHEN a.NODE_GROUP IS NULL THEN 'NULL'
            WHEN g.GRPNAME IS NOT NULL THEN 'GROUP'
            WHEN n.NODEID  IS NOT NULL THEN 'DIRECT_HOST'
            ELSE 'UNMATCHED'
          END
ORDER  BY rows_ DESC;

-- P6. DATA_CENTER domain vs the other two objects (should be the long form
--     everywhere — confirms the exact-long-form ControlMServer key rule).
SELECT DATA_CENTER FROM psgmgr.CM_AVG_RUN
MINUS
SELECT DATA_CENTER FROM psgmgr.CM_DEF_VTAB;

-- P7. SAMPLES_* parseability: array lengths + format spot-check.
--     SAMPLES_RUN_TIME = comma list of seconds; SAMPLES_START_TIME = comma
--     list of <ts>:<odate> pairs. Compare element counts between the two
--     (should match per row) and eyeball a few (do not commit values).
SELECT MIN(REGEXP_COUNT(SAMPLES_RUN_TIME, ',') + 1)   AS min_rt_samples,
       MAX(REGEXP_COUNT(SAMPLES_RUN_TIME, ',') + 1)   AS max_rt_samples,
       MIN(REGEXP_COUNT(SAMPLES_START_TIME, ',') + 1) AS min_st_samples,
       MAX(REGEXP_COUNT(SAMPLES_START_TIME, ',') + 1) AS max_st_samples,
       SUM(CASE WHEN REGEXP_COUNT(SAMPLES_RUN_TIME, ',')
                  <> REGEXP_COUNT(SAMPLES_START_TIME, ',')
                THEN 1 ELSE 0 END)                    AS mismatched_rows
FROM   psgmgr.CM_AVG_RUN;

-- P8. Is CAPTURE_DATE uniform per snapshot, or does the table keep history?
--     (Decides refresh strategy: full-replace vs windowed.)
SELECT COUNT(DISTINCT CAPTURE_DATE) AS distinct_caps,
       MIN(CAPTURE_DATE) AS min_cap, MAX(CAPTURE_DATE) AS max_cap
FROM   psgmgr.CM_AVG_RUN;
