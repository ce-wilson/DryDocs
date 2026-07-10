# DAT Naming & NFR Standard — Platform View (Data & Analytics)

**Corpus:** INTERNAL (governance, tier ③). **Status:** 🟠 DIGESTED — 2026-06-17.
**Owner:** DAT SRE (Data & Analytics). **Sources:** Escalation Manager portal (`PDCLD0051_AUTO…` → 1,173 rows), the CAF join SQL (`PARENT_TABLE LIKE 'PRDCL%-CAF-%'`, `OWNER='a_caf_dwh_np'`), SCIM examples, SME narration.

> ⚠️ **Provenance:** the DAT NFR standard itself is owned by the DAT SRE team and is **not** fully transcribed here — this digests what's observable in the data + the SME's account of an (unresolved) email exchange with the DAT SRE ("Sushant"). Inferred token meanings are marked *(inferred)*; confirm with DAT.

---

## 1. Purpose & philosophy (platform view)

DAT's standard exists to make job names **machine-parseable for one central Grafana monitoring platform**. Naming is **hard-coded and positional** *on purpose*: the dashboard tooling parses the name to publish platform-wide views. DAT SRE owns the dashboard team; other towers (incl. HLT) **piggyback** on that platform.

Optimization target = **platform monitoring** (one dashboard, all data jobs), not per-application ownership.

---

## 2. Observed naming structure (PDCL / platform-coded)

Example jobs: `PDCLD0051_AUTO_ACAPS_CAF_APPS_MASTER_AWS_RFND`, `PDCLD0051_AUTO_ACBS_LOAN_ACCRUAL_DPL_AWS_RFND`, `PDCLD002_WM_SZ_SCPP_TXN_DY_FCT_AWS_RFND`, `PDCLD0020_REFN_CAF_REFI_CLOSING_DATA_AWS_MON`.

Positional read (1-based; *some segment meanings inferred*):

| Segment | Example | Meaning |
|---|---|---|
| 1 | `P` | Environment = Production |
| 2–4 | `DCL` | **Platform** app code (`DCL` = data-cloud / Java-PySpark→AWS; `AOC` = Ab Initio on Cloud) — *a platform, not a business application* |
| 5 | `D` | Frequency (D/M/Q/Y) |
| 6–9 | `0051` | Sequence / instance |
| `_AUTO` | | Automation indicator *(inferred)* |
| next | `_ACAPS` / `_ACBS` / `_AFNC` / `_REFN` | **Source system** *(inferred: ACAPS, ACBS, AFNC…)* |
| middle | `_CAF_APPS_MASTER` / `_LOAN_ACCRUAL` | Dataset / business object |
| platform | `_AWS` / `_ONPM` | Execution/destination platform |
| stage | `_RFND` / `_DPL` / `_MON` | Pipeline stage / data-lake layer *(inferred: `RFND`≈Refined layer, `DPL`≈deploy/duplicate)* — **confirm with DAT** |

Folder pattern: `PRDCL…-CAF-…` (platform-coded folder; `CAF` grouping).

---

## 2b. Authoritative standard (CCB DAT Control-M guidelines)

> Source: DAT Control-M guidelines ("For Data & Analytics AREA Products only"; contact **CCB DAT IPM SRE**). Redesigned to standardize structure across all LOB Area products — common naming, inventory, platform-adoption/capacity forecasting, **self-heal**, observability. **HLT (§6) aligns to this master.**

**Platform scope:** VSIs (approved by the COE) run jobs only on the **ABINITIO ONPREM/AWS** or **DPL AWS/GKP** frameworks.

**Server:** all VSI Control-M jobs host on **`P032`, not `P012`** — P012 runs ~10K short of **300K**, the BMC-supported ceiling. Migrate dependencies to P032; use **global out conditions (`PG-`)** for cross-server dependents + prerequisites.

**Folder naming (Production PTO):** `PR<3-digit APPCODE>G-<AREA_PRODUCT>-<Product/Data-Domain SEAL>-<PROCESS>-<ZONE>-<Folder Frequency>`
- Continuum folders add `-CONTINUUM` to `<PROCESS>`; PRPL folders trail `-PRPL`; Verification folders are a variant. `APPLICATION = PR<3-digit APPCODE>`.
- **Near-identical to the HLT folder spec** — confirming HLT aligns to this CCB master; HLT adds HLDM/HLDF, the reporting-seal rule, and app-coded routing.

**Mandatory command-line / hygiene:**
- **No custom wrappers.** Use approved accelerators — **Abi Script** / **DPL Script**; DPL orchestrated **only** via the **Python DT Accelerator** (no Java-jar — stability/scaling).
- **ABIONCLOUD:** hardcode `-p` prefix `%%JOBNAME-%%ODATE-%%ORDERID-%%RUNCOUNT` **in the command line, not an env var**.
- **DPL:** hardcode the pipeline ID in the command line, not an env var.
- **Host groups: DO NOT hardcode a server name** — use the VSI-cluster host group for the job's framework.
- **FW SLA hygiene:** don't run File Watchers for long; schedule to the agreed SLA + average SLO (arrival) — not 8h when the file arrives in 1–2h.
- **Decommissioning:** decommissioned jobs (moved `%PRPL`→prod) are deleted with the **GTI team** after the normalization period (folders too).

