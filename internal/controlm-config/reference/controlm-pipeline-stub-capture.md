# controlm-pipeline-stub — verbatim capture (XML builder + validator package)

**Classification: Internal** (lives under `internal/`, excluded from public push —
carries real folder grammar, server/QR names, repo names, and sample-file names).
**Captured:** 2026-08-04, from 11 screenshots of the package's `detailed-readme.md`
and `AGENT_OVERVIEW.md` (screenshots gitignored in the repo root:
`dpl-plug-agent-detailed-readme*.png`, `dpl-plug-agent-overview*.png`,
`dpl-plug-variables*.png`). Transcription is **verbatim by intent**; where a
screenshot cut a line, the cut is marked `[…]`. The package itself lives in the
user's internal repo as a standalone project (`controlm-pipeline-stub`).
**Companion:** the integration backlog plan at
[`../controlm-pipeline-stub-integration-plan.md`](../controlm-pipeline-stub-integration-plan.md).
**Sibling capture:** [`controlm-job-metadata-standards-capture.md`](controlm-job-metadata-standards-capture.md)
(2026-08-11, C29) — the standards the generator is being asked to satisfy: REQ-1…REQ-4,
NFR-CTM-001 v2, and three description/file-name/route standards. It is the *target*
to this file's *as-built*, and the two `DESCRIPTION` string literals recorded below
are exactly where they conflict.

---

## A. What the package is (AGENT_OVERVIEW.md §1)

`controlm-pipeline-stub` is a **standalone, Python-first integration scaffold**
that reproduces the *entire* JPMC DPL **Control-M processing lifecycle** in one
runnable project:

```
config → generate → validate → upload → runtime-trigger
```

It exists because that lifecycle is spread across 4 languages and 3+ repos in
production (Java, Groovy, shell, Python). The project **re-implements all of it
in Python**, preserving the real class shapes, argument contracts, endpoint
URLs, and the two verbatim Control-M `DESCRIPTION` string literals — with live
side-effects (Spark, ITPAM REST, Control-M) replaced by `# TODO(integration):`
guarded stubs.

- **Fidelity level:** *integration scaffold* — real shapes, stubbed bodies. NOT
  a production deployment tool and NOT a pure mock/demo.
- **Status:** complete and green — 14/14 tests pass; CLI works end-to-end for
  all 5 stages. Built/tested on **Python 3.12**.

### Stage map (production source of truth per stage)

