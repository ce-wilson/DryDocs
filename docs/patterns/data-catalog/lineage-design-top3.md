# Cross-Platform Orchestration Lineage — Top 3 Neo4j Modeling Patterns

Neo4j modeling-skill analysis applied. Use cases defined first; three
patterns ranked by interoperability vs. migration cost.

---

## Use Cases (required before modeling)

| ID | Actor | Question | Graph query shape |
|---|---|---|---|
| UC1 | Customer | "We haven't received a file" | FileWatcher job → conditions → upstream blockers → owning app + team |
| UC2 | Customer | "Why hasn't this table loaded" | Job that writes to table → its dependencies → stalled predecessor |
| UC3 | Customer | "What is the impact of this broken job" | Downstream condition graph → affected jobs → affected applications |
| UC4 | Ops | "Which dev team supports this app" | Application → DevTeam via org hierarchy |
| UC5 | Ops | "How many apps/folders do we support + counts" | COUNT Application; count folders grouped by app |
| UC6 | Business | "What is the source of record for this dataset" | Backwards: CatalogDataset ← generates ← ControlMJob ← source platform |
| UC7 | Business | "End-to-end lineage for this data" | Full path: external-feed → FileWatch → processing → target platform |

---

## Application Node Pattern (3 children)

```
:Application {appId}
  ├─[:HAS_BATCH_PROCESS]──▶ :BatchProcess {appId}    ← process operations
  ├─[:HAS_EVENT_PROCESS]──▶ :EventProcess {appId}    ← event-driven operations
  └─[:HAS_DATA_FLOW]──────▶ :AppDataFlow  {appId}    ← DATA LINEAGE (3rd child)
```

All three children share the same `appId` as the parent — they are operational
facets of the same business application, each the entry point for a different
question type.

---

## Supernode Mitigation (applies to all patterns)

`:DataPlatform` (Snowflake, Oracle, Teradata, etc.) is a supernode candidate —
millions of jobs could connect to the same platform node.

**Resolution:** `platform` as a **property** on `:DataAsset` and `:ControlMJob`,
not a node. Use a `:DataPlatform` meta-node for schema documentation only.

```
// DO NOT:  (:ControlMJob)-[:RUNS_ON]->(:DataPlatform {type:'snowflake'})
// DO:      (:ControlMJob {platform: 'snowflake'})
//          (:DataAsset   {platform: 'snowflake', namespace: '...', name: '...'})
```

Range index on `platform` property enables fast filtering without supernode risk.

---

## PATTERN 1 — DataHub-Aligned ⭐ (Recommended for interoperability)

Matches DataHub's `dataFlow / dataJob / dataset` vocabulary. DryDocs lineage
becomes queryable by the data catalog team's tooling without translation.

### Model

```
:Application {appId}
  └─[:HAS_DATA_FLOW]──▶ :AppDataFlow
                         {appId, dataflowUrn, flowName, orchestrator, cluster}
                              │
                    [:ORCHESTRATES]
                              │
                    :ControlMJob
                    {jobId, folderId, dataCenterId, platform}
                         │              │
                    [:USED]        [:GENERATED]
                         │              │
                   :DataAsset      :DataAsset
                   {assetId, name, platform, namespace,
                    env, format, isExternalFeed, isSourceOfRecord}
```

### Key properties

- `AppDataFlow.dataflowUrn` = `urn:li:dataFlow:{controlm,<flowId>,<cluster>}` — DataHub-compatible
- `AppDataFlow.orchestrator = 'controlm'` — enables DataHub ingestion
- `DataAsset.isExternalFeed = true` — marks third-party / upstream data feeds
- `DataAsset.isSourceOfRecord = true` — answers UC6 directly
- `platform` = property on both `ControlMJob` and `DataAsset` (not a node)

### Constraints

