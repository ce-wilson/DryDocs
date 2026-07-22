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
--
-- ★ ALL PROBES RAN 2026-07-22 (internal SQL Developer session; conclusions
--   transcribed per-probe below + into the gate spec's provenance block).
--   Headline: 169,639 rows · 14 DCs · 26 COLUMNS (not the 14 observed —
--   see P0) · AVG_START_TIME is VARCHAR2(6) (P3a rewritten, ORA-01722 fix)
--   · grain (DC, SCHED_TABLE, JOB_MEM_NAME) is NOT unique (P2 → dedupe rule
--   needed, discriminator TBD) · DSN always null · full-snapshot table (P8
--   → full-replace refresh). The pilot Q0–Q5 family run also validated the
--   landing shape end to end (>24h normalization + next-day flag, 20-sample
--   arrays, folder window primitive).
-- =============================================================================

-- P0. [ANSWERED 2026-07-22] Object type + authoritative column census (the
--     missing DDL: types, lengths, nullability — decides staging column types
--     and whether the SAMPLES_* columns are VARCHAR2(4000) or CLOB).
--     ANSWER: CM_AVG_RUN is a real TABLE (VALID). 26 columns, ALL nullable —
--     the 14 observed PLUS 12 the result grid never showed:
--       CAPTURE_DATE DATE · INSTANCE_NAME VARCHAR2(20) · DATA_CENTER
--       VARCHAR2(20) · SCHED_TABLE VARCHAR2(770) · DSN VARCHAR2(44)
--       · JOB_MEM_NAME VARCHAR2(64) · NODE_GROUP VARCHAR2(128)
--       · AVG_START_TIME VARCHAR2(6) ← STRING, not number (see P3a)
--       · AVG_RUN_TIME/MIN_RUN_TIME/MAX_RUN_TIME/STD_DEV NUMBER
--       · SAMPLES_RUN_TIME/SAMPLES_START_TIME VARCHAR2(4000) (not CLOB)
--       NEW: STAT_CAL_CTM VARCHAR2(20) · STAT_CAL VARCHAR2(30)
--       · STAT_PERIOD VARCHAR2(1) · LAST_UPDATED DATE · AVG_CPU_TIME NUMBER
--       · SAMPLES_JOB_ID VARCHAR2(4000) · SAMPLES_CPU_TIME VARCHAR2(4000)
--       · AVG_AGENT_ELAPSED_TIME NUMBER · SAMPLES_AGENT_ELAPSED_TIME
--       VARCHAR2(4000) · STD_DEV_START_TIME NUMBER · AVG_ALL_START_TIME
--       VARCHAR2(6) · SAMPLES_FIRST_START_TIME VARCHAR2(4000).
--     The STAT_CAL*/STAT_PERIOD trio is the leading P2-dup discriminator
--     candidate (stat-calendar/period variants per job) — probe at build.
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

-- P1. [ANSWERED 2026-07-22] Volume + basic cardinalities.
--     ANSWER: 169,639 rows · 14 DATA_CENTERs · 1 INSTANCE_NAME ·
--     12,639 SCHED_TABLEs · 779 NODE_GROUPs.
SELECT COUNT(*)                        AS row_count,
       COUNT(DISTINCT DATA_CENTER)     AS dc_count,
       COUNT(DISTINCT INSTANCE_NAME)   AS instance_count,
       COUNT(DISTINCT SCHED_TABLE)     AS folder_count,
       COUNT(DISTINCT NODE_GROUP)      AS node_group_count
FROM   psgmgr.CM_AVG_RUN;

-- P2. [ANSWERED 2026-07-22] GRAIN CHECK — is (DATA_CENTER, SCHED_TABLE,
--     JOB_MEM_NAME) unique?
--     -CYC/-DLY twin folders each carry rows for the same job name, so
--     SCHED_TABLE must be part of the key. Rows back = a further
--     discriminator exists (INSTANCE_NAME? CAPTURE_DATE history?).
--     ANSWER: NOT unique — the first-20 sample shows dup_count 2–49
--     (agent-status folders worst at 49/39; most dups = 2). INSTANCE_NAME is
--     ruled out (constant, P2b) and CAPTURE_DATE is uniform (P8), so the
--     discriminator is among the P0-discovered columns — STAT_PERIOD /
--     STAT_CAL(_CTM) is the leading candidate. LOADER CONSEQUENCE: the P4
--     supplement loader needs a dedupe/aggregation rule before writing job
--     props — rule choice = HITL (gate residual, not decided here).
SELECT DATA_CENTER, SCHED_TABLE, JOB_MEM_NAME, COUNT(*) AS dup_count
FROM   psgmgr.CM_AVG_RUN
GROUP  BY DATA_CENTER, SCHED_TABLE, JOB_MEM_NAME
HAVING COUNT(*) > 1
FETCH  FIRST 20 ROWS ONLY;

-- P2b. [ANSWERED 2026-07-22] INSTANCE_NAME ↔ DATA_CENTER relation (sample
--      showed one instance spanning DATA_CENTERs — clarify what
--      INSTANCE_NAME identifies).
--      ANSWER: exactly ONE INSTANCE_NAME across all 14 DCs and 169,639 rows —
--      it identifies the reporting EM/CTM instance, never the data center;
--      constant, so it is neither a key part nor the P2 discriminator.
SELECT INSTANCE_NAME, COUNT(DISTINCT DATA_CENTER) AS dcs, COUNT(*) AS rows_
FROM   psgmgr.CM_AVG_RUN
GROUP  BY INSTANCE_NAME
ORDER  BY rows_ DESC;

-- P3. Value domains.
-- P3a. [ANSWERED 2026-07-22 — SQL FIXED same day] AVG_START_TIME >24h clock:
--      how far past 240000 do values run, and are they zero-padded HHMISS?
--      (Decides the normalization rule + next-day flag.)
--      BUG FIX (internal run): AVG_START_TIME is VARCHAR2(6) (P0), so the
--      original bare `>= 240000` forced an implicit string→number conversion
--      that raises ORA-01722 on any non-numeric/blank value, and MIN/MAX on
--      a string are LEXICAL, not numeric. Rewritten with
--      TO_NUMBER(... DEFAULT NULL ON CONVERSION ERROR) (Oracle 12.2+):
--      numeric min/max + a clean threshold test that never throws;
--      non_numeric_rows surfaces any value that failed to convert.
--      ANSWER: min_start −99561 (NEGATIVE values exist — sign-carrying
--      start offsets; normalization must handle a leading '-') ·
--      max_start 995959 · post_midnight_rows 113,849 of 169,639 (67%) ·
--      non_numeric_rows 1 (a single junk value — tolerate-and-report).
SELECT MIN(TO_NUMBER(AVG_START_TIME DEFAULT NULL ON CONVERSION ERROR)) AS min_start,
       MAX(TO_NUMBER(AVG_START_TIME DEFAULT NULL ON CONVERSION ERROR)) AS max_start,
       SUM(CASE WHEN TO_NUMBER(AVG_START_TIME DEFAULT NULL ON CONVERSION ERROR) >= 240000
                THEN 1 ELSE 0 END)                                     AS post_midnight_rows,
       SUM(CASE WHEN AVG_START_TIME IS NOT NULL
                 AND TO_NUMBER(AVG_START_TIME DEFAULT NULL ON CONVERSION ERROR) IS NULL
                THEN 1 ELSE 0 END)                                     AS non_numeric_rows,
       COUNT(*)                                                        AS total_rows
FROM   psgmgr.CM_AVG_RUN;

-- P3b. [ANSWERED 2026-07-22] DSN population (null in every sampled row —
--      confirm; if always null, disposition = excluded).
--      ANSWER: 0 of 169,639 non-null — always null. Disposition: EXCLUDED.
SELECT COUNT(*) AS total, COUNT(DSN) AS dsn_not_null
FROM   psgmgr.CM_AVG_RUN;

-- P3c. [ANSWERED 2026-07-22] Run-time sanity (seconds): range + the
--      FileWatcher ~240s signature.
--      ANSWER: min 0 · median 108 s · max 83,804,487 s (~2.65 YEARS — junk
--      outliers exist, e.g. never-reset counters/stuck watchers). LOADER
--      CONSEQUENCE: a sanity cap / outlier flag is needed before job props
--      are written — threshold choice = HITL (gate residual). The pilot
--      family showed the ~300 s FileWatcher signature cleanly.
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

-- P4s. [RAN 2026-07-22] Scoped smoke test — one folder family first
--      (substitute a real prefix locally; do not commit it). Cheap on both
--      sides.
--      ANSWER (pilot family, conclusions only): 76 rows · 6 folders · 46
--      distinct jobs · 1 DC · 2 node groups · 1 capture date. The pilot also
--      validated the LANDING SHAPE end to end (internal Q0–Q5 series):
--      >24h seconds-of-day normalization + next-day flags render correctly
--      per job; SAMPLES arrays uniform at 20 elements, run/start aligned
--      (0 mismatches); the folder-level maintenance-window primitive
--      (min start .. max start+run per folder) produces sane windows, and
--      each folder carries a SELF row (JOB_MEM_NAME = the folder name,
--      NODE_GROUP null, run time = the folder span) the loader must
--      separate from job rows.
-- SELECT COUNT(*) AS stats_rows,
--        SUM(CASE WHEN j.JOB_NAME IS NOT NULL THEN 1 ELSE 0 END) AS matched_to_job
-- FROM   psgmgr.CM_AVG_RUN a
-- LEFT JOIN (SELECT DISTINCT t.SCHED_TABLE, v.JOB_NAME
--            FROM   psgmgr.CM_DEF_VJOB v
--            JOIN   psgmgr.CM_DEF_VTAB t ON t.TABLE_ID = v.TABLE_ID
--            WHERE  v.IS_CURRENT_VERSION = 'Y'
--              AND  t.USER_DAILY IS NOT NULL
--              AND  t.SCHED_TABLE LIKE '<FOLDER-PREFIX>%') j
--        ON  j.SCHED_TABLE = a.SCHED_TABLE
--        AND j.JOB_NAME    = a.JOB_MEM_NAME
-- WHERE  a.SCHED_TABLE LIKE '<FOLDER-PREFIX>%';

-- P4a. [ANSWERED 2026-07-22] Estate-wide, stats → jobs direction.
--      ANSWER: 145,454 of 169,639 stats rows match a current-version active
--      job = 85.7% (ran in ~1 s — the CM_HIST_VW-style performance fear did
--      not materialize). The unmatched ~14% ≈ retired/renamed jobs + the
--      folder SELF rows (P4s).
SELECT COUNT(*) AS stats_rows,
       SUM(CASE WHEN j.JOB_NAME IS NOT NULL THEN 1 ELSE 0 END) AS matched_to_job
FROM   psgmgr.CM_AVG_RUN a
LEFT JOIN (SELECT DISTINCT t.SCHED_TABLE, v.JOB_NAME
           FROM   psgmgr.CM_DEF_VJOB v
           JOIN   psgmgr.CM_DEF_VTAB t ON t.TABLE_ID = v.TABLE_ID
           WHERE  v.IS_CURRENT_VERSION = 'Y'
             AND  t.USER_DAILY IS NOT NULL) j
       ON  j.SCHED_TABLE = a.SCHED_TABLE
       AND j.JOB_NAME    = a.JOB_MEM_NAME;

-- P4b. [ANSWERED 2026-07-22] Estate-wide, jobs → stats direction.
--      ANSWER: 144,827 of 489,096 active jobs have stats = 29.6% — most
--      active job definitions have no recent-run stats row (expected: stats
--      exist only for jobs that actually ran in the sampling window). The
--      supplement is therefore a PARTIAL enrichment by construction; the
--      gate's coverage expectation should be ~30%, not ~100%.
SELECT COUNT(*) AS active_jobs,
       SUM(CASE WHEN a.JOB_MEM_NAME IS NOT NULL THEN 1 ELSE 0 END) AS jobs_with_stats
FROM  (SELECT DISTINCT t.SCHED_TABLE, v.JOB_NAME
       FROM   psgmgr.CM_DEF_VJOB v
       JOIN   psgmgr.CM_DEF_VTAB t ON t.TABLE_ID = v.TABLE_ID
       WHERE  v.IS_CURRENT_VERSION = 'Y'
         AND  t.USER_DAILY IS NOT NULL) j
LEFT JOIN (SELECT DISTINCT SCHED_TABLE, JOB_MEM_NAME FROM psgmgr.CM_AVG_RUN) a
       ON  a.SCHED_TABLE  = j.SCHED_TABLE
       AND a.JOB_MEM_NAME = j.JOB_NAME;

-- P5. [ANSWERED 2026-07-22] NODE_GROUP cross-validation vs CM_HOSTS (the
--     topology gate's runtime counterpart): does every NODE_GROUP value match
--     a GRPNAME, a NODEID (hard-coded host case), or neither?
--     ANSWER: GROUP 131,960 (77.8%) · UNMATCHED 25,150 (14.8%) · NULL 11,048
--     (6.5%) · DIRECT_HOST 1,481 (0.9%). Group-match dominates, direct-host
--     is real-but-rare — both consistent with the hosts gate's group-wins
--     resolution rule; the ~15% UNMATCHED is the coverage number the P3
--     hosts loader must REPORT (never guess). NOTE: this is the RUNTIME-side
--     census only — the CM_HOSTS definition-side probes (grain, P4
--     BOTH-collisions, case-fold) are still owed.
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

-- P6. [ANSWERED 2026-07-22] DATA_CENTER domain vs the other two objects
--     (should be the long form everywhere — confirms the exact-long-form
--     ControlMServer key rule).
--     ANSWER: MINUS returned 0 rows — every CM_AVG_RUN DATA_CENTER exists in
--     CM_DEF_VTAB (long-form key rule confirmed). CM_AVG_RUN spans 14 DCs
--     (vs 22 in CM_HOSTS, 4 production) — a third scope datapoint for the
--     still-open DC scope call.
SELECT DATA_CENTER FROM psgmgr.CM_AVG_RUN
MINUS
SELECT DATA_CENTER FROM psgmgr.CM_DEF_VTAB;

-- P7. [ANSWERED 2026-07-22] SAMPLES_* parseability: array lengths + format
--     spot-check. SAMPLES_RUN_TIME = comma list of seconds;
--     SAMPLES_START_TIME = comma list of <ts>:<odate> pairs. Compare element
--     counts between the two (should match per row) and eyeball a few (do
--     not commit values).
--     ANSWER: array lengths 1..20 estate-wide (20 = the full window; short
--     arrays = young/rarely-run jobs); run/start element counts match on
--     EVERY row (0 mismatches). Day-of-week median derivation is safe.
SELECT MIN(REGEXP_COUNT(SAMPLES_RUN_TIME, ',') + 1)   AS min_rt_samples,
       MAX(REGEXP_COUNT(SAMPLES_RUN_TIME, ',') + 1)   AS max_rt_samples,
       MIN(REGEXP_COUNT(SAMPLES_START_TIME, ',') + 1) AS min_st_samples,
       MAX(REGEXP_COUNT(SAMPLES_START_TIME, ',') + 1) AS max_st_samples,
       SUM(CASE WHEN REGEXP_COUNT(SAMPLES_RUN_TIME, ',')
                  <> REGEXP_COUNT(SAMPLES_START_TIME, ',')
                THEN 1 ELSE 0 END)                    AS mismatched_rows
FROM   psgmgr.CM_AVG_RUN;

-- P8. [ANSWERED 2026-07-22] Is CAPTURE_DATE uniform per snapshot, or does the
--     table keep history? (Decides refresh strategy: full-replace vs windowed.)
--     ANSWER: 1 distinct CAPTURE_DATE (min = max = the snapshot date) — a
--     full snapshot with no history. Refresh strategy: FULL-REPLACE.
SELECT COUNT(DISTINCT CAPTURE_DATE) AS distinct_caps,
       MIN(CAPTURE_DATE) AS min_cap, MAX(CAPTURE_DATE) AS max_cap
FROM   psgmgr.CM_AVG_RUN;
