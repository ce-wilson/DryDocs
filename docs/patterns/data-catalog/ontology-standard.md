# Enterprise Data Catalog — Ontology Standard

## Verdict: LinkedIn DataHub + DCAT v2 + OpenLineage

Enterprise data catalogs following the DataHub pattern compose three open standards:

| Layer | Standard | Signal |
|---|---|---|
| **Identity / URN** | LinkedIn `urn:li:*` scheme | `urn:li:dataset:`, `urn:li:dataPlatform:` |
| **Catalog vocabulary** | DCAT v2 (W3C) | Dataset, Distribution, DataService alignment |
| **Lineage events** | OpenLineage | DataFlow / DataJob entity types |
| **Classification** | Organization-specific namespace | `<OrgCatalog>:` classifier prefix |

DataHub is an open-source metadata platform (github.com/datahub-project/datahub).
The `urn:li:` prefix ("li" = LinkedIn) is the conclusive identifier that a catalog
is using DataHub or a DataHub-derived schema.

---

## DataHub Entity Model

| DataHub Entity | DryDocs Analogue | Key |
|---|---|---|
| `dataset` | `CatalogDataset` / STG_* table | `urn:li:dataset:{...}` |
| `dataDistribution` | `CatalogDistribution` | `urn:li:dataset:{platform...}` |
| `dataPlatform` | target system (Oracle/Snowflake/etc.) | `urn:li:dataPlatform:{type}` |
| **`dataFlow`** | **AppDataFlow (3rd Application child)** | `urn:li:dataFlow:{orchestrator,flowId,cluster}` |
| **`dataJob`** | **ControlMJob** | `urn:li:dataJob:{dataFlowUrn,jobId}` |
| `corpUser` | `Employee` | employee ID |
| `corpGroup` | `DevTeam` | group ID |
| `glossaryTerm` | `CatalogBusinessTerm` | term URN |
| `tag` | `CatalogTag` | tag URN |

**Key finding for orchestration integration:** DataHub's `dataFlow` entity directly
models an orchestration pipeline (folder/DAG level). Its `dataJob` children map
1:1 to Control-M jobs. This is the standard pattern for the 3rd child node under
`Application`.

---

## DCAT v2 Alignment

| DCAT v2 Class | DataHub / DryDocs Map |
|---|---|
| `dcat:Catalog` | DataHub itself |
| `dcat:Dataset` | `CatalogDataset` |
| `dcat:Distribution` | `CatalogDistribution` |
| `dcat:DataService` | `dataPlatform` |
| `dct:creator` | `CatalogWorker` (owner) |
| `dct:publisher` | `Application` (publisher) |

DataHub extends DCAT below the Distribution level with `Schema → Field → Element`
(column-level granularity). DCAT v2 does not define field-level concepts.

---

## OpenLineage Alignment

OpenLineage (openlineage.io) defines:
- `Job` — named, reusable processing unit (`namespace` + `name`)
- `Run` — specific execution of a Job (`runId`, `runState`)
- `Dataset` — input or output (`namespace` + `name`)
- `RunEvent` — emitted at START / COMPLETE / FAIL

**DryDocs Control-M job → OpenLineage Job mapping:**
```json
{
  "job": {
    "namespace": "<data-center-name>",
    "name": "<FOLDER_NAME>/<JOB_NAME>"
  },
  "inputs":  [{"namespace": "<source-platform>", "name": "<source-object-name>"}],
  "outputs": [{"namespace": "<target-platform>", "name": "<target-object-name>"}]
}
```

DryDocs can emit OpenLineage `RunEvent` payloads from its staging layer, making
its lineage consumable by DataHub, Marquez, OpenMetadata, Atlan, and any
OpenLineage-aware tool.

---

## URN Format Templates

### Dataset URN
```
urn:li:dataset:{urn:li:dataPlatform:{app-id},{object-type}-{object-uuid},{env}}
```

### Data Distribution URN
```
urn:li:dataset:{urn:li:dataPlatform:{platform-type},{platform-instance}.{namespace}.{object-name},{env}}
```

Platform types seen in enterprise deployments: `glue`, `snowflake`, `teradata`,
`databricks`, `oracle`, `sqlserver`, `s3`.

Environment values: `PROD`, `DEV`, `TEST`, `UAT`.

### DataFlow URN (orchestration pipeline)
```
urn:li:dataFlow:{orchestrator,flowId,cluster}
```
For Control-M: `orchestrator = "controlm"`, `flowId = folder/job-group name`,
`cluster = data-center name`.

---

## Classifier Taxonomy Standard

Organization-specific data classifiers are layered on DataHub's generic `tag` and
`glossaryTerm` systems using an internal namespace prefix (`<OrgCatalog>:`).

Common regulatory-driven classifier categories for financial institutions:
- **Privacy / PII:** Personal Information Indicator, Direct Identifier, Privacy Classifier
- **Payment:** Payment Card Industry (PCI-DSS) Indicator
- **Credit:** Credit Bureau / Consumer Report Classifier (FCRA)
- **Financial regulation:** MNPi Classifier (SEC/FINRA), Models Classifier
- **Data governance:** Confidentiality Classification, Data Use Classifier, Sub Line of Business
- **Protection:** Protection Enhancement, Protection Group Code, Data Protection Driver

See `classifiers-example.csv` for a full example taxonomy.

---

## What Orchestration Graphs Contribute That Catalogs Cannot

| Capability | DataHub | Orchestration Graph (DryDocs) |
|---|---|---|
| Dataset catalog | ✅ Full | Reference only |
| Job-level lineage (single platform) | ✅ Via OpenLineage | ✅ Native |
| **Cross-platform orchestration lineage** | ❌ | ✅ Only here |
| **File-based lineage** (FileWatcher triggers) | ❌ | ✅ |
| **Third-party feed tracking** | ❌ | ✅ |
| **Impact analysis** (downstream condition graph) | ❌ | ✅ |
| Governance metadata / classifiers | ✅ | Reference only |
| Application ownership hierarchy | Partial | ✅ Full (SEAL/RCC) |

The orchestration layer (Control-M, Airflow, Dagster) sees ALL cross-platform hops
because it orchestrates them. No catalog system has this because catalog systems
observe data AT REST, not data IN MOTION across platform boundaries.
