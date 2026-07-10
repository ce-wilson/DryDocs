// =============================================================================
// registry_ontology_supplement.cypher  —  software-registry domain supplement
//
// Anchor terms for the third-party software registry (plan 07 / ADR 0004,
// gate-confirmed 2026-07-07 — config/gate-log.md). Idempotent; apply after
// the base ontology supplement:  drydocs apply-registry-supplement
//
// Declares:  Vendor (org:Organization), SoftwareProduct (dd:SoftwareProduct),
//            MADE_BY (prov:wasAttributedTo), USES_SOFTWARE (local edge).
// =============================================================================


// ----- Local-namespace anchor terms ------------------------------------------

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Vendor"})
  SET n.label = "Vendor",
      n.notes = "Third-party software company/brand ONLY (ADR 0004). "
              + "org:Organization; prov Agent. Ids shared with the "
              + "drydocs-icons manifest where an icon exists.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#SoftwareProduct"})
  SET n.label = "Software Product",
      n.notes = "What a Vendor ships (Control-M, Neo4j, Oracle Database). "
              + "prov Entity. role attribute (orchestrator|data-platform|"
              + "graph-platform|tool) absorbs the Tier-1/Tier-2 split; "
              + "versions carried as a property until per-version queries "
              + "demand nodes.";


// ----- :SUBCLASS_OF wiring to the W3C anchors ---------------------------------

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Vendor"})
MATCH (oc:OntologyTerm:OrgClass   {iri: "http://www.w3.org/ns/org#Organization"})
MERGE (lc)-[r:SUBCLASS_OF]->(oc)
  ON CREATE SET r.source = "drydocs.registry_ontology_supplement";

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#SoftwareProduct"})
MATCH (pc:OntologyTerm:ProvClass  {iri: "http://www.w3.org/ns/prov#Entity"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.registry_ontology_supplement";


// =============================================================================
// :LocalRelationship declarations
// =============================================================================

// MADE_BY  —  SoftwareProduct → Vendor  (prov:wasAttributedTo)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#madeBy"})
  SET n.label  = "MADE_BY",
      n.domain = "SoftwareProduct",
      n.range  = "Vendor",
      n.notes  = "Product attributed to the brand that ships it. "
               + "Matrix row: Entity → Agent = prov:wasAttributedTo.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#madeBy"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#wasAttributedTo"})
MERGE (local)-[:MAPS_TO]->(prov);

// USES_SOFTWARE  —  Application → SoftwareProduct  (LOCAL — no PROV row)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#usesSoftware"})
  SET n.label  = "USES_SOFTWARE",
      n.domain = "Application",
      n.range  = "SoftwareProduct",
      n.notes  = "Application (Agent) uses a software product (Entity). "
               + "LOCAL domain edge — PROV has no Agent → Entity usage row "
               + "(prov:used is Activity → Entity); precedent arch_contains. "
               + "Edge carries version, source, status. Derived candidates "
               + "come from CMD_LINE invocation patterns (plan-07 Phase 3), "
               + "never base ingest.";
