# Ontology — transcription set 1 of 4

*Part of the JPMC Confluence screenshot transcription set. Source screenshots live in `C:\coding\@SCREEN-SHOTS`; the unsplit master is `CONFLUENCE-TRANSCRIPT.md`.*

Everything covering ontology design, upper-ontology bridging, and the FCDO ontology-builder tooling. Screenshot groups: `ontologydesign-readme`, `ont-1`–`ont-4`, `ont-bui`, `fcdo-ontology-builder`1–4 (10 shots).

---

## Contents

| Section | Source | Type | Shots |
|---|---|---|---|
| 1 | Ontology Design Recommendations | Confluence — Thought Pieces child | 1 |
| 2 | Connecting a Physical Data Model to an Upper Ontology | Confluence — `https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5648554621/…` | 4 |
| 3 | FCDO Ontology Builder — SKILL.md + review session | **Not Confluence** — skill file + AI assistant session | 5 |

---

# Ontology Design Recommendations
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

---

# Connecting a Physical Data Model to an Upper Ontology
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

# FCDO Ontology Builder — skill definition and review session  *(not Confluence)*

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

## Gaps in this set

- **Connecting a Physical Data Model to an Upper Ontology** — §3.8 (the class "overlaps" use case) and §4 Discussion were not captured. Critically, the eight collapsed *Upper Ontology Model* / *Bridging Ontology Model* expandable panels were never expanded, so none of the actual model listings exist in any screenshot. If this page matters for the review, re-capture with those panels open.
- **FCDO Ontology Builder** — `SKILL.md` is cut off partway through Workflow Step 3; Steps 4–10 (generate JSON-LD, SHACL-of-SHACL validation, example validation, consistency check, iterate, HTML docs) are unseen. A band between session shots 2 and 3 is also missing.
- **Ontology Design Recommendations** — appears complete in its single shot.

---

## Transcription conventions

- Verbatim. Source typos, odd capitalisation and inconsistent section numbering are preserved, not corrected.
- Confluence property tables are rendered as Markdown tables; Turtle / JSON-LD / SHACL / SQL as fenced code blocks with original indentation.
- Rendered diagrams are described in a single italic `*Figure:` line capturing box and arrow labels.
- Overlaps between consecutive screenshots are de-duplicated; where the capture skipped a band, an italic `*(gap …)*` marker names what is missing.
- Sources that are not Confluence pages are labelled as such in their heading.
