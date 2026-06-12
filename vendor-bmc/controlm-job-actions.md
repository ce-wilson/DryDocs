# Control-M Job Actions - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Job_actions.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Job actions, conditional execution, automation triggers, and workflow control reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Six action categories; if-action condition types (job status, exit codes, execution counts, output patterns, variable values, z/OS specifics); eight if-action responses; notification destinations (Alerts Window, Email, Remedy, Job/User Console, z/OS); pre- vs post-action lifecycle.
- **SYNTHESIZED:** All JSON/example branching, Use Cases, Notes for Planning Agents, Vendor Attributes table.

---

## Job Actions Definition and Purpose

Job actions are "additional types of tasks that Control-M automatically performs before, during, or after a job executes."

**Scope:** Enable sophisticated workflow automation and monitoring beyond basic job execution

---

## Six Primary Action Categories

### 1. Events

**Purpose:** Add or remove conditional entities establishing sequential relationships

**Mechanism:**
- Adds events to trigger successor jobs
- Removes events when job completes
- Establishes dynamic workflow relationships
- Enables event-based job sequencing

### 2. Notifications Before Job Completion

**Purpose:** Send alerts before job execution completes

**Triggers:**
- Job submission delays
- Execution time thresholds
- Cyclic job submission delays
- Pre-completion alerting

### 3. If-Actions

**Purpose:** Conditional actions executing when user-defined job conditions are satisfied

**Value:** Branching logic within workflows based on runtime conditions

### 4. Notifications After Job Completion

**Purpose:** Send alerts following job completion

**Triggers:**
- Success (Ended OK) status
- Failure (Ended Not OK) status
- Completion-based notifications

### 5. Capture from Job Output

**Purpose:** Extract data from job output and store in variables

**Use Case:** Downstream job consumption of preceding job data

### 6. Output Handling

**Purpose:** Manage job output disposition

**Operations:**
- Copy output to specified locations
- Move output to archive
- Delete output
- Print output

---

## If-Action Conditions

If-actions evaluate diverse job conditions:

| Condition Type | Examples |
|---|---|
| **Job Completion Status** | OK, Not OK, any completion |
| **OS Exit Codes** | Specific return codes (0, 1, 127, etc.) |
| **Execution Counts** | Execution count, rerun count thresholds |
| **Output Availability** | Output exists, output contains patterns |
| **Variable Values** | String comparisons, numeric comparisons |
| **Output Patterns** | Specific statement patterns in job output |
| **z/OS Specific** | Program steps, JOBRC codes, step completion |

---

## If-Action Responses

When conditions are met, Control-M executes corresponding actions:

| Response | Purpose |
|---|---|
| **Notify** | Send notifications to destinations |
| **Set to OK/Not OK** | Override job completion status |
| **Rerun Job** | Re-execute the job |
| **Stop Cyclic Run** | Halt subsequent cyclic iterations |
| **Set Variable** | Define variables for downstream usage |
| **Run Job Ignoring Scheduling** | Force job execution bypassing schedule checks |
| **Handle Output** | Manage output disposition |
| **Add/Delete Event** | Modify workflow prerequisites dynamically |

---

## Notification Destinations

**Available Channels:**
- Alerts Window (Control-M UI)
- Email
- Remedy Help Desk
- Job Console
- User Console
- Platform-specific options:
  - **z/OS:** System Console, TSO User, IOA Log, Mail Group
  - **Distributed:** Email, SNMP trap, Webhook (implied)

---

## Pre-Actions (Before Job Execution)

Actions executed before job starts:

**Typical Use Cases:**
- Set variables before job execution
- Add prerequisites dynamically
- Create output directories
- Pre-job notifications
- Dependency setup

---

## Post-Actions (After Job Execution)

Actions executed after job completes:

**Typical Use Cases:**
- Notify based on completion status
- Capture output for downstream jobs
- Set variables from job results
- Generate events for successor jobs
- Clean up temporary files
- Archive output

---

## Conditional Action Flow

```
Job Executes
  ↓
Capture Exit Code/Status
  ↓
Evaluate If-Action Conditions:
├─ Completion status (OK/Not OK)
├─ Exit codes
├─ Variable values
├─ Output patterns
└─ Execution counts
  ↓
Conditions Met?
├─ YES → Execute Responses:
│   ├─ Notify
│   ├─ Set variable
│   ├─ Add/Delete event
│   ├─ Rerun job
│   └─ Handle output
└─ NO → Continue with next step
```

---

## Variable Setting Actions

**Purpose:** Define variables dynamically during job execution

**Variables Available from Job:**
- Job metadata (name, application, return code)
- Captured output values
- System information
- Execution context

**Use Case:** Pass job results to downstream jobs without manual coding

---

## Event Generation Actions

**Purpose:** Dynamically add or remove events based on job conditions

**Mechanism:**
- Add event → Trigger successor jobs
- Delete event → Skip dependent jobs
- Conditional event generation
- Dynamic workflow modification

**Use Case:** Event-based workflow branching based on runtime conditions

---

## Integration with Job Execution Lifecycle

### Execution Points

