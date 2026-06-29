# Dataset Registration — Platform Architecture Reference

> **Sanitized pattern doc.** Derived from an enterprise Data & Analytics "Dataset
> Registration" Architecture Decision Record (ADR) plus a "Semantic Engine Metadata
> Collection Framework". All organization-specific identifiers — real application /
> SEAL IDs, internal system code-names, line-of-business names — have been replaced
> with placeholders (`<seal-id>`, `<app-id>`, `<LoB>`, generic role labels). The raw,
> identifier-bearing version is kept **internal-only** and gitignored at
> `drydocs/data/data-catalog/ccb-dataset-registration-architecture.md`; it must
> never be committed to this public repo (see [`PUBLISH-BOUNDARY.md`](../../../PUBLISH-BOUNDARY.md)).
>
> This document consolidates the platform capability model (all 10 capabilities), the
> dataset-registration concept, the four use-case patterns, the roles & responsibilities,
> the integration data flow, the underlying data architecture (domains / datasets /
> products), the semantic-engine metadata-collection & graph-hydration framework, and the
> systems / entities / functions metamodel into one cohesive reference.

## Context & Goals

Data delivery is treated like a manufacturing line: just as manufacturing has specialized
stations (design, fabrication, assembly, quality control, distribution), **data progresses
through distinct phases**, each with its own systems and metadata requirements.

| Phase | What happens | Key activities (sequence) |
|-------|--------------|---------------------------|
| **Design Phase** | Conceptual concepts are translated into technical specifications. Conceptual / logical / physical data models and quality rules are defined. Engineers build pipelines that extract & transform data. | Conceptual Design → Data Design → Physical Design → Pipeline Design → Pipeline Deployment → **Dataset Registration** |
| **Publishing Phase** | Pipelines execute, ingesting data into distributions in Data Platforms. Each Data Job Run generates lineage metadata (source → transform → target). Data Quality rules validate data. | Pipeline Execution → Quality Execution → Lineage Generation → Metrics Collection → Report Generation |
| **Consumption Phase** | Consumers discover & access datasets through catalogs. Data Access Policies govern visibility. Observability reports track usage. Generates consumption metadata. | Discovery → Request Access → Request Approval → Data Consumption |

> *Dataset Registration is the final activity of the **Design Phase** and the hinge that makes
> everything downstream discoverable and governable.*

### What is Dataset Registration?

Dataset registration is the process of **cataloging datasets into the Business Catalog**, making
them discoverable, governable, and consumable organization-wide. Storage platforms keep
*technical* catalogs for their own datasets, but the **Business Catalog provides
platform-independent cataloging** that unifies metadata across multiple storage systems. This
enables enterprise-wide data discovery and governance regardless of physical data location.

### Scope

Data Management's scope is **enterprise-wide**. Any platform or system within the organization —
whether from managed or non-managed platforms — can register its datasets in Data Management's
Business Catalog.

---

## Platform Capability Model

The platform is organized into **ten** Level-1 capabilities, each decomposed into Level-2
functional descriptions. Capabilities 1–5 cover design & cataloging; 6–10 cover quality,
discovery, access governance, audit, and observability.

| # | Capability (L1) | Functional Description (L2) |
|---|-----------------|------------------------------|
| 1 | **Business Model Design** | Reference Data Management (Metadata); Ontology Management; Data Concepts Management (Conceptual Business Models); Business Term Management (Business Glossary Terms); Business Term Classification & Tagging *(open)* |
| 2 | **Data Model Design** | Data Modeling Governance & Standards; Data Modeling Tooling & Practices; Data Modeling Process & Workflows Management; Data Model Registry Management & Distribution |
| 3 | **Dataset Registration & Catalog Integrations** | Logical Dataset Registration; Physical Dataset Registration; External Catalog **Sourcing** (e.g. partner finance / risk orgs); External Catalog **Distribution** (e.g. external catalog products); Technical Catalog Metadata Sourcing & Distribution (Snowflake, model layer, Databricks); Distributed Metadata Reconciliation & Reporting |
| 4 | **Metadata Scoring & Enrichment** | Metadata maturity scope management (standards, maturity, scoped datasets); Enrichment via Data Design Integration; Enrichment via Business Information Authoring; Enrichment via AI-Curated Consumption Metadata; Metadata Standards Maturity Scoring & Reporting |
| 5 | **Data Lineage** | Automatic Lineage Extraction; Lineage Visualization & Management; Lineage Impact Analysis & Compliance Reporting |
| 6 | **Data Quality Reporting** | Data Quality Rule Management; Data Quality Monitoring & Reporting; Data Contract Management; Data Quality SDK Development & Integration |
| 7 | **Data Search, Discovery & Access Enablement** | Self-Service Experiences; Advanced Search & Browsing (multi-faceted); **Semantic model-based search & discovery**; Deep Data Context Research (Business Definitions, Data Quality, Lineage, Usage, Security Classification, Ownership, …); Self-Service Access Role Discovery; Request Access Workflows |
| 8 | **Data Access Governance & Usage Monitoring** | **Data Use-Case Inventory Management (Purpose)**; Access Policy / Role Management; **Access Request Approval Management**; Access Impact Assessment (Metadata Change); Data Access & Usage Monitoring; Data Access Audit Reporting |
| 9 | **Data Audit, Compliance & Controls Reporting** | **Data Asset Ownership Management (Dataset & Data Model)**; Metadata Audit Reporting — Data Owners; Metadata Audit Reporting — Controls & Compliance |
| 10 | **Data Observability** | Unified view of data readiness & state; Data-state signal correlation & anomaly detection; Metrics monitoring, alerting & notifications; Actionable insights for reliability |

