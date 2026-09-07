-- =============================================================================
-- probe_dc_table_id_collision.sql  —  run internally in SQL Developer against psgmgr
--
-- P6: does one Control-M folder id (TABLE_ID) appear in more than one data
-- center? The graph keys :ControlMFolder by folder_id ALONE
-- (drydocs_core/schema/constraints.cypher, controlmfolder_id) and :ControlMJob
-- by (folder_id, job_id); the staging DDL keys defensively by
-- (DATA_CENTER, TABLE_ID) — controlm_staging_ddl.sql section 0.1 asks this
-- same question and was never answered on record. If a table id is reused
-- across data centers, two different folders merge into ONE graph node the
-- first time more than one data center is loaded, and every job under the
-- second folder lands on the first. The single-data-center pilot cannot
-- expose this; a multi-data-center load must not run until it is answered.
--
-- Counts only, never result rows (the producer side has no psgmgr access —
-- user-run on the internal network, agent transcribes the conclusion; P1's
-- arrangement). Read-only. Record the outcome in the P6 item file:
--   ZERO ROWS from P6.1 → the invariant is documented beside the constraint
--     (P6 clause b), naming this probe and the date it was run.
--   ANY ROWS  → an IDENTITY change is owed (data center joins the folder and
--     job keys); that is a constraint migration and it routes through the HITL
--     gate (P6 clause c). Nothing about identity is decided by this probe.
-- =============================================================================

-- P6.0  Population: how many data centers, how many folder rows, how many
--       distinct table ids. Sets the denominator for P6.1 and confirms the
--       probe actually saw more than one data center (a one-data-center
--       replica returns zero from P6.1 trivially and proves nothing).
SELECT COUNT(DISTINCT DATA_CENTER) AS data_centers,
       COUNT(*)                    AS folder_rows,
       COUNT(DISTINCT TABLE_ID)    AS distinct_table_ids
FROM   psgmgr.CM_DEF_VTAB;

-- P6.1  THE PROBE. Table ids that appear in more than one data center.
--       Aggregated one level further than DDL section 0.1 so the answer is a
--       single row of counts and no folder id is ever written down:
--       colliding_table_ids = 0  →  zero rows outcome
--       colliding_table_ids > 0  →  any rows outcome; max_dc_per_id says how
--                                   wide the worst collision is.
SELECT COUNT(*)          AS colliding_table_ids,
       NVL(MAX(dc_count), 0) AS max_dc_per_id
FROM  (SELECT TABLE_ID, COUNT(DISTINCT DATA_CENTER) AS dc_count
       FROM   psgmgr.CM_DEF_VTAB
       GROUP  BY TABLE_ID
       HAVING COUNT(DISTINCT DATA_CENTER) > 1);

-- P6.2  Only if P6.1 > 0: are the colliding ids the SAME folder replicated
--       (same SCHED_TABLE name in every data center — a mirror, identity is
--       arguably one folder) or DIFFERENT folders sharing a number (distinct
--       names — two folders, one node)? The gate prompt needs this split.
--       Still counts only.
SELECT SUM(CASE WHEN names = 1 THEN 1 ELSE 0 END) AS same_name_mirrors,
       SUM(CASE WHEN names > 1 THEN 1 ELSE 0 END) AS different_folders
FROM  (SELECT TABLE_ID,
              COUNT(DISTINCT DATA_CENTER) AS dc_count,
              COUNT(DISTINCT SCHED_TABLE) AS names
       FROM   psgmgr.CM_DEF_VTAB
       GROUP  BY TABLE_ID
       HAVING COUNT(DISTINCT DATA_CENTER) > 1);

-- P6.3  Only if P6.1 > 0: how many JOBS sit under a colliding folder id —
--       the blast radius of the merge, i.e. how many :ControlMJob nodes would
--       be mis-parented on a multi-data-center load. Counts only.
SELECT COUNT(*) AS jobs_under_colliding_ids
FROM   psgmgr.CM_DEF_VJOB J
WHERE  J.TABLE_ID IN (SELECT TABLE_ID
                      FROM   psgmgr.CM_DEF_VTAB
                      GROUP  BY TABLE_ID
                      HAVING COUNT(DISTINCT DATA_CENTER) > 1);
