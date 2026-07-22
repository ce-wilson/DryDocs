# Documentation inventory — main @ a5bb0b3 (2026-07-22)

> **Pass 1 of the /documentation review.** Every tracked `*.md` on `main` (436 files), by
> folder, with git **created** / **last-updated** dates and purpose. Bulk reference corpora
> are rolled up as one line each (count + date range). A frozen verification copy of this
> list was delivered separately; pass 2 (grouped-by-purpose updates) must not touch it.
>
> **Date caveats:** main's history was squashed 2026-07-20 ("Initial import" `c5a84c3`), so
> *created* dates come from the local `archive/old-history-2026-07-20` tag and *last-updated*
> from post-squash commits (falling back to the archive when a file hasn't been touched
> since). Renames are not followed — a moved file's *created* is its first commit at the
> current path (e.g. `docs/history/*` shows the archive dates of the moved copies).
>
> **Status legend:**
> `living` — kept current; pass-2 update candidate.
> `record` — point-in-time decision/review/log; append or supersede, never rewrite. **Not updated in pass 2.**
> `historical` — preserved origin/milestone document. **Never updated.**
> `corpus` — verbatim/distilled external reference; changes only with a re-scrape. **Not updated in pass 2.**
> `wip` — active working area (concurrent-session territory). **Left alone in pass 2.**

## Root (repo governance & routing)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| README.md | 2026-05-05 | 2026-07-11 | living | Public repo front door: what DryDocs is, layer model, quick links |
| CLAUDE.md | 2026-06-20 | 2026-07-21 | living | The agent operating guide / routing brain (layers, references, ritual) |
| MODULE_MAP.md | 2026-06-26 | 2026-07-18 | living | drydocs-core vs component boundary map (ADR 0002-A Phase B) |
| PUBLISH-BOUNDARY.md | 2026-06-20 | 2026-06-20 | living | Sensitivity classifications → what is stripped on public push |
| VERSIONING.md | 2026-07-09 | 2026-07-10 | living | Versioning policy for the package family |
| CHANGELOG.md | 2026-07-09 | 2026-07-09 | living | Release changelog (currently stops at the 07-09 entry) |
| git-readme.md | 2026-06-09 | 2026-07-20 | living | Cross-repo port guide: producer → company GHE (disjoint mains) |

## docs/ (top level)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| docs/controlm-c3-normalization-status.md | 2026-06-11 | 2026-07-15 | living | C3/C4 normalization status & runbook (Phases A–D) |
| docs/controlm-job-type-tables-plan.md | 2026-07-15 | 2026-07-15 | living | Plan: job-type detail tables (Phase C/D extension) |
| docs/controlm-staging-ingestion-flow.md | 2026-07-07 | 2026-07-20 | living | Staging schema & orchestrated ingestion flow reference |
| docs/next-internal-session.md | 2026-07-16 | 2026-07-22 | living | Live-data confirmation checklist (internal-session queue) |
| docs/oracle-sql-logging.md | 2026-07-11 | 2026-07-11 | living | Guide: per-run SQL evidence logging on `ingest-controlm --use-oracle` |
| docs/port-prompt.md | 2026-06-22 | 2026-07-22 | living | Rolling producer→company port prompt (v2, steps 43+) |
| docs/port-prompt-archive-steps-1-42.md | 2026-07-21 | 2026-07-21 | historical | Frozen port steps 1–42 (applied via PORT-REPORT) |
| docs/port-T12-company-gate-pack.md | 2026-07-21 | 2026-07-21 | record | T12 company platforms gate session pack (supersede-or-reconcile) |
| docs/ruff-format-convergence.md | 2026-07-20 | 2026-07-20 | living | Two-sided ruff-format adoption plan (J10 amended scope) |
| docs/RELATIONSHIP_GUIDE.md | 2026-05-20 | 2026-07-15 | living | Relationship-type governance guide + vocabulary registry pointer |

