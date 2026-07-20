# ADR 0001 — Ontology base scope: freeze the PROV spine, demote the rest

```yaml
status: PROPOSED        # PROPOSED | ACCEPTED | SUPERSEDED
date: 2026-06-22
deciders: [chad.wilson, ontology-mapper, SME-gate]
layer: 2-ontology
affects:
  - drydocs/schema/ontology.cypher
  - docs/RELATIONSHIP_GUIDE.md
  - reference/standards/README.md
```

## Context

DryDocs stores its knowledge graph in **Neo4j (a Labeled Property Graph), not an
RDF triplestore.** Every W3C/OBO standard we cite is RDF/OWL; in an LPG we get no
OWL reasoning, no URI identity, and no `rdf:type` inference unless we add
neosemantics/n10s — which we do not, and should not, for a pull-based catalog.

Our existing base (`drydocs/schema/ontology.cypher`) already resolves this
correctly: ontology terms are seeded as `:OntologyTerm:<Source>Class/Property`
catalog nodes carrying the IRI as a **property**; the live graph uses
**domain-alias relationship types** (`CONTAINS_JOB`, `USED`, `GENERATED`) with the
formal mapping recorded in `prov_maps_to` (`config/taxonomy-ontology-map.yaml`);
node **identity is always a business key**, never a URL.

A second model reviewed an expanded standards set — adding **CSVW
(tabular-metadata), LDP, LDN** and leaning harder on **OBI/IAO** for provenance and
epistemology. That review reasoned in RDF triples and was unaware of what we had
already built (PROV spine, DataHub `Schema→Field→Element` column model). This ADR
records the decision on what actually enters the graph.

## Decision

**Seed only the spine. Cite everything else; keep it out of the graph.**

| Standard | Disposition | Rule |
|---|---|---|
| PROV-O | **Core — spine, frozen** | Canonical provenance: `Entity` / `Activity` / `Agent` + relations. |
| DCAT v3, DPROD, DQV, W3C ORG | **Core, frozen** | Already seeded and load-bearing. |
| OpenLineage + DataHub URN | **Core (identity + lineage)** | Per `docs/patterns/data-catalog/ontology-standard.md`. |
| SWO (SDLC subset) | **Core but scoped** | Language/script/platform classification only. Agents are `prov:SoftwareAgent`, not SWO. |
| OBI | **Anchor only — do NOT expand** | Keep the single `OBI_0200000` term as cross-reference. `obi:data transformation` = `prov:Activity`. |
| IAO | **Anchor only — do NOT expand** | Keep the single term. `iao:data item` = `prov:Entity` / `dcat:Dataset`. |
| CSVW | **Cite, do not seed** | Column granularity already covered by DataHub `Schema→Field→Element`. Only borrow ≤4 dialect *property names* (`csvw:delimiter`, `csvw:null`, `csvw:quoteChar`, `csvw:header`) on the file/`:Distribution` node **if** raw delimited-file dialect must be captured. No CSVW class hierarchy. |
| LDP / LDN | **Reject** | Active HTTP protocols (`POST`, inbox). Zero queryable value in an API-less, pull/batch system. Documentation footnote only. |

**Governing principle:** *Spine standards are seeded into the graph; everything
else is cited in `reference/standards/` and stays out of it.*

### Two LPG rules this ADR codifies (into `docs/RELATIONSHIP_GUIDE.md`)

1. **One canonical graph type per concept; synonyms are anchors.** A transform is
   `prov:Activity` (aliased to OpenLineage `Job`); OBI/IAO names are cross-reference
   terms, never modeled-with. This is the single namespace-clash risk in the base.
2. **Versioned external objects are distinct nodes keyed by `(object, versionId)`,
   linked `WAS_DERIVED_FROM` to the predecessor** (`prov:specializationOf`). Never
   smuggle a version into a URL string — a string is not queryable.

## Consequences

**Positive**
- Base is finalized mostly by *removing* proposed additions — KISS preserved.
- The PROV spine stays the unambiguous backbone; no OBI/IAO/PROV collision.
- Net new graph content: at most four optional dialect properties.
- Reduced HITL-gate burden — fewer seeded terms to govern.
- Staleness is already handled by DQV `freshness_sla` / `arrival_latency`; make it
  physical by stamping pulled nodes with `sourceSnapshotAt` / `lastObservedAt`.

**Negative / trade-offs**
- We forgo formal OWL/RDF interop. Acceptable: no consumer requires it. If true RDF
  export is ever needed, revisit via neosemantics in a new ADR (this one would be
  SUPERSEDED, not amended).
- Borrowing CSVW property names without the vocabulary means dialect terms are a
  local naming convention, not a validated import. Acceptable at our scale.

## Follow-up (small, bounded)

1. Add a comment block in `ontology.cypher` capping OBI + IAO at their current
   single anchor terms ("cross-reference only — never modeled-with").
2. Resolve the CSVW dialect question: add ≤4 properties to the file node, **or**
   record "not used — superseded by DataHub Schema→Field→Element."
3. Add the LDP/LDN "considered & rejected" paragraph to
   `reference/standards/README.md`.
4. Add the two LPG rules above to `docs/RELATIONSHIP_GUIDE.md`.
5. Route through the SME gate (`docs/restructure/03-hitl-sme-flow.md`) to move this
   ADR `PROPOSED → ACCEPTED`.
