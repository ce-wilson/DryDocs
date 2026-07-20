# Control-M Variables - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Variables.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Variable definition, scope, substitution, and parameterization reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **AUTHORITATIVE [VERBATIM/GROUNDED]:** the "Authoritative Corrections" section below — transcribed from classic Parameter Reference Help screenshots (2026-06-11), matches 9.0.21.300.
- **SYNTHESIZED / SaaS-derived (lower confidence):** the rest of this file (types/scope narrative, function library, ORDER_SYSTEM_VARIABLES_VALIDATION, simulation, examples, Notes, Vendor Attributes). Where it conflicts with the authoritative section, **the authoritative section wins.**

⚠️ **Hazard (reconciled):** Earlier this file said "folder-level variables NOT available to job scripts" as absolute. The classic reference refines this: a SMART-Folder variable **can** be resolved in a job's script when **`VARIABLE_INC_SEC = Global`** on the Control-M/Server. Treat the "not available" claim as the *default*, not an invariant.

---

## ✅ Authoritative Corrections — Classic Parameter Reference (2026-06-11)

Transcribed **[VERBATIM]/[GROUNDED]** from product Help screenshots (`bmc-screnshot-variables.png`, `bmc-screnshot--user-defined-variables.png`) — the classic Parameter Reference matching **9.0.21.300**. **These supersede any conflicting figures elsewhere in this file** (SaaS-derived/synthesized).

### Corrections to earlier content
| Field | Earlier (SaaS/synth) | Authoritative (classic) |
|---|---|---|
| Variable **value** length | 214 | **1–4000** (z/OS 1–66) |
| Variable **name** length | 1–38 (everywhere) | **Name 1–40** param (z/OS 1–66); **user-defined name ≤38** |
| Number of variable **types** | 3 | **4** (adds Job Submission variables) |
| Variable-list special var | `POOLSYM` | **`%%LIBMEMSYM`** |

### Verified facts
- **Prefix:** all variables use `%%`. **Name cannot start with a numeric digit.** Invalid Characters (parameter): **None**. Usage: Optional.
- **Length:** Name **1–40**, Value **1–4000** (z/OS: both **1–66**).
- **Alternate names:** EM Utilities `VARIABLE` · Report `VARIABLE` · Server Utilities `-variable` · EM API `variable`.
- **Non-resolution prefix:** `%%#` (Linux/UNIX) or `%%%%#` (Windows) marks a variable/function that should **not** be resolved; the actual name minus `#` is output. E.g. `Do Notification Variable %%#PARM1 is greater than 100` outputs `Variable %%PARM1 is greater than 100`.

**Four variable types:**
1. **Job Submission variables** — pass parameters to a job / set the job's working parameters.
2. **System variables** — auto-assigned from system info at submission (e.g. `%%DATE` = current system date).
3. **User-defined variables** — defined for inclusion in job processing parameters.
4. **Variable lists** — the special variable **`%%LIBMEMSYM`** points to a file containing assignment statements applied to a job; one list reusable across many job definitions.

**Scope & duplicate-name rule:** multiple variables (different scopes) can share a name; the **narrowest scope wins**. *Exception:* when distributed Control-M/Server → Control-M/Agent, the narrowest-scope value may not be the one the Agent uses. **`VARIABLE_INC_SEC`** (Control-M/Server) governs whether duplicate variables from different scopes are distributed to agents.

