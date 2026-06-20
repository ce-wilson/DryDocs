# Control-M General Parameters — Job Name · Folder Name · Priority · Description (Classic Parameter Reference)

**Source:** BMC Control-M/EM client Help — **classic Parameter Reference**, parent topic *General parameters*.
**Captured:** 2026-06-11, transcribed from product Help screenshots (`bmc-job-name.png`, `bmc-folder-name.png`, `bmc-job-priority.png`, `bmc-job-description.png`).
**Purpose:** Authoritative identity/priority parameter definitions for the **9.0.21.300 / XML** environment.

✅ Matches the target environment (classic Parameter Reference family — same as `Command`, Order, Variables params). See [[project-controlm-xml-not-json]].

---

## 📑 Provenance Classification

The parameter tables below are **[VERBATIM]/[GROUNDED]** — transcribed from product Help, not reconstructed. Only cross-reference notes and the explicitly-marked correction notes are **[SYNTHESIZED]**.

⚠️ One OCR caveat on the Priority ordering sequence string — flagged inline.

---

## Job Name

> Defines the name of the job processing definition; appears in the job definition and tracking displays; enables you to identify the job and order the job.

| Additional information | Description |
|---|---|
| **Usage** | Mandatory |
| **Length** | 1–64 characters; **z/OS: 1–8** |
| **Case Sensitive** | Yes |
| **Invalid Characters** | Single quotation marks; `$ / * ?`; leading or trailing spaces |
| **Variable Name** | `%%JOBNAME` |
| **Alternate Names** | EM Utilities `JOBNAME` · Report `JOB NAME` · Server Utilities `-jobname` · z/OS `JOB NAME` · EM API `job_name` |

- **IBM i (AS/400):** the value is the actual job name used by AS/400 (part of the submission command); must conform to AS/400 job-name conventions.
- Used when ordering or forcing a job (Order Job *Ignore Scheduling Criteria*, or Order/Force windows). You **can define a job without a job name** in `ctmcreate` and `ctmdefine`.
- **Accessing/overriding in variable expressions:** the value is accessible via **`%%JOBNAME`**; can be overridden when the job is ordered, e.g. `ctmorder` command line: `-variable %%JOBNAME newjobname`.

### BMC job-naming rule-of-thumb *(vendor generic guidance — not the company standard)*
> Job naming standards are a must for every successful Control-M implementation. While there is no set standard, a good rule-of-thumb: all jobs start with the **application moniker**, then a few characters for the job's **function/type**, then characters for the **specific purpose/destination/process**.

| Segment | Meaning | BMC examples |
|---|---|---|
| `AAA` | application moniker | DDA, SAV, MTG, LOA |
| `TTT` | job type | AFT, SAP, WIN, UNX, WJM, DBA |
| `FFFFFFFF` | function | POSTING, BACKUP, DBLOAD |

This naming format underpins Control-M **access control** (security restricts/allows by application moniker in the job name) and change/problem management.

> ⚠️ **Internal gap:** this is BMC's *generic* guidance. The **company's actual job naming standard** (the job-level analogue of the PRAOCG folder convention) is **not yet captured** — see [[project-folder-naming-praocg]]. The bank-flavored monikers above (DDA=Demand Deposit, SAV=Savings, MTG=Mortgage, LOA=Loan) are BMC's examples, not confirmed company codes.

---

## Folder Name

> Defines the name of the folder. In the Properties pane, this parameter indicates the folder where the job belongs.

| Additional information | Description |
|---|---|
| **Usage** | Mandatory, **if** values are specified for the Job Name and Date parameters |
| **Length** | 1–64 characters; **z/OS: 1–8** |
| **Case Sensitive** | Yes |
| **Invalid Characters** | Blanks; single quotation marks; z/OS non-English characters; `$ / * ?` and space |
| **Variable Name** | None *(the folder name field cannot itself be a variable)* |
| **Alternate Names** | EM Utilities `FOLDER_NAME` · Report `FOLDER_ID` · Server Utilities `FOLDER` · z/OS `FOLDER NAME` · EM API `folder_name` |
| **Previously Known As** | **Table Name** |

