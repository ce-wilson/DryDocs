# reference/ — Tier 1: source platforms you build WITH

External knowledge used to **build and reason about** DryDocs. Not graph content, not
something we ingest rows from — the platforms and standards the project is *built on top of*.

Distinct from [`../external/orchestration/`](../external/orchestration/README.md) (Tier 2 —
the orchestrators we ingest *from*, one level lower in the data pipeline).

| Subdir | What it is |
|--------|-----------|
| [`platforms/`](platforms/README.md) | Neo4j (graph platform), Oracle & Snowflake (data platforms), git |
| [`standards/`](standards/README.md) | Ontology standards: PROV-O, W3C ORG, DPROD, **SOSA/SSN**, DCAT, SKOS |
| [`research/`](research/README.md) | Academic papers backing modeling choices |

The machine-readable index is [`REGISTRY.yaml`](REGISTRY.yaml) — agents consult it to find the
right reference before writing code. The `reference-librarian` sub-agent keeps it current.

**All of this is PUBLIC knowledge** and stays in the repo when it is published.
