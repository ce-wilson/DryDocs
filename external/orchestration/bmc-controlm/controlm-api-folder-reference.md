# Control-M Folder API - Code Reference

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** API_CodeRef_Folder.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Folder API object structure, JSON format, and REST integration reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## ⚠️ FORMAT MISMATCH & SYNTHESIZED-JSON WARNING — READ FIRST

This page documents the **Control-M Automation API (JSON)** — a **SaaS** interface. The target environment (**9.0.21.300**) defines folders/jobs in **XML** (export/import via ctmdefine / ctmdeffolder / ctmpsm), **not JSON**. Use this file as a **conceptual reference only** — to learn *which properties, constraints, and behaviors exist* where they may add detail applicable to our XML definitions. **Do not treat the JSON as our format, and do not convert to JSON.**

Additionally, the JSON *structure* below was Claude-synthesized and is **confirmed structurally inaccurate** (verified 2026-06-11 against the live `API_CodeRef_Folder` page). The canonical Automation API uses the object **name as the JSON key**:
```json
"FolderSample": { "Type": "Folder", "When": {...}, "Job1": { "Type": "Job:Command", ... } }
```
— jobs nested as named keys, concrete types like `Job:Command`. My examples' top-level `"Name"` property and `"Jobs": []` array match **neither** the canonical (name-as-key) nor the array form. **All JSON blocks here are illustrative only.**

---

## 📑 Provenance Classification

Produced by WebFetch of one BMC page + Claude restructuring. Tiers: **[VERBATIM]** = BMC quotes · **[GROUNDED]** = Claude paraphrase of sourced content · **[SYNTHESIZED]** = Claude-authored, not in source (do NOT load as vendor ground truth).

- **GROUNDED:** Core properties (Type, When, ControlmServer, RunAs, OrderMethod, AdjustEvents, Application/SubApplication, Priority, TimeZone, Variables); inheritance statement; colon `\\:` escaping rule; `allowDuplicateJobNames` requirement; Folders/Jobs array structure.
- **VERBATIM:** The "A folder enables you to configure…" and colon-escape quotes.
- **SYNTHESIZED:** All JSON examples; every "Pattern"; "API Integration Patterns/Considerations"; Best Practices; Vendor Attributes table.

⚠️ **Hazard:** The BMC source **explicitly did not include API endpoints, HTTP methods, or REST service details.** The entire **"Folder Object Usage in API Requests" (Create/Update/Query/Delete)** section and all request/response JSON are SYNTHESIZED illustrations — not documented BMC API contracts.

---

## Folder API Overview

The Folder API enables programmatic management of Control-M folders using JSON-based requests.

**Key Concept:** "A folder enables you to configure various settings such as scheduling, event management, adding resources, or adding notifications at the folder level. Folder-level definitions are inherited by the jobs or sub-folders within the folder."

---

## Folder Object Structure

### Core Properties

| Property | Purpose | Details |
|----------|---------|---------|
| **Type** | Object designation | "Folder" literal |
| **When** | Scheduling criteria | Scheduling rules or RBC |
| **ControlmServer** | Server assignment | Which scheduling server |
| **RunAs** | Execution user | Job execution account |
| **OrderMethod** | Execution mode | "Automatic" (default) or "Manual" |

### Additional Properties

| Property | Purpose | Notes |
|----------|---------|-------|
| **AdjustEvents** | Event succession handling | Controls successor event waiting |
| **Application** | Logical grouping | Application name |
| **SubApplication** | Hierarchical organization | Sub-application categorization |
| **Priority** | Resource reservation | Execution priority level |
| **TimeZone** | Timezone specification | Timezone for folder execution |
| **Variables** | Folder-level variables | Custom configuration values |

---

## Configuration Inheritance

### Inheritance Model

Folder-level configurations inherit to:
- Jobs within the folder
- Sub-folders within the folder
- Nested job/sub-folder hierarchy

**Inherited Properties:**
- Scheduling criteria
- Event management configuration
- Resource requirements
- Notification settings
- Variables and parameters

### Implication

Jobs and sub-folders inherit folder-level definitions unless explicitly overridden at their own level.

