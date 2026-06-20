# DPROD (EKGF Data Product Ontology)

**IRI:** `https://ekgf.github.io/dprod/` (EKGF working default pending a corporate IRI).
Models data products and their **Ports**.

## DryDocs usage
- `Application` `HAS_PORT` `Port`, where Port kind is `EventProcessing` or `BatchProcessing`
  (stored as a node property). This is the two-port model in the SEAL domain.
- Treat Ports as the data-product interface boundary when reasoning about lineage between
  applications and the batch graph.

See the SEAL block (`seal_has_port`) in `relationship_vocabulary.yaml`.
