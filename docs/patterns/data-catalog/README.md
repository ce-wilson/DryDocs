# Enterprise Data Catalog + Orchestration Graph — Patterns

Best-practice guidelines for integrating an enterprise data catalog ontology
(DataHub-based) with a process orchestration knowledge graph (DryDocs /
BMC Control-M). These patterns apply to any organization running a DataHub-derived
catalog alongside batch orchestration at scale.

## Contents

| File | Purpose |
|---|---|
| `ontology-standard.md` | Identifies the underlying standards (DataHub, DCAT v2, OpenLineage) and how they compose |
| `enterprise-data-catalog-ontology.md` | Machine-first node/relationship reference for the DataHub entity model |
| `data-catalog-schema.cypher` | Cypher constraints + schema meta-graph; load into Neo4j dev instance as reference |
| `data-catalog-drydocs-crosswalk.md` | Crosswalk between the data catalog (data plane) and DryDocs (process plane) |
| `lineage-design-top3.md` | Top 3 Neo4j modeling patterns for cross-platform orchestration lineage |
| `classifiers-example.csv` | Example regulatory classifier taxonomy (replace `<OrgCatalog>:` prefix with your namespace) |

## The two-plane model

```
DATA PLANE (catalog)          PROCESS PLANE (DryDocs / Control-M)
──────────────────────        ────────────────────────────────────
DataDomain                    CatalogLOB / Product
Dataset                       STG_* staging tables (output of jobs)
DataDistribution              Control-M job output on a platform
Application ◄─────────────── Application  (SHARED — SEAL ID is the bridge)
Worker / WorkerGroup ◄─────── Employee / DevTeam
                              ControlMJob  (unique to DryDocs)
                              AppDataFlow  (new — DataHub dataFlow analogue)
                              DataAsset    (new — connects the planes)
```

The `Application` node (keyed by your organization's application ID) is the
single join point between the catalog team's tooling and DryDocs. No duplication;
both systems MERGE to the same node.

## Usage

1. Replace `<OrgCatalog>:` with your internal classifier namespace prefix
2. Replace `<org-id>` / `<seal-id>` / `<app-id>` with your identity scheme
3. The Cypher files use a `Catalog*` label prefix to avoid collision with your
   existing graph labels — rename if your conventions differ
4. Run `data-catalog-schema.cypher` against a dev Neo4j instance to validate
   the schema meta-graph before applying to production
