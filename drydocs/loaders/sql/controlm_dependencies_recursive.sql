-- =============================================================================
-- controlm_dependencies_recursive.sql
--
-- BMC Control-M recursive predecessor search.  **Walks BACKWARDS** —
-- starting from a job, finds its predecessors by matching IN conditions
-- to upstream OUT conditions, then recursing.
--
-- Source views (all psgmgr):
--   CM_DEF_VJOB, CM_DEF_VTAB, CM_DEF_LNKI_P_VW, CM_DEF_LNKO_P_VW
--
-- Design notes from the canonical version:
--   1. Anchor member scopes to a specific folder (PARENT_TABLE) via
--      :folder_filter; recursion walks across folder boundaries from
--      there.
--   2. Cyclic-type matching (CYCLIC_IN = CYCLIC_OUT) is intentionally
--      DISABLED — kept commented to preserve the canonical intent.
--   3. Cycle detection is by full-path INSTR check, not by visited-set
--      label. Sufficient because dependency_path is deterministic at
--      each level.
--   4. Recursion limit: 10 inside the CTE (anchor + recursion levels);
--      30 in the final SELECT (safety belt for the consumer).
--   5. Each output row has TABLE_JOB_ID composites (folder_id.job_id)
--      that the Neo4j loader uses as a stable key for the derived
--      :DEPENDS_ON edges.
--
-- Bind variable:
--   :folder_filter   one-or-many folder names to anchor the recursion.
--                    Use Oracle list-IN-binding syntax or pre-expand
--                    the list in application code. Example:
--                       'PRARAG-HLDM-111027-PEX-RFND-DLY'
--                    Replace with '%' or expand to all folders to derive
--                    dependencies across the full estate.
-- =============================================================================

