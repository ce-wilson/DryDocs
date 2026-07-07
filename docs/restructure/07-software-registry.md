# 07 — Third-party software registry (Vendor → Product → used-by)

**Status: PLANNED — captured 2026-07-07, not started.** Companion to the
"vendor" terminology audit (2026-07-06 session). KISS is the design constraint:
one taxonomy file, two node types, one edge — everything else is deferred until
a query demands it.

## Problem

"Vendor" currently means five different things in this repo (terminology audit):
the Tier-2 orchestration category (BMC/AutoSys/Airflow), the trust axis
("vendor's words" vs inference), the `vendor-bmc` corpus ID baked into tooling
(review-labels, gate-prompts, graph-tests), the brand/logo registry
(`drydocs-icons/vendors/` — includes Neo4j, Oracle, Snowflake), and loose
module-speak ("the vendor domain" = `drydocs/controlm/`). Meanwhile Oracle and
Neo4j — third-party software we depend on just as much as BMC — have no
registry entry at all, only prose roles in `reference/REGISTRY.yaml`.

The company's internal software library already shows the right shape (the
library's own name carries no meaning — only its metadata model does):
**Vendor → Vendor Product**, with per-product status
(approved/conditionally/research), software type
(commercial/open-source/internal/hybrid), per-**version** status
(allowed/restricted/not-allowed/no-position), and a governing domain. That is a
graph lookup, not a pile of YAML conventions.

Target questions the registry must answer:

- *Which applications use Ab Initio?* — support/impact analysis.
- *Which applications are on Oracle 19?* — version-risk sweeps.
- *What does DryDocs itself build with?* — the current Tier-1/Tier-2 story,
  restated as data instead of prose.

## Direction (KISS)

**One meaning per word, one source of truth per fact:**

- **`Vendor`** = the company/brand, nothing else (BMC, Oracle, Neo4j Inc,
  Ab Initio Software). Matches the icons registry's "Brands" reading — the
  icon manifest can key on the same ids.
- **`SoftwareProduct`** = what a vendor ships (Control-M, Oracle Database,
  Neo4j, Co>Operating System). Role becomes an **attribute**, not a vocabulary:
  `role: orchestrator | data-platform | graph-platform | tool` — this absorbs
  the Tier-1/Tier-2 split (tiers stay in CLAUDE.md as *reading guidance*, but
  the data lives here).
- **`USES_SOFTWARE`** edge: `(:Application)-[:USES_SOFTWARE {version, source,
  status}]->(:SoftwareProduct)` — and DryDocs itself is just another
  application node using Neo4j + Oracle + Control-M. Version is an **edge
  property** first; `SoftwareVersion` nodes only if per-version queries
  outgrow it (deferred).
- **YAML is the import artifact, the graph is the lookup.** The repo stays the
  source of truth (`config/taxonomy/software-registry.yaml`, taxonomy-first per
  CLAUDE.md §1), a loader MERGEs it; no relational sidecar — the graph *is*
  the table.
- **`vendor-bmc` leaves the tooling.** The corpus/source ID becomes `bmc-docs`
  (it names a documentation corpus, not a vendor relationship). Mechanical
  rename in review-labels.yaml, gate-prompts, graph-tests suite, tests, docs —
  same playbook as the JobFolder→ControlMFolder rename.

**Sanitization (mechanism, not instance):** the registry *schema* and DryDocs'
own stack are publishable. Company catalog rows (the internal library's
statuses, the get-request metadata, real app→software mappings) are
company-side data — `internal/` twin or company repo only, like the `ccb-`
convention.

**Field set (SME, 2026-07-07, from the company catalog export):** keep
**product name, publisher, publisherURL, category, version-if-known** — and
nothing else. The export's other columns (owner names/SIDs, `gspcId`,
`sealId`, evaluation decisions, support/EOL dates) are company governance
data: Internal/Internal-Confidential, Phase-4 material only, never in the
producer registry.

```yaml
# config/taxonomy/software-registry.yaml  (shape sketch)
schema: drydocs.software-registry.v1
classification: Internal-Public          # producer copy: DryDocs' own stack only
vendors:
  - id: neo4j          # matches drydocs-icons manifest id
    name: Neo4j
    publisher_url: https://neo4j.com/
products:
  - id: neo4j
    vendor: neo4j
    name: Neo4j
    category: DBMS — Graph Database
    role: graph-platform
    type: commercial            # EE via Docker; community edition open-source
    versions: ["5.x"]           # known-in-use, refine when verifiable
```

## Base list (Phase 1 seed — cherry-picked 2026-07-07)

From the catalog screenshots + what DryDocs/the batch estate demonstrably use.
One vendor search returns ~300 catalog rows (Bloom → drivers → utilities) —
the registry deliberately takes the handful that matter and skips the long
tail (drivers/utilities are dependencies, not products we track):

| Vendor | Product | Category | URL | Version (if known) |
|---|---|---|---|---|
| Neo4j | Neo4j | DBMS — Graph Database | neo4j.com | 5.x (EE via local Docker; catalog shows a 5.19–5.26 window) |
| Neo4j | Neo4j Bloom | BI — Graph Analytics/Visualization | neo4j.com | 2.x (catalog; separate product, kept because we have it) |
| BMC Software | Control-M | Workload Automation | bmc.com | **9.0.21.300** (company runtime — known) |
| Oracle | Oracle Database | DBMS — Relational | oracle.com | 19c (company `psgmgr` host — VERIFY) |
| Python Software Foundation | Python | Language Runtime | python.org | 3.11+ (3.13 in local use) |
| Ab Initio Software | Ab Initio (Co>Operating System) | Data Integration (ETL) | abinitio.com | unknown — Phase 3 detection target |
| Informatica | PowerCenter | Data Integration (ETL) | informatica.com | unknown — Phase 3 detection target (`pmcmd`) |

