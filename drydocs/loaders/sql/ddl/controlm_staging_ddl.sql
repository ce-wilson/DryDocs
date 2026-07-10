-- =============================================================================
-- controlm_staging_ddl.sql
--
-- Purpose      : DBA implementation script for the Control-M C3/C4 normalization
--                staging layer. Creates (1) base read views over the psgmgr
--                replicated Control-M views to simplify Python ingestion and
--                ad-hoc analysis, and (2) normalized write-back staging tables
--                that the Python normalizer populates.
--
-- Target schema: <maint_mgr>  (all objects are unqualified so the script runs
--                under the owning maintenance account placeholder)
--
-- Sources      : Control-M source objects follow the CM_* naming convention
--                under psgmgr, for example:
--                psgmgr.CM_DEF_VTAB    (folders; "tables" in BMC naming)
--                psgmgr.CM_DEF_VJOB    (jobs, ~100 cols, version history)
--                psgmgr.CM_DEF_SETVAR_VW  (job/folder variables)
--                  -- Confirmed 2026-07-10 against live psgmgr: the variable view
--                  -- behind the (TABLE_NAME|JOB_NAME|JOB_ID|APPL_TYPE|NAME|VALUE)
--                  -- extract; carries its own IS_CURRENT_VERSION / VERSION_SERIAL.
--
-- Volumes (capture 2026-06, 4 data centers):
--   Folders : ~18,800   (P012: 2,230 / P014: 4,188 / P021: 7,914 / P032: 4,441)
--   Jobs    : ~240,600  (P012: 42,688 / P014: 52,976 / P021: 59,712 / P032: 85,202)
--   Variable rows: ~1.1M (job-level ~1.03M + folder-level ~95K; max 67 per job)
--   Staging estimate after normalization: < 3M rows total, < 2 GB incl. indexes.
--   No partitioning required at this volume; plain heap tables + b-tree indexes.
--
-- Load pattern : full refresh. The Python normalizer DELETEs by RUN_ID (or
--                truncates) and bulk-inserts. Each run is recorded in STG_RUN.
--
-- Ownership / grants:
--   <maint_mgr> owns the staging objects created by this script.
--   Source reads follow the Control-M CM_* convention and are granted via
--   the read role CM_RO_USER.
--
-- Grants needed FOR consumers: see Section 6.
-- =============================================================================


-- =============================================================================
-- Section 0 : DBA pre-flight validation (run, review output, do not skip)
-- =============================================================================

-- 0.1  Is TABLE_ID unique ACROSS data centers? The downstream graph currently
--      keys folders by TABLE_ID alone. If this returns rows, TABLE_ID collides
--      across data centers and (DATA_CENTER, TABLE_ID) is the true key — the
--      staging design below already assumes the composite key defensively.
--
--   SELECT TABLE_ID, COUNT(DISTINCT DATA_CENTER) AS dc_count
--   FROM   psgmgr.CM_DEF_VTAB
--   GROUP  BY TABLE_ID
--   HAVING COUNT(DISTINCT DATA_CENTER) > 1;

-- 0.2  Confirm CM_DEF_VJOB has MEMLIB / OVERLIB columns (script-library paths;
--      valuable for command classification). If absent, drop those two columns
--      from JOB_DETAILED_VIEW below.
--
--   SELECT column_name FROM all_tab_columns
--   WHERE  owner = 'PSGMGR' AND table_name = 'CM_DEF_VJOB'
--   AND    column_name IN ('MEMLIB', 'OVERLIB', 'APPL_TYPE');


