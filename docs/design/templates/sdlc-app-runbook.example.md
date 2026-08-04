<!-- anchor: front-matter -->
# OrderHub — SDLC Application Run Book

> **TEMPLATE + WORKED EXAMPLE.** This document is the committed exemplar for
> `sdlc-app-runbook.outline.yaml` (doc type: SDLC-Runbook). Its structure is a
> verbatim transcription of a reviewed enterprise SDLC Run Book for an
> Informatica-ETL business application; **every value is synthesized** for the
> generic application "OrderHub" — no real host, schema, job, account, link, or
> person appears. To author a real run book, copy this file, keep every section
> and table shape, and replace the values. Angle-bracket tokens `<like this>`
> mark values that are always instance-specific.

| | |
|---|---|
| **Product/Application/System** | OrderHub (order-document processing portal) |
| **Document** | Run Book |
| **Project** | ExampleCo OrderHub Cloud |
| **Date** | 2026-08-04 |
| **Version** | 1.0 |
| **Classification** | Internal-Public (template; a filled instance is Internal) |
| **Reflects** | template — no commit binding; a filled instance records its source commit here |

<!-- anchor: document-control -->
## 1.0 Document Control

This section lists the details of the reviews for this document.

| Version No. | Name of Reviewer | Role | Date |
|---|---|---|---|
| 0.1 | <reviewer name> | Lead | <date> |
| 1.0 | <reviewer name> | Lead | <date> |

<!-- anchor: change-history -->
## 2.0 Change History

This section details the changes this document has undergone. Mark the current
version's rows (the source convention highlights them) so the latest changes
are visible at a glance.

| Version No. | Details of Change | Changed Sections | Prepared by | Date |
|---|---|---|---|---|
| 0.1 | Initial draft | All | <author> | <date> |
| 0.2 | Added new workflows; removed jobs no longer active | 5.2 Schedule; 6.1 ETL Jobs; 7.0 SLA | <author> | <date> |
| 1.0 | **Added details about the RPT reporting workflow** | 6.1 ETL Jobs | <author> | <date> |

<!-- anchor: purpose -->
## 3.0 Purpose

This document provides overall details about the OrderHub batch process and
acts as a reference document for the Tier 2 team (production-support
activities).

<!-- anchor: target-audience -->
## 4.0 Target Audience

The target audience for the Run Book is:

- Tier 2
- Tier 3

