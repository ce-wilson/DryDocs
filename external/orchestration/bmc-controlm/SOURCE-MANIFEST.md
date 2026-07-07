# BMC Control-M Documentation - Source Manifest

**Project:** DryDocs Vendor-BMC  
**Last Updated:** 2026-06-11  
**Purpose:** Track all scraped documentation sources, identify overlaps, and maintain cross-reference guide

**Version Notice:** ⚠️ SaaS source | Target: Control-M 9.0.21.300
**Classification:** `External` (public BMC documentation fetched from documents.bmc.com URLs — see per-doc URL + Date Scraped below). Publishable. See `config/classification.yaml`.

---

## 🗺️ PHYSICAL DATA MODEL — poster (added 2026-07-02)

- **File:** `BMC_ControlM_SVR_v6.4.01_DB_Poster.pdf` — BMC Control-M/Server 6.4.01
  physical data model (the `CMS_*` definition + `CMR_*` runtime tables, seven
  groups, PKs + columns + relationships).
- **Classification:** `External` doc, but the **raw PDF is a copyrighted BMC
  binary → gitignored** (`external/orchestration/**/*.pdf`), kept as local
  reference only. This repo is sometimes published; the summaries are ours, the
  vendor binary is not.
- **Trust:** the schema facts (table names / PKs / columns) are **GROUNDED** to
  BMC and transcribed into the `controlm-db` skill
  (`.claude/skills/controlm-db/references/er-model.md`). The vendor→company
  `CM_` crosswalk and all query recipes in that skill are **SYNTHESIZED**.
- **Version caveat:** poster is **6.4.01**; our target is **9.0.21.300**. Use it
  for entity relationships and column semantics, not for exact `psgmgr` object /
  column names — those come from `drydocs/loaders/sql/controlm_*.sql`. Newer
  version splits combined `CMS_CON_J` into `LNKI`/`LNKO` and adds the versioned
  `DEF_V*` view layer. See the skill's `schema-crosswalk.md`.

---

## 📑 PROVENANCE MODEL (read before graph ingestion)

Every `controlm-*.md` file was produced by **WebFetch of a single BMC page, then summarized and restructured by Claude.** These files are a human/agent *reference*, **not a source-of-record.** Before loading any of this into the knowledge graph, classify content into three tiers and set `provenance` on each chunk accordingly:

| Tier | Meaning | Graph treatment |
|---|---|---|
| **[VERBATIM]** | Direct BMC quote (passages in `"quotes"`) | Citable to BMC source URL |
| **[GROUNDED]** | Claude paraphrase of content present in the WebFetch extract — parameter/constraint tables, documented values, feature descriptions | Citable to BMC; wording is Claude's |
| **[SYNTHESIZED]** | Claude-authored, **not in source** — all code/JSON examples, "Patterns" / "Best Practices" / "Use Cases" / "Notes for Planning Agents" / workflow diagrams, and "Vendor Attributes" rollups | **Do NOT load as vendor ground truth.** Inference layer only |

**Default tier rule (applies to every file unless its own header overrides):**
- Opening *Definition and Purpose* + any `"quoted"` text → VERBATIM/GROUNDED
- Parameter tables, constraint tables, documented value/enum lists → GROUNDED
- All ```code/json``` blocks, Patterns, Advanced Patterns, Integration Patterns, Best Practices, Use Cases, Notes for Planning Agents, workflow/ASCII diagrams, Vendor Attributes table → **SYNTHESIZED**

Each file carries its own **📑 Provenance** block after the version notice with file-specific hazard callouts (places where the source explicitly *lacked* detail that Claude nonetheless illustrated).

**Why this matters (see project memory `project-drydocs-scrape-two-corpus`):** the vendor corpus validates the *model* ("is this legal per Control-M?"). If synthesized JSON shapes load as vendor-verbatim, the "legality" layer is polluted with Claude inference and the two-stage validation (vendor legality → internal conformance) breaks.

> ## ⚠️ FORMAT MISMATCH — JSON API pages vs our XML environment
>
> The four `controlm-api-*.md` files document the **Control-M Automation API (JSON)**, a **SaaS-only** interface. Our target (**9.0.21.300**) defines jobs/folders in **XML** (export/import, ctmdefine/ctmdeffolder/ctmpsm). **Decision (2026-06-11): do NOT convert these to JSON and do NOT rework the JSON into valid JSON.** They are demoted to **conceptual reference only** — mine them for *which properties/constraints/behaviors exist* that may add detail applicable to our XML, never for syntax.
>
> Confirmed 2026-06-11: the synthesized JSON is also **structurally wrong** vs the real API — canonical Automation API uses the object **name as the JSON key** (`"FolderSample": { "Type": "Folder", ... }`), jobs nested as named keys, types like `Job:Command`; my files invented a `"Name"` property + `"Jobs": []` array matching neither real form. Each API file carries a top-of-file warning.
>
> **GAP (acquisition STARTED 2026-07-02):** the XML-format definition docs (the real
> source-of-record for 9.0.21.300 config) are now tracked in
> `controlm-xml-definition-format.md` — an **acquisition stub**: exact fetch list
> identified, fetch blocked by documents.bmc.com 403 bot-protection from the producer
> environment; complete it from the company network, or better, from the local `.dtd`
> files in `<EM home>\Default\data\Resource` + a real `exportdeftable` output. Key fact
> already banked: XML definition files are **deprecated from 9.0.21.100, fully supported
> until 9.0.22** — our 9.0.21.300 sits inside the supported-but-deprecated window.

---

## 🔥 TOP 5 - HIGHEST PRIORITY DOCUMENTS

These five documents cover the foundational concepts and are referenced by almost all other topics:

### ⭐ 1. Control-M Planning - Core Architecture
- **File:** `controlm-planning-specifications.md`
- **Type:** Architecture, Foundational
- **Size:** 5.5 KB | **Usage:** Essential for understanding Control-M concepts
- **Key Content:** Planning domain, jobs, folders, workspaces, integration landscape
- **Used By:** All other documents reference this foundation

### ⭐ 2. Job Properties API - Complete Job Model
- **File:** `controlm-api-job-properties.md`
- **Type:** API Reference (JSON/SaaS) — ⚠️ **CONCEPTUAL ONLY for 9.0.21.300 (XML)**
- **Size:** 18 KB | **Usage:** Property/constraint/behavior catalog, NOT a syntax source for our XML
- **Key Content:** Type system, scheduling, events, actions, notifications, variables, resources
- **Caveat:** JSON format ≠ our XML format; JSON structure synthesized/inaccurate. Re-rank candidate — for XML work prefer `ctmdefine` / `ctmdeffolder` / `controlm-job-scheduling`.

### ⭐ 3. Job Scheduling - Temporal Control System
- **File:** `controlm-job-scheduling.md`
- **Type:** Core Feature, Architecture
- **Size:** 9 KB | **Usage:** Required for all scheduling logic
- **Key Content:** Two-plane model, calendar integration, exception handling, inheritance
- **Used By:** Every scheduled job definition

### ⭐ 4. Job Actions - Conditional Automation
- **File:** `controlm-job-actions.md`
- **Type:** Core Feature, Automation
- **Size:** 10 KB | **Usage:** Enables workflow branching and automation
- **Key Content:** If-statements, 8+ action types, notifications, event generation
- **Used By:** Complex workflow implementations

### ⭐ 5. Folder API - Hierarchy & Inheritance
- **File:** `controlm-api-folder-reference.md`
- **Type:** API Reference (JSON/SaaS) — ⚠️ **CONCEPTUAL ONLY for 9.0.21.300 (XML)**
- **Size:** 10 KB | **Usage:** Folder property/behavior concepts, NOT a syntax source for our XML
- **Key Content:** Folder types, nesting, inheritance, variables (concepts only — JSON structure synthesized/inaccurate)
- **Caveat:** JSON format ≠ our XML format. Re-rank candidate — for XML work prefer `controlm-folder-creation` / `ctmdeffolder`.

---

## Complete Documentation Library by Category

### CORE FEATURE DOCUMENTS (Used with all jobs)

#### Variables & Parameterization
- **File:** `controlm-variables.md`
- **Type:** Core Feature Reference
- **Size:** 14 KB | **Scope:** 4-level variable scoping (Local, Folder, Global, Pool)
- **Content:** System variables, functions (CALCDATE, GETENV, SUBSTR, WCALC, BLANK), inheritance, constraints
- **Status:** Complete

#### Events & Job Sequencing
- **File:** `controlm-events.md`
- **Type:** Core Feature Reference
- **Size:** 11 KB | **Scope:** Job-to-job dependencies and workflow triggers
- **Content:** Standard/Global events, wait-for-event, Boolean logic (AND/OR), event inheritance, dynamic properties
- **Status:** Complete

#### Calendars & Date Rules
- **File:** `controlm-calendars.md`
- **Type:** Core Feature Reference
- **Size:** 15 KB | **Scope:** Three calendar types with RBC and exception handling
- **Content:** Rule-Based Calendars (RBC), confirmation calendars, exception policies, Shift By, activity periods
- **Status:** Complete

#### Pattern-Matching & Filtering
- **File:** `controlm-pattern-matching.md`
- **Type:** Core Feature Reference
- **Size:** 10 KB | **Scope:** String matching, wildcards, regex patterns
- **Content:** Wildcards (*, ?, ., !, +, {n}), escaping, IF MATCHES operator, performance optimization
- **Status:** Complete

