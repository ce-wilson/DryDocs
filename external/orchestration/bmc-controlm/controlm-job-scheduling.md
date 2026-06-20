# Control-M Job Scheduling - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Job_scheduling.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Job scheduling types, frequency patterns, calendar integration, and temporal execution control reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Hierarchical levels (SMART folder → Sub-folder → Job); six scheduling types; cyclic/interval/specific-times patterns; From/To windows, Must End, time zones, tolerance; eight confirmation exception policies; Shift By −62..+62; max-rerun ranges (0–99 / 0–9,999 z/OS cyclic / 0–255 z/OS regular); Keep Active (0–98 or indefinite); two-plane (Scheduling + Prerequisites) model.
- **SYNTHESIZED:** Inheritance/override narrative framing, Notes for Planning Agents, Vendor Attributes table.

---

## Scheduling Definition and Hierarchical Levels

Control-M enables scheduling at three hierarchical levels:
- **SMART folders** (inherited by children)
- **Sub-folders** (inherit from parent, can override)
- **Individual jobs** (inherit or override parent)

---

## Scheduling Types

**Options:**
- **Every Day**: Daily execution
- **None**: Manual execution only
- **Specific Dates**: User-selected dates
- **Use Parent Schedule**: Inherit parent folder calendars
- **Advanced**: Rule-based calendars with complex criteria
- **Free Space on PDS**: z/OS-specific (dataset availability)

---

## Run Frequency and Patterns

### Interval-Based Execution

"The next time that the job runs is determined by the **Start**, **End**, or **Target** time of the current job run, rounded down to the minute, plus the specified interval."

**Types:**
- Regular intervals (measured from Start/End/Target time)
- Sequence-based intervals (varying gaps)
- Specific times (designated hours/minutes daily)

---

## Date and Time-Based Scheduling

| Constraint | Purpose | Notes |
|-----------|---------|-------|
| **From/To Time Windows** | Earliest execution and latest start window | Establishes execution boundaries |
| **Must End (z/OS)** | Completion deadline enforcement | Platform-specific |
| **Time Zone** | Global scheduling across regions | Timezone-aware execution |
| **Tolerance** | Buffer time for "At Specific Times" reruns | Handles clock drift |

---

## Calendar Integration

### Calendar Application

**Calendars Control:**
- Which dates jobs can run
- Exception handling for holidays/special dates
- Multi-date patterns and rules

### Rule-Based Calendars (RBCs)

RBCs enable flexible scheduling through:
- Complex criteria expressions
- Holiday and exception handling
- Multi-pattern rule combinations

### Confirmation Calendars

"Automate scheduled jobs and SMART folders to account for holidays and other scheduling exceptions."

**Mechanism:**
- Filter RBC dates against regular/periodic calendars
- Apply exception policies on mismatches
- Eight exception handling options

---

## Advanced Scheduling Patterns

Jobs execute on:

| Pattern Type | Details |
|-------------|---------|
| **Specific Weekdays** | Including targeted weeks within months (1st-5th, last) |
| **Month Days** | Including "last working day" calculations (L1, L2, etc.) |
| **Specific Months** | Selective monthly scheduling |
| **Combinations** | Multiple constraints simultaneously (weekday + month + calendar) |

---

## Scheduling Overrides and Exceptions

### Exception Policies

**Eight Options:**
1. Disable runs entirely
2. Shift to next confirmed working day
3. Shift to previous confirmed working day
4. Ignore confirmation calendar
5. Use alternative date selection
6. Combination shift patterns
7. Extended window handling
8. Custom logic rules

### Shift By Parameter

- **Range:** −62 to +62 days
- **Purpose:** Adjust scheduled dates without modifying base schedules
- **Use Case:** Holiday accommodation, resource balancing

---

## Constraint and Limits

### Maximum Reruns

| Platform | Maximum |
|----------|---------|
| **Standard** | 0–99 |
| **z/OS Cyclic** | 0–9,999 |
| **z/OS Regular** | 0–255 |

### Keep Active Parameter

- **Purpose:** Extend execution eligibility post-deadline
- **Range:** 0–98 additional days or indefinitely
- **Use Case:** Catch missed executions from server restarts

---

## Inheritance Mechanisms

### Scheduling Inheritance Options

**Three Approaches:**
1. **All Parent Calendars**: Inherit all parent folder rules
2. **Select from Parent**: Pick specific parent calendars
3. **Exclude Parameters**: Override parent with exclusion calendars

### Inheritance Flow

```
SMART Folder Scheduling
  ↓
Sub-folder (Inherit or Override)
  ↓
Job (Inherit or Override)
```

---

## Prerequisite Interaction

### Two-Plane Execution

