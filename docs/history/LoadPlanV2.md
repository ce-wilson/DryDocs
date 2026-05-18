# DryDocs — Neo4j Loader Plan (v2)

Project root: `C:\coding\projects\DryDocs` (Poetry-managed, Windows host)
**Reframed**: this is a **Data Product knowledge graph**. Control-M is the *operational substrate* feeding it; the conceptual model is data products, not jobs.

Ontology stack (in order of authority for any given fact):

1. **DPROD** — Data Product Ontology. Defines what a Data Product is, its input/output ports, agreements, owners.
2. **DCAT v3** — Catalog vocabulary. The *substance* of a data product is one or more Datasets / Distributions / DataServices.
3. **PROV-O / PROV-DM** *(treating "DPROV-O" / "DPROV-DM" as the data-product profile of these — confirm in §11)*. Canonical provenance: who did what to which Entity, when.
4. **OpenLineage** — runtime event firehose. Every Control-M run emits OL events; we project them into PROV.
5. **DQV** (W3C Data Quality Vocabulary) — quality metrics, dimensions, measurements. Carries the **TDQ** results.
6. **SWO** — software/code domain (scripts, languages, runtime hosts). Demoted to "infrastructure facts about how a product is *produced*".
7. **W3C ORG** — people, teams, accountability for products and quality.

Same goal as before: load Control-M CSV extracts, expose via Streamlit, wire into a KGoT-style agent later.

---

## 1. Goals & non-goals

In scope (phase 1):
- Idempotent loader for Control-M CSV extracts → DPROD/DCAT-shaped graph.
- Ontology backbone (DPROD, DCAT, PROV, OL, DQV, SWO, ORG anchor terms) seeded once.
- **TDQ pipeline modeled explicitly**: data file + control file → DQ activity → DQV measurements.
- OpenLineage event ingestion path (synthesized from CSV in phase 1; live webhook ready in phase 2).
- Read-only Streamlit explorer with a **Data Product** lens, lineage, and DQ scoreboard.
- KGoT seams — agent reads/writes via a single client wrapper.

