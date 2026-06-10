# DryDocs — Merge Guide: Product Ontology + Schema Consolidation

This file describes what changed in this personal repo relative to the company baseline.
Use it as a guide when merging changes back: **take the product ontology from here,
keep the Control-M Cypher from the company site.**

---

## What to take FROM this repo (product ontology)

### New node type: `AreaProduct`

Added `AreaProduct` as an intermediate org level between `Product` and `DevTeam`
(synonymous with "Area Product Group" / "Team of Teams" in Align/PAT).

**Files containing this change:**

| File | What was added |
|---|---|
| `drydocs/ontology/relationship_vocabulary.yaml` | `AreaProduct` node classification + 6 new local relationships |
| `drydocs/schema/catalog_ontology_supplement.cypher` | `AreaProduct` LocalClass node, 5 LocalRelationship declarations, full Role seed block |
| `drydocs/schema/constraints.cypher` | `area_product_id` uniqueness constraint |
| `drydocs/schema/schema_graph.cypher` | `AreaProduct` SchemaMeta node + 6 relationship MATCH/MERGE blocks |
| `drydocs/models/catalog.py` | `AreaProductRow`, `PatProductMappingRow`, `PatTeamRoleRow` Pydantic models |
| `drydocs/loaders/catalog.py` | `AreaProductsLoader`, `PatProductMappingLoader`, `PatTeamRolesLoader` classes |
| `drydocs/loaders/cypher/area_products.cypher` | MERGE AreaProduct + HAS_AREA_PRODUCT to parent Product |
| `drydocs/loaders/cypher/pat_product_mapping.cypher` | HAS_APPLICATION (Product→Application) + SUPPORTS edges |
| `drydocs/loaders/cypher/pat_team_roles.cypher` | DevTeam HAS_MEMBERSHIP n-ary pattern |
| `docs/NODE_QUICK_REFERENCE.md` | `AreaProduct` row in Catalog (active) table |
| `docs/Product/` | `product-overview.md`, `Technology_Team_Types.md`, `technology_roles_and_responsibilities.md`, `quad-mermaid.js` — full PAT product documentation |

### New graph topology

```
Product -[:HAS_APPLICATION]-> Application
Product -[:HAS_AREA_PRODUCT]-> AreaProduct -[:HAS_DEV_TEAM]-> DevTeam
DevTeam -[:SUPPORTS {team_type, sponsored}]-> Product | AreaProduct
DevTeam -[:HAS_MEMBERSHIP]-> Membership -[:OF_ROLE]-> Role
                                         -[:HELD_BY]-> Employee
```

- `team_type` is an edge property on `SUPPORTS` (`aligned` | `flex` | `dedicated`)
- `sponsored: bool` is an edge property on `SUPPORTS` — not a separate relationship type

### Full Role vocabulary

`catalog_ontology_supplement.cypher` now seeds all 31 Role nodes (SEAL embedded,
SEAL contact, PAT Technology, PAT Product/Portfolio, D&A, CCB Operations).
All roles MERGE on `name` to match how SEAL loaders MATCH roles at runtime.

### `models/seal.py` — Tech Partner alias

Added `"tech partner": "CTO"` to `_ROLE_CANONICAL`. PAT refers to the
application-level tech lead as "Tech Partner"; SEAL calls the same role "CTO".
Without this alias, PAT contact data would fail role canonicalization.

---

## What NOT to take from this repo (Control-M)

The company site has a more complete Control-M implementation. Do **not**
overwrite those files with the versions here. The only Control-M changes in
this repo are constraint key corrections (see below) — evaluate those
individually rather than doing a wholesale file replacement.

---

## Schema consolidation — evaluate against company baseline

These changes cleaned up patch files that existed because the original M0 seed
was stale. The company site may already have a cleaner version, or may have
diverged differently. Review each change before applying.

### Deleted files (patch files eliminated)

| Deleted file | Content absorbed into |
|---|---|
| `drydocs/schema/m3_constraints_upgrade.cypher` | `drydocs/schema/constraints.cypher` |
| `drydocs/schema/m1_role_vocabulary_update.cypher` | (eliminated — roles now seeded correctly from the start) |
| `drydocs/schema/m3_ontology_supplement.cypher` | Renamed to `drydocs/schema/ontology_supplement.cypher` |

