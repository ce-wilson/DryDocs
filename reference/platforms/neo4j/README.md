# Neo4j — the graph platform

Neo4j is the base of the DryDocs knowledge graph. **It is the platform the whole project is
built on** — historically under-referenced because, unlike BMC, it had no files in the repo.
This directory fixes that: it is Neo4j's first-class home alongside the orchestration vendors.

## Call the skill first — and WHICH one depends on the venue

**Getting this wrong means no Neo4j lens loads at all, silently.** A filesystem skill
loads everywhere; a plugin loads only under Claude Code.

| Venue | Route |
|-------|-------|
| **any venue** (VS Code / Copilot included) | [`.claude/skills/neo4j-db/`](../../../.claude/skills/neo4j-db/SKILL.md) — the repo-local skill |
| **Claude Code**, additionally | the `neo4j-skills` plugin below, for version-current vendor Neo4j |

The repo-local skill carries what is true of *this* graph: the two-database topology, the
client-side statement splitting, the Cypher-25 empty-statement boundary, the retired
databases, and the failure modes this project has already paid for. The plugin carries
general, version-current Neo4j practice. **They are complements, not substitutes.**

Plugin skills by task (**Claude Code only** — every row below resolves to nothing
elsewhere):

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


## Reference repos
- https://github.com/neo4j/neo4j
- https://github.com/neo4j/neo4j-graphrag-python
- https://github.com/neo4j/graph-data-science
- https://github.com/neo4j-labs/llm-graph-builder

## DryDocs-specific Neo4j facts
- Server: **`neo4j:2026.05.0-enterprise`** — the pin in `config/dev-environment.yaml`,
  guarded. NOT 5.x: the store was written by 2026.05.0 and cannot be downgraded. The
  `neo4j = "^5.20"` in `pyproject.toml` is the PYTHON DRIVER floor (resolves 5.28.4) and
  is not a server tag; conflating the two has produced defects.
- **APOC** is required, and its whole live surface here is two procedures: `apoc.text.join`
  in the vendor-docs loader, and `apoc.version()` as the install probe. **`apoc.cypher.runMany`
  is called NOWHERE** — dropped at D5 (2026-07-18) because it splits on semicolons inside
  comments and silently no-ops DDL. Multi-statement scripts split CLIENT-SIDE through
  `drydocs_core/cypher_split.py`.
- Connection: `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` from `.env`.
- The ontology backbone (PROV-O terms + supplements) is applied by `drydocs bootstrap` and
  the `apply-*-supplement` commands. See `drydocs_core/schema/`.
