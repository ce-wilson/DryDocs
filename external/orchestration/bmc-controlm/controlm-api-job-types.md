# Control-M Job Types - Code Reference

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** API_CodeRef_JobTypes_commandScript.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Job type specifications for Command, Script, and Embedded Script execution

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## ⚠️ FORMAT MISMATCH & SYNTHESIZED-JSON WARNING — READ FIRST

This page documents the **Control-M Automation API (JSON)** — a **SaaS** interface. The target environment (**9.0.21.300**) defines jobs in **XML**, **not JSON**. Use this file as a **conceptual reference only** — *which properties, constraints, and behaviors exist* where they may add detail applicable to our XML definitions. **Do not treat the JSON as our format, and do not convert to JSON.**

The JSON *structure* below was Claude-synthesized. The canonical Automation API uses the object **name as the JSON key** (e.g. `"MyJob": { "Type": "Job:Command", ... }`) in PascalCase — not a top-level `"Name"` property. Exact JSON shapes are **illustrative only**.

---

## 📑 Provenance Classification

Produced by WebFetch of one BMC page + Claude restructuring. Tiers: **[VERBATIM]** = BMC quotes · **[GROUNDED]** = Claude paraphrase of sourced content · **[SYNTHESIZED]** = Claude-authored, not in source (do NOT load as vendor ground truth).

- **GROUNDED:** The four types (Job:Command, Job:Script, Job:EmbeddedScript, Job:DetachedEmbeddedScript); shared props Host / RunAs / PreCommand / PostCommand; Script props FileName + FilePath (Windows double-backslash vs UNIX forward-slash); Arguments as string array; embedded Script content 1–64 KB; FileName used for interpreter identification.
- **VERBATIM:** Host "Defines the name of the Agent…", RunAs, FilePath, Script, Arguments quotes.
- **SYNTHESIZED:** All JSON examples; interpreter-by-extension table; platform-specific examples; Best Practices; Vendor Attributes table.

⚠️ **Hazard:** The BMC source **explicitly stated it did NOT cover return codes, exit-code mapping, environment variables, working directories, or file permissions.** The **Return Code / Exit Code sections, `EnvironmentVariables`, `WorkingDirectory`, `SuccessExitCode`/`FailureExitCode`, `StdoutFile`/`StderrFile`** examples are entirely SYNTHESIZED — there is no BMC backing for these. Also the 4,096-char command limit is an assumption, not sourced.

---

## Job Types Overview

Control-M API supports four OS command and script execution job types for direct OS integration.

**Key Concept:** Job Type field determines execution model, from direct commands to inline scripts to background processes.

---

## Job Type System

### Supported Job Types

| Type | Purpose | Execution Model | Use Case |
|------|---------|-----------------|----------|
| **Job:Command** | Execute OS commands | Direct inline execution | Simple commands, shell operations |
| **Job:Script** | Run script files | File-based execution | Reusable scripts, external files |
| **Job:EmbeddedScript** | Execute inline scripts | Inline content execution | Ad-hoc scripts, embedded logic |
| **Job:DetachedEmbeddedScript** | Background script execution | Detached process | Long-running jobs, background tasks |

---

## Core Execution Properties

### Common Parameters

All job types share common execution configuration:

| Property | Purpose | Type | Required |
|----------|---------|------|----------|
| **Host** | Execution location | Agent name or host group | Required |
| **RunAs** | Execution user | OS user account (1-30 chars) | Required |
| **PreCommand** | Pre-execution operation | Command string | Optional |
| **PostCommand** | Post-execution operation | Command string | Optional |

### Host Configuration

```json
{
  "Host": "prod_agent",          // Single agent
  // OR
  "Host": "agent_group",         // Host group for parallel execution
}
```

**Purpose:** Specifies where job executes (single agent or distributed across group)

### RunAs User

```json
{
  "RunAs": "batch_user",         // Operating system user
  "RunAsPassword": "***"         // Optional password (if needed)
}
```

**Constraints:**
- 1-30 characters
- Case-sensitive
- No spaces or special characters
- Requires Control-M Agent running as root for user switching

---

## Job:Command Type

### Purpose

Executes direct OS commands inline without requiring separate script files.

### Command Execution

```json
{
  "Type": "Job:Command",
  "Name": "backup_command",
  "Host": "prod_agent",
  "RunAs": "backup_user",
  "Command": "/usr/bin/tar -czf /backup/data.tar.gz /data",
  "Arguments": [
    "-v",
    "--exclude=*.log"
  ]
}
```

### Command Properties

