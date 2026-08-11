# VALUES TWIN — Control-M Greenfield Job Standard (real folder, accounts and ids)

**Classification: Internal.** This is the VALUE half of the split twin (J14). The MECHANISM half —
the scope ladder, the naming rule, the derived-handle pattern, the description token sets, the
`pipelineId` carrier ruling and every rationale — is publishable and lives at
[`knowledge/standards/technology/controlm-greenfield-job-standard.md`](../../../knowledge/standards/technology/controlm-greenfield-job-standard.md).

Only what cannot leave `internal/` is here: the real folder and job names, the run-as and MFT
service accounts, the SEAL, the FID, the dataset GUIDs, the author id, the DL addresses and the
paths. Captured 2026-08-11 (C30) from five Control-M UI screenshots (gitignored in the repo root:
`control-m-folder.png`, `control-m-job.png`, `control-m-job-fw-tok.png`, `control-m-job-plct.png`,
`control-m-job-trust.png`).

**Companions:** the standards corpus at
[`../../controlm-config/reference/controlm-job-metadata-standards-capture.md`](../../controlm-config/reference/controlm-job-metadata-standards-capture.md)
· the generator at
[`../../controlm-config/reference/controlm-pipeline-stub-capture.md`](../../controlm-config/reference/controlm-pipeline-stub-capture.md)
· the rules at [`../../remediation/standards-rules-registry.md`](../../remediation/standards-rules-registry.md) (R30–R40).

> ⚠️ **The folder was MID-EDIT when captured.** Some watcher findings below are the SME's own
> unfinished conversion to the new `FILE_*` scheme, not deployed breakage. They are marked, and they
> are kept because they are the clearest worked example of the failure the standard prevents — not
> as evidence of a broken production job.

---

## 1. The observed folder

**`PRSRVG-HLDM-110865-UDM-TRUST-UPD`** (SMART), Control-M server `P032-E0700-DMA`.

| Field | Value |
|---|---|
| Description | `User provided lookup fields for:` *(truncated — the sentence ends at the colon)* |
| Order Method | None (Manual Order) |
| Run As | `a_ccb_drc_np` |
| Application / Sub Application | `PRSRV` / `PRSRV-DCL` |
| Enforce Validations | **unchecked** |
| Site Standard | `-- None --` |
| Created By | `o288926` |
| Documentation | URL → `http://go/hlsss` |
| Priority | Low |

**Folder variables (all four):**

| Name | Value |
|---|---|
| `DEVX_KEY` | `CLHLSERV` |
| `EMAIL_DL_L3` | `hlsss_app_dev@restricted.chase.com` |
| `EMAIL_DL_L2` | `ICDW_MB_L2_Support@jpmorgan.com` |
| `EMAIL_DL_PDN` | `HL_Servicing_UDM_Delay@restricted.chase.com;Higgins_Team_All@restricted.chase.com` |

Note the folder declares **`DEVX_KEY`**, not REQ-1's `DevX-project`, and **`EMAIL_DL_L2/L3`**, not
REQ-1's `L2_EMAIL_DL_NM`. Both live spellings are the legal ones — see the mechanism half §2.

**13 jobs, three datasets × four jobs**, host group `PRECO-VSI-COMP` throughout:

| Dataset | DAT watcher | TOK watcher | Placement | Trust |
|---|---|---|---|---|
| `STG_SRVC_STATE_LKP` | `PSRVD9020_HLUDM_STG_SRVC_STATE_LKP_DAT_ONPM_FW` | `PSRVD9021_…_TOK_ONPM_FW` | `PSRVD9022_…_AWS_PLCT` | `PSRVD9023_…_AWS_TRUST` |
| `STG_SRVC_TEAM_LKP` | `PSRVD9030_…_DAT_ONPM_FW` | `PSRVD9031_…_TOK_ONPM_FW` | `PSRVD9032_…_AWS_PLCT` | `PSRVD9033_…_AWS_TRUST` |
| `STG_SRVC_DEF_LKP` | `PSRVD9040_…_DAT_ONPM_FW` | `PSRVD9041_…_TOK_ONPM_FW` | `PSRVD9042_…_AWS_PLCT` | `PSRVD9043_…_AWS_TRUST` |

