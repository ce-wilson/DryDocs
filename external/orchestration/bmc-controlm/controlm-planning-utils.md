# Control-M Planning Utilities - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Planning_Utils.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Command-line utilities, programmatic job/folder management, and API integration reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Utility names and one-line purposes — Job tools (defjob, copydefjob, deldefjob, exportdefjob, duplicatedefjob, loopdetecttool); updatedef; Folder tools (deffolder, exportdeffolder, ctmdeffolder, ctmdefsubfolder); Calendar tools (defcal, copydefcal, exportdefcal); Site Standards (export/importsitestandards).
- **SYNTHESIZED:** Everything else.

⚠️ **Hazard:** Source documents these utilities **at high level only** (it did NOT give detailed syntax). The `ctmdef defjob …` / `updatedef …` **command-line examples, workflows, and use cases are SYNTHESIZED illustrations** — not documented BMC syntax. For real syntax use the dedicated ctmdefine / ctmdeffolder docs.

---

## Planning Utilities Definition and Purpose

Planning Utilities are "command-line tools designed to programmatically define and manage Control-M/EM database objects."

**Scope:** Import, export, copy, delete jobs, folders, and calendars without manual UI interaction

---

## Core Utility Categories

### Job Management Tools

| Utility | Purpose | Function |
|---------|---------|----------|
| **defjob** | Import job definitions | Adds jobs to database programmatically |
| **copydefjob** | Duplicate jobs | Copies job between folders |
| **deldefjob** | Remove jobs | Deletes job definitions |
| **exportdefjob** | Export jobs | Exports jobs to files for reuse/backup |
| **duplicatedefjob** | Clone jobs | Duplicates jobs within same data center |
| **loopdetecttool** | Validate events | Prevents circular event dependencies |

### Definition Update Utilities

| Utility | Purpose | Scope |
|---------|---------|-------|
| **updatedef** | Modify parameters | Updates job definitions, folder definitions, SMART folder definitions, sub-folder definitions |

### Folder Management Tools

| Utility | Purpose | Type |
|---------|---------|------|
| **deffolder** | Define folders | Regular and SMART folder creation |
| **exportdeffolder** | Export folders | Exports folder definitions for reuse |
| **ctmdeffolder** | Create SMART folders | SMART folder programmatic definition |
| **ctmdefsubfolder** | Create sub-folders | Sub-folder programmatic definition |

### Calendar Management Tools

| Utility | Purpose | Function |
|---------|---------|----------|
| **defcal** | Define calendars | Creates calendar definitions |
| **copydefcal** | Copy calendars | Duplicates calendar between contexts |
| **exportdefcal** | Export calendars | Exports calendars for reuse |

### Site Standards Tools

| Utility | Purpose | Scope |
|---------|---------|-------|
| **exportsitestandards** | Export site standards | Exports organizational standards |
| **importsitestandards** | Import site standards | Batch updates standards across multiple contexts |

---

## Programmatic Access Patterns

### Job Definition Workflow

```
Define Job (defjob)
  ↓
Configure Parameters (updatedef)
  ↓
Export Job (exportdefjob)
  ↓
Copy to Other Folders (copydefjob/duplicatedefjob)
  ↓
Deploy to Production
```

### Folder Structure Creation

```
Define SMART Folder (ctmdeffolder)
  ↓
Define Sub-folders (ctmdefsubfolder)
  ↓
Assign Jobs (defjob)
  ↓
Configure Inheritance
  ↓
Export for Backup (exportdeffolder)
```

### Calendar Management

```
Define Calendar (defcal)
  ↓
Configure Rules/Dates
  ↓
Export Calendar (exportdefcal)
  ↓
Copy to Multiple Contexts (copydefcal)
  ↓
Import into Folders
```

---

## Integration with Control-M Architecture

### Programmatic Job Definition

Jobs created via utilities inherit full Control-M capabilities:
- Scheduling (calendar-based, time-based)
- Prerequisites (events, resources)
- Actions (if-actions, notifications)
- Variables (job-level, captured)
- File watching (via File Watcher jobs)

### Folder Hierarchy Definition

Utilities support complete hierarchy programmatically:
- SMART folder creation with inheritance rules
- Sub-folder nesting and parameter inheritance
- Regular folder creation for independent execution
- Parameter inheritance chain configuration

### Calendar Configuration

Calendars defined via utilities integrate with:
- Job scheduling (via calendar selection)
- Confirmation calendars (exception policies)
- Holiday/exception handling
- Multi-context calendar sharing

### Event Loop Prevention

**loopdetecttool** validates:
- Event dependencies
- Circular reference detection
- Job sequence integrity
- Prerequisite validity

---

## Programmatic Configuration Advantages

### Advantages

1. **Automation**
   - Script-based job/folder/calendar creation
   - Batch operations across multiple objects
   - Reproducible configurations

2. **Version Control**
   - Configuration stored in version control systems
   - Change tracking and rollback
   - Code review of definitions

3. **Infrastructure as Code**
   - Align with DevOps practices
   - GitOps workflows
   - Automated deployment pipelines

4. **Template Reuse**
   - Export standard definitions
   - Copy/clone across environments
   - Consistent configurations

5. **Bulk Operations**
   - Batch import of job definitions
   - Multi-object updates
   - Site standard synchronization

---

## Documentation Limitations

