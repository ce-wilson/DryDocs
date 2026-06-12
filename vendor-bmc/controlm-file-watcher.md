# Control-M File Watcher Job - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** File_Watcher_Job.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** File watcher job definition, monitoring modes, and file detection reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Create vs Delete detection modes; up to 5 sequential transfer definitions; watch conditions (time limit minutes, search interval seconds, file-size interval seconds, iterations, min/max file age); `%%FileWatch-FILE_PATH` variable; protocols (FTP, SFTP, cloud APIs); cloud platforms (S3, Azure, Google Cloud, Oracle Object Storage, AS2, SharePoint).
- **SYNTHESIZED:** Any JSON/workflow examples, Notes for Planning Agents, Vendor Attributes table.

---

## File Watcher Job Definition and Purpose

The File Watcher job type enables "detection of file creation or deletion within a defined timeframe. It monitors the file system for specific events without requiring manual intervention."

**Primary Use Cases:**
- Monitor for incoming files before processing
- Detect file deletion events
- Track file system activity
- Trigger jobs based on file events
- Enable event-driven job execution

**Key Characteristic:** File Watchers provide event-driven job triggering based on file system changes rather than time-based scheduling.

---

## How File Watchers Work

### File Watcher Mechanism

File Watchers operate by "periodically searching for files matching specified criteria."

**Detection Process:**
```
1. Search for files matching specified name pattern
2. (Create Mode) Confirm file properties (size, age)
3. (Delete Mode) Monitor for file deletion after initial detection
4. Trigger action when condition satisfied
5. Repeat at specified interval until complete or timeout
```

### Create Mode

- **Detection:** When files are created
- **Monitoring:** File size and age parameters
- **Exception:** Size monitoring can be disabled with wildcards
- **Use Case:** Wait for incoming file before starting dependent jobs

### Delete Mode

- **Detection:** When files are removed from system
- **Prerequisite:** Initial file must be detected in Create mode first
- **Monitoring:** Periodic checks for file deletion
- **Use Case:** Monitor when file is processed and removed

---

## File Path and Pattern Handling

### Wildcard Expressions

File paths support Control-M wildcard expressions:

| Wildcard | Meaning | Example |
|----------|---------|---------|
| **\*** | Matches one or more characters | `/data/input_*` matches `/data/input_001`, `/data/input_batch` |
| **?** | Matches a single character | `/data/file?.txt` matches `/data/file1.txt`, `/data/fileA.txt` |
| **\*\*** | Implied: matches path segments | (Check pattern matching doc for full syntax) |

### Path Formatting

| Requirement | Details | Example |
|------------|---------|---------|
| **Spaces in Paths** | Must be enclosed in quotes | `"/data/my files/input.txt"` |
| **Case Sensitivity** | Depends on OS | Windows: case-insensitive; Unix: case-sensitive |
| **Absolute Paths** | Recommended for reliability | `/data/input/file.txt` or `C:\data\input\file.txt` |

### File Path Variable

- **Variable Name:** `%%FileWatch-FILE_PATH`
- **Purpose:** Reference the detected file path in subsequent jobs
- **Scope:** Available to jobs triggered by the file watcher
- **Use Case:** Pass file path to dependent jobs for processing

---

## Watch Conditions and Monitoring Parameters

### Time Limit

| Parameter | Purpose | Details |
|-----------|---------|---------|
| **Time Limit** | Maximum execution duration | Specified in minutes |
| **Behavior** | Job terminates if limit exceeded | No retry after timeout |
| **Use Case** | Prevent indefinite waiting | Set based on expected file arrival time |

### Search and Detection Interval

| Parameter | Purpose | Details |
|-----------|---------|---------|
| **Search Interval** | Seconds between detection attempts | How often to check for files |
| **Frequency** | Controls polling frequency | Lower = more frequent checks, higher CPU |
| **Use Case** | Balance responsiveness vs. performance | Typical: 10-60 seconds |

### File Size Monitoring

| Parameter | Purpose | Details |
|-----------|---------|---------|
| **File Size Interval** | Seconds between size checks | Monitor if file is still growing |
| **Iterations** | Number of size confirmations | Requires N consecutive stable sizes |
| **Minimum Size** | File size threshold | Specified in: bytes, KB, MB, or GB |
| **Use Case** | Ensure file transfer complete | Wait for file to stop growing |

