# Control-M Connection Profiles - Code Reference

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** API_CodeRef_ConnectionProfiles_Container.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Connection profile specifications for container orchestration platforms and cloud services

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## ⚠️ FORMAT MISMATCH & SYNTHESIZED-JSON WARNING — READ FIRST

This page documents the **Control-M Automation API (JSON)** — a **SaaS** interface. The target environment (**9.0.21.300**) defines connection profiles in **XML**, **not JSON** (and SaaS-only container/cloud profile types may not exist in 9.0.21.300 at all). Use this file as a **conceptual reference only** — *which properties, auth methods, and behaviors exist* where they may add detail applicable to our XML. **Do not treat the JSON as our format, and do not convert to JSON.**

The JSON *structure* below was Claude-synthesized: the canonical Automation API uses the object **name as the JSON key** in PascalCase, and the field names in my profile bodies (e.g. `AccessKeyID`, `ServiceTokenFilePath`) are plausible reconstructions, **not verbatim**. Auth-method and parameter *concepts* are grounded; exact JSON is **illustrative only**.

---

## 📑 Provenance Classification

Produced by WebFetch of one BMC page + Claude restructuring. Tiers: **[VERBATIM]** = BMC quotes · **[GROUNDED]** = Claude paraphrase of sourced content · **[SYNTHESIZED]** = Claude-authored, not in source (do NOT load as vendor ground truth).

- **GROUNDED:** The five platforms (AWS ECS, AWS App Runner, Azure Container Instances, GCP Cloud Run, Kubernetes); auth methods per platform (Secret/IAM Role/Assume Role, Service Principal/Managed Identity, Service Account/IAM User, Service Token/remote-spec OAuth2/BasicAuth/AWS IAM/Google SA); key params (regional URLs, Subscription/Tenant/App IDs, Namespace, Service Token File, login/management URLs); centralized-vs-local storage; "Secrets in Code"; per-platform timeout defaults (30/20/50/20/50s); Azure 24-hour Managed Identity token.
- **VERBATIM:** Platform purpose quotes (e.g. ECS "Enables you to execute, stop, manage…").
- **SYNTHESIZED:** Every full JSON profile body and exact field naming (e.g. `AccessKeyID`, `ServiceTokenFilePath`, `ServiceAccountKey` sub-keys); the Container Job integration example; Best Practices; Vendor Attributes table.

⚠️ **Hazard:** Auth methods and parameter *concepts* are grounded, but **JSON field names and profile schemas are Claude's plausible reconstruction**, not verbatim from source. Verify exact key names against live API.

---

## Connection Profiles Overview

Connection Profiles enable secure authentication and communication with cloud container orchestration platforms.

**Key Concept:** Connection Profiles provide centralized or agent-local credential management for containerized application deployment and management across AWS, Azure, GCP, and Kubernetes platforms.

---

## Connection Profile Architecture

### Storage Model

| Model | Location | Scope | Use Case |
|-------|----------|-------|----------|
| **Centralized** | Control-M/EM database | Global | Shared across all agents |
| **Local** | Specific agent | Agent-specific | Agent-local credentials |

**Configuration:**
```json
{
  "Centralized": true,    // true = shared, false = agent-specific
  "Description": "Profile description"
}
```

### Secret Management

**Credential Protection:**
- Direct credential storage (in profile)
- "Secrets in Code" protection for sensitive fields
- Credential escaping and encoding

---

## Container Orchestration Profiles

### 1. AWS ECS (Elastic Container Service)

**Purpose:** "Enables you to execute, stop, manage, and monitor containerized applications in a cluster."

#### Authentication Methods

| Method | Use Case | Parameters |
|--------|----------|-----------|
| **Secret** | Basic authentication | Access Key + Secret Key |
| **IAM Role** | EC2 instance-based | Role name (automatic credential assumption) |
| **Assume Role** | Cross-account access | Role ARN + Session name |

#### Required Configuration