## docs/decisions/ (ADRs — immutable once accepted; superseded, never rewritten)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| docs/decisions/README.md | 2026-07-02 | 2026-07-14 | living | ADR index & conventions |
| 0001-ontology-base-scope.md | 2026-06-22 | 2026-06-22 | record | Freeze the PROV spine, demote the rest |
| 0002-component-database-topology.md | 2026-06-26 | 2026-07-11 | record | Modular components over isolated graphs |
| 0002-a-drydocs-core-extraction-plan.md | 2026-06-26 | 2026-07-10 | record | drydocs-core thin-extraction plan |
| 0002-a-1-phase-b-thin-relocate.md | 2026-07-10 | 2026-07-10 | record | Phase B physical relocate amendment |
| 0002-b-spinoff-rebase-checklist.md | 2026-06-26 | 2026-07-10 | record | controlm-spinoff → drydocs-remediation rebase checklist |
| 0002-c-depgraph-lineage-rehome.md | 2026-07-01 | 2026-07-11 | record | depgraph → drydocs-lineage re-home plan |
| 0003-application-naming-disambiguation.md | 2026-07-05 | 2026-07-05 | record | "Application" naming: source terms verbatim, one canonical label |
| 0004-software-registry-vendor-terminology.md | 2026-07-07 | 2026-07-07 | record | "Vendor" means the brand; software-registry model |
| 0005-browser-neo4j-access-path.md | 2026-07-14 | 2026-07-14 | record | Thin API is the deployment shape; bolt-from-browser dev-only |
| 0006-docmeta-component-and-doc-graph.md | 2026-07-20 | 2026-07-20 | record | docmeta is its own component; doc-graph vocabulary |

## docs/design/ (governed surfaces — `.md` is source of truth, `.html` renders are deterministic; publish VERBATIM)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| controlm-ingestion-tdd.md | 2026-07-07 | 2026-07-15 | living | TDD: the `ingest-controlm` M3 chain |
| drydocs-project-tdd.md | 2026-07-12 | 2026-07-12 | living | TDD: the platform (layers, components, governance, graph) |
| drydocs-remediation-tdd.md | 2026-07-08 | 2026-07-10 | living | TDD: drydocs-remediation (detect → transform → prove → Jira) |
| drydocs-web-console-tdd.md | 2026-07-18 | 2026-07-21 | living | TDD: web console + thin API |
| drydocs-project-review.md | 2026-07-14 | 2026-07-21 | living | The whole-project review (kept-updated review doc) |
| drydocs-startup-refresh-runbook.md | 2026-07-20 | 2026-07-20 | living | Runbook: local startup & refresh (EE container + sample ingest) |
| drydocs-web-console-runbook.md | 2026-07-21 | 2026-07-21 | living | Runbook: web console & API startup |
| drydocs-mapping-demo-runbook.md | 2026-07-21 | 2026-07-21 | living | Runbook: mapping-store demo site (O13 `/demo`) |
| drydocs-lineage-mac-runbook.md | 2026-07-21 | 2026-07-21 | living | Runbook: lineage ingest (jobs CSV + DPL MAC) → curated load |
| graph-retrieval-benchmark-explainer.md | 2026-07-16 | 2026-07-17 | record | Narrative explainer of the P0 retrieval benchmark result |
| feedback/README.md | 2026-07-08 | 2026-07-20 | living | HITL annotation flow for design docs (Epic L) |
| feedback/scans/README.md | 2026-07-08 | 2026-07-08 | living | Raw paper-HITL scan drop conventions (L6) |

## docs/restructure/ (the plan spine)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| 00-conceptual-model.md | 2026-06-20 | 2026-07-10 | living | Taxonomy → ontology → KG → context-graph conceptual model |
| 01-project-plan.md | 2026-06-20 | 2026-07-05 | living | The phased project plan |
| 02-backlog.md | 2026-06-20 | 2026-07-07 | record | Legacy text backlog view (superseded by backlog.yaml + board) |
| 03-hitl-sme-flow.md | 2026-06-20 | 2026-07-07 | living | The guided per-decision HITL SME gate flow |
| 04-sme-checklist-and-load-plan.md | 2026-06-21 | 2026-07-22 | record | SME checklist + sequential load plan (snapshot; supersession banner added in pass 2) |
| 05-drydocs-review-backflow.md | 2026-07-01 | 2026-07-07 | living | Company→producer back-flow plan (drydocs-review) |
| 06-provenance-source-audit-fields.md | 2026-07-06 | 2026-07-07 | living | Provenance diet + per-source audit envelope plan |
| 06a-controlm-source-er-review.md | 2026-07-06 | 2026-07-07 | living | Control-M source ER review for the audit-fields gate |
| 07-software-registry.md | 2026-07-07 | 2026-07-10 | living | Third-party software registry design (Vendor → Product) |
| 08-source-column-mappings.md | 2026-07-07 | 2026-07-07 | living | Per-source column ledger contract (profiled → projected → graph) |
| IDEAS.md | 2026-06-20 | 2026-07-21 | living | The idea inbox + groom audit trail |