Numbering is **dataset-grouped** (`902x` / `903x` / `904x`), not the HLT functional bands.

---

## 2. Real values behind the mechanism half

| Mechanism half | Real value |
|---|---|
| tenant dropbox | `/data/uds/ccb_data_reservoir-consumption/dropbox/UPD/` |
| config path | `/data/uds/ccb_data_reservoir-consumption/110865/cfg/hludm_prod_epv_conf.json` |
| launcher | `/apps/tenants/dpl_utils/dt-accelerators/dt-launcher.sh` |
| `SEAL` | `110865` |
| `FID` | `K024761` |
| `APP_NAME` | `hludm-srvc-prod` |
| artifact (`IMG`) | `hludm-prod-img` — a bare image NAME, no registry |
| `PIPELINE_ID` / `-pipeline` | `a6a248b2-0693-4331-af57-079e2802bb58` |
| dataset GUID | `103228cc-f785-35c4-be71-4922d1883a2e` |
| dataset version | `1.0.0` |
| `DATA_FLOW` | `STG_SRVC_STATE_LKP` |
| MFT service account | `sftpmsp` |
| MFTS instance | `ST 6.0 - FTS2` → the standard's `FTS_ID: FTS2` |
| `REC_ID` | `464468,464468` |
| `SOURCE_CONTACT` | `jason.simon@jpmchase.com` — an individual, not a DL (open item 2) |
| pool reference | `%%\\STG_SRVC_STATE_LKP\PROID` |

Both file watchers carry the identical description:

```
DELIVERY_MECHANISM: MFTS_AGENT | USER: sftpmsp | ENV: ST 6.0 - FTS2 | REC_ID: 464468,464468  | SOURCE_CONTACT: jason.simon@jpmchase.com
```

---

## 3. Findings on the observed folder

Split by cause, because the split changes what to fix.

### 3.1 Hand drift AWAY from generator output — the generator had these right

| Observed | Generator emits | Effect |
|---|---|---|
| `DATA_FLOW` | `%%DATAFLOW` | misses `FACT_REGISTRY`; **no lineage row for the dataset at all** |
| `IMG` | `%%IMAGE` (registered alias → `ARTIFACT_URI`) | misses the registry; no artifact row |
| `proid` (TRUST) vs `PROID` (PLCT) | `%%PROID` | case drift between siblings |
| `%%TIMEOUT` referenced, declared nowhere | `%%TIMEOUT` = `1` (PLCT) / `24` (TRUST) | resolves to `CTMERR` and reaches the launcher as literal text |
| TRUST: `DS_ID`=`1.0.0`, `DS_VER`=`103228cc-…` | `%%DS_ID`→dataset_id, `%%DS_VER`→dataset_version | **swapped** vs PLCT — both names resolve, so both write a fact row and one is false |
| `PIPELINE_ID` declared beside the `-pipeline` literal | no `PIPELINE_ID` variable at all | two carriers, silently divergeable |
| PLCT declares `LAUNCHER_SCRIPT_PATH`, references `%%SCRIPT_PATH`; TRUST declares `SCRIPT_PATH` | **neither builder emits a launcher variable** | hand-added twice, spelled two ways, one broken |

Root cause: the generator emits a partial job and expects a folder `AUTOEDIT` block that is never
emitted, so the missing variables get hand-added per job. ~17 job-scope declarations on each of
PLCT and TRUST, hand-copied.

### 3.2 Genuine gaps

- `ETL_PLATFORM`, `ETL_ARTIFACT_KIND`, `ETL_PLATFORM_FLAGS` absent from both command jobs, though
  REQ-4 requires them on every `cmd` job.
- `%%DROPBOX_DIR` and `%%DROPBOX_BKP_DIR` referenced by the TRUST post-command and declared at
  neither job nor folder scope.