```json
{
  "Type": "ConnectionProfile:AWS:ECS",
  "Name": "prod_ecs",
  "AuthenticationMethod": "Secret",
  "AccessKeyID": "AKIA...",
  "SecretAccessKey": "***",
  "ECSURL": "https://ecs.us-east-1.amazonaws.com",
  "CloudWatchURL": "https://monitoring.us-east-1.amazonaws.com",
  "AWSRegion": "us-east-1",
  "ConnectionTimeout": 30
}
```

#### AWS ECS Parameters

| Parameter | Purpose | Type | Default |
|-----------|---------|------|---------|
| **ECSURL** | ECS endpoint | Regional URL | Region-specific |
| **CloudWatchURL** | Monitoring endpoint | Regional URL | Region-specific |
| **AWSRegion** | AWS region | us-east-1, eu-west-1, etc. | Required |
| **ConnectionTimeout** | Timeout (seconds) | Numeric | 30 |
| **AccessKeyID** | AWS access key | String (secret) | Required (Secret auth) |
| **SecretAccessKey** | AWS secret key | String (secret) | Required (Secret auth) |
| **RoleARN** | IAM role ARN | String | Required (Assume Role) |
| **SessionName** | Session identifier | String | Optional |

---

### 2. AWS App Runner

**Purpose:** Deploys containerized web applications directly from source code or container images without infrastructure management.

#### Authentication Methods

| Method | Use Case | Parameters |
|--------|----------|-----------|
| **Secret** | Basic authentication | Access Key + Secret Key |
| **IAM Role** | EC2 instance-based | Role name (automatic assumption) |
| **Assume Role** | Cross-account access | Role ARN + Session name |

#### Required Configuration

```json
{
  "Type": "ConnectionProfile:AWS:AppRunner",
  "Name": "web_app_runner",
  "AuthenticationMethod": "Secret",
  "AccessKeyID": "AKIA...",
  "SecretAccessKey": "***",
  "AppRunnerURL": "https://apprunner.us-east-1.amazonaws.com",
  "AWSRegion": "us-east-1",
  "ConnectionTimeout": 20
}
```

#### AWS App Runner Parameters

| Parameter | Purpose | Type | Default |
|-----------|---------|------|---------|
| **AppRunnerURL** | App Runner endpoint | Regional URL | Region-specific |
| **AWSRegion** | AWS region | us-east-1, eu-west-1, etc. | Required |
| **ConnectionTimeout** | Timeout (seconds) | Numeric | 20 |
| **AccessKeyID** | AWS access key | String (secret) | Required (Secret auth) |
| **SecretAccessKey** | AWS secret key | String (secret) | Required (Secret auth) |

---

### 3. Azure Container Instances

**Purpose:** Runs isolated containers in Azure without managing virtual machines.

#### Authentication Methods

| Method | Use Case | Parameters |
|--------|----------|-----------|
| **Service Principal** | App registration | App ID + Client Secret |
| **Managed Identity** | Azure VM-based | Automatic (24-hour token) |

#### Required Configuration

```json
{
  "Type": "ConnectionProfile:Azure:ContainerInstances",
  "Name": "azure_containers",
  "AuthenticationMethod": "ServicePrincipal",
  "SubscriptionID": "12345678-1234-1234-1234-123456789012",
  "TenantID": "87654321-4321-4321-4321-210987654321",
  "ApplicationID": "app-id-guid",
  "ClientSecret": "***",
  "LoginURL": "https://login.microsoftonline.com",
  "ManagementURL": "https://management.azure.com",
  "ConnectionTimeout": 50
}
```

#### Azure Container Instances Parameters

