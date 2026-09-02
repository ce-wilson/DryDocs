# Full Circle Docs (FCD) — MVP Requirements & Design (2018)

> **Historic origin document — the genesis of DryDocs.**
> *Full Circle Docs (FCD)* was the original name for this project, authored by Chad Wilson,
> **v1.0, 2018-03-12**. It was later renamed **DryDocs** after the Python **DRY — "Don't Repeat
> Yourself"** principle: the doc's core idea is precisely DRY *for documentation* — never re-write
> a whole document per change; edit only the pieces that change against a versioned graph, and
> retain the business context.
>
> This is a faithful, lightly reformatted markdown rendering of the 2018 original. The only content
> removed is the Word-template footer chrome (a generic corporate document-template header/footer); no
> substantive content was changed. Preserved as the project's foundational use-case / MVP
> requirements record. The original binary `.doc` is kept local-only (carries the template chrome).

---

## 1. Introduction

The intent is to create a Single-Tenant or Multi-Tenant container service that supports the
documentation needs of any large-scale enterprise software project like a data warehouse. It will be
a new hybrid documentation process and repository that works with both **Agile and Waterfall**
development models.

The **first objective** is to take a customer's existing documentation — whether Word or Excel — and
convert it into a documentation database, templated to show the same information in a new web portal.
The **second objective** is to integrate with existing code repositories, third-party applications,
and databases. A subset of data from the code, requirements, and test cases is used to link the
documentation database to the corresponding development component.

Once both objectives are met, the time spent documenting changes and new processes should drop
dramatically. The analyst or developer no longer creates a new document with each change — they pull
out only the pieces changing, identify the corresponding process and code, then keep a versioned
history of the changes. As the business evolves, update / retire / archive the code as well as the
document, focusing on what is needed while retaining the business context. The business &
application context can be linked to infrastructure mapping, creating the source-data relationship
map.

### 1.1 Goals
- Create a working web portal as a first proof of concept to show potential customers or investors.
- Identify the technical and systems framework needed for a Single-Tenant or Multi-Tenant service.
- Estimate future development efforts and operating costs, and possible pricing options.

### 1.2 Scope
- **In scope:** high-level features needed for a minimum viable product — tagged `[MVP]`.
- **Out of scope:** high-level features that require extensive coding — tagged `[TBD]`.

## 2. Technical Framework
*[Placeholder — this POC will identify the Technical Framework.]* In general, the technical
environment specifications and constraints would be described here. Associated URL: `fullcircledocs.com`.

## 3. System Framework
*[Placeholder — this POC will identify the System Framework.]* Defines the overall design
specifications and the interfaces between automated and manual subsystems that form the systems
architecture.

## 4. Usage Scenario

### 4.1 Actors & Use Cases

**Super Administrator (1st-tier admin)**
1. Container maintenance and all company-level functions.
2. Initial company setup.
3. Create business and technical requirement templates.

**Company Administrator (2nd-tier admin)** — company-level configuration
4. Set up project.
5. Set up users (secondary actors).
6. Modify integrations, logins, and connections (GIT, JIRA, etc.).
7. Import code repository to create base code nodes.
8. Import database schema to create base table and procedure nodes.
9. Modify requirement templates.

**Stakeholders** — read-only; placeholder for notifications and reports.

**Project Manager** — read-only; placeholder for notifications and reports.

**Business or Systems Analyst (primary user)**
13. Create requirements based on a template — new or from a backlog item; select team members;
    create or modify business-flow diagram.
14. Query for existing requirements.
15. Print formatted requirements.
16. Create or modify use cases.
17. Assign or modify "Major Process / Sub-Process".
18. Add sample queries; modify SQL for actual results.

**Developer**
19. Query for existing requirements.
20. Create new technical requirements based on business requirements.
21. Assign or modify "Major Process / Sub-Process".
22. Create or modify data-flow diagram (similar to an ERD).
23. Identify & select tables, procedures, code to be updated.
24. Create `_TMP` objects when a new object (node) is needed.
25. Add sample code.
26. Create individual `SELECT` statements to validate data.
27. Perform a "Sync" to the bug / issue tracker for all issues related to code being changed.

