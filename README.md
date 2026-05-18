# DryDocs — M3 Part 1: Control-M Folders + Jobs

Loads BMC Control-M folder and job *definitions* from Oracle (`psgmgr.DEF_*`) into the graph. **Structural only** — phase 1 doesn't ingest execution history; that's phase 2 (P2-B per v3 §M).

This pack layers on top of M0 + M1. CLI is a strict superset.

## What this delivers

- **`controlm_folders.py`** — loads `psgmgr.CM_DEF_VTAB` (the `dtsremgr.DEF_TAB` passthrough). Creates `:JobFolder` nodes (with composite labels `:JobFolder:Collection` so the PROV anchor is visible at query time) and the `:ControlMServer` mesh (deduped on DATA_CENTER value, labeled `:ControlMServer:Platform`).
- **`controlm_jobs.py`** — loads `psgmgr.DEF_JOB`. Creates `:ControlMJob:Activity` nodes with composite NODE KEY `(job_id, version_serial)` so version history is non-destructive.
- **Pydantic row models** (`drydocs/models/controlm.py`) — `ControlMFolderRow` and `ControlMJobRow`, with tolerant coercers for empty/null fields and an `.active` derived property on folders.
- **SQL projections** (`drydocs/loaders/sql/controlm_folders.sql`, `controlm_jobs.sql`) — exactly the columns the row models expect, with `T.USER_DAILY IS NOT NULL` active filter.
- **Ontology supplement** (`drydocs/schema/m3_ontology_supplement.cypher`) — adds three local-namespace anchor terms (`:ControlMServer`, `:JobFolder`, `:ControlMJob`) and wires them via `:SUBCLASS_OF` to the PROV anchors M0 already seeded (`prov:Collection`, `prov:Activity`).
- **Concept-mapping doc** (`docs/m3_controlm_concept_mapping.md`) — local label ↔ ontology term table; the naming-gotcha callout (BMC "tables" are folders); what's out of scope for M3 part 1.
- **CLI additions** — `ingest-controlm`, `apply-m3-supplement`, `m3-verify`. Existing `load <name>` registry gains `controlm_folders` and `controlm_jobs`.
- **Sample CSVs** mirroring the SQL projection (`controlm_folders__sample.csv`, `controlm_jobs__sample.csv`) so the loaders are dry-runnable offline.
- **Unit tests** (no Neo4j needed) for the row models and Cypher templates.

## Drop-in mapping

```
drydocs_m3_folders_jobs/                  C:\coding\projects\DryDocs\
├── drydocs/
│   ├── models/
│   │   ├── controlm.py                   drydocs/models/controlm.py          (new)
│   │   └── __init__.py                   drydocs/models/__init__.py          (overwrites)
│   ├── loaders/
│   │   ├── controlm_folders.py           drydocs/loaders/controlm_folders.py (new)
│   │   ├── controlm_jobs.py              drydocs/loaders/controlm_jobs.py    (new)
│   │   ├── cypher/
│   │   │   ├── controlm_folders.cypher   drydocs/loaders/cypher/...          (new)
│   │   │   └── controlm_jobs.cypher      drydocs/loaders/cypher/...          (new)
│   │   └── sql/
│   │       ├── controlm_folders.sql      drydocs/loaders/sql/...             (new)
│   │       └── controlm_jobs.sql         drydocs/loaders/sql/...             (new)
│   ├── schema/
│   │   └── m3_ontology_supplement.cypher drydocs/schema/...                  (new)
│   └── cli.py                            drydocs/cli.py                      (overwrites M1)
├── data/samples/
│   ├── controlm_folders__sample.csv      data/samples/...                    (new)
│   └── controlm_jobs__sample.csv         data/samples/...                    (new)
├── tests/unit/
│   ├── test_controlm_models.py           tests/unit/...                      (new)
│   └── test_controlm_cypher.py           tests/unit/...                      (new)
└── docs/
    └── m3_controlm_concept_mapping.md    docs/...                            (new)
```

`cli.py` and `drydocs/models/__init__.py` overwrite the M1 versions — strict supersets, every prior command still works.

## Run order

```powershell
# One-time after M0 bootstrap: add the Control-M anchor terms.
poetry run drydocs apply-m3-supplement

# Sample-mode: load folders + jobs from data/samples/
poetry run drydocs ingest-controlm

# Or: production mode against Oracle (uses the SQL projections in drydocs/loaders/sql/)
poetry run drydocs ingest-controlm --use-oracle

# Verify M3 part-1 invariants.
poetry run drydocs m3-verify
```

Expected output of `m3-verify` after loading the sample CSVs (8 folders, 15 jobs, 4 servers P12/P14/P32/P33):

```
                    M3 (part 1) invariants
+--------------------------------------------+-----+----------------------------+
| Check                                      | OK  | Detail                     |
+============================================+=====+============================+
| every folder has a server                  | yes | folders=8 srv_links=8      |
| every job has a folder                     | yes | jobs=15 with_folder=15     |
| no duplicate (job_id, version_serial)      | yes | dupes=0                    |
| ControlM SchedulerKind seeded              | yes | n=1                        |
| M3 local anchor terms seeded               | yes | n=3 (expect >= 3 ...)      |
| active folders contain at least one job    | yes | empty=0 total=7            |
+--------------------------------------------+-----+----------------------------+
```

