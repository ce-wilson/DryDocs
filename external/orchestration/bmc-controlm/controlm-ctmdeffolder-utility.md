# Control-M ctmdeffolder Utility - Technical Reference

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Utilities/ctmdeffolder.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** ctmdeffolder command syntax, parameters, and folder definition API reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** "creates definitions for new SMART folders" purpose; SMART-only scope; sub-folders without RBC inherit all parent RBC; cyclic types (INTERVAL, INTERVAL_SEQUENCE, SPECIFIC_TIMES); documented parameters (-FOLDER, -APPLICATION/-SUBAPPLICATION, cyclic/calendar/execution-control, -VARIABLE apostrophe-for-`$` rule, -INCOND/-OUTCOND/-CONTROL); input_file method; the single source example (`-FOLDER job -SUBAPPLICATION supply …`).
- **SYNTHESIZED:** Additional multi-pattern examples, Best Practices, Vendor Attributes table.

---

## ctmdeffolder Definition and Purpose

The ctmdeffolder utility "creates definitions for new SMART folders in Control-M."

**Key Concept:** "SMART folders are used for jobs whose processing can be treated as a single unit."

**Scope:** Generate SMART folder configuration with parameters managing entire job collection

---

## Folder Type Support

### SMART Folders Only

**Supported Structures:**
- Empty SMART folders
- SMART folders containing jobs
- SMART folders with sub-folders (via ctmdefsubfolder)

**Sub-folder Inheritance:**
- Sub-folders without Rule-Based calendars inherit all RBC from parent definitions
- Enables hierarchical parameter propagation

---

## Core Command Syntax

### Basic Invocation

```
ctmdeffolder -FOLDER <name> [various parameters]
```

### Input File Method

```
ctmdeffolder -input_file <pathname>
```

---

## Parameter Reference

### Folder Identification

| Parameter | Purpose | Format |
|-----------|---------|--------|
| **-FOLDER** | SMART folder name | String (1-64 chars) |
| **-APPLICATION** | Application name | Logical grouping |
| **-SUBAPPLICATION** | Sub-application | Hierarchical organization |

### Scheduling Configuration

#### Cyclic Execution

| Parameter | Purpose | Values |
|-----------|---------|--------|
| **-CYCLIC** | Enable cyclic execution | Y\|N |
| **-CYCLIC_TYPE** | Cycle type | INTERVAL\|INTERVAL_SEQUENCE\|SPECIFIC_TIMES |
| **-INTERVAL** | Time interval | days/hours/minutes format |
| **-SPECIFIC_TIMES** | Execution times | HHMM format (comma-separated) |
| **-TOLERANCE** | Maximum delay allowed | Minutes (numeric) |

#### Date and Day Specification

| Parameter | Purpose | Format |
|-----------|---------|--------|
| **-DAYS** | Days to execute | ALL or numeric (1-31) |
| **-WEEKDAYS** | Days of week | MON,TUE,WED,THU,FRI,SAT,SUN |
| **-MONTH** | Months | ALL or specific months |

### Calendar Integration

| Parameter | Purpose | Details |
|-----------|---------|---------|
| **-RBC** | Rule-Based Calendar | Calendar name |
| **-DAYSCAL** | Day calendar | Regular calendar reference |
| **-WEEKCAL** | Week calendar | Regular calendar reference |

### Execution Control

| Parameter | Purpose | Details |
|-----------|---------|---------|
| **-PRIORITY** | Job priority level | Numeric or named level |
| **-RUN_AS** | Execution username | User account (1-30 chars) |
| **-MAXWAIT** | Maximum wait duration | Time specification |
| **-TIMEZONE** | Timezone specification | TZ format |

### Variables and Conditions

| Parameter | Purpose | Syntax |
|-----------|---------|--------|
| **-VARIABLE** | Define variables | Local, Global, or Pool |
| **-INCOND** | Input conditions | Event/prerequisite reference |
| **-OUTCOND** | Output conditions | Event definition |
| **-CONTROL** | Named controls | E (Even) or S (Set) states |

---

## Variable Specification Rules

### Important Syntax Rules

**Variable Enclosure:**
- Variables **without "$"**: Can use apostrophes or quotes
- Variables **containing "$"**: Must use apostrophes ONLY
  - ✅ Correct: `-VARIABLE 'VAR$NAME=value'`
  - ❌ Wrong: `-VARIABLE "VAR$NAME=value"` (prevents resolution)

**Implication:** Use apostrophes for safety when variables contain special characters

---

## Practical Example

### Example: SMART Folder Creation

```
ctmdeffolder -FOLDER job \
  -SUBAPPLICATION supply \
  -APPLICATION supplies \
  -RBC jobRbc \
  -DAYS ALL \
  -MONTH ALL Y
```

**Creates:**
- SMART folder named "job"
- Application: supplies
- Sub-application: supply
- Calendar: jobRbc (Rule-Based Calendar)
- Execution: All days, all months
- Cyclic execution: Enabled (Y)

---

## Advanced Parameter Patterns

### Pattern 1: Cyclic Folder with Specific Times

