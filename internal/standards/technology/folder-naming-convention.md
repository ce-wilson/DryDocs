# VALUES TWIN — Control-M Folder Naming Convention (real registry & inventory)

**Classification: Internal-Confidential.** This is the VALUE half of the split twin
(J14, 2026-07-27). The MECHANISM half — the PRAOCG grammar, position semantics,
platform-vs-application caveat, resolution rules — is publishable and lives at
[`knowledge/standards/technology/folder-naming-convention.md`](../../../knowledge/standards/technology/folder-naming-convention.md).
Real registry rows, real SEAL ids, real application names, and real production
inventory live ONLY here. Never copy a value from this file into any file outside
`internal/` — reference by stable id instead (PUBLISH-BOUNDARY.md rule for agents).

Captured 2026-06-11 from SME (chat); relocated here 2026-07-27 (J14).

---

## Known application-code registry (REAL — extend as confirmed)

| Code | Type | Meaning | SEAL tie |
|---|---|---|---|
| `PRAOC` | **Platform** | Ab Initio ETL platform (data lake, SRE-dictated) | **Carries the PLATFORM's SEAL** — see correction below |
| `PRDCL` | **Platform** | Java/PySpark jobs loading to AWS cloud (SRE-dictated) | Carries the platform's SEAL |

> **CORRECTED 2026-08-05 (SME).** "No direct SEAL" was wrong as stated, and the standards
> diagram's "framework, no direct SEAL" means something narrower. **A platform app code
> DOES carry a SEAL — the platform's own.** The Data Lake owns `AOC` and the app-code
> registry gives it the Data Lake's SEAL; what the code does not identify is the
> **consuming** application, because *other SEALs' jobs run under that same code*.
>
> Two consequences worth keeping straight:
> - The K8 loader's "declare a platform code by leaving `app_id` EMPTY" encoding discards
>   a true fact (the platform's own SEAL) in order to signal a different one (this code
>   does not identify consumers). An explicit row kind is the right discriminator; the
>   store's app_id-required check is correct as it stands.
> - Under OWNER-NOT-USER, a platform's OWN utility folders legitimately belong to the
>   platform's SEAL. So "platform code" does not mean "attributes nothing" — it means
>   attribution is per folder, and some of those folders resolve to the platform itself.
>
> Separately and NOT the same thing: `DDC` shows codes get **repurposed** over time
> because the 3-char namespace is scarce. That is a durability problem (a code is an
> as-of identifier), not a many-consumers problem.
| `PRSRV` | **Application** | Home Lending **Servicing** — created by our team (same platform, similar standards for Grafana dashboards) | **SEAL 110865** |
| `PRARA` | *(observed)* | Application field of the worked example folder (`PRARAG-…`); `ARA` ≈ Advice & Reporting? *(mnemonic unconfirmed)* | **SEAL 111027** Home Lending Advice and Reporting (via declared folder variable; code-type to confirm) |

### THE PLATFORM-CODE LIST — complete as of 2026-08-05 (SME standards page)