## docs/reviews/ (review & audit records; two living SDLC docs)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| CHECKPOINT.md | 2026-06-18 | 2026-07-01 | record | Persona-review cron checkpoint state |
| SDLC-CHECKPOINT.md | 2026-06-18 | 2026-07-01 | record | SDLC-docs cron checkpoint state |
| persona-review-plan.md | 2026-06-18 | 2026-07-01 | record | The resumable multi-persona review routine plan |
| persona-oracle-dba.md | 2026-06-18 | 2026-07-01 | record | Persona review: Oracle DBA (Phase 1) |
| persona-neo4j-architect.md | 2026-06-18 | 2026-07-01 | record | Persona review: Neo4j architect/ontology (Phase 2) |
| persona-review-summary.md | 2026-06-18 | 2026-07-01 | record | Synthesis of the persona reviews |
| drydocs-consolidated-plan.md | 2026-06-18 | 2026-07-01 | record | Consolidated work plan (pre-restructure era) |
| feature-oracle-ingestion-plan.md | 2026-06-18 | 2026-07-01 | record | Oracle-ingestion feature scaffold + sync contract |
| sdlc-docs-plan.md | 2026-06-18 | 2026-07-01 | record | SDLC documentation session plan |
| sdlc-neo4j-schema.md | 2026-06-18 | 2026-07-01 | living | Living SDLC doc: Neo4j schema meta (§FR §UC §DEP …) |
| sdlc-oracle-ingestion.md | 2026-06-18 | 2026-07-01 | living | Living SDLC doc: Oracle ingestion |
| doc-knowledge-ingestion-review.md | 2026-07-07 | 2026-07-07 | record | Review of documentation/knowledge ingestion paths |
| essential-graphrag-traversal-experiment.md | 2026-07-16 | 2026-07-16 | record | Q2 agent-traversal experiment write-up |
| tech-debt-documentation.md | 2026-07-11 | 2026-07-11 | record | Repo-wide documentation tech-debt audit |
| tech-debt-port-boundary.md | 2026-07-09 | 2026-07-11 | record | Port-boundary tech-debt audit |
| tech-debt-taxonomy-ontology-map.md | 2026-07-09 | 2026-07-11 | record | Taxonomy→ontology map tech-debt audit |
| doc-inventory-2026-07-22.md | 2026-07-22 | 2026-07-22 | record | THIS file — pass-1 documentation inventory |

## docs/history/ (milestone archive — never updated)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| README.md | 2026-05-18 | 2026-05-18 | historical | Index of the milestone archive |
| LoadPlanV2.md | 2026-05-18 | 2026-05-18 | historical | Original Neo4j loader plan v2 |
| LoadPlanV3.md | 2026-05-18 | 2026-07-21 | historical | Loader plan v3 (delta on v2; 07-21 touch = link fix) |
| M0-README.md | 2026-05-18 | 2026-05-18 | historical | M0 bootstrap milestone record |
| M1-Fix-README.md | 2026-05-18 | 2026-05-18 | historical | M1 SEAL fix + schema upgrade record |
| controlm-loader-flow.md | 2026-07-20 | 2026-07-20 | historical | Loader-flow baseline captured for schema review |
| next-session-cron-prompt.md | 2026-07-11 | 2026-07-11 | historical | Retired oracle-ingestion cron handoff prompt |

## docs/Product/ (captured org/product source material — treat as source, not prose to update)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| product-overview.md | 2026-06-09 | 2026-06-09 | record | LOB→Product→Team org taxonomy capture |
| Technology_Team_Types.md | 2026-06-09 | 2026-06-09 | record | Agile team types & interaction models capture |
| technology_roles_and_responsibilities.md | 2026-06-09 | 2026-06-09 | record | Standardized roles & responsibilities capture |
| seal/seal-application-hierarchy.md | 2026-07-15 | 2026-07-15 | record | SEAL application hierarchy (describes image-2) |
| seal/image-2.md | 2026-06-09 | 2026-06-09 | record | SEAL hierarchy image transcription |

