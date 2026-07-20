# Persona Review — Neo4j Architect / Ontology (Phase 2)

> **STATUS: Superseded (2026-07-01).** This review/plan is complete; its findings were rolled
> into `docs/decisions/` (ADRs), `MODULE_MAP.md`, and `docs/restructure/backlog.yaml`.
> Kept for historical reference.

Reviewer persona: **Neo4j Architect** (via `neo4j-getting-started-skill`,
`neo4j-modeling-skill`, `neo4j-cypher-skill`, `neo4j-import-skill`). Mandate:
review the Phase-1 Oracle DBA staging design from a graph/ontology standpoint;
validate the staging→graph mapping; critique and reconcile with Phase 1.

Architecture-level only — schema object names already in the repo; no real
SIDs, data values, credentials, or org names.

---

## 2.1 First-Time Setup Audit (getting-started-skill stage map)

DryDocs is not a greenfield project — the DB_TARGET is **existing** and most
stages are substantially complete. This section walks each of the 8 getting-
started stages and records what exists vs. what is absent or incomplete.

### Context (Stage 1)

| Variable | DryDocs value |
|---|---|
| `DOMAIN` | Enterprise batch scheduling / Control-M data catalog |
| `USE_CASE` | Job+variable provenance, org→job lineage, incremental graph refresh |
| `DB_TARGET` | `existing` (running Neo4j 5.x instance) |
| `DATA_SOURCE` | `oracle` (psgmgr via `OracleAdapter`; CSV sample mode also supported) |
| `APP_TYPE` | CLI (`drydocs/cli.py`) — notebook/API are planned but absent |
| `EXEC_METHOD` | Python driver (`drydocs/neo4j_client.py`); cypher files in `drydocs/loaders/cypher/` |
| `EXPERIENCE` | Intermediate — PROV-O ontology in place; no MCP integration yet |

### Prerequisites (Stage 0) — status: partial

**What exists:**
- Python project with `neo4j` driver dependency (used by `neo4j_client.py`).
- `drydocs/neo4j_client.py` — driver session management.
- `.gitignore` presumably covers `.env` (needs a confirm-check, not done here).

**What is absent / unverified:**
- No `progress.md` tracking file (the getting-started-skill format); not needed
  for an established project but a `docs/setup.md` runbook for new-environment
  bootstrap would be valuable.
- No documented MCP configuration file (`mcp-claude-code.json` etc.).
- Neo4j `neo4j-mcp` binary availability unverified — not required for loader
  operation but needed if agent-query integration is a goal.
- No `requirements.txt` lockfile at repo root (packages may be in a `pyproject.toml`
  or separate environment file — not checked here).

**Recommendation:** add a `docs/setup.md` (or supplement `git-readme.md`) with
the five-command bootstrap sequence: `pip install`, `neo4j drydocs bootstrap`,
`drydocs apply-m3-supplement`, `apply-seal-supplement`, `apply-catalog-supplement`.
This is the "prerequisites + provision" equivalent for an existing project.

### Provision (Stage 2) — status: assumed complete (existing DB)

`.env` with `NEO4J_URI/USERNAME/PASSWORD/DATABASE` is expected to exist locally
(gitignored). No gap — fast-path: `DB_TARGET=existing`.

### Model (Stage 3) — status: **substantially complete, with gaps**

This is the richest area. What exists:

**Constraints & indexes** (`drydocs/schema/constraints.cypher`):
- `OntologyTerm(iri)` unique — ontology backbone clean.
- `ControlMJob` composite NODE KEY `(folder_id, job_id)` — correct; old versioned
  key is dropped with `DROP CONSTRAINT controlmjob_key IF EXISTS` before recreating.
- `Condition` NODE KEY `(folder_id, name)` — correct.
- `JobFolder(folder_id)` unique — note: label is still `:JobFolder` here; label
  rename to `:ControlMFolder` is in progress (see node quick-reference footnote 7).
- `JobRun(run_id)` unique — provenance backbone correct.
- `Application(seal_id)` unique — SEAL anchor correct.
- `Employee(employee_id)`, `AreaProduct(area_product_id)`, `DevTeam(team_id)` all
  have constraints — org hierarchy anchors correct.
- `Port` NODE KEY `(parent_seal_id, kind)` — two-port pattern enforced.

**Ontology supplements** (`drydocs/schema/`):
- `ontology.cypher` — PROV-O base terms.
- `ontology_supplement.cypher` — base local extensions.
- `m3_ontology_supplement.cypher` — Control-M domain.
- `seal_ontology_supplement.cypher` — SEAL/people domain.
- `catalog_ontology_supplement.cypher` — org/catalog domain.
- `relationship_vocabulary.yaml` — single registry of all active/planned edges;
  drift guard (`test_schema.py`) enforces supplement coverage.

**Relationship matrix** (PROV-O aligned, `RELATIONSHIP_GUIDE.md`):
- All 9 PROV matrix rows declared; domain-specific labels mapped.
- Loaders emit `WAS_GENERATED_BY` → `:JobRun` on every node (provenance correct).
- `CONTAINS_JOB` (JobFolder → ControlMJob), `RUNS_ON` (JobFolder → ControlMServer),
  `REQUIRES_IN_CONDITION`, `EMITS_OUT_CONDITION` all active.

**Model gaps for Phase-1 supplemental staging work:**

1. **`:Developer` / SID→Employee link — not yet in active model.** The node quick
   reference marks `Developer` and `Deployment` as *planned (phase 2)*. The Phase-1
   inline `developer_sid` expression (from the DBA review) will produce a normalized
   SID value, but there is no constraint or loader yet to connect that SID to an
   `:Employee` node. When the `STG_DEV_SID` dimension is eventually promoted to a
   real object, the constraint needs to be:
   ```cypher
   CREATE CONSTRAINT developer_sid IF NOT EXISTS
     FOR (d:Developer) REQUIRE d.developer_sid IS UNIQUE;
   ```
   Until then, the `owner`/`author`/`version_user` properties on `:ControlMJob`
   carry raw SIDs — graph queries that want to attribute jobs to people must do a
   string-match join to `:Employee` rather than traversing an edge.

2. **`m3_constraints_upgrade.cypher` referenced but absent.** The job loader comment
   says "Run `m3_constraints_upgrade.cypher` to lock this on existing graphs" but the
   file does not exist in `drydocs/schema/`. The corrected NODE KEY (`folder_id,
   job_id` without `version_serial`) is in `constraints.cypher` (with the DROP
   guard), so the constraint is correct *for new deployments*. For existing databases
   that still carry the old versioned key, a migration file is needed. This is a
   deployment gap, not a design gap.

3. **`:JobFolder` → `:ControlMFolder` rename in progress.** Supplement and constraints
   still use `:JobFolder`; loaders emit both labels (from the node quick-reference).
   The migration cypher `MATCH (n:JobFolder) SET n:ControlMFolder REMOVE n:JobFolder`
   is documented but not in any file. Needs to land in `constraints.cypher` as a
   one-time migration block (guarded by existence check) or in a dedicated migration
   file.

4. **No constraint file for incremental staging integration.** The Phase-1 staging
   tables (`STG_LOAD_CONTROL`, `STG_SAMPLE_MANIFEST`) have no corresponding graph
   nodes — and they should not (they are Oracle-side metadata). But the graph-side
   equivalent — a watermark property or a provenance `:JobRun` annotation recording
   the HWM — has no schema anchor yet. See 2.3 for the mapping design.

