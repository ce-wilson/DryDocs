# Control-M ctmdefine Utility - Technical Reference

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Utilities/ctmdefine.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** ctmdefine command syntax, parameters, and detailed API reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** "API for adding job processing definitions…" purpose; five task types (JOB, EXTERNAL, DETACHED, COMMAND, DUMMY); keywords case-insensitive / values case-sensitive; 999-char post-decode line limit; input_file method; the documented parameter set (-FOLDER, -JOBNAME, -TASKTYPE, -APPLICATION/-SUB_APPLICATION, scheduling, calendar, -INCOND/-OUTCOND, -VARIABLE with apostrophe-for-`$` rule, action -ON/-DO, -CAPTURE INTO, -CREATED_BY, -quiet).
- **SYNTHESIZED:** Bash wrapper patterns, environment-specific/batch examples, Best Practices, Vendor Attributes table.

⚠️ **Hazard:** Some parameter *value enums* (e.g. CYCLIC_TYPE MINUTELY|HOURLY|DAILY|WEEKLY) are illustrative — confirm exact accepted values against source. Return codes were noted as not specified.

---

## ctmdefine Definition and Purpose

ctmdefine utility is "an API for adding job processing definitions to Control-M/Server database folders."

**Scope:** Convert job scheduling information from other systems; programmatic job definition creation equivalent to UI-based definition

---

## Command Syntax

### Basic Invocation

```
ctmdefine -FOLDER <Name> -JOBNAME <Name> -TASKTYPE <TYPE> [optional parameters]
```

### Input File Method

```
ctmdefine -input_file <fullPathFileName>
```

### Constraints

- **Case Sensitivity:** Keywords case-insensitive; parameter values case-sensitive
- **Line Limit:** 999 characters post-decoding
- **Quoted Strings:** Required for values containing spaces
- **Parameter Order:** Insignificant (except for -ON/-DO dependencies)

---

## Supported Object Types

### Folder Structures

| Type | Details |
|------|---------|
| **Regular Folders** | Standard job containers |
| **SMART Folders** | Created automatically if non-existent |
| **Sub-folders** | Nested pathway support |

### Task Types

| Type | Purpose |
|------|---------|
| **JOB** | Standard job (requires -file_name, -file_path) |
| **EXTERNAL** | External task reference |
| **DETACHED** | Detached execution (requires -file_name, -file_path) |
| **COMMAND** | Command-line execution (requires -cmdline) |
| **DUMMY** | Placeholder job (for testing/structure) |

---

## Essential Parameters

### Required Parameters

| Parameter | Purpose | Format |
|-----------|---------|--------|
| **-FOLDER** | Target folder name | String |
| **-JOBNAME** | Job identifier | String (1-64 chars) |
| **-TASKTYPE** | Job classification | JOB\|EXTERNAL\|DETACHED\|COMMAND\|DUMMY |

### Application Organization

| Parameter | Purpose | Details |
|-----------|---------|---------|
| **-APPLICATION** | Logical grouping name | Groups related jobs |
| **-SUB_APPLICATION** | Application categorization | Hierarchical organization |

### Job Type-Specific Requirements

| Task Type | Required Parameters |
|-----------|-------------------|
| **JOB/DETACHED** | -file_name, -file_path |
| **COMMAND** | -cmdline |
| **Folder Definition** | -RBC (rule-based calendar parameters) |

---

## Scheduling Parameters

### Cyclic Job Configuration

| Parameter | Purpose | Options |
|-----------|---------|---------|
| **-CYCLIC** | Enable cyclic execution | ON\|OFF |
| **-CYCLIC_TYPE** | Cycle type | MINUTELY\|HOURLY\|DAILY\|WEEKLY |
| **-INTERVAL** | Execution interval | Numeric (minutes/hours/days) |

### Date and Time Specifications

| Parameter | Purpose | Format |
|-----------|---------|--------|
| **-DAYS** | Specific days | DAY1,DAY2,... |
| **-WEEKDAYS** | Day of week | MON\|TUE\|WED\|THU\|FRI\|SAT\|SUN |
| **-MONTH** | Specific months | Repeated -month parameters for multiple |
| **-DATE** | Specific date | YYYYMMDD format |

### Calendar Integration

| Parameter | Purpose | Type |
|-----------|---------|------|
| **-DAYSCAL** | Day calendar | Regular calendar name |
| **-WEEKCAL** | Week calendar | Regular calendar name |
| **-CONFCAL** | Confirmation calendar | RBC confirmation filter |

---

## Advanced Parameters

