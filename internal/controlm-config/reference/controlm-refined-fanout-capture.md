# Capture — the downstream fan-out: one refined dataset, three targets

**Corpus:** INTERNAL (live production Control-M definitions — real FIDs, schemas, hosts,
service accounts, addresses and author SIDs). **Never leaves `internal/`.**
**Captured:** 2026-08-11 (desktop), from eight SME screenshots of the Control-M GUI.
**Status:** 🟠 capture + analysis. Nothing here is ratified.
**Mechanism twin (publishable):**
[`knowledge/standards/technology/controlm-guidelines-and-standards.md`](../../../knowledge/standards/technology/controlm-guidelines-and-standards.md) §13.

> **Reading order.** Part A is what the screenshots show. Part B is what it means for the
> standard. Part C is the defect list. Part D is the corrections this set forces on work
> already committed — including one on my own C30 rationale.

---

## Part A — what was captured

### A1. The folder set — four siblings, one source of record

All four are SMART folders on Control-M server `P032-E0700-DMA`, application `PRSRV`,
sub-application `PRSRV-AOC`, host group `PRECO-VSI-LNCH`, run-as `a_ccb_drc_np`.

| Folder | Target | Lifecycle |
|---|---|---|
| `PRSRVG-HLDM-110865-MSP465_EXA-RFND-DLY` | — (refine stage) | strategic |
| `PRSRVG-HLDM-110865-MSP465-SNF-RFND-DLY` | Snowflake | **strategic** |
| `PRSRVG-HLDM-110865-MSP465_EXA-PROV-DLY` | Oracle Exadata | **legacy — decom path** |
| `PRSRVG-HLDM-110865-MSP465-WRKLAYER-PROV-DLY` | Teradata | **legacy — decom path** |

**The separator is not consistent.** The two Exadata folders use `MSP465_EXA` (underscore);
the other two use `MSP465-SNF` and `MSP465-WRKLAYER` (hyphen). A SQL parse that splits the
folder name on `-` gets a different field count depending on which folder it is reading.

### A2. Folder variables — `…MSP465_EXA-RFND-DLY`

`Enforce Validations`: **unchecked**. `Site Standard`: **-- None --**. All variables are
scope `Local` at the folder.

| Name | Value |
|---|---|
| `SOR` | `msp465` |
| `SOR_UP` | `MSP465` |
| `RPATH` | `CDS/sor/caip_msp465_pvt/pset` |
| `ODAT` | `%%$ODATE` |
| `SCHEMA_ORA` | `MORTGMGR` |
| `DBNAME_ORA` | `infoprod` |
| `CURRENVIRON` | `%%SUBSTR %%DATACENTER 1 1` |
| `ENV_D` / `ENV_Q` / `ENV_P` | `dev` / `uat` / `prod` |
| `ENV` | `%%ENV_%%CURRENVIRON` |
| `CLUST` | `prod` |
| `FID_D` / `FID_Q` / `FID_P` | `B022876` / `H024490` / `K024761` |
| `FID` | `%%FID_%%CURRENVIRON` |
| `PREV_ODATE` | `%%$CALCDATE %%$ODATE -1` |
| `PSET_PATH` | `/home/aiadmin/projects/sandboxes/CDS/sor/caip_msp465_pvt/pset/` |
| `RPATH` **(second declaration)** | `/Data/abinitio/sandboxes/CDS/sor/caip_msp465_pvt/pset/` |
| `BIN_PATH` | `/apps/anaconda/4.6.14/3/bin/python3` |
| `ev_WRAPPER_SCRIPT_DIR` | `/apps/cds/abioncloud/script/` |
| `ev_SCRIPT_DIR` | `/Data/abinitio/sandboxes/caip_aws/` |
| `CONFIG_JSON` | `/data/uds/ccb_data_reservoir_consumption/110865/cfg/hl-srv-abi-aws-config.json` |
| `UNIX_WRAPPER_SCRIPT` | `runScript.sh` |
| `NOTIFY` | `ICDW_MB_L2_Support@jpmorgan.com` |
| `EMAIL_GRP` | `ICDW_MB_L2_Support@jpmorgan.com` |
| `EMAIL_GRP_S` | `ICDW_MB_L2_Support@jpmorgan.com` |
| `IMAGE_NAME` | `msp465` |

### A3. The five jobs captured

