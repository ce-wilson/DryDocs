# Control-M C3/C4 Normalization — Status & Runbook

**Last updated:** 2026-06-11
**Goal:** extract C3/C4 technical objects (file ops, ETL launches — Ab Initio /
Informatica / PySpark, notifications) from Control-M job definitions, one level
below the existing job-to-job lineage.

Architecture: SQL extract → Python normalize → Oracle staging write-back
(QA in SQL Developer) → Neo4j load under PROV `:JobRun`. Variable resolution
and command parsing happen in **Python, not recursive SQL**.

---

## Phase status

| Phase | Scope | Status |
|-------|-------|--------|
| DDL   | Staging schema for the DBA | **Delivered** — pending DBA execution (see below) |
| A     | Variable extract + taxonomy classifier + staging output | **Code complete** — pending production run (see below) |
| B     | Fixed-point variable resolver (offline AutoEdit simulation) | **Complete** |
| C     | Command parsing: FileWatch / OS launcher registry / PRECMD-POSTCMD shell / AIAWSWLK | **Code complete** — registry grows iteratively (Phase E) |
| D     | Graph load (staging → Neo4j under `:JobRun`) | Not started |
| E     | TDQ loop (DQV measurements, launcher-registry growth from unparsed backlog) | Not started |

## Delivered artifacts

| Artifact | Path |
|----------|------|
| Staging DDL (DBA script) | `drydocs/loaders/sql/ddl/controlm_staging_ddl.sql` |
| Variable extraction SQL | `drydocs/loaders/sql/controlm_variables.sql` |
| Taxonomy classifier (9 kinds) | `drydocs/controlm/variables.py` |
| Resolver (Phase B) | `drydocs/controlm/resolver.py` |
| Command parser + launcher registry (Phase C) | `drydocs/controlm/commands.py` |
| Path canonicalizer + role classifier (Phase C) | `drydocs/controlm/paths.py` |
| Fact / notification routing (Phase C) | `drydocs/controlm/facts.py` |
| Staging-row builder (all 8 STG_ tables) | `drydocs/controlm/staging.py` |
| Coverage report | `drydocs/controlm/variable_report.py` |
| Row model (accepts raw extract headers) | `drydocs/models/controlm.py` → `ControlMVariableRow` |
| Sample fixture (323 real rows) | `drydocs/data/samples/controlm_variables__sample.csv` |
| Vendor reference (validated against) | `vendor-bmc/controlm-{variables,os-job-parameters,file-watcher,api-job-types,file-transfer-job}.md` |
| Tests (102 across classifier/resolver/staging/commands) | `tests/unit/test_{variable_classifier,variable_resolver,variable_staging,command_parser}.py` |

CLI (no Neo4j needed):

```
drydocs analyze-variables [--csv FILE] [--delimiter "|"] [--use-oracle] [--resolve]
drydocs normalize-variables [--csv FILE] [--delimiter "|"] [--use-oracle] --out-dir DIR
```

`normalize-variables` now writes all 8 staging files: stg_run, stg_variable,
stg_parse_quality, **stg_invocation, stg_file_op, stg_file_ref,
stg_notification, stg_app_fact**.

## Phase C design notes (for Phase E registry growth)

- **Launcher registry** lives in `commands.py::LAUNCHER_REGISTRY` — a list of
  `(regex on executable basename, invocation_type, rule_id)`. Add a rule;
  don't touch parser logic. Seeded types: ABINITIO (`.m`, dtlaunch.sh),
  INFORMATICA (pmcmd, `m_*`), VALIDATION_UTIL (run_data_validation.sh,
  run_calp_temp.sh), PYTHON/PYSPARK, SHELL_SCRIPT, FILE_TRANSFER, UNKNOWN.
- **Unmatched executables** → `invocation_type=UNKNOWN`, surfaced in
  `ParsedCommand.unparsed`; these drive registry growth. On the sample, zero
  UNKNOWN remain after seeding.
- **Shell quoting gotcha (fixed):** production PRECMD/POSTCMD often wrap the
  whole shell string in double quotes; `split_statements` strips a single
  fully-enclosing quote pair before splitting on `;`/`|`/`&&`.
- **File ops** (`mkdir/cp/mv/rm/rmdir/sed/chmod/...`) → STG_FILE_OP; verb set
  matches the vendor pre/post-transfer command list. **Container overrides**
  (UCM) → inner command extracted and re-parsed (the `python /app/app.py`
  case). **FileWatch `*FILE_PATH`** → STG_FILE_REF WATCH_INPUT.