### Job Dependencies

| Parameter | Purpose | Syntax |
|-----------|---------|--------|
| **-INCOND** | Input condition (prerequisite) | Event reference |
| **-OUTCOND** | Output condition (generated event) | Event definition |

### Variable Assignment

| Parameter | Purpose | Example |
|-----------|---------|---------|
| **-VARIABLE** | Define variable | -VARIABLE VAR_NAME=VALUE |

### Post-Processing Actions

| Parameter Set | Purpose | Format |
|---|---|---|
| **-ON / -DO** | Conditional action | -ON condition -DO action |
| **-OUTPUT** | Output handling | KEEP\|DELETE\|ARCHIVE |
| **-CONTROL** | Control file | File path specification |

### Notifications

| Parameter | Purpose | Destination |
|-----------|---------|-------------|
| **-SHOUT** | Alert notification | Alert system |
| **-DOMAIL** | Email notification | Email address(es) |

### Output Capture

| Parameter | Purpose | Details |
|-----------|---------|---------|
| **-CAPTURE INTO** | Capture output to variable | Variable name |

---

## Application-Specific Jobs

### Specialized Definitions

**Parameter:**
```
-appltype <SAP|OAP|...>
```

**Variable Support:**
- Application-specific variables via `-VARIABLE` parameter
- Vendor documentation parameters supported
- Allows vendor-specific configuration

**Example:**
```
ctmdefine -appltype SAP -VARIABLE SAP_VARIANT=STANDARD
```

---

## Complete Parameter Reference

### Foundation Parameters

```
-FOLDER <name>              # Folder name
-JOBNAME <name>             # Job name
-TASKTYPE <type>            # JOB|EXTERNAL|DETACHED|COMMAND|DUMMY
-APPLICATION <app>          # Application name
-SUB_APPLICATION <subapp>   # Sub-application name
```

### Execution Parameters

```
-file_path <path>           # Script/file path
-file_name <filename>       # Script/file name
-cmdline <command>          # Command line to execute
```

### Scheduling Parameters

```
-DAYS <days>               # Specific days
-WEEKDAYS <weekday>        # Day of week
-MONTH <month>             # Month (repeat for multiple)
-DATE <YYYYMMDD>           # Specific date
-CYCLIC <ON|OFF>           # Cyclic execution
-CYCLIC_TYPE <type>        # MINUTELY|HOURLY|DAILY|WEEKLY
-INTERVAL <number>         # Interval value
```

### Calendar Parameters

```
-DAYSCAL <calendar>        # Day calendar
-WEEKCAL <calendar>        # Week calendar
-CONFCAL <calendar>        # Confirmation calendar
```

### Dependency Parameters

```
-INCOND <event>            # Input condition (prerequisite)
-OUTCOND <event>           # Output condition (generates event)
-VARIABLE <var=value>      # Variable assignment
```

### Action Parameters

```
-ON <condition>            # Conditional action trigger
-DO <action>               # Action to perform
-OUTPUT <KEEP|DELETE|ARCHIVE>  # Output handling
-CONTROL <filepath>        # Control file path
-SHOUT <destination>       # Alert notification
-DOMAIL <email>            # Email notification
-CAPTURE INTO <variable>   # Capture output to variable
```

### System Parameters

```
-CREATED_BY <user>         # User creating definition
-quiet                      # Suppress information messages
-input_file <filepath>     # Input file method
```

---

## Usage Examples

### Example 1: Basic OS Job

```
ctmdefine -FOLDER production -JOBNAME daily_backup \
  -TASKTYPE JOB -APPLICATION operations \
  -file_path /opt/scripts -file_name backup.sh \
  -WEEKDAYS MON,TUE,WED,THU,FRI -DAYS 2,15
```

### Example 2: Cyclic Job with Notifications

```
ctmdefine -FOLDER processing -JOBNAME hourly_processor \
  -TASKTYPE JOB -APPLICATION batch \
  -file_path /scripts -file_name process.sh \
  -CYCLIC ON -CYCLIC_TYPE HOURLY -INTERVAL 1 \
  -OUTCOND PROCESS_COMPLETE \
  -DOMAIL ops@company.com
```

### Example 3: Command Job with Dependencies

```
ctmdefine -FOLDER data_pipeline -JOBNAME validate_data \
  -TASKTYPE COMMAND -APPLICATION data \
  -cmdline "/usr/bin/validate --input /data/raw" \
  -INCOND DATA_EXTRACTED \
  -ON STATUS_OK -DO ADD_EVENT "DATA_VALIDATED"
```

