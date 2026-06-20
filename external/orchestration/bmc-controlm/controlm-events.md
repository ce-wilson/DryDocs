# Control-M Events - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Events.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Event-based job dependency and workflow orchestration reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Standard vs Global event types; wait-for-event attributes (Name 1–255 chars, Run Date, Delete, AND/OR relationship); drag-and-drop creation; wait-for-event inheritance conditions; same-Control-M/Server constraint; no-braces / identical-operator constraints.
- **SYNTHESIZED:** The "[Source]-TO-[Target]" naming convention framing, %%JOBNAME-TO / @HHMMSS examples, sequential/parallel/convergence workflow diagrams, Notes for Planning Agents, Vendor Attributes table.

---

## Event Definition and Purpose

Events serve as dependencies between jobs or SMART folders on Control-M/Servers. According to BMC documentation:

> "An event is a type of prerequisite, along with scheduling criteria and resource requirements."

**Key Characteristic:** Events enable successor entities to begin execution after predecessors complete, provided all other prerequisites are met. Events are the primary mechanism for defining job workflow sequences and cross-folder dependencies.

---

## Event Types

### Standard Events
- **Scope:** Dependencies within a single Control-M/Server
- **Connection:** Connect predecessor and successor jobs
- **Visualization:** Visual event lines with arrowheads showing direction
- **Use Case:** Intra-server job sequencing and workflow definition
- **Scope:** Single server, same job location

### Global Events
- **Scope:** Cross-server dependencies between jobs or SMART folders
- **Servers:** Connect different Control-M/Servers
- **Requirement:** Global event prefixes to define operational boundaries
- **Use Case:** Multi-server job orchestration and distributed workflows
- **Prefix:** Required for server identification and routing

---

## Event Processing and Triggering

### Event Creation Mechanism
- **Interface:** Drag-and-drop mechanism in Control-M workspace
- **Interaction:**
  1. Hover over predecessor job
  2. Arrowhead appears indicating event source
  3. Drag arrowhead to target successor job
  4. System automatically generates event line

### Event Trigger Conditions
Events trigger successor execution when:
1. **Predecessor completes successfully** — Job execution finishes without error
2. **All other prerequisites satisfied** — Scheduling, resource requirements, other events met
3. **Run date criteria met** — Event timing aligns with successor's run date

### Execution Flow
```
Predecessor Job Completes
  ↓
Event Generated/Delivered
  ↓
Check Successor Prerequisites (Scheduling, Resources, Other Events)
  ↓
All Prerequisites Met?
  ├─ YES → Successor Job Starts
  └─ NO  → Wait for remaining prerequisites
```

---

## Prerequisites and Conditions

### Events as Prerequisites
Events are one of three prerequisite types in Control-M:
1. **Scheduling Criteria** — Time and calendar-based conditions
2. **Resource Requirements** — Resource availability and locks
3. **Events** — Job completion dependencies from predecessor jobs

### Wait-for-Event Inheritance
The system has a special feature: "wait-for-event inheritance preserves workflow order when jobs are deleted, automatically transferring event dependencies to successor jobs under specific conditions."

**When Inheritance Occurs:**
- Predecessor job is deleted
- Successor job needs to maintain workflow continuity
- Conditions are met for automatic dependency transfer

**Inheritance Requirements:**
- All wait-for-events use identical Boolean operators (AND or OR)
- No complex expressions using braces `{}`
- All jobs reside on the same Control-M/Server

---

## Event Attributes and Properties

### Wait-for-Event Attributes (Successor Perspective)
These are configured on the job/folder that is waiting for an event:

| Attribute | Details | Constraints |
|-----------|---------|-----------|
| **Name** | Event identifier | 1–255 characters, case-sensitive, no apostrophes or parentheses |
| **Run Date** | When event is expected | Options: Current, Any, Previous, Next, Specific, or Offset dates |
| **Delete** | Post-execution removal | Determines if event persists after execution |
| **Relationship** | Multiple event logic | AND/OR operators for combining multiple wait-for-events |
| **Boolean Operators** | Event combination logic | AND: all events required, OR: any event sufficient |

### Event Attributes (Predecessor Perspective)
These are configured on the job/folder that generates an event:

| Attribute | Details | Notes |
|-----------|---------|-------|
| **Name** | Event identifier | Formatted as "[Source Job]-TO-[Target Job]" convention |
| **Run Date** | Event timing | When event is added or deleted relative to job execution |
| **Add** | Event creation trigger | Whether event is created after job completion |
| **Delete** | Event removal trigger | Whether event is removed after job completion |

### Dynamic Event Properties
Events support runtime substitution:
- **System Variables:** `%%<Variable_Name>` for parameterized event names
- **Timestamps:** `@HHMMSS` for time-based event naming during execution
- **Use Case:** Dynamically identify events during multi-instance job runs

---

## Event Management Capabilities

The Events tool in Control-M enables:

| Capability | Purpose |
|-----------|---------|
| **Add Events** | Create new job dependencies and workflow sequences |
| **Delete Events** | Remove completed or unnecessary dependencies |
| **Monitor Active Events** | Track current event status in workflows |
| **Search Events** | Locate specific event information by date or name |
| **Paste Jobs with Events** | Preserve event connections when copying job sequences |
| **Define Global Event Prefixes** | Configure multi-server event routing and boundaries |
| **Edit Event Properties** | Modify names, run dates, add/delete behavior |
| **Visual Event Navigation** | Follow event lines in workspace to trace workflows |

