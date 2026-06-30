---
name: data-context-extractor
description: "DryDocs domain context extractor. Adds platform, application, or organizational context to the DryDocs knowledge graph. Use when: (1) a target platform (Oracle, Snowflake, Teradata, S3, SQLServer, Linux, or reference documents) needs its data objects documented as DataAsset nodes, (2) a specific Application (by SEAL ID) needs its AppDataFlow and cross-platform lineage mapped, (3) the corporate hierarchy (BusinessSegment → CatalogLOB → ProductLine → Product → Application) needs inter-dependency queries answered, or (4) reference documents (PDF annual reports, 10-K filings) need content extracted into ddcontext as SYNTHESIZED DataAsset or BusinessSegment nodes. Outputs machine-first §META §DATAASSETS §JOBS §UC §CYPHER §OQ reference files. DO NOT generate SQL analyst skills, relational schemas, or any artifact that bypasses the Neo4j graph model."
---

# DryDocs Domain Context Extractor

Adds domain knowledge to the DryDocs knowledge graph — for a **target data
platform** (DataAsset nodes), an **Application domain** (AppDataFlow lineage),
or an **organizational/segment context** (BusinessSegment → LOB → Product chains
and inter-dependency queries). This skill replaces the generic SQL data analyst
skill builder.

---

## Critical constraints — read before every run

- **DO NOT generate SQL SKILL.md files.** Output is always machine-first graph
  reference docs in `§META §DATAASSETS §JOBS §UC §CYPHER §OQ` format.
- **DO NOT introduce new node types.** Only use labels already in the DryDocs
  ontology. See `references/nodes.md` for the complete list.
- **DO NOT introduce new relationship types.** Only use the edge vocabulary in
  `references/nodes.md §RELATIONSHIPS`. Flag unknowns as `[TO-BE-UPDATED]`.
- **Platform is always a property on `:DataAsset`, never a node.** Creating a
  `:DataPlatform` node with data edges causes a supernode — forbidden.
- **Sanitize before committing.** Internal versions (real SEAL IDs, server names,
  schema names) go to `drydocs/data/data-catalog/` (gitignored). Public sanitized
  versions go to `docs/patterns/data-catalog/`.
- **Document classification drives the target database.**
  - Public-domain documents (annual reports, 10-K SEC filings): `classification: External`,
    `trust: VERBATIM / GROUNDED`, load directly into `drydocs`. No sanitization needed.
    Always cite `source_url`.
  - Internal documents: `trust: SYNTHESIZED`, target `ddcontext` only.
    Never write to `drydocs` without HITL gate confirmation.

---

## Three modes

### Mode A — Platform Domain
Use when a target platform (Snowflake, Teradata, Oracle, S3, SQLServer, Linux,
or reference documents) needs to be documented so `:DataAsset` nodes can be
populated and lineage edges (`USED`/`GENERATED`) can be written by the DataAsset
loader. Valid `platform` values: `oracle | snowflake | teradata | s3 | sqlserver | linux | document`.

### Mode B — Application Domain
Use when a specific Application (identified by SEAL ID) needs its `:AppDataFlow`
and cross-platform lineage context documented.

### Mode C — Org Hierarchy / Segment Context
Use when you need to:
- Map **BusinessSegment → CatalogLOB → ProductLine → Product → Application** chains
- Answer inter-dependency questions: which apps/jobs belong to a segment? which
  teams support a product? what is the cross-segment blast radius?
- Extract business segment metrics from reference documents (annual reports, 10-K
  filings) into `ddcontext` as `trust: SYNTHESIZED` content

Mode C uses UC8–UC11 (`references/use-cases.md`) in addition to or instead of UC1–UC7.

All modes produce output in machine-first format (`references/domain-template.md`).

---

## Mode A — Platform Domain

### Step 1 — Identify the platform

Ask: "Which target platform are you documenting?"

Valid `platform` property values (these are string properties on `:DataAsset`, never
graph node labels or types):

`oracle` | `snowflake` | `teradata` | `s3` | `sqlserver` | `linux` | `document`

`document` = reference documents (PDF annual reports, 10-K filings, org charts).
Document DataAssets always carry `trust: SYNTHESIZED` and target `ddcontext`.

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

## Mode C — Org Hierarchy / Segment Context

### Step 1 — Identify the scope

Ask: "Are you documenting a segment, a LOB, a product line, or a product?"

Starting nodes and their keys:
- `BusinessSegment.code` — CCB / CIB / AWM / Corp / CB
- `CatalogLOB.lob_code` — internal LOB code
- `ProductLine.product_line_id` — product line identifier
- `Product.product_id` — product identifier

Run the schema discovery query first:
```cypher
MATCH (co:Company)-[:HAS_BUSINESS_SEGMENT]->(seg:BusinessSegment)
OPTIONAL MATCH (lob:CatalogLOB)-[:RECONCILES_TO]->(seg)
RETURN co.name, seg.code, seg.name, collect(lob.lob_code) AS lobs;
```

