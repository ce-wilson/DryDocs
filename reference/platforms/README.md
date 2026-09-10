# reference/platforms/ — the platforms DryDocs is built on

| Platform | Role | Primary reference |
|----------|------|-------------------|
| **Neo4j** | graph database (the KG itself lives here) | [`.claude/skills/neo4j-db/`](../../.claude/skills/neo4j-db/SKILL.md) (every venue) + [`neo4j/`](neo4j/README.md); the `neo4j-skills:*` plugin **under Claude Code only** |
| **Oracle** | source system (Control-M `psgmgr` views) + `DRYDOCS_STG` staging | [`.claude/skills/oracle-db/`](../../.claude/skills/oracle-db/SKILL.md) — the repo-local skill; the `db@oracle-skills` vendor plugin is a different thing and is disabled |
| **ServiceNow** | source system (CMDB/CSDM + the company TOM model), read through a Snowflake replica | public CMDB docs — see `REGISTRY.yaml#servicenow`; instance evidence in `knowledge/upgrade-plans/servicenow-replica-evidence.md` |
| **Snowflake** | placeholder for DryDocs' own use — but ALREADY LIVE as the **carrier** of the ServiceNow replica | no live route: `neo4j-skills:neo4j-snowflake-graph-analytics-skill` is outside the local keep-10 AND disabled, so it loads in no venue today |
| **git** | code/authorship provenance + mirrored modeling-reference repos | `gh` CLI |

## How agents should use these

1. **Neo4j work** (Cypher, modeling, import, GraphRAG, vector, GDS): start with the
   repo-local [`neo4j-db`](../../.claude/skills/neo4j-db/SKILL.md) skill — it is
   authoritative for *this* graph's topology, dialect boundary and failure modes, and it
   loads in every venue. **Under Claude Code**, add the matching `neo4j-skills:` plugin
   skill for version-current vendor Neo4j; under a venue with no plugin loader that
   route resolves to nothing.
2. **Oracle work** (extract SQL, staging DDL, tuning): use the repo-local
   [`oracle-db`](../../.claude/skills/oracle-db/SKILL.md) skill.
3. Record any non-obvious platform fact you discover in [`../REGISTRY.yaml`](../REGISTRY.yaml)
   so the next agent doesn't re-derive it.

Oracle/Snowflake are *data sources*; their **instance-specific** schema details (real table
names, SIDs) are confidential and belong in `internal/`, never here.
