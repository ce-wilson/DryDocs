# reference/standards/ — ontology standards

The W3C / community ontologies DryDocs maps to. These give the graph **meaning** (the
ontology layer). The `relationship_vocabulary.yaml` 9-row matrix is grounded in PROV-O;
the other standards cover org structure, data products, and catalogs.

Two tiers, by adoption status:

- **Declared / Adopted** — blessed for the production model. Seeded by `drydocs bootstrap`
  (via `ontology.cypher`) and the per-domain supplements; safe to map against directly.
- **Experimental / Early Adoption** — a real W3C standard, but **not yet a declared
  *company* standard**. Registered with IRIs so the ontology-mapper can use it, but fenced
  off from production (opt-in supplement only) and pending the HITL gate.

## Declared / Adopted

| Standard | IRI | Layer it serves | Notes |
|----------|-----|-----------------|-------|
| [PROV-O](prov-o/README.md) | `http://www.w3.org/ns/prov#` | provenance (core) | the decision matrix |
| [W3C ORG](w3c-org/README.md) | `http://www.w3.org/ns/org#` | organization | Membership/Role/OrgUnit; SEAL + PAT |
| [DPROD / EKGF](dprod-ekgf/README.md) | `https://ekgf.github.io/dprod/` | data products | Ports |
| DCAT | `http://www.w3.org/ns/dcat#` | dataset catalog | DataSource/DataTarget |
| SKOS | `http://www.w3.org/2004/02/skos/core#` | concept reconciliation | closeMatch for taxonomy mapping |
| DQV | `http://www.w3.org/ns/dqv#` | data quality | dimensions + metrics (seeded in `ontology.cypher`) |
| [DCMI Terms](dcmi-terms/README.md) | `http://purl.org/dc/terms/` | property-level authorship | the audit-envelope bindings (`property_terms` section; gate `envelope-property-terms`) |

## Experimental / Early Adoption

| Standard | IRI | Layer it serves | Notes |
|----------|-----|-----------------|-------|
| [**SOSA/SSN**](sosa-ssn/README.md) | `http://www.w3.org/ns/sosa/` | **context (temporal/observation)** | feeds layer 4; W3C but **not a declared company standard** |

SOSA/SSN is opt-in only — seeded by `drydocs apply-sosa-supplement`
(`drydocs_core/schema/sosa_experimental_supplement.cypher`), **never** by `drydocs bootstrap`.
Every term carries `adoption:"experimental"` in the graph. Promotion to **Declared /
Adopted** happens only after the SME confirms the `jobrun-observation` mapping through the
HITL gate (`docs/restructure/03-hitl-sme-flow.md`); see backlog Epic E.

### Why SOSA/SSN is here (it is not optional decoration)

A **context graph** answers "what matters *right now*." That is inherently temporal:
job-run freshness, last-success time, current health, observation windows. SOSA/SSN
(`Observation`, `Sensor`, `Result`, `phenomenonTime`, `resultTime`) is the standard pattern
for that. It is the bridge from the static knowledge graph (layers 1–3) to the context graph
(layer 4). It **layers on top of PROV** — `ControlMJob` / `ControlMFolder` keep their PROV types
and *additionally* play `sosa:FeatureOfInterest` — so nothing in the adopted model changes.
Local mirror: `../../sdw-sosa-ssn`.

## Rule for agents
Map to the **most precise valid term**, and record the mapping in `relationship_vocabulary.yaml`
+ the relevant supplement. Do not invent local terms when a standard term fits — that is how
the taxonomy/ontology drift started. When unsure, route to the HITL gate. Do **not** promote
an Experimental standard into the production model without that gate.