## docs/patterns/data-catalog/ (pattern reference set)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| README.md | 2026-06-18 | 2026-06-30 | living | Index of the catalog+orchestration pattern set |
| enterprise-data-catalog-ontology.md | 2026-06-18 | 2026-06-18 | record | Machine-first catalog ontology reference |
| ontology-standard.md | 2026-06-18 | 2026-06-18 | record | Catalog ontology standard write-up |
| data-catalog-drydocs-crosswalk.md | 2026-06-18 | 2026-06-18 | record | Catalog ↔ orchestration-graph crosswalk |
| lineage-design-top3.md | 2026-06-18 | 2026-06-18 | record | Top-3 Neo4j lineage modeling patterns |
| dataset-registration-architecture.md | 2026-06-28 | 2026-06-28 | record | Dataset-registration platform architecture |
| ingestion-formalization.md | 2026-06-28 | 2026-06-28 | record | Ingestion compare/contrast & formalization |
| jpmc-annual-report-domain.md | 2026-06-30 | 2026-06-30 | record | Worked example: two documents as DataAsset nodes |

## docs/whitepaper/

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| drydocs-whitepaper.md | 2026-07-12 | 2026-07-12 | living | Outward-facing whitepaper Rev 1 (non-governed; editorial OK) |

## SDLC-Docs/extracted/ (origin-method documents — historical, never updated)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| FCD-Requirements.md | 2026-06-26 | 2026-06-26 | historical | **Full Circle Docs (FCD) MVP requirements & design (2018)** — the genesis document; DryDocs' original name |
| adopt-bdd-sdd-howto.md | 2026-06-26 | 2026-06-26 | historical | How to adopt BDD + spec-driven dev, worked example |
| feasibility-memo-context-sufficiency.md | 2026-06-26 | 2026-06-26 | historical | Feasibility memo: which method captures enough context |
| issue-driven-capture-loop.md | 2026-06-26 | 2026-06-26 | historical | Issue-driven capture loop concept |
| modular-architecture-plan.md | 2026-06-26 | 2026-06-26 | historical | Core + independent components, grounded vs uncertain graphs |
| plan-incrementalContextLoop.prompt.md | 2026-06-26 | 2026-06-26 | historical | Incremental context-loop plan prompt |

## config/ (configuration-layer docs)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| config/README.md | 2026-06-20 | 2026-06-20 | living | The configuration layer explained (precedence, registry, maps) |
| config/gate-log.md | 2026-06-21 | 2026-07-21 | record | **Append-only** HITL gate decision log |
| config/taxonomy/README.md | 2026-06-20 | 2026-07-21 | living | Taxonomy import conventions (classification only) |
| config/manual-loads/README.md | 2026-07-14 | 2026-07-14 | living | SME-authored CSV mappings (manual final option) |
| config/overrides/README.md | 2026-07-21 | 2026-07-21 | living | User override lists (M2 origin-flagged store) |