### Load (Stage 4) — status: **working for full-refresh; incremental not yet built**

**What exists (loaders in `drydocs/loaders/`):**
- `controlm_folders.py` → `controlm_folders.cypher` — MERGE `:JobFolder` + `:ControlMServer`.
- `controlm_jobs.py` → `controlm_jobs.cypher` — MERGE `:ControlMJob`, link to folder, emit provenance.
- `controlm_conditions_in.py` / `_out.py` → `MERGE (:Condition)`, link `:REQUIRES_IN_CONDITION` / `:EMITS_OUT_CONDITION`.
- `seal_applications.py`, `seal_contacts.py`, catalog loaders — active.
- `controlm_dependencies_derived.py` — derived condition-chain relationships.
- SQL extracts: `controlm_folders.sql`, `controlm_jobs.sql`, `controlm_conditions_in/out.sql`.

**What is absent (gaps relevant to Phase-1 staging work):**
- **No `:ControlMVariable` graph node or loader.** `controlm_variables.sql` and
  `controlm_variables_scenarios.sql` exist for staging, but variables flow into
  `STG_VARIABLE` (Oracle) and do not yet have a graph representation. Whether
  variables should become graph nodes (`:Variable {name, value}`) or remain staging-
  only is an open design question (see 2.5 for the recommendation).
- **No `reset.cypher` / wipe-and-reload script.** Good practice for dev environments;
  needed once incremental loads go live so a full baseline rebuild is one command.
- **Incremental load** — the full-refresh pattern is the only implemented mode. The
  Phase-1 `STG_LOAD_CONTROL` HWM feeds the changed-job extract on the Oracle side;
  the graph-side equivalent (load only changed nodes) is designed in 2.4.

### Explore (Stage 5) — status: not documented

No `docs/setup.md`, `queries/` directory, or browser URL guide exists. A starter
Cypher block for visual exploration (job→folder→server subgraph, SEAL app attribution)
should be added to a `queries/` directory. Not a blocker for the incremental design.

### Query (Stage 6) — status: **absent as a formal library**

No `queries/queries.cypher` file exists. Individual queries live in test files and
the CLI verify commands. A formal library is a gap for ongoing use. Deferred — not
blocking Phase-2 architectural work.

### Build (Stage 7) — status: CLI only

The `drydocs` CLI is the primary artifact. No notebook, Streamlit app, or FastAPI
layer exists. No MCP configuration. Deferred.

---

**Task 2.1 summary:** The model (Stage 3) and load-framework (Stage 4) are well-
developed. Critical gaps for the Phase-1 incremental work are: (a) the
`m3_constraints_upgrade.cypher` migration file, (b) the `:JobFolder`→`:ControlMFolder`
rename migration, (c) no graph representation of variables (design decision pending),
and (d) no incremental graph loader. These are addressed in 2.3–2.4.

→ Next: **2.2 Ontology review** (neo4j-modeling-skill).

---

## 2.2 Ontology Review (modeling-skill Schema Assessment)

Source files reviewed: `constraints.cypher`, `ontology_supplement.cypher`,
`seal_ontology_supplement.cypher`, `catalog_ontology_supplement.cypher`,
`relationship_vocabulary.yaml`, and the M3 loaders.

### Schema Assessment

#### Compliant — what is correct

- **NODE KEYs for composite-key nodes:** `ControlMJob(folder_id, job_id)` and
  `Condition(folder_id, name)` are correctly compound; `DROP … IF EXISTS` guards the
  migration from any older versioned key. No duplicate nodes can be created on MERGE.
- **PROV-O classification is thorough:** every active node label is mapped to a
  PROV-O or W3C class (Activity, Entity, Collection, Agent, org:Membership, org:Role)
  via `SUBCLASS_OF` chains in the supplements. The vocabulary audit already corrected
  `prov:Membership` → `org:Membership`.
- **No generic labels or relationship types:** no `:Entity`, `:Node`, `:HAS`, or
  `:RELATED_TO` in the domain model. Domain-specific labels throughout.
- **Relationship direction encodes semantic meaning** throughout: `CONTAINS_JOB`
  (folder → job), `REQUIRES_IN_CONDITION` (job → condition), `WAS_GENERATED_BY`
  (node → run), `EMITS_OUT_CONDITION` (job → condition), `ACTED_ON_BEHALF_OF`
  (downstream direction). All correct.
- **N-ary Membership correctly intermediate-noded:** `(:Application)-[:HAS_MEMBERSHIP]->
  (:Membership)-[:OF_ROLE]->(:Role)` and `(:Membership)-[:HELD_BY]->(:Employee)`.
  Supports temporal `valid_from`/`valid_to` on the `:Membership` node. Matches the
  W3C ORG pattern exactly.
- **`IF NOT EXISTS` guards on all DDL.** All constraints and indexes are idempotent.
- **Low-cardinality booleans stored as properties**, not node types: `active`,
  `is_current_version`, `cyclic` on `:ControlMJob`. Correct.
- **Constraint-first order documented**: loaders filter `IS_CURRENT_VERSION='1'`
  upstream so one canonical node per logical job lands in the graph. Version audit
  via `version_serial` property only.

---

#### Issues Found

##### Issue 1 — `:JobFolder` vs `:ControlMFolder` label drift — Severity: **WARNING**

- **Current:** `relationship_vocabulary.yaml` declares the node label as
  `ControlMFolder`; `constraints.cypher` constrains `JobFolder(folder_id)`; the
  supplement's IRI is `#JobFolder`; the loader emits `:JobFolder:Collection`.
- **Problem:** The rename is half-applied. The vocabulary (the declared canonical
  truth) says `ControlMFolder`, but the three operational artefacts (constraint,
  supplement, loader) still use `JobFolder`. Queries that match `:ControlMFolder`
  will miss all existing nodes until the rename migration runs. The node quick-
  reference correctly documents the migration Cypher but it lives only in the doc.
- **Fix — two steps, both idempotent:**
  1. Add a migration block to `constraints.cypher` (or a new `migrations.cypher`):
     ```cypher
     // Rename :JobFolder → :ControlMFolder (idempotent: no-op if already done)
     MATCH (n:JobFolder) WHERE NOT n:ControlMFolder
     SET n:ControlMFolder REMOVE n:JobFolder;
     ```
  2. After the migration, update the constraint:
     ```cypher
     DROP CONSTRAINT folder_id IF EXISTS;
     CREATE CONSTRAINT folder_id IF NOT EXISTS
       FOR (f:ControlMFolder) REQUIRE f.folder_id IS UNIQUE;
     ```
  Until these run, keep the loader emitting `:JobFolder:Collection` (dual label) so
  existing queries don't break.

---

##### Issue 2 — `RUNS_ON` vs `SCHEDULED_ON` loader/supplement skew — Severity: **WARNING**

- **Current:** `relationship_vocabulary.yaml` renamed the relationship
  `RUNS_ON → SCHEDULED_ON` and reassigned `RUNS_ON` to a future execution-host
  edge. `ontology_supplement.cypher` declares the `LocalRelationship` as
  `SCHEDULED_ON`. However, `controlm_folders.cypher` still writes
  `MERGE (f)-[r:RUNS_ON]->(srv)`.