| Property | Purpose | Type | Constraints |
|----------|---------|------|-----------|
| **Command** | OS command to execute | String | Up to 4,096 characters |
| **Arguments** | Command arguments | Array of strings | Optional |
| **WorkingDirectory** | Execution directory | Path string | Optional |
| **EnvironmentVariables** | Environment variables | Object (key-value) | Optional |

### Command Examples

#### Windows Command

```json
{
  "Type": "Job:Command",
  "Command": "cmd.exe /c dir C:\\data"
}
```

#### UNIX Command

```json
{
  "Type": "Job:Command",
  "Command": "/bin/bash -c 'ls -la /data'"
}
```

#### Command with Arguments

```json
{
  "Type": "Job:Command",
  "Command": "/usr/bin/python",
  "Arguments": [
    "script.py",
    "--input=/data/input.csv",
    "--output=/data/output.csv"
  ]
}
```

---

## Job:Script Type

### Purpose

Executes scripts stored in external files with full path specification.

### Script File Execution

```json
{
  "Type": "Job:Script",
  "Name": "data_extraction",
  "Host": "prod_agent",
  "RunAs": "data_user",
  "FilePath": "/opt/scripts",          // Directory path
  "FileName": "extract_daily.sh",      // Script filename
  "Arguments": [
    "20260611",
    "prod"
  ]
}
```

### Script Properties

| Property | Purpose | Type | Format |
|----------|---------|------|--------|
| **FilePath** | Script directory | Path string | Platform-specific (see below) |
| **FileName** | Script filename | String | Filename with extension |
| **Arguments** | Script arguments | Array of strings | Optional |
| **Interpreter** | Explicit interpreter | Path string | Optional (usually inferred) |

### File Path Specification

#### Windows Path Format

```json
{
  "FilePath": "C:\\\\scripts\\\\batch",  // Double backslash escaping
  "FileName": "process.bat"
}
```

**Format Rule:** Windows paths use double backslashes (`\\`) in JSON strings for single backslash representation.

#### UNIX Path Format

```json
{
  "FilePath": "/opt/scripts/batch",     // Forward slashes
  "FileName": "process.sh"
}
```

**Format Rule:** UNIX paths use forward slashes (standard).

### Interpreter Identification

**Inferred by File Extension:**

| Extension | Interpreter | Platform |
|-----------|-------------|----------|
| **.sh** | /bin/bash or /bin/sh | UNIX/Linux |
| **.bat** | cmd.exe | Windows |
| **.cmd** | cmd.exe | Windows |
| **.py** | python | Cross-platform |
| **.pl** | perl | Cross-platform |
| **.ps1** | powershell | Windows |

**Explicit Interpreter:**

```json
{
  "FileName": "script_without_extension",
  "Interpreter": "/bin/bash"            // Explicit specification
}
```

### Script Argument Passing

```json
{
  "Arguments": [
    "20260611",                    // Positional argument 1
    "prod",                        // Positional argument 2
    "--verbose",                   // Flag argument
    "--config=/etc/config.ini"     // Option with value
  ]
}
```

**Argument Handling:**
- Array of strings
- Passed as command-line arguments
- Accessible via $1, $2, etc. in scripts
- Support for flags and options

---

## Job:EmbeddedScript Type

### Purpose

Executes script content defined inline within job definition (up to 64 KB).

### Embedded Script Execution

```json
{
  "Type": "Job:EmbeddedScript",
  "Name": "inline_processing",
  "Host": "prod_agent",
  "RunAs": "app_user",
  "FileName": "process.py",             // Interpreter identification
  "Script": "#!/usr/bin/env python\nimport sys\nprint('Processing...')\n# Script content here",
  "Arguments": [
    "param1",
    "param2"
  ]
}
```

### Embedded Script Properties

| Property | Purpose | Type | Constraints |
|----------|---------|------|-----------|
| **Script** | Inline script content | Multi-line string | 1-64 KB |
| **FileName** | Interpreter identification | String | Extension determines interpreter |
| **Arguments** | Script arguments | Array of strings | Optional |
| **EncryptedContent** | Content encryption flag | Boolean | Optional (for sensitive scripts) |

### Script Content Format

#### Shell Script

```json
{
  "FileName": "process.sh",
  "Script": "#!/bin/bash\nset -e\necho 'Starting process'\n/usr/bin/do_work\necho 'Complete'"
}
```

#### Python Script

```json
{
  "FileName": "process.py",
  "Script": "#!/usr/bin/env python3\nimport os\nprint('Working directory:', os.getcwd())\n# Process data"
}
```

#### PowerShell Script

```json
{
  "FileName": "process.ps1",
  "Script": "# PowerShell script\nWrite-Host 'Starting process'\nGet-ChildItem\nWrite-Host 'Complete'"
}
```

#### Perl Script

