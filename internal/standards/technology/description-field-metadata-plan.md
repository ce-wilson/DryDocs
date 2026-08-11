# VALUES TWIN — Description-Field Metadata Plan (real production examples & identifiers)

**Classification: Internal-Confidential.** This is the VALUE half of the split twin
(J14, 2026-07-27). The MECHANISM half — why the Description field, the key:value
format rules, the parsing hazards, the phased modernization plan, the SEAL
resolution hierarchy — is publishable and lives at
[`knowledge/standards/technology/description-field-metadata-plan.md`](../../../knowledge/standards/technology/description-field-metadata-plan.md).
Real folder/job names, SIDs, contact DLs, ServiceNow queues, MFT route ids, SEAL
ids and application names, the SEAL-ID format disclosure, and the escalation-table
schema identifiers live ONLY here.

Captured 2026-06-11 from SME (chat + production screenshots); relocated here
2026-07-27 (J14). Twin key (real SEAL ↔ synthetic sample id): see
[`folder-naming-convention.md`](folder-naming-convention.md#real--synthetic-twin-key-sanitized-sample-ids-used-in-publishable-files).

---

## Observed legacy vs modern (REAL production examples, P032-E0700-DMA)

### Folder `PRARAG-HLDM-89211-MLCM-ORIG-CRM-TRUST-DLY` (SMART)

| | Legacy | Modern (target pattern) |
|---|---|---|
| **Description** | `Generated Control-M Folder` *(autogen boilerplate)* | `datasetSeriesName: MLCM CRM \|SeriesSLA: 17:00 EST` |
| **Variables** | `NOTIFY` (email), `DRPBX_DIR`, `DROPBOX_BKP_DIR`, `FILEDATE=%%$ODATE`, `YARN_QUEUE` | adds **`SEAL=111027`**, `EMAIL_DL_L3`, `EMAIL_DL_L2`; renames `DRPBX_DIR`→`DROPBOX_DIR` |
| **Documentation** | File type, **empty** Doc Path/File | **URL** → SharePoint (INFOPROD docs) |
| **Created By** | o288926 *(personal SID, legacy)* | i738092 *(modern)* |

### Job `PARAD00010_MLCM_ORIGINATIONS_DAILY_CRM_INDICATOR_TOK_ONPM_FW` (FileWatcher)

| | Legacy | Modern (`PARAD0011b_…_FW`) |
|---|---|---|
| **Description** | `Contol-M File Watcher for TOK` *(typo in production)* | `FileDeliveryMechanism: MFTS_AGENT \| USER: ftsi37291 \| ENV: FTS2 \| ROUTE_ID: 372399 \| SourceOrigin: I \|SourceContact: DATA_ECO_SQLSRV_L2_SUPPORT@restricted.chase.com \| SourceSnowQueue: CCB_HLT_ASUP_SQLSRV` |
| **Watch Path** | `%%DRPBX_DIR.%%FILE_NM_PREFIX.%%BUS_DATE.%%FILE_NM_SUFFIX.%%EXTENSION` | `%%DROPBOX_DIR.Originations_Daily_CRM_Indicator_.%%$ODATE.tok` |
| **Local variables** | `FILE_NM_PREFIX=Originations_Daily_CRM_Indicator_`, `DRPBX_DIR=…`, `BUS_DATE=%%$ODATE`, **`FILE_NM_SUFFIX=.`**, `EXTENSION=tok` | **none** |

Real metadata key values observed: `USER: ftsi37291` (MFT service account),
`ROUTE_ID: 372399`, `SourceContact: DATA_ECO_SQLSRV_L2_SUPPORT@restricted.chase.com`,
`SourceSnowQueue: CCB_HLT_ASUP_SQLSRV`, `datasetSeriesName: MLCM CRM`.

### Standards-page values (C29, 2026-08-11) — and where they disagree with production

The four company standards pages captured at
[`../../controlm-config/reference/controlm-job-metadata-standards-capture.md`](../../controlm-config/reference/controlm-job-metadata-standards-capture.md)
carry their own worked values. They are transcribed in full there; only the
**disagreements with the production observation above** are worth repeating here,
because each one is a question for whoever ratifies the template:

| Key | Production (2026-06-11, observed) | Standards page (2026-08-11, documented) | The question |
|---|---|---|---|
| route id | `ROUTE_ID: 372399` — **numeric**, one value | `INBOUND_ROUTE: MFTS_RT_IN_CRM_001` / `OUTBOUND_ROUTE: MFTS_RT_OUT_APP_001` — **string, and split in two** | Is the numeric id the real MFTS route key and the string a documentation placeholder, or has the route-id format changed? A directional pair also cannot be stored in the single-valued observed key |
| transfer account | `USER: ftsi37291` | `USER: ftsi37291` | **Agrees** — the same real MFT service account appears in both, which is good corroboration that the standards page was written from this estate |
| environment | *(not observed on this job)* | `ENV: FTS2` | New |
| source contact | `SourceContact: DATA_ECO_SQLSRV_L2_SUPPORT@restricted.chase.com` — single address, CamelCase key | `SOURCE_CONTACT: <two addresses, semicolon-separated>` — SCREAMING_SNAKE key | Key renamed and the value became multi-valued |
| ServiceNow queue | `SourceSnowQueue: CCB_HLT_ASUP_SQLSRV` — the **source system's** queue, populated | `PDN_SNOW_QUEUE: NULL` — the **downstream consumer's** queue, unassigned | **Different subjects, not a rename.** A mapping that merges them is wrong |
| support DLs | folder variables `EMAIL_DL_L3` / `EMAIL_DL_L2` | job description tokens `EMAIL_DL_L3` / `EMAIL_DL_L2` **and** folder variables `L3_EMAIL_DL_NM` / `L2_EMAIL_DL_NM` | Two carriers and two spellings; unsettled (gate rider §G2) |

The standards pages also introduce values with no production counterpart yet: the
`JOB_ROLE: PUBLISHER` discriminator, the `PDN_DL` downstream consumer list, and the
`DevX-project` folder variable.

## SEAL identities (REAL)

- Folder variable **`SEAL=111027` = Home Lending Advice and Reporting**
  (SME-confirmed 2026-06-11; the earlier reading "111071" was a typo). This also
  ties `PRARA` (the folder's Application code) to SEAL 111027 via the declared
  folder variable.
- **`PRSRV` = SEAL 110865, Home Lending Servicing** (application-tied code created
  by our team; the data-lake SRE org does not support us).
- Name-embedded source SEAL in the worked folder: **89211** (5-digit legacy id).

## SEAL-ID format (REAL disclosure)

Sequential numbering, **currently 6 digits** (110865, 111027); older applications
have shorter ids (`89211` = 5 digits). Do not assume fixed width; store/compare as
integer or normalized string. The Control-M team only started tracking to SEAL in
the last couple of years — declared SEALs exist mostly on recent/modernized objects.

## Escalation/alerting table (REAL schema identifiers)

**`psgmgr.cm_escalation_db`**: join **`EJOBNAME VARCHAR2(64 BYTE)`** = `JOB_NAME`;
the SEAL is **`ECOMPONENT VARCHAR2(40 BYTE)`**, stored with a decimal suffix —
e.g. **`111027.00`**. Normalize on join: strip the trailing `.00` (or cast to
integer) before matching against SEAL keys. Gives a per-job, DECLARED SEAL from
escalation config — slots between tier 1 and tier 2 of the resolution hierarchy
when present.

> Note (J14): the schema/column identifiers `psgmgr` / `cm_escalation_db` /
> `EJOBNAME` / `ECOMPONENT` also appear in other tracked files (skills, gate
> prompts, taxonomy-ontology map, remediation TDD) — an IDENTIFIER class distinct
> from data values, not ruled on yet (same residual class as the platform
> vocabulary; see the 2026-07-27 IDEAS question). This twin is their authoritative
> home either way.