- **Problem:** The graph contains `RUNS_ON` edges (from every past load), but the
  ontology says `SCHEDULED_ON`. Any query using `SCHEDULED_ON` finds nothing; any
  new loader that emits `RUNS_ON` as the execution-host edge will collide with the
  existing folder→server edges.
- **Fix:**
  1. Update `controlm_folders.cypher` to write `SCHEDULED_ON` instead of `RUNS_ON`.
  2. One-time data migration in Neo4j:
     ```cypher
     // Rename all folder→server RUNS_ON edges to SCHEDULED_ON
     MATCH (f:JobFolder)-[r:RUNS_ON]->(srv:ControlMServer)
     MERGE (f)-[s:SCHEDULED_ON]->(srv)
       ON CREATE SET s.since        = r.since,
                     s.source       = r.source,
                     s.loader       = r.loader
     SET s.last_seen_at = r.last_seen_at,
         s.last_run_id  = r.last_run_id
     DELETE r;
     ```
  Note: relationship type rename in Neo4j requires create-new + delete-old (no
  in-place rename). The `MERGE` above is idempotent if re-run.

---

##### Issue 3 — `WAS_GENERATED_BY` → `:JobRun` full-load supernode — Severity: **WARNING**

- **Current:** Every loader emits `MERGE (node)-[:WAS_GENERATED_BY {source:'BMC'}]->(run)`
  where `run` is the single `:JobRun` node for that loader's execution. A full-refresh
  job load merges ~240K `WAS_GENERATED_BY` edges onto one `JobRun` node.
- **Problem:** The full-refresh `:JobRun` node accumulates the same degree as the
  total population loaded (≥240K for jobs alone; more with conditions and folders).
  This exceeds the 100K heuristic threshold. Traversals from the `:JobRun` side
  (`MATCH (run:JobRun)-[*]-(n)`) will be slow, and write-amplification during a
  `SET r.last_seen_at` update on the next run touches all edges.
- **Impact assessment:** Queries in DryDocs are typically node-first (start with
  `:ControlMJob`, traverse to `JobRun`) so the supernode is read from the leaf, not
  the hub — this is the safe direction. The problem only manifests if someone queries
  `MATCH (run:JobRun {run_id: $id})<-[:WAS_GENERATED_BY]-(n) RETURN n` with no
  label filter on `n`.
- **Fix (incremental path naturally mitigates):** The Phase-1 incremental design
  creates a **new `:JobRun` per incremental run** and only changed jobs point to it —
  so incremental runs are safe (degree proportional to delta, not population). For
  full-refresh runs, the mitigations are:
  1. Always query `(j:ControlMJob)-[:WAS_GENERATED_BY]->(run)` not the reverse.
  2. Add a `LIMIT` or label filter when querying from the run side.
  3. Long-term: if provenance audit at run level is needed, use a `count` property
     on the `:JobRun` node rather than traversing all edges.

---

##### Issue 4 — Temporal properties stored as strings — Severity: **WARNING**

- **Current:** `capture_date`, `last_updated`, `version_timestamp`, `active_from`,
  `active_till` on `:ControlMJob` and `:JobFolder` are set as raw values from Oracle
  (likely strings or Python datetime objects serialized without `datetime()` wrapping).
- **Problem:** Neo4j's temporal operators (`date()`, `datetime()`, range filters,
  `duration.between()`) do not work on string properties. Queries like
  `WHERE j.capture_date > date('2026-01-01')` will silently fail or do string
  comparison.
- **Fix:** In the Python loader, convert Oracle `DATE`/`TIMESTAMP` columns to ISO
  strings *before* the batch, then in Cypher use `datetime(row.capture_date)` rather
  than raw `row.capture_date`. Apply to all date properties across M3 loaders.
  Existing data can be migrated:
  ```cypher
  MATCH (j:ControlMJob) WHERE j.capture_date IS NOT NULL AND j.capture_date <> ''
  SET j.capture_date = datetime(j.capture_date)
  ```
  (Check that the string format is ISO 8601 first — Oracle `TIMESTAMP` default may
  not be ISO.)

---

##### Issue 5 — `ControlMFolder` LocalClass IRI not updated from `JobFolder` — Severity: **INFO**

- **Current:** `ontology_supplement.cypher` declares
  `{iri: "https://drydocs.local/ontology#JobFolder"}` and the `SET n.label = "Control-M
  Job Folder"`. The IRI still says `JobFolder` not `ControlMFolder`.
- **Problem:** The ontology backbone IRI is the durable identifier; if external tools
  (RDF export, SPARQL) ever consume it, the IRI should match the canonical label.
  Internal graph queries are unaffected (IRIs are properties, not Neo4j labels).
- **Fix:** After the `:JobFolder`→`:ControlMFolder` constraint migration (Issue 1),
  update the supplement IRI and `n.notes` label to `#ControlMFolder`.

---

##### Issue 6 — `AreaProduct` lacks `SUBCLASS_OF` wiring — Severity: **INFO**

- **Current:** The supplement comment explicitly defers: "No SUBCLASS_OF needed:
  dd:AreaProduct is a standalone local entity class." The vocabulary records
  `prov_type: Entity`.
- **Problem:** Without a SUBCLASS_OF chain, `AreaProduct` is ontologically
  unclassified — the PROV decision matrix (Entity→Agent, Entity→Entity paths) cannot
  be applied from AreaProduct as a source. The note in the vocabulary already marks
  `SUPPORTS` (DevTeam→AreaProduct) as local-only (no PROV mapping), which is correct
  given the gap, but it means AreaProduct edges are forever "local-only" unless this
  is resolved.
- **Fix (optional):** Add:
  ```cypher
  MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#AreaProduct"})
  MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Entity"})
  MERGE (lc)-[r:SUBCLASS_OF]->(pc)
    ON CREATE SET r.source = "drydocs.catalog_supplement";
  ```
  This enables AreaProduct→Agent edges to map to `prov:wasDerivedFrom` if needed
  later without redesign.

---

##### Issue 7 — `SUPPORTS` range declared as `"Product or AreaProduct"` (string ambiguity) — Severity: **INFO**

- **Current:** `n.range = "Product or AreaProduct"` in the supplement Cypher.
- **Problem:** Ontology systems expect a single IRI or a declared union class; a
  free-text "or" is invisible to any schema validation tooling.
- **Fix:** Split into two `LocalRelationship` nodes — `supports_product` and
  `supports_area_product` with distinct IRIs — or store `n.range` as the more precise
  union notation `"dd:Product | dd:AreaProduct"`. Low priority.

---

#### Developer SID → Employee attribution — design decision required

The Phase-1 DBA review deferred `STG_DEV_SID` and handles attribution inline (the
`UPPER(REGEXP_REPLACE(sid,'p$',''))` expression). On the graph side, `:ControlMJob`
carries `owner`, `author`, `version_user` as **string properties**, not edges.

Two paths forward:
1. **String-match join** (current): queries attribute jobs to people via
   `WHERE j.owner = e.employee_id`. Works, but requires case normalization at query
   time and doesn't leverage Neo4j traversal.
2. **Graph edge** (eventual): once `CREATION_USER`/`CHANGE_USERID` are confirmed
   on the source (Phase-1 open question 3), add a
   `(j:ControlMJob)-[:WAS_ASSOCIATED_WITH {role:'owner'}]->(e:Employee)` edge in the
   job loader. This requires a `Developer` node or reuse of the existing `:Employee`
   constraint (keyed on `employee_id`, which must match the normalized SID).

