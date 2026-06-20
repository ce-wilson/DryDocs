# Control-M OS Job Parameters - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** OS_Job_parameters.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** OS job types, command/script execution, and parameter configuration reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Three OS execution types (Script, Command, Embedded Script); file path 1–255 chars and file name 1–64 chars (case-sensitive); command ≤512 chars (case-sensitivity by platform); embedded script ≤64,000 bytes with `#!` interpreter prefix; supported languages (Perl, Python, PowerShell, VBScript); Run As 1–30 chars; **"folder-level variables don't transfer to jobs — define at job level"** (load-bearing constraint).
- **SYNTHESIZED:** Examples, Notes for Planning Agents, Vendor Attributes table.

⚠️ **Hazard:** Return-code/exit-code handling and any environment-variable / working-directory examples are SYNTHESIZED — the OS-job source documents the constraint set above, not exit-code semantics.

---

## OS Job Definition and Purpose

OS jobs execute tasks on distributed systems (Windows, Unix/Linux). They provide the primary mechanism for running operating system commands and scripts as part of Control-M workflows.

**Scope:** Available on distributed Control-M systems (not mainframe)

---

## Job Execution Types

Control-M supports three execution types for OS jobs:

### 1. Script Execution

- **Purpose:** Run scripts from file system
- **Source:** Specified file path and filename
- **File Path:** 1-255 characters (directory location)
- **File Name:** 1-64 characters (script filename)
- **Case Sensitivity:** Both path and name are case-sensitive
- **Character Constraints:** Cannot contain spaces or special characters (backslashes, asterisks)
- **Interpreter:** Determined by file extension or "#!" prefix (for embedded scripts)
- **Use Case:** Execute pre-written scripts stored on target system

### 2. Command Execution

- **Purpose:** Execute OS command line directly
- **Input:** Command line string entered in Control-M
- **Length Limit:** Up to 512 characters
- **Case Sensitivity:** Platform-dependent
  - **UNIX:** Yes (case-sensitive)
  - **Windows:** No (case-insensitive)
- **Use Case:** Run commands, tools, and utilities directly without separate script files

### 3. Embedded Script

- **Purpose:** Run inline scripts written directly in Control-M
- **Content:** Inline script code (up to 64,000 bytes)
- **Case Sensitivity:** Script content is case-sensitive
- **Languages Supported:** Perl, PowerShell, VBScript, Python
- **Interpreter Specification:** "#!" prefix on first line identifies interpreter
  - `#!/usr/bin/perl` → Perl script
  - `#!/usr/bin/python` → Python script
  - (Platform-specific syntax for Windows PowerShell, VBScript)
- **Syntax Requirements:** Each language has specific interpreter syntax
- **Use Case:** Inline script logic without separate files; useful for small scripts or inline logic

---

## Key Job Attributes

### Run As User

| Attribute | Details |
|-----------|---------|
| **Purpose** | Specifies OS account executing the job |
| **Length** | 1-30 characters |
| **Case Sensitivity** | Case-sensitive (MyUser ≠ myuser) |
| **Constraints** | No spaces or apostrophes |
| **Authorization** | User must exist and be authorized on target system |

### File Path and File Name

| Component | Details | Constraints |
|-----------|---------|-----------|
| **File Path** | Directory location for script | 1-255 characters; case-sensitive |
| **File Name** | Script filename | 1-64 characters; case-sensitive |
| **Spaces** | Not allowed in either | Use quoted paths if needed |
| **Special Chars** | Limited allowed characters | Cannot contain: \\, *, ?, /, etc. |

### Command

| Attribute | Details |
|-----------|---------|
| **Purpose** | OS command to execute |
| **Length** | Up to 512 characters |
| **Case Sensitivity** | UNIX: Yes; Windows: No |
| **Special Chars** | Supports shell metacharacters (pipes, redirects, etc.) |
| **Variables** | Can include Control-M variables (%%VARNAME) |

### Embedded Script

| Attribute | Details |
|-----------|---------|
| **Content** | Inline script code |
| **Max Size** | 64,000 bytes |
| **Case Sensitivity** | Script content case-sensitive |
| **Interpreter ID** | "#!" prefix on first line |
| **Languages** | Perl, PowerShell, VBScript, Python |

---

## Embedded Script Examples

### Perl Script

```perl
#!/usr/bin/perl
print "Hello from Perl\n";
my $file = "%%INPUTFILE";
# Script logic here
```

### Python Script

```python
#!/usr/bin/python
print("Hello from Python")
inputfile = "%%INPUTFILE"
# Script logic here
```

### PowerShell Script

```powershell
#!/usr/bin/powershell
Write-Host "Hello from PowerShell"
$inputfile = "%%INPUTFILE"
# Script logic here
```

### VBScript

```vbscript
#!/vbs
WScript.Echo "Hello from VBScript"
Dim inputfile
inputfile = "%%INPUTFILE"
' Script logic here
```

---

