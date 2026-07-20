# M0 PoC — Detailed Scope (Control-M Remediation)

**Corpus:** INTERNAL. **Status:** 🔵 SCOPED — 2026-06-11. **Branch:** `controlm-spinoff`.
**Parent:** [controlm-remediation-spinoff-plan.md](controlm-remediation-spinoff-plan.md) (milestone M0).
**Owner:** Production Support. **Implementer:** Dev team (via the M0 Jira).

---

## 0. Documentation readiness (confirmation)

| Need | Covered by | Status |
|---|---|---|
| Control-M function/parameter lookup | `vendor-bmc/` (25 docs: file-watcher, variables, general/folder/order params, scheduling, calendars, events, OS-job, utilities, API refs) | ✅ sufficient |
| Standards check (naming, time, metadata) | `internal-standards/` (PRAOCG, DC-default-time, description-metadata-plan, calendar-projection) | ✅ for M0; not yet machine-checkable |
| Analysis engine (extract→classify→resolve→parse) | `drydocs/controlm/` (8 modules), `loaders/sql/*.sql`, staging DDL | ✅ exists (C3 A/B/C) |

**Gaps (logged; none block M0):**
1. **Standards rules registry** — the standards are prose, not a structured rule set the tool can assert against. Needed for automated gate-2/3 checks → **M1 deliverable** (M0 checks by hand).
2. **`var.text` dot rule** — resolver consumes `.` only between `%%var.%%var`; the M0 job's *modern* reference uses `%%var.text` (`%%$ODATE.tok`). **This is M0's technical crux** (Gate 2/4 task below).
3. **Extract access** — `psgmgr.*` table names unverified; XML-export access unknown. M0 can fall back to transcribed screenshot data to stay unblocked.
4. **Internal job-naming standard** — not captured (only BMC generic). Greenfield job naming in Gate 3 uses the modern reference job as the pattern.
5. **Ratified Description key list** — Gate 3 uses the observed keys from the metadata plan as provisional.

---

## 1. Objective & Definition of Done

Take **one real legacy FileWatcher**, run it through all 5 gates, and produce **one dev-team-ready Jira** — entirely offline/read-only. Proves: the engine seam works end-to-end, the offline **equivalence proof** is credible, and the **SoD handoff** (we author + validate, dev deploys) is real.

**Done when:** the 5 deliverables (§5) exist, acceptance criteria (§6) pass, and we have a go/no-go on the engine spin-off (M1).

---

## 2. The unit (concrete — already captured from production screenshots)

| Attribute | Legacy | Greenfield reference (already exists in prod) |
|---|---|---|
| Job | `PARAD00010_MLCM_ORIGINATIONS_DAILY_CRM_INDICATOR_TOK_ONPM_FW` | `PARAD0011b_MLCM_ORIG_DAILY_CRM_INDICATOR_TOK_ONPM_FW` |
| Type | FileWatcher (Create) | FileWatcher (Create) |
| Folder | `PRARAG-HLDM-89211-MLCM-ORIG-CRM-TRUST-DLY` (SMART) | same |
| DC / Server | `P032-E0700-DMA` (default 07:00 EST) | same |
| SEAL / App | 111027 (PRARA — HL Advice & Reporting) | same |
| Run as | `mlc_p` | same |
| Watch path | `%%DRPBX_DIR.%%FILE_NM_PREFIX.%%BUS_DATE.%%FILE_NM_SUFFIX.%%EXTENSION` | `%%DROPBOX_DIR.Originations_Daily_CRM_Indicator_.%%$ODATE.tok` |
| Vars | DRPBX_DIR, FILE_NM_PREFIX, BUS_DATE=`%%$ODATE`, **FILE_NM_SUFFIX=`.`**, EXTENSION=`tok` | DROPBOX_DIR only (5 locals → 0) |

**Why this unit:** it has a *known-good greenfield* already in production (`PARAD0011b`), so we have a reference target and can sanity-check our greenfield authoring against what dev actually did. It exhibits the canonical concat-dot hazard. It's a FileWatcher (path-composition heavy = maximum resolver exercise).

---

## 3. Scope boundaries

**In:** this one job + its folder-scope variables; gates 1–5; the existing offline resolver + command parser; the concat-dot hazard; a hand-filled Jira.
**Out:** batch/multi-job; other job types; any graph/Neo4j load; **any write to Control-M**; full `var.text` rule generalization (only what this job needs); Jira REST automation (manual ticket is fine); the standards rules registry (M1).

