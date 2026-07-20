# Neo4j — the graph platform

Neo4j is the base of the DryDocs knowledge graph. **It is the platform the whole project is
built on** — historically under-referenced because, unlike BMC, it had no files in the repo.
This directory fixes that: it is Neo4j's first-class home alongside the orchestration vendors.

## Call the skills first

The `neo4j-skills` plugin is the authoritative, version-current reference. Pick by task:

| Task | Skill |
|------|-------|
| Write/optimize Cypher | `neo4j-skills:neo4j-cypher-skill` |
| Design/refactor the graph model | `neo4j-skills:neo4j-modeling-skill` |
| Structured import (CSV/LOAD CSV/admin import) | `neo4j-skills:neo4j-import-skill` |
| Document/entity import (KG from text) | `neo4j-skills:neo4j-document-import-skill` |
| GraphRAG retrieval | `neo4j-skills:neo4j-graphrag-skill` |
| Vector index / embeddings | `neo4j-skills:neo4j-vector-index-skill` |
| Graph algorithms | `neo4j-skills:neo4j-gds-skill` |
| Python driver | `neo4j-skills:neo4j-driver-python-skill` |
| Query tuning / EXPLAIN-PROFILE | `neo4j-skills:neo4j-query-tuning-skill` |
| Aura provisioning / agents / analytics | `neo4j-skills:neo4j-aura-*-skill` |
| Agent memory / context graphs (POLE+O) | `neo4j-skills:neo4j-agent-memory-skill` |

## Reference repos
- https://github.com/neo4j/neo4j
- https://github.com/neo4j/neo4j-graphrag-python
- https://github.com/neo4j/graph-data-science
- https://github.com/neo4j-labs/llm-graph-builder  (mirrored locally at `../../../llm-graph-builder`)

## DryDocs-specific Neo4j facts
- Server: Neo4j 5.x with **APOC** (loaders use `apoc.cypher.runMany`). Target 2025.x/2026.x.
- Connection: `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` from `.env`.
- The ontology backbone (PROV-O terms + supplements) is applied by `drydocs bootstrap` and
  the `apply-*-supplement` commands. See `drydocs_core/schema/`.
