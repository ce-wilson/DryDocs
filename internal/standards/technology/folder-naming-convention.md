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
| `PRAOC` | **Platform** | Ab Initio ETL platform (data lake, SRE-dictated) | **No direct SEAL** |
| `PRDCL` | **Platform** | Java/PySpark jobs loading to AWS cloud (SRE-dictated) | No direct SEAL |
| `PRSRV` | **Application** | Home Lending **Servicing** — created by our team (same platform, similar standards for Grafana dashboards) | **SEAL 110865** |
| `PRARA` | *(observed)* | Application field of the worked example folder (`PRARAG-…`); `ARA` ≈ Advice & Reporting? *(mnemonic unconfirmed)* | **SEAL 111027** Home Lending Advice and Reporting (via declared folder variable; code-type to confirm) |

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
