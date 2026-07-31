# Thought pieces, AI-agent discussions & vocabulary — transcription set 3 of 4

*Part of the JPMC Confluence screenshot transcription set. Source screenshots live in `C:\coding\@SCREEN-SHOTS`; the unsplit master is `CONFLUENCE-TRANSCRIPT.md`.*

Discussion and position pieces on AI/agent-native data, plus the AWM Data Mesh vocabulary/glossary page. Screenshot groups: `thoughts`, `readme-agent-graph-rag`1–3, `vocab-1`–`vocab-4`, `conceptual-entity-diagram` (9 shots).

---

## Contents

| Section | Source | Type | Shots |
|---|---|---|---|
| 1 | Our Vocabulary | Confluence — **DATAMESHANALYTICS** space, `4373543268/Our+Vocabulary` | 5 |
| 2 | Thought Pieces (index of child-page excerpts) | Confluence — `https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5140788914/Thought+Pieces` | 1 |
| 3 | Discussion About The Possible Form of AI & Agent Native Data Benchmarks | Confluence — `https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5938531925/…` | 2 |
| 4 | Discussions on AI Agents for Managing Data Access | Confluence — `https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/6206552010/…` | 1 |

Note: **Our Vocabulary** is the only page in the entire capture set from a different Confluence space (DATAMESHANALYTICS, AWM Data Mesh Strategy) rather than DATAPUBSTRATEGY.

---

# Our Vocabulary

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

# Thought Pieces
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

# Discussion About The Possible Form of AI & Agent Native Data Benchmarks
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

# Discussions on AI Agents for Managing Data Access
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

## Gaps in this set

- **Thought Pieces** — only one screenful of the child-page excerpt list was captured. The FIBO *Positives / Negatives* comparison table shows column headers with no rows (tab labels only). The individual thought-piece child pages listed there were not opened, except the two AI-agent ones included here.
- **Discussion About … AI & Agent Native Data Benchmarks** — captured complete.
- **Discussions on AI Agents for Managing Data Access** — captured complete.
- **Our Vocabulary** — captured from the Official Sources section through the Decision Log / mesh workshop material.

---

## Transcription conventions

- Verbatim. Source typos, odd capitalisation and inconsistent section numbering are preserved, not corrected.
- Confluence property tables are rendered as Markdown tables; Turtle / JSON-LD / SHACL / SQL as fenced code blocks with original indentation.
- Rendered diagrams are described in a single italic `*Figure:` line capturing box and arrow labels.
- Overlaps between consecutive screenshots are de-duplicated; where the capture skipped a band, an italic `*(gap …)*` marker names what is missing.
- Sources that are not Confluence pages are labelled as such in their heading.