## Variable Integration with OS Jobs

### Variable Scope Constraint

**Important:** "Variables defined at the folder level don't transfer to jobs—you must define variables at the job level for scripts and embedded scripts."

### Implication

| Scope Level | Availability in Scripts | Workaround |
|-------------|------------------------|-----------|
| **Folder-level variables** | NOT available to job scripts | Define same variables at job level |
| **Job-level variables** | Available to job scripts | Define all variables at job level |
| **System variables** | Available (%%JOBNAME, %%DATE, etc.) | Use system variables in scripts |
| **Environment variables** | Available via %%GETENV() | Use Variables doc GETENV function |

### Variable Usage Pattern

```
Folder Definition:
├─ %%APPDIR = "/data/app"  (NOT available to job scripts!)

Job Definition:
├─ %%APPDIR = "/data/app"  (Define at job level for script access)
├─ %%INPUTFILE = "%%FileWatch-FILE_PATH"  (From File Watcher)
└─ Script Content:
   #!/bin/bash
   cd $APPDIR
   process_file $INPUTFILE
```

---

## Supported Embedded Script Languages

### Language Support Matrix

| Language | Interpreter | First Line Syntax | Windows Support | Unix/Linux Support |
|----------|-------------|------------------|-----------------|-------------------|
| **Perl** | Perl | `#!/usr/bin/perl` | Yes | Yes |
| **Python** | Python | `#!/usr/bin/python` | Yes | Yes |
| **PowerShell** | PowerShell | `#!/usr/bin/powershell` (Windows-specific) | ✓ | Limited |
| **VBScript** | VBScript | `#!/vbs` (Windows-specific) | ✓ | ✗ |

### Language-Specific Syntax

Each language has specific requirements:
- **Perl:** Standard Perl syntax with shebang
- **Python:** Standard Python syntax with shebang
- **PowerShell:** PowerShell cmdlets and syntax
- **VBScript:** VBScript syntax (Windows only)

---

## OS Job Integration with Control-M Architecture

### As a Job Type

OS jobs are one of many Control-M job types:
- **Definition:** Defined like other jobs (folder, name, parameters)
- **Configuration:** Command, script path, or embedded script
- **Scheduling:** Subject to calendar and time-based scheduling
- **Prerequisites:** Can have file watchers, events, scheduling prerequisites
- **Variables:** Can use Control-M variables in commands and scripts

### With Folder Hierarchy

OS jobs are contained in:
- SMART folders (inherit scheduling, prerequisites, actions)
- Regular folders (independent scheduling)
- Sub-folders (inherit from parent SMART folder)

### With Variables System

Integration with Control-M Variables:
- **System Variables:** %%JOBNAME, %%DATE, %%COMPSTAT, etc. available
- **User Variables:** Job-level variables available to scripts
- **Folder Variables:** NOT available to scripts (important constraint!)
- **File Watcher Variables:** %%FileWatch-FILE_PATH available if triggered by File Watcher

### With Events and Prerequisites

OS jobs can:
- Be triggered by file watchers (File Watcher → Job)
- Generate events triggering downstream jobs
- Have event prerequisites (wait for other jobs)
- Have calendar-based scheduling

### With Pattern-Matching

Pattern matching in OS jobs:
- Used in command strings for filtering
- IF conditions in commands use pattern matching
- File path matching in File Watcher triggers

---

## OS Job Execution Flow

### Script Execution Flow

```
Job Triggered
  ↓
Resolve Control-M variables (%%VARNAME → actual values)
  ├─ System variables available
  ├─ Job-level variables available
  └─ Folder variables NOT available
  ↓
Execute script from specified path
  ├─ Run As user account used
  └─ Interpreter determined by extension/shebang
  ↓
Capture output and return code
  ↓
Return code determines success/failure
  ↓
Trigger actions (post-job logic)
```

### Command Execution Flow

```
Job Triggered
  ↓
Resolve Control-M variables in command string
  ↓
Execute OS command (512 char limit)
  ├─ Case sensitivity by platform
  └─ Supports shell features (pipes, redirects, etc.)
  ↓
Capture output and return code
  ↓
Return code determines success/failure
  ↓
Trigger actions
```

### Embedded Script Flow

```
Job Triggered
  ↓
Parse embedded script (up to 64,000 bytes)
  ├─ Identify interpreter from "#!" line
  └─ Resolve variables in script content
  ↓
Execute inline script with identified interpreter
  ├─ Perl, Python, PowerShell, or VBScript
  └─ Run As user account used
  ↓
Capture output and return code
  ↓
Return code determines success/failure
  ↓
Trigger actions
```

---

## Variable Resolution in OS Jobs

### What Gets Resolved

Variables in command lines and scripts are resolved before execution:
```
Original Command: /bin/process %%INPUTFILE %%DATE
Resolved Command: /bin/process /data/input_20260611.txt 20260611
```

### What's NOT Available