**Recommendation:** keep the string-property approach until open question 3 is
answered (column existence confirmed). When the SID→Employee graph edge is added,
it should:
- Normalize the SID via the Phase-1 expression before the MERGE.
- Use `WAS_ASSOCIATED_WITH {role: 'owner' | 'author' | 'version_user' | 'creator' | 'changer'}` — multiple roles, same label, distinguished by `role` property.
- Not require a new `:Developer` node type — reuse `:Employee` (same person, same
  SID, already in graph from SEAL contacts).

This keeps the ontology clean: ControlMJob (Activity) `WAS_ASSOCIATED_WITH`
Employee (Agent) maps directly to `prov:wasAssociatedWith` (Activity → Agent). No
new node type needed.

---

**Task 2.2 summary:** The DryDocs ontology is well-designed and ontologically
rigorous. Priority actions: (1) complete the `:JobFolder`→`:ControlMFolder`
rename migration [WARNING]; (2) fix the `RUNS_ON`→`SCHEDULED_ON` loader/data sync
[WARNING]; (3) convert date properties to Neo4j temporal types [WARNING]; (4) be
aware of the full-refresh JobRun supernode pattern and always query from the
leaf side [WARNING]. Lower-priority: AreaProduct SUBCLASS_OF, IRI rename, SUPPORTS
range cleanup.

→ Next: **2.3 Staging → graph mapping** (validation of DRYDOCS_STG incl. Phase-1
supplemental tables → Cypher load mapping; idempotent MERGE anchoring).

---

## 2.3 Staging → Graph Mapping

Each `DRYDOCS_STG` table mapped to its graph destination, with idempotency
anchors and incremental-load implications.

### Full mapping table

| Staging object | Graph destination | Idempotency anchor | Incremental note |
|---|---|---|---|
| `STG_RUN` | `:JobRun {run_id}` | `run_id` UNIQUE | One new `:JobRun` per run — incremental runs produce small-degree nodes |
| `STG_LOAD_CONTROL` | `:JobRun` **property** `hwm_version_serial`, `load_mode` | n/a — Oracle-side only | Record HWM on the `:JobRun` node for graph-side auditing; no new node type |
| `STG_SAMPLE_MANIFEST` | `:JobRun` **property** `sample_scenario`, `scope_folder` | n/a — Oracle-side only | Could also become `:SampleRun` nodes if sample lineage queries are needed |
| `JOB_DETAILED_VIEW` → jobs loader | `:ControlMJob {folder_id, job_id}` | NODE KEY `(folder_id, job_id)` | MERGE is idempotent; properties SET in place |
| `JOB_DETAILED_VIEW` → folders loader | `:ControlMFolder {folder_id}` + `:ControlMServer {name}` | `folder_id` UNIQUE; `name` UNIQUE | MERGE idempotent |
| `STG_VARIABLE` | **Not yet in graph.** Variables are staging-only at present. | See design decision below | Design decision: property or node? (below) |
| `STG_APP_FACT` | Graph edges: `(j:ControlMJob)-[:WAS_ASSOCIATED_WITH]->(a:Application)` | MERGE on job NODE KEY + `a.seal_id` UNIQUE | Idempotent if the MERGE pattern is correct; edge carries `role: 'seal_app_ref'` |
| `STG_INVOCATION` | `:Script {path}` nodes (planned) `(j)-[:USED {role:'executes_script'}]->(s)` | `path` property — needs a UNIQUE constraint on `:Script` | No constraint exists yet; must add before loader runs |
| `STG_FILE_REF` | `:File {canonical_path, date_token}` (planned) | Composite key needed: `(canonical_path, date_token)` | Needs new constraint; planned label `dd:File` in vocabulary |
| `STG_FILE_OP` | Not yet in vocabulary. Could be edges `(j)-[:WAS_DERIVED_FROM {role:'file_op'}]->(f:File)` | n/a | Design deferred |
| `STG_NOTIFICATION` | Not yet in vocabulary. Email/channel contact — consider `(j)-[:NOTIFIES]->(e:Employee)` reconciled on address | n/a | Design deferred; employee email match is fuzzy |
| `CM_DEF_LNKI/O_P_VW` (via loaders) | `:Condition {folder_id, name}` | NODE KEY `(folder_id, name)` | Idempotent MERGE; stale-edge issue (see below) |
| `STG_PARSE_QUALITY` | `:QualityMeasurement` (DQV, `constraints.cypher` has constraint) | `measurement_id` UNIQUE | Existing constraint covers this |

---

### Critical: idempotent MERGE vs. stale-edge problem

The Phase-1 incremental design removes and re-inserts **Oracle staging rows** per
changed job. The graph-side loaders use `MERGE` which is **append-only** — edges
are created on first assertion and updated on re-assertion, but **never deleted by
MERGE**.

**Consequence for condition edges:** If job J previously had `REQUIRES_IN_CONDITION`
edge to condition C1, and after a change it now requires C2 (C1 removed), the
incremental run will:
1. Oracle: delete J's old condition staging rows, insert C2.
2. Neo4j conditions loader: MERGE J→C2 ✓. But J→C1 edge **remains** from the prior
   full load — MERGE did not touch it.

The result is that the graph accumulates phantom edges for removed conditions. This
is the canonical incremental graph load problem.

**Two acceptable strategies:**

**Strategy A — `last_seen_at` age-out (current partial implementation):**
Every edge carries `last_run_id` (already in the loader pattern). A periodic cleanup
pass deletes edges where `last_run_id` is older than N runs:
```cypher
// Remove condition edges that haven't been re-asserted in the last 2 runs
MATCH (j:ControlMJob)-[r:REQUIRES_IN_CONDITION]->(:Condition)
WHERE r.last_run_id < $oldest_acceptable_run_id
DELETE r;
```
Pros: simple; consistent with existing edge pattern. Cons: stale edges exist between
cleanup runs; cleanup must be scheduled.

**Strategy B — per-job edge replacement (recommended for correctness):**
Before re-asserting a changed job's edges, delete all its edges of the types being
refreshed:
```cypher
// For each changed (folder_id, job_id) in the batch:
MATCH (j:ControlMJob {folder_id: $folder_id, job_id: $job_id})
OPTIONAL MATCH (j)-[r:REQUIRES_IN_CONDITION]->()
DELETE r
// ... then MERGE the new condition edges from the current staging rows
```
Pros: graph immediately consistent with staging after each incremental batch.
Cons: slightly more complex loader; must be done **within the same transaction** as
the node MERGE to avoid a window of missing edges.

**Recommendation:** implement Strategy B for condition/invocation edges (where
correctness matters for lineage queries), and Strategy A as the fallback cleanup for
any edge type not yet migrated. Add a `last_run_id` index on edge types used in
cleanup:
```cypher
CREATE INDEX conditions_in_last_run IF NOT EXISTS
  FOR ()-[r:REQUIRES_IN_CONDITION]-() ON (r.last_run_id);
```

---

### Variable graph-node design decision

`STG_VARIABLE` (~1.1M rows) has no current graph representation. Two choices:

**Option A — keep variables Oracle-only (staging as semantic store):**
The Python normalizer resolves and classifies variables in `STG_VARIABLE`; the graph
layer accesses them via `STG_APP_FACT` semantic extracts (SEAL refs, FIDs, etc.) as
graph edges. Raw variable resolution stays in Oracle. Graph stays focused on
structural lineage.

Pros: graph stays lean; no 1.1M-node population that most graph queries don't need.
Cons: variable-value queries require a join to Oracle staging from Neo4j (or a Python
bridge layer); can't do native graph traversal over variable references.

**Option B — selectively load graph-relevant variable facts:**
Only load variables where `var_kind IN ('SEMANTIC_FACT', 'FLOW_REF')` and only the
canonical classified form (not raw values). These become graph edges/nodes expressing
semantic linkage, not a bulk variable dump.

Volume reduction: `SEMANTIC_FACT` and `FLOW_REF` are a small fraction of the 1.1M
rows. A `STG_APP_FACT`-based loader already extracts the SEAL-ref subset. Extend
this to the other semantic kinds as the classification matures.

**Recommendation: Option B incrementally** — continue using `STG_APP_FACT` as the
staging→graph bridge for semantic facts; do not load raw `STG_VARIABLE` rows. When
`FLOW_REF` cross-flow variable links are analyzed, build a dedicated loader over
that subset. This avoids a 1.1M node population while retaining graph-native
traversal for what actually matters.

---

### `STG_LOAD_CONTROL` → `:JobRun` annotation

The Phase-1 `STG_LOAD_CONTROL` table records the high-water mark per
`(source_object, data_center)` pair. This metadata should be reflected in the
Neo4j `:JobRun` node so graph-side tools can inspect load provenance:

```cypher
// In the load-control update step (after advancing HWM in Oracle):
MERGE (run:JobRun {run_id: $run_id})
SET run.load_mode           = $load_mode,       // 'FULL' | 'INCREMENTAL'
    run.hwm_version_serial  = $hwm_version_serial,
    run.hwm_capture_date    = datetime($hwm_capture_date),
    run.source_object       = $source_object,
    run.data_center         = $data_center,
    run.rows_applied        = $rows_applied
```

This keeps the `STG_LOAD_CONTROL` oracle-side watermark consistent with the graph-
side provenance record. No new node type required.

---

**Task 2.3 summary:** The staging → graph mapping is mostly well-anchored on
existing NODE KEY constraints. Critical gap: incremental loads produce stale edges
for condition/invocation relationships — use per-job edge replacement (Strategy B)
before re-asserting. Variables should stay Oracle-only except for semantic-fact
extracts via `STG_APP_FACT`. `STG_LOAD_CONTROL` metadata should annotate the
`:JobRun` node in Neo4j. `:Script`, `:File` loaders need constraints before they
can be created safely.

→ Next: **2.4 Incremental graph load** (import-skill / cypher-skill: constraints-
first, UNWIND $batch + MERGE, CALL { } IN TRANSACTIONS, change-only loads driven by
the watermark staging).

---

## 2.4 Incremental Graph Load Design

### Load method selection (import-skill decision table)

DryDocs uses the **Python neo4j driver with UNWIND batching** (via `BaseLoader` +
`Neo4jClient`). This is the correct method for driver-based incremental loads where
the source is an Oracle result set, not a file. The `CALL IN TRANSACTIONS` clause is
most useful for file-based loads (LOAD CSV). For driver batching, the equivalent is
Python-controlled batching at `batch_size=1000` (already in `BaseLoader._flush`).

For very large full-refresh batches (>50K rows), the Python loop at 1 000 rows/batch
is correct. For the incremental delta (typically <<50K changed jobs per run), 1 000
rows/batch is ample.

**No change to the load method is needed.** The import-skill's key principles that
apply here are: (1) constraints-first, (2) node MERGE before relationship MERGE, (3)
`ON ERROR` strategy, (4) idempotent patterns.

---

### Constraints-first order (verified correct; one gap)

**Existing constraints** cover all active node types that accept incremental MERGE:
- `:ControlMJob` NODE KEY `(folder_id, job_id)` ✓
- `:ControlMFolder`/`:JobFolder` `folder_id` UNIQUE ✓
- `:ControlMServer` `name` UNIQUE ✓
- `:Condition` NODE KEY `(folder_id, name)` ✓
- `:JobRun` `run_id` UNIQUE ✓

**Missing constraint for planned loaders** (must be added before those loaders run):
```cypher
-- ":Script" loader (STG_INVOCATION → Script nodes)
CREATE CONSTRAINT script_path IF NOT EXISTS
  FOR (s:Script) REQUIRE s.executable_path IS UNIQUE;

-- ":File" loader (STG_FILE_REF → File nodes) — composite key needed
CREATE CONSTRAINT file_key IF NOT EXISTS
  FOR (f:File) REQUIRE (f.canonical_path, f.date_token) IS NODE KEY;
```
Do not activate these loaders until their constraints exist.

---

### Incremental load sequence (per data-center per run)

The incremental load is a Python orchestration layer over the existing loader
framework. The sequence for a changed-job batch:

```
[Oracle: STG_LOAD_CONTROL] → read HWM (VERSION_SERIAL / CAPTURE_DATE)
[Oracle: extract]           → query changed jobs WHERE VERSION_SERIAL > HWM
[Python: collect job keys]  → list of (data_center, folder_id, job_id) changed
[Neo4j: Step 1 — edge cleanup]   → delete stale edges for changed jobs
[Neo4j: Step 2 — node upsert]    → UNWIND $batch → MERGE ControlMJob (existing loader)
[Neo4j: Step 3 — edge re-assert] → UNWIND $batch → MERGE conditions, invocations, ...
[Oracle: advance HWM]            → UPDATE STG_LOAD_CONTROL, COMMIT
```

**Critical ordering**: edge cleanup (Step 1) **must** precede edge re-assert (Step 3).
All three Neo4j steps for a batch should be one logical unit; but since they are
separate Cypher statements in the driver, wrap them in the same Python transaction
or execute them in immediate sequence within one batch iteration.

---

### Cypher patterns for each step

**Step 1 — stale edge cleanup (per-job replacement, Strategy B)**

```cypher
// Delete all condition and invocation edges for the changed jobs in this batch.
// MUST run before re-asserting the current edge set.
UNWIND $changed_keys AS key
MATCH (j:ControlMJob {folder_id: key.folder_id, job_id: key.job_id})
OPTIONAL MATCH (j)-[r:REQUIRES_IN_CONDITION|EMITS_OUT_CONDITION]->()
DELETE r
```

`OPTIONAL MATCH` ensures the Cypher does not fail if the job has no condition edges
(new jobs, or first load). `DELETE r` inside `OPTIONAL MATCH` is safe — deletes
only if `r` is non-null.

**Step 2 — node upsert (existing pattern, already correct)**

The current `controlm_jobs.cypher` MERGE is idempotent and correct. For incremental
runs, pass only the changed-job rows (not the full population). The `SET` overwrites
all mutable properties in place — version_serial, capture_date, etc. — on each run.