-- =============================================================================
-- Section 1 : base read views (Python ingestion + general analysis)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- JOB_DETAILED_VIEW
--
-- One row per current-version job, joined to its folder and data center, with
-- the folder-name prefix decoded inline (environment / LOB / appcode / folder
-- type — same convention as drydocs.controlm.folder_name).
--
-- Deliberately NOT filtered on T.USER_DAILY: this view serves analyses beyond
-- the active-inventory use case. Consumers filter on IS_ACTIVE_FOLDER = 'Y'
-- to reproduce the phase-1 population. IS_CURRENT_VERSION = '1' IS enforced
-- here — historical versions would inflate every count and serve no analysis.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW job_detailed_view AS
SELECT
    T.DATA_CENTER                          AS data_center,
    J.TABLE_ID                             AS folder_id,
    T.SCHED_TABLE                          AS folder_name,
    CASE WHEN T.USER_DAILY IS NOT NULL
         THEN 'Y' ELSE 'N' END             AS is_active_folder,
    T.USER_DAILY                           AS user_daily,
    -- folder-name prefix decode (first dash-delimited segment, positions 1-6)
    CASE WHEN INSTR(T.SCHED_TABLE, '-') >= 7
         THEN SUBSTR(T.SCHED_TABLE, 1, 1) END  AS fn_environment_code,  -- P/D/Q
    CASE WHEN INSTR(T.SCHED_TABLE, '-') >= 7
         THEN SUBSTR(T.SCHED_TABLE, 2, 1) END  AS fn_lob_code,
    CASE WHEN INSTR(T.SCHED_TABLE, '-') >= 7
         THEN SUBSTR(T.SCHED_TABLE, 3, 3) END  AS fn_app_code,          -- SEAL crosswalk key
    CASE WHEN INSTR(T.SCHED_TABLE, '-') >= 7
         THEN SUBSTR(T.SCHED_TABLE, 6, 1) END  AS fn_folder_type_code,  -- G/D/W/M/Q/H/R
    -- folder-header flag: smart-folder header rows carry the folder name as
    -- their job name (observed as JOB_ID = 1 rows holding folder-scope vars)
    CASE WHEN J.JOB_NAME = T.SCHED_TABLE
         THEN 'Y' ELSE 'N' END             AS is_folder_header,
    J.JOB_ID                               AS job_id,
    J.JOB_NAME                             AS job_name,
    J.VERSION_SERIAL                       AS version_serial,
    J.APPLICATION                          AS application,      -- unreliable; see folder_name.py
    J.GROUP_NAME                           AS group_name,
    J.TASK_TYPE                            AS task_type,
    J.APPL_TYPE                            AS appl_type,        -- OS / FileWatch / AIAWSWLK / ...
    J.CYCLIC                               AS cyclic,
    J.CYCLIC_TYPE                          AS cyclic_type,
    J.JOB_ORDER                            AS job_order,
    J.OWNER                                AS owner,
    J.AUTHOR                               AS author,
    J.NODE_ID                              AS node_id,
    J.MEMNAME                              AS memname,
    J.MEMLIB                               AS memlib,           -- drop if column absent (sect 0.2)
    J.OVERLIB                              AS overlib,          -- drop if column absent (sect 0.2)
    J.CMD_LINE                             AS cmd_line,
    CASE WHEN J.CMD_LINE IS NOT NULL
         THEN 'Y' ELSE 'N' END             AS has_cmd_line,
    J.DESCRIPTION                          AS description,
    J.PRIORITY                             AS priority,
    J.CRITICAL                             AS critical,
    J.ACTIVE_FROM                          AS active_from,
    J.ACTIVE_TILL                          AS active_till,
    J.VERSION_TIMESTAMP                    AS version_timestamp,
    J.VERSION_USER                         AS version_user,
    J.INSTANCE_NAME                        AS instance_name,
    J.CAPTURE_DATE                         AS capture_date
FROM   psgmgr.CM_DEF_VJOB J
JOIN   psgmgr.CM_DEF_VTAB T  ON J.TABLE_ID = T.TABLE_ID
                            -- AND J.DATA_CENTER = T.DATA_CENTER  -- enable if 0.1 found collisions
WHERE  J.IS_CURRENT_VERSION = '1'
;

COMMENT ON TABLE job_detailed_view IS
  'Current-version Control-M jobs joined to folders, folder-name prefix decoded. Base for Python normalizer and ad-hoc analysis. Filter is_active_folder=''Y'' for the phase-1 inventory population.';


