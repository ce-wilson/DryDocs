# DryDocs — M0 Bootstrap

Production support inventory + data product knowledge graph for D&A batches.

This is the **M0 skeleton**: Poetry deps, Neo4j client, ontology backbone seed, constraint DDL, and a CLI to apply them. No data loaders yet — those land in M1.

## Prereqs

- Python 3.11+
- Poetry
- Neo4j 5.x (Desktop, Aura, or on-prem)
- **APOC** plugin enabled on the Neo4j server (`apoc.cypher.runMany` is used by the bootstrap)

## Quickstart (Windows / PowerShell)

```powershell
# 1. Install deps.
poetry install

# 2. Configure Neo4j connection.
Copy-Item .env.example .env
notepad .env   # set NEO4J_PASSWORD at minimum

# 3. Verify connectivity + APOC.
poetry run drydocs check

# 4. Apply constraints + ontology seed.
poetry run drydocs bootstrap

# 5. Verify the bootstrap.
poetry run drydocs verify
```

Expected output of `drydocs verify` after a clean bootstrap:

```
                Ontology terms by source
+--------------+-------+
| Label        | Terms |
+==============+=======+
| DcatClass    |     5 |
| DcatProperty |     8 |
| DprodClass   |     6 |
| DprodProperty|     3 |
| DqvClass     |     5 |
| DqvProperty  |     5 |
| OlClass      |     3 |
| OrgClass     |     5 |
| OrgProperty  |     5 |
| ProvClass    |     6 |
| ProvProperty |     6 |
| SwoClass     |     7 |
| SwoProperty  |     6 |
+--------------+-------+

         Seed instance counts
+-----------------+-------+
| Kind            | Count |
+=================+=======+
| Agent           |     1 |
| BusinessSegment |     5 |
| Dimension       |     5 |
| Metric          |    10 |
| Role            |     8 |
| SchedulerKind   |     3 |
+-----------------+-------+

Constraints in db: 33
```

## CLI

| Command | What it does |
|---|---|
| `drydocs check`      | Verify Bolt connectivity, server version, and APOC presence. |
| `drydocs bootstrap`  | Apply `constraints.cypher` + `ontology.cypher`. Idempotent. |
| `drydocs verify`     | Print ontology counts and constraint count. |
| `drydocs reset --yes`| **Destructive.** `MATCH (n) DETACH DELETE n` then exit. |

Common flags: `-v` for debug logging on any command. `bootstrap` accepts `--skip-constraints` and `--skip-ontology` if you need to apply only one.

## Project layout

```
DryDocs/
├── pyproject.toml
├── .env.example
├── README.md
├── drydocs/
│   ├── __init__.py
│   ├── config.py                pydantic-settings: Neo4j, Oracle, App
│   ├── neo4j_client.py          driver wrapper, run/run_script/execute_file
│   ├── cli.py                   typer entry point
│   ├── ontology/
│   │   ├── __init__.py
│   │   └── namespaces.py        CURIE prefix table + expand()
│   └── schema/
│       ├── constraints.cypher   v2 §5 + v3 §J — 33 constraints/indexes
│       └── ontology.cypher      DPROD, DCAT, PROV, DQV, ORG, SWO, OL anchors
│                                + Roles (F.3) + SchedulerKind + BusinessSegments
│                                + DQV dimensions/metrics catalog
└── tests/
    └── unit/
        ├── test_schema.py       static checks on cypher files
        └── test_namespaces.py   namespaces helper smoke
```

## What M0 delivers and what it doesn't

**Delivered:**

- Empty graph with all phase-1 constraints applied (v2 §5 + v3 §J).
- Ontology backbone for DPROD, DCAT, PROV-O, DQV, SWO (anchor subset), ORG, OpenLineage labels.
- Role vocabulary (8 roles, source-tagged SEAL vs PAT) for the §F Membership pattern.
- SchedulerKind vocabulary (ControlM / Autosys / Airflow).
- Effective-dated corporate hierarchy (Company `JPMC` + 4 current BusinessSegments + retired `CB` from pre-Q2-2024).
- DQV catalog: 5 dimensions (Completeness, Accuracy, Consistency, Timeliness, Integrity), 10 metrics, wired to dimensions.
- The canonical loader Agent (`drydocs.loader.v1`) for PROV attribution.

**Not delivered (later milestones):**

- M1: Oracle catalog scaffolding + SEAL CSV loaders.
- M2: PAT CSV loaders (incl. `pat_product_mapping` from the loader pack), employees, org chart, ServiceNow groups.
- M3: BMC Control-M structural ingest from `psgmgr.DEF_*`.
- M4: TDQ pipeline + channel typology.
- M5: Streamlit explorer.
- M6: KGoT seams.
- The full SWO SDLC subset (~250 terms): port `swo_sdlc_ontology.cypher` from the savepoint into `drydocs/schema/swo_sdlc_ontology.cypher` and add a `bootstrap --include-swo-sdlc` flag.

## Next step

Run `drydocs bootstrap` and `drydocs verify` against your Neo4j; eyeball the counts vs. the expected table above. When that's clean, M1 begins (Oracle catalog scaffolding + the two SEAL CSV loaders).