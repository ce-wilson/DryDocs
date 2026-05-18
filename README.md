# DryDocs — M3: Control-M Structural Lineage

Loads BMC Control-M folder, job, condition definitions and the derived `:DEPENDS_ON` dependency graph from Oracle (`psgmgr.*`). **Structural only** — phase 1 doesn't ingest execution history; that's phase 2 (P2-B per v3 §M).

This pack layers on top of M0 + M1. CLI is a strict superset.

## What this delivers

### M3 part 1 — folders + jobs

- **`controlm_folders.py`** — loads `psgmgr.CM_DEF_VTAB` (replicated copy of `dtsremgr.DEF_VTAB`). Creates `:JobFolder:Collection` nodes (folder name = `SCHED_TABLE`) and the `:ControlMServer:Platform` mesh (deduped on `DATA_CENTER`).
- **`controlm_jobs.py`** — loads `psgmgr.CM_DEF_VJOB`. Creates `:ControlMJob:Activity` nodes with composite NODE KEY `(job_id, version_serial)`. Captures the business-app name (`APPLICATION` column) for later reconciliation to `:Application.seal_id`.

### M3 part 2 — conditions + derived dependencies

- **`controlm_conditions_in.py`** — loads `psgmgr.CM_DEF_LNKI_P_VW`. Creates `:Condition:Entity` nodes (composite key `(folder_id, name, version_serial)`) and `:REQUIRES_IN_CONDITION` edges with the boolean-expression metadata (`AND_OR`, `PARENTHESES`, `ORDER_`).
- **`controlm_conditions_out.py`** — loads `psgmgr.CM_DEF_LNKO_P_VW`. Reuses the same `:Condition` nodes; creates `:EMITS_OUT_CONDITION` edges with the `SIGN` operator (`+`/`-`).
- **`controlm_dependencies_derived.py`** — materializes `:DEPENDS_ON` edges from the recursive predecessor SQL. Each edge carries `via_condition`, `recursion_level`, and `dependency_path`. Cycle-safe by construction (path-INSTR guard in the SQL).
- **`controlm_dependencies_recursive.sql`** — the canonical Oracle recursive CTE. Walks backwards from a successor through condition matching; cyclic-type matching intentionally disabled; recursion cap of 10 with full-path cycle detection.

### Support files

- Pydantic row models in `drydocs/models/controlm.py` — five distinct models matching the five source schemas.
- Five SQL projections in `drydocs/loaders/sql/` — one per source view, locked to real columns from the uploaded DDL.
- Five Cypher templates in `drydocs/loaders/cypher/`.
- Sample CSVs in `data/samples/` exercising the full chain end-to-end (8 folders, 15 jobs, 8 in-conditions, 8 out-conditions, 13 derived dependencies).
- Ontology supplement at `drydocs/schema/m3_ontology_supplement.cypher`.
- Concept-mapping doc at `docs/m3_controlm_concept_mapping.md`.

## Drop-in mapping

```
drydocs_m3_folders_jobs/                                C:\coding\projects\DryDocs\
├── drydocs/
│   ├── models/
│   │   ├── controlm.py                                 drydocs/models/controlm.py        (new)
│   │   └── __init__.py                                 drydocs/models/__init__.py        (overwrites)
│   ├── loaders/
│   │   ├── controlm_folders.py                         drydocs/loaders/controlm_folders.py            (new)
│   │   ├── controlm_jobs.py                            drydocs/loaders/controlm_jobs.py               (new)
│   │   ├── controlm_conditions_in.py                   drydocs/loaders/controlm_conditions_in.py      (new)
│   │   ├── controlm_conditions_out.py                  drydocs/loaders/controlm_conditions_out.py     (new)
│   │   ├── controlm_dependencies_derived.py            drydocs/loaders/controlm_dependencies_derived.py (new)
│   │   ├── cypher/
│   │   │   ├── controlm_folders.cypher                 drydocs/loaders/cypher/...        (new)
│   │   │   ├── controlm_jobs.cypher                    drydocs/loaders/cypher/...        (new)
│   │   │   ├── controlm_conditions_in.cypher           drydocs/loaders/cypher/...        (new)
│   │   │   ├── controlm_conditions_out.cypher          drydocs/loaders/cypher/...        (new)
│   │   │   └── controlm_dependencies_derived.cypher    drydocs/loaders/cypher/...        (new)
│   │   └── sql/
│   │       ├── controlm_folders.sql                    drydocs/loaders/sql/...           (new)
│   │       ├── controlm_jobs.sql                       drydocs/loaders/sql/...           (new)
│   │       ├── controlm_conditions_in.sql              drydocs/loaders/sql/...           (new)
│   │       ├── controlm_conditions_out.sql             drydocs/loaders/sql/...           (new)
│   │       └── controlm_dependencies_recursive.sql     drydocs/loaders/sql/...           (new)
│   ├── schema/
│   │   └── m3_ontology_supplement.cypher               drydocs/schema/...                (new)
│   └── cli.py                                          drydocs/cli.py                    (overwrites M1)
├── data/samples/
│   ├── controlm_folders__sample.csv                    data/samples/...                  (new)
│   ├── controlm_jobs__sample.csv                       data/samples/...                  (new)
│   ├── controlm_conditions_in__sample.csv              data/samples/...                  (new)
│   ├── controlm_conditions_out__sample.csv             data/samples/...                  (new)
│   └── controlm_dependencies__sample.csv               data/samples/...                  (new)
├── tests/unit/
│   ├── test_controlm_models.py                         tests/unit/...                    (overwrites)
│   └── test_controlm_cypher.py                         tests/unit/...                    (overwrites)
└── docs/
    └── m3_controlm_concept_mapping.md                  docs/...                          (new)
```