---

## Problem Statement

Four integration types exist for dataset registration (Managed Publishing, Federated Publishing,
External Catalog Federation, SoR Registration). Each follows a distinct pattern but shares a
common challenge:

> **There is no single integration point to orchestrate dataset registration across all
> use-cases.**

Today each system independently integrates with multiple Data Management systems, design
systems, and Data Storage platforms, which creates:

- **Integration complexity** — each client implements its own orchestration logic, duplicating effort.
- **Difficult maintenance** — changes to integration contracts require updates across multiple clients.

A **unified orchestration layer** is required: a single integration point that handles dataset
registration for all use-cases, enforces metadata quality standards, and simplifies client
integration.

---

## Suggested Approach

A solution that makes registration hassle-free and provides a single place to register, with:

- **API-Centric** — one API interface to deploy technical artifacts across Catalog, the publishing platform, and Data Management.
- **User-Experience Focus** — API plus CLI / Agent support for developer productivity, not just programmatic access.
- **Multi-System Coordination** — orchestration across design systems (model workflow, data-quality), storage platforms, and catalog systems.
- **Unified Orchestration** — centralized control supporting managed publishing, federated publishing, external catalog integration, and SoR use-cases.

### Proposed Solution

- **Long-Term:** a dedicated **Data Registration Orchestrator** component (requires design, dev, and test).
- **Interim:** **the Publishing Platform as Orchestrator** — until the Data Registration Orchestrator is production-ready, the data publishing & processing platform serves as the interim orchestration layer for Managed Publishing use-cases. (Focus on Data Products for near-term deliveries; this ADR is specifically about data-artifact deployment during Dataset Registration in Managed Platforms.)

### Build Recommendations

- **Ownership** of the Data Registration Orchestrator → **Data Management**.
- **The publishing platform continues** managed publishing until the orchestrator is ready.
- Orchestrator should **prioritize SoR registration and external-catalog federation** integrations to give timely coverage for wider use-cases.
- **DDL generation is an *assist* capability** — it usually needs review/update by data engineers. Build it as an independent, **API-first** capability (likely owned by Data Modeling or Data Platform) that multiple touch points can leverage.

---

## Roles & Responsibilities (Interim Solution)

| System | Roles | Responsibilities |
|--------|-------|------------------|
| **Data Management** | Author & manage metadata for data stored in data systems; validate that minimum metadata standards are met for any dataset; orchestration workflow for metadata authoring; support discovering data across systems. | Metadata management & change management of business metadata; **business-metadata release/propagation to production is the Business Catalog's responsibility**; **data registration is Data Management's responsibility**; Business Catalog observes metadata deployed in the Data Platform and reports on completeness & consistency; reporting on metadata quality (Lineage, Data Quality, Modernization reports). |
| **Data Publishing & Processing Platform** | Support designing the pipeline; orchestrate the publisher's experience (create objects in Data Platforms); translate user intent into deployment actions by executing the pipeline to ingest/transform data into storage. | Provide orchestration services for dataset registration during pipeline creation; integrate with the **model workflow system** to retrieve Physical Data Models; integrate with the **data-quality platform** to retrieve Data Quality Rules; enforce minimum metadata validation checks; register datasets in the Business Catalog; coordinate with Data Storage platforms for physical dataset creation. |
| **Data Platforms** | Data storage; data consumption. | Notify on any new distribution creation (consumed by Catalog); apply business metadata (access metadata) published by the Catalog. |

