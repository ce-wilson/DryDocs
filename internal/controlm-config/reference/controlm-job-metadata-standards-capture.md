# Control-M job metadata standards — verbatim capture (requirements + four standards pages)

**Classification: Internal** (lives under `internal/`, excluded from public push — carries real
support DL addresses, an MFT service account, the artifact-repository and source-control hosts,
the internal plugin repo/package names, real SEAL-shaped folder and job names, and a named
executive).
**Captured:** 2026-08-11, from 22 screenshots of a Confluence space (breadcrumb visible on
several screens: `Pages / CBTHLTAUTO Home / CBT-Standards and governance (WIP-DRAFT)`).
Screenshots are gitignored in the repo root by the `/*.png` rule:
`job-req-1.png`, `job-req-2.png`, `job-variable-1.png` … `job-variable-20.png`.
Transcription is **verbatim by intent**; where a screenshot cut a line or a table column, the
cut is marked `[…]`. Source-document errors are transcribed as written and marked `[sic]` —
they are not silently corrected, because the errors are evidence about the source's maturity.
**Companion:** the DPL generator this standard is aimed at is captured at
[`controlm-pipeline-stub-capture.md`](controlm-pipeline-stub-capture.md), with its integration
plan at [`../controlm-pipeline-stub-integration-plan.md`](../controlm-pipeline-stub-integration-plan.md).
The two describe the same Control-M generation lifecycle from opposite ends: that pair is *what
the generator emits today*, this file is *what the standard says it should emit*.
**Backlog:** C29 (capture, audit, register) · G66 (the DESCRIPTION read seam).

## Source-document map

| Part | Screens | Document | Sections captured |
|---|---|---|---|
| **A** | `job-req-1..2` | REQ-1 … REQ-4 (requirements page) | all four requirements, complete |
| **B** | `job-variable-1..4` | **NFR-CTM-001 v2** — Control-M Command-Line & Variable Naming Convention | §1, §2, §3, §5, §6.1–6.5, §7.1–7.2, §8, §9, §10 — **§4 NOT CAPTURED** |
| **C** | `job-variable-5..9` | File Name Component Standard — Variable Naming | §1–§9, complete |
| **D** | `job-variable-10..14` | MFTS Route IDs — Table & DPROD Extension | §1–§8, complete |
| **E** | `job-variable-15..20` | Source Contact & PDN Downstream | §1–§8, complete |

> ⚠️ **Known hole — NFR-CTM-001 §4 was never screenshotted.** `job-variable-1` ends at §3 and
> `job-variable-2` opens at §5. §4 is, by every reference to it, **the canonical variable
> registry** — §2 defines "canonical variable" as one "whose name appears in the canonical
> registry", §5 maps those names to `fact_type` values, and §8 says `variables.py FACT_REGISTRY`
> "adds canonical names + aliases". The registry table itself is therefore the one normative
> artifact of this document that is **not in hand**. Anything below that appears to enumerate
> canonical names is inferred from §5/§6/§8, not read from §4.

---

# Part A — REQ-1 … REQ-4 (`job-req-1.png`, `job-req-2.png`)

## REQ-1  Enhance Folder & Job level metadata

**Folder Variables — Folder Meta Data, add the Name placeholder for the developer to fill out
later.**

**Background:** Given that the Data & Analytics space uses a platform Control-m app code, the
folder ownership is often difficult to determine. SEAL_ID is in the name of the folder, but used
inconsistently. The developers devx project key should be used to determine ownership.

Add a Folder-level metadata VARIABLES (as opposed to per-job variables) — these carry
folder/onboarding meta such as the DevX project key.

**Folder metadata variables**

Folder-level metadata VARIABLES (as opposed to per-job variables) — folder / onboarding meta
such as the DevX project key and the support-email DLs. For all rows Node = VARIABLE,
File = `model/variable.py`.

| # | Variable | Meaning |
|---|---|---|
| 1 | `NAME=DevX-project` → `VALUE` *(example: AUTOORIGRA)* | DevX project key |
| 2 | `NAME=L2_EMAIL_DL_NM` → `VALUE=L2_support@restricted.chase.com` | Email — L2 support DL (if more than one, separate by semicolon) |
| 3 | `NAME=L3_EMAIL_DL_NM` → `VALUE=L2_support@restricted.chase.com; other_interested_people@restricted.chase.com` | Email — L3 support DL (if more than one, separate by semicolon) |

**Acceptance criteria**
1. The folder variables should contain the developers project key.
2. L2 & L3 contacts are added, **but not called in "Shout"**

> Transcription note: row 3's `L3_EMAIL_DL_NM` example value begins with the **same address** as
> row 2's `L2_EMAIL_DL_NM` (`L2_support@…`). Read verbatim, not normalized — whether that is a
> copy-paste artifact in the source or a deliberate "L3 includes L2" convention is unresolved.

## REQ-2  HIGH — Remove the Control-M "Shout" notifications

**Requirement:** The generated Control-M folder/job XML must **no longer emit Control-M "Shout"
notifications** (the `<SHOUT>` element and the DO SHOUT action `<DOSHOUT>`). Email notifications
(`<DOMAIL>`) are out of scope for this requirement and remain (see S9).

**Background:** Email Control-m shouts are not the driving action for Incident resolution, the
Service Now incident serves that purpose. I've also attached Lori Beer's directive last year to
turn off shouts in all lower env.

**Context (from S9 — Notifications)**

Control-M supports two notification mechanisms on a job/folder:

- **Shout** — `<SHOUT>` (time/state-based, e.g. late/early) and `<DOSHOUT>` (a DO SHOUT action
  fired from an ON condition). Routes a message to a Control-M shout destination / console / DL.
  **This is what REQ-1 removes.** `[sic — the surrounding requirement is REQ-2]`
- **Mail** — `<DOMAIL>` nested in `<ON STMT="*" CODE="NOTOK">` (the failure email; defaults
  `DEST=%%NOTIFY`, `SUBJECT="%%JOBNAME failed in %%SCHEDTAB for %%ODATE"`, `MESSAGE=00040000`,
  `URGENCY=R`, `ATTACH_SYSOUT=D`). **Retained.**

**Where "Shout" is generated in the original code (CCBDLENS/dplplugin, bitbucketdc-cluster03)**

Base path: `src/main/java/io/dpl/model/controlm/`

| Class | Role | XML |
|---|---|---|
| `ShoutData.java` | Folder/job-level shout model — time/state-based notification. | `<SHOUT>` |
| `DoShoutData.java` | DO SHOUT action model. Fields: URGENCY, MESSAGE, DEST (all XML attributes). | `<DOSHOUT>` |
| `OnData.java` | The ON element; holds `List<DoShoutData> doShoutData` (mapped `localName="DOSHOUT"`) alongside `List<DoMailData> doMail` (DOMAIL). | `<ON>...<DOSHOUT>` |
| `JobData.java` | Job model — carries a job-level SHOUT list (`.shout`). | job `<SHOUT>` |
| `SmartFolder.java`, `SmartTable.java`, `SubFolder.java`, `SubTable.java` | Folder/table containers — each carries a container-level SHOUT list (`.shout`). | folder `<SHOUT>` |

**Note:** The Python stub models **only** the mail path today —
`src/controlm_pipeline/model/on_do.py` (DoMail, OnStatement); there is **no** ShoutData/DoShoutData
equivalent. So in the stub, REQ-1 `[sic — REQ-2]` is already satisfied (no shout is emitted) and
serves as the reference target: the real plugin must be changed to match, i.e. stop populating
ShoutData/DoShoutData and drop the SHOUT/DOSHOUT lists from OnData, JobData, and the folder/table
containers above.

**Acceptance criteria**
1. Generated XML contains **zero** `<SHOUT>` and `<DOSHOUT>` elements for all job types.

## REQ-3  Medium — Add a post-command to the file_watcher job

**Requirement:** For job type `file_watcher`, add a post-command that reads the arrival token
file. This introduces two job VARIABLEs (`%%POSTCMD` and `%%FileWatch-FILE_PATH`) so the watcher
can emit / confirm the token path after the watched file arrives.

**Background:** The file watcher jobs do not log the counts of the files. The first opportunity
to read the file is after it's landed in the S3 bucket. Adding the Linux cat cmd to the file path
adds the count to the log in order for it to be searchable in Splunk.

**VARIABLE additions (to insert on the file_watcher JOB)**

Order matters: define `%%FileWatch-FILE_PATH` **first**, then `%%POSTCMD` **cats the value from
the previous variable** (it references `%%FileWatch-FILE_PATH` rather than repeating the literal
path).

**Variables to populate** — Numbered table (Child-Elements style) — populate with the VARIABLE
name / value pairs to add for `file_watcher`.

| # | Node | File | Variable |
|---|---|---|---|
| 1 | VARIABLE | `model/variable.py` | `NAME=%%FileWatch-FILE_PATH` → `VALUE=%%DROPBOX/%%FILE_NM_PREFIX.%%$NEXT..tok` |
| 2 | VARIABLE | `model/variable.py` | `NAME=%%POSTCMD` → `VALUE=cat %%FileWatch-FILE_PATH` *(cats the value from row 1)* |

