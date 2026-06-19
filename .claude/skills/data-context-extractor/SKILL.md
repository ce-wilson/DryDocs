---
name: data-context-extractor
description: "DryDocs domain context extractor. Adds platform or application domain knowledge to the DryDocs knowledge graph for DataAsset node population and AppDataFlow lineage mapping. Use when: (1) a target platform (Oracle, Snowflake, Teradata, S3, SQLServer, Linux) needs its key data objects documented as DataAsset nodes, (2) a specific Application (by SEAL ID) needs its AppDataFlow and cross-platform lineage mapped, (3) interviewing a domain expert using DryDocs use case questions. Outputs machine-first §META §DATAASSETS §JOBS §UC §CYPHER §OQ reference files. DO NOT generate SQL analyst skills, relational schemas, or any artifact that bypasses the Neo4j graph model."
---

# DryDocs Domain Context Extractor

Adds domain knowledge to the DryDocs knowledge graph — either for a **target data
platform** (to populate `:DataAsset` nodes) or for an **Application domain** (to
populate `:AppDataFlow` lineage). This skill replaces the generic SQL data analyst
skill builder.

---

## Critical constraints — read before every run

- **DO NOT generate SQL SKILL.md files.** Output is always machine-first graph
  reference docs in `§META §DATAASSETS §JOBS §UC §CYPHER §OQ` format.
- **DO NOT introduce new node types.** Only use labels already in the DryDocs
  ontology. See `references/nodes.md` for the complete list.
- **DO NOT introduce new relationship types.** Only use: `USED`, `GENERATED`,
  `ORCHESTRATES`, `HAS_DATA_FLOW`, `REPRESENTS_CATALOG_DATASET`, and the existing
  DryDocs edge vocabulary in `references/nodes.md §RELATIONSHIPS`.
- **Platform is always a property on `:DataAsset`, never a node.** Creating a
  `:DataPlatform` node with data edges causes a supernode — forbidden.
- **Sanitize before committing.** Internal versions (real SEAL IDs, server names,
  schema names) go to `drydocs/data/data-catalog/` (gitignored). Public sanitized
  versions go to `docs/patterns/data-catalog/`.

---

## Two modes

### Mode A — Platform Domain
Use when a target platform (Snowflake, Teradata, Oracle, S3, SQLServer, Linux)
needs to be documented so `:DataAsset` nodes can be populated and lineage edges
(`USED`/`GENERATED`) can be written by the DataAsset loader.

### Mode B — Application Domain
Use when a specific Application (identified by SEAL ID) needs its `:AppDataFlow`
and cross-platform lineage context documented.

Both modes use the same 7 interview questions (`references/use-cases.md`) and
produce output in machine-first format (`references/domain-template.md`).

---

## Mode A — Platform Domain

### Step 1 — Identify the platform

Ask: "Which target platform are you documenting?"

Valid `platform` property values (these are string properties on `:DataAsset`, never
graph node labels or types):

`oracle` | `snowflake` | `teradata` | `s3` | `sqlserver` | `linux`

See `references/platforms.md` for URN patterns and sanitization rules per platform.

### Step 2 — Identify key data objects

Ask: "Which 3–5 tables, files, or schemas do Control-M jobs most often read from
or write to on this platform?"

For each object, capture the `references/domain-template.md §DATAASSETS` fields:

| Field | Graph property | Ask the domain expert |
|---|---|---|
| Object name | `DataAsset.name` | "What is the table or file name?" |
| Schema/bucket/path | `DataAsset.namespace` | "What schema or directory path contains it?" |
| Format | `DataAsset.format` | TABLE / FILE / VIEW / STREAM |
| External feed? | `DataAsset.isExternalFeed` | "Does this originate outside your org's own jobs?" |
| Source of record? | `DataAsset.isSourceOfRecord` | "Is this the business-authoritative copy of this data?" |

Construct `assetId` as:
```
urn:drydocs:dataasset:{platform}:{namespace}:{name}
```

### Step 3 — Interview using DryDocs use case questions

