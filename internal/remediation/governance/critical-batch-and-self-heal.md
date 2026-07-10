# Critical Batch (Tier-1) & Self-Heal — SCIM Standards

**Corpus:** INTERNAL (governance). **Status:** 🟠 DIGESTED — 2026-06-17.
**Sources:** email thread *RE: "Critical Batch" Tier 1 SCIM Update & Verification* **CHG46712473** (Chad Wilson ↔ Sushant Dubey / CCB DAT IPM SRE; cc CES CBT Leads, DAT PROD MGMT, HALT Data SRE), Mar 12–13 2026; `go/dat6am` dashboard. Replaces the earlier "email not transcribed" note.

---

## 1. The Critical Batch Tier-1 initiative

A **6 AM / 4 PM batch SLA visualization** (`go/dat6am` Grafana dashboard) was built for timings and declared **"Critical Batch Tier 1."** Analysis of the jobs/folders the dashboard uses found **~1,000 critical-batch jobs set *lower* than P2** (counts: **P2 = 2,334, P3 = 325, P4 = 548**). The change (CHG46712473) updates job **SCIM to match the dashboard** so critical batch is correctly tiered and severitized.

**SCIM field mapping for critical batch:**

| SCIM field | Value |
|---|---|
| `ECOMPONENTFAILED` | Seal Id (number) |
| `EITEMFAILED` | **Tier-1 / 2 / 3 / PRPL** |
| `EMODULEFAILED` | Data Flow |
| `ESEVERITYFAILED` | **Critical → P2** |

**Verification mechanic:** each team verifies/updates the SCIM for *their* Area Product / App_Name / Data_Flow against `go/dat6am`; a **SNOW technician** group + **CTASK** peer-review task per group, with job/folder counts (e.g. `CCB_DAT_ASUP_CLDCUST`=643, `CLDCONSUMCRD`=435, `CONSBANK`=406, `CLDCAF`=277, `CLDCCT`=243, … plus `HLT` rows). Confirm jobs/folders (cols E–J) match expected SCIM (cols L–Q) for the data flow; **add Seal (col I)**; **verify Special Instructions (col T)**, and where blank/inaccurate/not actually self-heal, set from col X pre-filled `**CRITICAL BATCH** |Folder: |SLA`.

---

## 2. Self-heal — what it is and the `VR:` codes

**Self-heal** = automated recovery (the job is re-run/recovered without a human). It is driven by a **`VR:` code in the Special Instructions column** ([escalation reference §3](escalation-scim-reference.md)):

- **Legacy pattern:** `VR:AAAS_CONTROLMALERT-C1CCBDATAECO` — confirm the job can actually be recovered by self-heal and is configured for it (historically *set by folder*; not directly verifiable).
- **New pattern:** `VR:C1CCBDATAECO-CLOUD-JOB;` — leave as-is, no research needed.

**The friction (unresolved):** DAT SRE — *"Special instruction column is used by selfheal, please do not touch that column or else selfheal will stop working."* HLT's counter — *only* genuinely self-heal-capable jobs should carry `VR:`; others should carry runbook references. Both teams actually want the same end state (an accurate count of self-heal jobs + which patterns can be automated) but disagree on editing the column.

---

## 3. Self-heal EXCLUSIONS (do NOT enable self-heal when…)

The NFR is **not** "the job is re-runnable from Control-M" (a common developer misconception). Self-heal must be **disabled** when a blind re-run is unsafe or insufficient:

1. **Info1 / DB-function jobs** that create/drop indexes or **truncate tables** — a naive re-run can corrupt or double-apply.
2. **Predecessor-dependent jobs** — where a **predecessor must be re-run first** before the failed job can recover. (This is the same **predecessor/API gotcha** as the `_FW`-that-calls-an-API case — name/flag says "recoverable," the real flow says "no.")

For these, Special Instructions should reference the **runbook / recovery steps**, not a `VR:` self-heal code.

---

## 4. Data-quality problems to fix (named in the thread)

- **`Missing Item` / `Missing Module` are not real values** — they appear because the Excel field was **blank on upload**.
- **Copy/paste errors** across SCIM rows.
- **Priority spread P2 → P99** (P99!) — severities set without regard to business impact; ~1k critical jobs below P2.
- **SCIM created without understanding its purpose** — the core knowledge gap.

---

## 5. Implications for the greenfield

- **Self-heal eligibility is a derived property, not a default.** The greenfield must classify a job as self-heal-eligible only when (a) re-run is idempotent/safe and (b) no predecessor-rerun dependency — derived from the **resolved flow**, not the name or a copied flag. → candidate rule **R17** (self-heal-eligibility check).
- **Severity from business impact** (P2–P6), **Tier from the dashboard** (`go/dat6am`), **1:1 job↔SCIM** integrity — all checkable. → rules **R18** (severity sane, not P99/blank), **R19** (Tier matches critical-batch dashboard), **R20** (exactly one SCIM per job).
- **Column-T discipline:** `VR:` only when self-heal is truly configured; human runbook/metadata to the **Description** otherwise (avoids the DAT/HLT edit conflict and keeps self-heal automation intact).
- **Don't reuse "recoverable from Control-M" as the NFR** — it's the misconception the whole change exists to correct.

Related: [[project-controlm-escalation-governance]], [[project-description-metadata-plan]], [[project-controlm-remediation-spinoff]]