**Acceptance criteria**
2. If Job type=File Watcher, the contents of the token or control file should be written in the
   Control-M log. `[sic — the list starts at 2; there is no item 1]`

> Transcription note: row 1's value carries a **double dot** before `tok`
> (`…%%$NEXT..tok`). Read verbatim. Under Control-M's concatenation semantics the first `.` is
> the operator and the second is the literal separator — the same dot-smuggling shape the
> description-metadata plan documents as hazard #1, here appearing inside a *new* standard.

## REQ-4  Job metadata standardization

**Job metadata variables — uniform variable set for cmd jobs**

**Requirement:** If job type = `cmd`, pre-populate the associated VARIABLE **names** on the job
so every command job is uniform — the same declared variables regardless of ETL platform. Values
differ per platform (PySpark vs Java); the **names must always be present**. Sourced from
*Control-M Command line and variables v2*.

**PySpark command template (dt-launcher with `-py`)**

**Variables to pre-populate (uniform for every cmd job)** — For all rows Node = VARIABLE,
File = `model/variable.py`. Names are always declared; the PySpark / Java columns show example
values.

| # | NAME | PySpark value | DPL-Zilo value |
|---|---|---|---|
| 1 | `%%LAUNCHER_SCRIPT_PATH` | `/apps/tenants/dpl_utils/dt-accelerators/dt-launcher.sh` (same) | |
| 2 | `%%ETL_ARTIFACT_URI` | `Artifactory pypi/…/foo-0.1.22-py3-none-any.whl` | `Artifactory maven/…/bar-1.4.0.jar` |
| 3 | `%%ETL_PLATFORM` | `pyspark` | `Zilo or java?` |
| 4 | `%%ETL_ARTIFACT_KIND` | `wheel` | `jar` |
| 5 - optional | `%%ETL_PLATFORM_FLAGS` | `-py` | `(empty)` |

> Transcription note: row 3's DPL-Zilo cell is the literal string `Zilo or java?` — an
> unresolved question left in the table, not a value. Row 1's DPL-Zilo cell is empty; the
> PySpark cell's trailing "(same)" implies the two share the launcher path.

---

# Part B — NFR-CTM-001 v2 — Control-M Command-Line & Variable Naming Convention (`job-variable-1..4`)

> **Owner:** Control-M ontology working group **Audience:** Control-M job authors, ETL platform
> engineers, DPL/CDS pipeline owners **Applies to:** All new Control-M jobs and any job
> undergoing material refactor.

## §1 Purpose & Scope

This document defines the **non-functional requirements** for naming Control-M variables and
structuring command lines that reference ETL artifacts (wheels, jars, container images, psets,
ksh scripts) and their launcher entrypoints (`dt-launcher.sh`, `runScript.sh`,
`ICDW_etl_run_interface.ksh`, etc.).

It is a **standards document**, not a behavioral specification. It defines what to name things,
what shape they must have, and how the platform tooling will treat them. It does not specify what
your job does at runtime.

**In scope**
- Canonical variable names that identify platform, launcher, payload artifact, and platform flags.
- Casing, character set, and alias conventions.
- Required ontology shape produced from those variables (single `:Script` node, role property,
  `INVOKES` / `USES_ARTIFACT` edges).
- Reference command-line templates for the four supported launcher patterns.

**Out of scope (see §11)** `[sic — the out-of-scope section is §10]`
- Inferring canonical values by parsing legacy `CMDLINE`, `MEMNAME`, `MEMLIB`, `Task JSON Path`,
  `PRECMD`/`POSTCMD`, or `PARM1`–`PARMn` fields when canonical variables are absent.
- Plug-in tasks (`APPL_TYPE ∈ AWS, AZURE, GCP, SDK`) that carry no `CMDLINE`.
- Container-image registry URI shape validation.
- Folder-name signal mining.

## §2 Definitions

| Term | Definition |
|---|---|
| **Canonical variable** | A `%%`-prefixed Control-M auto-edit variable whose name appears in the canonical registry. Uppercase. |
| **Alias** | A historical or team-specific variable name registered as a synonym for a canonical variable. |
| **Launcher** | The script executed directly by Control-M / shell that hosts the invocation interface (flags). |
| **Payload artifact** | The file or identifier that the launcher dispatches, loads, or references (wheel/jar/pset/triple). |
| `**fact_type**` | The 30-char enumerated key on `STG_APP_FACT` that identifies the semantic role of a value. `[sic — the asterisks are literal in the source cell]` |

## §3 Ontology Overview

The Control-M ontology classifies the runtime universe into five active node labels —
`ControlMJob` (Activity), `ControlMFolder` (Collection), `ControlMServer` (local
infrastructure), `Condition` (Entity), `JobRun` (Activity) — and the supporting set `Script`,
`ETLProcess`, `ExecutionHost`, `AppUser`.

This NFR introduces **no new node labels**. It refines the `:Script` node by:
- Splitting it via a property `script_role ∈ {launcher, payload}`.
- Adding properties `platform`, `artifact_uri`, `artifact_kind`, `platform_flags`, `script_path`,
  plus four Informatica-specific identifiers (`infa_interface_local`, `infa_interface_global`,
  `infa_job`, `infa_database`).

It defines three relationship semantics:

| Edge label | From | To | PROV matrix row | PROV mapping |
|---|---|---|---|---|
| `INVOKES` | `ControlMJob` | `Script {script_role: launcher}` | Activity → Entity | `prov:used` |
| `USES_ARTIFACT` | `ControlMJob` | `Script {script_role: payload}` | Activity → Entity | `prov:used` |
| `TRIGGERS` | `Script {script_role: payload}` | `ETLProcess` | Entity → Activity *(graph-inverse for ergonomics)* | `prov:wasStartedBy` *(direction-inverted)* |

Distinct labels (`INVOKES` vs `USES_ARTIFACT`), not single-label-with-role, are used to avoid the
documented `RUNS_ON` overload risk.

## §4 — **[NOT CAPTURED]**

No screenshot covers §4. See the warning at the head of this file: this is the canonical variable
registry, referenced by §2 ("appears in the canonical registry"), §5, and §8.

## §5 Ontology Mapping Summary

| Variable | `STG_APP_FACT.fact_type` | Drives ontology output |
|---|---|---|
| `%%ETL_PLATFORM` | `ETL_PLATFORM` | `:Script.platform` on both launcher and payload nodes |
| `%%LAUNCHER_SCRIPT_PATH` | `LAUNCHER_PATH` | `MERGE :Script {script_role:launcher, script_path:<value>}` + `:INVOKES` |
| `%%ETL_ARTIFACT_URI` | `ARTIFACT_URI` | `MERGE :Script {script_role:payload, artifact_uri:<value>}` + `:USES_ARTIFACT` |
| `%%ETL_ARTIFACT_KIND` | `ARTIFACT_KIND` | `:Script.artifact_kind` on payload node |
| `%%ETL_PLATFORM_FLAGS` | `PLATFORM_FLAGS` | `:Script.platform_flags` on launcher node |
| `%%INFA_INTERFACE_LOCAL` | `INFA_INTERFACE_LOCAL` | NODE-KEY component on payload `:Script` for Informatica |
| `%%INFA_INTERFACE_GLOBAL` | `INFA_INTERFACE_GLOBAL` | NODE-KEY component |
| `%%INFA_JOB` | `INFA_JOB` | NODE-KEY component |
| `%%INFA_DATABASE` | `INFA_DATABASE` | `:Script.infa_database` on payload node (variant 2 only) |

## §6 Reference Command-Line Templates

### §6.1 PySpark (dt-launcher with `-py`)

```
%%LAUNCHER_SCRIPT_PATH -fid %%FID -env %%ENV -pipeline %%PIPELINE_ID \
  -bd %%BUS_DATE -od %%ODATE -dataflow %%DATAFLOW -alias %%DATAFLOW \
  -img %%ETL_ARTIFACT_URI -seal %%SEAL %%ETL_PLATFORM_FLAGS -i \
  -conf %%CONF_PATH -compute %%COMPUTE
```

Required folder/job declarations:

```
%%LAUNCHER_SCRIPT_PATH | /apps/tenants/dpl_utils/dt-accelerators/dt-launcher.sh
%%ETL_PLATFORM         | pyspark
%%ETL_ARTIFACT_URI     | https://artifacts.jpmchase.net/artifactory/pypi/.../foo-0.1.22-py3-none-any.whl
%%ETL_ARTIFACT_KIND    | wheel
%%ETL_PLATFORM_FLAGS   | -py
```

### §6.2 Java (dt-launcher without `-py`)

```
%%LAUNCHER_SCRIPT_PATH -fid %%FID -env %%ENV -pipeline %%PIPELINE_ID \
  -bd %%BUS_DATE -od %%ODATE -dataflow %%DATAFLOW -alias %%DATAFLOW \
  -img %%ETL_ARTIFACT_URI -seal %%SEAL -i \
  -conf %%CONF_PATH -compute %%COMPUTE
```

Required declarations:

