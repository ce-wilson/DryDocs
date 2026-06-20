# reference/research/ — academic & industry research

Papers, specs, and write-ups that justify modeling decisions. Cite these in ADRs
(`docs/`) rather than re-arguing from scratch. Keep entries as links + a one-line "why it
matters"; do not paste copyrighted full texts.

## Seed reading list (fill in as you go)

| Topic | Reference | Why it matters |
|-------|-----------|----------------|
| Taxonomy vs ontology vs KG | Neo4j blog: *Taxonomy vs Ontology vs Knowledge Graph* | the layer model in `docs/restructure/00-conceptual-model.md` |
| Context graphs for enterprise AI | Neo4j blog series 2/3 + 3/3 (*Why graphs… matter*, *The graph ecosystem*) | layer 4 (context) + the connected-context architecture |
| Provenance | W3C PROV-O primer | the decision matrix |
| Sensor/observation/time | W3C SSN/SOSA (`../standards/sosa-ssn/`) | the temporal context layer |
| Agent memory on graphs | Neo4j Agent Memory (POLE+O) | context-graph retrieval pattern |

> Source URLs for the three Neo4j blogs are recorded in
> `docs/restructure/00-conceptual-model.md`.