| Parameter | Purpose | Type | Default |
|-----------|---------|------|---------|
| **SubscriptionID** | Azure subscription GUID | UUID | Required |
| **TenantID** | Azure tenant GUID | UUID | Required |
| **ApplicationID** | App registration ID | GUID | Required (Service Principal) |
| **ClientSecret** | Client secret | String (secret) | Required (Service Principal) |
| **LoginURL** | Azure AD login endpoint | URL | https://login.microsoftonline.com |
| **ManagementURL** | Azure management endpoint | URL | https://management.azure.com |
| **ConnectionTimeout** | Timeout (seconds) | Numeric | 50 |
| **TokenValidity** | Token lifetime | 24 hours | Fixed (Managed Identity) |

**Note:** Managed Identity authenticates automatically on Azure VMs; Service Principal requires explicit credentials.

---

### 4. GCP Cloud Run

**Purpose:** Container management service for executing and monitoring containerized applications.

#### Authentication Methods

| Method | Use Case | Parameters |
|--------|----------|-----------|
| **Service Account** | API-based | RSA key pair (private key) |
| **IAM User** | Role-based | Service account roles |

#### Required Configuration

```json
{
  "Type": "ConnectionProfile:GCP:CloudRun",
  "Name": "gcp_cloudrun",
  "AuthenticationMethod": "ServiceAccount",
  "CloudRunURL": "https://run.googleapis.com",
  "ServiceAccountKey": {
    "type": "service_account",
    "project_id": "project-id",
    "private_key_id": "key-id",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----...",
    "client_email": "service-account@project.iam.gserviceaccount.com",
    "client_id": "client-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
  },
  "ConnectionTimeout": 20
}
```

#### GCP Cloud Run Parameters

| Parameter | Purpose | Type | Default |
|-----------|---------|------|---------|
| **CloudRunURL** | Cloud Run API endpoint | URL | https://run.googleapis.com |
| **ServiceAccountKey** | Key JSON object | JSON (secret) | Required (Service Account) |
| **ProjectID** | GCP project ID | String | Extracted from key |
| **PrivateKey** | RSA private key | PEM format (secret) | Required |
| **ClientEmail** | Service account email | Email | Extracted from key |
| **ConnectionTimeout** | Timeout (seconds) | Numeric | 20 |

**Note:** Service account key can be loaded from JSON file or inline.

---

### 5. Kubernetes

**Purpose:** Runs pods to completion in Kubernetes-based clusters.

#### Authentication Methods

#### Direct Cluster Access

```json
{
  "Type": "ConnectionProfile:Kubernetes",
  "Name": "k8s_prod",
  "AuthenticationMethod": "ServiceToken",
  "KubernetesClusterURL": "https://kubernetes.default.svc",
  "ServiceTokenFilePath": "/var/run/secrets/kubernetes.io/serviceaccount/token",
  "Namespace": "production",
  "ConnectionTimeout": 50
}
```

#### Remote Spec Endpoint Authentication

```json
{
  "Type": "ConnectionProfile:Kubernetes",
  "Name": "k8s_remote_spec",
  "SpecEndpointURL": "https://spec-server.example.com",
  "SpecAuthenticationMethod": "OAuth2",
  "OAuth2TokenURL": "https://oauth.example.com/token",
  "ClientID": "client-id",
  "ClientSecret": "***",
  "AdditionalHeaders": {
    "Authorization": "Bearer token-value"
  }
}
```

#### Kubernetes Parameters

| Parameter | Purpose | Type | Default |
|-----------|---------|------|---------|
| **KubernetesClusterURL** | Cluster API endpoint | URL | https://kubernetes.default.svc |
| **ServiceTokenFilePath** | Token file location | File path | /var/run/secrets/.../token |
| **Namespace** | K8s namespace | String | default |
| **SpecEndpointURL** | Remote spec server | Optional URL | None |
| **ConnectionTimeout** | Timeout (seconds) | Numeric | 50 |

#### Remote Spec Endpoint Options