```
Job Definition
  ↓
Pre-Actions (Before Execution)
├─ Set variables
├─ Create resources
└─ Send notifications
  ↓
Job Execution
  ↓
Post-Actions (After Execution)
├─ Capture output
├─ Evaluate conditions
├─ Execute responses
└─ Generate events
  ↓
Successor Job Trigger (via events/schedules)
```

---

## Integration with Control-M Architecture

### With Variables

- **Capture Action:** Extract job output → Variable
- **Set Variable Action:** Dynamic variable creation
- **Condition Evaluation:** Variable value conditions in if-actions
- **Substitution:** Variables used in action parameters

### With Events

- **Event Actions:** Add/Delete events based on conditions
- **Dynamic Triggering:** Successor jobs triggered by action-generated events
- **Conditional Flow:** Branch workflows based on job outcomes

### With Scheduling

- **Override Scheduling:** "Run Job Ignoring Scheduling Criteria" action
- **Rerun Scheduling:** Rerun action respects schedule constraints
- **Time-Based Conditions:** Execution time thresholds trigger notifications

### With Prerequisites

- **Event-Based Prerequisites:** Actions modify event prerequisites
- **Dynamic Workflow:** Prerequisites change based on job execution results
- **Conditional Prerequisites:** If-actions change prerequisite satisfaction

---

## Common Action Patterns

### Pattern 1: Success Notification

```
If-Action Condition: Ended OK
Response: Notify via Email
Destination: Team mailing list
Purpose: Alert successful completion
```

### Pattern 2: Failure Recovery

```
If-Action Condition: Ended Not OK
Responses:
├─ Notify via Alert
├─ Set Variable (error_code)
└─ Add Event (manual_intervention_required)
Purpose: Alert and escalate on failure
```

### Pattern 3: Output Capture & Pass-Forward

```
If-Action Condition: Output contains "RECORDS_PROCESSED: "
Response: Capture from Job Output
Variable: %%RECORD_COUNT
Next Job: Uses %%RECORD_COUNT in processing
Purpose: Data-driven workflow
```

### Pattern 4: Conditional Rerun

```
If-Action Condition: Exit code 5 (temporary failure)
Response: Rerun Job
Retry Count: 3
Interval: 30 seconds
Purpose: Transient error recovery
```

### Pattern 5: Dynamic Event Generation

```
If-Action Condition: Variable %%STATUS == "CRITICAL"
Response: Add Event
Event Name: escalate_to_management
Target Job: Executive notification job
Purpose: Escalation workflow
```

---

## Best Practices

### If-Action Design

1. **Specific Conditions**
   - Use exact exit codes, not ranges
   - Test pattern matching before deployment
   - Document condition logic

2. **Proportional Responses**
   - Notify appropriately (not excessive alerts)
   - Rerun only recoverable failures
   - Set variables for downstream usage

3. **Error Handling**
   - Capture failure details in variables
   - Set clear variable values for downstream logic
   - Avoid silent failures (notify on unexpected states)

### Notification Strategy

1. **Tiered Alerting**
   - Warnings to ops console
   - Errors to email/Remedy
   - Critical to multiple channels

2. **Relevant Information**
   - Include job name, application, timestamp
   - Add captured output/variables
   - Provide remediation guidance

### Variable Management

1. **Naming Convention**
   - Use descriptive variable names
   - Document variable content and format
   - Prefix with source/purpose (e.g., JOB_OUTPUT_*, ERROR_*)

2. **Validation**
   - Validate captured data format
   - Handle missing output gracefully
   - Set defaults for downstream use

---

## Constraints and Limitations

| Constraint | Impact | Workaround |
|-----------|--------|-----------|
| **Action execution time** | Delays job completion reporting | Async notifications recommended |
| **Output capture limits** | Large output may truncate | Split output capture into smaller pieces |
| **Variable size limits** | Variables have size constraints | Use file output for large data |
| **Notification delivery** | No guaranteed delivery | Log/archive critical notifications |
| **Cyclic action limits** | Excessive actions impact performance | Consolidate related actions |

---

## Notes for Planning Agents

1. **Six Action Categories:** Provide comprehensive workflow automation
2. **If-Action Conditions:** Support complex conditional logic (status, exit codes, output patterns, variables)
3. **Event Generation:** Dynamic workflow modification based on runtime conditions
4. **Variable Capture:** Pass data between jobs without manual coding
5. **Post-Job Automation:** Status-driven actions enable responsive workflows
6. **Multiple Triggers:** Before/during/after execution enables comprehensive control
7. **Notification Channels:** Multiple destinations for different alert priorities
8. **Integration Points:** Actions modify prerequisites, events, and variables dynamically
9. **Conditional Flow Control:** Branch workflows based on job outcomes
10. **Output Handling:** Manage job output automatically (copy, move, delete, print)

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | Job Actions |
| **Action Categories** | 6 primary types |
| **Execution Points** | Before, during, after job execution |
| **If-Action Conditions** | 7+ condition types |
| **Response Types** | 8+ response types |
| **Notification Channels** | 5+ destinations |
| **Variable Capture** | From job output (string extraction) |
| **Event Modification** | Dynamic add/delete events |
| **Output Operations** | Copy, move, delete, print |
| **Scheduling Override** | Ignore scheduling criteria option |
| **Rerun Support** | Automatic job rerun with retries |