```
Scheduling Plane (When):
├─ Calendar-determined dates
└─ Time windows (From/To)

Prerequisite Plane (What conditions):
├─ Events
├─ Resources
└─ Job prerequisites
```

Both planes must be satisfied for job execution.

### Time Window Logic

| Scenario | Behavior |
|----------|----------|
| **No Start Time** | Execute when prerequisites met (no wait) |
| **Start Time Specified** | Use time window as earliest/latest boundary |
| **Prerequisites Not Met** | Wait within time window |
| **Time Window Closed** | Job waits for next scheduled window |

---

## Additional Scheduling Features

### Retroactive Runs

- Resume missed executions when servers restart
- Catch up on delayed processing
- Maintain schedule continuity on recovery

### Activity Periods

- Restrict execution windows without modifying base schedules
- Temporary suspension mechanism
- Used for maintenance windows, blackout dates

### SAC (Scheduling Adjustment Criteria)

- Adjusts logical dates during product migrations
- Handles version transitions
- Date mapping and rule adjustments

### Cyclic Execution

- Multiple runs within single business days
- Defined intervals
- Intra-day scheduling patterns

---

## Integration with Control-M Architecture

### With Calendars

- **Regular/Periodic Calendars**: Define execution date patterns
- **Rule-Based Calendars**: Complex criteria and exceptions
- **Confirmation Calendars**: Filter and validate scheduled dates

### With Prerequisites

- Scheduling determines **when** job can run
- Prerequisites determine **if** job starts when time arrives
- Both must be satisfied

### With Events

- Scheduled jobs generate events
- Events can trigger other jobs
- Scheduling independent of event-based triggering

### With Variables

- Scheduled date variables available (%%DATE, %%WDAY, etc.)
- Schedule-based variable substitution
- Time-based conditional logic

### With Folders and Hierarchy

- Folder-level scheduling inherited by jobs
- Sub-folder override capabilities
- Hierarchical schedule propagation

---

## Scheduling Design Patterns

### Daily Processing

```
Schedule: Every Day
Time: 02:00 AM
Prerequisites: None
Result: Job runs daily at 2 AM
```

### Weekly Pattern

```
Schedule: Specific Weekdays
Days: Monday-Friday
Time: 06:00 AM
Result: Weekday morning execution
```

### Month-End Processing

```
Schedule: Advanced (Last Working Day)
Calculation: Last business day of month
Prerequisites: Previous jobs complete
Result: Month-end job execution
```

### Holiday-Aware Scheduling

```
Schedule: RBC (Advanced rules)
Confirmation Calendar: Company Holiday Calendar
Exception Policy: Shift to next working day
Result: Automatic holiday avoidance
```

---

## Best Practices

1. **Use SMART Folder Scheduling**
   - Define common schedules at folder level
   - Jobs inherit unless overridden
   - Reduces configuration duplication

2. **Leverage Calendars**
   - Regular calendars for simple patterns
   - RBCs for complex rules
   - Confirmation calendars for holiday handling

3. **Time Zone Awareness**
   - Specify time zones for global execution
   - Account for regional differences
   - Test across time zone boundaries

4. **Combine Scheduling with Prerequisites**
   - Scheduling = when job can run
   - Prerequisites = conditions for execution
   - Use both for robust workflows

5. **Activity Periods for Maintenance**
   - Use instead of modifying base schedules
   - Temporary blackout mechanism
   - Preserves original schedule definition

---

## Notes for Planning Agents

1. **Three-Level Hierarchy:** Scheduling flows SMART folder → Sub-folder → Job
2. **Calendar Integration:** RBCs provide complex pattern support
3. **Exception Handling:** 8 policies for confirmation calendar mismatches
4. **Time Windows:** From/To create execution boundaries
5. **Inheritance:** Jobs can inherit, select, or exclude parent calendars
6. **Shift By:** −62 to +62 day adjustment parameter
7. **Two-Plane Model:** Scheduling + Prerequisites must both be satisfied
8. **Retroactive Runs:** Catches up missed executions on restart
9. **Keep Active:** Extends execution eligibility past deadline
10. **Cyclic Execution:** Multiple intra-day runs supported

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | Job Scheduling |
| **Hierarchy Levels** | 3 (Folder, Sub-folder, Job) |
| **Schedule Types** | 6 primary types + advanced |
| **Max Reruns** | Varies by platform (99–9,999) |
| **Shift By Range** | −62 to +62 days |
| **Keep Active** | 0–98 days or indefinite |
| **Exception Policies** | 8 options |
| **Calendar Support** | Regular, Periodic, Rule-Based, Confirmation |
| **Time Zone Support** | Yes (global scheduling) |
| **Retroactive Runs** | Yes (post-restart catch-up) |