- `%%NOTIFY` — every generated job's `DOMAIL DEST` — declared nowhere. Per the SME this is **not** a
  wiring gap to close: notification is being removed and the incident is the call to action.
- `ETL_ARTIFACT_URI` equivalent (`IMG`) holds a bare image name, so NF-SEC-2's approved-repository
  boundary cannot be evaluated.
- Folder description truncated mid-sentence.
- `Enforce Validations` off, `Site Standard: -- None --`.

### 3.3 Mid-edit residue — NOT deployed defects

- **TOK watcher**: path and `cat` reference `%%FILE_NM_PREFIX` and `%%EXTENSION`; the declared names
  are `FILE_PREFIX` and `FILE_EXTENSION`. A conversion finished on the declarations and not on the
  references.
- **DAT watcher**: declares `FILE_BUSINESS_DATE` then uses `%%$ODATE` directly; composes
  `%%FILE_PATH%%FILE_PREFIX` with no delimiter (the adjacent-reference hazard).
- **DAT watcher** carries `cat %%FILE_PATH%%FILE_PREFIX.%%$ODATE.%%FILE_EXTENSION` with
  `FILE_EXTENSION=.txt` — a **DAT** file. The token-cat NFR's MUST NOT. Confirm whether this is also
  residue; if deployed it is the one finding with an operational (sysout-flood) consequence.

---

## 4. The greenfield folder, with real values

```
FOLDER  PRSRVG-HLDM-110865-UDM-TRUST-UPD          (SMART)
  ENV                  = prod
  FID                  = K024761
  SEAL                 = 110865
  APP_NAME             = hludm-srvc-prod
  ALIAS                = hludm-srvc-prod
  CONF_PATH            = /data/uds/ccb_data_reservoir-consumption/110865/cfg/hludm_prod_epv_conf.json
  LAUNCHER_SCRIPT_PATH = /apps/tenants/dpl_utils/dt-accelerators/dt-launcher.sh
  ETL_PLATFORM         = <java|pyspark>                    ← ADD (REQ-4)
  ETL_ARTIFACT_URI     = <registry-qualified URI>           ← was IMG=hludm-prod-img (bare name)
  ETL_ARTIFACT_KIND    = container                          ← ADD
  ETL_PLATFORM_FLAGS   = -i
  TIMEOUT              = 24                                 ← ADD (was referenced, undeclared)
  POLLING_INTERVAL     = 1
  FILE_BKP_DIR         = <dropbox backup dir>               ← ADD (was referenced, undeclared)
  DEVX_KEY             = CLHLSERV
  EMAIL_DL_L3          = hlsss_app_dev@restricted.chase.com
  EMAIL_DL_L2          = ICDW_MB_L2_Support@jpmorgan.com
  EMAIL_DL_PDN         = HL_Servicing_UDM_Delay@restricted.chase.com;Higgins_Team_All@restricted.chase.com

  SUB-FOLDER  STG_SRVC_STATE_LKP                   (× 3, one per dataset)
    DATAFLOW           = STG_SRVC_STATE_LKP         ← was DATA_FLOW (no lineage row)
    DS_ID              = 103228cc-f785-35c4-be71-4922d1883a2e
    DS_VER             = 1.0.0                      ← was swapped with DS_ID on TRUST
    PROID              = %%\\STG_SRVC_STATE_LKP\PROID   ← one spelling, uppercase
    FILE_DIR           = /data/uds/ccb_data_reservoir-consumption/dropbox/UPD/
    FILE_PREFIX        = STG_SRVC_STATE_LKP_
    FILE_BUSINESS_DATE = %%$ODATE
    F_NM_DAT           = %%FILE_PREFIX.%%FILE_BUSINESS_DATE..txt
    F_NM_TOK           = %%FILE_PREFIX.%%FILE_BUSINESS_DATE..tok
    F_FQN_DAT          = %%FILE_DIR.%%F_NM_DAT
    F_FQN_TOK          = %%FILE_DIR.%%F_NM_TOK

      JOB  PSRVD9020_…_DAT_ONPM_FW      FILE_EXTENSION = .txt
        Path      : %%F_FQN_DAT
        Post-exec : (none — DAT must not be cat'd)
        Desc      : DELIVERY_MECHANISM: MFTS_AGENT | USER: sftpmsp | FTS_ID: FTS2 |
                    REC_ID: 464468,464468 | SOURCE_CONTACT: <DL, open item 2>

      JOB  PSRVD9021_…_TOK_ONPM_FW      FILE_EXTENSION = .tok
        Path      : %%F_FQN_TOK
        Post-exec : cat %%F_FQN_TOK
        Desc      : (as above)

      JOB  PSRVD9022_…_AWS_PLCT         (no job-scope variables)
        Desc      : JOB_ROLE: PLACEMENT
        Cmd       : %%LAUNCHER_SCRIPT_PATH -env %%ENV
                    -pipeline a6a248b2-0693-4331-af57-079e2802bb58
                    -dataset %%DS_ID -version %%DS_VER -bd %%BUS_DATE -od %%ODATE
                    -datFile %%FILE_DIR/%%F_NM_DAT -tokFile %%FILE_DIR/%%F_NM_TOK
                    -fid %%FID -timeout %%TIMEOUT -sleep %%POLLING_INTERVAL -p
                    -conf %%CONF_PATH

      JOB  PSRVD9023_…_AWS_TRUST        (no job-scope variables)
        Desc      : JOB_ROLE: TRUST_INGEST
        Cmd       : %%LAUNCHER_SCRIPT_PATH -env %%ENV
                    -pipeline a6a248b2-0693-4331-af57-079e2802bb58
                    -appName %%APP_NAME -alias %%ALIAS -seal %%SEAL
                    -dataflow %%DATAFLOW -img %%ETL_ARTIFACT_URI
                    -bd %%BUS_DATE -od %%ODATE -fid %%FID -proId %%PROID
                    -timeout %%TIMEOUT -sleep %%POLLING_INTERVAL -i -conf %%CONF_PATH
        Post-exec : mv %%FILE_DIR/%%F_NM_DAT %%FILE_BKP_DIR/%%F_NM_DAT;
                    mv %%FILE_DIR/%%F_NM_TOK %%FILE_BKP_DIR/%%F_NM_TOK;
```

