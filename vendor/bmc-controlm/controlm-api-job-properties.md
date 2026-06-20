# Control-M Job Properties API - Code Reference

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** API_CodeRef_JobProperties.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Job object structure, JSON properties, and API integration reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## ⚠️ FORMAT MISMATCH & SYNTHESIZED-JSON WARNING — READ FIRST

This page documents the **Control-M Automation API (JSON)** — a **SaaS** interface. The target environment (**9.0.21.300**) defines jobs in **XML**, **not JSON**. Use this file as a **conceptual reference only** — *which properties, constraints, and behaviors exist* where they may add detail applicable to our XML definitions. **Do not treat the JSON as our format, and do not convert to JSON.**

The JSON *structure* below was Claude-synthesized. The canonical Automation API uses the object **name as the JSON key** (e.g. `"MyJob": { "Type": "Job:Command", ... }`) in PascalCase — **not** a top-level `"Name"` property as shown here. Property *names* are mostly grounded; exact JSON shapes/nesting are **illustrative only**, unverified against live source.

---

## 📑 Provenance Classification

Produced by WebFetch of one BMC page + Claude restructuring. Tiers: **[VERBATIM]** = BMC quotes · **[GROUNDED]** = Claude paraphrase of sourced content · **[SYNTHESIZED]** = Claude-authored, not in source (do NOT load as vendor ground truth).

- **GROUNDED (source was content-rich here):** Type/RunAs requirement; When fields (WeekDays e.g. "DMONW2", Months, MonthDays, FromTime/ToTime, Schedule, SpecificDates ≤400); calendar refs; WaitForEvents + AND/OR; AddEvents/DeleteEvents date types; If condition types (CompletionStatus, NumberOfReruns/Failures/Executions, Output wildcards, VariableValue operators); action type names (Mail, Rerun, Run, Set/SetToOK/SetToNotOK, StopCyclicRun, Notify, Event:Add/Delete, Output, CaptureOutput); Notify types; Rerun / RerunIntervals / RerunSpecificTimes / RerunLimit; Resource:Pool/Lock; Priority, DaysKeepActive, Critical, TimeZone, etc.; variable escaping; constraints (255 / 4000 chars, 400 dates).
- **SYNTHESIZED:** Every assembled JSON example body and its exact key nesting/casing; the Job-type "Type field" example block; all Pattern/Best-Practice prose; Vendor Attributes table.

⚠️ **Hazard:** Property *names* are grounded, but the **full JSON object shapes / nesting shown are Claude's reconstruction** — treat exact structure as illustrative, verify against live API before code generation.

---

## Job API Overview

The Job Properties API enables programmatic definition and configuration of Control-M jobs using JSON structures.

**Key Concept:** Jobs are defined with a Type field that determines available properties, followed by job-specific configuration for scheduling, events, actions, and execution control.

---

## Core Job Structure

### Required Properties

| Property | Purpose | Details |
|----------|---------|---------|
| **Type** | Job classification | Determines available properties (e.g., "Job:Command", "Job:Script") |
| **RunAs** | Execution user | OS user account for job execution |

### Identification Properties

| Property | Purpose | Format |
|----------|---------|--------|
| **Name** | Job identifier | String (escapes colons with `\\:` in arrays) |
| **Application** | Logical grouping | Application name (descriptive, no timing) |
| **SubApplication** | Categorization | Sub-application name |

---

## Job Type System

### Type Field Values

```json
{
  "Type": "Job:Command",     // Command-line execution
  // OR
  "Type": "Job:Script",       // Script file execution
  // OR
  "Type": "Job:Dummy",        // Placeholder job
  // OR
  "Type": "Job:External",     // External reference
  // OR
  "Type": "Job:FileWatcher"   // File detection job
}
```

**Implication:** Type field determines which additional properties are available and how job is executed.

---

## Scheduling Properties (When Object)

### Date and Time Constraints