---

## Integration with Control-M Architecture

### Relationship to Folders and Jobs
- **Folder Level:** Events connect SMART folders to other SMART folders
- **Job Level:** Events connect individual jobs within folders
- **Mixed Level:** Events can connect folders to jobs or jobs to folders
- **Inheritance:** Events respect folder hierarchy and parameter inheritance

### Relationship to Prerequisites
Events are one component of a three-part prerequisite system:
```
Job Execution Prerequisite Check:
├── Scheduling Criteria (When to run)
├── Resource Requirements (Resource availability)
└── Events (Predecessor completion)
```

All three must be satisfied for job execution to begin.

### Relationship to Actions
Events can be:
- **Generated by Actions** — Post-job-execution actions that add/delete events
- **Used in Actions** — Conditional actions based on event status
- **Monitored by Actions** — Actions triggered by event delivery

---

## Constraints and Best Practices

### Technical Constraints

| Constraint | Impact | Workaround |
|-----------|--------|-----------|
| **Special Characters in Names** | No apostrophes or parentheses in event names | Use underscores or hyphens instead |
| **Case Sensitivity** | Event names are case-sensitive | Maintain consistent naming conventions |
| **Wait-for-Event Inheritance Limits** | Only works with AND/OR operators, no braces | Keep prerequisite logic simple |
| **Cross-Server Events** | Require global event prefix configuration | Must be explicitly enabled per server pair |
| **Complex Prerequisites** | Cannot use braces in wait-for-event inheritance | Use separate prerequisite conditions |

### Best Practices

1. **Naming Convention**
   - Use standardized naming: `[PREDECESSOR]-TO-[SUCCESSOR]`
   - Use descriptive names indicating workflow purpose
   - Avoid special characters (apostrophes, parentheses)
   - Keep names under 255 characters but descriptive

2. **Event Design**
   - Use events for sequential job dependencies
   - Use scheduling criteria for time-based conditions
   - Use resources for shared resource management
   - Combine appropriately for complex workflows

3. **Wait-for-Event Logic**
   - Keep Boolean operators consistent (all AND or all OR)
   - Avoid complex nested conditions with braces
   - Document event dependencies in job descriptions
   - Test wait-for-event inheritance conditions

4. **Global Events**
   - Only use for true cross-server dependencies
   - Configure global event prefixes properly
   - Monitor global event delivery latency
   - Test failover scenarios for multi-server setups

5. **Variable Substitution**
   - Use system variables (`%%VAR_NAME`) for parameterized events
   - Use timestamps (`@HHMMSS`) for time-sensitive event naming
   - Document variable substitution in job definitions
   - Test variable resolution with actual data

6. **Performance Considerations**
   - Large numbers of events can impact performance
   - Monitor event processing in Control-M dashboards
   - Archive completed event history periodically
   - Use global events judiciously for cross-server ops

---

## Event Workflow Examples

### Simple Sequential Workflow
```
Job_A completes
  → Generates event "JOB_A-TO-JOB_B"
  → Job_B (waiting for "JOB_A-TO-JOB_B") 
  → Begins if scheduling + resources OK
```

### Parallel Convergence with AND
```
Job_A completes → Event_A
Job_B completes → Event_B
Job_C waits for: Event_A AND Event_B
  → Job_C starts only when both A and B complete
```

### Conditional Path with OR
```
Job_A completes → Event_A
Job_B completes → Event_B
Job_C waits for: Event_A OR Event_B
  → Job_C starts when either A or B completes
```

---

## Integration with Scheduling and Prerequisites

### Execution Order Determination
1. **Scheduling Criteria** determines time window
2. **Resource Requirements** checks availability
3. **Event Prerequisites** checks predecessor completion
4. **Only if all three satisfied** → Job execution begins

### Relationship to SMART Folder Scheduling
- Events operate independently of folder scheduling
- Jobs can override folder scheduling with event prerequisites
- Events respect folder-level prerequisites
- Inheritance chain: Folder prerequisites + Job prerequisites + Events

---

## Notes for Planning Agents

1. **Event as Dependency Model:** Events are the primary mechanism for expressing job sequencing
2. **Standard vs. Global:** Two-tier event system (single-server and cross-server)
3. **Drag-and-Drop Interface:** Events created visually, not through configuration
4. **Prerequisite Trinity:** Events work alongside scheduling and resources to control execution
5. **Wait-for-Event Inheritance:** Preserves workflow when jobs deleted (limited conditions)
6. **Boolean Logic:** AND/OR operators for complex prerequisites
7. **Dynamic Properties:** Variables and timestamps support parameterized workflows
8. **Workflow Visualization:** Event lines show job dependencies visually

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | Event-Based Job Dependencies |
| **Scope** | Single-server and cross-server |
| **Creation Method** | Drag-and-drop visual interface |
| **Naming** | 1–255 characters, case-sensitive |
| **Boolean Logic** | AND/OR operators |
| **Variable Support** | System variables and timestamps |
| **Inheritance** | Wait-for-event inheritance (limited conditions) |
