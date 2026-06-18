# Neo4j Schema Meta — Living SDLC Document

<!-- §META -->
```yaml
persona: neo4j-architect
flow: neo4j-schema-meta
skills: neo4j-getting-started-skill, neo4j-modeling-skill, neo4j-cypher-skill
status: DRAFT
version: 0.2
last_updated: 2026-06-18T18:00:00Z
populated_from: persona-neo4j-architect.md §2.1–2.6
diagrams_status: TODO (cron task 2.1–2.4)
traceability_status: TODO (cron task 2.5)
```

## §META — Scope and conventions

**Flow:** Define and maintain the Neo4j graph schema that represents Control-M
scheduling topology, SEAL application attribution, org hierarchy (PAT), and PROV-O
provenance. Provides idempotent incremental MERGE loading from DRYDOCS_STG. Ontology
is PROV-O aligned; relationship types registered in a single vocabulary file.

**Secrets discipline:** schema object names only; no real SIDs, data values,
credentials, org names, or server addresses.

**ID scheme:**
- Requirements: `FR-NS-NNN` (Functional Requirement, Neo4j Schema)
- Use Cases: `UC-NS-NNN`
- Open questions: `OQ-NS-N` (also tracked in persona-neo4j-architect.md §2.6)

**Status values per item:** `ACTIVE` | `PLANNED` | `PARTIAL` | `DEPRECATED`

