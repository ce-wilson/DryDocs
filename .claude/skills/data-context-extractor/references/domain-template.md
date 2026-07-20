# DryDocs Domain Reference — Output Template

Machine-first format. Fill one instance of this template per platform domain
(Mode A) or per application domain (Mode B). Replace all `[PLACEHOLDER]` values.
Mark unknowns `[TO-BE-UPDATED]` — do not leave blank.

---

```markdown
<!-- §META -->
```yaml
domain: [platform-name OR app-domain-name]
mode: [Platform | Application]
platform: [oracle | snowflake | teradata | s3 | sqlserver | linux]   # Mode A: primary platform
seal_id: [INTERNAL — gitignored version only; omit from public file]  # Mode B
version: 0.1
status: DRAFT
last_updated: [ISO-DATE]
populated_from: [interview with <role> on <date>]
open_questions: [count of remaining [TO-BE-UPDATED] markers]
```

---

## §SCOPE — Business context

[2–3 sentences: what data lives on this platform / what this application does with
data. No internal names, SEAL IDs, or server addresses in the public version.]

**Why this domain matters for DryDocs lineage:**
[Which DryDocs use cases (UC1–UC7) this domain is the primary entry point for.]

---

## §DATAASSETS — Key data objects

One row per named data object (table / file / view / stream) that Control-M jobs
interact with on this platform.

| assetId | name | namespace | env | format | isExternalFeed | isSourceOfRecord | notes |
|---|---|---|---|---|---|---|---|
| `urn:drydocs:dataasset:<platform>:<namespace>:<name>` | [name] | [schema/path] | PROD | TABLE | false | false | |
| `urn:drydocs:dataasset:<platform>:<namespace>:<name>` | [name] | [bucket/prefix] | PROD | FILE | true | false | external vendor feed |
| `urn:drydocs:dataasset:<platform>:<namespace>:<name>` | [name] | [schema/path] | PROD | TABLE | false | true | source of record |

**isExternalFeed = true** when data originates outside the org's own Control-M jobs
(third-party vendor drop, partner S3 upload, upstream market data feed).

**isSourceOfRecord = true** when this object is the business-authoritative copy
cited in reporting, compliance, or downstream system feeds.

---

## §JOBS — ControlMJob ↔ DataAsset edges

For each job that reads from or writes to objects on this platform. These rows
drive the `USED` / `GENERATED` edge population in the DataAsset loader (Stream C.4).

| Job pattern (folder / job name) | Direction | DataAsset name | platform | Notes |
|---|---|---|---|---|
| [FOLDER_NAME / JOB_NAME] | USED (reads) | [asset name] | [platform] | [context — e.g. "reads staging table"] |
| [FOLDER_NAME / JOB_NAME] | GENERATED (writes) | [asset name] | [platform] | [context — e.g. "final load to DW"] |

**Direction key:**
- `USED` → the job reads / consumes this asset (input)
- `GENERATED` → the job writes / produces this asset (output)

---

## §UC — Use case answers for this domain

Filled during the UC1–UC7 interview (`references/use-cases.md`). Replace `[ANSWER]`
with domain-specific findings; mark remaining unknowns `[TO-BE-UPDATED]`.

| UC | Question | Answer for this domain | Graph entry point |
|---|---|---|---|
| UC1 | File not received | [ANSWER] | `FileWatcher job → REQUIRES_IN_CONDITION →` |
| UC2 | Table not loaded | [ANSWER] | `ControlMJob → DataAsset {platform} →` |
| UC3 | Impact of broken job | [ANSWER] | `ControlMJob → EMITS_OUT_CONDITION →` |
| UC4 | Dev team for app | [ANSWER — internal] | `Application → HAS_MEMBERSHIP → Employee` |
| UC5 | App/folder counts | [ANSWER] | `COUNT(Application) WHERE platform=$p` |
| UC6 | Source of record | [ANSWER] | `DataAsset {isSourceOfRecord:true} ←` |
| UC7 | End-to-end lineage | [ANSWER] | `isExternalFeed → ... → isSourceOfRecord` |

---

## §CYPHER — Domain-specific discovery queries

```cypher
-- All DataAssets on this platform
MATCH (a:DataAsset {platform: '<platform>'})
RETURN a.name, a.namespace, a.format, a.isExternalFeed, a.isSourceOfRecord
ORDER BY a.namespace, a.name;

-- Jobs that read from this platform (inputs)
MATCH (j:ControlMJob)-[:USED]->(a:DataAsset {platform: '<platform>'})
RETURN j.folder_id, j.job_id, a.name, a.namespace;

-- Jobs that write to this platform (outputs)
MATCH (j:ControlMJob)-[:GENERATED]->(a:DataAsset {platform: '<platform>'})
RETURN j.folder_id, j.job_id, a.name, a.namespace;

-- End-to-end lineage through this platform
MATCH path = (src:DataAsset {isExternalFeed: true})
             <-[:USED]-(j:ControlMJob)-[:GENERATED]->(tgt:DataAsset {platform: '<platform>'})
RETURN path,
       src.name + '@' + src.platform AS source,
       tgt.name AS target;

-- Application ownership of jobs on this platform (UC4)
MATCH (app:Application)-[:HAS_DATA_FLOW]->(:AppDataFlow)-[:ORCHESTRATES]->(j:ControlMJob)
      -[:GENERATED]->(a:DataAsset {platform: '<platform>'})
RETURN app.seal_id, count(DISTINCT j) AS jobCount, count(DISTINCT a) AS assetCount;
```

---

## §OQ — Open questions

Mark any unknowns surfaced during the interview. These gate follow-up loaders.

1. [TO-BE-UPDATED]: Confirm `isSourceOfRecord` candidates with data governance team
2. [TO-BE-UPDATED]: Confirm which external feeds set `isExternalFeed = true`
3. [TO-BE-UPDATED]: Confirm DataHub `dataset_urn` for `REPRESENTS_CATALOG_DATASET` bridge
4. [TO-BE-UPDATED]: Are there additional DataAsset candidates not covered in this interview?

---

## §SANITIZE — Checklist before committing public version

Run before writing to `docs/patterns/data-catalog/<file>.md`:

- [ ] No real SEAL IDs — replace with `<seal-id-placeholder>`
- [ ] No real server names or SIDs — replace with `<server>` / `<sid>`
- [ ] No real employee IDs or names — replace with `<employee-id>`
- [ ] No internal org names or company GHE org references
- [ ] No real schema names if sensitive — replace with `<schema>`
- [ ] No real bucket names if sensitive — replace with `<bucket-name>`
- [ ] Asset names: use generic names if sensitive, specific if already public
- [ ] UC4 answers (team names, escalation contacts) — internal file ONLY
- [ ] Internal version saved to `drydocs/data/data-catalog/` (gitignored)
```