Folder-level variables do NOT get resolved in job scripts:
```
Folder Level:
├─ %%APPDIR = "/data/app"

Job Script:
├─ $APPDIR is NOT set to "/data/app"
└─ Script would fail if relying on %%APPDIR
```

### Workaround

Define variables at job level:
```
Job Level:
├─ %%APPDIR = "/data/app"
├─ Embedded Script:
  #!/bin/bash
  cd $APPDIR  # NOW available because defined at job level
```

---

## Best Practices

### Script Design

1. **Use Absolute Paths**
   - Specify full paths to scripts and files
   - Avoid relative paths (working directory may vary)
   - Example: `/opt/scripts/myscript.sh` not `./myscript.sh`

2. **Error Handling**
   - Set proper exit codes (0 for success, non-zero for failure)
   - Capture stderr to logging files
   - Test scripts on target system before deploying

3. **Variable Substitution**
   - Define all variables at job level (not folder level)
   - Use Control-M variable syntax (%%VARNAME)
   - Test variable resolution with variable simulation

4. **Logging**
   - Redirect output to log files
   - Include timestamp in logs
   - Monitor job output in Control-M UI

### Command Execution

1. **Command Length**
   - Stay within 512 character limit
   - Break long commands into multiple jobs if needed
   - Use scripts for complex logic

2. **Platform Differences**
   - Account for case sensitivity differences
   - Test commands on both Windows and Unix if cross-platform
   - Use appropriate shell syntax for each platform

3. **Quoting**
   - Quote paths with spaces
   - Quote variable values that may contain spaces
   - Escape special characters appropriately

### Embedded Script

1. **Language Selection**
   - Use language available on target platform
   - Perl/Python more portable than PowerShell/VBScript
   - Consider maintenance requirements

2. **Interpreter Specification**
   - Always include "#!" line with correct interpreter
   - Use platform-appropriate syntax
   - Test interpreter availability on target

3. **Size Management**
   - Keep scripts under 64,000 bytes
   - Move large logic to separate script files
   - Use modular script design

---

## Constraints and Limitations

| Constraint | Impact | Workaround |
|-----------|--------|-----------|
| **Folder variables not available** | Scripts can't use folder-level variables | Define variables at job level |
| **Command length limit** | Commands longer than 512 chars fail | Use script files for complex logic |
| **Embedded script size limit** | Scripts larger than 64KB not supported | Use external script files |
| **Platform-specific languages** | VBScript only on Windows | Use Perl/Python for cross-platform |
| **File path constraints** | No spaces in paths | Quote paths or use alternatives |
| **User authorization** | Run As user must exist and be authorized | Verify user exists on target system |

---

## Notes for Planning Agents

1. **Three Execution Types:** Script, Command, Embedded Script provide flexible execution options
2. **Embedded Languages:** Perl, PowerShell, VBScript, Python support inline scripting
3. **Variable Scope Constraint:** Folder variables NOT available to job scripts (job-level only)
4. **System Variables Available:** Standard Control-M variables work in all execution types
5. **File Watcher Integration:** %%FileWatch-FILE_PATH available if triggered by File Watcher
6. **User Authorization:** Run As user must have system permissions
7. **Case Sensitivity:** Varies by platform (UNIX yes, Windows no for commands)
8. **Size Limits:** Commands (512 chars), Scripts (64,000 bytes), File names (64 chars)
9. **Interpreter Requirements:** Embedded scripts need "#!" prefix for language identification
10. **Cross-Platform:** Perl/Python most portable; PowerShell/VBScript Windows-only

---

## Integration Points Summary

| Component | Integration | Details |
|-----------|-------------|---------|
| **Variables** | Variable substitution in commands/scripts | Folder variables NOT available (job-level only) |
| **File Watcher** | File path via %%FileWatch-FILE_PATH | Triggered by file detection |
| **Folders** | Job container | In SMART, Regular, or Sub-folders |
| **Scheduling** | Calendar-based and time-based | Control-M scheduling applies |
| **Events** | Event generation and prerequisites | Can trigger/be triggered by events |
| **Pattern-Matching** | In command filtering and IF conditions | Used for conditional logic |
| **OS Platforms** | Windows, Unix/Linux | Language support varies by platform |

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | OS Job Type |
| **Execution Types** | Script, Command, Embedded Script |
| **Command Length** | Up to 512 characters |
| **Script File Path** | 1-255 characters (case-sensitive) |
| **Script File Name** | 1-64 characters (case-sensitive) |
| **Embedded Script Size** | Up to 64,000 bytes |
| **Run As User** | 1-30 characters (case-sensitive, no spaces) |
| **Supported Languages** | Perl, Python, PowerShell, VBScript |
| **Variable Scope** | Job-level only (folder variables NOT available) |
| **System Variables** | Available (%%JOBNAME, %%DATE, etc.) |
| **Platform Support** | Windows, Unix/Linux |
| **Shebang Required** | Yes, for embedded script language identification |
