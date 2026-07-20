---
name: controlm-runbook-automation
description: "COMPANY-SPECIFIC workflow skill: automate runbook creation from the Control-M knowledge graph and fix job/folder metadata in small failure-driven batches. Use when: (1) planning or building any phase of the runbook pipeline — CMDLINE→dataset-GUID lineage extension, failure-batch selection, data-series extraction (FileWatcher → RAW → ING → LD provisioning chains), HITL metadata review, or the Jira fix package (xml before/after, change doc, mermaid flow, generated runbook), (2) generating a runbook for a data series or SEAL from graph data, (3) checking a series for naming/SCIM/escalation conformance or description-metadata completeness, or (4) deciding where a runbook field's system of record is. Builds ON the generic controlm-db skill (CM_ replica ingest/query) but encodes this company's integrations: PAT product catalog alignment, SCIM/escalation DB routing, the dataset metadata service, and the support→dev Jira handoff (SoD: we analyze, dev implements). Mechanism-only in committed files; real instances live in internal-local/ and internal/."
---

# Control-M runbook automation (company-specific)

**The primary use case.** The team is "application support" in name but supports
many apps without being in the design sessions. Runbooks arrive as folder-level
spreadsheets, yet ~95% of their content already lives in systems we can query.
This skill drives generating the runbook **from the graph** and using each
generation pass to fix the underlying metadata in small, failure-driven batches
— ending in a Jira the dev team implements (separation of duties: **we never
deploy**).

**This skill is company-specific by design.** It layers this company's
integrations — PAT catalog, SCIM/escalation DB, the dataset metadata service,
HLT/DAT naming standards, the Jira workflow — on top of two generic skills:

| Dependency | What it provides |
|---|---|
| `controlm-db` (generic) | CM_ replica schema map, ingest loaders, query cookbook, the derived `:WAS_INFORMED_BY` edge |
| `data-context-extractor` | `:DataAsset` conventions (platform = property, never a node), lineage edge vocabulary |
| review toolkit (`drydocs/graph_review.py` + gates) | every metadata change is a *proposal* through the HITL gate |

A template consumer adopting DryDocs should treat this skill as a **worked
example of an instance workflow**, not part of the generic base.

## Where everything is

- **The plan of record** — pipeline phases P1–P6, the runbook-field →
  system-of-record map (§RB, the generator spec), and the verified gap table:
  [`references/plan.md`](references/plan.md). Read it first for any task here.
- **The toolchain** — module/tool/skill inventory for the lineage model (C2
  `drydocs-lineage`) and the remediation sub-module decision (C1
  `drydocs-remediation`, no graph write), with build order:
  [`references/toolchain.md`](references/toolchain.md).
- **The fix-package contract** — the developer-handoff artifact spec (XML
  round-trip rules, Excel formats, the paste-ready Jira comment for an
  *existing* ticket): [`references/fix-package.md`](references/fix-package.md).
- Concept → table resolution, SQL patterns, ingest rules: the `controlm-db`
  skill (do not duplicate them here).
- Real values (SEALs, folders, queues, service hosts, runbook examples):
  gitignored `internal-local/CONSOLIDATED-runbook-standards-screenshots.md`
  (screenshot consolidation) — never in committed files.

## Quick orientation (from the plan)

```
P1 base graph  →  P2 CMDLINE lineage  →  P3 pick fix batch (failures)
      →  P4 extract data series (FW → provisioning)  →  P5 HITL review + target metadata
      →  P6 fix package → Jira (dev team implements)
```

- **First new build:** P2 — launcher `-pipeline <GUID>` extraction + the dataset
  metadata-service join + the file-name component decomposer
  (`CM_JOB_FILE_NAME_STANDARD` shape, proposed standard).
- **Highest-value P3 target:** jobs with **no SCIM row** (failures fall to the
  shared common queue and can be missed entirely).
- **Load-bearing conformance fact:** SCIM `EAPPLICATION` is derived from the job
  name and fails on naming-convention mismatch — naming conformance is a
  *routing defect* check, not cosmetics.

## Guardrails

- Everything in `controlm-db` §Guardrails applies (read-only replica, current
  version only, expensive history views, publish boundary).
- **SoD:** output of this workflow is analysis + a Jira package; the dev team
  changes Control-M. Never emit deployment steps as if we execute them.
- **HITL:** no metadata change lands in the graph or an XML without going
  through the review gate as a proposal.
- New edge/property types discovered while extending lineage (e.g. file-name
  components → DCAT terms) go through `ontology-mapper` + the HITL gate;
  extension → DistributionRole is a taxonomy import first.
