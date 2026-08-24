# DryDocs Graph Node Types

Use ONLY these node types during domain extraction. Do not introduce new labels.
Adding a new label requires an ontology supplement + constraint — that is out of
scope for the extractor skill.

---

## Active node types

| Label | Key property | PROV-O / W3C type | Domain | Description |
|---|---|---|---|---|
| `Application` | `seal_id` | `prov:SoftwareAgent` | Application | SEAL-registered business application — SHARED bridge with data catalog |
| `AppDataFlow` | `dataflowUrn` | `prov:Activity` | Application | DataHub dataFlow analogue; 3rd Application child |
| `BatchProcess` | `appId` | `prov:Activity` | Application | Batch operations facet of Application |
| `EventProcess` | `appId` | `prov:Activity` | Application | Event-driven operations facet of Application |
| `ControlMJob` | `(folder_id, job_id)` | `prov:Activity` | Orchestration | Individual Control-M job / task |
| `ControlMFolder` | `folder_id` | `prov:Collection` | Orchestration | Job folder (label rename from `:ControlMFolder` in progress) |
| `ControlMServer` | `name` | local | Orchestration | Execution server / data center host (not a PROV Agent) |
| `Condition` | `(folder_id, name)` | `prov:Entity` | Orchestration | Job dependency condition (in/out) |
| `DataAsset` | `assetId` | `prov:Entity` | Lineage | Named data object seen by the orchestration layer |
| `Employee` | `employee_id` | `prov:Agent` | Workforce | Person; reused for job owner/author attribution |
| `DevTeam` | `team_id` | `org:OrganizationalUnit` | Workforce | Development or support team |
| `Membership` | `(seal_id, role_id)` | `org:Membership` | Workforce | Intermediate n-ary node: Application/DevTeam ↔ Employee |
| `Role` | `name` | `org:Role` | Workforce | Named role on a Membership |
| `Company` | `name` | `org:FormalOrganization` | Corporate | Top-level legal entity (e.g., JPMC) |
| `BusinessSegment` | `code` | `org:FormalOrganization` | Corporate | Corporate reporting segment (CCB / CIB / AWM / Corp); effective-dated |
| `CatalogLOB` | `lob_code` | `org:OrganizationalUnit` | Catalog | Catalog line of business; reconciles to a BusinessSegment |
| `ProductLine` | `product_line_id` | local (`dd:ProductLine`) | Catalog | Product-line grouping under a CatalogLOB |
| `Product` | `product_id` | local (`dd:Product`) | Catalog | Business product under a ProductLine |
| `AreaProduct` | `area_product_id` | local (`dd:AreaProduct`) | Catalog | Team-of-teams / Area Product Group under a Product |
| `JobRun` | `run_id` | `prov:Activity` | Provenance | Single execution of the load pipeline |
| `CatalogDataset` | `dataset_urn` | — | Data Catalog | DataHub dataset; bridge target from DataAsset |

---

## DataAsset properties (fill these during extraction)

```
:DataAsset {
  assetId            STRING  UNIQUE  -- urn:drydocs:dataasset:{platform}:{namespace}:{name}
  name               STRING          -- table / file / object name
  platform           STRING          -- oracle | snowflake | teradata | s3 | sqlserver | linux | document
  namespace          STRING          -- schema / bucket / directory path
  env                STRING          -- PROD | DEV | TEST | UAT
  format             STRING          -- TABLE | FILE | VIEW | STREAM | PDF | METRICS
  isExternalFeed     BOOLEAN         -- true = data originates outside the org's own jobs
  isSourceOfRecord   BOOLEAN         -- true = business-authoritative copy of this dataset
  trust              STRING          -- VERBATIM | GROUNDED | SYNTHESIZED (required on :Uncertain rows)
  reliability        FLOAT           -- 0.0–1.0 (required when trust = SYNTHESIZED)
}
```

**Platform is ALWAYS a property, never a graph node.** Do not create
`:DataPlatform` nodes with data edges — this creates a supernode that degrades
every traversal query through it.

---

## AppDataFlow properties (fill for Mode B)

```
:AppDataFlow {
  dataflowUrn    STRING  UNIQUE  -- urn:li:dataFlow:{controlm,<flowName>,<data_center>}
  appId          STRING          -- matches parent Application.seal_id
  flowName       STRING          -- Control-M folder or job-group name
  orchestrator   STRING          -- always 'controlm'
  cluster        STRING          -- data center name (from ControlMServer.name)
}
```

---

## BusinessSegment properties (fill for Mode C)

