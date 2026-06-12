# Control-M Planning - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Control-M_Planning.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Design validation and planning agent reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Core concept quote ("sequence of connected jobs…"); jobs as execution units; folder organization (SMART/Regular/Sub-folders); planning domain functions; named integrations (AWS, Snowflake, Hadoop); workspaces + check-in workflow; SLA Manager / forecasting / templates existence.
- **SYNTHESIZED:** Notes for Planning Agents, any structural framing/diagrams, Vendor Attributes table.

---

## Executive Summary

Control-M is a workflow automation platform that enables business scheduling and processing across multiple platforms. The core function is managing "a sequence of connected jobs that executes at specific times, in a specific order, when they fulfill user-defined prerequisites."

---

## Core Components

### Jobs
- **Definition:** Fundamental execution units in Control-M
- **Capabilities:**
  - Execute scripts
  - Run commands at OS level
  - Connect to external services
  - Integrate with cloud platforms and data warehouses

### External System Integration
- Amazon Web Services (AWS)
- Snowflake
- Hadoop
- Other configurable external services

### Folder Organization
Control-M uses three folder types for hierarchical job management:

1. **SMART Folders**
   - Include extended definition parameters
   - Parameters apply collectively to all contained jobs
   - Enable standardized configuration across job groups

2. **Regular Folders**
   - Process jobs independently
   - Each job has individual parameters
   - No inherited parameter propagation

3. **Sub-folders**
   - Inherit parameters from parent SMART folders
   - Support nested hierarchy
   - Maintain parameter inheritance chain

---

## Planning Domain Functions

### Job Definition Areas
Control-M Planning manages four primary definition areas:

1. **General Parameters**
   - Based on folder type
   - Based on job type
   - Common configuration settings

2. **Scheduling Criteria**
   - Determine job execution timing
   - Define temporal constraints
   - Support periodic and event-driven triggers

3. **Prerequisites**
   - Establish submission requirements
   - Define job dependencies
   - Control execution order and conditions

4. **Actions**
   - Specify post-processing operations
   - Define output handling
   - Configure notifications and alerts

### Additional Planning Features

| Feature | Purpose |
|---------|---------|
| **Templates** | Standardized job and SMART folder definitions for reuse |
| **Periodic Statistics** | Collect and analyze job execution data over time |
| **Rules** | Define runtime expectations and behaviors |
| **Folder Management** | Organize and control jobs across all environments |
| **Workload Policy Controls** | Balance resource utilization |
| **SLA Manager** | Track and enforce Service Level Agreements |
| **Forecast Rules** | Predict and manage runtime expectations |

---

## Development Environment

### Workspaces
- **Purpose:** Development and testing environment for job creation
- **Workflow:** Users create working environments called "Workspaces"
- **Deployment:** Check-in procedures required before moving jobs to production
- **Benefits:** Isolated development without affecting production workflows

---

## Architecture Concepts

### Workflow Structure
Control-M organizes work as:
- **Connected jobs:** Jobs linked through dependencies and prerequisites
- **Temporal execution:** Jobs run at specific times in specific order
- **Conditional execution:** Jobs execute when user-defined prerequisites are met

### Parameter Inheritance Model
```
Folder (Regular or SMART)
├── Job 1 (uses folder parameters + individual parameters)
├── Job 2 (uses folder parameters + individual parameters)
└── Sub-folder (inherits from parent SMART folder)
    └── Job 3 (uses inherited + individual parameters)
```

---

## Key Design Characteristics

### Multi-Platform Support
- Cross-platform job execution
- Unified scheduling interface
- Heterogeneous system integration

### Scalability Features
- Folder-based organization for large job sets
- Template reuse for consistency at scale
- SMART folder inheritance for bulk parameter management

### Monitoring & Management
- SLA tracking and enforcement
- Forecast capabilities for planning
- Statistics collection for analysis
- Workload policy controls for resource optimization

---

## Integration Patterns

### Cloud Integration
- Native AWS integration
- Snowflake data warehouse support
- Flexible connector framework for other systems

### Batch Processing
- Hadoop integration for distributed processing
- OS-level command execution
- Script execution capabilities

### External Services
- Configurable job definitions for external systems
- Standardized connection parameters
- Template-based configuration

---

## Notes for Planning Agent

1. **Hierarchy Model:** SMART folders + inheritance enable efficient bulk configuration
2. **Execution Control:** Jobs respect prerequisites and scheduling criteria independently
3. **Template Pattern:** Standardized definitions suggest reusable patterns across job types
4. **Environment Separation:** Workspace/check-in model indicates development-to-production workflow
5. **Multi-tenant Ready:** Folder organization and policies support multi-team scenarios
6. **Monitoring Built-in:** SLA Manager and forecasting suggest integrated monitoring approach

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Edition** | SaaS |
| **Vendor** | BMC Software |
| **Primary Use** | Workflow Automation & Business Scheduling |
| **Integration Breadth** | High (Cloud, Data Warehouse, Big Data) |
| **Architecture Style** | Job-based orchestration with folder hierarchy |
