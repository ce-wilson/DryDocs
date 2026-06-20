# Control-M Changes History - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Changes_History.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Version management, change tracking, and job/folder history reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** "search, view, compare, restore…" capability quote; automatic versioning; 180-day retention (indefinite for current/previous); side-by-side JSON comparison; workspace-based (non-destructive) restoration; deleted-item recovery within 180 days; search filters (date, name, version, change type).
- **SYNTHESIZED:** Use Cases, workflow diagrams, Best Practices, Vendor Attributes table.

⚠️ **Hazard:** The "Limitations / Not Covered" lists (no approval workflow, limited audit logging) are **Claude inference from absence of mention**, not BMC statements — do not load as asserted product limitations.

---

## Changes History Definition and Purpose

Changes History is a version management system that enables users to "search, view, compare, restore previous job versions, and restore deleted jobs and SMART folders."

**Scope:** Automatic version tracking for all job and folder modifications

---

## Automatic Versioning

**Versioning Trigger:**
- Every job creation generates version 1
- Every modification generates new version
- Every deletion creates delete record
- Automatic timestamp and version sequencing

---

## Version Retention Policy

### Retention Periods

| Retention Type | Duration | Scope |
|---|---|---|
| **Standard** | 180 days | All job versions within past 180 days |
| **Current** | Indefinite | Current and previous job versions kept permanently |
| **Deleted Items** | 180 days | Deleted jobs and SMART folders preserved |

### Implication

- Versions older than 180 days may be purged
- Current and immediately previous versions always available
- Deleted items recoverable within 180-day window

---

## Key Capabilities

### Search and Retrieval

**Features:**
- Locate specific versions using filters
- Access via Tools menu
- Filter by date range, version number, or change type
- Search across job and folder versions

### Version Comparison

**Capabilities:**
- Side-by-side JSON script comparison
- "Pinpoint the differences between two versions"
- Visual diff display
- Identify change scope and impact

### Change Restoration

**Restore Options:**
- Restore job to earlier version
- "Creates a new workspace with the restored version"
- Retains changes made in later versions
- Restores deleted jobs
- Restores deleted SMART folders

**Restoration Mechanics:**
- Workspace-based restoration (non-destructive)
- Historical changes preserved
- Safe rollback without data loss

---

## Workspace Integration

### Restoration Workflow

```
Select Earlier Version
  ↓
Initiate Restore
  ↓
Creates New Workspace with Restored Version
  ↓
Later Changes Retained in History
  ↓
Changes Available for Comparison/Merge
```

### Implications

- Restoration is non-destructive
- Original version history preserved
- Multiple restoration points available
- Workspace-based approach enables review

---

## Change Types Tracked

**Automatically Tracked:**
- Job creation
- Job modification (all attributes)
- Job deletion
- SMART folder creation
- SMART folder modification
- SMART folder deletion
- Folder hierarchy changes
- Parameter modifications

---

## Search Capabilities

### Search Filters

**Available Filters:**
- Date range (from/to dates)
- Job name pattern
- Folder name pattern
- Version number
- Change type
- Modification status

### Search Results

- Version number
- Modification timestamp
- Change summary
- Associated job/folder
- Previous version reference

---

## JSON Comparison

### Side-by-Side Format

```
Version N-1          →          Version N
├─ Job Parameters      ├─ Job Parameters (modified)
├─ Scheduling          ├─ Scheduling (updated)
├─ Prerequisites       ├─ Prerequisites (changed)
├─ Actions             ├─ Actions (new/removed)
└─ Variables           └─ Variables (values updated)
```

### Difference Highlighting

- Additions shown distinctly
- Removals shown distinctly
- Modifications highlighted
- Context preserved

---

## Integration with Control-M Architecture

### With Job/Folder Management

- Every job/folder change versioned
- Change history part of job definition
- Accessible from job details
- Independent of job scheduling

### With Workspaces

- Restoration creates workspace
- Non-destructive recovery
- Enables change review
- Supports change approval workflow (implied)

### With Job Scheduling

- Versioning independent of execution
- Historical versions don't affect scheduling
- Restored versions follow current schedule
- Change history doesn't block job runs

---

## Notable Limitations