### `drydocs/schema/ontology_supplement.cypher` (renamed from `m3_ontology_supplement.cypher`)

Same content as the old `m3_ontology_supplement.cypher` with two fixes:
- All references to `RUNS_ON` updated to `SCHEDULED_ON` (relationship was renamed)
- Header updated to remove "M3" version markers

### `drydocs/schema/constraints.cypher` — Control-M key corrections

The M3 draft used incorrect composite keys. These were corrected:

```cypher
-- OLD (wrong — included version_serial in the key)
CREATE CONSTRAINT controlmjob_key FOR (j:ControlMJob) REQUIRE (j.job_id, j.version_serial) IS NODE KEY;
CREATE CONSTRAINT condition_key   FOR (c:Condition)   REQUIRE (c.folder_id, c.name, c.cyclic_type) IS NODE KEY;

-- NEW (correct — natural key without version_serial; loaders filter IS_CURRENT_VERSION='1')
DROP CONSTRAINT controlmjob_key IF EXISTS;
CREATE CONSTRAINT controlmjob_key FOR (j:ControlMJob) REQUIRE (j.folder_id, j.job_id) IS NODE KEY;

DROP CONSTRAINT condition_key IF EXISTS;
CREATE CONSTRAINT condition_key   FOR (c:Condition)   REQUIRE (c.folder_id, c.name) IS NODE KEY;
```

If the company site already has correct keys, skip this. If it still has the
old versioned keys, apply the DROP/CREATE pair above.

### `drydocs/schema/ontology.cypher` — stale role seeds removed

The original M0 seed contained 8 stale Role nodes with wrong names
(e.g., `"App Owner"` instead of `"Application Owner"`, `"Agility Lead"`,
`"Product Contact"`). These were removed. The company site may still have
them — if so, the `catalog_ontology_supplement.cypher` Role seeds will
create the correct nodes, but the stale ones will persist alongside them
unless manually cleaned up with:

```cypher
MATCH (r:Role) WHERE r.name IN [
  'App Owner', 'Agility Lead', 'Product Contact'
] AND NOT EXISTS { MATCH ()-[:OF_ROLE]->(r) }
DELETE r;
```

### `drydocs/cli.py` — command renames

| Old command | New command | Reason |
|---|---|---|
| `apply-m3-supplement` | `apply-ontology-supplement` | Removed version prefix |

Stale file-path constants removed: `M1_ROLE_VOCAB_UPGRADE`, `M3_SUPPLEMENT_FILE`,
`M3_CONSTRAINTS_UPGRADE`. Added: `ONTOLOGY_SUPPLEMENT_FILE`.

Also fixed: the `m3-verify` command Cypher used `RUNS_ON` (renamed to `SCHEDULED_ON`).

---

## Bootstrap order (authoritative)

```
1. constraints.cypher            — uniqueness constraints + indexes
2. ontology.cypher               — W3C backbone (PROV-O, ORG, DCAT, OWL, OL)
3. ontology_supplement.cypher    — Control-M local-namespace terms
4. seal_supplement.cypher        — SEAL/Application local-namespace terms
5. catalog_ontology_supplement.cypher  — Catalog terms + all 31 Role seeds
```

---

## New loaders registered in `cli.py` / `loaders/catalog.py`

| Loader name | Row model | Cypher file |
|---|---|---|
| `area_products.v1` | `AreaProductRow` | `loaders/cypher/area_products.cypher` |
| `pat_product_mapping.v1` | `PatProductMappingRow` | `loaders/cypher/pat_product_mapping.cypher` |
| `pat_team_roles.v1` | `PatTeamRoleRow` | `loaders/cypher/pat_team_roles.cypher` |

Sample CSV files for these loaders do not exist yet in `drydocs/data/samples/`.

---

## Files safe to copy wholesale from this repo

These files were either created new here or the company site will not have
a conflicting version:

- `drydocs/loaders/cypher/area_products.cypher` (new)
- `drydocs/loaders/cypher/pat_product_mapping.cypher` (new)
- `drydocs/loaders/cypher/pat_team_roles.cypher` (new)
- `drydocs/schema/catalog_ontology_supplement.cypher` (new)
- `drydocs/schema/ontology_supplement.cypher` (renamed from m3_)
- `docs/Product/` directory (all new documentation files)