-- -----------------------------------------------------------------------------
-- JOB_VARIABLE_VIEW
--
-- One row per variable definition, joined to job + folder context, with cheap
-- syntactic hint flags for SQL-side profiling. Semantic classification
-- (taxonomy, resolution) is the Python normalizer's job — these flags only
-- support quick coverage queries in SQL Developer.
--
-- NOTE: duplicate (job, name) definitions exist in the wild (same variable
-- defined twice on one job with different values) — this view does not and
-- must not dedupe.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW job_variable_view AS
SELECT
    T.DATA_CENTER                          AS data_center,
    V.TABLE_ID                             AS folder_id,
    T.SCHED_TABLE                          AS folder_name,
    CASE WHEN T.USER_DAILY IS NOT NULL
         THEN 'Y' ELSE 'N' END             AS is_active_folder,
    V.JOB_ID                               AS job_id,
    J.JOB_NAME                             AS job_name,
    J.APPL_TYPE                            AS appl_type,
    CASE WHEN J.JOB_NAME = T.SCHED_TABLE
         THEN 'FOLDER' ELSE 'JOB' END      AS var_scope,
    V.NAME                                 AS var_name,
    V.VALUE                                AS var_value,
    -- syntactic hints (profiling only; Python owns real classification)
    CASE WHEN INSTR(V.VALUE, '%%$') > 0
         THEN 'Y' ELSE 'N' END             AS has_system_func,   -- %%$ODATE, %%$CALCDATE, ...
    CASE WHEN INSTR(V.VALUE, '%%\') > 0
         THEN 'Y' ELSE 'N' END             AS has_flow_ref,      -- %%\FLOW\VAR cross-flow pointer
    CASE WHEN INSTR(REPLACE(REPLACE(V.VALUE, '%%$', ''), '%%\', ''), '%%') > 0
         THEN 'Y' ELSE 'N' END             AS has_var_ref,       -- references another %%VAR
    CASE WHEN INSTR(V.NAME, '-') > 0
         THEN 'Y' ELSE 'N' END             AS is_namespaced      -- %%FileWatch-*, %%UCM-*
FROM   psgmgr.CM_DEF_SETVAR_VW V
JOIN   psgmgr.CM_DEF_VJOB  J  ON V.TABLE_ID = J.TABLE_ID
                             AND V.JOB_ID   = J.JOB_ID
JOIN   psgmgr.CM_DEF_VTAB  T  ON J.TABLE_ID = T.TABLE_ID
WHERE  V.IS_CURRENT_VERSION = '1'
  AND  J.IS_CURRENT_VERSION = '1'
;

COMMENT ON TABLE job_variable_view IS
  'Control-M variable definitions with job/folder context and syntactic hint flags. ~1.1M rows. Duplicates per (job, name) are legitimate — do not dedupe.';


-- =============================================================================
-- Section 2 : run control (provenance for every normalizer execution)
-- =============================================================================

CREATE TABLE stg_run (
    run_id              VARCHAR2(64 CHAR)   NOT NULL,   -- UUID issued by the normalizer
    started_at          TIMESTAMP           DEFAULT SYSTIMESTAMP NOT NULL,
    ended_at            TIMESTAMP,
    status              VARCHAR2(20 CHAR)   DEFAULT 'RUNNING' NOT NULL,
                        -- RUNNING | SUCCEEDED | FAILED
    data_centers        VARCHAR2(200 CHAR),              -- comma list processed this run
    src_job_count       NUMBER(10),
    src_var_count       NUMBER(10),
    normalizer_version  VARCHAR2(40 CHAR),
    notes               VARCHAR2(1000 CHAR),
    CONSTRAINT stg_run_pk PRIMARY KEY (run_id),
    CONSTRAINT stg_run_status_ck CHECK (status IN ('RUNNING','SUCCEEDED','FAILED'))
);

COMMENT ON TABLE stg_run IS
  'One row per Python normalizer execution. All STG_ rows carry the producing run_id; maps to the PROV :JobRun node in the graph.';


-- =============================================================================
-- Section 3 : normalized staging tables (written by the Python normalizer)
--
-- Conventions:
--   * every table carries (run_id, data_center, folder_id, job_id)
--   * surrogate IDENTITY PKs — natural keys are NOT unique (duplicate variable
--     definitions per job exist; multiple invocations/file refs per job)
--   * raw text is always preserved alongside normalized forms
--   * resolved values may exceed the raw 4000-char limit after substitution;
--     resolved/args/raw-command columns are CLOB where expansion is possible
-- =============================================================================

-- -----------------------------------------------------------------------------
-- STG_VARIABLE : classified + resolved variable definitions
-- Expected volume: ~1.1M rows per run.
-- -----------------------------------------------------------------------------
CREATE TABLE stg_variable (
    variable_sk         NUMBER GENERATED ALWAYS AS IDENTITY,
    run_id              VARCHAR2(64 CHAR)   NOT NULL,
    data_center         VARCHAR2(40 CHAR)   NOT NULL,
    folder_id           NUMBER(12)          NOT NULL,
    job_id              NUMBER(12)          NOT NULL,
    src_ordinal         NUMBER(6)           NOT NULL,   -- definition order within job (dupes exist)
    var_scope           VARCHAR2(10 CHAR)   NOT NULL,   -- FOLDER | JOB
    var_name            VARCHAR2(255 CHAR)  NOT NULL,
    raw_value           VARCHAR2(4000 CHAR),
    resolved_value      CLOB,                            -- post fixed-point substitution
    var_kind            VARCHAR2(30 CHAR)   NOT NULL,
                        -- LITERAL | VAR_REF | SYSTEM_FUNC | DYNAMIC_NAME |
                        -- FLOW_REF | PLUGIN_NS | EMBEDDED_SHELL | SEMANTIC_FACT | MALFORMED
    env_tag             VARCHAR2(8 CHAR),                -- D/Q/P when _D/_Q/_P triplet expanded
    is_fully_resolved   CHAR(1)             DEFAULT 'N' NOT NULL,
    resolution_depth    NUMBER(3),
    unresolved_tokens   VARCHAR2(2000 CHAR),             -- comma list of leftover %%... tokens
    CONSTRAINT stg_variable_pk PRIMARY KEY (variable_sk),
    CONSTRAINT stg_variable_run_fk FOREIGN KEY (run_id) REFERENCES stg_run (run_id)
);

-- -----------------------------------------------------------------------------
-- STG_INVOCATION : every executable launch carved out of a job
-- (CMD_LINE, MEMNAME/MEMLIB, PRECMD/POSTCMD statements, container overrides).
-- Expected volume: ~250-500K rows per run.
-- -----------------------------------------------------------------------------
CREATE TABLE stg_invocation (
    invocation_sk       NUMBER GENERATED ALWAYS AS IDENTITY,
    run_id              VARCHAR2(64 CHAR)   NOT NULL,
    data_center         VARCHAR2(40 CHAR)   NOT NULL,
    folder_id           NUMBER(12)          NOT NULL,
    job_id              NUMBER(12)          NOT NULL,
    seq                 NUMBER(4)           NOT NULL,   -- order within the job
    invocation_source   VARCHAR2(30 CHAR)   NOT NULL,
                        -- CMDLINE | MEMNAME | PRECMD | POSTCMD | CONTAINER_OVERRIDE
    invocation_type     VARCHAR2(30 CHAR)   NOT NULL,
                        -- ABINITIO | INFORMATICA | PYSPARK | PYTHON | SHELL_SCRIPT |
                        -- ECS_TASK | VALIDATION_UTIL | FILE_TRANSFER | UNKNOWN
    executable_path     VARCHAR2(1000 CHAR),
    script_path         VARCHAR2(1000 CHAR),
    config_path         VARCHAR2(1000 CHAR),             -- app_conf_*.json etc.
    args_json           CLOB,                            -- parsed argv as JSON array
    raw_command         CLOB                NOT NULL,    -- resolved command text, pre-tokenize
    is_classified       CHAR(1)             DEFAULT 'N' NOT NULL,
    classifier_rule     VARCHAR2(100 CHAR),              -- launcher-registry rule that matched
    CONSTRAINT stg_invocation_pk PRIMARY KEY (invocation_sk),
    CONSTRAINT stg_invocation_run_fk FOREIGN KEY (run_id) REFERENCES stg_run (run_id)
);

-- -----------------------------------------------------------------------------
-- STG_FILE_REF : file/path references with symbolic date tokens
-- ({ODATE}, {ODATE-1}, {TS16}, ...) so one logical file = one row regardless
-- of business date. Expected volume: ~300-600K rows per run.
-- -----------------------------------------------------------------------------
CREATE TABLE stg_file_ref (
    file_ref_sk         NUMBER GENERATED ALWAYS AS IDENTITY,
    run_id              VARCHAR2(64 CHAR)   NOT NULL,
    data_center         VARCHAR2(40 CHAR)   NOT NULL,
    folder_id           NUMBER(12)          NOT NULL,
    job_id              NUMBER(12)          NOT NULL,
    ref_role            VARCHAR2(20 CHAR)   NOT NULL,
                        -- WATCH_INPUT | INPUT | OUTPUT | BACKUP | ARCHIVE |
                        -- LOG | CONFIG | DROPBOX | SCRIPT_DIR
    path_raw            VARCHAR2(2000 CHAR) NOT NULL,
    path_canonical      VARCHAR2(2000 CHAR),             -- wildcards + dates tokenized
    directory_path      VARCHAR2(1000 CHAR),
    filename_pattern    VARCHAR2(500 CHAR),
    date_token          VARCHAR2(30 CHAR),               -- {ODATE} | {ODATE-1} | {TS16} | ...
    source_field        VARCHAR2(60 CHAR),               -- var name or CMDLINE/PRECMD/POSTCMD
    CONSTRAINT stg_file_ref_pk PRIMARY KEY (file_ref_sk),
    CONSTRAINT stg_file_ref_run_fk FOREIGN KEY (run_id) REFERENCES stg_run (run_id)
);

-- -----------------------------------------------------------------------------
-- STG_FILE_OP : file operations parsed from PRECMD/POSTCMD/command shell
-- (mkdir/cp/mv/rm/sed chains).
-- -----------------------------------------------------------------------------
CREATE TABLE stg_file_op (
    file_op_sk          NUMBER GENERATED ALWAYS AS IDENTITY,
    run_id              VARCHAR2(64 CHAR)   NOT NULL,
    data_center         VARCHAR2(40 CHAR)   NOT NULL,
    folder_id           NUMBER(12)          NOT NULL,
    job_id              NUMBER(12)          NOT NULL,
    seq                 NUMBER(4)           NOT NULL,
    op_type             VARCHAR2(20 CHAR)   NOT NULL,
                        -- COPY | MOVE | DELETE | MKDIR | TRANSFORM | OTHER
    src_pattern         VARCHAR2(2000 CHAR),
    tgt_pattern         VARCHAR2(2000 CHAR),
    source_field        VARCHAR2(60 CHAR)   NOT NULL,    -- PRECMD | POSTCMD | CMDLINE
    raw_statement       VARCHAR2(4000 CHAR) NOT NULL,
    CONSTRAINT stg_file_op_pk PRIMARY KEY (file_op_sk),
    CONSTRAINT stg_file_op_run_fk FOREIGN KEY (run_id) REFERENCES stg_run (run_id)
);

-- -----------------------------------------------------------------------------
-- STG_NOTIFICATION : notification targets (NOTIFY/EMAIL/EMAIL_GRP vars,
-- already split on ';').
-- -----------------------------------------------------------------------------
CREATE TABLE stg_notification (
    notification_sk     NUMBER GENERATED ALWAYS AS IDENTITY,
    run_id              VARCHAR2(64 CHAR)   NOT NULL,
    data_center         VARCHAR2(40 CHAR)   NOT NULL,
    folder_id           NUMBER(12)          NOT NULL,
    job_id              NUMBER(12)          NOT NULL,
    channel             VARCHAR2(20 CHAR)   DEFAULT 'EMAIL' NOT NULL,
    address             VARCHAR2(320 CHAR)  NOT NULL,
    source_var          VARCHAR2(255 CHAR),
    CONSTRAINT stg_notification_pk PRIMARY KEY (notification_sk),
    CONSTRAINT stg_notification_run_fk FOREIGN KEY (run_id) REFERENCES stg_run (run_id)
);

-- -----------------------------------------------------------------------------
-- STG_APP_FACT : semantic facts mined from variables — independent SEAL
-- linkage (%%SEAL), FIDs, dataset ids, dataflow names, container images,
-- target tables. Cross-checked against folder-name appcode linkage downstream.
-- -----------------------------------------------------------------------------
CREATE TABLE stg_app_fact (
    app_fact_sk         NUMBER GENERATED ALWAYS AS IDENTITY,
    run_id              VARCHAR2(64 CHAR)   NOT NULL,
    data_center         VARCHAR2(40 CHAR)   NOT NULL,
    folder_id           NUMBER(12)          NOT NULL,
    job_id              NUMBER(12)          NOT NULL,
    fact_type           VARCHAR2(30 CHAR)   NOT NULL,
                        -- SEAL | FID | DS_ID | DATAFLOW | IMAGE | TGT_TABLE |
                        -- TGT_DB | APP_NAME | ALIAS
    fact_value          VARCHAR2(500 CHAR)  NOT NULL,
    environment         VARCHAR2(8 CHAR),                -- D/Q/P from triplet vars, else NULL
    source_var          VARCHAR2(255 CHAR),
    CONSTRAINT stg_app_fact_pk PRIMARY KEY (app_fact_sk),
    CONSTRAINT stg_app_fact_run_fk FOREIGN KEY (run_id) REFERENCES stg_run (run_id)
);

-- -----------------------------------------------------------------------------
-- STG_PARSE_QUALITY : per-job TDQ rollup; feeds DQV measurements in the graph
-- and the coverage report. One row per job per run.
-- -----------------------------------------------------------------------------
CREATE TABLE stg_parse_quality (
    run_id              VARCHAR2(64 CHAR)   NOT NULL,
    data_center         VARCHAR2(40 CHAR)   NOT NULL,
    folder_id           NUMBER(12)          NOT NULL,
    job_id              NUMBER(12)          NOT NULL,
    var_total           NUMBER(6)           DEFAULT 0 NOT NULL,
    var_resolved        NUMBER(6)           DEFAULT 0 NOT NULL,
    cmd_present         CHAR(1)             DEFAULT 'N' NOT NULL,
    cmd_classified      CHAR(1)             DEFAULT 'N' NOT NULL,
    invocation_count    NUMBER(4)           DEFAULT 0 NOT NULL,
    file_ref_count      NUMBER(6)           DEFAULT 0 NOT NULL,
    unresolved_tokens   VARCHAR2(2000 CHAR),
    notes               VARCHAR2(1000 CHAR),
    CONSTRAINT stg_parse_quality_pk
        PRIMARY KEY (run_id, data_center, folder_id, job_id),
    CONSTRAINT stg_parse_quality_run_fk FOREIGN KEY (run_id) REFERENCES stg_run (run_id)
);

-- -----------------------------------------------------------------------------
-- STG_UNPARSED_COMMAND : the iteration backlog. Anything the classifier could
-- not type lands here with the raw text; drives launcher-registry growth.
-- -----------------------------------------------------------------------------
CREATE TABLE stg_unparsed_command (
    unparsed_sk         NUMBER GENERATED ALWAYS AS IDENTITY,
    run_id              VARCHAR2(64 CHAR)   NOT NULL,
    data_center         VARCHAR2(40 CHAR)   NOT NULL,
    folder_id           NUMBER(12)          NOT NULL,
    job_id              NUMBER(12)          NOT NULL,
    source_field        VARCHAR2(60 CHAR)   NOT NULL,
    raw_text            CLOB                NOT NULL,
    fail_reason         VARCHAR2(200 CHAR),
    CONSTRAINT stg_unparsed_command_pk PRIMARY KEY (unparsed_sk),
    CONSTRAINT stg_unparsed_command_run_fk FOREIGN KEY (run_id) REFERENCES stg_run (run_id)
);


-- =============================================================================
-- Section 4 : indexes (job-key access path on every table; fact lookups)
-- =============================================================================

CREATE INDEX stg_variable_job_ix     ON stg_variable     (data_center, folder_id, job_id);
CREATE INDEX stg_variable_name_ix    ON stg_variable     (var_name);
CREATE INDEX stg_variable_kind_ix    ON stg_variable     (var_kind);
CREATE INDEX stg_invocation_job_ix   ON stg_invocation   (data_center, folder_id, job_id);
CREATE INDEX stg_invocation_type_ix  ON stg_invocation   (invocation_type);
CREATE INDEX stg_file_ref_job_ix     ON stg_file_ref     (data_center, folder_id, job_id);
CREATE INDEX stg_file_ref_role_ix    ON stg_file_ref     (ref_role);
CREATE INDEX stg_file_op_job_ix      ON stg_file_op      (data_center, folder_id, job_id);
CREATE INDEX stg_notification_job_ix ON stg_notification (data_center, folder_id, job_id);
CREATE INDEX stg_notification_addr_ix ON stg_notification (address);
CREATE INDEX stg_app_fact_job_ix     ON stg_app_fact     (data_center, folder_id, job_id);
CREATE INDEX stg_app_fact_lookup_ix  ON stg_app_fact     (fact_type, fact_value);
CREATE INDEX stg_unparsed_job_ix     ON stg_unparsed_command (data_center, folder_id, job_id);

-- Intentionally no index on path columns: 2000-char AL32UTF8 keys can exceed
-- the b-tree key size limit. If path lookups become a need, add a
-- function-based index on STANDARD_HASH(path_canonical) or SUBSTR(..., 1, 400).


-- =============================================================================
-- Section 5 : profiling views over staging (SQL Developer QA surface)
-- =============================================================================

CREATE OR REPLACE VIEW stg_coverage_summary AS
SELECT
    q.run_id,
    q.data_center,
    COUNT(*)                                          AS job_count,
    SUM(q.var_total)                                  AS var_total,
    SUM(q.var_resolved)                               AS var_resolved,
    ROUND(100 * SUM(q.var_resolved)
              / NULLIF(SUM(q.var_total), 0), 1)       AS pct_vars_resolved,
    SUM(CASE WHEN q.cmd_present = 'Y' THEN 1 END)     AS jobs_with_cmd,
    SUM(CASE WHEN q.cmd_classified = 'Y' THEN 1 END)  AS jobs_cmd_classified,
    ROUND(100 * SUM(CASE WHEN q.cmd_classified = 'Y' THEN 1 END)
              / NULLIF(SUM(CASE WHEN q.cmd_present = 'Y' THEN 1 END), 0), 1)
                                                      AS pct_cmds_classified
FROM   stg_parse_quality q
GROUP  BY q.run_id, q.data_center
;

COMMENT ON TABLE stg_coverage_summary IS
  'Per-run, per-data-center normalization coverage. The two pct_ columns are the phase-E TDQ headline metrics.';


-- =============================================================================
-- Section 6 : grants (adjust account names to site standard)
-- =============================================================================
--
-- Python normalizer account (read sources via views, write staging):
--   GRANT SELECT ON job_detailed_view      TO <PY_NORMALIZER_USER>;
--   GRANT SELECT ON job_variable_view      TO <PY_NORMALIZER_USER>;
--   GRANT SELECT, INSERT, UPDATE, DELETE ON stg_run              TO <PY_NORMALIZER_USER>;
--   GRANT SELECT, INSERT, DELETE ON stg_variable                 TO <PY_NORMALIZER_USER>;
--   GRANT SELECT, INSERT, DELETE ON stg_invocation               TO <PY_NORMALIZER_USER>;
--   GRANT SELECT, INSERT, DELETE ON stg_file_ref                 TO <PY_NORMALIZER_USER>;
--   GRANT SELECT, INSERT, DELETE ON stg_file_op                  TO <PY_NORMALIZER_USER>;
--   GRANT SELECT, INSERT, DELETE ON stg_notification             TO <PY_NORMALIZER_USER>;
--   GRANT SELECT, INSERT, DELETE ON stg_app_fact                 TO <PY_NORMALIZER_USER>;
--   GRANT SELECT, INSERT, DELETE ON stg_parse_quality            TO <PY_NORMALIZER_USER>;
--   GRANT SELECT, INSERT, DELETE ON stg_unparsed_command         TO <PY_NORMALIZER_USER>;
--
-- Analyst / QA accounts (read-only):
--   GRANT SELECT ON job_detailed_view, job_variable_view,
--                   stg_coverage_summary, <all stg_ tables> TO <ANALYST_ROLE>;
