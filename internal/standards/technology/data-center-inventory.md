# Internal — Control-M data-center inventory (REAL values)

**classification: Internal** — excluded from any public push per `PUBLISH-BOUNDARY.md`.

Home for the real values that the publishable
`knowledge/standards/technology/data-center-naming-convention.md` no longer carries.
Created 2026-08-11 at the J13 class-2 ruling.

## The environment-letter swap (SME ruling 2026-08-11)

The publishable page presents every data-center name and application code with a **`T`**
in position 1. The real inventory is **production — position 1 is `P`**. The SME ruled
that the publishable copy swaps that one character so no published example names a live
production object, while the grammar the page exists to teach (position 1 = environment,
`E####` = default time) stays exactly true.

| Publishable | Real |
|---|---|
| `T012-E0700-IB` | `P012-E0700-IB` |
| `T014-E0700-ANY` | `P014-E0700-ANY` |
| `T021-E0800-ANY` | `P021-E0800-ANY` |
| `T032-E0700-DMA` | `P032-E0700-DMA` |
| `TRICD` (application code) | `PRICD` |
| `TDCLD0003_…` (job name) | `PDCLD0003_…` |

The swap is mechanical and reversible: `P0NN` -> `T0NN` in position 1 only. Suffixes
(`IB` / `ANY` / `DMA`) and the `E####` time segment are unchanged — they carry no
production identity on their own.

## Per-data-center volumetrics (capture 2026-06)

Removed from `drydocs/loaders/sql/ddl/controlm_staging_ddl.sql` at the same pass. The
totals stay published because the sizing rationale rests on them; the per-DC split is an
estate map and does not.

| Data center | Folders | Jobs |
|---|---|---|
| `P012-E0700-IB` | 2,230 | 42,688 |
| `P014-E0700-ANY` | 4,188 | 52,976 |
| `P021-E0800-ANY` | 7,914 | 59,712 |
| `P032-E0700-DMA` | 4,441 | 85,202 |
| **Total** | **~18,800** | **~240,600** |

Volumetrics are a DISTINCT value class from identifiers and were NOT part of the SME's
class-2 ruling. They were pulled because the identifier swap had left real production
counts sitting under test-environment labels — wrong as well as disclosed. If the SME
rules volumetrics publishable, restore the split to the DDL header.

## Extraction scope (user direction, 2026-08-24)

The Control-M extracts are to be **filtered and run individually, one data center at a
time**, over these three:

| Data center | Folders | Jobs |
|---|---|---|
| `P012-E0700-IB` | 2,230 | 42,688 |
| `P014-E0700-ANY` | 4,188 | 52,976 |
| `P032-E0700-DMA` | 4,441 | 85,202 |

**`P021-E0800-ANY` is NOT in that list** — and it is the largest of the four by folder
count (7,914 folders / 59,712 jobs). Whether that is a deliberate scope cut or an
omission is the user's call, not an inference to make here; it is raised as the open
question on `Idea-169`.

This is an EXTRACTION-SCOPE direction, not the DC scope call. The
`controlm-hosts-topology` residual ("load all 22 data centers or production-only") is
still open and still the SME's — three production DCs to pull first says nothing about
what the graph should ultimately hold.

No data-center bind exists on any extract today (`:folder_filter` / `:run_as` /
`:developer_sid` / `:row_cap` are the whole scope surface), so this requires a build.

## Open, still

Environments beyond production: the CM_HOSTS profile found **22 distinct DATA_CENTER
values** against the 4 known production DCs, so non-production prefixes exist and are not
enumerated. Until they are, `T` is an ASSERTION that the published examples are
non-production, not a verified environment code from the real estate.
