# Control-M Infrastructure as Code Jobs - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Jobs_for_Infrastructure_as_Code.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Infrastructure as Code job types and cloud platform orchestration reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Five platforms (Ansible AWX, AWS CloudFormation, Azure Resource Manager, GCP Deployment Manager, Terraform); CloudFormation template URLs JSON/YAML up to 450KB or inline body; Azure JSON API requests; GCP YAML minified; Terraform workspace/run config; Ansible playbooks + JSON params; VCS-repo + OAuth for Ansible/Terraform; retry polling 15–20s default; rollback/delete-on-failure.
- **SYNTHESIZED:** Notes for Planning Agents, Vendor Attributes table, any assembled examples.

---

## Infrastructure as Code Job Definition and Purpose

Infrastructure as Code (IaC) jobs enable organizations to "create, configure, test, and manage your infrastructure" through integrated automation workflows across multiple cloud platforms.

**Scope:** Unified scheduling for cloud infrastructure deployment and orchestration

---

## Supported Infrastructure Tools & Platforms

**Five Primary Platforms:**

1. **Ansible AWX**
   - Manages playbooks, inventories, automation workflows
   - Source control repository integration
   - JSON parameter format

2. **AWS CloudFormation**
   - AWS resource stack creation and updates
   - Template URLs (JSON/YAML, up to 450KB) or inline bodies
   - AWS IAM role-based execution

3. **Azure Resource Manager**
   - Azure resource group deployments
   - JSON-formatted API requests
   - Incremental update mode support

4. **GCP Deployment Manager**
   - Google Cloud Platform resource orchestration
   - YAML minified configurations
   - Resource collection definitions

5. **Terraform**
   - Workspace creation and execution
   - Variable management and parameters
   - VCS repository integration with OAuth

---

## Code Deployment & Execution

**Platform-Specific Models:**

| Platform | Deployment Method | Format | Notes |
|----------|------------------|--------|-------|
| **CloudFormation** | Template-based | JSON/YAML | Up to 450KB |
| **Azure** | API request | JSON | Resource properties defined |
| **GCP** | Configuration | YAML (minified) | Resource collections |
| **Terraform** | Workspace | Parameters | VCS-repo configurations |
| **Ansible** | Playbook | JSON | Inventory & parameters |

---

## Cloud Platform Integration

**Connection Profiles:**
- Platform-specific authorization credentials
- Role-based execution (AWS IAM roles, Azure permissions)
- Connection management and validation

---

## Version Control & GitOps

**Repository Integration:**
- Ansible AWX: Source control for playbook management
- Terraform: VCS-repo configurations with:
  - Branch specifications
  - OAuth token authentication
  - Repository access control

---

## Templating & Parameterization

**Configuration Approaches:**
- JSON/YAML parameterized deployments
- Execution variables
- Resource properties
- Deployment modes (Azure Incremental updates)

---

## Error Handling & Validation

**Recovery Mechanisms:**

| Feature | Details |
|---------|---------|
| **Failure Tolerance** | Configurable status checks before "Not OK" |
| **CloudFormation** | Rollback or stack deletion on failure |
| **Others** | Retry mechanisms |
| **Polling** | Configurable frequency (default 15-20 seconds) |

---

## Monitoring Infrastructure Changes

**Capabilities:**
- Status Polling Frequency controls
- Detailed Output Logs tracking deployment execution
- Infrastructure change visibility throughout lifecycle

---

## Integration with Control-M Architecture

**Features:**
- Dependency chains with other job types
- Unified scheduling environment
- Variable sharing with other jobs
- Pre/post-execution integration

---

## Key Variables

**Runtime Variables:**
- Job execution context
- Platform-specific outputs
- Status and error information

---

## Prerequisites

**Requirements:**
- Platform account/subscription
- Connection profile establishment
- API permissions
- OAuth tokens (for VCS integration)
- Target resource permissions

---

## Use Cases

**Common Scenarios:**
- AWS infrastructure provisioning (CloudFormation)
- Azure resource group deployments
- Google Cloud resource orchestration
- Ansible playbook execution
- Terraform workspace management
- Multi-cloud infrastructure orchestration

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | Infrastructure as Code Job Types |
| **Platforms** | Ansible AWX, CloudFormation, Azure, GCP, Terraform |
| **Protocols** | Platform-native APIs, OAuth |
| **Template Format** | JSON, YAML |
| **Max Template Size** | 450KB (CloudFormation) |
| **Polling Default** | 15-20 seconds |
| **VCS Support** | Terraform (OAuth tokens) |
| **Execution Model** | Role-based (platform-specific) |
| **Integration** | Full Control-M scheduling integration |
