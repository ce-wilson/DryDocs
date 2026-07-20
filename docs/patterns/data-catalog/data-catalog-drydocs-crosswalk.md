# Enterprise Data Catalog ↔ Process Orchestration Graph — Crosswalk

## Two planes, one bridge

The data catalog maps **DATA OBJECTS** (where data lives, what it contains, who
owns it). An orchestration knowledge graph (DryDocs) maps **PROCESSES** (the
jobs that produce, move, and transform that data). They are complementary — the
`Application` node (keyed by your organizational application ID) is the join point.

```
DATA CATALOG PLANE                     PROCESS GRAPH PLANE (DryDocs)
──────────────────────                 ──────────────────────────────
CatalogDistribution                    ControlMJob + DataAsset
  -[DATASET_OWNED_BY]-> Application <─── Application  (SHARED NODE)
CatalogWorker ◄──────────────────────── Employee
CatalogWorkerGroup ◄─────────────────── DevTeam
                                        AppDataFlow  ← DataHub dataFlow analogue
                                        ControlMJob  ← DataHub dataJob analogue
                                        DataAsset    ← DataHub dataset analogue
```

---

## §DATAHUB — 3rd Application Child Node Pattern

DataHub defines `dataFlow` and `dataJob` as first-class entities — the exact
pattern for the 3rd child node under `Application`:

```
DataHub:     corpGroup ──▶ dataFlow ──▶ dataJob ──▶ (consumes/produces) ──▶ dataset
DryDocs:   Application ──▶ AppDataFlow ──▶ ControlMJob ──▶ (USED/GENERATED) ──▶ DataAsset
```

DataHub URN: `urn:li:dataFlow:{orchestrator,flowId,cluster}`
DryDocs mapping: `orchestrator = "controlm"`, `flowId = folder/job-group name`,
`cluster = data-center name`

---

## §SHARED — Nodes that are the same real-world entity

| Catalog Label | Process Graph Label | Key | Bridge |
|---|---|---|---|
| `Application` | `Application` | organizational app ID | **Same node** — MERGE to the same key; no translation |
| `CatalogWorker` | `Employee` | worker_id / employee_id | Same person; bridge via shared ID or add label |
| `CatalogWorkerGroup` | `DevTeam` | group_id / team_id | Same team; bridge via org hierarchy |

**Implementation:** when loading catalog nodes, MERGE on the existing `Application`
node. Never create a `CatalogApplication` — the same node cluster serves both graphs.

---

## §ANALOGOUS — Same domain, different granularity

| Catalog Concept | Process Graph Analogue | Notes |
|---|---|---|
| `CatalogDataDomain` | `CatalogLOB` / `Product` | Domain = subject area; LOB = org unit; overlap at enterprise level |
| `CatalogDataset` | Staging tables (`STG_*`) | A staging table IS the dataset in the catalog |
| `CatalogDistribution` | `STG_LOAD_CONTROL` record | Distribution = WHERE data lives; load control = WHEN the job ran |
| `CatalogElement` | `STG_VARIABLE` (SEMANTIC_FACT) | SEMANTIC_FACT variables declare the same business attributes as Elements |
| `CatalogClassifier` | App-fact values in `STG_APP_FACT` | Same `<OrgCatalog>:` namespace in both — MERGE to shared `:CatalogClassifier` nodes |
| `CatalogDataProduct` | `Product` | Both are curated business products; same hierarchy |
| `CatalogTag` | No direct node yet | Tags are a good addition — reuse `CatalogTag` in the process graph |
| `CatalogBusinessTerm` | `relationship_vocabulary.yaml` entries | Both are controlled glossaries |
| `CatalogSchema` | Not modeled yet | Schema = dataset structure; process graph doesn't track columns today |
| `CatalogField` | Not modeled yet | Field = column; process graph tracks jobs/variables, not columns |

---

## §DIVERGE — Fundamental differences

| Dimension | Data Catalog | Process Graph (DryDocs) |
|---|---|---|
| **Primary object** | Dataset (data at rest) | ControlMJob (process) |
| **Lineage direction** | Data lineage (source → sink) | Process lineage (job dependencies) |
| **Ownership model** | Worker/WorkerGroup owns data | SEAL / Employee governs Application |
| **Quality governance** | DataContract + DataQualityRule | STG_PARSE_QUALITY + STG_COVERAGE_SUMMARY |
| **Lifecycle** | DataLifeCycleManagementPolicy | STG_LOAD_CONTROL (ingestion history) |
| **Identity scheme** | `urn:li:*` URNs | Composite keys (data_center, folder_id, job_id) |

---

## §BRIDGE — Cross-plane edges

When catalog and process graph share a Neo4j instance:

```cypher
// A job PRODUCES a cataloged dataset
(j:ControlMJob)-[:GENERATES]->(a:DataAsset)-[:REPRESENTS_CATALOG_DATASET]->(d:CatalogDataset)

// A job READS FROM a platform distribution
(j:ControlMJob)-[:USED]->(a:DataAsset)-[:REPRESENTS_CATALOG_DATASET]->(dist:CatalogDistribution)

// Application owns both the process (job) and the data (distribution)
(app:Application)-[:HAS_DATA_FLOW]->(flow:AppDataFlow)-[:ORCHESTRATES]->(j:ControlMJob)
(app:Application)<-[:DATASET_OWNED_BY]-(dist:CatalogDistribution)

// Employee is both a CatalogWorker and a job developer
(e:Employee)-[:WAS_ASSOCIATED_WITH {role:'author'}]-(j:ControlMJob)
// Either: MERGE CatalogWorker into Employee (add label)
// Or: (e:Employee)-[:SAME_IDENTITY]->(w:CatalogWorker)
```

---

## §CLASSIFIERS — Cross-graph classifier reuse

The `<OrgCatalog>:` classifier namespace appears in both the data catalog (applied
to Elements and Datasets) and potentially in process graph metadata (app-fact
values parsed from job variables). They are the same classification scheme.

**Pattern:** when parsing process metadata that contains `<OrgCatalog>:*` values,
MERGE them against `:CatalogClassifier` nodes to create a typed attribution edge:

```cypher
MATCH (job:ControlMJob)-[:HAS_APP_FACT]->(fact:AppFact)
WHERE fact.value STARTS WITH '<OrgCatalog>:'
MERGE (clf:CatalogClassifier {classifier_name: fact.value})
MERGE (job)-[:CLASSIFIED_BY]->(clf)
```

This connects process metadata to data governance metadata without duplication.

---

## §URN — URN adoption consideration

The data catalog uses DataHub `urn:li:*` keys. DryDocs uses composite keys
(`data_center`, `folder_id`, `job_id`). A compatible scheme for process nodes:

```
urn:drydocs:controlmjob:{data_center}:{folder_id}:{job_id}
urn:drydocs:folder:{data_center}:{folder_id}
urn:drydocs:dataasset:{platform}:{namespace}:{object_name}
```

This enables DryDocs catalog entries to be referenced by DataHub as external
lineage sources without sharing a database.

---

## §OQ — Open questions for alignment

1. Does your catalog system expose an API DryDocs can query to resolve Dataset
   URNs to Application IDs automatically?
2. Are `<OrgCatalog>:` classifiers available as a machine-readable registry
   (JSON/YAML) for direct ingestion?
3. Should `CatalogWorker` merge into `Employee` (same node, add label) or use
   a `SAME_IDENTITY` bridge edge?
4. Which team owns catalog ontology evolution — can they add `dataFlow` / `dataJob`
   entity types if not already present?
5. Is `CatalogDataDomain` mapped to the application product hierarchy, or is it
   a separate subject-area classification?
