# Control-M Calendars - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Calendars.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Calendar definitions, scheduling integration, and date rule reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Three calendar types (Regular/Periodic/RBC); four RBC rule types; confirmation calendars; eight exception policies; Shift By −62..+62 days; Keep-Active; activity periods; 180-day retention; z/OS naming (8 uppercase).
- **SYNTHESIZED:** Worked examples, design/maintenance Best Practices, Notes for Planning Agents, Vendor Attributes table, the two-plane framing as presented here.
- **AUTHORITATIVE [VERBATIM/GROUNDED]:** the "Authoritative Additions — Classic Help" section below, transcribed 2026-06-11 from product Help screenshots (`bmc-regular-calendar.png`, `bmc-periodic-calendar.png`, `bmc-rulebased-calendar.png`) — matches 9.0.21.300. **Where it conflicts with the SaaS-derived body, it wins.**

---

## ✅ Authoritative Additions — Classic Help (2026-06-11)

### Regular / Relative calendar (creation & constraints)

- Created in **Tools domain → Planning → Calendars → New → Regular Calendar**.
- **Calendar Name:** distributed systems ≤ **30 characters**; Mainframe: **no lowercase, ≤ 8 characters, no white space**.
- **Control-M Server selection:** a specific server or **All** (all servers, distributed **and** mainframe — name must satisfy validation criteria for **both** systems).
- **Alias** field (Mainframe only).
- **Relative calendar (z/OS only):** schedules the closest scheduled date in the calendar relative to marked dates — `+` = run **after** the scheduled date, `-` = run **before**; relative calendars can be combined via the **IOABLCAL** utility (z/OS User Guide).
- **Day selection:** pick days directly, or use **Recurrence View Mode**: select **Month days** and/or **Week days**, then **Apply on** = the **years** the recurrence applies to. ⚠️ *Calendars are defined against explicit years — a projection can only extend as far as the calendar's year coverage.*
- **Check in** required to make a calendar available for scheduling.
- **Synchronization (Server = All):** Synchronization Status table lists servers + sync state; calendar syncs via the Definitions database. With **No Synchronization**, push explicitly via **Upload** / **Force Upload** (Force = same, but overrides changes).

### Periodic calendar (creation & constraints)

- A pre-defined calendar based on user-defined **periods**: periods may be **non-consecutive, of varying length, and overlapping**; **no single period can exceed 255 days**.
- **Period identifiers: `A–Z`, `1–9`** — select a period identifier, then mark its days (directly or via Recurrence/Apply-on-years); repeat per period.
- Same naming constraints as Regular (≤30 distributed; mainframe ≤8, no lowercase/whitespace); same Check-in and synchronization/upload mechanics.

### Specific Rule-based calendar scheduling (RBC combination semantics)

How RBC lists combine per entity — **this is the resolution logic for determining order dates**:

| Entity | Scheduling behavior |
|---|---|
| **Job in a regular folder** | Scheduled per its **individual scheduling criteria**; may also inherit from Control-M RBCs. Lists: **Rule-based Calendars List** (include — schedules per selected Control-M RBCs) + **Excluded RBC List** (selected Control-M RBCs whose dates are excluded). |
| **Job in a SMART folder** | Scheduled according to **AND or OR relationship with the parent SMART folder**. May schedule per the parent RBC. Lists: **RBC List** = selected **Folder RBCs**; **Excluded RBC List** = Control-M RBCs that **exclude the order dates**. |
| **Sub-folder in a SMART folder** | Scheduled per the **parent RBC**, or via its own **RBC List** (Folder RBCs) + **Excluded RBC List** (Control-M RBCs excluding order dates). |
| **SMART folder itself** | Scheduled per **Folder RBCs** defined for it or **Control-M RBCs** selected. Lists: **Rule-based Calendar List** (include) + **Excluded Rule-based Calendar List** (exclude order dates). |

Key distinctions: **Folder RBCs** (defined on the SMART folder) vs **Control-M RBCs** (server-level); **include lists schedule dates, exclude lists remove order dates**; the **job↔parent AND/OR relationship** governs how job criteria combine with the SMART folder's.

---

## Calendar Definition and Purpose

Control-M calendars are "user-defined timetables, which enable you to apply scheduling limitations to one or more job and SMART folder definitions."

**Key Characteristic:** Calendars provide a flexible mechanism to define complex scheduling rules and apply them consistently across multiple jobs and folders without modifying individual definitions.

**Primary Use Cases:**
- Define working day patterns
- Handle holidays and special dates
- Apply complex scheduling rules to job groups
- Shift execution dates based on calendar criteria
- Manage multi-region or multi-timezone schedules

---

## Calendar Types

Control-M supports three primary calendar types:

### 1. Regular Calendar
- **Purpose:** Schedules jobs on specific month days and weekdays within a defined year
- **Basis:** Standard calendar months and years
- **Patterns:** Select specific dates with recurrence rules
- **Use Case:** Simple, month-based scheduling patterns (e.g., run on 15th of each month)
- **Configuration:** Month/year ranges with day selections
- **Flexibility:** Moderate (month-centric)

### 2. Periodic Calendar
- **Purpose:** Organize scheduling around custom time periods rather than standard months
- **Period Types:** Weeks, months, quarters, or multi-year spans
- **Basis:** Custom period definitions (not standard calendar)
- **Use Case:** Fiscal periods, project cycles, or non-standard cycles
- **Configuration:** Custom period definitions with day selections
- **Flexibility:** High (period-centric)

### 3. Rule-Based Calendar (RBC)
- **Purpose:** Apply complex scheduling criteria using rules that cannot be expressed as absolute dates
- **Flexibility:** Highest (rule-driven)
- **Use Case:** Complex patterns, conditional scheduling, multi-criteria rules
- **Configuration:** Rules rather than static dates
- **Capability:** Combine multiple criteria types

---

## Calendar Rules and Date Definitions

### Regular and Periodic Calendars

Both types support recurring date patterns:

| Feature | Details |
|---------|---------|
| **Date Selection** | Specific dates selected within defined ranges |
| **Recurrence Rules** | Applied across month/year ranges |
| **Month Days** | Particular days of the month (1-31) |
| **Weekdays** | Specific days of week (MON-SUN) |
| **Year Range** | Define start and end years for pattern |
| **Month Range** | Restrict to specific months if needed |
| **Pattern** | Repeating pattern across defined period |

### Rule-Based Calendar (RBC) Rules

RBCs offer four rule types for complex scheduling:

#### 1. Specific Dates
- **Basis:** Independent of calendar year
- **Cycle:** Up to 12-month cycles
- **Purpose:** Define exact dates that recur (e.g., specific date each year)
- **Use Case:** Annual events, fiscal dates, specific anniversaries

#### 2. Weekdays
- **Target:** Specific weekdays (MON, TUE, WED, etc.)
- **Scope Options:** 
  - Any week (every occurrence)
  - Specific week within month (1st, 2nd, 3rd, 4th, last)
  - Multiple options combined
- **Use Case:** "First Monday of each month", "Last Friday"
- **Example:** Last business day of month, 3rd Wednesday

#### 3. Month Days
- **Target:** Specific dates within each month
- **Scope:** All months or selected months
- **Examples:** 15th of each month, specific dates
- **Use Case:** Recurring dates independent of weekday

#### 4. Advanced Rules
- **Combination:** Combines months, weekdays, and month days
- **Complexity:** Create complex multi-criteria rules
- **Logic:** AND/OR combinations possible
- **Use Case:** "First business day of Q1", "Every other week on Tuesday"

---

## Scheduling and Working Day Integration

### Confirmation Calendars (Filter Mechanism)

Rule-Based Calendars can reference existing calendars as confirmation filters:

**How It Works:**
```
Job scheduled via RBC
  ↓
RBC generates candidate date(s)
  ↓
Confirmation Calendar check:
  ├─ Date matches confirmation calendar
  │  → Use scheduled date
  └─ Date doesn't match
     → Apply Exception Policy
```

### Exception Policy Options

When a job scheduled via RBC doesn't align with confirmation calendar:

| Policy | Behavior | Use Case |
|--------|----------|----------|
| **Disable Execution** | Job does not execute on that date | Strict conformance required |
| **Shift Run Date** | Move execution to matching date | Delay acceptable |
| **Ignore Confirmation** | Execute regardless of calendar match | Calendar is advisory only |

### Shift By Parameter

- **Range:** -62 to +62 days
- **Purpose:** Adjust scheduled job runs without modifying underlying definitions
- **Direction:** 
  - Positive: Shift execution forward (later)
  - Negative: Shift execution backward (earlier)
- **Use Case:** Handle holidays, accommodate resource constraints, manage run sequence
- **Application:** Applied at execution time, definition unchanged

### Working Day Calculation

Calendars support working day calculations used in:
- **WCALC Function:** `%%$WCALC(start_date, num_days)` 
- **Purpose:** Calculate n working days from start date
- **Respects:** Calendar definitions (excludes non-working days)
- **Integration:** Works with Variables system

---

## Activity and Keep-Active Parameters

### Activity Period

- **Purpose:** Pause jobs for specified date ranges without altering job definitions
- **Mechanism:** Suspend execution for defined date windows
- **Scope:** Applied to individual jobs or job groups
- **Reversibility:** Temporary suspension, jobs resume after period ends
- **Use Case:** 
  - Seasonal maintenance windows
  - Planned downtime periods
  - Operational quiet times