```cypher
-- Existing controlm_jobs.cypher pattern (abbreviated):
UNWIND $batch AS row
MATCH (f:ControlMFolder {folder_id: row.folder_id})  -- after rename migration
MERGE (j:ControlMJob:Activity {folder_id: row.folder_id, job_id: row.job_id})
  ON CREATE SET j.created_at = datetime($loaded_at), j.source = 'psgmgr.CM_DEF_VJOB'
SET j.version_serial = row.version_serial,
    j.capture_date   = datetime(row.capture_date),   -- apply datetime() wrapping
    ...
    j.last_run_id    = $run_id
MERGE (f)-[r:CONTAINS_JOB]->(j) ...
MERGE (j)-[r:WAS_GENERATED_BY {source:'BMC'}]->(run:JobRun {run_id: $run_id}) ...
```

Two adjustments from the current loader (2.2 Issue 4):
1. Wrap date strings: `datetime(row.capture_date)` not `row.capture_date`.
2. Use `:ControlMFolder` after the rename migration (Issue 1).

**Step 3 — condition edge re-assert (idempotent MERGE after cleanup)**

Since Step 1 deleted the stale edges, Step 3 can safely MERGE all current edges:

```cypher
-- controlm_conditions_in.cypher — already correct pattern:
UNWIND $batch AS row
MATCH (j:ControlMJob {folder_id: row.folder_id, job_id: row.job_id})
MERGE (c:Condition {folder_id: row.folder_id, name: row.condition_name})
  ON CREATE SET c.created_at = datetime($loaded_at)
MERGE (j)-[r:REQUIRES_IN_CONDITION]->(c)
  ON CREATE SET r.first_seen_at = datetime($loaded_at), r.source = 'psgmgr'
SET r.odate       = row.odate,
    r.and_or      = row.and_or,
    r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id
```

This is already correct. The only addition needed is that Step 1 (edge cleanup) runs
**before** this, so removed conditions are properly deleted.

---

### `CALL IN TRANSACTIONS` — when to use in DryDocs

The Python-driver batching in `BaseLoader` is the primary batching mechanism and is
correct for incremental loads. However, two operations benefit from server-side
`CALL IN TRANSACTIONS`:

**1. Full-refresh load baseline (large populations):**
For the initial full-refresh of ~240K jobs, rather than looping 240 Python-submitted
batches, a single LOAD CSV from a temp file (if the environment supports it) with
`CALL IN TRANSACTIONS` would be more efficient. If not, the current Python loop is
acceptable.

**2. Stale-edge cleanup pass (age-out, Strategy A):**
The periodic cleanup of edges older than N runs is best expressed as a server-side
operation:
```cypher
// Scheduled cleanup: delete condition edges from runs older than $cutoff_run_id
MATCH ()-[r:REQUIRES_IN_CONDITION|EMITS_OUT_CONDITION]->()
WHERE r.last_run_id < $cutoff_run_id
CALL (r) {
  DELETE r
} IN TRANSACTIONS OF 10000 ROWS ON ERROR CONTINUE REPORT STATUS AS s
RETURN count(*), s.committed
```
This avoids loading all stale edges into Python memory. Add a range index on
`last_run_id` first (see 2.3 — already recommended).

---

### Incremental load Python integration sketch

The new `IncrementalControlMLoader` (to be built) layers over the existing loaders:

```python
class IncrementalControlMLoader:
    def run(self, data_center: str) -> LoadSummary:
        # 1. Read HWM from Oracle STG_LOAD_CONTROL
        hwm = self._oracle.get_hwm('CM_DEF_VJOB', data_center)

        # 2. Extract changed jobs from STG (VERSION_SERIAL > hwm.hwm_version_serial)
        changed = self._oracle.get_changed_jobs(data_center, hwm)
        if not changed:
            return LoadSummary(status='NO_CHANGES', ...)

        # 3. Open a :JobRun in Neo4j (BaseLoader._open_run pattern)
        run_id, loaded_at = self._graph.open_run(loader='controlm_jobs.incremental.v1')

        # 4. Batch loop — same BaseLoader._flush pattern
        for batch in _chunks(changed, self.batch_size):
            job_keys = [{'folder_id': r.folder_id, 'job_id': r.job_id} for r in batch]
            # Step 1: cleanup stale edges
            self._graph.run(STALE_EDGE_CLEANUP_CYPHER, {'changed_keys': job_keys})
            # Step 2: node upsert (reuse existing controlm_jobs.cypher)
            self._graph.run(JOBS_CYPHER, {'batch': [r.as_dict() for r in batch], ...})
            # Step 3: condition re-assert (reuse controlm_conditions_in.cypher)
            cond_rows = self._oracle.get_conditions_for_jobs(batch)
            if cond_rows:
                self._graph.run(CONDITIONS_IN_CYPHER, {'batch': cond_rows, ...})
            # Advance Oracle HWM after each committed graph batch
            self._oracle.advance_hwm('CM_DEF_VJOB', data_center, batch)

        # 5. Close :JobRun with row counts
        self._graph.close_run(run_id, rows_processed=len(changed))
        return LoadSummary(status='SUCCEEDED', ...)
```

This sketch reuses the existing cypher files; the only new file is
`stale_edge_cleanup.cypher` (Step 1 above).

---

### Full-refresh path (baseline rebuild)

The full-refresh loader (current production pattern) continues unchanged. The
incremental loader is additive — `STG_LOAD_CONTROL.load_mode = 'FULL'` for a
baseline run, `'INCREMENTAL'` for delta runs. Full refresh is the restart path if
incremental state is corrupted or a DBA requests a clean graph rebuild.

---

**Task 2.4 summary:** The Python-driver batching pattern is correct for DryDocs's
incremental load. Key additions: (1) a `stale_edge_cleanup.cypher` that deletes
condition/invocation edges before re-asserting them per batch; (2) an
`IncrementalControlMLoader` that reads the HWM from `STG_LOAD_CONTROL`, extracts
only changed jobs, loops cleanup→upsert→re-assert→advance-HWM; (3) a periodic
server-side `CALL IN TRANSACTIONS` cleanup for aged-out edges. Constraints for
`:Script` and `:File` must be created before those loaders are built.

→ Next: **2.5 Critique Phase 1** — reconcile the DBA staging design with graph needs;
flag mismatches; record adjustments as addenda to `persona-oracle-dba.md`.
→ Then: **2.6 Finalize** `persona-neo4j-architect.md`.

---

## 2.5 Phase 1 Critique & Reconciliation

The Phase-1 Oracle DBA design is architecturally sound. The mismatches are
small-scope additions, not redesigns. Five addenda are recorded in
`persona-oracle-dba.md §1.8` (see that file). Summary here:

**A — Date types at the Oracle→Python→Neo4j boundary.** Phase 1 correctly uses
`CAPTURE_DATE` / `VERSION_TIMESTAMP` as Oracle TIMESTAMP watermarks, but does not
specify how they cross into Neo4j. The graph side requires ISO 8601 strings that
Cypher wraps with `datetime()`. Addendum: the Python normalizer/loader must convert
Oracle TIMESTAMP values to ISO strings before the batch dict; Cypher loader files
must use `datetime(row.capture_date)` not bare `row.capture_date`.

**B — Stale-edge cleanup not in Phase 1.** Phase 1's per-job delete+insert is
correct for Oracle staging but silent on the graph-side edge removal problem. The
graph accumulates phantom condition/invocation edges unless they are explicitly
deleted before re-asserting. Addendum: introduce `stale_edge_cleanup.cypher` as a
new loader file that precedes condition re-assertion in the incremental batch loop.
This is a pure addition; it does not change Phase 1's Oracle-side design.