**This is the tier-2 list the K8 loader needs and could not previously get** (see the
mechanism twin's "Tier discrimination" section). Sourced from the DAT SRE standard's
Framework → APPCODE table. Every row here is a **framework/platform** code: the
`PR<code>` application is a framework with **no direct SEAL**, and its folders belong to
many consuming applications.

| Framework | App (PR-form) | APPCODE | Server | Software-registry product |
|---|---|---|---|---|
| DPL (Data Pipeline On Cloud, AWS) — also PySpark transformations | `PRDCL` | `DCL` | P032 | **no product row yet** (the standing gap) |
| Ab Initio (on cloud) | `PRAOC` | `AOC` | P032 | `abinitio` |
| Informatica → Snowflake | `PRIOS` | `IOS` | P014 | `informatica-powercenter` |
| Snowflake ETL *(the standard's label — see the SFS note below)* | `PRSFS` | `SFS` | P014 | **no product row yet** (`snowflake`, the data platform) |
| ABICOLO (DCM) — Informatica TD→SF + DMV | `PRDDC` | `DDC` | P032 | `informatica-powercenter` (+ DMV) |
| (legacy) Data Pipeline — predecessor of PRDCL | `PRDPL` | `DPL` | — | same gap as DCL |

⚠️ **`SFS` typing correction (SME, 2026-08-05):** AWS Snowflake is a **target DB
platform**, not an ETL product — the same family as AWS S3, AWS Glue tables, and AWS
Iceberg tables. The standard's "Snowflake ETL" label (kept verbatim in the table above)
names the loads-into-Snowflake **job family**, not a software product. The
software-registry row this code needs is `snowflake` the data platform (DBMS-family
category, sibling of `oracle-db`) — an edge derived from `SFS` means "loads into
Snowflake," never "runs a Snowflake ETL framework."

⚠️ **`DDC` / SEAL 111374 is the worked example of code repurposing:** the code was
*originally* created for the PySpark conversion and has since been **repurposed —
nothing PySpark now**. SEAL 111374 carries two deployments: the Informatica platform
supporting Teradata → Snowflake, and DMV (Data Migration & Validation across Teradata and
Snowflake). This is why the app-code `descr` column is majority-correct-not-authoritative:
a repurposed code keeps its old description until someone edits it.

### HLT application codes (tier 1 — code carries the SEAL)

Five HLT Control-M apps. Each carries one application QR on its jobs (`PR<appcode>-HL-QR`).

| App code | SEAL | Application (Reporting & Analytics) |
|---|---|---|
| `PREBM` | 111025 | Chase MyHome Explore, Buy, Manage R&A |
| `PRCOH` | 111026 | Correspondent Originations Platform R&A |
| `PRARA` | 111027 | Chase MyHome Advice R&A |
| `PRSRV` | 110865 | Home Loan Servicing R&A |
| `PRORG` | 110866 | Chase MyHome Originations R&A |

Confirms and supersedes the *(observed / mnemonic unconfirmed)* `PRARA` row above:
`ARA` = **Advice Reporting & Analytics**, SEAL 111027, tier 1, app-tied.

### HPSM → ServiceNow escalation queues (system of record: `internal/orchestration/hlt-hpsm-snow-queue-mapping.yaml`, carries SNOW group `sys_id`s)

Each app maps to one **L3** group (primary escalation target) and three **L2** groups by
platform (`…TD` Teradata · `…EXA` Exadata · `…SQL` SQLServer).

| App code | L3 queue | L2 queues (TD · EXA · SQL) | PTO (Mgd / Fed) |
|---|---|---|---|
| `PREBM` | `C3CMHEBMRA` | `C2CMHEBMRATD` · `C2CMHEBMRAEXA` · `C2CMHEBMRASQL` | ✓ / – |
| `PRCOH` | `C3COPRA` | `C2COPRATD` · `C2COPRAEXA` · `C2COPRASQL` | ✓ / – |
| `PRARA` | `C3CMHARA` | `C2CMHARATD` · `C2CMHARAEXA` · `C2CMHARASQL` | ✓ / ✓ |
| `PRSRV` | `C3HLSRA` | `C2HLSRATD` · `C2HLSRAEXA` · `C2HLSRASQL` | ✓ / – |
| `PRORG` | `C3CMHORA` | `C2CMHORATD` · `C2CMHORAEXA` · `C2CMHORASQL` | ✓ / – |

**The "book of work" claim (HLT standard, verbatim intent):** when Control-M jobs are
active and the job↔SCIM relationship is **1:1**, the SCIM HPSM queues can serve as the
Control-M inventory of folders/jobs **by SEAL**. Default queue is L3 to enforce hygiene:
if the SCIM is undefined, is in `PRPL`, or is decommissioned, **the L3 team is
accountable**. That accountability default is what makes the inventory claim hold —
worth keeping intact if this is ever modeled.

### Sources of record (internal)

| Standard | Source of record |
|---|---|
| DAT SRE (platform framework naming) | `go/dtjobstandards` — Control-M Job Naming Standards (ADESRE 3811523057) |
| HLT (application code naming) | Control-M guidelines for HLT AWS modernization effort (ADEOPS 3428013015) |
| Automated conformance check | Autom8 **Control-M Standards Checker** — XML check that files intended for future production promotion meet scheduling guidelines (`autom8.gaiacloud.jpmchase.net/control-m-standards-checker`) |
| HPSM/SNOW queue mapping | `internal/orchestration/hlt-hpsm-snow-queue-mapping.yaml` |
| App-code → SEAL registry | `internal/orchestration/controlm-app-codes-with-seal.csv` |

### Real ↔ synthetic twin key (sanitized sample ids used in publishable files)

| Real SEAL | Real application | Synthetic twin (`config/taxonomy/business-application.yaml`) |
|---|---|---|
| 111027 | Home Lending Advice and Reporting (`PRARA`) | **70002** — Retail Advice Reporting & Analytics |
| 110865 | Home Lending Servicing (`PRSRV`) | **70003** — Consumer Servicing Reporting & Analytics |
| 89211 | source-app SEAL embedded in the worked folder name (5-digit legacy id) | no dedicated twin; publishable examples use block 70001–70099 |

### J15 resweep additions (2026-07-27) — values pulled OUT of the publishable tree

Found building the J15 value-shape boundary guard. Realness noted per row; where
unconfirmed, the value sits in the real-SEAL range/shape and was treated as real
(boundary asymmetry: unknown → out).

| Old publishable value | Where it lived | Realness | Synthetic replacement |
|---|---|---|---|
| 85025 | sample folder family `PRARAG-HLDM-…-PEX-TRUST-{DLY,CYC}` (controlm.yaml, sample CSVs, TDDs, lineage fixture) | UNCONFIRMED — same real family/range as 89211 | **70011** |
| 94028 | sample folder `…-PEX-PROV-DLY` | UNCONFIRMED — same family | **70012** |
| 15001 / 15002 | authored sample folders `PRAUTG-AUTO-…` | authored synthetic, pre-block; uniformed into block | **70021 / 70022** |
| 20001 | authored sample folder `PRDATG-DAT-…` | authored synthetic, pre-block | **70031** |
| 19999 | authored retired folder `PRRPDG-RPD-…-RISK-RETIRED` | authored synthetic, pre-block | **70041** |
| 34544 | `%%SEAL` value in 3 unit-test fixtures | **REAL** — appears as a live `%%SEAL` value in the untracked production variables extract | **70004** |
| B022876 / H024490 / K024761 | `%%FID_D/_Q/_P` triplet in test fixtures | **REAL** (B022876 confirmed in the extract; triplet treated as real together) | **B0004 / H0005 / K0006** |
| B019757 | `%%RFID` value in a test fixture | REAL-shaped, same source | **B0007** |
| 24412 | numeric segment of the real job name `PDCLD0003_24412_CMS_IDW_SCRA_REPORTING_CZ_AWS_TRUST` quoted in a test fixture | **REAL** — verbatim from the extract | **70013** (name otherwise kept; string-vocab ruling parked with the platform-vocabulary residual) |
| 90001 | authored lineage-fixture folder `PRARAG-HLDM-…-PEX-SPARK-DLY` (G9/G20 era) | authored synthetic, pre-block — but sits in the real 9xxxx SEAL range | **70014** |
| 900101 / 900102 / 900201 | `seal_ids` column of `pat_product_mapping__sample.csv` | authored synthetic, out of block — SEAL-position by column definition | **70051 / 70052 / 70053** |

**Kept in the publishable tree with a recorded ruling (SME to confirm or flip):**
6-digit Control-M surrogate *table keys* (sample folder ids 161014–162001 family;
real-extract folder ids 176690, 185894, 188252, 183213, 185675, 155768, 161947,
179833 cited in variable-resolver/parser test comments). These are private-DB row
keys with no external meaning — no SEAL/roster/credential semantics, join to
nothing outside psgmgr — so they were allowlisted in the guard rather than
resweeped. If the SME disagrees, flip the guard allowlist entries to a resweep.

**PLATFORM TOKENS — RULED 2026-08-11, SME: `PRARAG-HLDM` IS AN AUTHORED FIXTURE
NAME.** This closes the first of the four value classes J13's notes recorded as
"deliberately left untouched by the 2026-07-27 sweep" and needing a user ruling.
The tokens `PRARAG` and `HLDM` — and the sample-corpus values derived from them,
`svc.hldm`, `/opt/scripts/hldm/`, `host-hldm-01` — are **authored, not captured**.
No sweep is owed and none should be run.

*Why this is worth a recorded line rather than silence.* The J15 table above
replaced the **numeric segments** inside these folder names (85025 → 70011,
94028 → 70012, 90001 → the block) because those were real or real-shaped SEAL
ids. The surrounding tokens were left, and reading the table alone it is easy to
infer they were left by oversight. They were not: the ids were the real part and
they are gone. Corroborated independently — the backlog records "PRARAG fixture
name already public" as the basis for committing a screenshot of the
controlm-ingestion-tdd render.

*What this prevents.* `PRARAG` appears in ~36 files across config, docs, loaders,
the folder-name parser, five tests that assert on it literally, the bundled
sample CSVs, the lineage fixtures, internal/, knowledge/, UI-WIP and the web demo
data. A sweep would rewrite the sample corpus, break the tests that pin the
parser's behaviour, and require a new synthetic prefix plus registry rows — all
to remove a name nobody captured. That sweep was proposed on 2026-08-11 and
stopped by this ruling.

*One consequence, applied the same day.* A scrub of the token from
`config/taxonomy/business-application.yaml`'s header comment (commit `f6b4285`)
was **reverted**: it left the prose reading `PR[app]G-[DataArea]` while
`config/taxonomy/controlm.yaml` carried the literal two directories away, which
is worse than either state alone. The header now names the fixture family as the
rest of the tree does.

*Still unruled — the other three classes J13 named:* datacenter codes,
schema/table/column identifiers, and the fourth in that list. This ruling covers
platform tokens ONLY and should not be read as disposing of the rest.

## Real worked example (name-embedded SEAL)

Folder `PRARAG-HLDM-89211-MLCM-ORIG-CRM-TRUST-DLY` (SMART, P032-E0700-DMA):
the numeric segment `89211` **is a SEAL ID** — the *source* application's SEAL
(File Watchers carry the source SEAL; processing folders carry the processing
app's SEAL). The folder's declared variable `SEAL=111027` is the *processing*
application (Home Lending Advice and Reporting) — one flow, two SEALs.

## Observed job inventory (2026-06-11 query, 60 (DC, APPLICATION) rows — REAL)

Top counts: `PRDCL` **8,850** (P032) + 43 (P012) · `PRICD` 6,288 (P012) + 523
(P014) + 18 (P032) · `PRIOS` 3,618 (P014) + 708 (P032) · `PCS4G` 1,378 (P021) ·
`PRSOP` 798 · `PRAOC` **634** · `PRSRV` **557** · `PRDDC` 389 · `PRARA` 236 …

- The four DCs observed: `P012-E0700-IB`, `P014-E0700-ANY`, `P021-E0800-ANY`,
  `P032-E0700-DMA` — note **E0800** on P021 (DC default times do vary).
- `P021` hosts `PC…` codes (PCS4I/PCS4C/PCS4G, PCOFTG-RESOFT) vs `PR…` elsewhere —
  consistent with position 2 = LOB (R=Retail, C=*to confirm*, Card?).
- JOBS_WITH_VARS ≈ JOB_TOTAL almost everywhere.

## Organizational background (identifying detail)

The company is one of the largest in the country; as it grew, SDLC roles
consolidated — QA teams phased out, support split between developer-supported
small apps and a centralized batch team for data warehousing. **Data-lake SRE
teams dictated platform Control-M app codes**; teams outside that SRE org (like
ours) created application-tied codes following similar standards (e.g. for
hardcoded Grafana dashboards).
