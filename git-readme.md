# DryDocs — Merge Guide

This repo diverges from the company baseline in two directions. Use this file
when pulling changes across:

- **Product ontology** (PAT/SEAL roles, AreaProduct hierarchy) — take FROM this repo
- **Control-M normalization** (variable taxonomy, staging DDL) — company site is ahead; take FROM company site
- **Schema consolidation** — patch files deleted, bootstrap order cleaned up; evaluate per file

---

## Commits in this repo not on company baseline

```
91882df  Add Control-M variable taxonomy (Phase A) and staging DDL
6c5b7b5  update-pat-seal-roles
0eb98a5  updated relationship_vocabulary.yaml to include new relationships
```

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

---

### 2. `.gitignore` — exclude sample data

`drydocs/data/` is now ignored. Sample CSVs stay local and off-repo.
Apply this if the company repo is also tracking sample files you want to stop committing.

---

## Take FROM company → this repo (Control-M)

The company site has a more complete Control-M implementation. Do **not**
overwrite company files with versions from here for anything under
`drydocs/loaders/controlm/`, `drydocs/schema/ontology_supplement.cypher`
(Control-M content), or the Control-M SQL loader queries.

The variable taxonomy work below (`91882df`) was done **here first** and
should be pushed TO the company site, not pulled from it.

---

## Control-M variable taxonomy — push TO company (`91882df`)

Phase A of the C3/C4 normalization pipeline: variable classification,
coverage reporting, staging DDL, and the `analyze-variables` CLI command.

### New files

| File | Purpose |
|---|---|
| `drydocs/controlm/variables.py` | `VariableKind` enum + `classify_variable()` / `classify_job_variables()` |
| `drydocs/controlm/variable_report.py` | `VariableCoverage` accumulator — kind distribution, plugin namespaces, fact types, system functions, resolution hot-set |
| `drydocs/loaders/sql/controlm_variables.sql` | Formal variable extract query over `psgmgr.CM_DEF_SETVAR` |
| `drydocs/loaders/sql/ddl/controlm_staging_ddl.sql` | Full C3/C4 staging layer DDL (see below) |
| `tests/unit/test_variable_classifier.py` | Unit tests for all 9 variable kinds |

### Modified files

| File | Change |
|---|---|
| `drydocs/controlm/__init__.py` | Exports `VariableKind`, `ClassifiedVariable`, `classify_variable`, `classify_job_variables`, `VariableCoverage` |
| `drydocs/models/__init__.py` | Exports `ControlMVariableRow` |
| `drydocs/models/controlm.py` | Added `ControlMVariableRow` — accepts both formal SQL projection and raw SQL Developer export column shapes via `AliasChoices` |
| `drydocs/cli.py` | Added `analyze-variables` command |

### Variable taxonomy (9 kinds, precedence order)

| Kind | Description |
|---|---|
| `MALFORMED` | Empty name, whitespace in name, or invalid token |
| `EMBEDDED_SHELL` | `PRECMD` / `POSTCMD` (and observed `POSCMD` typo) — value is shell text for Phase-C parser |
| `PLUGIN_NS` | Namespaced name (`%%FileWatch-*`, `%%UCM-*`) — routed to APPL_TYPE handler |
| `FLOW_REF` | Value points into another flow's namespace (`%%\FLOW\VAR`) — becomes `REFERENCES_FLOW` edge candidate |
| `DYNAMIC_NAME` | Adjacent `%%refs` compose a variable *name* at runtime — resolve per-environment in Phase B |
| `SEMANTIC_FACT` | Name in the fact registry (SEAL, FID_*, DATAFLOW, ...) with plain value — mined into `STG_APP_FACT` |
| `SYSTEM_FUNC` | Value uses only `%%$` system functions (`%%$ODATE`, `%%$CALCDATE`) — canonicalized to symbolic tokens |
| `VAR_REF` | Value references other plain `%%vars` — Phase B substitutes |
| `LITERAL` | None of the above |

### Staging DDL scope (`controlm_staging_ddl.sql`)

Targets schema `DRYDOCS_STG`. Covers:

- **Section 0**: DBA pre-flight validation queries
- **Section 1**: Base read views over psgmgr replicated views (`CM_DEF_VTAB`, `CM_DEF_VJOB`, `CM_DEF_SETVAR`)
- **Section 2**: `STG_RUN` — load run registry (full-refresh pattern)
- **Section 3**: `STG_VAR_CLASSIFIED` — classified variable definitions (~1.1M rows)
- **Section 4**: `STG_APP_FACT` — mined semantic facts (SEAL IDs, FID numbers, flow names)
- **Section 5**: Indexes
- **Section 6**: Consumer grants

Volume estimates (capture 2026-06, 4 data centers):

| DC | Folders | Jobs |
|---|---|---|
| P012 | 2,230 | 42,688 |
| P014 | 4,188 | 52,976 |
| P021 | 7,914 | 59,712 |
| P032 | 4,441 | 85,202 |
| **Total** | **~18,800** | **~240,600** |

Variable rows: ~1.1M (job-level ~1.03M + folder-level ~95K). Staging estimate: < 3M rows / < 2 GB incl. indexes. No partitioning required.

> **TODO (DBA)**: Confirm the variable source view name. The SQL Developer extract used `TABLE_NAME|JOB_NAME|JOB_ID|APPL_TYPE|NAME|VALUE` — `TABLE_NAME` actually carries `TABLE_ID` values. The formal query uses `CM_DEF_SETVAR`; verify this is the correct object name on the company database before running.

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
