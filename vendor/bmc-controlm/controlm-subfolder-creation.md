# Control-M Sub-folder Creation - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Creating_a_Sub-folder.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Sub-folder hierarchy and configuration reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Sub-folders only within SMART folders (not Regular); nesting depth 1–9 levels for reference sub-folders; name 1–64 chars, case-sensitive, no spaces/apostrophes; inheritance of scheduling/prerequisites/actions from parent; reference sub-folder reuse.
- **SYNTHESIZED:** Sub-folder-vs-Regular comparison matrix, best-practice prose, Notes for Planning Agents, Vendor Attributes table.

---

## Definition and Purpose

A sub-folder is a nested container within a SMART folder that organizes jobs hierarchically. According to BMC documentation:

> "Sub-folders and jobs inherit the attributes that you define at the SMART folder level."

**Key Characteristic:** Sub-folders enable multi-level hierarchical organization while maintaining parameter inheritance from the parent SMART folder.

---

## Hierarchy and Nesting Requirements

### Structural Constraints

- **SMART Folder Requirement:** Sub-folders can **only be created within SMART folders**, not as standalone entities
- **Nesting Depth:** Maximum nesting depth for reference sub-folders is 1-9 levels
- **Parent-Child Relationships:** Maintained through the Parent Folder attribute
- **No Sub-Sub-folders:** Cannot create sub-folders directly within sub-folders (only within SMART folders)

### Implication
This constraint creates a two-tier hierarchy:
```
SMART Folder (Top level)
├── Sub-folder 1 (Inherits from SMART Folder)
│   └── Jobs (Inherit from Sub-folder and SMART Folder)
├── Sub-folder 2 (Inherits from SMART Folder)
│   └── Jobs (Inherit from Sub-folder and SMART Folder)
└── Jobs (Direct children of SMART Folder)
```

---

## Core Sub-folder Properties

### Naming Rules