**C — `STG_LOAD_CONTROL` HWM → `:JobRun` annotation.** Phase 1 defines the table
but does not describe how its metadata crosses into the graph. Addendum: after
advancing the Oracle HWM, the Python loader also annotates the `:JobRun` node with
`load_mode`, `hwm_version_serial`, and `rows_applied`. No new constraint needed —
`:JobRun(run_id)` unique constraint already anchors the MERGE.

**D — Developer SID → graph attribution path.** Phase 1 provides the inline SID
normalization expression and the `JOB_DEVELOPER_VIEW` but defers the graph link.
Addendum (for when Phase-1 open question 3 is answered): the graph link should be
`(j:ControlMJob)-[:WAS_ASSOCIATED_WITH {role: 'owner'|'author'|...}]->(e:Employee)`
using `developer_sid` to MATCH `:Employee`. No `:Developer` node type is needed —
reuse `:Employee`. This requires `UPPER(REGEXP_REPLACE(sid,'p$',''))` normalization
in Python before the MATCH.

**E — `SCHEDULED_ON` (not `RUNS_ON`) in the folders loader.** Phase 1 does not
reference the folders loader rename. Addendum: `controlm_folders.cypher` must write
`:SCHEDULED_ON` after the vocabulary rename is applied; include the data migration
(create SCHEDULED_ON, delete RUNS_ON) as a step in the incremental implementation.

No Phase-1 design decisions need to be reversed. All five items are additive
clarifications that the DBA team can append to their implementation ticket.

---

## 2.6 Phase 2 Finalization

### Summary of findings

**What is well-designed and ready for incremental development:**
- Constraint and ontology backbone — correct, idempotent, PROV-O aligned.
- All active node NODE KEYs prevent duplicates under incremental MERGE.
- `STG_LOAD_CONTROL` (Phase-1 new) correctly captures the watermark needed to
  drive a change-only graph load — no structural change to this table is needed.
- `STG_SAMPLE_MANIFEST` (Phase-1 new) provides sample provenance that can annotate
  `:JobRun` nodes with no new node type.
- The existing loader cypher files (UNWIND + MERGE + ON CREATE SET + SET) are the
  correct pattern for incremental upsert — reuse them unchanged for incremental runs.

**What must be done before the incremental loader can ship:**

| Priority | Action | File / Object |
|---|---|---|
| **P1 — Blocker** | Fix `RUNS_ON`→`SCHEDULED_ON` in loader + data migration | `controlm_folders.cypher` + one-time graph Cypher |
| **P1 — Blocker** | Add `stale_edge_cleanup.cypher` (delete condition/invocation edges before re-assert) | New: `drydocs/loaders/cypher/stale_edge_cleanup.cypher` |
| **P1 — Correctness** | Wrap date strings with `datetime()` in all M3 loaders | `controlm_jobs.cypher`, `controlm_folders.cypher` |
| **P2 — Needed** | Complete `:JobFolder`→`:ControlMFolder` rename migration | Add migration block to `constraints.cypher` |
| **P2 — Needed** | Add `last_run_id` range index on condition edge types (for age-out cleanup) | `constraints.cypher` or new index file |
| **P3 — Eventually** | Add `:Script(executable_path)` and `:File(canonical_path, date_token)` constraints before activating those loaders | `constraints.cypher` |
| **P3 — Eventually** | Surface `hwm_version_serial` / `load_mode` on `:JobRun` nodes | Incremental loader Python code |

**Open questions inherited from Phase 1 (unchanged):**

1. Confirm `CM_DEF_SETVAR` object name — blocks variable extract and incremental
   variable hash.
2. Confirm `CAPTURE_DATE` is per-row or per-extract — determines whether it's a
   reliable change signal or just a coarse HWM.
3. Confirm `CREATION_USER`/`CHANGE_USERID` exist on `CM_DEF_VJOB` — gates the dev-
   SID graph attribution edge.
4. Incremental cadence and staging retention policy.

**Additional open questions raised by Phase 2:**

5. Should `RUNS_ON`→`SCHEDULED_ON` migration run before or after the incremental
   loader ships? (Recommend: before, as part of the same deploy.)
6. Is the full-load `:JobRun` supernode (300K+ `WAS_GENERATED_BY` edges) a
   practical query-performance issue in the current environment? If yes, add an index
   on `(j:ControlMJob)-[:WAS_GENERATED_BY]->(run)` direction or restructure the
   provenance linkage.
7. Is APOC available in the Neo4j instance? (Affects the availability of
   `apoc.periodic.iterate` for the age-out cleanup vs native `CALL IN TRANSACTIONS`.)

→ Phase 2 complete. Hand off to Phase 3 (synthesis).

---

## 2.7 Data Catalog & Lineage Integration (addendum — 2026-06-18)

**Source:** `docs/patterns/data-catalog/` (7 sanitized reference files committed to
`feature/oracle-ingestion` and merged to `main`). Internal originals in
`drydocs/data/data-catalog/` (gitignored, retain full CCB detail).

**Standard confirmed:** LinkedIn DataHub entity model + DCAT v2 (W3C) + OpenLineage.
The `urn:li:` prefix is the conclusive DataHub identifier. The data catalog team
follows this standard; DryDocs should align to it for cross-team interoperability.

---

### The two-plane model

```
DATA CATALOG PLANE                     PROCESS GRAPH PLANE (DryDocs)
──────────────────────                 ──────────────────────────────
CatalogDistribution                    ControlMJob + DataAsset
  -[DATASET_OWNED_BY]-> Application <─── Application  (SHARED NODE — same node)
CatalogWorker ◄──────────────────────── Employee
CatalogWorkerGroup ◄─────────────────── DevTeam
                                        AppDataFlow  ← DataHub dataFlow
                                        ControlMJob  ← DataHub dataJob
                                        DataAsset    ← DataHub dataset
```

`:Application` (keyed by organizational app ID) is the bridge. It is the **same
node** in both planes — never duplicate it as `CatalogApplication`. The existing
DryDocs `Application(seal_id)` constraint handles MERGE from both sides.

---

### 3rd Application child node — AppDataFlow

DataHub's own entity model provides the exact pattern needed:

```
DataHub:   corpGroup ──▶ dataFlow ──▶ dataJob ──▶ (consumes/produces) ──▶ dataset
DryDocs: Application ──▶ AppDataFlow ──▶ ControlMJob ──▶ (USED/GENERATED) ──▶ DataAsset
```

The full Application child pattern becomes:

```
:Application {appId / seal_id}
  ├─[:HAS_BATCH_PROCESS]──▶ :BatchProcess {appId}    ← existing
  ├─[:HAS_EVENT_PROCESS]──▶ :EventProcess {appId}    ← existing
  └─[:HAS_DATA_FLOW]───────▶ :AppDataFlow             ← NEW (this addendum)
                             {appId, dataflowUrn, flowName, orchestrator, cluster}
```

`AppDataFlow.orchestrator = 'controlm'` and `AppDataFlow.cluster = data_center`
make this node emit a DataHub-compatible URN:
`urn:li:dataFlow:{controlm,<folder-or-job-group-name>,<data_center>}`

---

### DataAsset node

Represents a named data object as seen by the orchestration layer. Platform is a
**property**, not a node — the `DataPlatform` supernode risk analysis
(`lineage-design-top3.md §Supernode Mitigation`) disqualifies it as a node.