```cypher
CREATE CONSTRAINT app_data_flow_urn IF NOT EXISTS
  FOR (f:AppDataFlow) REQUIRE f.dataflowUrn IS UNIQUE;

CREATE CONSTRAINT data_asset_id IF NOT EXISTS
  FOR (a:DataAsset) REQUIRE a.assetId IS UNIQUE;

CREATE INDEX data_asset_platform_idx IF NOT EXISTS
  FOR (a:DataAsset) ON (a.platform);

CREATE INDEX data_asset_name_idx IF NOT EXISTS
  FOR (a:DataAsset) ON (a.name);
```

### UC7 — End-to-end lineage query

```cypher
MATCH (tgt:DataAsset {name: $targetName, isSourceOfRecord: true})
MATCH path = (src:DataAsset {isExternalFeed: true})
             <-[:USED]-(j1:ControlMJob)-[:GENERATED]->(mid:DataAsset)
             <-[:USED]-(j2:ControlMJob)-[:GENERATED]->(tgt)
RETURN path,
       [n IN nodes(path) WHERE n:DataAsset | n.name + '@' + n.platform] AS platformHops
```

### Pros / Cons

| ✅ Pros | ⚠️ Cons |
|---|---|
| DataHub URN → catalog team can join without ETL | Must populate `dataflowUrn` in the loader |
| OpenLineage events can be emitted from this model | Two relationship paths to same ControlMJob |
| Standard vocabulary — cross-team documentation | |

---

## PATTERN 2 — OpenLineage Native (Best for observability ecosystem)

Models DryDocs lineage as first-class OpenLineage `Job/Dataset` nodes so any
OpenLineage-aware tool (Marquez, Atlan, Collibra, DataHub) consumes it natively.

### Model

```
:Application {appId}
  └─[:HAS_DATA_FLOW]──▶ :AppDataFlow {appId}
                              │
                    [:HAS_LINEAGE_JOB]
                              │
                    :LineageJob {jobName, namespace}     ← OpenLineage Job
                         │
                    [:EXECUTED_AS]──▶ :ControlMJob       ← existing node
                         │
              ┌───────────┴───────────┐
         [:INPUT]               [:OUTPUT]
              │                      │
       :LineageDataset         :LineageDataset
       {name, namespace,       {name, namespace,
        platform}               platform}
```

### OpenLineage event emission

```python
# Emit from the staging layer after each ControlMJob run
{
  "eventType": "COMPLETE",
  "job": {
    "namespace": "<data-center-name>",
    "name": "<FOLDER_NAME>/<JOB_NAME>"
  },
  "inputs": [
    {"namespace": "<source-platform>://<source-path>", "name": "<source-object>"}
  ],
  "outputs": [
    {"namespace": "<target-platform>://<target-schema>", "name": "<target-object>"}
  ]
}
```

### Pros / Cons

| ✅ Pros | ⚠️ Cons |
|---|---|
| Any OpenLineage tool consumes it without integration work | Extra abstraction layer (LineageJob wraps ControlMJob) |
| Enables real-time lineage event streaming | Requires an emitter component (new build) |
| Best interoperability story across the data ecosystem | More complex query paths |

---

## PATTERN 3 — PROV-O Extension (Best for minimum migration)

Extends DryDocs' existing PROV-O ontology. `:ControlMJob` is already a
`prov:Activity`; `:DataAsset` becomes a `prov:Entity`.

### Model

```
:Application {appId}  [prov:Agent]
  └─[:HAS_DATA_FLOW]──▶ :AppDataFlow {appId}  [prov:Activity cluster]
                              │
                    [:MANIFESTS_AS]
                              │
              :ControlMJob  [prov:Activity — existing]
              {jobId, folderId, platform}
                   │              │
              [:USED]        [:GENERATED]           ← PROV-O verbs
                   │              │
             :DataAsset    :DataAsset               ← prov:Entity (new)
             (input)       (output)
             {assetId, name, platform, namespace,
              format, isExternalFeed, isSourceOfRecord}
```

### Cross-platform lineage query (PROV-O)