### File Age

| Parameter | Purpose | Details |
|-----------|---------|---------|
| **Minimum Age** | Minimum time since last modification | Ensures file is stable (not being written) |
| **Maximum Age** | Maximum time since last modification | Ignore old files (stale detection) |
| **Unit** | Time unit for age threshold | Minutes, hours, days |
| **Use Case** | Distinguish fresh files from stale ones | Prevent processing old files |

---

## File Watcher Detection Workflow

### Create Mode Workflow

```
File Watcher Started
  ↓
Search for files matching pattern
  ├─ Match found?
  │  └─ YES → Check file properties
  │       ├─ Check file size interval (size stable?)
  │       ├─ Check iterations (N confirmations?)
  │       ├─ Check minimum size requirement
  │       ├─ Check file age requirements
  │       └─ All satisfied?
  │           └─ YES → File detected, trigger action
  └─ NO match → Wait, retry at search interval
        └─ Time limit exceeded? → Timeout
```

### Delete Mode Workflow

```
File created (from Create Mode)
  ↓
Monitor for file deletion at search interval
  ├─ File still exists?
  │  └─ YES → Continue monitoring
  └─ File deleted?
     └─ YES → File deletion detected, trigger action
```

---

## Execution Requirements

### Run As User Attribute

| Attribute | Details | Constraints |
|-----------|---------|-----------|
| **Run As** | Username for job execution authorization | Required |
| **Length** | Character count for username | 1-30 characters |
| **Case Sensitivity** | Case-sensitive username | MyUser ≠ myuser |
| **Allowed Characters** | Alphanumeric | No spaces or apostrophes |
| **Authorization** | User must exist and be authorized | System-dependent |

### User Authorization

- Specified user must have permissions to:
  - Read files in the watch directory
  - Monitor file system events
  - Execute on target server/host
  - Write log files if enabled

---

## File Watcher Integration with Control-M

### As a Job Type

File Watcher is one of many Control-M job types:
- **Definition:** Defined like other jobs (folder, name, parameters)
- **Configuration:** File path, watch mode, detection conditions
- **Scheduling:** Can use calendar-based scheduling (optional)
- **Monitoring:** Subject to SLA rules and forecasting

### With Folder and Hierarchy

File Watchers can be:
- Contained in SMART folders (inherit scheduling/prerequisites)
- Contained in regular folders
- Contained in sub-folders
- Referenced in events (trigger dependent jobs)

### With Events and Prerequisites

File Watcher as event source:
```
File Watcher Job (detects file)
  ↓
Generates event
  ↓
Dependent Jobs (wait for event)
  ├─ File Available Event
  └─ Other Prerequisites
```

### With Variables

Integration with Control-M Variables:
- **File Path Variable:** `%%FileWatch-FILE_PATH` available to triggered jobs
- **System Variables:** Standard job variables available (%%JOBNAME, etc.)
- **Use Case:** Pass detected file path to downstream processing jobs

### With Actions

File Watchers support post-detection actions:
- Execute jobs on file detection
- Send notifications on timeout
- Retry monitoring on failure
- Log file detection events

---

## File Watcher Best Practices

### Pattern Matching

1. **Use Specific Patterns**
   - Use exact file name when possible
   - Use wildcards only when necessary
   - Test patterns to ensure correct matching

2. **Avoid Overly Broad Patterns**
   - `*` matches many files; use `input_*.txt` instead
   - Narrow patterns improve performance
   - Reduce false matches

### Monitoring Parameters

1. **Time Limit**
   - Set based on expected file arrival window
   - Must accommodate network delays, processing time
   - Typical: 60-120 minutes for batch processes

2. **Search Interval**
   - Balance responsiveness vs. server load
   - 10-30 seconds for near-real-time (high load)
   - 60+ seconds for batch scenarios (low load)

3. **File Size Stability**
   - Enable for files being written
   - Set intervals long enough for transfer rate
   - Typical: 2-5 size checks before confirmation

4. **File Age**
   - Prevent picking up stale files
   - Useful when multiple files in directory
   - Set minimum age = file transfer time + margin

### Performance Optimization

