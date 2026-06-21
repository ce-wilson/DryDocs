# reference/research/ — academic & industry research

Papers, specs, and write-ups that justify modeling decisions. Cite these in ADRs
(`docs/`) rather than re-arguing from scratch. Keep entries as links + a one-line "why it
matters"; do not paste copyrighted full texts.

## Seed reading list (fill in as you go)

| Topic | Reference (link) | Why it matters |
|-------|------------------|----------------|
| Taxonomy vs ontology vs KG | [Neo4j: Taxonomy vs Ontology vs Knowledge Graph](https://neo4j.com/blog/knowledge-graph/taxonomy-vs-ontology-vs-knowledge-graph/) | the layer model (taxonomy → ontology → KG) in `docs/restructure/00-conceptual-model.md` |
| Why context matters (2 of 3) | [Neo4j: Why graphs, knowledge graphs & context graphs matter](https://neo4j.com/blog/graph-database/2-of-3-why-graphs-knowledge-graphs-and-context-graphs-matter-to-customers/) | defines the **context graph** (layer 4) — "what matters right now" |
| The graph ecosystem (3 of 3) | [Neo4j: The graph ecosystem — connected context for enterprise AI](https://neo4j.com/blog/graph-database/3-of-3-the-graph-ecosystem-bringing-connected-context-to-enterprise-ai/) | connected-context architecture; positions the KG as middleware to AI |
| Provenance | [W3C PROV-O Primer](https://www.w3.org/TR/prov-primer/) · [PROV-O](https://www.w3.org/TR/prov-o/) | the 9-row decision matrix (`reference/standards/prov-o/`) |
| Sensor / observation / time | [W3C SSN/SOSA](https://www.w3.org/TR/vocab-ssn/) (mirror: `../../../sdw-sosa-ssn`) | the temporal context layer (`reference/standards/sosa-ssn/`) |
| Org structure | [W3C ORG ontology](https://www.w3.org/TR/vocab-org/) | Membership/Role/OrgUnit for SEAL + LOB→Product→Team |
| Agent memory on graphs | [Neo4j Agent Memory (POLE+O)](https://neo4j.com/labs/) — see `neo4j-skills:neo4j-agent-memory-skill` | context-graph retrieval pattern for layer 4 |

Verified 2026-06-21 (A3). Add new rows as research is consulted; cite them in ADRs under `docs/`.
