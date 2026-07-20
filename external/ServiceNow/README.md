# ServiceNow CMDB/CSDM Documentation — Source Manifest

**Project:** DryDocs external reference — ServiceNow (C10)
**Captured:** 2026-07-20 (user download; analyzed same day)
**Purpose:** CMDB/CSDM/ITAM concept mining for the DryDocs ontology and the
generic-terminology (SaaS-configurable naming) research — see
`knowledge/upgrade-plans/servicenow-cmdb-analysis.md` (the committed analysis) and
`knowledge/upgrade-plans/generic-terminology-research.md`.

**Classification:** `External` (vendor documentation; per-file provenance below;
`captured_at: 2026-07-20`). **Redistribution decision (C10 housing step, the BMC
poster precedent):** the vendor binaries **and their verbatim extracted-text twins are
gitignored — local reference only** (`external/ServiceNow/*.pdf|pptx|docx`,
`external/ServiceNow/extracted/`). A full-text dump is the vendor's words, not our
summary; this repo is sometimes published. The committed record is THIS manifest plus
the analysis note (ours, GROUNDED/SYNTHESIZED). Note: the ITAM deck's own FAQ grants
ecosystem reuse of Now Create decks for *delivery/presentation*; we still keep binaries
out of the publishable tree — conservative by design.

**Source:** ServiceNow **Now Create** portal assets (identified by the in-file asset
numbers) plus ServiceNow customer-success/process-guide material.
`source_url` (portal): https://www.servicenow.com/success/now-create.html — individual
assets sit behind the portal login; the asset number is the stable citation.

## Files

| File | Now Create asset # | Date in file | What it is |
|---|---|---|---|
| `What are services and service offerings.pdf` | 0003948 | July 2024 | 4-page explainer: service vs service offering; the three CSDM service types (business / application / technical); the service→offering→application relationship example; categorization questions |
| `CMDB - Product Architecture.pptx` | 0002024 | Sept 2023 | CMDB product architecture: CI class/table structure (`cmdb` → `cmdb_ci` → child classes), CSDM one-pager with the Design/Build/Sell-Consume/Manage domain definitions, IRE flow, foundation data, model hierarchy |
| `CMDB Data Manager.pptx` | 0003551 | March 2025 | Policy-driven bulk CI lifecycle: Retire/Archive/Delete/Attestation policies, Managed-By-Group approvals, exclusion lists, orphan dependent-CI cleanup, cascade retire, staleness |
| `CMDB Governance Workshop.pptx` | (header carries "Asset Number:" without a legible value in extraction) | April 2025 | Governance workshop deck: 4-step operating sequence, CCB + RACI schema governance, CMDB health KPIs (completeness/correctness/compliance/relationships), maturity scorecard, CSDM table map + prescribed relationships, Yokohama renames (Application Service → Service Instance) |
| `CMDB - Process Guide.docx` | 0001261 | Dec 2025 | Configuration Management process guide: the five-activity CM process, IRE identification + per-attribute reconciliation, CSDM 5.0 six domains, Crawl/Walk/Run population ladder, CI lifecycle status/stage, health KPIs, RACI roles |
| `ITAM - SAM - Product Integration Options - Yokohama.pptx` | 0001397 | Yokohama release | Now Create partner-delivery template: SAM integration options, source-of-record integration types, SAM tables, Software Asset Connection via IRE, content service |

## Trust axis (provenance tiers — `config/classification.yaml` NB)

| Artifact | Tier |
|---|---|
| The binaries (local only) | **VERBATIM** vendor material |
| `extracted/*.txt` twins (local only; `scripts/extract_office_text.py`) | **VERBATIM** — mechanical text extraction, no interpretation |
| `knowledge/upgrade-plans/servicenow-cmdb-analysis.md` (committed) | **GROUNDED** summaries of doc content + **SYNTHESIZED** DryDocs dispositions (marked per section) |

## The hard rule

Nothing in this doc set is adopted into the graph or vocabulary by ingestion. Any
concept implying node/edge meaning is listed in the analysis note as a gate-bound
candidate (`status: planned/proposed`) and routes through the HITL gate
(`docs/restructure/03-hitl-sme-flow.md`) — the C10 acceptance clause.

## Regenerating the local text twins

```powershell
poetry run python scripts/extract_office_text.py external/ServiceNow
```
