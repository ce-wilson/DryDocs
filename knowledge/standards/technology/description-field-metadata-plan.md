---
standard: control-m-description-metadata
domain: technology
taxonomy_path: technology/orchestration/control-m/job
governs: ControlMJob.description      # repurposed as a structured metadata carrier
authority: internal-standards         # config/precedence.yaml tier 2 — refines the BMC baseline
refines: bmc-baseline
applies_to_source: controlm-psgmgr
status: planned
trust_tier: internal / SME-asserted / planned
---

# PLANNED PHASE — Description-Field Metadata & Variable Modernization

**Corpus:** INTERNAL (company-specific plan) — *not* vendor documentation.
**Status:** 🔵 **PLANNED / DRAFT-IN-PROGRESS** — captured 2026-06-11 from SME (chat + production screenshots). **The modern guidelines are not documented or communicated anywhere else yet — this document is the emerging draft, being created as-we-go.** Treat it as the working source for the standard until formally ratified.
**Role:** Roadmap note. Defines (a) the planned repurposing of the Control-M **Description** field as a structured metadata carrier for graph relationships, and (b) the phased **variable modernization** effort with the production support team + agents.

> 📄 **Amended 2026-08-11 (C29).** Four company standards pages and a four-item requirements
> page were captured, verbatim and Internal, at
> `internal/controlm-config/reference/controlm-job-metadata-standards-capture.md`. They are the
> first written form of the "modern guidelines" this document says are undocumented — so §2's
> observed-key table is no longer the only inventory. The consolidated, sanitized register is
> **§2b** (tokens and variables by job type) and **§2c** (the file-name component standard).
> Read §2 as the 2026-06-11 field observation and §2b/§2c as the 2026-08-11 documented standard;
> where they use different spellings for the same concept, §2b.7 carries the mapping. Still
> `status: planned` — the capture is a company draft (its own breadcrumb reads `WIP-DRAFT`),
> nothing in it is ratified here, and no vocabulary entry or loader exists for any proposed term.

> 🎯 **Superseded in part, same day (C30).** Where the corpus and a deployed folder disagreed, the
> **[Control-M greenfield job standard](controlm-greenfield-job-standard.md)** rules the target
> state across all four job types, and it has a working detector (R2, R30–R40). Four of §2b's rows
> change there and the reasons are worth following rather than re-deriving: the per-job
> `EMAIL_DL_L2`/`EMAIL_DL_L3` **description tokens** are dropped (they duplicate folder variables);
> `PDN_SNOW_QUEUE` is dropped outright (ServiceNow technician routing belongs to the escalation DB);
> the FileWatcher `INBOUND_ROUTE`/`OUTBOUND_ROUTE` pair is retired (a watcher is inherently inbound,
> and the live token is `REC_ID`, a source-system reference); and the FW description's `ENV` becomes
> `FTS_ID`, because `ENV` already means the deployment environment on the command jobs. §2b stays as
> the transcription of what the corpus says; the greenfield standard is what to build.
>
> **To author a job, read [Control-M Guidelines & Standards](controlm-guidelines-and-standards.md)
> instead** — one normative page (C31) that replaces this document's §2b/§2c along with four other
> partial standards. This file remains the *history*: the 2026-06-11 field observation, the
> 2026-08-11 transcription, and the key-prefix governance. It is no longer where the target state
> lives.

> ⚠️ **Trust tier:** internal / planned / SME-asserted. The "modern" examples below are the *target pattern* observed in early adopters — not yet validated estate-wide.

> 🔒 **Split twin (J14, 2026-07-27):** this file is the publishable MECHANISM half.
> The REAL production examples (folder/job names, SIDs, contact DLs, ServiceNow
> queues, MFT route ids), the real SEAL ids and application names, the SEAL-ID
> format disclosure, and the escalation-table schema identifiers live in the
> Internal-Confidential VALUES twin,
> `internal/standards/technology/description-field-metadata-plan.md`. Examples
> below are SANITIZED to the shapes the sample corpus already uses (synthetic SEAL
> block **70001–70099**, sample folder names from `config/taxonomy/controlm.yaml`);
> the twin holds the real↔synthetic key.

---

## 1. Why the Description field

**History (SME):** descriptions are **legacy-waterfall documentation**. People tried to update them with meaningful info over the years, but **folders/jobs are now auto-generated**, so the field typically contains boilerplate or stale prose.

**Plan:** repurpose Description to carry **information we don't capture anywhere else**, in a parseable structure, to create **relationships in the knowledge graph**.

