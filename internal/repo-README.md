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
| **Control-M structural lineage** | Oracle `psgmgr.*` (BMC Control-M) | `:ControlMFolder`, `:ControlMServer`, `:ControlMJob`, `:Condition`, derived `:WAS_INFORMED_BY` | Live (see below) |
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

### Editor line endings — install the EditorConfig extension

Per-machine setup, easy to miss because nothing fails loudly without it.
`.gitattributes` (`* text=auto eol=lf`) governs what git *checks out*; it does not
govern what an editor writes when it creates a file, and VS Code on Windows
defaults new files to CRLF. `.editorconfig` pins `end_of_line = lf` for every file
type, and VS Code honors it only with the **EditorConfig extension**
(`editorconfig.editorconfig`) installed — so install it on each machine.

Skipping it does not corrupt anything: the attributes rule normalizes on the way
into the index, so commits are LF regardless. What you get instead is CRLF churn in
the working tree, which is how `ruff format --check` came to report every file as
needing reformat purely on line endings (`docs/ruff-format-convergence.md`).

**Once per machine after an EOL policy change.** A plain `git pull` rewrites only
the files the incoming commits touched, so anything already checked out keeps its
old endings. On a **clean tree** (`git status` empty — `reset --hard` discards
uncommitted work):

```powershell
git rm --cached -r . -q
git reset --hard
```

Expect zero blob changes and a clean `git status` afterward — the index has always
held LF, so this only re-materializes the working tree. Verify with
`git ls-files --eol`, which should show no `w/crlf` or `w/mixed` rows. Blob changes
appearing here would mean something committed CRLF; investigate rather than commit.

## Quick start (bootstrap + sample ingest)

Everything below runs against the package-bundled CSV samples — no Oracle needed.

```powershell
# 1. Connectivity + APOC check
poetry run drydocs check

# 2. Schema backbone (constraints + ontology), then the whole supplement chain
poetry run drydocs bootstrap
poetry run drydocs bootstrap-schema-graph      # schema meta-graph → ddschema (its own database)
poetry run drydocs apply-supplements           # base → seal → catalog → registry, verified

# 3. Load sample data
poetry run drydocs refresh-reference           # catalog + SEAL + dev teams (M1 chain)
poetry run drydocs ingest-controlm             # Control-M folders → jobs → conditions → deps

# 3b. Demonstrable content — the document corpora. A FRESH OR REBUILT container
#     has none of these (they live only in the DB), so re-run this block after
#     any container re-bootstrap; the loaders are idempotent.
poetry run drydocs load-software-registry      # third-party software registry
poetry run drydocs load-bmc-docs               # BMC docs lexical graph (Document → Chunk)
poetry run drydocs load-doc-traceability       # L7 — DryDocs documenting itself
poetry run drydocs load-essential-graphrag     # optional: ebook corpus (→ ddcontext)

# 4. Verify invariants
poetry run drydocs m1-verify
poetry run drydocs m3-verify
```

The supplement order matters — `catalog_ontology_supplement.cypher` owns all canonical
`:Role` seeds that the SEAL/PAT loaders MATCH at runtime, and it reuses the
`:Attribution` class + `#hasAgent` term that the SEAL supplement declares. The
authoritative bootstrap order is: `constraints` → `ontology` → `ontology_supplement` →
`seal_ontology_supplement` → `catalog_ontology_supplement` → `registry_ontology_supplement`
(the first two are applied by `bootstrap`).

Since G29 that order is **data, not prose** — `drydocs_core/schema/supplements.py` holds
the one ordered registry and `apply-supplements` walks it, so the chain cannot be typed
out of order. Each file is applied and then *verified*: every `:OntologyTerm` IRI the
`.cypher` declares must be present in the graph afterwards, or the command exits 1. A
truncated or renamed supplement used to run "successfully" and seed nothing, surfacing
hundreds of rows later as a loader MATCH that quietly matched zero `:Role` nodes. The run
writes a `load.supplement.<stamp>.log` envelope to `DRYDOCS_LOGDIR`.

