# PROV-O — the provenance ontology (core)

**IRI:** `http://www.w3.org/ns/prov#`. The backbone of the DryDocs ontology. Every node carries
provenance and the **9-row decision matrix** in
[`../../../drydocs_core/ontology/relationship_vocabulary.yaml`](../../../drydocs_core/ontology/relationship_vocabulary.yaml)
is PROV-O.

## The matrix (memorize this)

| Source | Target | PROV term | Neo4j label |
|--------|--------|-----------|-------------|
| Activity | Activity | `prov:wasInformedBy` | `WAS_INFORMED_BY` |
| Activity | Entity | `prov:used` | `USED` |
| Activity | Entity (produces) | `prov:generated` | `GENERATED` |
| Activity | Agent | `prov:wasAssociatedWith` | `WAS_ASSOCIATED_WITH` |
| Entity | Activity | `prov:wasGeneratedBy` | `WAS_GENERATED_BY` |
| Entity | Entity | `prov:wasDerivedFrom` | `WAS_DERIVED_FROM` |
| Entity | Agent | `prov:wasAttributedTo` | `WAS_ATTRIBUTED_TO` |
| Agent | Agent | `prov:actedOnBehalfOf` | `ACTED_ON_BEHALF_OF` |
| Collection | any | `prov:hadMember` | `HAD_MEMBER` |

## The three core types
- **Activity** — something that happens over time (`ControlMJob`, `JobRun`, `ETLProcess`).
- **Entity** — a thing (`Condition`, `Script`, `DataSource`, `File`).
- **Agent** — bears responsibility (`Application`, `Employee`, `AppUser`).
- **Collection** (⊑ Entity) — groups members (`ControlMFolder`, `Code`, `Batch`).

## Discipline (this is where past drift happened)
1. Classify both nodes by PROV type **before** picking a label.
2. Use the matrix label, or a domain alias that **maps to** the matrix term (e.g.
   `CONTAINS_JOB` → `prov:hadMember`). Record the mapping; never a freestanding label.
3. A target that is "local infrastructure" (e.g. `ControlMServer`) is **not** an Agent —
   it cannot take `wasAssociatedWith`. Map to null and note why.