(The retired folder `F00102 CCB_AUTO_RETIRED` lands as `active: false` and is excluded from the last check, which is why `total=7` rather than 8.)

## Loader semantics

**Composite key on `:ControlMJob`.** The NODE KEY constraint M0 seeded — `REQUIRE (j.job_id, j.version_serial) IS NODE KEY` — means a new `VERSION_SERIAL` for the same `job_id` creates a **new node**. History is non-destructive: the previous version is still queryable, marked with its old `last_seen_at`. Phase-2 execution history (`:JobRun {kind:'controlm_execution'}`) attaches to specific versions, not just to job_id.

**Folder containment uses `:CONTAINS_JOB`.** That's the local edge type. It plays the role of `prov:hadMember` against the `:JobFolder:Collection` anchor — the supplement records that mapping at the term level. We don't use `prov:hadMember` as the actual relationship type because the SCM cardinality and lifecycle semantics differ slightly from the canonical PROV definition.

**Server dedup is by `DATA_CENTER` value.** If two folders share `P12` they share one `:ControlMServer` node. The `:RUNS_ON` edge carries `since` (set on create) and `last_seen_at` (updated each refresh) so a folder migration (e.g., P12 → P32) is visible as a stale edge that needs review.

## Phase-2 swap

When the BMC ingest moves from samples to production:

```powershell
# Production cadence (daily):
poetry run drydocs ingest-controlm --use-oracle
```

The SQL files in `drydocs/loaders/sql/` are the source of truth — edit table/column names there if the corporate `psgmgr` schema diverges from the BMC canonical names. Row models, Cypher templates, and loaders don't change.

## What's NOT in this pack (M3 part 2)

- `:Condition` nodes (`psgmgr.CM_DEF_LNKI_P_VW` / `psgmgr.CM_DEF_LNKO_P_VW`). SQL projections already drafted in `drydocs/loaders/sql/controlm_conditions_in.sql` and `controlm_conditions_out.sql`. `ControlMConditionRow` is in `models/controlm.py`. Loader + Cypher: M3 part 2.
- `:EMITS_OUT_CONDITION` and `:REQUIRES_IN_CONDITION` edges: M3 part 2.
- Derived `:DEPENDS_ON` edges. SQL already drafted in the savepoint v2 loader pack at `drydocs_loaders/sql/controlm_dependencies_psgmgr.sql`; M3 part 2 wires it to a `controlm_dependencies_derived.py` loader that re-derives after every refresh.
- Folder → `:BatchProcessing` port linkage. Requires a folder-naming-convention resolver + reliable PAT data. Defer to M3 phase or M4.
- `:REQUIRES_SCHEDULER → :SchedulerKind {name:"ControlM"}` edges on `:Application`. Post-load step after folder → application mapping exists.

## What's NOT in phase 1 at all (phase 2 / 3)

- Per-execution `:JobRun {kind:'controlm_execution'}` history with `start_time`, `end_time`, `duration_sec` (P2-B).
- Rolled-up datetime metrics on `:ControlMJob` (`avg_start_time`, `avg_end_time`, `avg_duration_sec`).
- OpenLineage event ingestion (P2-C, conditional).

## Tests

```powershell
poetry run pytest tests/unit/ -v
```

Coverage:

- `test_controlm_models.py` — folder + job pydantic validation, optional-field handling, composite-key constraints, empty-value coercion.
- `test_controlm_cypher.py` — every template uses `UNWIND $batch AS row`, MERGE-based idempotency, composite NODE KEY pattern on `:ControlMJob`, `:JobFolder:Collection` and `:ControlMServer:Platform` label composition, supplement wires correctly to PROV anchors.

Integration tests (testcontainers-neo4j) land alongside the §F.4 support-team derivation in M2 → M3 part 2 once the full Application → BatchProcessing → JobFolder → ControlMJob path exists.

## Next step

1. Run `apply-m3-supplement` then `ingest-controlm` against the bundled samples; confirm `m3-verify` passes.
2. Confirm the exact `psgmgr.CM_DEF_VTAB` and `psgmgr.CM_DEF_VJOB` column names with the BMC DBA (uploads of `CM_DEF_VJOB.sql` and `CM_DEF_VTAB.sql` came through empty — confirm by inline paste or DDL query); adjust `drydocs/loaders/sql/controlm_*.sql` if anything differs.
3. Switch to `--use-oracle` against a non-prod psgmgr replica; re-run `m3-verify`.
4. M3 part 2 begins with conditions in/out (`psgmgr.CM_DEF_LNKI_P_VW` / `CM_DEF_LNKO_P_VW`) and the derived `:DEPENDS_ON` materialization. Recursive-predecessor SQL needs re-upload (the existing file is 0 bytes).
