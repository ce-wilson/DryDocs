# DryDocs — Merge / Rebase Guide

This repo diverges from the company baseline in several directions. Use this file
when pulling changes across, or when rebasing local work onto the Control-M
normalization stream.

- **Control-M C3/C4 normalization** (variable taxonomy → resolver → command parser) —
  done **here first**, Phases A/B/C complete; push TO company, do not pull over.
- **Product ontology** (PAT/SEAL roles, AreaProduct hierarchy) — take FROM this repo
- **Schema consolidation** — patch files deleted, bootstrap order cleaned up; evaluate per file
- **Internal standards** (`internal-standards/`) — folder-naming, data-center-naming,
  description-metadata, calendar-projection plans; additive, take FROM this repo.

---

## Commit timeline (newest first)

```
cb6e056  Add Phase C command/script parser — invocations, file ops, file refs, facts
520f9ca  Add Phase B variable resolver, staging output, and vendor-doc validation
1f08b65  minor updates to settings and readme        (internal-standards/, bmc text)
91882df  Add Control-M variable taxonomy (Phase A) and staging DDL
f3f1a83  new sql
6c5b7b5  update-pat-seal-roles
0eb98a5  updated relationship_vocabulary.yaml to include new relationships
```

The three Control-M normalization commits are **`91882df` → `520f9ca` → `cb6e056`**
(Phase A → B → C), applied in that order.

---

# Rebasing local changes onto the Control-M stream (A → B → C)

If you have local changes and need to land them on top of Phases A–C, this is the
map of what each phase touched and where conflicts will surface.

## Files added (no conflict risk — pure additions)

| File | Phase | Purpose |
|---|---|---|
| `drydocs/controlm/variables.py` | A | `VariableKind` (9 kinds) + `classify_variable()` / `classify_job_variables()` |
| `drydocs/controlm/variable_report.py` | A | `VariableCoverage` accumulator |
| `drydocs/loaders/sql/controlm_variables.sql` | A | Variable extract query (`psgmgr.CM_DEF_SETVAR` — **name unverified**) |
| `drydocs/loaders/sql/ddl/controlm_staging_ddl.sql` | A | Full staging-layer DDL (8 STG_ tables + views) |
| `drydocs/controlm/resolver.py` | B | Offline AutoEdit substitution engine |
| `drydocs/controlm/staging.py` | B (ext. C) | STG_ row builder — `build_staging_bundle` / `collect_jobs` |
| `drydocs/controlm/commands.py` | C | Shell parser + `LAUNCHER_REGISTRY` |
| `drydocs/controlm/paths.py` | C | Path canonicalization + ref_role classification |
| `drydocs/controlm/facts.py` | C | Fact / notification routing |
| `docs/controlm-c3-normalization-status.md` | B (ext. C) | Status + operational runbook |
| `tests/unit/test_variable_classifier.py` | A | |
| `tests/unit/test_variable_resolver.py` | B | |
| `tests/unit/test_variable_staging.py` | B (ext. C) | |
| `tests/unit/test_command_parser.py` | C | |

## Files modified (potential conflict points)

| File | Phases | What to preserve when resolving |
|---|---|---|
| `drydocs/controlm/__init__.py` | A, B, C | Re-exports accumulate each phase. Final `__all__` must export: `VariableKind`, `ClassifiedVariable`, `classify_variable`, `classify_job_variables`, `VariableCoverage` (A); `ResolvedVariable`, `resolve_job`, `resolve_layers` (B); `Invocation`, `FileOp`, `parse_command`, `extract_container_command`, `FileRef`, `build_file_ref`, `canonicalize_path`, `classify_role`, `route_fact`, `build_staging_bundle`, `build_staging_rows`, `collect_jobs` (C). |
| `drydocs/cli.py` | A, B, C | Adds two commands: `analyze-variables` (A, `--resolve` flag added in B) and `normalize-variables` (B, extended in C to write 8 CSVs). Imports from `.controlm` and `.controlm.staging`. No existing command bodies changed. |
| `drydocs/models/controlm.py` | A | Adds `ControlMVariableRow` (and an `AliasChoices` import). Existing row models untouched — conflicts here mean someone else also edited the model file. |
| `drydocs/models/__init__.py` | A | Adds `ControlMVariableRow` to imports + `__all__`. |
| `drydocs/controlm/variables.py` | A, B | B reworked the token grammar (system-var registry, `%%$` century syntax, global/pool refs). If you patched A's `variables.py`, reapply onto B's grammar — see the `KNOWN_SYSTEM_VARIABLES` / `KNOWN_SYSTEM_FUNCS` registries. |
| `drydocs/controlm/staging.py` | B, C | C restructured the B builder around `StagingBundle`. `build_staging_rows` survives as a back-compat shim returning `(variable, parse_quality)`. |
| `drydocs/controlm/variable_report.py` | A, B | B added system-var / global-ref counters. |