```
%%LAUNCHER_SCRIPT_PATH | /apps/tenants/dpl_utils/dt-accelerators/dt-launcher.sh
%%ETL_PLATFORM         | java
%%ETL_ARTIFACT_URI     | https://artifacts.jpmchase.net/artifactory/maven/.../bar-1.4.0.jar
%%ETL_ARTIFACT_KIND    | jar
%%ETL_PLATFORM_FLAGS   | (empty)
```

### §6.3 Ab Initio (wrapper runner with embedded `.pset`)

```
sh %%LAUNCHER_SCRIPT_PATH -c %%CONFIG_JSON_PATH -f %%FID -e %%ENV -a %%APPNAME \
  -p %%JOBNAME-%%ODATE-%%ORDERID-%%RUNCOUNT \
  -g "%%ETL_ARTIFACT_URI %%ABINITIO_GRAPH_FLAGS" \
  -s %%START_DELAY -t %%TIMEOUT -r %%RESOURCE
```

Required declarations:

```
%%LAUNCHER_SCRIPT_PATH | /apps/cds/abioncloud/script/runScript.sh
%%ETL_PLATFORM         | abinitio
%%ETL_ARTIFACT_URI     | /home/aiadmin/projects/sandboxes/CDS/sor/.../hlsf_service_territory_ingestion_cdc.pset
%%ETL_ARTIFACT_KIND    | pset
%%ETL_PLATFORM_FLAGS   | (empty)
```

### §6.4 Informatica — variant 1 (interface identifiers only)

```
%%LAUNCHER_SCRIPT_PATH -S %%SRC_SYS_CD -I %%INFA_INTERFACE_LOCAL \
  -G %%INFA_INTERFACE_GLOBAL -F %%FREQUENCY -J %%INFA_JOB
```

Required declarations:

```
%%LAUNCHER_SCRIPT_PATH  | /etlapps/icdw/prod/ops/Scripts/ICDW_etl_run_interface.ksh
%%ETL_PLATFORM          | informatica
%%ETL_ARTIFACT_URI      | (empty)
%%ETL_ARTIFACT_KIND     | other
%%INFA_INTERFACE_LOCAL  | ICDW_OBE_FRW_EXT_BB
%%INFA_INTERFACE_GLOBAL | ICDW_OBE_FRW_GBL
%%INFA_JOB              | PICDDXL31_FRW_BB_OB_EXTRACT_DLY
```

### §6.5 Informatica — variant 2 (interface identifiers + `-D` database)

```
%%LAUNCHER_SCRIPT_PATH -S %%SOR_SYS_CD -F %%FREQUENCY \
  -I %%INFA_INTERFACE_LOCAL -G %%INFA_INTERFACE_GLOBAL -D %%INFA_DATABASE
```

Adds the following to the variant-1 declaration set:

```
%%INFA_DATABASE | ICTL_ERRAUD_T
```

> Transcription note: §6.4 uses `%%SRC_SYS_CD`, §6.5 uses `%%SOR_SYS_CD`. Both read as written —
> whether this is drift or two genuinely different variables is unresolved in the source.

## §7 Migration Examples

### §7.1 Existing job with `%%img_path` (lowercase, alias)

| Status | Job declares | Tooling result |
|---|---|---|
| Today | `%%img_path = .../foo.whl` | No `STG_APP_FACT` row (case miss). No `:Script` payload node. |
| Migrate | Rename to `%%IMG_PATH = .../foo.whl` | Alias `IMG_PATH → ARTIFACT_URI`. WARN logged. Node materializes. |
| Final | Rename to `%%ETL_ARTIFACT_URI = …` | Canonical. No WARN. |

### §7.2 Existing job with `%%IMAGE`

| Status | Job declares | Tooling result |
|---|---|---|
| Pre-NFR | `%%IMAGE = .../foo.whl` | `fact_type=IMAGE` (prior schema). |
| Post-NFR | Same job, no change | `fact_type=ARTIFACT_URI`. Same row, new label. WARN suggests rename. |

## §8 Tooling Behaviour

| Component | Behavior |
|---|---|
| `variables.py FACT_REGISTRY` | Adds canonical names + aliases. The standalone `IMAGE → IMAGE` mapping is removed and replaced with `IMAGE → ARTIFACT_URI`. |
| `staging.py` | `build_app_fact_rows()` writer emits `STG_APP_FACT` for any classified variable with `fact_type ≠ None` and `is_fully_resolved`. |
| DDL `controlm_staging_ddl.sql` | `fact_type` enumeration comment updated; `IMAGE` removed; new types added. |
| `m7_etl_artifact_supplement.cypher` | Declares `:LocalRelationship` for `INVOKES`, `USES_ARTIFACT`; `:MAPS_TO → prov:used`. |
| Loader `controlm_etl_artifacts.py` | Reads `STG_APP_FACT`, MERGEs `:Script` + edges per §5. |
| `m7-verify` | Enforces NF-VAL-1 through NF-VAL-7. |
| `audit-variable-aliases` CLI | Implements NF-AUD-2 and NF-AUD-3. |

> The NF-VAL-1…7 and NF-AUD-1…3 requirement bodies are **not captured** — they are referenced
> here and (presumably) defined in the uncaptured §4 or an adjacent section.

## §9 Decision Log

| Decision | Status | Rationale |
|---|---|---|
| `%%IMAGE` rolls up to `ARTIFACT_URI` (clean break, no dual-write) | Accepted | Drop-and-recreate Neo4j workflow makes the migration cost zero. The `STG_APP_FACT` writer is new, so no production consumer of the old `IMAGE` `fact_type` exists. |
| Canonical names are uppercase ASCII; lookup case-sensitive | Accepted | Control-M variables are case-sensitive at execution; normalizing the registry would silently merge intentionally distinct bindings. WARN is preferred over silent merge. |
| Distinct labels `INVOKES` vs `USES_ARTIFACT` (not single label with role) | Accepted | Avoids the documented `RUNS_ON` overload risk in `relationship_vocabulary.yaml`. |
| Option A modeling (one `:Script` label, role property) | Accepted | Minimal change to the existing ontology; sub-label split (Option B) deferred until query-side pressure justifies it. |
| Security boundary on `ETL_ARTIFACT_URI` (NF-SEC-2) | Accepted | Restricting artifact sources to JPMC-approved repositories prevents supply-chain risk and is enforceable by the verifier. |

## §10 Out of Scope

The following capabilities are explicitly **not** delivered by this NFR and are tracked
separately:

- Inferring canonical variable values by parsing `CMDLINE`, `MEMNAME` + `MEMLIB`, `Task JSON Path`,
  or `PARM1`–`PARMn` fields when the canonical variables are absent.
- Quoted-argument extraction (e.g., the Ab Initio `-g "<pset> -CAIP_PROC_SIZE_LARGE 50"` token).
- `PRECMD` / `POSTCMD` shell-hook handling for launcher/payload derivation.
- Folder-name signal mining as a platform fallback.
- Container-image registry URI shape validation (e.g., enforcing `registry.jpmchase.net/<path>:<tag>`).

---

# Part C — File Name Component Standard — Variable Naming (`job-variable-5..9`)

## §1 Decomposing the Full File Name

First, establish the anatomy of the full concatenated file name:

```
MLCM_CRM_ORIGINATIONS_20260530_001.dat.gz
|—————————————————|————————|———|——|—|
      PREFIX          BDATE   SEQ EXT COMPRESSION
```

| Component | Example | Description |
|---|---|---|
| **Prefix** | `MLCM_CRM_ORIGINATIONS` | Business identifier — source, domain, subject |
| **Business Date** | `20260530` | Date the data represents — not the file creation date |
| **Sequence** | `001` | Optional — handles multiple files per date |
| **Extension** | `.dat` | File format / DistributionRole indicator |
| **Compression** | `.gz` | Compression utility applied — may be absent |

> *Linux perspective:* The OS sees `MLCM_CRM_ORIGINATIONS_20260530_001.dat.gz` as one atomic
> string. Your standard must decompose this into named components that are individually parseable
> and ontology-mappable.

## §2 The Core Naming Question — What Are These Variables Called?

Three perspectives to consider before naming:

| Perspective | Sees the full name as | Implication |
|---|---|---|
| **Linux / OS** | One atomic filename string | `filename` — no decomposition |
| **Control-M** | A pattern with substitution variables | `%%FILENAME`, `%%BDATE` etc. |
| **Ontology / Catalog** | A structured identifier with typed components | Named properties on `dcat:Distribution` |

## §3 Recommended Variable Name Standard

**Naming Convention:** `File` prefix + component role in CamelCase

| Component | Variable Name | Ontology Term | Notes |
|---|---|---|---|
| Full concatenated name | `FileName` | `dcterms:title` on `dcat:Distribution` | What Linux sees — the atomic string |
| Prefix only | `FilePrefix` | `ex:filePrefix` | Business identifier portion — static |
| Business date | `FileBusinessDate` | `ex:fileBusinessDate` + `dcterms:temporal` | Date the **data** represents |
| Sequence number | `FileSequence` | `ex:fileSequence` | Optional — multi-file per date |
| Format extension | `FileExtension` | `dcat:mediaType` | `.dat` `.csv` `.txt` — format signal |
| Compression extension | `FileCompression` | `ex:fileCompression` | `.gz` `.tar` `.tar.gz` — may be absent |
| Full suffix | `FileSuffix` | `ex:fileSuffix` | Everything after the prefix — `.dat.gz` |
| Pattern / glob | `FilePattern` | `ex:watchFilePattern` | Used by FileWatcher — `MLCM_CRM_*.dat.gz` |

