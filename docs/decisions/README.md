# docs/decisions — architecture decision records (ADRs)

The durable record of *why the architecture is what it is*. Each ADR states the
decision, the options considered, and — deliberately kept discoverable — **the
alternatives that were rejected**, so they are not re-litigated in a future
session that never opens the ADR body.

| ADR | Decision |
|---|---|
| [0001 — ontology base scope](0001-ontology-base-scope.md) | PROV-O/ORG/DPROD-grounded ontology base; what the graph's edges are allowed to mean |
| [0002 — component & database topology](0002-component-database-topology.md) | Monorepo of components on `drydocs-core`; Enterprise multi-DB (`drydocs` ground truth vs `drydocs_context` uncertain) joined by a composite |
| [0002-a — drydocs-core extraction plan](0002-a-drydocs-core-extraction-plan.md) | Staged core/component split behind the `drydocs_core` shim; boundary enforced by `tests/unit/test_module_boundary.py` |
| [0002-b — spinoff rebase checklist](0002-b-spinoff-rebase-checklist.md) | `controlm-spinoff` → `drydocs-remediation` re-home flow |
| [0002-c — depgraph lineage re-home](0002-c-depgraph-lineage-rehome.md) | `depgraph@feat/controlm-lineage` absorbed as `drydocs-lineage`; one parser in core (delta fold = backlog G8, done) |
| [0003 — "Application" naming disambiguation](0003-application-naming-disambiguation.md) | Source terms verbatim on source nodes; `:Application` stays the SEAL-keyed canon; reconcile by relationship; bind renderers substitute in code regions only (comments/strings verbatim); BMC labels take the `ControlM` prefix (`JobFolder` → `ControlMFolder`) |
| [0004 — "Vendor" means the brand](0004-software-registry-vendor-terminology.md) | Software registry: `:Vendor` (org:Organization) = brand only; `:SoftwareProduct.role` absorbs the Tier-1/Tier-2 split; `MADE_BY` → prov:wasAttributedTo, `USES_SOFTWARE` local; `vendor-bmc` tooling id → `bmc-docs`; icons stay Brands |
| [0005 — browser ↔ Neo4j access path](0005-browser-neo4j-access-path.md) | Thin API is the deployment shape (server-side creds, read-only + DB routing, SSO home, layer-4 projections); bolt-from-browser survives only as a dev-mode adapter behind one `GraphAccess` seam in `web/src/lib/` |

## Rejected alternatives worth not re-litigating (ADR 0002, "Options Considered")

Three roads deliberately not taken — each was rejected for a *structural* reason,
not taste; re-proposing one means arguing against the reason, not rediscovering it:

1. **Community single DB** (+ `reliability` property + `:Candidate` label
   namespace) — rejected because it **commingles trust**: uncertain and curated
   nodes share one transaction domain and one bad query promotes noise into
   ground truth. The trust boundary must be structural (separate DBs), not a
   property filter.
2. **One capability, two `--mode` flags** — rejected because a single process
   writing to either DB on a flag is exactly the commingling risk the multi-DB
   split removes; **a flag bug crosses the trust boundary**. Two components
   (`drydocs-lineage` → `drydocs`; `drydocs-deepdoc` → `drydocs_context`) make
   the boundary structural.
3. **Polyrepo** (one repo per component, core published as a dependency) —
   rejected *for now*: stronger isolation but heavy version/dependency
   management for a small team. Monorepo + `drydocs-core` gives DRY sharing with
   independent run/deploy. Revisit only if a component needs an independent
   release cadence.

(A fourth D1 variant — separate DBMS instances + app-side join — fell for
violating the "no app-side data layer" invariant; the Enterprise composite does
the join natively.)

Full context, trade-off analysis, and consequences: [ADR 0002](0002-component-database-topology.md).
