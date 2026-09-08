-- =============================================================================
-- controlm_dependencies_recursive.sql
--
-- BMC Control-M DIRECT predecessor pairs.  **Walks BACKWARDS one level** —
-- for each job, finds its immediate predecessors by matching its IN
-- conditions to upstream OUT conditions.
--
-- DIRECT EDGES ONLY (phased-loader change, ported from the company repo
-- 2026-07-23; file name kept for loader/porting continuity): the recursive
-- CTE is gone. Transitive reach is a graph TRAVERSAL in Neo4j
-- (variable-length :WAS_INFORMED_BY patterns), not a stored closure —
-- the old level/path columns duplicated what the graph already answers.
--
-- Source views (all psgmgr):
--   CM_DEF_VJOB, CM_DEF_VTAB, CM_DEF_LNKI_P_VW, CM_DEF_LNKO_P_VW
--
-- Output rows are pure ctlm_id composites (folder_id.job_id — the
-- (folder_id, job_id) NODE KEY in composite form; P2 gate §B, 2026-07-14)
-- plus the linking condition. The Neo4j loader resolves both endpoints by
-- splitting on '.'.
--
-- Design notes preserved from the canonical version:
--   1. Cyclic-type matching (CYCLIC_IN = CYCLIC_OUT) is intentionally
--      DISABLED — kept commented to preserve the canonical intent.
--      WHY IT STAYS DISABLED (2026-09-02): CYCLIC_TYPE is the vendor's CYCLE TYPE
--      (INTERVAL / INTERVAL_SEQUENCE / SPECIFIC_TIMES — ctmdeffolder Parameter
--      Reference, GROUNDED), not an is-cyclic flag; that flag is CYCLIC (Y/N). A
--      company-side census found the letter C concentrated on the *_DLY folders
--      and S on the *_CYC folders, so equality here would split DAILY jobs by how
--      their cycles are measured and drop real dependencies. Test case:
--      .claude/skills/research-probe-discipline/evals/files/cyclic-type-trap.md
--   2. Self-references (a job feeding itself across DLY/CYC twins with the
--      same JOB_NAME) are excluded, as in the canonical anchor member.
--
-- Scope binds (optional, NULL = no filter; they scope the SUCCESSOR side
-- only — the predecessor side is ALWAYS unscoped, so rows can reference
-- jobs in OTHER folders):
--   :folder_filter  successor folder-name LIKE pattern (e.g.
--                   'PRARAG-HLDM-70002-PEX-RFND-DLY' or 'CCB_AUTO_%')
--   :run_as         successor job tenant FID (service) user — OWNER, exact
--   :developer_sid  successor authoring developer SID — AUTHOR /
--                   CREATION_USER / CHANGE_USERID (lowercase-initial;
--                   trailing 'p' = automation release process)
--   :row_cap        unordered sample cap (ROWNUM) on the final result
--
-- BECAUSE the predecessor side is unscoped, this extract's loader runs in
-- the deferred `ingest-controlm --phase relationships` pass: once,
-- UNSCOPED, after ALL nodes are loaded. Running it per-folder is what
-- silently dropped cross-folder edges (the second endpoint's MATCH missed)
-- — the reason --phase exists.
-- (Operational who-ran-it identity is separate — psgmgr.CM_AUD_ACTS, later.)
-- =============================================================================

SELECT
    J_SUB.IN_PARENT_TABLE_ID || '.' || J_SUB.IN_JOB_ID_STR             AS in_table_job_id,
    J_SUB.IN_CONDITION                                                 AS out_condition,
    D_SUB.PREDECESSOR_TABLE_ID || '.' || D_SUB.PREDECESSOR_JOB_ID_STR  AS out_table_job_id
FROM (
    SELECT DISTINCT
        LNKI.CONDITION         AS IN_CONDITION,
        JOB_DEF.TABLE_ID       AS IN_PARENT_TABLE_ID,
        JOB_DEF.JOB_NAME       AS IN_JOB_NAME,
        JOB_DEF.JOB_ID         AS IN_JOB_ID_STR,
        JOB_DEF.CYCLIC_TYPE    AS JOB_CYCLIC_IN
    FROM   psgmgr.CM_DEF_VJOB JOB_DEF
    JOIN   psgmgr.CM_DEF_VTAB TAB_DEF
             ON JOB_DEF.TABLE_ID = TAB_DEF.TABLE_ID
    JOIN   psgmgr.CM_DEF_LNKI_P_VW LNKI
             ON  JOB_DEF.TABLE_ID       = LNKI.TABLE_ID
             AND JOB_DEF.JOB_ID         = LNKI.JOB_ID
             AND JOB_DEF.VERSION_SERIAL = LNKI.VERSION_SERIAL
    WHERE  TAB_DEF.USER_DAILY IS NOT NULL
      -- optional scope on the successor set (NULL bind = no filter)
      AND  (:folder_filter IS NULL OR JOB_DEF.PARENT_TABLE LIKE :folder_filter)
      AND  (:run_as        IS NULL OR JOB_DEF.OWNER        =  :run_as)   -- tenant FID user
      AND  (:developer_sid IS NULL OR :developer_sid IN (JOB_DEF.AUTHOR, JOB_DEF.CREATION_USER, JOB_DEF.CHANGE_USERID))
) J_SUB
JOIN (
    SELECT DISTINCT
        LNKO.CONDITION         AS OUT_CONDITION,
        JOB_DEF.TABLE_ID       AS PREDECESSOR_TABLE_ID,
        JOB_DEF.JOB_NAME       AS PREDECESSOR_JOB_NAME,
        JOB_DEF.JOB_ID         AS PREDECESSOR_JOB_ID_STR,
        JOB_DEF.CYCLIC_TYPE    AS JOB_CYCLIC_OUT
    FROM   psgmgr.CM_DEF_VJOB JOB_DEF
    JOIN   psgmgr.CM_DEF_VTAB TAB_DEF
             ON JOB_DEF.TABLE_ID = TAB_DEF.TABLE_ID
    JOIN   psgmgr.CM_DEF_LNKO_P_VW LNKO
             ON  JOB_DEF.TABLE_ID       = LNKO.TABLE_ID
             AND JOB_DEF.JOB_ID         = LNKO.JOB_ID
             AND JOB_DEF.VERSION_SERIAL = LNKO.VERSION_SERIAL
    WHERE  TAB_DEF.USER_DAILY IS NOT NULL
) D_SUB
  ON  J_SUB.IN_CONDITION = D_SUB.OUT_CONDITION
  -- AND J_SUB.JOB_CYCLIC_IN = D_SUB.JOB_CYCLIC_OUT  -- intentionally disabled
WHERE J_SUB.IN_JOB_NAME <> D_SUB.PREDECESSOR_JOB_NAME
  AND (:row_cap IS NULL OR ROWNUM <= :row_cap)   -- optional unordered sample cap
;
