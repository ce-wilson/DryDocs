// =============================================================================
// ontology_supplement.cypher  —  base ontology supplement
//
// Anchor terms for the DryDocs domain that extend the W3C backbone seeded
// by ontology.cypher. Idempotent. Apply once after bootstrap; no-op on re-run.
//
// Covers:
//   Control-M structural lineage (M3): ControlMServer, ControlMFolder, ControlMJob
//
// Domain-specific supplements (apply separately after this file):
//   seal_ontology_supplement.cypher    — Application, Port, Membership, Role, Employee
//   catalog_ontology_supplement.cypher — CatalogLOB, Product, AreaProduct, DevTeam,
//                                        all Role seeds (SEAL + PAT + D&A + CCB Ops)
// =============================================================================


// ----- Control-M local-namespace anchor terms --------------------------------

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMServer"})
  SET n.label = "Control-M Server",
      n.notes = "BMC Control-M scheduler runtime host. Maps loosely to swo:Platform.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMFolder"})
  SET n.label = "Control-M Job Folder",
      n.notes = "BMC nomenclature calls these 'tables' (psgmgr.CM_DEF_VTAB; "
              + "wraps dtsremgr.DEF_TAB). A folder is a prov:Collection of "
              + "jobs that run on one server.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMJob"})
  SET n.label = "Control-M Job",
      n.notes = "A scheduled job definition. Composite key (folder_id, job_id). "
              + "Acts as a prov:Activity at runtime; phase-2 attaches per-execution :JobRun history.";


// ----- :SUBCLASS_OF wiring to PROV anchors -----------------------------------

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMFolder"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Collection"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.ontology_supplement";

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMJob"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Activity"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.ontology_supplement";


// ----- SchedulerKind: ControlM (double-check; seeded by ontology.cypher) ----

MERGE (k:SchedulerKind {name: "ControlM"})
  ON CREATE SET k.kind_label      = "BMC Control-M",
                k.phase_supported = 1;


// =============================================================================
// :LocalRelationship declarations — Control-M relationship → PROV-O mapping
// =============================================================================

// SCHEDULED_ON  —  ControlMFolder → ControlMServer
// Infrastructure placement; no PROV-O equivalent. (Renamed from RUNS_ON.)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#scheduledOn"})
  SET n.label  = "SCHEDULED_ON",
      n.domain = "ControlMFolder",
      n.range  = "ControlMServer",
      n.notes  = "Folder is scheduled on a Control-M server (DATA_CENTER). "
               + "Edge carries since + last_seen_at for migration audit. "
               + "Renamed from RUNS_ON; RUNS_ON reassigned to job/ETL → ExecutionHost.";

// CONTAINS_JOB  —  ControlMFolder → ControlMJob  (prov:hadMember)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#containsJob"})
  SET n.label  = "CONTAINS_JOB",
      n.domain = "ControlMFolder",
      n.range  = "ControlMJob",
      n.notes  = "ControlMFolder (prov:Collection) contains ControlMJob (prov:Activity). "
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
