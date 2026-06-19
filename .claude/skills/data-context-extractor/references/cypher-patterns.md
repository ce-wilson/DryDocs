# DryDocs Cypher Patterns

Discovery queries for domain interviews and output validation. Run in Neo4j Browser
or via `drydocs neo4j query`. Replaces the generic SQL dialect reference.

---

## Schema inspection — run first on any new session

```cypher
-- Current graph schema (visual in Neo4j Browser)
CALL db.schema.visualization() YIELD nodes, relationships RETURN nodes, relationships;

-- Constraints and indexes
SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties
RETURN name, type, labelsOrTypes, properties;

-- DataAsset population (how many, by platform)
MATCH (a:DataAsset)
RETURN a.platform, a.format,
       count(*) AS assetCount,
       sum(CASE WHEN a.isExternalFeed THEN 1 ELSE 0 END) AS externalFeeds,
       sum(CASE WHEN a.isSourceOfRecord THEN 1 ELSE 0 END) AS sourceOfRecord
ORDER BY assetCount DESC;

-- AppDataFlow population
MATCH (f:AppDataFlow)
RETURN f.orchestrator, f.cluster, count(*) AS flows;

-- Applications with all three children
MATCH (app:Application)
OPTIONAL MATCH (app)-[:HAS_BATCH_PROCESS]->(bp)
OPTIONAL MATCH (app)-[:HAS_EVENT_PROCESS]->(ep)
OPTIONAL MATCH (app)-[:HAS_DATA_FLOW]->(flow)
RETURN app.seal_id,
       bp IS NOT NULL AS hasBatch,
       ep IS NOT NULL AS hasEvent,
       flow IS NOT NULL AS hasDataFlow
ORDER BY app.seal_id;
```

---

## Mode A — Platform domain discovery

```cypher
-- All jobs interacting with a platform
MATCH (j:ControlMJob)-[r:USED|GENERATED]->(a:DataAsset {platform: $platform})
RETURN j.folder_id, j.job_id, type(r) AS direction,
       a.name, a.namespace, a.format
ORDER BY j.folder_id, j.job_id, direction;

-- Platform hop count (cross-platform paths through this platform)
MATCH (src:DataAsset {platform: $platform})<-[:USED]-(j:ControlMJob)-[:GENERATED]->(tgt:DataAsset)
WHERE src.platform <> tgt.platform
RETURN tgt.platform AS next_platform, count(*) AS pathCount
ORDER BY pathCount DESC;

-- External feeds entering the platform
MATCH (j:ControlMJob)-[:USED]->(a:DataAsset {platform: $platform, isExternalFeed: true})
RETURN a.name, a.namespace, count(DISTINCT j) AS jobsUsingIt
ORDER BY jobsUsingIt DESC;

-- Source-of-record objects on the platform
MATCH (a:DataAsset {platform: $platform, isSourceOfRecord: true})
OPTIONAL MATCH (j:ControlMJob)-[:GENERATED]->(a)
RETURN a.name, a.namespace, j.job_id AS producingJob;
```

---

## Mode B — Application domain discovery

```cypher
-- Full Application context (three children)
MATCH (app:Application {seal_id: $sealId})
OPTIONAL MATCH (app)-[:HAS_BATCH_PROCESS]->(bp:BatchProcess)
OPTIONAL MATCH (app)-[:HAS_EVENT_PROCESS]->(ep:EventProcess)
OPTIONAL MATCH (app)-[:HAS_DATA_FLOW]->(flow:AppDataFlow)
OPTIONAL MATCH (flow)-[:ORCHESTRATES]->(j:ControlMJob)
RETURN app, bp, ep, flow, count(j) AS jobCount;

-- All DataAssets touched by an application's jobs
MATCH (app:Application {seal_id: $sealId})
      -[:HAS_DATA_FLOW]->(:AppDataFlow)
      -[:ORCHESTRATES]->(j:ControlMJob)
      -[r:USED|GENERATED]->(a:DataAsset)
RETURN type(r) AS direction,
       a.name, a.platform, a.namespace, a.isExternalFeed, a.isSourceOfRecord
ORDER BY a.platform, type(r), a.name;

-- Jobs owned by application with folder structure
MATCH (app:Application {seal_id: $sealId})
      -[:HAS_DATA_FLOW]->(flow:AppDataFlow)
      -[:ORCHESTRATES]->(j:ControlMJob)
MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(j)
RETURN flow.flowName, f.folder_id, j.job_id, j.data_center_id
ORDER BY flow.flowName, f.folder_id;
```

---

## Use case queries (UC1–UC7)