---

## JSON Structure Patterns

### Folder Definition Object

```json
{
  "Type": "Folder",
  "Name": "folder_name",
  "ControlmServer": "server_name",
  "OrderMethod": "Automatic",
  "RunAs": "execution_user",
  "Application": "app_name",
  "SubApplication": "sub_app_name",
  "Priority": "priority_level",
  "TimeZone": "timezone",
  "When": {
    // Scheduling criteria or RBC definition
  },
  "Variables": {
    // Folder-level variables
  }
}
```

### Nested Folder Structure

```json
{
  "Type": "Folder",
  "Name": "parent_folder",
  "Folders": [
    {
      "Type": "Folder",
      "Name": "sub_folder_1"
    },
    {
      "Type": "Folder",
      "Name": "sub_folder_2"
    }
  ],
  "Jobs": [
    {
      "Type": "Job",
      "Name": "job_1"
    }
  ]
}
```

---

## Folder Containment

Folders support nested structures:

### Supported Nested Elements

- **Folders**: Sub-folders for hierarchical organization
- **Jobs**: Individual job definitions
- **Resources**: Resource requirements
- **Notifications**: Alert and messaging configuration
- **Events**: Event management definitions

---

## Special Characters and Escaping

### Colon Character Handling

**Important:** "If the folder name contains a colon character, escape the colon character with two backslashes."

**Example:**
```
Folder name: "data:processing"
API representation: "data\\:processing"
```

**Implication:** Double-backslash escaping required in JSON strings for colon characters.

---

## Array-Based Definition

### Folders and Jobs Arrays

Alternative to individual object definitions:

```json
{
  "Folders": [
    {
      "Type": "Folder",
      "Name": "folder_1",
      "Folders": [
        {
          "Type": "Folder",
          "Name": "sub_folder_1"
        }
      ]
    },
    {
      "Type": "Folder",
      "Name": "folder_2"
    }
  ],
  "Jobs": [
    {
      "Type": "Job",
      "Name": "job_1"
    }
  ]
}
```

### System Setting Requirement

**Prerequisite:** `allowDuplicateJobNames` system setting must be configured.

**Purpose:** Enables duplicate job names across different folders using array-based definitions.

---

## Folder API Integration Patterns

### Pattern 1: Simple Folder Definition

```json
{
  "Type": "Folder",
  "Name": "batch_processing",
  "ControlmServer": "PROD",
  "OrderMethod": "Automatic",
  "RunAs": "batch_user",
  "Application": "batch"
}
```

### Pattern 2: SMART Folder with Scheduling

```json
{
  "Type": "Folder",
  "Name": "daily_batch",
  "ControlmServer": "PROD",
  "RunAs": "scheduler",
  "When": {
    "SchedulingRule": "daily",
    "Time": "02:00"
  },
  "Priority": "HIGH",
  "TimeZone": "America/New_York"
}
```

### Pattern 3: Hierarchical Folder Structure

```json
{
  "Type": "Folder",
  "Name": "enterprise_workflows",
  "Application": "enterprise",
  "Folders": [
    {
      "Type": "Folder",
      "Name": "finance_batch",
      "SubApplication": "finance"
    },
    {
      "Type": "Folder",
      "Name": "hr_batch",
      "SubApplication": "hr"
    }
  ]
}
```

### Pattern 4: Folder with Variables and Inheritance

```json
{
  "Type": "Folder",
  "Name": "configurable_batch",
  "Variables": {
    "BATCH_DATE": "20260611",
    "BATCH_ENV": "PROD"
  },
  "Folders": [
    {
      "Type": "Folder",
      "Name": "child_folder"
      // Inherits variables and other properties from parent
    }
  ]
}
```

---

## API Integration Considerations

### Folder Object Mapping

API folder definitions map to Control-M's internal folder structure:
- SMART Folder → API Folder with When/Scheduling
- Regular Folder → API Folder without When
- Sub-folder → Nested Folder object

### Inheritance Propagation

API automatically propagates:
- Parent scheduling to children
- Parent variables to children
- Parent priority/timezone to children
- Unless explicitly overridden

### Character Encoding