## CLI reference

`poetry run drydocs <command>` (add `-v` for debug logging). Run `--help` on any command
for its options.

**Bootstrap & schema**
- `check` — verify Neo4j connectivity, server version, APOC.
- `bootstrap` — apply `constraints.cypher` + `ontology.cypher`.
- `bootstrap-schema-graph` — render + apply the schema meta-graph to `ddschema` (C21/G51). Its own database: the exemplars carry a real label beside `:SchemaMeta`, which the `drydocs` NODE KEYs reject. Chain-independent of the supplements; belongs in cold start because a wiped DBMS is when it gets forgotten. `--database` overrides the target.
- `apply-supplements` — the ordered, verified supplement chain (base → seal → catalog → registry). `--only NAME` (repeatable) scopes it; `--with-sosa` appends the experimental SOSA/SSN terms. Idempotent.
- `apply-ontology-supplement` / `apply-seal-supplement` / `apply-catalog-supplement` / `apply-registry-supplement` / `apply-sosa-supplement` — the pre-G29 per-file verbs, kept as delegating aliases (they inherit the verification and the run log).
- `verify` — report ontology-term counts by source label.
- `reset --yes` — **destructive**: `DETACH DELETE` every node + relationship.

**Ingest**
- `refresh-reference` — weekly catalog + SEAL + dev-teams chain (+ snapshots).
- `ingest-controlm` — Control-M chain (folders → jobs → conditions in/out → derived deps). `--skip-part2` stops after folders+jobs.
- `load <name> --csv FILE | --sql STMT` — run a single registered loader.

**Control-M variable normalization (no Neo4j needed)**
- `analyze-variables [--resolve]` — variable-taxonomy coverage report.
- `normalize-variables --out-dir DIR` — classify + resolve and emit the 8 `STG_*` staging CSVs.

**Lineage (no Neo4j needed)**
- `lineage-review <jobs.csv>` — render the drydocs-lineage SME review page (one
  self-contained HTML: folder sections, job cards + INVOKES dependencies, assertion
  panel, exportable notes). Candidates only — the curated write is gate-bound in
  `drydocs_lineage.writer`.

**Verify & ops**
- `m1-verify` / `m3-verify` — assert domain invariants on the populated graph.
- `snapshot` / `prune-snapshots --years N` — (re)compute / prune entity snapshots.
- `sweep-removed --days N [--label L] [--dry-run]` — hard-delete nodes soft-marked
  removed-from-source past the retention window (loads only ever MARK — D7).

Every command that runs an Oracle extract accepts `--use-oracle` plus the scope binds
`--folder` (folder-name LIKE pattern), `--run-as` (tenant FID/service user — `J.OWNER`),
`--developer-sid` (human author/changer), and `--row-cap` (ROWNUM sample cap). A `None`
bind = no filter on that dimension. Every `--use-oracle` extract also writes a per-run
SQL log (run metadata → the exact SQL → CSV result) to `SPIDERP_LOGDIR` (default
`~/logs/DryDocs`, outside the repo) so the HITL can verify what was extracted — see
[`docs/oracle-sql-logging.md`](docs/oracle-sql-logging.md).

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

Loads BMC Control-M folder, job, and condition definitions and the derived `:WAS_INFORMED_BY`
dependency graph (the registered m3_was_informed_by edge — replaces the older DEPENDS_ON name) from Oracle (`psgmgr.*`). **Structural only** — this pass does not ingest
execution history.

### What it delivers

**Folders + jobs**
- **`controlm_folders.py`** — loads `psgmgr.CM_DEF_VTAB` (replicated copy of `dtsremgr.DEF_VTAB`). Creates `:ControlMFolder:Collection` nodes (folder name = `SCHED_TABLE`) and the `:ControlMServer:Platform` mesh (deduped on `DATA_CENTER`).
- **`controlm_jobs.py`** — loads `psgmgr.CM_DEF_VJOB`. Creates `:ControlMJob:Activity` nodes keyed `(folder_id, job_id)`. Captures the business-app name (`APPLICATION` column) for later reconciliation to `:Application.seal_id`.

