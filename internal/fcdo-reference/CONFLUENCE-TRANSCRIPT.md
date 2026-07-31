# JPMC Confluence — Screenshot Transcription Log

**Space:** DATAPUBSTRATEGY (Firmwide Data Publishing Frameworks)
**Host:** `confluence.prod.aws.jpmchase.net`
**Transcribed:** 2026-07-30

---

## Capture Index

**117 screenshots · 22 sources · every file in `C:\coding\@SCREEN-SHOTS` transcribed.**

### DATAPUBSTRATEGY — Firmwide Data Publishing Frameworks

| # | Source page | Page ID / URL slug | Shots | Coverage |
|---|---|---|---|---|
| A | Identifiers Specification | `5574548071/Identifiers+Specification` | 3 | **Complete** — title → Appendix II |
| B | Telemetry Framework | `5772894333/Telemetry+Framework` | 1 | §4.3 → §5 intro only (single mid-document shot) |
| C | Data Mapping Framework – Draft | `5816635920/Data+Mapping+Framework+-+Draft` | 19 | Title → §7.3 Example 3. §7.4–§10 not captured |
| D | Provenance Framework | `5567744239/Provenance+Framework` | 13 | **Complete** — title → §12.5 OpenLineage→PROV |
| E | [WIP] Provenance CDAO Framework | `6194465802/WIP+Provenance+CDAO+Framework` | 10 | §3 → §12.5 end. Near-identical to D |
| F | Schema Metadata Framework | `5567745346/Schema+Metadata+Framework` | 9 | §4 → §6.4.1.3.1. §1–§3 and §7+ not captured |
| G | Business Processes Metadata Framework | `5762464960/Business+Processes+Metadata+Framework` | 9 | Title → §6.2. §6.3–Appendix A not captured |
| H | Data Authority Metadata Framework | `5899885596/Data+Authority+Metadata+Framework` | 3 | §5 → §9 heading. §1–§4 not captured |
| I | Taxonomy Framework | `5772894415/Taxonomy+Framework` | 2 | §4.1 → §5.1.1 (clipped). §1–§4 and §5.1.1+ not captured |
| U | People and Organizations Framework | `6030480492/People+and+Organizations+Framework` | 22 | Title → §9.3.1 end. §6 examples and §7–§8 clipped |

### DATAPUBSTRATEGY — Thought Pieces / backlog

| # | Source page | Page ID / URL slug | Shots | Coverage |
|---|---|---|---|---|
| K | Ontology Design Recommendations | *(Thought Pieces child)* | 1 | Complete single-page note |
| L | Connecting a Physical Data Model to an Upper Ontology | `5648554621/Connecting+a+Physical+Data+Model+to+an+Upper+Ontology` | 4 | Contents → §3.7. §3.8 and §4 Discussion not captured |
| N | Thought Pieces (index of child-page excerpts) | `5140788914/Thought+Pieces` | 1 | Partial — one screenful of excerpts |
| O | Technical Backlog | `5153183917/Technical+Backlog` | 1 | Backlog + Actionable Topics, clipped at bottom |
| P | Discussion About The Possible Form of AI & Agent Native Data Benchmarks | `5938531925/…AI+Agent+Native+Data+Benchmarks` | 2 | **Complete** |
| Q | Discussions on AI Agents for Managing Data Access | `6206552010/Discussions+on+AI+Agents+for+Managing+Data+Access` | 1 | **Complete** |

### Other Confluence space

| # | Source page | URL | Shots | Coverage |
|---|---|---|---|---|
| M | Our Vocabulary (AWM Data Mesh Strategy) | `spaces/DATAMESHANALYTICS/pages/4373543268/Our+Vocabulary` | 5 | Official Sources → Decision Log / Mesh workshop |

### Not Confluence

| # | Source | What it actually is | Shots |
|---|---|---|---|
| J | Taxonomy Information | `ccb-governance.gaiacloud.jpmchase.net/reference-data/taxonomies` — a reference-data web app (3 tabs of taxonomy rows) | 3 |
| R | Application | OneNote-style note page, two ServiceNow/SEAL/Verum ER diagrams | 1 |
| S | About the model | Neo4j SDLC graph-model documentation | 1 |
| T | SCRAPE WEBPAGE CONTENT CHECK | AI chat/tool output — ServiceNow CMDB class-tree analysis | 1 |
| V | FCDO Ontology Builder | A `SKILL.md` file + an AI coding-assistant review session comparing it to "DryDocs" | 5 |

Full host prefix for Confluence sources: `https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/`

**Not yet captured / known gaps** — see [Gaps & Follow-ups](#gaps--follow-ups) at the end.

---

# A. Identifiers Specification

> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5574548071/Identifiers+Specification
> **Page tree location:** Firmwide Data Publishing Frameworks → Identifiers Specification
> **Created by:** Marin, James · **Last updated by:** Tong, Jan on May 27, 2026 · 8 minute read
> **Screenshots:** `DATAPUBSTRATEGY-Identifiers-specs.png`, `DATAPUBSTRATEGY-Identifiers-specs-2.png`

## Identifiers Specification

### JPMC Firmwide CDAO – CDO Strategy Specification: Identifiers

This is a technical specification document - not a JPMC Standard

**Data Publishing Council Approval Date:** Mar 2025 (Driven via DDLC)

### Status of This Memo

This document specifies a JPMC Firmwide framework to track protocol for the firmwide community and requests discussion and suggestions for improvements. Distribution of this memo is unlimited.

### Abstract

A JPMC Data Identifier (JDI) is a serialization framework that represents identifiers as a compact string of characters and symbols for identifying an abstract or physical data resource. This document defines the syntax of a unique identifier URL and guidelines for their use. A URL (Uniform Resource Locator) is a particular type of URI that not only serves as an identifier but also specifies how to locate a resource — *RFC 3986: URI, URL, and URN*.

This document defines a grammar that is a firmwide framework to be used on all data published and shared across the firm. It is to be used such that an implementation can parse the common components of a URL reference without knowing the scheme-specific requirements of every possible identifier type. This document does not define a resolution or implementation for the URL. This task will be performed by the individual LoBs/CFs and Firmwide Product teams.

### References

This specification document pulls information from internal discussion, internal definitions, and external/open source definitions. Some references can be found below: • JMOF • JRN • RFC 3986: URI Generic Syntax • ISO/IEC 9834-8

### 1. Introduction

This document describes and specifies an identifier template, which defines a format that is clear, accessible, and constructed in a meaningful way, making it possible to be reconstructed, especially when the consumers of the data are not explicitly known. When a publisher creates datasets and shares it between LoBs/CFs, the JDI will follow the specification outlined in this document. The JDI Template is used for the following distinct purposes:

- **Self-Describing:** Identifiers convey essential information about the identifier itself, allowing users and systems to understand its context and publisher.
- **Efficient data retrieval:** Identifiers allow systems to locate and access data and metadata about specific data elements without ambiguity, enabling quick and precise data retrieval.
- **More efficient cross system work:** Identifiers make working across organizational and system boundaries easier, by reducing the needs for translation between different systems, and allowing data to be reused quickly and safely.
- **Data Integrity:** Identifiers help maintain data integrity by ensuring that each data element is distinct and can be accurately references, reducing the risk of errors or duplication.

#### 1.1. Key Requirements

The objective of this specification is to provide a unique reference for resources firmwide and enable efficient management, retrieval, and utilization of data. To achieve this requirement, the following requirements are to be achieved with this specification:

1. **Scalable:** Able to manage a massive scale of unique identifiers to support firmwide efforts. JPMC generates billions of events, datasets, tables, and logs every day and these need to be uniquely identified with a reduced risk of collision.
2. **Federated:** No single entity is required to create and store data identifiers. LoBs/CFs can individually create and assign their own identifier.
3. **Consistent:** Does not have anything embedded that could change within the identifier itself. An identifier does not change even if the data is moved, modified, or accessed in different systems. It maintains stability and integrity.
4. **Suitable:** Appropriate for any data use cases. (e.g., data sets, fields, tables, distributions, events, and event queues), as JPMC has different data use cases, having suitable identifiers makes it easier to manage complex databases.
5. **Framework Compliant:** Meets established specifications or criteria set by recognized internal and external frameworks. It is expected that this identifier specification within JPMC can be supported by off-the-shelf libraries and vendor tooling.
6. **Recognizable:** The identifier should be easily recognized and interpreted by systems, applications, and humans as a JDI. The identifier specification should allow for an efficient retrieval and input of information by internal systems.

##### 1.1.1. Assumptions / Decisions

During the discovery and development process, the following key component decisions were identified by firmwide team members from the LoBs, CFs, and CDAO:

1. Data should be identified with a namespace.
2. A domain should be provided from a central provider to avoid collisions and vendor lock.
3. Need to add constraints on subdomains of the root authority, but ensure they are not too restrictive.
4. Constraints on the identifier specific portion of the JPMC identifier are not required, but namespace owners are encouraged to use UUIDs and/or unique pathnames to reduce the likelihood of collisions.
5. If versioning is to be provided it must be assigned to the URL in a common expected format, but not stored in a central, firmwide location.

#### 1.2 Scope

This specification is a firmwide requirement. LoB/CFs may define more restrictive forms of identifiers, provided they are in compliance with the firmwide framework outlined in this specification.

### 2. Key Components

An identifier is to follow a simple structure of domain + value, often where the domain is human readable to determine the structure.

- The domain is unique within the full scope and is defined with a firmwide prefix and paths associated with LoB/CFs.
- The value is defined utilizing a unique or randomized identifier based on alphanumeric values.

#### 2.1. Defining an identifier

A specification for the JPMC identifier should be represented with a namespace and an identifier. The namespace is made up of a domain, path, and optional sub-paths to further define the structure. This can be represented in the following simplified format:

```
┌───────────── Authority/Namespace Domain ─────────────┐
│  ┌───────────┐  ┌──────────────┐  ┌──────────┐       │   ┌────────────┐
│  │ Authority │  │ Path         │  │ Sub-Path │       │   │ Identifier │
│  │           │  │ (Sub-Domain) │  │          │       │   │            │
│  └───────────┘  └──────────────┘  └──────────┘       │   └────────────┘
└──────────────────────┬───────────────────────────────┘         │
                       ▼                                         ▼
            markets.cib.data.jpmorgan                        identifier
```

Namespaces within JDIs are composed of segments, which are separated by periods (`.`). The identifier is separated from the namespace with a forward slash (`/`). The specific components and values used in the segments of a namespace and the identifier are constrained by the rules in following sections. The namespace and identifier are required fields.

##### 2.1.1. Namespace

A namespace is a Collection of names that obey three key constraints: each collection of names is unique, each individual name is assigned in a consistent way, and aligns with a common definition. It is comprised of multiple components such as the domain/root, path, and subsequent identifying paths. A namespace definition is comprised of these characteristics:

1. **Uniqueness constraint** means that a name within the parent namespace is never reassigned to a different identifier minting authority. This holds true even if the name itself is deprecated or becomes obsolete.
2. **The consistent assignment constraint** means that a name within the URL namespace is assigned by an organization or created in accordance with a process or algorithm that is always followed.
3. **The common definition constraint** means that there are clear definitions for the syntax of names within the URL namespace and for the process of assigning or creating them.

This specification will require that all unique identifiers created for data entities belong to a specified namespace. (e.g., a top level domain such jpmorgan and a subdomain such as CDAO)

A standardized set of domains that is commonly shared across the firm will be created to reduce conflicts for cross LoB/CF Data Identifiers, thus ensuring unique naming. This centralized authority is to be maintained by the CDAO Product/Platform team.

Sub-domains or paths will be owned and maintained by the sub-domain owner (e.g., CDAO, CCB, CIB, AWM, etc.).

**Note:** The namespace of an identifier does not indicate the owner of the data. For example, `cib.data.jpmorgan/data1234` is a namespace that was created by CIB, and does not imply that the data is owned by CIB. To determine the owner, one would need to dereference the identifier and access the metadata.

###### 2.1.1.1. Authority/Root

The authority/root is a top level identifier (e.g., `data.jpmorgan`). The authority/root is used to allow a centralized prefix provider from the CDAO for use across the firm. This concept will be owned and maintained by the CDAO and is a required component of the identifier specification.

###### 2.1.1.2. Path

The Path/Sub-Domain is a path field that allows the LoBs/CFs to group identifiers under a top level LoB/CF path and further federate ID creation without collisions. (e.g., CDAO, CCB, CIB, AWM, RMC). This concept will be owned by the LoBs/CFs depending on the path and is a required component of the identifier specification.

###### 2.1.1.3. Sub-Path

This sub-domain or sub-path field allows the LoBs/CFs to further group identifiers under additional paths. The number of sub-domains/paths is not limited though it is recommended to follow a simple approach of grouping where possible. This concept will be owned by the LoBs/CFs/CDAO depending on the path and is an optional component of the identifier specification.

##### 2.1.2. Unique Identifier

The unique identifier is a unique set of characters defined within the namespace. Any string (subject to the constraints of the URI spec *RFC 3986*) can be used. Segments of an identifier are separated with a forward slash (`/`) (e.g. `'path/uniqueId/'`). Where uniqueness of identifiers cannot be guaranteed, Universally Unique Identifiers (UUIDs) are encouraged for assigning unique identifiers. UUIDs are 128-bit alphanumeric strings that identify a digital entity. They are defined by the *ISO/IEC 9834-8* standard. This concept will be owned by the LoBs/CFs/CDAO depending on the path and is a required component of the identifier specification.

### 3. Examples

Utilizing the definitions above, generating a Uniform Resource Locator or URL will follow two patterns:

#### 3.1 UUID Example

| Component | Owner | Example |
|---|---|---|
| Root | JP Morgan Chase | data.jpmorgan |
| Path | CIB | cib |
| Sub-Path | Markets | markets |
| Identifier | sub-path owner | 7b085b7d-2bce-4f0a-88ef-baae4653a8c3 |

To bring the complete URL together we expect the following: `https://markets.cib.data.jpmorgan/7b085b7d-2bce-4f0a-88ef-baae4653a8c3`

#### 3.1 Pathname Example

*(captured in `Screenshot 2026-07-30 181337.png`)*

| Component | Owner | Example |
|---|---|---|
| Root | JP Morgan Chase | data.jpmorgan |
| Path | CIB | cib |
| Sub-Path | Markets | markets |
| Identifier | sub-path owner | path/uniqueId |

To bring the complete URL together we expect the following: `https://markets.cib.data.jpmorgan/path/uniqueId`

### Appendix I - Catalog Product Requirements

#### I.1 URL Versions

Versions are assigned values identifying the current state of the dataset, whether a current or previous version. Versions are expected to follow a common format such as increasing numerical values, semantic versioning number or a date and time combination. This concept will be owned by the LoB/CF that owns the sub-domain and is an optional component of the specification.

When a version of a URI is required, the version indicator is separated from the identifier with a question mark (?).

Example of a version indicator in a complete URL: `https://markets.cib.data.jpmorgan/path/uniqueId?version=3.2`

#### I.2 Requirement for moving a URL

When a URL is permanently removed it must support a HTTP 301 code indicating that the requested resource has been permanently moved to a URL. The HTTP 301 code is a redirection status code that informs the client that the resource is no longer available at the original URL and provides the new URL where the resource is found.

### Appendix II - Summary Table

Simplified specification in a table format:

| Part | Description | Owner | Required? |
|---|---|---|---|
| 2. Namespace | An identifier for a group or entity that can allocate providers to other groups. Groups identifiers to prevent conflicts, ensuring unique names. | CDAO/LoBs/CFs | Required |
| 2.1 Root | A top level identifier (e.g. com.jpmorgan). The authority/domain is used to allow a centralized prefix provider from CDAO. | CDAO | Required |
| 2.2 Path | A required field that allows the LoBs/CFs to group their identifiers under a top level LoB/CF path and further federate id creation without collisions (e.g. CDAO, CCB, CIB, AWM, RMC, etc.). | LoBs/CFs | Required |
| 2.3 Sub-Path | An optional Path field that allows LoBs/CFs to further group their identifiers under additional paths (e.g., Product names and sub-LoBs). | LoBs/CFs | Optional |
| 3. Identifier | The unique identifier within the namespace. Any string (subject to the constraints of the URI spec RFC 3986) can be used. Where uniqueness of identifiers cannot be guaranteed, Universally Unique Identifiers (UUIDs) are encouraged for assigning unique identifiers. | TBC | Required |
| A.I Version | If versioning is to be provided it must be assigned to the URL in a common expected format, but not stored in a central, firmwide location. | TBC | Optional |

---

### Page tree sidebar (as shown)

Firmwide Data Publishing Frameworks → Process, Council, and Working Groups · vteam Agent Ready Data · Descriptive Metadata Framework · Data Product Framework · Provenance Framework · Usage Rights Framework · Data Quality Framework · Date and Time Framework · Postal Address Framework · Party Identifier Framework · Schema Metadata Framework · **Identifiers Specification** · Knowledge Base Framework · Data Contracts Framework (DPROD Data Contracts) · Telemetry Framework · Drafts and Upcoming Frameworks · Data Mapping Framework

Then: Data Contracts · Data Authority Metadata Working Group · Enterprise Glossary · Thought Pieces · Conferences, Vendor Presentations, etc. · Proofs-of-Concept (POCs) · Technical Backlog · Client360 proposed data model · Working Groups Best Practices · Firmwide Namespace Catalog · List of Lists · Tools and Utilities

---

# B. Telemetry Framework

> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5772894333/Telemetry+Framework
> **Screenshot:** `open-telemetry-ss-1.png`
> **Note:** Single mid-document capture. Sections 1–4.2 and everything after §5 intro are not captured.

## 4.3. Information to be Included in Telemetry Data

```
A) For each Log Record, the following fields are required unless marked:
     a. A name for the log record, identifying its type or class.
     b. A timestamp marking when the recorded event occurred, or when the event was observed if the former is not known; ideally both.
     c. The content of the log record.
     d. The name of the service emitting the log.
     e. An identifier for the trace recorded by the log (optional).
     f. An identifier for the span recorded by the log (optional).
     g. W3C trace flags (optional).
     h. Severity information for the log, both textual and numeric (optional).
     i. The logical unit within the emitting application code with which the log record can be associated (optional).
     j. Additional information about the event structured as attributes (optional).

B) For each Span, the following fields are required unless marked:
     a. A name for the span, identifying its type or class.
     b. The identifier for the span's parent, if applicable.
     c. The time when the span began.
     d. The time when the span ended.
     e. The name of the service emitting the span.
     f. The Span Context, which includes:
          i.   The identifier for the trace of which this span is a part.
          ii.  The span's identifier.
          iii. W3C trace flags (optional).
          iv.  Vendor-specific trace information (optional).
     g. Additional information about the event structured as attributes (optional).
     h. Connections to related spans (optional).
     i. The status of the span, as defined by OpenTelemetry (optional).
     j. The kind of the span, as defined by OpenTelemetry (optional).

C) For each Trace, the following fields are required unless marked:
     a. The identifier for the trace.
     b. Any spans that are part of the trace.
     c. The name of the service emitting the trace.
     d. The time when the trace began (optional).
     e. The time when the trace ended (optional).

D) For each Metric, the following fields are required unless marked:
     a. A name identifying the metric.
     b. The time when the measurement was recorded.
     c. The numerical value associated with the measurement.
     d. The unit of measure for the metric.
     e. The name of the service emitting the metric.
     f. Additional information about the metric structured as attributes (optional).
     g. Additional metadata about the source of the metric (optional).

E) For any Entity, the following fields are required unless marked:
     a. A type, e.g. "service" or "host".
     b. An identifier.
     c. A textual description of the entity (optional).

F) For any Resource, the following fields are required unless marked:
     a. Entities associated with the resource.
     b. Attributes identifying the resource.
```

## 4.4. Available Open Frameworks

Within the firm, telemetry instrumentation and data MUST follow the FCDO-approved Telemetry Framework. Any implementation of observability instrumentation and telemetry data within the firm MUST therefore adhere to the requirements specified below. Additionally, all date and time values should adhere to the Data Publishing **Date and Time Framework**.

## 5. Telemetry Components and Fields

Telemetry data are defined in terms of the kinds of entities they represent and the fields that apply and persist throughout the observability lifecycle. The required and recommended fields for each type of telemetry data are specified below.

A few important concepts include the following:

1. The type `map<string,Attribute>` is a key-value pair mapping a string key to an Attribute.
2. An `Attribute` is a pair of a key, which MUST be a non-null, non-empty string, and a value, which MUST be a valid `AnyValue`.

*(capture ends here)*

---

# C. Data Mapping Framework – Draft

> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5816635920/Data+Mapping+Framework+-+Draft
> **Breadcrumb:** Pages / … / Drafts and Upcoming Frameworks · 573 views
> **Created by:** Henninger, Scott · **Last updated on:** Jul 21, 2026 · 34 minute read
> **Screenshots:** `DATAPPUBSTRATEGY-data-mapping.png`, `DATAPPUBSTRATEGY-data-mapping-readme-model-layers.png`, `-2` through `-17`

**DRAFT VERSION** - This document is a draft version of the Data Mapping Framework. It is superseded by **Data Mapping Framework**.

**Effective Date:** TBD

## Contents

1. Summary
2. Changes from Previous Version
3. Data Mapping Framework
   - 3.1. Key Definitions for Data Mapping Framework
   - 3.2. Relationship to Other Data Publishing Frameworks
4. Key Requirements for Data Mapping
   - 4.1. Open Standard Requirements
   - 4.2. Standard Access Method
   - 4.3. Definition of Mapping properties
   - 4.4. Available Open Frameworks
5. Classes and Associated Properties for Data Mapping
   - 5.1. Namespace Declarations
   - 5.2. Classes and Associated Properties for Data Mappings
     - 5.2.1. Mapping Set Class Definition
     - 5.2.2. Mapping Set Property Definitions
     - 5.2.3. Mapping Class Definitions
     - 5.2.4. Mapping Property Definitions
     - 5.2.5. Model Element Class Definition
     - 5.2.6. Model Element Property Definitions
     - 5.2.7 Specifying Path Expressions
       - 5.2.7.1 Path Navigation
       - 5.2.7.2 Path Filtering
       - 5.2.7.3 Path Indexing
       - 5.2.7.4 Path Casting
   - 5.3 Properties for Semantic Mapping Relationships
6. Overview of Data Mapping Framework Entities and Relationships
7. Specifying Data Mappings – Representative Examples
   - 7.1. Example 1: Semantic Alignment (realizes / represents)
   - 7.2. Example 2: Derivation: CONCAT in SQL
   - 7.3. Example 3: Physical-to-Physical Mapping with Column Multiplication
   - 7.4. Example 4: Cross-Technology Physical-to-Physical Mapping
   - 7.5. Example 5: Logical-to-Conceptual Mapping
   - 7.6. Example 6: Classification Mapping
8. SHACL Verification of Examples
9. Guiding Principles and Document Information
10. Appendix A: Mapping Type Concept Scheme

## 1. Summary

Modern enterprises maintain data across multiple layers of abstraction—physical storage schemas (SQL DDL, JSON Schema, Avro), logical data models (often authored in UML or ER diagrams), and conceptual or business ontologies. Keeping track not only of how elements at one layer relate to elements at another, but also of how semantically equivalent elements align within the same layer (e.g., table-to-table across databases), is critical for data governance, lineage analysis, impact assessment, regulatory reporting, and master-data management.

This document defines the Data Mapping Framework, a formal data-mapping framework that links the physical, logical, and conceptual layers of data-model abstraction. The central premise is that regardless of how a model is originally authored — whether as SQL DDL, a UML class diagram, a JSON Schema, or an ER model — an RDF representation of the model, such as defined in the **Schema Metadata Framework**, is created and all mappings operate between these RDF representations. This uniform representation layer means the framework does not map native artifacts directly; instead it maps the technology-neutral RDF descriptions of those artifacts to one another, ensuring that mappings are portable, queryable, and decoupled from the authoring tool or storage technology.

The framework specifies machine-readable metadata about mappings and is designed for use by AI (LLM) agents — both as consumers that traverse a contextual graph of data-element relationships, and as producers that document new mappings. By making mapping knowledge structured, self-describing, and accessible to intelligent systems, the framework enables agents to reason about how business concepts relate to their implementations across technologies. Organizations routinely store the same business concepts in many different technologies: a "Consumer Banking Account" may exist as a relational table in Postgres, a document in JSON, and a record in Avro. Without a rigorous mapping layer, knowing that these representations refer to the same real-world concept requires manual effort that is error-prone and difficult to maintain. The framework addresses this by organizing mappings as sets of element-to-element relationships between RDF model elements — each mapping set groups the individual attribute-level correspondences between a pair of RDF-described models — and by supporting classification mappings that associate model elements with taxonomy concepts. This enables bidirectional navigation across model layers: from a physical column up to the conceptual definition it implements, or from a business concept down to every system that stores data about it, regardless of the underlying storage technology. This supports critical capabilities including data lineage (tracing data from concept through all implementations), impact analysis, regulatory reporting, and — by bridging the gap between how business users think about data and how it is actually stored in systems — a shared understanding across technical and business teams and a contextual graph that AI agents can traverse to discover meaning and provenance.

The framework is organized into two parts. The first part, Mapping Metadata, defines the administrative envelope — identifiers, creators, dates, types, and mapping sets that group element-to-element mappings between models. The second part, Mapping Relationships, captures how elements relate across model layers through semantic alignment (realizes, represents, wasDerivedFrom). Together, these parts provide the structured, machine-readable metadata that AI agents need to discover, traverse, and reason over data mappings across the organization.

This framework builds on the **Schema Metadata Framework**, which specifies how schemas — regardless of their native format — are described as technology-independent, machine-readable RDF artifacts, including RDFS/OWL vocabularies and SHACL shapes. The Mapping Framework extends this foundation by capturing relationships between elements within those RDF representations, linking each model element back to the `jpmv:SchemaMetadata` instance that defines its schema. Because both source and target models are expressed in RDF, mappings form a single interconnected graph that AI agents and governance tools can query uniformly.

The framework is built on W3C Semantic Web technologies, leveraging established standards including RDF, RDFS, OWL, Dublin Core Terms, PROV-O, SKOS, VoID, R2RML, and RML. This standards-based design ensures that mapping definitions are interoperable, queryable, and readily consumable by both existing data-governance tooling and next-generation AI systems. The framework chooses RDF as the implementation language to be compatible with other AI and Agent Native Data Frameworks — particularly the Schema Metadata Framework — to draw on industry standards, and for its native ability to model data schemas and their relationships.

## 2. Changes from Previous Version

This is the first version of this Framework.

| Version | Date | Description of changes |
|---|---|---|
| 1 | 2026-06-24 | Initial version |

## 3. Data Mapping Framework

This framework is designed to cover the Data Mapping ontology and vocabulary at the Firm. This document defines a, standards-based ontology for recording the creation, maintenance, and lifecycle of formally defined mappings between data-model elements. It provides a rigorous yet accessible metadata vocabulary that enables teams to:

- Organize mappings as sets of element-to-element correspondences grouped under a mapping set that carries shared metadata.
- Record the agent, human or system, that created or modified a mapping and when.
- Classify mappings by type (e.g., physical-to-logical, logical-to-conceptual, classification).
- Document how model elements relate to other elements or taxonomy concepts, supporting navigation across and within model layers.
- Leverage well-known Semantic-Web standards (RDF/RDFS, Dublin Core, SKOS, PROV) so the metadata is interoperable, tool-agnostic and readily consumable by AI agents.

### 3.1 Key Definitions for Data Mapping Framework

| Term | Definition |
|---|---|
| **Data Mapping** | A formal linkage between a source model element and a target model element (or classification term) that enables bidirectional navigation across conceptual, logical, and physical layers for lineage, impact analysis, and governance. A mapping may be an individual element-to-element relationship or a classification mapping. |
| **Mapping Set** | A named collection of related element-to-element mappings that together describe the correspondence between two models (e.g., all attribute mappings between a physical table and its logical counterpart). A mapping set carries shared metadata (title, creator, dates, type) and its members references the Mapping Set via `dcterms:isPartOf`. |
| **Data Mapping Metadata** | The standards-based "envelope" that records the who/what/when/where of each mapping (e.g., identifier, creator, dates, source, target, type, confidence, status), expressed with RDF vocabularies for interoperability and discovery. |
| **Classification Mapping** | A mapping that classifies/categorizes a model element by associating it with a taxonomy/glossary term rather than with another model element. The source is a model element and the target is a term from a controlled vocabulary or taxonomy (ideally but not mandatorily a SKOS Concept) |
| **Mapping Expression** | An expression that captures how a mapping is defined. This is intended to show what the mapping represents and is not a transformation rule. |
| **Model Layers** | The abstraction levels across which mappings connect elements, allowing traversal from a business concept to all its implementations and from any physical attribute up to its conceptual definition and across peers. |
| **Conceptual Layer** | The business-level ontology where concepts and semantics are defined independent of implementation, enabling navigation from a business concept to all its system realizations. |
| **Logical Layer** | The technology-agnostic model of data structures and attributes that sits between business concepts and concrete storage, providing a stable target for mappings from both conceptual and physical representations. |
| **Physical Layer** | The concrete storage schemas and artifacts (e.g., SQL DDL, JSON Schema, Avro) where data is actually persisted and from which mappings can navigate up to logical and conceptual definitions and across to peer implementations. |
| **Semantic Mapping Relationship** | Controlled categories (e.g., Physical↔Logical, Logical↔Conceptual, Physical↔Physical, Physical↔Conceptual, Logical↔Logical, Classification) used to classify the nature and direction of a mapping for consistent governance and querying. |
| **Model Element** | An identifiable schema item (such as a column, JSON property, or ontology attribute) that participates in a mapping and is annotated with its schema reference, access point, and Semantic Mapping Relationship to another Model Element for end-to-end traceability. In classification mappings, the source is a model element while the target is a taxonomy concept (`skos:Concept`). |
| **Taxonomy Concept** | A uniquely identified, abstract idea or category within a controlled vocabulary that represents a distinct meaning or classification used for organizing and describing information. |

### 3.2 Relationship to Other Data Publishing Frameworks

Mapping metadata operates alongside other data-publishing frameworks – most notably the **Schema Metadata Framework**, which records metadata about data schemas in a technology independent manner.

## 4. Key Requirements for Data Mapping

It is essential for metadata about data mappings to be clear and accessible, especially when the consumers of the data are not explicitly known. Any mapping Metadata produced, including metadata hosted in shared data catalogs, must adhere to the requirements defined in this Framework.

### 4.1 Open Standard Requirements

Any **Mapping Metadata generated must** include metadata attributes about the mapping such as identifier, creator, created and modified dates, and information about the mapping including source, target and the type of mapping.

To ensure consistency and interoperability, the Mapping Metadata **must be** documented using the Mapping Metadata format defined in this framework. This standardization facilitates consistent integration with various tools and systems, allowing consumers to seamlessly access and interpret mapping information.

The framework that was used and how it was used **must be** documented.

Each implementation must include a machine-interpretable set of documentation that follows an approved framework or be approved as an exception/extension of an approved framework.

### 4.2 Standard Access Method

Whenever a publisher makes Data mappings available, **they must** implement a mechanism that allows consumers to retrieve and/or query the metadata.

To maximize accessibility, the Mapping Metadata **must be** accessible with standard encoding, preferably UTF-8, accessible via standard web protocols, and accessible from a non-proprietary interface. This approach ensures that consumers can easily retrieve and utilize Data Mapping information, regardless of their technical environment.

### 4.3 Definition of Mapping properties

The classes and properties defined for mapping metadata specify how elements across the conceptual, logical, and physical layers correspond to one another. For example, mappings can trace how concepts in the conceptual layer correspond to their implementations, so that systems know not only what a concept means but where it lives. From a business or conceptual element, users and AI agents can traverse the graph to discover every place the concept is materialized. Also, starting from any physical attribute, they can navigate up to the conceptual layer and then back down to locate all other physical sources that represent the same concept, regardless of storage technology. This bidirectional navigation is made possible because a mapping links data elements to their semantic meaning — as defined in the conceptual layer — and to their physical location, connecting where data resides and how to access it with what it represents. Mappings link sources to targets across conceptual, logical, and physical layers, capturing combinations of attributes with filters and constraints, and enumerating physical access paths.

The mapping metadata addresses the following semantic mapping relationships:

- **Physical ⟶ Logical:** Mapping a SQL table/column or JSON object-type/property (etc.) to its logical model counterpart.
- **Logical ⟶ Conceptual:** Mapping a logical class or property to a conceptual class or property in a reference ontology or data framework.
- **Physical ⟶ Conceptual:** Mapping a physical table/class or column/property to a conceptual class/property in a reference ontology or data framework.
- **Physical ⟶ Physical:** Mapping data between physical models.
- **Logical ⟶ Logical:** Tracking derivation chains across logical models.
- **Classification Mapping:** Associating a model element with a taxonomy/glossary term for the purpose of classification and/or categorization. Allows a model and its components to be classified/categorized externally without any changes to the model itself. Not specifically tied to terms from business glossaries.

The semantic mapping relationships flow from the more concrete layers to more abstract layers. However, these links can equally be traversed in reverse, navigating from abstract concepts down to their concrete implementations. This ensures a continuous, navigable path between the conceptual layer and the physical layer in either direction.

In all cases the Mapping Metadata must specify, unless otherwise indicated:

```
A) For each Mapping Set (jpmv:MappingSet):
     a. A JPMC identifier for the mapping set (See the JPMC Identifiers Specification). (dcterms:identifier)
     b. Title or brief summary statement about the Mapping Set. (dcterms:title) (optional)
     c. Description with sufficient detail for the consumer to unambiguously understand the mapping set. (dcterms:description) (optional)
     d. A field identifying the creator (person, software, or AI agent) responsible for producing the Mapping Set. (dcterms:creator) (optional)
     e. Last modification date of the Mapping Set. (dcterms:modified) (optional)
     f. The actor (person, software, or AI Agent) that modified the Mapping Set. (jpmv:modifiedBy) (optional)
     g. The type of mapping (e.g., physical-to-logical, logical-to-conceptual, physical-to-physical, classification). (jpmv:mappingType)
     h. The version of the Mapping Set. (dcterms:hasVersion) (optional)
     i. The lifecycle status of the mapping set (optional). (adms:status)
     j. The source model for the Mapping Set. (dcterms:source)
     k. The target model (or concept scheme) for the Mapping Set. (dcterms:target)

B) For each individual mapping (element-to-element relationship within a mapping set) (jpmv:Mapping):
     a. The source element of the mapping (a model element). (jpmv:sourceElement)
     b. The target element of the mapping (a model element, or for classification mappings, a taxonomy concept). (jpmv:targetElement)
     c. A reference to the parent Mapping Set. (dcterms:isPartOf)
     d. A confidence value on the accuracy of the mapping (optional). (jpmv:mappingConfidence)
     e. Description with sufficient detail for the consumer to unambiguously understand the mapping (optional). (dcterms:description)

C) For each model element (source and target of the mapping) (jpmv:ModelElement):
     a. A reference to a schema metadata instance. (jpmv:schemaMetadata)
     b. A reference to the specific term in the schema metadata vocabulary that defines the mapping element. (jpmv:vocabularyRef)
     c. A path expression locating the specific attribute within the model element. (jpmv:path) (optional)
```

## 5. Classes and Associated Properties for Data Mapping

The class and property definitions for defining data mapping are described below. There are two parts defined: a) mapping metadata — covering mapping set properties (identifiers, creators, dates, types), individual mapping properties (source, target, parent set), and model element properties; and b) semantic mapping relationships that define how model elements relate to other elements or taxonomy concepts across model layers. This structure enables AI agents to traverse the resulting contextual graph to discover, reason about, and document data mappings.

### 5.1 Namespace Declarations

The following namespace prefixes are used throughout this document.

| Prefix | Namespace IRI |
|---|---|
| jpmv: | https://vocabulary.jpmorgan/DataPublishing/ |
| rdf: | http://www.w3.org/1999/02/22-rdf-syntax-ns# |
| rdfs: | http://www.w3.org/2000/01/rdf-schema# |
| owl: | http://www.w3.org/2002/07/owl# |
| xsd: | http://www.w3.org/2001/XMLSchema# |
| dcterms: | http://purl.org/dc/terms/ |
| skos: | http://www.w3.org/2004/02/skos/core# |
| prov: | http://www.w3.org/ns/prov# |
| adms: | http://www.w3.org/ns/adms# |
| dcat: | http://www.w3.org/ns/dcat/ |
| ex: | http://example.com/ns# |
| schema: | http://schema.org/ |

### 5.2 Classes and Associated Properties for Data Mappings

The following defines a standards-based ontology for recording the "who, what, and where" context of data mappings, using and extending RDFS classes and widely adopted vocabularies (Dublin Core, SKOS, PROV) to ensure interoperability and tool-agnostic consumption. Collectively, these classes and properties standardize how mappings are identified, governed, and discovered across model layers. A mapping set groups related element-to-element mappings that together describe the correspondence between two models; individual mappings capture specific attribute-level relationships and link back to their parent mapping set via `dcterms:isPartOf`. This structure enables AI agents to navigate mappings at the appropriate level of granularity.

#### 5.2.1 Mapping Set Class Definition

The Mapping Set class contains information about the Mapping set. It is an instance of `rdfs:Class`.

**jpmv:MappingSet**

| Field | Value |
|---|---|
| Requirement section | A) |
| Definition | A named collection of related `jpmv:Mapping` instances that together describe the correspondence between two models. Carries shared metadata (title, creator, dates, type). Individual mappings link back to the set via `dcterms:isPartOf`. |
| Subclass of | prov:Activity |
| Usage Note | Use a MappingSet to group the individual attribute-level mappings between a pair of models (e.g., all column-to-attribute mappings between a physical table and its logical counterpart). AI agents can use the mapping set as a high-level entry point, then drill into individual member mappings for attribute-level detail. |

#### 5.2.2. Mapping Set Property Definitions

The properties below attach to instances of `jpmv:MappingSet`. Standard Dublin Core, SKOS, and PROV properties are reused where possible; only properties absent from those vocabularies are defined under the jpmv prefix.

**dcterms:identifier**

| Field | Value |
|---|---|
| Requirement section | A) a. |
| Definition | A unique identifier for the Mapping Set. The identifier should be compliant with **Identifiers Specification**. |
| Domain | jpmv:MappingSet |
| Range | xsd:anyURI or IRI |
| Usage note | Values must be compatible with the Identifiers Specification. |

**dcterms:title**

| Field | Value |
|---|---|
| Requirement section | A) b. |
| Definition | A free-text name identifying the Mapping Set. |
| Domain | jpmv:MappingSet |
| Range | rdfs:Literal |

**dcterms:description**

| Field | Value |
|---|---|
| Requirement section | A) c. |
| Definition | A free-text definition of the Mapping Set. |
| Domain | jpmv:MappingSet |
| Range | xsd:string |

**dcterms:creator**

| Field | Value |
|---|---|
| Requirement section | A) d. |
| Definition | The agent (person or system) responsible for producing the Mapping Set. |
| Domain | jpmv:MappingSet |
| Range | foaf:Agent |
| Usage note | When specifying a JPMC SID or FID, create an instance of `foaf:Agent` and use either `jpmv:sid` `jpmv:fid` to specify the id. |

**dcterms:modified**

| Field | Value |
|---|---|
| Requirement section | A) e. |
| Definition | Most recent date on which the Mapping Set was changed, updated or modified. |
| Domain | jpmv:MappingSet |
| Range | rdfs:Literal (recommend xsd:date or xsd:dateTime) in ISO 8601 Date and Time compliant string per **JPMC Datetime Standard** |

**jpmv:modifiedBy**

| Field | Value |
|---|---|
| Requirement section | A) f. |
| Definition | The actor (person, software, or AI Agent) that modified the Mapping Set. |
| Domain | jpmv:MappingSet |
| Range | foaf:Agent |

**jpmv:mappingType**

| Field | Value |
|---|---|
| Requirement section | A) g. |
| Definition | Categorizes the nature of the mappings in the set (e.g., physical-to-logical, logical-to-conceptual, physical-to-physical). |
| Domain | jpmv:MappingSet |
| Range | skos:Concept |
| Usage notes | Values should be drawn from `jpmv:MappingTypeScheme`. See Appendix A (Section 9) for the concept list |

**dcterms:hasVersion**

| Field | Value |
|---|---|
| Requirement section | A) h. |
| Definition | The version of the Mapping Set. |
| Domain | jpmv:MappingSet |
| Range | xsd:string |

**adms:status**

| Field | Value |
|---|---|
| Requirement section | A) i. |
| Definition | The lifecycle status of the mapping set (optional). |
| Domain | jpmv:MappingSet |
| Range | skos:Concept |
| Usage note | The values for `adms:status` are `jpmv:Proposed`, `jpmv:Rejected`, `jpmv:Approved`, `jpmv:Deprecated`, and `jpmv:Retired`. |

**dcterms:source**

| Field | Value |
|---|---|
| Requirement section | A) j. |
| Definition | The source model for the Mapping Set. |
| Domain | jpmv:MappingSet |
| Range | xsd:anyURI or IRI |

**dcterms:target**

| Field | Value |
|---|---|
| Requirement section | A) k. |
| Definition | The target model or concept scheme for the Mapping Set. |
| Domain | jpmv:MappingSet |
| Range | xsd:anyURI or IRI or skos:ConceptScheme |

#### 5.2.3 Mapping Class Definitions

The mapping class contains information about an individual mapping between model elements. It is an instance of `rdfs:Class`.

**jpmv:Mapping**

| Field | Value |
|---|---|
| Requirement section | B) |
| Definition | An individual element-to-element mapping that captures how a specific source model element relates to a target model element (or, for classification mappings, to a taxonomy concept). Links back to its parent mapping set via `dcterms:isPartOf`. |
| Subclass of | prov:Activity |
| Usage Note | Instances of `jpmv:Mapping` capture a single element-to-element relationship and are members of a `jpmv:MappingSet`. An individual mapping references its parent mapping set via `dcterms:isPartOf` and typically requires only its source, target, and semantic relationship (realizes/represents). |

#### 5.2.4 Mapping Property Definitions

The properties below attach to instances of `jpmv:Mapping`. Each mapping captures an individual element-to-element relationship and links back to its parent mapping set.

**jpmv:sourceElement**

| Field | Value |
|---|---|
| Requirement section | B) a. |
| Definition | The model element serving as the source (origin) of a mapping. |
| Domain | jpmv:Mapping |
| Range | jpmv:ModelElement |

**jpmv:targetElement**

| Field | Value |
|---|---|
| Requirement section | B) b. |
| Definition | The model element serving as the target (destination) of a mapping. For conceptual models, the URI of the class or property can be used. For classification mappings, the target is a `skos:Concept` from a taxonomy rather than a model element. |
| Domain | jpmv:Mapping |
| Range | jpmv:ModelElement or rdfs:Resource or skos:Concept |
| Usage note | When no mapping was found to exist, that fact should be documented using `jpmv:NoMapping`, a `skos:Concept`, as the value to the target element. |

**dcterms:isPartOf**

| Field | Value |
|---|---|
| Requirement section | B) c. |
| Definition | Links an individual `jpmv:Mapping` back to the `jpmv:MappingSet` it belongs to. |
| Domain | jpmv:Mapping |
| Range | jpmv:MappingSet |
| Usage note | Every mapping should reference its parent mapping set. This enables agents to navigate from an individual element-to-element mapping up to the broader mapping set context, and to discover sibling mappings within the same set. |

**jpmv:mappingConfidence**

| Field | Value |
|---|---|
| Requirement section | B) d. |
| Definition | A value indicating the confidence of the Mapping, assigned by the agent (person or system) defining the Mapping. |
| Domain | jpmv:Mapping |
| Range | xsd:decimal |
| Usage notes | Value should be between 0 (no confidence) and 1.0 (high confidence). Particularly useful when mapping sets are generated by AI agents, where the confidence score reflects the agent's certainty in the alignment. |

**dcterms:description**

| Field | Value |
|---|---|
| Requirement section | B) e. |
| Definition | A free-text definition of the individual mapping (optional). |
| Domain | jpmv:Mapping |
| Range | xsd:string |

**jpmv:semanticRelationship**

| Field | Value |
|---|---|
| Requirement section | B) f. |
| Definition | A semantic mapping relationship between the source and target elements. |
| Domain | jpmv:Mapping |
| Range | jpmv:SemanticRelationshipType |
| Usage notes | The values for `jpmv:SemanticRelationshipType` are `jpmv:Realizes`, `jpmv:Represents`, and `jpmv:WasDerivedFrom`, drawn from `jpmv:SemanticRelationshipScheme`. These concepts correspond to the relationship properties defined in Section 5.3. |

#### 5.2.5 Model Element Class Definition

The Model Element class represents an identifiable schema item that participates in a mapping. It is an instance of `rdfs:Class`.

**jpmv:ModelElement**

| Field | Value |
|---|---|
| Requirement section | C) |
| Definition | An identifiable element within a physical, logical, or conceptual model that participates in a mapping. Examples: a SQL column, a JSON property, an RDF/OWL resource. |

*(remaining rows of this table — Subclass of / Usage note — fall in the gap between screenshots 6 and 7)*

#### 5.2.6. Model Element Property Definitions

The properties below attach to instances of `jpmv:ModelElement`. These properties describe the model elements that participate in mappings.

**jpmv:schemaMetadata**

| Field | Value |
|---|---|
| Requirement section | C) a. |
| Definition | Links a model element to the `jpmv:SchemaMetadata` instance that describes the schema containing this element. |
| Domain | jpmv:ModelElement |
| Range | jpmv:SchemaMetadata |
| Usage notes | References the `jpmv:SchemaMetadata` resource defined in the **Schema Metadata Framework**. The referenced instance provides links to the schema vocabulary (`jpmv:schemaMetadataVocabulary`), SHACL shapes (`jpmv:schemaMetadataSHACL`), format (`dcterms:format`), and schema source (`dcterms:source`). This property bridges the Mapping Framework and the **Schema Metadata Framework**, enabling consumers to navigate from a mapped element to the full schema definition.<br><br>In the case of a conceptual model that is defined by an ontology, this property references the ontology IRI. |

**jpmv:vocabularyRef**

| Field | Value |
|---|---|
| Requirement section | C) b. |
| Definition | References the specific term URI within the schema metadata vocabulary that defines this model element. Provides a direct, dereferenceable link from the mapping element to its formal definition in the schema vocabulary. |
| Domain | jpmv:ModelElement |
| Range | xsd:anyURI |
| Usage notes | The URI points to a term within the vocabulary referenced by the associated `jpmv:SchemaMetadata` resource's `jpmv:schemaMetadataVocabulary` or the specific term in an ontolgy. Example: `<https://data.jpmorgan/DataPublishing/CustomerDB/vocabulary#firstName>`.<br><br>For details, see the **Schema Metadata Framework** |

**jpmv:path**

| Field | Value |
|---|---|
| Requirement section | C) c. |
| Definition | A path locating the specific attribute within the model element specified in an RDF List. |
| Domain | jpmv:ModelElement |
| Range | rdf:List |
| Usage notes | The `rdf:List` representation for different kinds of paths is as follows (See Section 5.2.7 for a detailed treatment of path expressions):<br>- **path navigation:** The path `p1/p2/p3` is represented by `( ex:p1 ex:p2 ex:p3 )`<br>- **filtering:** The path `p1[p2=V]/p3` is represented by `( ex:p1 [ a jpmv:Filter ; jpmv:filterPath ( ex:p2 ) ; rdf:value V ] ex:p3 )`<br>- **indexing:** The path `p1[1]` is represented by `( ex:p1 [ a jpmv:Index ; jpmv:index 1 ] )`<br>- **casting:** The path `p1[ . instance of element(C)]` is represented by `( ex:p1 [ a jpmv:Cast ; jpmv:class ex:C ] )` |

#### 5.2.7 Specifying Path Expressions

The `jpmv:path` property introduced in Section 5.2.6 carries a path expression that pinpoints the exact attribute a `jpmv:ModelElement` refers to within its schema. Whereas `jpmv:schemaMetadata` and `jpmv:vocabularyRef` identify *which* schema and *which* vocabulary term is in scope, the path expression resolves *where* inside a potentially nested or repeating structure the mapped attribute actually resides. This matters because model elements are frequently not flat: a JSON document, an Avro record, or a UML aggregation may nest structures several levels deep, repeat elements in arrays, or hold polymorphic values whose concrete type must be narrowed before an attribute is reachable. A simple vocabulary reference cannot express these traversal semantics on its own.

To keep path expressions portable and machine-traversable, they are encoded as an `rdf:List` of vocabulary terms rather than as an opaque string. This preserves the ordered, technology-neutral navigation steps in RDF itself, so that AI agents and governance tooling can walk the path programmatically — following each term through the associated schema vocabulary — without parsing a proprietary path grammar. Each step in the list is either a plain navigation term or a blank node that qualifies the step with additional selection logic.

The framework defines four kinds of path steps, each with a corresponding RDF representation, defined in the sections below.

##### 5.2.7.1 Path Navigation

Path navigation specifies an ordered sequence of vocabulary terms that walks from a root type down through its nested properties to the target attribute.

**XPath Example path:** `TradeMessage/tradeHeader/parties/name`

**RDF Representation of Example path:** `( message:TradeMessage message:tradeHeader message:parties message:name )`

##### 5.2.7.2 Path Filtering

Path filtering narrows a repeating or collection-valued step to the element(s) whose sub-attribute matches a given value.

**XPath Example path:** `TradeMessage/tradeHeader/parties[partyRole="Trader"]/name`

**RDF Representation of Example path:** `( message:TradeMessage message:tradeHeader message:parties [ a jpmv:Filter ; jpmv:filterPath ( message:partyRole ) ; rdf:value "TRADER" ] message:name )`

Again the `message:` prefix denotes the namespace of the schema vocabulary that defines the path terms. Ordering is retaind by using `rdf:List` to define the path. A blank node is defined that contains an object of type `jpmv:Filter`, a filter path denoted by `jpmv:filterPath` and the value of the match ispecified with the `rdf:value` property. The classes properties used here are defined below.

**jpmv:Filter**

| Field | Value |
|---|---|
| type | rdfs:Class |
| Definition | Defines filter in a path expression. It is used to identify that the object defined is used to filter the path given some value. |
| Subclass of | jpmv:PathQualifier |

**jpmv:filterPath**

| Field | Value |
|---|---|
| type | owl:ObjectProperty |
| Definition | Defines a filter in a path expression. |
| Domain | jpmv:Filter |
| Range | rdf:List |

**rdf:value**

| Field | Value |
|---|---|
| type | rdf:Property |
| Definition | Idiomatic property used for structured values. (From RDF 1.1) |
| Domain | jpmv:Filter (undefined in RDF 1.1) |
| Range | xsd:string (undefined in RDF 1.1) |

##### 5.2.7.3 Path Indexing

Path indexing selects a specific element from an ordered, collection-valued step by its numeric position rather than by a matching value. This is useful when the target attribute resides at a known offset within a repeating structure, such as the second cashflow in a list.

**XPath Example path:** `TradeMessage/cashflows[2]/amount`

**RDF Representation of Example path:** `( message:TradeMessage message:cashflows [ a jpmv:Index ; jpmv:index 2 ] message:amount )`

Casting is really filter based on type, so it may be equivently be expressed as a filter expression: `( message:TradeMessage message:product [ a map:Filter ; map:filterPath ( rdf:type ) ; message:EquityProduct ] message:equityValue )`

Again the `message:` prefix denotes the namespace of the schema vocabulary that defines the path terms. In the first indexing representation `jpmv:Index` and `jpmv:index` are defined below.

**jpmv:Index**

| Field | Value |
|---|---|
| type | rdfs:Class |
| Definition | Defines the index type. It is used to identify that the object defined in the expression is an indexed value. |
| Subclass of | jpmv:PathQualifier |

**jpmv:index**

| Field | Value |
|---|---|
| type | owl:DatatypeProperty |
| Definition | Defines the value of the indexed attribute in a path expression. |
| Domain | jpmv:Index |
| Range | xsd:integer |

##### 5.2.7.4 Path Casting

Path casting narrows a polymorphic step to a specific subtype so that traversal can continue into properties defined only on that subtype. In the example below, `product` is a polymorphic element that must first be cast to `EquityProduct` before the `equityValue` attribute — which exists only on that subtype — becomes reachable.

**XPath Example path:** `TradeMessage/product[ . instance of EquityProduct]/equityValue`

**RDF Representation of Example path:** `( message:TradeMessage message:product [ a jpmv:Cast ; jpmv:class message:EquityProduct ] message:equityValue )`

Casting can be seen as a filter based on type, so it may be equivently be expressed as a filter expression: `( message:TradeMessage message:product [ a map:Filter ; map:filterPath ( rdf:type ) ; message:EquityProduct ] message:equityValue )`

Again the `message:` prefix denotes the namespace of the schema vocabulary that defines the path terms. In the first casting representation `jpmv:Class` and `jpmv:class` are defined below. For the second representation, see the previous section on **Path Filtering**.

**jpmv:Cast**

| Field | Value |
|---|---|
| type | rdfs:Class |
| Definition | Defines the casting type. It is used to identify that the object defined in the expression narrows a step to a specific subtype. |
| Subclass of | jpmv:PathQualifier |

**jpmv:class**

| Field | Value |
|---|---|
| type | owl:ObjectProperty |
| Definition | Defines the value of the subtype in a casting expression. |
| Domain | jpmv:Cast |
| Range | rdfs:Resource |

### 5.3 Properties for Semantic Mapping Relationships

The following diagram illustrates how these semantic relationship properties work together to enable end-to-end traceability for a single business concept. Using "first name" as a running example, the diagram shows a staging column (`staging.Customer.CUST_FIRST_NM`) that realizes its logical counterpart (`customer:Customer.firstName`), which in turn realizes the conceptual ontology term (`jpmv:givenName`). Within the physical layer, a warehouse column (`dw.Customer.CUST_FIRST_NM`) is linked back to the staging column via `jpmv:WasDerivedFrom`, capturing data pipeline lineage. In practice, each of these individual attribute mappings would be a member of a mapping set that groups all attribute correspondences between the two models. Together, these relationships create a contextual graph that AI agents can traverse to discover the full chain of meaning and provenance — starting from any point in the graph, an agent can navigate vertically across abstraction layers and horizontally within a layer to find all related elements.

The links in the diagram represent the value of the `jpmv:semanticRelationship` property. Although the directed links defined below (`jpmv:semanticRelationship` with the values `jpmv:Realizes`, `jpmv:Represents`, `jpmv:WasDerivedFrom`) point from the more concrete layer toward the more abstract one, the graph is inherently bi-directional. By traversing the inverse of these directed relationships, a consumer can navigate from a conceptual term down through its logical representations and onward to every physical column that implements it.

```
                    ┌──────────────────────────────────────────┐
                    │  Conceptual Model – Firmwide Ontology     │
                    │   ┌────────────────────────────────────┐  │
                    │   │ Ontology Concept (e.g.             │  │
                    │   │ jpmv:givenName)                    │  │
  Conceptual Layer  │   └────────────────────────────────────┘  │
- - - - - - - - - - └───────▲──────────────────▲────────────────┘ - - - - -
                    jpmv:Realizes        jpmv:Realizes
          ┌──────────────────────┐        ┌──────────────────────┐
          │ Logical Model–C360_001│        │ Logical Model–CCB_012│
          │  ┌──────────────────┐ │        │  ┌────────────────┐  │
          │  │ Logical Attribute│ │        │  │Logical Attribute│ │
          │  │ (e.g. Customer.  │ │        │  │(e.g. Client.    │ │
          │  │ firstName)       │ │        │  │ firstName)      │ │
  Logical │  └──────────────────┘ │        │  └────────────────┘  │
   Layer  └──────▲────────────────┘        └──▲──────────▲────────┘
- - - - - - - -  │  jpmv:Realizes    jpmv:Realizes   jpmv:Realizes
   ┌─────────────────────────┐ ┌──────────────────────┐ ┌───────────────────────────────┐
   │ Physical Model–C360Portal│ │Physical Model-RetailCRM│ │Physical Model–RetailCRM Warehouse│
   │  ┌────────────────────┐  │ │ ┌──────────────────┐  │ │ ┌──────────────────────────┐  │
   │  │ Portal Column (e.g.│  │ │ │ Staging Column   │  │ │ │ Warehouse Column (e.g.   │  │
   │  │ Customer.CLIENT_   │  │ │ │ (e.g. Client.    │  │ │ │ dw.Client.CUST_FIRST_NM) │  │
   │  │ FST_NM)            │  │ │ │ CUST_FIRST_NM)   │◄─┼─┼─┤                          │  │
   │  └────────────────────┘  │ │ └──────────────────┘  │ │ └──────────────────────────┘  │
   └──────────────────────────┘ └───────────────────────┘ └───────────────────────────────┘
  Physical Layer                        jpmv:WasDerivedFrom
```

The semantic mapping relationships are enumerated as a SKOS concept scheme, `jpmv:SemanticRelationshipScheme`, with one `skos:Concept` defined for each relationship type. These concepts are the permitted values of the `jpmv:semanticRelationship` property on a `jpmv:Mapping` (see Section 5.2.4), and each relationship is directional, applying from the source element to the target element.

**jpmv:Realizes**

| Field | Value |
|---|---|
| Type | skos:Concept, jpmv:SemanticRelationshipType |
| Definition | Asserts that a more concrete element realizes (implements) a more abstract one, analogous to UML realization. Example: `TABLE1.COLUMN2` realizes `LogicalModel.property4`. |
| In Scheme | jpmv:SemanticRelationshipScheme |
| Preferred Label | Realizes |
| Usage Notes | Usen when a model element from one level is the concrete implementation of a higher level. |

**jpmv:Represents**

| Field | Value |
|---|---|
| Type | skos:Concept, jpmv:SemanticRelationshipType |
| Definition | A softer semantic alignment than `jpmv:Realizes`: one element represents another in a different model layer or data framework, without implying full structural equivalence. |
| In Scheme | jpmv:SemanticRelationshipScheme |
| Preferred Label | Represents |
| Usage Notes | Example: `ex:Address-firstLine jpmv:represents jpmv:addressLine`. Suitable when SKOS match-like approximate alignment is sufficient. |

**jpmv:WasDerivedFrom**

| Field | Value |
|---|---|
| Type | skos:Concept, jpmv:SemanticRelationshipType |
| Definition | Indicates that the target element is computed or derived from one or more source elements, capturing lineage or derivation provenance. |
| In Scheme | jpmv:SemanticRelationshipScheme |
| Preferred Label | Was Derived From |
| Usage Notes | Use when lineage or derivation is defined. |

## 6. Overview of Data Mapping Framework Entities and Relationships

```
prov:Activity
      ▲              ▲
      │              │
 subClassOf     subClassOf
      │              │
 MappingSet      Mapping
      │              │
      │              ├── jpmv:sourceElement ─────► ModelElement
      │              ├── jpmv:targetElement ─────► ModelElement
      │              └── dcterms:ispartOf   ─────► MappingSet
      │
      ├── jpmv:mappingType ──────────────────────► Concept
      ├── adms:status ───────────────────────────► Concept
      ├── dcterms:creator ───────────────────────► Agent
      └── jpmv:modifiedBy ───────────────────────► Agent


ModelElement
      │
      ├── jpmv:schemaMetadata ───────────────────► SchemaMetadata
      ▲ ▲ ▲                                              │
      │ │ │                              └── dcterms:conformsTo ── dcat:Dataset|Distribution
      │ │ └── PhysicalModel  — jpmv:realizes|jpmv:represents ─► LogicalModel
      │ │                    └─ jpmv:realizes|jpmv:represents ─► ConceptualModel
      │ └──── LogicalModel   — jpmv:realizes|jpmv:represents ─► ConceptualModel
      └────── ConceptualModel


jpmv:Classification (jpmv:mappingType on MappingSet)
    Mapping:  sourceElement ──► ModelElement  (physical/logical/conceptual column)
              targetElement ──► skos:Concept  (taxonomy concept)
    ↳ Unlike element-to-element mappings, classification
      mappings link a model element to a taxonomy concept
      for governance & discovery (ontological data-concept mapping)
```

## 7. Specifying Data Mappings – Representative Examples

The following Turtle snippets show how the framework captures common mapping patterns. Several examples include mapping metadata (titles, creators, dates, status) to illustrate how the two parts of the framework work together. Example 1 demonstrates how a mapping set groups multiple element-to-element mappings between two models. Examples use a variety of rule languages to demonstrate language neutrality.

### 7.1 Example 1: Semantic Alignment (realizes / represents)

This example demonstrates end-to-end lineage for a customer first-name field across the three abstraction layers using three mapping sets. The first mapping set, `ex:Mappingset-customer-phys-to-logical`, groups two attribute mappings: `ex:Mapping-006a` traces the physical SQL column `CUST_FIRST_NM` upward to the logical attribute `Customer.firstName`, and `ex:Mapping-006d` maps `CUST_LAST_NM` to `Customer.lastName`. Each source element asserts `jpmv:realizes` on its logical counterpart. The second mapping set, `ex:Mappingset-logical-to-conceptual`, contains `ex:Mapping-006b`, which traces the logical attribute `Customer.firstName` upward to the conceptual property `jpmv:givenName`; here the source element asserts the softer `jpmv:represents` alignment on the target. Together these mappings form a navigable lineage chain: physical → logical → conceptual. Note that the metadata envelope (identifier, creator, dates, type, status) is carried by each mapping set, while the individual member mappings capture the element-to-element relationships.

Additionally, a physical-to-physical mapping set, `ex:Mappingset-staging-to-dw`, demonstrates horizontal navigation within the physical layer. Its member mapping `ex:Mapping-006c` maps a staging account-id column (`ex:Elem-stgAcctId`) to its data warehouse counterpart (`ex:Elem-dwAcctId`), using `prov:wasDerivedFrom` to capture derivation provenance between the two systems.

*Diagram: `ex:mappingset-customer-phys-to-logical` (Mapping Set, yellow) ← `dcterms:isPartOf` ← `ex:mapping-006a` and `ex:mapping-006d` (Mappings, green); mappings point via `jpmv:targetElement` / `jpmv:sourceElement` to Model Elements (purple) in the Logical Layer (`ex:elem-customerFirstName`, `ex:elem-customerLastName`) and Physical Layer (`ex:elem-custFirstNm`, `ex:elem-custLastNm`), linked by `jpmv:realizes`. Legend: yellow = Mapping Set, green = Mapping, purple = Model Element.*

```turtle
# — Mapping Set: groups all attribute mappings between Customer physical table and logical model —
ex:Mappingset-customer-phys-to-logical a jpmv:MappingSet ;
    dcterms:identifier   <https://data.jpmorgan/mappings/mappingset-customer-phys-to-logical> ;
    dcterms:title        "Customer Physical-to-Logical Mapping Set" ;
    dcterms:creator      jpmc:Emp_O123456 ;
    dcterms:modified     "2026-03-08"^^xsd:date ;
    jpmv:modifiedBy      jpmc:Emp_O123456 ;
    jpmv:mappingType     jpmv:PhysicalToLogical ;
    adms:status          jpmv:Approved ;
    dcterms:description  "Groups all attribute-level mappings between the Customer physical table and the customer logical model." .

# — Member mapping: physical column realizes a logical attribute —
ex:Mapping-006a a jpmv:Mapping ;
    dcterms:isPartOf     ex:Mappingset-customer-phys-to-logical ;
    jpmv:sourceElement   ex:Elem-custFirstNm ;
    jpmv:targetElement   ex:Elem-customerFirstName ;
    dcterms:description  "Physical column realizes its logical counterpart." .

ex:Elem-custFirstNm  jpmv:realizes  ex:Elem-customerFirstName .

# — Member mapping: another attribute in the same mapping set —
ex:Mapping-006d a jpmv:Mapping ;
    dcterms:isPartOf     ex:Mappingset-customer-phys-to-logical ;
    jpmv:sourceElement   ex:Elem-custLastNm ;
    jpmv:targetElement   ex:Elem-customerLastName ;
    dcterms:description  "Maps the physical column to its logical counterpart; the source element defines the semantic mapping relationship." .

ex:Elem-custLastNm  jpmv:realizes  ex:Elem-customerLastName .
```

*Diagram: `ex:mappingset-logical-to-conceptual` ← `dcterms:isPartOf` ← `ex:mapping-006b`; `jpmv:targetElement` → Conceptual Layer `jpmv:givenName`, `jpmv:sourceElement` → Logical Layer `ex:elem-customerFirstName`, joined by `jpmv:realizes`.*

```turtle
# — Mapping Set for Logical-to-Conceptual mappings —

ex:Mappingset-logical-to-conceptual a jpmv:MappingSet ;
    dcterms:identifier   <https://data.jpmorgan/mappings/mappingset-logical-to-conceptual> ;
    dcterms:title        "Customer Logical-to-Conceptual Mapping Set" ;
    dcterms:creator      jpmc:Emp_V123456 ;
    dcterms:modified     "2026-03-08"^^xsd:date ;
    jpmv:modifiedBy      jpmc:Emp_O123456 ;
    jpmv:mappingType     jpmv:LogicalToConceptual ;
    adms:status          jpmv:Approved ;
    dcterms:description  "Maps logical customer model attributes to conceptual ontology concepts." .

# — Representation: logical attribute represents a reference ontology concept —
ex:Mapping-006b a jpmv:Mapping ;
    dcterms:isPartOf     ex:Mappingset-logical-to-conceptual ;
    jpmv:sourceElement   ex:Elem-customerFirstName ;
    jpmv:targetElement   jpmv:givenName ;
    dcterms:description  "Maps the logical attribute to its conceptual layer counterpart; the source element asserts jpmv:represents on the target." .

ex:Elem-customerFirstName  jpmv:represents  jpmv:givenName .
```

*Diagram: `ex:mappingset-staging-to-dw` ← `dcterms:isPartOf` ← `ex:mapping-006c`; `jpmv:targetElement` → `ex:elem-stgAcctId`, `jpmv:sourceElement` → `ex:elem-dwAcctId`, both in the Physical Layer, joined by `jpmv:realizes`.*

```turtle
# — Mapping Set for Staging-to-Warehouse derivation —
ex:Mappingset-staging-to-dw a jpmv:MappingSet ;
    dcterms:identifier   <https://data.jpmorgan/mappings/mappingset-staging-to-dw> ;
    dcterms:title        "Staging to Data Warehouse Mapping Set" ;
    dcterms:creator      jpmc:Emp_E345678 ;
    dcterms:modified     "2026-03-10"^^xsd:date ;
    jpmv:modifiedBy      jpmc:Emp_O123456 ;
    jpmv:mappingType     jpmv:PhysicalToPhysical ;
    adms:status          jpmv:Approved ;
    dcterms:description  "Maps staging table attributes to data warehouse counterparts." .

# — Derivation provenance —
ex:Mapping-006c a jpmv:Mapping ;
    dcterms:isPartOf     ex:Mappingset-staging-to-dw ;
    jpmv:sourceElement   ex:Elem-stgAcctId ;
    jpmv:targetElement   ex:Elem-dwAcctId ;
    dcterms:description  "Data warehouse column derived from staging source." .

ex:Elem-dwAcctId  prov:wasDerivedFrom  ex:Elem-stgAcctId .

# — Model Elements —
ex:Elem-custFirstNm a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/CustomerDB> ;
    jpmv:vocabularyRef   <https://data.jpmorgan/DataPublishing/CustomerDB/vocabulary#CUST_FIRST_NM> .
<https://data.jpmorgan/SchemaMetadata/CustomerDB> a jpmv:SchemaMetadata .

ex:Elem-customerFirstName a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/CustomerLogical> ;
    jpmv:vocabularyRef      <https://data.jpmorgan/DataPublishing/CustomerLogical/vocabulary#firstName> .
<https://data.jpmorgan/SchemaMetadata/CustomerLogical> a jpmv:SchemaMetadata .

ex:Elem-custLastNm a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/CustomerDB> ;
    jpmv:vocabularyRef   <https://data.jpmorgan/DataPublishing/CustomerDB/vocabulary#CUST_LAST_NM> .
<https://data.jpmorgan/SchemaMetadata/CustomerDB> a jpmv:SchemaMetadata .

ex:Elem-customerLastName a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/CustomerLogical> ;
    jpmv:vocabularyRef   <https://data.jpmorgan/DataPublishing/CustomerLogical/vocabulary#lastName> .
<https://data.jpmorgan/SchemaMetadata/CustomerLogical> a jpmv:SchemaMetadata .

ex:Elem-address a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/CustomerLogical>;
    jpmv:vocabularyRef   <https://data.jpmorgan/DataPublishing/CustomerLogical/vocabulary#address> .
<https://data.jpmorgan/SchemaMetadata/CustomerLogical> a jpmv:SchemaMetadata .

ex:Elem-stgAcctId a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/StagingDB> ;
    jpmv:vocabularyRef   <https://data.jpmorgan/DataPublishing/StagingDB/vocabulary#ACCT_ID> .
<https://data.jpmorgan/SchemaMetadata/StagingDB> a jpmv:SchemaMetadata .

ex:Elem-dwAcctId a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/WarehouseAnalytics> ;
    jpmv:vocabularyRef   <https://data.jpmorgan/DataPublishing/WarehouseAnalytics/vocabulary#ACCOUNT_ID> .
<https://data.jpmorgan/SchemaMetadata/WarehouseAnalytics> a jpmv:SchemaMetadata .

jpmv:givenName a owl:DatatypeProperty .

jpmv:LogicalToConceptual a skos:Concept .
jpmv:PhysicalToPhysical a skos:Concept .
jpmv:PhysicalToLogical a skos:Concept .

jpmv:Approved a skos:Concept .

# — Schema metadata definitions —

ex:Customer_dataset a jpmv:SchemaMetadata ;
    dcterms:title "Schema metadata attributes for Customer dataset" ;
    dcterms:identifier <https://jpmchase.com/SchemaMetadata/Customer_dataset> ;
    jpmv:schemaMetadataVocabulary <https://jpmchase.com/SchemaMetadata/vocabulary/Customer_dataset-schema.ttl> ;
    jpmv:schemaMetadataSHACL <https://jpmchase.com/SchemaMetadata/shapes/Customer_dataset.ttl> ;
    dcterms:format "sql" ;
    dcterms:source "https://jpmchasecom/UML/Customer_dataset" ;
.

ex:Customer_logical_model a jpmv:SchemaMetadata ;
    dcterms:title "Schema metadata attributes for logical model of Customer dataset" ;
    dcterms:identifier <https://jpmchase.com/SchemaMetadata/Customer_logical_model> ;
    jpmv:schemaMetadataVocabulary <https://jpmchase.com/SchemaMetadata/vocabulary/Customer_logical-schema.ttl> ;
    dcterms:format "UML" ;
    dcterms:source "https://jpmchasecom/UML/Customer_dataset.xmi" ;
.

ex:Customer_logical_model a jpmv:SchemaMetadata ;
    dcterms:title "Schema metadata attributes for logical model of Customer dataset" ;
    dcterms:identifier <https://jpmchase.com/SchemaMetadata/Customer_logical_model> ;
    jpmv:schemaMetadataVocabulary <https://jpmchase.com/SchemaMetadata/vocabulary/Customer_logical-schema.ttl> ;
    dcterms:format "UML" ;
    dcterms:source "https://jpmchasecom/UML/Customer_dataset.xmi" ;
.

ex:Account_staging_dataset a jpmv:SchemaMetadata ;
    dcterms:title "Schema metadata attributes for Staging database for Accounts" ;
    dcterms:identifier <https://jpmchase.com/SchemaMetadata/Account_staging_dataset> ;
    jpmv:schemaMetadataVocabulary <https://jpmchase.com/SchemaMetadata/vocabulary/Account_staging_dataset-schema.ttl> ;
    jpmv:schemaMetadataSHACL <https://jpmchase.com/SchemaMetadata/shapes/Account_staging_dataset.ttl> ;
    dcterms:format "sql" ;
    dcterms:source "https://jpmchasecom/UML/Account_staging_dataset" ;
.

ex:Account_warehouse_dataset a jpmv:SchemaMetadata ;
    dcterms:title "Schema metadata attributes for Staging database for Accounts" ;
    dcterms:identifier <https://jpmchase.com/SchemaMetadata/Account_warehouse_dataset> ;
    jpmv:schemaMetadataVocabulary <https://jpmchase.com/SchemaMetadata/vocabulary/Account_warehouse_dataset-schema.ttl> ;
    jpmv:schemaMetadataSHACL <https://jpmchase.com/SchemaMetadata/shapes/Account_warehouse_dataset.ttl> ;
    dcterms:format "sql" ;
    dcterms:source "https://jpmchasecom/UML/Account_warehouse_dataset" ;
.

# — Other metadata —

jpmc:Emp_O123456 a foaf:Agent ;
    foaf:name "Agent 1" ;
    jpmv:sid "O123456" ;
    foaf:mbox "agent@jpmchase.com" .

jpmc:Emp_V123456 a foaf:Agent ;
    foaf:name "Agent 1" ;
    jpmv:sid "V123456" ;
    foaf:mbox "agent2@jpmchase.com" .

jpmc:Emp_E345678 a foaf:Agent ;
    foaf:name "Jane Doe" ;
    jpmv:sid "E345678" ;
    foaf:mbox "jane.doe@jpmchase.com" .
```

### 7.2 Example 2: Mapping Names

The logical attribute `fullName` maps to two physical source columns.

```turtle
ex:Elem-firstName a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmchase/SchemaMetadata/CustomerDB>  ;
    jpmv:vocabularyRef   <https://data.jpmorgan/DataPublishing/CustomerDB/vocabulary/FIRST_NAME> .

ex:Elem-lastName a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/CustomerDB>  ;
    jpmv:vocabularyRef   <https://data.jpmorgan/DataPublishing/CustomerDB/vocabulary/LAST_NAME> .

ex:Elem-fullName a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/CustomerLogical> ;
    jpmv:vocabularyRef      <https://data.jpmorgan/DataPublishing/CustomerLogical/vocabulary#fullName> .

# — Mapping Set —
ex:Mappingset-customer-name a jpmv:MappingSet ;
    dcterms:identifier      <https://data.jpmorgan/mappings/mappingset-customer-name> ;
    dcterms:title           "Customer Name Derivation Mapping Set" ;
    dcterms:creator         "SEAL:456789 AnalyticsMappingEngine" ;
    dcterms:created         "2026-02-10"^^xsd:date ;
    dcterms:modified        "2026-03-05"^^xsd:date ;
    jpmv:mappingType        jpmv:PhysicalToLogical ;
    jpmv:mappingConfidence  "0.93"^^xsd:decimal ;
    adms:status             jpmv:Approved ;
    dcterms:description     "Maps physical customer name columns to logical full name attribute." .

ex:Mapping-002 a jpmv:Mapping ;
    dcterms:isPartOf        ex:Mappingset-customer-name ;
    jpmv:sourceElement      ex:Elem-firstName, ex:Elem-lastName ;
    jpmv:targetElement      ex:Elem-fullName ;
    dcterms:description     "Combines first and last name via concatenation." .

ex:Elem-firstName  jpmv:realizes  ex:Elem-fullName .
ex:Elem-lastName   jpmv:realizes  ex:Elem-fullName .

<https://jpmchase.com/SchemaMetadata/CustomerDB>
    a jpmv:SchemaMetadata, dcterms:Standard ;
    dcterms:title "Schema metadata for Customer physical model" ;
    jpmv:schemaMetadataVocabulary <https://data.jpmorgan/SchemaMetadata/vocabulary/CustomerVocab.ttl> ;
    jpmv:schemaMetadataSHACL <https://data.jpmorgan/SchemaMetadata/shapes/CustomerShapes.ttl> .

ex:Person_dataset a jpmv:SchemaMetadata ;
    dcterms:title "Schema metadata attributes for Person dataset" ;
    dcterms:identifier <https://jpmchase.com/SchemaMetadata/Person_dataset> ;
    jpmv:schemaMetadataVocabulary <https://jpmchase.com/SchemaMetadata/vocabulary/Person_dataset-schema.ttl> ;
    jpmv:schemaMetadataSHACL <https://jpmchase.com/SchemaMetadata/shapes/Person_dataset.ttl> ;
    dcterms:format "sql" ;
    dcterms:source "https://jpmchasecom/UML/Customer_dataset" .

ex:Customer_dataset a jpmv:SchemaMetadata ;
    dcterms:title "Schema metadata attributes for Customer dataset" ;
    dcterms:identifier <https://jpmchase.com/SchemaMetadata/Customer_dataset> ;
    jpmv:schemaMetadataVocabulary <https://jpmchase.com/SchemaMetadata/vocabulary/Customer_dataset-schema.ttl> ;
    jpmv:schemaMetadataSHACL <https://jpmchase.com/SchemaMetadata/shapes/Customer_dataset.ttl> ;
    dcterms:format "sql" ;
    dcterms:source "https://jpmchasecom/UML/Customer_dataset" .

jpmc:Emp_E345678 a foaf:Agent ;
    foaf:name "Jane Doe" ;
    jpmv:sid "E345678" ;
    foaf:mbox "jane.doe@jpmchase.com" .

jpmv:PhysicalToLogical a skos:Concept .

jpmv:Approved a skos:Concept .
```

### 7.3 Example 3: Physical-to-Physical Mapping

Maps between two physical-layer tables — a staging table and a warehouse fact table.

```turtle
ex:Elem-stg-qty a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/StagingOrders>  ;
    jpmv:vocabularyRef   <https://data.jpmorgan/DataPublishing/StagingOrders/vocabulary/quantity> .

ex:Elem-stg-unit-price a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/StagingOrders>  ;
    jpmv:vocabularyRef   <https://data.jpmorgan/DataPublishing/StagingOrders/vocabulary/unit_price> .

ex:Elem-wh-total-amount a jpmv:ModelElement ;
    jpmv:schemaMetadata  <https://data.jpmorgan/SchemaMetadata/WarehouseAnalytics>  ;
    jpmv:vocabularyRef   <https://data.jpmorgan/DataPublishing/WarehouseAnalytics/vocabulary/total_amount> .

# — Mapping Set —
ex:Mappingset-order-lines a jpmv:MappingSet ;
    dcterms:identifier      <https://data.jpmorgan/mappings/mappingset-order-lines> ;
    dcterms:title           "Order Lines Staging-to-Warehouse Mapping Set" ;
    dcterms:creator         "SEAL:O12345 OrderProcessingPipeline" ;
    dcterms:created         "2026-01-20"^^xsd:date ;
    dcterms:modified        "2026-03-12"^^xsd:date ;
    jpmv:mappingType        jpmv:PhysicalToPhysical ;
    jpmv:mappingConfidence  "1.0"^^xsd:decimal ;
    adms:status             jpmv:Approved ;
    dcterms:description     "Maps staging order line attributes to warehouse fact table." .

ex:Mapping-009 a jpmv:Mapping ;
    dcterms:isPartOf        ex:Mappingset-order-lines ;
    jpmv:sourceElement      ex:Elem-stg-qty, ex:Elem-stg-unit-price ;
    jpmv:targetElement      ex:Elem-wh-total-amount ;
    dcterms:description     "Maps total_amount as quantity times unit_price." .

ex:Elem-wh-total-amount   prov:wasDerivedFrom   ex:Elem-stg-qty, ex:Elem-stg-unit-price .

ex:Orders_staging_model a jpmv:SchemaMetadata ;
    dcterms:title "Schema metadata attributes for physical model of orders Staging dataset" ;
    dcterms:identifier <https://jpmchase.com/SchemaMetadata/Orders_staging-schema_model> ;
    jpmv:schemaMetadataVocabulary <https://jpmchase.com/SchemaMetadata/vocabulary/Orders_staging-schema_model.ttl> ;
    dcterms:format "UML" ;
    dcterms:source "https://jpmchasecom/UML/COrders_staging.xmi" .

ex:Order_warehouse_dataset a jpmv:SchemaMetadata ;
    dcterms:title "Schema metadata attributes for Wharehouse model of orders" ;
    dcterms:identifier <https://jpmchase.com/SchemaMetadata/Order_warehouse_dataset> ;
    jpmv:schemaMetadataVocabulary <https://jpmchase.com/SchemaMetadata/vocabulary/Order_warehouse_dataset-schema.ttl> ;
    jpmv:schemaMetadataSHACL <https://jpmchase.com/SchemaMetadata/shapes/Order_warehouse_dataset.ttl> ;
    dcterms:format "sql" ;
    dcterms:source "https://jpmchasecom/UML/Order_warehouse_dataset" .

jpmc:Emp_V123456 a foaf:Agent ;
    foaf:name "Agent 1" ;
    jpmv:sid "V123456" ;
    foaf:mbox "agent1@jpmchase.com" .

jpmv:PhysicalToPhysical a skos:Concept .

jpmv:Approved a skos:Concept .
```

*(capture ends here — §7.4 onward not screenshotted)*

---

# D. Provenance Framework

> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/pages/viewpage.action?pageId=5567744239&spaceKey=DATAPUBSTRATEGY&title=Provenance%2BFramework
> **Breadcrumb:** Pages / DATAPUBSTRATEGY Home / Firmwide Data Publishing Frameworks · 182 views
> **Created by:** Marin, James · **Last updated by:** Tong, Jian on May 27, 2026 · 14 minute read
> **Screenshots:** `Screenshot 2026-07-30 175205.png` … `175732.png` (13 shots — page captured end to end)

## Provenance Metadata Production and Use

**Data Publishing Council Approval Date:** Feb 2025

## 1. Summary

Provenance metadata is an important data related component that is shared across the entire firm, encompassing all Lines of Business (LOBs) and Corporate Functions (CFs). The purpose of this document is to establish a consistent framework to be used when documenting the flow of data sources, ensuring that all provenance metadata is available in a machine-readable document that specifies their origins or the flow from source to destination. This is achieved by adhering to recognized, industry standardized approaches such as PROV-O, PROV-DM, and OpenLineage, which provide structured, open methodologies for capturing and representing data lineage information. These industry standardized approaches are vendor- and tool-agnostic, allowing for extensions to meet the unique requirements of the Firm.

## 2. Changes from Previous Version

This is the first version of this Framework.

## 3. Data Provenance

This Framework is designed to cover Data Provenance ontology and vocabulary at the Firm and supports the requirements of the (Top Level Policy).

### 3.1 Data Provenance Definition

Data Provenance is the documentation of the origins, history, and transformations of data as it moves through organization's systems and processes.

### 3.2 Data Provenance Tooling

This JPMC Framework is not intentioned to specify tooling for use in implementing Data Provenance, but seeks to offer an extended format of current industry adopted vocabularies and approaches. Any tooling identified for use by the Firm must adhere to the ontology and vocabulary requirements of this Framework.

## 4. Key Requirements of Data Provenance

It is essential for data provenance metadata to be clear and accessible, especially when the consumers of the data are not explicitly known.

### 4.1 Open Framework Requirements

Any **provenance metadata generated must** include detailed information about the entity, the actions and transformations that were applied to generate the entity, and the actors involved in these processes, such as data engineers or automated systems.

To ensure consistency and interoperability, the data provenance **must be** documented using a standard provenance format specification as specified in this framework. This standardization facilitates easier integration with various tools and systems, allowing consumers to seamlessly access and interpret the lineage information.

Provenance metadata **must provide** Data provenance mapped from use back to source (i.e. data capture).

Each implementation **does not require** a manually documented diagram, but must include a machine readable set of documentation that follows an approved framework or be approved as an exception/extension of an approved framework.

### 4.2 Framework Access Method

If a publisher makes provenance metadata available, they must implement a mechanism that allows consumers to access, query, or determine the provenance of the data.

### 4.3 Information to be Included in Provenance Metadata

If provenance metadata is made available, it must specify the following classes and properties. Each class is identified with supporting properties. In addition to the outlined classes and properties, each class requires additional properties of "Identifier", "Title", and "Description" which are defined in the Descriptive Metadata Framework.

The Provenance metadata described below follows the terminology used in the PROV-O standard, which focuses on activities, actors and entities. Activities are anything that occurs over time and acts upon or with entities. Activities include consuming, processing, transforming, modifying, relocating, using, or generating entities. Actors are anything that has some responsibility for an activity taking place. Actors include people, applications, and other software processes. Entities are physical, digital, conceptual, or other kinds of things. Entities include datasets, data elements, files, and other digital assets.

In all cases the data provenance must specify:

```
A) For each entity, the following attributes are required:
     a. A unique identifier that identifies the dataset. (See JPMC Identifiers Specification).
     b. Title or brief summary statement about the data.
     c. Description with sufficient detail for the consumer to unambiguously understand the entity.
     d. At least one of the following are required:
          i.  The activity that generates this entity.
          ii. The dataset(s) that were used to derive this entity.
     e. The actor(s) hosting or otherwise attributed to the entity (optional for external source of data).
B) For each activity, the following attributes are required unless otherwise indicated:
     a. An identifier that uniquely identifies the activity. (See JPMC Identifiers Specification).
     b. Title or brief summary statement about the activity.
     c. Description with sufficient detail for the consumer to unambiguously understand the activity.
     d. The input entity/entities the activity used to generate the oputput entity (optional).
     e. The actor(s) associated with performing the activity.
     f. The start time of the activity (optional).
     g. The end time of the activity (optional).
C) For each actor, the following attributes are required:
     a. An identifier that uniquely identifies the actors. (See JPMC Identifiers Specification).
```

Any implementation of Data Provenance within the firm must follow the standardized format with extensions created to meet the firm's needs. These extensions may include OpenLineage to accommodate ETL (Extract Transform Load) pipelines.

## 5. Data Provenance Minimum Specification Definitions

Data Provenance, is defined by instantiating standard classes and associated properties. The definitions closely follow the PROV Standard Framework, with some extensions where required. The required and optional classes are described in the following section.

### 5.1. Class: Entities

Entities are physical, digital, conceptual, or other kinds of things with some fixed aspects. Entities are the objects whose provenance is being described. For example, a document, an image, a dataset, or data elements can be considered an entity.

**prov:Entity**

| Class | Description |
|---|---|
| Definition | Target data asset, which may be physical, digital, conceptual, or other kind of thing with some fixed aspects, entities may be physical or virtual. |
| Usage Note | Always required when defining provenance for datasets. |
| Properties | dcterms:identifier · dcterms:title · dcterms:description · prov:wasGeneratedBy · prov:wasDerivedFrom |
| Example | `:eodTradeDataset a prov:Entity .` |

#### 5.1.1. Property: Generation

**prov:wasGeneratedBy**

| Property | Description |
|---|---|
| Requirement Section | A) d.i. |
| Definition | The activity that generates this entity. |
| Domain | prov:Entity |
| Range | prov:Activity |
| Optionality | Required |
| Example | `:eodTradeDataset prov:wasGeneratedBy :eodTradeAggregationActivity .` |

#### 5.1.2. Property: Derivations

**prov:wasDerivedFrom**

| Property | Description |
|---|---|
| Requirement Section | A) d.ii. |
| Definition | The dataset(s) that were used to derive this entity. A transformation of an entity into another, an update of an entity resulting in a new one, or the construction of a new entity based on a pre-existing entity. May include revisions where the resulting entity is a revised version of some original. |
| Domain | prov:Entity |
| Range | prov:Entity |
| Optionality | Required |
| Example | `:eodJapanTradeDataset prov:wasDerivedFrom :eodTradeDataset .` |

*(the middle rows of this table fall in the seam between screenshots `175312` and `175332`; they are recovered from the identical table on the [WIP] Provenance CDAO Framework page — section E below)*

#### 5.1.3. Property: Attribution

**prov:wasAttributedTo**

| Property | Description |
|---|---|
| Requirement Section | A) e. |
| Definition | The actor(s) hosting or otherwise attributed to the entity. |
| Domain | prov:Entity |
| Range | prov:Agent |
| Optionality | Optional for original source of data |
| Example | `:eodTradeDataset prov:wasAttributedTo :athenaRates .` |

### 5.2. Class: Activities

An activity is something that occurs over a period of time and acts upon or with entities. It may include consuming, processing, transforming, modifying, relocating, using, or generating entities. Just as entities cover a broad range of notions, activities can cover a broad range of notions: information processing activities may for example move, copy, or duplicate digital entities; physical activities can include driving a car between two locations or printing a book.

Activities generate new entities. For example, creating a dataset brings the dataset into existence, while revising the dataset brings a new version into existence. Activities also make use of entities. For example, revising a dataset to fix mistakes uses the original version of the dataset as well as a list of corrections. Generation does not always occur at the end of an activity, and an activity may generate entities part-way through. Likewise, usage does not always occur at the beginning of an activity.

**prov:Activity**

| Class | Description |
|---|---|
| Definition | Something that occurs over a period of time and acts upon or with entities. |
| Usage Note | Always required when defining provenance for datasets. |
| Properties | dcterms:identifier · dcterms:title · dcterms:description · prov:startedAtTime · prov:endedAtTime |
| Example | `:eodJapanTradeFilterActivity a prov:Activity .` |

#### 5.2.1. Property: Usage

**prov:used**

| Property | Description |
|---|---|
| Requirement Section | B) d. |
| Definition | The entity the activity used to generate the entity. |
| Domain | prov:Activity |
| Range | prov:Entity |
| Optionality | Optional |
| Example | `:eodJapanTradeFilterActivity prov:used :eodTradeDataset .` |

#### 5.2.2. Property: Association

**prov:wasAssociatedWith**

| Property | Description |
|---|---|
| Requirement Section | B) e. |
| Definition | The actor(s) associated with performing the activity. |
| Domain | prov:Activity |
| Range | prov:Agent |
| Optionality | Required |
| Example | `:eodJapanTradeFilterActivity prov:wasAssociatedWith :athenaRates .` |

#### 5.2.3. Property: Start

**prov:startedAtTime**

| Property | Description |
|---|---|
| Requirement Section | B) f. |
| Definition | The start time of the activity. |
| Domain | prov:Activity |
| Range | xsd:dateTime or xsd:date |
| Optionality | Optional |
| Example | `:eodJapanTradeFilterActivity prov:startedAtTime "2025-09-01T23:30:00Z"^^xsd:dateTime .` |

#### 5.2.4. Property: End

**prov:endedAtTime**

| Property | Description |
|---|---|
| Requirement Section | C) g. |
| Definition | The end time of the activity. |
| Domain | prov:Activity |
| Range | xsd:dateTime or xsd:date |
| Optionality | Optional |
| Example | `:eodJapanTradeFilterActivity prov:endedAtTime "2025-09-01T23:35:23Z"^^xsd:dateTime .` |

*(note: the "Requirement Section" for End reads `C) g.` on the page — as published; it logically belongs to list B)*

### 5.3. Class: Actors

An actor takes a role in an activity such that the actor can be assigned some degree of responsibility for the activity taking place. An actor can be a person, a piece of software, an inanimate object, an organization, a SEAL ID, or other entities that may be ascribed responsibility. When an actor has some responsibility for an activity, the actor is associated with the activity, where several actors may be associated with an activity and vice-versa.

**prov:Agent**

| Property | Description |
|---|---|
| Definition | A person, piece of software, and organization, or entity ascribed a responsibility that takes a role in an activity. |
| Usage Note | Always required when defining provenance for datasets. |
| Properties | dcterms:identifier |
| Example | `athenaRates a prov:Agent .` |

## 6. ETL/ELT Pipelines

For ETL/ELT pipelines that monitor data movement across multiple systems, databases, data warehouses, applications, BI dashboards, and reports, and where traditional provenance tracking is impractical, provenance should be recorded using OpenLineage with JPMC-approved extensions. OpenLineage is an open framework designed to facilitate the collection, representation, and exchange of data provenance and lineage information across various data processing systems. It enables consistent collection of provenance metadata, allowing for a systems level understanding of how data is produced and used. It aims to provide a unified framework for tracking the flow of data through data ecosystems, enabling organizations to gain insights into data dependencies, transformations, and usage patterns.

OpenLineage is built around several core concepts that capture the essential elements of data provenance. Each implementation of OpenLineage must adhere to the following concepts and provide the following objects:

- Jobs (prov:Activity)
- Runs (prov:Activity)
- Dataset (prov:Entity)

### 6.1 Jobs

| Jobs | |
|---|---|
| Definition | Jobs are tasks or processes that perform operations on data, ranging from simple data transformations to complex data processing workflows, and are central to understanding how data is processed and moved through a system.Each job is defined by its inputs and outputs (the datasets it consumes and produces), is uniquely named within a namespace assigned by the scheduler, and its evolution is documented through its execution over time. |
| Range | ol:jobs |
| Not Required When | Always required when defining provenance for data pipelines. |
| Required Properties | `jobname`: unique identifier for Job ID<br>`sourceCodeLocation`: Captures the source code location and version of the job<br>`sourceCode`: captures the language (e.g., python) and complete source code of the job. |
| Example | A set of tasks or processes that are scheduled to run at a later time. |

### 6.2 Runs

| Runs | |
|---|---|
| Definition | Runs are specific instances of jobs being executed. They capture the dynamic aspect of data processing, recording when and how jobs are executed and what datasets are involved. This allows for detailed tracking of data provenance over time. An event describing an observed state of a job run. Sending at least a START event and a COMPLETE/FAIL/ABORT event is required. Additional events are optional. |
| Range | `ol:runs` |
| Not Required When | Always required when defining Provenance for data pipelines. |
| Required Properties | `runuuid`: unique identifier for Run ID<br>`nominalTime`: the time this run is scheduled for<br>`parent`: the parentJob and Run<br>`errorMessage`: captures potential error messages |
| Example | An instance at a specific runtime of a scheduled job. |

### 6.3 Dataset

| dcat:Dataset | |
|---|---|
| Definition | A collection of Data, published or curated by a single agent, and available for access or download in one or more representations. |
| Sub-class of | dcat:Resource |
| Usage note | Required when a dataset is specified. |
| Properties | dcterms:title, dcterms:description, dcterms:creator, dcterms:contactPoint, dcterms:publisher, dcat:keyword, dcterms:language, dcterms:issued, dcterms:modified, dcat:accrualPeriodicity, dcterms:temporal, dcterms:spatial, dcterms:identifier, dcat:conformsTo, dcat:distribution |

## 7. Ontology Extensions and Exceptions

The process for requesting an exception from this Framework, an extension to the current recommended framework options, or an adjustment to tailor fit your team's needs, as defined in the Data Publishing Frameworks Exception procedure.

## 8. Defined Terms

| Concept | Description |
|---|---|
| Provenance (W3C) | A record that describes the people, institutions, entities, and activities involved in producing, influencing, or delivering a piece of data or a thing. |
| Entity (Prov-O) | A physical, digital, or conceptual thing with a documented provenance, representing data or objects subject to change over time. |
| Activity (Prov-O) | Something that occurs over a period of time and acts upon or with entities; it may include consuming, processing, transforming, modifying, relocating, using, or generating entities. |
| Actor (Prov-O) | Something that bears some form of responsibility for an activity taking place, for the existence of an entity, or for another actor's activity. |
| Jobs (OpenLineage) | Tasks or processes that perform operations on data. |
| Dataset | Collection of related sets of information that is composed of separate elements but can be manipulated as a unit. |
| Runs (OpenLineage) | Specific instances of jobs being executed. |
| Data Provenance | Data provenance is the comprehensive tracking of Data through an organization's systems, tracing the journey from the initial source to consumption or report generation. |
| Metadata | Set of data which describes and gives information about other data. |

## 9. Legal and Other References

Enterprise Library Application (ELA) at https://oloela.gaiacloud.jpmchase.net/procedures-other or go/ela Statutes, Laws, Rules, Regulations or External Guidance. The requirements under this document are to be applied consistent with the statutes, laws, rules, regulations, or external guidance of the jurisdictions in which the firm operates. The below may not represent an exhaustive list and should be cross-referenced with the Obligations in ELA.

## 10. Firm References

Internal Firm Policies and/or Standards, Policy Supplements, Procedures, and Other Documents, Forms, and Systems.

## 11. Document Information

| Concept | Details |
|---|---|
| Primary Risk Category | Enter the applicable risk type from the CCOR Risk Type Taxonomy (required for Operational Risk – Risk Management documents, optional for all others). Level one risk type > level two risk > level three risk |
| Document Level | Level 2, Firmwide |
| Document Owner | Andrew Jennings, Managing Director, Chief Data & Analytics Office, United States |
| Document Primary Contact | Andrew Jennings, Managing Director, Chief Data & Analytics Office, United States |
| Document Secondary Contact | Mitchell Rothenberg, Executive Director, Chief Data & Analytics Office, United States |
| Document Manager | Amanda Brizendine |
| Initial Effective Date | TBD |
| Additional Contacts | TBD |

## 12. Appendix A

Cross-References to PROV-O and PROV-N. PROV-DM is a conceptual data model which can be serialized in various ways. The following table contains the PROV-O classes and properties, as described in PROV-O, and PROV-N productions, as described in PROV-N that correspond to PROV-DM concepts.

| PROV-DM Concept | PROV-O Equivalent | PROV-N Expression |
|---|---|---|
| Entity | Entity | entityExpression |
| Activity | Activity | activityExpression |
| Generation | wasGeneratedBy, Generation | generationExpression |
| Usage | used, Usage | usageExpression |
| Communication | wasInformedBy, Communication | communicationExpression |
| Start | startedAtTime, Start | startExpression |
| End | endedAtTime, End | endExpression |
| Invalidation | wasInvalidatedBy, Invalidation | invalidationExpression |
| Derivation | wasDerivedFrom, Derivation | derivationExpression |
| Revision | wasRevisionOf, Revision | type Revision |
| Quotation | wasQuotedFrom, Quotation | type Quotation |
| Primary Source | hadPrimarySource, PrimarySource | type PrimarySource |
| Agent | Agent | agentExpression |
| Attribution | wasAttributedTo, Attribution | attributionExpression |
| Association | wasAssociatedWith, Association | associationExpression |
| Delegation | actedOnBehalfOf, Delegation | delegationExpression |
| Plan | Plan | type Plan |
| Person | Person | type Person |
| Organization | Organization | type Organization |
| SoftwareAgent | SoftwareAgent | type SoftwareAgent |
| Influence | wasInfluencedBy, Influence | influenceExpression |
| Bundle constructor | bundle description | bundle |
| Bundle type | Bundle | type Bundle |
| Alternate | alternateOf | alternateExpression |
| Specialization | specializationOf | specializationExpression |
| Collection | Collection | type Collection |
| EmptyCollection | EmptyCollection | type EmptyCollection |
| Membership | hadMember | membershipExpression |

### 12.1. PROV Example

In the following example, a Data Consumer utilizes Dataset to create a Report. Metadata for the provenance between the Report and the Dataset will reflect the required classes and properties to understand the complete provenance.

### 12.2. PROV Example Diagram

In Figure 1.1 PROV Example, the entities include Dataset and Report. There is one primary activity performed.

- Activity:Compile show the activity of generating an Entity:Report through the use of Dataset. The Actor:Data Consumer is associated with this action and is attributed to owning the Entity:Report.

In addition to the activity, there is one actor who performed the activities called out.

- Actor:Data Consumer of type person is the consumer of Dataset and creator of the Report. This actor is a downstream dependent on a not displayed Data Producer who would be documented in the provenance metadata of Entity:Dataset. In addition, this actor is directly associated with the Report entity. This allows for clear and documented accountability.

Finally, the blue call out box display metadata attributes of the actions that the actor took.

- Actor:Data Consumer started the compile activity at 9:21:01 AM UTC on January 9th, 2025 and the Activity:Compile completed it at 9:21:15 AM UTC on January 9th 2025.

*Figure 1.1 — PROV graph diagram. A blue call-out box reading "startedAtTime=2025-01-09T09:21:01Z / endedAtTime=2025-01-09T09:21:15Z" attaches by dashed line to "Activity: Compile". "Agent: Data Consumer (Type: Person)" sits at top, linked by `wasAttributedTo` to "Entity: Report" and by `wasAssociatedWith` to "Activity: Compile". "Activity: Compile" links via `used` to "Entity: Dataset (Id, Attributes)" and via `wasGeneratedBy` to "Entity: Report (Id, Attributes)". "Entity: Report" links back to "Entity: Dataset" via `wasDerivedFrom`.*

Figure 1.1: PROV Example To gather a complete data provenance of each Entity:Report attribute, the lineage of each upstream step can be brought together to create a complete picture.

### 12.3. PROV Example Turtle RDF

Converting PROV into a machine readable format, whether Turtle, YML, or XML is critical for automatically checking the lifecycle and provenance of the dataset elements. This above example can be rendered as the following in RDF Turtle syntax.

```turtle
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix ex: <http://example.com/ns#> .

ex:Dataset1
    a prov:Entity ;
    dcterms:identifier "https://jpmchase.com/dataset/Dataset1"^^xsd:anyURI ;
    dcterms:title "An example dataset" ;
    dcterms:description "A source dataset used to compile a report." ;
    prov:wasGeneratedBy ex:DataSourceCreation1 ;
.

ex:Report1
    a prov:Entity ;
    dcterms:identifier "https://jpmchase.com/report/Report1"^^xsd:anyURI ;
    dcterms:title "An example report" ;
    dcterms:description "A report generated from a dataset." ;
    prov:wasDerivedFrom ex:Dataset1 ;
    prov:wasGeneratedBy ex:Compile1 ;
    prov:wasAttributedTo ex:DataConsumer1 ;
.

ex:Compile1
    a prov:Activity ;
    dcterms:identifier "https://jpmchase.com/activity/Compile1"^^xsd:anyURI ;
    dcterms:title "An example compile action" ;
    dcterms:description "An activity that compiles a report from a dataset." ;
    prov:used ex:Dataset1 ;
    prov:wasAssociatedWith ex:DataConsumer1 ;
    prov:startedAtTime "2025-01-09T09:21:01Z"^^xsd:dateTime ;
    prov:endedAtTime "2025-01-09T09:21:15Z"^^xsd:dateTime ;
.

ex:DataSourceCreation1
    a prov:Activity ;
    dcterms:identifier "https://jpmchase.com/activity/DataSourceCreation1"^^xsd:anyURI ;
    dcterms:title "An example of creating an original source data" ;
    dcterms:description "An activity that creates a new dataset." ;
    prov:wasAssociatedWith ex:DataCreator1 ;
    prov:startedAtTime "2025-01-09T09:21:01Z"^^xsd:dateTime ;
    prov:endedAtTime "2025-01-09T09:21:15Z"^^xsd:dateTime ;
.

ex:DataConsumer1
    a prov:Agent ;
    dcterms:identifier "https://jpmchase.com/agent/DataConsumer1"^^xsd:anyURI ;
.

ex:DataCreator1
    a prov:Agent ;
    dcterms:identifier "https://jpmchase.com/agent/DataCreator1"^^xsd:anyURI ;
.
```

### 12.4. PROV Example JSON-LD

The following shows the example in an RDF JSON-LD serialization.

```json
{
 "@context": {
   "dcterms": "http://purl.org/dc/terms/",
   "xsd": "http://www.w3.org/2001/XMLSchema#",
   "prov": "http://www.w3.org/ns/prov#",
   "ex": "http://example.com/ns#"
 },
 "@graph": [
   {
     "@id": "ex:Dataset1",
     "@type": "prov:Entity",
     "dcterms:identifier": {
       "@value": "https://jpmchase.com/dataset/Dataset1",
       "@type": "xsd:anyURI"
     },
     "dcterms:title": "An example dataset",
     "dcterms:description": "A source dataset used to compile a report.",
     "prov:wasGeneratedBy": { "@id": "ex:DataSourceCreation1" }
   },
   {
     "@id": "ex:Report1",
     "@type": "prov:Entity",
     "dcterms:identifier": {
       "@value": "https://jpmchase.com/report/Report1",
       "@type": "xsd:anyURI"
     },
     "dcterms:title": "An example report",
     "dcterms:description": "A report generated from a dataset.",
     "prov:wasDerivedFrom": { "@id": "ex:Dataset1" },
     "prov:wasGeneratedBy": { "@id": "ex:Compile1" },
     "prov:wasAttributedTo": { "@id": "ex:DataConsumer1" }
   },
   {
     "@id": "ex:Compile1",
     "@type": "prov:Activity",
     "dcterms:identifier": {
       "@value": "https://jpmchase.com/activity/Compile1",
       "@type": "xsd:anyURI"
     },
     "dcterms:title": "An example compile action",
     "dcterms:description": "An activity that compiles a report from a dataset.",
     "prov:used": { "@id": "ex:Dataset1" },
     "prov:wasAssociatedWith": { "@id": "ex:DataConsumer1" },
     "prov:startedAtTime": {
       "@value": "2025-01-09T09:21:01Z",
       "@type": "xsd:dateTime"
     },
     "prov:endedAtTime": {
       "@value": "2025-01-09T09:21:15Z",
       "@type": "xsd:dateTime"
     }
   },
   {
     "@id": "ex:DataConsumer1",
     "@type": "prov:Agent",
     "dcterms:identifier": {
       "@value": "https://jpmchase.com/agent/DataConsumer1",
       "@type": "xsd:anyURI"
     }
   },
   {
     "@id": "ex:DataCreator1",
     "@type": "prov:Agent",
     "dcterms:identifier": {
       "@value": "https://jpmchase.com/agent/DataCreator1",
       "@type": "xsd:anyURI"
     }
   }
 ]
}
```

### 12.5. OpenLineage Specification Translated to PROV

Similar to PROV, OpenLineage must have specific properties, or facets, defined in a manner that allow for a machine readable format. All OpenLineage data, and extensions within the firm, must be able to be read by a PROV format. For example, the following turtle code shows a basic example of OpenLineage translated into PROV. In this example, an event is started and track the start and end time of a job that takes an input entity with multiple fields and performs a transformation with a tool "dbt."

```turtle
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix : <http://example.com/ns#> .
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix ol: <http://openlineage.io/ns/0-1-8/> .
@prefix jpmc: <https://data.jpmorgan/> .
@prefix jpmv: <https://vocabulary.jpmorgan/DataPublishing/> .

:Run_uuid a prov:Activity ;
    dcterms:identifier "https://jpmchase.com/activity/Run_uuid"^^xsd:anyURI ;
    dcterms:title "Run:uuid" ;
    dcterms:description "An example activity that started a job." ;
    ol:eventType "START" ;
    prov:startedAtTime "2020-12-28T19:52:00.001+10:00"^^xsd:dateTime ;
    prov:wasAssociatedWith :dbt_executor_1 ;
    ol:runId "d46e465b-d358-4d32-83d4-df660ff614dd" ;
    ol:parent :Parent_id ;
    ol:job :Job_1 ;
    prov:used :Inputs_1 ;
.

:Parent_id a prov:Activity ;
    dcterms:identifier "https://jpmchase.com/activity/Parent_id"^^xsd:anyURI ;
    dcterms:description "An example parent activity that started a job." ;
    dcterms:title "dbt-execution-parent-job";
    prov:wasAssociatedWith :dbt_executor_1 ;
    ol:namespace "dbt-namespace" ;
    ol:runId "f99310b4-3c3c-1a1a-2b2b-c1b95c24ff11" ;
.

:Job_1 a prov:Activity ;
    dcterms:identifier "https://jpmchase.com/activity/Job_1"^^xsd:anyURI ;
    dcterms:description "An example activity associated with executing a SQL query." ;
    ol:namespace "workshop" ;
    dcterms:title "process_taxes" ;
    prov:wasAssociatedWith :dbt_executor_1 ;
    rr:sqlQuery "insert into taxes_out select id, name, is_active from taxes_in" ;
.

:Inputs_1 a prov:Entity ;
    dcterms:identifier "https://jpmchase.com/entity/Inputs_1"^^xsd:anyURI ;
    dcterms:title "Inputs_1" ;
    dcterms:description "An example entity for public taxes." ;
    prov:wasGeneratedBy :ExternalSourceLoad ;
    ol:namespace "postgres://workshop-db:None" ;
    rr:tableName "workshop.public.taxes-in" ;
    ol:sql_schema :Schema_1 ;
.

:Schema_1 a prov:Entity ;
    dcterms:identifier <https://jpmchase.com/entity/Schema_1> ;
    dcterms:title "Schema_1" ;
    dcterms:description "An example schema entity specifying data fields." ;
    prov:wasGeneratedBy :CreateSchema ;
    ol:sql_field :Field_1 ;
    ol:sql_field :Field_2 ;
    ol:sql_field :Field_3 ;
.

:Field_1 a prov:Entity ;
    dcterms:identifier <https://jpmchase.com/entity/Field_1> ;
    dcterms:title "Field_1" ;
    rr:colum "id" ;
    rr:datatype "int" ;
    dcterms:description "Customer's identifier" ;
    prov:wasDerivedFrom :Schema_1 ;
.

:Field_2 a prov:Entity ;
    dcterms:identifier <https://jpmchase.com/entity/Field_2> ;
    dcterms:title "Field_2" ;
    rr:colum "name" ;
    rr:datatype "string" ;
    dcterms:description "Customer's name" ;
    prov:wasDerivedFrom :Schema_1 ;
.

:Field_3 a prov:Entity ;
    dcterms:identifier <https://jpmchase.com/entity/Field_3> ;
    dcterms:title "Field_3" ;
    rr:column "is_active" ;
    rr:datatype "boolean" ;
    dcterms:description "Has customer completed activation process" ;
    prov:wasDerivedFrom :Schema_1 ;
.

:Outputs_1 a prov:Entity ;
    dcterms:identifier <https://jpmchase.com/entity/Outputs_1> ;
    dcterms:title "Outputs_1" ;
    dcterms:description "An example output entity for public taxes." ;
    ol:namespace "postgres://workshop-db:None" ;
    rr:tableName "workshop.public.taxes-out" ;
    ol:sql_schema :Schema1 ;
    prov:wasGeneratedBy :Run_uuid ;
.

:dbt_executor_1 a prov:Agent ;
    dcterms:identifier "https://jpmchase.com/agent/E123456"^^xsd:anyURI ;
    jpmv:sid "E123456" ;
.

:CreateSchema a prov:Activity ;
    dcterms:identifier "https://jpmchase.com/activity/CreateSchema"^^xsd:anyURI ;
    dcterms:description "An example activity associated with creating a schema." ;
    dcterms:title "Create Schema" ;
    prov:wasAssociatedWith :Developer_1 ;
.

:Developer_1 a prov:Agent ;
    dcterms:identifier "https://jpmchase.com/agent/U123456"^^xsd:anyURI ;
    jpmv:sid "U123456" ;
.

:ExternalSourceLoad a prov:Activity ;
    dcterms:identifier "https://jpmchase.com/activity/ExternalSourceLoad"^^xsd:anyURI ;
    dcterms:description "An example activity associated with obtaining data from an external source." ;
    dcterms:title "External Source Load" ;
    prov:wasAssociatedWith :dbt_executor_1 ;
.
```

---

# E. [WIP] Provenance CDAO Framework

> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/6194465802/WIP+Provenance+CDAO+Framework
> **Page tree location:** Firmwide Data Publishing Frameworks → Provenance Framework → **[WIP] Provenance CDAO Framework** (child page) · 1 view
> **Screenshots:** `Screenshot 2026-07-30 180040.png` … `180553.png` (10 shots)

**This page is a work-in-progress copy of the Provenance Framework (section D above).** Every section captured — §3 through §12.5 — matches the parent page verbatim: same class and property tables, same OpenLineage sections, same Defined Terms, same Document Information (Andrew Jennings / Mitchell Rothenberg / Amanda Brizendine), same Appendix A cross-reference table, and the same Turtle / JSON-LD / OpenLineage-to-PROV examples. No content differences were visible in the captured range.

Two things this capture adds that the parent capture clipped:

1. **§5.1.2 Property: Derivations** — the full `prov:wasDerivedFrom` table (reproduced in section D above; its middle rows were lost in the seam between the parent page's screenshots).
2. Confirmation that the CDAO WIP page carries the identical `:Field_1` / `:Field_2` typo `rr:colum` (vs `rr:column` on `:Field_3`).

One difference worth flagging: in this copy the §5.2.4 End example reads `prov:endedAtTime "2025-09-01T23:23Z"^^xsd:dateTime` (rendered without seconds), where the parent page reads `"2025-09-01T23:35:23Z"`. This may be a rendering artifact rather than a real divergence — worth a second look at the source page.

The capture starts partway down the page (at §3 Data Provenance in the earliest shot, with §5.2.2 onward in the clearest sequence); the page title block, §1 Summary and §2 Changes from Previous Version were not screenshotted for this page.

---

# F. Schema Metadata Framework

> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5567745346/Schema+Metadata+Framework
> **Breadcrumb:** Pages / DATAPUBSTRATEGY Home / Firmwide Data Publishing Frameworks · 410 views
> **Screenshots:** `Screenshot 2026-07-30 180728.png` … `181123.png` (9 shots)
> **Coverage:** starts mid-document at §4 (§1–§3 not screenshotted) and ends mid-§6.4.1.3.1.

## 4. Key Requirements of Schema Metadata

It is essential for metadata about schemas to be clear and accessible, especially when the consumers of the data are not explicitly known. Any Schema Metadata produced, including metadata hosted in shared data catalogs, must adhere to the requirements defined in this Framework.

### 4.1 Open Standard Requirements

Any **Schema Metadata generated must** include metadata attributes about the schema metadata such as identifier, format, a reference to the schema metadata components, and a reference to the schema.

To ensure consistency and interoperability, the Schema Metadata **must be** documented using the Schema Metadata format defined in this framework. This standardization facilitates consistent integration with various tools and systems, allowing consumers to seamlessly access and interpret metadata information.

The framework used and how it was used **must be** documented.

Each implementation does not require a manually documented diagram but must include a machine-readable set of documentation that follows an approved framework or be approved as an exception/extension of an approved framework.

### 4.2 Standard Access Method

Whenever a publisher makes Schema Metadata available, **they must** implement a mechanism that allows consumers to query the metadata.

To maximize accessibility, the Schema Metadata **must be** accessible with standard encoding, preferably UTF-8, accessible via standard web protocols, and accessible from a non-proprietary interface. This approach ensures that consumers can easily retrieve and utilize Schema Metadata information, regardless of their technical environment.

### 4.3 Information to be Included in Schema Metadata

Schema Metadata provides essential information for understanding the structure of data across schema types on data shared between LOBs / CFs. Schema Metadata must be applied to schemas for data in the form of structured data (tables and tabular), semi-structured data (JSON, XML), Data Services (APIs, streaming), events (event streaming, message brokers), and other data resources where schemas are applied.

In all cases, metadata must accompany each dataset and its distributions to capture the essential Schema Metadata attributes. At the dataset level, this metadata aligns the logical model with detailed descriptors of each class and its properties. At the distribution level, the logical model is mapped to the physical model for the distribution format. These requirements can be satisfied by providing an RDFS/OWL or SHACL Shapes model of the schema per the guidelines provided in Section 6.

```
A) For each dataset, a logical model (when available) including:
     a. JPMC identifier for the logical model (See the JPMC Identifiers Specification).
     b. For every class in the logical model, model, the following information is required:
          i. A class definition for the logical model class
          ii. The class name
     c. For each property in the logical model, the following information is required::
          i. A property definition for the logical model property
          ii. The class the property belongs to
          iii. The property name
          iv. The data type of the property
B) For each dataset distribution where a model is available, the following physical model properties are required, unless otherwise specified:
     a. For distributions using a relational database
          i.    Characteristics of the table (temporary, ReadOnly)
          ii.   For each column:
               1. The property in the corresponding logical model which the column represents
               2. Type of the column
               3. Precision of the column
               4. Scale of the column
               5. Length of the column
               6. Boolean indicating whether the column is Nullable
     b. For distributions using a delimited file
          i. The delimiter used in the file
          ii. Boolean indicating the delimited file uses quoted text
          iii. Boolean indicating whether the first row contains column names
          iv. The record terminator for the file
          v. For each column:
               1. The position of the column
               2. Precision of the column
               3. Scale of the column
               4. Length of the column (optional)
               5. Boolean indicating whether the first column contains column names
     c. For distributions using XML
          i. Elements defined in the XML, including:
               1. The namespace of the element
          ii. Attributes defined in the XML
          iii. If applicable, a complex shape consisting of elements and attributes
     d. For distributions using Protocol Buffer messages
          i. The elements defined in the message
          ii. The element number of the field
     e. For distributions using JSON Schema
          i. Arrays
          ii. Class
          iii. Enumerations
     f. For distributions using Avro Schema
          i. Array
          ii. Record
          iii. Enumeration
```

### 4.4 Information to be Included in Schema Metadata Attributes

When referencing schema metadata within Datasets and Distributions, it is necessary to provide a file that defines the relevant schema metadata attributes. For example, the `dcterms:conformsTo` property in the **Descriptive Metadata Framework** connects a Dataset or Distribution to its schema definition. These attributes provide key information about the Schema Metadata, including links both to the Schema Metadata itself and to the schema it describes. See Section 7 for an example.

```
C) For each Schema the following attributes are required, unless specified otherwise:
     a. A JPMC identifier for the schema metadata (See JPMC Identifiers Specification).
     b. The format of the data represented by the schema (optional).
     c. Links to the Schema Metadata files:
          i. The RDFS/OWL representation of the schema vocabulary (see Section 6.3.1 for an example)
          ii. For physical models the SHACL Extensions for the schema type, as defined in Section 6.4.x.2 (optional)
          iii. The SHACL Shapes file for Schema Metadata, as shown in Sections 6.3 and 6.4 (optional).
     d. A reference to the schema (optional).
     e. The version of the schema (optional).
     f. Title or brief summary statement about the schema metadata (optional).
     g. Brief description with sufficient detail for the consumer to unambiguously understand and identify the schema metadata (optional).
```

Other attributes may be required to adequately describe a schema. Custom attributes can be defined by extending the Schema Metadata Framework per Section 8.

## 5. Schema Attributes Classes and Associated Properties

Schema attributes of the Schema Metadata are properties that provide information about the schema metadata and schema. Schema attributes are defined by instantiating classes and properties as defined below.

### 5.1 Specifying Schema Metadata Attributes

The metadata attributes for Schema Metadata are specified by creating an instance of the `jpmv:SchemaMetadata` class. For compliance with `dcterms:conformsTo` in the Descriptive Metadata Framework and elsewhere, instances of `jpmv:SchemaMetadata` should also be declared to be an instance of `dcterms:Standard`.

**jpmv:SchemaMetadata**

| Field | Value |
|---|---|
| Requirement section | C) |
| Definition | Metadata about the schema. |
| Properties: | `dcterms:title, dcterms:description, dcterms:identifier, dcterms:format, dcterms:conformsTo, dcterms:source, dcterms:hasVersion` |
| Usage Note: | Instances should also be declared to be an instance of `dcterms:Standard`. |

#### 5.1.1 Schema Properties

The following properties are required for instances of jpmv:SchemaMetadata.

**dcterms:identifier**

| Field | Value |
|---|---|
| Requirement section | C) a. |
| Definition | A unique identifier for the schema attributes for the schema metadata. The identifier should be compliant with the JPMC Identifiers Specification. |
| Domain: | jpmv:SchemaMetadata |
| Range: | xsd:anyURI or IRI |
| Usage Note: | Values must be compatible with the JPMC Identifiers Specification. |

**jpmv:schemaMetadataVocabulary**

| Field | Value |
|---|---|
| Requirement section | C) c.i. |
| Definition | A link to the RDFS/OWL representation of the schema vocabulary. |
| Domain: | jpmv:SchemaMetadata |
| Range: | xsd:anyURI or IRI |

#### 5.1.2 Optional Schema Properties

**dcterms:format**

| Field | Value |
|---|---|
| Requirement section | C) b. |
| Definition | The file format of the schema. |
| Domain: | jpmv:SchemaMetadata |
| Range: | rdfs:Resource |
| Usage Note: | Use the IRI of the IANA Media Type (formerly known as MIME types) to describe the file format. Use a text description in the cases where the media type is not registered with IANA. |

**jpmv:schemaMetadataSHACLExtensions**

| Field | Value |
|---|---|
| Requirement section | C) c.ii. |
| Definition | A link to the SHACL Extensions for the schema type. |
| Domain: | jpmv:SchemaMetadata |
| Range: | xsd:anyURI or IRI |
| Usage Note: | This field applies to the physical model representations. |

**jpmv:schemaMetadataSHACL**

| Field | Value |
|---|---|
| Requirement section | C) c.iii. |
| Definition | A link to the SHACL Shapes file for Schema Metadata. |
| Domain: | jpmv:SchemaMetadata |
| Range: | xsd:anyURI or IRI |

**dcterms:source**

| Field | Value |
|---|---|
| Requirement section | C) d. |
| Definition | A reference to the schema. |
| Domain: | jpmv:SchemaMetadata |
| Range: | xsd:anyURI or IRI |

**dcterms:hasVersion**

| Field | Value |
|---|---|
| Requirement section | C) e. |
| Definition | The version number of the schema. |
| Domain: | jpmv:SchemaMetadata |
| Range: | xsd:string |

**dcterms:title**

| Field | Value |
|---|---|
| Requirement section | C) f. |
| Definition | A free-text name given to the schema metadata. |
| Domain: | jpmv:SchemaMetadata |
| Range: | xsd:string |

**dcterms:description**

| Field | Value |
|---|---|
| Requirement section | C) f. |
| Definition | A free-text definition of the schema metadata. |
| Domain: | jpmv:SchemaMetadata |
| Range: | xsd:string |

*(both `dcterms:title` and `dcterms:description` are labelled requirement section `C) f.` — as published)*

Any additional attributes must follow the Schema framework published on https://vocabulary.jpmorgan.

## 6. Representing Schema Metadata

This framework outlines an approach using SHACL metamodeling to define schema metadata for logical and physical data.

### 6.1 Representing Schema Metadata through SHACL Modeling

SHACL (SHApes Constraint Language) is used as a modeling language for describing schema metadata. Its ability to define primitive and structured types, inheritance hierarchies, multiplicity, ordering, uniqueness, and property types makes SHACL particularly well suited for specifying schema metadata.

Key features:

- **Define Classes and Inheritance:** Use `sh:targetClass` or `sh:targetNode` to indicate which RDF classes a shape constrains, and compose hierarchies via shand and `sh:or` to model sub-classing and multiple inheritance.
- **Specify Attributes and Property Types:** `sh:property` shapes capture attributes, specifying datatypes (`sh:datatype`), allowed value classes (`sh:class`), and node kinds (`sh:nodeKind`). Cardinality constraints (`sh:minCount`, `sh:maxCount`) and multiplicity patterns precisely define how many values an attribute may have.
- **Model Relationships and Logical Composition:** Nested shapes enable you to model complex associations: a property's value can be constrained by another Node Shape. Logical operators (`sh:and`, `sh:or`, `sh:not`, `sh:xone`) permit rich combinations of constraints, mirroring the expressivity of OWL class expressions.

By leveraging these constructs, SHACL does more than validate – it becomes the canonical, machine-readable definition of schema, unifying documentation, constraint specification, and model semantics.

### 6.2 Representing Logical and Physical Models with SHACL

The figure below depicts SHACL modeling with logical and physical models and levels of validation. The top picture shows how SHACL is used as a language for validating RDF graphs. Furthermore, those Shapes are expressed using the SHACL Vocabulary and SHACL Shapes can be created to validate that the SHACL Shapes themselves are correctly using the SHACL Vocabulary (W3C has published the shacl-shacl.ttl file for this purpose). The SHACL Shapes can be used to validate themselves (the bent red arrow).

*Figure: a two-part layered diagram. The upper part shows boxes "Inst" (blue), "Vocab" and "Shapes" (green), and "SHACL Vocab" and "SHACL Shapes" (orange), connected by blue "uses vocab" arrows and red "checks" arrows, with a bent red self-referencing arrow on SHACL Shapes. The lower part repeats the same layering with hatched "Vocab", green "Shapes", and orange "SHACL Shapes" plus a yellow "Physical Extras" box, grouped under braces labelled M0, M1 and M2; annotation to the right reads "Physical Extras includes" / "Physical Extras SHACL says that Table shape can have at most one isTemporary property of type xsd:boolean".*

Representing Schema Metadata involves defining both the schema vocabulary and its SHACL Shape model. Modeling a physical schema builds on this by extending those shapes, via subclassing sh:NodeShape and sh:PropertyShape, while defining the schema vocabulary and using the SHACL Extended Shapes to capture the concrete structure.

#### 6.2.1 Defining a SHACL Subset for Schema Modelling

SHACL allows the definition of any number of constraints – even none – but for schema modeling we mandate that a core set of constraints be specified:

- For every class-like or table-like structure, there must be a `sh:NodeShape`
- The Node Shape will use `sh:targetClass` to identify an underlying `rdfs:Class`
- The underlying class will have a `rdfs:label`, giving its name
- The underlying class can have a `rdfs:comment` providing additional explanation about the class
- If the underlying `rdfs:Class` specializes (inherits from) another class, it will `rdfs:subClassOf` the general class
- The sh:NodeShape will have one or more `sh:property` expression for each `rdf:Property` that applies to the `rdfs:Class` — If the property is "set-like", i.e. the property has a maximum number of instances of one or is unordered and unique, the `sh:property` (which is a `sh:PropertyShape`) will have:
    - `sh:path` specifying the `rdf:Property`
    - The underlying `rdf:Property` property will have a `rdfs:label`, giving its name
    - The underlying `rdf:Property` property can have a `rdfs:comment`, providing additional explanation about the property
    - `sh:datatype` specifying the datatype if it is a primitive type
    - `sh:class` specifying the nested class, if it is not a primitive type
    - `sh:minCount` if the lower multiplicity is not 0
    - `sh:maxCount` if the upper multiplicity is not unbounded
- Else it can use a different pattern designed to ensure that each member of a `rdf:List` (or other container) is of the right type

A "set-like" property has upper multiplicity of 1, or is unordered and unique. Non-"set-like" properties can be represented using `rdf:List` (or other containers).

Lists preserve the order and allow duplicates. This pattern for lists is allowed and supported:

```turtle
sh:property [
        sh:path ex:SomeClass-someMultiValuedProperty ;
        sh:maxCount 1 ;
   ] , [
        sh:path ( ex:SomeClass-someMultiValuedProperty
          [ sh:zeroOrMorePath rdf:rest ] rdf:first ) ;
        sh:class ex:SomeValueType ;
   ]
```

In a logical model, the `sh:datatype` would be one of the standard XML Schema Definition (`xsd:`) types.

When physical models are represented in SHACL:

- A specific physical extension of `sh:NodeShape` must be used
- This extended shape can have additional properties, specifying class level information
- A specific physical extension of `sh:PropertyShape` must be used
- This extended shape can have additional properties, specifying property level information. In some cases, these additional properties will be mandatory
- The `sh:datatype` could well identify a specific physical datatype (e.g. ORACLE VARCHAR2)
- A publisher can supply a mapping from the physical datatypes as they understand them, to the set of physical datatypes as defined by firmwide, For example what CIB knows as ORACLE VARCHAR2 is known in firmwide as VARCHAR. When such mappings are known, `jpmv:mapsToType` should be used for the mapping e.g.

```
`cib-oracle:VARCHAR2 jpmv:mapsToType jpmc:VARCHAR`
```

### 6.3 SHACL Model for a Logical Example

The following figure depicts a logical model for an example defining Person and Home Address classes with associated attributes and relationships (associations).

*Figure: a UML class diagram in a frame labelled "package Address Example [ AddressExample ]". A "Person" class with attributes familyName : string [1] and givenName : string [1..\*] is linked by an association labelled "address" (multiplicity 1) to a "Postal Address" class with attributes addressLine : string [1], postalCity : string [1], postalRegion : string [1..\*] and postalCode : string [1].*

#### 6.3.1 Defining a Schema Vocabulary for the Example Address – Logical Model

The following, in RDF Turtle serialization, defines a schema vocabulary for the example address model. This model would be generated from the modelling tool. The MagicDraw Concept Modeler support a variation of this mapping out-of-the-box (see Appendix B).

**Note:** The properties in this example and other below are defined as members of `owl:DatatypeProperty` (literals) and `owl:ObjectProperty` (objects). Alternatively, their common superclass, `rdf:Property`, could be used in place of these specific property types.

```turtle
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix expha: <http://cdao.data.jpmorgan/examples/PersonHomeAddress/> .

expha: a owl:Ontology ;
     dcterms:identifier "http://cdao.data.jpmorgan/examples/PersonHomeAddress/"^^xsd:anyURI ;
     rdfs:label "Vocabulary for Person Home Address example" ;
     rdfs:comment "Conversion of Person with a home address example from a logical model to an RDFS/OWL ontology." .

expha:Person a rdfs:Class ;
     rdfs:label "Person" ;
     rdfs:comment "Class representing the Person class in the logical model" ;
     rdfs:isDefinedBy expha: .

expha:firstName a owl:DatatypeProperty ;
     rdfs:label "First Name" ;
     rdfs:comment "Property representing the first name property for the Person class" ;
     rdfs:domain expha:Person ;
     rdfs:range xsd:string ;
     rdfs:isDefinedBy expha: .

expha:lastName a owl:DatatypeProperty ;
     rdfs:label "Last Name" ;
     rdfs:comment "Property representing the last name property for the Person class" ;
     rdfs:domain expha:Person ;
     rdfs:range xsd:string ;
     rdfs:isDefinedBy expha: .

expha:address a owl:ObjectProperty ;
     rdfs:label "address" ;
     rdfs:comment "The address relationship between instances of Person and Home Address" ;
     rdfs:domain expha:Person ;
     rdfs:range expha:HomeAddress ;
     rdfs:isDefinedBy expha: .

expha:HomeAddress a rdfs:Class ;
     rdfs:label "Home Address" ;
     rdfs:comment "Class representing the HomeAddress class in the logical model" ;
     rdfs:isDefinedBy expha: .

expha:streetAddress a owl:DatatypeProperty ;
     rdfs:label "Street Address" ;
     rdfs:comment "Property representing the street address property for the HomeAddress class" ;
     rdfs:domain expha:HomeAddress ;
     rdfs:range xsd:string ;
     rdfs:isDefinedBy expha: .

expha:floorNumber a owl:DatatypeProperty ;
     rdfs:label "Floor Number" ;
     rdfs:comment "Property representing the floor number property for the HomeAddress class" ;
     rdfs:domain expha:HomeAddress ;
     rdfs:range xsd:int ;
     rdfs:isDefinedBy expha: .

expha:city a owl:DatatypeProperty ;
     rdfs:label "City" ;
     rdfs:comment "Property representing the city property for the HomeAddress class" ;
     rdfs:domain expha:HomeAddress ;
     rdfs:range xsd:string ;
     rdfs:isDefinedBy expha: .

expha:region
     a owl:DatatypeProperty ;
     rdfs:label "Region" ;
     rdfs:comment "Property representing the region property for the HomeAddress class" ;
     rdfs:domain expha:HomeAddress ;
     rdfs:range xsd:string ;
     rdfs:isDefinedBy expha: .

expha:postalCode
     a owl:DatatypeProperty ;
     rdfs:label "Postal Code" ;
     rdfs:comment "Property representing the postal code property for the HomeAddress class" ;
     rdfs:domain expha:HomeAddress ;
     rdfs:range xsd:string ;
     rdfs:isDefinedBy expha: .
```

#### 6.3.2. RDFS/OWL Model for Address Example

The following satisfies the criteria in Section 4.3 for defining schema metadata. It adds multiplicity definitions to the vocabulary to specify the logical model schema.

```turtle
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix expha: <http://cdao.data.jpmorgan/examples/PersonHomeAddress/> .

expha:
     a owl:Ontology ;
     dcterms:identifier
      "http://cdao.data.jpmorgan/examples/PersonHomeAddress/"^^xsd:anyURI ;
     rdfs:label "Vocabulary for Person Home Address example" ;
     rdfs:comment "Conversion of Person with a home address example from a logical model to an RDFS/OWL ontology." .

expha:Person
     a rdfs:Class ;
     rdfs:label "Person" ;
     rdfs:comment "Class representing the Person class in the logical model" ;
     rdfs:subClassOf [
```

*(**gap** between screenshots `181006` and `181055` — the remainder of §6.3.2's RDFS/OWL listing, any following 6.3.x subsections, and §6.4, §6.4.1 and §6.4.1.1 up to the start of §6.4.1.2 were not captured)*

```turtle
     rdfs:isDefinedBy expha: .
```

#### 6.4.1.2. Datatypes for Relational Schema

The following define datatypes to be used in the schema metadata for relational schema. These values are from ANSI SQL. Where physical implementations differ, datatypes can be declare in the same manner, as instances of `rdfs:Datatype`.

```turtle
phys-sql-types:Bigint                       a rdfs:Datatype .
phys-sql-types:BinaryLargeObject            a rdfs:Datatype .
phys-sql-types:Blob                         a rdfs:Datatype .
phys-sql-types:Boolean                      a rdfs:Datatype .
phys-sql-types:CharLargeObject              a rdfs:Datatype .
phys-sql-types:Character                    a rdfs:Datatype .
phys-sql-types:CharacterLargeObject         a rdfs:Datatype .
phys-sql-types:CharacterVarying             a rdfs:Datatype .
phys-sql-types:Date                         a rdfs:Datatype .
phys-sql-types:Decimal                      a rdfs:Datatype .
phys-sql-types:DoublePrecision              a rdfs:Datatype .
phys-sql-types:Float                        a rdfs:Datatype .
phys-sql-types:Integer                      a rdfs:Datatype .
phys-sql-types:Interval                     a rdfs:Datatype .
phys-sql-types:NationalCharacter            a rdfs:Datatype .
phys-sql-types:NationalCharacterLargeObject a rdfs:Datatype .
phys-sql-types:NationalCharacterVarying     a rdfs:Datatype .
phys-sql-types:Numeric                      a rdfs:Datatype .
phys-sql-types:Real                         a rdfs:Datatype .
phys-sql-types:Smallint                     a rdfs:Datatype .
phys-sql-types:Time                         a rdfs:Datatype .
phys-sql-types:TimeWithTimezone             a rdfs:Datatype .
phys-sql-types:Timestamp                    a rdfs:Datatype .
phys-sql-types:TimestampWithTimezone        a rdfs:Datatype .
phys-sql-types:Xml                          a rdfs:Datatype .
```

#### 6.4.1.3. SHACL Extensions for Relational Schema

The following defines a set of extensions to SHACL for relational schemas:

```turtle
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix phys-sql-shapes: <http://physical.dps.fdm.jpmc.com/sql/shapes/> .
@prefix phys-sql-types: <http://physical.dps.fdm.jpmc.com/sql/types/> .

phys-sql-shapes:
     a owl:Ontology ;
     rdfs:label "SHACL extensions for relational schema physical models." .

phys-sql-shapes:TableShape
     a rdfs:Class ;
     rdfs:subClassOf sh:NodeShape .

phys-sql-shapes:TableShape-isTemporary
     a rdf:Property ;
     rdfs:domain phys-sql-shapes:TableShape ;
     rdfs:range xsd:boolean .

phys-sql-shapes:ViewShape
     a rdfs:Class ;
     rdfs:subClassOf sh:NodeShape .

phys-sql-shapes:ViewShape-isReadOnly
     a rdf:Property ;
     rdfs:domain phys-sql-shapes:ViewShape ;
     rdfs:range xsd:boolean .

phys-sql-shapes:ViewShape-queryExpression
     a rdf:Property ;
     rdfs:domain phys-sql-shapes:ViewShape ;
     rdfs:range xsd:string .

phys-sql-shapes:ColumnShape
     a rdfs:Class ;
     rdfs:subClassOf sh:PropertyShape .

phys-sql-shapes:ColumnShape-precision
     a rdf:Property ;
     rdfs:domain phys-sql-shapes:ColumnShape ;
     rdfs:range xsd:integer .

phys-sql-shapes:ColumnShape-scale
     a rdf:Property ;
     rdfs:domain phys-sql-shapes:ColumnShape ;
     rdfs:range xsd:integer .

phys-sql-shapes:ColumnShape-length
     a rdf:Property ;
     rdfs:domain phys-sql-shapes:ColumnShape ;
     rdfs:range xsd:integer .

phys-sql-shapes:ColumnShape-isNullable
     a rdf:Property ;
     rdfs:domain phys-sql-shapes:ColumnShape ;
     rdfs:range xsd:boolean .
```

#### 6.4.1.4. Alternatives for Defining Relational Physical Models

The following sections define the Vocabulary/SHACL and RDFS/OWL approach to defining a common machine-readable format for relational physical models.

#### 6.4.1.3.1. SHACL Shapes for Relational Schema Example

*(the page numbers 6.4.1.4 before 6.4.1.3.1 — as published)*

The following defines the shapes based on the extensions for Relational Schema. Note that the SHACL extensions from the previous section are used for the type statement on the Node shapes. I.e. `phys-sql-shapes:TableShape`, the extension to Node shape for relational schema is the type for `expha-rel-shapes:Person`. The schema vocabulary, as defined for the logical model in Section 6.4.1.1 for the Relational Schema example are referenced in the `sh:path` expressions.

```turtle
expha-rel-shapes:
    a owl:Ontology ;
    rdfs:label "Shapes for Relational Schema person address example" ;
    owl:imports <http://cdao.data.jpmorgan/examples/PersonHomeAddress/>,
                <http://physical.dps.fdm.jpmc.com/sql/shapes/> .

expha-rel-shapes:Person
    a phys-sql-shapes:TableShape ;
    sh:targetClass expha:Person ;
    rdfs:isDefinedBy expha-rel-shapes: ;
    sh:property [ a phys-sql-shapes:ColumnShape ;
            phys-sql-shapes:ColumnShape-length 10 ;
            rdfs:isDefinedBy expha-rel-shapes: ;
            sh:datatype phys-sql-types:Character ;
            sh:maxCount 1 ;
            sh:path expha:person_address ],
        [ a phys-sql-shapes:ColumnShape ;
            phys-sql-shapes:ColumnShape-isNullable false ;
            phys-sql-shapes:ColumnShape-length 50 ;
            rdfs:isDefinedBy expha-rel-shapes: ;
            sh:datatype phys-sql-types:Character ;
            sh:maxCount 1 ;
```

*(capture ends here — the rest of §6.4.1.3.1 and everything from §7 onward were not screenshotted)*

---

# G. Business Processes Metadata Framework

> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5762464960/Business+Processes+Metadata+Framework
> **Breadcrumb:** Pages / … / Drafts and Upcoming Frameworks · 445 views
> **Created by:** Marin, James · **Last updated by:** Tong, Jan on Jul 09, 2026 · 15 minute read
> **Screenshots:** `Screenshot 2026-07-30 181812.png` … `182057.png` (9 shots)

## Business Process Framework

\*\* Effective Date: TBD \*\* This is a draft version as of 2026/07/07 intended for review and commentary at the Council vote, and is subject to change prior to official adoption.

**This Framework represents a recommended default approach; however, adoption is only required when specified by a firmwide Standard or Procedure. Must statements in this document are only applicable when adopting this Framework.**

### TABLE OF CONTENTS

1. Summary
2. Changes from Previous Version
3. Business Process Framework
   - 3.1. Key Definitions
4. Key Requirements to Create a New Business Process Framework
   - 4.1. Open Standard Requirements
   - 4.2. Standard Access Method
   - 4.3. Information to be Included
5. Business Process Framework Classes and Associated Properties
   - 5.1. Required Metadata Properties
     - 5.1.1. Class: jpmv:BusinessProcess — Business Process
       - 5.1.1.5. Property: jpmv:hasGrounding — Grounding Concept
     - 5.1.2. Class: jpmv:BusinessProcessSubProcess — Sub-process
     - 5.1.3. Class: jpmv:BusinessProcessPerformerRelierRelationship — Performer-Relier Relationship
     - 5.1.4. Class: jpmv:ThirdPartyOutsourcingEngagement — TPO Engagement
6. Specifying a Business Process Framework: Examples
   - 6.1. Client Onboarding
   - 6.2. Payments Exception Handling Sub-process (Multiple Performer-Relier Relationships)
   - 6.3. KYC Verification Sub-process
7. SHACL Verification
- Appendix A. Specifying a Business Process Framework: Examples (Turtle Format)
   - A.1. Client Onboarding
   - A.2. KYC Verification Sub-process
   - A.3. Payments Exception Handling Sub-process (Multiple Performer-Relier Relationships)

## 1. Summary

The Business Process Framework defines the core data items that JPMorgan Chase captures for business processes. A business process is a series of steps that, when executed, achieve a specific desired outcome. Processes can be executed with a pre-defined frequency and sequence or can be event-based. In practice, these processes are represented as structured sets of related activities that collectively produce a specific service or product for customers, or that achieve a business goal. Its primary purpose is to provide a clear, authoritative description of the information the Firm records about each business process, including processes and sub-processes and the key organizational and application context associated with them. The framework captures the core data items for these processes — not every known attribute, but the essential ones that support consistent data management and AI-enabled processes across the Firm.

The framework is intended for a broad audience within the Firm, including managers and data owners who are responsible for business process data, subject-matter experts (SMEs) who work with that data day to day, and the data scientists and developers who build and maintain the systems that consume it.

The Business Process Framework provides a structured reference for AI Agents that read, write, or query business process data, helping accelerate AI readiness across the Firm. To support this, each data item includes a description designed to be correctly understood by AI Agents without the need for additional context.

The framework's initial version focuses on *what* is involved in a business process and *how* those things are related to each other. Future versions will accommodate models that capture *what happens* during the execution of a business process. The model is intentionally extensible so that all types of business assets — people, locations, products, technology, and more — can be associated at the right level of granularity with a business process, sub-process, or performer-relier relationship. Assets that are stable regardless of the performer-relier combination are typically modeled at the business process or sub-process level, while assets that vary by performer-relier combination are modeled at the performer-relier relationship level.

## 2. Changes from Previous Version

| Version | Effective Date | Summary of Changes |
|---|---|---|
| 0.1.0 | 2026-05-13 | Initial version of the Business Process Framework. |

## 3. Business Process Framework

A business process is a series of steps that, when executed, achieve a specific desired outcome. Processes can be executed with a pre-defined frequency and sequence or can be event-based. In the context of this framework, business processes are represented as related, structured activities that collectively produce a specific service or product for a customer or achieve a business goal. Business processes are the building blocks of the products and services a firm delivers. They may be decomposed into sub-processes, each of which can be owned, governed, and monitored independently while remaining connected to the overall process flow.

Understanding this framework requires familiarity with a small number of core concepts. The key terms used throughout this document are defined in section 3.1 below.

### 3.1. Key Definitions

**Business Process.** Series of steps that, when executed achieve a specific desired outcome. Processes can be executed with a pre-defined frequency and sequence or can be event-based. (per the CORE Firmwide Standard)

**Sub-process.** Specific and distinct actions or steps required to execute each process. (per the CORE Firmwide Standard)

**Performer-Relier Relationship.** A performer-relier relationship captures the organizational sides for a sub-process — specifically, the legal entity and line of business or corporate function (LOB/CF) that performs the sub-process, and the legal entity and LOB/CF that relies on its outcome. A single sub-process can have multiple performer-relier relationships to represent different performer and relier combinations. Each performer-relier relationship can also capture associated application context and third-party outsourcing engagements used in carrying out the sub-process.

## 4. Key Requirements to Create a New Business Process Framework

This section defines the key requirements for applications and data models that hold or provide access to business process metadata at JPMorgan Chase.

The requirements span three areas: openness of data formats; standardization of access methods; and the scope of information to be captured. Together they aim to ensure that business process data is accessible, interoperable, and usable by both AI Agents and business users.

### 4.1. Open Standard Requirements

Applications that hold business process metadata must make that data available in an open data format — either a JPMorgan Chase open data format or a widely adopted third-party open data format. Rich metadata describing the business process data must also be made available in an open data format, and must be directly usable by AI Agents, Subject Matter Experts (SMEs), Data Scientists, and Software Developers without requiring specialist tools to decode it.

Where business process data or its metadata is accessible only through a vendor-proprietary format, this creates an interoperability risk. It can limit the ability of AI tools and human practitioners to access and use the data in a consistent way, and should be addressed in line with applicable governance and prioritization.

To support AI Agents uniformly across different applications, recommended practice is for all business process metadata models to include a mapping to this Business Process Framework — that is, to the RDFS/SHACL schema and the concept schemes defined in section 5. A consistent mapping enables AI Agents to interpret and work with business process data regardless of the underlying application that stores it.

### 4.2. Standard Access Method

Applications that hold business process metadata must make that data accessible via a standard API type, such as a REST API or a simple URL-based access mechanism. Documentation describing the access method must be made available alongside the data, and must be directly usable by AI Agents, Subject Matter Experts (SMEs), Data Scientists, and Software Developers without requiring specialist knowledge of a particular system.

Where business process metadata is available only in a proprietary format, this creates an interoperability risk. It can introduce barriers for AI-driven workflows and for users who need to access data across multiple systems.

### 4.3. Information to be Included

The following section describes the information recorded for each class in the Business Process Framework.

**Business Process.** Series of steps that, when executed achieve a specific desired outcome. Processes can be executed with a pre-defined frequency and sequence or can be event-based. (per the CORE Firmwide Standard) A **Business Process** has:

- a process name (title), which is required;
- a description, which is required;
- a process identifier, which is required;
- a process owner, which is required;
- zero or more grounding concept references, which are optional and used when a grounding taxonomy is available for the business unit.

**Sub-process.** Specific and distinct actions or steps required to execute each process. (per the CORE Firmwide Standard) A **Sub-process** has:

- a process name (title), which is required;
- a description, which is required;
- a process identifier, which is required;
- a process owner, which is required;
- a reference to the parent business process, which is required;
- one or more performer-relier relationships.

**Performer-Relier Relationship.** Captures the performer and relier for a sub-process. A **Performer-Relier Relationship** has:

- one or more relier legal entities, which are required;
- zero or more relier LOB or CF values;
- one or more performer legal entities, which are required (multiple performers may be required for "follow-the-sun" processes, for example);
- one or more performer LOBs or CFs, included if known or applicable;
- zero or more technology asset identifiers;
- zero or more technology deployment identifiers (when provided, a corresponding technology asset identifier should also be provided);
- optionally, one or more third-party outsourcing engagements.

A sub-process can include more than one **Performer-Relier Relationship** to capture different performer and relier combinations. Each relationship instance records the specific performer-relier combination and associated context for that case. In general, relationship-specific execution context belongs on **Performer-Relier Relationship**, whereas assets that remain true across all performer-relier combinations for the same sub-process should be modeled at the process or sub-process level.

**Third-Party Outsourcing Engagement** records an engagement involving an external supplier, including where the supplier performs services and where third-party software or technology is used in execution. A **Third-Party Outsourcing Engagement** has:

- a unique identifier, which is required;
- a title, which is required;
- a description, which is required.

## 5. Business Process Framework Classes and Associated Properties

This section defines the technical specifications for the Business Process Framework, covering classes and associated properties and controlled vocabularies.

### 5.1. Required Metadata Properties

#### 5.1.1. Class: jpmv:BusinessProcess — Business Process

| Property | Value |
|---|---|
| URI | `jpmv:BusinessProcess` |
| Label | Business Process |
| Description | Series of steps that, when executed achieve a specific desired outcome. Processes can be executed with a pre-defined frequency and sequence or can be event-based. |

#### 5.1.1.1. Property: dcterms:title — Process Name

| Property | Value |
|---|---|
| URI | `dcterms:title` |
| Label | Process Name |
| Description | The name of the business process. |
| Domain | `jpmv:BusinessProcess` |
| Range | `xsd:string` |
| Min Count | 1 |
| Max Count | 1 |

#### 5.1.1.2. Property: dcterms:description — Description

| Property | Value |
|---|---|
| URI | `dcterms:description` |
| Label | Description |
| Description | A textual description of the business process, including its purpose and scope. |
| Domain | `jpmv:BusinessProcess` |
| Range | `xsd:string` |
| Min Count | 1 |
| Max Count | 1 |

#### 5.1.1.3. Property: bpds:processIdentifier — Process ID

| Property | Value |
|---|---|
| URI | `bpds:processIdentifier` |
| Label | Process ID |
| Description | A unique identifier for the business process within the Firm's process inventory. Subproperty of `dcterms:identifier`. |
| Domain | `jpmv:BusinessProcess` |
| Range | Literal |
| Min Count | 1 |
| Max Count | 1 |
| Subproperty of | `dcterms:identifier` |

#### 5.1.1.4. Property: jpmv:processOwner — Process Owner

| Property | Value |
|---|---|
| URI | `jpmv:processOwner` |
| Label | process owner |
| Description | The person or organizational unit accountable for the design, performance, and improvement of the business process. |
| Domain | `jpmv:BusinessProcess` (also `jpmv:BusinessProcessSubProcess`) |
| Range | IRI |
| Min Count | 1 |
| Max Count | 1 |

#### 5.1.1.5. Property: jpmv:hasGrounding — Grounding Concept

| Property | Value |
|---|---|
| URI | `jpmv:hasGrounding` |
| Label | has grounding |
| Description | Optional reference from a business process to one or more grounding taxonomy concepts. This is a parent property intended for extensibility: implementations may define specialized subproperties (for example, for function, capability, risk, or regulatory grounding) as subproperties of `jpmv:hasGrounding`. Use `jpmv:hasGrounding` directly when no specialized subproperty is defined. Should be used when the business unit has a controlled vocabulary or taxonomy to classify business processes. |
| Domain | `jpmv:BusinessProcess` |
| Range | IRI (`skos:Concept`) |
| Min Count | 0 |
| Max Count | unbounded |

#### 5.1.2. Class: jpmv:BusinessProcessSubProcess — Sub-process

| Property | Value |
|---|---|
| URI | `jpmv:BusinessProcessSubProcess` |
| Label | Sub-process |
| Description | Specific and distinct actions or steps required to execute each process. |

#### 5.1.2.1. Property: dcterms:title — Process Name

| Property | Value |
|---|---|
| URI | `dcterms:title` |
| Label | Process Name |
| Description | The name of the sub-process. |
| Domain | `jpmv:BusinessProcessSubProcess` |
| Range | `xsd:string` |
| Min Count | 1 |
| Max Count | 1 |

#### 5.1.2.2. Property: dcterms:description — Description

| Property | Value |
|---|---|
| URI | `dcterms:description` |
| Label | Description |
| Description | A textual description of the sub-process, including its purpose and scope within the parent business process. |
| Domain | `jpmv:BusinessProcessSubProcess` |
| Range | `xsd:string` |
| Min Count | 1 |
| Max Count | 1 |

#### 5.1.2.3. Property: bpds:processIdentifier — Process ID

| Property | Value |
|---|---|
| URI | `bpds:processIdentifier` |
| Label | Process ID |
| Description | A unique identifier for the sub-process within the Firm's process inventory. |
| Domain | `jpmv:BusinessProcessSubProcess` |
| Range | Literal |
| Min Count | 1 |
| Max Count | 1 |
| Subproperty of | `dcterms:identifier` |

#### 5.1.2.4. Property: jpmv:processOwner — Process Owner

| Property | Value |
|---|---|
| URI | `jpmv:processOwner` |
| Label | process owner |
| Description | The person or organizational unit accountable for the sub-process. |
| Domain | `jpmv:BusinessProcessSubProcess` |
| Range | IRI |
| Min Count | 1 |
| Max Count | 1 |

#### 5.1.2.5. Property: jpmv:subProcessOf — Sub-process Of

| Property | Value |
|---|---|
| URI | `jpmv:subProcessOf` |
| Label | subprocess of |
| Description | Links the sub-process to the parent business process of which it forms a part. |
| Domain | `jpmv:BusinessProcessSubProcess` |
| Range | `jpmv:BusinessProcess` |
| Min Count | 1 |
| Max Count | 1 |

#### 5.1.2.6. Property: jpmv:hasExecutionRelationship — Execution Relationship

| Property | Value |
|---|---|
| URI | `jpmv:hasExecutionRelationship` |
| Label | has execution relationship |
| Description | Associates the sub-process with one or more performer-relier relationships that capture the performer and relier organizational sides. |
| Domain | `jpmv:BusinessProcessSubProcess` |
| Range | `jpmv:BusinessProcessPerformerRelierRelationship` |
| Min Count | 1 |
| Max Count | unbounded |

#### 5.1.3. Class: jpmv:BusinessProcessPerformerRelierRelationship — Performer-Relier Relationship

| Property | Value |
|---|---|
| URI | `jpmv:BusinessProcessPerformerRelierRelationship` |
| Label | Performer-Relier Relationship |
| Description | A performer-relier relationship captures the organizational sides for a sub-process, including the entities that perform it and those that rely on its outcome, together with any relevant third-party engagements and other relationship-specific execution context. Assets that are not relationship-specific should be modeled at the process or sub-process level. |

#### 5.1.3.1. Property: jpmv:relierLegalEntity — Relier Legal Entity

| Property | Value |
|---|---|
| URI | `jpmv:relierLegalEntity` |
| Label | relier legal entity |
| Description | A relier legal entity is the legal entity that relies on a business process being conducted. The relier legal entity may or may not be the same legal entity that performs the business process. |
| Domain | `jpmv:BusinessProcessPerformerRelierRelationship` |
| Range | IRI |
| Min Count | 1 |
| Max Count | unbounded |

#### 5.1.3.2. Property: jpmv:relierLobCf — Relier LOB or CF

| Property | Value |
|---|---|
| URI | `jpmv:relierLobCf` |
| Label | relier LOB or CF |
| Description | The line of business (LOB) or corporate function (CF) that relies on the outcomes, results, or services produced by a specific process, subprocess, or task. |
| Domain | `jpmv:BusinessProcessPerformerRelierRelationship` |
| Range | IRI |
| Min Count | 0 |
| Max Count | unbounded |

#### 5.1.3.3. Property: jpmv:performerLegalEntity — Performer Legal Entity

| Property | Value |
|---|---|
| URI | `jpmv:performerLegalEntity` |
| Label | performer legal entity |
| Description | A performer legal entity carries out a business process. It can carry out the business process on its own behalf or for a relier legal entity. Multiple performer legal entities can be associated with a single performer-relier relationship, particularly to support follow-the-sun operations or other collaborative execution models. |
| Domain | `jpmv:BusinessProcessPerformerRelierRelationship` |
| Range | IRI |
| Min Count | 1 |
| Max Count | unbounded |

#### 5.1.3.4. Property: jpmv:performerLobCf — Performer LOB or CF

| Property | Value |
|---|---|
| URI | `jpmv:performerLobCf` |
| Label | performer LOB or CF |
| Description | The line of business (LOB) or corporate function (CF) that carries out, executes, or completes a specific process, subprocess, or task. Multiple LOBs or CFs can be associated with a single performer-relier relationship, particularly to support follow-the-sun operations or other collaborative execution models. |
| Domain | `jpmv:BusinessProcessPerformerRelierRelationship` |
| Range | IRI |
| Min Count | 0 |
| Max Count | unbounded |

#### 5.1.3.5. Property: jpmv:technologyAsset — Technology Asset

| Property | Value |
|---|---|
| URI | `jpmv:technologyAsset` |
| Label | Technology Asset |
| Description | A URI identifying a technology asset (such as an application) used in executing the sub-process. |
| Domain | `jpmv:BusinessProcessPerformerRelierRelationship` |
| Range | IRI |
| Min Count | 0 |
| Max Count | unbounded |

#### 5.1.3.6. Property: jpmv:technologyDeployment — Technology Deployment

| Property | Value |
|---|---|
| URI | `jpmv:technologyDeployment` |
| Label | Technology Deployment |
| Description | A URI identifying a specific deployment of a technology asset used in executing the sub-process. Technology Deployment is scoped to a technology asset and should not be provided without `jpmv:technologyAsset`. |
| Domain | `jpmv:BusinessProcessPerformerRelierRelationship` |
| Range | IRI |
| Min Count | 0 |
| Max Count | unbounded |

#### 5.1.3.7. Property: jpmv:usesThirdPartyEngagement — Uses Third-Party Engagement

| Property | Value |
|---|---|
| URI | `jpmv:usesThirdPartyEngagement` |
| Label | uses third party engagement |
| Description | Associates the performer-relier relationship with one or more third-party outsourcing engagements, including cases where an external supplier performs part of the sub-process and cases where third-party software or technology is used in execution. |
| Domain | `jpmv:BusinessProcessPerformerRelierRelationship` |
| Range | `jpmv:ThirdPartyOutsourcingEngagement` |
| Min Count | 0 |
| Max Count | unbounded |

#### 5.1.4. Class: jpmv:ThirdPartyOutsourcingEngagement — TPO Engagement

| Property | Value |
|---|---|
| URI | `jpmv:ThirdPartyOutsourcingEngagement` |
| Label | TPO Engagement |
| Description | An outsourcing arrangement involving an external supplier, including where a function, activity, or service is performed on behalf of the Firm and where third-party software, platforms, or other technology assets are used to execute the sub-process. TPO engagements are associated with performer-relier relationships where third-party involvement is a material feature of execution. |

#### 5.1.4.1. Property: dcterms:identifier — Engagement Identifier

| Property | Value |
|---|---|
| URI | `dcterms:identifier` |
| Label | Engagement Identifier |
| Description | A unique identifier for the TPO engagement within the Firm's supplier management system. |
| Domain | `jpmv:ThirdPartyOutsourcingEngagement` |
| Range | `xsd:string` |
| Min Count | 1 |
| Max Count | 1 |

#### 5.1.4.2. Property: dcterms:title — Engagement Title

| Property | Value |
|---|---|
| URI | `dcterms:title` |
| Label | Engagement Title |
| Description | A human-readable title for the TPO engagement, typically including the supplier name and the nature of services provided. |
| Domain | `jpmv:ThirdPartyOutsourcingEngagement` |
| Range | `xsd:string` |
| Min Count | 1 |
| Max Count | 1 |

#### 5.1.4.3. Property: dcterms:description — Engagement Description

| Property | Value |
|---|---|
| URI | `dcterms:description` |
| Label | Engagement Description |
| Description | A detailed description of the services, data, and scope covered by the TPO engagement. |
| Domain | `jpmv:ThirdPartyOutsourcingEngagement` |
| Range | `xsd:string` |
| Min Count | 1 |
| Max Count | 1 |

## 6. Specifying a Business Process Framework: Examples

The following examples show related records — a business process and sub-processes — encoded as RDF data in JSON-LD format. These examples use realistic but representative data and illustrate how the key classes and relationships in this framework are used in practice.

For standalone readability, each JSON-LD example repeats the same `@context` block.

The identifiers and references in these examples are illustrative. In production implementations, IRIs should resolve to authoritative enterprise records in source systems (for example, process ownership records, legal-entity references, and organizational structures) and should follow the firm's established identifier governance.

### 6.1. Client Onboarding

Client Onboarding is modeled as a business process owned by the Consumer and Community Banking (CCB) line of business. The process is identified by a unique process identifier.

```json
{
  "@context": {
    "rdf":    "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs":   "http://www.w3.org/2000/01/rdf-schema#",
    "dcterms":"http://purl.org/dc/terms/",
    "jpmv":   "https://vocabulary.jpmorgan/DataPublishing/",
    "bpds":   "https://corp.jpmorgan/bpds/",
    "bpex":   "https://vocabulary.jpmorgan/DataPublishing/examples/",
    "ccb":    "https://vocabulary.jpmorgan/DataPublishing/examples/ccb/",
    "xsd":    "http://www.w3.org/2001/XMLSchema#"
  },
  "@id": "bpex:ClientOnboarding",
  "@type": "jpmv:BusinessProcess",

  "dcterms:title": "Client Onboarding",
  "dcterms:description": "The end-to-end process by which a new client relationship is established with the Firm, including identification, verification, agreement execution, and account set-up.",
  "bpds:processIdentifier": "BP-CCB-001",
  "jpmv:processOwner": { "@id": "bpex:CCB_OnboardingOwner" },
  "jpmv:hasGrounding": { "@id": "https://taxonomy.jpmorgan.com/business-process/ClientLifecycle/Onboarding" },
  "ccb:hasCapabilityGrounding": { "@id": "https://taxonomy.jpmorgan.com/business-process/Capability/ClientAcquisition" }
}
```

In this example, `ccb:hasCapabilityGrounding` is an implementation-defined specialized subproperty of `jpmv:hasGrounding`.

### 6.2. Payments Exception Handling Sub-process (Multiple Performer-Relier Relationships)

Payments Exception Handling is modeled as a sub-process that demonstrates multiple performer-relier relationships for the same sub-process. One relationship represents internal processing by an operations legal entity, and a second relationship represents a shared-services arrangement for a different performer legal entity.

```json
{
  "@context": {
    "rdf":    "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs":   "http://www.w3.org/2000/01/rdf-schema#",
    "dcterms":"http://purl.org/dc/terms/",
    "jpmv":   "https://vocabulary.jpmorgan/DataPublishing/",
    "bpds":   "https://corp.jpmorgan/bpds/",
    "bpex":   "https://vocabulary.jpmorgan/DataPublishing/examples/",
    "xsd":    "http://www.w3.org/2001/XMLSchema#"
  },
  "@id": "bpex:PaymentsExceptionHandling",
  "@type": "jpmv:BusinessProcessSubProcess",
```

*(capture ends here — the remainder of the §6.2 JSON-LD block, §6.3 KYC Verification Sub-process, §7 SHACL Verification and Appendix A (A.1–A.3, Turtle format) were not screenshotted)*

---

# H. Data Authority Metadata Framework
> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5899885596/Data+Authority+Metadata+Framework
> **Screenshots:** data-authority.png, data-authority2.png, data-authority3.png
> **Coverage:** capture starts mid-document at §5; §1–§4 not screenshotted.

## 5. Data Authority Metadata Classes and Associated Properties

Data Authority is defined by instantiating standard classes and associated properties. The definitions closely follow DCAT, and PROV-O standards, with extensions where required. The classes are described in the following sections.

### 5.1 Specifying Data Authority Designation

| jpmv:DataAuthority | |
| --- | --- |
| Definition | The recognition of a Technical System to provide minimum assurances that the Data provided by that Designee is accurate and complete. |
| Subclass of | `dcat:DataSet` |
| Usage Note | Required when a Data Authority designation is specified. |
| Properties | jpmv:designationEntity, jpmv:schemaMetadata, jpmv:designation, jpmv:requestedBy, jpmv:owningApplication, jpmv:decidedAt |
| Example | `:tradeDataAuthority a jpmv:DataAuthority` |

#### 5.1.1 Data Authority Properties

| jpmv:designationEntity | |
| --- | --- |
| Requirement Section | 4.3.A.1 |
| Definition | A conceptual group or entity representing the data subject of the authority designation. Used to identify the business terms or concept (e.g., "transaction", "customer", "account") for which authority is being established. |
| Range | `rdfs:Literal` |
| Usage Note | Required to identify the designated entity. |
| Example | `:tradeDataAuthority jpmv:designationEntity "transaction"` |

| jpmv:schemaMetadata | |
| --- | --- |
| Requirement Section | 4.3.A.2 |
| Definition | Metadata about the schema defining the structure of the designated data. Used to formally define the specific schema elements (properties/fields) or business element terms that receive an authority designation. |
| Range | URI (reference to a schema property or data element) |
| Usage Note | Required to identify the specific element designated. The URI should reference a property defined in the associated schema metadata to enable automated validation and lineage tracking. |
| Example | `:tradeDataSchema a jpmv:SchemaMetadata ; jpmv:targetClass :Trade ; jpmv:property :executionPriceProperty .` |

| jpmv:designation | |
| --- | --- |
| Requirement Section | 4.3.A.3 |
| Definition | Represents the authority designation assigned to a data asset. Multiple designations can be assigned to data entities (e.g., a system can be both SOR and SOC). For data elements, typically only one designation is expected, though multiple designations are technically permitted. |
| Range | Literal (e.g., "ADS", "SOC", "SOR") - Repeatable property |
| Usage Note | Required to specify the type of authority. Multiple values may be specified for an entity that serves different authority roles. |
| Example | `:tradeDataAuthority jpmv: designation "ADS", "SOR" .` |

| jpmv:requestedBy | |
| --- | --- |
| Requirement Section | 4.3.A.4 |
| Definition | Represents the person responsible for the designation. |
| Range | Literal (e.g., E123456) |
| Usage Note | Required to identify the person making the designation. |
| Example | `:tradeDataAuthority jpmv:requestedBy "E123456" .` |

| jpmv:decidedAt | |
| --- | --- |
| Requirement Section | 4.3.A.5 |
| Definition | Represents the date when the designation was made. |
| Range | xsd:date or xsd:dateTime |
| Usage Note | Required to document when the designation occurred. |
| Example | `:tradeDataAuthority jpmv:decidedAt "2026-03-15"^^xsd:date .` |

| jpmv:owningApplication | |
| --- | --- |
| Requirement Section | 4.3.A.6 |
| Definition | The associated Technical System for which the authority designation is linked or mapped to. |
| Range | jpmv:application |
| Usage Note | Required to associate authority designation to a technical system. |
| Example | `:107295 jpmv:owningApplication "MDS Data Discovery (SCUDO)" .` |

## 6. Specifying Data Authority Designation: An Example

The following non-normative example, specified in the turtle serialization format, defines metadata for a business process and related subprocesses:

```turtle
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix jpmv: <https://vocabulary.jpmorgan/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# — Schema Metadata ————————————————————————————

:accountDataSchema a jpmv:SchemaMetadata ;
    jpmv:targetClass :Account ;
    jpmv:property :accountNumberProperty, :accountBalanceProperty .

:accountNumberProperty a rdf:Property ;
    rdfs:label "Account Number" ;
    rdfs:domain :Account ;
    rdfs:range xsd:string .

:accountBalanceProperty a rdf:Property ;
    rdfs:label "Account Balance" ;
    rdfs:domain :Account ;
    rdfs:range xsd:decimal .

# — System Metadata ————————————————————————

:accountApplication a jpmv:owningApplication;
    jpmv:applicationID "123456" ;
    jpmv:applicationName "Banking Data Platform" .
```

*(gap between data-authority2.png and data-authority3.png — remainder of the section 6 turtle example after `jpmv:applicationName "Banking Data Platform"` is clipped, along with any text between the end of the code block and the "7. Defined Terms" heading)*

## 7. Defined Terms

| | |
| --- | --- |
| **Data Elements** | Refer to the Data Tiering Procedure – Firmwide. |
| **Data Entities** | Refer to the Data Tiering Procedure – Firmwide. |
| **Model** | Refer to the Estimations and Model Risk Management Policy – Firmwide. |
| **System of Capture** | Refer to the Data Authority Framework – Firmwide. |
| **System of Record** | Refer to the Data Authority Framework – Firmwide. |
| **Technical System** | Refer to the Data Authority Framework – Firmwide. |
| **Business Term** | Refer to the Glossary Operating Model - Firmwide. |
| **Business Element Term** | Refer to the Glossary Operating Model - Firmwide. |

## 8. Glossary

| Term | Definition |
| --- | --- |
| Authoritative Data Source (ADS) | An Application or Intelligent Solution that can provide a copy of SOR data that can demonstrably be in sync with its SOR up to a particular point in time (e.g., end of day). |
| Accountable Owner | The CDO delegate who is responsible for the registration and maintenance of Authoritative Data Sourcing designations. |
| Corporate Function (CF) | A supporting function that operates across the firm. |
| Data Authority | The recognition of a Technical System to provide minimum assurances that the Data provided by that Designee is accurate and complete. |
| Data Consumer | Entities that use data from designated authoritative sources. |
| Data Elements | Individual properties or characteristics of a Data Entity. |
| Data Entities | Abstract classes used to represent instances, defined by a Data Concept or an entity in a logical data model. |
| Data Lineage | The documentation of how key data is created and controlled as it moves through processes and systems within an organization. |
| Data Owner | The individual or team accountable for the data asset. |
| Data Provider | Entities that create or provide data to designated systems. |
| Designation Rationale | The reasoning or justification for why a particular system or element was designated with a specific authority type. |
| Designation Requestor | The Chief Data Officer or authorized delegate who makes the authority designation |
| Functional Lineage | Describes the contents of data flows for each hop without specifying the physical schemas; provides a conceptual view of Data Lineage using Data Elements. |
| Information Owner | The individual or team who owns the information content of a data asset and is responsible for the accuracy and quality of the data content. |
| Lineage | Captures the data flow by documenting the movement of data in a prescribed direction between registered Technical Systems. |
| Line of Business (LOB) | A major operational division within the firm. |
| System of Capture (SOC) | A Technical System that initially creates, amends, or ingests data that will be made available for consumption by a System of Record. |
| System of Record (SOR) | A Technical System that holds the official version of Data for a defined scope. |
| Technical Lineage | Provides an implementation view of Data Lineage using physical specifications at the level of the physical schema. |
| Technical System | An Application, Model, User Tool, or Intelligent Solution that makes data available to other systems. |
| Technical System Owner | The owner of the Application, Model, User Tool, or Intelligent Solution. |

## 9. References

*(capture ends here — the References section body was not screenshotted)*

---

# I. Taxonomy Framework

> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5772894415/Taxonomy+Framework
> **Screenshots:** taxonomy.png, taxonomy2.png
> **Coverage:** capture begins at §4.1; §1–§4 heading not screenshotted, and the page is clipped mid-§5.1.1.

### 4.1. Open Standard Requirements

To ensure consistency and interoperability, any Taxonomy must be documented as defined in this framework. This standardization facilitates consistent integration with various tools and systems, allowing consumers to seamlessly access and interpret taxonomies.

Individual implementations do not require a manually documented diagram, but must include a machine-readable set of documentation that follows an approved framework or be approved as an exception/extension of an approved framework.

### 4.2. Standard Access Method

Whenever a publisher makes a Taxonomy available, they must implement a mechanism that allows consumers to query the metadata.

To maximize accessibility, the Taxonomy must be accessible with standard encoding, preferably UTF-8, and accessible from a non-proprietary interface, such as a REST API. This approach ensures that consumers can easily retrieve and utilize the Taxonomy, regardless of their technical environment.

### 4.3. Information to be Included in a Taxonomy

```
A) For each concept in a taxonomy, the following attributes are required unless marked:
   a. A preferred label.
   b. The taxonomy (or taxonomies) to which it belongs.
   c. The date(time) when the concept was created.
   d. The creator(s) of the concept.
   e. The unique identifier for the concept.
   f. A definition of the concept.
   g. The date(time) when the concept was last updated (required if applicable).
   h. The actor that modified the concept (required if applicable).
   i. The taxonomy of which it is a top concept (required if applicable).
   j. Any additional labeling properties (optional):
      i. One or more alternative labels that might be useful.
      ii. One or more labels that are hidden to users (e.g., in some UI), but still useful for some purpose.
   k. Any relational properties (optional):
      i. Any concept(s) which are more general "parents" of the current concept in the taxonomy.
      ii. Any concept(s) which are more specific "children" of the current concept in the taxonomy.
      iii. Any concept(s) which are considered "related" to the current concept and which do not fall into any of the previous relations in the taxonomy.
   l. Any mapping properties (optional):
      i. Any concepts in *other* taxonomies which are more general than the current concept.
      ii. Any concepts in *other* taxonomies which are more specific than the current concept.
      iii. Any concepts in *other* taxonomies which are sufficiently similar to the current concept, such that they can be used interchangeably.
      iv. Any concepts in *other* taxonomies which are equivalent to the current concept.
   m. Any additional notations (optional):
      i. Any additional information about the intended meaning or scope of the concept.
      ii. Any administrative information about the concept.
B) For each taxonomy, the following attributes are required unless marked:
   a. The label of the taxonomy.
   b. The date(time) when the taxonomy was created.
   c. The creator(s) of the taxonomy.
   d. The unique identifier for the taxonomy.
   e. A description of the taxonomy.
   f. The date(time) when the taxonomy was last updated (required if applicable).
   g. The actor that modified the taxonomy (required if applicable).
   h. Any concepts in the taxonomy which are considered the top concepts (at least one required per taxonomy).
   i. Any additional labeling properties (optional):
      i. One or more alternative labels that might be useful.
      ii. One or more labels that are hidden to users, but still useful for some purpose.
   j. Any additional notations (optional):
      i. Any additional information about the intended meaning or scope of the taxonomy.
      ii. Any administrative information about the taxonomy.
```

### 4.4. Available Open Frameworks

Within the firm, any taxonomy must adhere to the requirements detailed in this document, the Data Publishing Council-approved Taxonomy Framework.

This Framework adopts a subset of the **Simple Knowledge Organization System (SKOS)** and **Dublin Core Metadata Initiative (DCMI) Metadata Terms**.

**SKOS** is a data model for knowledge organization that produces machine-readable data for thesauri, classification schemes, subject heading schemes, and importantly, taxonomies. It is an OWL (Web Ontology Language) Full ontology, expressed in Resource Description Framework (RDF) triples; any RDF syntax, such as Turtle (TTL), JSON-LD, and RDF/XML.

**DCMI Metadata Terms** is a general purpose metadata vocabulary for describing resources of any kind.

Additional applicable properties can be used provided they do not conflict with the requirements **here**.

## 5. Taxonomy Classes and Associated Properties

The fundamental building blocks of taxonomies consist of the following:

- A particular domain
- The concepts or categories of that domain
- Any relations that exist between those concepts (e.g., parent-child)

A rudidemtnary taxonomy of mammals, for example, could have two "top" concepts, Monotremes and Therians, and two subcategories of Therians, Marsupials and Placental Mammals.

Taxonomy metadata should the creation time and creator(s) of the taxonomy, provenance information, labels, and more. Concept metadata should include information about their history, scope, relationships they have with concepts within the same taxonomy or outside of it, and any different names or labels that might facilitate their discoverability.

Taxonomies are defined by instantiating standard classes and properties, namely `skos:Concept` and `skos:ConceptScheme`. The former represent individual concepts, terms, categories, or classifications within a taxonomy, and the latter represent the taxonomy itself, as a collection of `skos:Concepts`. The required, recommended, and optional properties for those classes are described in the following sections.

### 5.1. Specifying a Concept

The basic elements of a taxonomy--individual concepts, terms, categories, classifications, etc.--are instantiated as `skos:Concepts`, which are defined below.

| `skos:Concept` | |
| --- | --- |
| **Definition** | A unit of thought, such as an idea, meaning, (categories of) objects and or events, both abstract and concrete. |
| **Properties** | `skos:prefLabel, skos:inScheme, dcterms:created, dcterms:creator, dcterms:identifier, skos:definition, dcterms:modified, jpmv:modifiedBy, skos:topConceptOf, skos:altLabel, skos:hiddenLabel, skos:broader, skos:narrower, skos:related, skos:broadMatch, skos:narrowMatch, skos:closeMatch, skos:exactMatch, skos:scopeNote, skos:editorialNote` |

#### 5.1.1. Required Concept Properties

The following are required properties for every `skos:Concept`.

| `skos:prefLabel` | |
| --- | --- |
| **Requirement section** | A) a. |
| **Definition** | Specifies the preferred lexical label for a concept or concept scheme. |
| **Domain** | `skos:Concept` or `skos:ConceptScheme` |
| **Range** | `xsd:string` |
| **Usage note** | For a single concept, there can only be **one** value for this property per language tag. For example, there cannot be two preferred labels bearing the language tag `@en`. There **MUST** be a language tag. |

| `skos:inScheme` | |
| --- | --- |
| **Requirement section** | A) b. |
| **Definition** | Indicates the concept scheme(s) to which the concept belongs. |
| **Domain** | `skos:Concept` |
| **Range** | `skos:ConceptScheme` |
| **Usage note** | Though compatible with the SKOS model, it is recommended that a concept be included in only one concept scheme. |

| `dcterms:created` | |
| --- | --- |
| **Requirement section** | A) c. |
| **Definition** | Date or dateTime of creation of the resource. |

*(clipped at the bottom of taxonomy2.png — the remaining rows of the `dcterms:created` table, e.g. Domain, Range, Usage note, and all subsequent property tables, are not captured)*

---

# J. Taxonomy Information  *(not Confluence — CCB Governance reference-data application)*

> **URL:** https://ccb-governance.gaiacloud.jpmchase.net/reference-data/taxonomies
> **Screenshots:** taxonomy-list.png, taxonomy-list2.png, taxonomy-list3.png

Tabs: **Customer Offering Products** | **Business Domains** | **Business Subdomains**

## Customer Offering Products

*(tab shown in taxonomy-list.png)*

| Customer Offering Product Id | Customer Offering Product Name | Event Physical Name | API Basepath Name | Description | Created Timestamp | Updated Timestamp | Created By | Effective Date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Firm | jpmc | jpmc | This is a grouping that should be used when products span any of the offerings provided by Chase, Wealth Management and Investment Banking. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 2 | CCB/Cross-LOB | ccb | ccb | This is a grouping level that should be used when products fall within 2 or more of the following categories: Auto Lending, Business Banking, Consumer Banking or Student Loan | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 3 | Business Banking | business_banking | business-banking | Business banking products which include Business Checking and Savings, Business Loans, Business Credit Lines and Merchant Services | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 4 | Consumer Banking | consumer_banking | consumer-banking | This is a grouping level which should be used when products fall within 2 or more of the following categories: Deposit Account or Safe Deposits. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 5 | CD/IRA | cd_ira | cd-ira | Time deposit products such as CD/IRAs. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 6 | Deposit Account | deposit_account | deposit-account | Deposit account products, which include: Savings Accounts, Checking Accounts and Money Market Accounts | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 7 | Safe Deposits (Boxes) | safe_deposits | safe-deposits | This product line is limited to Safe Deposit boxes. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 8 | Auto Lending | auto_lending | auto-lending | Auto financing products which include Chase Car Buying services, Auto Loans, Refinancing a car loan, and Auto leasing. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 9 | Student Loan | student_loan | student-loan | Educational financing products which includes Student loans. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 10 | Card | card | card | This is a grouping that should be used when the products supported include two or more of Credit Card, Debit Card, electronic Gift (eGift) Card, and/or Prepaid Card | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 11 | Credit Card | credit_card | credit-card | This is a grouping that should be used when the products supported include two or more of (Consumer) Personal Credit Card, Small Business Card, and/or Commercial Card. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 12 | Small Business Card | business_card | business-card | A small business credit card account is a financial account designed for small businesses, allowing them to borrow funds up to a specified credit limit for business-related expenses. The borrowed amount must be repaid monthly and may incur interest if not paid in full. Accessed via physical cards and electronic methods, these accounts offer features like expense tracking, rewards programs, and fraud protection, helping businesses manage cash flow and build credit history.  This card is issued to individuals for business use and owner is personally liable, both individually and jointly with the Company. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 13 | Personal Credit Card (Consumer) | consumer_card | consumer-card | A consumer credit card account is a personal financial account that allows individuals to borrow funds up to a set credit limit for purchases or cash withdrawals. The borrowed amount must be repaid (usually monthly) and may incur interest if not paid in full. Accessed via physical credit cards and electronic methods, these accounts offer fraud protection, credit history building, and may include additional features like rewards programs, travel insurance, or purchase protection. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 16 | Home Lending | home_lending | home-lending | This is a grouping level which should be used when categorizing products that belong to both Mortgages and Home Equity | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 17 | First Mortgage | first_mortgage | first-mortgage | A legal agreement by which a bank or other creditor lends money at interest in exchange for taking title of the debtor's property, with the condition that the conveyance of title becomes void upon the payment of the debt | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | 2019-09-30 |
| 18 | Home Equity | home_equity | home-equity | A home equity loan is a type of loan in which the borrower uses the equity of his or her home as collateral | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 19 | Investments | investments | investments | Investment services which are offered to consumer banking customers, which include JP Morgan Advisor Services or Online Investing which is also known as "You Invest". This product category includes products such as Insurance, Annuities, 529 Plans and IRAs (SEP, Roth) | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 20 | Merchant Services | merchant_services | merchant-services | Services and products to help merchants securely accept card transactions | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 21 | Auto Save | auto_save | auto-save | A feature which allows an account holder to specify rules for transferring money from one account to another in order to save more. | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 22 | BillPay | bill_pay | bill-pay | A service through which a customer can set up recurring payments, pay bills and transfer money from Chase.com or a mobile device. | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 23 | Car Buying Service | car_buying | car-buying | A service by which Chase customers can search for a car and see what others have paid; locate an in-stock vehicle that matches their search preferences; obtain a savings certificate which can be used with participating dealers. | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 24 | ChasePay | chase_pay | chase-pay | A Chase provided payment application created on a digital device used to interact with the Point of Sale (POS) device as a catalyst for a transaction. | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 25 | Credit Journey | credit_journey | credit-journey | | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 26 | Donor Advised Fund | donor_advised | donor-advised | A donor-advised fund (DAF) is a charitable giving vehicle administered by a public charity created to manage charitable donations on behalf of organizations, families, or individuals. | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | 2019-05-15 |

## Business Domains

*(tab shown in taxonomy-list2.png)*

| Business Domain Id | Business Domain Name | Event Physical Name | API Basepath Name | Description | Owner Name | Created Timestamp | Updated Timestamp | Created By |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Customer Services | customer | customer | Services that expose Customer-specific data for inquiry and/or maintenance. Examples: Account Relationships, Customer Combine, Customer Contact Info Change, Financial Profile, Industry Classification Inquiry, KYC, Language Preference, Privacy Preferences, Shared Secrets Maintenance, Tax ID Maintenance | Schmitter, Todd | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 2 | Sales & Relationship | sales_relationship | sales-relationship | Business Processes related to developing and executing strategies for lead and sales management and retention for prospects and customers, and establishing, retaining, and enriching relationships with partners, third parties and investors. | Medicharla, Ravi | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 3 | Marketing | marketing | marketing | Business Processes related to the activities, operational areas and processes for creating, learning, communicating, delivering and exchanging offers that have value for prospects, customers, clients and partners. | Romanelli, Rick | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 4 | Risk | risk | risk | Identification, assessment and measurement of risk - and the implementation of mechanisms to mitigate those risks. | Abate, Pio | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 5 | Fraud | fraud | fraud | Business Processes supporting the prevention, detection, remediation, and prosecution of criminal activity resulting in identity or monetary theft that victimizes Chase customers including activities related to AML, OFAC/Sanctions | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 6 | Originations | originations | originations | Business Processes related to application and document capture, decisioning, underwriting and funding for debit/credit products, investment products and/or merchant acquiring services. This includes initiation of applications from Chase and third party vendors/affiliates/partners to create new customer accounts KEYWORD: Acquisitions (Cards) | Various | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 7 | Payments | payments | payments | Services that support payment and transfer service capabilities for our customers. This includes setup / enrollment, payment requests, and payment status inquiry. These services span across multiple products / accounts. It is important to note that the activities included in this category do not include the posting of payment transactions to an account, which will be found under Transaction Processing. These services enable mobile, b2b, p2p, etc. and can have all types of payments such as QP, BP, ACH, Wires. Does not include payment posting transactions, with amounts that change balances. | Various | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 8 | Transaction Processing | transactions | transactions | Business Processes related to processing value transactions (i.e. monetary or rewards) created as a result of a customer using Chase credit or debit products or services. It is important to note that all transaction processing activities result in an accounting function (debits and credits) which will impact account balances. | Various | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 9 | Servicing | servicing | servicing | Business Processes related to establishing and fulfilling new accounts and providing individual answers, information, assistance, account and product maintenance and problem resolution related to disputes or escalated complaints. Includes attended and self service channels. | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 10 | Loyalty Management | loyalty_rewards | loyalty | Services that provide inquiry and maintenance capabilities for Reward account activity, including Rewards Summary, Balance, Transaction history (Earns and Redemptions). | Moyer, Gary | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 11 | Customer Fulfillment Services | fulfillment | fulfillment | Business processes related to preparing, packaging and shipping account documents or materials to the account holder. | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 12 | Merchant Acquiring Services | merchant_acquiring_services | acquiring-services | Services that primarily support the Acquiring side of our business and enable our Merchants to integrate with us to use our payment products and process payments through multiple channels | Shuttleworth, Ryan | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 13 | Document Management | document_management | document-management | Managing processes for document acquisition [capture/indexing of inbound documents], document generation of outbound documents, and storage/retrieval document information in support of all business functions. | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 14 | Default Management | default_management | default-management | Business Processes related to the management of non-performing credit products where Chase Customers are unable or unwilling to adhere to the repayment terms of their agreements. For products involving physical assets such as homes or auto, processes may include preservations, liquidations and repossessions. | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 15 | Shared Functions | shared_functions | shared-functions | Business Processes related to establishing and operating core business functions that span across products and channels offering economies of scale for execution across CCB. | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 16 | Finance & Accounting | finance_accounting | finance-accounting | Business Processes related to the financial control of the business including budgeting, forecasting, accounting and settlement, reserve management and financial reporting and analytics. | Abate, Pio | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 17 | Content Management | content_management | content-management | End to end creation, approval and publication of client facing content. | Romanelli, Rick | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 18 | Management and Controls | management_controls | management-controls | Business Processes related to critical support functions that manage and control operations. These are activities which are driven by corporate decisions and functions. | Various | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 19 | Technology Management | technology | technology | Technology management is a comprehensive function that involves the strategic planning, implementation, and oversight of technology systems and processes within an organization. It encompasses various specialized functions, including build management, deployment management, runtime management, design management, and test management. These functions collectively ensure the efficient development, deployment, operation, and maintenance of software applications and infrastructure. The goal of technology management is to align technology initiatives with organizational objectives, optimize resource utilization, enhance system performance, and ensure the delivery of high-quality, reliable technology solutions. | Various | 2025-05-07T17:03:21Z | 2026-05-29T19:58:01Z | |

## Business Subdomains

*(tab shown in taxonomy-list3.png. The table is scrolled: the header row and the upper portion of the first visible row are cut off above the top of the shot. Column labels below are inferred from the Business Domains tab and the visible data.)*

| Business Subdomain Id | Business Subdomain Name | Event Physical Name | API Basepath Name | Description | Business Domain Id | Effective Date | Created Timestamp | Updated Timestamp | Created By | Business Domain Name |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| *(clipped)* | ...Management | *(clipped)* | contracts | ...relationships with those who participate in the sales process. Keywords: Pricing tiers, Profit Sharing, Cost Sharing, Interchange, contract, associations, Software Vendor, Service Vendor, Hardware Vendor, Third Party | *(clipped)* | ...-26 | ...27T18:30:39Z | ...02T21:24:33Z | | ...Relationship |
| 83 | Customer Relationship Management | crm | crm | Strategy used to manage and analyze customer interactions and data throughout the customer lifecycle, with the goal of improving customer service relationships and assisting in customer retention and driving sales growth Keyword: Retain, Rewards Offers, Cross Sell | 2 | 2018-10-10 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Sales & Relationship |
| 84 | Lead Management | lead_management | lead-management | Manage the process of identifying and evaluating prospects to develop qualified leads to whom offers may be sent. Keywords: Pre-Screen Offer | 2 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Sales & Relationship |
| 85 | Manage Partner Relationships | partner_relationship | partner-relationship | Activites required to manage partner relationships, such as on-boarding partners, maintaining the partner's profile information, and enrolling partners in those services necessary to support interactions between the partner and the firm | 2 | 2019-03-01 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Sales & Relationship |
| 86 | Merchant Loyalty | merchant_loyalty | merchant-loyalty | Processes which help merchants reward their customers, increase revenue and create lasting relationships with repeat shoppers. Merchant Loyalty may include loyalty cards, which are similar to a plastic Gift Card and identifies the card holder as a member in a loyalty program. | 2 | 2019-04-23 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Sales & Relationship |
| 87 | Sales Reporting | sales_reporting | sales-reporting | Returns sales and incentive performance data at branch and employee level | 2 | 2019-03-15 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Sales & Relationship |
| 383 | Third Party Contract Management | third_party_contract_management | 3rdparty-contracts | Manage relationship with third party vendors, partners, investors, dealers and merchants. Includes managing issuer and acquirer agreements with payment networks such as Visa, MasterCard, Discover, and American Express. Maintain channel relationships with those who participate in the sales process. Keywords: Pricing tiers, Profit Sharing, Cost Sharing, Interchange, contract, associations, Software Vendor, Service Vendor, Hardware Vendor, Third Party, MAKE AGREEMENTS | 2 | 2018-11-26 | 2025-09-04T17:12:30Z | 2026-05-29T19:58:01Z | | Sales & Relationship |
| 282 | Eligibility Assessment | eligibility_assessment | eligibility-assessment | The right of a customer to hold or enroll in a Product (e.g., Financial Products, Relationship/Experience Products, Financial Service Product, Product Due Diligence - to determine whether a customer is eligible for a particular product or service, Digital Credit Line Exchange) or a benefit/offer thereof | 2 | 2023-05-11 | 2023-05-11T11:25:51Z | 2026-05-29T19:58:01Z | | Sales & Relationship |
| 56 | Acquisitions Marketing | acquisitions_marketing | acquisitions-marketing | Execution of marketing campaigns to acquire new customers Keywords: Rewards Offers, Partner Offers, Rate Sale | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 57 | Advertising / Media / Social Networking | advertising_media_social_networking | advertising-media | Building our brand, reputation and product awareness through communications via a variety of media and channels. | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 58 | Brand Management | brand_management | brand-management | Defining and influencing the perception of the company and its products, developing that perception via a variety of communications methods and reinforcing it in the way products and services are delivered to customers. | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 59 | Campaign Management | campaign_management | campaign-management | Assess the coverage and impact of internal/ customer campaigns and redirect campaign development and execution activity accordingly Keywords: Analytics, Strategy | 3 | | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 60 | Competitive Intelligence | competitive_intelligence | competitive-intelligence | Evaluation of the awareness, performance, and satisfaction of customers with our products/services as compared to the offerings of our competitors. | 3 | 2018-12-10 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 61 | Marketing Strategy | marketing_strategy | marketing-strategy | Determining the markets & customer segments in which to compete, and defining the products/services and methods to be employed to successfully compete in those markets. | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 62 | Offer Management | offer_management | offer-management | Orchestrate the processing of an offer for a new customer or an existing customer. The offer process is defined primarily by the nature of the product or service being considered, but can include actions such as document checks, collateral allocation, credit assessments, underwriting decisions, regulatory and procedural checks, eligibility checks, the use of internal and external specialist services (such as evaluations and legal advice). Management of rewards offer eligibility rules, including opt-in or opt-out would be included here, but not support of the process to enroll. | 3 | | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 63 | Portfolio Marketing | portfolio_marketing | portfolio-marketing | Execution of marketing campaigns to improve account penetration and profitability with our existing customer base Keywords: Proactive Credit Line Increase (PCLI), Access Checks, Balance Transfer, Loan on Line, Slice, Promo, Rewards, Spend and Get | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 64 | Product Management | product_management | product-management | Management of the product portfolio and product life cycle from concept through retirement. | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 243 | Catalog Management | catalog_management | catalog-management | Activities required to allow the bank's clients to manage catalogs of products and services offered to their consumers. Includes enabling clients to create and update their inventory of products and services (i.e. "their catalog") and make the catalog information available to their customers. May include services that allow clients to manage their inventory of catalog items by region, store, etc.. Keywords: SKU-level inventory, Merchant Catalog, Rewards Catalog | 3 | 2023-02-24 | 2023-02-24T09:37:46Z | 2026-05-29T19:58:01Z | | Marketing |
| 342 | Manage Rated Offerings | manage_rated_offerings | manage-rated-offerings | Management of an inventory of offerings such as dining locations or vacation packages, for example, for use in loyalty or marketing activities. For example, the bank may gather curated reviews of restaurants (e.g. from Zagat) and manage the list of restaurants to be included/reviewed by criteria such as price range, type of cuisine, etc. But this can go much further than restaurants to include resorts, sightseeing tours and activities, cruises, hotels, etc. Key words: Infatuation, Zagat, Ratings. | 3 | 2025-03-11 | 2025-03-11T22:18:55Z | 2026-05-29T19:58:01Z | | Marketing |
| 78 | Asset Valuation | asset_valuation | asset-valuation | Provides services for the valuation of loans and the assets used to collateralize them. | 4 | 2018-12-11 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Risk |
| 79 | Credit Risk Decisioning | credit_decision | credit-decision | Execution of credit risk models to determine a customer's credit worthiness. | 4 | 2019-03-08 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Risk |
| 80 | Credit Risk Profile | credit_profile | credit-profile | Provides services for analyzing customer creditworthiness and managing exposure. A credit profile consists of assembled and generated data required to make a credit decision regarding a customer. This includes customer stated income, inferred or derived income, credit bureau data, credit scores, and the products and lines that a customer has and contrasting to what they have used, in order to determine their creditworthiness and to assist in making credit decisions Keywords: Credit Reporting Agency, Credit Bureau (Experian, Equifax, TransUnion, Innovis, FICO), Business Bureau (Dunn & Bradstreet, Equifax, Experian, Paynet) | 4 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Risk |
| 81 | Credit Risk Strategy | credit_risk | credit-risk | Activities to develop, maintain and test a credit risk strategy across a product credit life cycle, based on our appetite for risk. Includes scoring and decision model development, behavior analytics, customer treatment optimization, and a reporting and analysis feedback loop. Keywords: Pricing, Re-pricing, Penalty Pricing, Line Management, Credit Line Decrease (CLD), Credit Line Increase (CLI), Exposure Management, Credit Reporting Agency, Credit Bureau (Experian, Equifax, TransUnion, Innovis, FICO), Business Bureau (Dunn & Bradstreet, Equifax, Experian, Paynet) | 4 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Risk |
| 36 | Authentication | authentication | authentication | Assuring that all account access and transaction activity is restricted to the customer or a duly authorized representative. Includes procedures to facilitate the implementation of identification and authentication controls such as CVV (Card Verification Value), CVV2, CVC (Card Verification Code), chip, RFID, multi-factor authentication (MFA), etc.. For a full breakdown of authentication processes, refer to NIST at: https://gtpc-archer.jpmchase.net/archer/apps/ArcherApp/Home.aspx#record/67/7/208533 Keywords: Chip | 5 | | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Fraud |
| 37 | Fraud Detection | fraud_detection | detection | Update and use measures to detect suspicious/potential fraudulent activity or illegal actions targeting the bank, its customers, its partners, or government agencies. This function includes activities that identify fraud that has happened or is | 5 | | 2020-04-*(clipped)* | 2026-05-*(clipped)* | d607893 | Fraud |

*(the Business Subdomains table continues below the bottom of taxonomy-list3.png — row 37's description and all subsequent rows are not captured)*

---

# K. Ontology Design Recommendations
> **URL:** *(address bar not visible in this screenshot)*
> **Screenshots:** ontologydesign-readme.png
> Pages / DATAPUBSTRATEGY Home / Thought Pieces • 59 views
> Created by Baron, Kit, last updated by Henninger, Scott on Jun 01, 2026 • 2 minute read

This page contains ontology design recommendations agreed upon by the Firmwide Data Publishing Strategy Team's ontologists. These recommendations are discussed in regular syncs, and will be implemented as part of our team's ontology development.

2026/05/29 Scott, Tony, James

1. Consistency in defining ontology files:
   a. Currently the following frameworks define an ontology file and a separate SHACL shapes file:
      i. Data Contracts, Data Mapping, Postal Address, People And Organizations (planned)
   b. The following frameworks define only a shapes file (we may want to add ontology files for some of these):
      i. Data Authority, Data Products, Data Quality, Date and Time, Descriptive Metadata, Knowledge Bases, Provenance, Usage Rights
2. Naming conventions for ontology and SHACL resources:
   a. The shape URIs are the class URIs with "Shapes" appended to it (e.g. the class org:Organization would have a nod shape with the URI orgsh:OrganizationShape)

2026/03/06 Sync

1. Namespaces and prefixes:
   a. `jpmv:  https://vocabulary.jpmorgan/DataPublishing/`
   b. Additional namespaces and prefixes: `https://vocabulary.jpmorgan/DataPublishing/(subspace)` ; prefix based on `(subspace)`
2. Use of properties in Descriptive Metadata framework should be consistent throughout ontologies and frameworks (e.g., use `dcterms:title` over `rdfs:label`)

2026/02/27 Sync

1. Naming of ontology layers (Tony)
   - See https://lucid.app/lucidchart/3d81c499-d350-4190-9190-1d6aeb2726b3/edit?viewport_loc=32%2C153%2C3017%2C1579%2C0_0&invitationId=inv_7dbdf11d-1da9-42ec-b115-2a21af663f90

- Upcoming topics:
  1. Use of **rdfs:label** vs. **dcterms:title**, **rdfs:comment** or **dcterms:description** or **skos:definition**?
  2. Namespaces for framework-specific terms—are they distinct from a central **jpmv** namespace?
  3. Modification/addition process for the firmwide ontology
  4. SHACL Constraints and OWL Restrictions in the ontology

2026/02/18 Sync

1. Term formatting
   a. Capitalization:
      i. IRIs follow **camelCase**: classes begin with a capital letter, and properties begin with a lower case letter, and each word following is capitalized.
         - Acronyms should be entirely capitalized **except** where they begin a property, in which case the whole acronym is lower case (e.g. `_:zipCode`).
      ii. Term labels (**rdfs:label**): first letter capitalized, all other words lower case.
         - **Exception:** proper nouns should be capitalized, and each letter of an acronym, e.g. "Enterprise Party Identifier" and "ZIP code".
   b. Punctuation: definitions of terms (**rdfs:comment**) should end in a period; no punctuation should occur in labels.
   c. Acronyms: if *widely* recognizable within or outside of the firm, they can be used, e.g. "SID" and "PIN". Avoid using obscure or LOB-specific acronyms. If the spelled out version is recognizable, it can be included in the definition; otherwise it can be omitted.
   d. Verb-form properties:
      - Generally, *avoid* use of **has** as in `_:hasName` in favor of simply `_:name`
      - If the verb-form has a more "natural" verb, use it, e.g. `_:dependsOn` or `_:owns`
   e. Versioning: terms should carry information about the version of the ontology of which they are a part. Exact format TBD.
2. Properties in the firmwide ontology: scope and type
   - We should aim for the minimal workable model when adding object *and* datatype properties—think about what kinds of things have starts and ends if `_:startDate` and `_:endDate` are being considered

# L. Connecting a Physical Data Model to an Upper Ontology
> **URL:** confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5648554621/Connecting+a+Physical+Data+Model+to+an+Upper+Ontology
> **Screenshots:** ont-1.png, ont-2.png, ont-3.png, ont-4.png
> Pages / DATAPUBSTRATEGY Home / Thought Pieces • 19 views
> Created by Coates, Anthony (Tony), last updated on Jan 27, 2026 • 23 minute read

## Contents

- 1 Overview
- 2 Terminology
- 3 Use Cases
  - 3.1 Upper Ontology Contains a Property That Exactly Matches a Physical Data Model Property/Column
  - 3.2 Upper Ontology Contains a Property That Is Narrower In Scope/Datatype/Multiplicity Than a Physical Data Model Property/Column
  - 3.3 Upper Ontology Contains a Property That Is Broader In Scope/Datatype/Multiplicity Than a Physical Data Model Property/Column
  - 3.4 Upper Ontology Contains a Property That Overlaps In Scope/Datatype/Multiplicity With a Physical Data Model Property/Column, But Is Not Strictly Broader or Narrower
  - 3.5 Upper Ontology Contains a Class That Exactly Matches a Physical Data Model Class/Table
  - 3.6 Upper Ontology Contains a Class That Is Narrower In Scope or Property Scope/Datatype/Multiplicity Than a Physical Data Model Class/Table
  - 3.7 Upper Ontology Contains a Property That Is Broader In Scope/Datatype/Multiplicity Than a Physical Data Model Property/Column
  - 3.8 Upper Ontology Contains a Class That Overlaps In Scope or Proprety Scope/Datatype/Multiplicity With a Physical Data Model Class/Table, But Is Not Strictly Broader Or Narrower
- 4 Discussion

## 1. Overview

This page discusses an approach to connecting/mapping a physical data model to an upper ontology, such that the upper ontology can be used sensibly to run high-level queries across the physical data.

1. It is assumed here that the upper ontology is a SHACL ontology (which may also contain RDFS and/or OWL).
2. It is assumed that the physical data model has been converted into a SHACL ontology (which may also contain RDFS and/or OWL), and that the SHACL ontology reflects the physical data model as directly as possible. i.e. with a few modelling comprimises as possible.

**For an example of the value of such a physical-to-upper mapping** - many physical data model contain many "name" attributes of different kinds.  If you wanted to query all of the names in the physical data, you would first have to collate all of the physical model attributes that correspond to some kind of name.  Those physical attributes may or may not have the word "name" within the attribute name.

Alternatively, if all of those name attributes are **already mapped** to a single upper ontology "name" attribute, then you can just query the physical data directly for names, knowing that you already know which physical attributes contain a name or not.  You can use a query mapping library that knows how to read the connection/mapping between the physical data model and the upper ontology.

The approach below makes use of `rdfs:subClassOf` and `rdfs:subPropertyOf`.  Note that SHACL recognizes `rdfs:subClassOf`, but not yet `rdfs:subPropertyOf`.

## 2. Terminology

When we say "narrower" or "broader", we mean that:

- Given two classes, or two datatypes, A and B:
  - A is narrower than B is all instances of A are valid instances of B (or trivially mappable to valid instances of B).
  - A is broader than B is all instances of B are valid instances of A (or trivially mappable to valid instances of A).
  - A and B match exactly is all instances of A are valid instances of B (or trivially mappable to valid instances of B), and vice-versa.
    - Exact matches of this sort tend to be a rare occurrence.

"Validity" here can refer to either or both of:

- Technical validity - validation of the format/structure of data.
- Business validity - validation of whether the data makes sense in a particular business context.

## 3. Use Cases

**Note:** for detailed testing results for the use cases, download the HTML output from the matching Jupyter notebook, and open it in your browser.

**The use cases are split into two groups:**

- The first four use cases look at properties only, and how to map between them depending on the scope relationship between a property in the upper ontology and a property/column in the physical data model.
- The second four use cases look at classes, and focus on how to map between classes depending on the scope relationship between a class in the upper ontology and a class/table in the physical data model.
  - As the first four use cases focus on properties only, the second four use cases focus on issues specifically relating to the classes rather than issues related to specific properties of those classes.
- The aim here is simply to deal with either property mapping issues or class mapping issues, but not both at once - just for simplicity.

We will use the following physical data models in these use cases (expand them to see the details).

> Property-only Physical Data Model

> Class+Property Physical Data Model

### 3.1 Upper Ontology Contains a Property That **Exactly** Matches a Physical Data Model Property/Column

For this, we use the property-only physical data model.

"Exactly" here means that the upper ontology properties can be matched 1-to-1 with physical data model properties which have (or can have) exactly the same definition (albeit the names can differ between physical and upper properties).

Each physical data model property is made a subproperty of its matching upper ontology property using `rdfs:subPropertyOf`.  This makes sense because the physical data model properties can be viewed as implementations of the upper ontology properties, albeit in this case exact implementations.

Expand the upper ontology model to view it.

> Upper Ontology Model

You might find it easiest to open this page in a second browser window so that you can see the upper ontology model and the physical data model at the same time - right-click on the link and select "Open link in a new window".

Expand the bridging ontology model to view it.

> Bridging Ontology Model

So for this use case:

1. "firstNameColumn" in the PDM becomes a subproperty of "givenName" in the upper ontology.
2. "lastNameColumn" in the PDM becomes a subproperty of "familyName" in the upper ontology.
3. "ageColumn" in the PDM becomes a subproperty of "age" in the upper ontology.
4. "loyaltyRatingColumn" in the PDM becomes a subproperty of "loyaltyRating" in the upper ontology.

This gives us full traceability between the PDM and the upper ontology.

### 3.2 Upper Ontology Contains a Property That Is **Narrower** In Scope/Datatype/Multiplicity Than a Physical Data Model Property/Column

For this, we use the property-only physical data model.

"Narrower" here means that the upper ontology properties do not have broader datatypes or broader business definitions than their matching physical data model properties - and/or that some physical data model properties do not have a mapping to the upper ontology at all.

Each physical data model property is made a subproperty of its matching upper ontology property, where an upper ontology match exists, using `rdfs:subPropertyOf`.

Expand the upper ontology model to view it.

> Upper Ontology Model

You might find it easiest to open this page in a second browser window so that you can see the upper ontology model and the physical data model at the same time - right-click on the link and select "Open link in a new window".

Expand the bridging ontology model to view it.

> Bridging Ontology Model

So for this use case:

1. "firstNameColumn" in the PDM becomes a subproperty of "givenName" in the upper ontology.
2. "lastNameColumn" in the PDM becomes a subproperty of "familyName" in the upper ontology.
3. "ageColumn" in the PDM **has no mapping** to the upper ontology.
4. upper:extendedLoyaltyRating is added to the upper ontology to accommodate all of the values of the PDM property pdm:loyaltyRatingColumn
5. Both "loyaltyRating" in the upper ontology and "loyaltyRatingColumn" in the PDM becomes subproperties of "extendedloyaltyRating" in the upper ontology.

This gives us the necessary traceability between the PDM and the upper ontology.

### 3.3 Upper Ontology Contains a Property That Is **Broader** In Scope/Datatype/Multiplicity Than a Physical Data Model Property/Column

For this, we use the property-only physical data model.

"Broader" here means that the upper ontology properties do not have narrower datatypes or narrower business definitions than their matching physical data model properties - and/or that some upper ontology properties do not have a mapping to the physical data model at all.

Each physical data model property is made a subproperty of its matching upper ontology property, using `rdfs:subPropertyOf`.

Expand the upper ontology model to view it.

> Upper Ontology Model

You might find it easiest to open this page in a second browser window so that you can see the upper ontology model and the physical data model at the same time - right-click on the link and select "Open link in a new window".

Expand the bridging ontology model to view it.

> Bridging Ontology Model

So for this use case:

1. "firstNameColumn" in the PDM becomes a subproperty of "givenName" in the upper ontology.
2. "lastNameColumn" in the PDM becomes a subproperty of "familyName" in the upper ontology.
3. "ageColumn" in the PDM becomes a subproperty of "age" in the upper ontology.
4. "loyaltyRatingColumn" in the PDM becomes a subproperty of "loyaltyRating" in the upper ontology.
5. "birthYear" in the upper ontology **has no mapping** from the PDM.

This gives us the necessary traceability between the PDM and the upper ontology.

### 3.4 Upper Ontology Contains a Property That **Overlaps** In Scope/Datatype/Multiplicity With a Physical Data Model Property/Column, But Is Not Strictly Broader or Narrower

For this, we use the property-only physical data model.

"Overlapping" here means that the upper ontology properties are in some cases broader and in some cases narrower than the physical data model properties.  Hence this this is like a combination of the "narrower" and "broader" use cases.

Expand the upper ontology model to view it.

> Upper Ontology Model

You might find it easiest to open this page in a second browser window so that you can see the upper ontology model and the physical data model at the same time - right-click on the link and select "Open link in a new window".

Expand the bridging ontology model to view it.

> Bridging Ontology Model

So for this use case:

1. "firstNameColumn" in the PDM becomes a subproperty of "givenName" in the upper ontology.
2. "lastNameColumn" in the PDM becomes a subproperty of "familyName" in the upper ontology.
3. "ageColumn" in the PDM **has no mapping** to the upper ontology.
4. "extendedLoyaltyRating" is added to the upper ontology to accommodate all of the values of the PDM property pdm:loyaltyRatingColumn.
5. Both "loyaltyRating" in the upper ontology and "loyaltyRatingColumn" in the PDM becomes subproperties of "extendedloyaltyRating" in the upper ontology.
6. "birthYear" in the upper ontology **has no mapping** from the PDM.

This gives us the necessary traceability between the PDM and the upper ontology.

### 3.5 Upper Ontology Contains a Class That **Exactly** Matches a Physical Data Model Class/Table

For this, we use the class+property physical data model.

"Exactly" here means that the upper ontology class and the physical data model class/table have (or can have) exactly the same definition - but it also requires them to have exactly the same properties with exactly the same multiplicities (albeit the names can differ between physical and upper properties).  If one of the two classes has more properties, or has broader proerties, it is broader, see the use case below.  If one of the two classes has fewer attributes, or has narrower properties, it is narrower, see the use case below.

Each physical data model class/table is made a subclass of the matching upper ontology class using `rdfs:subClassOf`.  This makes sense because the physical data model class/table can be viewed as an implementation of the upper ontology class, albeit in this case an exact implementation.

Expand the upper ontology model to view it.

> Upper Ontology Model

You might find it easiest to open this page in a second browser window so that you can see the upper ontology model and the physical data model at the same time - right-click on the link and select "Open link in a new window".

*(gap between ont-3.png and ont-4.png — the "Expand the bridging ontology model to view it." line for 3.5 is partially clipped)*

Expand the bridging ontology model to view it.

> Bridging Ontology Model

So for this use case:

1. "PersonRow" in the PDM becomes a subclass of "Person" in the upper ontology.
2. "firstNameColumn" in the PDM becomes a subproperty of "givenName" in the upper ontology.
3. "lastNameColumn" in the PDM becomes a subproperty of "familyName" in the upper ontology.
4. "ageColumn" in the PDM becomes a subproperty of "age" in the upper ontology.
5. "loyaltyRatingColumn" in the PDM becomes a subproperty of "loyaltyRating" in the upper ontology.

This gives us full traceability between the PDM and the upper ontology.

### 3.6 Upper Ontology Contains a Class That Is **Narrower** In Scope or Property Scope/Datatype/Multiplicity Than a Physical Data Model Class/Table

For this, we use the class+property physical data model.  As we have already looked at property narrowing, we only look at class narrowing here.

"Narrower" here means that the upper ontology classes do not have more properties or broader business definitions than their matching physical data model tables/classes.  It also means that some physical data model classes may not have a mapping to the upper ontology at all.

Each physical data model table/class is made a subclass of its matching upper ontology class, where an upper ontology match exists, using `rdfs:subClassOf`.

Expand the upper ontology model to view it.

> Upper Ontology Model

You might find it easiest to open this page in a second browser window so that you can see the upper ontology model and the physical data model at the same time - right-click on the link and select "Open link in a new window".

Expand the bridging ontology model to view it.

> Bridging Ontology Model

So for this use case:

1. "personRow" in the PDM becomes a subclass of "Person" in the upper ontology.
2. "firstNameColumn" in the PDM becomes a subproperty of "givenName" in the upper ontology.
3. "lastNameColumn" in the PDM becomes a subproperty of "familyName" in the upper ontology.
4. "ageColumn" in the PDM **has no mapping** to the upper ontology.
5. "loyaltyRatingColumn" in the PDM **has no mapping** to the upper ontology.

This gives us the necessary traceability between the PDM and the upper ontology.

### 3.7 Upper Ontology Contains a Property That Is **Broader** In Scope/Datatype/Multiplicity Than a Physical Data Model Property/Column

For this, we use the class+property physical data model.  As we have already looked at property broadening, we only look at class broadening here.

"Broader" here means that the physical data model classes do not have more properties or broader business definitions than their upper ontology tables/classes.  It also means that some upper ontology classes may not have a mapping to the physical data model at all.

Each physical data model table/class is made a subclass of its matching upper ontology class, using `rdfs:subClassOf`.

Expand the upper ontology model to view it.

> Upper Ontology Model

You might find it easiest to open this page in a second browser window so that you can see the upper ontology model and the physical data model at the same time - right-click on the link and select "Open link in a new window".

Expand the bridging ontology model to view it.

> Bridging Ontology Model

So for this use case:

1. "AbstractPerson" is added to the upper ontology to accommodate all of the values of the PDM class "PersonRow".
2. "Person" in the upper ontology becomes a subclass of "AbstractPerson" in the upper ontology.
3. "PersonRow" in the PDM becomes a subclass of "AbstractPerson" in the upper ontology.
4. "firstNameColumn" in the PDM becomes a subproperty of "givenName" in the upper ontology.
5. "lastNameColumn" in the PDM becomes a subproperty of "familyName" in the upper ontology.
6. "ageColumn" in the PDM becomes a subproperty of "age" in the upper ontology.
7. "loyaltyRatingColumn" in the PDM becomes a subproperty of "loyaltyRating" in the upper ontology.
8. "birthYear" in the upper ontology has no mapping from the PDM.

This gives us the necessary traceability between the PDM and the upper ontology.

---

# M. Our Vocabulary

> **URL:** confluence.prod.aws.jpmchase.net/confluence/spaces/DATAMESHANALYTICS/pages/4373543268/Our+Vocabulary#OurVocabulary-ADS:
> **Screenshots:** vocab-1.png, vocab-2.png, vocab-3.png, vocab-4.png, conceptual-entity-diagram.png
> **Breadcrumb:** Pages / AWM Data Mesh Strategy / E2E AWM Data Producer Journey — 353 views

## Official Sources:

### SOR :

A single originating source for one or more specific sets of data. An SOR is typically where data is created, first consumed into JPMC, and/or maintained.

- A system an SOR in context of a set of data.   For example, KYC may be the SOR for source of wealth and for the KYC steps taken - but it is NOT the SOR for client address information or client account info (that is Meridian)
- This means that for application which is an SOR there needs to be a description of which data it is an SOR for (domain and subset).

NOTE: Please refer to "SOR Principles" approved by AWM Architecture for more details of the responsibilities on an SOR

### ADS :

Contains a copy of one or more specific sets of data from one or more SOR(s) and is approved for redistribution of these specific sets of data.    Similar to SOR - a system is an ADS for a subset of data / domain.

**Notes:**

- We agreed not to introduce a new concept like "System Of Origin (SoO) as an authoritative source for a piece of the whole but not representative of the whole cohesive set of data like an SoR."    An SoR can be the record for a subset of the domain
- Although the concept of "System of Capture" is valid - it is not relevant in the context of building our Mesh

## Domains

### Data Domain:

A data domain is a logical grouping of data that holds business significance and features federated ownership, utilized by Asset and Wealth Management to enhance data.  A data domain covers a defined context (called a Bounded Context) - within this context terms have a consistent meaning, but outside of this bounded context the terms may have different meanings (example "Client" means something different for a Sales Mgmt domain, vs. "Client" for a "Network" Domain).

### Sub Domain:

A breakdown of the Data Domain for ease of understanding & consumption

### Master List of Domains:

The master list of all domains & sub-domains in DEx - and this should be reflected in Architecture Workbench too.

### Relationship to SOR

- there is a many to many relationship between Domain / subdomain and a given SOR.   Example: Holding / Positions (domain / subdomain):    these positions come from Teminos; Murex; FM3; SCPP; Omni; Olympic
- A given SOR application is an SOR for a domain/ sub-domain or a subset of that data.
- This relationship will be modelled in AWB in time.

## Data Products:

### Data Product Line:

A group of data products rolled up - in our case, it's a sub-LOB.

### Data Product:

A data product is a collection of data sets which are useful to clients of this product - datasets in this product share column names; definition of terms; a common broader model; a permissioning & entitlement model etc. The data product owner is captured at this level.    A Data Product is comprised of data sets.    For all data sets within a data product, there is an expectation of consistency of concepts and field names - and the data model for the data product must indicate how to use the data sets together (interoperability)

A data product can be completely within a domain, or comprised of multiple domains.    In some cases a data product is not part of a data domain.    A data product **should not** be system / SOR linked (e.g. a Meridian or a PANDAS data product) - it should abstract the SOR away from the user.    A data product is not explicitly tied to a particular method of distribution the same data product can be distributed by API, bulk (SQL), file, event etc.
A data product must have a client (and should be built based on client requirements) and must have a Data Product owner who is responsible to continue to evolve and develop this data product over time

A data product can have data from one domain, many domains, or potentially zero domains.    The Data Product is responsible to retain the traceability to the original domains & SORs.

Entitlement: Over time we would like to move to Data Products being the unit of entitlement - however this is currently done at Data Set level.

#### Types of Data Product:

1. **Source Aligned Data Products**: These are data products that are closely aligned with the operational systems and source data / domain. They represent the core data from the domain, often with minimal additional enrichment or calculated fields. The goal is to provide a faithful representation of the source data for downstream consumers.
    a. NOTE: Much of our current bulk mesh is raw data extracted from SoRs, rather than being transformed into a Source Domain aligned data product.
    b. NOTE: At present our bulk mesh only allows for Source Aligned data products (enrichments across domains are frowned upon)
2. **Consumer Aligned Data Products**: These data products are designed with the needs of specific data consumers in mind. They often involve significant transformation and aggregation to meet the specific requirements of analytical or business intelligence applications.
3. **Aggregate Data Products**: These products involve the aggregation of data from multiple sources or domains. They are designed to provide a consolidated view of data, often for reporting or analytical purposes.
4. **Derived Data Products**: Derived data products are created by applying transformations, calculations, or enrichments to existing data products. They are often used to generate insights or support specific analytical models.
    a. NOTE: This is a key need which is not currently supported by our Bulk Mesh / operating model since analytical (non tech) teams cannot currently produce data products

### Data Set:

A data set is an independent set of data (fields with definition; types etc) which can be consumed on its own.    The data set is a unit of data - and should not contain multiple different sets of data (e.g. multiple different files from a vendor)

This can be a subset of all the data contained in the data product, built for consumption. For example the data product could be "Alteryx Telemetry data" which would be comprised of "Run history"; "Error History"; "User logins" etc.    A data set may have multiple ways that it can be consumed (distributions / channels of consumption) - see below.

A data set can appear / participate in zero; one or more data products

A dataset should named in a way which is system / SOR agnostic (see naming conventions)

### Distribution:

A distribution is a way of consuming data via a particular channel or service.    A consumer will connect to a data set via a particular distribution (e.g. via Snowflake, or via GraphQL). Given that a dataset / data product can be distributed by multiple channels - each distribution covers:

- the channel details (e.g. if it's kafka, then what topic; if it's Snowflake then what DB; Schema; Table)
- how to get access / entitlement
- what are the terms of use and the service levels for this distribution (captured in a data contract)

Notes:

- One core tennant of the Mesh paradigm is that a data product can be provided polyglotically (via different channels).    The same data product can / should be available for consumption by API / GraphQL / ProtoBuf / File / SQL etc.
- The data schema for a distribution should be identical to the data product (excluding changes needed by the distribution channel)
    - We agreed that these channel specific changes need to be programmatic & consistent
- The data contract is captured at this level - and is related to the distribution for a data set.
- subscribing to the data is captured at this level
- tracking of usage happens at this level.

### Conceptual Entity Diagram: 🔗

*Figure: Conceptual entity-relationship diagram with entities Domain (name, data domain owner, description), SubDomain (name, sub domain owner, description), SOR (covered portion), Application (SEAL ID, Application Name), Domain / Product, Data Product (name, description, provider, owner, data model), Data Prod / Data Set, Domain / DataSet, DataSet (name, model / schema, owner, producer), Data Distribution (Distribution type <default>), Distribution Type, Data Contract and Consumer; Domain has a one-to-many crow's-foot link down to SubDomain and both Domain and SubDomain link many-to-many to SOR (annotated "Describes the relationship between an SOR and the domain / subdomain", "SOR is AWB"), SOR links one-to-many to Application (annotated "SOR is SEAL (SNow)"), Domain/SubDomain link via the associative box Domain / Product (annotated "Domain can be mapped to domain or sub domain") to Data Product, Data Product links via Data Prod / Data Set to DataSet, SubDomain links via Domain / DataSet to DataSet (both annotated "Dictionary?", with two further "Dictionary?" notes beside Data Product and DataSet), and DataSet links one-to-many to Data Distribution, which links to Distribution Type on the left and to Data Contract and then Consumer on the right.*

## Lineage & Data Glossary Related Terms:

### Agreed:

- **Provenance:** Where did you get the data from, and is it a valid source for this data.
    - Interesting governance question (not definition but governance) – how do we treat data that comes from external parties
        - Is the "source" the first hop inside AWM world or is it from the original supplier.    This also ties to who would be the "Data Provider" for these data sets
        - Is Cross-LOB / cross Legal Entity a similar case?
        - Added to backlog
- **Lineage:** what path did the data take to get to the final outcome
    - Horizontal Lineage: lineage across systems (from system A to system B to system C – generally storage point to storage point with transformation in-between)
    - Vertical Lineage: Lineage within systems (I took in field A and then transformed it as follows)
- **Glossary:** The business definition of terms which can be used to describe, classify and categorize data.    This is different than the logical or physical model.
    - We acknowledge that a glossary term may not be consistent across different areas, so there may need to be a linkage as these diverge by LOB or domain.
        - Example is client holdings, mutual fund holdings, custodial holdings
        - Tom perhaps to add some guiding principles as we build this out.
    - NOTE: open questions about how we manifest glossary in detail

### Not yet fully agreed:

- **Data Dictionary:** The list of fields on a data set with either a definition or a tie to a glossary to define these terms.    This very definitely is based on logical / physical model
- **Taxonomy:** A categorization of knowledge (or data) into a strict tree with one root
- **Ontology:** A categorization of knowledge (or data) into a tree structure where each element can roll up to many roots
- **Etymology:** a description of the origin of words, including how they have changed usage over time
- **Business Glossary Mapping (Possibly call this Data Etymology):** Mapping from business glossary to dictionary to specific field to physical names.    This is sometimes mistakenly called "Vertical Lineage"

## Mesh:

### What is AWM Mesh:

This was the most controversial discussion - and the final agreement is that the Mesh includes all mechanisms of production of data - not just bulk via S3/Snowflake, but also API, Events, Denodo etc.
To avoid confusion the S3/Snowflake piece is called "The Bulk Mesh" and is treated as a subset of the AWM Mesh

### Key Mesh principles:

1. **Treat Data as a Product:** This principle emphasizes the need to treat data with the same level of care and attention as a product. This means focusing on the quality, usability, and discoverability of data, ensuring that it meets the needs of its consumers. Data should be managed with clear ownership, accountability, and a focus on delivering value.
    a. Status: This is still in progress for 2 reasons.    Data Owners are still being put in place; and Data Owners are not yet acting as product owners, working with data users as clients or driving product cabinets or user groups
2. **Domain-Oriented Decentralized Data Ownership and Architecture:** Data mesh advocates for decentralizing data ownership to align with business domains. Each domain is responsible for its own data, allowing for more agile and scalable data management. This approach helps to break down silos and encourages collaboration across different parts of the organization.
    a. Status: This is very nascent - and there's a lot of work to do here.    At present we are landing in the mesh by SOR not by Domain
3. **Self-Serve Data Infrastructure as a Platform:** To empower domains to manage their own data, data mesh promotes the creation of a self-serve data infrastructure. This platform provides the necessary tools and capabilities for domains to build, deploy, and manage their data products independently, reducing the reliance on centralized data teams.
    a. Status:
        i. For the journey from SOR to a publication ready data set - we still have a long way to go (Pipeline in a Box)
        ii. For paving and providing the consumption points - this is well automated in the Bulk Mesh (S3/Snowflake / Starburst)
        iii. For driving towards federated data provision where each team are providing their own data rather than a central data warehouse - this is built into the model.    We still have a lot of work to do, to migrate & decommission many of the old data marts / reservoirs / warehouses
4. **Federated Computational Governance:** This principle focuses on establishing a governance model that balances the need for global standards and policies with the autonomy of individual domains. It involves setting up a federated governance structure that allows for consistent data quality, security, and compliance across the organization while enabling domains to innovate and adapt to their specific needs.
    a. Status:
        i. For Bulk Mesh this is well established via Immuta
        ii. For other distributions - this is still largely nascent

### Open discussions about Mesh:

There is discussion and disagreement about a few elements of the AWM Mesh between internal stakeholders

- Is an application consuming data from Mesh a valid use case (e.g. a trading app getting ref data from Mesh) - or only anlaytics?

*(gap between vocab-3.png and vocab-4.png — the remaining bullets of "Open discussions about Mesh" and any content between them and the "Data Producer:" section)*

### Data Producer:

This is a team or org group that publish to the mesh - either raw data from SOR, or Domain conformed data products.

At present it is not possible for any team other than tech to publish data to the mesh (since this requires tech infra and a SEAL) - this is a blocker for Derived / Analytical Data Products, and is a key reason for significant reinvention of the wheel in the BI / analytics space

## Pipeline Fundamentals:

Although we've not yet agreed every key piece of the pipeline for Mesh - there is broad alignment around a few concepts:

- **Raw data:** Data published from the SOR without conforming to an agreed data model, usually in SOR grammar (and usually without much data cleansing) - would be Raw Data.    This is different than a Data Product.    This should be landed in a Raw / Staging / Bronze layer in the pipeline
- **Conformed:** Data which has been conformed to the target data model and grammar and enumerations would be conformed.    Users must be able to read conformed data without knowing which source system it came from (i.e. no need for source-specific logic for the consumer).    This should be landed in a Conformed / Silver layer
- **Consumable:** Data which has been shaped for the need of the client from the Conformed layer and would be a Data Product.    Users should be able to consume this data directly via multiple channels with one common model.    For a given conformed data set (e.g. Instrument Data) there may be multiple consumable data products (e.g. EU Mortgage Instruments; Corporate Actions Impacted Instruments; Low liquidity instruments) - it is completely OK to have multiple different data products published from a conformed domain-aligned data set.    This data would be in the Consumption / Gold layer

## Decisions Made:

### Caveats....

- with the caveat that we need to road test these with reality – and reserve the right to revisit if reality disagrees
- we are deciding this for AWM

### Decision Log:

1. 2024-12-09: Taxonomy Meeting hosted by Roop
    a. Zhebei will keep us honest with respect to DCAT so that we don't diverge unnecessarily from an industry standard.   Zhebei is our DCAT Rep
    b. We will Eliminate / avoid the term Data Offering
    c. A system is an SOR for some subset of data, not for everything – so the term SOR is not just a label on a system, it's a reflection of the subset of data for which this system is the master record
    d. A data product is a collection of one or more data sets
    e. A given dataset can appear in many different products, so there is a many to many relationship between datasets & data products
2. 2024-12-16: Taxonomy meeting hosted by Roop:
    a. **A data set is a single set of data, with a conceptual / logical model, usable on their own.** If there are different sets of data which together create a usable item, then this would be a data product.
    b. **A dataset can have multiple distributions** - these are the ways to access this data which are congruent and produce the same result (e.g. if I get the data by SQL from snowflake or by API - I should get the same data with the same results). Given the specifics of distribution channels, the physical names may differ.
    c. Translations to **different names for different distributions must NOT be arbitrary** (rule based to drive consistency)
    d. Data Distributions either have all attributes or a subset of the attributes defined on the Data Set. A **distribution can be a subset, not a superset** of fields in the DataSet (i.e. a new field cannot be created at the distribution level).
    e. **A dataset can be standalone or may be part of one or more data products**
    f. **A data product has 1 or more data sets** and data sets can be shared across data products
    g. **A data product can belong to one domain, many domains, or zero domains.** Initially, most data products will come from only 1 domain, but this is not a defined constraint since we see this changing with maturity.    A data product can be comprised of data from multiple different domains - however they need to consult with the domain owners as they construct a data product from the domains.
    h. For **data products from multiple domains** (or derived / aggregated data products) - the **traceabilty back to the original data domain needs to be maintained**.
3. 2025-07-29; E2E Producer Weekly Meeting
    a. Agreed on the definition of Provenance; Lineage & Glossary
    b. **Provenance:** Where did you get the data from, and is it a valid source for this data.
    c. **Lineage:** what path did the data take to get to the final outcome
        - Horizontal Lineage: lineage across systems (from system A to system B to system C – generally storage point to storage point with transformation in-between)
        - Vertical Lineage: Lineage within systems (I took in field A and then transformed it as follows)
    d. **Glossary:** The business definition of terms which can be used to describe, classify and categorize data.    This is different than the logical or physical model.
        - We acknowledge that a glossary term may not be consistent across different areas, so there may need to be a linkage as these diverge by LOB or

**Mesh: (Jan Workshop)**

1. What is the definition of Data Mesh with regard to:
    a. Distribution Channel: is it just "things that are available in bulk via Eddie's team in Snowflake; Data Bricks; Starburst" or does the Mesh include Denodo data; API endpoints (Radix); Kafka queues
        i. We agreed in Jan that Mesh is all channels (including Denodo and Bulk Mesh and API and Events and other)
        ii. We agreed that the S3 / Snowflake channel will be called "Bulk Mesh"
    b. Timing: is it near-real time or just batches

---

# N. Thought Pieces
> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5140788914/Thought+Pieces
> **Screenshots:** thoughts.png

*(single shot — only this portion of the page was captured; the page title and any content above "MCP Server Interfaces" are scrolled out of view. The body is a listing of child-page excerpts.)*

## MCP Server Interfaces

### Contents

### LLM Suite Query

> @deepresearch What would the MCP server interface look like when the MCP's role is to allow querying of a relational database, or querying of an RDF knowledge graph?

## Connecting a Physical Data Model to an Upper Ontology

### Contents

### Overview

This page discusses an approach to connecting/mapping a physical data model to an upper ontology, such that the upper ontology can be used sensibly to run high-level queries across the physical data.

## Managing Ontologies and their Versions for Ontologists, Developers/SMEs and Production Applications

> **Proposed Content - Summary Version**
> - By "ontologies", we mean sets of triples that are an RDFS vocabulary, an OWL ontology or a group of SHACL shapes (with the possibility that multiple of these might be together in the one set of triples, depending on the final deployment strategy)
> - An ontology could be packaged as a file, but it could also be made available as a query against a triple store (or other database).  They may also be packaged in artifact packages in the firm's Artifactory repository - those Artifactory packages capture their dependencies on any other Artifactory packages that they require

## Tricky OWL Constructs in FIBO

### Contents

### Introduction

For the Firmwide CDAO Data Frameworks, we have an RDF focus for the data representation/integration format, and we use SHACL rather than OWL to express the ontology rules.  This is because SHACL has "closed-world" validation semantics, and OWL has "open-world" validation semantics.  What's the different in practice?

## What are Upper Ontologies, and are they valuable?

### Overview (from LLM Suite)

Upper ontologies are high-level ontologies that provide a general framework for organizing knowledge across various domains. They consist of abstract concepts and relationships that are common to multiple domains, serving as a foundation for more specific ontologies. Upper ontologies aim to facilitate interoperability and integration among different domain-specific ontologies by providing a shared vocabulary and structure.

## Use of different RDF serialization formats

Most data formats have a single serialization format - a text file is a text file, a CSV file is a CSV file (albeit with options for line endings & such), an XML file is an XML file.

JSON effectively has two serialization formats now - JSON and YAML.

RDF, however, has a plethora - as this W3C page shows: RdfSyntax - W3C Wiki

## Comparison of potential contributor ontologies/standards for FCDO Data Publishing Standards

### FIBO (Financial Industry Business Ontology)

| Positives | Negatives |
| --- | --- |

*(tab labels only — tab content not visible in this shot)*

Like · 2 people like this

---

# O. Technical Backlog
> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5153183917/Technical+Backlog
> **Screenshots:** technical-backlog.png
> Pages / DATAPUBSTRATEGY Home · 34 views
> Created by Marin, James, last updated by Coates, Anthony (Tony) on Sep 02, 2025 • 2 minute read

| Topic | Notes |
| --- | --- |
| **Versioning of Standards**<br><br>**(Publishing Process)** | <ul><li>What platform do we use? (Github or something else?)</li><li>Stakeholder notification</li><li>How we handle backward-compatible vs. breaking changes</li><li>Documentation vs. machine-readable artifacts</li><li>Tactical vs. strategic plan?</li></ul> |
| **Standard Tooling Suite** | <ul><li>Want to establish a standard suite of tools for consistency in authoring, testing, and deployment</li><li>Applies to internal tooling used by the team as well as recommended tooling to be used by stakeholders for usage/implementation of our standards</li><li>Might need to split this topic up depending on type of tooling</li></ul> |
| **AI Integration** | <ul><li>How do we help our stakeholders implement our standards?</li><li>Simple scenario: A team wants to create ttl from their data. How can we enable that?</li><li>How do users navigate the graph of our standards and make sense of them without having to use SPARQL?</li></ul> |
| **Materialization/Realization/Productization** | <ul><li>Where do our graphs live (i.e., what http endpoint do I hit?)</li><li>Where do our written standards live?</li><li>What services do we make available (SPARQL endpoint, MCP server, other APIs?)</li></ul> |
| **Syntactical Conventions** | <ul><li>Namespaces (creating new internal namespaces)</li><li>Named graphs</li><li>Classes</li><li>Properties (verb phrases? target class in lower-case? something else?)</li></ul> |
| **Documentation** | <ul><li>What platform does our technical documentation live on?</li><li>Includes standards and guidance, as well as technical artifacts (such as ttl files, notebooks, etc.)</li><li>Many factors to consider including, usability (for both authors and consumers), availability within JPMorgan, and features</li></ul> |
| **Third Party Standards Integration** | <ul><li>When to reference 3rd Party Standards</li><li>How to reference</li><li>Articulable method for deciding which standards to use</li><li>How do we integrate into our graph (when we have it) and resolve URIs?</li><li>To quote @Tony :</li></ul><br>There probably needs to be something about use of 3<sup>rd</sup> party standards – we seem to equivocate between the ideas of "using 3<sup>rd</sup> party standards", "building things appropriate to JPMC using the components of 3<sup>rd</sup> party standards" and just "building things appropriate to JPMC", and we might need something to cover which of these approaches we use, and when/why we would choose one over another. |

## Actionable Topics

| Backlog Topic | Actionable Topic | Notes | Status | Owner |
| --- | --- | --- | --- | --- |
| Versioning of Standards | Use GitHub, separate repos | <ul><li>Use GitHub for publishing standards (Markdown, SHACL, etc.)</li><li>Create a separate repo for development work - standards, tools, etc. - without need for FCDO sign-off on main</li><li>Have a mechanical process for pushing changes from dev repo to a branch of the standard publishing repo</li></ul> | Proposed (Tony) | |
| Stakeholder notification | Capture producers/consumers of each standard in CDAO Catalog | <ul><li>Capture all producers/consumers of each standard in the CDAO Catalog, so that we always know who are the stakeholders who need notifying of impending versions, etc.</li></ul> | Proposed (Tony) | |
| How we handle backward-compatible vs. breaking changes | Versioning rules for FCDO standards | <ul><li>Versioning: M.N.P where M is major version, N is minor version, P is patch version</li><li>When M is 0, any new version can be backwards incompatible</li><li>When M >= 1, backwards-incompatible changes require an increment of M **unless** all stakeholders approve that the change will have no knock-on impact for them</li><li>Minor version changes must be backwards-compatible (except as noted above)</li><li>Patch versions are used to correct backwards-compatibility issues in a previous minor or patch release, so version M.N.P must be backwards compatible with version</li></ul> | Proposed (Tony) | |

*(page is clipped at the bottom of the screenshot mid-way through the last bullet of the final row)*

---

# P. Discussion About The Possible Form of AI & Agent Native Data Benchmarks
> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5938531925/Discussion+About+The+Possible+Form+of+AI+Agent+Native+Data+Benchmarks
> **Screenshots:** readme-agent-graph-rag.png, readme-agent-graph-rag2.png
> Pages / DATAPUBSTRATEGY Home / Thought Pieces · 11 views
> Created by Coates, Anthony (Tony) on Apr 24, 2026 • 5 minute read

**For what things could/would we create benchmarks, within the scope of AI & Agent Native Data?**
**What would be the nature of those benchmarks?**
**How would we make them widely applicable across applications?**

FCDO OSI POC recommends having the LLM rate its confidence in the quality of its text-to-SQL transformations, and to enrich the metadata supplied to the LLM until the confidence rate is sufficiently high (e.g. 80%+, 90%+).

What isn't explicitly recommended in that document, but would probably be good practice, is to cache past queries and the SQL created from them, so that where users ask the same query regularly, they get the same consistent response.  We already have problems with some AI apps in the firm where AI was used to implement what was essentially a rules-based problem, and users are frustrated that they aren't getting consistent responses to common queries, so it's important to avoid the natural variability of AI responses when the same question is asked over and over.

The FCDO OSI POC was done using a small amount of synthetic data; ideally a broadly deployed AI & Agent Native Data benchmark for natural-language-to-query-language conversion would be done on the actual production data for each application, so that any intricacies of the particular data set are taken into account as part of the benchmarking.  If the benchmarking was done against only a subset of the production data, then care would need to be taken that the subset was self-consistent and captured all of the important relationships between tables or between columns within the same table (and similarly for non-relational data).

Data and data models change over time, the queries that users ask change over time as business priorities change, and our benchmark process will likely also be updated periodically, so the benchmarks discussed here would have to be **run continuously**, and reported on regularly, to catch any negative drift in the benchmark scores over time.

The FCDO OSI POC was careful about separating different AI model instances so that they operated independently when they should, but also careful to make sure that each AI model instance has access to the full history of what prompts it has processed and what answers it had provided or what artifact changes it had made in response.  This is highly important because the AI model instances regularly check back over that interaction history to see what was previously done, in order that future responses are (relatively) consistent with past responses.

In particular in the FCDO OSI POC, the text-to-SQL conversion was done by a single AI model instance, mean that the AI was aware of all inputs into the text-to-SQL process, and had the full information required to provide a confidence rate percentage for each conversion.  **Importantly, the AI could also be asked** for information on why the confidence rate for a particular text-to-SQL conversion was low, and on what improvements to the metadata would be required to lift that confidence rate.  It's worth keeping in mind that while we can't delve into the innards of the AIs knowledge directly, because it's stored in the form of statistical weightings, **we can ask the AI** to translate that knowledge into descriptions of what it has done, why it did things in the way it did, and what things limited its ability to provide the best quality result.  Ideally this should be a regular part of how we work with AI model instances, especially given the unavoidable variance in responses between different AI model instances.

As a counter-example, in CCB's AI-based "FAST" Graph-RAG implementation, the text-to-SQL isn't a single AI step as in the FCDO OSI POC, but instead spread across a series of steps, which for this discussion can be summarized as:

1. Generating a vector embedding for tables and columns, based their names and descriptions
2. Choose tables and columns for the query, based on similarity results between the vectorized version of the natural-language query and the table/column vectorizations
3. Split the natural-language query up into sub-queries, convert each sub-query to SQL, and then compose the final SQL query.

Here, to get a confidence rating for conversion of the natural language query to SQL, it might not be enough to just ask the LLM in step #3 for its confidence **given the subset of tables/columns that it has been allowed to use, after step #2.**  Instead, the proximity results from step #2 would might need to be provided, depending on how large the vector mismatches are allowed to be in step #2.

The point here isn't to single out the FAST project in any way, but rather to point out that where there are multiple steps in the process, it may be necessary to calculate confidences cumulatively in order to get the most representative final confidence values.

Another key question for any benchmark of text-to-SQL functionality is how you decide whether the set of results returned by the generated SQL query is exactly the right set of results (not too many, not too few, not the wrong data) for the original natural language query.

In the FCDO OSI POC report, there is an appendix with a review, compiled by LLM Suite, on what is known about risks in converting natural language queries to SQL.  For example, read the section "The Distribution Shift Challenge: Training vs. Real-World Usage".  Over time, the kinds of queries that users are asking can increasingly deviate from the kinds of queries that we used to train/test to text-to-SQL converter, and that can lead to significant degradations in the quality of the generated SQL.

The main testing strategy that we have encountered so far in the firm is:

- Pick some common SQL queries, write natural-language (NL) equivalents for them, and then test that the SQL query results and the NL query results are the same
  - A variant of this is to use AI to create the NL queries, rather than having an SME do it

The advantage of this strategy is that the results of well-known queries are themselves well-known.  The disadvantage is that there is that users are likely to ask some queries that are unlike the queries that were tested, and the results returned to the user may be from a query that is untested and not of sufficient correctness.

For the FCDO OSI POC, many of the test queries were constructed to flush out cases where the AI would have problems, and this was done by asking the AI which tables/columns had ambiguous naming and/or definitions.  Queries constructed from such ambiguous names produced low confidence values for the SQL.  The AI was used to create possible test queries, and then unworkable ones were culled from the query set manually, until there were sufficient for testing.

So there are ways to construct test queries, beyond just taking the most commonly executed queries - but note that having a good static set of test queries doesn't replace the need for continuous benchmark monitoring, as discussed above.

These are things that should feed in to answers to the questions from the start of this discussion.

Like · Be the first to like this

Write a comment...

---

# Q. Discussions on AI Agents for Managing Data Access
> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/6206552010/Discussions+on+AI+Agents+for+Managing+Data+Access
> **Screenshots:** readme-agent-graph-rag3.png
> Pages / DATAPUBSTRATEGY Home / Thought Pieces · 8 views
> Created by Coates, Anthony (Tony), last updated on Jul 24, 2026 • 3 minute read

This page is for capturing discussions within FCDO and with our partner groups within JPMC, on the topic of how best to manage AI Agents whose role is to act as an SME for one or more data sets, providing functionality like converting natural language queries to structured queries (SQL, etc.).

## Contents

- 1 With Cheryl Kimathi from CIB Information Architecture (CIB CDO)

## With Cheryl Kimathi from CIB Information Architecture (CIB CDO)

Based on discussions from 24th July 2026.

- When you are first working out what metadata you can provide to an AI Agent that is handling data access to one or more data sets, the best bang for buck seems to come from column-level documentation (aka property-level or attribute-level documentation)
  - Class/Entity/Table documentation is also valuable, but what seems to help the AI Agent the most is providing documentation that clearly distinguishes between things at the lowest level of granularity.
  - Mapping undocumented or poorly documents physical database columns to a well-documented logical model has also been found to work - although it won't help the AI Agent distinguish the differences between multiple physical columns that are all mapped to the one logical column (if those columns aren't just identical copies of the data).
- Databricks supports "benchmark questions", where the SQL for particular natural language questions is persistently cached, and users (including other AI Agents) are directed first to benchmark questions that are similar to their own questions, before the AI tries to convert their actual question into SQL.  This is a great idea, because if the AI Agent for the data set regenerates the SQL from scratch every time, it will likely provide different SQL on different days for the same natural language question, which is confusing for users.  Also, "benchmark questions" are approved as such by human SMEs, which increases human confidence in the results provided by the AI Agent.
  - *(Idea) Where a question is similar to a benchmark question, but not the same, it would be good to get the AI to structure the new SQL to be as close as possible to the benchmark SQL, from a text-diff perspective, so that human users see that similar questions lead to similar SQL, in the cases where they know this should be the case.*
- Typically natural language to query language conversions are tested using a small number of benchmark questions, but real-world natural language questions from human and/or AI users can easily require parts of the data set(s), and relationships thereof, that are not well tested, or not tested at all, by the benchmark questions.
  - A good practice is to ask the AI to rate its percentage confidence in every new conversion that it performs, and warn the user if their conversion comes with a low confidence level.
    - All questions, queries and confidence levels should be logged so that the AI Agents performance is converting questions to queries can be monitored and improved over time.
  - Additional benchmark questions should be added over time as required.
  - The history of low confidence conversions should be analyzed periodically to determine what new metadata would allow the AI to do a high confidence conversion for those natural language questions that produced only a low confidence conversion.
  - See also: Risks in Converting Natural Language Queries to SQL, (from LLM Suite) - see the section 6 appendix
- In future, the vast majority of queries to our data sets are likely to come from other AI agents, not from human users, so we have to assume that the queries will often come from AI agents that don't know the data set, don't know the business, and don't know "what good looks like".
  - The AI agent that handles the queries to a data set needs wide-ranging information about the data set and about the business area, so it can advise other AI agents on follow-up questions about how to correctly interpret the results of a query.
  - It's a good practice to test the ability of an AI agents to handle follow-up questions as part of the release qualification of the AI Agent.
- We have the option to use the AI agents themselves to filter incoming questions so that only questions that are within an approved scope are answered. Over time, as we gain more confidence in the AI results, we can expand the scope. This would help avoid scenarios where an AI agent, tested primarily against only benchmark questions, is bombarded in production by thousands of questions from other AI agents for which only low confidence query conversions are possible.
- AI agents that handle data sets should provide MCP server tools that give structured access to all of the metadata that can be structured sensibly, e.g. data models and data validation rules, data examples, query examples, usage rules, data record creation helpers, etc.

Like · Be the first to like this

Write a comment...

Powered by Atlassian Confluence 9.2.13 (i-097719c99e569dc00: 24e2ebb3) · Report a bug · Atlassian News

---

# R. Application  *(not Confluence — OneNote-style note page)*
> **URL:** *(no address bar visible — this screenshot is not a Confluence page)*
> **Screenshots:** application-datasources.png
> Tuesday, March 25, 2025    8:41 AM

*(single shot — only this portion of the page was captured; the page consists of two embedded diagrams side by side and is clipped at the bottom of the right-hand diagram)*

*Figure: Left-hand crow's-foot ER diagram, colour-coded by a "Data Sources" legend (pink = ServiceNow, blue = SEAL, yellow = Verum). Boxes: "Business Application (cmdb_ci_business_app)" [blue], "Application Service (cmdb_ci_service_discovered)" [pink], "TOM Role (x_jpmc_cmdb_tom_main)" [pink], "TOM Main (x_jpmc_cmdb_tom_main)" [pink], "Group (sys_user_group)" [pink], "Technical Service (cmdb_ci_service)" [pink], "Technical Service Offering (service_offering)" [pink], "Configuration Item (cmdb_ci)" [yellow], "Group Member (sys_user_group_member)" [pink]; a bracket over Application Service is annotated "Environment Specific Instance of SEAL Logical Deployment"; unlabelled crow's-foot relationships connect Business Application–Application Service, Application Service–Technical Service, Technical Service–Technical Service Offering, Configuration Item–Technical Service Offering, Application Service/Technical Service Offering–TOM Main, TOM Role–TOM Main, TOM Main–Group and Group–Group Member.*

*Figure: Right-hand diagram split into two colour-banded swimlanes, "IT Services Management" (green) and "Architecture Management" (blue), with green boxes "Service Portfolio", "Service", "Service Offering", "Application Service" on the left and "Business Process", "Business Capability", "Business Application" on the right; arrows labelled "Provides" (Service Portfolio→Service, Service→Service Offering, Service→Application Service), "depends on" (Service Portfolio→Business Process, Service→Application Service, Service Offering→Application Service, Application Service→ box clipped at bottom), "used by" (Service→Application Service), "manages" (Service Offering→ box clipped at bottom), "uses"/"used by" (Business Process↔Business Capability), "members"/"members of" (Business Capability↔Business Application) and "instantiates" (Business Application→Application Service).*

---

# S. About the model  *(not Confluence — Neo4j SDLC model documentation)*
> **URL:** *(no address bar visible in this screenshot)*
> **Screenshots:** neo4j-sdlc.png

*(single shot — only this portion of the page was captured)*

## About the model

*Figure: Radial graph diagram with a red central node "Software Development" and six yellow nodes — "Human", "Knowledge", "Process", "Web", "Technical" and "Testing" — each connected to the centre by an arrow labelled "PART_OF" pointing inwards to Software Development.*

In this model, the following categories have been adopted to group closely-related labels:

| Node Domain | Labels included |
| --- | --- |
| Human | :Audience, :Group, :Organization, :Person, :Role |
| Process | :CheckIn, :Defect, :Feature, :Iteration, :Release, :Requirement, :Task, :TestCase, :TestSuite, :UserProfile, :UserStory |
| Technical | :AppLayer, :CodeProject, :CodeSolution, :Component, :CssFile, :Database, :DbFunction, :DbTable, :DbSchema, :DbView, :Environment, :File, :JsFile, :LocalizationKey, :Location, :MvcController, :MvcView, :Platform, :Permission, :Service, :Server |
| Knowledge | :Audience, :Document, :Term, :Publication, :Skill |
| Testing | :Defect, :Environment, :Feature, :Requirement, :TestCase, :TestSuite, :UserProfile, :UserStory |
| Web | :CssFile, :JsFile, :MvcController, :MvcView |

---

# T. SCRAPE WEBPAGE CONTENT CHECK — ServiceNow CMDB class analysis  *(not Confluence — AI chat/tool output panel)*
> **URL:** *(no address bar visible — dark-mode AI chat/tool output panel labelled "SCRAPE WEBPAGE CONTENT CHECK")*
> **Screenshots:** snow-cmdb.png

*(single shot — only this portion of the page was captured; the first line is clipped at the top and the closing paragraph is clipped at the bottom)*

Now I have the full map. The family splits cleanly into technical "IT" trees (the iterating mass) and a small **business/logical layer**. Here's the cut.

## How the 1,235 split

**IT_Services** — technical trees (iterations you don't need) — collapsed to counts:

| Branch | # | Branch | # |
| --- | --- | --- | --- |
| Application (`cmdb_ci_appl`) | 286 | Storage / SAN (all `_storage_*`, `_san*`) | ~60 |
| Hardware (`cmdb_ci_hardware`) | 269 | Network / IP / DNS / LB / Firewall | ~50 |
| Virtual Machine Object (`cmdb_ci_vm_object`) | 171 | Facility / Rack / UPS / PDU / CRAC | ~25 |
| Endpoint (`cmdb_ci_endpoint`) | 141 | Cloud / VPC / VNET / GCP / OSLV / Container | ~25 |
| Kubernetes (`cmdb_ci_kubernetes_component`) | 28 | Database Catalog (`cmdb_ci_db_catalog`) | 13 |
| Cluster (+ node/resource) | ~40 | CloudFoundry (`cmdb_ci_pcf_component`) | 12 |

...plus your three kept examples: `cmdb_ci_datacenter` (Data Center), `cmdb_ci_database` (Database), and the VM/server instance class under `cmdb_ci_vm_object` (VSI).

## non-IT_SERVICE — the business / logical / management classes

These are the top-level classes that are **not** IT infrastructure (≈22 roots; a few carry small subtrees):

| Label | Table | Note |
| --- | --- | --- |
| Business Application | `cmdb_ci_business_app` | |
| Business Capability | `cmdb_ci_business_capability` | |
| Business Process | `cmdb_ci_business_process` | +4 in subtree |
| Business Process Activity | `cmdb_ci_business_process_activity` | |
| Service | `cmdb_ci_service` | +16 (business/app/technical services) — boundary call |
| Information Object | `cmdb_ci_information_object` | |
| API | `cmdb_ci_api` | +API Component (4), Product Bundle, Consumer Subscription |
| Custom Application | `cmdb_ci_custom_application` | + `m2m_custom_application_ci` |
| Batch Job | `cmdb_ci_batch_job` | app/business-relevant |
| Unique Certificate | `cmdb_ci_certificate` | security/logical |
| Environment | `cmdb_ci_environment` | |
| Group | `cmdb_ci_group` | +1 |
| Outage | `cmdb_ci_outage` | operational record |
| Logical Composite | `cmdb_ci_logical_composite` | |
| Model Entry | `cmdb_ci_model_entry` | CMDB meta |
| End Of Life Ledger | `cmdb_ci_end_of_life_ledger` | CMDB meta |
| State Management Task→CIs | `cmdb_ci_state_management_task_to_ci` | CMDB meta |
| SDLC Component | `cmdb_ci_sdlc_component` | |
| Workload Config Provider | `cmdb_ci_workload_config_provider` | |

The boundary I used: "IT_Service" = anything under the technical infra/app/endpoint/VM/storage/network/cloud/facility trees; "non_IT_SERVICE" = the

*(capture ends here — the closing paragraph is clipped)*

---

# U. People and Organizations Framework

> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/6030480492/People+and+Organizations+Framework (unchanged across all 11 screenshots)
> **Breadcrumb:** Pages / … / Drafts and Upcoming Frameworks — 236 views
> **Screenshots:** people-org-1.png … people-org-11.png

## 1. Summary

The People and Organizations Framework establishes a unified, standards-based approach for representing the firm's workforce, its lines of business, and the diverse organizational groups that collectively form JPMorganChase. By defining core concepts such as Person, Organization, Agent, Party, and Role, the framework provides a consistent vocabulary and ontology for describing individuals, their affiliations, and the structural relationships that underpin the enterprise. It enables the modeling of roles, reporting hierarchies, business units, cross-functional affiliations, and memberships, offering a comprehensive lens through which to understand how people interact with and operate within the broader organizational structure of JPMorganChase.

A central purpose of this framework is to make people and organization data AI-ready—enabling seamless sharing, discovery, and intelligent use of data across Lines of Business (LOBs) and Corporate Functions (CFs) without requiring changes to how data is currently stored, structured, or managed. Data remains in its current form and location - the objective here is providing the data structured for data exchange. The framework does not prescribe or impose transformations on underlying data stores. Instead, it provides the scaffolding — a framework — to represent data as it exists today and to capture the entities and relationships capable of sharing data about people and organizations.

This framework is integral to the broader suite of frameworks published by the Agent Ready Data group, serving as a foundational component that underpins classes and properties—such as creator, owner, and modified by—defined by Descriptive Metadata, Data Products, Knowledge Bases, and Data Mapping Frameworks. By providing standardized definitions and relationships for people and organizations, it ensures consistency and interoperability across these frameworks, enabling seamless integration and data exchange. As a result, applications and AI agents can leverage a unified approach to identity, affiliation, and organizational structure, supporting advanced analytics, automation, and intelligent decision-making throughout the firm.

The framework is built on W3C Semantic Web technologies, leveraging established standards including The Organization Ontology, Schema.org, Friend of a Friend (FOAF), vCard, OWL, Dublin Core Terms and SKOS. This standards-based design ensures that definitions are interoperable, queryable, and readily consumable by both existing data-governance tooling and next-generation AI systems. The framework chooses RDF as the implementation language to be compatible with other AI and Agent Native Data Frameworks, to draw on industry standards, and for its native ability to model data schemas and their relationships.

## 2. Changes from Previous Version

| Version | Date | Description of changes |
| --- | --- | --- |
| 0.1.0 | 2026-05-26 | Initial version |
| 0.1.1 | 2026-07-10 | Modified model per collaboration with HR |

## 3. People and Organizations Framework

This Framework models the workforce and organizational structure of the firm as a small set of interconnected components, keeping who a person is separate from how they are engaged and where they sit in the organization. The people and organization entities modeled by this framework are specifically designed to interoperate with other data publishing frameworks, enabling a detailed and consistent representation of these entities across diverse systems. This separation allows a single person to hold more than one engagement over time, allows positions to persist independently of the individuals who fill them, and allows organizational structure to be described consistently regardless of the underlying source systems. The key components are:

- **Person** — an individual human being, described by identifying attributes such as given and family names (`schema:Person`).
- **Employment** — a person's employment relationship with an organization, capturing their worker classification (employee or contingent worker), and employer of record. A person may hold one or more Employments over time (`jpmv:Employment`).
- **Position** — a position within an organization that exists independently of the person filling it, and that can be linked into a reporting chain of Positions. An Employment is tied to the Position that the person fulfills (`jpmv:Position`).
- **Organization** — the entity a person is employed by, which may be a formal, legally recognized organization such as the firm itself (`org:Organization`, `org:FormalOrganization`).
- **Business Unit hierarchy** — the departments, lines of business, and corporate functions that decompose an organization into a nested structure, expressed through sub-organization and unit relationships (`org:BusinessUnit`).

Together these components describe how a person is employed by an organization, engaged through an employment, fulfills a position within a reporting structure, and is situated within a hierarchy of organizational units.

### 3.1. Key Definitions for People and Organizations Framework

| Term | Definition |
| --- | --- |
| Person | An individual human being, living or deceased, who can be uniquely identified and distinguished from other individuals and from organizations. |
| Agent | Any entity — whether a person, an organization, or a software artifact — capable of acting, making decisions, or producing effects within a given context. |
| Party | Individuals or organizations that assume a specific role or position within a relationship, transaction, agreement, or event. |
| Role | A function, capacity, or position in which a person or organization acts within a particular context or relationship. |
| Worker | The role a person holds when engaged by an organization to perform work, whether as an employee or a contingent worker (such as a contractor). |
| Organization | A collection of people organized together into a community or other social, commercial or political structure. |
| Business Unit | An organizational unit within the firm's hierarchy, such as a Line of Business (LOB) or Corporate Function (CF), that can be further decomposed into nested units. |
| Position | A position within an organization that exists independently of the person filling it and can be linked into a reporting chain of positions. |

*(gap between people-org-1.png and people-org-2.png — the Key Definitions table may continue with additional rows below "Position" that are cut off at the bottom of shot 1 and scrolled past at the top of shot 2)*

### 3.2. Relationship to Other Data Publishing Frameworks

People and organizations operates alongside other data-publishing frameworks. The FCDO Data Publishing Frameworks, including Descriptive Metadata, Data Products, Knowledge Bases, Data Contracts, and Data Mapping Frameworks do not generally define their own Person or Organization classes; instead, they reference people and organizations, as the values of agent-bearing properties such as creator, publisher, owner, modifier, contact, assigner, and assignee. The ranges of these properties are drawn from three different external vocabularies — `foaf:Agent`, `prov:Agent`, and `odrl:Party` — and the only other framework that defines its own Party, Organization, or Person classes is the Party Identifier Framework, which does so for the narrower purpose of identification. The result is a consistent reliance on the *idea* of an Agent across the frameworks but no shared vocabulary for describing one, which is the gap this Framework is intended to fill.

See Appendix A for a full analysis of how this framework works with the other FCDO Data Publishing Frameworks.

## 4. Key Requirements for People and Organizations

It is essential for metadata about people and organizations to be clear and accessible, especially when the consumers of the data are not explicitly known. Any People and Organizations data produced, including metadata hosted in shared data catalogs, must adhere to the requirements defined in this Framework.

### 4.1. Open Standard Requirements

Applications that hold People and Organizations data must make that data available in an open data format - either a JPMorgan Chase open data format or a widely adopted third-party open data format. Rich metadata describing the People and Organizations data must also be made available in an open data format, and must be directly usable by AI Agents, Subject Matter Experts (SMEs), Data Scientists, and Software Developers without requiring specialist tools to decode it.

Where People and Organizations data or its metadata is accessible only through a vendor-proprietary format, this creates an interoperability risk. It can limit the ability of AI tools and human practitioners to access and use the data in a consistent way, and should be addressed in line with applicable governance and prioritization.

To support AI Agents uniformly across diverse applications, the recommended practice is for all People and Organizations data models to include a mapping to this Framework — specifically, to the RDFS/SHACL schema and the concept schemes defined in Section 5. A consistent mapping enables AI Agents to interpret and operate on People and Organizations data regardless of the underlying application in which it resides.

### 4.2. Standard Access Method

Applications with People and Organization data must be accessible with standard encoding, preferably UTF-8, accessible via standard web protocols, and accessible from a non-proprietary interface. Documentation describing the access method must be made available alongside the data, and must be directly usable by AI Agents, Subject Matter Experts (SMEs), Data Scientists, and Software Developers without requiring specialist knowledge of a particular system.

### 4.3. Definition of People and Organizations Classes and Properties

The classes and properties defined for people and organizations specify the core concepts needed to represent persons, organizations, organizational units, roles, posts, and sites in a consistent and interoperable way.

The People and Organizations data specify the following classes and properties:

```
A)  For each person (schema:Person):
    a) The given name of the person (schema:givenName). This property is required.
    b) The family name of the person (schema:familyName). This property is required.
    c) The full name of the person (schema:name)
    d) Additional names for the person, such as a middle name (schema:additionalName)
    e) Worker roles held by the person, through which their employment is recorded (jpmv:holdsEmployment)
B)  For each worker (jpmv:Worker):
    a) The Worker Standard Identifier for the worker (jpmv:sid). This property is required.
    b) Sites at which the worker is based (org:basedAt). This property is required.
    c) Contact points for the worker (dcat:contactPoint). This property is required.
    d) The employment status code for the worker (jpmv:employmentStatusCode)
    e) The grade code for the worker (jpmv:gradeCode)
C)  The class describes a contingent worker, such as a contractor employed by the organization (jpmv:ContingentWorker)
D)  The class describes the employee role held by a person (jpmv:Employee)
E)  For each organization (org:Organization):
    a) The name of the organization (jpmv:name). This property is required.
    b) Alternative names for the organization (jpmv:alternativeName)
    c) Internal names of the organization (jpmv:internalName)
    d) The identifier for the organization (org:identifier)
    e) Sub-organizations or child organizations of the organization (org:hasSubOrganization)
    f) Units which are part of the organization (org:hasUnit)
    g) Contact points for the organization (dcat:contactPoint)
F)  For each formal organization (org:FormalOrganization):
    a) The official legal name of the formal organization (schema:legalName). This property is required. Formal organizations use schema:legalName in place of jpmv:name.
G)  The class describes a legal company entity, including listed and unlisted firms, represented for identity and registration purposes (jpmv:LegalEntity)
H)  The class describes an organizational unit, such as a department or support unit which is part of some larger organization and only has full recognition within the context of that organization (org:OrganizationalUnit)
I)  For each business unit (jpmv:BusinessUnit):
    a) The cost center for the business unit (jpmv:costCenterId)
    b) Business units which are part of the business unit (jpmv:hasUnit)
J)  For each employment (jpmv:Employment):
    a) Formal organizations the employment is employed by (jpmv:employedBy). This property is required.
    One an only one of the following is required:
      b) The employee associated with the employment (jpmv:employee).
      c) Contingent workers associated with the employment (jpmv:contingentWorker)
    d) Positions the employment is assigned to (jpmv:assignedTo)
    e) The start date of the employment (schema:startDate). This property is required.
    f) The end date of the employment (schema:endDate)
    g) Local managers for the employment (jpmv:localManager)
    h) Alternate managers for the employment (jpmv:alternateManager)
K)  For each instance of a vCard business card (vcard:Kind):
    a) The formatted full name of the object (vcard:fn)
    b) Email addresses for communication with the object (vcard:email)
    c) Telephone numbers for communication with the object (vcard:hasTelephone)
L)  For each position (jpmv:Position):
    a) Names of the position (jpmv:positionName)
    b) Business units in which the position exists (jpmv:positionIn)
    c) The higher-level position to which this position reports (org:reportsTo)
M)  For each site (org:Site):
    a) The address for the site (org:siteAddress)
N)  For each structured identifier (jpmv:StructuredIdentifier):
    a) The value of the identifier (rdf:value)
    b) The source for the identifier (dcterms:source)
```

### 4.4. Available Open Frameworks

Any implementation of People and Organizations within the firm must adhere to this framework per the requirements specified below. Within the firm, any People and Organizations implementation must follow one of the standards approved by the CDO office. The People and Organizations Framework published at Firmwide Data Publishing Frameworks meets this requirement.

## 5. Classes and Associated Properties for People and Organizations

The class and property definitions for defining people and organizations are described below.

### 5.1. Namespace Declarations

The following namespace prefixes are used throughout this document.

| Prefix | Namespace |
| --- | --- |
| cmns-dt: | https://www.omg.org/spec/Commons/DatesAndTimes/ |
| cmns-org: | https://www.omg.org/spec/Commons/Organizations/ |
| cmns-pts: | https://www.omg.org/spec/Commons/PartiesAndSituations/ |
| cmns-sfc: | https://www.omg.org/spec/Commons/SitesAndFacilities/ |
| dcat: | http://www.w3.org/ns/dcat# |
| dcterms: | http://purl.org/dc/terms/ |
| ex: | http://example.com/ns# |
| fibo-fnd-aap-ppl: | https://spec.edmcouncil.org/fibo/ontology/FND/AgentsAndPeople/People/ |
| fibo-fnd-org-fm: | https://spec.edmcouncil.org/fibo/ontology/FND/Organizations/FormalOrganizations/ |
| fibo-fnd-plc-vrt: | https://spec.edmcouncil.org/fibo/ontology/FND/Places/VirtualPlaces/ |
| fibo-fnd-rel-rel: | https://spec.edmcouncil.org/fibo/ontology/FND/Relations/Relations/ |
| foaf: | http://xmlns.com/foaf/0.1/ |
| jpmv: | https://vocabulary.jpmorgan/DataPublishing/ |
| jpmvpo: | https://vocabulary.jpmorgan/DataPublishing/PeopleAndOrganizations/ |
| org: | http://www.w3.org/ns/org# |
| owl: | http://www.w3.org/2002/07/owl# |
| prov: | http://www.w3.org/ns/prov# |
| rdf: | http://www.w3.org/1999/02/22-rdf-syntax-ns# |
| rdfs: | http://www.w3.org/2000/01/rdf-schema# |
| schema: | http://schema.org/ |
| vcard: | http://www.w3.org/2006/vcard/ns# |
| xsd: | http://www.w3.org/2001/XMLSchema# |

### 5.2. People and Organizations Model and Class Definitions

The following defines a standards-based ontology for representing people, organizations, organizational units, roles, posts, and sites within JPMorganChase. The diagram below shows the main classes, attributes and relationships defined in the following sections for People and their employment in an organization.

*Figure: (PeopleAndOrganizations-SchemaOverview-People.png, v.3) Class diagram in which schema:Person (schema:givenName, schema:familyName, schema:additionalName) is rdfs:subClassOf jpmv:Party (jpmv:identifier) and links via jpmv:holdsEmployment to jpmv:Worker (jpmv:sid, org:basedAt, jpmv:employmentStatusCode, jpmv:gradeCode, dcat:contactPoint), which is rdfs:subClassOf jpmv:PartyRole and is the superclass of jpmv:Employee and jpmv:ContingentWorker; jpmv:Employment (schema:startDate, schema:endDate) is rdfs:subClassOf jpmv:PartyRoleRelationship and connects by jpmv:employee to jpmv:Employee, by jpmv:contingentWorker to jpmv:ContingentWorker, by jpmv:assignedTo to jpmv:Position (jpmv:positionName), by jpmv:localManager / jpmv:alternativemanager back to itself, and by jpmv:employedBy to jpmv:LegalEntity (schema:legalName), while jpmv:Position links by org:reportsTo to itself and by jpmv:positionIn to jpmv:BusinessUnit; a legend shows a blue arrow for "relationship" and a black arrow for "rdfs:subClassOf".*

The following shows the main classes, attributes, and relationships defined in the following sections for Organizations.

*Figure: Class diagram in which jpmv:LegalEntity (schema:legalName) is rdfs:subClassOf org:FormalOrganization, which is rdfs:subClassOf org:Organization (jpmv:name, jpmv:alternativeName); org:OrganizationalUnit is also rdfs:subClassOf org:Organization; jpmv:BusinessUnit is rdfs:subClassOf org:OrganizationalUnit with a self-relationship jpmv:hasUnit; org:Organization has a self-relationship org:hasSubOrganization and is rdfs:subClassOf jpmv:Party (jpmv:identifier).*

#### 5.2.1 Person Class Definition

The Person class contains information about a person (alive, dead, undead, or fictional). It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | schema:Person |
| Requirement section | A) |
| Label | Person |
| Definition | A person (alive, dead, undead, or fictional). |
| Subclass Of | jpmv:Party |
| See Also | prov:Person, foaf:Person, fibo-fnd-aap-ppl:Person |

##### 5.2.1.1 Person Property Definitions

The properties below attach to instances of schema:Person. They describe the identifying names for an individual person and link the person to the worker roles that record their engagement with an organization.

| Property | Value |
| --- | --- |
| URI | schema:givenName |
| Requirement section | A) a. |
| Label | given name |
| Definition | Given name. In the U.S., the first name of a Person. |
| Domain | schema:Person |
| Range | xsd:string |
| Max Count | 1 |
| Min Count | 1 |

| Property | Value |
| --- | --- |
| URI | schema:familyName |
| Requirement section | A) b. |
| Label | family name |
| Definition | Family name. In the U.S., the last name of a Person. |
| Domain | schema:Person |
| Range | xsd:string |
| Max Count | 1 |
| Min Count | 1 |

| Property | Value |
| --- | --- |
| URI | schema:name |
| Requirement section | A) c. |
| Label | name |
| Definition | The full name of the person. |
| Domain | schema:Person |
| Range | xsd:string |

| Property | Value |
| --- | --- |
| URI | schema:additionalName |
| Requirement section | A) d. |
| Label | additional name |
| Definition | An additional name for a Person, can be used for a middle name. |
| Domain | schema:Person |
| Range | xsd:string |

| Property | Value |
| --- | --- |
| URI | jpmv:holdsEmployment |
| Requirement section | A) e. |
| Label | holds employment |
| Definition | Indicates a Worker role (an Employee or Contingent Worker) held by the Person, through which the Person's Employment with an Organization is recorded. |
| Subproperty Of | org:hasMembership |
| Domain | schema:Person |
| Range | jpmv:Worker |

#### 5.2.2 Worker Class Definition

The Worker class contains information about the worker role held by an employee or contingent worker. It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | jpmv:Worker |
| Requirement section | B) |
| Label | Worker |
| Definition | The worker role held by an employee or contingent worker. |
| Subclass Of | jpmv:PartyRole |

##### 5.2.2.1 Worker Property Definitions

The properties below attach to instances of jpmv:Worker. They identify the worker within the engaging organization (including the JPMorganChase Standard Id), record the worker's employment status and grade, provide a contact point for the worker, and link the worker to the sites at which they are based.

| Property | Value |
| --- | --- |
| URI | jpmv:sid |
| Requirement section | B) a. |
| Label | Worker Standard Identifier |
| Definition | The JPMC Standard ID is a common internal identifier used to identify JPMC-affiliated persons. This property may be used in addition to jpmv:identifier when identifying a person with a SID. |
| Domain | jpmv:Worker |
| Range | xsd:string |
| Max Count | 1 |
| Min Count | 1 |
| Usage Note | jpmv:sid is required for JPMorganChase workers and must follow the pattern of a letter followed by six numbers. |

| Property | Value |
| --- | --- |
| URI | org:basedAt |
| Requirement section | B) b. |
| Label | based at |
| Definition | Indicates the site at which an employment position is based. We do not restrict the possibility that a person is based at multiple sites. |
| Domain | jpmv:Worker |
| Range | org:Site |
| Min Count | 1 |

| Property | Value |
| --- | --- |
| URI | dcat:contactPoint |
| Requirement section | B) c. |
| Label | contact point |
| Definition | A contact point for a person or organization. |
| Domain | jpmv:Worker |
| Range | vcard:Kind |
| Min Count | 1 |

| Property | Value |
| --- | --- |
| URI | jpmv:employmentStatusCode |
| Requirement section | B) d. |
| Label | employment status code |
| Definition | Code that identifies an individual Employment status. Valid values include A (Active), L (Leave), T (Terminated). |
| Domain | jpmv:Worker |
| Range | xsd:string |
| Max Count | 1 |

| Property | Value |
| --- | --- |
| URI | jpmv:gradeCode |
| Requirement section | B) e. |
| Label | grade code |
| Definition | The grade code associated with a person's employment, for example "Managing Director", "Vice President", etc. |
| Domain | jpmv:Worker |
| Range | xsd:string |
| Max Count | 1 |

#### 5.2.3 Contingent Worker Class Definition

The Contingent Worker class contains information about a contingent worker, such as a contractor employed by the organization. It is an instance of rdfs:Class.

Properties for `jpmv:ContingentWorker` are defined in its superclass `jpmv:Worker`.

| Property | Value |
| --- | --- |
| URI | jpmv:ContingentWorker |
| Requirement section | C) |
| Label | Contingent worker |
| Definition | A contingent worker, such as a contractor employed by the organization. |
| Subclass Of | jpmv:Worker |

#### 5.2.4 Employee Class Definition

The Employee class contains information about an employee employed by the organization. It is an instance of rdfs:Class.

Properties for `jpmv:Employee` are defined in its superclass `jpmv:Worker`.

| Property | Value |
| --- | --- |
| URI | jpmv:Employee |
| Requirement section | D) |
| Label | Employee |
| Definition | An employee employed by the organization. |
| Subclass Of | jpmv:Worker |

#### 5.2.5 Organization Class Definition

The Organization class contains information about a collection of people organized together into a community or other social, commercial or political structure. The group has some common purpose or reason for existence which goes beyond the set of people belonging to it and can act as an Agent. Organizations are often decomposable into hierarchical structures. It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | org:Organization |
| Requirement section | E) |
| Label | Organization |
| Definition | Represents a collection of people organized together into a community or other social, commercial or political structure. The group has some common purpose or reason for existence which goes beyond the set of people belonging to it and can act as an Agent. Organizations are often decomposable into hierarchical structures. |
| Subclass Of | jpmv:Party |
| See Also | prov:Organization, foaf:Organization, cmns-org:Organization |

##### 5.2.5.1 Organization Property Definitions

The properties below attach to instances of org:Organization. They describe the name, alternative name, and internal name of the Organization, its organization identifier, its hierarchical relationships with sub-organizations and units, and a contact point for the Organization.

| Property | Value |
| --- | --- |
| URI | jpmv:name |
| Requirement section | E) a. |
| Label | name |
| Definition | Name of the item. |
| Domain | owl:Thing |
| Range | xsd:string |
| Max Count | 1 |
| Min Count | 1 |
| See Also | foaf:name |

| Property | Value |
| --- | --- |
| URI | jpmv:alternativeName |
| Requirement section | E) b. |
| Label | alternative name |
| Definition | Alternative name for the item. |
| Domain | owl:Thing |
| Range | xsd:string |

| Property | Value |
| --- | --- |
| URI | jpmv:internalName |
| Requirement section | E) c. |
| Label | internal name |
| Definition | The JPMC internal entity name. |
| Domain | org:Organization |
| Range | xsd:string |
| Usage Note | This property corresponds to Entity Name (entity_name) in the Fusion Data Dictionary. |

| Property | Value |
| --- | --- |
| URI | org:identifier |
| Requirement section | E) d. |
| Label | identifier |
| Definition | Gives an identifier, such as a company registration number, that can be used to uniquely identify the organization. |
| Domain | org:Organization |
| Range | xsd:string |
| Max Count | 1 |

| Property | Value |
| --- | --- |
| URI | org:hasSubOrganization |
| Requirement section | E) e. |
| Label | has sub organization |
| Definition | Represents hierarchical containment of Organizations or OrganizationalUnits; indicates an organization which is a sub-part or child of this organization. |
| Domain | org:Organization |
| Range | org:Organization |

| Property | Value |
| --- | --- |
| URI | org:hasUnit |
| Requirement section | E) f. |

*(shot 11 ends mid-table — the org:hasUnit property table is clipped after "Requirement section | E) f.")*

| Property | Value |
| --- | --- |
| URI | org:hasUnit |
| Requirement section | E) f. |
| Label | has unit |
| Definition | Indicates a unit which is part of this Organization, e.g. a Department within a larger Organization. |
| Subproperty Of | org:hasSubOrganization |
| Domain | org:Organization |
| Range | org:OrganizationalUnit |

| Property | Value |
| --- | --- |
| URI | dcat:contactPoint |
| Requirement section | E) g. |
| Label | contact point |
| Definition | A contact point for a person or organization. |
| Domain | org:Organization |
| Range | vcard:Kind |

#### 5.2.6 Formal Organization Class Definition

The Formal Organization class contains information about an Organization which is recognized in the world at large, in particular in legal jurisdictions, with associated rights and responsibilities. Examples include a corporation, charity, government or church. It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | org:FormalOrganization |
| Requirement section | F) |
| Label | Formal Organization |
| Definition | An Organization which is recognized in the world at large, in particular in legal jurisdictions, with associated rights and responsibilities. Examples include a corporation, charity, government or church. |
| Subclass Of | org:Organization |
| See Also | cmns-org:FormalOrganization |

##### 5.2.6.1 Formal Organization Property Definitions

The property below attaches to instances of org:FormalOrganization. Per the SHACL constraints, Formal Organizations use schema:legalName in place of jpmv:name to record their official registered name.

| Property | Value |
| --- | --- |
| URI | schema:legalName |
| Requirement section | F) a. |
| Label | legal name |
| Definition | Official legal name as recorded in a register. |
| Domain | org:FormalOrganization |
| Range | xsd:string |
| Min Count | 1 |
| Max Count | 1 |
| See Also | fibo-fnd-rel-rel:hasLegalName |
| Usage Note | Use schema:legalName instead of jpmv:name for formal organizations. |

#### 5.2.7 Legal Entity Class Definition

The Legal Entity class contains information about a legal company entity, including listed and unlisted firms, represented for identity and registration purposes. It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | jpmv:LegalEntity |
| Requirement section | G) |
| Label | Legal Entity |
| Definition | A legal company entity, including listed and unlisted firms, represented for identity and registration purposes. |
| Subclass Of | org:FormalOrganization |

#### 5.2.8 Organizational Unit Class Definition

The Organizational Unit class contains information about an Organization such as a department or support unit which is part of some larger Organization and only has full recognition within the context of that Organization. In particular the unit would not be regarded as a legal entity in its own right. It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | org:OrganizationalUnit |
| Requirement section | H) |
| Label | Organizational Unit |
| Definition | An Organization such as a department or support unit which is part of some larger Organization and only has full recognition within the context of that Organization. In particular the unit would not be regarded as a legal entity in its own right. |
| Subclass Of | org:Organization |
| See Also | cmns-org:OrganizationalSubUnit |

#### 5.2.9 Business Unit Class Definition

The Business Unit class contains information about a business unit within the organization's hierarchy, such as a line of business, corporate function, or department. It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | jpmv:BusinessUnit |
| Requirement section | I) |
| Label | Business unit |
| Definition | An organizational unit within the firm's hierarchy, such as a Line of Business (LOB) or Corporate Function (CF). |
| Subclass Of | org:OrganizationalUnit |

##### 5.2.9.1 Business Unit Property Definitions

The properties below attach to instances of jpmv:BusinessUnit. They record the cost center that identifies the business unit as the organization's lowest-level unit for headcount and accounting purposes, and link the business unit to nested business units it contains.

| Property | Value |
| --- | --- |
| URI | jpmv:costCenterId |
| Requirement section | I) a. |
| Label | cost center |
| Definition | Provides a reference to the associated primary department. If this is a primary department, it will refer to itself. Represents the cost center for an employee or non-employee. The cost center is the organization's lowest level business unit. Examples include: 038754=Central Operations HR, 287212 = Commercial Mortgage Loans, and 003478 = CCB Midwest 0102. |
| Domain | jpmv:BusinessUnit |
| Range | xsd:string |
| Max Count | 1 |

| Property | Value |
| --- | --- |
| URI | jpmv:hasUnit |
| Requirement section | I) b. |
| Label | has unit |
| Definition | Indicates a business unit which is part of another business unit, e.g. a a sub-LOB within a LOB. |
| Subproperty Of | org:hasUnit |
| Domain | jpmv:BusinessUnit |
| Range | jpmv:BusinessUnit |

#### 5.2.10 Employment Class Definition

The Employment class contains information about a specific type of membership in an organization indicating employment. It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | jpmv:Employment |
| Requirement section | J) |
| Label | Employment |
| Definition | A specific type of membership in an organization indicating employment. |
| Subclass Of | org:Membership, jpmv:PartyRoleRelationship |

##### 5.2.10.1 Employment Property Definitions

The properties below attach to instances of jpmv:Employment. They link the employment to the employer of record and the employee role it realizes, capture the dates of the engagement, tie the employment to the Position it fills, and record the worker's local and alternate managers.

| Property | Value |
| --- | --- |
| URI | jpmv:employedBy |
| Requirement section | J) a. |
| Label | employed by |
| Definition | Indicates the organization a person is employed by. |
| Subproperty Of | org:organization |
| Domain | jpmv:Employment |
| Range | org:FormalOrganization |
| Min Count | 1 |
| Max Count | 1 |
| See Also | fibo-fnd-org-fm:isEmployedBy |

| Property | Value |
| --- | --- |
| URI | jpmv:employee |
| Requirement section | J) b. |
| Label | employee |
| Definition | The employee relationship between the party role relationship of Employee and an employee. |
| Domain | jpmv:Employment |
| Range | jpmv:Employee |
| Max Count | 1 |

| Property | Value |
| --- | --- |
| URI | jpmv:contingentWorker |
| Requirement section | J) c. |
| Label | contingent worker |
| Definition | The contingent worker relationship between a party role relationship of Employment and a contingent worker. |
| Domain | jpmv:Employment |
| Range | jpmv:ContingentWorker |

| Property | Value |
| --- | --- |
| URI | jpmv:assignedTo |
| Requirement section | J) d. |
| Label | assigned to |
| Definition | Indicates a Position associated with an Employment object. |
| Domain | jpmv:Employment |
| Range | jpmv:Position |

| Property | Value |
| --- | --- |
| URI | schema:startDate |
| Requirement section | J) e. |
| Label | start date |
| Definition | The start date and time of the item (in format defined in Date and Time Framework). |
| Domain | jpmv:Employment |
| Range | xsd:date |
| Max Count | 1 |
| Min Count | 1 |
| See Also | cmns-dt:hasStartDate |

| Property | Value |
| --- | --- |
| URI | schema:endDate |
| Requirement section | J) f. |
| Label | end date |
| Definition | The end date and time of the item (in format defined in Date and Time Framework). |
| Domain | jpmv:Employment |
| Range | xsd:date |
| Max Count | 1 |
| See Also | cmns-dt:hasEndDate |

| Property | Value |
| --- | --- |
| URI | jpmv:localManager |
| Requirement section | J) g. |
| Label | local manager |
| Definition | Represents a local manager for an employee. |
| Domain | jpmv:Employment |
| Range | jpmv:Employment |

| Property | Value |
| --- | --- |
| URI | jpmv:alternateManager |
| Requirement section | J) h. |
| Label | alternate manager |
| Definition | Represents an alternate manager for an employee. |
| Domain | jpmv:Employment |
| Range | jpmv:Employment |

#### 5.2.11 Kind Class Definition

The Kind class contains information about a vCard business card. It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | vcard:Kind |
| Requirement section | K) |
| Label | Kind |
| Definition | A vCard business card. |

##### 5.2.11.1 Kind Property Definitions

The properties below attach to instances of vcard:Kind. They describe contact information including the formatted display name, electronic mail address, and telephone number for communication with the contact entity.

| Property | Value |
| --- | --- |
| URI | vcard:fn |
| Requirement section | K) a. |
| Label | fn |
| Definition | The formatted text corresponding to the name of the object (the full name string). |
| Domain | vcard:Kind |
| Range | xsd:string |
| Max Count | 1 |

| Property | Value |
| --- | --- |
| URI | vcard:email |
| Requirement section | K) b. |
| Label | email |
| Definition | To specify the electronic mail address for communication with the object. |
| Domain | vcard:Kind |
| Range | xsd:anyURI |
| See Also | fibo-fnd-plc-vrt:hasElectronicMailAddress |

| Property | Value |
| --- | --- |
| URI | vcard:hasTelephone |
| Requirement section | K) c. |
| Label | has telephone |
| Definition | To specify the telephone number for telephony communication with the object. |
| Domain | vcard:Kind |
| Range | xsd:string |
| See Also | fibo-fnd-plc-vrt:hasTelephoneNumber |

#### 5.2.12 Position Class Definition

The Position class contains information about the position held by and employee. It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | jpmv:Position |
| Requirement section | L) |
| Label | Position |
| Definition | The position held by an employee. Subclass of org:Post. |
| Subclass Of | org:Post |

##### 5.2.12.1 Position Property Definitions

The properties below attach to instances of jpmv:Position. They record the human-readable name of the position, the Organization in which the position exists, and the higher-level position to which it reports.

| Property | Value |
| --- | --- |
| URI | jpmv:positionName |
| Requirement section | L) a. |
| Label | position name |
| Definition | Name of the position (ex: Data Scientist Director). |
| Domain | jpmv:Position |
| Range | xsd:string |

| Property | Value |
| --- | --- |
| URI | jpmv:positionIn |
| Requirement section | L) b. |
| Label | position in |
| Definition | Indicates the Organization in which the Position exists. |
| Subproperty Of | org:postIn |
| Domain | jpmv:Position |
| Range | jpmv:BusinessUnit |
| Usage Note | This property normally reflects the organizational unit a position resides in. |

| Property | Value |
| --- | --- |
| URI | org:reportsTo |
| Requirement section | L) c. |
| Label | reports to |
| Definition | Indicates a reporting relationship as might be depicted on an organizational chart. It can be used to indicate a reporting relationship directly between Agents or between Posts that Agents could hold. |
| Domain | jpmv:Position |
| Range | jpmv:Position |
| Max Count | 1 |
| See Also | schema:worksFor |

#### 5.2.13 Site Class Definition

The Site class contains information about an office or other premise at which the organization is located. Many organizations are spread across multiple sites and many sites will host multiple locations. It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | org:Site |
| Requirement section | M) |
| Label | Site |
| Definition | An office or other premise at which the organization is located. Many organizations are spread across multiple sites and many sites will host multiple locations. |
| See Also | cmns-sfc:Site |

##### 5.2.13.1 Site Property Definitions

The properties below attach to instances of org:Site. They describe the address of the site, which may include physical, email, telephone, or geo-location information.

| Property | Value |
| --- | --- |
| URI | org:siteAddress |
| Requirement section | M) a. |
| Label | site address |
| Definition | Indicates an address for the site in a suitable encoding. The values must conform to the Postal Address Framework. The address may include email, telephone, and geo-location information and is not restricted to a physical address. |
| Domain | org:Site |
| Range | jpmv:PostalAddress |
| Max Count | 1 |

#### 5.2.14 Structured Identifier Class Definition

The Structured Identifier class contains information about an identifier consisting of an identifier and the source that the identifier is defined in. It is an instance of rdfs:Class.

| Property | Value |
| --- | --- |
| URI | jpmv:StructuredIdentifier |
| Requirement section | N) |
| Label | Structured identifier |
| Definition | Identifier consisting of an identifier and the source that the identifier is defined in. |

##### 5.2.14.1 Structured Identifier Property Definitions

The properties below attach to instances of jpmv:StructuredIdentifier. They record the value of the identifier and the source system from which it originates.

| Property | Value |
| --- | --- |
| URI | rdf:value |
| Requirement section | N) a. |
| Label | value |
| Definition | The value of a resource. |
| Domain | jpmv:StructuredIdentifier |
| Range | xsd:string |

| Property | Value |
| --- | --- |
| URI | dcterms:source |
| Requirement section | N) b. |
| Label | source |
| Definition | The source for the identifier. This should point to a rdfs:Resource that is a JPMC SoR. |
| Domain | jpmv:StructuredIdentifier |
| Range | rdfs:Resource |

## 6. Specifying People and Organizations – Representative Examples

The following Turtle snippets show how the framework captures common patterns for specifying people and organizations in the context of JPMorganChase. The examples share the prefix declarations below.

```turtle
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix ex: <http://example.com/ns#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix jpmv: <https://vocabulary.jpmorgan/DataPublishing/> .
@prefix org: <http://www.w3.org/ns/org#> .
@prefix schema: <http://schema.org/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
```

### 6.1. A Person With Identifying Attributes and a Contact Point

This example shows a Person with required given and family names and an additional name. The Person carries a structured identifier (`jpmv:identifier`) whose `jpmv:StructuredIdentifier` records the identifier value (`rdf:value`) and its source system (`dcterms:source`). The Person holds an Employee role (`jpmv:Employee`) reached via `jpmv:holdsEmployment`. The Employee role carries the worker's Standard Id (`jpmv:sid`), the worker's employment status (`jpmv:employmentStatusCode`), a vCard contact point (`dcat:contactPoint`), and the `org:Site` the worker is based at via `org:basedAt`, whose `org:siteAddress` conforms to the Postal Address Framework. A separate `jpmv:Employment` ties the Employee role to the employer of record (`jpmv:JPMorganChase`, a `jpmv:LegalEntity` — a subclass of `org:FormalOrganization` — identified by its `schema:legalName`) via `jpmv:employedBy` and links the Employee role through `jpmv:employee`.

```turtle
ex:MariaGarcia a schema:Person ;
  schema:givenName "Maria" ;
  schema:familyName "Garcia" ;
  schema:additionalName "Elena" ;
  jpmv:identifier ex:MariaGarcia_ID ;
  jpmv:holdsEmployment ex:MariaGarcia_Employee .

# Structured identifier carrying the value and its source system.
ex:MariaGarcia_ID a jpmv:StructuredIdentifier ;
```

*(gap between people-org-20.png and people-org-21.png — the remainder of Section 6 (examples 6.1 onward), Sections 7 and 8, and the beginning of the table ending in the "Additional Contacts | TBD" row are not screenshotted)*

| | |
| --- | --- |
| Additional Contacts | TBD |

## 9. Appendix A: Relationship to Other FCDO Data Publishing Frameworks

### 9.1 People and Organization Classes and Properties Defined in Other Frameworks

Other FCDO Data Publishing Frameworks specify properties related to people and organizations such as publisher, contact point, owner, creator, modifier, assigner, and assignee. These specify people and agent data whose classes are defined in this framework. The following sections detail how the frameworks use people and organization concepts. A common theme among those properties is ownership. Therefore ownership appears in a dedicated section.

### 9.2 Framework Specifying People and Organization Ownership

A key issue for many relationships with People and Organizations is the concept of ownership: who owns a dataset, a data product, a knowledge base, a data contract, a mapping, or an identifier namespace. Across the FCDO Data Publishing Frameworks, ownership is consistently expressed as a relationship between a managed asset (Dataset, Data Product, Knowledge Base, Policy, Mapping Set, Provenance Entity, etc.) and an *Agent* — that is, a Person, an Organization, an Organizational Unit, or in some cases a software/AI agent. Ownership is therefore modelled as one or more *properties* whose range is an Agent-typed individual, and the People and Organizations Framework provides the canonical definition of those Agent-typed individuals.

Two of the FCDO frameworks introduce a JPMC-specific owner predicate — Data Products (`dprod:dataProductOwner`) and Descriptive Metadata (`jpmv:datasetOwner`), both required. The remaining ownership statements across the frameworks are either inherited rights-holder semantics from Dublin Core (`dcterms:rightsHolder`), ODRL actions that transfer ownership of an asset between parties (`odrl:transferOwnership`, `odrl:give`, `odrl:sell`), or prose-level mandates without a corresponding predicate (Knowledge Bases, Identifiers). Authorship, publication, modification, contact, policy-role, and provenance-attribution properties are *not* treated as ownership in this section — they are addressed separately in Section 9.3.

**Implications for the People and Organizations Framework**

This Framework is the unifying point for all of the above. Any instance that fills an owner slot in any of the FCDO frameworks should be specified as one of the People and Organizations classes defined in Section 5 — `schema:Person`, `org:Organization`, or `org:OrganizationalUnit`. Concretely:

1. **A single canonical representation of owners.** Every owner-typed value in another framework (whether typed `foaf:Agent`, `prov:Agent`, or `odrl:Party` in the source vocabulary) must also be an instance of a People and Organizations class so that it carries an identifier, name, and the other properties required by Section 5.
2. **Ownership is a relationship, not a property of People/Organizations.** This Framework defines *who* owners are, not *what* they own. The "owns" direction is asserted by the consuming framework (e.g., a Data Product asserts `dprod:dataProductOwner` pointing at an Organization defined here). The People and Organizations Framework does not introduce an `owns` predicate.
3. **Organizations and Organizational Units are first-class owners.** Several framework definitions (notably Knowledge Bases, which states "Every knowledge base must have an owner (individual or group)") permit groups as owners. Section 5's `org:Organization` and `org:OrganizationalUnit` classes are the intended target for these group-owner cases.

#### 9.2.1 Overview of Ownership Properties

The following enumerates every ownership statement in the other FCDO frameworks — whether expressed as a dedicated owner property, an ODRL ownership-transfer action, or a prose-level mandate without a corresponding predicate — and identifies the People and Organizations class expected to fill it.

| Property / mechanism | Frameworks where defined | Range as defined | People & Organizations class to instantiate |
| --- | --- | --- | --- |
| `dprod:dataProductOwner` | Data Products | `prov:Agent ∨ foaf:Agent` | `schema:Person` |
| `jpmv:datasetOwner` | Descriptive Metadata | `foaf:Agent` | `schema:Person` |
| `dcterms:rightsHolder` | Data Contracts (via DC import) | `dcterms:Agent` | `schema:Person, org:Organization` |
| `odrl:transferOwnership` (action) | Usage Rights, Data Contracts | transfers ownership between `odrl:Party` (assigner ↔ assignee) | `schema:Person, org:Organization` |
| `odrl:give` (action) | Usage Rights, Data Contracts | transfers ownership between `odrl:Party` (assigner ↔ assignee) | `schema:Person, org:Organization` |
| `odrl:sell` (action) | Usage Rights, Data Contracts | transfers ownership between `odrl:Party` (assigner ↔ assignee) | `schema:Person, org:Organization` |
| Prose-level owner mandate (no predicate) | Knowledge Bases | n/a — narrative requirement ("individual or group") | `schema:Person, org:Organization, org:OrganizationalUnit` |
| Prose-level owner mandate (no predicate) | Identifiers | n/a — narrative requirement | `schema:Person, org:Organization, org:OrganizationalUnit` |

In all cases, the Person, Organization, or Organizational Unit individual that fills these properties **must conform to the requirements of Section 5** of this Framework — including the required identifier, source-of-identifier, and naming attributes — so that ownership relationships can be resolved consistently across all FCDO Data Publishing Frameworks.

### 9.3 Other People and Organization References in Other Frameworks

Beyond ownership, the other FCDO frameworks reference People and Organizations through a number of related but distinct relationships — authorship, publication, modification, contact, policy roles, and provenance attribution. None of these are ownership in the sense of Section 9.2, but each places a Person or Organization at the other end of the property, and each therefore requires an instance defined under this Framework. The relationships fall into the following groups:

- **Authorship** — the actor that created the asset (`dcterms:creator`).
- **Publication** — the actor that makes the asset available (`dcterms:publisher`).
- **Modification** — the actor that last changed the asset (`jpmv:modifiedBy`).
- **Contact** — a contact endpoint, modelled as a `vcard:Kind`, that identifies *how* to reach a responsible party (`dcat:contactPoint`).
- **Policy roles** — the data provider and data consumer in usage rights and contracts (`odrl:assigner`, `odrl:assignee`, `dprod:subject`, `dprod:object`); party hierarchy (`dprod:partOfTransitive`).
- **Attribution and association** — the agent(s) responsible for an entity's existence or for performing an activity in PROV-O terms (`prov:wasAttributedTo`, `prov:wasAssociatedWith`).

As with ownership, the ranges used across the frameworks are not consistent — `foaf:Agent` in Descriptive Metadata, Data Mapping, and Knowledge Bases; `prov:Agent` in Provenance; `odrl:Party` in Data Contracts and Usage Rights — and instances of those classes are expected to also be instances of the corresponding People and Organizations Framework classes from Section 5. One specific reconciliation point is worth noting:

- **Provenance attribution complements but does not replace ownership.** `prov:wasAttributedTo` records historical attribution; the explicit ownership properties in Section 9.2 record current accountability. Both should reference the same People and Organizations instances when they refer to the same actor.

#### 9.3.1 Summary of Non-Ownership People and Organization Properties Across Frameworks

| Property | Frameworks where defined | Range as defined | People & Organizations class to instantiate |
| --- | --- | --- | --- |
| `dcterms:creator` | Descriptive Metadata, Data Products, Data Mapping, Knowledge Bases | `foaf:Agent` | `schema:Person, org:Organization` |
| `dcterms:publisher` | Descriptive Metadata, Data Products, Knowledge Bases | `foaf:Agent` | `schema:Person, org:Organization` |
| `dcat:contactPoint` | Descriptive Metadata, Data Products, Knowledge Bases | `vcard:Kind` | Contact endpoint for an Agent |
| `jpmv:modifiedBy` | Data Mapping, Descriptive Metadata, Data Products | `foaf:Agent` | `schema:Person, org:Organization` |
| `odrl:assigner` | Usage Rights, Data Contracts | `odrl:Party` | `org:Organization, schema:Person` |
| `odrl:assignee` | Usage Rights, Data Contracts | `odrl:Party` | `org:Organization, schema:Person` |
| `dprod:subject` | Data Contracts | `odrl:Party` | `org:Organization, schema:Person` |
| `dprod:object` | Data Contracts | `odrl:Party` | `org:Organization, schema:Person` |
| `dprod:partOfTransitive` | Data Contracts | `odrl:Party → odrl:Party` | `org:Organization` hierarchy |
| `prov:wasAttributedTo` | Provenance, Data Contracts (test data) | `prov:Agent` | `schema:Person, org:Organization` |
| `prov:wasAssociatedWith` | Provenance | `prov:Agent` | `schema:Person, org:Organization` |

As in Section 9.2, the Person, Organization, or Organizational Unit individual that fills these properties **must conform to the requirements of Section 5** of this Framework so that the references can be resolved consistently across all FCDO data publishing frameworks.

*(capture ends here — page content ends at Section 9.3.1; the URL stayed `confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/6030480492/People+and+Organizations+Framework` throughout all twenty-two screenshots)*

---

# V. FCDO Ontology Builder — skill definition and review session  *(not Confluence)*

> **Source:** these five screenshots are **not** Confluence pages. `ont-bui.png` shows a raw `SKILL.md` file; the four `fcdo-ontology-builder*.png` shots show an AI coding-assistant session (footer reads "Claude Opus 4.8 • 128.5 credits") reviewing that skill against a system called DryDocs. No address bar is visible in any of them.
> **Screenshots:** ont-bui.png, fcdo-ontology-builder.png, fcdo-ontology-builder2.png, fcdo-ontology-builder3.png, fcdo-ontology-builder4.png

## Part 1 — `fcdo-ontology-builder` SKILL.md (raw file view, `ont-bui.png`)

```markdown
---
name: fcdo-ontology-builder
description: Build FCDO-compliant RDFS/OWL/SHACL ontologies and SKOS taxonomies for JPMorgan Chase from user-supplied artifacts (DDL, JSON Schema, XML Schema, existing ontologies, spreadsheets, glossaries, CWM/UML XMI, OSI YAML, prose docs). Generates JSON-LD ontology files plus example data, SHACL validation report, name-consistency report, and a tracked design-decisions file.
---

# fcdo-ontology-builder

Builds FCDO (Firmwide Chief Data Office, JPMorgan Chase) compliant
ontologies. Produces an RDFS/OWL ontology, a SHACL shapes ontology,
optionally a SKOS Concept Schemes file, validated example RDF data, and
two Markdown reports (validation + name consistency).

## Recommended AI model

**Claude Opus** is the best choice for running this skill. Sonnet may miss
subtle ontological distinctions.

JPMorgan Chase users work in the **Dev Shell** environment. Before running
`claude` or `code` at the Dev Shell prompt, set:

```cmd
set CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000
```

## When to use this skill

Activate when the user asks to:
- "Build an ontology" / "Build a SHACL ontology" / "Create an RDFS model"
  in a JPMorgan / FCDO context.
- Convert any of the artifact types listed in `references/artifact-handling.md`
  into an FCDO-compliant RDFS/OWL/SHACL ontology.
- Produce or refresh SKOS taxonomies that pair with an FCDO ontology.

## Workflow

Follow these steps in order. Ask the user before assuming anything; record
every choice in `design-decisions.md`.

### Step 1 — Discover candidate artifacts

- Glob the project working directory for likely artifacts: `*.sql`,
  `*.ddl`, `*.json`, `*.xsd`, `*.xml`, `*.xmi`, `*.yaml`, `*.yml`,
  `*.xlsx`, `*.csv`, `*.ttl`, `*.rdf`, `*.jsonld`, `*.md`.
- Show the candidate list to the user. **Do not** assume any specific file
  is a source unless the user confirms.

### Step 2 — Confirm scope and the ontology IRI

Ask:
1. Which of the discovered artifacts should be used as sources?
2. What namespace prefix should the ontology use? Default the ontology
   namespace IRI to `https://vocabulary.jpmorgan/DataPublishing/<prefix>/`
   with a trailing slash.
3. Should a SKOS file be produced? (Required if any source artifact
   contains enumerations — confirm anyway.)
4. What is the project / ontology short name (used for filenames and the
   `owl:Ontology` `rdfs:label`)?

### Step 3 — Read artifacts and propose the model

Use `references/artifact-handling.md` for per-artifact-type rules. While
reading:
- Look for **denormalization** (e.g. `home*` and `work*` columns on
  `Person` → split out an `Address` class). Always confirm a normalization
  with the user before applying it.
- Identify **enumerations** → SKOS Concept Schemes.
- Note any names you have to **invent** for `rdfs:label`/`rdfs:comment`;
  these go in `<project-working-dir>\generated-labels.xlsx` (project root).

Present the proposed class/property list to the user and ask for
```

*(the SKILL.md view is clipped here — the rest of Step 3 and Steps 4–10 are not captured)*

## Part 2 — "REVIEW FCDO DIRECTORIES AND COMPARE" (assistant session)

*The remaining four screenshots capture an assistant response reviewing the two `fcdo-` skills and comparing them to a system called DryDocs.*

I now have a full picture of both. Here's the review and comparison.

### Part 1 — First-pass review of the `fcdo-` skills

The `fcdo-ontology-builder-github-copilot` workspace contains **two peer agent skills** (each a `SKILL.md` + supporting references/scripts), plus a shared `memory`. They are a JPMorgan/FCDO ontology-authoring toolchain.

**Skill A — `fcdo-ontology-builder`**

**What it does:** turns user-supplied source artifacts (DDL, JSON Schema, XSD, existing RDFS/OWL/SHACL, LinkML, spreadsheets, glossaries, CWM/UML XMI, OSI YAML, prose) into an **FCDO-compliant RDFS/OWL ontology + SHACL shapes + optional SKOS taxonomy**, with validated example data and two audit reports.

**Structure:**

- `SKILL.md` — a strict 10-step workflow: discover artifacts → confirm scope/IRI → propose model → **record design decisions** → generate JSON-LD → validate SHACL-of-SHACL → validate examples → consistency check → iterate → generate HTML docs.
- `references/artifact-handling.md` — a per-artifact-type "cookbook" (mapping tables: table→class, column→property, FK→ObjectProperty, CHECK-IN→SKOS, etc.).
- `references/output-specs.md` — the normative spec for every output file: IRI conventions (`https://vocabulary.jpmorgan/DataPublishing/<prefix>/`), required triples, **forbidden OWL constructs** (only `owl:Class` / `ObjectProperty` / `DatatypeProperty` / `Ontology` / `imports` allowed; everything richer must be re-expressed in SHACL).
- `references/design-decisions-template.md` — a themed, stable-ID (`DD-001`) decision log; every Claude inference is flagged 🟡.
- `references/python-bootstrap.md` — JPMC Dev Shell / Artifactory-mirror env setup.
- `scripts` — `validate_shacl.py` (pyshacl, `inference="rdfs"`, OWL off), `consistency_check.py` (round-trips source names ↔ ontology IRIs), `resources/rdf/*.ttl` (SHACL-of-SHACL + SKOS shapes).

**Skill B — `fcdo-ontology-html-doc`**

**What it does:** renders existing ontology/taxonomy files (Turtle/RDF-XML/JSON-LD) into a **single self-contained HTML** data dictionary — class/property hierarchies, concept browser, per-class Mermaid diagrams, embedded CSS/JS. Read-only (builder Step 10 invokes it with `--combine`).

**First-pass observations**

- **Governance-first, not automation-first.** The dominant motif is "never invent silently" — every inference is a logged, user-reviewable decision; the skill repeatedly stops to ask.
- **Standards-locked output.** A deliberately narrow OWL profile forces expressiveness into SHACL — a house style, enforced by spec docs + a SHACL-of-SHACL meta-validation.
- **Round-trip verification.** The consistency report checks that source names survive into the ontology (catches silent drops/renames).
- **Enterprise-runtime realism.** Dev Shell env vars, Artifactory mirror, "no direct PyPI," forward-slash→backslash rules — clearly written for the locked-down JPMC network.

### Part 2 — Comparison with the DryDocs ontology model + HITL gates

Both are ontology-governance systems built around the same core belief: **meaning must be human-confirmed, never auto-asserted.** But they sit at opposite ends of the pipeline.

| Axis | `fcdo-ontology-builder` | **DryDocs** |
| --- | --- | --- |
| **Goal** | *Author* a new ontology (blueprint) from source schemas | *Populate* a knowledge graph from live operational sources |
| **Direction** | Design-time: artifact → RDFS/OWL/SHACL/SKOS files | Ingest-time: taxonomy import → ontology mapping → Neo4j load → context projection |
| **Standards** | RDFS/OWL (narrow profile) + SHACL + SKOS + XSD | PROV-O (9-row matrix) + W3C ORG + DPROD + SOSA/SSN + DCAT/SKOS |
| **Layering** | Implicit (source → ontology in one guided pass) | Explicit 4 layers — taxonomy → ontology → knowledge graph → context (`00-conceptual-model.md`) |
| **Output** | Static files (JSON-LD, HTML, reports) | A running Neo4j graph across trust-separated DBs (`drydocs` vs `drydocs_context`) |

**Where they strongly converge**

The two systems independently arrived at the **same anti-drift discipline**, and even the same failure story:

- **FCDO's "never invent silently → `design-decisions.md` with 🟡 flags"** is functionally identical to DryDocs' "no edge until the mapping is `confirmed`" (`taxonomy-ontology-map.yaml`).
- **DryDocs' explicit reason for the gate** is the "POC drift" — *"relationships that ignored taxonomy/ontology because import and meaning were done in one step."* FCDO guards the exact same risk by making artifact-reading and model-proposal separate, confirm-gated steps.
- Both keep an **auditable decision record**: FCDO's themed `DD-###` log ↔ DryDocs' `gate-log.md` + per-entry `confirmed_by`/`confirmed_on`.
- Both **validate the schema itself before trusting it**: FCDO runs SHACL-of-SHACL (`shacl-shacl.ttl`); DryDocs runs `pytest` gate tests (`test_gate_pages.py`, `test_classification.py`) and the load-map/enforcement-matrix renders.

**Where they differ (the interesting gaps)**

1. **State machine maturity.** DryDocs has a formal lifecycle (`proposed → confirmed → applied → rejected`) with routing rules (batch the obvious, pause the ambiguous) and precedence-conflict resolution. FCDO's HITL is a looser conversational "ask-before-assume" loop with a decision log — no explicit per-mapping status field or batching rule.
2. **Trust axis.** DryDocs separates *sensitivity* (External/Internal/Confidential publish boundary) from *trust* (VERBATIM/GROUNDED/SYNTHESIZED) and even enforces trust with a **DB boundary** (`drydocs_context` promotion is a gated write). FCDO has one analogous marker — the synthetic-example flag (`ex:syntheticData true`) — but no sensitivity/trust taxonomy.
3. **Provenance as first-class output.** DryDocs gate pages badge every property **SOURCE vs DERIVED**; its whole ontology is PROV-O-shaped (the graph *is* a provenance model). FCDO tracks provenance in prose (design-decisions + consistency report) rather than in the ontology's own semantics.
4. **Precedence / multi-source reconciliation.** DryDocs has `precedence.yaml` (BMC baseline → internal standards → LOB/Product/Team) to resolve source disagreement. FCDO handles multi-source reconciliation only as an ad-hoc design-decision theme.
5. **Direction of the standards.** FCDO models *data structure* (classes/attributes/constraints — a data-dictionary ontology). DryDocs models *operational behavior and lineage* (what ran, depends-on, who owns — a provenance/context ontology). They're complementary, not competing.

**Bottom line**

FCDO is a **front-end authoring skill** — it produces the *blueprint* (RDFS/OWL/SHACL). DryDocs is a **back-end ingestion + graph system** — it *builds and populates* the graph and adds the runtime/context layer FCDO doesn't attempt. If you ever needed a formal, publishable schema for the DryDocs ontology, FCDO's builder is exactly the tool to emit it; conversely, DryDocs' `proposed→confirmed→applied` state machine, precedence config, and trust-DB boundary are more mature governance machinery than FCDO's design-decisions log, and could inform hardening FCDO's HITL loop.

Want me to go deeper on any one axis — e.g. map FCDO's SHACL constraint patterns onto DryDocs' PROV matrix, or draft how FCDO's `design-decisions.md` could adopt DryDocs' status lifecycle?

Created 3 todos

> Review fcdo- directories (1/3)
> `+ artifact-handling.md`

*(gap between fcdo-ontology-builder2.png and fcdo-ontology-builder3.png — the remainder of the todo panel, the user's follow-up prompt, and the opening of the next response are not captured)*

## Part 3 — Follow-up: does FCDO fit the PAT source-onboarding flow?

### What "profile" means on each side (the crux)

The word means two different things, and the gap between them decides the fit.

**DryDocs profiling** (add-source-object Step 1) is *data* profiling: object type → column census → constraints/indexes → **stats/volume** → **grain check** → **value domains** → **cross-object join-coverage probes**. Output is *conclusions* — counts, null rates, distinct-value domains, match rates — never rows. For PAT that's "native Product Line ID is populated on X% of the 7,853 rows," "the role column has N distinct values," "the join to SEAL Application ID matches Y%."

**FCDO "profiling" is structural, not data.** The builder reads *structure* (DDL / JSON Schema / XSD / CSV headers / glossary) and proposes an ontology. It has **no** census/cardinality/grain/join-coverage step. Its one verification pass — `consistency_check.py` — round-trips *names* (source column ↔ ontology IRI), not data.

So FCDO cannot replace DryDocs' Step 1 profile. It's a **model-from-structure** tool, not a **profile-from-data** tool.

### Where it *does* fit PAT — and fits well

PAT-catalog is exactly the artifact class FCDO is strongest on: a **CSV, 27 columns, one-row-per-role-assignment**, encoding a 5-level hierarchy (LoB ▸ Sub-LoB ▸ Product Line ▸ Product ▸ Area Product ▸ Dev Team) + a role enumeration + native IDs at each level (`source-registry.yaml:247`).

FCDO's `references/artifact-handling.md` has **three** cookbooks that hit this dead-on:

- **Spreadsheet (entity + property)** and **glossary (no entity column)** → **cluster columns into classes** — precisely the denormalized-flat-table case.
- **Enumerations → SKOS Concept Scheme** — the role vocabulary becomes a proper `skos:ConceptScheme` instead of the hand-rolled lists DryDocs writes today.
- **Denormalization detection** (`home*`/`work*` → split `Address`) — the same reflex needed to lift the flat PAT row into the LoB→…→DevTeam class hierarchy with object properties.

Pointed at the PAT header (plus a few rows), FCDO would emit: classes for each catalog level + `RoleAssignment`/`Person`, object properties for the containment chain, a SKOS scheme for roles, SHACL shapes (native-id `sh:minCount 1`, role `sh:in`/`inScheme`), plus a `design-decisions.md` log and `generated-labels.xlsx` — a ready-made HITL review packet. The peer HTML-doc skill then renders it as a browsable data dictionary — a strong gate-review surface.

Notably there is no `config/source-mappings/pat-catalog.yaml` today (only Control-M ones exist), so FCDO's structural output could genuinely *seed* the PAT column ledger that Step 2 needs.

### Where it does *not* fit (the gaps you'd hit)

| Gap | Detail |
| --- | --- |
| **No data profiling** | Won't give counts, null rates, value domains, grain confirmation, or the SEAL join match-rate. You still run the oracle-db/csv probes for those. |
| **Wrong ontology target** | FCDO emits RDFS/OWL/SHACL/SKOS **files**. DryDocs is a **Neo4j property graph** shaped by PROV-O + a 9-row matrix + `relationship_vocabulary.yaml`. PAT maps to **W3C ORG** (`org:OrganizationalUnit`, `org:FormalOrganization`, the n-ary membership pattern) — FCDO doesn't know ORG/PROV/DPROD and would emit generic `owl:Class` / `ObjectProperty`. Its output must be *translated* into matrix/vocab terms — which is literally the `ontology-mapper` job. |
| **Grain blindness** | PAT's "one row per role assignment" is a fact-table grain. FCDO's denormalization logic is column-prefix heuristics, not grain/fact reasoning; left ungudied it may model every column as a `Person` attribute. Its ask-before-assume loop surfaces this, but not automatically. |
| **Publish boundary** | FCDO reads the CSV directly and, by default, emits example data from real rows. PAT rows carry SIDs/names → must stay in `internal`. DryDocs enforces mechanism-only; FCDO doesn't. You'd run it against a header-only/redacted extract and keep all outputs in `internal`. |
| **IRI convention** | FCDO hard-codes `https://vocabulary.jpmorgan/DataPublishing/<prefix>/`; DryDocs uses Neo4j labels + URN business keys. Cosmetic, but real translation friction. |

### Verdict

**Use FCDO as a structural-profiler / ontology-draft aid at add-source-object Step 3 — not as the Step 1 data profiler and not as a loader.**

Concrete PAT workflow that would actually pay off:

1. Run FCDO against a **header-only or redacted PAT extract** (kept in `internal`) → first-cut RDFS/OWL/SHACL/**SKOS** + `design-decisions.md`.
2. Keep DryDocs' **data-profile probes** (counts, domains, grain, SEAL join-coverage) as the Step 1 FCDO can't do.
3. **Translate** FCDO's classes/properties into DryDocs' PROV/ORG matrix terms + `relationship_vocabulary.yaml` entries (`status: planned`) and `taxonomy-ontology-map.yaml` (`status: proposed`).
4. Feed that into the **existing HITL gate** unchanged.

The two pieces reusable **as-is** with the least translation are the **SKOS role-vocabulary extraction** and the **HTML data-dictionary render**. Everything else is a draft that still has to be re-expressed in DryDocs' PROV/ORG vocabulary before it can load.

Want me to sketch what FCDO would actually emit for the PAT 27-column header (the class/property/SKOS breakdown) and show the side-by-side translation into DryDocs' ORG matrix terms?

Created 4 todos

---

## Gaps & Follow-ups

All 117 files in `C:\coding\@SCREEN-SHOTS` have been transcribed. What remains are gaps *in the screenshots themselves* — pages where the scroll capture started late, stopped early, or skipped a band between two shots.

**Second batch (H–V):**

- **H. Data Authority Metadata Framework** — §1–§4 not captured (the requirement lists that §5's "Requirement Section 4.3.A.n" references point back to); §6 Turtle example clipped mid-block; §9 References body missing.
- **I. Taxonomy Framework** — the largest hole in this batch. §1–§4 missing entirely, and the capture dies three rows into the first property table of §5.1.1. Everything from `dcterms:created` onward — the rest of the required concept properties, all optional/relational/mapping properties, and the whole of §5.2 `skos:ConceptScheme` — is uncaptured.
- **J. Taxonomy Information** (web app) — Customer Offering Products appears complete; Business Domains complete; **Business Subdomains is heavily truncated** — the header row is scrolled off, the first row is clipped, and the table cuts off at row 37 (Fraud Detection) with an unknown number of rows below.
- **L. Connecting a Physical Data Model to an Upper Ontology** — §3.8 (the class "overlaps" use case) and §4 Discussion not captured. The eight collapsed "Upper Ontology Model" / "Bridging Ontology Model" expandable panels were never expanded, so none of the actual model listings are in any shot.
- **N. Thought Pieces** — only one screenful of the child-page excerpt list; the FIBO positives/negatives comparison table is empty (tab labels only).
- **O. Technical Backlog** — clipped mid-sentence in the last Actionable Topic row.
- **U. People and Organizations Framework** — §6's worked Turtle examples break off two lines into example 6.1; §7 and §8 are missing entirely (only the stray "Additional Contacts | TBD" row survives).
- **V. FCDO Ontology Builder** — `SKILL.md` is cut off partway through Workflow Step 3; Steps 4–10 unseen. A band between shots 2 and 3 of the session is missing.

**A. Identifiers Specification** — ✅ complete, no gaps.

**D. Provenance Framework** — ✅ complete end to end. The one seam (middle rows of the §5.1.2 `prov:wasDerivedFrom` table, between shots `175312`/`175332`) is filled in from the CDAO WIP copy.

**E. [WIP] Provenance CDAO Framework** — page title, §1 Summary and §2 Changes not captured; several small seams mid-page. Not worth re-capturing unless the WIP page has diverged from its parent — the captured range is identical.

**F. Schema Metadata Framework** — the largest remaining hole:

- §1 Summary, §2 Changes from Previous Version, §3 (everything before §4).
- Between shots `181006` and `181055`: the tail of §6.3.2's RDFS/OWL listing, any §6.3.x subsections after it, and all of §6.4, §6.4.1 and §6.4.1.1.
- Everything after §6.4.1.3.1's first shape block — §7 (the schema-metadata-attributes example referenced from §4.4), §8 (extension procedure), and any appendices including "Appendix B" on the MagicDraw Concept Modeler mapping.

**G. Business Processes Metadata Framework**

- The rest of the §6.2 JSON-LD example.
- §6.3 KYC Verification Sub-process.
- §7 SHACL Verification.
- Appendix A in full (A.1 Client Onboarding, A.2 KYC Verification, A.3 Payments Exception Handling — Turtle format).

**B. Telemetry Framework**

- Everything before §4.3 (§1 Introduction through §4.2).
- Everything after the §5 intro (the actual Telemetry Components and Fields tables).

**C. Data Mapping Framework – Draft**

- §5.2.5 `jpmv:ModelElement` table: the *Subclass of* and *Usage note* rows fall between screenshots 6 and 7.
- §5.2.7.1 → §5.2.7.2: a small band between the Path Navigation RDF example and the Path Filtering heading (top of screenshot 8 is clipped).
- §7.4 Example 4: Cross-Technology Physical-to-Physical Mapping
- §7.5 Example 5: Logical-to-Conceptual Mapping
- §7.6 Example 6: Classification Mapping
- §8 SHACL Verification of Examples
- §9 Guiding Principles and Document Information
- §10 Appendix A: Mapping Type Concept Scheme

### Duplicate captures

- `Screenshot 2026-07-30 182209.png` is byte-identical to `DATAPPUBSTRATEGY-data-mapping-readme-model-layers.png` (both 307,203 bytes) — same view of the Data Mapping Framework – Draft page. Transcribed once, under section C.
- `open-telemetry-ss-1.png` is **not** an OpenTelemetry.io page — it is the JPMC **Telemetry Framework** Confluence page. Filed under its real URL as section B.

### Sources that are not Confluence

Five of the captures are not Confluence pages at all, and are filed under their real identity rather than guessed at:

- **J. Taxonomy Information** — the CCB Governance reference-data app (`ccb-governance.gaiacloud.jpmchase.net`), not a wiki page.
- **R. Application** — a OneNote-style note dated Tuesday, March 25 2025 8:41 AM, containing two ER diagrams mapping ServiceNow / SEAL / Verum as data sources.
- **S. About the model** — Neo4j's SDLC graph-model documentation (node-domain groupings for :Human, :Process, :Technical, :Knowledge, :Testing, :Web).
- **T. SCRAPE WEBPAGE CONTENT CHECK** — an AI tool-output panel analysing the ServiceNow CMDB class tree (1,235 classes split into IT vs business/logical).
- **V. FCDO Ontology Builder** — a `SKILL.md` file plus an AI coding-assistant session reviewing it against a system called "DryDocs". Despite the filename, `ont-bui.png` is the same skill, not a Confluence page.

Note also that **B (`open-telemetry-ss-1.png`) is the JPMC Telemetry Framework Confluence page**, not an OpenTelemetry.io page.

### Page-tree neighbours seen but never opened

The sidebar shows these sibling pages in *Firmwide Data Publishing Frameworks*, none of which were screenshotted: Process/Council and Working Groups · vteam Agent Ready Data · Descriptive Metadata Framework · Data Product Framework · Usage Rights Framework · Data Quality Framework · Date and Time Framework · Postal Address Framework · Party Identifier Framework · Knowledge Base Framework · Data Contracts Framework (DPROD). And under *Drafts and Upcoming Frameworks*: Taxonomy Framework · Data Contracts Framework · Data Authority Metadata Framework · Securities Framework · People and Organizations Framework · Companies Framework.

The Descriptive Metadata Framework is cross-referenced repeatedly by the pages above (it defines the shared Identifier / Title / Description properties) — that one is probably the highest-value next capture.

---

## Transcription notes

- Typos and inconsistencies in the source pages have been preserved verbatim. A partial list: "Usen when a model element…", "Ordering is retaind", "equivently", "Wharehouse", "ispecified", "ontolgy", "Framework Complaint" (Identifiers spec), the duplicated `ex:Customer_logical_model` block in Data Mapping §7.1, "not intentioned to specify tooling" and "oputput entity" (Provenance §3.2/§4.3), `rr:colum` vs `rr:column` in the OpenLineage Turtle, "datatypes can be declare" (Schema Metadata §6.4.1.2), and "compose hierarchies via shand and `sh:or`" (Schema Metadata §6.1 — "shand" is almost certainly a mangled `sh:and`).
- Section-numbering oddities preserved as-published: the Identifiers Specification numbers two consecutive sections "3.1" (UUID Example and Pathname Example); Provenance §5.2.4 cites requirement "C) g." where the list is B); Schema Metadata labels both `dcterms:title` and `dcterms:description` as "C) f." and places §6.4.1.4 immediately *before* §6.4.1.3.1.
- ASCII diagrams are reconstructions of the rendered images, not literal page text.
- Hyperlinked cross-references appear in **bold** where the source rendered them as links.
