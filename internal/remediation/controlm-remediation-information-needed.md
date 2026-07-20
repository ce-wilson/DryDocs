# Information-Needed Register (Control-M Remediation)

**Corpus:** INTERNAL. **Status:** 🔵 OPEN — 2026-06-11. **Branch:** `controlm-spinoff`.
A single checklist of inputs the remediation initiative needs, by category, with which phase each blocks. Severity: 🔴 blocks the phase · 🟡 needed for quality · ⚪ nice-to-have.

---

## A. Access & data

| # | Need | Why / blocks | Sev | How to obtain |
|---|---|---|---|---|
| A1 | Confirm `psgmgr.*` extract table names (variables, jobs, folders, conditions) | Extraction source; blocks real-data M0/M1 | 🔴 M1 (🟡 M0 — screenshot fallback) | DBA / Control-M admin; inspect schema |
| A2 | Read access to **definition XML exports** (or confirm UI-only) | Determines ingest path; XML is the 9.0.21.300 native form | 🟡 M0/M1 | Control-M admin |
| A3 | **Ground-truth resolved watched filename** for the M0 job | Validates the resolver; settles the `var.text` dot rule | 🔴 M0 Gate-2 | Control-M Monitoring / run history |
| A4 | Job-type distribution across the estate (FileWatcher/OS/Command/FT/…) | Sizes M2 documenter coverage | 🟡 M2 | Extract `TASKTYPE`/job-type counts |
| A5 | Per-job-type ground-truth samples | Validates documenter + prover per type | 🟡 M2 | Monitoring/history |

---

## B. Standards to ratify (turn prose → rules)

| # | Need | Why / blocks | Sev | Source today |
|---|---|---|---|---|
| B1 | **`var.text` dot rule** confirmed (`%%$ODATE.tok` → `{ODATE}.tok` or `{ODATE}tok`?) | Resolver correctness; M0 equivalence crux | 🔴 M0 | A3 settles it |
| B2 | Ratified **Description metadata key list** + required-vs-optional + escaping for `|`/`:` | Greenfield Description authoring | 🔴 M3 (🟡 M2) | [description-field-metadata-plan](description-field-metadata-plan.md) (observed, not ratified) |
| B3 | Internal **job-naming standard** (the job-level analogue of PRAOCG) | Greenfield job naming | 🟡 M3 | Not captured — only BMC generic in [general-parameters](../vendor-bmc/controlm-general-parameters.md) |
| B4 | Canonical **variable-name map** (DRPBX_DIR→DROPBOX_DIR, …) | Var canonicalization rule | 🟡 M2/M3 | **Ratification source now exists** — [governance/command-line-and-variables-standard](governance/command-line-and-variables-standard.md) §1 (canonical registry + alias rollups, e.g. img_path/IMAGE→ETL_ARTIFACT_URI); confirm completeness vs estate |
| B5 | PRAOCG completeness: env codes (beyond P), LOB codes (beyond R/C), app-vs-platform per code | Naming validation rules | 🟡 M2 | [folder-naming-convention](folder-naming-convention.md) open items |
| B6 | `SEAL` var **mandatory?** in the greenfield template | Conformance rule strength | 🟡 M3 | SME ruling |
| B7 | `SourceOrigin` code set (I=Internal confirmed; others?) | Metadata validation | ⚪ M3 | SME |

---

## C. Org & process

| # | Need | Why / blocks | Sev | Owner |
|---|---|---|---|---|
| C1 | **Dev-team Jira definition-of-ready** | Gate-5 packaging must match their intake | 🔴 M3 (🟡 M0 proxy) | Dev team |
| C2 | Change-management batching cadence (how many remediations per release) | M3/M4 throughput planning | 🟡 M3 | Dev + change mgmt |
| C3 | Remediation **prioritization policy** (volume vs risk vs SEAL-coverage) | M4 sequencing | 🟡 M4 | Prod-support lead |
| C4 | Reporting / dashboard requirements | M4 metrics | ⚪ M4 | Stakeholders |

---

## D. Technical / infra

| # | Need | Why / blocks | Sev | Notes |
|---|---|---|---|---|
| D1 | CI runner for `ctm-remediate` | M1 packaging | 🟡 M1 | Mirror DryDocs CI |
| D2 | Shared models/adapters: copy vs published lib | M1 structure | 🟡 M1 | Recommend copy now |
| D3 | STG_ staging-contract **version** scheme | M1 interface stability | 🟡 M1 | Pin in DryDocs |
| D4 | (If lib route) internal package registry | M1 | ⚪ M1 | Only if D2 → lib |

---

## E. Governance / escalation to ratify (R13–R29)

Surfaced from the tier ③/④ governance corpus (2026-06-17). These turn the DAT/HLT standards into enforceable rules.

| # | Need | Why / blocks | Sev | Source today |
|---|---|---|---|---|
| E1 | **Org adoption of the owning-dev-queue default** (R14) — DAT/Platform agreement vs platform L1 `C1CCBDATAECO` | The crux of the platform-vs-application fork; greenfield routing | 🔴 M3/M4 | Unresolved DAT↔HLT dialogue ("Sushant") — [governance/README §3](governance/README.md) |
| E2 | **Self-heal eligibility ruling** (R17): authoritative exclusion list (Info1/DB-function, predecessor-rerun) + who may edit column-T | Self-heal correctness; active DAT/HLT dispute | 🔴 M3 | [governance/critical-batch-and-self-heal](governance/critical-batch-and-self-heal.md) |
| E3 | **Governed descriptor/type-token vocabulary** (stages/types; API-watcher token vs `_FW`) (R13) | Name↔intent rule; greenfield retoken | 🟡 M3 | enumerate w/ DAT+HLT |
| E4 | **Structured-log key set + monitoring binding** ratified as enforceable (R21/R23) | NFR evidence; observability orphan check | 🟡 M4 | DAT NFR — [governance/nfr-catalog §2](governance/nfr-catalog.md) |
| E5 | **NFR evidence-gate definition** (R25): which high-risk NFRs gate "greenfield-complete" + acceptable evidence | Greenfield sign-off | 🟡 M4 | ICDW *Evidence Required* — [governance/nfr-catalog §3](governance/nfr-catalog.md) |
| E6 | Numeric **LOB code** completeness (R≈41/S=5/K=3/B=82) + queue-role suffix decode (`TD`/`EXA`) | SCIM derivation + queue registry | ⚪ M2 | [governance/escalation-scim-reference §4](governance/escalation-scim-reference.md) |

---

## Critical path (the 🔴s, in order)

**A3 (ground-truth filename) → B1 (var.text rule)** unblock M0's equivalence proof — get these first; they're one fetch from Control-M monitoring. **A1 (psgmgr tables)** unblocks real-data M1. **C1 (Jira DoR)** and **B2 (Description keys)** unblock M3. **E1 (dev-queue-default adoption)** and **E2 (self-heal ruling)** are the 🔴 *governance* blockers for M3/M4 — both are unresolved cross-tower disputes, so start the dialogue early; they don't block M0/M1. Everything else is quality/sequencing.

Related: [[project-controlm-remediation-spinoff]], [[project-controlm-xml-not-json]], [[project-description-metadata-plan]]
