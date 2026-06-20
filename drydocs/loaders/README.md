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
- SQL extracts live in `sql/` (Oracle); reference docs in `../../vendor/bmc-controlm/`.

## Internally-sourced
- SEAL: `seal_applications` · `seal_contacts`
- Catalog/PAT: `catalog` · `business_segments` · `products` · `product_lines` ·
  `dev_teams` · `area_products` · `pat_*`

## Shared
- `base.py` — the loader lifecycle
- `cypher/` — `UNWIND $batch` MERGE templates (one per loader)
- `sql/` — Oracle extract queries + staging DDL (vendor source)