| Method | Parameters | Use Case |
|--------|-----------|----------|
| **BasicAuth** | Username, Password | Simple authentication |
| **OAuth2** | TokenURL, ClientID, ClientSecret | Token-based |
| **AWS IAM** | AccessKey, SecretKey, Region | AWS signature auth |
| **GoogleServiceAccount** | Service account key JSON | GCP integration |
| **CustomHeaders** | Key-value pairs | Header-based auth |
| **CustomBodyParameters** | Form data | Body parameter auth |

---

## Common Connection Profile Features

### Metadata

```json
{
  "Type": "ConnectionProfile:...",
  "Name": "profile_name",
  "Description": "Human-readable description",
  "Centralized": true,
  "CreatedBy": "admin_user",
  "CreatedTime": "2026-06-11T14:30:00Z"
}
```

### Connection Timeout

```json
{
  "ConnectionTimeout": 30  // Seconds until connection fails
}
```

**Guidelines:**
- AWS services: 20-30 seconds typical
- Azure services: 50 seconds (authentication overhead)
- GCP services: 20 seconds
- Kubernetes: 50 seconds (variable overhead)

### Secret Protection

**"Secrets in Code" Pattern:**
```json
{
  "SecretAccessKey": "{{SECRET:aws_secret_key}}",
  "ClientSecret": "{{SECRET:azure_client_secret}}"
}
```

---

## Integration with Control-M Jobs

### Container Job Execution

Connection profiles enable:

```json
{
  "Type": "Job:Container",
  "Name": "ecs_task",
  "ConnectionProfile": "prod_ecs",
  "ContainerImage": "myapp:latest",
  "ContainerName": "myapp_container",
  "ClusterName": "production",
  "TaskDefinition": "myapp_task_def"
}
```

### Job Properties Integrated

- **ConnectionProfile:** Profile name reference
- **Authentication:** Inherited from profile
- **Timeout:** Job-specific override of profile timeout
- **Retry:** Profile-level retry logic

---

## Best Practices

### Authentication Strategy

1. **Credential Storage**
   - Use "Secrets in Code" for sensitive values
   - Store access keys in secure vault
   - Rotate credentials periodically

2. **Multi-Account Setup**
   - Use Assume Role for cross-account access
   - Separate profiles per environment (dev, test, prod)
   - Role-based access control at profile level

3. **Connection Pooling**
   - Set appropriate timeouts per platform
   - Profile shared/centralized based on usage
   - Monitor connection failures

### Platform-Specific Practices

#### AWS ECS
- Use IAM roles in EC2 when possible (avoid access keys)
- Regional endpoint configuration per cluster
- CloudWatch integration for monitoring

#### Azure Container Instances
- Prefer Managed Identity on Azure VMs
- Service Principal for external agents
- 24-hour token validity for planning

#### GCP Cloud Run
- Service account key rotation annually
- Project ID validation before deployment
- Scope-appropriate service account roles

#### Kubernetes
- Service token for in-cluster jobs
- Remote spec endpoint for external scheduling
- Namespace isolation per environment

---

## Constraints and Limitations

| Constraint | Impact | Mitigation |
|-----------|--------|-----------|
| **Token validity (Azure)** | 24-hour Managed Identity limit | Refresh cycles, Service Principal for extended sessions |
| **Key rotation** | GCP service account key management | Annual rotation schedule, key versioning |
| **Timeout configuration** | Connection failures on slow networks | Increase timeouts per environment |
| **Credential escaping** | Special characters in secrets | Use "Secrets in Code" pattern |
| **Regional endpoints** | AWS region specification required | Store region in profile, support multi-region failover |
| **Namespace isolation** | Kubernetes access control | Define namespace per profile, RBAC enforcement |

---

## JSON Structure Patterns

### AWS ECS Profile

```json
{
  "Type": "ConnectionProfile:AWS:ECS",
  "Name": "prod_ecs_cluster",
  "AuthenticationMethod": "Secret",
  "AccessKeyID": "AKIA1234567890AB",
  "SecretAccessKey": "{{SECRET:aws_secret}}",
  "ECSURL": "https://ecs.us-east-1.amazonaws.com",
  "CloudWatchURL": "https://monitoring.us-east-1.amazonaws.com",
  "AWSRegion": "us-east-1",
  "ConnectionTimeout": 30,
  "Centralized": true,
  "Description": "Production ECS cluster in us-east-1"
}
```

