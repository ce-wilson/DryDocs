# Control-M Folder Definition Parameters (Classic Parameter Reference)

**Source:** BMC Control-M/EM client Help — **classic Parameter Reference** (the parameter-centric documentation style, breadcrumb family `Parameters > …`).
**Captured:** 2026-06-11, transcribed from product Help screenshots (`bmc-screnshot-smartfolder1.png`, `bmc-screnshot-smartfolder2.png`, `bmc-screnshot-folder-parameters.png`).
**Purpose:** Authoritative folder / SMART-folder / sub-folder parameter list for the **XML-era / 9.0.21.300** environment.

✅ **This doc matches the target environment.** Unlike the SaaS-derived `controlm-folder-creation.md` (JSON Automation API framing), this is the classic Parameter Reference — same family as the `Command` parameter page — and is the **preferred folder reference for 9.0.21.300**. See [[project-controlm-xml-not-json]].

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** = transcribed from the BMC Help screenshot · **[GROUNDED]** = light paraphrase of that text · **[SYNTHESIZED]** = added by Claude.

- **Essentially the entire parameter table below is [VERBATIM]/[GROUNDED]** — transcribed directly from the product Help, not reconstructed. This is high-fidelity vendor content.
- **[SYNTHESIZED]:** only the cross-reference notes explicitly marked as such, and the "Internal standard" pointers (which link out to the separate internal corpus — NOT vendor assertions).

⚠️ One transcription caveat: the SMART Folder intro line was cut off in the screenshot at "Only Control-M/Server…" — final clause not captured.

---

## Folder Types (overview)

> Jobs are sorted into the following types of folders:

- **Regular folder** — Enables you to define a container for jobs. Jobs in a regular folder are normally processed **independently** of each other; each job is handled only according to the parameters in its own job processing definition.
- **SMART Folder** — Enables you to define **extended processing parameters**. The jobs and sub-folders contained in the SMART folder inherit the scheduling definitions according to the specific **AND/OR relationships** defined in the job and in the SMART folder. When a SMART Folder is ordered and runs, you can monitor its status in the Monitoring domain and perform actions affecting its jobs and sub-folders. Just as you can define post-processing tasks that Control-M/Server performs when a job successfully finishes, you can define post-processing tasks performed when **all** jobs in a SMART folder successfully finish.
- **Sub Folder** — Enables you to apply the extended processing parameters to folders contained in a SMART folder. When you add a folder to a SMART folder, the Sub Folder can inherit the extended processing parameters of the SMART folder. When you order a SMART folder with Sub Folders, you can monitor the status of the SMART folder, the sub-folders, and the jobs, and perform actions affecting the sub-folder and its jobs.

> **z/OS constraint:** SMART folders can only contain jobs, **not** sub-folders, in Control-M for z/OS.

(For organizing jobs into folder types for scheduling, see *Specific Rule-based calendar scheduling*.)

---

## SMART Folder Parameters

> The following table describes parameters for a SMART folder used to define scheduling, prerequisites, and actions of the jobs and Sub Folders contained in the SMART folder. (Only Control-M/Server … *[intro truncated in source]*)

