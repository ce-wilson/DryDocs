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

---

## Mode C — Org hierarchy / segment context discovery

```cypher
-- Full corporate hierarchy: Company → BusinessSegment → CatalogLOB → ProductLine → Product
MATCH (co:Company)-[:HAS_BUSINESS_SEGMENT]->(seg:BusinessSegment)
OPTIONAL MATCH (lob:CatalogLOB)-[:RECONCILES_TO]->(seg)
OPTIONAL MATCH (lob)-[:HAS_PRODUCT_LINE]->(pl:ProductLine)
OPTIONAL MATCH (pl)-[:HAS_PRODUCT]->(prod:Product)
RETURN co.name AS company,
       seg.code AS segment,
       lob.lob_code AS lob,
       pl.name AS product_line,
       prod.name AS product
ORDER BY seg.code, lob.lob_code, pl.name, prod.name;

-- Which applications belong to a business segment?
MATCH (seg:BusinessSegment {code: $segmentCode})
OPTIONAL MATCH (lob:CatalogLOB)-[:RECONCILES_TO]->(seg)
OPTIONAL MATCH (lob)-[:HAS_PRODUCT_LINE]->(pl:ProductLine)
                    -[:HAS_PRODUCT]->(prod:Product)
                    -[:HAS_APPLICATION]->(app:Application)
RETURN seg.code, lob.lob_code, pl.name, prod.name,
       app.seal_id, app.name
ORDER BY pl.name, prod.name, app.seal_id;

-- Which jobs run under a given business segment?
MATCH (seg:BusinessSegment {code: $segmentCode})
MATCH (lob:CatalogLOB)-[:RECONCILES_TO]->(seg)
MATCH (lob)-[:HAS_PRODUCT_LINE]->(pl)-[:HAS_PRODUCT]->(prod)
           -[:HAS_APPLICATION]->(app:Application)
           -[:HAS_DATA_FLOW]->(:AppDataFlow)-[:ORCHESTRATES]->(j:ControlMJob)
RETURN seg.code AS segment, app.seal_id, j.folder_id, j.job_id
ORDER BY app.seal_id, j.folder_id;

-- Which dev teams support a product?
MATCH (prod:Product {product_id: $productId})
OPTIONAL MATCH (prod)-[:HAS_DEV_TEAM]->(dt:DevTeam)
OPTIONAL MATCH (prod)-[:HAS_AREA_PRODUCT]->(ap:AreaProduct)-[:HAS_DEV_TEAM]->(dt2:DevTeam)
RETURN prod.name AS product,
       dt.team_id AS direct_team,
       ap.name AS area_product, dt2.team_id AS apg_team;

-- LOB → segment reconciliation (with confidence scores)
MATCH (lob:CatalogLOB)-[r:RECONCILES_TO]->(seg:BusinessSegment)
RETURN lob.lob_code, lob.name, seg.code, seg.name,
       r.confidence AS reconciliation_confidence
ORDER BY seg.code, r.confidence DESC;

-- Cross-segment dependency: which applications span multiple segments?
MATCH (app:Application)
MATCH (app)<-[:HAS_APPLICATION]-(prod:Product)
            <-[:HAS_PRODUCT]-(pl:ProductLine)
            <-[:HAS_PRODUCT_LINE]-(lob:CatalogLOB)
            -[:RECONCILES_TO]->(seg:BusinessSegment)
WITH app, collect(DISTINCT seg.code) AS segments
WHERE size(segments) > 1
RETURN app.seal_id, app.name, segments AS spans_segments
ORDER BY size(segments) DESC, app.seal_id;

-- Segment hierarchy with effective-date filtering (post-reorg only)
MATCH (co:Company)-[r:HAS_BUSINESS_SEGMENT]->(seg:BusinessSegment)
WHERE r.effective_to IS NULL   -- open-ended = current
RETURN co.name, seg.code, seg.name, r.effective_from;

-- DataAsset footprint per segment (which data does a segment's jobs touch?)
MATCH (seg:BusinessSegment {code: $segmentCode})
MATCH (lob:CatalogLOB)-[:RECONCILES_TO]->(seg)
MATCH (lob)-[:HAS_PRODUCT_LINE]->(:ProductLine)-[:HAS_PRODUCT]->(prod:Product)
           -[:HAS_APPLICATION]->(app:Application)
           -[:HAS_DATA_FLOW]->(:AppDataFlow)-[:ORCHESTRATES]->(j:ControlMJob)
           -[r:USED|GENERATED]->(a:DataAsset)
RETURN seg.code AS segment,
       type(r) AS direction,
       a.platform, a.name, a.namespace,
       a.isExternalFeed, a.isSourceOfRecord,
       count(DISTINCT j) AS jobsUsingAsset
ORDER BY a.platform, type(r), a.name;

-- Segment metrics carried as SYNTHESIZED (verify before clearing :Uncertain).
-- NO cross-database hop: this used to open `CALL { USE ddall.ddcontext ... }`, and
-- both that composite and ddcontext retired at the G32/G102 fold (2026-08-18). One
-- content database, and the :Uncertain LABEL is the separation — which is also why
-- this reads as an ordinary MATCH now rather than a federated subquery.
MATCH (seg:BusinessSegment&Uncertain)
WHERE seg.trust = 'SYNTHESIZED' AND seg.metric_year IS NOT NULL
RETURN seg.code AS code, seg.name AS name, seg.roe_2024 AS roe_2024,
       seg.metric_year AS metric_year, seg.metric_source AS metric_source,
       seg.reliability AS reliability
ORDER BY code;
```

