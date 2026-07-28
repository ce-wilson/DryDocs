// =============================================================================
// ontology_supplement.cypher  —  base ontology supplement
//
// Anchor terms for the DryDocs domain that extend the W3C backbone seeded
// by ontology.cypher. Idempotent. Apply once after bootstrap; no-op on re-run.
//
// Covers:
//   Control-M structural lineage (M3):  ControlMServer, ControlMFolder, ControlMJob,
//                                       ControlMApplication (gate controlm-q1q3-phase1)
//   Docs-corpus lexical graph:          Document, Chunk (gate bmc-docs-lexical-load)
//   Doc traceability + review feedback: DesignDoc, DocSection, Requirement, Component,
//                                       TestCase, FeedbackNote (gate doc-traceability-feedback / L7)
//
// Applied by `drydocs apply-supplements` as chain step 1. The chain and its
// order are declared once, in supplements.py beside this file — not here, and
// not in prose. Domain-specific supplements follow (seal before catalog —
// catalog reuses seal's Attribution class + #hasAgent term):
//   seal_ontology_supplement.cypher     — BusinessApplication, Port, Employee,
//                                         TOM qualified attribution + tom_roles seeds
//   catalog_ontology_supplement.cypher  — CatalogLOB, Product, AreaProduct, DevTeam,
//                                         all Role seeds (SEAL + PAT + D&A + CCB Ops),
//                                         K6 Product Cabinet + product_roles seeds
//   registry_ontology_supplement.cypher — Vendor, SoftwareProduct (ADR 0004)
//   sosa_experimental_supplement.cypher — SOSA/SSN observation terms (opt-in via
//                                         apply-sosa-supplement; NOT in the standard chain)
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

// --- Host topology (P3; gate controlm-hosts-topology 2026-07-09) ------------

// Class anchors: the host-group Collection and the reused ExecutionHost agent.
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMHostGroup"})
  SET n.label = "Control-M Host Group",
      n.notes = "CM_HOSTS.GRPNAME per data center (vendor 6.4.01 poster: CMS_NODGRP; "
              + "9.0.x term 'host group'). A prov:Collection of member ExecutionHosts; "
              + "may itself front a load-balancer DNS alias. NOT the CM_DEF_VJOB.GROUP_NAME "
              + "application-group concept.";
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ExecutionHost"})
  SET n.label = "Execution Host",
      n.notes = "Agent host a job/ETL workload executes on (prov:SoftwareAgent), keyed on "
              + "nodeid alone — one node per distinct CM_HOSTS.NODEID; multi-group membership expected.";

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ControlMHostGroup"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Collection"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.ontology_supplement";

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ExecutionHost"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#SoftwareAgent"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.ontology_supplement";

// RUNS_ON  —  ControlMJob | ETLProcess → ControlMHostGroup | ExecutionHost
// Infrastructure placement; no PROV-O equivalent (SCHEDULED_ON precedent).
// One label, role-disambiguated: host_group (2-hop, NODE_ID names a group —
// group match WINS, mirroring Control-M's own resolution), agent_host (1-hop
// hard-coded member host), etl_host (planned). Written by the derived
// resolution pass (runs_on_resolution.cypher) — UNMATCHED reported as
// coverage, never guessed.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#runsOn"})
  SET n.label  = "RUNS_ON",
      n.domain = "ControlMJob | ETLProcess",
      n.range  = "ControlMHostGroup | ExecutionHost",
      n.notes  = "Definition-time execution placement, role-disambiguated "
               + "(host_group | agent_host | etl_host). Derived from CM_DEF_VJOB.NODE_ID "
               + "x CM_HOSTS; group match wins (gate controlm-hosts-topology §B). "
               + "Rerun host affinity is runtime state — phase-2, never this edge.";

// CONTAINS_HOST  —  ControlMHostGroup → ExecutionHost  (prov:hadMember)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#containsHost"})
  SET n.label  = "CONTAINS_HOST",
      n.domain = "ControlMHostGroup",
      n.range  = "ExecutionHost",
      n.notes  = "Host-group membership from psgmgr.CM_HOSTS (one edge per DATA_CENTER/"
               + "GRPNAME/NODEID row); carries participation_type + last_capture_date. "
               + "Semantics: prov:hadMember (CONTAINS_JOB / CONTAINS_FOLDER family).";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#containsHost"})
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
               + "Carries via_condition, derived=true. DIRECT pairs only since the "
               + "phased-loader port (2026-07-23): transitive reach is a graph "
               + "traversal, not a stored closure.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#wasInformedBy"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#wasInformedBy"})
MERGE (local)-[:MAPS_TO]->(prov);