---

## 4. Task breakdown (per gate)

| # | Gate | Tasks | Exists vs New | Est |
|---|---|---|---|---|
| 1 | **Capture** | Obtain legacy definition: confirm `psgmgr` extract OR XML export; **fallback:** transcribe from screenshots to stay unblocked. Record raw vars + watch template. | extract SQL exists; **new:** confirm source | 1–2d |
| 2 | **Validate** | Run `classify_variable` + `resolve_job` on the vars. Confirm `value_is_delimiter` flags `FILE_NM_SUFFIX='.'`. Produce **resolved baseline** = watched filename. **Obtain ground-truth filename** from Control-M monitoring/history and reconcile. **Resolve the `var.text` dot rule** (does `%%$ODATE.tok`→`{ODATE}.tok` or `{ODATE}tok`?). | resolver/classifier exist; **new:** ground-truth fetch + rule confirmation (may extend resolver) | 2–3d |
| 3 | **Design** | Author greenfield definition: canonical var names, direct path, no dot-smuggling, Description key:value metadata (datasetSeriesName/SLA/SEAL…), declared `SEAL=111027`. Compare to the real `PARAD0011b`. | **new:** by-hand authoring for one job | 1–2d |
| 4 | **Prove** | Resolve greenfield offline; **diff** its watched filename vs the legacy baseline / ground truth. Assert identical, or document a justified delta. Build a minimal reusable diff harness. | resolver exists; **new:** equivalence/diff harness | 2–3d |
| 5 | **Package** | Fill the [Jira template](controlm-remediation-spinoff-plan.md#jira-ticket-template-fill-in): before/after, equivalence evidence, acceptance criteria, rollback. | **new:** manual fill | 1d |

**Total: ~7–11 working days (~2–3 wk).**

---

## 5. Deliverables (artifacts produced by M0)

1. `legacy/PARAD00010…FW.md` — current-state definition + resolved behavior + hazard report.
2. `greenfield/PARAD00010…FW.md` — proposed modernized definition.
3. `equivalence/PARAD00010…FW.md` — legacy baseline vs greenfield resolved watched filename, with ground-truth reconciliation.
4. `jira/CTM-REMEDIATE-001.md` — filled Jira ticket for the dev team.
5. `M0-retro.md` — what worked, resolver gaps found (esp. `var.text`), Jira-template fixes, go/no-go for M1.

---

## 6. Acceptance criteria

- [ ] Resolver's legacy watched filename **matches the ground-truth** filename Control-M actually watches (or the discrepancy is explained and the resolver corrected).
- [ ] `value_is_delimiter` correctly flags the smuggled `FILE_NM_SUFFIX='.'`.
- [ ] Greenfield resolves to the **same** watched filename as the legacy baseline.
- [ ] `var.text` dot rule is confirmed and encoded (or explicitly deferred with the one job's case handled).
- [ ] Jira ticket meets the dev team's definition-of-ready (or our best proxy, pending their confirmation).
- [ ] **Zero writes** to Control-M; all artifacts are read/author/validate only.

---

## 7. M0 risks

| Risk | Sev | Mitigation |
|---|---|---|
| `var.text` dot rule unconfirmed — could require resolver work | **High** (technical crux) | Get one ground-truth resolved filename; encode the confirmed rule; it's a small, contained resolver change |
| No read access to live definitions / monitoring | Med | Screenshot-transcribed fallback for definition; ground-truth filename is the one item that truly needs system access |
| Dev-team intake format unknown | Med | Draft Jira to our best proxy; treat their review as an M0 output, not a blocker |
| Legacy ≠ modern reference resolve differently | Low–Med | That's a *finding*, not a failure — document it; the modern job is a style reference, ground truth is the oracle |

---

## 8. Exit → M1 readiness

M0 closes with: end-to-end proven on one job; resolver gaps logged and (ideally) fixed; Jira template validated against a real ticket; **go/no-go decision** on lifting the engine into `ctm-remediate`. If go, M1 (engine spin-off) starts with a known-good vertical slice to regression-test against.

Related: [[project-controlm-remediation-spinoff]], [[project-description-metadata-plan]], [[project_controlm_c3_normalization]]