---

## Mode C — Use-case queries (UC8–UC11)

```cypher
-- UC8: Which applications belong to this business segment?
-- (see Mode C patterns above for full version)

-- UC9: What product lines exist under this LOB, and how many apps do they own?
MATCH (lob:CatalogLOB {lob_code: $lobCode})
      -[:HAS_PRODUCT_LINE]->(pl:ProductLine)
      -[:HAS_PRODUCT]->(prod:Product)
OPTIONAL MATCH (prod)-[:HAS_APPLICATION]->(app:Application)
RETURN pl.name AS product_line,
       prod.name AS product,
       count(DISTINCT app) AS application_count
ORDER BY pl.name, prod.name;

-- UC10: Which teams support this product and what applications do they develop?
MATCH (prod:Product {product_id: $productId})
OPTIONAL MATCH (prod)-[:HAS_AREA_PRODUCT]->(ap:AreaProduct)
                    <-[:SUPPORTS]-(dt:DevTeam)
OPTIONAL MATCH (dt)-[:DEVELOPS]->(app:Application)
RETURN prod.name, ap.name AS area_product,
       dt.team_id AS team, dt.name AS team_name,
       collect(DISTINCT app.seal_id) AS applications
ORDER BY ap.name, dt.team_id;

-- UC11: Segment-level blast radius — if jobs under segment X fail, what's the impact?
MATCH (seg:BusinessSegment {code: $segmentCode})
MATCH (lob:CatalogLOB)-[:RECONCILES_TO]->(seg)
MATCH (lob)-[:HAS_PRODUCT_LINE]->(:ProductLine)-[:HAS_PRODUCT]->(:Product)
           -[:HAS_APPLICATION]->(:Application)
           -[:HAS_DATA_FLOW]->(:AppDataFlow)-[:ORCHESTRATES]->(j:ControlMJob)
           -[:EMITS_OUT_CONDITION]->(c:Condition)
           <-[:REQUIRES_IN_CONDITION]-(downstream:ControlMJob)
OPTIONAL MATCH (downstream)<-[:ORCHESTRATES]-(:AppDataFlow)
               <-[:HAS_DATA_FLOW]-(downApp:Application)
               <-[:HAS_APPLICATION]-(:Product)<-[:HAS_PRODUCT]-(:ProductLine)
               <-[:HAS_PRODUCT_LINE]-(:CatalogLOB)-[:RECONCILES_TO]->(downSeg:BusinessSegment)
RETURN seg.code AS broken_segment,
       j.job_id AS broken_job,
       c.name AS blocked_condition,
       downstream.job_id AS affected_job,
       downApp.seal_id AS affected_app,
       downSeg.code AS affected_segment
ORDER BY downSeg.code, downApp.seal_id;
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