## Load / dependency order (import-time)

```
variables.py      (no intra-package deps)
  ├── variable_report.py   (imports variables)
  ├── resolver.py          (imports variables: ENV_LETTER_MAP, _is_system_func/_var)
  ├── paths.py             (standalone)
  ├── commands.py          (standalone)
  ├── facts.py             (imports variables)
  └── staging.py           (imports models, commands, facts, paths, resolver, variables)
```

`__init__.py` imports `staging` last (it pulls in everything). If you split or move
any of these, keep `staging` downstream of the rest.

## Sanity check after rebase

```
poetry run pytest tests/unit/test_variable_classifier.py \
                  tests/unit/test_variable_resolver.py \
                  tests/unit/test_variable_staging.py \
                  tests/unit/test_command_parser.py -q
poetry run drydocs analyze-variables --resolve        # coverage tables
poetry run drydocs normalize-variables --out-dir stg_out   # writes 8 CSVs
```

Expect 102 passing in the four variable-stream files. The 6 failures in
`test_schema.py`, `test_folder_name_parser.py`, `test_controlm_cypher.py`
**pre-exist on `main`** and are unrelated to this stream — do not let them block a rebase.

---

# Control-M C3/C4 normalization — current state (push TO company)

Three phases below the existing job-to-job lineage, all delivered here. The company
site has a more complete Control-M *loader* implementation, but the **normalization
pipeline (A/B/C) was authored here** and should be pushed TO company, not pulled over.
Do not overwrite local files under `drydocs/loaders/controlm/`,
`drydocs/schema/ontology_supplement.cypher` (Control-M content), or the Control-M SQL
loaders with versions from elsewhere.

Architecture: **SQL extract → Python normalize → Oracle staging (`DRYDOCS_STG`,
QA in SQL Developer) → Neo4j under PROV `:JobRun`.** Variable resolution and command
parsing happen in Python, not recursive SQL.

## Phase A — variable taxonomy + staging output (`91882df`, output side completes the phase)

`VariableKind` (9 kinds, precedence order):

| Kind | Description |
|---|---|
| `MALFORMED` | Empty / whitespace / invalid name token |
| `EMBEDDED_SHELL` | `PRECMD` / `POSTCMD` (+ observed `POSCMD` typo) — shell text for Phase C |
| `PLUGIN_NS` | `%%FileWatch-*`, `%%UCM-*` — routed to APPL_TYPE handler |
| `FLOW_REF` | `%%\VAR` global / `%%\\POOL\VAR` pool — cross-job shared state, kept verbatim |
| `DYNAMIC_NAME` | Adjacent `%%refs` compose a name at runtime — per-env expansion in B |
| `SEMANTIC_FACT` | Fact-registry name (SEAL, FID_*, DATAFLOW...) — mined into `STG_APP_FACT` |
| `SYSTEM_FUNC` | Only system tokens (CALCDATE/SUBSTR/GETENV/WCALC/BLANK + system vars) |
| `VAR_REF` | References other user `%%vars` — resolved in B |
| `LITERAL` | None of the above |

Output side (`staging.py` + `normalize-variables`) writes `STG_RUN`, `STG_VARIABLE`,
`STG_PARSE_QUALITY` with columns matching the DDL exactly. ~1.1M variable rows across
4 DCs (~18.8K folders / ~240.6K jobs); 59% of jobs have zero variables.

## Phase B — variable resolver (`520f9ca`)

`resolver.py` — offline AutoEdit simulation. Sequential assignment (ordered defs,
last binding wins, forward refs stay unresolved); longest-defined-name matching at
each `%%` site; canonical symbolic tokens (`{ODATE}`, CALCDATE compaction `{ODATE-1}`);
cross-pass blocked-set kills self-reference loops; env-triplet variant expansion
(`%%SCRIPT_PATH_%%HOSTNM`); global/pool refs kept verbatim. Sample: 86% fully resolved.

