# reference/standards/ — ontology standards

The W3C / community ontologies DryDocs maps to. These give the graph **meaning** (the
ontology layer). The `relationship_vocabulary.yaml` 9-row matrix is grounded in PROV-O;
the other standards cover org structure, data products, observation/time, and catalogs.

| Standard | IRI | Layer it serves | Notes |
|----------|-----|-----------------|-------|
| [PROV-O](prov-o/README.md) | `http://www.w3.org/ns/prov#` | provenance (core) | the decision matrix |
| [W3C ORG](w3c-org/README.md) | `http://www.w3.org/ns/org#` | organization | Membership/Role/OrgUnit; SEAL + PAT |
| [DPROD / EKGF](dprod-ekgf/README.md) | `https://ekgf.github.io/dprod/` | data products | Ports |
| [**SOSA/SSN**](sosa-ssn/README.md) | `http://www.w3.org/ns/sosa/` | **context (temporal/observation)** | feeds layer 4 |
| DCAT | `http://www.w3.org/ns/dcat#` | dataset catalog | DataSource/DataTarget |
| SKOS | `http://www.w3.org/2004/02/skos/core#` | concept reconciliation | closeMatch for taxonomy mapping |

## Why SOSA/SSN is here (it is not optional decoration)

A **context graph** answers "what matters *right now*." That is inherently temporal:
job-run freshness, last-success time, current health, observation windows. SOSA/SSN
(`Observation`, `Sensor`, `Result`, `phenomenonTime`, `resultTime`) is the standard pattern
for that. It is the bridge from the static knowledge graph (layers 1–3) to the context graph
(layer 4). Local mirror: `../../sdw-sosa-ssn`.

## Rule for agents
Map to the **most precise valid term**, and record the mapping in `relationship_vocabulary.yaml`
+ the relevant supplement. Do not invent local terms when a standard term fits — that is how
the taxonomy/ontology drift started. When unsure, route to the HITL gate.
