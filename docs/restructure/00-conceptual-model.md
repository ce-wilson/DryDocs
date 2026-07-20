# DryDocs conceptual model — taxonomy → ontology → knowledge graph → context graph

This document fixes the confusion that accumulated as DryDocs grew: knowledge graph, ontology,
and "context" were treated as the same thing. They are four distinct layers. Grounded in the
Neo4j series:

1. https://neo4j.com/blog/knowledge-graph/taxonomy-vs-ontology-vs-knowledge-graph/
2. https://neo4j.com/blog/graph-database/2-of-3-why-graphs-knowledge-graphs-and-context-graphs-matter-to-customers/
3. https://neo4j.com/blog/graph-database/3-of-3-the-graph-ecosystem-bringing-connected-context-to-enterprise-ai/

## The four layers

> "The knowledge graph is what you build; taxonomies and ontologies are the blueprints."
> Graphs answer *what is connected*; knowledge graphs answer *what the connections mean*;
> context graphs answer *what matters right now*.

| # | Layer | Question | DryDocs home | Built from |
|---|-------|----------|--------------|------------|
| 1 | **Taxonomy** | What category is this? | `config/taxonomy/` | imported hierarchies — apps, products, LOB→Product→Team, Oracle schemas, scripts, Control-M variables |
| 2 | **Ontology** | What do the connections mean? | `drydocs_core/schema/`, `drydocs_core/ontology/`, `knowledge/ontology/` | PROV-O matrix + ORG + DPROD + SOSA/SSN + DCAT |
| 3 | **Knowledge graph** | What is connected *and* what does it mean? | the Neo4j graph | loaders applying confirmed mappings |
| 4 | **Context graph** | What matters right now (for this support decision)? | task-scoped projections (future) | temporal state (SOSA/SSN), ownership, permissions, current health |

## Where DryDocs is today
- **Layers 1–3 exist** and are strong: Control-M lineage, SEAL, Catalog, a PROV-O ontology with
  a 9-row matrix and a relationship vocabulary registry.
- **Layer 4 is missing.** What you kept reaching for under the name "knowledge graph" or
  "context" is the **context graph** — the task-scoped, time-aware view that answers a
  production-support question *now*. SOSA/SSN (the `sdw-sosa-ssn` repo) is the standard that
  unlocks it.

## The discipline that prevents drift (the POC problem)
The POC created relationships that did not follow taxonomy/ontology correctly because import and
meaning were done in one step. The fix is a strict order:

```
import as taxonomy  →  classification only, no meaning edges      (taxonomy-importer)
       ↓
map to ontology     →  PROV matrix / standards, SME-confirmed      (ontology-mapper + HITL gate)
       ↓
load                →  loader writes confirmed edges to Neo4j      (loaders)
       ↓
project context     →  task-scoped, time-aware views               (layer 4, future)
```

The configuration layer (`config/`) is the seam between layers 1 and 2: it records every
taxonomy→ontology binding and its confirmation state, so nothing reaches the graph unconfirmed.

## Production-support viewpoint (the lens for every layer)
DryDocs exists to support production & development support. Each layer earns its place by
answering a support question:
- *What runs / depends on what / who owns it* → layers 1–3 (done).
- *Did it run, is it healthy, is the data fresh, who do I call right now* → layer 4 (context).

## Vendors, symmetrically (the BMC-only fix)
The "Claude only considers BMC" failure was structural: BMC had files in the repo; Neo4j,
Oracle, and the standards lived only as skills. Now `reference/` (platforms + standards) and
`external/orchestration/` (BMC baseline + AutoSys/Airflow) make every external source
first-class and symmetrical. See `CLAUDE.md` §2 and `reference/REGISTRY.yaml`.
