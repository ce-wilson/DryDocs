# config/ — the configuration layer for the data pipeline

This is where **taxonomy meets ontology** under SME control. It is data, not code: agents and
loaders read it; the `pipeline-config` sub-agent maintains it; **it never writes the graph
directly.** Every change is reviewable by `git diff`, and ambiguous decisions pause for the SME
via the guided gate (`docs/restructure/03-hitl-sme-flow.md`).

## Files

| File | Purpose |
|------|---------|
| [`precedence.yaml`](precedence.yaml) | The authority order when sources disagree: BMC baseline → internal standards → LOB→Product→Team. |
| [`source-registry.yaml`](source-registry.yaml) | Every pipeline source: which orchestrator, which adapter, which taxonomy it feeds, confirmed crosswalk. |
| [`taxonomy-ontology-map.yaml`](taxonomy-ontology-map.yaml) | The HITL-confirmed bindings: "this imported taxonomy → apply this ontology rule." |
| `taxonomy/` | Imported raw hierarchies (apps, products, schemas, scripts, variables, LOB→Product→Team) as **pure classification** — no meaning-bearing edges yet. |

## The flow this layer enables

```
import (taxonomy-importer)          →  config/taxonomy/*          (classification only)
   │
propose mapping (ontology-mapper)   →  taxonomy-ontology-map.yaml (status: proposed)
   │
SME confirms (guided gate)          →  status: confirmed
   │
loader applies ontology             →  Neo4j knowledge graph
```

No taxonomy becomes graph edges until its mapping is `confirmed`. This is the fix for the POC
problem where relationships were created that did not follow taxonomy/ontology correctly.

## Precedence in one sentence
When two sources describe the same thing differently, the **higher-precedence authority wins**,
and the loser is recorded as an alias/closeMatch — never silently dropped.
