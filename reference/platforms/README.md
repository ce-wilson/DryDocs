# reference/platforms/ — the platforms DryDocs is built on

| Platform | Role | Primary reference |
|----------|------|-------------------|
| **Neo4j** | graph database (the KG itself lives here) | `neo4j-skills:*` plugin + [`neo4j/`](neo4j/README.md) |
| **Oracle** | source system (Control-M `psgmgr` views) + `DRYDOCS_STG` staging | Oracle `db:` skill |
| **Snowflake** | future data platform (placeholder) | `neo4j-skills:neo4j-snowflake-graph-analytics-skill` |
| **git** | code/authorship provenance + mirrored modeling-reference repos | `gh` CLI |

## How agents should use these

1. **Neo4j work** (Cypher, modeling, import, GraphRAG, vector, GDS, Aura): use the matching
   `neo4j-skills:` skill *first* — it is authoritative for current Neo4j (2025.x/2026.x).
2. **Oracle work** (extract SQL, staging DDL, tuning): use the `db:` skill.
3. Record any non-obvious platform fact you discover in [`../REGISTRY.yaml`](../REGISTRY.yaml)
   so the next agent doesn't re-derive it.

Oracle/Snowflake are *data sources*; their **instance-specific** schema details (real table
names, SIDs) are confidential and belong in `internal/`, never here.