## §4 Why `FileBusinessDate` Not `FileDate`

This is the most important naming decision:

```
FileDate          ✗ ambiguous: could be creation date,
                    modified date, or business date

FileBusinessDate  ✓ unambiguous: the date the DATA represents
                    maps to dcterms:temporal on dcat:Distribution
                    aligns with data warehouse concept of
                    "business date" vs "load date"
```

| Variable | Meaning | Ontology |
|---|---|---|
| `FileBusinessDate` | Date the **data** represents | `dcterms:temporal` |
| `FileLoadDate` | Date the file was **processed** | `dcterms:modified` |
| `FileArrivalDate` | Date the file **arrived** on disk | `prov:generatedAtTime` |

> These are three distinct dates — conflating them is a common data quality error. Naming them
> explicitly prevents it.

## §5 Compression — Two-Part Suffix Problem

The `.dat.gz` case is the trickiest because Linux treats it as one suffix but it encodes two
distinct concepts:

```
.dat.gz
 │   └── FileCompression → how it is stored → ex:fileCompression
 └────── FileExtension   → what it contains → dcat:mediaType
```

**Controlled Vocabulary for Each:**

`FileExtension` — format/DistributionRole signal:

```
.dat   → DistributionRole: DAT
.csv   → DistributionRole: DAT
.txt   → DistributionRole: DAT
.tok   → DistributionRole: TOK
.ctl   → DistributionRole: CTL
.done  → DistributionRole: DONE
```

`FileCompression` — storage encoding:

```
.gz      → GZIP
.tar     → TAR (archive only — no compression)
.tar.gz  → TAR + GZIP
.zip     → ZIP
(absent) → NONE
```

## §6 Full Variable Standard — With Examples

```
Full FileName:   MLCM_CRM_ORIGINATIONS_20260530_001.dat.gz
                 |                    |          |
                 ▼                    ▼          ▼
FilePrefix:      MLCM_CRM_ORIGINATIONS      (static — business identity)
FileBusinessDate:20260530                   (YYYYMMDD — data date)
FileSequence:    001                         (optional — pad to 3 digits)
FileExtension:   .dat                        (format — maps to DistributionRole)
FileCompression: .gz                         (encoding — may be NONE)
FileSuffix:      .dat.gz                     (full suffix — what Linux appends)
FileName:        MLCM_CRM_ORIGINATIONS_20260530_001.dat.gz  (full atomic string)
FilePattern:     MLCM_CRM_ORIGINATIONS_*.dat.gz              (FileWatcher glob)
```

## §7 Oracle Column Standard

```sql
CREATE TABLE CM_JOB_FILE_NAME_STANDARD (
    JOB_NAME              VARCHAR2(200)   NOT NULL,

    -- ── Full atomic name (Linux view) ───────────────
    FILE_NAME             VARCHAR2(500),   -- FileName: full string
    FILE_PATTERN          VARCHAR2(500),   -- FilePattern: glob for FileWatcher

    -- ── Decomposed components ───────────────
    FILE_PREFIX           VARCHAR2(200),   -- FilePrefix: business identifier
    FILE_BUSINESS_DATE    VARCHAR2(8),     -- FileBusinessDate: YYYYMMDD
    FILE_SEQUENCE         VARCHAR2(10),    -- FileSequence: 001 (nullable)
    FILE_EXTENSION        VARCHAR2(20),    -- FileExtension: .dat .csv .tok .ctl
    FILE_COMPRESSION      VARCHAR2(20),    -- FileCompression: .gz .tar NONE
    FILE_SUFFIX           VARCHAR2(50),    -- FileSuffix: .dat.gz (full suffix)

    -- ── Derived / mapped ───────────────
    DISTRIBUTION_ROLE     VARCHAR2(10)     -- derived from FILE_EXTENSION
        REFERENCES CM_DISTRIBUTION_TYPE_REF(DISTRIBUTION_ROLE),

    CONSTRAINT PK_FILE_STD  PRIMARY KEY (JOB_NAME)
);
```

## §8 Ontology Mapping — All Components

| Variable Name | Column | Ontology Term | Ontology Class |
|---|---|---|---|
| `FileName` | `FILE_NAME` | `dcterms:title` | `dcat:Distribution` |
| `FilePattern` | `FILE_PATTERN` | `ex:watchFilePattern` | `ex:ControlMFileWatcherJob` |
| `FilePrefix` | `FILE_PREFIX` | `ex:filePrefix` | `dcat:Distribution` |
| `FileBusinessDate` | `FILE_BUSINESS_DATE` | `dcterms:temporal` | `dcat:Distribution` |
| `FileSequence` | `FILE_SEQUENCE` | `ex:fileSequence` | `dcat:Distribution` |
| `FileExtension` | `FILE_EXTENSION` | `dcat:mediaType` | `dcat:Distribution` |
| `FileCompression` | `FILE_COMPRESSION` | `ex:fileCompression` | `dcat:Distribution` |
| `FileSuffix` | `FILE_SUFFIX` | `ex:fileSuffix` | `dcat:Distribution` |

## §9 Design Rules — File Name Standard

- `FilePrefix` **is static** — it never changes between runs; it is the business identity of the file
- `FileBusinessDate` **is dynamic** — it changes every batch cycle; always `YYYYMMDD` format
- `FileSequence` **is optional** — only present when multiple files of the same type arrive on the same date
- `FileExtension` **drives** `DistributionRole` — the extension is the authoritative source for file classification, not the job name suffix
- `FileCompression` **is independent** — compression is a storage concern, not a content concern; `.dat.gz` is still a `DAT` file
- `FileName` **is the Linux truth** — it is the full concatenated string and is the authoritative identifier for file arrival detection
- `FilePattern` **is the FileWatcher truth** — it is the glob pattern Control-M uses to detect arrival; it replaces the dynamic components with wildcards

---

# Part D — MFTS Route IDs — Table & DPROD Extension (`job-variable-10..14`)

## §1 The Core Addition

Since MFTS is the **only intermediary**, the route IDs are a **first-class property** of the MFTS
delivery — not optional metadata. Each route ID maps directly to a `dprod:DataProductPort`:

| Route | DPROD Mapping | Direction |
|---|---|---|
| `MFTS_INBOUND_ROUTE_ID` | `dprod:inputPort` | Source System → MFTS |
| `MFTS_OUTBOUND_ROUTE_ID` | `dprod:outputPort` | MFTS → Application Landing Zone |

## §2 Updated Table — Add Route ID Columns

```sql
CREATE TABLE CM_JOB_METADATA_FILE_WATCHERS (
    JOB_NAME                VARCHAR2(200)   NOT NULL,
    DELIVERY_MECHANISM      VARCHAR2(30),      -- MFTS_AGENT | SFTP_DIRECT | API_GENERATED
    USER_ID                 VARCHAR2(50),      -- parsed: MFTS user / SFTP user / API svc acct
    ENV                     VARCHAR2(20),      -- parsed: FTS2 | PROD etc.

    -- ----------------------------------------------------
    -- MFTS Route IDs  ← NEW
    -- maps to dprod:inputPort  (source → MFTS)
    -- maps to dprod:outputPort (MFTS  → landing zone)
    -- ----------------------------------------------------
    MFTS_INBOUND_ROUTE_ID   VARCHAR2(100),     -- ex: MFTS_RT_IN_CRM_001
    MFTS_OUTBOUND_ROUTE_ID  VARCHAR2(100),     -- ex: MFTS_RT_OUT_APP_001

    DESCRIPTION             VARCHAR2(1000),    -- raw pipe-delimited parse source
    CONSTRAINT PK_CM_FW PRIMARY KEY (JOB_NAME)
);
```

> Transcription note: `DESCRIPTION` is `VARCHAR2(1000)` here but `VARCHAR2(4000)` in Part E's
> revision of the same table. Part E is later and supersedes; both are recorded.

## §3 Updated Description Format — Include Route IDs

Extend the pipe-delimited standard to carry route IDs as labeled tokens:

**MFTS Agent — Full Description with Routes**

```
DELIVERY_MECHANISM: MFTS_AGENT | USER: ftsi37291 | ENV: FTS2 | INBOUND_ROUTE: MFTS_RT_IN_CRM_001 | OUTBOUND_ROUTE: MFTS_RT_OUT_APP_001
```

**SFTP Direct — Routes not applicable**

```
DELIVERY_MECHANISM: SFTP_DIRECT | USER: svc_srcapp_sftp | ENV: PROD | INBOUND_ROUTE: NULL | OUTBOUND_ROUTE: NULL
```

**API Generated — Routes not applicable**

```
DELIVERY_MECHANISM: API_GENERATED | USER: svc_api_export | ENV: PROD | INBOUND_ROUTE: NULL | OUTBOUND_ROUTE: NULL
```

## §4 Updated REGEXP Parsing — All Five Tokens