```
:DataAsset
  { assetId            -- UNIQUE key (drydocs:dataasset:{platform}:{namespace}:{name})
  , name               -- table/file/object name
  , platform           -- 'oracle' | 'snowflake' | 'teradata' | 's3' | 'sqlserver' | 'linux'
  , namespace          -- schema/bucket/path
  , env                -- 'PROD' | 'DEV' | 'TEST'
  , format             -- 'TABLE' | 'FILE' | 'VIEW' | 'STREAM'
  , isExternalFeed     -- boolean: third-party / upstream data feed
  , isSourceOfRecord   -- boolean: business source-of-record for this data
  }
```

---

### New relationships

| Edge | From | To | Notes |
|---|---|---|---|
| `HAS_DATA_FLOW` | `Application` | `AppDataFlow` | 3rd facet of Application |
| `ORCHESTRATES` | `AppDataFlow` | `ControlMJob` | pipeline → task containment |
| `USED` | `ControlMJob` | `DataAsset` | PROV-O prov:used; input |
| `GENERATED` | `ControlMJob` | `DataAsset` | PROV-O prov:wasGeneratedBy; output |
| `REPRESENTS_CATALOG_DATASET` | `DataAsset` | `CatalogDataset` | optional bridge; populate only when URN confirmed |

`USED` and `GENERATED` map directly to `prov:used` (Activity → Entity) and
`prov:wasGeneratedBy` (Entity → Activity) — consistent with the existing PROV-O
ontology without adding new vocabulary.

---

### Constraints and indexes to add

Add to `drydocs/schema/constraints.cypher`:

```cypher
-- AppDataFlow
CREATE CONSTRAINT app_data_flow_urn IF NOT EXISTS
  FOR (f:AppDataFlow) REQUIRE f.dataflowUrn IS UNIQUE;

-- DataAsset
CREATE CONSTRAINT data_asset_id IF NOT EXISTS
  FOR (a:DataAsset) REQUIRE a.assetId IS UNIQUE;

-- Performance indexes (platform + name are the two most common filter axes)
CREATE INDEX data_asset_platform_idx IF NOT EXISTS
  FOR (a:DataAsset) ON (a.platform);

CREATE INDEX data_asset_name_idx IF NOT EXISTS
  FOR (a:DataAsset) ON (a.name);
```

Add to `drydocs/schema/catalog_ontology_supplement.cypher` (or a new
`data_lineage_supplement.cypher`):

```cypher
// AppDataFlow — prov:Activity cluster, DataHub dataFlow analogue
MERGE (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#AppDataFlow"})
  ON CREATE SET lc.label        = "Application Data Flow",
               lc.prov_type    = "Activity",
               lc.datahub_entity = "dataFlow",
               lc.openlineage_entity = "Job",
               lc.source       = "drydocs.data_lineage_supplement";
MERGE (pc:OntologyTerm:ProvClass {iri: "http://www.w3.org/ns/prov#Activity"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc) ON CREATE SET r.source = "drydocs.data_lineage_supplement";

// DataAsset — prov:Entity, DataHub dataset analogue
MERGE (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#DataAsset"})
  ON CREATE SET lc.label        = "Data Asset",
               lc.prov_type    = "Entity",
               lc.datahub_entity = "dataset",
               lc.openlineage_entity = "Dataset",
               lc.source       = "drydocs.data_lineage_supplement";
MERGE (pc:OntologyTerm:ProvClass {iri: "http://www.w3.org/ns/prov#Entity"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc) ON CREATE SET r.source = "drydocs.data_lineage_supplement";
```

---

### Supernode prevention — platform as property

The `:DataPlatform` node would accumulate millions of edges (one per ControlMJob
that runs on Snowflake, Oracle, etc.) — a classic modeling supernode.

**Rule:** `platform` is a property on `:DataAsset` and `:ControlMJob`, not a node.
The `data_catalog_schema.cypher` in `docs/patterns/` already documents a
`:DataPlatform` meta-node for schema documentation only (`:SchemaMeta` label);
that node has no data edges.

---

### The DryDocs lineage moat

No enterprise data catalog can answer "what is the full path for data that ends up
in table X?" at the cross-platform level. Catalogs observe data AT REST; Control-M
orchestrates all hops. The DryDocs unique query:

```cypher
MATCH (tgt:DataAsset {name: $targetName, isSourceOfRecord: true})
MATCH path = (src:DataAsset {isExternalFeed: true})
             <-[:USED]-(j1:ControlMJob)-[:GENERATED]->(mid:DataAsset)
             <-[:USED]-(j2:ControlMJob)-[:GENERATED]->(tgt)
RETURN path,
       [n IN nodes(path) WHERE n:DataAsset | n.name + '@' + n.platform] AS platformHops
```

traces: `[s3-file] → FileWatcher job → [oracle-staging] → ETL job → [teradata] →
Export job → [snowflake-table]`.

---

### Updated priority table (incorporating catalog items)

| Priority | Action | File | Notes |
|---|---|---|---|
| **P0** | RUNS_ON → SCHEDULED_ON loader + data migration | `controlm_folders.cypher` | Edge collision blocker |
| **P0** | `stale_edge_cleanup.cypher` | new | Required before incremental loader runs |
| **P0** | datetime() wrapping in M3 loaders | `controlm_jobs.cypher`, `controlm_folders.cypher` | Temporal operators broken without this |
| **P1** | `:ControlMFolder` rename migration | `constraints.cypher` | Vocabulary/constraint/loader drift |
| **P1** | `:JobRun` HWM annotation | incremental loader Python | Graph-side audit of Oracle HWM state |
| **P1** | `last_run_id` range index on condition edges | `constraints.cypher` | Age-out cleanup enabler |
| **P1-NEW** | `AppDataFlow` + `DataAsset` constraints + indexes | `constraints.cypher` | Gate for any data-lineage loader |
| **P1-NEW** | Ontology supplement for `AppDataFlow` + `DataAsset` | new supplement or extend `catalog_ontology_supplement.cypher` | PROV-O wiring |
| **P2** | `:Script(executable_path)` + `:File` constraints | `constraints.cypher` | Gate for STG_INVOCATION / STG_FILE_REF loaders |
| **P2-NEW** | `AppDataFlow` population loader (stub) | new `drydocs/loaders/app_data_flow_loader.py` | Populate one node per Application per DC; `ORCHESTRATES` edges from folders |
| **P2-NEW** | `DataAsset` population loader | new | Parse STG_INVOCATION + STG_FILE_REF for input/output objects |
| **P3-NEW** | `REPRESENTS_CATALOG_DATASET` bridge edges | additive | Only when catalog URN can be resolved; not blocking |

---

### Reference files (all in public repo)

- `docs/patterns/data-catalog/ontology-standard.md` — DataHub + DCAT v2 + OpenLineage
- `docs/patterns/data-catalog/enterprise-data-catalog-ontology.md` — 17-node-type ontology
- `docs/patterns/data-catalog/lineage-design-top3.md` — 3 patterns + hybrid recommendation
- `docs/patterns/data-catalog/data-catalog-schema.cypher` — constraints + meta-graph + bridge
- `docs/patterns/data-catalog/data-catalog-drydocs-crosswalk.md` — two-plane model
- `docs/patterns/data-catalog/classifiers-example.csv` — 20-row classifier taxonomy
