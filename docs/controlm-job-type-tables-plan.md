# Control-M Job-Type Detail Tables — Plan (Phase C/D extension)

**Created:** 2026-07-15
**Extends:** `docs/controlm-c3-normalization-status.md` (the C3/C4 runbook, 2026-06-11)
**Motivation:** command lines cannot be parsed in SQL — variable resolution has
Control-M-specific semantics (the concatenation-delimiter period / smuggled-dot
pattern, SME-confirmed 2026-06-11, `drydocs_core/controlm/resolver.py`; plus
longest-name-in-scope binding and `%%VAR` vs `%%$VAR` duality). So the split
stays: **SQL extracts and stores raw job/variable rows in Oracle; Python
resolves and parses; results write back to `DRYDOCS_STG` for SQL-side QA.**

## What this adds

Three new job-type-shaped outputs on top of the existing statement-grain
staging tables (`STG_INVOCATION`, `STG_FILE_OP`, `STG_FILE_REF`):

| # | Output | Grain | For |
|---|--------|-------|-----|
| 1 | `STG_JOB_FILEWATCH` | one row per FileWatch job | watch path + watch conditions as columns |
| 2 | `STG_JOB_OS_COMMAND_VW` | one row per OS job | the job's primary launch, command line decomposed into fields |
| 3 | `STG_LAUNCH_DETAIL` | one row per DATA_PIPELINE / ABINITIO invocation (child of `STG_INVOCATION`) | framework arguments as named fields (dt-launcher args; Ab Initio pset + graph flags) |

---

## 1. `STG_JOB_FILEWATCH` — File Watcher detail by job type

**Selector (SQL side).** Two signals, unioned, with a disagreement flag:
- `J.APPL_TYPE = 'FileWatch'` — valid *here* because FileWatch is an
  engine-implemented job type. (Contrast: `APPL_TYPE` is a confirmed
  **dead-end for product derivation** — Ab Initio/Informatica run as plain OS
  commands, see `docs/restructure/07-software-registry.md`. Structural job
  types like FileWatch are the exception where it still means something.)
- The job defines `%%FileWatch-*` variables (`plugin_namespace = 'FileWatch'`
  in the classifier).

A job matching only one signal is still emitted, with `selector_agreement='N'`
— that mismatch is itself a metadata-quality finding for the remediation loop.

**Columns (Python fills from resolved variables + vendor watch conditions,
`external/orchestration/bmc-controlm/controlm-file-watcher.md`):**

```
run_id, data_center, folder_id, job_id            -- standard staging keys
selector_agreement      CHAR(1)                   -- APPL_TYPE and %%FileWatch-* agree?
watch_path_raw          VARCHAR2(2000)            -- resolved %%FileWatch-FILE_PATH source
watch_path_canonical    VARCHAR2(2000)            -- via paths.canonicalize (date tokens)
directory_path          VARCHAR2(1000)
filename_pattern        VARCHAR2(500)
date_token              VARCHAR2(30)              -- {ODATE} etc.
detect_mode             VARCHAR2(10)              -- CREATE | DELETE
time_limit_min          NUMBER(6)
search_interval_sec     NUMBER(6)
file_size_interval_sec  NUMBER(6)
iterations              NUMBER(6)
min_file_age            VARCHAR2(20)
max_file_age            VARCHAR2(20)
min_size                VARCHAR2(20)
reassignment_count      NUMBER(3)                 -- see gotcha below
```

**Known gotcha carried forward:** duplicate `(job, var_name)` FileWatch
variables are legitimate sequential reassignment (`%%FileWatch-TIME_LIMIT`
twice on one job). The job-grain table stores the **last effective value** and
a `reassignment_count`; the full sequence stays un-deduped in `STG_VARIABLE`.
Whether "last wins" is the correct effective-value rule is a **HITL gate
question** before Phase D load.

**Reuse:** `paths.build_file_ref` already produces WATCH_INPUT rows from
`%%FileWatch-FILE_PATH`; the new builder is a job-grain pivot of the same
handler plus the non-path condition variables it currently drops.

---

## 2. `STG_JOB_OS_COMMAND_VW` — OS command line into fields

`STG_INVOCATION` already carries the field decomposition
(`invocation_source/type`, `executable_path`, `script_path`, `config_path`,
`args_json`, `classifier_rule`) at statement grain. Don't duplicate the data —
project it to job grain as an Oracle **view** for SQL Developer QA:

- one row per OS job = its first `CMDLINE`-sourced invocation (`seq = 1`),
- plus rollups: `invocation_count`, `precmd_count`, `postcmd_count`,
  `file_op_count`, `unparsed_count` (joined from `STG_PARSE_QUALITY`),
- plus the `STG_LAUNCH_DETAIL` columns when the launch is a classified
  framework (LEFT JOIN on `invocation_sk`).

Materialize as a physical table only if view performance on ~250–500K
invocation rows proves inadequate for the QA workflow.