// WAS_ASSOCIATED_WITH {role: seal_app_ref}  —  ControlMJob → Application  (prov:wasAssociatedWith)
// K2 activation (gate seal-attribution-match-policy, 2026-07-14). IRI is
// role-discriminated: the label hosts future roles (owner/author) with their
// own declarations. K3 rider: type-checks while :BusinessApplication is prov:SoftwareAgent —
// the K4 reclass re-opens the edge shape at its own gate. (Comment ';' is
// harmless since D5: run_script splits client-side, comment-aware.)
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


// =============================================================================
// Documentation traceability + review feedback (backlog L7; gate
// doc-traceability-feedback SIGNED OFF 2026-07-20 — config/gate-log.md).
// PRODUCT-PLANE family: source-agnostic classes with an `origin` discriminator;
// DryDocs' own outline system is source connector #1 ("tenant 0"). Managed
// (authored/rev-tracked/annotatable) vs ingested (Document/Chunk above) is a
// product boundary — gate A6. Keys are source-namespaced — gate A2.
// =============================================================================

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#DesignDoc"})
  SET n.label = "DesignDoc",
      n.notes = "MANAGED authored document (rev-tracked, outline-validated). prov:Entity. "
              + "Key (origin, doc_id). Connector #1: docs/design/*.md (drydocs.doc-outline.v1).";
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#DocSection"})
  SET n.label = "DocSection",
      n.notes = "Authored section of a DesignDoc, key (origin, doc_id, anchor). prov:Entity. "
              + "Shared target of traceability (SPECIFIED_IN) and review feedback (ANNOTATES).";
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Requirement"})
  SET n.label = "Requirement",
      n.notes = "Requirement/capability proposition from any registered source. prov:Entity. "
              + "Key (origin, requirement_id); kind FR|UC|NFR (gate A3 — Scenario deferred "
              + "to a future BDD-connector gate); id format is per-source config (gate D5).";
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Component"})
  SET n.label = "Component",
      n.notes = "Implementation artifact cited as a Requirement's realization. prov:Entity. "
              + "Key (origin, ref); same-basename within one origin = SME-merge case (gate D1).";
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#TestCase"})
  SET n.label = "TestCase",
      n.notes = "Test/verification citation proving a Requirement. prov:Entity. Key (origin, ref); "
              + "kind is an OPEN enum: unit|verify|gate|graph-test today (gate A7/D2).";
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#FeedbackNote"})
  SET n.label = "FeedbackNote",
      n.notes = "Anchor-keyed review annotation. prov:Entity (aboutness, not derivation). "
              + "Carries doc_rev + lifecycle status open|applied|rejected|superseded (gate C2/C3).";

// PART_OF  —  DocSection → DesignDoc  (structural containment; Document/Chunk precedent — gate B1)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#docSectionPartOf"})
  SET n.label  = "PART_OF",
      n.domain = "DocSection",
      n.range  = "DesignDoc",
      n.notes  = "DocSection belongs to its DesignDoc — authored/ordered outline containment; "
               + "C8-clean twin of the Chunk→Document PART_OF (from/to differ). Gate B1.";

// SPECIFIED_IN  —  Requirement → DocSection  (prov:hadPrimarySource — gate B2)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#specifiedIn"})
  SET n.label  = "SPECIFIED_IN",
      n.domain = "Requirement",
      n.range  = "DocSection",
      n.notes  = "Requirement's specification is primary-sourced from this section's text "
               + "(seal_had_primary_source reuse pattern). Gate B2.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#specifiedIn"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#hadPrimarySource"})
MERGE (local)-[:MAPS_TO]->(prov);

// IMPLEMENTED_BY  —  Requirement → Component  (research-grounded local — gate B3)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#implementedBy"})
  SET n.label  = "IMPLEMENTED_BY",
      n.domain = "Requirement",
      n.range  = "Component",
      n.notes  = "Requirement realized by an implementation artifact. No declared-standard term; "
               + "research-grounded local (Ramesh & Jarke Satisfies/Allocated-to). Gate B3.";

// VERIFIED_BY  —  Requirement → TestCase  (research-grounded local — gate B3)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#verifiedBy"})
  SET n.label  = "VERIFIED_BY",
      n.domain = "Requirement",
      n.range  = "TestCase",
      n.notes  = "Requirement proven by a test/verification citation. No declared-standard term; "
               + "research-grounded local (Ramesh & Jarke Verifies). Gate B3.";