### Azure Container Instances Profile

```json
{
  "Type": "ConnectionProfile:Azure:ContainerInstances",
  "Name": "azure_containers",
  "AuthenticationMethod": "ServicePrincipal",
  "SubscriptionID": "12345678-1234-1234-1234-123456789012",
  "TenantID": "87654321-4321-4321-4321-210987654321",
  "ApplicationID": "abcd1234-efgh-5678-ijkl-9012mnop",
  "ClientSecret": "{{SECRET:azure_client_secret}}",
  "LoginURL": "https://login.microsoftonline.com",
  "ManagementURL": "https://management.azure.com",
  "ConnectionTimeout": 50,
  "Centralized": true,
  "Description": "Azure production environment"
}
```

### GCP Cloud Run Profile

```json
{
  "Type": "ConnectionProfile:GCP:CloudRun",
  "Name": "gcp_production",
  "AuthenticationMethod": "ServiceAccount",
  "CloudRunURL": "https://run.googleapis.com",
  "ServiceAccountKey": {
    "type": "service_account",
    "project_id": "my-project-123",
    "private_key_id": "key123",
    "private_key": "{{SECRET:gcp_private_key}}",
    "client_email": "my-service@my-project.iam.gserviceaccount.com",
    "client_id": "123456789",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
  },
  "ConnectionTimeout": 20,
  "Centralized": true
}
```

### Kubernetes Profile

```json
{
  "Type": "ConnectionProfile:Kubernetes",
  "Name": "k8s_prod",
  "AuthenticationMethod": "ServiceToken",
  "KubernetesClusterURL": "https://kubernetes.default.svc",
  "ServiceTokenFilePath": "/var/run/secrets/kubernetes.io/serviceaccount/token",
  "Namespace": "production",
  "ConnectionTimeout": 50,
  "Centralized": false,
  "Description": "Production Kubernetes cluster"
}
```

---

## Notes for Planning Agents

1. **Five Container Platforms:** AWS ECS, AWS App Runner, Azure Container Instances, GCP Cloud Run, Kubernetes
2. **Authentication Hierarchy:** Cloud credentials → Regional config → Service endpoints → Timeout
3. **Credential Protection:** "Secrets in Code" pattern for sensitive fields
4. **Centralized vs. Local:** Global database storage vs. agent-specific profiles
5. **Multi-Auth Support:** IAM roles, access keys, service accounts, managed identities
6. **Cross-Account Access:** Assume Role capability for AWS platforms
7. **Token Management:** 24-hour Managed Identity for Azure, RSA keys for GCP
8. **Remote Spec Endpoints:** Kubernetes support for external scheduling servers
9. **Connection Timeouts:** Platform-specific defaults (20-50 seconds)
10. **Integration:** Connection profiles referenced by container jobs for end-to-end orchestration

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **API Type** | REST (JSON-based) |
| **Profile Types** | 5 container platforms (AWS ECS, App Runner, Azure ACI, GCP Cloud Run, Kubernetes) |
| **Format** | JSON |
| **Authentication Methods** | 10+ (Secret, IAM Role, Service Principal, Managed Identity, Service Account, OAuth2, BasicAuth, etc.) |
| **Storage Models** | Centralized (EM database) or local (agent-specific) |
| **Secret Protection** | "Secrets in Code" pattern with credential escaping |
| **Connection Timeout** | Configurable per platform (20-50 seconds default) |
| **Multi-Region Support** | AWS regional endpoints, Azure regions, GCP locations |
| **Cross-Account Access** | AWS Assume Role capability |
| **Remote Spec Endpoints** | Kubernetes external scheduling server support |
| **Integration** | Container jobs reference profiles for authentication |