```sql
UPDATE CM_JOB_METADATA_FILE_WATCHERS
SET
    DELIVERY_MECHANISM = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'DELIVERY_MECHANISM:\s*([^|]+)', 1, 1, 'i', 1)
    ),
    USER_ID = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'USER:\s*([^|]+)', 1, 1, 'i', 1)
    ),
    ENV = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'ENV:\s*([^|]+)', 1, 1, 'i', 1)
    ),
    MFTS_INBOUND_ROUTE_ID = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'INBOUND_ROUTE:\s*([^|]+)', 1, 1, 'i', 1)
    ),
    MFTS_OUTBOUND_ROUTE_ID = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'OUTBOUND_ROUTE:\s*([^|$]+)', 1, 1, 'i', 1)
    )
WHERE DESCRIPTION IS NOT NULL;
```

> Transcription note: the last token's character class is `[^|$]+` — anchoring on end-of-string
> for the final token — while every earlier token uses `[^|]+`. Read verbatim. `USER:` will also
> match inside `DELIVERY_MECHANISM: … USER…` only if the earlier key does not contain the
> substring; here it does not, but the pattern is positionally naive by construction.

## §5 Updated DPROD Ontology — Route IDs as Port Properties

```turtle
#-----------------------------------------------------
# Data Product — with MFTS Route IDs on Ports
#-----------------------------------------------------

ex:InboundBatchDataProduct
    a dprod:DataProduct ;
    rdfs:label       "Source System Batch Ingest Data Product" ;
    dcterms:description
        """Daily CRM Originations batch ingest data product.
           File pair (DAT + CTL) delivered via MFTS Agent
           ENV: FTS2 | User: ftsi37291.
           Inbound Route: MFTS_RT_IN_CRM_001 |
           Outbound Route: MFTS_RT_OUT_APP_001.""" ;
    dprod:inputPort  ex:MFTSInputPort ;
    dprod:outputPort ex:LandingZoneOutputPort .

#-----------------------------------------------------
# Input Port — Source System into MFTS
# Direction: Source System ──SFTP──▶ MFTS (FTS2)
#-----------------------------------------------------

ex:MFTSInputPort
    a dprod:DataProductPort ;
    rdfs:label            "MFTS Inbound Port — Source to MFTS" ;
    ex:mftsRouteId        "MFTS_RT_IN_CRM_001" ;     ← INBOUND_ROUTE_ID
    ex:mftsRouteDirection "INBOUND" ;
    ex:mftsEnv            "FTS2" ;
    ex:mftsUser           "ftsi37291" ;
    ex:transferProtocol   "SFTP" ;
    dprod:dataset         ex:InboundBatchDataset ;
    prov:wasAssociatedWith ex:MFTS_Agent_FTS2 .

#-----------------------------------------------------
# Output Port — MFTS to Application Landing Zone
# Direction: MFTS (FTS2) ──▶ Application /landing/inbound/
#-----------------------------------------------------

ex:LandingZoneOutputPort
    a dprod:DataProductPort ;
    rdfs:label            "MFTS Outbound Port — MFTS to Landing Zone" ;
    ex:mftsRouteId        "MFTS_RT_OUT_APP_001" ;    ← OUTBOUND_ROUTE_ID
    ex:mftsRouteDirection "OUTBOUND" ;
    ex:mftsEnv            "FTS2" ;
    ex:depositPath        "/mnt/landing/inbound/sourceapp/" ;
    dprod:dataset         ex:LandedBatchDataset ;
    prov:wasAssociatedWith ex:MFTS_Agent_FTS2 .

#-----------------------------------------------------
# MFTS Agent — Shared across both ports
#-----------------------------------------------------

ex:MFTS_Agent_FTS2
    a prov:SoftwareAgent ;
    rdfs:label     "MFTS Agent — FTS2" ;
    ex:mftsEnv     "FTS2" ;
    ex:systemUser  "ftsi37291" ;
    ex:platform    "MFTS" .
```

> Transcription note: the `←` annotations are callout arrows drawn on the screenshot, not Turtle
> syntax. Reproduced so the mapping intent survives; they must be stripped before any parse.
> Also: the port block uses `ex:mftsUser` while the agent block uses `ex:systemUser` for the same
> value — two spellings, recorded as read.

## §6 Route ID → Port Mapping — Full Picture

```
CM_JOB_METADATA_FILE_WATCHERS
═════════════════════════════
    JOB_NAME               : PARAD00010_..._FW
    DELIVERY_MECHANISM     : MFTS_AGENT
    USER_ID                : ftsi37291
    ENV                    : FTS2
    MFTS_INBOUND_ROUTE_ID  : MFTS_RT_IN_CRM_001  ─────────────────┐
    MFTS_OUTBOUND_ROUTE_ID : MFTS_RT_OUT_APP_001 ────────────────┐│
                                                                 ││
DPROD Ontology                                                   ││
══════════════                                                   ││
    ex:InboundBatchDataProduct                                   ││
        │                                                        ││
        ├── dprod:inputPort  ── ex:MFTSInputPort                 ││
        │        └── ex:mftsRouteId  ◀── MFTS_INBOUND_ROUTE_ID ──┘│
        │        └── ex:mftsRouteDirection = "INBOUND"            │
        │                                                         │
        └── dprod:outputPort ── ex:LandingZoneOutputPort          │
                 └── ex:mftsRouteId ◀── MFTS_OUTBOUND_ROUTE_ID ───┘
                 └── ex:mftsRouteDirection = "OUTBOUND"
```

## §7 Validation Query — MFTS Route Completeness Check

```sql
-- Flag any MFTS jobs missing route IDs
SELECT
    JOB_NAME,
    USER_ID,
    ENV,
    MFTS_INBOUND_ROUTE_ID,
    MFTS_OUTBOUND_ROUTE_ID,
    CASE
        WHEN DELIVERY_MECHANISM = 'MFTS_AGENT'
            AND (   MFTS_INBOUND_ROUTE_ID  IS NULL
                 OR MFTS_INBOUND_ROUTE_ID  = 'NULL'
                 OR MFTS_OUTBOUND_ROUTE_ID IS NULL
                 OR MFTS_OUTBOUND_ROUTE_ID = 'NULL')
        THEN 'MISSING_ROUTE_IDS'
        WHEN DELIVERY_MECHANISM != 'MFTS_AGENT'
            AND (   MFTS_INBOUND_ROUTE_ID  IS NOT NULL
                 OR MFTS_OUTBOUND_ROUTE_ID IS NOT NULL)
        THEN 'UNEXPECTED_ROUTE_IDS'
        ELSE 'OK'
    END AS ROUTE_VALIDATION
FROM CM_JOB_METADATA_FILE_WATCHERS
ORDER BY ROUTE_VALIDATION, JOB_NAME;
```

## §8 Updated Minimum Vocabulary Checklist

| Column | Required When | Maps To |
|---|---|---|
| `DELIVERY_MECHANISM` | Always | `ex:fileDeliveredVia` |
| `USER_ID` | Always | `ex:systemUser` on Agent |
| `ENV` | Always | `ex:mftsEnv` on Agent |
| `MFTS_INBOUND_ROUTE_ID` | `MFTS_AGENT` only | `ex:mftsRouteId` on `dprod:inputPort` |
| `MFTS_OUTBOUND_ROUTE_ID` | `MFTS_AGENT` only | `ex:mftsRouteId` on `dprod:outputPort` |

---

# Part E — Source Contact & PDN Downstream (`job-variable-15..20`)

## §1 Conceptual Model — Two New Contact Dimensions

These map to distinct roles in the data flow lifecycle:

| Concept | Job Type | Direction | Ontology Role |
|---|---|---|---|
| **Source Contact** | FileWatcher | Upstream → Us | `prov:wasAttributedTo` — who owns the data at origin |
| **Downstream DL** | Publisher Job | Us → Downstream | `dprod:outputPort` consumer notification |
| **Downstream SNOW Queue** | Publisher Job | Us → Downstream | `ex:serviceNowQueue` — incident/change routing |

## §2 Description Token Design — Both Job Types

**FileWatcher — Add Source Contact**

```
DELIVERY_MECHANISM: MFTS_AGENT | USER: ftsi37291 | ENV: FTS2 | INBOUND_ROUTE: MFTS_RT_IN_CRM_001 | OUTBOUND_ROUTE: MFTS_RT_OUT_APP_001 | EMAIL_DL_L3: EDS_Scrum_Stars@chase.com; ade_masterminds@restricted.chase.com | EMAIL_DL_L2: ade_masterminds@restricted.chase.com | SOURCE_CONTACT: source_owner@chase.com; source_support@chase.com
```

**Publisher Job — Downstream Notification**

```
JOB_ROLE: PUBLISHER | EMAIL_DL_L3: EDS_Scrum_Stars@chase.com | EMAIL_DL_L2: ade_masterminds@restricted.chase.com | PDN_DL: digital_data_owners@restricted.chase.com; ADE_Customer@chase.com; adexdc_sapiens@restricted.chase.com | PDN_SNOW_QUEUE: NULL
```

> **Design Rule:** `PDN_SNOW_QUEUE: NULL` must still be present as a token even when empty — this
> ensures the REGEXP always finds the key and returns a parseable result rather than a missing
> match.

## §3 Updated Tables

