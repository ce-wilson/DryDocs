# config/ — the configuration layer for the data pipeline

This is where **taxonomy meets ontology** under SME control. It is data, not code: agents and
loaders read it; the `pipeline-config` sub-agent maintains it; **it never writes the graph
directly.** Every change is reviewable by `git diff`, and ambiguous decisions pause for the SME
via the guided gate (`docs/restructure/03-hitl-sme-flow.md`).

## Files

| File | Purpose |
|------|---------|
| [`precedence.yaml`](precedence.yaml) | The authority order when sources disagree: BMC baseline → internal standards → LOB→Product→Team. |
| [`source-registry.yaml`](source-registry.yaml) | Every pipeline source: orchestrator, adapter, taxonomy fed, confirmed crosswalk, **and its `classification` + `source`**. |
| [`classification.yaml`](classification.yaml) | The sensitivity vocabulary (External / Internal-Public / Internal; 3 levels since the J23 collapse 2026-07-31) that drives the GitHub publish boundary. Required on every source. |
| [`taxonomy-ontology-map.yaml`](taxonomy-ontology-map.yaml) | The HITL-confirmed bindings: "this imported taxonomy → apply this ontology rule." |
| `taxonomy/` | Imported raw hierarchies (apps, products, schemas, scripts, variables, LOB→Product→Team) as **pure classification** — no meaning-bearing edges yet. |
| [`gate-log.md`](gate-log.md) | **Append-only** record of every HITL gate decision. |
| `gate-prompts/` | SME gate-prompt specs (`drydocs.gate-prompt.v1`) — one per pending/decided gate; rendered to interactive gate pages by `drydocs/review/gate_pages.py`. |
| `source-mappings/` | Per-source column ledgers (doc 08): every profiled column → projected / filter-only / excluded / deferred, with census reconciliation. |
| `crosswalks/` | Orchestrator vendor→baseline term crosswalks (BMC is the baseline). |
| `manual-loads/` | SME-authored CSV mappings — the tier-5 manual final option (manifest-gated). |
| `overrides/` | User override lists (the M2 origin-flagged store): committed CSVs materialized into the mapping store with origin flags. |
| [`audit-fields.yaml`](audit-fields.yaml) | Per-source HITL-gated audit envelope definitions (doc 06). |
| [`review-labels.yaml`](review-labels.yaml) | Source → DATA-label review backbone consumed by `drydocs-review`. |
| [`doc-source-registry.yaml`](doc-source-registry.yaml) | Registry of ingested documentation sources (doc-ingestion track). |
| [`dev-environment.yaml`](dev-environment.yaml) | Single source of truth for local dev/test Neo4j container/DB names + ports (drift-guarded). |

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

## The three axes (don't conflate them)
Every ingested source carries three independent labels:
1. **Precedence authority** ([`precedence.yaml`](precedence.yaml)) — *which source wins on conflict*.
2. **Provenance tier** (in each `SOURCE-MANIFEST`) — *trust*: vendor's words vs Claude inference
   (`VERBATIM`/`GROUNDED`/`SYNTHESIZED`), decided at ingestion.
3. **Sensitivity classification** ([`classification.yaml`](classification.yaml)) — *who may see it /
   may it be published*. Drives the GitHub publish boundary. **Required on every source**, enforced
   by `tests/unit/test_classification.py`.
