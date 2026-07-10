# Control-M Standards — Governance Hierarchy

**Corpus:** INTERNAL (governance). **Status:** 🟠 ASSEMBLED — 2026-06-17. **Branch:** `controlm-spinoff`.
Source of internal guidelines, assembled from SME-supplied screenshots (escalation DB DDL + join SQL/SCIM template, Escalation Manager portal, the SCIM Details Confluence page, the **DAT NFR Checklist** + ICDW/Snowflake variant, the HLT decommissioning/compliance page, CHG46712473 critical-batch thread, the HL app-code→queue mapping, and the HLT/DAT Control-M guideline pages) and SME narration. This README defines the **authority hierarchy** the other docs sit in.

> ⚠️ These are *internal* standards — mutable, sometimes contested between towers (see §3). Authoritative for *our* conformance, not vendor capability. Tag provenance accordingly on graph load. See the corpus split in [[project-drydocs-scrape-two-corpus]].

---

## 1. The four tiers (precedence: top wins on capability, narrows going down)

| Tier | Owner | Viewpoint | Answers | Authority |
|---|---|---|---|---|
| **① Vendor (master)** | BMC | Product capability | "Is this *possible/legal* in Control-M?" | Absolute on capability — `../../vendor-bmc/` |
| **② Control-M Platform team** | internal platform org | Platform operation | "How does *this shop* run Control-M?" (servers, folders, versioning, site standards) | Binds across all towers |
| **③ DAT — Data & Analytics** | DAT SRE | **Platform monitoring** | "How are *data/analytics platform* jobs named + escalated?" (Grafana, NFR) | Within DAT/platform-coded estates |
| **④ HLT — Home Lending** | us (prod support) | **Application monitoring** | "How are *Home Lending application* jobs named + escalated?" | Within HLT estates |

- **Capability flows down, conformance narrows down.** A tower standard may *tighten* the platform standard but never exceed vendor capability.
- ③ and ④ are **peer towers with different philosophies** (§3), not a strict parent/child. Where they diverge, document both; for HLT-owned folders, HLT wins.

---

## 2. Documents in this set

| Doc | Tier | What |
|---|---|---|
| [escalation-scim-reference.md](escalation-scim-reference.md) | cross (②–④) | The **escalation DB / SCIM** record + queue routing — how a job failure routes to a support queue. The shared mechanism all towers configure. |
| [dat-naming-standard.md](dat-naming-standard.md) | ③ DAT | DAT SRE platform-view naming + NFR standard (hardcoded for Grafana). |
| [hlt-naming-standard.md](hlt-naming-standard.md) | ④ HLT | HLT application-view naming + the philosophy/gotchas behind it. |
| [nfr-catalog.md](nfr-catalog.md) | ③ DAT (inherited ④) | The full **DAT NFR Checklist** by category (Monitoring/Alerting/Logging/Performance/Op-Readiness/Batch/Resiliency/Build/Security), structured-logging spec, ICDW/Snowflake variant, decommissioning workflow. |
| [scim-hpsm-queue-registry.md](scim-hpsm-queue-registry.md) | cross | Area-Product→SEAL→queue grid, queue-code anatomy, L2/L3 support flow, job↔SCIM 1:1. |
| [critical-batch-and-self-heal.md](critical-batch-and-self-heal.md) | cross | Tier-1 critical batch (`go/dat6am`), self-heal `VR:` codes + exclusions, SCIM data-quality fixes (CHG46712473). |
| [command-line-and-variables-standard.md](command-line-and-variables-standard.md) | ④ HLT (formalized) | The **CBT "Command line and variables v2"** spec — canonical variable registry + alias rollups, per-framework command-line templates, NF-VAL/AUD/SEC IDs, and the tooling behaviour that maps onto the engine. Ratifies R2/R16. |
| [nfr-consistency-and-greenfield.md](nfr-consistency-and-greenfield.md) | synthesis | What's consistent across towers + best-practice → ideal greenfield. |
| [greenfield-recommendations.md](greenfield-recommendations.md) | 🟣 recommendation (D5) | Best-practice → ideal greenfield, grounded in ontology/SDLC/corporate. Worked first: **job naming & numbering** (GUI alphanumeric order == execution order; R29). |

Foundational naming already in the parent corpus: [folder-naming (PRAOCG)](../folder-naming-convention.md), [data-center default time](../data-center-naming-convention.md), [Description metadata plan](../description-field-metadata-plan.md), [standards rules registry](../standards-rules-registry.md).

---

## 3. The central tension (platform view vs application view)

The two tower viewpoints disagree on **what monitoring is for**, and it shows up in escalation routing defaults:

- **DAT (platform view):** naming is *hardcoded* so the platform's Grafana dashboards can parse it; failures of platform-coded jobs (e.g. `PRAOC`, `PRDCL`) **default to the platform L1 queue `C1CCBDATAECO`** when there's no escalation-DB entry. Optimized for one central dashboard team.
- **HLT (application view):** monitoring should route a failure to *the team that owns the application*. HLT therefore **defaults to the owning dev queue** (not a generic platform L1) when no escalation entry exists — so an un-configured failure still lands with someone accountable.

Practical consequence (the SME's core concern): with shared platform app codes (`PRAOC`, `PRDCL`) spanning *many* folders across teams, teams lose track and **default to their own** conventions; mis- or un-configured jobs silently route to the platform L1 queue. HLT exists to counter that. The remediation greenfield (§ synthesis doc) should encode the application-view default explicitly.

> **Bandwidth reality:** HLT has no dashboard team; it **piggybacks** on DAT's Grafana platform. So HLT naming must stay *parseable by DAT's tooling* even while expressing an application view — a real constraint on how far HLT can diverge.

---

## 4. How this maps to the remediation / greenfield

- The **escalation/SCIM** config and the **naming** standards are two halves of the same conformance surface; the [standards rules registry](../standards-rules-registry.md) (**R1–R29**) is where they become checkable.
- Goal-2 synthesis turns "what's consistent across ② ③ ④" into the **ideal greenfield** target the spin-off authors and proves.
- ⚠️ **Naming ≠ intent (ontology gotcha):** job names encode a *type token* (e.g. `_FW`), but the token doesn't always equal the behavior — some `_FW` File Watchers depend on a **predecessor preprocessing job that calls an API**, not a file transfer. The ontology must derive intent from the *resolved flow*, not the name token alone (carried into the synthesis doc).

Related: [[project-folder-naming-praocg]], [[project-description-metadata-plan]], [[project-controlm-remediation-spinoff]], [[project-drydocs-scrape-two-corpus]]