Out of scope (now):
- Parsing `.pset` internals or .ksh AST.
- Writing back to Control-M.
- Catalog UI / governance workflow (we surface; we don't approve).

---

## 2. Stack

| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Poetry already initialized |
| DB driver | `neo4j` (official) | Per your "base neo4j-tools" ask |
| Data | `pandas` | CSV ergonomics |
| Validation | `pydantic` v2 | Row-level contracts catch bad CSVs |
| Lineage events | `openlineage-python` | Native OL event objects + JSON serialization |
| Config | `pydantic-settings` + `.env` | Bolt URI/creds out of source |
| UI | `streamlit` + `streamlit-agraph` | Quick interactive lineage |
| Tests | `pytest` + `testcontainers-neo4j` | Real driver against ephemeral DB |
| Lint/format | `ruff` + `mypy` | Cheap correctness |

`pyproject.toml` deps (drop into Poetry):

```toml
[tool.poetry.dependencies]
python = "^3.11"
neo4j = "^5.20"
pandas = "^2.2"
pydantic = "^2.7"
pydantic-settings = "^2.3"
python-dotenv = "^1.0"
openlineage-python = "^1.18"
streamlit = "^1.36"
streamlit-agraph = "^0.0.45"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2"
pytest-cov = "^5.0"
testcontainers = {version = "^4.5", extras = ["neo4j"]}
ruff = "^0.5"
mypy = "^1.10"
```

---

## 3. Project layout

```
DryDocs/
├── pyproject.toml
├── .env.example
├── README.md
├── data/
│   ├── raw/                       # Control-M CSV extracts
│   ├── lineage/                   # OpenLineage event JSON (in/out)
│   └── samples/                   # checked-in fixtures for tests
├── ontology/
│   ├── namespaces.py              # IRI prefixes for dprod, dcat, prov, ol, dqv, swo, org, local
│   ├── dprod_terms.py
│   ├── dcat_terms.py
│   ├── prov_terms.py
│   ├── openlineage_terms.py       # OL canonical job/run/dataset facets we care about
│   ├── dqv_terms.py
│   ├── swo_terms.py
│   ├── org_terms.py
│   └── seed.cypher                # generated MERGE for anchor terms
├── drydocs/
│   ├── __init__.py
│   ├── config.py
│   ├── neo4j_client.py
│   ├── schema/
│   │   ├── constraints.cypher
│   │   └── ontology.cypher
│   ├── models/
│   │   ├── controlm_rows.py       # pydantic models per CSV
│   │   ├── lineage_events.py      # OL event pydantic shape
│   │   └── iri.py
│   ├── loaders/
│   │   ├── base.py
│   │   ├── data_products.py       # DPROD entry: every target table family is a product
│   │   ├── datasets.py            # DCAT Dataset + Distribution
│   │   ├── folders.py
│   │   ├── jobs.py                # Control-M Jobs + DEPENDS_ON
│   │   ├── shell_scripts.py
│   │   ├── psets.py
│   │   ├── tables.py
│   │   ├── servers.py
│   │   ├── orgs.py                # business apps, teams, owners
│   │   ├── runs.py                # PROV Activities derived from CSV
│   │   ├── lineage_events.py      # OpenLineage event ingest (folder watch)
│   │   ├── dq_arrivals.py         # data file + control file pair tracker
│   │   └── dq_measurements.py     # DQV measurements from TDQ output
│   ├── tdq/
│   │   ├── arrival_pair.py        # joins data file + control file → triggers TDQ
│   │   ├── checks.py              # row-count match, hash match, schema, nulls
│   │   └── dimensions.py          # canonical DQV dimensions/metrics catalog
│   ├── kg/
│   │   └── client.py              # query/expand/add_thought (KGoT seam)
│   ├── cli.py                     # `drydocs ingest`, `verify`, `replay-lineage`
│   └── streamlit_app.py
├── tests/
│   ├── unit/
│   └── integration/
└── docs/
    ├── ontology-mapping.md
    └── tdq-pipeline.md
```

---

## 4. Ontology mapping (data product centric)

The mental model: a **DPROD Data Product** is the user-visible thing. It *exposes* DCAT Datasets through ports. Each Dataset is *produced by* a PROV Activity (a Control-M job run), captured as OpenLineage events. Every run produces DQV Measurements against the Dataset. SWO/ORG explain the **how** and **who**.

### 4.1 The Data Product layer (DPROD + DCAT)

| Concept | IRI | Local label | Notes |
|---|---|---|---|
| Data Product | `dprod:DataProduct` | `:DataProduct` | One per logical product (e.g. "Daily Trades", "Positions Rollup") |
| Input Port | `dprod:InputPort` | `:Port:Input` | Where the product *consumes* from |
| Output Port | `dprod:OutputPort` | `:Port:Output` | Where the product *exposes* via DCAT |
| Dataset | `dcat:Dataset` | `:Dataset` | The conceptual data (e.g. `fact_trades`) |
| Distribution | `dcat:Distribution` | `:Distribution` | Concrete materialization (Athena/Parquet, CSV file) |
| Data Service | `dcat:DataService` | `:DataService` | Athena query endpoint, JDBC URL |
| Catalog | `dcat:Catalog` | `:Catalog` | Container for products/datasets |
| Theme | `dcat:theme` | property | Domain tag (Trades / Risk / Positions) |
| Contact Point | `dcat:contactPoint` | edge → `:Organization` | Owner team |

Every Control-M target table becomes a `:Distribution` of a `:Dataset`, exposed via an `OutputPort` on a `:DataProduct`.

### 4.2 Provenance layer (PROV-O / PROV-DM)

| Concept | IRI | Local label |
|---|---|---|
| Entity | `prov:Entity` | base label on Datasets, Distributions, files |
| Activity | `prov:Activity` | `:Activity` on every Job Run, TDQ Check, Pipeline Run |
| Agent | `prov:Agent` | `:Agent` on schedulers, services, humans |
| `prov:wasGeneratedBy` | predicate | `:WAS_GENERATED_BY` |
| `prov:used` | predicate | `:USED` |
| `prov:wasInformedBy` | predicate | `:WAS_INFORMED_BY` (Control-M "Dependent On") |
| `prov:wasAttributedTo` | predicate | `:WAS_ATTRIBUTED_TO` → `:Organization` |
| `prov:wasAssociatedWith` | predicate | `:WAS_ASSOCIATED_WITH` → scheduler / human |
| `prov:wasDerivedFrom` | predicate | `:WAS_DERIVED_FROM` (Dataset-to-Dataset) |

The PROV layer is the **canonical, time-agnostic** record. OpenLineage events (next section) are projected into this.

### 4.3 Runtime lineage (OpenLineage)

OpenLineage is event-shaped, not class-shaped. We model it as:

| OL concept | Local label | Maps to |
|---|---|---|
| Run | `:LineageRun {run_id}` | PROV Activity (one per OL run) |
| Job | `:LineageJob {namespace, name}` | links to `:Software` (the runner) |
| Dataset | `:LineageDataset {namespace, name}` | reconciled to `:Dataset` / `:Distribution` |
| Run Facet | property bag on `:LineageRun` | preserved as JSON for replay |
| Dataset Facet | property bag on link | schema, dataSource, columnLineage |
| Quality Facet | `dataQualityMetrics` | becomes `:QualityMeasurement` (DQV) |

Pattern: OL events land in `data/lineage/`, the ingester emits/updates `:LineageRun` + reconciles datasets, **and** projects PROV edges (`:USED`, `:WAS_GENERATED_BY`) onto the canonical `:Dataset` graph. OL is the source-of-truth for run-level facts; PROV is the integrated view.

### 4.4 Data Quality (DQV) — the TDQ pipeline

You called out the specific TDQ flow: a Control-M job emits **two artifacts** — a *data file* and a *control file* — and TDQ runs after both arrive. Modeled explicitly:

| Concept | IRI | Local label |
|---|---|---|
| Quality Dimension | `dqv:Dimension` | `:Dimension` (Completeness, Accuracy, Consistency, Timeliness, Integrity) |
| Quality Metric | `dqv:Metric` | `:Metric` (rowcount_match, hash_match, schema_conformance, null_rate, freshness_sla) |
| Quality Measurement | `dqv:QualityMeasurement` | `:QualityMeasurement` |
| Has Quality | `dqv:hasQualityMeasurement` | `:HAS_QUALITY` |
| Computed On | `dqv:computedOn` | `:COMPUTED_ON` → Dataset |
| Is Measurement Of | `dqv:isMeasurementOf` | `:IS_MEASUREMENT_OF` → Metric |

The **arrival pair** — data file + control file — is modeled as:

```
(:File:DataFile {arrived_at})  -[:PAIR_OF]->  (:File:ControlFile {arrived_at})
                  \                                          /
                   v                                        v
                  (:Activity:TDQCheck {started_at, status, run_id})
                          |  prov:used both files
                          v
                  (:QualityMeasurement)+  -[:HAS_QUALITY]-  (:Dataset)
```

A `TDQCheck` is a `prov:Activity` and emits one or more `:QualityMeasurement`s. The `:Dataset` (and its current `:Distribution`) is only marked **certified** if all required-dimension measurements pass. Failures generate `:HAS_RISK → :RiskAnnotation` so they surface in the Streamlit Risks page.

The TDQ check itself is also represented as an OpenLineage `:LineageRun` (job namespace `tdq.controlm`, name = `<dataset>__tdq`) for consistent run-event handling.

### 4.5 Diagram component → ontology (consolidated)

Reading from your attached Control-M diagram, every element gets typed:

| Diagram component | Primary class | Secondary | Notes |
|---|---|---|---|
| Business APP | `org:Organization` | `dcat:contactPoint` | Owner of one or more `:DataProduct`s |
| Control-M Scheduler | `swo:software` + `prov:SoftwareAgent` | — | The Agent on `wasAssociatedWith` |
| Control-M Server (P12/P32) | `swo:Platform` | — | `swo:is_executed_in` target |
| Control-M Folder | `prov:Collection` | local `:JobFolder` | Container of jobs |
| Control-M Job | `prov:Activity` | local `:ControlMJob` | One per scheduled job; runs become `:LineageRun` |
| ctlm Dependency ("Dependent On") | `prov:wasInformedBy` | — | Job-to-job edge |
| Linux Shell Script | `swo:software` (Shell-encoded) | — | `:CALLS` from Job |
| Ab Initio Graph (.pset) | `swo:software` + `obi:OBI_0200000` | — | `swo:implements → :DataTransformation` |
| `.pset` parameter set | local `:Config:PSet` | — | `:CONFIGURES → AbInitioGraph` |
| Source Tables | `dcat:Dataset` (consumed) | `prov:Entity` | Surface via `:Port:Input` |
| Target Tables | `dcat:Dataset` + `dcat:Distribution` | `prov:Entity` | Output of a `:DataProduct` |
| Table attributes (TABLE_NM, DATABASE_NM, SCHEMA) | `dcat:Distribution` properties | — | Scalars |
| **Data file (arrival)** | `prov:Entity` + local `:File:DataFile` | — | Half of TDQ pair |
| **Control file (arrival)** | `prov:Entity` + local `:File:ControlFile` | — | Half of TDQ pair |
| **TDQ Check** | `prov:Activity` + local `:Activity:TDQCheck` | `:LineageRun` | Yields `dqv:QualityMeasurement`s |
| PROD / DR Server | `swo:Platform` | local `:Platform:DataServer` | DR `:HOSTS_REPLICA_OF` PROD |
| Load Balancer (manual MVP) | local `:Infra:LoadBalancer` | — | `:USES_INFRA` |
| Variable resolution / naming notes | properties + `:HAS_RISK` annotations | — | Surfaces in Risks page |

---

## 5. Graph schema

Constraints:

```cypher
CREATE CONSTRAINT ontology_iri    IF NOT EXISTS FOR (n:OntologyTerm)        REQUIRE n.iri IS UNIQUE;
CREATE CONSTRAINT asset_id        IF NOT EXISTS FOR (a:Asset)               REQUIRE a.id  IS UNIQUE;
CREATE CONSTRAINT dataproduct_id  IF NOT EXISTS FOR (p:DataProduct)         REQUIRE p.id  IS UNIQUE;
CREATE CONSTRAINT dataset_iri     IF NOT EXISTS FOR (d:Dataset)             REQUIRE d.iri IS UNIQUE;
CREATE CONSTRAINT distribution_id IF NOT EXISTS FOR (x:Distribution)        REQUIRE x.id  IS UNIQUE;
CREATE CONSTRAINT lineagerun_id   IF NOT EXISTS FOR (r:LineageRun)          REQUIRE r.run_id IS UNIQUE;
CREATE CONSTRAINT measurement_id  IF NOT EXISTS FOR (m:QualityMeasurement)  REQUIRE m.id IS UNIQUE;
CREATE INDEX     job_name         IF NOT EXISTS FOR (j:ControlMJob)         ON  (j.ctlm_job_name);
CREATE INDEX     table_qualified  IF NOT EXISTS FOR (t:Distribution)        ON  (t.database_nm, t.schema_nm, t.table_nm);
CREATE INDEX     file_arrival     IF NOT EXISTS FOR (f:File)                ON  (f.arrived_at);
```

Relationship vocabulary, **partitioned by ontology** (never collapse):

```
DPROD   :HAS_INPUT_PORT  :HAS_OUTPUT_PORT  :EXPOSES_DATASET  :HAS_AGREEMENT
DCAT    :HAS_DISTRIBUTION  :ACCESSED_VIA  :IN_CATALOG  :CONFORMS_TO
PROV    :USED  :WAS_GENERATED_BY  :WAS_ATTRIBUTED_TO  :WAS_ASSOCIATED_WITH
        :WAS_INFORMED_BY  :WAS_DERIVED_FROM  :ACTED_ON_BEHALF_OF
OL      :HAS_LINEAGE_RUN  :LINEAGE_INPUT  :LINEAGE_OUTPUT  :HAS_FACET
DQV     :HAS_QUALITY  :COMPUTED_ON  :IS_MEASUREMENT_OF  :IN_DIMENSION
SWO     :IS_EXECUTED_IN  :IS_ENCODED_IN  :IMPLEMENTS  :USES_PLATFORM
ORG     :HAS_UNIT  :HAS_MEMBER  :HEADS  :REPORTS_TO
LOCAL   :CALLS  :CONFIGURES  :DEPENDS_ON  :SCHEDULED_BY  :USES_INFRA
        :HOSTS_REPLICA_OF  :HAS_RISK  :PAIR_OF
META    :INSTANCE_OF  :SUBCLASS_OF  :IN_PHASE  :SOURCED_FROM
```

Every edge carries `{source: 'csv'|'lineage'|'tdq'|'agent'|'human', loader: 'jobs.v1', run_id: …}` so we can later distinguish CSV-derived facts from agent-derived ones.

---

## 6. Loader architecture

Two ingestion paths converge on the same graph:

**Path A — Control-M CSV (structural facts, "what exists")**
1. Discover `data/raw/*.csv` by filename prefix → matching loader.
2. pandas → pydantic row models. Bad rows route to `data/raw/_rejects/`.
3. UNWIND batched MERGE (default 1000); properties via `SET n += $props`.
4. Loader run wrapped in a `:JobRun` (PROV Activity) with `source='csv'`.

**Path B — OpenLineage events (runtime facts, "what happened")**
1. Watch `data/lineage/*.json` (or HTTP receiver in phase 2).
2. Validate against OL schema; build `:LineageRun`, link to `:LineageJob`, `:LineageDataset`.
3. Reconcile OL `Dataset {namespace,name}` to existing `:Dataset` / `:Distribution` by deterministic key (`namespace = 'athena'`, `name = '<db>.<schema>.<table>'`).
4. Project canonical PROV edges (`:USED`, `:WAS_GENERATED_BY`) when reconciliation succeeds.
5. Lift `dataQualityMetrics` facets into DQV `:QualityMeasurement` nodes.

**Path C — TDQ (the data-file + control-file pair)**
1. `dq_arrivals.py` watches arrival metadata (CSV row per file: dataset, kind=`data|control`, sha256, row_count, arrived_at).
2. When both halves of a pair are present (matched by `dataset_id` + `business_date`), emit a `:Activity:TDQCheck` and run `tdq/checks.py`.
3. Each check produces a `:QualityMeasurement` linked to the Dataset via `:HAS_QUALITY`, to the Metric via `:IS_MEASUREMENT_OF`, and to the TDQ Activity via `prov:wasGeneratedBy`.
4. Pass/fail rolls up to `:Dataset.certified_for_business_date` and surfaces in Streamlit.

`BaseLoader` interface (sketch):

```
class BaseLoader(Protocol):
    name: str
    csv_glob: str
    row_model: type[BaseModel]
    def cypher(self) -> str: ...
    def to_params(self, row: BaseModel) -> dict: ...
```

CLI:

```
drydocs ingest --source data/raw                 # Path A
drydocs replay-lineage --dir data/lineage        # Path B
drydocs run-tdq --business-date 2026-04-29       # Path C
drydocs verify                                   # assertion suite
```

---

## 7. Ontology seeding

`ontology/seed.cypher` (generated from the `*_terms.py` files) creates `:OntologyTerm` nodes for the **anchor terms we actually use** — not the full ontologies:

- DPROD: ~10 terms (DataProduct, Port, InputPort, OutputPort, Agreement, …).
- DCAT v3: ~15 (Catalog, Dataset, Distribution, DataService, theme, contactPoint, …).
- PROV-O: ~15 (Activity, Entity, Agent, plus the predicates listed in §5).
- OpenLineage: not an OWL ontology but we record canonical class names for reference.
- DQV: ~10 (Metric, Dimension, Measurement, Category, predicates).
- DQV catalog of **standard TDQ metrics** and **dimensions** — seeded as `:Metric` / `:Dimension` nodes (not just term descriptors) so measurements link to them.
- SWO: the SDLC subset already generated (`swo_sdlc_ontology.cypher`) — port directly.
- ORG: ~8 (Organization, OrganizationalUnit, Membership, Role, …).

Backbone edges: `:SUBCLASS_OF`, `:SUB_PROPERTY_OF`. Every term tagged `:IN_PHASE` for the SDLC view from the earlier work.

---

## 8. Streamlit (phase 1)

Pages:

- **Data Products** — list of `:DataProduct`s with owner, datasets exposed, current DQ score, last successful run.
- **Product Detail** — drill into one product: ports, datasets, recent `:LineageRun`s, DQ measurements over time, owners.
- **Lineage** — pick a `:Dataset`, walk `:WAS_GENERATED_BY` / `:USED` (and OL projections) backward and forward.
- **Pipeline Explorer** — Control-M view: Folder → Job → Script → PSet → AbInitioGraph → Dataset.
- **Data Quality Scoreboard** — DQV measurements aggregated by dimension (Completeness / Accuracy / …), by product, by week. Failures highlighted.
- **Arrivals & TDQ** — pair-tracker: which datasets are waiting on a control file, which TDQ checks ran today, pass/fail timeline.
- **Recent Runs** — `:LineageRun` and `:JobRun` timeline.
- **Risks** — every `:HAS_RISK` annotation (unresolved variables, manual GREP debt, failed TDQ).
- **Ontology Coverage** — count of populated instances per anchor term across DPROD/DCAT/PROV/OL/DQV/SWO/ORG, gaps highlighted.

Auth: read-only Neo4j user, separate from loader/agent users. Driver pool reused via `@st.cache_resource`.

---

## 9. KGoT bridge (phase 2 — design hooks today)

`drydocs.kg.client` exposes:

```
query(cypher, **params)
expand(node_id, depth=1, follow: list[str] | None = None)
add_thought(s, p, o, *, agent_id, confidence, evidence)
record_quality(dataset_iri, metric_iri, value, unit, *, agent_id)
```

Rules:
- Agent-authored triples get the `:Thought` label and a `source='agent'` edge property — never auto-promoted.
- All canonical loaders write `prov:wasAttributedTo → :Agent {id: 'drydocs.loader.v1'}` so agent-vs-CSV provenance is queryable.
- The agent talks Cypher; no DSL.

When KGoT wires up, the `Tool` it gets is `kg.client`. That's the only integration surface.

---

## 10. Milestones

1. **M0 — Skeleton** (½ day): Poetry deps, `neo4j_client.py`, constraints, ontology seed (DPROD/DCAT/PROV/DQV/SWO/ORG terms).
2. **M1 — One product, end-to-end** (2 days): one Control-M job → Dataset → Distribution → one TDQ check → DQ Measurement, with sample CSV + integration test.
3. **M2 — All Control-M loaders** (3 days): folders, jobs, scripts, psets, tables, servers, orgs, runs.
4. **M3 — TDQ pipeline** (2 days): arrival pair tracker + canonical metric catalog + measurement projection.
5. **M4 — OpenLineage path** (2 days): event ingester + reconciliation + PROV projection.
6. **M5 — Streamlit** (3 days): all nine pages above.
7. **M6 — KGoT seams** (1 day): `kg.client` wrapper, `:Thought` reserved, agent-id provenance.

---

## 11. Assumptions & open questions

Assumptions (override before M0):
- Control-M extracts are CSV with one concept per file. If the export is one wide table, splay inside loaders.
- Neo4j 5.x via Bolt; auth in `.env`.
- OpenLineage events are *file-shipped JSON* in phase 1 (live HTTP receiver in phase 2).
- Each Control-M target table maps to one `:Dataset` and one initial `:Distribution`.
- TDQ check inputs (data file + control file) are paired by `(dataset_id, business_date)`.

Questions I need answered before M0:
1. **DPROV-O / DPROV-DM** — confirm you mean **PROV-O / PROV-DM** (W3C standards) used as the data-product provenance profile, vs. a specific DPROD-published "DPROV" extension. If the latter, please share a link / spec — I'll update §4.2.
2. CSV schemas — please share one sample of each Control-M extract (or just column lists). The pydantic models depend on this.
3. Neo4j flavor — local Desktop, Aura cloud, on-prem? Affects bootstrap and testcontainers wiring.
4. Two Control-M servers (P12, P32) — separate `:Platform` instances or one logical scheduler with two hosts?
5. Business APP block — flat list of apps, or nested org chart from day one?
6. **TDQ catalog** — which of these dimensions/metrics do you want pre-seeded? Suggested baseline:
   - **Completeness**: `rowcount_match` (data vs control), `null_rate`
   - **Accuracy**: `hash_match` (file hash vs control file claim), `value_range`
   - **Consistency**: `schema_conformance`, `referential_integrity`
   - **Timeliness**: `freshness_sla`, `arrival_latency`
   - **Integrity**: `pkey_uniqueness`, `fkey_validity`
7. Does Control-M emit OpenLineage natively in your stack, or do we synthesize OL events from the CSV ingest in phase 1?
8. Pruning policy — keep all `:LineageRun` / `:JobRun` history forever, or window N days?