---

### FOLDER HIERARCHY DOCUMENTS

#### Sub-folders (Nested Organization)
- **File:** `controlm-subfolder-creation.md`
- **Type:** Hierarchy Configuration
- **Size:** 9 KB | **Scope:** Sub-folder nesting within SMART folders (max 9 levels)
- **Content:** Nesting constraints, reference sub-folders, inheritance mechanism, naming rules
- **Status:** Complete

#### Folder Creation & Configuration
- **File:** `controlm-folder-creation.md`
- **Type:** Hierarchy Configuration (SaaS-derived) — ⚠️ superseded for parameter list by classic-param-ref below
- **Size:** 6 KB | **Scope:** SMART vs. Regular folder types and properties
- **Content:** Folder types, core properties, configuration tabs, naming constraints
- **Status:** Complete (retire candidate)

---

### CLASSIC PARAMETER REFERENCE (9.0.21.300 / XML-aligned — transcribed from product Help)

These are **GROUNDED/VERBATIM** transcriptions of the classic Parameter Reference (same family as the `Command` parameter page), and are the **preferred** references for the XML environment over SaaS-derived files. See [[project-controlm-xml-not-json]].

#### Folder Definition Parameters
- **File:** `controlm-folder-definition-parameters.md`
- **Type:** Classic Parameter Reference — authoritative folder/SMART/sub-folder parameter list
- **Content:** SMART folder param table (Order Method/New Day/User Daily, Site Standard, Business Parameters, Enforce Validations), folder-types overview; cross-links to internal naming standard
- **Status:** Complete | Supersedes `controlm-folder-creation.md` for parameters

#### Order Parameters & ODATE Logic
- **File:** `controlm-order-parameters.md`
- **Type:** Classic Parameter Reference — job/folder ordering + Order Date logic
- **Content:** Order param table (Jobs/Mask, Ignore scheduling criteria, Hold, Order Into Folder, Create Duplicate, Set Variables); ODATE logic (Current working date / Select a date / Wait for Order Date) tied to `%%ODATE`
- **Status:** Complete

#### General Parameters — Job Name · Folder Name · Priority
- **File:** `controlm-general-parameters.md`
- **Type:** Classic Parameter Reference — identity + priority parameters
- **Content:** Job Name (length/invalid chars, `%%JOBNAME`, override via `ctmorder -variable`, BMC naming rule-of-thumb AAA-TTT-FFFFFFFF); Folder Name (1–64/z8, invalid chars, "Table Name", → PRAOCG); Priority (2 alphanumeric, AA lowest/99 highest, 9>0>Z>A, z/OS `*`=critical path)
- **Corrections:** Priority — classic format is strictly 2 alphanumeric (supersedes SaaS "Very High…Very Low" in `controlm-api-job-properties.md`)
- **Status:** Complete

---

### JOB EXECUTION TYPE DOCUMENTS

#### OS Job Types (Command, Script, Embedded)
- **File:** `controlm-os-job-parameters.md`
- **Type:** Job Execution
- **Size:** 14 KB | **Scope:** Four OS execution models (Command, Script, Embedded, Detached)
- **Content:** Script paths, command syntax, embedded script limits (64KB), interpreter specification, RunAs user
- **Critical Constraint:** Folder variables NOT available to job scripts (job-level required)
- **Status:** Complete

#### File Watcher Job (Event-Driven Detection)
- **File:** `controlm-file-watcher.md`
- **Type:** Job Execution, Event-Driven
- **Size:** 12 KB | **Scope:** File system monitoring and event triggering
- **Content:** Create/Delete modes, watch conditions, time limits, file age, system variables (%%FileWatch-FILE_PATH)
- **Protocols:** FTP, SFTP, cloud APIs (S3, Azure, GCP, Oracle Object Storage, AS2, SharePoint)
- **Status:** Complete

#### File Transfer Job (Distributed Management)
- **File:** `controlm-file-transfer-job.md`
- **Type:** Job Execution, Data Management
- **Size:** 4 KB | **Scope:** Seven transfer operations with cloud platform support
- **Content:** Standard, watch & transfer, watch-only, directory listing, bidirectional sync, incremental, concurrent
- **Cloud:** S3, Azure, GCP, Oracle; FTP/SFTP protocols; AS2, SharePoint
- **Status:** Complete

#### Infrastructure as Code Job (Cloud Deployment)
- **File:** `controlm-infrastructure-as-code.md`
- **Type:** Job Execution, Cloud Orchestration
- **Size:** 4 KB | **Scope:** Five IaC platforms for cloud infrastructure
- **Platforms:** Ansible AWX, AWS CloudFormation, Azure Resource Manager, GCP Deployment Manager, Terraform
- **Features:** Version control (VCS), GitOps, rollback, error tolerance, retry with polling
- **Status:** Complete

---

### REST/JSON API REFERENCE DOCUMENTS

#### Job Types API (Command, Script, Execution)
- **File:** `controlm-api-job-types.md`
- **Type:** API Reference, JSON/REST
- **Size:** 10 KB | **Scope:** Four job type execution specifications
- **Platforms:** Windows, UNIX/Linux; Path escaping, interpreter identification, pre/post commands
- **Status:** Complete

#### Job Properties API (Complete Job Model)
- **File:** `controlm-api-job-properties.md`
- **Type:** API Reference, JSON/REST
- **Size:** 21 KB | **Scope:** Comprehensive job object specification
- **Content:** Type system, scheduling (When object), events, conditions, actions, notifications, cycles, resources
- **Status:** Complete

#### Connection Profiles API (Cloud Authentication)
- **File:** `controlm-api-connection-profiles.md`
- **Type:** API Reference, JSON/REST
- **Size:** 10 KB | **Scope:** Multi-cloud credential and authentication management
- **Platforms:** AWS ECS, AWS App Runner, Azure Container Instances, GCP Cloud Run, Kubernetes
- **Auth:** 10+ methods (Secret, IAM Role, Service Principal, Managed Identity, OAuth2, BasicAuth, etc.)
- **Status:** Complete

---

### PROGRAMMATIC MANAGEMENT DOCUMENTS

#### Planning Utilities (CLI Tools Overview)
- **File:** `controlm-planning-utils.md`
- **Type:** Utility Reference, Programmatic
- **Size:** 10 KB | **Scope:** 13 command-line management tools
- **Tools:** defjob, copydefjob, deldefjob, exportdefjob, duplicatedefjob, loopdetecttool, updatedef, ctmdeffolder, ctmdefsubfolder, defcal, copydefcal, exportdefcal, import/exportsitestandards
- **Status:** Complete

#### ctmdefine Utility (Job Definition API)
- **File:** `controlm-ctmdefine-utility.md`
- **Type:** Utility Reference, Programmatic
- **Size:** 11 KB | **Scope:** Programmatic job creation with 30+ parameters
- **Parameters:** Task types, scheduling, calendar, dependencies, variables, actions, notifications, system
- **Input Method:** Command-line or input file
- **Status:** Complete

#### ctmdeffolder Utility (SMART Folder Creation)
- **File:** `controlm-ctmdeffolder-utility.md`
- **Type:** Utility Reference, Programmatic
- **Size:** 9 KB | **Scope:** SMART folder definition with parameter inheritance
- **Parameters:** Scheduling, calendars, execution control, variables, conditions
- **Sub-folder Integration:** Sub-folders inherit RBC from parent automatically
- **Status:** Complete

---

### OPERATIONAL & REFERENCE DOCUMENTS

#### Changes History (Version Management)
- **File:** `controlm-changes-history.md`
- **Type:** Operational, Version Control
- **Size:** 8 KB | **Scope:** Automatic versioning and change tracking
- **Features:** Workspace-based restoration (non-destructive), 180-day retention (indefinite for current), JSON comparison
- **Search:** Date range, name pattern, version number, change type
- **Status:** Complete

#### Planning Quick Reference (Fast Lookup)
- **File:** `controlm-planning-quick-reference.md`
- **Type:** Reference, Quick Guide
- **Size:** 3 KB | **Scope:** Planning overview and Q&A
- **Content:** Planning concepts, feature overview, quick lookup guide
- **Status:** Complete

---

### ARCHIVED REFERENCE

#### Original 1. Control-M Planning
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Control-M_Planning.htm
- **Saved As:** `controlm-planning-specifications.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Comprehensive guide to planning functions
- **Key Topics:**
  - Overview and core concept
  - Jobs as execution units
  - Folder organization (SMART, Regular, Sub-folders)
  - Planning domain functions
  - Integration capabilities
  - Development workspaces

### 2. Creating a Folder
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Creating_a_Folder.htm
- **Saved As:** `controlm-folder-creation.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Detailed folder configuration guide
- **Key Topics:**
  - Folder types (Regular, SMART)
  - Core folder properties and constraints
  - Configuration options (tabs)
  - Additional parameters
  - Naming constraints
  - Rename operations