Ab Initio and Informatica earn rows *before* any `USES_SOFTWARE` edges exist —
Phase 3's invocation-pattern table needs product ids to point at. Drivers,
Cypher Shell, Helm charts, `neovis.js` etc. stay out (dependency tail).
Snowflake gets a row when it stops being a future.

## What already feeds it

- `CM_DEF_VJOB.APPL_TYPE` — **dead-end for product derivation** (SME,
  2026-07-07): Ab Initio / Informatica workloads run as plain OS *commands*,
  so the Control-M job/application types are not used to their full potential
  and don't reflect the actual software. Do not build the mapping on
  `APPL_TYPE`; at best it contributes a weak secondary signal
  (`AIAWSWLK`-typed jobs exist but are the exception, not the census).
- **`CMD_LINE` is the real signal.** The Phase C command/script parser
  (`drydocs/controlm/commands.py` → typed `STG_INVOCATION` rows) already
  decomposes `CMD_LINE`; product detection = an invocation-pattern table
  (e.g. Ab Initio `air`/`m_run`-style launchers, Informatica `pmcmd`) keyed to
  registry ids. Harder than a column read, but it measures what actually runs.
- `:Application` nodes already exist keyed on `seal_id` (constraint
  `application_seal`).
- `drydocs-icons/manifest.json` ids double as `Vendor.id` — the brand axis is
  already enumerated and stays purely visual.
- `reference/REGISTRY.yaml` remains the *docs index* (where to read about a
  platform); it gains a `product: <registry-id>` cross-link instead of being
  the ersatz registry.

## Phases

- **Phase 0 — ADR 0004 + vocabulary gate. ✅ DONE 2026-07-07** (gate record in
  `config/gate-log.md`): ADR 0004 ACCEPTED (5× Confirm, 0 edits); `Vendor` =
  `org:Organization` (Agent), `SoftwareProduct` = `dd:SoftwareProduct`
  (Entity); `MADE_BY` → `prov:wasAttributedTo`; `USES_SOFTWARE` local edge —
  all registered `status: planned` in `relationship_vocabulary.yaml`
  (`reg_made_by` / `reg_uses_software`). Phases 1 and 2 are ungated.
- **Phase 1 — registry seed + loader. ✅ DONE 2026-07-07** (built, offline-
  verified; the graph write runs when the Docker EE container is wired):
  `config/taxonomy/software-registry.yaml` (6 vendors / 7 products, base list
  above); `SoftwareRegistryLoader` + `RegistryYamlAdapter`
  (`drydocs/loaders/software_registry.py` → `software_registry.cypher`);
  constraints `vendor_id` + `softwareproduct_id`;
  `registry_ontology_supplement.cypher` (+ `drydocs
  apply-registry-supplement` / `drydocs load-software-registry` commands);
  source-registry entry `software-registry` (confirmed, Internal-Public);
  vocabulary entries flipped `planned → active`; guarded by
  `tests/unit/test_software_registry.py` (7 tests).
- **Phase 2 — retire `vendor-bmc` from tooling. ✅ DONE 2026-07-07.**
  Renamed corpus id → `bmc-docs`: `graph-tests/bmc-docs-smoke.yaml`
  (suite id) + `config/gate-prompts/bmc-docs-example.yaml` (spec id) via
  `git mv`; review-labels.yaml prose; the two unit-test references
  (test_gate_pages, test_graph_verify); live doc links (graph-tests README,
  05-backflow, 02-backlog). Baseline-grep → rename → re-grep → tests
  (JobFolder-rename playbook). Historical records (gate-log, ADR text,
  backlog notes, ARCHITECTURE.md pre-restructure paths) left verbatim.
  Icons directory untouched (Brands).
- **Phase 3 — derived app→software edges from `CMD_LINE`.** An
  invocation-pattern → product-id table (inside the registry yaml,
  HITL-confirmed) applied over the command parser's `STG_INVOCATION` output;
  derive `(:Application)-[:USES_SOFTWARE {source:'controlm-cmdline'}]->()`.
  `APPL_TYPE` is explicitly NOT the basis (dead-end, see above). DERIVED
  edges, gate before load — never base ingest.
- **Phase 4 — company-side catalog ingest: DEFERRED until necessary (SME,
  2026-07-07).** The catalog is noisy at product grain (~300 rows per vendor
  search: product + drivers + utilities + every minor version as a row), and
  wholesale ingest buys nothing the four kept fields don't already give.
  Revisit only when a real query needs the governance statuses
  (approved/version-allowed/EOL dates) — then it's an `internal/` source,
  owner SIDs and `gspcId`/`sealId` included, never producer-side.

## Deliberately NOT doing (KISS)

- No `SoftwareVersion` nodes, no per-version status model, until a real query
  needs more than the edge property.
- No relational database — the graph is the lookup; the YAML is the ledger.
- No renaming of `external/orchestration/` paths or the CLAUDE.md tier
  headings; they read fine once "vendor" has a single data meaning.
- No poetry-dependency auto-harvest into the registry (tempting, cute, noisy).

## Risks / open questions

- Invocation-pattern coverage: wrapper scripts hide the real launcher
  (`run_all.sh` telling us nothing) — expect a long tail the pattern table
  can't classify; report unclassified invocations as a coverage metric rather
  than guessing.
- DryDocs-as-Application: needs its own node id producer-side (no SEAL there);
  use a reserved id, company side reconciles to the real SEAL.
- The `bmc-docs` rename touches the drydocs-review back-flow surface — company
  copy holds the real review-labels; coordinate like the back-flow rule
  (port-prompt step 10) so the rename doesn't clobber company data.
