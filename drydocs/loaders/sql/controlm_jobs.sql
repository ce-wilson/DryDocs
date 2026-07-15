-- =============================================================================
-- controlm_jobs.sql
--
-- Source table : psgmgr.CM_DEF_VJOB (replicated copy of dtsremgr.DEF_VJOB)
--                                    governed access via CM_RO_USER
-- Projection   : the subset of CM_DEF_VJOB columns the ControlMJobRow model
--                captures. CM_DEF_VJOB has 100+ columns; we project the
--                identity, classification, versioning, and lifecycle fields
--                needed for the inventory + lineage use case. Schedule-detail
--                columns (DAY_STR, INTERVAL_SEQUENCE, etc.) are excluded
--                from phase 1 — surface them later if a use case demands.
--
-- Filter rule:
--   J.IS_CURRENT_VERSION = 'Y'  — only current-version jobs (column is
--                                  VARCHAR2(1) — the literal must be a
--                                  string; domain value 'Y' confirmed by the
--                                  finalized company ingestion TDD, 2026-07-15)
--   T.USER_DAILY IS NOT NULL    — only actively-scheduled folders
--
-- Scope binds (optional, NULL = no filter; shared across all psgmgr extracts):
--   :folder_filter  folder-name LIKE pattern
--   :run_as         tenant FID (service) user — J.OWNER, exact
--   :developer_sid  authoring developer SID — J.AUTHOR/CREATION_USER/CHANGE_USERID
--                   (lowercase-initial; trailing 'p' = automation release process)
--   :row_cap        ROWNUM sample cap
--   (operational who-ran-it identity is separate — psgmgr.CM_AUD_ACTS, later)
-- =============================================================================

SELECT
    J.JOB_ID              AS job_id,
    J.VERSION_SERIAL      AS version_serial,
    J.TABLE_ID            AS folder_id,
    J.JOB_NAME            AS job_name,
    J.PARENT_TABLE        AS parent_table,    -- denormalized folder name on the job row
    J.APPLICATION         AS application,     -- business app name; reconcile to :Application.seal_id when possible
    J.GROUP_NAME          AS group_name,
    J.TASK_TYPE           AS task_type,
    J.CYCLIC              AS cyclic,          -- Y/N flag
    J.CYCLIC_TYPE         AS cyclic_type,     -- 1-char type code; matters for condition matching
    J.JOB_ORDER           AS job_order,
    J.OWNER               AS owner,
    J.AUTHOR              AS author,
    J.NODE_ID             AS node_id,         -- target host/agent
    J.CMD_LINE            AS cmd_line,
    J.DESCRIPTION         AS description,
    J.MEMNAME             AS memname,
    J.PRIORITY            AS priority,
    J.CRITICAL            AS critical,
    J.ACTIVE_FROM         AS active_from,
    J.ACTIVE_TILL         AS active_till,
    J.END_FOLDER          AS end_folder,
    J.IS_CURRENT_VERSION  AS is_current_version,
    J.VERSION_OPCODE      AS version_opcode,
    J.VERSION_TIMESTAMP   AS version_timestamp,
    J.VERSION_USER        AS version_user,
    J.INSTANCE_NAME       AS instance_name,
    J.CAPTURE_DATE        AS capture_date,
    -- source audit envelope (doc 06 Phase 1; gate controlm-q1q3-phase1):
    -- CREATION_* + CHANGE_* are the envelope; VERSION_* are current-version
    -- duplicates and stay non-envelope audit properties.
    J.CREATION_USER       AS creation_user,
    J.CREATION_DATE       AS creation_date,
    J.CHANGE_USERID       AS change_userid,
    J.CHANGE_DATE         AS change_date
FROM   psgmgr.CM_DEF_VJOB J
JOIN   psgmgr.CM_DEF_VTAB T   ON J.TABLE_ID = T.TABLE_ID
WHERE  J.IS_CURRENT_VERSION = 'Y'
  AND  T.USER_DAILY IS NOT NULL
  -- optional scope (any bind NULL = no filter on that dimension)
  AND  (:folder_filter IS NULL OR T.SCHED_TABLE LIKE :folder_filter)
  AND  (:run_as        IS NULL OR J.OWNER        =  :run_as)   -- tenant FID user
  AND  (:developer_sid IS NULL OR :developer_sid IN (J.AUTHOR, J.CREATION_USER, J.CHANGE_USERID))
  AND  (:row_cap       IS NULL OR ROWNUM        <=  :row_cap)
;