| Property | Purpose | Format | Examples |
|----------|---------|--------|----------|
| **WeekDays** | Day/week specification | Code format | "DMONW2" = Monday in week 2 |
| **Months** | Calendar months | Month abbreviation | "JAN", "FEB", or "ALL" |
| **MonthDays** | Days of month | Numeric or "ALL" | 1-31 or "ALL" |
| **FromTime** | Start time window | HHMM format | "0800" = 8:00 AM |
| **ToTime** | End time window | HHMM format | "1700" = 5:00 PM |
| **Schedule** | Execution frequency | Predefined values | "Everyday" or "Never" |
| **SpecificDates** | Explicit dates | MM/DD format | Up to 400 entries |

### Advanced Scheduling

#### Calendar Integration

```json
{
  "When": {
    "MonthDaysCalendar": "calendar_name",
    "WeekDaysCalendar": "calendar_name"
  }
}
```

#### Rule-Based Calendars

```json
{
  "When": {
    "RuleBasedCalendar": {
      "Name": "calendar_name",
      "Included": ["rule1", "rule2"],
      "Excluded": ["exception1"]
    }
  }
}
```

#### Confirmation Calendars

```json
{
  "When": {
    "ConfirmationCalendar": {
      "Name": "calendar_name",
      "ExceptionPolicy": "Shift",
      "ShiftBy": 3
    }
  }
}
```

### Date Range Periods

```json
{
  "When": {
    "StartDate": "2026-01-01",
    "EndDate": "2026-12-31",
    "ActivePeriod": true
  }
}
```

---

## Event Management

### Wait for Events (Prerequisites)

**Purpose:** Pause job execution until specified events occur

```json
{
  "WaitForEvents": [
    {
      "Name": "event_name",
      "Date": "OrderDate",
      "Relationship": "AND"
    }
  ]
}
```

**Relationship Options:**
- AND: All events must occur
- OR: Any event can trigger

**Date Options:**
- OrderDate: Same execution date
- PreviousOrderDate: Previous day
- NextOrderDate: Next day
- Specific MMDD: Month/day specification

**Boolean Logic:** Support for parenthetical grouping and complex expressions

### Add/Delete Events (Post-Execution Actions)

```json
{
  "AddEvents": [
    {
      "Name": "job_complete_event",
      "DateType": "OrderDate"
    }
  ],
  "DeleteEvents": [
    {
      "Name": "waiting_event"
    }
  ]
}
```

**Date Type Options:**
- AnyDate
- OrderDate
- PreviousOrderDate
- NextOrderDate
- MMDD (month/day format)

---

## Conditional Actions (If Statements)

### Condition Types

#### Job Completion Status

```json
{
  "Condition": {
    "CompletionStatus": "NotOK"
    // OR "OK", "ANY", specific values
    // OR ">= value", "<= value", "< value", "> value", "!= value"
    // OR "Even", "Odd"
  }
}
```

#### Rerun/Failure Tracking

```json
{
  "Condition": {
    "NumberOfReruns": ">= 3"
  },
  // OR
  "Condition": {
    "NumberOfFailures": "<= 5"
  }
}
```

#### Execution Frequency

```json
{
  "Condition": {
    "NumberOfExecutions": "2"
  }
}
```

#### Absence Conditions

```json
{
  "Condition": {
    "JobNotSubmitted": "By 1400"  // By time in HHMM
  },
  // OR
  "Condition": {
    "JobOutputNotFound": true
  }
}
```

#### Output Pattern Matching

```json
{
  "Condition": {
    "Output": {
      "Pattern": "ERROR*",  // Wildcards: * (multiple), $ or ? (single)
      "SearchOption": "StartsWith"
    }
  }
}
```

#### Variable Value Conditions

```json
{
  "Condition": {
    "VariableValue": {
      "Variable": "STATUS",
      "Operator": "EqualTo",
      "Value": "SUCCESS"
    }
  }
}
```

