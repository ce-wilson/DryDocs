---
standard: control-m-folder-naming
domain: technology
taxonomy_path: technology/orchestration/control-m/folder
governs: JobFolder.name              # the 6-char folder name (SCHED_TABLE)
authority: internal-standards         # config/precedence.yaml tier 2 — refines the BMC baseline
refines: bmc-baseline
applies_to_source: controlm-psgmgr
status: active
trust_tier: internal / SME-asserted / mutable
---

# Internal Standard — Control-M Folder Naming Convention (PRAOCG)

**Corpus:** INTERNAL (company-specific standard) — *not* vendor documentation.
**Captured:** 2026-06-11, from SME (chat). Source of record: SME knowledge; confirm against the canonical internal standards page when available.
**Role:** Conformance layer — defines what a *valid* Control-M folder name is **here**. The vendor side only says the Folder Name field exists ([controlm-folder-definition-parameters](../../../external/orchestration/bmc-controlm/controlm-folder-definition-parameters.md)); this defines how we fill it.

> ⚠️ **Trust tier:** internal / mutable / SME-asserted. "The **majority** follow" this convention — it is a strong norm, not a guaranteed invariant. Items marked *(to confirm)* are gaps the SME did not fully enumerate; do **not** invent values for them.

---

## The convention

Most Control-M folders follow a **6-character positional code**: **`PRAOCG`**

Worked example: **`PRAOCG`** = Production · Retail(CCB) · `AOC` (Ab Initio On Cloud) · `G` (Smart folder)

| Pos | Code (example) | Meaning | Notes |
|-----|----------------|---------|-------|
| 1 | `P` | **Environment** — `P` = Production | Other environment codes *(to confirm)* — e.g. non-prod codes not provided |
| 2 | `R` | **Line of business code** — `R` = **CCB Retail** | Other LOB codes *(to confirm)* |
| 3–5 | `AOC` | **3-char code** — chosen as close as possible to the acronym | Example: **A**b **I**nitio **O**n **C**loud → `AOC`. Mnemonic, not a registry lookup. ⚠️ **Often a *platform* name, not an application/area-application name** — see caveat below |
| 6 | `G` | **Folder type marker** — `G` = **Smart folder** | See historical note below |

So `P` + `R` + `AOC` + `G` → `PRAOCG`.

---

## Position 6 — historical meaning (important context)

The 6th character was **originally a frequency indicator**, not a folder-type marker:

| Historical code | Meaning |
|---|---|
| `D` | Daily |
| `W` | Weekly |
| `M` | Monthly |
| … | others *(to confirm — SME said "etc.")* |

**Today, everything is a SMART folder**, so position 6 is now `G` (Smart folder) rather than a frequency code. Expect **legacy folder names still carrying frequency codes** (`…D`, `…W`, `…M`) in the existing estate — graph/analysis logic should treat position 6 as *either* frequency (legacy) *or* `G` (current), not assume one.

---

## ⚠️ Platform-vs-application caveat (SME, 2026-06-11 — RESOLVED)

**The majority of folders carry a *platform* code in positions 3–5, not an application or area-application code.**

**Organizational background (why):** as the company (one of the largest in the country) grew, SDLC roles consolidated — QA teams phased out, support now split between developer-supported small apps and a **centralized batch team** for data warehousing, with silos between support and other groups. **Data-lake SRE teams dictated platform Control-M app codes** and hardcoded naming standards for data products on the data lake. Teams not supported by that SRE org (like ours) created their own application-tied codes following similar standards (e.g. for hardcoded Grafana dashboards).

### Known application-code registry (seed — extend as confirmed)

| Code | Type | Meaning | SEAL tie |
|---|---|---|---|
| `PRAOC` | **Platform** | Ab Initio ETL platform (data lake, SRE-dictated) | **No direct SEAL** |
| `PRDCL` | **Platform** | Java/PySpark jobs loading to AWS cloud (SRE-dictated) | No direct SEAL |
| `PRSRV` | **Application** | Home Lending **Servicing** — created by our team (same platform, similar standards for Grafana dashboards) | **SEAL 110865** |
| `PRARA` | *(observed)* | Application field of the worked example folder (`PRARAG-…`); `ARA` ≈ Advice & Reporting? *(mnemonic unconfirmed)* | **SEAL 111027** Home Lending Advice and Reporting (via declared folder variable; code-type to confirm) |

### Observed job inventory (2026-06-11 query, 60 (DC, APPLICATION) rows)

Top counts: `PRDCL` **8,850** (P032) + 43 (P012) · `PRICD` 6,288 (P012) + 523 (P014) + 18 (P032) · `PRIOS` 3,618 (P014) + 708 (P032) · `PCS4G` 1,378 (P021) · `PRSOP` 798 · `PRAOC` **634** · `PRSRV` **557** · `PRDDC` 389 · `PRARA` 236 …

What it shows:
- **The same app code spans multiple data centers** (PRICD in 3 DCs; PRDCL, PRIOS in 2) — code→DC is many-to-many.
- The four DCs observed: `P012-E0700-IB`, `P014-E0700-ANY`, `P021-E0800-ANY`, `P032-E0700-DMA` — note **E0800** on P021 (DC default times do vary).
- `P021` hosts `PC…` codes (PCS4I/PCS4C/PCS4G, PCOFTG-RESOFT) vs `PR…` elsewhere — consistent with position 2 = LOB (R=Retail, C=*to confirm*).
- **JOBS_WITH_VARS ≈ JOB_TOTAL** almost everywhere — nearly every job carries variables, which sizes the variable-modernization effort at effectively the whole estate.

Consequences:
- A folder name does **not** reliably identify the business application. Do not derive folder→`:Application` joins from the name code alone.
- The original intent of embedding a **SEAL ID** in auto-generated folder names (e.g. `PRARAG-HLDM-89211-…`: File Watchers carry the *source* SEAL, processing folders the *processing app's* SEAL) is **not valid estate-wide** for the same reason.
- **SEAL resolution hierarchy:** folder variable `SEAL` (primary) → *(planned)* SEAL derived from the data pipeline/dataset the job touches → name-embedded SEAL (weak hint only). Full detail: [description-field-metadata-plan](description-field-metadata-plan.md).

## Why this matters for the knowledge graph

- This convention makes a folder name **parseable into attributes** — environment, LOB, application, folder-type/frequency — which can become node properties or relationships (e.g., folder → `:Application` join via the 3-char app code).
- The **application-code → application-name** mapping (`AOC` → "Ab Initio On Cloud") is a candidate cross-graph link to SEAL `:Application` / business ontology. ⚠️ Beware the **"Application" name collision** with Control-M's own `Application` parameter — keep them namespaced (see [[project-drydocs-scrape-two-corpus]]).
- Enforcement path on the vendor side: **Site Standard + Business Parameters + Enforce Validations** (see the folder-definition-parameters doc) is where such a naming rule would be enforced in Control-M itself.

---

## Open items to confirm (do not fill speculatively)

1. Full list of **environment codes** (position 1) beyond `P` = Production.
2. Full list of **line-of-business codes** (position 2) beyond `R` = CCB Retail.
3. Full historical **frequency code** list (position 6) beyond D/W/M.
4. Is the app code **always exactly 3 chars**, and is there a governed registry or is it per-team mnemonic?
5. How non-conforming / legacy names are handled (exceptions, grandfathering).

Related: [[project-drydocs-scrape-two-corpus]], [[project-controlm-xml-not-json]]
