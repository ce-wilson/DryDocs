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
| Semantic layer from a warehouse | [Neo4j: Build a Semantic Layer from GCP with NeoCarta](https://neo4j.com/blog/genai/build-a-semantic-layer-from-gcp-with-neocarta/) | Neo4j Labs build of exactly our data-catalog layer — crosswalk below |
| GraphRAG (book) | [Essential GraphRAG — Knowledge Graph-Enhanced RAG](https://www.manning.com/books/essential-graphrag) (Bratanič & Hane, Manning 2025; Neo4j-sponsored ebook — local PDF gitignored at repo root, cite don't commit; link verified 2026-07-16) | worked lexical-graph + graph-retrieval patterns; input to the docmeta P0 benchmark verdict and the agent-traversal experiment (backlog Q1/Q2) |
| Catalog + glossary as one governed object model | [Databricks Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/) — full notes: [`databricks-unity-catalog.md`](databricks-unity-catalog.md) (links verified 2026-07-25) | vendor build of the layer in `docs/patterns/data-catalog/`; its Domains / Glossary / governed tags / classification land on our `CatalogDataDomain` / `CatalogBusinessTerm` / `CatalogTag` / `classification.yaml` — plus lineage derived from execution plans, never declared |

Verified 2026-06-21 (A3). Add new rows as research is consulted; cite them in ADRs under `docs/`.

## NeoCarta — context for the data-catalog layer

[NeoCarta](https://neo4j.com/blog/genai/build-a-semantic-layer-from-gcp-with-neocarta/)
is a Neo4j Labs **Python library + MCP server** that auto-generates a semantic-layer
graph from a cloud warehouse for agent-driven query routing and data discovery. It is
the closest public parallel to our `docs/patterns/data-catalog/` work — same shape, a
different source vendor (GCP instead of Control-M/Oracle).

**Its model (two subgraphs):**
- **Metadata subgraph:** `Database → Schema → Table → Column` — built from BigQuery,
  plus relationships *inferred from query-log JOIN/CTE patterns*.
- **Glossary subgraph:** `Glossary → Category → BusinessTerm` — built from Dataplex,
  linked to the metadata via `TAGGED_WITH` (BusinessTerm → Table/Column).
- **Retrieval:** vector + full-text indexes on Tables/Columns/BusinessTerms; hybrid
  search (vector + full-text + business-term traversal), normalized and ranked.

**Crosswalk to DryDocs (why it matters here):**
| NeoCarta | DryDocs analogue |
|---|---|
| `Database→Schema→Table→Column` | DataHub `Schema→Field→Element` (`docs/patterns/data-catalog/ontology-standard.md`) |
| `Glossary→Category→BusinessTerm` + `TAGGED_WITH` | `CatalogBusinessTerm` / `CatalogTag` glossary terms |
| Relationships inferred from query-log JOINs | our lineage from Control-M conditions / script reads-writes |
| OSI YAML semantic-interchange files | our `config/taxonomy-ontology-map.yaml` bridge |
| Hybrid vector + full-text + term search | candidate retrieval pattern for the layer-4 context graph |

**Takeaways for us:** (1) validates a **graph-native catalog + glossary, linked**, as
the right structure; (2) **query logs as a lineage source** — relevant once we ingest
Oracle/Snowflake SQL, complementing orchestration-derived lineage; (3) it leans on
**embeddings/hybrid search, not formal RDF/OWL** — consistent with ADR 0001's LPG-first,
cite-don't-seed stance. It uses **no formal ontology** (no PROV/DCAT), so it is a *tool
pattern* to borrow from, not a *standard* to seed.

**Companion:** [`databricks-unity-catalog.md`](databricks-unity-catalog.md) covers the other
public build of this layer. NeoCarta is the closer *architectural* parallel (a graph, built
from a warehouse); Unity Catalog is the closer *governance* parallel (glossary, domains, and
policy-enforced tags in one object model, with lineage derived from execution plans). Same
verdict on both: tool pattern to borrow, not a standard to seed.