### Keep-Active Setting

- **Purpose:** Determines how many additional days SMART folders await execution if originally scheduled runs fail
- **Scope:** SMART folder level
- **Behavior:** Extends execution window when primary run doesn't occur
- **Range:** Configurable day count (typically 1-30 days)
- **Use Case:**
  - Retry failed executions beyond original run date
  - Handle delayed dependencies
  - Provide execution flexibility
- **Integration:** Works with folder-level scheduling

---

## Calendar Scope and Synchronization

### Server Synchronization

Calendars synchronize with:
- **Single Control-M/Server:** Calendar applies to specific server
- **Distributed Systems:** Across multiple distributed Control-M/Servers
- **Mainframe Systems:** Synchronization to z/OS Control-M/Server
- **All Systems:** Can be published to all servers simultaneously

### Naming Constraints

Calendar names must meet validation criteria:

| Platform | Constraint | Example |
|----------|-----------|---------|
| **z/OS** | 8 uppercase characters maximum | `HOLIDAYS` (8 chars) |
| **Distributed** | Up to standard length limits | `Holiday_Calendar_2026` |
| **Case Sensitivity** | Platform-dependent | z/OS: uppercase only |

### Calendar Publication

- **Status:** Calendars appear in system with "Published" status once saved
- **Visibility:** Published calendars available for job/folder assignment
- **Scope:** Published status indicates ready for use
- **Availability:** Becomes immediately available for scheduling rules

---

## Calendar Integration with Scheduling

### How Jobs Use Calendars

Jobs reference calendars in scheduling definitions:

```
Job Scheduling
├── Base Schedule (day/time)
└── Calendar Rule
    ├── Regular Calendar → Specific month days/weekdays
    ├── Periodic Calendar → Custom periods
    └── Rule-Based Calendar → Complex rules
```

### Calendar and SMART Folder Scheduling

SMART folders can have calendar-based scheduling:
- **Folder-Level Calendar:** Applied to all contained jobs
- **Job-Level Override:** Individual jobs can override with different calendar
- **Inheritance:** Jobs inherit folder calendar unless overridden
- **Interaction:** Calendar criteria combined with folder scheduling

### Interaction with Prerequisites

Calendars determine **when** job can run (scheduling plane):
- **Scheduling Plane:** Calendar determines candidate dates
- **Prerequisite Plane:** Prerequisites determine if job starts when date arrives
- **Execution Decision:** Both must align for job execution
  ```
  Calendar date matches ✓
      AND
  Scheduling criteria met ✓
      AND
  Prerequisites satisfied (events, resources) ✓
      ↓
  Job Executes
  ```

---

## Calendar Types Comparison

| Aspect | Regular | Periodic | Rule-Based |
|--------|---------|----------|-----------|
| **Basis** | Standard months/years | Custom periods | Rules (any criteria) |
| **Complexity** | Low | Medium | High |
| **Configuration** | Date selection | Period definition | Rule definition |
| **Flexibility** | Low (month-bound) | Medium (period-bound) | High (rule-driven) |
| **Use Case** | Simple patterns | Fiscal periods | Complex patterns |
| **Rule Types Supported** | Single (dates) | Single (period dates) | Four types |
| **Confirmation Filter** | Limited | Limited | ✓ Yes |
| **Exception Policy** | ✗ | ✗ | ✓ Yes |
| **Shift By Parameter** | ✗ | ✗ | ✓ Yes |

---

## Advanced Calendar Features

### Confirmation Filtering

Rule-Based Calendars can confirm dates against another calendar:

**Workflow:**
1. RBC generates schedule date(s)
2. Check if date matches confirmation calendar
3. If no match: Apply Exception Policy
4. Result: Final scheduled execution date

**Use Case:** "Schedule using Q1 rules, but only if date is a working day per company calendar"

### Activity Periods (Blackout Dates)

Temporarily exclude date ranges without modifying definitions:

**Configuration:**
- Start date of blackout period
- End date of blackout period
- Jobs automatically skip dates in range
- Definitions unchanged; suspension is temporary

**Use Case:**
- System maintenance windows
- Planned downtime
- Operational maintenance periods

### Shift By Offset

Automatically adjust execution dates:

**Example:**
- Job normally runs on 15th
- Shift By = +2 (if 15th is not working day)
- Job runs on 17th instead
- Definition remains "15th"

**Benefits:**
- Handle holidays automatically
- Distribute load without modifying schedules
- Manage run sequences dynamically

---

## Calendar System Variables

Calendars integrate with the Variables system:

### Working Day Function

**%%$WCALC(start_date, num_days)**
- Calculates working days using calendar definitions
- Respects defined working/non-working days
- Returns resulting date
- Example: `%%$WCALC(%%DATE, 5)` → Date 5 working days from now