### 3. Creating a Sub-folder
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Creating_a_Sub-folder.htm
- **Saved As:** `controlm-subfolder-creation.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Hierarchical organization and sub-folder configuration
- **Key Topics:**
  - Sub-folder definition and nesting requirements
  - Hierarchy constraints (SMART folder only, max 9 levels)
  - Sub-folder properties and naming rules
  - Inheritance mechanism (scheduling, prerequisites, actions)
  - Reference sub-folders (advanced feature)
  - Creation procedure and configuration tabs

### 4. Events
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Events.htm
- **Saved As:** `controlm-events.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Event-based job dependency and workflow orchestration
- **Key Topics:**
  - Event definition as prerequisite type
  - Standard vs. global event types
  - Event processing and triggering mechanism
  - Event attributes and properties
  - Wait-for-event inheritance
  - Event management and dynamic properties
  - Integration with scheduling and prerequisites

### 5. Variables
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Variables.htm
- **Saved As:** `controlm-variables.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Variable definition, scope, substitution, and parameterization
- **Key Topics:**
  - Variable types (User-defined, System, List)
  - Variable scope and inheritance (Local, Folder, Global, Pool)
  - Variable substitution and resolution
  - System variables reference
  - Variable naming constraints (1-38 chars, alphanumeric only)
  - Variable functions (CALCDATE, GETENV, SUBSTR, WCALC, BLANK)
  - Variable integration with jobs, folders, events, actions
  - Variable priority and override mechanisms

### 6. Calendars
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Calendars.htm
- **Saved As:** `controlm-calendars.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Calendar definitions, scheduling integration, and date rule reference
- **Key Topics:**
  - Calendar types (Regular, Periodic, Rule-Based)
  - Calendar rules and date definitions
  - Scheduling and working day integration
  - Rule-Based Calendar (RBC) with 4 rule types
  - Confirmation filtering and exception policies
  - Shift By parameter (-62 to +62 days)
  - Activity periods and Keep-Active parameters
  - Calendar scope and server synchronization
  - Integration with scheduling, prerequisites, variables (WCALC)

### 7. Pattern-Matching Strings
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Pattern-Matching_Strings.htm
- **Saved As:** `controlm-pattern-matching.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Pattern matching syntax, wildcards, and string comparison reference
- **Key Topics:**
  - Pattern matching definition and wildcards (*, ?, ., !, +, {n})
  - Grouping and escape character (\ \)
  - String comparison operators and MATCHES logic
  - Multiple pattern OR logic (comma-separated)
  - Special character escaping and constraints
  - Usage in if-actions, prerequisites, variable conditions
  - Performance best practices (blank fields vs *)
  - Pattern examples and naming integration

### 8. File Watcher Job
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/File_Watcher_Job.htm
- **Saved As:** `controlm-file-watcher.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** File watcher job type definition and monitoring reference
- **Key Topics:**
  - File watcher job definition and purpose (event-driven triggering)
  - Detection modes (Create, Delete)
  - File path and wildcard pattern handling
  - Watch conditions (time limit, search interval, file size, age)
  - File monitoring parameters and detection workflow
  - Execution requirements and user authorization
  - File path variable (%%FileWatch-FILE_PATH)
  - Integration with jobs, folders, events, variables
  - Best practices and common scenarios

### 9. OS Job Parameters
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/OS_Job_parameters.htm
- **Saved As:** `controlm-os-job-parameters.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** OS job type execution, command/script parameters, and integration reference
- **Key Topics:**
  - OS job types (Script, Command, Embedded Script)
  - Execution types and supported languages (Perl, Python, PowerShell, VBScript)
  - Run As user and authorization requirements
  - File path and file name constraints
  - Command execution (512 char limit, case sensitivity by platform)
  - Embedded script limits (64,000 bytes, interpreter shebang)
  - **CRITICAL: Folder-level variables NOT available to scripts (job-level only)**
  - Variable integration and resolution in job execution
  - Integration with scheduling, variables, file watcher, events
  - Error handling and best practices

### 10. File Transfer Job
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/File_Transfer_Job.htm
- **Saved As:** `controlm-file-transfer-job.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** File transfer job type, protocols, and distributed file management reference
- **Key Topics:**
  - File transfer job definition (up to 5 sequential definitions per job)
  - Transfer modes (local, agentless, cloud, AS2, SharePoint)
  - Protocols (FTP, SFTP, cloud APIs)
  - Seven transfer operations (standard, watch, sync, listing, incremental, concurrent)
  - File selection (wildcards, regex patterns)
  - Transfer conditions and triggers (pre/post-commands, watching, destination renaming)
  - Error handling (resume from failure, retries, duplicate handling)
  - Transfer variables ($$WATCH_*, $$AFTFILE_*)
  - Cloud platform integration (S3, Azure, GCP, Oracle)

### 11. Infrastructure as Code Jobs
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Jobs_for_Infrastructure_as_Code.htm
- **Saved As:** `controlm-infrastructure-as-code.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Infrastructure as Code job types and cloud platform orchestration reference
- **Key Topics:**
  - IaC job definition and purpose (cloud infrastructure orchestration)
  - Five platforms (Ansible AWX, CloudFormation, Azure, GCP, Terraform)
  - Code deployment models (template-based, API requests, YAML configs)
  - Cloud platform integration (role-based execution, credentials)
  - Version control and GitOps (Ansible AWX, Terraform VCS)
  - Templating and parameterization (JSON/YAML)
  - Error handling (failure tolerance, rollback, retries)
  - Monitoring and status polling (configurable frequency)
  - Integration with Control-M scheduling and variables

### 12. Job Scheduling
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Job_scheduling.htm
- **Saved As:** `controlm-job-scheduling.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Job scheduling types, frequency patterns, and temporal execution control reference
- **Key Topics:**
  - Scheduling definition and hierarchical levels (SMART folder → Sub-folder → Job)
  - Six scheduling types (Every Day, None, Specific Dates, Use Parent, Advanced, Free Space)
  - Run frequency and patterns (interval-based, sequence-based, specific times)
  - Date and time-based scheduling (From/To windows, time zones, tolerance)
  - Calendar integration and confirmation calendars
  - Advanced scheduling patterns (weekdays, month days, combinations)
  - **Eight exception policies** for confirmation calendar mismatches
  - Shift By parameter (−62 to +62 days)
  - Constraint and limits (max reruns, keep active)
  - **Critical: Two-plane execution (Scheduling + Prerequisites)**
  - Inheritance mechanisms and override patterns
  - Retroactive runs, activity periods, SAC, cyclic execution

### 13. Job Actions
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Job_actions.htm
- **Saved As:** `controlm-job-actions.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Job actions, conditional execution, automation triggers, and workflow control reference
- **Key Topics:**
  - Six action categories (Events, Pre-Notifications, If-Actions, Post-Notifications, Capture, Output Handling)
  - If-action conditions (status, exit codes, output patterns, variable values, counts)
  - Eight if-action responses (Notify, Set OK/Not OK, Rerun, Stop Cyclic, Set Variable, Run Ignoring Schedule, Handle Output, Add/Delete Event)
  - Notification destinations (Alerts Window, Email, Remedy, Console, z/OS options)
  - Pre-actions and post-actions lifecycle integration
  - Variable capture and setting from job execution
  - Dynamic event generation based on conditions
  - Output handling operations (copy, move, delete, print)
  - Conditional branching and status-driven responses
  - Integration with variables, events, scheduling, prerequisites

### 14. Changes History
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Changes_History.htm
- **Saved As:** `controlm-changes-history.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Version management, change tracking, and recovery reference
- **Key Topics:**
  - Automatic versioning (every creation/modification)
  - Retention policy (180 days standard, indefinite for current versions)
  - Search and retrieval capabilities
  - Version comparison (JSON side-by-side diff)
  - Workspace-based change restoration
  - Change tracking for jobs and SMART folders
  - Deletion recovery within 180-day window
  - Integration with job/folder management

### 15. Planning Utilities
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Planning_Utils.htm
- **Saved As:** `controlm-planning-utils.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Command-line utilities and programmatic management overview
- **Key Topics:**
  - Job management tools (defjob, copydefjob, deldefjob, exportdefjob, duplicatedefjob, loopdetecttool)
  - Folder management tools (deffolder, exportdeffolder, ctmdeffolder, ctmdefsubfolder)
  - Calendar management tools (defcal, copydefcal, exportdefcal)
  - Definition update utilities (updatedef)
  - Site standards tools (exportsitestandards, importsitestandards)
  - Programmatic access patterns
  - Integration with Control-M architecture

### 16. ctmdefine Utility - Technical Reference
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Utilities/ctmdefine.htm
- **Saved As:** `controlm-ctmdefine-utility.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Detailed ctmdefine API reference with 30+ parameters
- **Key Topics:**
  - Command syntax and invocation
  - Five task types (JOB, EXTERNAL, DETACHED, COMMAND, DUMMY)
  - 30+ parameter documentation
  - Scheduling parameters (cyclic, date-based, calendar-integrated)
  - Advanced parameters (dependencies, variables, actions, notifications)
  - Application-specific job configuration
  - Input file method for batch definitions
  - Parameter syntax rules and constraints
  - Integration with Control-M components

