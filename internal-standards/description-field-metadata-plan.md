# PLANNED PHASE — Description-Field Metadata & Variable Modernization

**Corpus:** INTERNAL (company-specific plan) — *not* vendor documentation.
**Status:** 🔵 **PLANNED / DRAFT-IN-PROGRESS** — captured 2026-06-11 from SME (chat + production screenshots). **The modern guidelines are not documented or communicated anywhere else yet — this document is the emerging draft, being created as-we-go.** Treat it as the working source for the standard until formally ratified.
**Role:** Roadmap note. Defines (a) the planned repurposing of the Control-M **Description** field as a structured metadata carrier for graph relationships, and (b) the phased **variable modernization** effort with the production support team + agents.

> ⚠️ **Trust tier:** internal / planned / SME-asserted. The "modern" examples below are the *target pattern* observed in early adopters — not yet validated estate-wide.

---

## 1. Why the Description field

**History (SME):** descriptions are **legacy-waterfall documentation**. People tried to update them with meaningful info over the years, but **folders/jobs are now auto-generated**, so the field typically contains boilerplate or stale prose.

**Plan:** repurpose Description to carry **information we don't capture anywhere else**, in a parseable structure, to create **relationships in the knowledge graph**.

**Vendor constraints that make this viable** (see [general-parameters → Description](../vendor-bmc/controlm-general-parameters.md#description)):
- 1–**4000 characters**, free text, optional, case-sensitive — ample room for key:value metadata.
- **Variable Name: None** — the field is *not* runtime-accessible as a `%%` variable. It's **metadata-only**: safe to restructure without affecting job execution. (Corollary: it can never *drive* behavior — purely descriptive/graph-feed.)

---

## 2. Observed legacy vs modern (production examples, P032-E0700-DMA)

### Folder `PRARAG-HLDM-89211-MLCM-ORIG-CRM-TRUST-DLY` (SMART)

| | Legacy | Modern (target pattern) |
|---|---|---|
| **Description** | `Generated Control-M Folder` *(autogen boilerplate, zero info)* | `datasetSeriesName: MLCM CRM \|SeriesSLA: 17:00 EST` *(pipe-delimited key:value)* |
| **Variables** | `NOTIFY` (email), `DRPBX_DIR`, `DROPBOX_BKP_DIR`, `FILEDATE=%%$ODATE`, `YARN_QUEUE` | adds **`SEAL=111027`**, `EMAIL_DL_L3`, `EMAIL_DL_L2`; renames `DRPBX_DIR`→`DROPBOX_DIR` |
| **Documentation** | File type, **empty** Doc Path/File | **URL** → SharePoint (INFOPROD docs) |
| **Created By** | o288926 | i738092 |

### Job `PARAD00010_MLCM_ORIGINATIONS_DAILY_CRM_INDICATOR_TOK_ONPM_FW` (FileWatcher)

| | Legacy | Modern (`PARAD0011b_…_FW`) |
|---|---|---|
| **Description** | `Contol-M File Watcher for TOK` *(human attempt, typo, low info)* | `FileDeliveryMechanism: MFTS_AGENT \| USER: ftsi37291 \| ENV: FTS2 \| ROUTE_ID: 372399 \| SourceOrigin: I \|SourceContact: DATA_ECO_SQLSRV_L2_SUPPORT@restricted.chase.com \| SourceSnowQueue: CCB_HLT_ASUP_SQLSRV` |
| **Watch Path** | `%%DRPBX_DIR.%%FILE_NM_PREFIX.%%BUS_DATE.%%FILE_NM_SUFFIX.%%EXTENSION` *(5-variable indirection chain)* | `%%DROPBOX_DIR.Originations_Daily_CRM_Indicator_.%%$ODATE.tok` *(direct, 1 variable + literals)* |
| **Local variables** | `FILE_NM_PREFIX=Originations_Daily_CRM_Indicator_`, `DRPBX_DIR=…`, `BUS_DATE=%%$ODATE`, **`FILE_NM_SUFFIX=.`**, `EXTENSION=tok` | **none** (eliminated) |

### Observed metadata keys (initial inventory — extend as adopted)

| Scope | Key | Example | Graph relationship it enables |
|---|---|---|---|
| Folder | `datasetSeriesName` | MLCM CRM | folder → dataset series node |
| Folder | `SeriesSLA` | 17:00 EST | SLA property/edge (note: EST, consistent with [data-center convention](data-center-naming-convention.md)) |
| Job | `FileDeliveryMechanism` | MFTS_AGENT | job → delivery-mechanism |
| Job | `USER` | ftsi37291 | job → service/functional account |
| Job | `ENV` | FTS2 | job → transfer environment |
| Job | `ROUTE_ID` | 372399 | job → MFT route node |
| Job | `SourceOrigin` | I | **`I` = Internal** (company data) vs external/vendor-supplied data — *code set open to change* |
| Job | `SourceContact` | DATA_ECO_SQLSRV_L2_SUPPORT@… | job → support contact/DL |
| Job | `SourceSnowQueue` | CCB_HLT_ASUP_SQLSRV | job → ServiceNow assignment queue |
| Folder var | `SEAL` | 111027 | **direct join: folder → SEAL `:Application`** ⭐ |
| Folder vars | `EMAIL_DL_L2` / `EMAIL_DL_L3` | support DLs | folder → escalation contacts by tier |

### ⭐ SEAL semantics & resolution hierarchy (SME-confirmed 2026-06-11)

The `SEAL` folder variable is the highest-value addition — a *declared* key for the structured↔unstructured cross-graph join ([[project-drydocs-scrape-two-corpus]] intent #3).

**Original naming intent (confirmed):** the numeric segment in folder names **is a SEAL ID** (`89211` above). The design was: **File Watchers carry the *source* SEAL** (the application that produced the file), and **processing folders carry the *processing application's* SEAL** — in the worked example, folder variable `SEAL=111027` = **Home Lending Advice and Reporting** (SME-confirmed 2026-06-11). So one flow legitimately touches **two SEALs**: source app and processing app — model them as distinct edges, e.g. `(job)-[:WATCHES_FILE_FROM]->(:Application {source seal})` vs `(folder)-[:PROCESSED_BY]->(:Application {processing seal})`.

**Why name-embedded SEAL is NOT valid estate-wide:** the majority of folders carry a **platform** name rather than an application / area-application name (SME example: `PRAOC` vs `PRSRV`). Because the name identifies the platform, the SEAL/application association implied by the folder name can't be trusted.

**Resolution hierarchy for determining a job's SEAL:**
1. **Folder variable `SEAL`** — primary; if present, it wins.
2. **(Planned)** derive the SEAL from the **data pipeline / dataset** the job touches — the future per-*job* SEAL source, independent of folder naming.
3. **Name-embedded SEAL** — legacy intent only; unreliable (platform-named folders), use as a weak hint, never as ground truth.

**Additional planned source — Control-M escalation/alerting table (`psgmgr.cm_escalation_db`):** join `EJOBNAME VARCHAR2(64 BYTE)` = `JOB_NAME`; the SEAL is **`ECOMPONENT VARCHAR2(40 BYTE)`**, stored with a decimal suffix — e.g. **`111027.00`**. ⚠️ Normalize on join: strip the trailing `.00` (or cast to integer) before matching against SEAL keys. This gives a *per-job, declared* SEAL from escalation config — slots between tier 1 and tier 2 when present.

**SEAL ID format:** sequential numbering, **currently 6 digits** (110865, 111027); older applications have shorter IDs (`89211` = 5 digits). **Do not assume fixed width**; store/compare as integer or normalized string.

⚠️ **Coverage caveat:** the Control-M team only started tracking to SEAL **in the last couple of years** — declared SEALs (tier 1) exist mostly on recent/modernized objects; the bulk of the estate needs tiers 2–3 plus derivation.

### Target Neo4j model (SME, 2026-06-11 — already modeled)

- **`SealId` is the primary node for the business application.** Organizational relationships attach there: dev team supports SealId, application contacts, etc.
- **Density buffer:** technical objects do *not* attach to the Application node directly. Every application gets a corresponding **child label — `:BatchProcess` or `:EventProcess` — keyed by `sealId`**, and all tech objects (Control-M folders/jobs, etc.) join through that child node. This keeps the Application node clean while every tech object remains reachable via the sealId key.
- **Pre-population strategy:** `Application → SealID` can be pre-populated **when known**; otherwise `Application → Platform` (e.g. PRAOC, PRDCL). **Which of the two applies cannot be determined from the Control-M data alone.** A later phase links to SEAL with what we know and **derives** the rest — derivations are "not always intuitive" (expect manual/SME adjudication for a tail).
- Platform-coded estates (PRAOC = Ab Initio ETL, PRDCL = Java/PySpark→AWS) have **no direct SEAL**; application-coded ones do (PRSRV = SEAL **110865**, Home Lending Servicing — code created by our team since the data-lake SRE org doesn't support us). Registry: [folder-naming-convention](folder-naming-convention.md#known-application-code-registry-seed--extend-as-confirmed).

**Parsing format (as observed):** `key: value` pairs delimited by `|` (pipe). Spacing is inconsistent in the wild (`|SeriesSLA`, `| USER`) — parser must be whitespace-tolerant. No escaping convention defined yet for values containing `|` or `:` (e.g. `SeriesSLA: 17:00 EST` — value itself contains `:`; **split on first `:` only**).

---

## 3. The variable parsing problem (what modernization must fix)

The legacy job illustrates the hazards agents must handle when parsing/resolving variables (ties to [[project_controlm_c3_normalization]] — Python owns var resolution):

1. **Concatenation-dot ambiguity.** In `%%DRPBX_DIR.%%FILE_NM_PREFIX.%%BUS_DATE.%%FILE_NM_SUFFIX.%%EXTENSION` the `.` is Control-M's **concatenation operator**, *not* a literal dot. The literal dot before the extension is smuggled in as a variable *value* (`FILE_NM_SUFFIX = "."`). A naive parser that treats `.` as literal produces the wrong filename; one that treats all dots as operators loses the real dot.
   ⚠️ **SME (2026-06-11): this bad practice appears under *many different variable names* across the estate** — people invented their own names for the same dot-smuggling trick. Phase-2 detection must therefore be **pattern-based** (flag any variable whose value is pure punctuation/delimiter — `.`, `_`, `-`, `/` …), **never name-based** (grepping for `FILE_NM_SUFFIX` finds one team's spelling, not the practice).
2. **Deep indirection for static values.** Five variables to compose what is effectively a static pattern + `%%$ODATE`. Each indirection is a place for drift and a resolution dependency.
3. **Name drift.** `DRPBX_DIR` vs `DROPBOX_DIR` for the same path — same concept, two spellings, breaks naive joins across jobs/folders.
4. **Punctuation stored as data.** Variables whose values are single delimiters (`.`) are invisible landmines in any text-level analysis.

---

## 4. Phased plan (production support team + agents)

> **Owner:** production support team, assisted by agents. Captured verbatim intent: *"creating a template for proper variables, then validating what's present so we don't break it, then 'modernize it' by using ontology to define what it's doing."*

### Phase 1 — Template
Define the **proper-variable template**: canonical names (e.g. `DROPBOX_DIR` not `DRPBX_DIR`), when a variable is warranted vs a literal, no punctuation-as-value, direct paths over indirection chains. Plus the **Description metadata template**: approved key list (table above as seed), `key: value | key: value` format, split-on-first-colon rule, escaping convention (to define).

### Phase 2 — Validate (don't break)
Inventory existing variables/descriptions estate-wide and validate against the template **read-only**. Classify: conforming / non-conforming-but-functional / hazardous (e.g. concatenation-dot patterns). **Nothing is changed in this phase** — resolution behavior of legacy patterns (per [controlm-variables](../vendor-bmc/controlm-variables.md) scope/resolution rules, incl. `VARIABLE_INC_SEC`) must be preserved.

### Phase 3 — Modernize via ontology
Map each job/folder's variables + description metadata onto the **DryDocs ontology** so the graph *defines what the job is doing* (dataset series, delivery route, source system, support queue, SEAL application). Remediate legacy patterns to the template only once the graph confirms equivalence (the modern job above is the worked example: 5 locals → 0, path direct, metadata moved to Description/variables where it's queryable).

---

## 5. Open items to confirm (do not invent)

**Resolved 2026-06-11 (SME):**
- ~~`SourceOrigin` meaning~~ → `I` = Internal vs external/vendor data (code set open to change).
- ~~Is `89211` a SEAL ID?~~ → Yes; name-embedded SEAL was the original intent (source SEAL on File Watchers, processing SEAL on processing folders) but is **not valid estate-wide** — folder variable is primary. See SEAL section above.
- ~~Guidelines documentation status~~ → not documented/communicated anywhere yet; **this doc is the emerging draft**.

**Resolved 2026-06-11 (SME background):**
- ~~PRAOC vs PRSRV~~ → **PRAOC = platform** (Ab Initio ETL, SRE-dictated, no direct SEAL); **PRSRV = application-tied** (created by our team, SEAL 110865 Home Lending Servicing). Also PRDCL = platform (Java/PySpark→AWS). Registry seeded in [folder-naming-convention](folder-naming-convention.md).
- Graph model defined: SealId primary node + `:BatchProcess`/`:EventProcess` child labels keyed by sealId for all tech objects (see Target Neo4j model above).

**Still open:**
1. Full approved **metadata key list** (the table above is observed, not ratified).
2. **Escaping/format rules** for `|` and `:` inside values; required vs optional keys per object type.
3. Whether `SEAL` as a folder variable becomes **mandatory** in the Phase-1 template (recommended ⭐ — SME: "if it's in the folder variable it should be primary"; note SEAL tracking only began ~2 years ago, so mandatory-for-new is realistic, retrofit is the long tail).
4. ~~Exact processing SEAL for the worked example~~ → **RESOLVED 2026-06-11: `SEAL=111027` = Home Lending Advice and Reporting** (earlier "111071" was a typo). This also ties `PRARA` (the folder's Application code) to SEAL 111027 via the declared folder variable.
5. Naming: does the modern pattern formalize the long auto-generated folder/job names, and how does it reconcile with [PRAOCG](folder-naming-convention.md) (observed: `PRARAG-…` = PRAOCG-style 6-char prefix + generated suffix, `-DLY` frequency suffix at the end)?
6. Catalog of the **variable-name aliases** used for the dot-smuggling practice (Phase-2 inventory output).
7. `PRARA`: now tied to SEAL 111027 via folder variable — confirm whether the *code itself* is application-tied estate-wide (like PRSRV) or platform-style (`ARA` ≈ Advice & Reporting App? — plausible mnemonic, unconfirmed).
8. LOB letter decode: P021 hosts `PC…` codes vs `PR…` elsewhere — confirm `C` LOB (Card?).

Related: [[project-drydocs-scrape-two-corpus]], [[project_controlm_c3_normalization]], [[project-folder-naming-praocg]], [[project-datacenter-naming-time]]