## knowledge/ (internal design prose that defines the graph)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| knowledge/README.md | 2026-06-19 | 2026-07-10 | living | What knowledge/ holds and how it's organized |
| knowledge/ARCHITECTURE.md | 2026-06-19 | 2026-07-10 | living | Repository organization & tuning plan |
| knowledge/refactor-plan.vendor-internal-separation.md | 2026-06-20 | 2026-07-10 | record | Executed vendor/internal separation plan |
| knowledge/ontology/DryDocs_Ontology_Documentation.md | 2026-06-19 | 2026-07-10 | living | Consolidated ontology documentation |
| knowledge/ontology/NODE_QUICK_REFERENCE.md | 2026-07-09 | 2026-07-10 | living | Node-label quick reference |
| knowledge/depgraph-snapshots/README.md | 2026-06-21 | 2026-07-01 | living | Depgraph snapshot ritual + viewer |
| knowledge/standards/README.md | 2026-06-19 | 2026-07-05 | living | Standards tree layout (by taxonomy path) |
| knowledge/standards/business/README.md | 2026-06-20 | 2026-06-20 | living | Placeholder: org-taxonomy standards |
| knowledge/standards/data/README.md | 2026-06-20 | 2026-06-20 | living | Placeholder: data-platform standards |
| knowledge/standards/technology/folder-naming-convention.md | 2026-06-20 | 2026-07-05 | living | PRAOCG folder-naming standard |
| knowledge/standards/technology/data-center-naming-convention.md | 2026-06-20 | 2026-07-09 | living | DC naming = default-time encoding standard |
| knowledge/standards/technology/description-field-metadata-plan.md | 2026-06-20 | 2026-06-20 | living | PLANNED: description-field metadata modernization |
| knowledge/standards/technology/calendar-resolution-projection-plan.md | 2026-06-20 | 2026-06-20 | living | PLANNED: calendar resolution & run projection |
| knowledge/standards/technology/filewatcher-postexec-token-cat.md | 2026-07-06 | 2026-07-06 | living | NFR: FileWatcher post-exec token `cat` standard |
| knowledge/upgrade-plans/internal-import.md | 2026-06-20 | 2026-06-20 | record | Executed internal-import upgrade plan v1 |
| knowledge/upgrade-plans/graphrag-llm-navigation.md | 2026-06-19 | 2026-07-17 | living | GraphRAG/LLM-navigation upgrade plan (benchmarked) |
| knowledge/upgrade-plans/docmeta-component.md | 2026-07-07 | 2026-07-16 | living | drydocs-docmeta component upgrade plan |
| knowledge/upgrade-plans/docmeta-p0-verdict.md | 2026-07-16 | 2026-07-16 | record | P0 benchmark verdict: traversal vs manifest vs vector |
| knowledge/upgrade-plans/mapping-store-plan-2026-07-17.md | 2026-07-17 | 2026-07-18 | record | Mapping-store (SQLite) plan — built (Epic O) |
| knowledge/upgrade-plans/neo4j-advisor-confirmation-2026-07-17.md | 2026-07-17 | 2026-07-17 | record | GraphAcademy MCP advisor configuration review |
| knowledge/upgrade-plans/generic-terminology-research.md | 2026-07-20 | 2026-07-20 | living | Replacing SEAL/PAT with configurable generic naming |
| knowledge/upgrade-plans/servicenow-cmdb-analysis.md | 2026-07-20 | 2026-07-20 | record | ServiceNow CMDB/CSDM doc-set analysis (C10) |

## reference/ (Tier-1 platforms & standards)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| reference/README.md | 2026-06-20 | 2026-06-20 | living | Tier-1 reference tier explained |
| reference/platforms/README.md | 2026-06-20 | 2026-06-20 | living | Platform reference index |
| reference/platforms/neo4j/README.md | 2026-06-20 | 2026-07-10 | living | Neo4j platform reference + skills pointer |
| reference/standards/README.md | 2026-06-20 | 2026-07-10 | living | Ontology-standards index |
| reference/standards/prov-o/README.md | 2026-06-20 | 2026-07-10 | corpus | PROV-O distillation |
| reference/standards/w3c-org/README.md | 2026-06-20 | 2026-06-20 | corpus | W3C ORG distillation |
| reference/standards/dprod-ekgf/README.md | 2026-06-20 | 2026-06-20 | corpus | DPROD/EKGF distillation |
| reference/standards/sosa-ssn/README.md | 2026-06-20 | 2026-07-05 | corpus | SOSA/SSN distillation |
| reference/research/README.md | 2026-06-20 | 2026-07-16 | living | Research-notes index |
| reference/research/essential-graphrag-notes.md | 2026-07-16 | 2026-07-16 | record | Essential GraphRAG pattern inventory notes |

## external/ (Tier-2 vendors we ingest FROM)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| external/orchestration/README.md | 2026-06-20 | 2026-06-20 | living | Tier-2 orchestrator index (BMC baseline) |
| external/orchestration/bmc-controlm/SOURCE-MANIFEST.md | 2026-06-20 | 2026-07-09 | living | Provenance manifest for the BMC corpus |
| external/orchestration/bmc-controlm/controlm-\*.md (27 files) | 2026-06-20 | 2026-07-09 | corpus | Distilled BMC Control-M vendor topics (API, folders, jobs, events, variables, XML format, utilities…) |
| external/orchestration/autosys/README.md | 2026-06-20 | 2026-07-05 | living | AutoSys placeholder (map-to-baseline) |
| external/orchestration/airflow/README.md | 2026-06-20 | 2026-07-05 | living | Airflow/MWAA placeholder (map-to-baseline) |
| external/ServiceNow/README.md | 2026-07-20 | 2026-07-20 | living | ServiceNow CMDB/CSDM doc-set source manifest |