---

## Integration Data Flow

Integration between Data Management, Data Platform, and the publishing platform begins when an
engineer comes to **design a pipeline**.

**Pre-requisite actions** (assumed already done):

- Logical and physical model for new datasets is created and stored in the **model workflow system**.
- Business (centralized) quality rules for new datasets are present in the **data-quality platform**.

The flow then runs through **Data Pipeline Design Integration** (for new datasets), spanning
Data Orchestration Systems and Data Storage Systems, with the orchestrator coordinating the model
workflow system (models), the data-quality platform (quality rules), the storage platforms
(physical creation), and the Business Catalog (registration).

---

## The Four Use-Case Patterns

All four patterns share the same shape: a **Data Engineer** drives a first step (dev/publish/
create), then a second step routes **Source(s) → Dataset Registration Orchestrator → Target(s)**
into a PROD environment. What differs is *who owns the systems* (the central data org vs. external)
and *which catalogs/stores* are written.

> **Legend:** 🟩 Central data-org System · 🟧 External System · ⬛ Non-Prod Environment (dashed) · 🟪 Prod Environment (dashed).

### #1 — Managed Publishing
*Example: a line-of-business publishing its SoR datasets to the enterprise Data Lake.*

- **Step 1 — Dev Testing:** Data Engineer → DEV/TEST: Business Catalog, Data Pipelines, Technical Catalog, Data Storage — **all central data-org** systems.
- **Step 2 — Prod Deployment:** Data Engineer → Dataset Registration Orchestrator → Source(s)/Target(s) → PROD: Business Catalog, Data Pipelines, Technical Catalog, Data Storage — **all central data-org**.
- *Registration performed by the Managed Publishing Platform as part of publishing data to Data Platforms. E.g. Managed Data Lake.*

### #2 — Federated Publishing
*Example: a line-of-business integrating its (self-published) data into the enterprise Data Lake.*

- **Step 1 — Dev Testing:** Data Engineer → DEV/TEST: Business Catalog 🟩, **Data Pipelines 🟧**, Technical Catalog 🟩, **Data Storage 🟧** (publisher owns its own pipelines/storage).
- **Step 2 — Prod Deployment:** Data Engineer → Dataset Registration Orchestrator → Source/Target → PROD: Business Catalog 🟩, Technical Catalog 🟩, **Data Storage 🟧**.
- *Publishers have their own storage but share their catalog with the Managed Platform for consumption; dataset must be registered for governance & discovery.*

### #3 — External Catalog Federation
*Example: an external/partner org integrating its data into the enterprise Data Lake for analytical consumption.*

- **Step 1 — Data Publishing:** Data Engineer → PROD (external): Business Catalog, Data Pipelines, Technical Catalog, Data Storage — **all external 🟧**.
- **Step 2 — Catalog Federation:** Data Engineer → Dataset Registration Orchestrator → Source/Target → PROD: Technical Catalog 🟩, Business Catalog 🟩.
- *Catalogs share data via catalog federation; data is registered in the business catalog for governance & discovery.*

### #4 — SoR Data Registration
*Example: a line-of-business creating an inventory of data deployed across SoR data systems.*

- **Step 1 — Data Creation:** Data Engineer → PROD: **Transaction Systems 🟧**, **Data Storage (SoR)s 🟧**.
- **Step 2 — Data Cataloging:** Data Engineer → Dataset Registration Orchestrator → Source/Target → PROD: Business Catalog 🟩.
- *SoR tools/systems need their data registered in the business catalog for discovery purposes.*

### Use-Case Summary

| # | Integration Type | Description | Example |
|---|------------------|-------------|---------|
| 1 | Managed Publishing | Registration performed by the Managed Publishing Platform as part of publishing data to Data Platforms. | Managed Data Lake |
| 2 | Federated Publishing | Publishers own their storage but share their catalog with the Managed Platform; registered for governance & discovery. | A federated-publishing LoB |
| 3 | External Catalog Federation | Catalogs share data via catalog federation; registered for governance & discovery. | An external/partner org |
| 4 | SoR Registration | Tools/systems need their data registered in the business catalog for discovery. | A SoR-owning LoB |

---

## Data Architecture (Domains, Datasets, Products)

The data architecture is built around three fundamental elements — **data domains, datasets, and
data products** — with **data concepts** providing a conceptual/semantic layer above them.