---

## 3. `STG_LAUNCH_DETAIL` — Data Pipeline & Ab Initio pset sub-table

Child of `STG_INVOCATION` (`invocation_sk` FK). Emitted when
`invocation_type IN ('DATA_PIPELINE', 'ABINITIO')`; the mechanism extends to
`INFORMATICA` later without schema change.

**Parser (Python).** Per-framework arg-spec parsers seeded from the canonical
command-line templates in
`internal/remediation/governance/command-line-and-variables-standard.md` §2:

- **dt-launcher (Data Pipeline, java/python):** `-fid -env -pipeline -bd -od
  -dataflow -alias -img -seal -conf -compute`; `-py` in the flags ⇒
  `platform=python`, else `java`.
- **Ab Initio wrapper (`runScript.sh`):** `-c <config_json> -f <fid> -e <env>
  -a <appname> -p <order_prefix> -g "<pset> <graph_flags>" -s <start_delay>
  -t <timeout> -r <resource>`. Splitting the quoted `-g` argument into
  `pset_path` + `graph_flags` **closes the "quoted-argument extraction" item
  that the governance standard lists as out-of-scope (§6)** — it belongs to
  this engine, not the NFR tooling.

**Columns (canonical names align with the R2 variable registry):**

```
launch_detail_sk        IDENTITY PK
invocation_sk           FK -> stg_invocation
run_id, data_center, folder_id, job_id
framework               VARCHAR2(20)     -- DATA_PIPELINE | ABINITIO
platform                VARCHAR2(20)     -- java | python | (null for abinitio)
fid                     VARCHAR2(100)
env                     VARCHAR2(20)
seal                    VARCHAR2(20)
appname                 VARCHAR2(100)
pipeline_id             VARCHAR2(200)
dataflow                VARCHAR2(200)
artifact_uri            VARCHAR2(1000)   -- -img / the -g pset URI
artifact_kind           VARCHAR2(20)     -- jar | wheel | pset
pset_path               VARCHAR2(1000)   -- abinitio: first token of -g
graph_flags             VARCHAR2(1000)   -- abinitio: remainder of -g
conf_path               VARCHAR2(1000)
compute                 VARCHAR2(100)
order_prefix            VARCHAR2(200)    -- abinitio -p (%%JOBNAME-%%ODATE-…)
extra_args_json         CLOB             -- anything the spec didn't name
```

Wide columns for the canonical set + `extra_args_json` overflow was chosen
over an EAV shape: the canonical registry makes the column set stable, and QA
queries in SQL Developer read far better against named columns.

**Launcher-registry changes (`commands.py::LAUNCHER_REGISTRY`):**
- new rule `dt-launcher.sh` → `DATA_PIPELINE` (new invocation_type; add to the
  DDL enumeration comment),
- `runscript.sh` wrapper: keep matching, but when a `.pset`/`.m` argument is
  present the existing script-arg fallback already surfaces it — reclassify
  those from `SHELL_SCRIPT` to `ABINITIO` so they route to the detail parser.

---

## SQL / Python division of labor (unchanged principle, new pieces)

| Side | New work |
|------|----------|
| **SQL (extract)** | job-population extract adding `APPL_TYPE`, `CMD_LINE`, `MEMNAME/MEMLIB` per current-version job (extend `controlm_variables*.sql` companion or new `controlm_jobs.sql`); `IS_CURRENT_VERSION='Y'` filter as established (D4) |
| **Python (parse)** | `filewatch.py` job-grain builder; `launch_detail.py` arg-spec parsers; registry rows; `staging.py` bundle grows `stg_job_filewatch` + `stg_launch_detail`; `normalize-variables` writes the two new CSVs |
| **SQL (staging DDL)** | DDL addendum **Section 7**: two tables + the OS view + indexes (`(data_center, folder_id, job_id)`; `framework`) + grant templates |
| **SQL (QA)** | coverage additions: FileWatch selector-agreement rate; launch-detail fill rate by framework; `-g` split success rate |

## Order of work

1. DDL addendum (Section 7) — tables, view, indexes, grants.
2. `STG_JOB_FILEWATCH` builder + tests (fixture rows exist in
   `drydocs/loaders/sql/controlm_variables_scenarios.sql` scaffold).
3. Registry rows + arg-spec parsers + `STG_LAUNCH_DETAIL` builder + tests
   (mirror `tests/unit/test_command_parser.py`).
4. `STG_JOB_OS_COMMAND_VW`.
5. QA queries; the Phase E unparsed-backlog loop grows the registry as before.

## Gates

Staging-only — no graph writes here. Two HITL questions before Phase D
consumes these tables: (a) FileWatch "last wins" effective-value rule,
(b) `DATA_PIPELINE` as a new invocation_type label (it will surface in the
software-registry Phase 3 invocation-pattern work, which is itself at gate).