**Resolution order** (which value is used when a variable is referenced in a job processing definition):
1. **Local** variable (for the job) — if it exists, its value is used.
2. Else if the job is in a **SMART Folder** — use the variable defined in the SMART Folder definition. *(A system variable like `%%ORDERID` assigned to a SMART Folder resolves to the **job's** run ID, not the SMART Folder's.)*
3. Else search for a **Global** variable. *(`VARIABLE_INC_SEC` must be **Global** to resolve a variable used in a job's **script** where it is defined in the SMART Folder.)*
4. If no definition is found → resolves to the reserved word **`CTMERR`**.

**User-defined variables (verified):**
- Created via the **Variable Assignment** parameter or the **Do Variable** parameter.
- Four Variable-Type drop-down choices: **Local**, **Global**, **Named Pool**, **Smart Folder** (Smart Folder appears only when the job is in a SMART Folder; can also be defined for all jobs in a SMART Folder via the folder properties pane).
- **Named Pool** syntax: `%%\\<named_pool>\<variable_name>`. A local variable can serve as the pool name (pass a pre-defined pool name at order time). Example: Local `localvar`=`val`; Named Pool `namepool`, Pool Name `%%localvar`, Value `namval` → pool name resolves to `val`.
- **Names & values are case-sensitive** (`%%TEST` ≠ `%%Test`). **z/OS: variable names must be UPPERCASE.**
- **Forbidden** in user-defined names (plus blanks): `< > [ ] { } ( ) = ; \` ~ | : ? . + - * / & ^ # @ ! , " '`
- **Application-specific prefixes** (may not appear in variable values): `%%` + app abbreviation + `-`, e.g. `%%SAPR3-` (SAP), `%%OAP-` (Oracle).
- **Global** variables pass info between jobs on a Control-M/Server (job A sets `%%\A`=Yes; job B on another agent resets to No). Created/modified via the **`ctmvar`** utility. View all Global & Named Pool variables in Control-M/EM → Tools domain → **Shared Variables**.

---

## Variable Definition and Types

Control-M supports **four** primary variable categories (corrected per Authoritative Corrections above — the SaaS-derived text below originally listed three, omitting Job Submission variables):

### 0. Job Submission Variables
- **Purpose:** Pass parameters to a job or set the job's working parameters at submission
- **Type:** First-class variable type per the classic Parameter Reference

### 1. User-Defined Variables
- **Creation:** Created by users with custom names and values
- **Scope:** Can be local, global, or pool-based
- **Definition Location:** Within job or folder definitions
- **Flexibility:** Fully customizable names and values
- **Purpose:** Enable dynamic parameterization of job attributes

### 2. System Variables
- **Creation:** Pre-defined by Control-M with static names
- **Values:** Automatically assigned by Control-M
- **Categories:**
  - Job general information
  - Job scheduling details
  - Environment information
  - Action-related data
- **Purpose:** Provide access to runtime context and metadata
- **Override:** Can be restricted by administrators via `ORDER_SYSTEM_VARIABLES_VALIDATION` config

### 3. List Variables (a.k.a. Variable lists)
- **Definition:** Special variable **`%%LIBMEMSYM`** points to a file containing a list of assignment statements applied to a job *(corrected — earlier said "POOLSYM", which is not the documented special variable)*
- **Purpose:** Define one or more lists of assignment statements reusable across many job processing definitions
- **Capacity:** "~1,024 variables" was SaaS/synth — **unverified** against the classic reference; do not rely on
- **Use Case:** Manage large collections of related variables

---

## Variable Scope and Inheritance

Variables operate within four distinct scopes:

### Scope Levels and Syntax

| Scope | Syntax | Accessibility | Use Case |
|-------|--------|----------------|----------|
| **Local** | `%%VariableName` | Referenced only by defining job/folder | Job-specific values |
| **Global** | `%%\VariableName` | Any job on same Control-M/Server | Cross-job sharing |
| **Named Pool** | `%%\\PoolName` | Jobs referencing the same pool | Related variable collections |
| **SMART Folder** | `%%VariableName` (in folder context) | Jobs and sub-folders within SMART folder | Inherited from parent |

### Scope Hierarchy
```
System Variables (Global to Control-M)
├── Global Variables (%%\VAR) - All jobs on server
├── Pool Variables (%%\\POOLNAME) - Jobs in named pool
└── Local/Folder Variables (%%VAR) - Job or folder scope
    └── Sub-folder Inheritance - Jobs inherit from SMART folder
```

### Inheritance Characteristics
- **Folder-Level Variables:** Available to jobs and sub-folders within SMART folder
- **Sub-folder Inheritance:** Sub-folders inherit parent SMART folder variables
- **Job Override:** Jobs can override folder-level variables with local definitions
- **Scope Prefix:** Determines resolution order and accessibility

---

## Variable Substitution and Resolution

### Resolution Timing
- **Execution Trigger:** Variables resolve when jobs begin or complete execution
- **Definition Preservation:** Original job definition remains unchanged after resolution
- **One-Time Resolution:** Each job execution performs fresh variable substitution

### Variable Simulation
- **Purpose:** View original and resolved variable values without job execution
- **Use Case:** Validate variable expressions before deployment
- **Benefits:**
  - Test complex expressions safely
  - Verify substitution logic
  - Identify variable reference errors
  - Preview dynamic values

### Resolution Process
```
Job Triggered
  ↓
Control-M Resolves Variables:
  1. Check local scope (%%VAR)
  2. Check folder scope (if in SMART folder)
  3. Check global scope (%%\VAR)
  4. Check system variables (%%JOBNAME, etc.)
  5. Apply functions if present
  ↓
Job Executes with Resolved Values
  ↓
Original Definition Unchanged
```

---

## System Variables Reference

### Job General Variables
Provide metadata about the job itself:

| Variable | Purpose | Example |
|----------|---------|---------|
| `%%JOBNAME` | Current job name | "DailyReport" |
| `%%OWNER` | Job owner/creator | "admin" |
| `%%APPLIC` | Job application | "PAYROLL" |
| `%%ORDERID` | Job order ID | "12345678" |
| `%%RUNCOUNT` | Job execution count | "3" |

### Job Scheduling Variables
Provide scheduling context:

| Variable | Purpose | Format |
|----------|---------|--------|
| `%%ODATE` | Job order date | YYYYMMDD |
| `%%NEXT` | Next execution date | YYYYMMDD |
| `%%ODAY` | Order day of month | 01-31 |
| `%%OMONTH` | Order month | 01-12 |
| `%%OYEAR` | Order year | YYYY |
| `%%OWDAY` | Order day of week | 1-7 (MON-SUN) |

### Environment Variables
Provide runtime environment information:

| Variable | Purpose | Format |
|----------|---------|--------|
| `%%DATE` | Current date | YYYYMMDD |
| `%%TIME` | Current time | HHMMSS |
| `%%MONTH` | Current month | 01-12 |
| `%%DAY` | Current day | 01-31 |
| `%%YEAR` | Current year | YYYY |
| `%%WDAY` | Current weekday | 1-7 (MON-SUN) |

### Action Variables
Provide job execution status information:

| Variable | Purpose | Use Case |
|----------|---------|----------|
| `%%COMPSTAT` | Job completion status | Post-execution actions |
| `%%AVG_TIME` | Average job execution time | Performance monitoring |
| `%%JOBID` | Unique job identifier | Job tracking |
| `%%NODEID` | Execution node ID | Multi-node environments |

---

## Variable Naming and Constraints

### User-Defined Variable Rules

| Constraint | Details |
|-----------|---------|
| **Length** | **User-defined variable name ≤ 38 chars**; the general **Variable parameter Name is 1–40** (z/OS 1–66) — see Authoritative Corrections |
| **Case Sensitivity** | Case-sensitive (MyVar ≠ myvar); **z/OS names must be UPPERCASE** |
| **Starting Character** | Cannot begin with a numeric digit |
| **Allowed Characters** | Alphanumeric; blanks not allowed |
| **Prohibited Characters** | `< > [ ] { } ( ) = ; ` ~ | : ? . + - * / & ^ # @ ! , " '` |

### Variable Value Constraints

| Constraint | Details |
|-----------|---------|
| **Length** | **1–4000 characters** (z/OS: 1–66) — *corrected from earlier "214"* |
| **Content** | Text and variables/functions; Invalid Characters (parameter): None |
| **Manipulations** | Support concatenations, functions, and expressions |
| **Dynamic Values** | Can include system variables and calculated values |

---

## Variable Usage in Jobs and Folders

### Usage Locations
Variables can be referenced in:

| Location | Purpose | Example |
|----------|---------|---------|
| **Command Lines** | Parameterize job commands | `/bin/myscript %%INPUTFILE` |
| **File Names** | Dynamic file paths and names | `/data/%%APPLIC/%%DATE.txt` |
| **Notification Messages** | Include runtime data in alerts | "Job %%JOBNAME completed at %%TIME" |
| **If-Action Conditions** | Condition execution on variable values | `IF %%COMPSTAT == OK` |
| **Folder/Job Attributes** | Parameterize any field | Application, description, priority |

### Variable Concatenation
Variables can be combined to create composite values:
```
%%APPLIC_%%DATE_%%TIME  →  PAYROLL_20260611_163000
```

### Nested Substitution
System variables can be used within user-defined variables:
```
User defines: %%LOGFILE = /logs/%%JOBNAME_%%DATE.log
At runtime resolves to: /logs/MyJob_20260611.log
```

---

## Variable Priority and Override Mechanisms

### Variable Resolution Priority (Order of Lookup)
1. **Job-Level Variables** — Highest priority; override folder and global
2. **Folder-Level Variables** (in SMART folder) — Override global
3. **Global Variables** — Available to all jobs on server
4. **System Variables** — Pre-defined by Control-M
5. **Named Pools** — Referenced by pool name

### Administrator Control: ORDER_SYSTEM_VARIABLES_VALIDATION

When `ORDER_SYSTEM_VARIABLES_VALIDATION = Y` in config file:

**Blocked Operations:**
- User override of critical system variables
- Variable redefinition in folder/job definitions
- Set Variable if-action overrides
- Variable capture operations

**Purpose:** Protect critical system variables from accidental or unauthorized modification

**Impact:**
- Ensures system variable integrity
- Prevents job misconfiguration
- Enforces organizational policy
- Maintains audit trail consistency

---

## Variable Functions

Control-M provides specialized functions for variable manipulation:

### Date Calculation Function

**%%CALCDATE**
- **Purpose:** "Adds or subtracts a specified number of days from a specified date"
- **Use Case:** Dynamic date calculations in job parameters
- **Example:** `%%CALCDATE(%%DATE, -7)` → Date 7 days ago
- **Syntax:** `%%CALCDATE(base_date, offset_days)`

### Environment Variable Function

**%%GETENV**
- **Purpose:** Retrieve OS environment variable values
- **Use Case:** Access system environment settings
- **Example:** `%%GETENV(PATH)` → System PATH variable
- **Syntax:** `%%GETENV(env_var_name)`

### String Extraction Function

**%%SUBSTR**
- **Purpose:** Extract substring values from a source string
- **Use Case:** Parse portions of variable values
- **Example:** `%%SUBSTR(%%JOBNAME, 1, 5)` → First 5 chars
- **Syntax:** `%%SUBSTR(source, start_pos, length)`

### Working Days Function

**%%$WCALC**
- **Purpose:** Calculate working days using calendar definitions
- **Use Case:** Business day calculations excluding weekends/holidays
- **Example:** `%%$WCALC(%%DATE, 5)` → Date 5 working days from now
- **Syntax:** `%%$WCALC(start_date, num_days)`
- **Note:** Respects configured calendar definitions

### Whitespace Function

**%%BLANK**
- **Purpose:** Insert whitespace characters
- **Use Case:** Format output with spaces
- **Example:** `Value%%BLANK(5)Name` → "Value     Name"
- **Syntax:** `%%BLANK(num_spaces)`

---

## Variable Scope Examples

### Local Variable Scope
```
SMART Folder: PAYROLL
├── Job1: %%EMPID = "12345" (local to Job1)
└── Job2: Cannot access %%EMPID from Job1
```

### Folder-Level Scope
```
SMART Folder: PAYROLL
  Variables: %%DEPT = "Finance", %%PERIOD = "2026-Q2"
├── Job1: Accesses %%DEPT and %%PERIOD
├── Job2: Accesses %%DEPT and %%PERIOD
└── Sub-folder: REPORTS
    └── Job3: Inherits %%DEPT and %%PERIOD
```

### Global Scope
```
%%\BASEPATH = "/data/shared"

All jobs on Control-M/Server can reference:
  %%\BASEPATH → "/data/shared"
```

### Pool Variables
```
Pool: LOCATIONS
Contains: LOC_US = "NewYork", LOC_EU = "London", LOC_ASIA = "Tokyo"

Jobs referencing %%\\LOCATIONS can access:
  %%LOC_US, %%LOC_EU, %%LOC_ASIA
```

---

## Best Practices

### Variable Design
1. **Use Descriptive Names**
   - Clear purpose indicated by name
   - Consistent naming convention
   - Document purpose in job/folder description

2. **Scope Appropriately**
   - Local for job-specific values
   - Folder-level for shared group values
   - Global for widely-used constants
   - Pools for large variable collections

3. **Leverage System Variables**
   - Use `%%DATE`, `%%TIME` for consistency
   - Use `%%JOBNAME` for identification
   - Use `%%COMPSTAT` for status-dependent actions
   - Reduces need for custom variables

### Variable Validation
1. **Test Before Deployment**
   - Use variable simulation to validate expressions
   - Preview resolved values with actual data
   - Identify reference errors early
   - Test with edge cases (dates, special characters)

2. **Document Variables**
   - Document custom variable purpose
   - Note any functions or concatenations
   - Record dependency relationships
   - Share documentation with team

### Security and Governance
1. **Protect Sensitive Variables**
   - Use global variables for sensitive data (stored securely)
   - Limit access via named pools
   - Monitor variable usage via audit logs
   - Prevent override with `ORDER_SYSTEM_VARIABLES_VALIDATION`

2. **Maintain Version Control**
   - Track variable changes in version control
   - Document evolution of variable definitions
   - Review variable updates before deployment
   - Archive old variable definitions

### Performance Considerations
1. **Minimize Function Calls**
   - Pre-calculate values when possible
   - Avoid excessive nested functions
   - Cache frequently-used calculated values
   - Monitor variable resolution performance

2. **Use Pools Efficiently**
   - Organize related variables in pools
   - Limit pool sizes to relevant variables
   - Document pool purposes and contents
   - Review and clean pools periodically

---

## Integration with Control-M Architecture

### Variables in Folder Hierarchy
```
SMART Folder (Variables inherited by children)
├── Folder-level variables (%%VAR)
├── Sub-folder (Inherits folder variables)
│   └── Jobs (Inherit folder + sub-folder variables + locals)
└── Jobs (Inherit folder variables + locals)
```

### Variables with Events
- Event names can use system variables: `%%JOBNAME-TO-%%NEXTJOB`
- Variables resolved at event creation/delivery time
- Dynamic event naming supports parameterized workflows

### Variables with Actions
- If-action conditions test variable values: `IF %%COMPSTAT == OK`
- Set Variable action creates/modifies variables
- Post-execution actions can pass data via variables

### Variables with Scheduling
- Variables in scheduling criteria enable dynamic scheduling
- `%%DATE`, `%%WDAY` support conditional execution
- Variables calculated at job execution time

---

## Notes for Planning Agents

1. **Three-Tier Variable System:** User-defined, System, and List variables provide flexibility
2. **Four-Level Scoping:** Local, Folder, Global, Pool enable appropriate data sharing
3. **Dynamic Resolution:** Variables resolve at execution time, enabling parameterized workflows
4. **Simulation Support:** Can preview resolved values without execution
5. **Function Library:** Specialized functions for dates, strings, environment, calculations
6. **Priority & Override:** Job-level variables override folder/global; admins can lock system variables
7. **Wide Integration:** Variables used across jobs, folders, events, actions, scheduling
8. **Inheritance Pattern:** Folder variables inherit to jobs and sub-folders (consistent with hierarchy)

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | Variable Management & Substitution |
| **Variable Types** | **4**: Job Submission, System, User-defined, Variable lists (`%%LIBMEMSYM`) |
| **Scope Levels** | Local, Global, Named Pool, Smart Folder |
| **Max Length** | Name 1–40 (user-defined name ≤38); Value **1–4000** (z/OS both 1–66) |
| **Unresolved variable** | Resolves to reserved word `CTMERR` |
| **Functions Provided** | CALCDATE, GETENV, SUBSTR, WCALC, BLANK |
| **Resolution Timing** | Job execution (begin/complete) |
| **Simulation** | Yes (preview without execution) |
| **Administrator Control** | ORDER_SYSTEM_VARIABLES_VALIDATION config |
