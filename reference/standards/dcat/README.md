# DCAT — Data Catalog Vocabulary (`dcat:`)

**IRI:** `http://www.w3.org/ns/dcat#` · **Spec (source_url):** https://www.w3.org/TR/vocab-dcat-3/
· **Captured:** 2026-08-07 (A4 — this per-standard page; the registry row predates it)

Classification: External (public W3C recommendation; cite the spec URL).

DCAT is the W3C vocabulary for data catalogs: `dcat:Catalog` describes the catalog,
`dcat:Dataset` the data being cataloged, `dcat:Distribution` a concrete access form of a
dataset, `dcat:DataService` an access endpoint, `dcat:CatalogRecord` the catalog's own
entry about a dataset (the record-vs-thing split DryDocs leans on when modeling the
enterprise data catalog *about* datasets it does not itself hold).

## Where DryDocs uses it

| Term | Use in this repo |
|---|---|
| `dcat:Dataset` | The `asset_type` stamped on (nearly) every dataset row in `config/source-registry.yaml` — the v2 registry's statement that a row is a cataloged dataset, not a system. |
| `dcat:Distribution` | The enterprise-catalog crosswalk: the catalog's distributions view (`catalog@[db].[schema].distributions_v`) maps concrete placements (S3/Glue/warehouse) to this class. |
| `dcat:DataService` / `dcat:Catalog` / `dcat:CatalogRecord` | Data-catalog domain crosswalk (`config/taxonomy-ontology-map/30-mappings-catalog.yaml` area) — the catalog itself, its services, and its records about datasets. |
| `dcat:contactPoint` | The email-DL contact-point direction (gate `email-dl-contact-point`, pending) — how an ownership DL attaches to a dataset/application without minting a person. |
| `dcat:mediaType` | Media-type facet on captured artifacts (doc/code snapshot adapters). |

The prefix expands via
[`drydocs_core/ontology/namespaces.py`](../../../drydocs_core/ontology/namespaces.py);
crosswalk entries live in the taxonomy-ontology map and the relationship-vocabulary
registry, never in prose.

## Discipline

- Documentation-grade bindings, same rule as `dct:` (see
  [`../dcmi-terms/README.md`](../dcmi-terms/README.md)): they state meaning for
  crosswalks and future RDF export; no loader writes a `dcat:` edge because this page
  says so.
- New `dcat:` term adoptions go through the HITL gate like any other meaning decision
  and land in the registries, with this page updated to match — not the reverse.
- DPROD (the EKGF data-product profile, [`../dprod-ekgf/`](../dprod-ekgf/README.md))
  builds ON DCAT; where both could apply, the crosswalk names which profile a term was
  adopted from.
