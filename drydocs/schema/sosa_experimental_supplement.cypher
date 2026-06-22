// =============================================================================
// sosa_experimental_supplement.cypher  —  SOSA/SSN observation & temporal terms
//
// STATUS: EXPERIMENTAL / EARLY ADOPTION.
//   SOSA/SSN is a W3C standard but NOT a declared *company* standard, so it is
//   fenced off from the confirmed production model:
//     * NOT applied by `drydocs bootstrap`. Opt-in only:
//         drydocs apply-sosa-supplement
//     * Every term carries  adoption:"experimental"  so it is queryable but
//       visibly distinct from the declared/adopted backbone (PROV/ORG/DPROD/
//       DCAT/SKOS/DQV) seeded by ontology.cypher.
//     * No instance data (Observations/Sensors/Results) is loaded here — that
//       is the layer-4 context-graph pilot (backlog E2), gated by the SME via
//       docs/restructure/03-hitl-sme-flow.md.
//
// PURPOSE: register sosa:* terms with real IRIs so the ontology-mapper can bind
//   taxonomy → SOSA rules in config/taxonomy-ontology-map.yaml (entry
//   `jobrun-observation`) and carry them through the HITL gate. This is the
//   "terms present with IRIs" half of backlog item E1.
//
// HOW IT INTEGRATES (does not conflict with the existing ontologies):
//   * SOSA *layers on top of* PROV — it does not replace it. PROV/ORG/DPROD
//     answer layers 1-3 ("what runs, depends, who owns"); SOSA answers layer 4
//     ("what matters right now").
//   * Multi-classification: ControlMJob / JobFolder keep their PROV behavioural
//     types (Activity / Collection) AND additionally play sosa:FeatureOfInterest
//     (orthogonal axes — see :CAN_ACT_AS below). No existing label changes.
//   * SOSA relationships sit OUTSIDE the PROV 9-row matrix (same as how DPROD
//     hasPort does): they are LocalRelationships that MAPS_TO a sosa:* property.
//   * A sosa:Result can later carry a dqv:QualityMeasurement (freshness_sla is
//     already seeded in ontology.cypher) — SOSA is the observation envelope,
//     DQV the metric. Complementary, not duplicative.
//
// Namespaces (kept in sync with drydocs/ontology/namespaces.py):
//   sosa  http://www.w3.org/ns/sosa/      (trailing slash, not '#')
//   ssn   http://www.w3.org/ns/ssn/
//
// Idempotent. Safe to re-run.
// =============================================================================


// ----- SOSA core classes (experimental) -------------------------------------
MERGE (n:OntologyTerm:SosaClass {iri:"http://www.w3.org/ns/sosa/Observation"})
  SET n.label = "Observation", n.adoption = "experimental",
      n.notes = "An act that produced a Result about an ObservableProperty of a FeatureOfInterest.";
MERGE (n:OntologyTerm:SosaClass {iri:"http://www.w3.org/ns/sosa/Sensor"})
  SET n.label = "Sensor", n.adoption = "experimental",
      n.notes = "The monitoring source making the observation (e.g. Control-M history API, a health probe).";
MERGE (n:OntologyTerm:SosaClass {iri:"http://www.w3.org/ns/sosa/FeatureOfInterest"})
  SET n.label = "Feature of Interest", n.adoption = "experimental",
      n.notes = "The thing observed. ControlMJob / JobFolder can act as this (see :CAN_ACT_AS).";
MERGE (n:OntologyTerm:SosaClass {iri:"http://www.w3.org/ns/sosa/ObservableProperty"})
  SET n.label = "Observable Property", n.adoption = "experimental",
      n.notes = "What is observed: run-status, run-duration, exit-status, freshness.";
MERGE (n:OntologyTerm:SosaClass {iri:"http://www.w3.org/ns/sosa/Result"})
  SET n.label = "Result", n.adoption = "experimental",
      n.notes = "The value an observation produced; may carry a dqv:QualityMeasurement.";
MERGE (n:OntologyTerm:SosaClass {iri:"http://www.w3.org/ns/sosa/Procedure"})
  SET n.label = "Procedure", n.adoption = "experimental",
      n.notes = "The method/workflow a sensor used to produce the result.";


// ----- SOSA properties (experimental) ----------------------------------------
MERGE (n:OntologyTerm:SosaProperty {iri:"http://www.w3.org/ns/sosa/hasFeatureOfInterest"})
  SET n.label = "has feature of interest", n.adoption = "experimental";
MERGE (n:OntologyTerm:SosaProperty {iri:"http://www.w3.org/ns/sosa/observedProperty"})
  SET n.label = "observed property", n.adoption = "experimental";
MERGE (n:OntologyTerm:SosaProperty {iri:"http://www.w3.org/ns/sosa/madeBySensor"})
  SET n.label = "made by sensor", n.adoption = "experimental";
MERGE (n:OntologyTerm:SosaProperty {iri:"http://www.w3.org/ns/sosa/hasResult"})
  SET n.label = "has result", n.adoption = "experimental";
MERGE (n:OntologyTerm:SosaProperty {iri:"http://www.w3.org/ns/sosa/resultTime"})
  SET n.label = "result time", n.adoption = "experimental",
      n.notes = "When the result became available. Range xsd:dateTime (OWL-Time optional, deferred).";