- JSON standard UTF-8 encoding
- Special characters require escaping
- Colon character requires double-backslash
- Quote characters use standard JSON escaping

---

## Folder Object Usage in API Requests

### Create Folder

Expected request structure:
```json
{
  "Type": "Folder",
  "Name": "new_folder",
  "ControlmServer": "server_name",
  "RunAs": "user",
  // Additional properties
}
```

### Update Folder

Modify properties in folder object (implementation details in REST documentation).

### Query Folder

Retrieve folder definition with nested structure for:
- Jobs within folder
- Sub-folders
- Configuration inheritance

### Delete Folder

Remove folder and optionally:
- Cascade delete to sub-folders
- Cascade delete to jobs (configuration-dependent)

---

## Integration with Other API Components

### With Job API

Folders contain Job objects:
```json
{
  "Type": "Folder",
  "Name": "folder_name",
  "Jobs": [
    {
      "Type": "Job",
      "Name": "job_1"
    }
  ]
}
```

### With Event API

Folders support event configuration:
```json
{
  "Type": "Folder",
  "Name": "folder_name",
  "Events": {
    // Event definitions
  }
}
```

### With Resource API

Folders can reference resources:
```json
{
  "Type": "Folder",
  "Name": "folder_name",
  "Resources": [
    {
      "Name": "resource_1"
    }
  ]
}
```

---

## Best Practices for Folder API

### JSON Structure Design

1. **Hierarchy Planning**
   - Design folder hierarchy before API calls
   - Plan inheritance at each level
   - Consider variable scope requirements

2. **Property Configuration**
   - Set essential properties (Name, ControlmServer, RunAs)
   - Configure application hierarchy (Application/SubApplication)
   - Define scheduling at appropriate level

3. **Special Character Handling**
   - Escape colons with `\\:`
   - Use standard JSON escaping for quotes
   - Test special characters in folder names

4. **Inheritance Strategy**
   - Define common properties at folder level
   - Override only when necessary at job/sub-folder level
   - Document inheritance chain for maintenance

### API Integration

1. **Request Structure**
   - Use proper JSON formatting
   - Include all required properties
   - Validate before submission

2. **Response Handling**
   - Parse JSON response structures
   - Validate successful creation
   - Handle error responses appropriately

3. **Error Handling**
   - Check for colon escaping issues
   - Validate property values
   - Handle nested structure conflicts

---

## Limitations and Constraints

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| **Colon character** | Requires escaping | Use `\\:` in JSON |
| **Duplicate job names** | Requires system setting | Enable `allowDuplicateJobNames` |
| **Character encoding** | UTF-8 only | Use standard JSON encoding |
| **Nested depth** | May have limits | Flatten hierarchy if needed |

---

## Notes for Planning Agents

1. **JSON-Based Definition:** Folders defined as JSON objects with structured properties
2. **Core Properties:** Type, Name, ControlmServer, RunAs, OrderMethod, When
3. **Inheritance Model:** Folder properties inherit to jobs and sub-folders
4. **Nested Structure:** Support for hierarchical folder and job organization
5. **Array Support:** Alternative array-based definitions for bulk operations
6. **Character Escaping:** Colons require double-backslash escaping
7. **Element Containment:** Support for Folders, Jobs, Resources, Notifications, Events
8. **Variable Support:** Folder-level variables with inheritance propagation
9. **Timezone Support:** Timezone configuration at folder level
10. **API Integration:** JSON structure maps to Control-M internal folder model

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **API Type** | REST (JSON-based) |
| **Object Type** | Folder |
| **Format** | JSON |
| **Core Properties** | Type, Name, ControlmServer, RunAs, OrderMethod |
| **Optional Properties** | Application, SubApplication, Priority, TimeZone, Variables |
| **Scheduling Support** | When property with scheduling criteria |
| **Inheritance** | To jobs and sub-folders |
| **Nesting** | Folders, Jobs, Resources, Notifications, Events |
| **Array Support** | Yes (with allowDuplicateJobNames) |
| **Special Characters** | Colon requires `\\:` escaping |
| **Encoding** | UTF-8 JSON |