## Run order

```powershell
# One-time: add the Control-M anchor terms to the ontology backbone.
poetry run drydocs apply-m3-supplement

# Sample-mode: full M3 chain (folders -> jobs -> conditions in/out -> deps).
poetry run drydocs ingest-controlm

# Production mode against Oracle psgmgr views.
poetry run drydocs ingest-controlm --use-oracle --folder-filter "CCB_AUTO_%"

# Verify M3 invariants.
poetry run drydocs m3-verify
```

Expected output of `m3-verify` after the sample chain (8 folders, 15 jobs, 5 conditions distinct, 13 derived dependency edges):

```
                          M3 (part 1 + part 2) invariants
+--------------------------------------------------+-----+---------------------------------+
| Check                                            | OK  | Detail                          |
+==================================================+=====+=================================+
| every folder has a server                        | yes | folders=8 srv_links=8           |
| every job has a folder                           | yes | jobs=15 with_folder=15          |
| no duplicate (job_id, version_serial)            | yes | dupes=0                         |
| ControlM SchedulerKind seeded                    | yes | n=1                             |
| M3 local anchor terms seeded                     | yes | n=3 (expect >= 3 ...)           |
| active folders contain at least one job          | yes | empty=0 total=7                 |
| no orphan conditions                             | yes | orphan=0 total=5                |
| DEPENDS_ON edges have recursion_level + path     | yes | total=13 missing_level=0 ...    |
+--------------------------------------------------+-----+---------------------------------+
```

## Schema notes worth knowing

Three things in the real schema that didn't match the BMC canonical references:

1. **Folder name lives in `SCHED_TABLE`**, not `PARENT_TABLE`. `PARENT_TABLE` is on the job side as a denormalized FK to the folder's `SCHED_TABLE` value. The folder loader uses `SCHED_TABLE`; the job loader keeps `PARENT_TABLE` as a property for query convenience.

2. **Folders are not versioned.** `CM_DEF_VTAB` has no `IS_CURRENT_VERSION` or `VERSION_SERIAL`. Only `USER_DAILY IS NOT NULL` filters active folders.

3. **LNKI and LNKO have different schemas.** LNKI has `AND_OR` / `PARENTHESES` / `ORDER_` for the boolean-expression tree. LNKO has `SIGN` (`+`/`-`). Distinct row models — they can't share one — but both write to the same `:Condition` node when `(folder_id, name, version_serial)` matches.

## Cyclic-type handling

The canonical recursive SQL **intentionally disables** cyclic-type matching (`-- AND J_SUB.JOB_CYCLIC_IN = D_SUB.JOB_CYCLIC_OUT`). The commented line is preserved in `controlm_dependencies_recursive.sql` so the design intent travels with the code. Cross-cyclic-type dependencies are real (e.g., a 15-minute cyclic FW job feeds a daily ETL job), and the cycle-safety comes from the `INSTR(dependency_path, ...)` guard, not from cyclic-type filtering.

## Phase-2 swap

When the BMC ingest moves from samples to production:

```powershell
poetry run drydocs ingest-controlm --use-oracle --folder-filter "%"
```

For a focused refresh of just one product line:

```powershell
poetry run drydocs ingest-controlm --use-oracle --folder-filter "CCB_HL_%"
```

The SQL files in `drydocs/loaders/sql/` are the source of truth — edit there if the corporate `psgmgr` schema diverges from the DDL we locked. Row models, Cypher templates, and loaders don't change.

## What's NOT in this pack

- Per-execution `:JobRun {kind:'controlm_execution'}` history with `start_time` / `end_time` / `duration_sec` (P2-B).
- Rolled-up datetime metrics on `:ControlMJob` (`avg_start_time`, `avg_end_time`, `avg_duration_sec`).
- Folder → `:BatchProcessing` linkage. Requires a folder-naming-convention resolver + reliable PAT data.
- `:REQUIRES_SCHEDULER → :SchedulerKind {name:"ControlM"}` edges on `:Application`. Post-load step.
- Quantitative-resource modeling (`CM_DEF_LNKI_Q_VW`). Out of scope.
- OpenLineage event ingestion (P2-C, conditional).

## Tests

```powershell
poetry run pytest tests/unit/ -v
```

Coverage:

- `test_controlm_models.py` — pydantic validation for all five row models; confirms `SCHED_TABLE` (not `PARENT_TABLE`) on the folder side; confirms LNKI has boolean-expression columns while LNKO has `SIGN`; confirms recursion_level >= 1 on dependency rows.
- `test_controlm_cypher.py` — every Cypher uses `UNWIND $batch AS row` + MERGE-based idempotency; folder Cypher uses `SCHED_TABLE`; conditions share composite key; derived deps carry `recursion_level` + `dependency_path`; recursive SQL has the cycle guard and recursion cap.

## Next step

1. Run `apply-m3-supplement` then `ingest-controlm` against the bundled samples; confirm `m3-verify` passes.
2. Run `ingest-controlm --use-oracle --folder-filter "<one folder>"` against a non-prod psgmgr replica; spot-check the derived `:DEPENDS_ON` edges against a known dependency tree.
3. Widen the folder filter incrementally; re-run `m3-verify` after each refresh.
4. Phase 2 (P2-B) wires up the per-execution `:JobRun` history for SLA tracking.