**Table A — `CM_JOB_METADATA_FILE_WATCHERS` (Source Contact Added)**

```sql
CREATE TABLE CM_JOB_METADATA_FILE_WATCHERS (
    JOB_NAME                VARCHAR2(200)   NOT NULL,
    DELIVERY_MECHANISM      VARCHAR2(30),
    USER_ID                 VARCHAR2(50),
    ENV                     VARCHAR2(20),
    MFTS_INBOUND_ROUTE_ID   VARCHAR2(100),
    MFTS_OUTBOUND_ROUTE_ID  VARCHAR2(100),
    EMAIL_DL_L3             VARCHAR2(500),   -- Dev / Scrum team
    EMAIL_DL_L2             VARCHAR2(500),   -- Ops support group

    -- ----------------------------------------------------
    -- Source Contact  ← NEW
    -- Who owns / supports the file at the originating system
    -- prov:wasAttributedTo on the source Entity
    -- ----------------------------------------------------
    SOURCE_CONTACT          VARCHAR2(500),   -- semicolon-separated emails

    DESCRIPTION             VARCHAR2(4000),
    CONSTRAINT PK_CM_FW PRIMARY KEY (JOB_NAME)
);
```

**Table B — `CM_JOB_METADATA_PUBLISHERS` (New Table)**

```sql
CREATE TABLE CM_JOB_METADATA_PUBLISHERS (
    JOB_NAME         VARCHAR2(200)   NOT NULL,
    JOB_ROLE         VARCHAR2(30),      -- PUBLISHER
    EMAIL_DL_L3      VARCHAR2(500),     -- Dev / Scrum team
    EMAIL_DL_L2      VARCHAR2(500),     -- Ops support group

    -- ----------------------------------------------------
    -- PDN / Downstream Notification  ← NEW
    -- Who receives notification when data is published
    -- maps to dprod:outputPort consumer contact
    -- ----------------------------------------------------
    PDN_DL           VARCHAR2(1000),    -- semicolon-separated downstream DLs
    PDN_SNOW_QUEUE   VARCHAR2(200),     -- ServiceNow queue for incidents/changes

    DESCRIPTION      VARCHAR2(4000),
    CONSTRAINT PK_CM_PUB PRIMARY KEY (JOB_NAME)
);
```

## §4 Sample INSERT Rows

```sql
-- FileWatcher with Source Contact
INSERT INTO CM_JOB_METADATA_FILE_WATCHERS
    (JOB_NAME, DESCRIPTION)
VALUES (
    'PARAD00010_MLCM_ORIGINATIONS_DAILY_CRM_DAT_ONPM_FW',
    'DELIVERY_MECHANISM: MFTS_AGENT | USER: ftsi37291 | ENV: FTS2 | ' ||
    'INBOUND_ROUTE: MFTS_RT_IN_CRM_001 | OUTBOUND_ROUTE: MFTS_RT_OUT_APP_001 | ' ||
    'EMAIL_DL_L3: EDS_Scrum_Stars@chase.com; ade_masterminds@restricted.chase.com | ' ||
    'EMAIL_DL_L2: ade_masterminds@restricted.chase.com | ' ||
    'SOURCE_CONTACT: source_owner@chase.com; source_support@chase.com'
);

-- Publisher Job with PDN Downstream Notification
INSERT INTO CM_JOB_METADATA_PUBLISHERS
    (JOB_NAME, DESCRIPTION)
VALUES (
    'PARAD00010_MLCM_ORIGINATIONS_DAILY_CRM_DAT_ONPM_PUB',
    'JOB_ROLE: PUBLISHER | ' ||
    'EMAIL_DL_L3: EDS_Scrum_Stars@chase.com | ' ||
    'EMAIL_DL_L2: ade_masterminds@restricted.chase.com | ' ||
    'PDN_DL: digital_data_owners@restricted.chase.com; ' ||
    […]
);
```

> The Publisher INSERT is cut by the screenshot after the `PDN_DL:` line; by the §2 token design
> it continues with the remaining two PDN addresses and `PDN_SNOW_QUEUE: NULL`.

## §5 REGEXP Parsing — Both Tables

**FileWatcher Parse (adds SOURCE_CONTACT)**

```sql
UPDATE CM_JOB_METADATA_FILE_WATCHERS
SET
    DELIVERY_MECHANISM = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'DELIVERY_MECHANISM:\s*([^|]+)', 1, 1, 'i', 1)),
    USER_ID = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'USER:\s*([^|]+)', 1, 1, 'i', 1)),
    ENV = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'ENV:\s*([^|]+)', 1, 1, 'i', 1)),
    MFTS_INBOUND_ROUTE_ID = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'INBOUND_ROUTE:\s*([^|]+)', 1, 1, 'i', 1)),
    MFTS_OUTBOUND_ROUTE_ID = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'OUTBOUND_ROUTE:\s*([^|]+)', 1, 1, 'i', 1)),
    EMAIL_DL_L3 = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'EMAIL_DL_L3:\s*([^|]+)', 1, 1, 'i', 1)),
    EMAIL_DL_L2 = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'EMAIL_DL_L2:\s*([^|]+)', 1, 1, 'i', 1)),
    -- SOURCE_CONTACT: semicolons inside value are safe — pipe is delimiter
    SOURCE_CONTACT = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'SOURCE_CONTACT:\s*([^|]+)', 1, 1, 'i', 1))
WHERE DESCRIPTION IS NOT NULL;
```

**Publisher Parse**

```sql
UPDATE CM_JOB_METADATA_PUBLISHERS
SET
    JOB_ROLE = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'JOB_ROLE:\s*([^|]+)', 1, 1, 'i', 1)),
    EMAIL_DL_L3 = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'EMAIL_DL_L3:\s*([^|]+)', 1, 1, 'i', 1)),
    EMAIL_DL_L2 = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'EMAIL_DL_L2:\s*([^|]+)', 1, 1, 'i', 1)),
    -- PDN_DL: multiple emails semicolon-separated within value
    PDN_DL = TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'PDN_DL:\s*([^|]+)', 1, 1, 'i', 1)),
    -- PDN_SNOW_QUEUE: last token — may be NULL string
    PDN_SNOW_QUEUE = NULLIF(TRIM(
        REGEXP_SUBSTR(DESCRIPTION,
            'PDN_SNOW_QUEUE:\s*([^|]+)', 1, 1, 'i', 1)),
        'NULL')
WHERE DESCRIPTION IS NOT NULL;
```

> **Note:** `NULLIF(..., 'NULL')` converts the literal string `'NULL'` to a true SQL `NULL` on
> parse — keeping the stored value clean.

## §6 Updated Ontology — Source Contact & PDN Downstream

```turtle
#-----------------------------------------------------
# SOURCE CONTACT — FileWatcher / Inbound
# Who owns the file at the originating system
# prov:wasAttributedTo on the source dataset entity
#-----------------------------------------------------

ex:SourceSystemContact
    a ex:EmailDistributionList ;
    rdfs:label          "Source System Contact" ;
    ex:dlTier           "SOURCE" ;
    ex:dlTierDesc       "File owner / support contact at originating system" ;
    ex:ctmVariableName  "SOURCE_CONTACT" ;
    ex:dlAddress        "source_owner@chase.com" ;
    ex:dlAddress        "source_support@chase.com" .

ex:InboundBatchDataset
    a dcat:Dataset ;
    prov:wasAttributedTo  ex:SourceSystemContact .

#-----------------------------------------------------
# PDN / DOWNSTREAM NOTIFICATION — Publisher Job
# Who receives notification when data is published
# maps to dprod:outputPort consumer contact
#-----------------------------------------------------

ex:PDN_DownstreamContact
    a ex:EmailDistributionList ;
    rdfs:label          "PDN Downstream Consumer Distribution List" ;
    ex:dlTier           "PDN" ;
    ex:dlTierDesc       "Downstream business / data owners notified on publish" ;
    ex:ctmVariableName  "PDN_DL" ;
    ex:dlAddress        "digital_data_owners@restricted.chase.com" ;
    ex:dlAddress        "ADE_Customer@chase.com" ;
    ex:dlAddress        "adexdc_sapiens@restricted.chase.com" .

#-----------------------------------------------------
# PDN SNOW Queue — ServiceNow incident/change routing
# NULL when not yet assigned
#-----------------------------------------------------

ex:PDN_SNOWQueue
    a ex:ServiceNowQueue ;
    rdfs:label          "PDN Downstream ServiceNow Queue" ;
    ex:ctmVariableName  "PDN_SNOW_QUEUE" ;
    ex:queueName        NULL ;              ← not yet assigned
    ex:queueStatus      "PENDING_ASSIGNMENT" .

#-----------------------------------------------------
# Publisher Data Product Output Port
# Carries both DL and SNOW queue as consumer contacts
#-----------------------------------------------------

ex:PublisherOutputPort
    a dprod:DataProductPort ;
    rdfs:label            "Publisher Output Port — PDN Downstream" ;
    ex:consumerContact    ex:PDN_DownstreamContact ;
    ex:serviceNowQueue    ex:PDN_SNOWQueue ;
    dprod:dataset         ex:PublishedBatchDataset .

ex:OutboundBatchDataProduct
    a dprod:DataProduct ;
    rdfs:label            "Outbound Batch Data Product — PDN Publisher" ;
    dprod:outputPort      ex:PublisherOutputPort ;
    ex:supportContact     ex:DL_L3_DevGroup ;
    ex:supportContact     ex:DL_L2_SupportGroup .
```

