# DCMI Metadata Terms (Dublin Core, `dct:`)

**IRI:** `http://purl.org/dc/terms/` · **Spec:** https://www.dublincore.org/specifications/dublin-core/dcmi-terms/

Adopted 2026-08-04 (gate `envelope-property-terms`, backlog M4) for **property-level
authorship bindings** on the source audit envelope — the four frozen node properties
in `config/audit-fields.yaml`:

| Envelope property | DCMI term | Note |
|---|---|---|
| `source_created_by` | `dct:creator` | No personhood required — a team Functional ID (org-agent) is conformant. |
| `source_created_at` | `dct:created` | "Date of creation of the resource." |
| `source_updated_by` | `dct:contributor` | **Nearest term** — DCMI defines no "modifier"; the stretch is recorded in the registry note by ruling. |
| `source_updated_at` | `dct:modified` | "Date on which the resource was changed." |

The registry of record is the `property_terms` section of
[`drydocs_core/ontology/relationship_vocabulary.yaml`](../../../drydocs_core/ontology/relationship_vocabulary.yaml);
the `dct:` prefix expands via `drydocs_core/ontology/namespaces.py`.

## Discipline

- The bindings are **documentation-grade**: they state meaning for crosswalks and
  future RDF export. No edges, no loader changes, no `dct:` OntologyTerm nodes are
  seeded by `ontology.cypher`.
- SOSA is ruled OUT for authorship provenance (gate §A2) — observation vocabulary
  models measurement acts, not record editing.
- New property→term bindings go through the HITL gate like any other meaning
  decision, and land in `property_terms`, never in prose.
