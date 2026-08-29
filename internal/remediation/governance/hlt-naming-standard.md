# HLT Naming Standard & Philosophy — Application View (Home Lending)

**Corpus:** INTERNAL (governance, tier ④). **Status:** 🟠 DIGESTED — 2026-06-17.
**Owner:** Production Support / Home Lending (the SME). **Sources:** Escalation Manager portal (`PSRVD0…` → 8,474 rows), SCIM example `PRSVG-HLDM-110865-MOODY-TRUST-MTH`, SME narration. HLT exists *because* the SME disagrees with applying the platform-view default (tier ③) to Home Lending application jobs.

---

## 1. Purpose & philosophy (application view)

Monitoring should route a failure to **the team that owns the application**, not a generic platform queue. So HLT's defining rule:

> **If no escalation-DB entry exists, default the incident to the owning DEV queue** — never silently to the platform L1 queue `C1CCBDATAECO`. An un-configured failure must still land with someone accountable.

HLT is an **application-monitoring** standard layered on top of the platform. Hard constraint: HLT has **no dashboard team** and **piggybacks on DAT's Grafana**, so HLT names must remain **parseable by DAT's tooling** even while expressing an application view.

---

## 2. Observed naming structure (PSRV / Home Lending Servicing)

Example jobs: `PSRVD0001_BKPCN_SRC_AWS_FW`, `PSRVD0001_BKPCN_SRC_AWS_SFTP`, `PSRVD0001_BKPCN_SRC_AWS_UNZIP`, `PSRVD0001_BKPCN_SRC_FILECOPY_ONPM_CPY`, `PSRVD0001_BKPCN_CP_AWS_PREPROC_DLY_PRPL`, `PSRVD0001_BKPCN_OPEN_ONPM_HK`.

Positional read (1-based; *some meanings inferred — confirm*):

| Segment | Example | Meaning |
|---|---|---|
| 1 | `P` | Environment = Production |
| 2–4 | `SRV` | **Application** app code (`SRV` = Servicing, SEAL 110865) — *a business app, not a platform* |
| 5 | `D` | Frequency (D/M/Q/Y) |
| 6–9 | `0001` | Sequence |
| `_BKPCN` | | Subsystem / dataset *(inferred)* |
| stage | `_SRC` / `_CTL` / `_CP` / `_OPEN` | Pipeline stage (source / control / copy-prep / open) *(inferred)* |
| platform | `_AWS` / `_ONPM` / `_FILECOPY` | Execution platform / mechanism |
| **type** | `_FW` / `_SFTP` / `_UNZIP` / `_CPY` / `_HK` / `_PREPROC` / `_CTL` | **Job type/action** — File Watcher, SFTP, unzip, copy, housekeeping, preprocess |
| freq | `_DLY` | Frequency (long form) |
| **designation** | `_PRPL` | **Lifecycle designation** → routes escalation to the **dev** queue |

Folder example: `PRSVG-HLDM-110865-MOODY-TRUST-MTH` (HL Servicing, SEAL 110865, MOODY-TRUST dataset, Monthly).

**HLT vs DAT structural difference:** HLT job names carry **file-pipeline stages** (`SRC/FW/SFTP/UNZIP/CPY/HK/CTL/PREPROC`) because HLT jobs are largely **file movement**; DAT names carry **data-lake stages** (`AWS RFND`) because DAT jobs are data pipelines. Same positional backbone, different middle vocabulary.

---

## 2b. Authoritative naming spec (HLT Control-M guidelines, updated Nov 14 2025)

> Supersedes the *inferred* structure in §2. Source: "Control-M guidelines for HLT AWS modernization effort" (`cm-guidelines`) — HLT consolidated business applications to **Product SEAL**; aligned to CCB Control-M standards.

**Delimiters:** folder = **hyphen** `-`; job = **underscore** `_`. *Exception:* underscore inside the DataSet-Group/Business-Process segment for multi-word names (`SAS_DWR`).

**Folder name:** `PR<appcode>G-HLD<M|F>-<SOR-Seal>-<DataSet_Process>-<Zone>-<Frequency>-PRPL`
- `PR<appcode>` business app (ARA/SRV/ORG/EBM/COH) · `G` = group/SMART folder.
- `HLD<M|F>` = Home Lending Data **Managed** / **Federated**.
- `<SOR-Seal>` = source-of-record SEAL (**1 seal per folder**; use the **Reporting Application Seal** *only* when data is aggregated from multiple sources).
- `<Zone>` landing zone (RAW/TRUS/ONPM/HIST) · `<Frequency>` (DLY/WKLY/…) · trailing `-PRPL` for Production-Parallel.
- **Variants:** Trusted `…-<TRUST>-…`; Refined `…-<RFND>-…`; Verification `PRARAG-<AreaProduct>-<Product_Seal_R&A>-<Product_Process>-PROV-<Freq>-VERF`.
- Sample: `PRARAG-HLDM-33031-CORELOGIC-RAW-DLY-PRPL`; live tree uses `+` joins too: `PRARAG+HLDM-111027+HLSF-CDC-RFND-DLY-PRPL`.

**Job name:** `P<AppCode><JobFreq><JobCode>_<SOR/APP>_<DataSet_Process>_<Zone>_<Type>` (job freq matches folder). `<Zone>` processing = AWS/ONPM/AZURE/GKP; `<Type>` = FW/MV/TDLOAD/CDC/RFND/PLCT/TRUST/PREPROC.

**`<JobCode>` numeric ordering code** — groups like functions and orders jobs top→bottom in the Control-M GUI (pre-processors slot in by run order):

