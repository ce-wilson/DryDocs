# ADR 0004 — "Vendor" means the brand: software registry terminology and model

```yaml
status: ACCEPTED        # gate-confirmed 2026-07-07 (config/gate-log.md)
date: 2026-07-07
deciders: [chad.wilson, SME-gate]
layer: 2-ontology
affects:
  - docs/restructure/07-software-registry.md    # the plan this ADR ungates
  - drydocs/ontology/relationship_vocabulary.yaml
  - config/review-labels.yaml                   # Phase 2: vendor-bmc → bmc-docs
  - config/gate-prompts/                        # Phase 2 rename
  - graph-tests/                                # Phase 2 rename
```

## Context

The 2026-07-06 terminology audit found "vendor" carrying five meanings in the
repo: the Tier-2 orchestration category (BMC/AutoSys/Airflow), the trust axis
("vendor's words" vs Claude inference), the `vendor-bmc` corpus id baked into
review tooling, the brand registry (`drydocs-icons/vendors/` — which includes
Neo4j, Oracle, Snowflake), and loose module-speak ("the vendor domain" =
`drydocs/controlm/`). Meanwhile Oracle and Neo4j — software we depend on as
much as BMC — had no registry classification at all. The company's internal
software library demonstrates the target shape: Vendor → Vendor Product with
category/version metadata, queryable ("which applications use Ab Initio?").

## Decision

1. **"Vendor" = the brand/company only.** A `:Vendor` node
   (`org:Organization`, prov Agent), ids shared with the `drydocs-icons`
   manifest — the icons directory keeps its name because it already means
   Brands.
2. **`:SoftwareProduct`** (`dd:SoftwareProduct` local class, prov Entity) is
   what a vendor ships. Its `role` attribute
   (`orchestrator | data-platform | graph-platform | tool`) **absorbs the
   Tier-1/Tier-2 split** — the tiers stay in CLAUDE.md as reading guidance,
   but the classification lives in data.
3. **Edges:** `(SoftwareProduct)-[:MADE_BY]->(Vendor)` maps to
   `prov:wasAttributedTo` (Entity → Agent matrix row).
   `(Application)-[:USES_SOFTWARE {version, source, status}]->(SoftwareProduct)`
   is a **local domain edge** (`prov_maps_to: ~`) — PROV has no Agent → Entity
   usage row; precedent `arch_contains`. Both registered `status: planned`
   until the Phase 1 supplement + loader exist.
4. **Trust-axis prose stops saying "vendor's words."** The manifests'
   VERBATIM / GROUNDED / SYNTHESIZED tiers already carry that meaning; new
   prose uses "the source's own words."
5. **The `vendor-bmc` tooling id is renamed `bmc-docs`** (it names a
   documentation corpus, not a vendor relationship) — review-labels,
   gate-prompts, graph-tests, tests, docs; mechanical rename per the
   ControlMFolder playbook; coordinate with the company back-flow rule
   (port-prompt step 10). Icons untouched.

## Consequences

- One meaning per word: vendor = brand; product roles are data; the registry
  YAML (`config/taxonomy/software-registry.yaml`) is the ledger and the graph
  is the lookup — no relational sidecar.
- "Which applications use Ab Initio / Oracle 19" becomes a one-hop query once
  plan-07 Phases 1–3 land (CMD_LINE-derived edges; APPL_TYPE is a recorded
  dead-end).
- `reference/REGISTRY.yaml` stays the docs index and gains `product:` id
  cross-links instead of being the ersatz registry.

## Follow-up (small, bounded)

1. Plan-07 Phase 1: seed `software-registry.yaml` (base list in the plan),
   schema test, loader, constraints, supplement blocks for the two edges.
   ✅ Done 2026-07-07 (`caa1e79`).
2. Plan-07 Phase 2: execute the `vendor-bmc` → `bmc-docs` rename
   (baseline-grep → rename → re-grep → tests). ✅ Done 2026-07-07.
3. Sweep trust-axis prose for "vendor's words" phrasing when files are next
   touched (not a dedicated pass).