| Parameter | Description |
|---|---|
| **SMART** | Defines whether a folder is SMART. When selected, the folder has an extended set of folder definition parameters and can include Sub Folders. The jobs and Sub Folders in the SMART Folder can **inherit scheduling definitions** from the SMART Folder that contains them. To define a regular folder, clear the check box (see Regular folder parameters). |
| **Folder Type** | Indicates whether the folder type is a regular folder, a SMART folder, or a Sub Folder. Value: **SMART**. |
| **Folder Name** | Defines the name of the folder; indicates the folder where the job belongs. **Length 1–64 (z/OS 1–8); case-sensitive; invalid chars: blanks, single quotes, `$ / * ?`, space; not a variable; formerly "Table Name".** Full param detail → [general-parameters](controlm-general-parameters.md#folder-name). → *Internal standard governs this value:* see [folder-naming-convention](../../../knowledge/standards/technology/folder-naming-convention.md). |
| **Description** | Provides a description of the job in free text. A well-written description helps determine why the job was defined and how it fits into your business workflow. |
| **Folder Library** | Defines the name of the library that contains the job's folder. **Only z/OS folders.** |
| **Control-M/Server** | Defines the name of the Control-M/Server (or Control-M for z/OS) that processes the job. |
| **Order Method** | Defines the method for ordering the entity, one of: <br>• **Automatic (Daily)** — at the same time each day (**New Day** time), each Control-M/Server runs the New Day procedure, which schedules the day's jobs and runs maintenance/cleanup; it orders the folder or folder jobs. <br>• **None (Manual Order)** — the folder is not automatically ordered. <br>• **Specific User Daily** — identifier used to assign the folder to a specific User Daily job, ordered at a specific time of day (used for load balancing across the day, other than New Day time). |
| **User Daily name** | Defines User Daily jobs whose sole purpose is to order jobs. Instead of directly scheduling production jobs, the New Day procedure can schedule User Daily jobs, which in turn schedule the production jobs. Set when Order Method = Specific User Daily. |
| **Run as** | Identifies the user name with the authorization to execute the job. Used by the Control-M security mechanism. |
| **More** | Defines an area of the Properties pane to click to define more parameters. |
| **Variables** | All variables are identified by the **`%%` prefix**. If `%%` is included in the value for a job processing parameter, Control-M assumes it refers to a variable or function. (See *Adding a variable*.) |
| **Additional Information** | An area in the Properties pane with: Application, Sub Application, Created by (**not z/OS folders**). |
| **Application** | Provides a logical name for sorting groups of jobs — a common descriptive name for a set of related job groups. The jobs do not necessarily run at the same time. |
| **Sub Application** | Name of the Sub Application where the job belongs logically; a sub-category of Application. (e.g., Application = Finances, Sub Application = Payroll.) |
| **Created by** | Indicates the Control-M/EM user who defined the job. (**not z/OS folders**) |
| **Documentation** | Defines a description related to the job, saved in a defined location. z/OS: in a Doc Member in a Doc Library. Non-z/OS: depends on whether type is File or URL. |
| **Type** (documentation) | Defines whether the documentation for an OS job is in a **file** or **URL**. URL format starts with `http://`, `ftp://`, or `files://`. File: specifies the file that contains the job script. |
| **Doc Path** | z/OS: Doc Library = name of the library where Documentation is saved. Non-z/OS: file path where Documentation is saved. |
| **Doc File** | z/OS: name of the member where Documentation is saved. Non-z/OS: name of the file where Documentation is saved. |
| **Priority** | Determines the order of job processing by Control-M in the Active Jobs database. |
| **Enforce Validations** | Read-only. Indicates whether the folder's enforcement policy requires resolving all validation errors. |
| **Site Standard** | Applies the defined **Site Standard** to the folder and all jobs contained in it. If only one Site Standard exists, it is selected by default; if none are defined, set to **None**. (Contact your Control-M Administrator.) → *This is the BMC mechanism that could enforce the internal naming standard — see note below.* |
| **Business Parameters** | Defines one or more Business parameters, according to the selected Site Standard. If Site Standard = None, no Business parameters are displayed. |

---

## 🔗 Cross-corpus note: Site Standard ↔ internal naming convention

The **Site Standard** + **Business Parameters** + **Enforce Validations** parameters are the *vendor mechanism* by which an organization can enforce folder/job definition rules (including naming). The company's **PRAOCG folder naming convention** is an *internal standard* that maps onto this mechanism. The two are deliberately kept in **separate corpora**:

- **Vendor (this file):** the Folder Name field exists; Site Standards can enforce rules. *(capability — "what's possible")*
- **Internal:** [folder-naming-convention](../../../knowledge/standards/technology/folder-naming-convention.md) defines what a valid folder name *is* here. *(conformance — "our standard")*

This is the two-stage validation split — see [[project-drydocs-scrape-two-corpus]].

---

## Notes for Planning Agents

1. **Use this over `controlm-folder-creation.md`** for the authoritative folder parameter list in a 9.0.21.300/XML environment — it's transcribed from the classic Parameter Reference, not the SaaS JSON pages.
2. **Order Method** has three real values (Automatic/Daily, None/Manual, Specific User Daily) tied to the **New Day** procedure and **User Daily** ordering jobs — operational detail absent from the SaaS-derived docs.
3. **Site Standard / Business Parameters / Enforce Validations** are the enforcement hooks for organizational standards — the bridge to the internal naming convention.
4. z/OS-specific fields (Folder Library, Doc Library/Member) are flagged inline.
