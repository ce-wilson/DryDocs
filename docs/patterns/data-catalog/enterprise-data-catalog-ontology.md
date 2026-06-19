# Enterprise Data Catalog — Machine-First Ontology Reference

<!-- §META -->
```yaml
standard: LinkedIn DataHub entity model + DCAT v2 + OpenLineage
version: 0.1
status: REFERENCE
note: Replace <OrgCatalog> and <org-id> placeholders with your organization's values
```

---

## §SCHEMA — Overview

Five visual domains in a DataHub-aligned enterprise data catalog:

| Domain | Role |
|---|---|
| **Business Data Catalog** | Core: Dataset, DataProduct, DataDomain, Element, Field, Schema, DataDistribution, Tag, Classifier |
| **Workforce** | Ownership: Worker, WorkerGroup |
| **Business Glossary** | Semantics: ValidValue, BusinessTerm, EncodingInstance |
| **Data Quality** | Quality governance: DataContract, DataQualityRule |
| **Application** | Consuming/owning system — shared node with process orchestration graph |

**Hub node:** `DataDistribution` — the physical instantiation of a Dataset on a
platform. All ownership, lifecycle, policy, and application edges flow through it.

---

## §NODES — Node Types

### Business Data Catalog

| Label | Key Property | Description |
|---|---|---|
| `CatalogDataset` | `dataset_urn` | Logical dataset; primary catalog object |
| `CatalogDistribution` | `distribution_urn` | Physical instantiation on a platform |
| `CatalogDataProduct` | `data_product_id` | Curated product from one or more datasets |
| `CatalogDataDomain` | `domain_id` | Subject-area grouping; top-level data partition |
| `CatalogElement` | `element_id` | Logical data element (field-level concept) |
| `CatalogField` | `field_id` | Physical field implementing an Element in a Schema |
| `CatalogSchema` | `schema_id` | Physical schema grouping Fields |
| `CatalogTag` | `name` | Free-form or system-controlled tag |
| `CatalogClassifier` | `classifier_name` | `<OrgCatalog>:` controlled-vocabulary attribute |
| `CatalogLifecyclePolicy` | `policy_id` | Retention/disposition policy for a Distribution |

### Workforce

| Label | Key Property | Description |
|---|---|---|
| `CatalogWorker` | `worker_id` | Individual; maps to process graph `:Employee` |
| `CatalogWorkerGroup` | `group_id` | Team/group; maps to process graph `:DevTeam` |

### Business Glossary

| Label | Key Property | Description |
|---|---|---|
| `CatalogBusinessTerm` | `term_id` | Canonical business definition |
| `CatalogValidValue` | `value_id` | Allowed enumeration value |
| `CatalogEncodingInstance` | `encoding_id` | Code encoding for a term's value set |

### Data Quality

| Label | Key Property | Description |
|---|---|---|
| `CatalogDataContract` | `contract_id` | Formal data quality contract |
| `CatalogDataQualityRule` | `rule_id` | Quality rule within a contract |

### Shared (bridge to process graph)

| Label | Key Property | Description |
|---|---|---|
| `Application` | `app_id` | Business application — **same node** in both catalog and process graph; keyed by organizational application ID (e.g., SEAL/RCC) |

---

## §EDGES — Relationship Types

### Ownership

| From | Relationship | To |
|---|---|---|
| `CatalogDataDomain` | `OWNED_BY` | `CatalogWorker` / `CatalogWorkerGroup` |
| `CatalogDistribution` | `OWNED_BY` | `CatalogWorker` / `CatalogWorkerGroup` |
| `CatalogDistribution` | `DATASET_OWNED_BY` | `Application` |
| `CatalogDistribution` | `DATASET_PUBLISHED_BY` | `Application` |
| `CatalogDistribution` | `PUBLISHED_BY` | `Application` |
| `CatalogDataProduct` | `OWNED_BY` | `CatalogWorkerGroup` |
| `CatalogDataset` | `OWNED_BY` | `CatalogWorker` / `CatalogWorkerGroup` |
| `CatalogWorkerGroup` | `HAS_MEMBER` | `CatalogWorker` |

### Catalog structure

| From | Relationship | To |
|---|---|---|
| `CatalogDataset` | `BELONGS_TO` | `CatalogDataDomain` |
| `CatalogDataset` | `IS_PART_OF` | `CatalogDataProduct` |
| `CatalogDataset` | `IMPLEMENTED_ON` | `CatalogDistribution` |
| `CatalogDataset` | `HAS` | `CatalogElement` |
| `CatalogSchema` | `HAS` | `CatalogField` |
| `CatalogElement` | `IS_IMPLEMENTED_AS` | `CatalogField` |
| `CatalogElement` | `IS_REPRESENTED_AS` | `CatalogBusinessTerm` |

### Tagging

All catalog object types support: `(:AnyNode)-[:IS_TAGGED_WITH]->(:CatalogTag)`

### Classification

| From | Relationship | To |
|---|---|---|
| `CatalogDataset` | `IS_ASSOCIATED_WITH` / `CLASSIFIED_BY` | `CatalogClassifier` |
| `CatalogElement` | `CLASSIFIED_BY` | `CatalogClassifier` |

### Policy and quality

| From | Relationship | To |
|---|---|---|
| `CatalogDistribution` | `HAS_LIFECYCLE_POLICY` | `CatalogLifecyclePolicy` |
| `CatalogLifecyclePolicy` | `POLICY_CONFINES_TO` | `Application` |
| `CatalogDataContract` | `HAS_QUALITY_RULE` | `CatalogDataQualityRule` |

### Glossary

| From | Relationship | To |
|---|---|---|
| `CatalogValidValue` | `HAS_ALLOWED_VALUES` | `CatalogBusinessTerm` |
| `CatalogBusinessTerm` | `DEFINED_FOR` | `CatalogEncodingInstance` |
| `CatalogValidValue` | `DEFINED_FOR` | `CatalogEncodingInstance` |

---

## §URN — Format Reference

### Dataset URN
```
urn:li:dataset:{urn:li:dataPlatform:{<app-id>},{<object-type>}-{<object-uuid>},{<env>}}
```

### Distribution URN
```
urn:li:dataset:{urn:li:dataPlatform:{<platform-type>},{<platform-instance>}.{<namespace>}.{<object-name>},{<env>}}
```

Platform types: `glue`, `snowflake`, `teradata`, `databricks`, `oracle`, `sqlserver`, `s3`

### DataFlow URN (orchestration pipeline — the 3rd Application child)
```
urn:li:dataFlow:{<orchestrator>,<flow-id>,<cluster>}
```

---

## §TAGS — System Tag Format

System-controlled tags follow the pattern:
```
<org>:<category>:<value>
```

Common categories:
- `<org>:physicalorigination:<source>` — how the distribution was discovered/harvested
- `<org>:logicalorigination:<migration-source>` — migration provenance
- `<org>:datadomain:<domain-code>` — domain assignment tag

---

## §OQ — Open Questions (for any implementation)

1. Is `DataDomain -[IS_RELATED_TO]->` self-referential (domain hierarchy) or points to another type?
2. Does `DataDistribution -[IS_IMPLEMENTED_AS]-> CatalogSchema` exist in your schema?
3. Full set of `platform-type` values for your environment?
4. Is `CatalogWorker` the same identity as your HR/employee system, or a catalog-local concept?
5. Does `DataContract` exist between two Applications, or between Distribution and Application?
6. What environments beyond PROD/DEV/TEST does your URN scheme use?