**Cross-reference:** see `sdlc-oracle-ingestion.md` for the upstream Oracle ingestion
flow that feeds DRYDOCS_STG (the graph's data source).

---

## §FR — Functional Requirements

| ID | Requirement | Priority | Status | Implementation Object | Notes |
|---|---|---|---|---|---|
| FR-NS-001 | Schema SHALL enforce NODE KEY constraints on all composite-identity nodes before any loader executes | P0 | ACTIVE | `drydocs/schema/constraints.cypher` | IF NOT EXISTS guards make DDL idempotent |
| FR-NS-002 | Schema SHALL enforce UNIQUE constraints on all single-property identity nodes | P0 | ACTIVE | `constraints.cypher` | Includes :Application(seal_id), :Employee(employee_id), :JobRun(run_id), etc. |
| FR-NS-003 | Schema SHALL align every active node label to a PROV-O or W3C ORG class via SUBCLASS_OF chain | P0 | ACTIVE | `drydocs/schema/ontology_supplement.cypher`, `m3_ontology_supplement.cypher`, `seal_ontology_supplement.cypher`, `catalog_ontology_supplement.cypher` | All 9 PROV matrix rows declared |
| FR-NS-004 | Schema SHALL maintain a single relationship vocabulary registry; every active relationship type SHALL be registered before use | P0 | ACTIVE | `drydocs/ontology/relationship_vocabulary.yaml` | Drift guard in `tests/test_schema.py` enforces coverage |
| FR-NS-005 | Schema SHALL prohibit generic labels (`:Entity`, `:Node`) and generic relationship types (`:HAS`, `:RELATED_TO`) in the domain model | P0 | ACTIVE | Code review + drift guard | Enforced by convention and test |
| FR-NS-006 | Schema SHALL support idempotent MERGE for all node types: no duplicate nodes created on re-load | P0 | ACTIVE | UNWIND $batch + MERGE pattern in all loaders | Anchored on NODE KEY / UNIQUE constraints |
| FR-NS-007 | Schema SHALL track provenance for every loaded node via `(node)-[:WAS_GENERATED_BY {source:'BMC'}]->(run:JobRun)` | P0 | ACTIVE | All M3 loaders | One :JobRun node per loader execution; incremental runs produce low-degree :JobRun nodes |
| FR-NS-008 | Schema SHALL support per-job stale edge cleanup: delete condition and invocation edges for changed jobs before re-asserting the current edge set | P1 | PLANNED | `drydocs/loaders/cypher/stale_edge_cleanup.cypher` (new file needed) | Without this, removed conditions persist as phantom edges after incremental runs |
| FR-NS-009 | Schema SHALL store all date/timestamp properties as Neo4j temporal types using `datetime(row.field)` wrapping in Cypher | P1 | PLANNED | All M3 loader cypher files (fix needed) | Current state: raw strings break Neo4j temporal operators |
| FR-NS-010 | Schema SHALL support idempotent label migration via guarded migration blocks (MATCH n:OldLabel WHERE NOT n:NewLabel SET n:NewLabel REMOVE n:OldLabel) | P1 | PARTIAL | `constraints.cypher` migration blocks | :JobFolder→:ControlMFolder migration block needed |
| FR-NS-011 | Schema SHALL use `:ControlMFolder` as the canonical folder label; `:JobFolder` is the legacy label during migration only | P1 | PARTIAL | `constraints.cypher`, `controlm_folders.cypher` | Vocabulary says ControlMFolder; constraints/loaders still say JobFolder — half-applied |
| FR-NS-012 | Schema SHALL use `SCHEDULED_ON` (not `RUNS_ON`) as the folder→server relationship type | P0 | PARTIAL | `controlm_folders.cypher` | Vocabulary renamed RUNS_ON → SCHEDULED_ON; loader still writes RUNS_ON — fix needed before incremental ships |
| FR-NS-013 | Schema SHALL load SEAL application attribution via `(j:ControlMJob)-[:WAS_ASSOCIATED_WITH {role:'seal_app_ref'}]->(a:Application)` from `STG_APP_FACT` | P1 | ACTIVE | SEAL attribution loader | Maps to prov:wasAssociatedWith (Activity → Agent) |
| FR-NS-014 | Raw variable rows SHALL NOT become graph nodes; only semantic extracts (SEMANTIC_FACT, FLOW_REF subsets via STG_APP_FACT) enter the graph | P1 | ACTIVE | Design decision — no :ControlMVariable loader | Prevents 1.1M-node population for data that graph queries don't need |
| FR-NS-015 | Schema SHALL support developer SID attribution via `(j:ControlMJob)-[:WAS_ASSOCIATED_WITH {role:'owner'|'author'|...}]->(e:Employee)` when SID→Employee link is confirmed | P2 | PLANNED | Future job loader extension | Reuses :Employee (not a new :Developer type); SID normalized by `UPPER(REGEXP_REPLACE(sid,'p$',''))` |
| FR-NS-016 | Schema SHALL support periodic age-out cleanup of stale condition edges by `last_run_id` using server-side CALL IN TRANSACTIONS | P2 | PLANNED | Range index on REQUIRES_IN_CONDITION.last_run_id + cleanup Cypher | Fallback strategy (Strategy A) complementing per-job replacement (Strategy B) |
| FR-NS-017 | Incremental :JobRun nodes SHALL be annotated with load metadata: `load_mode`, `hwm_version_serial`, `rows_applied` from STG_LOAD_CONTROL | P2 | PLANNED | IncrementalControlMLoader Python code | Graph-side visibility of Oracle HWM state |
| FR-NS-018 | AreaProduct node SHALL have a SUBCLASS_OF wiring to prov:Entity to enable future PROV-O edge mapping | P3 | PLANNED | `catalog_ontology_supplement.cypher` | Currently deferred as "standalone local entity"; blocks future PROV mapping |

---

## §UC — Use Cases

### UC-NS-001: Full Graph Load (Baseline)

| Field | Value |
|---|---|
| Actor | Data Engineer / CLI (`drydocs` command) |
| Goal | Load all Control-M jobs, folders, conditions, and SEAL applications into Neo4j from DRYDOCS_STG |
| Preconditions | Constraints applied; DRYDOCS_STG populated (UC-OI-001 complete); `.env` configured |
| FR linkage | FR-NS-001, FR-NS-002, FR-NS-006, FR-NS-007, FR-NS-013, FR-NS-014 |
| Status | ACTIVE |

**Steps (dependency-ordered):**
1. Apply `constraints.cypher` (idempotent).
2. Apply ontology supplement cypher files.
3. Run `controlm_folders.cypher` (folders + servers).
4. Run `controlm_jobs.cypher` (jobs; depends on folders).
5. Run `controlm_conditions_in.cypher` / `controlm_conditions_out.cypher`.
6. Run SEAL attribution loader (depends on jobs + applications).
7. Log `:JobRun` node with `WAS_GENERATED_BY` on all loaded nodes.

**Postconditions:** Graph contains full current snapshot; all nodes have provenance edges to the `:JobRun` created in this run.

**Exceptions:**
- Constraint apply fails → stop; fix schema before loading.
- Loader error on a batch → `BaseLoader._flush` raises; run is aborted; re-run is safe (MERGE is idempotent).

---

### UC-NS-002: Incremental Graph Update

| Field | Value |
|---|---|
| Actor | Scheduled job / `IncrementalControlMLoader` |
| Goal | Merge only changed jobs into graph; clean up stale edges; preserve graph consistency |
| Preconditions | Baseline graph exists; `STG_LOAD_CONTROL` has HWM; `stale_edge_cleanup.cypher` deployed |
| FR linkage | FR-NS-006, FR-NS-007, FR-NS-008, FR-NS-017 |
| Status | PLANNED |

**Steps (per batch of changed jobs):**
1. Read changed job keys from `incremental_changed_jobs.sql`.
2. Execute `stale_edge_cleanup.cypher` (OPTIONAL MATCH + DELETE for condition/invocation edges).
3. Execute `controlm_jobs.cypher` (UNWIND $batch MERGE — only changed rows).
4. Execute `controlm_conditions_in.cypher` / `_out.cypher` (re-assert current edges).
5. Annotate `:JobRun` with `load_mode='INCREMENTAL'`, `hwm_version_serial`, `rows_applied`.

**Postconditions:** Graph reflects the delta; stale condition edges removed; `:JobRun` records load provenance.

**Exceptions:**
- Stale edge cleanup fails → do not proceed to node upsert; abort batch; retry from last committed HWM.
- Node upsert fails mid-batch → no HWM advance; safe to restart.

---

### UC-NS-003: Schema Constraint Application

| Field | Value |
|---|---|
| Actor | DBA / CI pipeline |
| Goal | Apply or re-apply all constraints and indexes to the Neo4j instance idempotently |
| Preconditions | Neo4j running; credentials in `.env` |
| FR linkage | FR-NS-001, FR-NS-002 |
| Status | ACTIVE |

**Steps:**
1. Execute `constraints.cypher` — all statements are `IF NOT EXISTS` guarded.
2. No manual cleanup needed; re-running is always safe.

**Postconditions:** All NODE KEY and UNIQUE constraints present; no duplicates can be created by MERGE.

---

### UC-NS-004: Label Migration (:JobFolder → :ControlMFolder)

| Field | Value |
|---|---|
| Actor | DBA |
| Goal | Complete the rename of :JobFolder to :ControlMFolder for all existing nodes |
| Preconditions | Migration Cypher block added to `constraints.cypher`; loaders still emit both labels (`:JobFolder:Collection`) |
| FR linkage | FR-NS-010, FR-NS-011 |
| Status | PLANNED |

**Steps:**
1. Run migration block: `MATCH (n:JobFolder) WHERE NOT n:ControlMFolder SET n:ControlMFolder REMOVE n:JobFolder`.
2. Drop old constraint: `DROP CONSTRAINT folder_id IF EXISTS` (keyed on :JobFolder).
3. Create new constraint: `CREATE CONSTRAINT folder_id IF NOT EXISTS FOR (f:ControlMFolder) REQUIRE f.folder_id IS UNIQUE`.
4. Update loaders to emit `:ControlMFolder:Collection` only (remove dual-label emit).

**Postconditions:** No `:JobFolder`-only nodes remain; `:ControlMFolder` constraint active; loaders emit canonical label.

---

### UC-NS-005: SEAL Application Attribution Query

| Field | Value |
|---|---|
| Actor | Analyst / Application |
| Goal | Find all Control-M jobs attributed to a given SEAL application |
| Preconditions | SEAL attribution loader has run; `WAS_ASSOCIATED_WITH` edges exist |
| FR linkage | FR-NS-013 |
| Status | ACTIVE |

**Query pattern:**
```cypher
MATCH (a:Application {seal_id: $seal_id})<-[:WAS_ASSOCIATED_WITH]-(j:ControlMJob)
RETURN j.folder_id, j.job_id, j.job_name, j.data_center
ORDER BY j.folder_id, j.job_id
```

---

### UC-NS-006: Ontology Term Browser Query

| Field | Value |
|---|---|
| Actor | Developer / Analyst |
| Goal | Traverse the ontology class hierarchy to understand node/edge semantics |
| Preconditions | Ontology supplement cypher files applied |
| FR linkage | FR-NS-003 |
| Status | ACTIVE |

**Query pattern:**
```cypher
MATCH (t:OntologyTerm:LocalClass)-[:SUBCLASS_OF*1..3]->(p:OntologyTerm)
RETURN t.label, t.iri, p.label, p.iri
ORDER BY t.label
```

---

### UC-NS-007: Stale Edge Age-Out Cleanup

| Field | Value |
|---|---|
| Actor | Scheduled job / DBA |
| Goal | Remove condition edges not re-asserted in recent incremental runs (age-out / Strategy A fallback) |
| Preconditions | Range index on `REQUIRES_IN_CONDITION.last_run_id` exists; cutoff `run_id` determined |
| FR linkage | FR-NS-016 |
| Status | PLANNED |

**Query pattern:**
```cypher
MATCH ()-[r:REQUIRES_IN_CONDITION|EMITS_OUT_CONDITION]->()
WHERE r.last_run_id < $cutoff_run_id
CALL (r) {
  DELETE r
} IN TRANSACTIONS OF 10000 ROWS ON ERROR CONTINUE REPORT STATUS AS s
RETURN count(*), s.committed
```

---

## §DEP — Dependencies

| System | Role | Interface | Access Pattern | Notes |
|---|---|---|---|---|
| **DRYDOCS_STG** | Upstream data source | `JOB_DETAILED_VIEW`, `STG_APP_FACT` | Read via OracleAdapter; same Oracle DB connection | Feed for all M3 loaders |
| **Neo4j Instance** | Graph database target | Python `neo4j` driver; `NEO4J_URI`/`USERNAME`/`PASSWORD`/`DATABASE` in `.env` | Write/read; UNWIND batches | Existing 5.x instance |
| **neo4j_client.py** | Driver session management | `drydocs/neo4j_client.py` | Python object; wraps driver | Internal DryDocs framework |
| **BaseLoader** | Batch flush abstraction | `drydocs/loaders/` Python base class | `_flush(batch_size=1000)` pattern | Reused by all loaders including incremental |
| **constraints.cypher** | Schema DDL | Cypher; run before loaders | Idempotent; `IF NOT EXISTS` guards | Applied once per environment setup; re-runnable |
| **relationship_vocabulary.yaml** | Relationship type registry | YAML; `drydocs/ontology/` | Parsed by `test_schema.py` drift guard | Single source of truth for edge types |
| **SEAL** (via staging) | Application metadata | Pre-enriched in `STG_APP_FACT` | Indirect — SEAL data enters via Oracle ingestion flow | No direct Neo4j→SEAL connection |
| **PAT** (via staging) | Org hierarchy | Pre-loaded `:AreaProduct`, `:DevTeam` etc. | Indirect | Same pattern as SEAL |
| **APOC** | Optional: `apoc.periodic.iterate` | Neo4j APOC plugin | Used for age-out cleanup if available | **OQ-NS-3: APOC availability unconfirmed** |

---

## §C1 — C1 Context Diagram

<!-- TODO: cron task 2.1 — generate Mermaid flowchart diagram -->
<!-- Diagram should show: DRYDOCS_STG (upstream) → Neo4j Client → Schema Layer →
     Loader Layer → Neo4j Instance → Consumers (CLI, query library).
     Verify file paths against drydocs/schema/ and drydocs/loaders/cypher/ first. -->

```
[DIAGRAM PENDING — cron task 2.1]

Upstream input:
  - DRYDOCS_STG (Oracle; JOB_DETAILED_VIEW, STG_APP_FACT)

System boundary: DryDocs Neo4j Schema Meta
  - Schema Layer (constraints.cypher, ontology supplement cypher files)
  - Loader Layer (drydocs/loaders/cypher/ + Python wrappers)
  - Neo4j Client (drydocs/neo4j_client.py)

Graph target:
  - Neo4j Instance (node labels, relationships, ontology backbone)

Consumers:
  - drydocs CLI (cli.py)
  - Query library (queries/ — planned)
```

---

## §DES — Design Diagrams

### §DES/schema — Graph Node-Relationship Schema

<!-- TODO: cron task 2.2 — Mermaid graph showing all active node labels, NODE KEY
     properties, and relationship matrix with PROV-O class annotation per node.
     Source: constraints.cypher + relationship_vocabulary.yaml -->

```
[DIAGRAM PENDING — cron task 2.2]

Node labels to include (with idempotency anchor):
  :ControlMFolder   folder_id UNIQUE           [:Collection]
  :ControlMJob      NODE KEY (folder_id,job_id) [:Activity]
  :Condition        NODE KEY (folder_id,name)   [:Entity]
  :ControlMServer   name UNIQUE                 [:Entity]
  :Application      seal_id UNIQUE              [:Agent]
  :Employee         employee_id UNIQUE          [:Agent]
  :AreaProduct      area_product_id UNIQUE      [:Entity]
  :DevTeam          team_id UNIQUE              [:Agent]
  :JobRun           run_id UNIQUE               [:Activity]
  :Membership       (intermediate n-ary)        [:org:Membership]
  :Role             (via Membership)             [:org:Role]
  :OntologyTerm     iri UNIQUE                  [:OntologyTerm]
  :Port             NODE KEY (parent_seal_id,kind) [:Entity]

Relationship types (from vocabulary):
  CONTAINS_JOB         ControlMFolder → ControlMJob
  SCHEDULED_ON         ControlMFolder → ControlMServer  (was RUNS_ON — migration needed)
  REQUIRES_IN_CONDITION ControlMJob → Condition
  EMITS_OUT_CONDITION  ControlMJob → Condition
  WAS_GENERATED_BY     (any node) → JobRun
  WAS_ASSOCIATED_WITH  ControlMJob → Application {role:seal_app_ref}
                       ControlMJob → Employee {role:owner|author|...} (planned)
  HAS_MEMBERSHIP       Application → Membership
  OF_ROLE              Membership → Role
  HELD_BY              Membership → Employee
  SUPPORTS             DevTeam → AreaProduct
  SUBCLASS_OF          OntologyTerm → OntologyTerm
```

### §DES/ontology — Ontology Class Hierarchy

<!-- TODO: cron task 2.3 — Mermaid graph showing SUBCLASS_OF chains from local
     classes to PROV-O / W3C ORG parent classes.
     Source: ontology_supplement.cypher, m3_ontology_supplement.cypher,
             seal_ontology_supplement.cypher, catalog_ontology_supplement.cypher -->

```
[DIAGRAM PENDING — cron task 2.3]

PROV-O roots: prov:Activity, prov:Entity, prov:Agent, prov:Collection
W3C ORG roots: org:Membership, org:Role

Local classes and their PROV-O parents:
  dd:ControlMJob       SUBCLASS_OF prov:Activity
  dd:ControlMFolder    SUBCLASS_OF prov:Collection
  dd:Condition         SUBCLASS_OF prov:Entity
  dd:ControlMServer    SUBCLASS_OF prov:Entity
  dd:JobRun            SUBCLASS_OF prov:Activity
  dd:Application       SUBCLASS_OF prov:Agent
  dd:Employee          SUBCLASS_OF prov:Agent
  dd:DevTeam           SUBCLASS_OF prov:Agent
  dd:AreaProduct       SUBCLASS_OF prov:Entity  (wiring PLANNED — FR-NS-018)
  dd:Membership        SUBCLASS_OF org:Membership
  dd:Role              SUBCLASS_OF org:Role
```

### §DES/incremental — Incremental Graph Load Sequence

<!-- TODO: cron task 2.4 — Mermaid sequenceDiagram for incremental graph load
     Participants: STG_LOAD_CONTROL, IncrementalControlMLoader, Neo4j
     Sequence: read HWM → get changed keys → stale edge cleanup → node upsert →
               condition re-assert → JobRun annotation
     Reference: stale_edge_cleanup.cypher (new), controlm_jobs.cypher,
                controlm_conditions_in.cypher -->

```
[DIAGRAM PENDING — cron task 2.4]

Key steps per batch:
  1. stale_edge_cleanup.cypher: UNWIND $changed_keys → OPTIONAL MATCH condition edges → DELETE r
  2. controlm_jobs.cypher: UNWIND $batch → MERGE ControlMJob → SET properties
  3. controlm_conditions_in/out.cypher: UNWIND $batch → MERGE Condition → MERGE edge
  4. :JobRun annotation: SET hwm_version_serial, load_mode, rows_applied
  5. Oracle side: advance STG_LOAD_CONTROL HWM (COMMIT)
```

---

## §TM — Traceability Matrix

<!-- TODO: cron task 2.5 — generate FR→UC→implementation file mapping -->
```
[TRACEABILITY PENDING — cron task 2.5]

For each FR-NS-*: map to UC-NS-*, implementation file (cypher/python/yaml),
status, blocking OQ, and gap vs. actual code
```

---

## §SRC — Source Views and Schema Files

### Schema definition files (Neo4j DDL layer)

| File | Role | Status |
|---|---|---|
| `drydocs/schema/constraints.cypher` | NODE KEY + UNIQUE constraints; migration blocks | ACTIVE; :ControlMFolder migration block NEEDED |
| `drydocs/schema/ontology_supplement.cypher` | Base PROV-O local class and relationship declarations | ACTIVE |
| `drydocs/schema/m3_ontology_supplement.cypher` | Control-M domain ontology terms | ACTIVE |
| `drydocs/schema/seal_ontology_supplement.cypher` | SEAL / people domain ontology | ACTIVE |
| `drydocs/schema/catalog_ontology_supplement.cypher` | Org / catalog ontology (AreaProduct, DevTeam) | ACTIVE |
| `drydocs/ontology/relationship_vocabulary.yaml` | Single registry of all relationship types + PROV-O mapping | ACTIVE; drift guard in test_schema.py |

### Cypher loader files (load layer)

| File | Role | Status | Issues |
|---|---|---|---|
| `drydocs/loaders/cypher/controlm_folders.cypher` | :ControlMFolder + :ControlMServer MERGE; SCHEDULED_ON edge | ACTIVE | Writes `RUNS_ON` — must change to `SCHEDULED_ON` (P0) |
| `drydocs/loaders/cypher/controlm_jobs.cypher` | :ControlMJob MERGE; CONTAINS_JOB; WAS_GENERATED_BY | ACTIVE | Date strings not wrapped with `datetime()` (P0) |
| `drydocs/loaders/cypher/controlm_conditions_in.cypher` | :Condition MERGE; REQUIRES_IN_CONDITION edge | ACTIVE | Correct pattern; stale-edge cleanup precedes this |
| `drydocs/loaders/cypher/controlm_conditions_out.cypher` | :Condition MERGE; EMITS_OUT_CONDITION edge | ACTIVE | Same as above |
| `drydocs/loaders/cypher/stale_edge_cleanup.cypher` | Delete condition/invocation edges before re-assert | **NEEDED** | New file required for incremental (FR-NS-008) |
| `drydocs/loaders/controlm_folders.py` | Python wrapper for folders loader | ACTIVE | — |
| `drydocs/loaders/controlm_jobs.py` | Python wrapper for jobs loader | ACTIVE | — |
| `drydocs/loaders/incremental_controlm.py` | IncrementalControlMLoader orchestrator | **PLANNED** | New file (FR-NS-008, FR-NS-017) |

### Upstream staging objects read by graph loaders

| Staging object | Read by | Purpose |
|---|---|---|
| `JOB_DETAILED_VIEW` | `controlm_jobs.py` | Full job extract; developer SID normalization inline |
| `STG_APP_FACT` | SEAL attribution loader | SEAL application-attributed semantic variable facts |
| `STG_LOAD_CONTROL` | `IncrementalControlMLoader` (planned) | HWM for changed-job extract |

---

## §OQ — Open Questions

| ID | Question | Blocks | Source |
|---|---|---|---|
| OQ-NS-1 | Should `RUNS_ON`→`SCHEDULED_ON` migration run before or at the same time as incremental loader deploy? | FR-NS-012 deploy order | persona-neo4j-architect.md §2.6 D5 |
| OQ-NS-2 | Is the full-load `:JobRun` supernode (300K+ `WAS_GENERATED_BY` edges) causing observable query latency in the current environment? | Prioritization of provenance restructuring (FR-NS-007) | persona-neo4j-architect.md §2.6 D7 |
| OQ-NS-3 | Is APOC available on the Neo4j instance? | Age-out cleanup method: `apoc.periodic.iterate` vs native `CALL IN TRANSACTIONS` (FR-NS-016) | persona-neo4j-architect.md §2.6 D6 |
| OQ-NS-4 | Should `m3_constraints_upgrade.cypher` be created or should the stale reference in `controlm_jobs.cypher` comment be removed? | Developer clarity; no functional block | persona-neo4j-architect.md §2.1 gap 2 |

---

## §LOG — Change Log (newest at bottom)

- 2026-06-18T18:00:00Z v0.1 scaffold: §META, §FR (FR-NS-001 to FR-NS-018), §UC (UC-NS-001 to UC-NS-007), §DEP populated from persona-neo4j-architect.md §2.1–2.6. Diagram/TM sections are stubs for cron task 2.1–2.5.
- 2026-06-18T18:00:00Z v0.2 §SRC with schema files + loader files + upstream staging objects added; §OQ section added.