```cypher
-- UC1: Trace why a file hasn't arrived
-- Start from the expected DataAsset and walk backwards through conditions
MATCH (tgt:DataAsset {name: $fileName, isExternalFeed: true})
OPTIONAL MATCH (j:ControlMJob)-[:GENERATED]->(tgt)
OPTIONAL MATCH (j)-[:REQUIRES_IN_CONDITION]->(c:Condition)
OPTIONAL MATCH (blocker:ControlMJob)-[:EMITS_OUT_CONDITION]->(c)
RETURN tgt.name, tgt.platform,
       j.job_id AS expectedJob, c.name AS blockedOnCondition,
       blocker.job_id AS blockerJob;

-- UC2: Trace why a table hasn't loaded
MATCH (tgt:DataAsset {name: $tableName, format: 'TABLE'})
MATCH (j:ControlMJob)-[:GENERATED]->(tgt)
MATCH (j)-[:REQUIRES_IN_CONDITION]->(c:Condition)
OPTIONAL MATCH (upstream:ControlMJob)-[:EMITS_OUT_CONDITION]->(c)
RETURN tgt.name, tgt.platform,
       j.job_id AS loadJob,
       c.name AS prerequisiteCondition,
       upstream.job_id AS upstream_job;

-- UC3: Impact of a broken job (downstream blast radius)
MATCH (broken:ControlMJob {job_id: $jobId})
      -[:EMITS_OUT_CONDITION]->(c:Condition)
      <-[:REQUIRES_IN_CONDITION]-(downstream:ControlMJob)
OPTIONAL MATCH (downstream)<-[:ORCHESTRATES]-(:AppDataFlow)<-[:HAS_DATA_FLOW]-(app:Application)
RETURN downstream.job_id AS affected_job,
       c.name AS blocked_on_condition,
       app.seal_id AS affected_application
ORDER BY affected_application, affected_job;

-- UC4: Dev team for an application
MATCH (app:Application {seal_id: $sealId})
      -[:HAS_MEMBERSHIP]->(m:Membership)
      -[:HELD_BY]->(e:Employee)
MATCH (m)-[:OF_ROLE]->(r:Role)
RETURN e.employee_id, r.name AS role, m.valid_from, m.valid_to;

-- UC5: Counts by platform
MATCH (app:Application)-[:HAS_DATA_FLOW]->(:AppDataFlow)-[:ORCHESTRATES]->(j:ControlMJob)
      -[:GENERATED|USED]->(a:DataAsset)
RETURN a.platform,
       count(DISTINCT app) AS appCount,
       count(DISTINCT j.folder_id) AS folderCount,
       count(DISTINCT a) AS assetCount
ORDER BY appCount DESC;

-- UC6: Source of record for a named dataset
MATCH (tgt:DataAsset {isSourceOfRecord: true, name: $datasetName})
      <-[:GENERATED]-(j:ControlMJob)
      <-[:ORCHESTRATES]-(:AppDataFlow)
      <-[:HAS_DATA_FLOW]-(app:Application)
RETURN tgt.name, tgt.platform, tgt.namespace,
       j.job_id AS producingJob,
       app.seal_id AS owningApplication;

-- UC7: Full cross-platform lineage (the DryDocs moat query)
MATCH path = (src:DataAsset {isExternalFeed: true})
             <-[:USED]-(j1:ControlMJob)-[:GENERATED]->(mid:DataAsset)
             <-[:USED]-(j2:ControlMJob)-[:GENERATED]->(tgt:DataAsset {isSourceOfRecord: true})
RETURN path,
       src.name + '@' + src.platform AS origin,
       [n IN nodes(path) WHERE n:DataAsset | n.name + '@' + n.platform] AS platformHops,
       tgt.name + '@' + tgt.platform AS destination
LIMIT 10;
```

---

## Cypher conventions for DryDocs

| Convention | Value |
|---|---|
| Node labels | `PascalCase` — `:ControlMJob`, `:DataAsset`, `:AppDataFlow` |
| Relationship types | `SCREAMING_SNAKE_CASE` — `USED`, `GENERATED`, `ORCHESTRATES` |
| Properties | `camelCase` — `folder_id`, `assetId`, `dataflowUrn` |
| Date properties | Always `datetime(row.capture_date)` — never bare strings |
| MERGE safety | Every MERGE target must have a uniqueness constraint first |
| Platform | Always `a.platform = 'snowflake'` (property) — never `(:Snowflake)` (node) |
| Relationship direction | Encodes semantic meaning; never arbitrary |
| `IF NOT EXISTS` | All DDL (constraints/indexes) — makes re-runs idempotent |
