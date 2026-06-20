# Control-M Order Parameters & ODATE Logic (Classic Parameter Reference)

**Source:** BMC Control-M/EM client Help — **classic Parameter Reference** (`Parameters > … > Order`).
**Captured:** 2026-06-11, transcribed from product Help screenshot (`bmc-screnshot-order-parameters.png`).
**Purpose:** How jobs/folders are **ordered** into the Active Jobs database, and the **Order Date (ODATE)** logic — supplement to scheduling and `%%ODATE`.

✅ Matches the target environment (**9.0.21.300 / XML**, classic Parameter Reference family). See [[project-controlm-xml-not-json]].

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** transcribed from Help · **[GROUNDED]** light paraphrase · **[SYNTHESIZED]** Claude-added.

- The parameter table below is **[VERBATIM]/[GROUNDED]** — transcribed from the Help screenshot, not reconstructed.
- **[SYNTHESIZED]:** only the "ODATE logic — how it fits" interpretation section and cross-references, marked as such.
- ⚠️ Minor truncation: intro line cut at "…Planning and Monitoring doma[ins]".

---

## What "ordering" means

> The Order parameters describe ordering from the Planning and Monitoring domains.

**Ordering** = placing a job or folder into the **Active Jobs database** with an assigned **Order Date (ODATE)**. Ordering is distinct from running: once ordered, scheduling criteria + prerequisites decide *if/when* it actually runs (see two-plane model in [controlm-job-scheduling](controlm-job-scheduling.md)).

---

## Order Parameters

| Field | Description |
|---|---|
| **Control-M** | *(Monitoring domain only)* Name of the Control-M/Server (or Control-M for z/OS) that processes the job. |
| **Folder** | *(Monitoring domain only)* Name of the folder. The icon opens the folder's parameter settings. (See [folder parameters](controlm-folder-definition-parameters.md).) |
| **Library** | *(Monitoring for z/OS only)* Name of the library that contains the job's folder. |
| **Jobs** | *(Monitoring domain only)* How to select the jobs to order: <br>• **All Jobs** — select all jobs. <br>• **Selected jobs** — select jobs/folders from a tree or grid view (grid view allows delete, edit, move, filter columns). <br>• **Mask** — filter jobs. |
| **Ignore scheduling criteria** | Determines if the job or folder is placed in the Active Jobs database **regardless of the scheduling criteria**. |
| **Hold** | Determines if the job or folder is put on **Hold** as it enters the Monitoring domain — lets you make changes to a job before it starts running. |
| **Order as independent flow** | Determines if a flow in a folder is ordered **uniquely** (a unique suffix is added to every condition name). Only when ordering a single folder created in version **8.0.00+**. **Not applicable to sub-folders.** (See Conditions management.) |
| **Current working date** | Determines if the job or folder is scheduled on the **current working date** (date includes the year). To choose another date, clear this option. |
| **Select a date** | Determines if the job or folder is ordered on a **selected date** (including year). To use the current working date instead, clear this option. |
| **Wait for Order Date to run** | Determines if jobs must **wait for the defined Order date** to run. *Example: time-zone jobs are ordered **before** their order date.* |
| **Order Into Folder** | How to order jobs/Sub Folders belonging to a SMART Folder: <br>• **New** — insert into a new folder <br>• **Recent** — insert into a recent folder <br>• **Selected** — insert into a selected folder (use the **Folder Order ID** field) <br>• **Standalone** — insert into a regular folder (disables **Create Duplicate**) <br><br>If inserted into an existing folder/Sub Folder that has **already completed**, the status of all parent folders is set to **Executing**. If not possible due to scheduling criteria, the job remains in **WAIT_SCHEDULING** status. **Ignored if the ordered folder is not a SMART Folder.** |
| **Create Duplicate** | Defines if Jobs/Sub Folders with the **same name** already existing in the Folder are added to the SMART folder when you select **Recent** or **Selected**. |
| **Set Variables** | Ad-hoc variable assignments you can add at order time, in addition to those in the job definition. (See [variables](controlm-variables.md).) |

---

## ODATE logic — how it fits *(synthesized interpretation)*

The **Order Date (ODATE)** is the scheduling date assigned when a job is ordered, exposed as the **`%%ODATE`** system variable ([controlm-variables](controlm-variables.md)). The three ordering-date controls above set it:

| Parameter | Effect on ODATE |
|---|---|
| **Current working date** | ODATE = the current **working date** (New Day working date, includes year) — the normal/automatic case driven by the **New Day** procedure (Order Method = Automatic/Daily; see [folder-definition-parameters](controlm-folder-definition-parameters.md)). |
| **Select a date** | ODATE = an explicitly chosen date — used for back-dated / forward-dated manual orders. |
| **Wait for Order Date to run** | Decouples *ordering time* from *run eligibility*: a job can be ordered **ahead of** its ODATE (e.g. time-zone jobs) and held until the ODATE arrives. |

Practical notes:
- `%%ODATE` (and date math via `%%CALCDATE`) resolve against the ODATE set here, **not** the wall-clock run time — important for date-derived file names, partitions, and `CALCDATE` offsets.
- `Ignore scheduling criteria` forces a job into the Active Jobs DB even when its scheduling rule would exclude that ODATE — i.e. a manual override of the scheduling plane, leaving prerequisites still in force.
- `Order Into Folder` + `WAIT_SCHEDULING` / `Executing` status transitions matter when injecting jobs into already-running or completed SMART folders.

---

## Cross-references

- **Scheduling plane:** [controlm-job-scheduling](controlm-job-scheduling.md) (two-plane model; ordering feeds it)
- **`%%ODATE` / `%%CALCDATE`:** [controlm-variables](controlm-variables.md)
- **New Day / Order Method / User Daily:** [controlm-folder-definition-parameters](controlm-folder-definition-parameters.md)
- **Default time-of-day (internal):** ODATE sets the *date*; when a folder declares **no time**, the **data center name** supplies the default time (all EST) — see [data-center-naming-convention](../internal-standards/data-center-naming-convention.md).