> Transcription note: `ex:queueName NULL ;` is not valid Turtle — a bare `NULL` is neither an IRI
> nor a literal. Recorded as written; it is a placeholder the source page never resolved. The `←`
> is a screenshot callout, as in Part D §5.

## §7 Full Contact Role Map — Across Both Job Types

```
                    SOURCE_CONTACT              EMAIL_DL_L3 / L2
                    (file owner at origin)      (our team)
                            │                        │
[Source System] ────────────┤                        │
                            │                        │
        [FileWatcher Job] ──┴────────────────────────┤
                                                     │
                            [Publisher Job] ─────────┤
                                                     │
                    ┌────────────────────────────────┴────────┐
                    │                                          │
                 PDN_DL                              PDN_SNOW_QUEUE
            (downstream consumers)                  (ServiceNow queue)
        digital_data_owners@…                        NULL / pending
        ADE_Customer@…
        adexdc_sapiens@…
```

## §8 Complete Token & Column Reference — All Job Types

| Token Key | Table | Column | Ontology Mapping | Notes |
|---|---|---|---|---|
| `DELIVERY_MECHANISM` | FW | `DELIVERY_MECHANISM` | `ex:fileDeliveredVia` | Always required |
| `USER` | FW | `USER_ID` | `ex:systemUser` | Service account |
| `ENV` | FW | `ENV` | `ex:mftsEnv` | Runtime env |
| `INBOUND_ROUTE` | FW | `MFTS_INBOUND_ROUTE_ID` | `dprod:inputPort` route | MFTS only |
| `OUTBOUND_ROUTE` | FW | `MFTS_OUTBOUND_ROUTE_ID` | `dprod:outputPort` route | MFTS only |
| `EMAIL_DL_L3` | FW + PUB | `EMAIL_DL_L3` | `ex:supportContact` L3 | Dev/Scrum team |
| `EMAIL_DL_L2` | FW + PUB | `EMAIL_DL_L2` | `ex:supportContact` L2 | Ops support |
| `SOURCE_CONTACT` | FW | `SOURCE_CONTACT` | `prov:wasAttributedTo` | Origin file owner |
| `JOB_ROLE` | PUB | `JOB_ROLE` | `ex:jobRole` | PUBLISHER |
| `PDN_DL` | PUB | `PDN_DL` | `ex:consumerContact` on `dprod:outputPort` | Downstream DLs |
| `PDN_SNOW_QUEUE` | PUB | `PDN_SNOW_QUEUE` | `ex:serviceNowQueue` | NULL if unassigned |

> This is the source document's own summary table and the closest thing the corpus has to a
> single register. It covers the FileWatcher and Publisher description tokens only — it does
> **not** cover the Part C file-name components, the Part B ETL/cmd variables, or the REQ-1
> folder variables. The consolidated register across all five parts is the C29 deliverable in
> `knowledge/standards/technology/description-field-metadata-plan.md`.

---

# Components by job type

Derived from the five parts above. **File watchers first, then ETL**, per the capture request.
"Carrier" is the mechanism that holds the value: the `DESCRIPTION` field, a job VARIABLE, or a
folder VARIABLE. The three are governed by different change-control paths and must not be
conflated.

## 1. FileWatcher jobs

| Carrier | Name | Value shape | Source |
|---|---|---|---|
| description-token | `DELIVERY_MECHANISM` | `MFTS_AGENT` \| `SFTP_DIRECT` \| `API_GENERATED` | D §3, E §8 |
| description-token | `USER` | service account id | D §3 |
| description-token | `ENV` | transfer environment | D §3 |
| description-token | `INBOUND_ROUTE` | route id, or literal `NULL` when not MFTS | D §3 |
| description-token | `OUTBOUND_ROUTE` | route id, or literal `NULL` when not MFTS | D §3 |
| description-token | `EMAIL_DL_L3` | semicolon-separated addresses | E §2 |
| description-token | `EMAIL_DL_L2` | semicolon-separated addresses | E §2 |
| description-token | `SOURCE_CONTACT` | semicolon-separated addresses | E §2 |
| job-variable | `%%FileWatch-FILE_PATH` | token path, defined **first** | A REQ-3 |
| job-variable | `%%POSTCMD` | `cat %%FileWatch-FILE_PATH` — references row 1 | A REQ-3 |
| file-name component | `FileName`, `FilePattern`, `FilePrefix`, `FileBusinessDate`, `FileSequence`, `FileExtension`, `FileCompression`, `FileSuffix` | see Part C §3 | C |

**Landing tables:** `CM_JOB_METADATA_FILE_WATCHERS` (D §2 / E §3 Table A),
`CM_JOB_FILE_NAME_STANDARD` (C §7), with `CM_DISTRIBUTION_TYPE_REF` as the `DISTRIBUTION_ROLE`
lookup.

**Ordering constraint (REQ-3):** `%%FileWatch-FILE_PATH` must be declared before `%%POSTCMD`.
This is a *document-order* dependency of exactly the kind the G47 extractor's ordinal contract
exists to preserve, and the kind a naive re-emit would silently break.

## 2. Publisher jobs

| Carrier | Name | Value shape | Source |
|---|---|---|---|
| description-token | `JOB_ROLE` | `PUBLISHER` | E §2 |
| description-token | `EMAIL_DL_L3` | semicolon-separated addresses | E §2 |
| description-token | `EMAIL_DL_L2` | semicolon-separated addresses | E §2 |
| description-token | `PDN_DL` | semicolon-separated downstream addresses | E §2 |
| description-token | `PDN_SNOW_QUEUE` | queue name, or literal `NULL` — **the token is mandatory even when empty** | E §2 |

**Landing table:** `CM_JOB_METADATA_PUBLISHERS` (E §3 Table B).

## 3. ETL / `cmd` jobs

| Carrier | Name | Value shape | Source |
|---|---|---|---|
| job-variable | `%%LAUNCHER_SCRIPT_PATH` | launcher script path | A REQ-4, B §5/§6 |
| job-variable | `%%ETL_ARTIFACT_URI` | wheel / jar / pset / (empty for Informatica) | A REQ-4, B §5/§6 |
| job-variable | `%%ETL_PLATFORM` | `pyspark` \| `java` \| `abinitio` \| `informatica` | A REQ-4, B §6 |
| job-variable | `%%ETL_ARTIFACT_KIND` | `wheel` \| `jar` \| `pset` \| `other` | A REQ-4, B §6 |
| job-variable | `%%ETL_PLATFORM_FLAGS` | `-py` \| empty — optional | A REQ-4, B §6 |
| job-variable | `%%INFA_INTERFACE_LOCAL` | Informatica only — NODE-KEY component | B §5, §6.4 |
| job-variable | `%%INFA_INTERFACE_GLOBAL` | Informatica only — NODE-KEY component | B §5, §6.4 |
| job-variable | `%%INFA_JOB` | Informatica only — NODE-KEY component | B §5, §6.4 |
| job-variable | `%%INFA_DATABASE` | Informatica variant 2 only | B §5, §6.5 |

**Landing table:** `STG_APP_FACT`, keyed by the 30-char `fact_type` (B §2, §5, §8).

**Names always declared, values may differ (REQ-4).** This is the load-bearing rule: the
uniform *name set* is what makes a cross-platform query possible; the value tells you which
platform you are on. It is the same contract as the FACT_REGISTRY's aliases-suggest-values-decide
discipline, arrived at from the authoring side rather than the parsing side.

## 4. Folder level — all job types

| Carrier | Name | Value shape | Source |
|---|---|---|---|
| folder-variable | `DevX-project` | DevX project key | A REQ-1 |
| folder-variable | `L2_EMAIL_DL_NM` | semicolon-separated addresses | A REQ-1 |
| folder-variable | `L3_EMAIL_DL_NM` | semicolon-separated addresses | A REQ-1 |
| folder-variable | `SEAL` | SEAL id — *not from these documents*; the existing primary SEAL source | description-field-metadata-plan §2 |

**Two spellings for one concept.** REQ-1 puts support DLs in **folder variables** named
`L2_EMAIL_DL_NM` / `L3_EMAIL_DL_NM`; Part E puts them in the **job description** as
`EMAIL_DL_L2` / `EMAIL_DL_L3`. Different carrier, different grain, different spelling, same
concept. Nothing in the corpus states which wins. This is carried to the gate as §G2.

## 5. Removed by REQ-2 — for all job types

`<SHOUT>` and `<DOSHOUT>` are to disappear from generated XML entirely. `<DOMAIL>` (nested in
`<ON STMT="*" CODE="NOTOK">`) is retained.

---

# Ontology coverage — what exists today

Every term the five documents name, checked against this repo on 2026-08-11 (desktop, `main` at
`f8e7b98`). Verdicts cite `file:line` where something exists.

## Already built

