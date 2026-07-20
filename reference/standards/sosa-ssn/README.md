# SOSA / SSN — the observation & temporal standard (context-graph layer)

**Source:** W3C Spatio-Temporal Data on the Web Working Group — *Semantic Sensor Network* /
*Sensor, Observation, Sample, and Actuator* ontologies. Local mirror: `../../../sdw-sosa-ssn`
(the `ssn/` and `ogcapi-sosa/` trees). IRI base: `http://www.w3.org/ns/sosa/`.

## Why DryDocs uses it

DryDocs has a strong **knowledge graph** (what runs, what depends on what, who owns it) but no
**context graph** (what matters *right now*). SOSA/SSN supplies the missing temporal/observation
vocabulary so production-support questions become first-class:

| Support question | SOSA/SSN pattern |
|------------------|------------------|
| "Did this batch run, and when?" | `sosa:Observation` with `sosa:resultTime` / `sosa:phenomenonTime` |
| "What is the current health of folder X?" | latest `sosa:Result` observed by a `sosa:Sensor` (monitor) on a `sosa:FeatureOfInterest` (the job/folder) |
| "Is the data fresh enough to decide?" | `sosa:resultTime` vs SLA window |
| "What is this job a property of?" | `sosa:ObservableProperty` (run-duration, exit-status) of the `ControlMJob` feature |

## Mapping sketch (proposal — goes through the HITL gate before any graph write)

- `ControlMJob` / `ControlMFolder` → can act as `sosa:FeatureOfInterest`.
- A monitoring source (Control-M history API, a health probe) → `sosa:Sensor`.
- One health/run reading → `sosa:Observation` → `sosa:Result` (+ `resultTime`).
- `run-duration`, `exit-status`, `freshness` → `sosa:ObservableProperty`.

These map cleanly onto the *planned* `ControlMJobRun` execution-lineage nodes already in
`relationship_vocabulary.yaml` (the phase-2 / execution stream). SOSA/SSN gives them a
standards-grounded vocabulary instead of ad-hoc properties.

## What NOT to do
- Do not import SOSA/SSN as taxonomy rows. It is an **ontology** reference — it informs the
  meaning layer, it is not data to load.
- Do not add `sosa:*` labels to nodes until the `ontology-mapper` has registered them in the
  vocabulary and the SME has confirmed via `docs/restructure/03-hitl-sme-flow.md`.