Refer to [Production Support](#210-production-support) for contact details.

<!-- anchor: architecture-model -->
## 5.0 Architecture Model

*The end-to-end diagram belongs here: source databases (CORELEDGER on
`CORE01P`, document store DOCSTORE on `DOC01P`), the Informatica ETL hop(s)
per environment (DEV/UAT/PROD), the DW target (`DWPROD_X`), managed file
transfer in/out, and downstream consumers — environment names on every node.*

Per-stream schedule diagrams follow, each headed by its Control-M trigger job
and start time:

**OrderHub DocLoad:**

| Control-M job | Start |
|---|---|
| POHUB1101-OHUB-TR | 01:30 AM ET |

*(diagram: DOCSTORE + CORELEDGER + portal files → OrderHub ETL → DW)*

**OrderHub Letters:**

| Control-M job | Days | Start |
|---|---|---|
| POHUB1102-OHUB-TR | MON–SUN | 7:30 PM ET |
| POHUB1103-OHUB-EVNG-TR | MON–SUN | 12:15 AM ET |

<!-- anchor: etl-process-overview -->
### 5.1 ETL Process Overview

The OrderHub ETL process populates the OrderHub application with document data
from DOCSTORE and the corresponding order information from CORELEDGER. New
cases are created for documents sent to OrderHub and placed in their work
baskets by the application. Order information is updated daily for cases still
active or pending. For detailed design, refer to the Technical Design Document
at: `<link to the application TDD in the document repository>`.

The ETL (Extract, Transform, Load) process is covered in this document across
the following layers:

a. Schedule
b. FTP / SFTP output files
c. Archival and file management
d. Informatica objects
e. UNIX objects

<!-- anchor: schedule -->
### 5.2 Schedule

| Task Name | Type | Schedule Time | Event Wait Trigger Files / Dependencies |
|---|---|---|---|
| wf_OHUB_Data_Load (document load) | Workflow | Mon–Sat 01:15 ET, Sun 13:01 ET | Docstore trigger — `/apps/infa/infa_shared/prod/data/triggerinfiles/ORDER_IMAGE_INDEX.done`. A script waits for the trigger; if it has not arrived it alerts Prod Support **every hour up to 10.5 hrs and then stops the process**. Prod Support works with the upstream team on the trigger and **restarts the workflow if the 10.5-hr window passed**. Also waits on `/apps/infa/infa_shared/prod/data/OrderHub/SrcFiles/OHUB_Stage_Load_DataLoad.done`. |
| wf_OHUB_Stage_Load | Workflow | Tue–Sun 04:00 ET *(update: no longer scheduled — follows Pre-Data-Load completion)* | `/apps/infa/infa_shared/prod/data/triggerinfiles/ledger_bde.done` |
| wf_OHUB_Delete_Old_Stage_Data | Workflow | Mon–Sun 20:00 ET | — |
| ohub_wf_monitor_v2 | Script | Mon–Sat 02:00–07:00 ET, Sun 13:00–18:00 ET | Sends workflow run statistics for wf_OHUB_Data_Load |

*(one row per scheduled workflow and monitoring script — the table is complete
in a real instance)*

<!-- anchor: archival-file-management -->
### 5.3 Archival and File Management

Data files are archived every day after the process is complete. Retention of
archived files:

| Sl# | Name | Location (Folder/Schema) | Type | Retention Period |
|---|---|---|---|---|
| 1 | OHUB_OrderData_Upd_MMDDYYYYHH24MISS.txt | /apps/infa/infa_shared/prod/data/OrderHub/Archive | Text file | 90 days |
| 2 | OHUB_Payments_Upd_MMDDYYYYHH24MISS.txt | /apps/infa/infa_shared/prod/data/OrderHub/Archive | Text file | 90 days |
| 3 | src_ohub_rpt_*yyyymmdd_001.{xml,ctl,go} | /apps/infa/infa_shared/prod/data/OrderHub/Archive | Text file | 7 days |

<!-- anchor: end-to-end-process -->
## 6.0 End-to-End Process Overview

<!-- anchor: etl-jobs -->
### 6.1 Informatica ETL Jobs

The Informatica process comprises the following workflows to process and load
data to the OrderHub application database.

**Informatica Jobs:**

| Sl# | Workflow Name | Description |
|---|---|---|
| 1 | wf_OHUB_Data_Load | Loads the documents data to the OrderHub application database |
| 2 | wf_OHUB_Delete_Old_Stage_Data | Deletes data older than 90 days in fulfillment batch tables |
| 3 | wf_OHUB_Stage_Load | Loads the staging tables from the upstream extract |
| 4 | wf_OHUB_Nightly_Update | Syncs order data for all active orders incrementally |
| 5 | wf_OHUB_Attribute_Load | Loads document attributes to the DW |
| 6 | wf_OHUB_RPT_Reporting_Loads | Loads reporting data from work tables to the reporting schema |

**Newly added workflows** (this revision):

| S.no | Workflow | Comments |
|---|---|---|
| 1 | wf_OHUB_Load_ORDER_XREF | To load the data to ORDER_XREF table from file |
| 2 | wf_OHUB_Load_FULFILLMENT_PC_WORK | To load the data to FULFILLMENT_PC_WORK table |

---

**Workflow: wf_OHUB_Data_Load**

| | |
|---|---|
| **Control-M job name** | POHUB1101-OHUB-TR |
| **Schedule Information** | Mon–Sat 01:15 ET, Sun 13:01 ET |
| **Param File Path** | /apps/infa/infa_shared/prod/code/OrderHub/ParmFiles/wf_OHUB_Data_Load.parm |
| **Src Schema/DB** | DOCPREP_OWNER@CORE01P |
| **Stg Schema/DB** | OHUBSTG@DWPROD_X |
| **Target Schema/DB** | DWADM@DWPROD_X |
| **Folder name** | map_PRD_OrderHub |
| **Source Table** | DOCSTORE_WORKED_GRID_DAILY_IMG |
| **Stage Table** | OHUB_WORKED_GRID_IMG_ADHOC, FULFILLMENT_BATCH_DOCUMENTS, FULFILLMENT_BATCH_PAYMENTS |
| **Target Table** | FULFILLMENT_FEED_DOCUMENTS |

Below is the description of each task in the workflow:

| Task Name | Task function |
|---|---|
| cmd_Docstore_TriggerCheck | Waits for the upstream trigger (`ORDER_IMAGE_INDEX.done`); sends alerts at specified intervals and stops the process after alerting Prod Support if the file is not received by the window |
| tim_Wait_Done_File | Waits for the trigger file for the configured interval, else triggers the control task to stop the parent |
| ew_Image_Trigger_Received | Event wait; succeeds when the trigger check completes and waits for the internal trigger (`FW_wf_OHUB_Data_Load.done`) created by the script |
| cmd_Initialize_ETLprocess | Records the ETL process as 'NEW' for this load cycle |
| s_m_OHUB_Document_Load | Loads DOCPREP_OWNER.DOCSTORE_WORKED_GRID_DAILY_IMG to OHUBSTG.OHUB_WORKED_GRID_IMG_ADHOC |
| s_m_OHUB_Payments_Load | Loads OHUB_PAYMENTS_TEMP and DOCSTORE_WORKED_GRID_DAILY_IMG to FULFILLMENT_BATCH_SCHEDULE and FULFILLMENT_BATCH_PAYMENTS |
| cmd_Update_ETLprocess_STGD | Records the ETL process as 'STGD' for this load cycle |
| s_m_OHUB_Delete_DocumentsData | Deletes data older than 7 days from FULFILLMENT_FEED_DOCUMENTS |
| s_m_Fulfillment_Feed_Documents_File | Extracts the outbound file from the FULFILLMENT_FEED_DOCUMENTS table |

*(repeat this block — header table + task table — for EVERY workflow in the
inventory; the two grains matter: schema@DB in the header, table-to-table in
the task rows)*

*(close with the Control-M workspace screenshot(s) for the evening batch: the
folder tree of POHUB* jobs and the flow view)*

<!-- anchor: etl-adhoc-jobs -->
### 6.2 Informatica ETL Adhoc Jobs

The workflows below run on demand (adhoc) to load data to the DW application
database.

| S.no | Workflow Name | Comments |
|---|---|---|
| 1 | wf_OHUB_Adhoc_FULFILLMENT_BATCH_DOCUMENTS_HIST_LOAD | One-time load to the table FULFILLMENT_BATCH_DOCUMENTS_HIST |
| 2 | wf_OHUB_Adhoc_ORDER_XREF_HIST_LOAD | One-time load to the table ORDER_XREF_HIST |

Conversion loads (run once per conversion, on confirmation from the DW team):

| Sequence # | Workflow Name | Comments |
|---|---|---|
| 1 | wf_Adhoc_OHUB_ORDER_XREF_Load | Loads the old→new order-number cross-reference file into the DW static stage table. On rerun, deletes and reloads conversion rows. **Source (flat file, fixed width):** `$PMRootDir/data/OrderHub/SrcFiles/ALL_XREF_CONV.txt` **Target table at DW DB `DWPROD_X`:** OHUBSTG.ORDER_XREF |
| 2 | wf_OHUB_Conversion_Accounts_Load | Loads the conversion file provided by the DW/business team to the DW stage table; identifies orders whose documents are pulled from history tables. **Source (flat file):** `$PMRootDir/data/OrderHub/SrcFiles/OHUB_Pipeline_conversion_File.csv` **Target table at DW DB `DWPROD_X`:** OHUBSTG.CONVERSION_ACCOUNTS |

<!-- anchor: unix-shell-scripts -->
### 6.3 UNIX Shell Scripts

Below are the Unix shell scripts invoked from Informatica workflows or
Control-M.

| Unix Script Name | Descriptions | Invoking Workflow (session) |
|---|---|---|
| OrderHubEnvSetup | Initializes the variables across all Unix shell scripts | Used in all the scripts |
| functions.ksh | Contains common functions used to build the DW | Used in all the scripts |
| start_infa_workflow.ksh | Runs most of the Informatica workflows; first determines whether the workflow was suspended and needs recovery, or must start from the beginning | All the workflows |
| Remove_Trigger_OrderHub.ksh | Removes all the OrderHub done files at the end of the day | Scheduled in Control-M |
| ohub_counts.ksh | Emails the live order count and ETL count to the application team | Scheduled in Control-M |
| OHUB_Archive.ksh | Archives the OHUB Upd files and performs the 90-day purge | wf_OHUB_Delete_Old_Stage_Data |
| ohub_scard_wrapper.ksh / ohub_scard.ksh / ohub_scard_params.ksh | Creates entries in the DW scorecard tables for document load, sync and letter processes (start/end times and record counts) | Scheduled in Control-M |
| wf_Jobs_Monitor_statistics.ksh | Sends run statistics of the ETL workflows for attribute and document load jobs | Scheduled in Control-M |
| DW_Load_Check.ksh | Checks DW document-processing completion to kick off the attribute load process | Scheduled in Control-M |
| ParamGen_MailTracking.ksh | Generates the parameter file for the mail-tracking load; the date parameter is replaced each day with the previous maximum date to allow incremental pull | Scheduled in Control-M |
| ohub_file_validation_generic.ksh | Validates the control file and data file — date and count in the file must match | wf_OHUB_Load_FULFILLMENT_PC_WORK |
| ohub_archival_generic.ksh | Archives all files with the current date order after the workflow run | wf_OHUB_Load_FULFILLMENT_REFRESH |
| ohub_SFTP_Outbound.ksh | Transfers files from one location to another using SFTP connections | wf_OHUB_Load_ORDER_XREF |
| RPT_Inbound_Prevalidation.ksh | Checks that all expected data and control files exist in the source directory; once found, moves them to the ETL source directory | wf_OHUB_Extract_RptFields |
| RPT_Data_ctl_Validation.ksh | Notifies Prod Support if the extract output data-file count does not match the count in the control file | wf_OHUB_Extract_RptFields |
| loadstatuscheck_docstore.ksh | Checks for availability of the latest data in the source status table by comparing against the previous max load date | wf_OHUB_Attribute_Load_Critical_Doc |
| dependent_job_status_check.ksh | Ensures the attribute load is not running while the critical-doc attribute load runs, and vice versa (mutual exclusion) | wf_OHUB_Attribute_Load & wf_OHUB_Attribute_Load_Critical_Doc |
| update_param_file.ksh | Updates the "date" parameter in the workflow parameter file with the previous execution date | wf_OHUB_Attribute_Load_Critical_Doc |
| Initialize_ETLprocess.ksh | Initializes the run-audit table (APPL_SYS_CPNT_EXEC) for the run: creates a new row for the cycle and assigns cycle metadata. Valid values: 'ATTRIBUTE LOAD' / 'ORDER DOC LOAD' | Scheduled in Control-M |
| Update_ETLprocess.ksh | Updates the run-audit table for the cycle with completion metadata | Scheduled in Control-M |
| cmd_create_control_file.ksh | Generates control files for the respective data files produced by the ETL jobs | Scheduled in Control-M |
| OHUB_Record_Count.ksh | Finds the record count of the file passed as parameter and mails it | Scheduled in Control-M |

<!-- anchor: unix-servers -->
### 6.4 UNIX Servers

DNS: `orderhub-informatica-prod.example.net`

PROD servers:

- `etl-app-01.prod.example.net`
- `etl-app-02.prod.example.net`

<!-- anchor: password-retrieval-scripts -->
### 6.5 Password Retrieval for UNIX Shell Scripts

Database passwords required by the UNIX scripts are retrieved from the
enterprise credential vault through a function call. The scripts below retrieve
passwords from the vault's application safe. The existing function
`get_connect` has been modified to achieve this.

| Script Name | Vault function call |
|---|---|
| wf_Jobs_Monitor_statistics.ksh | `get_connect ohubbat dwstg1p >> ${logfile}` |
| ohub_scard_wrapper.ksh | `get_connect etlmgr dwprod >> ${LOG_FILE}` |
| Initialize_ETLprocess.ksh | `get_connect ohubbat dwstg1p >> ${logfile}` |
| Update_ETLprocess.ksh | `get_connect ohubbat dwstg1p >> ${logfile}` |
| DW_Load_Check.ksh | `get_connect etlmgr dwsprod >> ${LOG_FILE}` |

*Note: the log-file parameter in the function call is the script log used to
record errors from the retrieval call.*

Details of the PROD safe:

| Env | Server | Safe Name | Provider Name | Vault Server |
|---|---|---|---|---|
| Prod workflow run user | `<domain-service-account-1>` | `<safe-name>` | `<provider-id>` | `vault.example.net` |
| Prod workflow deployment user | `<domain-service-account-2>` | `<safe-name>` | `<provider-id>` | `vault.example.net` |

Vaulted database accounts in the PROD safe:

| Sl# | User | Database | Password object | Comments |
|---|---|---|---|---|
| 1 | ohubbat | dwstg1p | ohubbat-dwstg1p | |
| 2 | etlmgr | dwprod | etlmgr-dwprod | |
| 3 | ~~olduser~~ | ~~olddb~~ | ~~olduser-olddb~~ | ~~Not used currently in scripts~~ |

Vault troubleshooting:

- For any vault failure, first verify the provider is running:
  `/etc/rc.d/init.d/aimprv status`
- Verify the provider logs at `/var/opt/<vault>/logs` (`APPConsole.log`,
  `APPAudit.log`) and take the action in the vendor troubleshooting guide.
- If the provider is not running or other issues are encountered, contact the
  IAM team — see [Server/Database Support](#215-serverdatabase-support).
- For further vault details, refer to `<vault operations doc>` at
  `<link to document repository>`.

<!-- anchor: password-retrieval-adhoc -->
### 6.6 Password Retrieval for Adhoc Requests

When production data must be queried ad hoc for analysis or production issues,
the maintenance IDs below, stored in the vault's break-glass safe, are used.
Production Support raises a ticket to break glass and obtain the password.

| Sl# | Maintenance FID | Database |
|---|---|---|
| 1 | OHUBBAT_MNT | CORE01P |
| 2 | OHUBBAT_MNT | DWPROD_X |
| 3 | OHUBMNT | RPT01P |

<!-- anchor: controlm-job-details -->
### 6.7 Control-M Job Details

Control-M job details are available at the location below.

FileName: `Control-M_Template_OrderHub.xlsm`

`<link to the requirements/template repository>`

<!-- anchor: service-level-agreement -->
## 7.0 Service Level Agreement

OrderHub jobs depend on upstream CORELEDGER batch (BDE) completion.

Upstream SLAs applicable to OrderHub:

- LEDGER-A — 5 AM ET
- LEDGER-B — 6 AM ET
- DOCSTORE — 8 AM ET

**DW processes:**

| DW Process | Job Name | Frequency | Expected Start Time | Expected End Time | SLA | Inbound/Outbound |
|---|---|---|---|---|---|---|
| DW DocLoad | wf_OHUB_Data_Load | Mon–Sat | 01:15 ET (dependent on Docstore trigger) | 02:30 ET | 03:00 ET | Inbound |
| DW DocLoad | wf_OHUB_Data_Load | Sun | 13:00 ET | 14:15 ET | 16:00 ET | |
| DW DocLoad | wf_OHUB_Nightly_Update | Tue–Sat | 04:00 ET (dependent on BDE, doc load, pre-data) | 06:30 ET | 10:00 ET (based on upstream SLA) | Inbound |
| DW DocLoad | wf_OHUB_Attribute_Load | Mon–Sat | ~02:00 ET (dependent on DW doc processing and Docstore trigger) | 02:30 ET | 08:00 ET | |
| DW DocLoad | wf_OHUB_Load_ORDER_A | Mon–Sun | 04:00 ET | 05:00 ET | 06:00 ET | |

*(one row per job per distinct schedule — weekday and Sunday rows separately)*

<!-- anchor: architecture-contacts -->
## 8.0 High-Level Project Technical Architecture and Project Contact Information

The OrderHub process runs using the following software tools/architecture:

- Informatica PowerCenter `<version>`
- IBM AIX OS
- Oracle `<version>`

Management staff responsible for the various aspects of the project:

| Project | Name | Role | Areas of Responsibility |
|---|---|---|---|
| OrderHub | <name> | ADM | Project Management & Support |

<!-- anchor: task-overview -->
## 9.0 Task Overview

Not applicable.

<!-- anchor: pre-installation-checklist -->
## 10.0 Pre-Installation Checklist

Refer to the Deployment Checklist.

<!-- anchor: configuration-setup -->
## 11.0 Configuration & Setup

<!-- anchor: operating-system -->
### 11.1 Operating System

N/A

<!-- anchor: database-server -->
### 11.2 Database Server

N/A

#### 11.2.1 Database Server Setup

N/A

#### 11.2.2 Creation & Setup of Database

Connect descriptors per environment:

| Env | Connect descriptor |
|---|---|
| DEV — DEV_X | `DEV_X = (DESCRIPTION = (CONNECT_TIMEOUT=120 sec)(RETRY_COUNT=20)(RETRY_DELAY=3)(ADDRESS_LIST = (LOAD_BALANCE=on)(ADDRESS = (PROTOCOL=TCP)(HOST = db-scan-dev.example.net)(PORT = 1521)))(CONNECT_DATA = (SERVICE_NAME = DEV_X_SVC)))` |
| UAT — DWUAT_X | `DWUAT_X = (DESCRIPTION = (CONNECT_TIMEOUT=120 sec)(RETRY_COUNT=20)(RETRY_DELAY=3)(ADDRESS_LIST = (LOAD_BALANCE=on)(ADDRESS = (PROTOCOL=TCP)(HOST = db-scan-uat.example.net)(PORT = 1521)))(CONNECT_DATA = (SERVICE_NAME = DWUAT_X_SVC)))` |
| PROD — DWPROD_X | `DWPROD_X = (DESCRIPTION = (CONNECT_TIMEOUT=120 sec)(RETRY_COUNT=20)(RETRY_DELAY=3)(ADDRESS_LIST = (LOAD_BALANCE=on)(ADDRESS = (PROTOCOL=TCP)(HOST = db-scan-prod.example.net)(PORT = 1521)))(CONNECT_DATA = (SERVICE_NAME = DWPROD_X_SVC)))` |

**Access request:** sample request to get access to the DW schemas —
`<link to the access-request system>`; ask for proxy access to `<reporting
schema>` and `<staging schema>`.

<!-- anchor: data-migration -->
## 12.0 Data Migration

N/A

<!-- anchor: web-server -->
## 13.0 Web Server

N/A

<!-- anchor: application-server -->
## 14.0 Application Server

N/A

### 14.1 Application Server Setup

N/A

### 14.2 Database Connection Setup

N/A

<!-- anchor: front-end-gui-setup -->
## 15.0 Front-End / GUI Setup

N/A

<!-- anchor: security-issues -->
## 16.0 Security Issues

N/A

<!-- anchor: other-packages -->
## 17.0 Other Packages

N/A

<!-- anchor: application-login-ids -->
## 18.0 Application Login IDs

This section states the list of all login ids and privileged accounts used in
the application. Retired accounts remain as struck-through rows — the table is
also the retirement record.

| Application | Systems | Login-id |
|---|---|---|
| Oracle | CORE01P | a_ohub_db_prd |
| ~~Oracle~~ | ~~OLDDB1P~~ | ~~olduser~~ |
| Oracle | RPT01P | a_ohub_db_prd |
| Unix | ETL Server | infadm/etlmgr (CONTROL-M) |
| Informatica | OrderHub folder | infadm |

<!-- anchor: directory-configuration -->
## 19.0 Content and Application Directory Configuration

This section states the list of directories for the application.

| Components of Application | Path | Owner |
|---|---|---|
| Informatica repository details | Repository: REPO_DW_PRD · Integration Service: INT_SVC_DW · Domain: DMN_NA_PRD · Gateway host/port: `etl-gw-01.prod.example.net`, `etl-gw-02.prod.example.net` /9001 · Folder: map_PRD_OrderHub | |
| All scripts location to run the process | /apps/infa/infa_shared/prod/code/OrderHub/Scripts | |
| Informatica session log files | /apps/infa/infa_shared/prod/data/OrderHub/SessLogs — one file per session | |
| Source files location | /apps/infa/infa_shared/prod/data/OrderHub/SrcFiles | |
| Target files location | /apps/infa/infa_shared/prod/data/OrderHub/TgtFiles | |
| Target FTP location | servers listed in [UNIX Servers](#64-unix-servers) | |
| Archive files location | /apps/infa/infa_shared/prod/data/OrderHub/Archive | |
| Script log files location | /apps/infa/infa_shared/prod/data/OrderHub/scriptlogs | |

<!-- anchor: recovery-procedures -->
## 20.0 Recovery Procedures

Manual.

| Sr. No. | Failure Category | Probable Failure Reasons | Action Required |
|---|---|---|---|
| 1 | All | Any | Contact Level 2 support |
| 2 | Control-M downtime/outage | Scheduler unavailable | **Execute the script** `$PMRootDir/code/OrderHub/Scripts/OHUB_check.ksh OrderHub` **and check for the done file** `$PMRootDir/data/OrderHub/SrcFiles/OHUB.DONE.YYYYMMDD` **before starting any workflows/jobs** |

**Special-case recovery for wf_OHUB_Stage_Load:**

- **Same-day recovery** — for any failure on the same day, restart the workflow
  from the failed task, but do not run any task multiple times until confirmed
  by the AD team.
- **Recovery in case of multiple days' load** — for any missed day, run the
  adhoc workflow `wf_OHUB_ONETIME_Load_ADVANCE_TRAN` after changing its
  parameter file `wf_OHUB_ONETIME_Load_ADVANCE_TRAN.parm`:

  ```
  $$OVERRIDE_QUERY=SELECT DISTINCT ORDER_NUMBER, UPDATE_STATUS_CD, ADV_TRANSACTION_DATE,
  ADV_TRANSACTION_CODE, ADV_AMOUNT, ADV_PAYEE_ID, ADV_REASON_CODE, ADV_SEQUENCE_NUMBER
  FROM SRCMGR.ADVANCE_TRAN_R WHERE UPDATE_STATUS_CD IN ('I','U')
  AND TRUNC(LOAD_DT) >= to_date('<missed-load-date>','DD-MON-YY')
  ```

  The date literal is the missed load date from the source DB — reach out to
  the AD team when recovering the workflow for any old date.
- **At no time should there be multiple loads for a single day, and this job
  should never be skipped for any odate.**

<!-- anchor: production-support -->
## 21.0 Production Support

<!-- anchor: alerts -->
### 21.1 Alerts Generated by System

Two types of alerts are generated by the system:

- **Threshold Alert** — the process either has not started on time or has not
  ended on time.
- **Failure Alert** — there is an issue with the execution of the process; it
  needs to be fixed/debugged and restarted.

| Sr. No. | Failure Category | Probable Failure Reasons | Action Required |
|---|---|---|---|
| 1 | Failure | Any job failure | Contact Level 2 Support |
| 2 | Threshold | The process has not started on time | Automated email notification |
| 3 | Threshold | The process started on time but has not ended on time, or hangs | 1) Automated email notification 2) Escalate if the process hangs or takes unusually long |

<!-- anchor: job-monitoring -->
### 21.2 ETL Job Monitoring / Visual Confirmation

Informatica jobs are monitored using Workflow Monitor; any failure or deviation
from scheduled run timings/SLA is captured and reported. The on-call support
person is contacted in such scenarios via pager. This monitoring also ensures
platform-level issues (e.g., the Informatica server down) are captured and
reported. Sample incremental-load and full-refresh reports are used for
capturing daily run statistics.

#### 21.2.1 ETL Rejects

ETL jobs fail when records get rejected for any reason. Sessions in the
workflow are configured to **fail on the first error** (session config:
`Stop on errors = 1`). Prod Support identifies the root cause and follows up
with the appropriate teams to resolve the issue before proceeding with the
ETL load. *(screenshot: session Config Object → Error handling, with Stop on
errors = 1 highlighted)*

<!-- anchor: tier2-escalation -->
### 21.3 General Tier 2 Escalation Procedures

Escalation procedure for production-support calls, by type of problem.

**Tier II and steady-state contact list (sorted by escalation level):**

| Escalation Level | Role | Primary Contact # | Comments |
|---|---|---|---|
| 1 | Level 2 Support | <phone> · Queue: <ticket-queue> | <name> (Prod Supp) |
| 2 | Default IT / Developers — 1st point escalation | <phone> | <name> (Developer) |
| 3 | Manager — 2nd point escalation | <phone> | <name> |

**Guidelines for the escalation process:**

1. If the trigger file `ORDER_IMAGE_INDEX.done` is **not** received by
   **02:15 ET**, contact the upstream document-store prod support to check the
   trigger's status. The ETL job alerts Prod Support hourly from 02:15 ET up to
   10.5 hrs and then gracefully stops. Level 2 works with the upstream team to
   send the trigger; if 10.5 hrs passed after job start and the final alert was
   received, the workflow must be restarted.
2. If the upstream ledger load is not complete and its trigger is not received
   by the deadline, the Control-M job sends email alerts to Prod Support at the
   configured times; Prod Support works with the upstream batch L2 team.
   The mail message reads:
   > Mail message from CONTROL-M: Job <job-id>: upstream Control-M job for
   > <view refresh> (condition <condition-name>) is not complete yet. Please
   > work with <upstream> Prod support.
3. If any OrderHub workflow/session fails, escalate to **Level 2 Support**; if
   the issue continues and poses any threat to SLA, escalate per the contact
   list. The task-failure description is sent in the status-report email body
   using the mailing list:

   > Hi All,
   >
   > Following OrderHub job has failed during execution:
   >
   > Status: FAILED
   > Workflow: `<workflow>`
   > Task/Session Name: `<task>`
   >
   > Error Message: `<copy from task log, e.g. session log>`
   >
   > Please acknowledge upon receiving this notification.

4. Contact/mailing list: for all the guidelines above, notifications are
   addressed to: To: `<app ETL support DL>`; Cc: `<upstream + business DLs>`.

<!-- anchor: security-admin-support -->
### 21.4 Security Administration Support

N/A

<!-- anchor: server-database-support -->
### 21.5 Server/Database Support

**Server/Database support contact list:**

| Escalation Level | Role | Primary Contact | Alternate Contact |
|---|---|---|---|
| 3 | Unix SA | <server team / change queue> | <names> · <ticket-queue> (queue name for tickets) |
| 3 | Source Oracle DBA | <DBA queue> | |
| 3 | Informatica Admin | <name> | |
| 3 | Vault IAM | <name> | <IAM team> |

**ETL process failure & contact information:**

| Area | Name | Primary Contact # | Comments |
|---|---|---|---|
| ETL | <name> | <phone> | |
| ETL | <name> | <phone> | Offshore |

<!-- anchor: business-contact -->
### 21.6 Business Contact

| Group | Contact | Role | Primary Contact # | Secondary Contact # | Responsibility |
|---|---|---|---|---|---|
| OrderHub Prod Support | <name> | Prod Support Manager | <phone> | <phone> | |
| OrderHub Development | <name> | Development Manager | <phone> | | |

<!-- anchor: appendix -->
## 22.0 Appendix

The additional or external teams to be contacted in case of support/recovery
issues:

| Sr. No. | Name of Team | Primary Contact | Secondary Contact |
|---|---|---|---|
| 1 | Application Team | <name> | <name> |
| 2 | Connectivity Services | <name> | |
| 3 | Upstream Ledger Support | <upstream L2 batch support DL> | |