```cypher
MATCH (tgt:DataAsset {name: $targetName})
MATCH path = (src:DataAsset {isExternalFeed: true})
             -[:GENERATED|USED*1..10]-
             (tgt)
WHERE ALL(n IN nodes(path) WHERE n:DataAsset OR n:ControlMJob)
WITH path,
     [n IN nodes(path) WHERE n:DataAsset | n.platform] AS platforms,
     [n IN nodes(path) WHERE n:ControlMJob | n.jobName] AS jobs
RETURN DISTINCT
  head([n IN nodes(path) WHERE n:DataAsset | n.name]) AS sourceAsset,
  platforms AS platformHops,
  jobs AS orchestrationJobs,
  length(path) / 2 AS hopCount
ORDER BY hopCount DESC
LIMIT 10
```

This query traces: `[s3-file] → FileWatcherJob → [oracle-staging] → ETL-Job
→ [teradata-intermediate] → SnowflakeLoad-Job → [snowflake-table]`

### Pros / Cons

| ✅ Pros | ⚠️ Cons |
|---|---|
| Zero new vocabulary — pure PROV-O extension | Less interoperable with catalog tooling |
| Minimal migration cost | No OpenLineage emission without adapter |
| Consistent with existing constraints.cypher | |

---

## Recommendation — Hybrid (Pattern 1 structure + Pattern 3 edges)

```
:Application {appId}
  ├─[:HAS_BATCH_PROCESS]──▶ :BatchProcess {appId}    (existing)
  ├─[:HAS_EVENT_PROCESS]──▶ :EventProcess {appId}    (existing)
  └─[:HAS_DATA_FLOW]───────▶ :AppDataFlow             (NEW — DataHub URN)
                             {appId, dataflowUrn, flowName, orchestrator, cluster}
                                  │
                        [:ORCHESTRATES]
                                  │
                        :ControlMJob (existing)
                        {jobId, folderId, dataCenterId, platform}
                            │                │
                       [:USED]          [:GENERATED]    (PROV-O verbs)
                            │                │
                      :DataAsset         :DataAsset
                      {assetId, name, platform, namespace,
                       env, format, isExternalFeed, isSourceOfRecord}

// Optional bridge to catalog (when URN is known):
:DataAsset -[:REPRESENTS_CATALOG_DATASET]-> :CatalogDataset
```

**Why hybrid:**
- DataHub-style `AppDataFlow` with URN = interoperability with catalog team at zero extra schema cost
- PROV-O `USED`/`GENERATED` on existing `ControlMJob` = zero migration cost for existing loaders
- `isExternalFeed` / `isSourceOfRecord` on `DataAsset` answer UC6 and UC7 directly
- `platform` as property (not node) = no supernode
- Bridge edge `REPRESENTS_CATALOG_DATASET` optional and additive — only populate when URN is confirmed

---

## The Unique Orchestration Lineage Value

No enterprise data catalog (DataHub, Collibra, Alation, Atlan) can answer
"what is the end-to-end path for data that ends up in table X?" at the
cross-platform level — because they observe data AT REST on individual platforms.

An orchestration layer (Control-M, Airflow) sees ALL cross-platform hops because
it orchestrates them. DryDocs surfaces this as a graph query:

```
External feed (S3/SFTP/API)
  ↓ [FileWatcher job — Linux]
Oracle staging table
  ↓ [ETL job — Oracle]
Teradata intermediate
  ↓ [Export job — Teradata]
Snowflake production table    ← "source of record" for the business
```

This is the answer to: "why hasn't this table loaded?" — trace backwards from
the Snowflake table through the full orchestration path to find the broken link,
the blocked condition, and the owning application and team.

---

## Implementation Sequence

1. Create constraints: `AppDataFlow.dataflowUrn`, `DataAsset.assetId`
2. Create indexes: `DataAsset.platform`, `DataAsset.name`
3. Populate `AppDataFlow` nodes (one per Control-M folder/job-graph per Application)
4. Populate `DataAsset` nodes from `STG_INVOCATION` + `STG_FILE_REF` (parsed job commands)
5. Write `USED` / `GENERATED` edges from staging data
6. Optionally populate `dataflowUrn` for DataHub compatibility
7. Bridge `DataAsset → CatalogDataset` when distribution URN can be resolved
