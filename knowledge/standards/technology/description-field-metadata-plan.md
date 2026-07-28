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