### 17. ctmdeffolder Utility - Technical Reference
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Utilities/ctmdeffolder.htm
- **Saved As:** `controlm-ctmdeffolder-utility.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Detailed ctmdeffolder API reference for SMART folder creation
- **Key Topics:**
  - SMART folder creation and parameters
  - Cyclic execution configuration
  - Calendar integration (RBC, day calendars, week calendars)
  - Execution control (priority, run-as user, timezone, maxwait)
  - Variable specification and syntax rules
  - Sub-folder inheritance of RBC
  - Input file method
  - Integration with ctmdefsubfolder and ctmdefine

### 18. Folder API - Code Reference
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/API_CodeRef_Folder.htm
- **Saved As:** `controlm-api-folder-reference.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** REST API specification for folder object structure and JSON integration
- **Key Topics:**
  - Folder API overview and JSON-based requests
  - Core properties (Type, When, ControlmServer, RunAs, OrderMethod)
  - Additional properties (Application, SubApplication, Priority, TimeZone, Variables)
  - Configuration inheritance model
  - JSON structure patterns and examples
  - Nested folder structures (Folders, Jobs, Resources, Notifications, Events)
  - Special character handling (colon escaping with `\\:`)
  - Array-based definitions for bulk operations
  - Integration patterns (SMART folders, hierarchies, variables)
  - API integration considerations and best practices
  - Limitations and constraints

### 19. Planning Quick Reference
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/Planning_Quick_Reference.htm
- **Saved As:** `controlm-planning-quick-reference.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** Quick lookup guide for planning concepts
- **Key Topics:**
  - Planning feature overview
  - Architecture style summary
  - Q&A section for planning agents
  - Fast reference for common planning questions

### 20. Job Properties API - Code Reference
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/API_CodeRef_JobProperties.htm
- **Saved As:** `controlm-api-job-properties.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** REST API specification for job object structure and properties
- **Key Topics:**
  - Core job structure (Type, RunAs, Name, Application, SubApplication)
  - Type field system (Job:Command, Job:Script, Job:Dummy, Job:External, Job:FileWatcher)
  - Scheduling properties (When object with date/time constraints)
  - Calendar integration (regular, rule-based, confirmation calendars)
  - Event management (WaitForEvents, AddEvents, DeleteEvents)
  - Conditional actions (If statements with 8+ action types)
  - Notification properties (pre/post execution, duration-based)
  - Cyclic execution (simple rerun, complex intervals, specific times)
  - Resource management (pools and locks)
  - Variable system (job, folder, and pool scoping)
  - Priority and execution control
  - Documentation properties
  - JSON structure patterns and examples
  - Character escaping (colon handling)
  - Constraints and limitations

