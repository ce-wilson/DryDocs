# Example: Generated Domain Reference

This is an example of what a Mode A (Platform Domain) output looks like after an
interview session. The platform is `snowflake` (fictional/sanitized example).

This file lives at:
- Internal: `drydocs/data/data-catalog/snowflake-domain.md` (gitignored, real names)
- Public: `docs/patterns/data-catalog/snowflake-domain.md` (sanitized, committed)

---

```markdown
<!-- §META -->
```yaml
domain: snowflake-reporting
mode: Platform
platform: snowflake
version: 0.1
status: DRAFT
last_updated: 2026-06-18T00:00:00Z
populated_from: interview with data warehouse lead on 2026-06-18
open_questions: 2
```

---

## §SCOPE — Business context

The Snowflake reporting layer is the final destination for financial and operational
data that originates from Oracle staging and Teradata processing. Control-M jobs
write to this layer nightly after cross-platform processing completes. Business
reporting and compliance queries run exclusively from this layer.

**Why this domain matters for DryDocs lineage:**
UC6 (source of record), UC7 (end-to-end lineage), and UC2 (table not loaded) all
terminate or start their traversal at Snowflake DataAsset nodes.

---

## §DATAASSETS — Key data objects

| assetId | name | namespace | env | format | isExternalFeed | isSourceOfRecord | notes |
|---|---|---|---|---|---|---|---|
| `urn:drydocs:dataasset:snowflake:<schema>:DAILY_SUMMARY` | DAILY_SUMMARY | `<schema>` | PROD | TABLE | false | true | Business source of record for daily reporting |
| `urn:drydocs:dataasset:snowflake:<schema>:CUSTOMER_DIM` | CUSTOMER_DIM | `<schema>` | PROD | TABLE | false | true | Master customer dimension |
| `urn:drydocs:dataasset:snowflake:<schema>:STAGING_INBOUND` | STAGING_INBOUND | `<schema>` | PROD | TABLE | false | false | Intermediate load staging — not source of record |

---

## §JOBS — ControlMJob ↔ DataAsset edges

| Job pattern | Direction | DataAsset name | platform | Notes |
|---|---|---|---|---|
| `<FOLDER>/SNOWFLAKE_DAILY_LOAD` | GENERATED (writes) | DAILY_SUMMARY | snowflake | Nightly batch from Teradata |
| `<FOLDER>/SNOWFLAKE_DIM_REFRESH` | GENERATED (writes) | CUSTOMER_DIM | snowflake | Full refresh from Oracle master |
| `<FOLDER>/TERADATA_EXPORT` | USED (reads) | `<teradata-table>` | teradata | Source feed for DAILY_SUMMARY |
| `<FOLDER>/SNOWFLAKE_DAILY_LOAD` | USED (reads) | STAGING_INBOUND | snowflake | Reads from own staging first |

---

## §UC — Use case answers for this domain

| UC | Question | Answer for this domain | Graph entry point |
|---|---|---|---|
| UC1 | File not received | No file-based feeds land on Snowflake directly — files arrive via S3 and are loaded by a Snowflake COPY job | `DataAsset {platform:'s3', isExternalFeed:true} → COPY job → Snowflake` |
| UC2 | Table not loaded | DAILY_SUMMARY not loaded = `SNOWFLAKE_DAILY_LOAD` blocked; check TERADATA_EXPORT completion condition | `ControlMJob {job_id:'SNOWFLAKE_DAILY_LOAD'} → REQUIRES_IN_CONDITION →` |
| UC3 | Impact of broken job | `SNOWFLAKE_DAILY_LOAD` failure blocks 3 downstream reporting jobs and 1 compliance extract | `ControlMJob → EMITS_OUT_CONDITION → 4 downstream jobs` |
| UC4 | Dev team | [TO-BE-UPDATED — internal file only] | `Application → HAS_MEMBERSHIP → Employee` |
| UC5 | App/folder counts | ~4 Applications, ~12 folders write to Snowflake | `COUNT(app) WHERE j.platform='snowflake'` |
| UC6 | Source of record | DAILY_SUMMARY and CUSTOMER_DIM are sources of record; STAGING_INBOUND is not | `DataAsset {isSourceOfRecord:true, platform:'snowflake'}` |
| UC7 | End-to-end lineage | `[vendor S3 file] → S3 COPY job → STAGING_INBOUND → SNOWFLAKE_DAILY_LOAD → DAILY_SUMMARY` | `isExternalFeed:true@s3 → ... → isSourceOfRecord:true@snowflake` |

---

## §CYPHER — Domain-specific discovery queries

```cypher
-- All Snowflake DataAssets
MATCH (a:DataAsset {platform: 'snowflake'})
RETURN a.name, a.namespace, a.format, a.isExternalFeed, a.isSourceOfRecord
ORDER BY a.namespace, a.name;

-- Jobs writing to Snowflake
MATCH (j:ControlMJob)-[:GENERATED]->(a:DataAsset {platform: 'snowflake'})
RETURN j.folder_id, j.job_id, a.name;

-- Cross-platform path ending at Snowflake source-of-record
MATCH path = (src:DataAsset {isExternalFeed: true})
             <-[:USED]-(j1:ControlMJob)-[:GENERATED]->(mid:DataAsset)
             <-[:USED]-(j2:ControlMJob)-[:GENERATED]->(tgt:DataAsset {platform: 'snowflake', isSourceOfRecord: true})
RETURN path,
       [n IN nodes(path) WHERE n:DataAsset | n.name + '@' + n.platform] AS platformHops;
```

---

## §OQ — Open questions

1. [TO-BE-UPDATED]: Confirm `CUSTOMER_DIM.isSourceOfRecord = true` with data governance
2. [TO-BE-UPDATED]: Is there a DataHub `dataset_urn` for DAILY_SUMMARY for `REPRESENTS_CATALOG_DATASET` bridge?

---

## §SANITIZE — Checklist (this file is the sanitized public version)

- [x] No real SEAL IDs — using `<seal-id-placeholder>`
- [x] No real server names or SIDs
- [x] No real schema names — using `<schema>`
- [x] No real employee IDs
- [x] UC4 answer — internal gitignored file only
- [x] Internal version at `drydocs/data/data-catalog/snowflake-domain.md`
```

---

## What this example demonstrates

- **§META block** is YAML, machine-first — future tooling can parse it
- **§DATAASSETS** table drives the DataAsset loader (Stream C.4): one node per row
- **§JOBS** table drives the USED/GENERATED edge creation (C.4 loader)
- **§UC** answers are the deliverable of the interview session — not the questions
- **§CYPHER** blocks are runnable immediately in Neo4j Browser for validation
- **§OQ** captures follow-up items that gate the final `isSourceOfRecord` flag
- **§SANITIZE** checklist is run before every public commit — enforces security rules
- `[TO-BE-UPDATED]` markers are NEVER committed — they must all be resolved or
  replaced with `N/A — not applicable: <reason>` before a file is considered final
