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

```yaml
# config/taxonomy/software-registry.yaml  (shape sketch)
schema: drydocs.software-registry.v1
classification: Internal-Public          # producer copy: DryDocs' own stack only
vendors:
  - id: bmc            # matches drydocs-icons manifest id
    name: BMC Software
products:
  - id: controlm
    vendor: bmc
    name: Control-M
    role: orchestrator
    type: commercial
  - id: neo4j
    vendor: neo4j
    name: Neo4j
    role: graph-platform
    type: commercial   # EE via Docker; community edition open-source
  - id: oracle-db
    vendor: oracle
    name: Oracle Database
    role: data-platform
    type: commercial
```

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

- **Phase 0 — ADR 0004 + vocabulary gate.** One short ADR fixing the words:
  Vendor = brand; SoftwareProduct with `role` attribute; trust-axis prose stops
  saying "vendor's words" (the manifests' VERBATIM/GROUNDED/SYNTHESIZED tiers
  already carry that meaning); Tier-2 heading stays but is documented as a role
  value. Register `Vendor`/`SoftwareProduct`/`USES_SOFTWARE`/`MADE_BY` in
  `relationship_vocabulary.yaml` as `status: planned` → HITL gate.
- **Phase 1 — registry seed + loader.** `software-registry.yaml` with DryDocs'
  own stack (~10 rows); schema unit test (like `test_backlog`/classification);
  small loader MERGEs `(:Vendor)`, `(:SoftwareProduct)-[:MADE_BY]->(:Vendor)`,
  and DryDocs' own `USES_SOFTWARE` edges. Constraints: `vendor_id`,
  `softwareproduct_id`.
- **Phase 2 — retire `vendor-bmc` from tooling.** Rename corpus id →
  `bmc-docs` across review-labels.yaml, `config/gate-prompts/`, `graph-tests/`,
  the four unit tests, docs. Baseline-grep → rename → re-grep → tests
  (JobFolder-rename playbook). Icons directory untouched (Brands).
- **Phase 3 — derived app→software edges from `CMD_LINE`.** An
  invocation-pattern → product-id table (inside the registry yaml,
  HITL-confirmed) applied over the command parser's `STG_INVOCATION` output;
  derive `(:Application)-[:USES_SOFTWARE {source:'controlm-cmdline'}]->()`.
  `APPL_TYPE` is explicitly NOT the basis (dead-end, see above). DERIVED
  edges, gate before load — never base ingest.
- **Phase 4 — company-side catalog ingest (optional, company repo).** The
  internal software library exports; ingest as an `internal/` source with its
  statuses (approved/version-allowed/governed-by) as properties. Producer keeps
  only the schema slot. This is where "which apps are on Oracle **19**" gets
  real version data; producer-side the version stays an edge property.

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
