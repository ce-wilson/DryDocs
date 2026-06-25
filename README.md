@claude - https://console.neo4j.io/projects/8992a0b9-2827-537f-b362-3821da9505e9/home

# DryDocs

**Production-support inventory + data-product knowledge graph for D&A (Data & Analytics) batches.**

DryDocs ingests batch-scheduling and ownership metadata from several systems into a
single Neo4j knowledge graph governed by a PROV-style ontology, so that "what runs,
what it depends on, who owns it, and which application it belongs to" can be answered
in one place. It is a Python CLI (`poetry run drydocs …`) on top of pydantic-validated
loaders, with two source adapters: bundled CSV samples for dev, and the Oracle
`psgmgr` views (the replicated BMC Control-M schema) for production.

The graph spans four domains, loaded by independent command chains:

| Domain | Source | What it adds | Status |
| --- | --- | --- | --- |
| **Control-M structural lineage** | Oracle `psgmgr.*` (BMC Control-M) | `:JobFolder`, `:ControlMServer`, `:ControlMJob`, `:Condition`, derived `:DEPENDS_ON` | Live (see below) |
| **SEAL applications** | Internal SEAL extract | `:Application` (two-port: `:EventProcessing` / `:BatchProcessing`), `:Port`, `:Membership`, `:Role`, `:Employee` | Live |
| **Catalog / PAT** | Internal product catalog | `:CatalogLOB`, `:BusinessSegment`, `:ProductLine`, `:Product`, `:AreaProduct`, `:DevTeam` + team-alignment edges | Live |
| **Control-M variable normalization (C3/C4)** | Oracle `psgmgr` variable extract | Variable taxonomy → resolver → command parser → Oracle `DRYDOCS_STG` staging | Staging only — graph load (Phase D) not started |

> Earlier milestone READMEs (M0 bootstrap, M1 reference refresh, M3 Control-M lineage)
> are frozen under [`docs/history/`](docs/history/README.md). This file is the
> authoritative current view across all of them.

## Requirements