// ANNOTATES  —  FeedbackNote → DocSection  (local aboutness; oa:hasTarget analog deferred — gate D4)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#annotates"})
  SET n.label  = "ANNOTATES",
      n.domain = "FeedbackNote",
      n.range  = "DocSection",
      n.notes  = "Review note targets a section — aboutness, not derivation (docs_describes "
               + "reasoning). W3C oa:hasTarget is the undeclared-standard analog (gate D4). "
               + "Correlation to Requirement rides ANNOTATES + reverse SPECIFIED_IN (gate C4).";

// WAS_ATTRIBUTED_TO {role: feedback_author}  —  FeedbackNote → Employee  (prov:wasAttributedTo — gate C1)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#feedbackAuthoredBy"})
  SET n.label  = "WAS_ATTRIBUTED_TO",
      n.role   = "feedback_author",
      n.domain = "FeedbackNote",
      n.range  = "Employee",
      n.notes  = "Note authored by the reviewing Employee — collapsed form (one author, no role "
               + "scheme; p2_authored_by precedent). role=feedback_author discriminates on the "
               + "shared label. Gate C1.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#feedbackAuthoredBy"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#wasAttributedTo"})
MERGE (local)-[:MAPS_TO]->(prov);

// --- Self-documentation code graph (G33 / Epic U; gate ---------------------
// self-documentation-code-graph SIGNED OFF 2026-07-27). DryDocs' own source
// tree as a queryable subgraph — the depgraph ritual's output entering Neo4j.

// Project + CodeModule local class anchors.
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Project"})
  SET n.label = "Project",
      n.notes = "The single software-repository root (prov:Collection) — ONE node per repo "
              + "(gate B1(a)); the snapshot's six scan roots are the CodeModule.project "
              + "property, never sibling roots. The 'is this our own code?' one-hop anchor; "
              + "nothing else hangs off it (F2). Reads against the PAT :Product family as "
              + "SOFTWARE repo vs BUSINESS product (F3).";
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#CodeModule"})
  SET n.label = "Code Module",
      n.notes = "One source FILE (prov:Entity), keyed on file_id = repo-relative path — the "
              + "only non-colliding key (C2/C4). One file = one module (C1(a); the label says "
              + "'module', the thing is a file — accepted cost, recorded at the gate). MUST "
              + "NEVER also carry :SoftwareProduct (F1 — graph-test in m1-verify).";

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Project"})
MATCH (pc:OntologyTerm:ProvClass  {iri: "http://www.w3.org/ns/prov#Collection"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.ontology_supplement";

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#CodeModule"})
MATCH (pc:OntologyTerm:ProvClass  {iri: "http://www.w3.org/ns/prov#Entity"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.ontology_supplement";

// HAS_MODULE  —  Project → CodeModule  (prov:hadMember; u1_has_module)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasModule"})
  SET n.label  = "HAS_MODULE",
      n.domain = "Project",
      n.range  = "CodeModule",
      n.notes  = "Repository contains this source file — from the SINGLE root to ALL modules; "
               + "'which of the six scan roots' is the CodeModule.project property, never this "
               + "edge (gate B1(a)). prov:hadMember, Collection -> any matrix row.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasModule"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#hadMember"})
MERGE (local)-[:MAPS_TO]->(prov);

// IMPORTS  —  CodeModule → CodeModule  (prov:wasDerivedFrom; u1_imports)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#imports"})
  SET n.label  = "IMPORTS",
      n.domain = "CodeModule",
      n.range  = "CodeModule",
      n.notes  = "Source-level import, importer -> imported. ACCEPTED LIMIT (gate D2): bare "
               + "pairs — cannot distinguish `import x` / `from x import y` / TYPE_CHECKING-"
               + "only. Never read as 'breaks if removed'.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#imports"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#wasDerivedFrom"})
MERGE (local)-[:MAPS_TO]->(prov);

// IS_ENCODED_IN  —  CodeModule → SwoClass  (SWO_0000741; u1_is_encoded_in)
// FIRST USE of the SWO layer (seeded in ontology.cypher with zero consumers
// until this gate). Precedent set at E1(b): bind to a seeded term that already
// means the thing, derive the value from data the artifact carries, invent
// nothing. MAPS_TO the seeded SwoProperty rather than a PROV property.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#isEncodedIn"})
  SET n.label  = "IS_ENCODED_IN",
      n.domain = "CodeModule",
      n.range  = "SwoClass",
      n.notes  = "Module -> programming language, value derived from node.extension "
               + "(.py -> the seeded SWO Python term). Realises SWO_0000741 'is encoded in'; "
               + "function-level binding ('implements', 'uses platform') REJECTED at E1 — a "
               + "dependency snapshot does not know software function.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#isEncodedIn"})
MATCH (swo:OntologyTerm:SwoProperty         {iri: "http://www.ebi.ac.uk/swo/SWO_0000741"})
MERGE (local)-[:MAPS_TO]->(swo);