### Step 2 — Map inter-dependencies

For each scope node, capture:
- Which LOBs `RECONCILES_TO` each segment (with `confidence`)
- Which ProductLines and Products exist under each LOB
- Which Applications are owned by each Product (`HAS_APPLICATION`)
- Which AreaProducts and DevTeams are aligned under each Product (`HAS_AREA_PRODUCT` + `SUPPORTS`)
- Which Control-M jobs run under those applications

Use `references/use-cases.md` UC8–UC11 to drive the interview.

### Step 3 — Extract document metrics (optional)

If ingesting from a reference document:

**Public-domain documents (annual reports, 10-K SEC filings):**
- `classification: External` — no sanitization needed; data is in the public domain
- Model the document as `DataAsset {platform: 'document', trust: 'VERBATIM'}` for
  direct quotes, or `trust: 'GROUNDED'` for derived/calculated facts
- Always set `source_url` to the public filing URL
- Load directly into `drydocs` — no ddcontext staging required
- Carry extracted metrics as properties on `BusinessSegment` nodes in `drydocs`
- Write `GENERATED` edges: document → BusinessSegment, document → DataAsset (firmwide)

**Internal documents:**
- `classification: Internal-Public` or higher
- Model as `DataAsset {platform: 'document', trust: 'SYNTHESIZED'}`
- Target `ddcontext` only; promote to `drydocs` via HITL gate

### Step 4 — Generate output files

**Internal (gitignored, real LOB/product/team names):**
`drydocs/data/data-catalog/<segment-code>-context.md`

**Public (sanitized, committed):**
`docs/patterns/data-catalog/<segment-code>-context.md`

Use `references/domain-template.md` format. Mode C output replaces `§JOBS` with
`§HIERARCHY` (the LOB→Product→App chain) and adds a `§SEGMENTS` section.

---

## Output file locations

```
docs/patterns/data-catalog/            ← sanitized, public, committed to repo
├── <platform>-domain.md               ← Mode A output
├── <app-domain>-lineage.md            ← Mode B output
├── <segment-code>-context.md          ← Mode C output (sanitized)
└── (existing shared reference files already committed)

drydocs/data/data-catalog/             ← internal, gitignored, never committed
├── <platform>-domain.md               ← Mode A with real names/SIDs
├── <seal-id>-lineage.md               ← Mode B with real SEAL ID / team names
└── <segment-code>-context.md          ← Mode C with real LOB/product/team data
```

---

## Reference files

| File | Load when |
|---|---|
| `references/use-cases.md` | Starting the domain interview (UC1–UC7 for Mode A/B; UC8–UC11 for Mode C) |
| `references/nodes.md` | Choosing node types and properties during generation |
| `references/domain-template.md` | Writing the output reference file |
| `references/cypher-patterns.md` | Running discovery queries; Mode C patterns in §Mode C section |
| `references/platforms.md` | Checking platform URN patterns + sanitization rules |

---

## Quality checklist

### All modes
- [ ] Output format: machine-first `§META §DATAASSETS §JOBS §UC §CYPHER §OQ`
- [ ] No new node types introduced — only labels in `references/nodes.md`
- [ ] No new relationship types — only edges in `references/nodes.md §RELATIONSHIPS`
- [ ] All `[TO-BE-UPDATED]` markers replaced with actual domain-specific answers
- [ ] Sanitized public version: no real SEAL IDs, SIDs, server names, org names
- [ ] Internal version in `drydocs/data/data-catalog/` (gitignored)
- [ ] Public version in `docs/patterns/data-catalog/` committed to feature branch

### Mode A / B additional checks
- [ ] Platform is a property on `DataAsset`, not a graph node or label
- [ ] `assetId` URN: `urn:drydocs:dataasset:{platform}:{namespace}:{name}`
- [ ] `dataflowUrn` DataHub format: `urn:li:dataFlow:{controlm,<flowId>,<cluster>}`

### Mode C additional checks
- [ ] Segment codes verified against live graph: CCB / CIB / AWM / Corp (active), CB (retired)
- [ ] LOB → BusinessSegment `RECONCILES_TO` edges include `confidence` property
- [ ] `§HIERARCHY` section documents the full LOB → ProductLine → Product → App chain
- [ ] Cross-segment dependency queries (UC11) scoped to active segments only (no CB)
- [ ] **Public documents** (annual reports, 10-K): `classification: External`, `trust: VERBATIM/GROUNDED`, `source_url` set, load to `drydocs` — no sanitization, no ddcontext staging
- [ ] **Internal documents**: `trust: SYNTHESIZED`, `reliability` set (0.0–1.0), target `ddcontext` only
