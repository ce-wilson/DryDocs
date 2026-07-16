// =============================================================================
// ontology_supplement.cypher  —  base ontology supplement
//
// Anchor terms for the DryDocs domain that extend the W3C backbone seeded
// by ontology.cypher. Idempotent. Apply once after bootstrap; no-op on re-run.
//
// Covers:
//   Control-M structural lineage (M3): ControlMServer, ControlMFolder, ControlMJob,
//                                      ControlMApplication (gate controlm-q1q3-phase1)
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

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMApplication"})
  SET n.label = "Control-M Application",
      n.notes = "Control-M APPLICATION grouping from the folder header row "
              + "(CM_DEF_VJOB JOB_ID=1) — NOT the business :BusinessApplication / SEAL "
              + "concept. A prov:Collection of folders. "
              + "Gate controlm-q1q3-phase1 (2026-07-07).";


// ----- :SUBCLASS_OF wiring to PROV anchors -----------------------------------

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMFolder"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Collection"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.ontology_supplement";

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMJob"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Activity"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.ontology_supplement";

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMApplication"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Collection"})
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

// --- Docs corpus lexical graph (gate bmc-docs-lexical-load, 2026-07-08) -----

// Document + Chunk local class anchors (both prov:Entity).
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Document"})
  SET n.label = "Document",
      n.notes = "Converted external/internal document (first corpus: bmc-docs). "
              + "prov:Entity; NOT a source-of-record — SOURCE-MANIFEST provenance model governs.";
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Chunk"})
  SET n.label = "Chunk",
      n.notes = "H2-section slice of a Document (deterministic chunking, no LLM). prov:Entity; "
              + "carries provenance tier VERBATIM|GROUNDED|SYNTHESIZED — SYNTHESIZED is never vendor ground truth.";

// DESCRIBES  —  Document → SoftwareProduct  (dcterms:subject / foaf:primaryTopic pattern)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#describes"})
  SET n.label  = "DESCRIBES",
      n.domain = "Document",
      n.range  = "SoftwareProduct",
      n.notes  = "Document is ABOUT a SoftwareProduct — dcterms:subject / foaf:primaryTopic "
               + "pattern; no PROV row (aboutness, deliberately NOT wasDerivedFrom). "
               + "Edge carries target_version. Gate bmc-docs-lexical-load (2026-07-08).";

// PART_OF  —  Chunk → Document  (dcterms:isPartOf pattern; lexical containment)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#partOf"})
  SET n.label  = "PART_OF",
      n.domain = "Chunk",
      n.range  = "Document",
      n.notes  = "Lexical-graph containment (llm-graph-builder pattern) — dcterms:isPartOf "
               + "pattern; kept off prov:hadMember to stay distinct from domain Collections.";

// FIRST_CHUNK / NEXT_CHUNK  —  sequence edges (no standard term; SCHEDULED_ON precedent)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#firstChunk"})
  SET n.label  = "FIRST_CHUNK",
      n.domain = "Document",
      n.range  = "Chunk",
      n.notes  = "Chunk-chain entry point. Local structural sequence edge; no standard term.";
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#nextChunk"})
  SET n.label  = "NEXT_CHUNK",
      n.domain = "Chunk",
      n.range  = "Chunk",
      n.notes  = "Reading order within one Document; singly-linked (out-degree <= 1). "
               + "Local structural sequence edge; no standard term.";

// CONTAINS_FOLDER  —  ControlMApplication → ControlMFolder  (prov:hadMember)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#containsFolder"})
  SET n.label  = "CONTAINS_FOLDER",
      n.domain = "ControlMApplication",
      n.range  = "ControlMFolder",
      n.notes  = "ControlMApplication (prov:Collection; Control-M APPLICATION grouping "
               + "from the folder header row — NOT the SEAL business Application) "
               + "contains ControlMFolder (prov:Collection). Semantics: prov:hadMember. "
               + "Gate controlm-q1q3-phase1 (2026-07-07).";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#containsFolder"})
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

// WAS_ASSOCIATED_WITH {role: seal_app_ref}  —  ControlMJob → Application  (prov:wasAssociatedWith)
// K2 activation (gate seal-attribution-match-policy, 2026-07-14). IRI is
// role-discriminated: the label hosts future roles (owner/author) with their
// own declarations. K3 rider: type-checks while :BusinessApplication is prov:SoftwareAgent —
// the K4 reclass re-opens the edge shape at its own gate. (No line may end
// with ';' inside a comment: apoc.cypher.runMany splits there and Cypher 25
// rejects the empty fragment — see base.py::_code_semicolons.)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#wasAssociatedWithSealAppRef"})
  SET n.label  = "WAS_ASSOCIATED_WITH",
      n.role   = "seal_app_ref",
      n.domain = "ControlMJob",
      n.range  = "BusinessApplication",
      n.notes  = "Job attributed to its SEAL-registered application via STG_APP_FACT "
               + "semantic facts (precedence SEAL > FID > APP_NAME > ALIAS; never raw "
               + "job.APPLICATION). Matrix row: Activity → Agent = prov:wasAssociatedWith. "
               + "role=seal_app_ref discriminates from future owner/author roles. "
               + "Loader: seal_attribution.cypher; manual tier-5 pins via manual_seal_attribution.cypher.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#wasAssociatedWithSealAppRef"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#wasAssociatedWith"})
MERGE (local)-[:MAPS_TO]->(prov);