### Calendar Availability in Jobs

- Job can reference calendar in scheduling criteria
- Calendar definitions become available at job execution
- WCALC function uses calendar to calculate working days

---

## Best Practices

### Calendar Design

1. **Organizational Alignment**
   - Create calendars matching business structure
   - Use separate calendars for different organizational units
   - Name calendars descriptively (CALENDAR_DESCRIPTION_YEAR)

2. **Scope Appropriately**
   - Server-specific calendars for local scheduling
   - Shared calendars for cross-server operations
   - Master calendars for organization-wide dates

3. **Maintenance Strategy**
   - Update calendars annually or as business changes
   - Maintain separate calendars for special periods
   - Archive old calendar definitions
   - Version control calendar changes

4. **Documentation**
   - Document calendar purpose and scope
   - Record special date inclusions/exclusions
   - Document business rules embedded in calendar
   - Share calendar dictionary with team

### Using Calendars Effectively

1. **Rule-Based Calendars**
   - Use for complex, difficult-to-express patterns
   - Prefer RBCs for conditional scheduling
   - Document RBC rules clearly
   - Test RBC rule combinations

2. **Confirmation Filters**
   - Use confirmation to enforce business rules
   - Test exception policy behavior
   - Document why confirmation is needed
   - Monitor exception policy decisions

3. **Shift By Parameter**
   - Use to handle holidays automatically
   - Test shift calculations before deployment
   - Document shift logic
   - Monitor actual vs. scheduled dates

4. **Activity Periods**
   - Plan maintenance windows in advance
   - Use for planned downtime only
   - Document blackout periods
   - Communicate to job owners

### Performance Considerations

1. **Calendar Evaluation**
   - Complex RBCs evaluated at job execution time
   - Multiple rules increase evaluation time
   - Test performance with large rule sets
   - Consider consolidating similar rules

2. **Server Synchronization**
   - Synchronize calendars before deployment
   - Allow time for calendar propagation
   - Verify calendar availability on all servers
   - Monitor synchronization status

---

## Integration with Control-M Architecture

### Calendars in Scheduling Hierarchy
```
Control-M System
├── Global/Server Calendars
│   ├── Company Holiday Calendar
│   ├── Fiscal Period Calendar
│   └── Working Day Calendar
│
└── Job/Folder Scheduling
    ├── SMART Folder
    │   ├── Calendar: FISCAL_2026
    │   └── Keep-Active: 7 days
    │
    └── Job
        ├── Calendar: FISCAL_2026 (inherited)
        ├── Base Schedule: Day 15
        └── Shift By: +2 (if non-working)
```

### Interaction with Other Components

| Component | Interaction |
|-----------|-------------|
| **Scheduling** | Calendar defines execution dates |
| **Prerequisites** | Calendar provides execution window; prerequisites determine start |
| **Events** | Calendar-determined date combines with event prerequisites |
| **Variables** | %%$WCALC function uses calendar for working day calc |
| **Actions** | Actions can reference calendar-derived dates |
| **SMART Folders** | Folder-level calendar inherited by jobs |

---

## Notes for Planning Agents

1. **Three-Tier Calendar System:** Regular (simple), Periodic (custom periods), RBC (complex rules)
2. **Rule Types:** 4 RBC rule types enable expression of complex scheduling patterns
3. **Confirmation Filtering:** RBCs can validate against other calendars with exception policies
4. **Dynamic Shifting:** Shift By parameter enables automatic date adjustment
5. **Activity Periods:** Temporary blackout mechanism without modifying definitions
6. **Server Synchronization:** Calendars propagate across Control-M infrastructure
7. **Integration Points:** Works with Variables (WCALC), Scheduling, Prerequisites, Events
8. **Naming Constraints:** Platform-dependent (z/OS: 8 uppercase chars max)
9. **Keep-Active:** SMART folder parameter extends execution window on failure
10. **Two-Plane Execution:** Calendar (scheduling plane) + Prerequisites (execution plane)

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | Calendar Management & Scheduling |
| **Calendar Types** | Regular, Periodic, Rule-Based |
| **RBC Rule Types** | 4 (Specific Dates, Weekdays, Month Days, Advanced) |
| **Shift By Range** | -62 to +62 days |
| **Confirmation Filtering** | RBCs only |
| **Exception Policies** | Disable, Shift, Ignore |
| **Activity Period** | Blackout/suspension mechanism |
| **Platform Support** | Distributed and mainframe (z/OS) |
| **Naming (z/OS)** | 8 uppercase characters max |
| **Server Sync** | Single or multi-server |
| **Integration** | Variables (WCALC), Scheduling, Prerequisites |