Vendor validation (`vendor-bmc/controlm-variables.md`) corrected three things in
`variables.py`: system variables exist without `$` (`%%ORDERID`, `%%JOBNAME`); `%%$X`
is century-format syntax; `%%\VAR` (global) vs `%%\\POOL\VAR` (pool) both captured.

## Phase C — command / script parser (`cb6e056`)

Parses the executable side into the five remaining staging tables.

| Module | Produces |
|---|---|
| `commands.py` | `STG_INVOCATION` (data-driven `LAUNCHER_REGISTRY`: `.m`→ABINITIO, `pmcmd`→INFORMATICA, `run_data_validation.sh`→VALIDATION_UTIL, `python`→PYTHON/PYSPARK, …), `STG_FILE_OP` (mkdir/cp/mv/rm/sed) |
| `paths.py` | `STG_FILE_REF` (canonical paths, `{TS16}` wildcards, ref_role) |
| `facts.py` | `STG_APP_FACT` + `STG_NOTIFICATION` |

`normalize-variables` now writes all 8 STG_ CSVs. Sample: 6 invocations (0 UNKNOWN),
16 file ops, 92 file refs, 14 notifications, 66 app facts.

Grow `LAUNCHER_REGISTRY` (add a `(basename regex, invocation_type, rule_id)` tuple)
as the UNKNOWN backlog reveals new launchers — that is Phase E. Vendor docs read for
this phase: `controlm-{os-job-parameters,file-watcher,api-job-types,file-transfer-job}.md`.

## Staging DDL (`controlm_staging_ddl.sql`, schema `DRYDOCS_STG`)

8 tables: `STG_RUN`, `STG_VARIABLE`, `STG_PARSE_QUALITY`, `STG_INVOCATION`,
`STG_FILE_OP`, `STG_FILE_REF`, `STG_NOTIFICATION`, `STG_APP_FACT`, plus base read views
and `STG_COVERAGE_SUMMARY`. Surrogate identity PKs (duplicate `(job, var_name)` defs are
legitimate). All keys carry `DATA_CENTER` (TABLE_ID may collide across the 4 DCs).
< 3M rows / < 2 GB; no partitioning.

> **TODO (DBA)**: confirm the variable source view name. The SQL Developer extract used
> `TABLE_NAME|JOB_NAME|JOB_ID|APPL_TYPE|NAME|VALUE` (`TABLE_NAME` carries `TABLE_ID`
> values). The query uses `psgmgr.CM_DEF_SETVAR` — verify before running. Flagged in
> both `controlm_variables.sql` and the DDL.

See `docs/controlm-c3-normalization-status.md` for the full status + operational runbook.

---

## Take FROM this repo → company

### 1. PAT Product Ontology — `AreaProduct` node + team alignment model

**Commit: `6c5b7b5`**

Added `AreaProduct` (Area Product Group / Team of Teams) as an intermediate org
level between `Product` and `DevTeam`, team type edge properties on `SUPPORTS`,
and the full PAT human role vocabulary.

| File | What was added |
|---|---|
| `drydocs/ontology/relationship_vocabulary.yaml` | `AreaProduct` node classification + 6 new local relationships |
| `drydocs/schema/catalog_ontology_supplement.cypher` | `AreaProduct` LocalClass, 5 LocalRelationship declarations, all 31 Role seeds |
| `drydocs/schema/constraints.cypher` | `area_product_id` uniqueness constraint |
| `drydocs/schema/schema_graph.cypher` | `AreaProduct` SchemaMeta node + 6 relationship MATCH/MERGE blocks |
| `drydocs/models/catalog.py` | `AreaProductRow`, `PatProductMappingRow`, `PatTeamRoleRow` Pydantic models |
| `drydocs/loaders/catalog.py` | `AreaProductsLoader`, `PatProductMappingLoader`, `PatTeamRolesLoader` |
| `drydocs/loaders/cypher/area_products.cypher` | MERGE AreaProduct + HAS_AREA_PRODUCT to parent Product |
| `drydocs/loaders/cypher/pat_product_mapping.cypher` | HAS_APPLICATION (Product→Application) + SUPPORTS edges |
| `drydocs/loaders/cypher/pat_team_roles.cypher` | DevTeam HAS_MEMBERSHIP n-ary pattern |
| `drydocs/models/seal.py` | Added `"tech partner": "CTO"` to `_ROLE_CANONICAL` |
| `docs/NODE_QUICK_REFERENCE.md` | `AreaProduct` row in Catalog (active) table |
| `docs/Product/` | `product-overview.md`, `Technology_Team_Types.md`, `technology_roles_and_responsibilities.md`, `quad-mermaid.js` |