```
ctmdeffolder -FOLDER hourly_batch \
  -APPLICATION batch \
  -CYCLIC Y \
  -CYCLIC_TYPE SPECIFIC_TIMES \
  -SPECIFIC_TIMES 02:00,06:00,10:00,14:00,18:00,22:00
```

### Pattern 2: Calendar-Based SMART Folder

```
ctmdeffolder -FOLDER monthly_process \
  -APPLICATION finance \
  -RBC month_end_calendar \
  -DAYSCAL company_calendar \
  -PRIORITY HIGH \
  -RUN_AS batch_user
```

### Pattern 3: SMART Folder with Conditions

```
ctmdeffolder -FOLDER conditional_batch \
  -APPLICATION processing \
  -CYCLIC N \
  -INCOND APPROVAL_RECEIVED \
  -OUTCOND BATCH_COMPLETE \
  -VARIABLE 'BATCH_DATE=20260611'
```

### Pattern 4: Multi-Timezone Folder

```
ctmdeffolder -FOLDER global_daily \
  -APPLICATION global \
  -DAYS ALL \
  -WEEKDAYS MON,TUE,WED,THU,FRI \
  -TIMEZONE America/New_York \
  -RUN_AS global_ops
```

---

## Integration with Control-M Components

### Scheduling Integration

ctmdeffolder SMART folders support:
- Calendar-based scheduling (via -RBC)
- Cyclic execution patterns
- Time windows and tolerances
- Multi-timezone coordination

### Hierarchical Integration

- Creates parent SMART folder for job organization
- Sub-folders created via ctmdefsubfolder inherit RBC
- Parameter inheritance chain: SMART Folder → Sub-folder → Jobs

### Event Integration

- Input conditions (-INCOND) trigger folder execution
- Output conditions (-OUTCOND) generate folder completion events
- Event-based sequencing of dependent folders

### Variable Integration

- Folder-level variables defined via -VARIABLE
- Available to jobs within folder
- ⚠️ **Remember:** Folder variables NOT available to job scripts (job-level required)

---

## Parameter Best Practices

### Syntax Considerations

1. **Variable Safety**
   - Always use apostrophes for variables with "$"
   - Prevents shell interpretation issues
   - Ensures proper variable resolution

2. **Timezone Handling**
   - Specify timezone for global operations
   - Ensures consistent execution across regions
   - Overrides server default timezone

3. **Calendar Integration**
   - Use Rule-Based Calendars for complex patterns
   - Reference day/week calendars for validation
   - Enable sub-folder inheritance of RBC

4. **Execution Control**
   - Set appropriate PRIORITY for resource management
   - Specify RUN_AS for proper authorization
   - Define MAXWAIT for timeout protection

---

## Folder Type Context

### SMART Folder vs Regular Folder

**ctmdeffolder creates SMART folders:**
- Parameters inherited by child jobs/sub-folders
- Suitable for related job groups
- Enables parameter propagation
- Scheduling at folder level

**Regular folders require deffolder utility:**
- Independent job execution
- No parameter inheritance
- Each job configured independently
- Separate scheduling per job

---

## Integration with Other Utilities

### Workflow with ctmdefsubfolder

```
ctmdeffolder
  ↓ (creates SMART folder)
ctmdefsubfolder
  ↓ (creates sub-folders)
ctmdefine
  ↓ (creates jobs)
Complete hierarchy
```

### Workflow with ctmdefine

```
ctmdeffolder (create SMART folder structure)
  ↓
ctmdefine -FOLDER folder_name (add jobs to SMART folder)
  ↓
Jobs inherit SMART folder parameters
```

---

## Notes for Planning Agents

1. **SMART Folder Creation:** ctmdeffolder creates SMART folders only (not regular folders)
2. **Hierarchy Support:** Works with sub-folders (ctmdefsubfolder) and jobs (ctmdefine)
3. **Parameter Inheritance:** Parameters propagate to child jobs and sub-folders
4. **Calendar Integration:** Full RBC support with day/week calendar references
5. **Cyclic Scheduling:** Supports INTERVAL, INTERVAL_SEQUENCE, SPECIFIC_TIMES patterns
6. **Variable Handling:** Folder-level variables with special character safety rules
7. **Execution Control:** Priority, run-as user, timezone, timeout configuration
8. **Event Integration:** Input/output conditions for event-based sequencing
9. **Timezone Support:** Multi-timezone coordination for global operations
10. **Inheritance Chain:** Sub-folders inherit RBC from SMART parent automatically

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Utility** | ctmdeffolder |
| **Purpose** | Create SMART folder definitions |
| **Folder Type** | SMART folders only |
| **Sub-folder Support** | Via ctmdefsubfolder |
| **Scheduling** | Cyclic, calendar-based, time-based |
| **Calendar Types** | RBC, day calendar, week calendar |
| **Execution Control** | Priority, run-as user, timezone, maxwait |
| **Variables** | Local, Global, Pool (apostrophe syntax for $) |
| **Conditions** | Input/output events, named controls |
| **Inheritance** | Automatic to sub-folders and jobs |
| **Cyclic Types** | INTERVAL, INTERVAL_SEQUENCE, SPECIFIC_TIMES |