## internal/ (confidential — never published)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| internal/README.md | 2026-06-20 | 2026-06-20 | living | What internal/ holds; publish-strip rules |
| internal/repo-README.md | 2026-07-21 | 2026-07-21 | living | Company-side repo README (runnable pipeline) |
| internal/helpmeloginlocalneo4j.md | 2026-07-11 | 2026-07-11 | living | Local Neo4j login setup & troubleshooting |
| internal/pat-evidence/README.md | 2026-07-20 | 2026-07-20 | living | PAT screenshot evidence conventions |
| internal/remediation/README.md | 2026-07-10 | 2026-07-12 | living | Remediation doc-port index (G3 / ADR 0002-B) |
| internal/remediation/controlm-remediation-flow.md | 2026-07-10 | 2026-07-10 | record | Remediation purpose & operating flow (target-state) |
| internal/remediation/controlm-remediation-spinoff-plan.md | 2026-07-10 | 2026-07-10 | record | Spin-off feasibility & templated plan |
| internal/remediation/controlm-remediation-m0-poc-scope.md | 2026-07-10 | 2026-07-10 | record | M0 PoC detailed scope |
| internal/remediation/controlm-remediation-phases-m1-m4-scope.md | 2026-07-10 | 2026-07-10 | record | M1–M4 phase scopes |
| internal/remediation/controlm-remediation-information-needed.md | 2026-07-10 | 2026-07-10 | record | Information-needed register |
| internal/remediation/m0-poc-worked-example.md | 2026-07-10 | 2026-07-10 | record | M0 PoC worked example (offline) |
| internal/remediation/m0/engine-run-2026-07-10.md | 2026-07-10 | 2026-07-10 | record | First mechanized engine run log |
| internal/remediation/standards-normalization-plan.md | 2026-07-10 | 2026-07-10 | record | Confluence standards → tiered lookup normalization plan |
| internal/remediation/standards-rules-registry.md | 2026-07-10 | 2026-07-10 | living | R1–R28 machine-checkable standards rules registry (DRAFT) |
| internal/remediation/governance/README.md | 2026-07-10 | 2026-07-10 | living | Governance corpus hierarchy index |
| internal/remediation/governance/\* (8 standards docs) | 2026-07-10 | 2026-07-10 | corpus | Captured company standards (CMD_LINE/vars v2, DAT/HLT naming, NFR catalog+synthesis, critical batch, greenfield, continuation plan) |

## Component / code-adjacent READMEs

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| drydocs/loaders/README.md | 2026-06-19 | 2026-06-20 | living | Loader layout by source |
| drydocs/loaders/sql/adhoc/README.md | 2026-06-18 | 2026-06-18 | living | Ad-hoc probe SQL conventions (outside the ship path) |
| drydocs_api/README.md | 2026-07-14 | 2026-07-14 | living | Thin read API over the graph |
| drydocs_core/schema/provisioning/README.md | 2026-07-10 | 2026-07-22 | living | Multi-DB topology provisioning (G1 / ADR 0002 D1) |
| drydocs_lineage/collect/README.md | 2026-07-11 | 2026-07-11 | living | Run-As-User inventory collector |
| web/README.md | 2026-07-03 | 2026-07-15 | living | DryDocs web console (React) |
| scripts/README.md | 2026-06-20 | 2026-07-22 | living | Operational ingestion entry points |
| graph-tests/README.md | 2026-07-01 | 2026-07-07 | living | Data-driven acceptance suites for graph-verify |
| agents/README.md | 2026-07-03 | 2026-07-03 | living | Google ADK agent service sandbox |
| libs/oracle_kerberos/README.md | 2026-07-02 | 2026-07-10 | living | Kerberos SID-login module (Spider/PSGMGR) |
| drydocs-icons/SOURCE.md | 2026-07-03 | 2026-07-03 | record | Icon registry source attribution |