| # | Job | Folder | Description |
|---|---|---|---|
| 1 | `PSRVD0070_MSP465_ADDITIONAL_CONTACT_AWS_RFND` | `_EXA-RFND-DLY` | `CDC Job [ Legacy Name : PECOD006_MSP465_ADDITIONAL_CONTACT_CD ]` |
| 2 | `PSRVD0070_MSP465_ADDITIONAL_CONTACT_SNF_AWS_RFND` | `-SNF-RFND-DLY` | `MSP_ADDITIONAL_CONTACT INFO1 VIEWS LOAD IN AWS` |
| 3 | `PSRVD0080_MSP465_ADDITIONAL_CONTACT_ONPM_EXALD` | `_EXA-PROV-DLY` | `Oracle Load Ready File Job [ Legacy Name : PECOD008_MSP465_ADDITIONAL_CONTACT_LRF_EXA_LD ]` |
| 4 | `PSRVD0080_MSP465_LOAN_EVENT_W1_META_LRF_ONPM_TDLOAD` | `-WRKLAYER-PROV-DLY` | `Teradata Load Job to load into MSP465_LOAN_EVENT_W1_META [ Legacy Name : PECOD005_MSP465_LOAN_EVENT_W1_META_LRF_TD_LD ]` |
| 5 | `PSRVD0080_MSP465_WKLAYER_VALIDATION_ONPM_TDLOAD` | `-WRKLAYER-PROV-DLY` | `Load validation job for wk layer [ Legacy Name : PECOD009_MSP465_WKLAYER_VALIDATION ]` |

All five: job type **OS**, priority Low, `Critical (reserve resources)` unchecked, no
pre- or post-execution command, "Submitted past next New Day", "Keep active for: 5 days".

### A4. Command lines, verbatim

**Job 1 — CDC / refine (AWS launcher form):**
```
sh %%ev_WRAPPER_SCRIPT_DIR.%%UNIX_WRAPPER_SCRIPT -c %%CONFIG_JSON -f %%FID -e %%CLUST
   -a %%IMAGE_NAME -p %%JOBNAME-%%ODATE-%%ORDERID-%%RUNCOUNT
   -g "%%PSET_PATH/cdc/%%SOR._%%ENTITY_NM._ingestion_cdc.pset" -s 30 -t 3600 -r %%RESOURCE
```

**Job 2 — Snowflake views load (same launcher, different pset):**
```
sh %%ev_WRAPPER_SCRIPT_DIR.%%UNIX_WRAPPER_SCRIPT -c %%CONFIG_JSON -f %%FID -e %%CLUST
   -a %%IMAGE_NAME -p %%JOBNAME-%%ODATE-%%ORDERID-%%RUNCOUNT
   -g "%%PSET_PATH/%%SOR._%%ENTITY_NM._views_entity.pset" -s 30 -t 3600 -r %%RESOURCE
```

**Job 3 — Oracle load (on-prem wrapper form):**
```
%%ev_SCRIPT_DIR/MB/mb_common/bin/hadoop_abi_wrapper.ksh ${RPATH}/ora_load
   %%SOR._%%ENTITY_NM._ingestion_lrf_ora_plan.pset
   " -DATABASE_NM %%DBNAME_ORA -TGT_SCHEMA_NM %%SCHEMA_ORA"
```

**Job 4 — Teradata load:**
```
%%ev_SCRIPT_DIR.hadoop_abi_wrapper.ksh MB/rmi_pvt/pset
   msp465_loan_event_w1_meta_lrf_td.pset "-TGT_SCHEMA_NM %%SCHEMA_TD"
```

**Job 5 — Teradata work-layer validation:**
```
%%ev_SCRIPT_DIR.hadoop_abi_wrapper.ksh MB/rmi_pvt/pset/semantic/msp465
   rmi_msp465_wklayer_validation.pset "-SOR_NAME msp465 -TGT_SCHEMA_NAME %%SCHEMA_TD"
```

### A5. Job-scope variables

| Job | Declared locally |
|---|---|
| 1, 2, 3 | `ENTITY_NM = additional_contact` · `RESOURCE = exlarge` |
| 4 | `ENTITY_NM = loan_event_w1` *(only)* |
| 5 | `SCHEMA_TD = ICDW_MB_PRSN_ECO_V` · `RESOURCE = large` |

### A6. Dependencies as the GUI reports them