**Operators:** EqualTo, StartsWith, Contains, IsEmpty, GreaterThan, LessThan

### Available Actions

#### Mail Notification

```json
{
  "Action:Mail": {
    "To": "admin@company.com",
    "Subject": "Job Failure Alert",
    "CC": "ops@company.com",
    "Urgency": "VeryUrgent"
  }
}
```

**Urgency Levels:** Regular, Urgent, VeryUrgent

#### Job Rerun

```json
{
  "Action:Rerun": {}
}
```

#### Execute Another Job

```json
{
  "Action:Run": {
    "JobName": "cleanup_job",
    "Variables": {
      "STATUS": "FAILED"
    },
    "DateOverride": "NextOrderDate"
  }
}
```

#### Status Modification

```json
{
  "Action:Set": {
    "Variable": "JOB_STATUS",
    "Value": "COMPLETED"
  },
  // OR
  "Action:SetToOK": {},
  // OR
  "Action:SetToNotOK": {}
}
```

#### Stop Cyclic Execution

```json
{
  "Action:StopCyclicRun": {}
}
```

#### Event Manipulation

```json
{
  "Event:Add": {
    "Name": "job_recovered_event"
  },
  // OR
  "Event:Delete": {
    "Name": "failure_event"
  }
}
```

#### Output Handling

```json
{
  "Action:Output": {
    "Operation": "Copy",  // Copy, Move, Delete, Print
    "Destination": "/archive/logs"
  }
}
```

#### Capture Output to Variable

```json
{
  "Action:CaptureOutput": {
    "Variable": "CAPTURED_TEXT",
    "LineOffset": 1,      // Start from line 1
    "ColumnOffset": 0     // Start from column 0
  }
}
```

---

## Notification Properties

### Notification Types

#### Success Notification

```json
{
  "Notify:OK": {
    "Message": "Job completed successfully",
    "Destination": "Alerts"
  }
}
```

#### Failure Notification

```json
{
  "Notify:NotOK": {
    "Message": "Job failed",
    "Destination": "JobLog"
  }
}
```

#### Job Not Started

```json
{
  "Notify:DoesNotStart": {
    "By": "0900",  // HHMM format
    "Message": "Job did not start by 9:00 AM"
  }
}
```

#### Execution Time Notification

```json
{
  "Notify:ExecutionTime": {
    "LongerThan": 600,  // Minutes
    "Message": "Job running longer than expected"
  }
}
```

**Comparison Options:**
- LessThan
- GreaterThan
- LessThanAverage
- GreaterThanAverage

#### Job Not Completed

```json
{
  "Notify:DoesNotEnd": {
    "By": "1700",
    "Message": "Job did not complete by 5:00 PM"
  }
}
```

#### Rerun Notification

```json
{
  "Notify:ReRun": {
    "Message": "Job is being rerun"
  }
}
```

### Common Notification Parameters

| Parameter | Purpose | Values |
|-----------|---------|--------|
| **Message** | Notification text | String (notification content) |
| **Destination** | Where to send | Alerts, JobLog, Console, custom |
| **Urgency** | Priority level | Regular, Urgent, VeryUrgent |

---

## Cyclic Execution Properties

### Simple Rerun

```json
{
  "Rerun": {
    "Every": 30,
    "Units": "Minutes",  // Minutes, Hours, Days
    "From": "Start",     // Start, End, or Target
    "Times": 5           // Number of repetitions
  }
}
```

### Complex Rerun Intervals

```json
{
  "RerunIntervals": {
    "Months": 1,
    "Days": 2,
    "Hours": 3,
    "Minutes": 30,
    "From": "End",
    "Times": 10
  }
}
```

### Rerun at Specific Times

```json
{
  "RerunSpecificTimes": {
    "Times": ["0800", "1200", "1600", "2000"],
    "Tolerance": 15  // Minutes
  }
}
```

