# internal/server-inventory/ — the infrastructure server-export landing zone (Z1)

**Classification: Internal** (PUBLISH-BOUNDARY.md — this whole directory is excluded from
any public push). Real exports committed here carry real hostnames, racks, building
locations and owning-application identifiers; they are TRACKED in the private repo on
purpose — a tracked file survives every `git clean`, which is what makes an in-tree
landing zone legitimate (`acquisition.drop_dir_base: repo`; guard:
`tests/unit/test_landing_zones.py`).

Registry row: `infra:server-export` in [`config/source-registry.yaml`](../../config/source-registry.yaml).
Field contract + hierarchy capture: [`config/taxonomy/server-location.yaml`](../../config/taxonomy/server-location.yaml).

## Download procedure (mechanism only — the site name and URL stay company-side)

1. Open the infrastructure inventory site (the internal per-application server
   inventory UI; its address belongs in this file's company-side twin, never here).
2. Filter the application list on **prod**.
3. Download the server export **PER BUSINESS APPLICATION** — one file per application;
   that grain is the acquisition contract, so never merge downloads into one file.
4. Each download's rows carry **BOTH prod and DR servers** (the prod filter selects
   which applications are listed, not which of their servers appear).
5. Drop the file in this directory and commit it (private repo only). Record the pull
   date in the commit message.

## Standing caution (carried verbatim from the Epic Z groom)

> The export's data-center/location field is NOT the Control-M field of the same
> name — the Control-M "DC" is a SCHEDULING concept (its name encodes the default run
> time, e.g. T032-E0700-DMA), while this source carries PHYSICAL geography (rack,
> building, city/state/country). Never join or crosswalk the two by field name.

## What happens to the data

Nothing loads it yet: the dataset row ships `confirmed: false` and every edge meaning
(the Server node shape, the server↔Control-M-node join rule, geography grain, prod/DR
designation) is a Z2 gate decision. The Z3 loader activates only after that gate signs.
The publishable synthetic sample lives at
`tests/fixtures/server_inventory/synthetic-server-export.csv`.