**Conditions + derived dependencies**
- **`controlm_conditions_in.py`** — loads `psgmgr.CM_DEF_LNKI_P_VW`. Creates `:Condition:Entity` nodes (key `(folder_id, name)`) and `:REQUIRES_IN_CONDITION` edges with boolean-expression metadata (`AND_OR`, `PARENTHESES`, `ORDER_`).
- **`controlm_conditions_out.py`** — loads `psgmgr.CM_DEF_LNKO_P_VW`. Reuses the same `:Condition` nodes; creates `:EMITS_OUT_CONDITION` edges with the `SIGN` operator (`+`/`-`).
- **`controlm_dependencies_derived.py`** — materializes `:WAS_INFORMED_BY` edges from the dependency SQL. DIRECT pairs only since the phased-loader port (2026-07-23): each edge carries `via_condition` and `derived=true`; the stored level/path properties are retired — transitive reach is a graph traversal. Runs in the deferred `--phase relationships` pass (once, unscoped, after all nodes).
- **`controlm_dependencies_recursive.sql`** — direct predecessor pairs via one IN=OUT condition join (the recursive CTE is gone; file name kept for continuity). Rows are pure ctlm_id composites (`folder_id.job_id`) + the linking condition; cyclic-type matching intentionally disabled.

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
└── docs/history/
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

Expected `m3-verify` output after the sample chain. **Reconciled 2026-07-18 (D6) to the
bundled sample, verified live:** 8 folders, **17 jobs**, **15 conditions** (7 distinct
names), **10 derived dependency rows (8 distinct `WAS_INFORMED_BY` edges)**. The formerly
jobless active folders (`161020`, `160501`) gained sample jobs at D6, so every check —
including "active folders contain at least one job" — now passes and the quick-start chain
exits 0. (Earlier docs said 13 jobs with an `empty=2` sample gap, and before that 15 jobs /
5 conditions / 13 deps — those were different fixtures.)

```
                          M3 (part 1 + part 2) invariants
+--------------------------------------------------+-----+---------------------------------+
| Check                                            | OK  | Detail                          |
+==================================================+=====+=================================+
| every folder has a server                        | yes | folders=8 srv_links=8           |
| every ControlMApplication contains a folder      | yes | apps=0 with_folder=0            |
| every job has a folder                            | yes | jobs=17 with_folder=17          |
| no duplicate (folder_id, job_id)                 | yes | dupes=0                         |
| M3 local anchor terms seeded                      | yes | n=3 (expect >= 3 ...)           |
| active folders contain at least one job          | yes | empty=0 total=7                 |
| no orphan conditions                              | yes | orphan=0 total=15               |
| WAS_INFORMED_BY edges carry via_condition        | yes | total=8 missing_condition=0     |
+--------------------------------------------------+-----+---------------------------------+
```

