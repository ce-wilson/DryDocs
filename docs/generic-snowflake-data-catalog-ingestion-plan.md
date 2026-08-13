# Generic Snowflake data-catalog (dataset/distribution) ingestion — loader plan

**Status:** PLAN (2026-07-28, SME screenshot walkthrough). Nothing here loads the graph;
every graph write stays behind the HITL gate chain (G22 family / its own gate).
**Classification of this document:** Internal-Public — mechanism only. The company's
dataset-registration catalog is referred to generically throughout (`<CATALOG>` in view
names); the real system name, real view/database names, and all real values (dataset
names, GUIDs, app ids, emails, hosts, buckets) stay company-side in the internal twin
(the sanitized↔raw twin convention). The evidence screenshots are Internal-Confidential
and live outside the repo tree (repo-root `*.png` is gitignored; relocate to the G19
landing zone, see §6).

---

## 1. What the catalog is, and why it is the inventory backbone

The catalog is the company's dataset registration system (dataset + distribution
controller, fed by a registration API / Kafka event stream). It is exposed for query as
curated Snowflake views in the metadata data product:

- `<PROD_DB>.<SCHEMA>.<CATALOG>_DATASETS_V` — one row per registered **dataset** (logical).
- `<PROD_DB>.<SCHEMA>.<CATALOG>_DISTRIBUTIONS_V` — one row per **distribution** = a
  physical materialization of a dataset on a specific platform.
- Event views (`<CATALOG>_DATASET_REGISTERED_V`, `<CATALOG>_DISTRIBUTION_REGISTERED_V` /
  `_UPDATED_V` / `_DELETED_V`, `<CATALOG>_DATASET_DISTRIBUTION_CERTIFIED_V`) — the
  curated Kafka stream, reordered to the API's key/value pairs (lifecycle feed;
  deferred, §5e).

Why it matters (the project problem statement): the target is the **complete inventory
by application with source and target locations**. The catalog is the closest thing to
that inventory already assembled — it names the dataset, the producing application id,
the contact, the registration source, and (per distribution) the exact physical
coordinates on each platform. It populates the *nodes* of the puzzle; the DPL lineage
chain (G15 → G17 → G25 → G41) supplies the *arrows*. This plan deliberately loads no
arrows: **once lineage is done, we create the relationships** — through the gate, not
during import.

## 2. Field contract observed (mechanism-only, from the 2026-07-28 screenshots)

### 2.1 `<CATALOG>_DATASETS_V`