**VSI onboarding checklist (the `cm-vsi-guidelines-DAT` page) — additional mandatory items:**
- **AbinitioAWS command-wrapper template** = the PTO-approved version from `go:abijobs` (e.g. v1.2.4); use the latest approved template, not a custom wrapper.
- **Hygiene Script** adopted; **no dynamic directories created in `/tmp` or `/home`** (filesystem hygiene).
- **DPL jobs** use the new **DT Python accelerator** launcher (the no-Java-jar rule, stated as a VSI gate).
- **Deployment automation = "Zero Click"** (CI/CD; manual fallback per the [NFR catalog](nfr-catalog.md) Build/Test/Deploy row).

---

## 2c. Authoritative enumerations (the full `cm-guidelines-DAT` vocabulary)

> Supersedes the *inferred* segment meanings in §2. These are the **governed value lists** for each name segment — the "enumerated-but-extensible descriptor vocabulary" the [synthesis doc](nfr-consistency-and-greenfield.md) design-principle 6 hoped for, **confirmed to exist as a real artifact.** HLT (§6) carries the *same* job-type/zone vocabulary (consistency finding).

**Application ↔ framework ↔ Control-M server registry** (appcode is registered per *underlying framework*, not business app):

| Framework | Control-M Application | 3-char APPCODE | Server |
|---|---|---|---|
| DPL | `PRDCL` | `DCL` | **P032** |
| Ab Initio | `PRAOC` | `AOC` | **P032** |
| Informatica→Snowflake (ICDW) | `PRIOS` | `IOS` | **P014** *(renamed from DPC→IOS, 1/30/25)* |
| Snowflake ETL | `PRSFS` | `SFS` | P014 *(being deprecated)* |
| ABICOLO DCM | `PRDDC` | `DDC` | P032 |
| External Data | `PRAED` | `AED` | **P033** |

> Refines the "all VSI on P032" rule (§2b): **P032** = DPL/Ab Initio/DCM; **P014** = Informatica/Snowflake (ICDW); **P033** = External Data.

**`<AREA_PRODUCT>`** — must equal the **PAT-tool product name** (`pat.gaiacloud.jpmchase.net/.../data-and-analytics/data-delivery`); **no roll-ups or breakings**. Ties naming to the [[project-pat-ontology-analysis]] ontology. Values → Product: `CB/BB/DGTL/CCT/TCH/CC/CAMP/RSK/FIN/OPT/CAF(Auto)/MAP/FRDRSK`→Data Delivery(DD); `DOP/CUST/CNTD/WM(Integrated Customer DW)/EXTD`→ADP; `INFO1`→Data Lake; `PRCY`→Privacy; `DAG`→Data Governance; `CCJ`→Customer Interaction Insights; `BCPL`(was PNL)→DD.

**`<Folder Frequency>`** (folder-name suffix): `-DLY` daily · `-WKLY` weekly · `-MTH` monthly · `-QTRL` quarterly · `-CYC` multiple cycles/day · `-ADHOC` manual · `-HIST` history · `-WEND` weekend · `-WDAY` weekdays (Mon-Fri/Sat) · `-BD` business-day calendar (BD1–BD15) · `-HLDY` federal holidays · `-CO` calendar-day calendar · `-BWKLY` bi-weekly · `-UFD` adhoc-loaded daily (no fixed arrival).

**`<Job Frequency>`** (job-name **position 5**, single char): `D` daily · `W` weekly · `M` monthly · `Q` quarterly · `R` adhoc/history.

**`<SEQ_NO>`** = 3–4 digit job-order sequence.

**`<ZONE>`** (data-lake layer): `TRUST` ingestion to Trusted (placement + ingest) · `RFND` Refined (CDC + semantic→refined) · `OVRH` on-prem hydration/preprocessing for cloud (split/token/unzip/copy) · `PROV` provision to consumption (Teradata/Exadata) · `TECH` tech-debt workarounds removed after legacy→cloud (back-up copy, legacy SFTP, TD unload). *(ICDW Snowflake SH stage/integration/semantic zones being removed.)*