| Rule | Details |
|------|---------|
| **Length** | 1–64 characters (z/OS: 1–8 max) |
| **Case Sensitivity** | Case-sensitive (MyFolder ≠ myfolder) |
| **Prohibited Characters** | Spaces, apostrophes, dollar signs ($), forward slashes (/), asterisks (*), question marks (?), quotes ("), and other special characters |
| **Uniqueness** | Job names must remain unique within each sub-folder |

### Key Attributes

| Attribute | Purpose | Notes |
|-----------|---------|-------|
| **Folder Type** | Designation as SMART or Regular | Sub-folders inherit from SMART parent |
| **Description** | Free-text documentation | Up to 4,000 characters |
| **Control-M/Server** | Server processing assignment | Inherited from parent SMART folder |
| **Run As** | Username for execution authorization | 1-30 characters; Must be authorized |
| **Application/Sub-Application** | Logical job grouping | Hierarchical organization unit |
| **Priority** | Resource reservation order | Determines execution priority |
| **Parent Folder Attribute** | References parent SMART folder | Maintains hierarchical relationship |

---

## Inheritance Mechanism

### What Gets Inherited

Sub-folders and jobs inherit the following from parent SMART folder:

1. **Scheduling Attributes**
   - Execution timing
   - Calendar-based scheduling
   - Frequency patterns

2. **Prerequisites Capabilities**
   - Prerequisite conditions
   - Dependency definitions
   - Event-based triggers

3. **Action Definitions**
   - Post-execution operations
   - Notifications
   - Conditional actions

### Inheritance Benefits
- Reduces configuration redundancy
- Ensures consistent scheduling across job groups
- Simplifies maintenance of common rules
- Enables bulk updates via parent folder changes

### Parameter Override
Child elements inherit from parent but can override specific attributes at the sub-folder or job level.

---

## Reference Sub-folders (Advanced Feature)

### Definition
A reference sub-folder is **"an empty sub-folder that points to another SMART folder or job"** enabling reuse without duplication of jobs.

### Capabilities
Reference sub-folders support:
- **Variable Resolution Override** — Substitute variables at reference point
- **If-Actions Inheritance** — Conditional actions from referenced folder
- **Lock Resource Management** — Resource locking propagated
- **Notification Propagation** — Alerts and notifications inherited

### Constraints
- Cannot contain actual jobs (empty container only)
- Referenced folders cannot include wildcards in pathnames
- Points to existing SMART folder or job (no creation of new content)

### Use Cases
- Reuse of common job sequences without duplication
- Parameterized job flows through variable override
- Multi-location job submission through single reference
- Resource pooling and lock management

---

## Constraints and Limitations

### Structural Constraints
| Constraint | Impact | Workaround |
|-----------|--------|-----------|
| Sub-folders only within SMART folders | Cannot nest within Regular folders | Use SMART folders for hierarchical organization |
| Reference sub-folders cannot contain jobs | Read-only references only | Use regular sub-folders for actual job containers |
| Referenced folders cannot include wildcards | Explicit folder reference required | Specify exact folder paths |
| No sub-folder within sub-folder nesting | Maximum 2-level hierarchy | Flatten structure or use SMART folders |

### Operational Constraints
- Renaming requires manual updates to all dependent prerequisites and actions
- All jobs must be fully loaded in workspace before renaming
- Cross-references in event definitions must be manually updated

### Job Uniqueness
- Job names must be unique within each sub-folder scope
- Same job name can exist in different sub-folders

---

## Creation Procedure

The sub-folder creation process involves:

1. **Drag folder into workspace**
   - Create new folder entity
   - Position in working environment

2. **Designate as SMART folder**
   - Set folder type to SMART
   - Enable scheduling and inheritance

3. **Nest additional folders**
   - Create sub-folders within SMART folder
   - Establish parent-child relationships

4. **Define properties through configuration tabs**
   - **General tab:** Folder info, naming, description
   - **Scheduling tab:** Timing and frequency
   - **Prerequisites tab:** Dependency conditions
   - **Actions tab:** Post-execution operations

---

## Configuration Tabs

Sub-folders support the same configuration structure as regular folders:

| Tab | Content |
|-----|---------|
| **General** | Basic folder information, metadata, naming |
| **Scheduling** | Inherited timing/frequency; Can override at sub-folder level |
| **Prerequisites** | Inherited conditions; Can add additional prerequisites |
| **Actions** | Inherited actions; Can add sub-folder-specific actions |

---

## Sub-folder vs. Regular Folder Comparison

| Aspect | Sub-folder | Regular Folder |
|--------|-----------|-----------------|
| **Parent Required** | Must be within SMART folder | Standalone or at root |
| **Inheritance** | Inherits from parent SMART folder | No inheritance |
| **Nesting** | Can be nested within SMART folders | Cannot contain sub-folders |
| **Scheduling Inheritance** | Inherits parent scheduling | Uses own scheduling |
| **Use Case** | Hierarchical organization with inheritance | Flat grouping or independent scheduling |
| **Reference Type** | Can be reference sub-folders | Not applicable |
| **Configuration Complexity** | Medium (inherits + overrides) | Low (standalone config) |

---

## Best Practices for Sub-folder Organization

1. **Use SMART Folders as Top Level**
   - Always use SMART folder at hierarchy root
   - Enables inheritance throughout structure

2. **Logical Grouping**
   - Organize by business process or application
   - Use sub-folders to group related job sequences

3. **Naming Convention**
   - Avoid special characters (spaces, $, /, *, ?, ")
   - Use clear, hierarchical naming (e.g., PAYROLL_WEEKLY_BATCH)
   - Keep names short (remember z/OS 1-8 char limit)

4. **Inheritance Strategy**
   - Define common scheduling at SMART folder level
   - Override only when specific jobs need different behavior
   - Use prerequisites for flow control

5. **Reference Sub-folders**
   - Use for reusable job sequences
   - Parameterize through variable override
   - Document referenced folder intentions

6. **Maintenance Considerations**
   - Document folder hierarchy
   - Update cross-references when renaming
   - Test inheritance chain before deployment
   - Monitor for duplicate parameter definitions

---

## Integration with Planning Architecture

Sub-folders support the planning architecture by:
- Enabling hierarchical job organization
- Propagating SMART folder scheduling to multi-level depth
- Supporting reuse through reference sub-folders
- Maintaining parameter inheritance across levels
- Reducing configuration complexity through inheritance

---

## Notes for Planning Agents

1. **Hierarchy Depth:** Sub-folders support up to 9 levels of nesting with 1-9 reference depth
2. **SMART Only:** Sub-folders must be within SMART folders to get inheritance
3. **Reference Pattern:** Reference sub-folders enable reuse without duplication
4. **Naming Constraints:** Stricter than regular folders (no spaces, apostrophes, etc.)
5. **Inheritance Chain:** Properties flow from SMART folder → Sub-folder → Jobs
6. **Operational Impact:** Renaming cascades through manual updates

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | Sub-folder Management & Hierarchy |
| **Max Nesting Depth** | 1-9 levels for references |
| **Parent Requirement** | SMART folder required |
| **Inheritance Support** | Full (scheduling, prerequisites, actions) |
| **Reference Folders** | Supported for reuse patterns |
