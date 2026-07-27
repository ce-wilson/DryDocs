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