### Definition & Purpose

- **Data Concepts** — help identify the entity a dataset / data product represents.
- **Data Domains** — organize data assets (datasets, data models, data products); used to determine ownership.
- **Data Products** — package a set of datasets made available for consumption (product perspective).
- **Dataset** — a collection of related data organized in a structured format (like tables).

### Organization Model

- **Dataset Organization** — datasets are organized within specific data domains (foundational building blocks).
- **Data Product Composition** — one data product can incorporate one or many datasets; the same dataset may be **reused** across products to avoid duplication and promote consistency.
- **Governance & Ownership** — each data product is assigned to **exactly one** data domain for clear accountability.
- **Conceptual Linkage** — data domains are conceptually linked to broader **data concepts**, providing a semantic layer for context & relationships.

#### Example domain structure

```
Data Concept layer:        Party  ──►  Account  ──►  Deposit Account  ──►  ...

Customer (Data Domain)     Account (Data Domain)         Deposit Account (Data Domain)
├─ Customer Contact        ├─ Account Asset              ├─ Account Balance
│   Name/Address/Email     │   Deposit Acc/Card Acc/...  │   Balance
├─ Customer Document       ├─ Account Profile            └─ Account Profile
│   Name/Address/SSN       │   Delinquent/Collection/        Account Type/Tier/Features
├─ Customer Legal Profile  │   HighVal Customer
│   Name/Address/SSN       └─ Account Documents
└─ Customer Account            1099K / Statement
    Banking/Cards/Loans
```

*Boxes nest as: Data Concept ▸ Data Domain ▸ Data Product ▸ Dataset.*

### Operating Model

| Component | Ownership | Naming Structure | SoR | ADS | Use Cases | Constraints | Uniqueness |
|-----------|-----------|------------------|-----|-----|-----------|-------------|------------|
| **Data Concepts** | Information Architecture | Multi-level; data domains hierarchical | `<concepts-api>` | DataHub | — | — | — |
| **Data Domains** | Information Architecture | Multi-level | `<concepts-api>` | DataHub | Provides namespaces for Datasets, Logical Data Models, Data Products | — | — |
| **Logical Data Model / Logical Dataset** | Data Domain | — | Modelling | DataHub | Design-time definition of what data *should* exist (a blue-print) | Data Domain used as namespace; established at creation; immutable for lifecycle | namespace (canonical data domain name) + Logical Dataset identifier; unique **within scope of data domain** |
| **Physical Data Model / Dataset** | Data Domain | — | DataHub | DataHub | Actual data stored in a specific format (Glue, Snowflake) — the house built from the blue-print | Logical Data Model identifier used as basis to **auto-generate** | namespace (canonical data domain name) + Physical Dataset identifier |
| **Data Products** | Data Products organization | — | DataHub | DataHub | — | Data Domain used as namespace; established at creation; immutable for lifecycle | namespace (canonical data domain name) + Data Product identifier |

> **Uniqueness principle:** every artifact is uniquely identified by *canonical data domain
> namespace + its own named identifier*. The data domain is fixed at creation and immutable for
> the artifact's lifecycle.

---

## Semantic Engine — Metadata Collection & Graph Hydration Framework

> Source: a *Semantic Engine Metadata Collection Framework* design document.

### Overview & Goal

The goal is a robust framework that **systematically collects metadata aligned with a defined
ontology**, ensuring the graph is hydrated with relevant, high-quality data elements. **The
ontology is the blueprint** — it specifies which data elements and relationships are required
for semantic enrichment.

### Key Components

1. **Ontology Definition** *(stored in version control)* — establish the ontology describing
   the domain (entities, attributes, relationships); keep it **versioned** and accessible to all
   stakeholders.
2. **Collection Mechanism** — automated processes that extract metadata from source systems
   (APIs, databases); **standardize metadata formats** for consistency.
3. **Metadata Mapping** — map ontology elements to available data sources / metadata fields and
   **identify gaps** where metadata is missing or incomplete.
4. **Graph Hydration Logic** — define transformation rules to convert collected metadata into
   graph **nodes and edges**, then **validate each graph element aligns with the ontology**.

### Worked Example — an Application (`<app-id>`)

**Collection** (via the catalog collection API `<catalog-api>`):