MERGE (n:OntologyTerm:SosaProperty {iri:"http://www.w3.org/ns/sosa/phenomenonTime"})
  SET n.label = "phenomenon time", n.adoption = "experimental",
      n.notes = "When the observed phenomenon happened. Range xsd:dateTime / time:TemporalEntity.";


// ----- Multi-classification: existing PROV nodes can ALSO play sosa roles ----
// :CAN_ACT_AS is orthogonal to :SUBCLASS_OF — it records a role a class may
// take in the context graph WITHOUT changing its primary PROV classification.
MATCH (lc:OntologyTerm:LocalClass {iri:"https://drydocs.local/ontology#ControlMJob"})
MATCH (foi:OntologyTerm:SosaClass {iri:"http://www.w3.org/ns/sosa/FeatureOfInterest"})
MERGE (lc)-[r:CAN_ACT_AS]->(foi)
  ON CREATE SET r.source = "drydocs.sosa_experimental_supplement", r.adoption = "experimental";

MATCH (lc:OntologyTerm:LocalClass {iri:"https://drydocs.local/ontology#JobFolder"})
MATCH (foi:OntologyTerm:SosaClass {iri:"http://www.w3.org/ns/sosa/FeatureOfInterest"})
MERGE (lc)-[r:CAN_ACT_AS]->(foi)
  ON CREATE SET r.source = "drydocs.sosa_experimental_supplement", r.adoption = "experimental";


// ----- Candidate LocalRelationships (experimental) ---------------------------
// These mirror the PROV-mapped LocalRelationship pattern, but MAPS_TO a sosa:*
// property (SOSA edges are not in the PROV matrix). The exact wiring of an
// Observation to a job run (is ControlMJobRun itself the Observation, or a
// separate Observation node?) is the OPEN GATE DECISION — see the
// `jobrun-observation` entry in config/taxonomy-ontology-map.yaml. These terms
// are declared so the gate has something concrete to confirm.

// OBSERVES  —  Observation → FeatureOfInterest  (sosa:hasFeatureOfInterest)
MERGE (n:OntologyTerm:LocalRelationship {iri:"https://drydocs.local/ontology#observes"})
  SET n.label = "OBSERVES", n.domain = "Observation", n.range = "FeatureOfInterest",
      n.adoption = "experimental",
      n.notes = "Observation is about a feature of interest (the job/folder). Semantics: sosa:hasFeatureOfInterest.";
MATCH (local:OntologyTerm:LocalRelationship {iri:"https://drydocs.local/ontology#observes"})
MATCH (sosa:OntologyTerm:SosaProperty       {iri:"http://www.w3.org/ns/sosa/hasFeatureOfInterest"})
MERGE (local)-[:MAPS_TO]->(sosa);

// HAS_RESULT  —  Observation → Result  (sosa:hasResult)
MERGE (n:OntologyTerm:LocalRelationship {iri:"https://drydocs.local/ontology#hasResult"})
  SET n.label = "HAS_RESULT", n.domain = "Observation", n.range = "Result",
      n.adoption = "experimental",
      n.notes = "Observation produced a result (carries resultTime). Semantics: sosa:hasResult.";
MATCH (local:OntologyTerm:LocalRelationship {iri:"https://drydocs.local/ontology#hasResult"})
MATCH (sosa:OntologyTerm:SosaProperty       {iri:"http://www.w3.org/ns/sosa/hasResult"})
MERGE (local)-[:MAPS_TO]->(sosa);

// MADE_BY_SENSOR  —  Observation → Sensor  (sosa:madeBySensor)
MERGE (n:OntologyTerm:LocalRelationship {iri:"https://drydocs.local/ontology#madeBySensor"})
  SET n.label = "MADE_BY_SENSOR", n.domain = "Observation", n.range = "Sensor",
      n.adoption = "experimental",
      n.notes = "Observation was made by a monitoring source. Semantics: sosa:madeBySensor.";
MATCH (local:OntologyTerm:LocalRelationship {iri:"https://drydocs.local/ontology#madeBySensor"})
MATCH (sosa:OntologyTerm:SosaProperty       {iri:"http://www.w3.org/ns/sosa/madeBySensor"})
MERGE (local)-[:MAPS_TO]->(sosa);

// OF_OBSERVABLE_PROPERTY  —  Observation → ObservableProperty  (sosa:observedProperty)
MERGE (n:OntologyTerm:LocalRelationship {iri:"https://drydocs.local/ontology#observedProperty"})
  SET n.label = "OF_OBSERVABLE_PROPERTY", n.domain = "Observation", n.range = "ObservableProperty",
      n.adoption = "experimental",
      n.notes = "Observation targets an observable property (run-status, freshness). Semantics: sosa:observedProperty.";
MATCH (local:OntologyTerm:LocalRelationship {iri:"https://drydocs.local/ontology#observedProperty"})
MATCH (sosa:OntologyTerm:SosaProperty       {iri:"http://www.w3.org/ns/sosa/observedProperty"})
MERGE (local)-[:MAPS_TO]->(sosa);