**`<Type>` job-type token** (last segment) — a **governed ~60-token enumeration** with a **Framework** applicability column (`All` / `DPL & Abinitio` / `ICDW Snowflake` / `External` / `DPL`). Representative: `_FW` file-watcher · `_SFTP`/`_PRESFTP` · `_PREPROC` (non-monitored prep: manual token, split, special-char) · `_CPY`/`_MV`/`_UNZIP`/`_ZIP` · `_PLCT` placement · `_TRUST`/`_TRUSTD` · `_CDC` · `_RFND`/`_RFNDT` · `_TDSTG`/`_TDPOSTLD`/`_TDSEM`/`_TDLOAD`/`_TDVNLD` (Teradata) · `_EXASTG`/`_EXAPOSTLD`/`_EXASEM` (Exadata) · `_SQLSTG`/`_SQLPOSTLD`/`_SQLSEM` (SQL Server) · `_HYD`/`_HYDR` (hydration / reverse-copy tech-debt) · `_MON`/`_MONTRST` (shift-left monitoring) · `_GLU` · `_RECON` · `_SK` (surrogate key) · `_PURG` (hygiene/archive) · `_NTFY` · `_EXT` · `_DSDK` (DPL SDK) · `_CASNLD` (Cassandra GKP) · ICDW: `_SFDEL/_IOSFTP/_SFRLS/_SFERR/_HKO/_HKC/_SFLM/_SFSTG`. → directly the vocabulary **R12/R13** validate against.

**Folder/job variants:** Verification `…-VERF` (folders + jobs); Purge-only folders `…<PROCESS>_PURGE-…`; **ICDW Informatica-migration PRE-PROD** jobs append **`_PP`** *after the job-type* **and** add `_PP` to in/out conditions (run on P032; PROD on P014).

**File-Watcher rules (operational, checkable):**
- **Time limit 1–240 min (4 hr max); NEVER 0/unlimited.** DD evaluates SLA impact from the AVG SOR arrival time. → candidate rule **R26**.
- FW jobs live **only in ONPM or TRUST zone folders**; scheduled from any VSI on on-prem compute.
- **Dated file for delta loads; non-dated only for full loads.** Missed SLO ⇒ job should **fail + raise a ticket to the L2 team**.

**QR = Quantitative Resource** (Control-M concurrency/workload control on shared servers — **not** a support queue). Every job adopts *multiple* QRs with **max-quantity caps** to protect shared clusters: a compute VSI QR (e.g. `PRECO-COMPUTE-CTRL-VSI`), a task-service QR (`PRDCL-DAT-DCL-VSI` DPL-on-AWS, `PRDCL-DAT-GKP-VSI` GKP, `PRAOC-DAT-VSI` ABI, `PRECO-TD-CTRL-VSI`/`PRICD-TD-ST{01,02,04,08,16}-VSI` Teradata by load-type), a **low-cap app-specific QR** (`PR<app>-<AREAPRODUCT>-VSI`, cap ≈15, so one app can't hog the cluster), and FW-only `PR<app>-FW-CTRL-VSI`. Caps observed: load-balancer 1000, individual-node 200, Snowflake 200 (PROD) / 50 (PRE-PROD). **The HLT `PR<app>-HL-QR` (§6) is the same Quantitative-Resource concept.**

---

## 3. Escalation behavior (platform default)

- Failures route to **CCB Data / CAF platform queues** (`C1CCBDATAECO`, `C2CCBDATACLDCAF`, `C3BCSCAFUSICDW`).
- **No escalation-DB entry ⇒ defaults to the platform L1 queue `C1CCBDATAECO`.** (See [escalation reference §5](escalation-scim-reference.md).)
- `ECOMPONENT` = SealId, but **platform app codes (`PRDCL`/`PRAOC`) don't map cleanly to a single business SEAL** — many applications share the platform, so the name alone can't identify the owning app. (See the platform-vs-application caveat in [folder-naming](../folder-naming-convention.md).)

---

## 4. Strengths

- **Deterministically parseable** → enables the central Grafana dashboards with no per-team dashboard work.
- **Consistent** across the data estate (one convention, enforced by tooling).
- Encodes pipeline stage + platform + source system in the name — useful lineage signal.

## 5. Weaknesses (SME concern + analysis)

- **Platform-coded ⇒ weak ownership signal.** The name identifies the *platform*, not the *application*; un-configured failures fall to a generic platform L1 queue rather than the owning team.
- **Rigidity vs reality.** A fully hard-coded positional scheme can't express every scenario; teams either **can't follow it** for edge cases or **drift** into ad-hoc variable naming. (The SME's core complaint about over-rigid NFR guidance.)
- **SEAL ambiguity** on shared platform codes (`PRAOC`/`PRDCL`) → teams "default to their own" because they can't track which of many folders is theirs.
- **Naming ≠ intent.** A stage token classifies the *platform step*, not necessarily the business behavior (carried into the synthesis doc's ontology note).

---

## 6. Relationship to HLT

HLT (tier ④) **must stay parseable by DAT's tooling** (HLT piggybacks on DAT's Grafana) while expressing an *application* view and routing un-configured failures to the **owning dev queue** instead of `C1CCBDATAECO`. The two are reconciled — not replaced — in the [synthesis / greenfield doc](nfr-consistency-and-greenfield.md). See also [HLT standard](hlt-naming-standard.md).

Related: [[project-folder-naming-praocg]], [[project-controlm-remediation-spinoff]]
