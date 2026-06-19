# DryDocs Graph Node Types

Use ONLY these node types during domain extraction. Do not introduce new labels.
Adding a new label requires an ontology supplement + constraint — that is out of
scope for the extractor skill.

---

## Active node types

| Label | Key property | PROV-O type | Domain | Description |
|---|---|---|---|---|
| `Application` | `seal_id` | `prov:Agent` | Application | Business application — SHARED bridge with data catalog |
| `AppDataFlow` | `dataflowUrn` | `prov:Activity` | Application | 3rd Application child; DataHub `dataFlow` analogue |
| `BatchProcess` | `appId` | `prov:Activity` | Application | Batch operations facet of Application |
| `EventProcess` | `appId` | `prov:Activity` | Application | Event-driven operations facet of Application |
| `ControlMJob` | `(folder_id, job_id)` | `prov:Activity` | Orchestration | Individual Control-M job / task |
| `ControlMFolder` | `folder_id` | `prov:Collection` | Orchestration | Job folder (label rename from `:JobFolder` in progress) |
| `ControlMServer` | `name` | `prov:Agent` | Orchestration | Execution server / data center host |
| `Condition` | `(folder_id, name)` | `prov:Entity` | Orchestration | Job dependency condition (in/out) |
| `DataAsset` | `assetId` | `prov:Entity` | Lineage | Named data object seen by the orchestration layer |
| `Employee` | `employee_id` | `prov:Agent` | Workforce | Person; reused for job owner/author attribution |
| `DevTeam` | `team_id` | `org:OrganizationalUnit` | Workforce | Development or support team |
| `AreaProduct` | `area_product_id` | `prov:Entity` | Org | Team-of-teams / area product group |
| `Product` | `product_id` | `prov:Entity` | Org | Business product |
| `JobRun` | `run_id` | `prov:Activity` | Provenance | Single execution of the load pipeline |
| `Membership` | `(seal_id, role_id)` | `org:Membership` | Workforce | Intermediate node: Application ↔ Employee |
| `CatalogDataset` | `dataset_urn` | — | Data Catalog | DataHub dataset; bridge target from DataAsset |

---

## DataAsset properties (fill these during extraction)

```
:DataAsset {
  assetId            STRING  UNIQUE  -- urn:drydocs:dataasset:{platform}:{namespace}:{name}
  name               STRING          -- table / file / object name
  platform           STRING          -- oracle | snowflake | teradata | s3 | sqlserver | linux
  namespace          STRING          -- schema / bucket / directory path
  env                STRING          -- PROD | DEV | TEST | UAT
  format             STRING          -- TABLE | FILE | VIEW | STREAM
  isExternalFeed     BOOLEAN         -- true = data originates outside the org's own jobs
  isSourceOfRecord   BOOLEAN         -- true = business-authoritative copy of this dataset
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

## Active relationship types

Use ONLY these. If a new edge type seems necessary, flag it as `[TO-BE-UPDATED]`
and discuss with the graph architect before adding it.

| Type | From | To | Notes |
|---|---|---|---|
| `HAS_DATA_FLOW` | Application | AppDataFlow | 3rd Application facet; NEW |
| `HAS_BATCH_PROCESS` | Application | BatchProcess | existing |
| `HAS_EVENT_PROCESS` | Application | EventProcess | existing |
| `ORCHESTRATES` | AppDataFlow | ControlMJob | pipeline → task; NEW |
| `USED` | ControlMJob | DataAsset | input; PROV-O `prov:used`; NEW |
| `GENERATED` | ControlMJob | DataAsset | output; PROV-O `prov:wasGeneratedBy`; NEW |
| `REPRESENTS_CATALOG_DATASET` | DataAsset | CatalogDataset | optional bridge; NEW |
| `CONTAINS_JOB` | ControlMFolder | ControlMJob | structural containment |
| `SCHEDULED_ON` | ControlMFolder | ControlMServer | scheduling (was `RUNS_ON` — migration in progress) |
| `REQUIRES_IN_CONDITION` | ControlMJob | Condition | job dependency (in-condition) |
| `EMITS_OUT_CONDITION` | ControlMJob | Condition | job dependency (out-condition) |
| `WAS_GENERATED_BY` | any | JobRun | PROV-O provenance — every node links to its load run |
| `HAS_MEMBERSHIP` | Application | Membership | org membership (intermediate node pattern) |
| `OF_ROLE` | Membership | Role | role in the membership |
| `HELD_BY` | Membership | Employee | person linked to membership |
| `WAS_ASSOCIATED_WITH` | ControlMJob | Employee | job attribution (role: owner/author/creator) |
| `SUPPORTS` | DevTeam | AreaProduct / Product | org support relationship |

**Edges marked NEW** are added by Stream C of the consolidated plan and may not
yet exist in the graph — check constraints before assuming they're present.