**Not Covered in Documentation:**
- Formal approval workflows
- Detailed audit logging
- Change categorization system
- Reporting and tracking mechanisms
- Integration specifications with deployment systems
- Role-based change restrictions
- Change notification workflows
- Mandatory change approval processes

**Implication:** Changes History provides technical version management but may not cover organizational change control requirements.

---

## Use Cases

### Use Case 1: Accidental Modification Recovery

```
Job Modified Incorrectly
  ↓
Search Changes History
  ↓
Compare Current vs. Previous Version
  ↓
Restore to Known Good Version
  ↓
Review Changes in Workspace
  ↓
Deploy Restored Version
```

### Use Case 2: Change Review & Audit

```
View Job Version History
  ↓
Compare Sequential Versions
  ↓
Identify Who Changed What/When
  ↓
Document Changes for Audit
  ↓
Approve & Deploy if Acceptable
```

### Use Case 3: Rollback After Deployment

```
Job Deployed with Bug
  ↓
Check Changes History
  ↓
Identify Last Known Good Version
  ↓
Restore to Previous Version
  ↓
Verify in Workspace
  ↓
Deploy Previous Good Version
```

### Use Case 4: Deleted Job Recovery

```
Job Accidentally Deleted
  ↓
Search Changes History for Deleted Jobs
  ↓
Locate Deletion within 180 days
  ↓
Restore Deleted Job
  ↓
Job Available in Workspace
  ↓
Redeploy if Needed
```

---

## Best Practices

### Version Management

1. **Review Before Critical Changes**
   - View current version before modification
   - Understand existing configuration
   - Plan changes based on history

2. **Document Change Reasons**
   - Use job descriptions for change justification
   - Reference version numbers in notes
   - Enable future change understanding

3. **Test Restored Versions**
   - Create test workspace from restored version
   - Verify functionality before deployment
   - Compare with current to understand differences

### Change Recovery

1. **Identify Correct Version**
   - Use version comparison to find correct version
   - Review timestamps for context
   - Confirm version before restoration

2. **Workspace-Based Recovery**
   - Restore to workspace first
   - Review changes thoroughly
   - Verify dependencies and impacts
   - Then promote to production

3. **Maintain Change Records**
   - Document why change needed
   - Record restoration actions
   - Keep audit trail for compliance

---

## Constraints and Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| **180-day retention** | Older versions purged | Archive versions if long-term retention needed |
| **No approval workflow** | Changes not formally reviewed | Use workspace verification process |
| **No audit logging** | Change authorization not tracked | Document change decisions separately |
| **Workspace-based restoration** | Requires workspace management | Understand workspace merge implications |
| **JSON comparison only** | May be hard to read for non-technical | Use diff tools or documentation |

---

## Integration with Deployment

### Deployment Considerations

- Restored version has no deployment history
- Must be re-deployed after restoration
- Scheduling from restoration point applies
- Dependencies must be re-verified

### Change Tracking

- Version history available for audit
- Restoration creates traceable change
- Previous versions accessible for review
- Deletion recovery available (180-day window)

---

## Notes for Planning Agents

1. **Automatic Versioning:** Every change creates new version automatically
2. **180-Day Retention:** Standard retention, indefinite for current versions
3. **Non-Destructive Restoration:** New workspace created with restored version
4. **JSON Comparison:** Side-by-side diff viewing of versions
5. **Workspace-Based Recovery:** Changes can be reviewed before promotion
6. **Deleted Item Recovery:** Deleted jobs/folders recoverable within 180 days
7. **Search Capabilities:** Filter by date, name, version, change type
8. **No Formal Approval:** Technical version management without workflow approval
9. **Change Auditing:** Version history provides change trail but limited audit logging
10. **Integration Gap:** May require additional tools for formal change management

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | Changes History / Version Management |
| **Versioning** | Automatic (every creation/modification) |
| **Retention** | 180 days standard, indefinite for current |
| **Comparison** | JSON side-by-side diff |
| **Restoration** | Workspace-based (non-destructive) |
| **Search** | By date, name, version, type |
| **Scope** | Jobs and SMART folders |
| **Deleted Recovery** | 180-day window |
| **Approval Workflow** | Not included |
| **Audit Logging** | Limited (version history only) |
| **Deployment Integration** | Manual re-deployment required |