Work through `references/use-cases.md` for this platform's objects. For each UC:
- "Which jobs PRODUCE (GENERATED) objects on this platform?"
- "Which jobs CONSUME (USED) objects on this platform?"
- Capture `(job → direction → asset)` triples

### Step 4 — Generate output files

**Internal (gitignored, real names):**
`drydocs/data/data-catalog/<platform>-domain.md`

**Public (sanitized, committed):**
`docs/patterns/data-catalog/<platform>-domain.md`

Use `references/domain-template.md` format exactly. Run `§SANITIZE` checklist
before writing the public version.

---

## Mode B — Application Domain

### Step 1 — Identify the Application

Ask: "What is the SEAL ID (organizational application ID) for this Application?"

Run discovery query to see current graph state:
```cypher
MATCH (app:Application {seal_id: $sealId})
OPTIONAL MATCH (app)-[:HAS_BATCH_PROCESS]->(bp:BatchProcess)
OPTIONAL MATCH (app)-[:HAS_EVENT_PROCESS]->(ep:EventProcess)
OPTIONAL MATCH (app)-[:HAS_DATA_FLOW]->(flow:AppDataFlow)
RETURN app, bp, ep, flow
```

### Step 2 — Map the data flow

Ask: "What do this application's Control-M jobs do — what data do they read, and
what do they produce?"

For each job group or Control-M folder:
- `AppDataFlow.flowName` → descriptive name of the pipeline / folder
- `AppDataFlow.dataflowUrn` → `urn:li:dataFlow:{controlm,<flowName>,<data_center>}`
- Inputs → `DataAsset {isExternalFeed: ?}` ←`[:USED]`← ControlMJob
- Outputs → ControlMJob →`[:GENERATED]`→ `DataAsset {isSourceOfRecord: ?}`

### Step 3 — Interview using DryDocs use case questions

Work through `references/use-cases.md` scoped to this application and its
platforms. All 7 UC questions apply; focus on UCs most relevant to this domain.

### Step 4 — Generate output files

**Internal:** `drydocs/data/data-catalog/<seal-id>-lineage.md`
**Public:** `docs/patterns/data-catalog/<app-domain>-lineage.md`

---

## Output file locations

```
docs/patterns/data-catalog/            ← sanitized, public, committed to repo
├── <platform>-domain.md               ← Mode A output
├── <app-domain>-lineage.md            ← Mode B output
└── (existing shared reference files already committed)

drydocs/data/data-catalog/             ← internal, gitignored, never committed
├── <platform>-domain.md               ← Mode A with real names/SIDs
└── <seal-id>-lineage.md               ← Mode B with real SEAL ID / team names
```

---

## Reference files

| File | Load when |
|---|---|
| `references/use-cases.md` | Starting the domain interview (UC1–UC7 questions) |
| `references/nodes.md` | Choosing node types and properties during generation |
| `references/domain-template.md` | Writing the output reference file |
| `references/cypher-patterns.md` | Running discovery queries in Neo4j Browser |
| `references/platforms.md` | Checking platform URN patterns + sanitization rules |

---

## Quality checklist

- [ ] Output format: machine-first `§META §DATAASSETS §JOBS §UC §CYPHER §OQ`
- [ ] No new node types introduced — only labels in `references/nodes.md`
- [ ] No new relationship types — only edges in `references/nodes.md §RELATIONSHIPS`
- [ ] Platform is a property on `DataAsset`, not a graph node or label
- [ ] `assetId` URN: `urn:drydocs:dataasset:{platform}:{namespace}:{name}`
- [ ] `dataflowUrn` DataHub format: `urn:li:dataFlow:{controlm,<flowId>,<cluster>}`
- [ ] All `[TO-BE-UPDATED]` markers replaced with actual domain-specific answers
- [ ] Sanitized public version: no real SEAL IDs, SIDs, server names, org names
- [ ] Internal version in `drydocs/data/data-catalog/` (gitignored)
- [ ] Public version in `docs/patterns/data-catalog/` committed to feature branch
