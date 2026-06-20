# Control-M File Transfer Job - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** File_Transfer_Job.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** File transfer job type, protocols, and distributed file management reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Up to 5 sequential transfer definitions; seven transfer operations (standard, watch & transfer, watch-only, directory listing, bidirectional sync, incremental, concurrent); transfer variables (`$WATCH_ALLn$`, `$WATCH_NAMEn$`, `$WATCH_EXTn$`, `$AFTFILE$`, `$AFTFILE_ALL$`, `$AFTFILE_NAME$`, `$AFTFILE_EXT$`); destination manipulation tokens ([N],[E],[C],[D],[T],[FD]); duplicate handling options; resume-from-failure (FTP REST dependent).
- **SYNTHESIZED:** Notes for Planning Agents, Vendor Attributes table, any assembled examples.

---

## File Transfer Job Definition and Purpose

File Transfer jobs in Control-M enable "watching and transferring files across local hosts, agentless hosts, cloud storage, and containers."

**Scope:** Single job can contain up to five sequential file transfer definitions

---

## Transfer Modes & Protocols

**Supported Scenarios:**
- Local host ↔ Agentless Host
- Agentless Host ↔ Agentless Host  
- Cloud storage (S3, Azure, Google Cloud, Oracle Object Storage)
- AS2 Server and SharePoint Online

**Protocols:** FTP, SFTP, cloud-native APIs

---

## Source & Destination Configuration

**Endpoint Options:**
- Two Single Endpoints (separate source/destination profiles)
- Endpoint1 ↔ Endpoint2 (combined profile definitions)

**Cloud Configuration:**
- Buckets, containers, or shares specified
- SharePoint: site names and document library via Graph API

---

## File Selection & Transfer Operations

**Seven Transfer Operations:**
1. Standard transfer (→ or ←)
2. Watch & transfer (with size/time thresholds)
3. Watch-only monitoring
4. Directory listing (optional recursion)
5. Bidirectional synchronization (Windows/Linux)
6. Incremental transfers (modification timestamps)
7. Concurrent multi-file transfers

**File Filtering:**
- Wildcard patterns and regular expressions
- Directory paths cannot use wildcards

---

## Transfer Conditions & Triggers

**Advanced Features:**
- Pre/post-transfer commands (chmod, mkdir, rename, rm, rmdir)
- File watching: minimum size, age thresholds, time limits
- Destination filename manipulation: [N], [E], [C], [D], [T], [FD] variables
- Post-transfer actions: delete, rename, move, change permissions
- PGP encryption/decryption integration

---

## Error Handling & Recovery

**Mechanisms:**
- Resume from exact point of failure (FTP REST dependent)
- Configurable retry counts
- Continue on failure option
- Duplicate handling: overwrite, append, abort, skip, add counter, timestamp

---

## Job Status Lifecycle

**States:**
- Waiting → In Progress → Ended OK/Failed
- Killed (user-canceled), Abandoned (prior failure blocking)
- Skipped (successful prior execution)
- File Watching (active monitoring phase)

---

## Variable Support

**System Variables:**
- $$WATCH_ALLn$$ (all watched files)
- $$WATCH_NAMEn$$ (file names)
- $$WATCH_EXTn$$ (file extensions)
- $$AFTFILE$$ (transferred file)
- $$AFTFILE_ALL$$ (all transferred files)
- $$AFTFILE_NAME$$, $$AFTFILE_EXT$$

---

## Integration Points

- Dependency chains with other job types
- Variable sharing between watch operations
- Named pool variables for cross-job reference
- Pre/post-execution command integration

---

## Prerequisites

- Managed File Transfer connection profile
- Graph API permissions (SharePoint)
- Write permissions on destination paths
- FTP REST support for resume
- Agent installation for pre/post-commands

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | File Transfer Job Type |
| **Max Sequential Definitions** | 5 per job |
| **Transfer Operations** | 7 types |
| **Protocols** | FTP, SFTP, Cloud APIs |
| **Cloud Platforms** | S3, Azure, GCP, Oracle, AS2, SharePoint |
| **Filename Variables** | [N], [E], [C], [D], [T], [FD] |
| **System Variables** | $$WATCH_*, $$AFTFILE_* |
| **Resume Support** | FTP REST dependent |
| **Bidirectional Sync** | Windows/Linux |
