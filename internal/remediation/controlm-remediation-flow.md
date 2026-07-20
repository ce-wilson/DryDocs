# Control-M Remediation — Purpose & Operating Flow (TARGET-STATE CORRECTION)

**Corpus:** INTERNAL. **Status:** 🟠 CAPTURED 2026-06-18 — **pending integration** into [controlm-remediation-spinoff-plan.md](controlm-remediation-spinoff-plan.md). **Branch:** `controlm-spinoff`.

> ⚠️ **This corrects/expands the spin-off's stated purpose.** Captured from SME on 2026-06-18; not yet folded into the plan/scope docs (that's the next build). Source of truth for the *why* and the *operating loop* until integrated.

---

## 1. The correction (what the spin-off actually is)

**Wrong framing (my earlier summary):** "we author change-specs/Jiras; the dev team implements on `main`." That conflated *production Control-M release* with the *DryDocs repo*, and made it sound like a generic legacy-modernization pipeline.

**Correct framing:** `ctm-remediate` is an **incident-driven remediation tool that OUR (production-support) team operates** to **fix recurring issues that are resolvable within the orchestration / Control-M job-flow layer.** We author + prove the fix; the dev team's role is only the **release into production Control-M** (SoD) — with a code review on a fully-packaged, pre-validated change. After release, **DryDocs re-ingests the new production state and updates the knowledge graph** (closed loop).

**Why it matters:** there are **many** dev teams and they **don't consistently follow best practices**. Concrete scenario: 3 teams doing one migration, each owning a different flow layer (file-watchers / ingestion / refined / provisioning) — and they diverge on standards. The recurring failures land on *us* (prod support), so we need a tool to remediate at the layer we legitimately own.

**Fix scope = orchestration / job-flow layer** (timings, schedules, dependencies/conditions, file-watcher settings, calendars, variables, Control-M metadata, runbooks) — **not** application code (that stays dev-owned).

---

## 2. The operating flow (A–G) — incident-driven remediation loop

**Prioritization (setup):** last year's **incident counts trended and sorted by top job failures** → pick the highest-recurring target.

| Step | Action | Notes / data source |
|---|---|---|
| **A. Gather the data-series neighborhood** | Pull the `.xml` for the target folder (by naming convention); pull **upstream/downstream folders for the same data series (3–4 folders)**; match with a **trailing wildcard (`*`)** on the folder name; **also pull folders on manual order**. | The full FW→ingestion→refined→provisioning neighborhood of one data series, not one folder in isolation. |
| **B. Get SCIM** | Use the **folder→jobs relationship** to query Oracle for the **corresponding SCIM** (escalation) records. | `CM_DEF_VJOB ⋈ CM_ESCALATION_DB` (the join we already have; [escalation-scim-reference §4](governance/escalation-scim-reference.md)). |
| **C. Analyze** | Analyze **error logs**; check **current flow timings, schedule, incoming files, dependencies, long-running** jobs. | Needs monitoring/history + log access (see open inputs §4). |
| **D. Root-cause + fix (human)** | Human identifies the issue (often 2–3 candidate fixes), then **applies the fix**. *Archetype:* a file-watcher triggers, but the job processes a **large file still being written**, so the next **TDQ validation job fails** (file-stability / still-writing race). | Multi-option remediation; human-in-the-loop is explicit here. |
| **E. Agent — standards + metadata** | A **Control-M-aware agent** scans for **our standards** (variables, naming), **adds Control-M metadata**, updates toward **greenfield**. | Drives the R1–R29 registry + the Description-metadata plan. |
| **F1. Agent — config conflicts** | Agent scans the **Control-M configuration for conflicts** (e.g. calendar issues). | Cross-folder/server consistency, calendar/RBC ([calendar-resolution plan](calendar-resolution-projection-plan.md)). |
| **F2. Runbook** | Generate a **new production-support runbook** (deterministic). | Output artifact for ops. |
| **G. Package + handoff** | Create a **Jira to the dev team** (cards / HLT / auto / …): summarize **issue, root cause, resolution**; package **legacy `.xml` + greenfield `.xml` + SCIM update**; **code review** with that team **to release**. | The SoD handoff = *release*, not authoring. |
| **Close loop** | Once released to production, **DryDocs ingests it → knowledge graph updates.** | Recurring issue retired; metadata + graph enriched. |

**The value loop:** fix recurring issues → update Control-M metadata → produce deterministic runbooks → enrich the knowledge graph → fewer recurrences.

---

## 3. Docs to update when integrating (next build)
- [controlm-remediation-spinoff-plan.md](controlm-remediation-spinoff-plan.md) §1 purpose + §3 architecture: add the incident-driven loop, the agent-assisted steps (E/F1/F2), the closed-loop ingestion, and the orchestration-layer fix-scope boundary. Fix the "implements on `main`" → "releases into production Control-M."
- [controlm-remediation-m0-poc-scope.md](controlm-remediation-m0-poc-scope.md) / [phases M1–M4](controlm-remediation-phases-m1-m4-scope.md): map A–G onto the gate model (A–C ≈ Capture/analyze, D–F ≈ Design/validate + agent, G ≈ Package).
- [controlm-remediation-information-needed.md](controlm-remediation-information-needed.md): add the new inputs (§4 below).
- [main-branch-gap-analysis.md](main-branch-gap-analysis.md): note the SoD wording = production-Control-M release, not DryDocs-repo `main`.
- [standards-rules-registry.md](standards-rules-registry.md): add a **file-stability / FW-still-writing** rule candidate (the D archetype) — e.g. min-size + search-interval + a stability gate before downstream TDQ.

---

## 4. Open questions / inputs to resolve before building
1. **"Apply the fix" (step D) boundary:** offline `.xml` authoring + equivalence-proof only (dev does the *only* deploy), **or** do we have a **dev/QA Control-M** we can write to for testing before dev releases to prod?
2. **Fix-scope catalog:** do we want the tool to **enforce** a defined set of "orchestration-layer-fixable" issue types (FW settings, conditions/deps, timings/calendar, variables/metadata, runbook) and explicitly exclude app-code — or leave the boundary to human judgment per case?
3. **"Control-M agent"** = an AI/automation agent operating on Control-M data/config (assumed), not the CTM execution Agent — confirm.
4. **Data sources** for A–C: incident trending (SNOW? a report?), error logs (Splunk? Control-M log? agent host?), file-arrival/long-running timings (Control-M monitoring/history = the same **A3** access already flagged).
5. **Data-series gather rule (A):** define "same data series" precisely (shared SEAL/dataset across the 4 flow layers, matched by folder-name prefix + wildcard) + the manual-order inclusion rule.

Related: [[project-controlm-remediation-spinoff]], [[project-controlm-escalation-governance]], [[project-description-metadata-plan]], [[project-calendar-projection-plan]]