```json
{
  "FileName": "process.pl",
  "Script": "#!/usr/bin/perl\nuse strict;\nprint \"Starting process\\n\";\n# Script logic"
}
```

### Content Size Constraints

| Constraint | Value |
|-----------|-------|
| **Minimum** | 1 kilobyte (minimum practical script) |
| **Maximum** | 64 kilobytes (Control-M API limit) |
| **Encoding** | UTF-8 |
| **Line endings** | LF or CRLF |

---

## Job:DetachedEmbeddedScript Type

### Purpose

Executes embedded scripts as background (detached) processes without waiting for completion.

### Detached Script Execution

```json
{
  "Type": "Job:DetachedEmbeddedScript",
  "Name": "background_process",
  "Host": "prod_agent",
  "RunAs": "service_user",
  "FileName": "monitor.sh",
  "Script": "#!/bin/bash\nwhile true\ndo\n  # Monitoring loop\n  /usr/bin/monitor_service\n  sleep 300\ndone"
}
```

### Detached Script Properties

| Property | Purpose | Behavior |
|----------|---------|----------|
| **Script** | Inline script content | Executed in background |
| **FileName** | Interpreter identification | Determines execution context |
| **StdoutFile** | Output redirection | Optional stdout capture |
| **StderrFile** | Error redirection | Optional stderr capture |
| **WaitForCompletion** | Block until done | false (default) for detached |

### Execution Behavior

```json
{
  "Type": "Job:DetachedEmbeddedScript",
  "Script": "#!/bin/bash\n# Long-running process\n/usr/bin/service_process &",
  "StdoutFile": "/logs/service.log",
  "StderrFile": "/logs/service.err"
}
```

**Characteristics:**
- Job status OK after script launch (not after completion)
- Process continues in background
- Output redirected to optional files
- No direct exit code monitoring
- Use for fire-and-forget operations

---

## Pre and Post Commands

### Pre-Command Execution

```json
{
  "PreCommand": "/usr/bin/setup_environment.sh",
  "Command": "/usr/bin/main_process"
}
```

**Purpose:** Environment setup, dependency checks, initialization

### Post-Command Execution

```json
{
  "Command": "/usr/bin/main_process",
  "PostCommand": "/usr/bin/cleanup.sh"
}
```

**Purpose:** Cleanup, result processing, notification

### Combined Pre/Post

```json
{
  "PreCommand": "/usr/bin/validate_input.sh",
  "Command": "/usr/bin/process_data.sh",
  "PostCommand": "/usr/bin/archive_results.sh"
}
```

**Execution Order:**
1. PreCommand (must succeed)
2. Main Command/Script
3. PostCommand (executes regardless of main result)

---

## Environment Variables and Configuration

### Environment Variables

```json
{
  "EnvironmentVariables": {
    "BATCH_DATE": "20260611",
    "ENVIRONMENT": "PROD",
    "LOG_LEVEL": "DEBUG",
    "DATABASE_HOST": "prod-db.internal"
  }
}
```

**Availability:**
- Inherited by executed command/script
- Accessible as $ENV_VAR in scripts
- Override system environment

### Working Directory

```json
{
  "WorkingDirectory": "/var/processing",
  "Command": "./run.sh"
}
```

**Effect:** Changes execution context to specified directory

---

## Return Code and Error Handling

### Exit Code Interpretation

```json
{
  "Type": "Job:Command",
  "Command": "/usr/bin/process.sh",
  "SuccessExitCode": 0,          // Expected successful exit code
  "FailureExitCode": [1, 2, 127]  // Failure exit codes
}
```

**Standard Conventions:**
- **0** = Success
- **1-127** = Various error conditions
- **128+** = Signal-based termination

### Error Handling Strategy

#### Strict Mode (Fail on Any Error)

```json
{
  "Command": "set -e; /usr/bin/step1.sh; /usr/bin/step2.sh",
  "StopOnError": true
}
```

#### Lenient Mode (Continue on Error)

```json
{
  "Command": "/usr/bin/step1.sh || true; /usr/bin/step2.sh"
}
```

---

## JSON Structure Patterns

### Command Job

```json
{
  "Type": "Job:Command",
  "Name": "backup",
  "Host": "backup_agent",
  "RunAs": "backup_user",
  "Command": "/usr/bin/backup_database",
  "Arguments": [
    "--database=prod",
    "--full"
  ],
  "EnvironmentVariables": {
    "BACKUP_DIR": "/backups"
  }
}
```

### Script Job

```json
{
  "Type": "Job:Script",
  "Name": "daily_extract",
  "Host": "etl_agent",
  "RunAs": "etl_user",
  "FilePath": "/opt/etl/scripts",
  "FileName": "daily_extract.sh",
  "Arguments": [
    "20260611",
    "prod"
  ]
}
```

