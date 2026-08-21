# Business glossary — the SCHEMA half (Internal-Public)

**Status: scaffold (G34, 2026-08-21) + public senses.** This directory holds the *shape* of the DryDocs
business glossary and the few senses that are safe to publish; company-specific senses never live here. Reserved so the internal port cannot
collide on a name or a backlog slot (gate `business-application-identity` §F2, 2026-07-27).

## The split

| Half | Where | Classification | Ports to the company repo? |
|---|---|---|---|
| Schema — label, key, edge terms, YAML shape | `config/glossary/schema.yaml` (this dir) | Internal-Public | yes |
| Public senses — expansion AND source are public (first entry: `DRY`, the project's own name) | `config/glossary/terms-public.yaml` (this dir) | Internal-Public | yes |
| Definitions — the actual senses, expansions, does-NOT-mean notes | `internal/glossary/terms.yaml` | Internal | no (excluded before any public push) |
| Industry-standard terms | bind to SKOS (`reference/standards/` — declared; local copy fetched with the content pass) | External | yes |

Graph names reserved (`status: planned`, `drydocs_core/ontology/relationship_vocabulary/`):
`CatalogBusinessTerm {term_id}` · `CatalogValidValue {value_id}` · `CatalogElement {element_id}` ·
`CatalogEncodingInstance {encoding_id}` and the edges `IS_REPRESENTED_AS` · `HAS_ALLOWED_VALUES` ·
`DEFINED_FOR`. Map entry: `config/taxonomy-ontology-map/30-mappings-catalog.yaml#catalog-business-term`
(`proposed`).

## Scope rule (SME, 2026-08-21)

The company runs a **dedicated acronym tool**. This glossary does not compete with it. It holds
**only** acronyms and terms that correlate to what DryDocs ingests — a job-name token, a zone, a
launcher flag, a platform, a feed — each sense carrying an **evidence breadcrumb** to where it was
seen. The first producer is `drydocs_deepdoc` (epic MM): the acronym table an investigation builds
(term · meaning · confidence) lands as *candidate* senses in `internal/glossary/`, `:Uncertain` until
the SME confirms; confirmed senses may be relayed to the company tool, never the reverse.

## What the shape must hold (from Idea-35, merged into G34)

- key by **acronym**; carry **many senses per key**;
- each sense tagged with its **scope**: `area | business-domain | technical-domain | industry`
  (what an outsider would assume);
- wherever a misreading has actually happened, an explicit **does-NOT-mean** note — that note, not
  the expansion, is the protective sentence (the worked example: a modelling idiom vs an org
  platform family vs a retired graph label that meant neither);
- SKOS binding: sense = `skos:Concept` in a scoped `skos:ConceptScheme`; `prefLabel` /
  `altLabel` / `definition` / `scopeNote`;
- provenance per sense: `evidence_ref`, `confidence`, `confirmed_by`, `confirmed_on`.

## What does NOT happen here

No loader reads this directory. No HITL gate is run by the scaffold.
`config/taxonomy/software-registry.yaml#acronyms` remains the durable home for the expansions it
holds until the gate-log Q6 acronym ruling decides whether they migrate.
