// =============================================================================
// m3_ontology_supplement.cypher
//
// Anchor terms specific to M3 (Control-M structural lineage). Idempotent.
// Apply once after the M0 bootstrap; no-op on re-run.
//
// All the heavy lifting was already done by M0 ontology.cypher — this file
// only adds the local-namespace concept terms that M3 introduces and wires
// them via :SUBCLASS_OF to the PROV anchors M0 seeded.
// =============================================================================

// ----- Local-namespace anchor terms (concept-level) -------------------------

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMServer"})
  SET n.label = "Control-M Server",
      n.notes = "BMC Control-M scheduler runtime host. Maps loosely to swo:Platform.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#JobFolder"})
  SET n.label = "Control-M Job Folder",
      n.notes = "BMC nomenclature calls these 'tables' (psgmgr.CM_DEF_VTAB; "
              + "wraps dtsremgr.DEF_TAB). A folder is a prov:Collection of "
              + "jobs that run on one server.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMJob"})
  SET n.label = "Control-M Job",
      n.notes = "A scheduled job definition. Composite key (job_id, version_serial). "
              + "Acts as a prov:Activity at runtime; phase-2 attaches per-execution :JobRun history.";


// ----- :SUBCLASS_OF wiring to PROV anchors (seeded by M0) -------------------

// JobFolder is a prov:Collection.
MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#JobFolder"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Collection"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.m3_supplement";

// ControlMJob is a prov:Activity (at runtime; phase-2 makes this concrete).
MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMJob"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Activity"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.m3_supplement";


// ----- :SchedulerKind for ControlM was seeded by M0; double-checked here ----

MERGE (k:SchedulerKind {name: "ControlM"})
  ON CREATE SET k.kind_label      = "BMC Control-M",
                k.phase_supported = 1;


// =============================================================================
// :LocalRelationship declarations  —  M3 relationship → PROV-O mapping
//
// Each block declares one relationship type used by M3 loaders and wires it
// to the PROV-O anchor seeded by ontology.cypher via :MAPS_TO.
// Relationship types without a PROV-O equivalent carry no :MAPS_TO edge.
// =============================================================================

// RUNS_ON  —  JobFolder → ControlMServer
// Infrastructure placement; no PROV-O equivalent.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#runsOn"})
  SET n.label  = "RUNS_ON",
      n.domain = "JobFolder",
      n.range  = "ControlMServer",
      n.notes  = "Folder is scheduled on a Control-M server (DATA_CENTER). "
               + "Edge carries since + last_seen_at for migration audit.";

// CONTAINS_JOB  —  JobFolder → ControlMJob  (prov:hadMember)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#containsJob"})
  SET n.label  = "CONTAINS_JOB",
      n.domain = "JobFolder",
      n.range  = "ControlMJob",
      n.notes  = "JobFolder (prov:Collection) contains ControlMJob (prov:Activity). "
               + "Semantics: prov:hadMember.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#containsJob"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#hadMember"})
MERGE (local)-[:MAPS_TO]->(prov);

// REQUIRES_IN_CONDITION  —  ControlMJob → Condition  (prov:used)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#requiresInCondition"})
  SET n.label  = "REQUIRES_IN_CONDITION",
      n.domain = "ControlMJob",
      n.range  = "Condition",
      n.notes  = "Job requires a named IN condition before execution. "
               + "Semantics: prov:used. Edge carries odate, and_or, parentheses, order_.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#requiresInCondition"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#used"})
MERGE (local)-[:MAPS_TO]->(prov);

// EMITS_OUT_CONDITION  —  ControlMJob → Condition  (prov:generated)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#emitsOutCondition"})
  SET n.label  = "EMITS_OUT_CONDITION",
      n.domain = "ControlMJob",
      n.range  = "Condition",
      n.notes  = "Job emits a named OUT condition on completion. "
               + "SIGN='+' posts; SIGN='-' removes. Semantics: prov:generated.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#emitsOutCondition"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#generated"})
MERGE (local)-[:MAPS_TO]->(prov);

// WAS_INFORMED_BY  —  ControlMJob → ControlMJob  (prov:wasInformedBy)
// Replaces the local DEPENDS_ON label used in earlier drafts.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#wasInformedBy"})
  SET n.label  = "WAS_INFORMED_BY",
      n.domain = "ControlMJob",
      n.range  = "ControlMJob",
      n.notes  = "Derived dependency. Successor job was informed by predecessor via "
               + "shared OUT→IN condition. Direction: (successor)→(predecessor). "
               + "Carries via_condition, recursion_level, dependency_path, derived=true.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#wasInformedBy"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#wasInformedBy"})
MERGE (local)-[:MAPS_TO]->(prov);
