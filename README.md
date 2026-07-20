# drydocs

Personal sandbox where I try out graph data modeling ideas. Started as a way to
actually learn Neo4j instead of just following tutorials, and has since collected
a bunch of half-finished experiments.

Rough map of what's in here:

- **Property-graph schema experiments** — Cypher schema drafts in
  `drydocs_core/schema/`, plus an attempt at keeping a relationship vocabulary
  honest in `drydocs_core/ontology/`.
- **Taxonomy vs. ontology** — turns out *classifying things* and *giving edges
  meaning* are different problems. Notes in `docs/`, config-driven mapping
  experiments in `config/`.
- **Semantic-web standards reading** — PROV-O, W3C ORG, SKOS, DCAT, SOSA
  summaries under `reference/standards/`, so I don't have to keep re-reading
  the specs.
- **Job-scheduler metadata parsing** — `external/orchestration/` mirrors public
  vendor docs that I use as test input for hierarchy-import experiments.
- **A CLI** that glues the experiments together: `poetry run drydocs --help`.

## Running it

```
poetry install
poetry run pytest -q
```

The tests are mostly how I check that the graph-loading experiments still hold
together after I change something.

Nothing here is intended for production use. Expect churn, dead ends, and
inconsistent naming while I figure out what I'm doing.