| Stage | This project | Real origin (repo / class) |
|---|---|---|
| 1 Config | `config/` | `io.dpl.model.Job.JobConfig` + DryDocs `ingestion-config.yaml` |
| 2 Generate | `model/`, `jobs/`, `generator/` | `CCBDLENS/dplplugin` `io/dpl/model/controlm/*`, `io/dpl/model/Job/*`, `io/dpl/utils/ControlMUtils.java` |
| 3 Validate | `validation/`, `schema/Folder.xsd` | JGL DAL `ba0.sh` (CR### rules) + `ControlMValidations.groovy` |
| 4 Upload | `deploy/` | JGL `ITPAMapiModel.groovy` / `ControlM.groovy` |
| 5 Runtime | `runtime/` | `DPL/datapipeline-launcher-core-sdk` `DataLauncher → ExecutionProcessor → SparkBatchProcessor → ZiloUserDefinedTransformationProcessor`; shell `dpl_spark_processor.sh` |

> **Provenance:** distilled from `DryDocs/internal/controlm-config/reference/DPL-CONTROLM-TRACE-FINDINGS.md`
> and the JGL DAL guide `.../jules-global-library/jules-guide-readme.md`.

### The two literals that must never drift

Defined once in `src/controlm_pipeline/__init__.py` and asserted by tests:

- `FOLDER_DESCRIPTION = "Generated Control-M Folder"` (folder header —
  `ControlMUtils.java:885`)
- `AWS_TRANSFORM_JOB_DESCRIPTION_PREFIX = "Generated job to trigger DPL
  transformation in AWS for dataset: "` (job —
  `AwsTransformationTrigger.getDescription()`)

### How to run (AGENT_OVERVIEW.md §2)

```powershell
python -m venv .venv                  # use Python 3.12 (NOT 3.14 — see gotchas)
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt       # lean core (no pyspark)
pip install -e .[dev]                 # + pytest/ruff/mypy
pytest -q                             # 14 tests

controlm-pipeline generate --dataset MSP465_OLD_NEW_FILE --out out
controlm-pipeline validate out\<folder>.generated.xml --report out\report
controlm-pipeline upload   out\<folder>.generated.xml --server PRECO-VSI-COMP
controlm-pipeline run --pipeline-id <uuid> --dataset-id <id> \
    --business-date 20260803 --odate 20260803 --job-id PRSRVD0050 \
    --flow-definition resources\flow_definition.json
```

`pip install -e .[runtime]` adds **pyspark** (secondary/optional) for the real
SparkSession path; without it Stage 5 runs a pure-Python stub.

---

## B. Stage 2 (Generate) — attribute & element reference (detailed-readme.md)

### B0. Mental model: `%%TOKENS` are Control-M runtime variables

Anything of the form `%%NAME` is a **Control-M auto-edit / global substitution
token**. The Python generator writes these **literally** into the XML via
`make_element` (which only stringifies). They are resolved **at Control-M job
execution time**, never by `model/`, `jobs/`, or `generator/`. Example: a
`DOMAIL SUBJECT="%%JOBNAME failed …"` is emitted verbatim; Control-M swaps
`%%JOBNAME` / `%%ODATE` / etc. when the job actually runs.

### B1. `model/` — the XML nodes and every attribute each emits

**`DEFTABLE` root — `model/deftable.py`**

| Attribute / part | Value | Source |
|---|---|---|
| `xmlns:xsi` | `http://www.w3.org/2001/XMLSchema-instance` | constant nsmap |
| `xsi:noNamespaceSchemaLocation` | `Folder.xsd` | `schema_location` field |
| `<?xml?>` decl + `<!--Exported at DD-MM-YYYY HH:MM:SS-->` | timestamp | `exported_at` (defaults `datetime.now()`) |

**`SMART_FOLDER` — `model/smart_folder.py`** — populated dynamically (from the
`SmartFolder` dataclass fields, set by the generator):

| Attribute | Fed from |
|---|---|
| `JOBISN` | `job_isn` (folder = `1`) |
| `APPLICATION` | `application` |
| `SUB_APPLICATION` | `sub_application` (= folder name) |
| `JOBNAME` | `folder_name` |
| `DESCRIPTION` | `description` (the `"Generated Control-M Folder"` literal) |
| `CREATED_BY` | `created_by` |
| `RUN_AS` | `run_as` |
| `PRIORITY` | `priority` |
| `NODEID` | `node_id` |
| `JOBS_IN_GROUP` | **computed** `len(self.jobs)` → `%05d` |
| `PARENT_FOLDER` | `parent_folder` |
| `DATACENTER` | `data_center` |
| `FOLDER_NAME` | `folder_name` |

**Hard-coded constants** always emitted: `CRITICAL=0`, `TASKTYPE="SMART Table"`,
`CYCLIC=0`, `INTERVAL=00001M`, `CONFIRM=0`, `MAXWAIT=5`, `AUTOARCH=1`,
`DAYS=ALL`, `DAYS_AND_OR=O`, `SHIFT="Ignore Job"`, `SYSDB=1`, `ADJUST_COND=N`,
`IND_CYCLIC=5`, `APPL_TYPE=OS`, `USE_INSTREAM_JCL=N`, `PLATFORM=UNIX`,
`TYPE=2`, `ENFORCE_VALIDATION=N`.

**`JOB` — `model/job.py`** — populated dynamically (from the `Job` dataclass,
set by each builder):

| Attribute | Fed from |
|---|---|
| `JOBISN` | `job_isn` (jobs = `2..n`) |
| `APPLICATION` | `application` |
| `SUB_APPLICATION` | `sub_application` (= parent folder) |
| `JOBNAME` | `job_name` |
| `DESCRIPTION` | `description` (builder's `get_description()`) |
| `CREATED_BY` | `created_by` |
| `RUN_AS` | `run_as` |
| `PRIORITY` | `priority` (default `JA`) |
| `TASKTYPE` | `task_type` (default `Command`; `Detached` for file-watcher) |
| `NODEID` | `node_id` |
| `CMDLINE` | `cmd_line` |
| `APPL_TYPE` | `appl_type` (default `OS`) |
| `PARENT_FOLDER` | `parent_folder` |

**Constants:** `CRITICAL=0`, `CYCLIC=0`, `INTERVAL=00001M`, `CONFIRM=0`,
`RETRO=0`, `MAXWAIT=5`, `MAXRERUN=0`, `AUTOARCH=1`, `DAYS=ALL`,
`DAYS_AND_OR=O`, `SHIFT="Ignore Job"`, `SYSDB=1`, `IND_CYCLIC=S`,
`USE_INSTREAM_JCL=N`, `END_FOLDER=N`.

**Child order (fixed):** `VARIABLE*` → `INCOND*` → `QUANTITATIVE*` →
`OUTCOND*` → `ON*`.

### B2. Folder → job inheritance (what is actually pushed vs. shared)

The generator passes only **two** things from the folder assembly into each job
builder (`generator/controlm_generator.py`):
`builder.build(job_isn=offset, parent_folder=folder_name)`. Everything else the
job and folder share is **not** read off the `SMART_FOLDER` object — each
builder re-reads it from the same `JobConfig`.

| JOB attribute | Source | Relationship to folder |
|---|---|---|
| `SUB_APPLICATION` | `parent_folder` arg = `folder_name` | **Pushed from folder** (generator → builder) |
| `PARENT_FOLDER` | `parent_folder` arg = `folder_name` | **Pushed from folder** (same `folder_name`) |
| `JOBISN` | `job_isn` = offset `2..n` | Generator-sequenced (not a folder value) |
| `APPLICATION` | `config.application` | Shared source (`JobConfig`) — matches folder, not read from it |
| `RUN_AS` | `config.run_as` | Shared source (`JobConfig`) |
| `NODEID` | `config.node_id` | Shared source (`JobConfig`) |
| `CREATED_BY` | `dataset.fid.lower()` | Shared source (`JobConfig`) |
| `PRIORITY` | `config.priority` (default `JA`) | Shared source (`JobConfig`) |
| `JOBNAME`, `DESCRIPTION`, `CMDLINE`, `TASKTYPE` | builder `get_job_name()` / `get_description()` / cmd / `task_type` | Job-only (no folder counterpart) |

> **Net:** the folder only contributes its `folder_name` to each job (as
> `SUB_APPLICATION` + `PARENT_FOLDER`). The apparent inheritance of
> `APPLICATION`/`RUN_AS`/`NODEID`/`CREATED_BY`/`PRIORITY` is really both reading
> the same `JobConfig`. The real `ControlMUtils` does the same — folder and job
> attributes are set independently from the job config, not copied folder→job.

### B3. Child elements (attributes each populates)

| Node | File | Attributes |
|---|---|---|
| `VARIABLE` | `model/variable.py` | `NAME`, `VALUE` |
| `INCOND` | `model/conditions.py` | `NAME`, `ODATE` (=`ODAT`), `AND_OR` (=`A`) |
| `OUTCOND` | `model/conditions.py` | `NAME`, `ODATE` (=`ODAT`), `SIGN` (=`+`) |
| `QUANTITATIVE` | `model/quantitative.py` | `NAME`, `QUANT` (=`1`), `ONFAIL` (=`R`), `ONOK` (=`R`) |
| `ON` | `model/on_do.py` | `STMT` (=`*`), `CODE` (=`NOTOK`) |
| `DOMAIL` | `model/on_do.py` | `URGENCY`, `DEST` (=`%%NOTIFY`), `SUBJECT`, `MESSAGE`, `ATTACH_SYSOUT` |

### B4. `jobs/` — where each `VARIABLE` is created + per-builder detail

`Variable(name, value)` just emits `<VARIABLE NAME=… VALUE=…/>`; it holds **no
defaults**. All values are set inside each builder's `variables=[…]` list. Job
names come from `jobs/base.py` `get_job_name()` =
`{APP[:4]}{FREQ}{JOB_NUM}_{SOR}_{DATASET}_AWS_{SUFFIX}`
(e.g. `PRSRD0020_MSP465_MSP465_OLD_NEW_FILE_AWS_PLCT`).

| Builder | `JOB_NUM`/`SUFFIX` | DESCRIPTION | VARIABLEs (NAME → VALUE) | INCOND | QUANTITATIVE | OUTCOND | ON/DOMAIL |
|---|---|---|---|---|---|---|---|
| `jobs/aws_transformation_trigger.py` | `0051`/`TRUST` | `"Generated job to trigger DPL transformation in AWS for dataset: <name>"` | `%%DATAFLOW`→`ds.dataset_name`; `%%IMAGE`→`cfg.get_image()`; `%%TIMEOUT`→`"24"`; `%%POLLING_INTERVAL`→`"1"`; `%%PROID`→`%%\\<dataset>\PROID` | `PL-…_AWS_PLCT-OK` | `PRSRV-HL-QR`, `PRDCL-DAT-DCL-VSI`, `PRECO-COMPUTE-CTRL-VSI` | `PL-<jobname>-OK` | **2** (generic + "AWS Provisioning Failed") |
| `jobs/placement.py` | `0020`/`PLCT` | `"Control-M Placement Job for <name>"` | `%%DS_ID`→`ds.dataset_id`; `%%DS_VER`→`ds.dataset_version`; `%%FID`→`ds.fid`; `%%CONF_PATH`→`ds.conf_path`; `%%TIMEOUT`→`"1"`; `%%POLLING_INTERVAL`→`"1"`; `%%BUS_DATE`→`"%%$ODATE"`; `%%ENV`→`ds.env` | `PL-…_DAT_ONPM_FW-OK` | `PRSRV-HL-QR`, `PRDCL-DAT-PLCT-VSI`, `PRECO-COMPUTE-CTRL-VSI` | `PL-<jobname>-OK` | 1 |
| `jobs/ingestion_trigger.py` | `0050`/`INGEST` | `"Trigger Ingestion for Dataset <name>."` | `%%DATAFLOW`→`cfg.get_dataset_name()` | – | – | – | 1 |
| `jobs/aws_provision.py` | `0060`/`PROV` | `"Generated AWS provisioning job for dataset: <name>"` | `%%MANIFEST_FILE`→`"%%\MANIFEST\PATH"` | – | – | – | 1 |
| `jobs/file_mover.py` | `0005`/`MOVE` | `"Move source file to HDFS for dataset: <name>"` | `%%SRC_FILE`→`/apps/cds/sftp/%%SOR/%%FILE`; `%%HDFS_LOCATION`→`/tmp/dpl/%%DATAFLOW` | – | – | – | 1 |
| `jobs/file_watcher.py` | `0001`/`FW` | `"Watch for source file for dataset: <name>"` | `%%WATCH_FILE`→`/apps/cds/sftp/%%SOR/%%FILE`; `%%TIMEOUT`→`"60"` (+ `TASKTYPE=Detached`) | – | – | – | 1 |

`CREATED_BY` on every job = `dataset.fid.lower()`; `RUN_AS`/`NODEID`/
`APPLICATION` come from the shared `JobConfig`.

**⚠ Fidelity gap — undefined CMDLINE tokens.** Each builder's `CMDLINE`
references tokens it does **not** define as a `VARIABLE`. The transform command
uses `%%ENV %%APP_NAME %%ALIAS %%SEAL %%BUS_DATE %%FID %%CONF_PATH` but only
defines `%%DATAFLOW/%%IMAGE/%%TIMEOUT/%%POLLING_INTERVAL/%%PROID`. In real
Control-M those resolve from **folder-level `AUTOEDIT`/`SET VAR` blocks or
global variables** — which the stub does **not** emit. So a generated transform
job is not self-contained; it assumes folder/global vars exist. (The real
`dplplugin` emits those folder AUTOEDIT vars.)

### B5. `ON`/`DOMAIL` — where the values are pulled and used

`DoMail` (`model/on_do.py`) is a dataclass whose **defaults are the
failure-mail template**:

| Attr | Default (source) |
|---|---|
| `DEST` | `%%NOTIFY` — a Control-M var the folder/global is expected to define; **never set by the stub** |
| `SUBJECT` | `"%%JOBNAME failed in %%SCHEDTAB for %%ODATE"` |
| `MESSAGE` | `"00040000"` (Control-M message-table id) |
| `URGENCY` | `"R"` (regular) |
| `ATTACH_SYSOUT` | `"D"` |

`OnStatement` wraps it: emits `<ON STMT="*" CODE="NOTOK">` and appends the
nested `DOMAIL`. One `OnStatement` = one `ON` + one `DOMAIL`.

**How builders use them:**

- **Every builder except the transform job** passes a single
  `OnStatement(do_mail=DoMail())` — all defaults unchanged (generic "job
  failed" email on `NOTOK`).
- **The transform job** is the only one with **two** `ON` blocks (both on
  `CODE="NOTOK"`, so two mails fire on failure):
  1. `OnStatement(do_mail=DoMail())` — generic default mail.
  2. `OnStatement(do_mail=DoMail(subject="AWS Provisioning Failed",
     message="0077%%DATACENTER - AWS Provisioning Job: (%%JOBNAME) failed to
     load data into AWS", attach_sysout="N"))` — **overrides** `subject`,
     `message`, `attach_sysout`; leaves `dest=%%NOTIFY`, `urgency=R` at
     defaults.

**Resolution flow:** builder chooses `DoMail` field values (mostly
`%%`-tokens) → `OnStatement.to_element()` nests `ON`→`DOMAIL` → `make_element`
writes verbatim → Control-M substitutes `%%NOTIFY`, `%%JOBNAME`, `%%SCHEDTAB`,
`%%ODATE`, `%%DATACENTER` at run time. None come from `JobConfig`; the only
config-derived piece is indirect (`%%JOBNAME` resolves to the `JOBNAME` attr
the generator set).

### B6. `generator/` — folder assembly and the fields it fills

`generator/controlm_generator.py` `ControlMGenerator.build(config)`:

- **`folder_name`** ← `config.folder_name` = `f"{application}G-HLDM-{seal}-{sor}_ONF"`
  (drives `SUB_APPLICATION`, `JOBNAME`, `FOLDER_NAME`, `PARENT_FOLDER`, and
  every child job's `SUB_APPLICATION`/`PARENT_FOLDER`).
- **`DESCRIPTION`** ← the `FOLDER_DESCRIPTION` constant `"Generated Control-M Folder"`.
- **`CREATED_BY`** ← `config.dataset.fid.lower()`;
  **`RUN_AS`/`NODEID`/`DATACENTER`/`PRIORITY`/`APPLICATION`** ← merged
  `JobConfig` defaults.
- **`JOBISN` sequencing** — folder = `1`; jobs enumerated `start=2`.
- **Job selection** — iterates `config.dataset.jobs` (the `jobs:` list in
  `ingestion-config.yaml`), resolves each via `get_builder(job_key)`, appends
  `builder.build(job_isn=offset, parent_folder=folder_name)`.
- **`JOBS_IN_GROUP`** derived at serialize time from `len(folder.jobs)`.
- Wraps folder in `DefTable(folders=[folder])`; `generate_xml()` writes
  `<folder_name>.generated.xml`.

### B7. Known fidelity gaps vs. the real export

1. **`%%NOTIFY` is never assigned** — the stub relies on it existing as a
   folder/global var; a real folder sets it (often the escalation DL from the
   escalation Excel templates in `resources/templates/`).
2. **No folder `AUTOEDIT`/`SET VAR` block** — CMDLINE tokens not in a job's own
   `VARIABLE` list are unresolved in stub output.
3. **Constant fields that are dynamic upstream** — `DAYS`, `TIMEFROM`/`TIMETO`,
   calendar attrs (`RULE_BASED_CALENDARS`) are hard-coded here but vary per
   schedule in the real `dplplugin`/`ControlMUtils`.

---

## C. File-by-file inventory (AGENT_OVERVIEW.md §3)

### Project root

| File | What it is |
|---|---|
| `README.md` | Human-facing intro, install, usage, layout, scope boundaries |
| `AGENT_OVERVIEW.md` | Agent handoff briefing |
| `requirements.txt` | Canonical core dependency list (pyspark deliberately excluded) |
| `pyproject.toml` | Package metadata, `[project.optional-dependencies]` (`runtime`, `dev`), `console_scripts` entry point `controlm-pipeline`, ruff/mypy/pytest config |
| `.gitignore` | Ignores `.venv/`, caches, `out/`, generated XML/reports |
| `env.properties.sample` | Template for git-ignored `env.properties` (ITPAM URL, Control-M server, HDFS/queue) |

### `config/` — runtime config data (not code)

| File | What it is |
|---|---|
| `config/ingestion-config.yaml` | Stage-1 seed: `defaults:` + `sources:`→`datasets:`. Drives generation. **Mirrors the DryDocs internal-twin shape.** |
| `config/logging.yaml` | stdlib logging dictConfig used by structlog |

### `resources/` — fixtures

| File | What it is |
|---|---|
| `resources/sample-xml/PRSRVG-HLDM-25638.xml` | **Verbatim** 17,312-line real Control-M export (2.4 MB, unscrubbed). Golden fixture for the XSD round-trip test. |
| `resources/flow_definition.json` | Sample Zilo declarative transform spec consumed by Stage 5 |

### `scripts/`

| File | What it is |
|---|---|
| `scripts/dpl_spark_processor.sh` | Shell wrapper reproducing the real launcher's arg contract; `exec`'s `python -m controlm_pipeline.runtime.data_launcher "$@"`. Includes the Kerberos-ticket check the real script does. |

### `src/controlm_pipeline/` — the package

| File | Module role |
|---|---|
| `__init__.py` | Package version + the two verbatim DESCRIPTION constants (single source of truth) |
| `cli.py` | **Entry point.** `typer` app with 4 commands: `generate`, `validate`, `upload`, `run`. Thin — delegates to the stage packages. |

**Stage 1 — `config/`:** `config/job_config.py` (pydantic models: `JobFrequency`
enum, `PipelineDetails`, `DatasetConfig`, `JobConfig` — mirrors
`io.dpl.model.Job.JobConfig`; `.folder_name`, `get_dataset_name()` etc.);
`config/loader.py` (`load_ingestion_config`, `load_job_configs` (merges
`defaults:` over each dataset → `JobConfig`), `configure_logging`, `load_env`).

**Stage 2 — `model/` (XML object model):** `model/_base.py` (`XmlNode` protocol
+ `make_element()` helper — lxml element builder, drops `None`);
`model/deftable.py` (`DefTable` = `DEFTABLE` root,
`xsi:noNamespaceSchemaLocation="Folder.xsd"`; `to_xml()` emits the `<?xml?>` +
`<!--Exported at ...-->` preamble); `model/smart_folder.py` (`SmartFolder` =
`SMART_FOLDER` element (folder-level attrs + jobs)); `model/job.py` (`Job` =
`JOB` element (attrs + VARIABLE/INCOND/QUANTITATIVE/OUTCOND/ON children in
stable order)); `model/variable.py` (`Variable` = `VARIABLE` (`%%NAME=VALUE`));
`model/conditions.py` (`InCond`/`OutCond` = `INCOND`/`OUTCOND`);
`model/quantitative.py` (`Quantitative` = `QUANTITATIVE` resource);
`model/on_do.py` (`OnStatement`/`DoMail` = `ON`+`DOMAIL` failure-notify block).

**Stage 2 — `jobs/` (per-job builders):** `jobs/base.py` (`JobBuilder` ABC
(`io.dpl.model.Job.Job` analog) + registry (`@register_builder`,
`get_builder`). Name/prefix helpers.); `jobs/aws_transformation_trigger.py`
(**Key builder** — `JOB_NUM="0051"`; `get_description()` emits the verbatim
AWS-transform literal); `jobs/placement.py` (`JOB_NUM="0020"` placement/token
job (`-p` dt-launcher)); `jobs/ingestion_trigger.py` (ingestion trigger job);
`jobs/aws_provision.py` (provisioning job (DB load, no transform));
`jobs/file_mover.py` (Dropbox→HDFS copy job); `jobs/file_watcher.py`
(file-arrival watch job).

**Stage 2 — `generator/`:** `generator/controlm_generator.py` (`ControlMUtils`
analog. `ControlMGenerator.build(config)` assembles the folder (sets
`FOLDER_DESCRIPTION`) + one job per `dataset.jobs` key → `DefTable`.
`generate_xml()` writes the file.)

**Stage 3 — `validation/`:** `validation/rules.py` (CR### rule **registry**.
Implements CR015a (ctmag), CR041 (folder naming), CR042 (job naming), CR050
(app-code prefix), CR060 (NODEID known), CR070 (failure DOMAIL present). Loads
reference lists. `RuleResult` dataclass.); `validation/validator.py` (runs the
registry + optional `Folder.xsd` validation → `ValidationReport` (`.passed`,
`.failures`, `to_html`/`to_json`). `validate_file`, `write_report`.);
`validation/reference/folder_prefixes.txt` (valid 3-char app codes
(`FolderPrefixList` analog)); `validation/reference/servers.txt` (known
NODEID/servers (`ServerList` analog));
`validation/reference/high_priority.txt` (high-priority folder prefixes
(`HighPriorityList` analog)); `schema/Folder.xsd` (**lenient reference subset**
of the Control-M folder schema. Requires `DEFTABLE` root + `SMART_FOLDER`
`APPLICATION`/`FOLDER_NAME`; `DESCRIPTION` optional (nested folders omit it);
`anyAttribute`/`xs:any` lax elsewhere so BOTH generated and the real 17k-line
export validate.)

**Stage 4 — `deploy/`:** `deploy/itpam_client.py` (`ItpamClient`
(`ITPAMapiModel.groovy` analog). `upload_xml` (XML_VALIDATION_AND_UPLOAD),
`delete_folders` (batched by 10, `FOLDER_DELETE_BATCH`),
`update_escalation_db`. Kerberos/SPNEGO auth (guarded import). `dry_run=True`
by default — real HTTP only when disabled.)

**Stage 5 — `runtime/`:** `runtime/data_launcher.py` (`DataLauncher` analog +
the **argument contract** (`--pipeline-id`, `--odate`, `--aws`, `--queue-name`
default `ccb_etl_dynamic`, `--spark-params`, …). `parse_args`, `run`, `main`
(exit code).); `runtime/execution_processor.py` (`ExecutionProcessor.process()`
analog — logs identifiers, runs processor, maps exceptions→1, always
`stop()`.); `runtime/spark_batch_processor.py` (`SparkBatchProcessor.run()` —
initSession → read → branch (PROVISIONING vs transform) → write. **Lazy/guarded
pyspark import**; `_StubSparkSession` fallback.); `runtime/reader.py` (`Reader`
ABC + `StubReader` (in-memory rows)); `runtime/writer.py` (`Writer` ABC +
`StubWriter` (logs + row count)); `runtime/zilo_transformer.py`
(`ZiloTransformer` — declarative JSON flow (NOT reflective JAR load, per the
trace correction); `initialize`/`set_configuration`/`transform`.)

### `tests/`

| File | Covers |
|---|---|
| `tests/conftest.py` | Paths (`SAMPLE_XML`, `FLOW_DEF`, `INGESTION_CONFIG`) + `job_config` fixture |
| `tests/test_generator.py` | Both verbatim DESCRIPTION literals, DEFTABLE preamble, file write |
| `tests/test_validation.py` | Generated XML passes rules+XSD; **real sample validates vs XSD**; ctmag + app-code negative cases |
| `tests/test_deploy.py` | ITPAM dry-run; folder-delete batching (23→3 requests) |
| `tests/test_runtime.py` | Arg contract; transform run **without pyspark**; provisioning branch; stub-session fallback |

### Data / control flow (one line per hop)

```
ingestion-config.yaml —(loader)→ JobConfig
  └—(ControlMGenerator + JobBuilder registry)→ DefTable→SmartFolder→Job tree
      └—(DefTable.to_xml / lxml)→ <folder>.generated.xml
          └—(validator + Folder.xsd + CR### rules)→ ValidationReport (html/json)
              └—(ItpamClient.upload_xml, Kerberos, dry-run)→ Control-M server [stub]
  ... at Control-M run time ...
  dpl_spark_processor.sh → data_launcher → ExecutionProcessor
      └→ SparkBatchProcessor (read → ZiloTransformer.transform → write) → exit code
```

### Third-party packages

Core (`requirements.txt`): `lxml` (build/serialize Control-M XML; XSD
validation — `model/*`, `validation/validator.py`), `pydantic` v2 (typed
config models — `config/job_config.py`), `PyYAML` (parse ingestion/logging
YAML), `requests` (ITPAM REST calls), `requests-gssapi` (Kerberos/SPNEGO auth,
guarded — needs MIT KfW on Windows), `typer` (>=0.15, CLI), `click` (8.x,
transitive), `jsonschema` (validate Zilo `flow_definition.json` — extension
point), `python-dotenv` (load `env.properties`), `structlog` (structured
logging, all stages). Optional `[runtime]`: `pyspark` (secondary — real
SparkSession path). Dev `[dev]`: `pytest`, `pytest-cov`, `ruff`, `mypy`.
Stdlib notably: `argparse` (launcher arg contract), `dataclasses`, `abc`,
`enum`, `pathlib`, `re`, `json`.

### Gotchas / constraints for the next agent (AGENT_OVERVIEW.md §6)

1. **Use Python 3.12.** On 3.14 there are no prebuilt `lxml`/`pydantic-core`
   wheels → source build fails without a C/Rust toolchain.
2. **typer must be ≥0.15.** typer 0.12 + click 8.2/8.4 raises *"Secondary flag
   is not valid for non-boolean flag."*
3. **`requests-gssapi` imports fail on Windows without MIT KfW** — expected and
   **guarded**; `ItpamClient` degrades to no-auth dry-run. Don't "fix" it by
   making it a hard dependency.
4. **`Folder.xsd` is intentionally lenient.** Tightening it (e.g. making
   `DESCRIPTION` required) breaks validation of the real sample export, which
   has nested `SMART_FOLDER`s without a description.
5. **CR### rules are a registry with ~6 of ~50 rules.** Add more by decorating
   a function with `@register_rule("CRxxx")` in `validation/rules.py`.
6. **All live side-effects are `# TODO(integration):` stubs.** To go live: drop
   `ItpamClient.dry_run`, install `[runtime]` for real Spark, and point
   `env.properties` at real ITPAM/Control-M hosts.
7. **The sample XML is unscrubbed** (real SIDs/FIDs/paths) — treat as
   Internal-Confidential; do not publish externally.

### Suggested first tasks (if extending) — from the package itself

- Add more CR### rules to reach parity with `ba0.sh`.
- Wire `jsonschema` validation of `flow_definition.json` into `ZiloTransformer`.
- Implement a real `Reader`/`Writer` pair behind the `[runtime]` extra.
- Add a `generate --all` mode to emit every dataset in the config.
