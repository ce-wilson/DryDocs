# internal-standards/

**Corpus: INTERNAL** — company-specific configurations, standards, and conventions.

This is the **conformance** corpus, kept deliberately separate from `vendor-bmc/` (the **capability** corpus). Vendor docs answer *"is this legal/possible in Control-M?"*; these docs answer *"is this how we do it / are allowed to do it here?"* A validation skill runs both stages — vendor legality, then internal conformance — so the two must not be merged into one undifferentiated set.

See project memory `project-drydocs-scrape-two-corpus` for the architecture, trust-tier, and graph-ingestion rationale. Longer term, the `drydocs-scrape` build (Confluence ingestion) feeds this corpus; manually-captured SME standards live here too.

**Trust tier:** internal / mutable / may be stale or SME-asserted — lower authority than vendor capability statements, but authoritative for *our* standards. Tag provenance accordingly on graph load.

## Contents

- [folder-naming-convention.md](folder-naming-convention.md) — PRAOCG 6-char folder naming standard (environment · LOB · app code · folder-type/frequency).
- [data-center-naming-convention.md](data-center-naming-convention.md) — DC name encodes the **default execution time** when a folder declares none (e.g. `P032-E0700-DMA` = Production DC 032, 7:00 AM EST). All times EST.
- [description-field-metadata-plan.md](description-field-metadata-plan.md) — 🔵 **PLANNED**: repurpose the 4000-char Description field as pipe-delimited key:value metadata for graph relationships (datasetSeriesName, SLA, ROUTE_ID, SourceSnowQueue, SEAL…); 3-phase variable modernization (template → validate → ontology-driven modernize) with prod support + agents.
- [calendar-resolution-projection-plan.md](calendar-resolution-projection-plan.md) — 🔵 **PLANNED**: resolve calendar/RBC definitions to project when jobs will run (reproduce Control-M forecast); 4-phase (acquire → date-set resolver → time projection → validate); scheduling-plane exact, prerequisite-plane out of scope.