| Job | Predecessors | Successors |
|---|---|---|
| 1 | `PSRVD0060_MSP465_CTL_AWS_CPY` ×3, `PSRVD0050_MSP465_ADDITIONAL_CONTACT_AWS_TRUST` ×2 | 6 successors |
| 3 | `PSRVD0070_MSP465_ADDITIONAL_CONTACT_AWS_RFND` ×2 | `PSRVD9999_MSP465_EXALOAD_DONE_ONPM_DUMMY` ×2 |
| 5 | 12 predecessors | `PSRVD0099_MSP465_WORK_CLOSE_ONPM_HK` |

The repeated rows are **not** screenshot duplicates: the GUI lists one row per in-condition,
so three rows naming `…CTL_AWS_CPY` means three distinct conditions from one producer job.

### A7. Quantitative resources — they name the platform

| Job | Resource pools (all quantity 1) |
|---|---|
| 1 | `PRAOC-DAT-VSI`, `PRECO-LNCH-CTRL-VSI`, `PRSRV-HL-QR` |
| 3 | `PRAOC-DAT-VSI`, `PRECO-LNCH-CTRL-VSI`, **`PRSRV-HLDM-ORAC-EXA`**, `PRSRV-HL-QR` |
| 5 | `PRECO-LNCH-CTRL-VSI`, `PRAOC-ONPM-VSI`, **`PRICD-TD-ST04-VSI`**, `PRSRV-HL-QR` |

`PRSRV-HLDM-ORAC-EXA` appears only on the Oracle load; `PRICD-TD-ST04-VSI` only on the
Teradata one.

### A8. Schedules, notification, authorship

- Calendars: `MON-SAT-TAG` (jobs 1–4), `MON-SAT-RET-TAG` (job 5).
- On-Do Actions, every job: **`When Job ended Not OK → Send mail notification to %%EMAIL_GRP`**.
- `Created By` = `o288926` on **all five jobs**, while the audit trail differs per job:

| Job | Creation user / date | Modification user / date |
|---|---|---|
| 1 | `n255577p` · 10/14/2024 | — |
| 3 | `e412464p` · 4/28/2025 | `n518921p` · 7/6/2026 |
| 5 | `o714455p` · 9/16/2024 | `f749643p` · 6/19/2025 |

---

## Part B — what it teaches the standard

### B1. The fan-out is a stage the standard does not have

C30/C31 modeled **ingestion**: watcher → placement → trust, ending where the data lands.
This set is what happens after, and its shape is different: **one refined dataset fans out to
three targets on two different lifecycles.** Stage numbers carry it:

```
0050 TRUST → 0060 CTL_AWS_CPY → 0070 RFND ─┬─→ 0070 SNF_AWS_RFND    (Snowflake, strategic)
                                            ├─→ 0080 ONPM_EXALD      (Oracle, decom)
                                            └─→ 0080 ONPM_TDLOAD     (Teradata, decom)
                                                     ↓
                                        9999 DUMMY / 0099 HK (close)
```

The strategic path and the decommissioning paths run **side by side in the same estate**, and
nothing in a job definition says which is which. That is the fact a support decision needs
most — *is this load on its way out?* — and it currently exists only in the SME's head.

### B2. Target platform and channel are two axes, not one

`PSRVD0070_MSP465_ADDITIONAL_CONTACT_SNF_AWS_RFND` carries **both** `SNF` and `AWS`.
Snowflake is the target platform; AWS is the execution channel. The C31 §5.4 grammar has one
`{CHANNEL}` slot and cannot express that job. Observed values:

- **Platform:** `SNF` (Snowflake), `EXA` (Oracle Exadata), `TD` (Teradata) — the last two via
  the `EXALD` / `TDLOAD` type suffix rather than a separate token.
- **Channel:** `AWS`, `ONPM`.

### B3. The job-type vocabulary is much larger than FW / PLCT / TRUST

Deployed suffixes: `TRUST`, `CPY`, `RFND`, `EXALD`, `TDLOAD`, `HK`, `DUMMY` — plus the
ingestion set. A standard that enumerates four types cannot validate this folder.

### B4. `LEGACY_NAME` is a description token already in use

Four of five descriptions carry `[ Legacy Name : PECOD…_… ]`. That is **the decommissioning
crosswalk** — old job → new job — living in prose, in the one field with no other home for it.
It is exactly what the description-carries-metadata rule is for, and it should be a registered
token rather than a convention.

The rest of each description is the job's role in prose ("CDC Job", "Oracle Load Ready File
Job", "Load validation job for wk layer"), i.e. `JOB_ROLE` unstructured.

### B5. Environment selection by datacenter prefix — a supported pattern, not a defect

