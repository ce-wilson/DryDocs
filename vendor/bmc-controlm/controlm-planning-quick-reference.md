# Control-M Planning - Quick Reference

**Source:** BMC Software - Control-M SaaS Documentation  
**Date Scraped:** 2026-06-11

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

This is a **distilled quick-reference** — almost entirely Claude organization/framing layered over grounded facts. The core-concept quote is VERBATIM; the feature summary is GROUNDED; the Q&A, architecture-style framing, and any "for planning agents" guidance are SYNTHESIZED. Treat as an index, not as a citable vendor source — defer to the full-topic docs.

---

## What is Control-M?
Workflow automation platform for business scheduling and job orchestration across multiple platforms.

## Core Concept
> "A sequence of connected jobs that executes at specific times, in a specific order, when they fulfill user-defined prerequisites."

## Job Types & Execution
- **Jobs:** Basic execution units (scripts, commands, external service calls)
- **Supported Targets:** OS-level commands, Hadoop, AWS, Snowflake, other external services

## Folder Organization
| Type | Purpose | Parameters |
|------|---------|-----------|
| SMART Folder | Group related jobs | Inherited by children |
| Regular Folder | Standard job container | Per-job basis |
| Sub-folder | Nested organization | Inherited from parent |

## Planning Definition Areas
1. **General Parameters** — Folder/job type configuration
2. **Scheduling Criteria** — When jobs execute
3. **Prerequisites** — Dependencies and conditions
4. **Actions** — Post-processing and notifications

## Key Features at a Glance
- ✓ Templates for job standardization
- ✓ Multi-environment support (Workspaces)
- ✓ Check-in workflow for deployment control
- ✓ SLA Manager for compliance
- ✓ Forecast rules for runtime prediction
- ✓ Workload policies for resource balancing
- ✓ Statistics collection for analysis

## Integration Support
- **Cloud:** AWS
- **Data:** Snowflake
- **Big Data:** Hadoop
- **General:** Configurable connectors

## Architecture Style
- **Job-centric:** Jobs are primary execution unit
- **Hierarchical:** Folders organize jobs and propagate parameters
- **Prerequisites-driven:** Jobs execute when conditions met
- **Time-based:** Scheduling determines execution windows

## Development Workflow
1. Create workspace (isolated development environment)
2. Define jobs with parameters, scheduling, prerequisites, actions
3. Check-in to move to production
4. Monitor with SLA Manager and forecasts

---

## For Planning Agents: Key Design Questions Answered

**Q: How are jobs organized?**  
A: Three-tier hierarchy (Folders → Jobs, with SMART folder inheritance)

**Q: Can parameters be shared across jobs?**  
A: Yes, SMART folders propagate parameters to all contained jobs

**Q: How are dependencies managed?**  
A: Via Prerequisites defined within each job definition

**Q: What environments are supported?**  
A: Multi-environment via Workspaces with check-in deployment model

**Q: How is execution order determined?**  
A: By scheduling criteria + prerequisites, independent per job

**Q: What monitoring/alerting exists?**  
A: SLA Manager, forecast rules, statistics collection, workload policies
