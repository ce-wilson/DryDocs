# Control-M Folder Creation - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Creating_a_Folder.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Folder configuration and design reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Folder types (Regular vs SMART); name 1–64 chars; description ≤4000 chars; Run As user; Control-M/Server assignment; four config tabs (General, Scheduling, Prerequisites, Actions); folder-variable 1–40 chars; naming constraints (no spaces / special chars); rename behavior.
- **SYNTHESIZED:** Any structural examples, Notes for Planning Agents, Vendor Attributes table.

⚠️ **Hazard:** Source contained **no JSON**; any structural/example snippets here are SYNTHESIZED.

---

## Folder Types

Control-M supports two primary folder classifications:

### Regular Folder
- **Purpose:** Collect and group jobs together
- **Inheritance:** Scheduled definitions are NOT inherited by sub-folders or contained jobs
- **Job Processing:** Jobs process independently according to their own parameters
- **Use Case:** When jobs need independent scheduling without parent folder constraints

### SMART Folder
- **Purpose:** Define scheduling criteria at folder level for inheritance
- **Default:** SMART is the default folder type in Control-M
- **Inheritance:** Jobs and sub-folders inherit scheduling criteria defined at folder level
- **Features:** Supports prerequisites and actions in addition to scheduling
- **Use Case:** When multiple jobs share common scheduling, prerequisites, or post-processing logic

## Core Folder Properties

| Property | Details | Constraints |
|----------|---------|-----------|
| **Folder Name** | Identifier for the folder | 1-64 characters (z/OS: 1-8 max); Case-sensitive; Cannot contain special characters: $, /, *, ?, or quotes |
| **Description** | Free-text documentation | Up to 4,000 characters |
| **Control-M/Server** | Specifies which server processes the folder | Required; Determines execution environment |
| **Run Method** | Execution schedule type | Options: Automatic (Daily), Manual (None), or Specific User Daily |
| **Run As** | User account for job execution | 1-30 characters; Must be authorized for job execution |

## Folder Configuration Tabs

Folders support editable attributes across multiple configuration areas:

### 1. General Tab
- Basic folder information
- Metadata and identification
- Naming and description

### 2. Scheduling Tab
- Timing and frequency parameters
- Execution windows
- Calendar-based scheduling
- **Note:** Only applies to SMART folders; Regular folders do not inherit scheduling

### 3. Prerequisites Tab
- Conditions required before folder execution
- Dependencies on other jobs/folders
- Event-based prerequisites

### 4. Actions Tab
- Post-execution operations performed by Control-M
- Notifications
- Conditional actions based on job outcomes

## Additional Folder Parameters

| Parameter | Purpose | Details |
|-----------|---------|---------|
| **Application/Sub-application** | Logical grouping | Organize related jobs into application domains |
| **Site Standard** | Organization-specific rules | Applied at folder level; Enforces company standards |
| **Variables** | Custom values for job processing | 1-40 character limit per variable |
| **Priority** | Resource reservation order | Determines execution priority when resources constrained |
| **Documentation** | Folder documentation reference | URL or file path linking to documentation |

## Naming Constraints & Special Characters

### Character Restrictions
- Cannot include uppercase/lowercase Latin-1 special characters
- Cannot include blank spaces
- Allowed characters: Standard alphanumeric characters

### Parentheses Handling
- Parentheses require forward slash escaping in certain contexts
- Escape syntax: `/(` for opening parenthesis, `/)` for closing
- Example: Folder name with parentheses: `MyFolder/(SubGroup/)`

## Folder Rename Operations

### Rename Requirements
- **Full Load Requirement:** All jobs must be fully loaded in the workspace before renaming
- **Manual Updates:** When folder names appear in other contexts, manual updates may be required

### Update Scenarios
1. Conditional actions referencing old folder name
2. Event definitions referencing old folder name
3. Job prerequisites pointing to old folder name
4. Documentation or labels with old folder name

## Folder Operations Summary

### Creating a Folder
1. Specify folder type (Regular or SMART)
2. Enter folder name (1-64 chars, case-sensitive, no special chars)
3. Select Control-M/Server for execution
4. Set run method (Automatic, Manual, or User Daily)
5. Configure run-as user account
6. Fill additional properties (Application, Priority, Variables, etc.)
7. Configure scheduling (SMART folders only), prerequisites, and actions
8. Save to workspace

### Best Practices
- Use SMART folders for job groups with shared scheduling
- Use Regular folders for independent job execution
- Include descriptive documentation URL
- Set appropriate site standards
- Define clear variable naming conventions
- Plan naming to avoid special character issues

---

## Integration with Job System

Folders serve as containers for:
- Individual jobs
- Sub-folders (hierarchical organization)
- Inherited scheduling and prerequisites (SMART only)
- Shared variables and site standards

Jobs within folders:
- Inherit SMART folder scheduling (if applicable)
- Execute with inherited prerequisites and actions
- Override general parameters at job level if needed
- Respect folder-level resource priorities

---

## Notes for Planning Agents

1. **Folder Hierarchy:** Supports nested sub-folders with inheritance from parent SMART folders
2. **Naming is Critical:** Character restrictions and manual update requirements suggest careful naming strategy
3. **Type Selection:** Clear distinction between Regular (independent) and SMART (inherited) creates two execution patterns
4. **Configuration Levels:** Folder properties span General, Scheduling, Prerequisites, and Actions — mirroring job configuration
5. **Server Assignment:** Folders are server-bound, indicating multi-server coordination possible at Control-M level
6. **Variable Management:** Folder-level variables enable parameterization across contained jobs

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | Folder Management & Configuration |
| **Supports Nesting** | Yes (sub-folders) |
| **Supports Inheritance** | Yes (SMART folders only) |
| **Configuration Scopes** | General, Scheduling, Prerequisites, Actions |