| Code | Function | | Code | Function |
|---|---|---|---|---|
| 0001 | House Keeping | | 0050 | AWS Trust Ingestion |
| 0010 | AWS File Watcher | | 0060 | AWS CDC / ETL / intermediate |
| 0020 | AWS Placement | | 0070 | CDC / RFND (per samples) |

**Folder layout:** Application folder (`PRARA`) → **platform sub-folders** (`PRARA-AOC` Ab Initio, `PRARA-DCL`, `PRARA-EKS`) → SMART folders. Sub-application encodes the platform framework + correlates to a **Platform Framework QR**.

**QR convention:** `PR<appcode>-HL-QR` (PRSRV/PRORG/PREBM/PRCOH/PRARA-HL-QR). **QR = Quantitative Resource** (Control-M concurrency/workload control on shared servers — *not* a support queue; see the [DAT QR enumeration §2c](dat-naming-standard.md) for the multi-QR + max-quantity-cap model HLT shares).

> **Shared vocabulary (consistency finding):** HLT uses the **same governed zone (`TRUST/RFND/OVRH/PROV/TECH`) and job-type (`_FW/_SFTP/_PREPROC/_CPY/_MV/_AUT/_EXT/_RECON/_SPLIT/_SK/_FM/…`) enumerations as DAT** ([dat-naming-standard §2c](dat-naming-standard.md)) — same positional backbone, same descriptor vocabulary. The deltas are the appcode (application vs platform) and the escalation default (§3), not the token sets.

**Anti-redundancy (stated):** avoid repeated tokens (`…COMPLIANCE_ONE…COMPLIANCE_ONE…`); modernize legacy acquisition names (`WAMUSBO`, 2009 WaMu → `SBO`).

### IN/OUT conditions & variables
- **OUT default = `PL` (local); use `PG` (global) only when necessary** — cross-server deps (DWS/Trust jobs run on `P021-E0800-ANY` + `P033-E1200-ANY`).
- **No On-Do/Shout email in production** (`Send mail to %%NOTIFY` removed).
- **Create variables only when necessary; reuse common.** Common DPL launcher `%%SCRIPT_PATH=/apps/uds/tenants/dpl_utils/dt-accelerators/dt-launcher.sh`. **Consolidate duplicate date vars** (`BUS_DATE`≡`DAT_FILE_DT_FMT`=`%%$ODATE` → keep one) — same variable-hygiene the [resolver](../../drydocs/controlm/resolver.py) targets.

### Command-line NFR (`NFR-CTM-301`)
No custom wrappers; hardcode `-p` prefix `%%JOBNAME-%%ODATE-%%ORDERID-%%RUNCOUNT` (not env var); hardcode DPL pipeline ID; use the approved accelerator (`dt-launcher.sh`); **do not hardcode host-group/server names**.

---

## 3. The dev-queue default mechanism

HLT achieves "default to the owning team" via the **lifecycle designation suffix** (`_PRPL`, `VERF`, `Decommissioned`) which the escalation rules route to the **dev-team HPSM queue** ([escalation reference §2](escalation-scim-reference.md)). Encoding the designation *in the name* means routing degrades gracefully to dev even when the SCIM row is missing/incomplete — the opposite of the platform L1 default.

---

## 4. SEAL rule — SOR vs processing (the gotcha)

> **File Watcher (`_FW`) folders → SEAL = the SOURCE (system-of-record) SEAL** — the application that *produces/sends* the file.
> **All other (processing) folders → SEAL = the PROCESSING application's SEAL.**

So one end-to-end flow legitimately carries **two SEALs** (source + processing) — model them as distinct edges, not one association (consistent with the [description-metadata plan](../description-field-metadata-plan.md) two-SEAL note and the SEAL resolution hierarchy). `ECOMPONENT` in the SCIM row should reflect the *right* one for that folder's role.

---

## 5. Gotchas / why consistency is hard (SME)

1. **Shared platform-code folder sprawl.** With shared codes (`PRAOC`, `PRDCL`) spanning *many* folders, teams can't track which folders are theirs and **default to their own** conventions → drift.
2. **Naming ≠ intent — the API gotcha.** A `_FW` (File Watcher) job *usually* watches for a **file transfer**, but **some `_FW` jobs depend on a predecessor `_PREPROC` job that calls an API** — there's no incoming file in the usual sense. The name token says "file watcher"; the real behavior is "API-driven trigger." **Intent must be derived from the resolved flow (predecessor + what it does), not the `_FW` token alone.**
3. **Rigidity vs coverage.** Over-rigid NFR guidance can't express every scenario; under-specified guidance drifts. HLT is the SME's attempt at a middle path, still being refined.

---

## 6. Strengths / weaknesses

**Strengths:** accountability-preserving default (dev queue, not platform L1); correct SEAL semantics (source vs processing); stays Grafana-parseable; lifecycle designation drives graceful routing.

**Weaknesses:** depends on discipline against folder sprawl; the `_FW`/API mismatch defeats name-only classification; not yet a fully ratified, documented standard (this digest is part of formalizing it); reconciliation with DAT's platform view is still open (see §7).

---

## 7. Open dialogue with DAT (per SME; email not transcribed)

The SME raised the application-view concerns with the DAT SRE team ("Sushant" replied but the thread did not resolve back to the SME). DAT's NFR standards reflect the **platform** viewpoint; HLT reflects the **application** viewpoint. The reconciliation — what's genuinely consistent across both, and the recommended greenfield — is the job of the [synthesis doc](nfr-consistency-and-greenfield.md). *(Recorded from the SME's account, not from the email contents.)*

Related: [[project-folder-naming-praocg]], [[project-description-metadata-plan]], [[project-controlm-remediation-spinoff]]