1. **Directory Scope**
   - Monitor specific directories, not entire filesystems
   - Use absolute paths
   - Consider using dedicated input directories

2. **Wildcard Efficiency**
   - More specific patterns = faster matching
   - Narrow date/time in pattern if possible
   - Consider file naming conventions

3. **Cleanup**
   - Process files promptly
   - Archive or delete processed files
   - Avoid directory clutter

### Error Handling

1. **Timeout Planning**
   - Set realistic time limits
   - Monitor timeout occurrences
   - Investigate patterns of timeouts

2. **File Validation**
   - Use file size minimum to reject partial files
   - Use file age to ensure stability
   - Consider follow-up validation jobs

3. **Notification**
   - Alert on timeout
   - Log file detection events
   - Monitor watcher job success rate

---

## Common File Watcher Scenarios

### Scenario 1: Batch File Arrival

**Goal:** Trigger batch job when daily file arrives

```
File Watcher Configuration:
├─ Path: /data/batch/daily_*.csv
├─ Mode: Create
├─ Time Limit: 180 minutes (3 hours, arrival window)
├─ Search Interval: 30 seconds
├─ File Size Interval: 10 seconds
├─ Iterations: 3 (stable size confirmation)
└─ Minimum Size: 1 KB

Action: Trigger downstream batch processing job
File Path: %%FileWatch-FILE_PATH → passed to processing job
```

### Scenario 2: Real-Time File Monitoring

**Goal:** Process files as they arrive (near real-time)

```
File Watcher Configuration:
├─ Path: /input/realtime_*.txt
├─ Mode: Create
├─ Time Limit: 60 minutes
├─ Search Interval: 10 seconds (frequent checks)
├─ File Size Interval: 5 seconds
├─ Iterations: 2
└─ Minimum Size: 0 (accept any size)

Action: Trigger processing job immediately
```

### Scenario 3: Completion Detection

**Goal:** Detect when file is processed and removed

```
File Watcher Configuration:
├─ Path: /processing/file_*.lock
├─ Mode: Delete (after initial Create detection)
├─ Time Limit: 120 minutes
├─ Search Interval: 30 seconds
└─ (Monitor for lock file deletion)

Action: Trigger cleanup/notification job after completion
```

---

## File Watcher Limitations and Constraints

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| **Network Paths** | May have higher latency | Reduce search interval, increase time limit |
| **File System Delays** | OS may delay file visibility | Increase file size interval |
| **Pattern Matching** | Limited to Control-M wildcards | Rely on consistent naming conventions |
| **Scalability** | Many watchers = CPU impact | Monitor server load, consolidate patterns |
| **Cross-Platform** | Paths are OS-specific | Test on target OS |

---

## Notes for Planning Agents

1. **Event-Driven Triggering:** File Watchers provide event-driven alternative to time-based scheduling
2. **Pattern Matching Integration:** Uses Control-M wildcards (* and ?)
3. **File Path Variable:** %%FileWatch-FILE_PATH enables file path propagation to dependent jobs
4. **Two Modes:** Create (file arrival) and Delete (completion detection)
5. **Monitoring Parameters:** Size stability, age, time limit control detection sensitivity
6. **Folder Integration:** Like other job types, can be in SMART/Regular folders
7. **Events & Prerequisites:** Can generate events to trigger dependent jobs
8. **Performance Tuning:** Search interval and pattern specificity affect CPU load
9. **User Authorization:** Run As user must have file system permissions
10. **Common Use Cases:** Batch file arrival, real-time monitoring, completion detection

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | File Watcher Job Type |
| **Detection Modes** | Create, Delete |
| **Wildcards** | \*, ? (Control-M standard) |
| **File Path Variable** | %%FileWatch-FILE_PATH |
| **Time Limit** | Minutes (configurable) |
| **Search Interval** | Seconds (configurable) |
| **File Size Interval** | Seconds (configurable) |
| **Iterations** | Count (for size stability) |
| **Minimum Size** | Bytes, KB, MB, GB |
| **File Age** | Minimum and Maximum (time-based) |
| **Run As User** | 1-30 chars, case-sensitive, no spaces |
| **Integration** | Events, Variables (%%FileWatch-FILE_PATH), Folders, Prerequisites |