| Step | Artifact | How |
|------|----------|-----|
| 1 | **Dataset** | Collect datasets for an application identifier, filter by dataset name if present. `Dataset V3 → GET datasets` (+ filters). |
| 2 | **Data Element** | Returned alongside the datasets when querying as above. |
| 3 | **Distribution** | For each dataset identifier, get the distributions maintained for it. `Distribution V3 → GET distributions` (+ filters). |
| 4 | **DQ** | For each distribution identifier, get the DQ rules if defined. `GET Rules for distributions`. |

**Mapping** (ontology ↔ collected metadata):

| Step | Artifact | Mapping rule |
|------|----------|--------------|
| 1 | Dataset | *TBD* |
| 2 | **Data Element** | When a **term identifier** exists on a data element, map it to the respective **glossary term** from the Glossary details snapshot. |
| 3 | Distribution | *TBD* |
| 4 | DQ | *TBD* |

### Ontology Graph (Information Architecture) — Sample Hydration

The hydrated graph spans **six color-coded layers**. Node inventory by layer:

| Layer | Nodes |
|-------|-------|
| 🟩 **Business Glossary & Semantic Ontology** | Application (`<seal-id>`); Data Domain; Ontology; Business Term; Data Quality Definitions; Valid Values; Definition; Classification |
| 🟦 **Data Model** | Logical Data Entity; Logical Data Entity Relationship; Logical Data Element; Business Data Quality; Business Data Quality Rules; Technical Data Quality Rules; Physical Data Entity; Physical Data Entity Relationship; Physical Data Property |
| 🟧 **Business Data Catalog** | Data Product; Dataset; Distribution; Element; Property |
| 🟨 **Technical Data Catalog** | Table; View; Column; Event Schema; API Schema; Property; Data Lineage; Data Pipeline |
| 🟥 **Data Quality** | Data Subscription; Data Contract; TDQ; BDQ; Data Quality Checks; Data Jobs; Metrics; BDQ Results; TDQ Results |
| ⬜ **Data State Insight** | Query; Data Job Execution; Query Logs/Metrics; Job Results |

**Key relationships** (selected edges, source → edge → target):

- Application (`<seal-id>`) — *is associated with* → Data Domain
- Data Domain — *is associated with* → Data Product · Ontology · Business Term
- Business Term — *has relationship to* → Ontology; *Defines* → Logical Data Element; *has* → Definition / Classification / Valid Values / Data Quality Definitions
- Ontology — *is associated with* → Logical Data Entity
- Logical Data Entity — *is derived from* → Logical Data Entity Relationship & Business Data Quality; *has* → Logical Data Element; → *is derived from* → Physical Data Entity
- Logical Data Element — *is tagged with* → Definition / Classification / Valid Values / Data Quality Definitions; *is derived from* → Physical Data Property
- Physical Data Entity — *is associated with* → Physical Data Entity Relationship; *has* → Element / Physical Data Property
- Dataset — *is part of / is associated with* → Data Product; *has 1 or more* → Distribution
- Distribution — *is engineered from* → Physical Data Entity; *has* → Element / Property; *is deployed as* → Table / View / Event Schema / API Schema
- Physical Data Property — *is engineered from* → Property
- Data Subscription / Data Contract — *Has a* → TDQ / BDQ; Subscription *Subscribes to* → Distribution; Contract *is associated with* → Data Jobs
- Table / View / Event Schema — *has* → Column / Property; Data Jobs *Uses* → Column / View / Event Schema / API Schema
- Data Jobs — *produces* → Data Lineage & Metrics; *has* → Query / Data Pipeline / Data Job Execution
- Metrics — has subtypes → BDQ Results / TDQ Results / Job Results

> *This is a sample visualization of the target ontology, not an exhaustive edge list; it shows
> how the six layers connect glossary → model → catalog → technical → quality → state.*

---

## Metamodel — Systems, Entities & Functions

> Source: a *Metamodel Diagram — Systems, Entities & Functions.* Application IDs are shown as
> `<seal-id>` placeholders. Each system is classified as a **Metadata System** (🟩) or **Data
> System** (🟦); each contained entity is a **Metadata Entity** or **Data Entity** and carries a
> **function**: **Author** (⬜), **Observe** (🟧), or **Control** (🟨).