```
CURRENVIRON = %%SUBSTR %%DATACENTER 1 1      → "P"
FID         = %%FID_%%CURRENVIRON             → %%FID_P → K024761
ENV         = %%ENV_%%CURRENVIRON             → %%ENV_P → prod
```

A variable whose **name** is composed from another variable's value. One folder definition
promotes across dev/uat/prod with no edit — genuinely good practice, and it extends the
datacenter-naming finding already recorded (the DC name encodes the default run time; its
**first character encodes the environment tier**).

The cost is real and must be stated rather than discovered: **a static resolver cannot resolve
`%%FID`.** It has to evaluate `%%SUBSTR` first, then re-resolve. Any lineage pass that treats
`%%FID` as an ordinary reference gets a literal `CTMERR` or a miss, and the FID is a join key.

### B6. The resource pools are an independent platform signal

`PRSRV-HLDM-ORAC-EXA` on the Oracle job and `PRICD-TD-ST04-VSI` on the Teradata one name the
target platform **without parsing a job name**. Two independent signals that should agree; where
they disagree, one of them is a typo — and that is a detector, not a judgement call.

---

## Part C — defects this set shows

| # | Defect | Rule |
|---|---|---|
| 1 | `RPATH` declared **twice** in one folder with different values (`CDS/sor/…` vs `/Data/abinitio/sandboxes/CDS/sor/…`) | R31 / **NEW: duplicate declaration in one scope** |
| 2 | `NOTIFY`, `EMAIL_GRP`, `EMAIL_GRP_S` — three names, one value, one concept | R2 / R33 |
| 3 | `ev_WRAPPER_SCRIPT_DIR`, `ev_SCRIPT_DIR` — lowercase prefix, violating UPPER_SNAKE | R2 |
| 4 | Folder separator inconsistent: `MSP465_EXA` vs `MSP465-SNF` | **NEW: folder-name delimiter** |
| 5 | `WKLAYER` (job) vs `WRKLAYER` (folder) — a straight typo in a name that is parsed | R2 |
| 6 | Two paths to one wrapper: `%%ev_SCRIPT_DIR/MB/mb_common/bin/hadoop_abi_wrapper.ksh` vs `%%ev_SCRIPT_DIR.hadoop_abi_wrapper.ksh` | R36 |
| 7 | `${RPATH}` (shell) beside `%%RPATH` (Control-M) — same name, two carriers, two resolvers | **NEW: carrier collision** |
| 8 | `SCHEMA_TD` declared at job scope on job 5, referenced by job 4 which does not declare it | R35 |
| 9 | Job 4 declares no `RESOURCE` but its siblings do; the launcher takes `-r %%RESOURCE` on the AWS form only | R30 (conditional) |
| 10 | `Created By = o288926` on all five jobs while three different users actually created them | **NEW: stale authored provenance** |
| 11 | `Enforce Validations` off, `Site Standard: -- None --` on the folder | R-advisory (C31 §9) |
| 12 | Two jobs share `PSRVD0080` in one folder | R29 (numbering) |

Defect 10 matters beyond tidiness: `Created By` is an authored field that travels when a job is
copied, so it records **the template's author, not the job's**. Anything treating it as
authorship is wrong, and the audit-envelope work (M3/M4) should read the Creation/Modification
user instead.

---

## Part D — corrections this set forces on committed work

**D1. The DOMAIL rationale was too strong, and this folder disproves half of it.**
C30 §5.3.1 and R40 argue the mail block is safe to delete partly because its destination is
"declared nowhere" — every such block already resolving to `CTMERR` and mailing nothing. That
is **true of the DPL-generated folders** and **false here**: this folder declares `NOTIFY`,
`EMAIL_GRP` and `EMAIL_GRP_S`, all three to a real L2 support address, and its On-Do block
would really send.

The SME ruling is unchanged — mail goes, the incident is the call to action. What changes is the
reason: deletion is **deliberate**, not costless, and on hand-built Ab Initio folders it removes
a mail path that works today. Fix the argument in the standard rather than carry one the next
folder disproves.

**D2. §5.4's grammar is wrong as written** — see B2. One `{CHANNEL}` slot cannot describe
`…_SNF_AWS_RFND`.

**D3. The four-job-type framing is too narrow** — see B3.

---

Related: [`controlm-job-metadata-standards-capture.md`](controlm-job-metadata-standards-capture.md)
(the ingestion half) · [`controlm-pipeline-stub-capture.md`](controlm-pipeline-stub-capture.md)
(the DPL generator) · [`../../remediation/standards-rules-registry.md`](../../remediation/standards-rules-registry.md)
