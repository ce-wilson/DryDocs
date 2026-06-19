-- =============================================================================
-- controlm_staging_supplement_ddl.sql
--
-- Supplemental staging objects for the Oracle-ingestion feature, layered on top
-- of controlm_staging_ddl.sql. Adds the incremental WATERMARK control table and
-- the SAMPLE provenance table, plus developer-SID-aware view extensions.
--
-- Branch: producer feature/oracle-ingestion -> company psgmgr-base.
-- Target schema: DRYDOCS_STG (all objects unqualified; run as the owning schema).
-- Site-specific names are PLACEHOLDERS — substitute per site, do not hardcode:
--   DRYDOCS_STG, CM_RO_USER, <PY_NORMALIZER_USER>, and the unverified
--   psgmgr.CM_DEF_SETVAR object.
--
-- Idempotent by construction: CREATE OR REPLACE for views; existence-checked
-- CREATE for tables/indexes (ORA-00955 swallowed); GRANT is idempotent.
-- Re-runnable every iteration; the company applies it as a delta.
-- =============================================================================


-- =============================================================================
-- Section 1 : STG_LOAD_CONTROL — incremental high-water-mark (the keystone)
--   Advanced ONLY after a committed batch; the restart point for incremental.
-- =============================================================================
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE stg_load_control (
      source_object       VARCHAR2(128 CHAR) NOT NULL,   -- CM_DEF_VJOB | CM_DEF_VTAB | CM_DEF_SETVAR | ...
      data_center         VARCHAR2(40 CHAR)  NOT NULL,
      load_mode           VARCHAR2(12 CHAR)  DEFAULT ''INCREMENTAL'' NOT NULL,  -- FULL | INCREMENTAL
      hwm_capture_date    TIMESTAMP,                       -- coarse high-water mark
      hwm_version_serial  NUMBER(12),                      -- versioned-source change signal
      last_run_id         VARCHAR2(64 CHAR),               -- FK-able to stg_run.run_id
      last_status         VARCHAR2(12 CHAR),               -- RUNNING | SUCCEEDED | FAILED
      rows_applied        NUMBER(12),
      updated_at          TIMESTAMP          DEFAULT SYSTIMESTAMP NOT NULL,
      CONSTRAINT stg_load_control_pk PRIMARY KEY (source_object, data_center),
      CONSTRAINT stg_load_control_mode_ck CHECK (load_mode IN (''FULL'',''INCREMENTAL''))
    )';
EXCEPTION WHEN OTHERS THEN IF SQLCODE = -955 THEN NULL; ELSE RAISE; END IF;  -- ORA-00955 = already exists
END;
/

-- =============================================================================
-- Section 2 : STG_SAMPLE_MANIFEST — sample provenance (scope binds + coverage)
-- =============================================================================
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE stg_sample_manifest (
      run_id              VARCHAR2(64 CHAR)  NOT NULL,
      scope_folder        VARCHAR2(128 CHAR),
      scope_run_as        VARCHAR2(64 CHAR),
      scope_developer_sid VARCHAR2(64 CHAR),
      scope_row_cap       NUMBER(10),
      scenario            VARCHAR2(40 CHAR),               -- from controlm_variables_scenarios.sql
      rows_pulled         NUMBER(10),
      captured_at         TIMESTAMP          DEFAULT SYSTIMESTAMP NOT NULL
    )';
EXCEPTION WHEN OTHERS THEN IF SQLCODE = -955 THEN NULL; ELSE RAISE; END IF;
END;
/

-- =============================================================================
-- Section 3 : developer-SID-aware view (inline normalization; NO dimension table)
--   Trailing lowercase 'p' = automation release process (detect on RAW value,
--   before UPPER, so the marker is not masked). STG_DEV_SID dimension deferred.
-- =============================================================================
CREATE OR REPLACE VIEW job_developer_view AS
SELECT data_center, folder_id, job_id, role, sid,
       UPPER(REGEXP_REPLACE(sid, 'p$', ''))            AS developer_sid,
       CASE WHEN sid LIKE '%p' THEN 'Y' ELSE 'N' END    AS is_automation
FROM (
    SELECT T.DATA_CENTER AS data_center, J.TABLE_ID AS folder_id, J.JOB_ID AS job_id,
           col.role, col.sid
    FROM   psgmgr.CM_DEF_VJOB J
    JOIN   psgmgr.CM_DEF_VTAB T ON J.TABLE_ID = T.TABLE_ID
    CROSS  APPLY (                                        -- one row per SID-bearing column ** VERIFY cols exist (0.x) **
        SELECT 'AUTHOR'       AS role, J.AUTHOR        AS sid FROM DUAL UNION ALL
        SELECT 'CREATION_USER',        J.CREATION_USER         FROM DUAL UNION ALL
        SELECT 'CHANGE_USERID',        J.CHANGE_USERID         FROM DUAL
    ) col
    WHERE  J.IS_CURRENT_VERSION = '1' AND col.sid IS NOT NULL
);
-- NOTE: pre-flight CREATION_USER / CHANGE_USERID existence on CM_DEF_VJOB
--       (ALL_TAB_COLUMNS check) before relying on this view — see
--       persona-oracle-dba.md §1.7 open question 3.


-- =============================================================================
-- Section 4 : indexes (idempotent; add as access paths are confirmed)
-- =============================================================================
-- (none required yet — STG_LOAD_CONTROL is PK-only access; add here per iteration)


-- =============================================================================
-- Section 5 : grants (PLACEHOLDER account names — adjust to site standard)
--   GRANT is idempotent. Deltas vs the base script:
--     GRANT SELECT, INSERT, UPDATE, DELETE ON stg_load_control    TO <PY_NORMALIZER_USER>;  -- UPDATE advances HWM
--     GRANT SELECT, INSERT, DELETE        ON stg_sample_manifest  TO <PY_NORMALIZER_USER>;
--     GRANT SELECT ON job_developer_view  TO <PY_NORMALIZER_USER>;
--     GRANT SELECT ON stg_load_control, stg_sample_manifest, job_developer_view TO <ANALYST_ROLE>;
--   Source reads use the EXISTING CM_RO_USER grants (dev-SID columns are columns
--   on already-granted CM_DEF_VJOB/VTAB — no new psgmgr grant; confirm CM_DEF_SETVAR).
-- =============================================================================