### Example 4: Input File Method

```
ctmdefine -input_file /etc/control-m/job_definitions.cfg
```

---

## Integration with Control-M Components

### Security Integration

**Parameter:** `-CREATED_BY <user>`
- Associates user with job definition
- Integrates with Control-M/Server security mechanisms
- Enables audit tracking

### Calendar Integration

- Rule-based calendars (RBC) for complex scheduling
- Confirmation calendars for exception handling
- Day/week calendar selection

### Event System Integration

- Input conditions (prerequisites via events)
- Output conditions (events generated by job)
- Conditional actions based on status
- Event-based job sequencing

### Notification Integration

- Alert notifications via -SHOUT
- Email notifications via -DOMAIL
- Output capture for downstream processing

---

## Parameter Syntax Rules

### Key Rules

1. **Case Rules**
   - Keywords: case-insensitive
   - Parameter values: case-sensitive
   
2. **Spacing & Quoting**
   - Quoted strings required for spaces
   - Multiple parameters per line allowed
   - No parameter order dependency (except -ON/-DO)

3. **Multi-Value Parameters**
   - Month specifications: repeat -month for multiple
   - Weekday specifications: comma-separated list
   - Multiple variables: repeat -VARIABLE parameter

4. **Character Limits**
   - Command line: 999 characters (post-decoding)
   - Job name: 1-64 characters
   - Folder name: 1-64 characters

---

## Error Handling

### Information Messages

- Suppressible via `-quiet` flag
- Provide feedback on successful definition
- Include validation warnings

**Note:** Explicit return codes not specified in source documentation. Recommend consulting Control-M Administrator documentation for detailed error codes.

---

## Advanced Patterns

### Pattern 1: Environment-Specific Job Definition

```bash
#!/bin/bash
ENV=${1:-dev}
FOLDER="jobs_${ENV}"
FILE_PATH="/opt/${ENV}/scripts"

ctmdefine -FOLDER "$FOLDER" -JOBNAME daily_job \
  -TASKTYPE JOB -file_path "$FILE_PATH" \
  -file_name job.sh
```

### Pattern 2: Batch Job Import

```bash
for job_config in /etc/jobs/*.cfg; do
  ctmdefine -input_file "$job_config"
done
```

### Pattern 3: Conditional Action Chains

```
ctmdefine ... -ON EXIT_CODE_0 -DO ADD_EVENT SUCCESS
ctmdefine ... -ON EXIT_CODE_1 -DO ADD_EVENT FAILURE
ctmdefine ... -ON EXIT_CODE_1 -DO SEND_MAIL admin@company.com
```

---

## Best Practices

1. **Parameterization**
   - Use variables for values that change
   - Reference -VARIABLE for job inputs
   - Support environment-specific configuration

2. **Error Handling**
   - Always capture output (-CAPTURE INTO)
   - Define on-error conditions (-ON)
   - Set up notifications for failures

3. **Documentation**
   - Use meaningful job/folder names
   - Document job purposes in -APPLICATION
   - Include -CREATED_BY for audit trail

4. **Validation**
   - Test definitions in dev environment
   - Verify calendar integration
   - Validate event prerequisites

---

## Notes for Planning Agents

1. **Command-Line API:** ctmdefine provides programmatic job definition
2. **Flexible Task Types:** Support JOB, EXTERNAL, DETACHED, COMMAND, DUMMY
3. **Rich Scheduling:** Cyclic, date-based, calendar-integrated
4. **Event Integration:** Input/output conditions for sequencing
5. **Notifications:** Built-in alert and email support
6. **Variable Support:** Custom variables and application-specific configuration
7. **Conditional Actions:** ON/DO syntax for status-driven automation
8. **Output Capture:** Direct integration with variable system
9. **Input File Support:** Batch definitions from configuration files
10. **Enterprise Integration:** User tracking, calendar integration, security mechanisms

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Utility** | ctmdefine |
| **Purpose** | API for job definition |
| **Task Types** | JOB, EXTERNAL, DETACHED, COMMAND, DUMMY |
| **Folder Types** | Regular, SMART, Sub-folders |
| **Scheduling** | Cyclic, date-based, calendar-integrated |
| **Parameters** | 30+ configuration options |
| **Event Support** | Input/output conditions |
| **Variables** | Custom variables, application-specific |
| **Notifications** | Alert, Email |
| **Output Capture** | TO variable integration |
| **Input Methods** | Command-line, input file |
| **Character Limit** | 999 characters (post-decode) |