(`apps=0` is sample-mode reality — `:ControlMApplication` header rows come from the Oracle
extract's JOB_ID=1 join, which the bundled CSVs do not carry.)

### Schema notes worth knowing

Three things in the real schema that didn't match the BMC canonical references:

1. **Folder name lives in `SCHED_TABLE`**, not `PARENT_TABLE`. `PARENT_TABLE` is on the job side as a denormalized FK to the folder's `SCHED_TABLE` value. The folder loader uses `SCHED_TABLE`; the job loader keeps `PARENT_TABLE` as a property for query convenience.
2. **Folders are not versioned.** `CM_DEF_VTAB` has no `IS_CURRENT_VERSION` or `VERSION_SERIAL`. Only `USER_DAILY IS NOT NULL` filters active folders.
3. **LNKI and LNKO have different schemas.** LNKI has `AND_OR` / `PARENTHESES` / `ORDER_` for the boolean-expression tree; LNKO has `SIGN` (`+`/`-`). Distinct row models — but both write to the same `:Condition` node when `(folder_id, name)` matches.

### Cyclic-type handling

The canonical SQL **intentionally disables** cyclic-type matching
(`-- AND J_SUB.JOB_CYCLIC_IN = D_SUB.JOB_CYCLIC_OUT`). The commented line is preserved in
`controlm_dependencies_recursive.sql` so the design intent travels with the code.
Cross-cyclic-type dependencies are real (e.g., a 15-minute cyclic FW job feeds a daily
ETL job). Cycle safety needs no guard anymore — the SQL emits direct pairs only
(phased-loader port 2026-07-23), so nothing recurses; cycles in the graph are legitimate
data and traversals handle them with standard Cypher semantics.

The SQL files in `drydocs/loaders/sql/` are the source of truth — edit there if the
corporate `psgmgr` schema diverges from the locked DDL. Row models, Cypher templates,
and loaders don't change.

### Not yet wired

- Per-execution `:JobRun {kind:'controlm_execution'}` history with `start_time` / `end_time` / `duration_sec`, and rolled-up datetime metrics on `:ControlMJob`.
- Folder → `:BatchProcessing` linkage (needs a folder-naming resolver + reliable PAT data).
- Graph load of the variable/command normalization output (Phase D — see below).

(WIRED 2026-07-21, backlog C14: `(:BusinessApplication)-[:USES_SOFTWARE {source:"batch-port"}]->(:SoftwareProduct {role:"orchestrator"})` edges from the SEAL-declared batch-port orchestrator strings — `drydocs load-batch-orchestrators`, replacing the retired `REQUIRES_SCHEDULER → :SchedulerKind` design from the C12 gate.)

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

Lives in `drydocs_core/controlm/` (`variables.py`, `resolver.py`, `commands.py`, `paths.py`,
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
- `test_lineage_inventory.py` / `test_lineage_review.py` / `test_lineage_writer.py` — the drydocs-lineage component (shared-parser oracle, SME page, gate-bound Fork-3 writer + ground-truth-only boundary).
- `test_sql_run_log.py` — the per-extract SQL log + display-only bind renderer (code-regions-only substitution pinned byte-identical on the recursive extract).

End-to-end (opt-in; Docker + testcontainers — a throwaway Neo4j, the real CLI chain,
the m3-verify core invariants; deselected from all default runs):

```powershell
poetry run pytest tests/integration -m integration -q
```

No manual environment prep: `tests/integration/conftest.py` defaults
`TESTCONTAINERS_RYUK_DISABLED=true` (J36) because the ryuk reaper's port
mapping intermittently fails on the producer Windows desktops ("port 8080 is
not available" — shifting WinNAT excluded-port ranges, or a reaper left by a
crashed run). The conftest docstring carries the full why, the override
(`TESTCONTAINERS_RYUK_DISABLED=false`), and the stale-container cleanup
one-liners for a hard-killed run.

## Further reading

- [`knowledge/ARCHITECTURE.md`](knowledge/ARCHITECTURE.md) — the original repo-organization rationale (historical; the current boundary is [`MODULE_MAP.md`](MODULE_MAP.md) + `CLAUDE.md`).
- [`docs/history/controlm-loader-flow.md`](docs/history/controlm-loader-flow.md) — Control-M loader walkthrough (2026-06-11 baseline; §4 drift resolved 2026-07-15, moved to history).
- [`knowledge/ontology/NODE_QUICK_REFERENCE.md`](knowledge/ontology/NODE_QUICK_REFERENCE.md) / [`docs/RELATIONSHIP_GUIDE.md`](docs/RELATIONSHIP_GUIDE.md) — node + relationship catalog.
- [`docs/history/`](docs/history/README.md) — frozen M0 / M1 / planning milestone docs.