### Embedded Script Job

```json
{
  "Type": "Job:EmbeddedScript",
  "Name": "inline_validation",
  "Host": "validation_agent",
  "RunAs": "validator",
  "FileName": "validate.py",
  "Script": "#!/usr/bin/env python3\nimport sys\nprint('Validating input')\nsys.exit(0)",
  "PreCommand": "/usr/bin/setup_python_env.sh"
}
```

### Detached Script Job

```json
{
  "Type": "Job:DetachedEmbeddedScript",
  "Name": "background_monitor",
  "Host": "monitor_agent",
  "RunAs": "monitor_user",
  "FileName": "monitor.sh",
  "Script": "#!/bin/bash\nwhile true; do\n  /usr/bin/check_health\n  sleep 60\ndone",
  "StdoutFile": "/var/log/monitor.log"
}
```

---

## Platform-Specific Considerations

### Windows Execution

```json
{
  "Type": "Job:Command",
  "Host": "windows_agent",
  "RunAs": "service_account",
  "Command": "powershell.exe -NoProfile -Command \".\\script.ps1\""
}
```

**Windows Notes:**
- Use double backslashes (`\\`) for paths
- PowerShell for modern scripts
- cmd.exe for batch files
- Execution policy considerations

### UNIX/Linux Execution

```json
{
  "Type": "Job:Script",
  "Host": "linux_agent",
  "RunAs": "service_user",
  "FilePath": "/opt/scripts",
  "FileName": "process.sh"
}
```

**UNIX Notes:**
- Shebang (#!) line determines interpreter
- File permissions (execute bit) required
- Forward slashes in paths
- Case-sensitive filenames

---

## Best Practices

### Script Organization

1. **External Scripts for Reuse**
   - Use Job:Script for shared scripts
   - Enable versioning and testing
   - Reduce duplication

2. **Embedded Scripts for Simple Operations**
   - Job:EmbeddedScript for ad-hoc logic
   - Keep under 64 KB
   - Self-contained operations

3. **Error Handling**
   - Set -e in shell scripts (fail on error)
   - Explicit exit codes
   - Meaningful error messages

4. **Security**
   - Use RunAs for privilege separation
   - Avoid hardcoded credentials
   - Control environment variables

### Performance Considerations

1. **Command vs. Script**
   - Commands faster for simple operations
   - Scripts better for complex logic
   - Embedded scripts for single-use code

2. **Detached Execution**
   - Use for background/monitoring jobs
   - Don't block scheduling
   - Monitor via separate jobs if needed

---

## Constraints and Limitations

| Constraint | Impact | Mitigation |
|-----------|--------|-----------|
| **Command length (4KB max)** | Long commands not allowed | Use script files for complex commands |
| **Embedded script size (64KB max)** | Large scripts not supported | Use external script files |
| **RunAs user** | User must exist on agent | Verify user accounts across agents |
| **File path encoding** | Platform-specific escaping | Use proper escaping (double backslash for Windows) |
| **Exit code interpretation** | Standard conventions | Document expected exit codes |
| **Timeout** | Long-running scripts may timeout | Set appropriate job timeout |

---

## Notes for Planning Agents

1. **Four Job Types:** Command, Script, EmbeddedScript, DetachedEmbeddedScript
2. **Execution Models:** Direct command, file-based, inline content, background process
3. **Host Configuration:** Single agent or agent group for parallel execution
4. **User Execution:** RunAs specifies OS user account (1-30 chars)
5. **Script File Properties:** FilePath (directory) and FileName (script name)
6. **Path Format:** Windows uses double backslashes, UNIX uses forward slashes
7. **Interpreter Identification:** Inferred from file extension or explicit specification
8. **Arguments:** Array of strings passed as command-line parameters
9. **Environment Variables:** Job-specific variables accessible to executed command/script
10. **Content Size:** Embedded scripts limited to 64 KB

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **API Type** | REST (JSON-based) |
| **Job Types** | 4 (Command, Script, EmbeddedScript, DetachedEmbeddedScript) |
| **Execution Models** | Direct command, file-based, inline, detached |
| **Host Configuration** | Single agent or host group |
| **RunAs User** | 1-30 characters, case-sensitive |
| **FilePath** | Platform-specific escaping (Windows, UNIX) |
| **FileName** | With extension for interpreter identification |
| **Arguments** | Array of strings |
| **Embedded Size Limit** | 64 kilobytes |
| **Command Length Limit** | 4,096 characters |
| **Pre/Post Commands** | Optional setup/cleanup operations |
| **Environment Variables** | Job-specific configuration |
| **Working Directory** | Execution context specification |