| Term / mechanism | Where it lives here | Note |
|---|---|---|
| `ETL_ARTIFACT_URI`, `ETL_ARTIFACT_KIND`, `ETL_PLATFORM`, `ETL_PLATFORM_FLAGS`, `LAUNCHER_SCRIPT_PATH` | `drydocs_core/orchestration/controlm/variables.py:180-230` (FACT_REGISTRY + alias rollups) | Built at G16 under gate `cmdline-nfr-vetting` (SIGNED 2026-07-21, 4/4) |
| aliases-suggest-values-decide contract | `drydocs_core/orchestration/controlm/variables.py:238-247` | The NFR's §7 alias/migration behaviour, already implemented |
| `USES_ARTIFACT` edge | `drydocs_core/ontology/relationship_vocabulary/40-local-controlm.yaml:456` (`m7_uses_artifact`) | Activated at gate `rua-load-shapes` §A4 (2026-08-06) |
| `INVOKES` edge | same fragment (`m3_invokes`) | Payload invocations migrate onto `USES_ARTIFACT`; launcher stays on `INVOKES` — the same launcher/payload split NFR §3 describes |
| `:Script` `script_role {launcher, payload}` + `platform` / `artifact_uri` / `artifact_kind` / `platform_flags` / `script_path` | `drydocs/schema/ontology_supplement.cypher:275` and the `rua-load-shapes` §A4 riders | SME-ruled at `cmdline-nfr-vetting` SME-3 |
| `ETL_ARTIFACT_SHA` | FACT_REGISTRY | **DryDocs has a canonical the NFR does not name** — a content hash the NFR's §5 table omits |

**Reading:** NFR-CTM-001 v2 is, for the ETL/cmd family, a company-side restatement of work
DryDocs already did. The two agree on the launcher/payload split, on distinct edge labels rather
than one label with a role, and on `prov:used` as the PROV mapping. Where they differ is
direction of travel: the NFR tells job authors what to declare; the FACT_REGISTRY decides from
values regardless of what was declared. Both are needed — the NFR reduces the alias tail the
registry has to absorb.

## Observed but not registered

| Term | Where it appears here | Gap |
|---|---|---|
| `FileDeliveryMechanism`, `USER`, `ENV`, `ROUTE_ID`, `SourceOrigin`, `SourceContact`, `SourceSnowQueue` | `knowledge/standards/technology/description-field-metadata-plan.md:70-76` — prose rows in an "observed metadata keys" table with a "graph relationship it enables" column | No vocabulary entry, no property-term binding, no loader. The column names an intended edge; nothing declares it. |
| `EMAIL_DL_L2` / `EMAIL_DL_L3` | same file, line 78 — listed as folder variables | Same gap |
| pipe-delimited `key: value` grammar, split-on-first-colon, whitespace tolerance | same file, line 105 | Stated as a parsing rule in prose; **no parser implements it** (G66 closes this) |
| key-prefix governance (`drydocs.` reserved, `snow.` / `mfts.` system-owned, bare = team-local) | same file, lines 128-158 (C16, ratified 2026-07-28) | **Collides with the captured spellings** — C16 targets `snow.assignmentQueue` and `mfts.routeId`; the documents use bare `PDN_SNOW_QUEUE` and `INBOUND_ROUTE` |

## Not registered at all

Every one of the following appears in the captured documents and **nowhere** in
`drydocs_core/ontology/relationship_vocabulary/` (checked across all 13 fragments), in
`config/taxonomy-ontology-map/`, or in any loader:

`ex:fileDeliveredVia` · `ex:systemUser` · `ex:mftsEnv` · `ex:mftsUser` · `ex:mftsRouteId` ·
`ex:mftsRouteDirection` · `ex:transferProtocol` · `ex:depositPath` · `ex:platform` ·
`ex:supportContact` · `ex:consumerContact` · `ex:serviceNowQueue` · `ex:jobRole` ·
`ex:dlTier` · `ex:dlTierDesc` · `ex:dlAddress` · `ex:ctmVariableName` · `ex:queueName` ·
`ex:queueStatus` · `ex:filePrefix` · `ex:fileBusinessDate` · `ex:fileSequence` ·
`ex:fileCompression` · `ex:fileSuffix` · `ex:watchFilePattern`

Classes: `ex:EmailDistributionList` · `ex:ServiceNowQueue` · `ex:ControlMFileWatcherJob`

## Standards families — namespace yes, bindings no

| Standard | Status here |
|---|---|
| `dcterms:` (`title`, `temporal`, `modified`) | Namespace resolves via `drydocs_core/ontology/namespaces.py`; `dct:` bindings exist in `20-property-terms.yaml` section 0b **only for the audit envelope** (gate `envelope-property-terms`, 2026-08-04). No file-name or description bindings. |
| `dcat:` (`Distribution`, `mediaType`, `Dataset`) | Adopted family — `:DataAsset` / `:DocSource` are `dcat:Dataset`-shaped. No `dcat:Distribution` node class exists. |
| `prov:` (`wasAttributedTo`, `generatedAtTime`, `SoftwareAgent`, `wasAssociatedWith`) | Fully adopted. `WAS_ATTRIBUTED_TO` exists with a `role` property (`43-local-architecture.yaml`, `arch_develops`) — the captured `SOURCE_CONTACT → prov:wasAttributedTo` mapping would be a **new role on an existing edge**, not a new edge type. |
| `dprod:` (`DataProduct`, `DataProductPort`, `inputPort`, `outputPort`, `dataset`) | Declared family (CLAUDE.md §2 Tier 1). **No port-shaped entries exist.** The MFTS-route-as-port modeling is entirely new. |

## The class collision

`ex:EmailDistributionList` (with `ex:dlTier`, `ex:dlTierDesc`, `ex:dlAddress`,
`ex:ctmVariableName`) is the same concept as `dd:DistributionList`, proposed at
`config/gate-prompts/email-dl-contact-point.yaml` §A1 with standards alignment `vcard:Group`
and keyed on the lower-cased SMTP address. That gate is **drafted 2026-07-22 and unsigned** — it
does not appear in `config/gate-log.md`. Two spellings for one class, neither ratified.

**Verdict for the C29 question — "do we have ontology defined already for fields like EMAIL_DL,
DELIVERY_MECHANISM?"** No. The ETL/cmd variable family is built; every description-token term is
either observed-in-prose or absent, and the one class that has a repo-side proposal has it in a
gate nobody has signed.

---

# Conflicts this capture surfaces

Recorded here because each one is a decision, not a defect to fix in passing. None is resolved
by this file.

**1. The gate says the opposite about the authoring surface.**
`email-dl-contact-point` §C2 recommends the escalation DB's special-instructions field as the
authored surface for notification routing and §C3 explicitly demotes the Description field to a
"per-job exception carrier", partly on the ground that "the 4000 chars are shared with all other
planned description metadata". These documents author contacts in the Description field *and* in
folder variables. Carried to the gate as rider §G.

**2. Folder grain vs job grain, both present.**
REQ-1 → folder variables. Part E → job description tokens. `email-dl-contact-point` §B2 asked
this exact question and preferred folder grain with per-job exceptions. The corpus now has both
and states no precedence.

**3. REQ-2 deletes half of the gate's corroboration feed.**
`email-dl-contact-point` §B2 treats DO-MAIL/SHOUT extraction as the *wired* evidence that
corroborates *intended* routing. REQ-2 removes `<SHOUT>`/`<DOSHOUT>` entirely, leaving `<DOMAIL>`.

**4. The DESCRIPTION field is claimed twice on generated objects.**
`../controlm-pipeline-stub-integration-plan.md` item **E1** uses the two literal DESCRIPTION
strings the DPL stub emits (`"Generated Control-M Folder"` and `"Generated job to trigger DPL …"`)
as a machine-generated provenance discriminator. This standard fills the same field with tokens.
Add a token block and E1's exact-literal match breaks; require the literal and the token block
has nowhere to go. Three exits — exempt generated objects from the token standard, fold the
literal in as one token, or move the discriminator off DESCRIPTION — and it is a ruling, not a
default.

**5. C16's key prefixes vs the captured spellings.**
C16 (ratified 2026-07-28) assigns `SourceSnowQueue → snow.assignmentQueue` and
`ROUTE_ID → mfts.routeId`. The captured documents use bare `PDN_SNOW_QUEUE`, `INBOUND_ROUTE`,
`OUTBOUND_ROUTE`. C16's own migration note grandfathers observed spellings pending template
ratification, so this is a mapping to record rather than a contradiction — recorded in the
register.

**6. Internal inconsistencies in the source documents themselves.**
Listed with `[sic]` at the point of transcription: REQ-2's text says "REQ-1" twice; REQ-3's
acceptance list starts at item 2; NFR §1 points at "§11" for a section numbered §10; §6.4 uses
`%%SRC_SYS_CD` where §6.5 uses `%%SOR_SYS_CD`; Part D §5 uses `ex:mftsUser` where the agent block
uses `ex:systemUser`; Part E §6 contains `ex:queueName NULL` which is not valid Turtle; REQ-1's
L3 example value repeats the L2 address; REQ-4 leaves `Zilo or java?` as a value. The corpus is
`WIP-DRAFT` per its own breadcrumb.