**QA Tester**
28. Query for existing requirements.
29. Query for test cases based on process.
30. Query for test cases based on affected code.
31. If a test suite exists, "Sync", then verify requirements are traced to test cases.
32. If no testing suite exists, create new test cases.
33. *[Insert SOX audit requirements here.]*

**Release Manager**
34. Query for requirements, code, released items.
35. Sync with GIT / databases for changed objects and create a diff with the release (audit report).

### 4.2 Implementation Design
*[Placeholder — this POC will identify the Implementation Design.]* Documentation for this section
includes (but is not limited to): Implementation Specification, inter-unit / external module
interface design, external interface design. For each implementation module: identification &
purpose; inputs (files, screens, on-line queues); outputs (files, screens, queues, reports); linkage
section (to other modules); programming constraints; processing functions; module complexity level.

### 4.3 Technical Data Design
*[Placeholder.]* Two major specifications: Physical Data Model packet; DBMS database and view
definitions. Available in some instances via a Data Dictionary / Data Storage (DD/DS) or a simplified
modeling tool like this one.

### 4.4 Development Dependencies
Describes the interdependencies between components of the integrated system.

## 5. Unit Test Specifications

The TSD document covers major test phases (Integration, Systems, Performance, User Acceptance,
Post-production). Unit testing may be documented here.

- **5.1 Unit Test Framework** — hardware/software required for testing; tools and computer-operations
  support during the testing period.
- **5.2 Unit Test Design Specifications** — per-test design: Test Identifier, Features to be Tested,
  Testing Approach, Pass/Fail Criteria, Test Procedure, Expected Test Results.

## 6. Conversion System Design

### 6.1 Conversion Framework
*[Placeholder.]* Identifies the hardware, software, user operational requirements, and technical
constraints during conversion. For the MVP, the approach is a combination of manual tasks and
existing tool sets.

- *Initial thought:* Jenkins is a multi-application integration tool — can it serve as the interface
  engine for this platform?
- Initial population is manual: copy data from existing documentation and recreate it in the POC
  (e.g., build a template from an existing requirement doc, then populate via copy & paste). Direct
  import is preferred, but implemented later as a feature.
- Tooling references (all public): Neo4j RDBMS→graph ETL tool; SchemaCrawler
  (`sualeh.github.io/SchemaCrawler`); MySQL→Neo4j migration; a small POC to import a JIRA database
  into Neo4j.

### 6.2 Conversion Implementation Design
*[Placeholder — this POC will identify the Conversion Design.]*

## 7. Full Circle MVP Brief and FAQ

Basic outline of the app to ensure the major features are documented and to capture questions or
inconsistencies early. Includes: brief description of platform components; actors (examples to
modify as needed); a parsimonious MVP summary; and an FAQ probing each persona — how is the account
created, what does the user see before/after first login and as a regular user, what is the user
feeling, why are they using the app, who pays whom, is security important, which actions should be
tracked (internally or via a 3rd-party analytics tool).

## Appendices

### A.1 Unit Test Case Specifications
For each test case: Test Case Identifier; Input Specifications; Expected Results; Environmental
Requirements; Procedural Requirements; Prerequisites. Enough cases to exercise all system functions
and responses to external and internal business conditions.

### A.2 Thoughts and Ideas (uncategorized)
- Portal: template-based editor — LaTeX? GitBooks?
- Backend: data flows like draw.io / arrows.
- Word compatibility; suggested font: Source Sans Pro.
- Show code blocks like Stack Overflow (light-grey background, syntax highlighting, scrolling).

### A.3 Competition
Example of a one-page PRD (e.g., a fully fleshed-out product requirements document built in
Confluence). No two PRDs are identical — use such examples to understand the elements a PRD should
include, not as the definitive way to do it.

---

*Original: Full Circle Docs — MVP Requirements & Design, v1.0, 2018-03-12, Chad Wilson. Reformatted to
markdown for the DryDocs history; corporate Word-template chrome removed, substance preserved.*