**Count:** ~19 folder + (3 × 11 sub-folder) + (12 × ≤1 job) ≈ **64 declarations**, against roughly
**204** today (17 × 12 jobs). More importantly: **one** copy of `LAUNCHER_SCRIPT_PATH`, one of
`DS_ID`, one composition of each filename.

`-pipeline` stays a literal by ruling (mechanism half §4.3); the `PIPELINE_ID` variable is removed
from both command jobs.

---

## 5. Real ↔ synthetic key

The mechanism half and the test fixtures use these stand-ins:

| Real | Sanitized |
|---|---|
| `110865` | SEAL `70002` (the 70001–70099 synthetic block) |
| `STG_SRVC_STATE_LKP` | `SAMPLE_LKP` |
| `PRSRVG-HLDM-110865-UDM-TRUST-UPD` | `FOLDER-SYNTH-GREEN` |
| `/data/uds/ccb_data_reservoir-consumption/dropbox/UPD/` | `/data/synth/dropbox/UPD/` |
| `K024761` | `S000001` |
| `sftpmsp` | `svc_mfts_sample` |
| the DL addresses | `l2@example.invalid` / `l3@example.invalid` / `pdn@example.invalid` |
| `hludm-prod-img` | `sample-1.0.0.jar` |
| `103228cc-f785-35c4-be71-4922d1883a2e` (dataset GUID) | `00000000-0000-4000-8000-000000000001` |
| `a6a248b2-0693-4331-af57-079e2802bb58` (pipeline GUID) | the same synthetic UUID — the fixtures do not distinguish them |

Folder-naming twin key: see
[`folder-naming-convention.md`](folder-naming-convention.md#real--synthetic-twin-key-sanitized-sample-ids-used-in-publishable-files).