**Not Fully Specified in Source:**
- JSON/YAML format specifications
- Detailed command syntax examples
- Parameter documentation for each utility
- Error handling and validation rules
- Return codes and status messages
- Script language examples (Python, Bash, etc.)
- Integration with CI/CD pipelines
- Authentication and authorization details

**Implication:** Utilities are documented at high level; detailed API/CLI specification would require additional technical reference documentation.

---

## Operational Workflow Example

### Scenario: Automated Job Deployment

```
1. Define Job Configuration (CLI/API)
   ctmdef defjob -job MyJob -folder MyFolder \
     -type os -command "/bin/process.sh"

2. Set Job Scheduling
   ctmdef updatedef -job MyJob -folder MyFolder \
     -scheduling "every_day" -start_time "02:00"

3. Configure Prerequisites
   ctmdef updatedef -job MyJob -folder MyFolder \
     -event_wait "PREVIOUS_JOB_COMPLETE"

4. Export Configuration
   ctmdef exportdefjob -job MyJob -folder MyFolder \
     -output job_backup.json

5. Duplicate to Test
   ctmdef duplicatedefjob -source MyJob \
     -source_folder MyFolder \
     -target TestJob -target_folder TestFolder

6. Deploy to Production
   ctmdef copydefjob -source TestJob \
     -source_folder TestFolder \
     -target ProdJob -target_folder ProdFolder
```

---

## Integration with Existing Components

### With Variables

Utilities can configure:
- Job-level variables via defjob parameters
- Variable substitution in command definitions
- Capture variables via if-action definitions

### With Job Actions

Utilities can define:
- If-action conditions
- Notification actions
- Event generation actions
- Variable capture actions

### With Scheduling

Utilities support:
- Calendar selection and assignment
- Time window configuration
- Exception policy specification
- Shift By parameter configuration

### With Folders

Utilities enable:
- Folder creation (regular and SMART)
- Sub-folder hierarchy definition
- Parameter inheritance configuration
- Folder deletion and export

---

## Use Cases for Planning Utilities

### Use Case 1: Environment Promotion

```
Dev → Test → Staging → Production
Export from Dev (exportdefjob)
  ↓
Import to Test (defjob)
  ↓
Validate in Test
  ↓
Copy to Staging (copydefjob)
  ↓
Deploy to Production (defjob)
```

### Use Case 2: Bulk Standardization

```
Apply Site Standards (importsitestandards)
  ↓
Update All Jobs (updatedef)
  ↓
Validate Configuration (loopdetecttool)
  ↓
Export for Audit (exportdefjob)
```

### Use Case 3: Disaster Recovery

```
Export All Objects (exportdefjob, exportdeffolder, exportdefcal)
  ↓
Store in Version Control
  ↓
On Failure: Import All Objects (defjob, deffolder, defcal)
  ↓
Restore Configuration in Minutes
```

### Use Case 4: Template-Based Deployment

```
Create Template (defjob with standard parameters)
  ↓
Export Template (exportdefjob)
  ↓
Duplicate for Each Instance (duplicatedefjob)
  ↓
Customize per Instance (updatedef)
  ↓
Deploy All
```

---

## Best Practices

### Configuration Management

1. **Version Control Integration**
   - Export definitions to Git
   - Track changes via commits
   - Review PRs before deployment

2. **Automation Scripts**
   - Create wrapper scripts for complex operations
   - Document command parameters
   - Log all operations for audit trail

3. **Validation**
   - Use loopdetecttool before deployment
   - Test in lower environments first
   - Verify event dependencies

4. **Backup Strategy**
   - Export critical jobs/folders regularly
   - Store exports in version control
   - Test recovery procedures

### Deployment Pipeline

1. **Development**
   - Create jobs via UI or utilities
   - Export to version control
   - Commit with documentation

2. **Testing**
   - Import from version control
   - Validate with loopdetecttool
   - Test in isolated environment

3. **Staging**
   - Copy from test environment
   - Run full integration tests
   - Verify all prerequisites

4. **Production**
   - Deploy from version control
   - Monitor execution
   - Maintain backup exports

---

## Notes for Planning Agents

1. **Programmatic Control:** Utilities enable automated job/folder/calendar management
2. **Batch Operations:** Support bulk import/export/copy/delete
3. **Version Control:** Enable infrastructure-as-code approach
4. **Loop Detection:** loopdetecttool validates event dependencies
5. **Folder Hierarchy:** Support SMART/Regular folders and sub-folders programmatically
6. **Calendar Management:** Full calendar definition and reuse via utilities
7. **Parameter Updates:** updatedef modifies existing definitions across object types
8. **Environment Promotion:** Copy/duplicate support DevOps workflows
9. **Disaster Recovery:** Export/import enable quick configuration recovery
10. **Integration:** Full support for scheduling, variables, actions, prerequisites

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | Planning Utilities (CLI/API) |
| **Job Tools** | 6 utilities (def, copy, del, export, duplicate, loop-detect) |
| **Definition Tools** | 1 utility (updatedef) for all object types |
| **Folder Tools** | 4 utilities (def regular, SMART, sub-folder, export) |
| **Calendar Tools** | 3 utilities (def, copy, export) |
| **Site Standards Tools** | 2 utilities (import/export) |
| **Supported Objects** | Jobs, Folders, SMART folders, Sub-folders, Calendars |
| **Integration** | Job scheduling, events, variables, actions, prerequisites |
| **Validation** | Event loop detection, dependency checking |
| **Use Cases** | Automation, environment promotion, disaster recovery, IaC |
