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