- **Vendor nuance recorded:** controlm-os-job-parameters.md says folder
  variables don't transfer to job *scripts* — that's the runtime shell env,
  NOT Control-M %%-substitution into command fields, so Phase B folder→job
  resolution remains correct for parsing.

---

## Remaining Phase A steps (operational — no code work)

1. **Confirm the variable source view name.**
   The DDL and `controlm_variables.sql` use the placeholder
   `psgmgr.CM_DEF_SETVAR` (flagged `** VERIFY VIEW NAME **` in both files).
   Identify the actual object behind the SQL Developer extract
   (`TABLE_NAME|JOB_NAME|JOB_ID|APPL_TYPE|NAME|VALUE`) and substitute it.

2. **DBA runs the staging DDL** (`controlm_staging_ddl.sql`):
   - Section 0 pre-flight FIRST: (0.1) TABLE_ID-unique-across-data-centers
     check; (0.2) MEMLIB / OVERLIB / APPL_TYPE column existence on
     CM_DEF_VJOB — drop those view columns if absent.
   - Then Sections 1–6 top-to-bottom as the owning schema (`DRYDOCS_STG`).
   - Grants: schema needs SELECT on the three psgmgr objects; the Python
     account needs SELECT on views + INSERT/DELETE on STG_ tables
     (templates in Section 6).
   - A paste-ready overview statement for the DBA was drafted in the
     2026-06-11 session (pure-DDL, no PL/SQL; run_id = batch-audit pattern).

3. **Run the normalizer against the full population** (per data center or all
   at once — ~1.1M rows is fine in one run):

   ```
   drydocs normalize-variables --use-oracle --out-dir stg_out/
   ```

   or, without Oracle connectivity from Python, export the extract from SQL
   Developer and run `--csv export.txt --delimiter "|"`.
   Output: `stg_run.csv`, `stg_variable.csv`, `stg_parse_quality.csv` —
   columns match the DDL exactly.

4. **Load the three CSVs into DRYDOCS_STG** (SQL Developer import or
   SQL*Loader; `stg_run` first for the FK).

5. **QA in SQL Developer** via `stg_coverage_summary` and ad-hoc queries on
   `stg_variable.var_kind`. Checks:
   - Does the sample distribution (45% LITERAL / 24% SEMANTIC_FACT /
     15% PLUGIN_NS) hold at population scale? The 323-row sample skews
     toward variable-rich folders, so expect LITERAL share to shift.
   - Review `MALFORMED` rows (sample had mis-keyed entries, e.g. a
     CALCDATE expression in the NAME field).
   - Review top `unresolved_tokens` — expected residents are
     runtime-provided names (MONTH_END_DATE pattern) and FileWatch
     runtime tokens; anything else may be a missing folder header or a
     classifier gap.
   - Pilot DC order: **P012-E0700-IB → P032 (variable-heavy, stresses the
     resolver) → P014 → P021** (bimodal: ~23% of its jobs share one
     ~29-variable template — likely a single classifier rule in Phase C).

## Phase C entry criteria / first moves

- Validate handler designs against the vendor docs BEFORE coding:
  `vendor-bmc/controlm-file-watcher.md`, `controlm-os-job-parameters.md`,
  `controlm-api-job-types.md` (same drill as the variables doc — it caught
  three classifier corrections).
- 59% of jobs define **zero variables** — their classification rests
  entirely on CMD_LINE/MEMNAME, so the OS launcher registry is the
  critical path. Build order: FileWatch (already structured) → launcher
  registry → PRECMD/POSTCMD shell parsing → AIAWSWLK/UCM.
- `STG_PARSE_QUALITY.cmd_present / cmd_classified / invocation_count /
  file_ref_count` are emitted as 'N'/0 placeholders — Phase C fills them.
- Suitable for a cheaper model session (well-specified, test-guarded,
  iterative registry growth).

## Known facts that bite

- Duplicate `(job, var_name)` definitions are legitimate (sequential
  reassignment — `%%FileWatch-TIME_LIMIT` twice on one job). Never dedupe.
- User vars are referenced with BOTH `%%VAR` and `%%$VAR` syntax; system
  variables also exist WITHOUT `$` (`%%ORDERID`, `%%JOBNAME`). The
  registries in `variables.py` are the source of truth.
- `%%\VAR` = global scope, `%%\\POOL\VAR` = pool — cross-job shared state,
  kept verbatim as `external_refs`, never inlined.
- All staging keys include `DATA_CENTER` (TABLE_ID may collide across the
  4 DCs — DDL Section 0.1 verifies).
- 6 unit-test failures pre-exist on main (folder_name_parser, schema,
  controlm_cypher) — unrelated to this work stream.