## UI-WIP/ (active design working area — concurrent-session territory, left alone in pass 2)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| site-plan.md | 2026-07-17 | 2026-07-21 | wip | Single-track ReUI site plan (the UI source of truth) |
| DryDocs_UI_Development_Specs.md | 2026-07-21 | 2026-07-21 | wip | UI development specifications |
| kept-orbit-philosophy.md | 2026-07-21 | 2026-07-21 | wip | "Kept Orbit" design philosophy |
| layout-anatomy-checklist.md | 2026-07-21 | 2026-07-21 | wip | App-shell layout anatomy checklist |
| icons.md | 2026-07-21 | 2026-07-21 | wip | Icon set notes |
| gemini-wire-frame.md | 2026-07-21 | 2026-07-21 | wip | Imported wireframe concept |
| design-review.md | 2026-07-14 | 2026-07-14 | wip | Critique of drydocs-landing-dark.html |
| wireframe-guide.md | 2026-07-14 | 2026-07-14 | wip | Wireframing-with-Claude working guide |
| wf-landing-01.md / wf-admin-config-01.md / wf-mapping-01.md / wf-module-subpage-01.md (4 files) | 2026-07-17 | 2026-07-17 | wip | Rung-2 text wireframes |
| wf-runbook-path-01.md | 2026-07-21 | 2026-07-21 | wip | Rung-2 wireframe: app-to-app path runbook |

## .claude/ (agents & skills — operating configuration)

| File | Created | Updated | Status | Purpose |
|---|---|---|---|---|
| agents/taxonomy-importer.md | 2026-06-20 | 2026-07-10 | living | Layer-1 import sub-agent definition |
| agents/ontology-mapper.md | 2026-06-20 | 2026-07-10 | living | Layer-2 mapping sub-agent definition |
| agents/pipeline-config.md | 2026-06-20 | 2026-06-20 | living | Config-layer sub-agent definition |
| agents/reference-librarian.md | 2026-06-20 | 2026-06-20 | living | External-reference sub-agent definition |
| skills/run-drydocs/SKILL.md | 2026-05-25 | 2026-07-22 | living | Pipeline run skill (oldest living skill) |
| skills/groom-backlog/SKILL.md | 2026-07-01 | 2026-07-20 | living | IDEAS → backlog.yaml grooming procedure |
| skills/add-source-object/SKILL.md | 2026-07-09 | 2026-07-10 | living | Onboard one object of an existing source |
| skills/verify/SKILL.md | 2026-07-09 | 2026-07-09 | living | Runtime verification recipes |
| skills/reconcile-port/SKILL.md | 2026-06-18 | 2026-07-21 | living | Cross-repo port reconciliation procedure |
| skills/transcribe-doc-markup/SKILL.md | 2026-07-08 | 2026-07-08 | living | Paper-HITL scan → anchor-keyed feedback (L6) |
| skills/setup-cowork/SKILL.md | 2026-06-18 | 2026-06-18 | living | Cowork surface setup |
| skills/\* (22 generic toolkit skills: analyze, debug, code-review, documentation, …) | 2026-06-18 | 2026-06-18 | corpus | Stock task-methodology skills (installed set, not project-authored) |
| skills/controlm-db/\* (5 files) | 2026-07-04 | 2026-07-15 | living | Generic Control-M DB query skill + references |
| skills/controlm-runbook-automation/\* (4 files) | 2026-07-04 | 2026-07-10 | living | Company-specific runbook-automation skill + references |
| skills/oracle-db/\* (164 files) | 2026-06-30 | 2026-06-30 | corpus | Vendor-distilled Oracle reference corpus (admin, appdev, containers, migrations, ords, plsql, sqlcl, …) |
| skills/data-context-extractor/\* (7 files) | 2026-06-18 | 2026-07-05 | corpus | Data-context extraction skill + references |
| skills/skill-creator/\* (5), pptx (3), pdf (3), docx (1), xlsx (1) | 2026-06-18 | 2026-06-18 | corpus | Stock authoring/office skills |

---

**Totals:** 436 tracked `*.md` — ≈145 project-authored living docs, ≈60 records, 13 historical,
≈215 corpus/stock files, 13 UI-WIP.