### Non-Cyclic Reruns

```json
{
  "RerunLimit": {
    "Times": 3,
    "Interval": 10  // Minutes between retries
  }
}
```

---

## Resource Management

### Resource Pool (Quantitative)

```json
{
  "Resource:Pool": {
    "Name": "database_connections",
    "Quantity": 5  // Max concurrent jobs
  }
}
```

**Purpose:** Limit concurrent access to shared resources

### Resource Lock (Exclusive/Shared)

```json
{
  "Resource:Lock": {
    "Name": "file_lock",
    "Type": "Exclusive"  // Exclusive or Shared
  }
}
```

**Purpose:** Prevent simultaneous execution or allow shared access

---

## Variable System

### Variable Definition Levels

#### Job-Level Variables

```json
{
  "Variables": {
    "BATCH_DATE": "20260611",
    "ENVIRONMENT": "PROD"
  }
}
```

#### Folder-Level Variables (Double Backslash Escaping)

```json
{
  "Variables": {
    "\\\\SHARED_VAR": "shared_value"
  }
}
```

#### Named Pool Variables

```json
{
  "Variables": {
    "\\\\poolname\\variable": "value"
  }
}
```

### System Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| **%%$DATE** | Current date | 2026-06-11 |
| **%%JOBNAME** | Job name | my_job_name |
| **%%ODATE** | Order date | 20260611 |
| **%%TIME** | Current time | 142530 |
| **%%COMPSTAT** | Completion status | OK or NotOK |

### Variable Constraints

| Constraint | Value |
|-----------|-------|
| **String length** | 1-255 chars (up to 4000 when resolved) |
| **Integer length** | 1-10 chars base (11 with +/- signs) |
| **Date format** | mmdd, ddmm, yymmdd, yyddmm (site-dependent) |
| **Specific dates** | Max 400 entries |

---

## Priority and Execution Control

### Priority Levels

```json
{
  "Priority": "Very High"    // Textual values
  // OR
  "Priority": "AA"           // Alphanumeric codes (AA-99)
}
```

**Textual Options:** Very High, High, Medium, Low, Very Low  
**Alphanumeric:** AA through 99

### Keep Active Duration

```json
{
  "DaysKeepActive": 5        // 0-98 days
  // OR
  "DaysKeepActive": "Forever"
}
```

### Critical Job Flag

```json
{
  "Critical": true           // Higher resource priority
}
```

### Timezone

```json
{
  "TimeZone": "America/New_York"  // IANA timezone IDs
}
```

---

## Job Execution Modifiers

| Property | Purpose | Values |
|----------|---------|--------|
| **CreatedBy** | User identifier | Username string |
| **Confirm** | Require approval | true/false |
| **RunAsDummy** | Disable without workflow impact | true/false |
| **RunOnAllAgentsInGroup** | Parallel execution | true/false |
| **RetroactiveJob** | Compensatory runs | true/false |
| **EndFolder** | Complete folder after job | true/false |
| **OverridePath** | Alternative script location | Path string |
| **PathElement** | Root-level positioning | Position specification |
| **ReferencePath** | Job templating | Template reference |

---

## Documentation Properties

| Property | Purpose | Format |
|----------|---------|--------|
| **Description** | Object description | String (displayed) |
| **Comment** | Development notes | String (not uploaded) |
| **Documentation** | Reference material | File path or URL |

---

## JSON Structure Patterns

### Basic Job Definition

```json
{
  "Type": "Job:Command",
  "Name": "daily_process",
  "RunAs": "batch_user",
  "Application": "processing",
  "SubApplication": "daily"
}
```

### Job with Scheduling and Events

```json
{
  "Type": "Job:Script",
  "Name": "extract_data",
  "RunAs": "data_user",
  "When": {
    "Schedule": "Everyday",
    "FromTime": "0100",
    "ToTime": "0400"
  },
  "WaitForEvents": [
    {
      "Name": "DATA_READY",
      "Date": "OrderDate"
    }
  ],
  "AddEvents": [
    {
      "Name": "EXTRACT_COMPLETE",
      "DateType": "OrderDate"
    }
  ]
}
```

