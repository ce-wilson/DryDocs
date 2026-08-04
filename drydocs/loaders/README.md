# drydocs/loaders/ — ingestion by source

Every loader inherits `BaseLoader` (stream → pydantic-validate → `UNWIND $batch`
into a `.cypher` template → provenance `:JobRun`). Loaders are grouped here by
**where the data comes from** — vendor system vs internal system.

> A subpackage split (`controlm/`, `internal/seal/`, `internal/catalog/`) is
> planned but not yet executed — see `../../knowledge/ARCHITECTURE.md` §4a.
> Until then this table is the map.

## Vendor-sourced (BMC Control-M, via the Oracle `psgmgr` extract)
- `controlm_folders` · `controlm_jobs`
- `controlm_conditions_in` · `controlm_conditions_out`
- `controlm_dependencies_derived` · `controlm`
- SQL extracts live in `sql/` (Oracle; `sql/adhoc/` is the manual probe bench,
  deliberately OUTSIDE the ship path); reference docs in
  `../../external/orchestration/bmc-controlm/`.

## Internally-sourced
- SEAL: `seal_applications` · `seal_contacts` · `seal_attribution` (K2 —
  `WAS_ASSOCIATED_WITH` facts, gate-confirmed match policy)
- Catalog/PAT: `catalog` · `business_segments` (product/team classes live
  inside `catalog`)
- Registry/config: `software_registry` (ADR 0004) · `manual_loads` (tier-5
  SME CSVs, manifest-gated) · `batch_port_orchestrator` (C14 migration)

## Docs corpus (lexical graph)
- `bmc_docs` (Document→Chunk, gate `bmc-docs-lexical-load`) ·
  `essential_graphrag` (Q2 ebook load) · `doc_traceability` (L7 spine:
  DesignDoc/DocSection/Requirement/Component/TestCase/FeedbackNote)

## Shared
- `base.py` — the loader lifecycle (incl. index preflight)
- `cypher/` — `UNWIND $batch` MERGE templates (one per loader)
- `sql/` — Oracle extract queries + staging DDL (vendor source)

## The source audit envelope (doc 06)

Four frozen node properties — `source_created_by/_at`, `source_updated_by/_at` —
carry "who created / last changed this record IN THE SOURCE." A loader may SET
them **only** when its source's entry in `config/audit-fields.yaml` is
`status: confirmed` (gate-decided column→envelope mapping; `test_audit_fields.py`
enforces it). Today that is the two Control-M definition loaders (jobs = full
envelope, folders = updated-side only). Every other source is a **ruled stub** —
the Phase-4 gate (`audit-envelope-phase4`, 2026-08-04) recorded per-source WHY no
envelope applies (SEAL: lifecycle dates, not record audit; PAT reports: no audit
columns projected; repo-committed ledgers: git history is the envelope). Do not
invent an envelope mapping in Cypher — the entry's note names the revisit
trigger if one exists. Distinct from pull tracking (`first_seen_at`/
`last_seen_at`/`last_run_id`) and from `:JobRun` load provenance. The properties'
standard-term bindings (dct:) live in the vocabulary's `property_terms` section.