```
:BusinessSegment {
  code              STRING  UNIQUE  -- CCB | CIB | AWM | Corp | CB
  name              STRING          -- full segment name
  retired           BOOLEAN         -- true = pre-reorg segment no longer active
  -- Metric properties (SYNTHESIZED — the node carries :Uncertain, never bare)
  roe_{year}        FLOAT           -- return on equity for a given year
  metric_year       INTEGER         -- year the metrics apply to
  metric_source     STRING          -- source doc + page reference
  trust             STRING          -- SYNTHESIZED when carrying extracted metrics
  reliability       FLOAT           -- 0.0–1.0
}
```

## CatalogLOB properties (fill for Mode C)

```
:CatalogLOB {
  lob_code          STRING  UNIQUE  -- internal LOB code (e.g. 'R', 'S', 'K', 'B')
  name              STRING          -- LOB display name
  reconciles_to     STRING          -- BusinessSegment.code this LOB maps to (denorm ref)
}
```

## ProductLine / Product / AreaProduct properties (fill for Mode C)

```
:ProductLine {
  product_line_id   STRING  UNIQUE
  name              STRING
  lob_code          STRING          -- parent CatalogLOB.lob_code
}

:Product {
  product_id        STRING  UNIQUE
  name              STRING
  product_line_id   STRING          -- parent ProductLine.product_line_id
}

:AreaProduct {
  area_product_id   STRING  UNIQUE
  name              STRING
  product_id        STRING          -- parent Product.product_id
}
```

---

## Active relationship types

Use ONLY these. If a new edge type seems necessary, flag it as `[TO-BE-UPDATED]`
and discuss with the graph architect before adding it.

### Orchestration / lineage edges
| Type | From | To | Notes |
|---|---|---|---|
| `HAS_DATA_FLOW` | Application | AppDataFlow | 3rd Application facet |
| `HAS_BATCH_PROCESS` | Application | BatchProcess | existing |
| `HAS_EVENT_PROCESS` | Application | EventProcess | existing |
| `ORCHESTRATES` | AppDataFlow | ControlMJob | pipeline → task |
| `USED` | ControlMJob | DataAsset | input (prov:used) |
| `GENERATED` | ControlMJob / DataAsset | DataAsset / BusinessSegment | output (prov:generated); also document→fact |
| `REPRESENTS_CATALOG_DATASET` | DataAsset | CatalogDataset | optional DataHub bridge |
| `CONTAINS_JOB` | ControlMFolder | ControlMJob | structural containment |
| `SCHEDULED_ON` | ControlMFolder | ControlMServer | scheduling placement |
| `REQUIRES_IN_CONDITION` | ControlMJob | Condition | job dependency (in-condition) |
| `EMITS_OUT_CONDITION` | ControlMJob | Condition | job dependency (out-condition) |
| `WAS_GENERATED_BY` | any | JobRun | PROV-O provenance — every node links to its load run |

### Workforce / membership edges
| Type | From | To | Notes |
|---|---|---|---|
| `HAS_MEMBERSHIP` | Application / DevTeam | Membership | org membership (n-ary node pattern) |
| `OF_ROLE` | Membership | Role | role in the membership |
| `HELD_BY` | Membership | Employee | person linked to membership |
| `WAS_ASSOCIATED_WITH` | ControlMJob | Employee | job attribution (role: owner/author/creator) |

### Corporate / catalog hierarchy edges (Mode C)
| Type | From | To | Notes |
|---|---|---|---|
| `HAS_BUSINESS_SEGMENT` | Company | BusinessSegment | effective-dated; carries `effective_from`, `effective_to` |
| `RECONCILES_TO` | CatalogLOB | BusinessSegment | LOB→segment crosswalk; carries `confidence` (0.0–1.0) |
| `HAS_PRODUCT_LINE` | CatalogLOB | ProductLine | catalog hierarchy — LOB contains product lines |
| `HAS_PRODUCT` | ProductLine | Product | catalog hierarchy — product line contains products |
| `HAS_APPLICATION` | Product | Application | structural support link — the applications supporting a product, 1:many by design (planned) |
| `HAS_AREA_PRODUCT` | Product | AreaProduct | product contains Area Product Groups (planned) |
| `HAS_DEV_TEAM` | Product / AreaProduct | DevTeam | product or APG owns a dev team |
| `SUPPORTS` | DevTeam | AreaProduct | confirmed range: AreaProduct (not Product); carries `team_type`, `sponsored` |
| `DEVELOPS` | DevTeam | Application | dev team develops an application (HITL-confirmed 2026-06-21) |