### Job with Conditional Actions

```json
{
  "Type": "Job:Command",
  "Name": "process_with_fallback",
  "RunAs": "app_user",
  "If": [
    {
      "Condition": {
        "CompletionStatus": "NotOK"
      },
      "Action:Run": {
        "JobName": "error_handler"
      }
    },
    {
      "Condition": {
        "Output": {
          "Pattern": "WARNING*"
        }
      },
      "Action:Mail": {
        "To": "ops@company.com",
        "Subject": "Job Warning"
      }
    }
  ]
}
```

### Cyclic Job Definition

```json
{
  "Type": "Job:Script",
  "Name": "hourly_monitor",
  "RunAs": "monitor_user",
  "Rerun": {
    "Every": 60,
    "Units": "Minutes",
    "From": "Start",
    "Times": 24
  }
}
```

---

## Special Character Handling

### Colon Escaping

```json
{
  "Name": "data:processing",
  "Escaped": "data\\:processing"  // Double backslash escaping
}
```

### Variable Notation

```json
{
  "Variables": {
    "TIMESTAMP": "%%$DATE_%%TIME",
    "FOLDER_VAR": "\\\\shared_variable"
  }
}
```

---

## API Integration Patterns

### Create Job

```json
{
  "Type": "Job:Command",
  "Name": "new_job",
  "RunAs": "execution_user",
  "Application": "app_name",
  // Additional properties as needed
}
```

### Update Job

Modify properties in job object and re-submit (implementation details in REST documentation).

### Query Job

Retrieve job definition with all properties for inspection or comparison.

### Delete Job

Remove job definition from Control-M.

---

## Constraints and Limitations

| Constraint | Impact | Details |
|-----------|--------|---------|
| **Colon character** | Name escaping | Requires `\\:` in JSON |
| **Specific dates** | Limit 400 | Maximum 400 explicit dates |
| **Variable length** | String max 4000 | When resolved; base 255 |
| **Property availability** | Type-dependent | Job Type determines available properties |
| **Cyclic reruns** | Timing control | Complex patterns via RerunIntervals |
| **Date formats** | Site-dependent | mmdd, ddmm, yymmdd, yyddmm based on config |

---

## Notes for Planning Agents

1. **Type-Driven Properties:** Job Type field determines available configuration options
2. **When Object:** Comprehensive scheduling with calendar support
3. **Event System:** Both WaitForEvents (prerequisites) and AddEvents/DeleteEvents (actions)
4. **Conditional Logic:** If statements with 8+ action types and multiple condition types
5. **Notifications:** Pre-execution, post-execution, and duration-based alerts
6. **Cyclic Execution:** Simple intervals or complex multi-unit patterns
7. **Resource Management:** Quantitative pools and exclusive/shared locks
8. **Variable Scoping:** Job-level, folder-level, and named pool variables
9. **Character Escaping:** Colons require `\\:` in JSON strings
10. **API Integration:** Maps to Control-M's internal job model via JSON

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **API Type** | REST (JSON-based) |
| **Object Type** | Job |
| **Format** | JSON |
| **Core Properties** | Type, Name, RunAs, Application, SubApplication |
| **Scheduling** | When object with calendar support |
| **Events** | WaitForEvents, AddEvents, DeleteEvents |
| **Conditional Logic** | If statements with 8+ action types |
| **Notifications** | Pre/post execution and duration-based |
| **Cyclic Execution** | Simple and complex rerun patterns |
| **Resources** | Pools and locks |
| **Variables** | Job, folder, and pool scoping |
| **Character Encoding** | UTF-8 JSON with colon escaping |
| **Constraints** | Type-dependent, 400 date max, special character handling |