WITH RecursiveJobDependencies (
    SUCCESSOR_PARENT_TABLE,
    SUCCESSOR_JOB_NAME,
    SUCCESSOR_PARENT_TABLE_ID,
    SUCCESSOR_JOB_ID,
    depends_on_literal,
    MATCHING_CONDITION,
    PREDECESSOR_PARENT_TABLE,
    PREDECESSOR_JOB_NAME,
    PREDECESSOR_PARENT_TABLE_ID,
    PREDECESSOR_JOB_ID_INTERNAL,
    recursion_level,
    dependency_path
) AS (
    -- =========================================================================
    -- ANCHOR MEMBER
    -- =========================================================================
    SELECT
        J_SUB.IN_PARENT_TABLE,
        J_SUB.IN_JOB_NAME,
        J_SUB.IN_PARENT_TABLE_ID,
        J_SUB.IN_JOB_ID_STR,
        ':depends_on'                              AS depends_on_literal,
        J_SUB.IN_CONDITION                         AS MATCHING_CONDITION,
        D_SUB.PREDECESSOR_TABLE                    AS PREDECESSOR_PARENT_TABLE,
        D_SUB.PREDECESSOR_JOB_NAME                 AS PREDECESSOR_JOB_NAME,
        D_SUB.PREDECESSOR_TABLE_ID                 AS PREDECESSOR_PARENT_TABLE_ID,
        D_SUB.PREDECESSOR_JOB_ID_STR               AS PREDECESSOR_JOB_ID_INTERNAL,
        1                                          AS recursion_level,
        J_SUB.IN_JOB_NAME || ' -> ' || D_SUB.PREDECESSOR_JOB_NAME  AS dependency_path
    FROM (
        SELECT DISTINCT
            LNKI.CONDITION         AS IN_CONDITION,
            JOB_DEF.PARENT_TABLE   AS IN_PARENT_TABLE,
            JOB_DEF.TABLE_ID       AS IN_PARENT_TABLE_ID,
            JOB_DEF.JOB_NAME       AS IN_JOB_NAME,
            JOB_DEF.JOB_ID         AS IN_JOB_ID_STR,
            JOB_DEF.CYCLIC_TYPE    AS JOB_CYCLIC_IN,
            JOB_DEF.VERSION_SERIAL AS JOB_VERSION_SERIAL
        FROM   psgmgr.CM_DEF_VJOB JOB_DEF
        JOIN   psgmgr.CM_DEF_VTAB TAB_DEF
                 ON JOB_DEF.TABLE_ID = TAB_DEF.TABLE_ID
        JOIN   psgmgr.CM_DEF_LNKI_P_VW LNKI
                 ON  JOB_DEF.TABLE_ID       = LNKI.TABLE_ID
                 AND JOB_DEF.JOB_ID         = LNKI.JOB_ID
                 AND JOB_DEF.VERSION_SERIAL = LNKI.VERSION_SERIAL
        WHERE  TAB_DEF.USER_DAILY IS NOT NULL
          AND  JOB_DEF.PARENT_TABLE IN (:folder_filter)
    ) J_SUB
    JOIN (
        SELECT DISTINCT
            LNKO.CONDITION         AS OUT_CONDITION,
            JOB_DEF.PARENT_TABLE   AS PREDECESSOR_TABLE,
            JOB_DEF.TABLE_ID       AS PREDECESSOR_TABLE_ID,
            JOB_DEF.JOB_NAME       AS PREDECESSOR_JOB_NAME,
            JOB_DEF.JOB_ID         AS PREDECESSOR_JOB_ID_STR,
            JOB_DEF.CYCLIC_TYPE    AS JOB_CYCLIC_OUT,
            JOB_DEF.VERSION_SERIAL AS JOB_VERSION_SERIAL
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

    UNION ALL

    -- =========================================================================
    -- RECURSIVE MEMBER
    -- =========================================================================
    SELECT
        PREV_DEP.SUCCESSOR_PARENT_TABLE,
        PREV_DEP.SUCCESSOR_JOB_NAME,
        PREV_DEP.SUCCESSOR_PARENT_TABLE_ID,
        PREV_DEP.SUCCESSOR_JOB_ID,
        ':depends_on'                              AS depends_on_literal,
        J_REC.IN_CONDITION                         AS MATCHING_CONDITION,
        D_REC.PREDECESSOR_TABLE                    AS PREDECESSOR_PARENT_TABLE,
        D_REC.PREDECESSOR_JOB_NAME                 AS PREDECESSOR_JOB_NAME,
        D_REC.PREDECESSOR_TABLE_ID                 AS PREDECESSOR_PARENT_TABLE_ID,
        D_REC.PREDECESSOR_JOB_ID_STR               AS PREDECESSOR_JOB_ID_INTERNAL,
        PREV_DEP.recursion_level + 1,
        PREV_DEP.dependency_path || ' -> ' || D_REC.PREDECESSOR_JOB_NAME  AS dependency_path
    FROM   RecursiveJobDependencies PREV_DEP
    JOIN (
        SELECT DISTINCT
            LNKI.CONDITION         AS IN_CONDITION,
            JOB_DEF.PARENT_TABLE   AS IN_PARENT_TABLE,
            JOB_DEF.TABLE_ID       AS IN_PARENT_TABLE_ID,
            JOB_DEF.JOB_NAME       AS IN_JOB_NAME,
            JOB_DEF.JOB_ID         AS IN_JOB_ID_STR,
            JOB_DEF.CYCLIC_TYPE    AS JOB_CYCLIC_IN,
            JOB_DEF.VERSION_SERIAL AS JOB_VERSION_SERIAL
        FROM   psgmgr.CM_DEF_VJOB JOB_DEF
        JOIN   psgmgr.CM_DEF_VTAB TAB_DEF
                 ON JOB_DEF.TABLE_ID = TAB_DEF.TABLE_ID
        JOIN   psgmgr.CM_DEF_LNKI_P_VW LNKI
                 ON  JOB_DEF.TABLE_ID       = LNKI.TABLE_ID
                 AND JOB_DEF.JOB_ID         = LNKI.JOB_ID
                 AND JOB_DEF.VERSION_SERIAL = LNKI.VERSION_SERIAL
        WHERE  TAB_DEF.USER_DAILY IS NOT NULL
    ) J_REC
      ON J_REC.IN_JOB_NAME = PREV_DEP.PREDECESSOR_JOB_NAME
    JOIN (
        SELECT DISTINCT
            LNKO.CONDITION         AS OUT_CONDITION,
            JOB_DEF.PARENT_TABLE   AS PREDECESSOR_TABLE,
            JOB_DEF.TABLE_ID       AS PREDECESSOR_TABLE_ID,
            JOB_DEF.JOB_NAME       AS PREDECESSOR_JOB_NAME,
            JOB_DEF.JOB_ID         AS PREDECESSOR_JOB_ID_STR,
            JOB_DEF.CYCLIC_TYPE    AS JOB_CYCLIC_OUT,
            JOB_DEF.VERSION_SERIAL AS JOB_VERSION_SERIAL
        FROM   psgmgr.CM_DEF_VJOB JOB_DEF
        JOIN   psgmgr.CM_DEF_VTAB TAB_DEF
                 ON JOB_DEF.TABLE_ID = TAB_DEF.TABLE_ID
        JOIN   psgmgr.CM_DEF_LNKO_P_VW LNKO
                 ON  JOB_DEF.TABLE_ID       = LNKO.TABLE_ID
                 AND JOB_DEF.JOB_ID         = LNKO.JOB_ID
                 AND JOB_DEF.VERSION_SERIAL = LNKO.VERSION_SERIAL
        WHERE  TAB_DEF.USER_DAILY IS NOT NULL
    ) D_REC
      ON J_REC.IN_CONDITION = D_REC.OUT_CONDITION
      -- AND J_REC.JOB_CYCLIC_IN = D_REC.JOB_CYCLIC_OUT  -- intentionally disabled
    WHERE J_REC.IN_JOB_NAME <> D_REC.PREDECESSOR_JOB_NAME
      AND PREV_DEP.recursion_level < 10
      AND INSTR(PREV_DEP.dependency_path, D_REC.PREDECESSOR_JOB_NAME) = 0   -- cycle guard
)
SELECT
    SUCCESSOR_PARENT_TABLE                                       AS in_parent_table,
    SUCCESSOR_JOB_NAME                                           AS in_job_name,
    SUCCESSOR_PARENT_TABLE_ID                                    AS in_parent_table_id,
    SUCCESSOR_JOB_ID                                             AS in_job_id,
    SUCCESSOR_PARENT_TABLE_ID || '.' || SUCCESSOR_JOB_ID          AS in_table_job_id,
    MATCHING_CONDITION                                           AS out_condition,
    PREDECESSOR_PARENT_TABLE                                     AS dependent_table,
    PREDECESSOR_JOB_NAME                                         AS dependent_job,
    PREDECESSOR_PARENT_TABLE_ID                                  AS dependent_table_id,
    PREDECESSOR_JOB_ID_INTERNAL                                  AS dependent_job_id,
    PREDECESSOR_PARENT_TABLE_ID || '.' || PREDECESSOR_JOB_ID_INTERNAL  AS out_table_job_id,
    recursion_level,
    dependency_path
FROM   RecursiveJobDependencies
WHERE  recursion_level < 30
ORDER BY in_job_name, recursion_level
;