| Column | Reading |
|---|---|
| `DATASET_NAME`, `DATASET_BUSINESSNAME` | technical + business names |
| `DATASET_IDENTIFIER` | **dataset GUID — the identity key** (same GUID space as the DPL registry's `datasetId` when the registration source is DPL, §3) |
| `BUSINESS_DESCRIPTION_TEXT` | free text |
| `PUBLISHER_COMPANY_NAME` | publishing org/product line (taxonomy fact, not identity) |
| `PRODUCEDBY_APPLICATION_IDENTIFIER` | **numeric application id — the SEAL-shaped bridge key** to `:BusinessApplication` |
| `EMAIL_ADDRESS_TEXT` | contact (individual or DL) — routes to the drafted `email-dl-contact-point` gate, never a new ad-hoc concept |
| `REGISTRATION_SOURCE_SYSTEMNAME` | observed enum: `DPL`, a second warehouse-side registration authority (`AUTHORITY2` in this doc; real name company-side), null — **which upstream registry registered it** |
| `REGISTRATION_SOURCE_SYSTEMDATAASSET_IDENTIFIER` | **explicit foreign key into that upstream registry** (for DPL rows: the DPL dataset GUID) |
| `TIMESTAMP` | audit time (see union note below) |

DDL observation (GET_DDL on the view): it is a `UNION ALL` of a flat catalog table plus
two governance/registered event tables, with `PARSE_JSON` extraction (producing app id
from the technology-application `produced_by` object, first contact's email,
registration-source object) and a `COALESCE` over audit update/create dates **in two
different timestamp formats**. Consequences for the extractor: (a) the same
`DATASET_IDENTIFIER` can appear more than once across the union — stage latest-per-GUID,
count the dupes; (b) the view is already a lossy flattening (first contact only) — the
Kafka/event views are the richer upstream if we ever need more than contact #1.

### 2.2 `<CATALOG>_DISTRIBUTIONS_V`

Key + lifecycle: `DATASET_IDENTIFIER` (parent), `DISTRIBUTION_IDENTIFIER` (GUID),
`DISTRIBUTION_NAME` (encodes platform + location via platform-prefixed naming —
cross-check only, never an extraction source), `CONSUMABLE_INDICATOR` (Y/N),
`PUBLICATIONMODE_TEXT` (observed: `SNAPSHOT`), registration-source triplet
(systemname / systemdataasset id / parent dataasset id), create/update user + dates,
`TABLE_DESCRIPTION_TEXT`.

Then a wide, **sparse union of three physical shapes** — exactly one shape is
populated per row:

| Shape | Columns | Platforms observed |
|---|---|---|
| **table** | `TABLE_NAME`, `TABLETYPE_TEXT` (`TABLE`\|`VIEW`\|`EXTERNAL_TABLE`), `LOGICALDATABASE_NAME`, `DATABASE_NAME`, `DATABASE_STORAGE_RESOURCE_URI_TEXT` (jdbc:/https: URI), `DATATECHNOLOGY_NAME` (`SNOWFLAKE`\|`TERADATA`\|…), `DATABASESCHEMA_NAME` | Snowflake, Teradata warehouse, Glue external tables |
| **file** | `FILE_NAME`, `FILE_STORAGE_FORMATTYPE`, `FILE_EXTENSION_TEXT`, `FILE_SYSTEM_NAME`, `FILE_STORAGE_RESOURCE_URI_TEXT` (hdfs: URI), `FILE_SYSTEMTYPE_TEXT`, `DIRECTORY_NAME` | Hadoop/HDFS |
| **s3** | `S3BUCKET_NAME`, `S3BUCKET_ARN_IDENTIFIER`, `S3DATA_ASSET_SYSTEMNAME`, `AWSACCOUNT_IDENTIFIER`, `STORAGE_RESOURCE_URI_TEXT` (s3a: URI), `AWSREGION_IDENTIFIER`, `KMSARN_IDENTIFIER`, `S3DATAASSET_NAME`, `S3_STORAGE_FORMATTYPE` (`PARQUET`), `S3_FILEEXTENSION_TEXT` | AWS S3 (bucket names embed app-id + deployment-id) |

Sentinel observed: the literal string `NOT INSTRUMENTED` appears in
`LOGICALDATABASE_NAME` / `FILE_SYSTEM_NAME` — treat as null **and count it**
(instrumentation coverage is itself a finding). Rows with no shape populated at all:
staged shape `""`, counted.

## 3. Where the catalog sits among the existing seams (identity model)

The catalog is the **fourth registry seam**, and the one that ties the others together:

```
DPL registry (G25)    pipeline/dataset GUIDs per SEAL      ── GUID ──┐
MAC set (G17)         per-pipeline dataflow (READS/WRITES) ── GUID ──┤
Glue inventory (G41)  per-zone physical placements         ── GUID ──┼── DataAsset
Data catalog (this)   dataset + distribution + app + contact ─ GUID ─┘   identity
                                                                         space
```

- **Dataset identity:** for `REGISTRATION_SOURCE_SYSTEMNAME = DPL`, the
  `REGISTRATION_SOURCE_SYSTEMDATAASSET_IDENTIFIER` is the DPL dataset GUID — catalog
  rows land on the **same `dpl_dataset` DataAsset identity** G17/G25/G41 already
  stage (identity = GUID alone, the G17 ruling). The catalog adds names, description,
  producing app id, contact — as **properties/facts**, not new nodes.
- **`AUTHORITY2` rows** (the Teradata-warehouse world) are a **second GUID authority**.
  Never join its ids into DPL GUID space (the G41 rule: never join a non-GUID/foreign
  id scheme into GUID space) — they stage under their own origin; unification is a gate
  ruling.
- **Null-source rows** (legacy/manual registrations) key on the catalog's own
  `DATASET_IDENTIFIER`, own origin, same rule.
- **Distribution identity:** each distribution resolves to a **candidate physical
  DataAsset URN** (`urn:drydocs:dataasset:{platform}:{namespace}:{name}` — platform
  from `DATATECHNOLOGY_NAME`/shape, namespace from db+schema / bucket / directory,
  name from table / file / s3 asset). Glue-shaped rows reuse G41's canonical
  lowercase `db.table` path so they join the placements G41 already staged. The URN
  is staged as a **fact column** (`candidate_asset_urn`), not an identity ruling.
- **dataset ↔ distribution** is DCAT's own split: `dcat:Dataset` (logical) →
  `dcat:distribution` → `dcat:Distribution` (physical form). Our existing `DataAsset`
  (class `dcat:Dataset`) currently covers both levels; whether the logical catalog
  dataset and its physical distributions become one node with placement properties
  (the G41 pattern) or two nodes with a `HAS_DISTRIBUTION` edge is **the central
  question for the gate** (§5a). The extractor stages both records either way.

This is the deterministic replacement for the PoC's hand-made "relates to / has
table" edges: every one of those becomes either a property on a GUID-keyed node or a
gated, standards-named edge.

## 4. Build plan (taxonomy-first, mirrors G25/G41)

**Phase 0 — acquisition + registration (no code)**
- Land exports of the two views (CSV or JSON, full pull — row counts are small-
  registry scale) in the G19 landing zone: `DRYDOCS_DATA_ROOT/catalog/` — THE POINTER,
  NEVER THE DATA. Event views: not pulled yet.
- Register source `snowflake-data-catalog` in `config/source-registry.yaml`:
  classification `Internal-Confidential`, kind `registry`, `confirmed: false`
  (activation = its gate), locator → data root + this plan as the mapping ledger.
- Move the evidence screenshots out of the repo root into the landing zone.

**Phase 1 — extractor (staging only)**
`drydocs_lineage/extractors/snowflake_catalog.py`, the G25 shape:
- `CatalogDatasetRecord` (guid, name, business_name, description, publisher,
  producedby_app_id, contact_email, registration_source, registration_source_ref,
  origin = `dpl` | `authority2` | `catalog` per §3, source_file, timestamp) and
  `CatalogDistributionRecord` (dataset_guid, distribution_guid, name, shape =
  `table`|`file`|`s3`|`""`, platform, namespace fields, candidate_asset_urn,
  consumable, publication_mode, registration triplet, source_file).
- ASSUMED FIELD CONTRACT defined by SYNTHETIC fixtures (the dpl_mac discipline);
  adjust when a real sample validates it. Fixtures cover all three shapes, the
  `NOT INSTRUMENTED` sentinel, the union-duplicate case, and one row per
  registration-source origin.
- Coverage counters, every skip by reason, never silent: files_invalid, dupes
  (latest-per-GUID wins), no_guid, shape_unresolved, sentinel_not_instrumented,
  origin census, urn_underived.

**Phase 2 — cross-check reports (immediate value, zero graph writes)**
The reports ARE the deliverable while lineage completes — measured lists instead of
guesses:
1. Catalog DPL-rows ↔ G25 registry dataset GUIDs (registered-both-sides /
   catalog-only / registry-only).
2. Catalog distribution URNs ↔ G41 Glue placements (same canonical path join).
3. `producedby_app_id` ↔ SEAL extract BusinessApplication ids (attribution census —
   an Epic K fact, staged not edged).
4. Registration-source census (DPL / AUTHORITY2 / null) + instrumentation coverage
   (`NOT INSTRUMENTED` and empty-shape counts).

**Phase 3 — ontology proposal + gate (before any loader)**
`ontology-mapper` drafts `status: proposed` entries; gate prompt
`config/gate-prompts/snowflake-data-catalog.yaml`. Questions in §5.

**Phase 4 — loader (post-gate) + relationships (post-lineage)**
Loader merges properties onto GUID-keyed DataAssets and creates whatever node/edge
shape the gate ruled. Then — and only then — the relationship pass: G17
READS_FROM/WRITES_TO candidates + K attribution + catalog placement land on the same
nodes, giving application → dataset → physical source/target locations end to end.

## 5. Questions the gate must rule (do not pre-decide)

a. **One node or two:** logical dataset + physical distribution as a single DataAsset
   with placement properties (G41 precedent), or `Dataset` + `Distribution` nodes with
   a `HAS_DISTRIBUTION` (`dcat:distribution`) edge. DCAT supports the two-node reading;
   the G41 precedent supports properties. Trade-off: one dataset with N placements
   across platforms is exactly what distributions model — properties flatten that.
b. **Cross-authority unification:** does an AUTHORITY2 / null-origin dataset ever
   unify with a DPL GUID (name/path corroboration)? Default no; ruling required (the
   G41 never-join-foreign-ids-into-GUID-space rule of §3 — an earlier draft cited
   "the G22 clause-f pattern", which is GUID-vs-URN and the version axis, a different
   question; corrected 2026-08-12 at the G44 ontology second pass).
c. **Attribution edge:** `producedby_app_id` → `:BusinessApplication` — which K-family
   edge (`prov:wasAttributedTo` shape), and does catalog attribution corroborate or
   contradict the STG_APP_FACT SEAL facts (precedence ruling).
d. **Contact email:** fold into the already-drafted `email-dl-contact-point` gate
   (the catalog is a *fixable, ingestible* source in that gate's terms) — do not open
   a parallel concept.
e. **Event views / lifecycle:** registered/updated/deleted/certified is temporal,
   layer-4 territory (PROV activity / SOSA-style observations) — explicitly deferred;
   `CONSUMABLE_INDICATOR` + certification state stage as properties only.
f. **`PUBLISHER_COMPANY_NAME`** → org taxonomy (LOB→Product→Team) mapping or plain
   property. Default: property now, taxonomy join later.

## 6. Publish-boundary actions in this plan

- Screenshots: Internal-Confidential; currently repo-root and caught by the
  `/*.png` gitignore — move to `DRYDOCS_DATA_ROOT/catalog/screenshots/` so the repo
  tree never carries them even ignored.
- Real exports: landing zone only; guard test extends the `test_data_root.py`
  sweep to `catalog/` artifacts.
- Real system/view/database names: internal-side twin only (the sanitized↔raw twin
  convention); this doc keeps the `<CATALOG>` / `AUTHORITY2` placeholders.
- Fixtures: SYNTHETIC only, synthetic app-id block per the standing convention.
- This plan + extractor + fixtures + gate prompt: publishable (mechanism-only).