**Vendor constraints that make this viable** (see [general-parameters → Description](../../../external/orchestration/bmc-controlm/controlm-general-parameters.md#description)):
- 1–**4000 characters**, free text, optional, case-sensitive — ample room for key:value metadata.
- **Variable Name: None** — the field is *not* runtime-accessible as a `%%` variable. It's **metadata-only**: safe to restructure without affecting job execution. (Corollary: it can never *drive* behavior — purely descriptive/graph-feed.)

---

## 2. Observed legacy vs modern (SANITIZED examples — real ones in the values twin)

### Folder — sample shape `PRARAG-HLDM-70002-PEX-RFND-DLY` (SMART)

| | Legacy | Modern (target pattern) |
|---|---|---|
| **Description** | `Generated Control-M Folder` *(autogen boilerplate, zero info)* | `datasetSeriesName: PEX RFND \|SeriesSLA: 17:00 EST` *(pipe-delimited key:value)* |
| **Variables** | `NOTIFY` (email), `DRPBX_DIR`, `DROPBOX_BKP_DIR`, `FILEDATE=%%$ODATE`, `YARN_QUEUE` | adds **`SEAL=70002`**, `EMAIL_DL_L3`, `EMAIL_DL_L2`; renames `DRPBX_DIR`→`DROPBOX_DIR` |
| **Documentation** | File type, **empty** Doc Path/File | **URL** → internal docs site |
| **Created By** | *(personal SID — legacy pattern)* | *(modern id pattern; twin has the real pair)* |

### Job — sample shape `PARAD00010_PEX_DAILY_RFND_INDICATOR_TOK_FW` (FileWatcher)

| | Legacy | Modern |
|---|---|---|
| **Description** | `Contol-M File Watcher for TOK` *(human attempt, typo, low info — typo verbatim from production)* | `FileDeliveryMechanism: MFTS_AGENT \| USER: <mft-service-account> \| ENV: <transfer-env> \| ROUTE_ID: <route-id> \| SourceOrigin: I \|SourceContact: <L2-support-DL>@<company-domain> \| SourceSnowQueue: <snow-assignment-queue>` |
| **Watch Path** | `%%DRPBX_DIR.%%FILE_NM_PREFIX.%%BUS_DATE.%%FILE_NM_SUFFIX.%%EXTENSION` *(5-variable indirection chain)* | `%%DROPBOX_DIR.Rfnd_Daily_Indicator_.%%$ODATE.tok` *(direct, 1 variable + literals)* |
| **Local variables** | `FILE_NM_PREFIX=Rfnd_Daily_Indicator_`, `DRPBX_DIR=…`, `BUS_DATE=%%$ODATE`, **`FILE_NM_SUFFIX=.`**, `EXTENSION=tok` | **none** (eliminated) |

### Observed metadata keys (initial inventory — extend as adopted)

| Scope | Key | Example (sanitized) | Graph relationship it enables |
|---|---|---|---|
| Folder | `datasetSeriesName` | PEX RFND | folder → dataset series node |
| Folder | `SeriesSLA` | 17:00 EST | SLA property/edge (note: EST, consistent with [data-center convention](data-center-naming-convention.md)) |
| Job | `FileDeliveryMechanism` | MFTS_AGENT | job → delivery-mechanism |
| Job | `USER` | *(MFT service/functional account)* | job → service/functional account |
| Job | `ENV` | *(transfer environment)* | job → transfer environment |
| Job | `ROUTE_ID` | *(numeric MFT route)* | job → MFT route node |
| Job | `SourceOrigin` | I | **`I` = Internal** (company data) vs external/vendor-supplied data — *code set open to change* |
| Job | `SourceContact` | *(support DL address)* | job → support contact/DL |
| Job | `SourceSnowQueue` | *(ServiceNow assignment queue)* | job → ServiceNow assignment queue |
| Folder var | `SEAL` | 70002 *(sanitized)* | **direct join: folder → SEAL `:Application`** ⭐ |
| Folder vars | `EMAIL_DL_L2` / `EMAIL_DL_L3` | support DLs | folder → escalation contacts by tier |

### ⭐ SEAL semantics & resolution hierarchy (SME-confirmed 2026-06-11)

The `SEAL` folder variable is the highest-value addition — a *declared* key for the structured↔unstructured cross-graph join ([[project-drydocs-scrape-two-corpus]] intent #3).

**Original naming intent (confirmed):** the numeric segment in folder names **is a SEAL ID**. The design was: **File Watchers carry the *source* SEAL** (the application that produced the file), and **processing folders carry the *processing application's* SEAL** — in the sanitized worked example, folder variable `SEAL=70002` = the *processing* application (Retail Advice Reporting & Analytics, sample id), while the name-embedded id is the *source* application's. So one flow legitimately touches **two SEALs**: source app and processing app — model them as distinct edges, e.g. `(job)-[:WATCHES_FILE_FROM]->(:Application {source seal})` vs `(folder)-[:PROCESSED_BY]->(:Application {processing seal})`.

**Why name-embedded SEAL is NOT valid estate-wide:** the majority of folders carry a **platform** name rather than an application / area-application name (platform vs application codes — see the [folder-naming registry](folder-naming-convention.md#application-code-registry-shape--sanitized-rows-real-registry-in-the-values-twin)). Because the name identifies the platform, the SEAL/application association implied by the folder name can't be trusted.

**Resolution hierarchy for determining a job's SEAL:**
1. **Folder variable `SEAL`** — primary; if present, it wins.
2. **(Planned)** derive the SEAL from the **data pipeline / dataset** the job touches — the future per-*job* SEAL source, independent of folder naming.
3. **Name-embedded SEAL** — legacy intent only; unreliable (platform-named folders), use as a weak hint, never as ground truth.

**Additional planned source — the Control-M escalation/alerting table** (in the scheduler metadata schema; real schema/table/column names in the values twin): join its job-name column to `JOB_NAME`; the SEAL lives in a component column **stored with a decimal suffix** (e.g. `<seal>.00`). ⚠️ Normalize on join: strip the trailing `.00` (or cast to integer) before matching against SEAL keys. This gives a *per-job, declared* SEAL from escalation config — slots between tier 1 and tier 2 when present.

**SEAL ID format:** variable width — **do not assume fixed width**; store/compare as integer or normalized string. (Actual digit widths and the sequential-numbering detail are an internal disclosure — values twin.)

⚠️ **Coverage caveat:** the Control-M team only started tracking to SEAL **in the last couple of years** — declared SEALs (tier 1) exist mostly on recent/modernized objects; the bulk of the estate needs tiers 2–3 plus derivation.

### Target Neo4j model (SME, 2026-06-11 — already modeled)

- **`SealId` is the primary node for the business application.** Organizational relationships attach there: dev team supports SealId, application contacts, etc.
- **Density buffer:** technical objects do *not* attach to the Application node directly. Every application gets a corresponding **child label — `:BatchProcess` or `:EventProcess` — keyed by `sealId`**, and all tech objects (Control-M folders/jobs, etc.) join through that child node. This keeps the Application node clean while every tech object remains reachable via the sealId key.
- **Pre-population strategy:** `Application → SealID` can be pre-populated **when known**; otherwise `Application → Platform` (platform-coded estates have **no direct SEAL**; application-coded ones do). **Which of the two applies cannot be determined from the Control-M data alone.** A later phase links to SEAL with what we know and **derives** the rest — derivations are "not always intuitive" (expect manual/SME adjudication for a tail). Registry: [folder-naming-convention](folder-naming-convention.md#application-code-registry-shape--sanitized-rows-real-registry-in-the-values-twin).

**Parsing format (as observed):** `key: value` pairs delimited by `|` (pipe). Spacing is inconsistent in the wild (`|SeriesSLA`, `| USER`) — parser must be whitespace-tolerant. No escaping convention defined yet for values containing `|` or `:` (e.g. `SeriesSLA: 17:00 EST` — value itself contains `:`; **split on first `:` only**).

---

## 2b. Token & variable register (C29, 2026-08-11)

**What this is.** A consolidated register of every metadata token and variable the standard
asks a Control-M object to carry, with its carrier, its Oracle landing column, the ontology
term the source documents propose, and — the column that matters most — an honest **status**
saying whether DryDocs has actually built it.

**Where it comes from.** Four company standards pages plus a four-item requirements page,
captured verbatim (real values, real DLs) in the Internal capture
`internal/controlm-config/reference/controlm-job-metadata-standards-capture.md`. That capture
carries the source's own §8 summary table, its SQL DDL, its REGEXP parse statements, its Turtle,
and the `[sic]` list of the source's internal inconsistencies. **This section is the sanitized
mechanism view of it** — shapes and names only; every real address, account, route id, folder
and job name lives in the values twin.

> ⚠️ **Nothing here is ratified.** The `proposed` rows are one company draft's modeling, not a
> DryDocs decision. No relationship-vocabulary entry, no property-term binding, and no loader
> exists for any of them. The class question in particular is live — see §2b.5.

### 2b.1 Carrier — the distinction this register exists to keep

Three different mechanisms hold this metadata, and §2 above blurs them. They differ in change
control, in grain, and in whether a loader can even see them:

| Carrier | What it is | Grain | Read path |
|---|---|---|---|
| **description-token** | a `key: value` pair inside the 4000-char `DESCRIPTION` field | per job | XML export → parse (`drydocs_core.orchestration.controlm.description_tokens`, G66) |
| **job-variable** | a `%%`-prefixed VARIABLE declared on the job | per job | already staged ordered by the G47 extractor |
| **folder-variable** | a VARIABLE declared at folder / sub-folder scope | per folder | already staged ordered by the G47 extractor |

**Why it matters:** `DESCRIPTION` is metadata-only and never runtime-accessible (§1), so it is
safe to restructure but can never drive behavior. A VARIABLE is the opposite — it is live at
execution, so changing one is a behavioral change requiring the equivalence proof the
remediation module exists to produce. A register that conflates the two invites someone to
"just rename a variable" the way you would edit prose.

### 2b.2 FileWatcher jobs

| Component | Token / variable | Carrier | SQL column | Ontology term | Ontology class | Vocabulary | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| Delivery mechanism | `DELIVERY_MECHANISM` | description-token | `DELIVERY_MECHANISM` | `ex:fileDeliveredVia` | ControlMJob (FileWatcher) | `MFTS_AGENT` \| `SFTP_DIRECT` \| `API_GENERATED` | proposed | Always required. §2's observed spelling was `FileDeliveryMechanism` — the standard uses SCREAMING_SNAKE |
| Transfer account | `USER` | description-token | `USER_ID` | `ex:systemUser` | prov:SoftwareAgent (the MFT agent) | free — service/functional account | proposed | Property of the *agent*, not the job |
| Transfer environment | `ENV` | description-token | `ENV` | `ex:mftsEnv` | prov:SoftwareAgent | free — small env set | proposed | |
| Inbound route | `INBOUND_ROUTE` | description-token | `MFTS_INBOUND_ROUTE_ID` | `ex:mftsRouteId` on `dprod:inputPort` | dprod:DataProductPort | route id, or literal `NULL` | proposed | MFTS only; literal `NULL` when not applicable |
| Outbound route | `OUTBOUND_ROUTE` | description-token | `MFTS_OUTBOUND_ROUTE_ID` | `ex:mftsRouteId` on `dprod:outputPort` | dprod:DataProductPort | route id, or literal `NULL` | proposed | MFTS only |
| Route direction | *(derived, no token)* | — | — | `ex:mftsRouteDirection` | dprod:DataProductPort | `INBOUND` \| `OUTBOUND` | proposed | Derived from which column the value came from |
| L3 support DL | `EMAIL_DL_L3` | description-token | `EMAIL_DL_L3` | `ex:supportContact` | EmailDistributionList *(class unsettled — §2b.5)* | semicolon-separated addresses | proposed | Dev / Scrum team |
| L2 support DL | `EMAIL_DL_L2` | description-token | `EMAIL_DL_L2` | `ex:supportContact` | EmailDistributionList *(unsettled)* | semicolon-separated addresses | proposed | Ops support group |
| Source contact | `SOURCE_CONTACT` | description-token | `SOURCE_CONTACT` | `prov:wasAttributedTo` | dcat:Dataset → contact | semicolon-separated addresses | proposed | Origin file owner. **Would be a new `role` on the existing `WAS_ATTRIBUTED_TO` edge, not a new edge type** |
| Watched token path | `%%FileWatch-FILE_PATH` | job-variable | — | *(none proposed)* | — | path expression | proposed | REQ-3. **Must be declared before `%%POSTCMD`** |
| Post-command | `%%POSTCMD` | job-variable | — | *(none proposed)* | — | `cat %%FileWatch-FILE_PATH` | proposed | REQ-3. References the previous variable rather than repeating the path |

**Landing table:** `CM_JOB_METADATA_FILE_WATCHERS`, `DESCRIPTION VARCHAR2(4000)` as the raw
parse source, `JOB_NAME` primary key.

### 2b.3 Publisher jobs

| Component | Token | Carrier | SQL column | Ontology term | Ontology class | Vocabulary | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| Job role | `JOB_ROLE` | description-token | `JOB_ROLE` | `ex:jobRole` | ControlMJob | `PUBLISHER` | proposed | The discriminator that says which table a job lands in |
| L3 support DL | `EMAIL_DL_L3` | description-token | `EMAIL_DL_L3` | `ex:supportContact` | EmailDistributionList *(unsettled)* | semicolon-separated | proposed | Same token as FileWatcher |
| L2 support DL | `EMAIL_DL_L2` | description-token | `EMAIL_DL_L2` | `ex:supportContact` | EmailDistributionList *(unsettled)* | semicolon-separated | proposed | Same token as FileWatcher |
| Downstream consumers | `PDN_DL` | description-token | `PDN_DL` | `ex:consumerContact` on `dprod:outputPort` | EmailDistributionList *(unsettled)* | semicolon-separated | proposed | Notified on publish |
| Downstream queue | `PDN_SNOW_QUEUE` | description-token | `PDN_SNOW_QUEUE` | `ex:serviceNowQueue` | ServiceNowQueue *(class unsettled)* | queue name, or literal `NULL` | proposed | **The token is mandatory even when the value is empty** — see §2b.6 |

**Landing table:** `CM_JOB_METADATA_PUBLISHERS`, same 4000-char `DESCRIPTION` + `JOB_NAME` key.

### 2b.4 ETL / `cmd` jobs — the one family that is already built

| Component | Variable | Carrier | Staging key | Ontology term | Ontology class | Vocabulary | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| Launcher path | `%%LAUNCHER_SCRIPT_PATH` | job-variable | `LAUNCHER_PATH` | `:Script.script_path` + `INVOKES` | Script `{script_role: launcher}` | path | **built** | FACT_REGISTRY, G16 |
| Payload artifact | `%%ETL_ARTIFACT_URI` | job-variable | `ARTIFACT_URI` | `:Script.artifact_uri` + `USES_ARTIFACT` | Script `{script_role: payload}` | approved-repository URI or path | **built** | G16; edge active at `rua-load-shapes` §A4 |
| Platform | `%%ETL_PLATFORM` | job-variable | `ETL_PLATFORM` | `:Script.platform` | Script (both roles) | `pyspark` \| `java` \| `abinitio` \| `informatica` | **built** | |
| Artifact kind | `%%ETL_ARTIFACT_KIND` | job-variable | `ARTIFACT_KIND` | `:Script.artifact_kind` | Script (payload) | `wheel` \| `jar` \| `pset` \| `other` | **built** | |
| Platform flags | `%%ETL_PLATFORM_FLAGS` | job-variable | `PLATFORM_FLAGS` | `:Script.platform_flags` | Script (launcher) | flag string, may be empty | **built** | Optional per REQ-4 |
| Artifact hash | `%%ETL_ARTIFACT_SHA` | job-variable | `ARTIFACT_SHA` | *(corroboration input)* | Script (payload) | content hash | **built** | **DryDocs has this and the company standard does not name it** |
| Informatica local interface | `%%INFA_INTERFACE_LOCAL` | job-variable | `INFA_INTERFACE_LOCAL` | NODE-KEY component | Script (payload) | interface id | proposed | Informatica only |
| Informatica global interface | `%%INFA_INTERFACE_GLOBAL` | job-variable | `INFA_INTERFACE_GLOBAL` | NODE-KEY component | Script (payload) | interface id | proposed | Informatica only |
| Informatica job | `%%INFA_JOB` | job-variable | `INFA_JOB` | NODE-KEY component | Script (payload) | job id | proposed | Informatica only |
| Informatica database | `%%INFA_DATABASE` | job-variable | `INFA_DATABASE` | `:Script.infa_database` | Script (payload) | database id | proposed | Variant 2 only |

**Landing:** `STG_APP_FACT`, keyed by the 30-char `fact_type`.

**Two contracts pointing the same way.** The standard's rule is *declare the names uniformly,
let the values differ by platform*. The FACT_REGISTRY's rule is *aliases suggest, values decide*
— a variable's name is a hint and `_value_fact()` adjudicates. They are complements, not
duplicates: the standard shrinks the alias tail the registry has to absorb, and the registry
keeps working on the estate that never adopts the standard.

### 2b.5 Folder-level metadata

| Component | Variable | Carrier | Ontology term | Vocabulary | Status | Notes |
|---|---|---|---|---|---|---|
| Ownership project key | `DevX-project` | folder-variable | *(none proposed)* | project key | proposed | The stated purpose is ownership attribution where the platform app code makes the folder's owner unreadable |
| L2 support DL | `L2_EMAIL_DL_NM` | folder-variable | `ex:supportContact` | semicolon-separated | proposed | **Different spelling and different carrier from the job-level `EMAIL_DL_L2`** |
| L3 support DL | `L3_EMAIL_DL_NM` | folder-variable | `ex:supportContact` | semicolon-separated | proposed | Same |
| Application | `SEAL` | folder-variable | joins `:Application` | SEAL id, variable width | *(pre-existing)* | Unchanged by these documents; §2's resolution hierarchy still governs |

⚠️ **Unsettled: two carriers, two spellings, one concept.** Support DLs appear as folder
variables (`L2_EMAIL_DL_NM` / `L3_EMAIL_DL_NM`) *and* as job description tokens (`EMAIL_DL_L2` /
`EMAIL_DL_L3`). Nothing in the source states which wins. This is exactly the folder-vs-job grain
question already open at gate `email-dl-contact-point` §B2, now with evidence on both sides;
it is carried there as rider §G2 rather than decided here.

⚠️ **Unsettled: the class.** The source models the DL as `ex:EmailDistributionList` with
properties `ex:dlTier`, `ex:dlTierDesc`, `ex:dlAddress`, `ex:ctmVariableName`. The repo's own
proposal — `email-dl-contact-point` §A1, **drafted 2026-07-22 and not signed** — is
`dd:DistributionList` aligned to `vcard:Group`, keyed on the lower-cased SMTP address. One
concept, two spellings, neither ratified. Carried as rider §G3.

### 2b.6 Grammar rules the parser must honor

These are the source's rules, restated as parser obligations. `parse_description()` in
`drydocs_core/orchestration/controlm/description_tokens.py` (G66) implements them.

1. **Pipe is the only delimiter.** Semicolons appear *inside* values — a multi-address DL is one
   token, not several.
2. **Split on the first colon only.** A value may contain colons (`SeriesSLA: 17:00 EST`).
3. **Whitespace-tolerant on both sides.** Both `| USER: x` and `|USER:x` occur.
4. **A key with an empty value still emits its token.** `PDN_SNOW_QUEUE: NULL` is mandatory even
   when unassigned, so the parse always finds the key and returns a parseable result rather than
   a missing match. The Oracle side does `NULLIF(..., 'NULL')`; the Python side returns `None`.
5. **Unknown keys are preserved, never dropped.** §4's key-prefix governance makes a bare key a
   legal team-local annotation — kept verbatim, never load-bearing.
6. **A value outside its vocabulary is a finding, not an error.** Report it; do not raise, and do
   not silently coerce.

### 2b.7 Key-prefix migration (reconciles §4's C16 governance)

C16 assigned every observed key a prefixed home. The captured standard uses bare spellings. Both
are recorded so Phase-2 validation can recognize either during the transition — C16's own
migration note grandfathers observed spellings until the template is ratified.

| Observed in §2 (2026-06-11) | Used by the captured standard | C16 target | Class |
|---|---|---|---|
| `FileDeliveryMechanism` | `DELIVERY_MECHANISM` | `drydocs.fileDeliveredVia` | reserved core |
| `USER` | `USER` | `mfts.user` | system-owned |
| `ENV` | `ENV` | `mfts.env` | system-owned |
| `ROUTE_ID` | `INBOUND_ROUTE` / `OUTBOUND_ROUTE` *(split into two)* | `mfts.routeId` *(needs a direction qualifier)* | system-owned |
| `SourceContact` | `SOURCE_CONTACT` | `drydocs.sourceContact` | reserved core |
| `SourceSnowQueue` | `PDN_SNOW_QUEUE` *(different subject — downstream, not source)* | `snow.assignmentQueue` | system-owned |
| *(not observed)* | `EMAIL_DL_L2` / `EMAIL_DL_L3` | `drydocs.supportContactL2` / `L3` | reserved core |
| *(not observed)* | `JOB_ROLE` | `drydocs.jobRole` | reserved core |
| *(not observed)* | `PDN_DL` | `drydocs.consumerContact` | reserved core |

Two of these are more than a rename. `ROUTE_ID` **split into a directional pair**, so a single
C16 target no longer suffices. And `SourceSnowQueue` and `PDN_SNOW_QUEUE` are *different
subjects* — the source system's queue versus the downstream consumer's — that a naive mapping
would merge. Both go to the template ratification, not to a find-and-replace.

---

## 2c. File-name component standard (C29, 2026-08-11)

A companion standard from the same corpus, governing how a watched file's name decomposes. It
belongs here rather than in its own file because it is authored on the same objects, lands
through the same carriers, and answers to the same ratification.

### 2c.1 The decomposition

```
<PREFIX>_<BUSINESS_DATE>_<SEQ>.<EXT>.<COMPRESSION>
```

Worked shape (sanitized): `SAMPLE_SRC_SUBJECT_20260530_001.dat.gz`

| Component | Variable name | SQL column | Ontology term | Ontology class | Vocabulary | Status | Notes |
|---|---|---|---|---|---|---|---|
| Full atomic name | `FileName` | `FILE_NAME` | `dcterms:title` | `dcat:Distribution` | free | proposed | What the OS sees; authoritative for arrival detection |
| Watch glob | `FilePattern` | `FILE_PATTERN` | `ex:watchFilePattern` | ControlMJob (FileWatcher) | glob | proposed | Dynamic components replaced by wildcards |
| Business identifier | `FilePrefix` | `FILE_PREFIX` | `ex:filePrefix` | `dcat:Distribution` | free | proposed | **Static** — never changes between runs |
| Business date | `FileBusinessDate` | `FILE_BUSINESS_DATE` | `dcterms:temporal` | `dcat:Distribution` | `YYYYMMDD` | proposed | The date the **data** represents |
| Sequence | `FileSequence` | `FILE_SEQUENCE` | `ex:fileSequence` | `dcat:Distribution` | zero-padded, 3 digits | proposed | Optional — multiple files per date |
| Format extension | `FileExtension` | `FILE_EXTENSION` | `dcat:mediaType` | `dcat:Distribution` | `.dat` `.csv` `.txt` `.tok` `.ctl` `.done` | proposed | **Authoritative for classification** — not the job-name suffix |
| Compression | `FileCompression` | `FILE_COMPRESSION` | `ex:fileCompression` | `dcat:Distribution` | `GZIP` \| `TAR` \| `TAR+GZIP` \| `ZIP` \| `NONE` | proposed | Independent of format |
| Full suffix | `FileSuffix` | `FILE_SUFFIX` | `ex:fileSuffix` | `dcat:Distribution` | free | proposed | Everything after the prefix |
| Distribution role | *(derived)* | `DISTRIBUTION_ROLE` | — | lookup `CM_DISTRIBUTION_TYPE_REF` | `DAT` \| `TOK` \| `CTL` \| `DONE` | proposed | Derived from `FILE_EXTENSION` |

**Landing table:** `CM_JOB_FILE_NAME_STANDARD`, `JOB_NAME` primary key, `DISTRIBUTION_ROLE`
foreign-keyed to a reference table.

### 2c.2 The two rulings worth keeping

**`FileBusinessDate`, never `FileDate`.** Three dates get conflated routinely and the standard
names all three so they cannot be:

| Variable | Meaning | Ontology term |
|---|---|---|
| `FileBusinessDate` | the date the **data** represents | `dcterms:temporal` |
| `FileLoadDate` | the date the file was **processed** | `dcterms:modified` |
| `FileArrivalDate` | the date the file **arrived** on disk | `prov:generatedAtTime` |

**Format and compression are two concepts in one suffix.** Linux treats `.dat.gz` as one string;
it encodes *what it contains* (`dcat:mediaType`) and *how it is stored* (`ex:fileCompression`)
separately. A `.dat.gz` is still a `DAT` file. A parser that treats the suffix atomically loses
the classification.

### 2c.3 ⚠️ Casing — this table is CamelCase and everything else here is not

The names above are **CamelCase**, deliberately: the source states "Naming Convention: `File`
prefix + component role in CamelCase". Every other name in §2b is UPPER_SNAKE, and
NFR-CTM-001 requires Control-M canonical variables to be **uppercase ASCII with case-sensitive
lookup** — so a `%%FileBusinessDate` would violate the variable standard as written.

Three namespaces are in play and only two agree:

| Namespace | Convention | Where ruled |
|---|---|---|
| Control-M `%%` variables | UPPERCASE, case-sensitive | NFR-CTM-001 §2, §9 (and §7.1 migrates `%%img_path` → `%%IMG_PATH` → canonical) |
| DESCRIPTION metadata keys | UPPER_SNAKE (was CamelCase in the 2026-06-11 observation — see §2b.7) | the 2026-08-11 standards pages |
| File-name components (this section) | **CamelCase** | the file-name standard, unsuperseded |

The likely resolution is that these are **ontology property names, not `%%` variable spellings**
— §2c.1's own mapping is CamelCase name → UPPER_SNAKE column → `ex:` term, three namespaces per
row by design, and the source's perspective table gives the *Control-M* spelling of the same
concepts as `%%FILENAME` / `%%BDATE`, uppercase. But the section that names them is titled
"Recommended **Variable Name** Standard", so the source does call them variables.

**Do not resolve this by normalizing.** Control-M is case-sensitive at execution, which is
exactly why NFR-CTM-001 §9 rejected case folding: silently upper-casing a name merges bindings
the estate may have intended to keep distinct. The ruling is which namespace each name belongs
to, and it belongs with the Phase-1 template ratification alongside §2b.7's prefix migration.

### 2c.4 Relation to the legacy pattern §3 warns about

§3's hazard #1 is dot-smuggling — a literal dot stored as a variable value so the concatenation
operator does not eat it. This standard is the structural answer: name each component, derive
the suffix, and never store punctuation as data. Worth noting honestly that the *new*
requirement REQ-3 (captured in the Internal file) reintroduces a double-dot in one variable
value, so the practice is not yet extinct in the standards themselves.

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

#### Key-prefix governance (C16, 2026-07-28 — modeled on annotation-naming governance)

Metadata keys carry an **ownership prefix**, the way annotation keys do in
catalog systems (Backstage's `<domain>/<name>` annotation convention): the
prefix says *who owns the key's meaning*, so two teams can never silently
collide on the same spelling and a parser can tell load-bearing keys from
local notes. Three classes:

1. **Reserved core prefix — `drydocs.`** Keys whose meaning the template/graph
   owns (`drydocs.datasetSeriesName`, `drydocs.seriesSLA`). Only this standard
   (post-ratification: only the gate) may add or change `drydocs.*` keys; they
   are the keys loaders may build relationships from.
2. **System-owned prefixes.** A key whose value belongs to an external
   system's namespace carries that system's prefix — the `scim.` / `jira.` /
   `seal.` families, plus the ones the observed table already implies
   (`snow.` for ServiceNow queues, `mfts.` for MFT routes/accounts). The
   owning system's documentation defines the value format; this standard only
   registers the prefix. Example targets for the observed keys:
   `SourceSnowQueue` → `snow.assignmentQueue`, `ROUTE_ID` → `mfts.routeId`,
   `SEAL` (Description-carried, if ever) → `seal.id`.
3. **Unprefixed = team-local.** A bare key (`myNote`, `runbookHint`) is a
   team-local annotation: legal, preserved verbatim, **never load-bearing for
   ingestion** — no loader may key a relationship or a join on an unprefixed
   key, and validation never fails a folder/job for its team-local keys.

**Migration note:** every key in the observed-inventory table above is
currently unprefixed. They are grandfathered as *observed* spellings only;
ratification of the Phase-1 template assigns each one a home (`drydocs.*` or
a system prefix) and records the old→new mapping so Phase-2 validation can
recognize both during the transition. (Open items 1–2 in §5 — the approved
key list and the escaping rules — are decided in the same ratification.)

### Phase 2 — Validate (don't break)
Inventory existing variables/descriptions estate-wide and validate against the template **read-only**. Classify: conforming / non-conforming-but-functional / hazardous (e.g. concatenation-dot patterns). **Nothing is changed in this phase** — resolution behavior of legacy patterns (per [controlm-variables](../../../external/orchestration/bmc-controlm/controlm-variables.md) scope/resolution rules, incl. `VARIABLE_INC_SEC`) must be preserved.
Validation **will enforce the key-prefix governance rules** (Phase 1 above):
an unregistered `drydocs.*` key, a system-prefixed key whose value fails the
owning system's format, or a loader observed keying on an unprefixed key are
each findings; bare team-local keys themselves are reported informationally,
never as failures.

### Phase 3 — Modernize via ontology
Map each job/folder's variables + description metadata onto the **DryDocs ontology** so the graph *defines what the job is doing* (dataset series, delivery route, source system, support queue, SEAL application). Remediate legacy patterns to the template only once the graph confirms equivalence (the modern job above is the worked example: 5 locals → 0, path direct, metadata moved to Description/variables where it's queryable).

---

## 5. Open items to confirm (do not invent)

**Resolved 2026-06-11 (SME):**
- ~~`SourceOrigin` meaning~~ → `I` = Internal vs external/vendor data (code set open to change).
- ~~Is the name-embedded numeric segment a SEAL ID?~~ → Yes; name-embedded SEAL was the original intent (source SEAL on File Watchers, processing SEAL on processing folders) but is **not valid estate-wide** — folder variable is primary. See SEAL section above.
- ~~Guidelines documentation status~~ → not documented/communicated anywhere yet; **this doc is the emerging draft**.

**Resolved 2026-06-11 (SME background):**
- ~~Platform vs application codes~~ → platform codes are SRE-dictated with **no direct SEAL**; application-tied codes carry one (real registry: values twin). Registry shape seeded in [folder-naming-convention](folder-naming-convention.md).
- Graph model defined: SealId primary node + `:BatchProcess`/`:EventProcess` child labels keyed by sealId for all tech objects (see Target Neo4j model above).

**Still open:**
1. Full approved **metadata key list** (the table above is observed, not ratified).
2. **Escaping/format rules** for `|` and `:` inside values; required vs optional keys per object type.
3. Whether `SEAL` as a folder variable becomes **mandatory** in the Phase-1 template (recommended ⭐ — SME: "if it's in the folder variable it should be primary"; note SEAL tracking only began ~2 years ago, so mandatory-for-new is realistic, retrofit is the long tail).
4. ~~Exact processing SEAL for the worked example~~ → **RESOLVED 2026-06-11** (SME; an earlier reading was a typo). Real ids: values twin. This also ties the folder's Application code to its SEAL via the declared folder variable.
5. Naming: does the modern pattern formalize the long auto-generated folder/job names, and how does it reconcile with [PRAOCG](folder-naming-convention.md) (observed: `PRARAG-…` = PRAOCG-style 6-char prefix + generated suffix, `-DLY` frequency suffix at the end)?
6. Catalog of the **variable-name aliases** used for the dot-smuggling practice (Phase-2 inventory output).
7. The advice-R&A code (`PRARA`): tied to its SEAL via folder variable — confirm whether the *code itself* is application-tied estate-wide (like the servicing code) or platform-style (`ARA` ≈ Advice & Reporting App? — plausible mnemonic, unconfirmed).
8. LOB letter decode: one DC hosts `PC…` codes vs `PR…` elsewhere — confirm the `C` LOB (Card?).

Related: [[project-drydocs-scrape-two-corpus]], [[project_controlm_c3_normalization]], [[project-folder-naming-praocg]], [[project-datacenter-naming-time]]