### 21. Connection Profiles - Code Reference
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/API_CodeRef_ConnectionProfiles_Container.htm
- **Saved As:** `controlm-api-connection-profiles.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** REST API specification for container orchestration connection profiles
- **Key Topics:**
  - Five container platforms (AWS ECS, AWS App Runner, Azure Container Instances, GCP Cloud Run, Kubernetes)
  - Connection profile architecture (centralized vs. local storage)
  - AWS ECS authentication (Secret, IAM Role, Assume Role)
  - AWS App Runner authentication (Secret, IAM Role, Assume Role)
  - Azure Container Instances authentication (Service Principal, Managed Identity)
  - GCP Cloud Run authentication (Service Account, IAM User)
  - Kubernetes authentication (Service Token, Remote Spec Endpoints)
  - Remote spec endpoint authentication options (BasicAuth, OAuth2, AWS IAM, Google Service Account)
  - Secret protection ("Secrets in Code" pattern)
  - Connection timeout configuration per platform
  - Multi-region and multi-account support
  - Integration with container jobs
  - Best practices for credential management

### 22. Job Types - Code Reference
- **URL:** https://documents.bmc.com/supportu/controlm-saas/en-US/Documentation/API_CodeRef_JobTypes_commandScript.htm
- **Saved As:** `controlm-api-job-types.md`
- **Date Scraped:** 2026-06-11
- **Content Type:** REST API specification for command and script job type execution
- **Key Topics:**
  - Four job types (Job:Command, Job:Script, Job:EmbeddedScript, Job:DetachedEmbeddedScript)
  - Core execution properties (Host, RunAs, PreCommand, PostCommand)
  - Command execution with inline syntax
  - Script file execution with FilePath and FileName
  - Platform-specific path formatting (Windows double backslash, UNIX forward slash)
  - Interpreter identification via file extension
  - Embedded script inline execution (1-64 KB limit)
  - Detached background script execution
  - Script argument passing as array of strings
  - Environment variables and working directory configuration
  - Pre/post command sequencing
  - Error handling and exit code interpretation
  - Platform-specific considerations (Windows, UNIX/Linux)
  - Performance and security best practices

---

## Content Overlap Analysis

### Nine-Way Overlap: Concepts Appearing in Multiple Documents

| Concept | Doc 1 (Planning) | Doc 2 (Folder) | Doc 3 (Sub-folder) | Doc 4 (Events) | Doc 5 (Variables) | Doc 6 (Calendars) | Doc 7 (Pattern-Match) | Doc 8 (FileWatcher) | Doc 9 (OSJobParams) | Notes |
|---------|-----------------|-----------------|-------------------|-----------------|------------------|-------------------|----------------------|-------------------|-------------------|-------|
| **Job Types** | ✓ (Overview) | (Container) | (Container) | ✗ | ✗ | ✗ | ✗ | ✓ (File Watcher) | ✓✓ (OS job types) | Planning overview; FileWatcher & OSJobParams are specific types |
| **Variables** | ✓ (Mention) | ✓ (1-40) | ✓ (Override) | ✓ (Names) | ✓✓ (Complete) | ✓ (WCALC) | (Conditions) | ✓ (%%FileWatch-FILE_PATH) | ✓✓ (CRITICAL: Folder vars NOT available!) | CRITICAL: OS Job doc reveals folder variables unavailable to scripts |
| **Job Execution** | ✓ (Overview) | ✓ (Params) | ✓ (Inherited) | ✓ (Sequencing) | ✓ (Substitution) | ✓ (Scheduling) | (Filtering) | ✓ (Run As) | ✓✓ (Command/Script execution) | Multiple job execution types detailed in OS Job doc |
| **Folder Hierarchy** | ✓ (Concept) | ✓ (SMART) | ✓✓ (Detailed) | ✓ (Scope) | ✓ (Scope) | ✓ (Scope) | ✗ | ✓ (Container) | ✓ (Job container) | All job types contained in folder hierarchy |
| **User Authorization** | ✗ | (Implied) | (Implied) | ✗ | ✗ | ✗ | ✗ | ✓ (Run As user) | ✓ (Run As user, 1-30 chars) | Execution permission model in File Watcher & OS Job docs |
| **Events & Triggering** | ✓ (Overview) | (Implied) | (Implied) | ✓✓ (Primary) | ✓ (Actions) | ✗ | ✗ | ✓ (Event source) | (Triggered by events) | Multiple triggering mechanisms across docs |
| **Naming Constraints** | ✗ | ✓ (Folder) | ✓ (Sub-folder) | ✓ (Event) | ✓ (Variable) | ✓ (Calendar) | ✓ (Pattern) | (File paths) | ✓ (File/Command constraints) | Each component specifies naming/constraint rules |
| **Prerequisites System** | ✓ (Overview) | ✓ (Structure) | ✓ (Inheritance) | ✓ (Events) | ✗ | ✓ (Calendar) | (Conditions) | ✓ (File detection) | (Can have prerequisites) | Multiple prerequisite mechanisms |
| **System Integration** | ✓ (Broad) | ✗ | ✗ | ✗ | ✓ (Jobs/actions) | ✓ (Variables/Scheduling) | ✓ (Filtering) | ✓ (File system) | ✓ (OS integration) | OS Job doc reveals integration points with OS platforms |
| **Configuration Tabs** | ✓ (4 areas) | ✓ (4 tabs) | ✓ (4 tabs) | ✗ | ✗ | ✗ | ✗ | (Job-specific) | (Job-specific) | Standard structure applies to all job types |

### Non-Overlapping Content

**Document 1 (Planning Only):**
- Jobs as execution units (detailed)
- Integration with external systems (AWS, Snowflake, Hadoop)
- Workspaces and check-in workflow
- SLA Manager and forecasting
- Templates and statistics
- Workload policies

**Document 2 (Folder Creation Only):**
- Run method options (Automatic, Manual, User Daily)
- Server assignment details
- Application/Sub-application categorization

**Document 3 (Sub-folder Creation Only):**
- Maximum nesting depth (1-9 levels)
- Reference sub-folders (advanced pattern)
- Sub-folder vs. Regular folder comparison matrix
- Hierarchical organization best practices

**Document 4 (Events Only):**
- Event types (Standard vs. Global)
- Event processing and triggering mechanism
- Event attributes and properties (wait-for-event vs. event perspective)
- Event management capabilities
- Drag-and-drop event creation interface
- Wait-for-event inheritance rules
- Boolean logic (AND/OR) for multiple events
- Event workflow examples (sequential, parallel, convergence)

**Document 5 (Variables Only):**
- Three variable types (User-defined, System, List)
- Four scope levels (Local, Folder, Global, Pool)
- Variable substitution and resolution mechanism
- Complete system variables reference
- Variable naming constraints (1-38 chars, alphanumeric)
- Variable value constraints (up to 214 chars)
- Variable functions (CALCDATE, GETENV, SUBSTR, WCALC, BLANK)
- Variable simulation feature (preview without execution)
- Administrator control (ORDER_SYSTEM_VARIABLES_VALIDATION)
- Variable priority and override mechanisms
- Performance considerations for variable resolution

**Document 6 (Calendars Only):**
- Three calendar types (Regular, Periodic, Rule-Based)
- Four RBC rule types (Specific Dates, Weekdays, Month Days, Advanced)
- Regular and Periodic Calendar recurring patterns
- Rule-Based Calendar confirmation filtering with exception policies
- Shift By parameter (-62 to +62 days) for automatic date adjustment
- Activity periods (blackout/suspension mechanism)
- Keep-Active parameter (SMART folder level)
- Calendar naming constraints (platform-dependent, z/OS: 8 uppercase max)
- Server synchronization scope (single or multi-server)
- Working day calculation integration with Variables (WCALC function)
- Two-plane execution model (Calendar plane + Prerequisite plane)
- Calendar design and maintenance best practices

**Document 7 (Pattern-Matching Only):**
- Pattern matching wildcards (*, ?, ., !, +, {n})
- Quantifier operators (one or more, exact count, range)
- Grouping and grouping scope with parentheses
- Escape character (\\) for special character literals
- Special characters requiring escape (parentheses, brackets, braces, operators, etc.)
- Pattern matching in search and filter operations
- IF MATCHES operator for conditional logic
- Multiple pattern OR logic with comma separator
- Performance constraints (blank fields vs. *)
- Best practices for pattern design and testing
- Integration with If-Actions, Prerequisites, Variables, Job filtering
- Case sensitivity and platform-specific behavior

**Document 8 (File Watcher Job Only):**
- File Watcher job type definition and purpose
- Event-driven triggering based on file system changes
- Detection modes (Create for file arrival, Delete for completion)
- File path variable (%%FileWatch-FILE_PATH) for downstream jobs
- Wildcard pattern handling for file names (* and ?)
- Watch conditions (time limit, search interval, file size, iterations, age)
- File size monitoring parameters (stability checks, minimum size)
- File age constraints (minimum and maximum age since modification)
- Execution requirements (Run As user with file system permissions)
- Detection workflow and trigger mechanism
- Integration with folder hierarchy and events
- File watcher as event source for downstream jobs
- Common scenarios (batch arrival, real-time monitoring, completion detection)
- Performance tuning (search interval, pattern specificity, CPU load)
- Limitations and platform-specific behavior

**Document 9 (OS Job Parameters Only):**
- OS job types (Script, Command, Embedded Script)
- Script execution from file path (1-255 chars) and file name (1-64 chars)
- Command execution (up to 512 characters, case sensitivity by platform)
- Embedded script support (up to 64,000 bytes, requires "#!" interpreter line)
- Supported embedded languages (Perl, Python, PowerShell, VBScript)
- Run As user configuration (1-30 characters, case-sensitive, no spaces)
- File path and file name constraints (no spaces, limited special characters)
- **CRITICAL CONSTRAINT: Folder-level variables NOT available to job scripts**
- Job-level variable requirement and workaround for script access
- Variable resolution mechanism in commands and scripts
- System variables availability (%%JOBNAME, %%DATE, etc.)
- File Watcher variable integration (%%FileWatch-FILE_PATH)
- Platform-specific differences (UNIX vs. Windows case sensitivity)
- Interpreter specification for embedded scripts (shebang syntax)
- Error handling and exit codes
- Best practices for script design, command execution, embedded scripts
- Integration with OS platforms (Windows, Unix/Linux)

---

## Cross-Reference Guide

Use this guide to navigate between related topics across documents:

### If You're Reading About...

**Jobs & Execution**
- → See: Planning doc (controlm-planning-specifications.md)
- → Context: Folder Creation doc for folder context
- → Hierarchy: Sub-folder doc for organizational context
- → Sequencing: Events doc for job dependencies

**Folder Organization**
- → Start: Planning doc (folder hierarchy section)
- → Details: Folder Creation doc (folder types and properties)
- → Deep Dive: Sub-folder doc (hierarchical organization, nesting)
- → Event Scope: Events doc (events across folder levels)

**SMART Folders**
- → Concept: Planning doc (core components, why SMART folders)
- → Implementation: Folder Creation doc (SMART folder features, inheritance)
- → Usage: Sub-folder doc (SMART as required parent, inheritance chain)
- → Event Scope: Events doc (SMART folders can generate/receive events)

**Sub-folder Hierarchy**
- → Overview: Planning doc (sub-folders mentioned in hierarchy)
- → Basics: Folder Creation doc (sub-folder creation mentioned)
- → Complete: Sub-folder doc (all hierarchy details, nesting constraints, reference sub-folders)
- → Event Integration: Events doc (events work across folder levels)

**Prerequisites & Actions**
- → Overview: Planning doc (planning definition areas)
- → Configuration: Folder Creation doc (prerequisites tab, actions tab)
- → Inheritance: Sub-folder doc (inherited prerequisites/actions + overrides)
- → Events Component: Events doc (events as one of three prerequisite types)

**Scheduling**
- → Concept: Planning doc (scheduling criteria)
- → Implementation: Folder Creation doc (scheduling tab, SMART scheduling)
- → Inheritance: Sub-folder doc (scheduling inheritance from parent)
- → With Events: Events doc (scheduling works alongside events; they're separate)

**Job Sequencing & Dependencies**
- → Mechanism: Events doc (primary dependency control)
- → Visual Interface: Events doc (drag-and-drop event creation)
- → Boolean Logic: Events doc (AND/OR operators for multiple events)
- → Inheritance Pattern: Events doc (wait-for-event inheritance on job deletion)

**Integration**
- → See: Planning doc (integration capabilities)
- → Note: Other docs do not cover external system integrations

**Workspaces & Development**
- → See: Planning doc (working environment section)
- → Note: Other docs assume workspace exists

**Variables & Parameters**
- → Planning level: Planning doc (variables overview)
- → Folder level: Folder Creation doc (1-40 char limit for folder variables)
- → Reference level: Sub-folder doc (variable override in reference sub-folders)
- → Event level: Events doc (system variables %%VAR_NAME and timestamps @HHMMSS in events)
- → Complete: Variables doc (all scopes, types, functions, substitution mechanism)

**Variable Scope & Inheritance**
- → See ONLY: Variables doc (Local, Folder, Global, Pool scopes)
- → Integration: Folder doc (folder-level variables) + Sub-folder doc (inheritance) + Variables doc (complete mechanism)

**Variable Functions & Substitution**
- → See ONLY: Variables doc (CALCDATE, GETENV, SUBSTR, WCALC, BLANK functions)
- → Use: For dynamic calculations and parameterized values

**System Variables**
- → See ONLY: Variables doc (complete system variables reference)
- → Categories: Job general, Job scheduling, Environment, Action

**Variable Simulation**
- → See ONLY: Variables doc (preview resolved values without execution)
- → Use: Validate variable expressions and substitution before deployment

**Variable Override & Priority**
- → See ONLY: Variables doc (priority order and ORDER_SYSTEM_VARIABLES_VALIDATION)
- → Use: Understand which variable wins when multiple exist at different scopes

**Nesting & Hierarchy Constraints**
- → Concept: Planning doc (mentions hierarchy)
- → Rules: Folder Creation doc (sub-folder basics)
- → Constraints: Sub-folder doc (SMART only, max 9 levels, no sub-sub-folders)
- → Event Scope: Events doc (events work across all folder levels)

**Reference Sub-folders** (Advanced Pattern)
- → See ONLY: Sub-folder doc (reference sub-folders section)
- → Use: For reusable job sequences and variable parameterization
- → Event Integration: Events can be associated with reference sub-folders

**Working Day Calculations**
- → Function: Variables doc (%%$WCALC function definition)
- → Calendar Context: Calendars doc (WCALC uses calendar for working day determination)
- → Integration: Variables doc shows function; Calendars doc shows how calendars enable it

**Calendar Types & Rules**
- → See ONLY: Calendars doc (Regular, Periodic, RBC types and 4 RBC rule types)
- → Advanced: Calendars doc (confirmation filtering, exception policies, shift by)

**Scheduling with Calendars**
- → Calendar Types: Calendars doc (3 types for different patterns)
- → Scheduling Criteria: Folder/Sub-folder docs (tab structure) + Calendars doc (calendar-based criteria)
- → Integration: Calendars doc (two-plane execution: calendar window + prerequisites)

**Date Adjustment & Shifting**
- → Shift By Parameter: Calendars doc (-62 to +62 days automatic adjustment)
- → Use: Handle holidays, manage run sequences without modifying definitions

**Activity Periods & Blackouts**
- → See ONLY: Calendars doc (Activity Period mechanism, Keep-Active parameter)
- → Use: Temporary suspension of jobs for maintenance windows

**Naming Conventions**
- → Basic: Folder Creation doc (1-64 chars, case-sensitive, special chars)
- → Stricter Rules: Sub-folder doc (additional restrictions for sub-folders)
- → Events: Events doc (1–255 chars, no apostrophes/parentheses in event names)
- → Calendars: Calendars doc (platform-dependent; z/OS: 8 uppercase max)
- → Pattern Matching: Pattern-Matching doc (wildcards and escaping for special chars)

**Pattern Matching & Filtering**
- → See ONLY: Pattern-Matching doc (wildcards: *, ?, ., !, +, {n})
- → Wildcards: *, ?, ., !, +, {n}, ( ), \ for grouping and escaping
- → Usage: Search filters, job filtering, condition evaluation

**IF MATCHES Conditions**
- → See ONLY: Pattern-Matching doc (IF MATCHES operator with patterns)
- → Integration: Used with Variables doc (pattern match variable values)
- → Use: Conditional if-action logic based on string patterns

**String Filtering**
- → Pattern-Matching doc (comprehensive filtering examples)
- → Negation: Use ! to exclude matching strings
- → OR Logic: Comma-separated patterns (host1,host2,host3)
- → Performance: Blank fields more efficient than *

**Escape Sequences**
- → See ONLY: Pattern-Matching doc (\ \ escape character)
- → Special Chars: Parentheses, brackets, braces, operators all need escaping
- → Example: \\(job\\) matches literal "(job)"

**File Watcher Jobs**
- → See ONLY: File Watcher Job doc (complete job type specification)
- → Triggering: Event-driven based on file system changes
- → File Path Variable: %%FileWatch-FILE_PATH available to triggered jobs

**Event-Driven Triggering**
- → Events doc: Job-to-job sequencing via events
- → File Watcher doc: File detection as event source
- → Together: Two complementary triggering mechanisms (events between jobs, files from system)

**File Path Patterns**
- → Pattern-Matching doc: Wildcard syntax (* and ?)
- → File Watcher doc: File paths using wildcard patterns
- → OS Job doc: File paths in script/command execution
- → Together: Pattern system enables flexible file name matching

**Variables in Triggered Jobs**
- → Variables doc: Variable scoping and substitution
- → File Watcher doc: %%FileWatch-FILE_PATH variable
- → OS Job doc: **CRITICAL - Folder variables NOT available to scripts (job-level only)**
- → Use: Define variables at job level for script/command access

**Job Execution Types**
- → See ONLY: OS Job Parameters doc (Script, Command, Embedded Script)
- → Languages: Perl, Python, PowerShell, VBScript
- → Execution: Varies by platform and language

**OS Job Variable Integration**
- → Variables doc: Complete variable system overview
- → Folder doc: Folder-level variables (1-40 chars)
- → OS Job doc: **Folder variables NOT available to scripts - define at job level**
- → Critical: Scripts must have job-level variables, not folder-level
- → File Watcher: %%FileWatch-FILE_PATH works in OS job scripts

**Command Execution Limits**
- → See ONLY: OS Job Parameters doc
- → Command length: 512 characters max
- → File path: 1-255 characters max (case-sensitive)
- → File name: 1-64 characters max (case-sensitive)

**Embedded Script Support**
- → Languages: Perl, Python, PowerShell, VBScript
- → Size limit: 64,000 bytes
- → Interpreter: "#!" prefix on first line required
- → See: OS Job Parameters doc for syntax examples

**Cross-Server Operations**
- → Events: Events doc (global events for multi-server dependencies)
- → Calendars: Calendars doc (calendar synchronization scope)
- → OS Jobs: Platform-specific execution (Windows vs. Unix/Linux)
- → Note: Different mechanisms; Events sequence jobs, Calendars define scheduling rules

---

## Document Comparison Matrix

| Aspect | Planning | Folder | Sub-folder | Events | Variables | Calendars | Pattern-Match | FileWatcher | OSJobParams | Recommendation |
|--------|----------|--------|-----------|--------|-----------|-----------|---------------|-------------|------------|----------------|
| **Overall Architecture** | ✓✓ | (Foundation) | (Hierarchy) | (Workflow) | (Parameterization) | (Scheduling) | (Filtering) | (File trigger) | (Execution) | Start with Planning |
| **Covers Job Types** | ✓ (Overview) | (Container) | (Container) | ✗ | ✗ | ✗ | ✗ | ✓ (File Watcher) | ✓✓ (OS types) | Planning + Job type docs |
| **Covers Job Execution** | ✓ (Overview) | ✓ (Params) | ✓ (Inherited) | ✓ (Sequencing) | ✓ (Substitution) | ✓ (Scheduling) | (Filtering) | ✓ (Run As) | ✓✓ (Complete) | Use OS Job doc for details |
| **Covers Variables** | (Mention) | ✓ (Limit) | ✓ (Override) | ✓ (Dynamic) | ✓✓ (Complete) | ✓ (WCALC) | (Conditions) | ✓ (%%FileWatch-FILE_PATH) | ✓ (**CRITICAL: Folder vars NOT available!**) | **OS Job doc reveals constraint** |
| **Covers Variable Scope** | ✗ | ✗ | ✗ | ✗ | ✓✓ (4 scopes) | ✗ | ✗ | ✗ | ✓ (Job vs. Folder) | Variables + OS Job docs |
| **Covers Script/Command** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | (In commands) | ✗ | ✓✓ (Complete) | Only in OS Job doc |
| **Covers Embedded Script** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ (Languages, size) | Only in OS Job doc |
| **Covers File Operations** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | (File patterns) | ✓✓ (File monitoring) | ✓ (File paths) | FileWatcher + OS Job docs |
| **Covers Event Triggering** | ✓ (Concept) | (Implied) | (Implied) | ✓✓ (Job events) | ✓ (In actions) | ✗ | ✗ | ✓ (File events) | (Can be triggered) | Events + FileWatcher |
| **Covers Prerequisites** | ✓ (Overview) | ✓ (Details) | ✓ (Inheritance) | ✓✓ (Complete) | ✗ | ✓ (Calendar) | (Conditions) | ✓ (File detection) | (Can have) | Events doc |
| **Covers User Authorization** | ✗ | (Implied) | (Implied) | ✗ | ✗ | ✗ | ✗ | ✓ (Run As) | ✓ (Run As user) | FileWatcher + OS Job docs |
| **Covers Platform Differences** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ (Case sensitivity) | (Path constraints) | ✓✓ (UNIX vs. Windows) | OS Job + Pattern-Matching docs |
| **Covers Constraint Critical** | ✗ | ✓ (Folder vars) | (Implied) | ✗ | (Overview) | ✗ | ✗ | ✗ | ✓✓ (**Folder vars NOT available!**) | **OS Job doc clarifies** |
| **Covers Integration** | ✓✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | Only in Planning |
| **Covers Scheduling** | ✓ (Overview) | ✓ (Details) | ✓ (Inheritance) | ✓ (Separate) | ✓ (With vars) | ✓✓ (Calendar) | (Conditions) | (Optional) | (Can have) | Calendar doc |

---

## Content Summary by Topic

### SMART Folders

**Planning Doc Says:**
- Include extended definition parameters
- Parameters apply collectively to contained jobs
- Enable standardized configuration

**Folder Creation Doc Says:**
- Default folder type
- Define scheduling criteria at folder level
- Inherited by jobs and sub-folders
- Support prerequisites and actions

**Sub-folder Doc Says:**
- Required parent for sub-folders
- Only way to enable inheritance chain
- Enables hierarchical organization

**How to Use Together:**
1. Planning doc explains WHY (standardization, collective parameters)
2. Folder doc explains HOW (inheritance model, configuration tabs)
3. Sub-folder doc explains WHERE (as parent in hierarchy)

### Regular Folders

**Planning Doc Says:**
- Process jobs independently
- Each job has individual parameters
- No inherited parameter propagation

**Folder Creation Doc Says:**
- Collect and group jobs together
- Scheduled definitions are NOT inherited
- Jobs process independently

**Sub-folder Doc Says:**
- Not applicable for sub-folders
- Sub-folders must be within SMART folders only

**How to Use Together:**
1. Planning doc shows use cases (independent execution)
2. Folder doc clarifies constraints (no scheduling inheritance)
3. Sub-folder doc clarifies restriction (SMART only)

### Folder Hierarchy

**Planning Doc Says:**
- Three folder types: SMART, Regular, Sub-folders
- Sub-folders inherit parameters from parent SMART folders

**Folder Creation Doc Says:**
- Sub-folder creation mentioned briefly
- Rename operations require all jobs fully loaded
- Manual updates needed for cross-references

**Sub-folder Doc Says:**
- Sub-folders can ONLY be within SMART folders
- Maximum nesting depth: 1-9 levels
- Inheritance chain: SMART Folder → Sub-folder → Jobs
- Cannot create sub-folders within sub-folders (max 2-tier)
- Reference sub-folders for advanced reuse patterns

**How to Use Together:**
1. Planning doc provides architecture overview
2. Folder doc provides basic operational info
3. Sub-folder doc provides detailed constraints and patterns

### Inheritance Mechanism

**Planning Doc Says:**
- Parameters inherit from parent folders to children

**Folder Creation Doc Says:**
- SMART folders propagate to child jobs
- General, Scheduling, Prerequisites, Actions all inherited

**Sub-folder Doc Says:**
- Scheduling attributes inherited
- Prerequisites capabilities inherited
- Action definitions inherited
- Child can override inherited attributes
- Reference sub-folders enable selective inheritance with variable override

**Events Doc Says:**
- Wait-for-event inheritance preserves workflow when jobs deleted
- Automatically transfers event dependencies under specific conditions
- Requires identical Boolean operators (AND or OR) across all events

**How to Use Together:**
1. Planning doc introduces concept
2. Folder doc shows structure
3. Sub-folder doc explains detailed mechanism and override capability
4. Events doc explains wait-for-event inheritance (special case)

### Prerequisites System

**Planning Doc Says:**
- Prerequisites are one of the planning definition areas
- Work alongside scheduling and other configurations

**Folder Creation Doc Says:**
- Prerequisites are a configuration tab
- Configure at folder level for inheritance

**Sub-folder Doc Says:**
- Prerequisites inherited from parent SMART folder
- Can be overridden at sub-folder level
- Contribute to job execution decision

**Events Doc Says:**
- Events are one of THREE prerequisite types (alongside scheduling and resources)
- Wait-for-event is successor's view of event prerequisites
- All three types must be satisfied for execution

**How to Use Together:**
1. Planning doc introduces prerequisites concept
2. Folder/Sub-folder docs show configuration structure
3. Events doc explains events as prerequisite type
4. Together: Prerequisites = Scheduling + Resources + Events

### Job Execution Control

**Planning Doc Says:**
- Jobs execute based on folder and job parameters
- Scheduling, prerequisites, and actions control workflow

**Folder Creation Doc Says:**
- Folder parameters inherited by jobs
- Jobs configure their own parameters
- Run method and run-as user control execution

**Sub-folder Doc Says:**
- Inheritance chain determines execution parameters
- Jobs inherit from sub-folder and SMART folder
- Overrides possible at job level

**Events Doc Says:**
- Events are PRIMARY mechanism for job sequencing
- Drag-and-drop interface creates visual workflow
- Separate from scheduling (both must be satisfied)

**Variables Doc Says:**
- Jobs execute with resolved variable values
- Variables substitute in command lines, file paths, conditions
- Multiple scopes enable appropriate data sharing
- Resolution happens at execution time

**How to Use Together:**
1. Planning doc shows overall control mechanisms
2. Folder docs show parameter inheritance
3. Events doc shows job sequencing via events
4. Variables doc shows parameterization via substitution
5. Together: Jobs execute when params OK + scheduling OK + events delivered + variables resolved

### Variable Scope & Inheritance

**Planning Doc Says:**
- Mentions variables at folder/job level

**Folder Creation Doc Says:**
- Folder variables (1-40 chars)
- Inherited by contained jobs

**Sub-folder Doc Says:**
- Inherits folder-level variables
- Can override with sub-folder/job variables
- Reference sub-folders support variable override

**Events Doc Says:**
- Event names can use variables (%%JOBNAME-TO-%%NEXTJOB)
- Variables resolved at event delivery time

**Variables Doc Says:**
- Four scope levels: Local (%%VAR), Folder (%%VAR in SMART), Global (%%\VAR), Pool (%%\\POOL)
- Local overrides Folder, Folder overrides Global
- SMART folder variables inherited by jobs and sub-folders
- Variable simulation allows preview before execution

**How to Use Together:**
1. Folder doc shows folder-level variable basics
2. Sub-folder doc shows variable inheritance in hierarchy
3. Variables doc explains all four scopes and resolution priority
4. Together: Scopes enable parameterization at appropriate levels

### Parameterization & Dynamic Values

**Planning Doc Says:**
- Parameters control job behavior

**Folder Creation Doc Says:**
- Folder-level parameters inherited by jobs

**Sub-folder Doc Says:**
- Inheritance chain passes parameters down

**Events Doc Says:**
- Dynamic event names via variables (%%JOBNAME-TO-%%NEXT)
- Timestamps in event names (@HHMMSS)

**Variables Doc Says:**
- User-defined, System, and List variables
- Variable functions: CALCDATE, GETENV, SUBSTR, WCALC, BLANK
- Used in: command lines, file names, conditions, actions
- Resolved at execution time (one-time, not recurring)

**Calendars Doc Says:**
- Calendar-based scheduling parameters
- Shift By parameter (-62 to +62 days)
- Variables used in scheduling criteria via WCALC

**How to Use Together:**
1. Folder/Sub-folder docs show parameter inheritance patterns
2. Events doc shows variables in dynamic naming
3. Variables doc provides complete parameterization toolkit
4. Calendars doc provides scheduling rule parameterization
5. Together: Four-layer parameterization (inherited params + event naming + variable substitution + calendar-based rules)

### Scheduling System

**Planning Doc Says:**
- Scheduling criteria determine job execution timing

**Folder Creation Doc Says:**
- Scheduling tab for folder-level scheduling
- Can inherit or override

**Sub-folder Doc Says:**
- Scheduling inherited from parent SMART folder
- Can override at sub-folder or job level

**Events Doc Says:**
- Scheduling separate from event prerequisites
- Both must be satisfied for execution

**Variables Doc Says:**
- Variables can be used in scheduling criteria
- WCALC function calculates working days

**Calendars Doc Says:**
- Three calendar types (Regular, Periodic, RBC)
- Calendars define execution date windows
- Two-plane execution: Calendar window + Prerequisites
- Integration with Variables (WCALC for working days)

**How to Use Together:**
1. Folder/Sub-folder docs show scheduling structure
2. Events doc shows scheduling separate from prerequisites
3. Variables doc shows parameterization of scheduling
4. Calendars doc provides scheduling rule engine and date math
5. Together: Complete scheduling system with temporal control, parameterization, and rule application

### Conditional Logic and Filtering

**Variables Doc Says:**
- Variables used in if-action conditions
- Variable value comparison and substitution

**Pattern-Matching Doc Says:**
- IF MATCHES operator for conditional logic
- Wildcards and patterns for string matching
- Used in if-actions and conditions

**Calendars Doc Says:**
- RBC uses Boolean logic (Advanced rules)
- Exception policies based on conditions

**Events Doc Says:**
- Boolean logic (AND/OR) for multiple events
- Prerequisite conditions

**How to Use Together:**
1. Variables doc explains variable substitution and conditions
2. Pattern-Matching doc provides wildcard syntax for conditions
3. IF MATCHES (Pattern-Matching) evaluates variable values (Variables)
4. Events doc shows prerequisite logic (AND/OR)
5. Calendars doc shows RBC condition combinations
6. Together: Multi-level conditional logic (variables + pattern matching + Boolean operators)

### String Naming and Filtering

**Folder Creation Doc Says:**
- Folder naming constraints (1-64 chars, special chars)
- Job name formats

**Variables Doc Says:**
- Variable naming (1-38 chars, alphanumeric only)

**Events Doc Says:**
- Event naming (1-255 chars, no apostrophes/parentheses)

**Calendars Doc Says:**
- Calendar naming (platform-dependent, z/OS: 8 uppercase max)

**Pattern-Matching Doc Says:**
- Pattern matching for filtering by name
- Wildcards and escape sequences for special characters
- Used in job/folder/calendar search and filtering

**How to Use Together:**
1. Folder/Variable/Event/Calendar docs specify naming constraints
2. Pattern-Matching doc shows how to filter using wildcards
3. Special character escaping (Pattern-Matching) needed for names with special chars
4. Together: Naming constraints define valid names; Pattern-Matching enables flexible filtering

### Event-Driven Job Triggering

**Planning Doc Says:**
- Jobs triggered through prerequisites

**Events Doc Says:**
- Events as job-to-job dependencies
- Boolean AND/OR logic for multiple events
- Wait-for-event mechanism

**File Watcher Doc Says:**
- File detection generates events
- File Watcher as event source
- Triggers downstream jobs when conditions met

**Variables Doc Says:**
- Variables in event names
- Event names can be dynamic (%%JOBNAME-TO-%%NEXT)

**How to Use Together:**
1. Events doc explains job-to-job sequencing via events
2. File Watcher doc shows file detection as alternative trigger
3. Variables doc shows dynamic naming
4. Together: Multiple triggering mechanisms (job completion, file detection, variables)

### Integration of File System Monitoring

**Folder Creation Doc Says:**
- Folders contain jobs

**File Watcher Doc Says:**
- File Watcher is a job type
- Contained in folders like other jobs
- Generates events triggering downstream jobs

**Variables Doc Says:**
- %%FileWatch-FILE_PATH variable passes detected file path
- Variable substitution in downstream jobs

**Pattern-Matching Doc Says:**
- Wildcard patterns (* and ?) for file name matching
- Used in File Watcher path specifications

**Events Doc Says:**
- File Watcher generates events
- Events trigger dependent jobs

**OS Job Parameters Doc Says:**
- OS jobs can receive %%FileWatch-FILE_PATH from File Watcher
- Scripts/commands execute with resolved variables
- Job-level variables required for script access

**How to Use Together:**
1. Folder doc provides container structure
2. File Watcher doc defines file detection mechanism
3. Pattern-Matching enables flexible file path patterns
4. Variables doc provides %%FileWatch-FILE_PATH for downstream jobs
5. Events doc shows how detection triggers dependent jobs
6. OS Job doc receives file path and executes script/command with it
7. Together: Complete file-driven workflow system

### CRITICAL: Variable Scope in Job Execution

**Folder Creation Doc Says:**
- Folders define folder-level variables (1-40 chars)
- Variables inherited by jobs

**Variables Doc Says:**
- Variables have four scopes (Local, Folder, Global, Pool)
- Folder-level variables available to jobs
- Variable inheritance in folder hierarchy

**OS Job Parameters Doc Says:**
- **CRITICAL: "Variables defined at the folder level don't transfer to jobs—you must define variables at the job level for scripts and embedded scripts"**
- Job-level variables ARE available to scripts
- System variables (%%JOBNAME, %%DATE, etc.) ARE available

**Implication:**
Despite Folder and Variables docs suggesting folder-level variables transfer to jobs, OS Job Parameters doc reveals this is NOT true for script access. Scripts must have job-level variable definitions.

**How to Use Together:**
1. Variables doc explains the general scoping model
2. Folder doc shows folder-level variable definition
3. OS Job doc reveals the CRITICAL constraint: folder vars NOT available in scripts
4. **Action Required:** Define variables at job level for script/command access, not at folder level

---

## Additional Pages to Scrape (Recommendations)

Based on cross-references and gaps in current documentation, consider scraping:

### Critical Priority (Foundational)
1. **Job Creation/Definition** — Referenced across all 7 docs; foundational execution unit (jobs not yet detailed)
2. **Prerequisites & Conditions** — Complete three-part prerequisite system (scheduling, resources, events)

### High Priority (Core Workflow)
3. **Actions & Post-Processing** — Referenced in multiple docs as configuration tab; how actions trigger and use variables/events/calendars
4. **Scheduling Details** — Covered in tabs but deeper implementation needed; coordination with calendars and variables
5. ~~**Variables & Substitution**~~ — ✓ COMPLETED (controlm-variables.md covers all scopes, types, functions)
6. ~~**Calendars**~~ — ✓ COMPLETED (controlm-calendars.md covers types, rules, integration)

### High Priority (Job Execution)
7. **Prerequisites & Conditions Detailed** — Resource requirements (third prerequisite type alongside events and scheduling)
8. **Wait-for-Event Conditions** — Deep dive into event prerequisite logic and Boolean combinations
9. **Lock Resources** — Mentioned in Sub-folder/Calendar docs; resource management in execution

### Medium Priority (Advanced Features)
10. **Set Variable Actions** — How actions create/modify variables (mentioned in Variables doc)
11. **Templates** — Referenced in Planning doc; reusable job/folder patterns using variables and calendars
12. **Reference Patterns** — Sub-folder reference sub-folders; deeper integration with variables and calendars
13. **IF-Actions Conditions** — How if-action conditions evaluate variable expressions and calendar/event states

### Medium Priority (Planning Features)
14. **SLA Manager** — Mentioned in Planning doc; monitoring job execution against SLAs
15. **Workspaces & Check-in** — Mentioned in Planning doc; development/deployment workflow
16. **Periodic Statistics & Rules** — Referenced in Planning doc; forecast rules for runtime

### Lower Priority (Integration & Operations)
17. **Error Handling & Recovery** — Not yet referenced; job failure handling patterns
18. **Monitoring & Reporting** — Beyond SLA Manager; dashboards and reporting
19. **Integration Details** — AWS, Snowflake, Hadoop specifics (referenced in Planning doc)
20. **Advanced Calendar Patterns** — Deeper cross-calendar coordination and complex RBC rules

### Suggested Order (Optimized for Learning Path)
1. Job Creation/Definition (foundational for everything)
2. Prerequisites & Conditions (complete system: Scheduling + Resources + Events)
3. Actions & Post-Processing (automation logic and integration with all components)
4. Wait-for-Event Conditions (advanced event prerequisite logic)
5. Lock Resources (resource management in execution)
6. Set Variable Actions (dynamic variable creation via actions)
7. IF-Actions Conditions (conditional automation logic)
8. Templates (reuse patterns with variables and calendars)

---

## Usage for Planning Agents

1. **Start with Planning doc** for architectural understanding
2. **Reference Folder doc** when implementing folder configuration
3. **Check overlap analysis** to understand different coverage levels
4. **Use cross-reference guide** to navigate between docs
5. **Note unique topics** to identify where additional pages needed
6. **Track gaps** for follow-up documentation requests

---

## Manifest Maintenance

**Version:** 2.0  
**Status:** Complete Foundation Documentation + Active for new sources  
**Document Count:** 13 main + 2 companion = 15 total (Planning, Folder, Sub-folder, Events, Variables, Calendars, Pattern-Matching, FileWatcher, OSJobParams, FileTransfer, IaC, JobScheduling, JobActions)  
**Total Lines:** 5,500+ lines of documentation  
**Total Size:** ~245K  
**Overlap Detection:** Manual review + automated detection for duplicate concepts  
**Update Frequency:** After each new document scraped  
**Coverage Focus:** Job execution, workflow orchestration, hierarchy, prerequisites, events, parameterization, scheduling, filtering, conditions, file-driven triggers, OS job execution, file transfer, infrastructure automation, temporal control, workflow automation
**CRITICAL FINDINGS:** 
  - Folder-level variables NOT available in job scripts (must use job-level)
  - Two-plane execution model (Scheduling plane + Prerequisite plane)
  - If-Actions enable complex conditional workflow branching
  - Dynamic event generation enables status-driven sequencing

---

## 📊 JOB TYPE COVERAGE ANALYSIS

**Control-M Supports 150+ Job Types** across these categories:

| Category | Count | Documented | Status |
|----------|-------|-----------|--------|
| **Data Integration** | 18+ | 0 | ⏳ Not Covered (Airbyte, AWS AppFlow, Azure Data Factory, Informatica, Talend, etc.) |
| **Data Processing** | 16+ | 0 | ⏳ Not Covered (BigQuery, Snowflake, Databricks, Spark, EMR, Redshift, etc.) |
| **Cloud Computing** | 14+ | 0 | ⏳ Not Covered (Lambda, Functions, Batch, SageMaker, etc.) |
| **Container & Orchestration** | 5 | ✅ 5 | Complete (ECS, App Runner, ACI, Cloud Run, Kubernetes) |
| **Application Workflows** | 6+ | 0 | ⏳ Not Covered (Airflow, Step Functions, Logic Apps, Composer, etc.) |
| **Infrastructure as Code** | 5 | ✅ 5 | Complete (Ansible, CloudFormation, Azure, GCP, Terraform) |
| **CI/CD** | 5+ | 0 | ⏳ Not Covered (Jenkins, GitHub Actions, GitLab, etc.) |
| **Messaging & Pub/Sub** | 5+ | 0 | ⏳ Not Covered (SNS, SQS, Kafka, Service Bus, RabbitMQ) |
| **Machine Learning** | 5+ | 0 | ⏳ Not Covered (Bedrock, Vertex AI, Azure ML, etc.) |
| **Backup & Recovery** | 6+ | 0 | ⏳ Not Covered (AWS Backup, Veeam, Rubrik, etc.) |
| **BI & Analytics** | 4+ | 0 | ⏳ Not Covered (QuickSight, Power BI, Tableau) |
| **RPA** | 2 | 0 | ⏳ Not Covered (UiPath, Automation Anywhere) |
| **ERP** | 6+ | 0 | ⏳ Not Covered (SAP, Oracle Fusion) |
| **OS & General** | 6 | ✅ 4 | Mostly Complete (OS, File Transfer, File Watcher, REST/SOAP) |
| **Utility Jobs** | 2 | ✅ 1 | Partial (Dummy documented, SLA undocumented) |

**Current Coverage: ~10 of 150+ job types (7% complete)**

---

## 📝 DOCUMENTATION COMPLETION PRIORITIES

**Phase 1 (Current - Foundational):** ✅ COMPLETE
- Core architecture, scheduling, variables, events, calendars
- 5 container platforms, 5 IaC platforms, OS jobs
- Foundation for all advanced job types

**Phase 2 (Recommended - High-Value):** ⏳ TODO
- Data Integration (most enterprise jobs use these)
- Data Processing (critical for analytics)
- Cloud Computing (serverless execution)
- CI/CD (DevOps integration)
- Application Workflows (orchestration frameworks)

**Phase 3 (Advanced):** ⏳ TODO
- Messaging & Pub/Sub (event-driven architectures)
- Machine Learning (AI/ML workflows)
- RPA (robotic process automation)
- ERP (SAP, Oracle integration)

---

When adding new documents:
1. Update "Scraped Documents" section (with URL, save location, date, key topics)
2. Re-analyze content overlaps (identify multi-way overlaps with existing docs)
3. Update cross-reference guide (add navigational paths to new content)
4. Update document comparison matrix (add new doc column and evaluate coverage)
5. Update content summary by topic (add new doc perspective)
6. **FLAG CRITICAL CONSTRAINTS:** Note when new docs reveal constraints contradicting earlier docs
7. Update this manifest with version bump and document count

**Change Log:**
- v1.0 (2026-06-11): Initial manifest with 2 documents (Planning, Folder)
- v1.1 (2026-06-11): Added Sub-folder Creation
- v1.2 (2026-06-11): Added Events document
- v1.3 (2026-06-11): Added Variables document
- v1.4 (2026-06-11): Added Calendars document
- v1.5 (2026-06-11): Added Pattern-Matching document
- v1.6 (2026-06-11): Added File Watcher Job document
- v1.7 (2026-06-11): Added OS Job Parameters; **CRITICAL: folder variables NOT in scripts**
- v1.8 (2026-06-11): Added File Transfer Job & IaC Jobs (11 documents)
- v1.9 (2026-06-11): Added Job Scheduling (12 documents); **Two-plane execution model**
- v2.0 (2026-06-11): Added Job Actions (13 documents); **FOUNDATION DOCUMENTATION COMPLETE**