- Python `^3.11` and [Poetry](https://python-poetry.org/)
- Neo4j `5.x` with **APOC** installed (the loaders use `apoc.cypher.runMany` for
  multi-statement templates; `drydocs check` verifies availability)
- For production ingest: Oracle access to the `psgmgr` views (via `python-oracledb`)

## Install & configure

```powershell
poetry install
Copy-Item .env.example .env   # then edit: NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD
                              # (+ ORACLE_* only when using --use-oracle)
```

## Quick start (bootstrap + sample ingest)

Everything below runs against the package-bundled CSV samples — no Oracle needed.

```powershell
# 1. Connectivity + APOC check
poetry run drydocs check

# 2. Schema backbone (constraints + ontology), then the three domain supplements
poetry run drydocs bootstrap
poetry run drydocs apply-ontology-supplement   # Control-M anchor terms
poetry run drydocs apply-seal-supplement       # SEAL domain terms
poetry run drydocs apply-catalog-supplement    # Catalog/PAT terms + all Role seeds

# 3. Load sample data
poetry run drydocs refresh-reference           # catalog + SEAL + dev teams (M1 chain)
poetry run drydocs ingest-controlm             # Control-M folders → jobs → conditions → deps

# 4. Verify invariants
poetry run drydocs m1-verify
poetry run drydocs m3-verify
```

The supplement order matters — `catalog_ontology_supplement.cypher` owns all canonical
`:Role` seeds that the SEAL/PAT loaders MATCH at runtime. The authoritative bootstrap
order is: `constraints` → `ontology` → `ontology_supplement` → `seal_ontology_supplement`
→ `catalog_ontology_supplement` (the first two are applied by `bootstrap`).

## CLI reference

`poetry run drydocs <command>` (add `-v` for debug logging). Run `--help` on any command
for its options.

**Bootstrap & schema**
- `check` — verify Neo4j connectivity, server version, APOC.
- `bootstrap` — apply `constraints.cypher` + `ontology.cypher`.
- `apply-ontology-supplement` / `apply-seal-supplement` / `apply-catalog-supplement` — idempotent domain ontology supplements.
- `verify` — report ontology-term counts by source label.
- `reset --yes` — **destructive**: `DETACH DELETE` every node + relationship.

**Ingest**
- `refresh-reference` — weekly catalog + SEAL + dev-teams chain (+ snapshots).
- `ingest-controlm` — Control-M chain (folders → jobs → conditions in/out → derived deps). `--skip-part2` stops after folders+jobs.
- `load <name> --csv FILE | --sql STMT` — run a single registered loader.

**Control-M variable normalization (no Neo4j needed)**
- `analyze-variables [--resolve]` — variable-taxonomy coverage report.
- `normalize-variables --out-dir DIR` — classify + resolve and emit the 8 `STG_*` staging CSVs.

**Verify & ops**
- `m1-verify` / `m3-verify` — assert domain invariants on the populated graph.
- `snapshot` / `prune-snapshots --years N` — (re)compute / prune entity snapshots.

Every command that runs an Oracle extract accepts `--use-oracle` plus the scope binds
`--folder` (folder-name LIKE pattern), `--run-as` (tenant FID/service user — `J.OWNER`),
`--developer-sid` (human author/changer), and `--row-cap` (ROWNUM sample cap). A `None`
bind = no filter on that dimension.

## Architecture

Every loader inherits `BaseLoader` and follows one lifecycle: **stream rows → pydantic
-validate → `UNWIND $batch` MERGE into a `.cypher` template → write a provenance
`:JobRun`**, at `batch_size=1000`, with MERGE keys backed by constraints. Source is
abstracted by adapters — `CsvAdapter` (samples) and `OracleAdapter` (psgmgr) — so the
same loader runs in dev and production.

```
drydocs/                # Python package
  adapters/             #   CsvAdapter (samples) + OracleAdapter (psgmgr)
  controlm/             #   Control-M variable taxonomy / resolver / command parser (C3/C4)
  loaders/              #   one loader per source, with cypher/ and sql/ siblings
    cypher/             #     UNWIND $batch MERGE templates
    sql/                #     Oracle extract queries + ddl/ staging schema
  models/               #   pydantic row models (controlm / seal / catalog)
  schema/               #   constraints + ontology (.cypher)
  snapshots/            #   snapshot writer
  data/samples/         #   bundled CSV fixtures (git-ignored; CLI default source)
docs/                   # process + product docs (history, reviews, Product, flows, restructure)
knowledge/              # DryDocs-owned, graph-defining design prose (ontology, naming standards)
reference/              # Tier-1 external: platforms (Neo4j, Oracle) + ontology standards + research
external/orchestration/ # Tier-2 external: orchestrators we ingest from (BMC baseline, AutoSys, Airflow)
config/                 # the configuration layer: precedence, source registry, taxonomy→ontology map
internal/               # CONFIDENTIAL internal data (stripped on publish)
scripts/                # thin shell wrappers around the CLI chain
tests/unit/             # pytest suite
```

The external/internal split is now three-tier (see [`CLAUDE.md`](CLAUDE.md) §2–3 and
[`docs/restructure/00-conceptual-model.md`](docs/restructure/00-conceptual-model.md)):
**`reference/`** = platforms/standards you build *with*; **`external/orchestration/`** =
vendors you ingest *from* (BMC is the baseline); **`knowledge/`** = internal graph-defining
prose; **`internal/`** = confidential data. The legacy `vendor/bmc-controlm/` now lives at
`external/orchestration/bmc-controlm/`. See [`knowledge/ARCHITECTURE.md`](knowledge/ARCHITECTURE.md)
for the original two-bucket rationale this extends.

---

## Control-M structural lineage

Loads BMC Control-M folder, job, and condition definitions and the derived `:DEPENDS_ON`
dependency graph from Oracle (`psgmgr.*`). **Structural only** — this pass does not ingest
execution history.

### What it delivers

**Folders + jobs**
- **`controlm_folders.py`** — loads `psgmgr.CM_DEF_VTAB` (replicated copy of `dtsremgr.DEF_VTAB`). Creates `:JobFolder:Collection` nodes (folder name = `SCHED_TABLE`) and the `:ControlMServer:Platform` mesh (deduped on `DATA_CENTER`).
- **`controlm_jobs.py`** — loads `psgmgr.CM_DEF_VJOB`. Creates `:ControlMJob:Activity` nodes keyed `(folder_id, job_id)`. Captures the business-app name (`APPLICATION` column) for later reconciliation to `:Application.seal_id`.

**Conditions + derived dependencies**
- **`controlm_conditions_in.py`** — loads `psgmgr.CM_DEF_LNKI_P_VW`. Creates `:Condition:Entity` nodes (key `(folder_id, name)`) and `:REQUIRES_IN_CONDITION` edges with boolean-expression metadata (`AND_OR`, `PARENTHESES`, `ORDER_`).
- **`controlm_conditions_out.py`** — loads `psgmgr.CM_DEF_LNKO_P_VW`. Reuses the same `:Condition` nodes; creates `:EMITS_OUT_CONDITION` edges with the `SIGN` operator (`+`/`-`).
- **`controlm_dependencies_derived.py`** — materializes `:DEPENDS_ON` edges from the recursive predecessor SQL. Each edge carries `via_condition`, `recursion_level`, and `dependency_path`. Cycle-safe by construction (path-`INSTR` guard in the SQL).
- **`controlm_dependencies_recursive.sql`** — the canonical Oracle recursive CTE. Walks backwards from a successor through condition matching; cyclic-type matching intentionally disabled; recursion cap of 10 with full-path cycle detection.

### File map

Where the structural-lineage files live (`C:\coding\projects\sandbox\DryDocs\`):

```
DryDocs/
├── drydocs/
│   ├── models/
│   │   └── controlm.py                              row models (folders / jobs / cond-in / cond-out / deps)
│   ├── loaders/
│   │   ├── controlm_folders.py
│   │   ├── controlm_jobs.py
│   │   ├── controlm_conditions_in.py
│   │   ├── controlm_conditions_out.py
│   │   ├── controlm_dependencies_derived.py
│   │   ├── cypher/
│   │   │   ├── controlm_folders.cypher
│   │   │   ├── controlm_jobs.cypher
│   │   │   ├── controlm_conditions_in.cypher
│   │   │   ├── controlm_conditions_out.cypher
│   │   │   └── controlm_dependencies_derived.cypher
│   │   └── sql/
│   │       ├── controlm_folders.sql
│   │       ├── controlm_jobs.sql
│   │       ├── controlm_conditions_in.sql
│   │       ├── controlm_conditions_out.sql
│   │       └── controlm_dependencies_recursive.sql
│   ├── schema/
│   │   └── ontology_supplement.cypher               Control-M anchor terms live in the shared base supplement
│   └── cli.py                                       registers ingest-controlm + m3-verify
├── drydocs/data/samples/
│   ├── controlm_folders__sample.csv
│   ├── controlm_jobs__sample.csv
│   ├── controlm_conditions_in__sample.csv
│   ├── controlm_conditions_out__sample.csv
│   └── controlm_dependencies__sample.csv
├── tests/unit/
│   ├── test_controlm_models.py
│   └── test_controlm_cypher.py
└── docs/
    └── controlm-loader-flow.md
```

### Run order

```powershell
# Sample-mode: full chain (folders → jobs → conditions in/out → deps).
poetry run drydocs ingest-controlm

# Production against Oracle psgmgr views, scoped to one product line.
poetry run drydocs ingest-controlm --use-oracle --folder "CCB_AUTO_%"

# Verify invariants.
poetry run drydocs m3-verify
```

Expected `m3-verify` output after the sample chain. **Reconciled 2026-06-20 to the bundled
sample:** 8 folders, **13 jobs**, **15 conditions** (7 distinct names), **10 derived dependency
edges**. The bundled sample is a *reduced* fixture — 2 active folders (`161020`, `160501`) carry
no jobs, so the "active folders contain at least one job" invariant reports `empty=2`. That is a
known sample gap (folders included without their jobs); close it by regenerating the sample from
`psgmgr`. (Earlier docs said 15 jobs / 5 conditions / 13 deps — that was a different, larger
fixture.)

```
                          M3 (part 1 + part 2) invariants
+--------------------------------------------------+-----+---------------------------------+
| Check                                            | OK  | Detail                          |
+==================================================+=====+=================================+
| every folder has a server                        | yes | folders=8 srv_links=8           |
| every job has a folder                            | yes | jobs=13 with_folder=13          |
| no duplicate (folder_id, job_id)                 | yes | dupes=0                         |
| ControlM SchedulerKind seeded                     | yes | n=1                             |
| M3 local anchor terms seeded                      | yes | n=3 (expect >= 3 ...)           |
| active folders contain at least one job          | no* | empty=2 total=7 (sample gap)    |
| no orphan conditions                              | yes | orphan=0 total=15               |
| DEPENDS_ON edges have recursion_level + path     | yes | total=10 missing_level=0 ...    |
+--------------------------------------------------+-----+---------------------------------+
```

> *`empty=2` is the known bundled-sample gap noted above: folders `161020` and `160501` are
> active but jobless in the fixture. Regenerate the sample from `psgmgr` to restore `empty=0`.

### Schema notes worth knowing

Three things in the real schema that didn't match the BMC canonical references:

1. **Folder name lives in `SCHED_TABLE`**, not `PARENT_TABLE`. `PARENT_TABLE` is on the job side as a denormalized FK to the folder's `SCHED_TABLE` value. The folder loader uses `SCHED_TABLE`; the job loader keeps `PARENT_TABLE` as a property for query convenience.
2. **Folders are not versioned.** `CM_DEF_VTAB` has no `IS_CURRENT_VERSION` or `VERSION_SERIAL`. Only `USER_DAILY IS NOT NULL` filters active folders.
3. **LNKI and LNKO have different schemas.** LNKI has `AND_OR` / `PARENTHESES` / `ORDER_` for the boolean-expression tree; LNKO has `SIGN` (`+`/`-`). Distinct row models — but both write to the same `:Condition` node when `(folder_id, name)` matches.

### Cyclic-type handling

The canonical recursive SQL **intentionally disables** cyclic-type matching
(`-- AND J_SUB.JOB_CYCLIC_IN = D_SUB.JOB_CYCLIC_OUT`). The commented line is preserved in
`controlm_dependencies_recursive.sql` so the design intent travels with the code.
Cross-cyclic-type dependencies are real (e.g., a 15-minute cyclic FW job feeds a daily
ETL job), and cycle-safety comes from the `INSTR(dependency_path, ...)` guard, not from
cyclic-type filtering.

The SQL files in `drydocs/loaders/sql/` are the source of truth — edit there if the
corporate `psgmgr` schema diverges from the locked DDL. Row models, Cypher templates,
and loaders don't change.

### Not yet wired

- Per-execution `:JobRun {kind:'controlm_execution'}` history with `start_time` / `end_time` / `duration_sec`, and rolled-up datetime metrics on `:ControlMJob`.
- Folder → `:BatchProcessing` linkage (needs a folder-naming resolver + reliable PAT data).
- `:REQUIRES_SCHEDULER → :SchedulerKind {name:"ControlM"}` edges on `:Application` (post-load step).
- Graph load of the variable/command normalization output (Phase D — see below).

---

## Control-M variable normalization (C3/C4)

A separate workstream that extracts the *technical* objects one level below job-to-job
lineage — variable definitions, ETL launches (Ab Initio / Informatica / PySpark), file
operations, and notifications — from Control-M job definitions.

Architecture: **SQL extract → Python normalize → Oracle staging (`DRYDOCS_STG`, QA in
SQL Developer) → Neo4j under PROV `:JobRun`.** Variable resolution and command parsing
happen in Python, not recursive SQL. Phases A (taxonomy), B (offline AutoEdit resolver),
and C (command/launcher parser) are complete; the graph load (Phase D) is not started.

```powershell
# Coverage report (classify + optionally resolve), no database needed.
poetry run drydocs analyze-variables --resolve

# Emit the 8 STG_* staging CSVs for load into DRYDOCS_STG.
poetry run drydocs normalize-variables --out-dir stg_out
```

Lives in `drydocs/controlm/` (`variables.py`, `resolver.py`, `commands.py`, `paths.py`,
`facts.py`, `staging.py`, `variable_report.py`); staging DDL in
`drydocs/loaders/sql/ddl/`. Full status + runbook:
[`docs/controlm-c3-normalization-status.md`](docs/controlm-c3-normalization-status.md).

## Tests

```powershell
poetry run pytest tests/unit/ -v
```

Coverage highlights:
- `test_controlm_models.py` / `test_controlm_cypher.py` — structural-lineage row models and Cypher (idempotent `UNWIND $batch` + MERGE; `SCHED_TABLE` on the folder side; shared `:Condition` key; recursive SQL cycle guard).
- `test_variable_classifier.py` / `test_variable_resolver.py` / `test_variable_staging.py` / `test_command_parser.py` — the C3/C4 normalization stream. A few sample-backed tests skip when the production CSV is absent.
- `test_schema.py`, `test_namespaces.py`, `test_folder_name_parser.py`, `test_base_loader_smoke.py` — schema/ontology and loader-core guards.

## Further reading

- [`knowledge/ARCHITECTURE.md`](knowledge/ARCHITECTURE.md) — repo organization + tuning plan.
- [`docs/controlm-loader-flow.md`](docs/controlm-loader-flow.md) — Control-M loader walkthrough.
- [`docs/NODE_QUICK_REFERENCE.md`](docs/NODE_QUICK_REFERENCE.md) / [`docs/RELATIONSHIP_GUIDE.md`](docs/RELATIONSHIP_GUIDE.md) — node + relationship catalog.
- [`docs/history/`](docs/history/README.md) — frozen M0 / M1 / planning milestone docs.