**New graph topology:**
```
Product -[:HAS_APPLICATION]-> Application
Product -[:HAS_AREA_PRODUCT]-> AreaProduct -[:HAS_DEV_TEAM]-> DevTeam
DevTeam -[:SUPPORTS {team_type, sponsored}]-> Product | AreaProduct
DevTeam -[:HAS_MEMBERSHIP]-> Membership -[:OF_ROLE]-> Role -[:HELD_BY]-> Employee
```

- `team_type` on `SUPPORTS`: `aligned` | `flex` | `dedicated` (edge property, not node property)
- `sponsored: bool` on `SUPPORTS`: edge property, not a separate relationship type
- 31 Role nodes seeded — all MERGE on `name` to match how SEAL loaders MATCH roles at runtime

**Key alias added to `models/seal.py`:**
PAT calls the application-level tech lead "Tech Partner"; SEAL calls it "CTO".
Without this alias, PAT contact data fails role canonicalization.

### 2. `.gitignore` — exclude sample data

`drydocs/data/` is now ignored. Sample CSVs stay local and off-repo.
Apply this if the company repo is also tracking sample files you want to stop committing.

---

## Schema consolidation — evaluate against company baseline

These changes clean up patch files that existed because the M0 seed was stale.
The company site may have already fixed this differently — review each change before applying.

### Deleted files (absorbed elsewhere)

| Deleted | Content moved to |
|---|---|
| `drydocs/schema/m3_constraints_upgrade.cypher` | `drydocs/schema/constraints.cypher` |
| `drydocs/schema/m1_role_vocabulary_update.cypher` | Eliminated — roles now seeded correctly from the start in `catalog_ontology_supplement.cypher` |
| `drydocs/schema/m3_ontology_supplement.cypher` | Renamed to `drydocs/schema/ontology_supplement.cypher` |

### `constraints.cypher` — Control-M key corrections

The M3 draft used incorrect composite keys (included `version_serial` and `cyclic_type`).
Corrected to natural keys; loaders filter `IS_CURRENT_VERSION='1'` so one canonical node per logical entity:

```cypher
-- OLD (wrong)
CREATE CONSTRAINT controlmjob_key FOR (j:ControlMJob) REQUIRE (j.job_id, j.version_serial) IS NODE KEY;
CREATE CONSTRAINT condition_key   FOR (c:Condition)   REQUIRE (c.folder_id, c.name, c.cyclic_type) IS NODE KEY;

-- NEW (correct)
DROP CONSTRAINT controlmjob_key IF EXISTS;
CREATE CONSTRAINT controlmjob_key FOR (j:ControlMJob) REQUIRE (j.folder_id, j.job_id) IS NODE KEY;
DROP CONSTRAINT condition_key IF EXISTS;
CREATE CONSTRAINT condition_key   FOR (c:Condition)   REQUIRE (c.folder_id, c.name) IS NODE KEY;
```

### `ontology.cypher` — stale M0 role seeds removed

The original M0 seed had 8 stale Role nodes with wrong names (`"App Owner"`,
`"Agility Lead"`, `"Product Contact"`, etc.). These were removed. If the company
site still has them, the correct nodes from `catalog_ontology_supplement.cypher`
will coexist alongside the stale ones. Clean up stale nodes only if no
memberships reference them:

```cypher
MATCH (r:Role) WHERE r.name IN ['App Owner', 'Agility Lead', 'Product Contact']
AND NOT EXISTS { MATCH ()-[:OF_ROLE]->(r) }
DELETE r;
```

### `cli.py` — command rename

| Old | New |
|---|---|
| `apply-m3-supplement` | `apply-ontology-supplement` |

Stale constants removed: `M1_ROLE_VOCAB_UPGRADE`, `M3_SUPPLEMENT_FILE`, `M3_CONSTRAINTS_UPGRADE`.
Added: `ONTOLOGY_SUPPLEMENT_FILE`. Also fixed: `m3-verify` Cypher used `RUNS_ON` (now `SCHEDULED_ON`).

### Bootstrap order (authoritative)

```
1. constraints.cypher
2. ontology.cypher
3. ontology_supplement.cypher         (was m3_ontology_supplement.cypher)
4. seal_ontology_supplement.cypher
5. catalog_ontology_supplement.cypher  (owns all 31 Role seeds)
```