- Together with **Job Name**, the Folder Name determines the **position of the job in the Control-M Folder hierarchy**. May include a folder name **or a folder path**.
- EXAMPLE (serial number): `SchFld03`. EXAMPLE (time period): `SeptOctFld2`.

> 🔗 **Internal standard governs this value:** the company's **PRAOCG** convention defines valid folder names here — see [folder-naming-convention](../../../knowledge/standards/technology/folder-naming-convention.md). (Also referenced from [folder-definition-parameters](controlm-folder-definition-parameters.md).)

---

## Priority

> Determines the order of job processing by Control-M in the Active Jobs database.

| Additional information | Description |
|---|---|
| **Usage** | Optional |
| **Format** | **2 alphanumeric characters** |
| **Default** | **Blank** = lowest priority |
| **Case Sensitive** | No |
| **Invalid Characters** | Single quotation marks; non-English characters |
| **Alternate Names** | EM Utilities `PRIORITY` · Report `PRIORITY` · Server Utilities `-priority` · z/OS `PRIORITY` · EM API `priority` |

**Active Jobs database prioritizing:**
- Per-character order is **`9 > 0 > Z > A`** (characters are **not** case-sensitive).
- 2-character string: **`AA` = lowest, `99` = highest**. If a single character is specified, uppercase **`A` is inserted as the first character** (e.g. priority `1` → `A1`).
- Sequence low→high (⚠️ *some middle tokens OCR-ambiguous*): `AA–A9 … ZA–Z9, 0A–0Z, 01–09, 1A–19 … 9A–99`.
- **z/OS:** if the **first character is `*` (asterisk)**, the job is a **critical path job**. *There is no relationship between the **Critical** parameter and the **Priority** parameter.*
- Resource interaction: a waiting job (quantitative resources unavailable) with higher priority does **not** preempt a ready lower-priority job — the lower one submits. Use **Critical** to force Control-M to reserve resources. (See Critical.)

> ⚠️ **Correction:** [controlm-api-job-properties](controlm-api-job-properties.md) (SaaS/JSON) described Priority as textual "Very High…Very Low" *or* `AA–99`. The classic/9.0.21.300 format is **strictly 2 alphanumeric chars (`AA` lowest … `99` highest)** — treat the textual scale as SaaS-only.

---

## Description

> Provides a description of the job in free text. A well written description can help you determine why the job was defined and how it fits into your business workflow.

| Additional information | Description |
|---|---|
| **Usage** | Optional |
| **Length** | **1–4000 characters** |
| **Case Sensitive** | Yes |
| **Variable Name** | **None** *(the description is not exposed as a `%%` variable — metadata only, cannot drive runtime behavior)* |
| **Alternate Names** | EM Utilities `DESCRIPTION` · Report `DESCRIPTION` · Server Utilities `-description` · z/OS `Description` · EM API `description` |

> 🔗 **Internal planned use:** the company plans to repurpose this 4000-char free-text field as a **structured metadata carrier** (pipe-delimited key:value pairs) for graph relationship extraction — see [description-field-metadata-plan](../../../knowledge/standards/technology/description-field-metadata-plan.md). The vendor constraints that enable this: 4000-char capacity, free text, case-sensitive, no character restrictions documented.

---

## Cross-references
- **Folder hierarchy / SMART params:** [controlm-folder-definition-parameters](controlm-folder-definition-parameters.md)
- **Ordering / `%%ODATE`:** [controlm-order-parameters](controlm-order-parameters.md)
- **`%%JOBNAME` and variable rules:** [controlm-variables](controlm-variables.md)
- **Internal folder naming (PRAOCG):** [folder-naming-convention](../../../knowledge/standards/technology/folder-naming-convention.md)
- **Internal Description-field metadata plan:** [description-field-metadata-plan](../../../knowledge/standards/technology/description-field-metadata-plan.md)