| System (generic role) | SEAL ID | Type | Representative entities / functions |
|--------|-----------|------|--------------------------------------|
| **Reference Data Hub** | `<seal-id>` | Metadata | Reference Data; Metadata Attributes; Term Valid Values; Authoring Governance |
| **Business Vocabulary** | `<seal-id>` | Metadata | Business Terms; Context & Definition; Access Classifiers; Data Concepts; Referenced Concepts; Change Process Workflows |
| **Model Workflow System** | `<seal-id>` | Metadata | Logical/Physical Data Models; Business Attributes; Quality/Platform Technical Metadata; Data Concepts & Glossary Term Associations; Change/Version Mgmt; **LDM & PDM Certification Process Workflows**; Logical/Physical Dataset Association |
| **Metadata Reporting** | `<seal-id>` | Metadata | Dataset Metadata; Metadata Standards; Dataset Ownership; Metadata Maturity Reporting & Scores |
| **Central Business Catalog** | `<seal-id>` | Metadata | Logical/Physical Datasets; Domain Object Definition; Business/Technical Metadata Attributes; Logical Model Association; Business/Access/Retention Attribute Change Workflows; Metadata Distribution Process Workflow; Data Job & Run Lineage; Design-time/Runtime Lineage Metadata & Reports; Data Access & Quality Reports |
| **Data Publishing & Processing** | `<seal-id>`, … | Data | Data Jobs; Data Job Run; Execution Schedule Metadata; Data Distribution Objects; Physical Data Model Association; Data Quality Rules Association & Execution; Data Quality / Lineage Reports; Job Deployment Process Workflow |
| **Data State Insight** | `<seal-id>` | Metadata | Data Observability Reports; Data Cost / Flow / Platform / Metrics Reports |
| **Data Quality Platform** | `<seal-id>` | Metadata | Data Quality Contracts & Rules; Data Contracts; BDQ/TDQ Rules; Change/Version Mgmt; Data Contract & Quality Reports; Data Contract Control Procedure; Data Quality Control |
| **Data Access Governance** | `<seal-id>` | Metadata | Data Access Policy; Data Obligation Restriction Policies; RBAC Role Enablement Policies; Data Access Reports / Monitoring / Audit Reports |
| **Data Platform(s)** | `<seal-id>`, … | Data | Data Distributions & Access Points; Physical Data Objects; Role Access Policy Metadata; Business/Access Attributes; Identity Roles; Data Distribution Access Metadata & Reports; Data Retention Metadata; Data Lifecycle Management; Data Access & Security Controls |

> **Reading the metamodel:** the left/center systems (reference data, vocabulary, model workflow,
> catalog, data-quality, data-access governance, metadata reporting, data state insight) are
> **metadata systems** that *Author* and *Control* metadata; the right-hand **data systems** (data
> publishing & processing, data platforms) *execute* and are *Observed*. Arrows between Catalog ↔
> Publishing ↔ Platforms show the metadata push (Author/Control) and the runtime feedback (Observe)
> loop.

---

## Glossary of Systems & Acronyms

> Generic functional terms only. Internal system code-names and SEAL IDs are intentionally omitted;
> see the internal twin for the organization-specific mapping.

| Term | Meaning |
|------|---------|
| **D&A** | Data & Analytics (the central data org) |
| **LoB** | Line of Business (e.g. an auto, cards, home-lending, or finance line) |
| **Publishing Platform** | Data Processing & Publishing Platform — interim orchestration layer |
| **DM** | Data Management |
| **Model Workflow System** | Design system holding logical & physical data models |
| **Data-Quality Platform** | Holds centralized data-quality rules |
| **Business Catalog** | Platform-independent catalog of registered datasets (discovery & governance) |
| **Technical Catalog** | Storage-platform-local catalog of its own datasets |
| **DataHub** | Authoritative Data Store (ADS) for several components |
| **`<concepts-api>`** | System of Record (SoR) for data concepts & domains |
| **`<catalog-api>`** | Catalog collection API used by the Semantic Engine (Dataset V3 / Distribution V3 / DQ rules) |
| **SoR** | System of Record |
| **ADS** | Authoritative Data Store |
| **Snowflake / model layer / Databricks** | Technical catalog sources |
| **BDQ / TDQ** | Business Data Quality / Technical Data Quality (rules, checks, results) |
| **LDM / PDM** | Logical Data Model / Physical Data Model (with certification process workflows) |
| **RBAC** | Role-Based Access Control |
| **SEAL ID** | Enterprise application identifier (shown here as `<seal-id>`) |

---

*Derived from the source ADR + Semantic Engine images; section ordering normalized for reading
flow, identifiers sanitized. Where the source left an item open (e.g. "Business Term Classification
& Tagging ???" or a "TBD" mapping step) it is preserved as open above. The ontology graph and
metamodel are captured as node/system inventories with key edges — faithful to the diagrams without
claiming an exhaustive edge list.*
</content>
</invoke>
