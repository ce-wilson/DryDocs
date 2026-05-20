// =============================================================================
// catalog_ontology_supplement.cypher
//
// Anchor terms specific to the internal product catalog domain. Idempotent.
// Apply once after the M0 bootstrap; no-op on re-run.
//
// Node classifications:
//   CatalogLOB      → org:OrganizationalUnit  (a line of business)
//   BusinessSegment → org:Organization        (corporate segment)
//   ProductLine     → local (catalog hierarchy; no direct W3C equivalent)
//   Product         → local (catalog hierarchy)
//   DevTeam         → org:OrganizationalUnit  (a development team)
//   JiraBoard       → local (planning tool artifact)
// =============================================================================


// ----- Local-namespace anchor terms (node types) ----------------------------

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#CatalogLOB"})
  SET n.label = "Catalog Line of Business",
      n.notes = "An internal product-catalog Line of Business. Subclass of "
              + "org:OrganizationalUnit. May reconcile (approx.) to a corporate "
              + "BusinessSegment via RECONCILES_TO.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#BusinessSegment"})
  SET n.label = "Business Segment",
      n.notes = "A canonical corporate business segment (e.g., CCB, AWM). "
              + "Subclass of org:Organization. Seeded by bootstrap from the "
              + "effective-dated segment list.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ProductLine"})
  SET n.label = "Product Line",
      n.notes = "A grouping of products within a CatalogLOB. Local catalog hierarchy; "
              + "no direct W3C ontology equivalent.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Product"})
  SET n.label = "Product",
      n.notes = "A product within a ProductLine. Local catalog hierarchy.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#DevTeam"})
  SET n.label = "Dev Team",
      n.notes = "A development team that owns a Product. Subclass of "
              + "org:OrganizationalUnit.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#JiraBoard"})
  SET n.label = "Jira Board",
      n.notes = "A Jira planning board associated with a DevTeam. Local tooling artifact.";


// ----- :SUBCLASS_OF wiring to W3C ORG anchors --------------------------------

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#CatalogLOB"})
MATCH (oc:OntologyTerm:OrgClass    {iri: "http://www.w3.org/ns/org#OrganizationalUnit"})
MERGE (lc)-[r:SUBCLASS_OF]->(oc)
  ON CREATE SET r.source = "drydocs.catalog_supplement";

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#BusinessSegment"})
MATCH (oc:OntologyTerm:OrgClass    {iri: "http://www.w3.org/ns/org#FormalOrganization"})
MERGE (lc)-[r:SUBCLASS_OF]->(oc)
  ON CREATE SET r.source = "drydocs.catalog_supplement";

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#DevTeam"})
MATCH (oc:OntologyTerm:OrgClass    {iri: "http://www.w3.org/ns/org#OrganizationalUnit"})
MERGE (lc)-[r:SUBCLASS_OF]->(oc)
  ON CREATE SET r.source = "drydocs.catalog_supplement";


// ----- :LocalRelationship declarations  —  Catalog relationship mapping -----

// RECONCILES_TO  —  CatalogLOB → BusinessSegment
// Approximate match (skos:closeMatch semantics); no strict PROV-O equivalent.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#reconcilesTo"})
  SET n.label  = "RECONCILES_TO",
      n.domain = "CatalogLOB",
      n.range  = "BusinessSegment",
      n.notes  = "Catalog LOB reconciled to a canonical corporate segment. "
               + "Approximate mapping (skos:closeMatch semantics). "
               + "Edge carries confidence (0.0–1.0). Not always 1:1 (e.g., AWMCIB).";

// HAS_PRODUCT_LINE  —  CatalogLOB → ProductLine
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasProductLine"})
  SET n.label  = "HAS_PRODUCT_LINE",
      n.domain = "CatalogLOB",
      n.range  = "ProductLine",
      n.notes  = "LOB contains product lines. Local catalog hierarchy.";

// HAS_PRODUCT  —  ProductLine → Product
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasProduct"})
  SET n.label  = "HAS_PRODUCT",
      n.domain = "ProductLine",
      n.range  = "Product",
      n.notes  = "Product line contains products. Local catalog hierarchy.";

// HAS_DEV_TEAM  —  Product → DevTeam
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasDevTeam"})
  SET n.label  = "HAS_DEV_TEAM",
      n.domain = "Product",
      n.range  = "DevTeam",
      n.notes  = "Product has an owning dev team. Local organizational linkage.";

// HAS_JIRA_BOARD  —  DevTeam → JiraBoard
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasJiraBoard"})
  SET n.label  = "HAS_JIRA_BOARD",
      n.domain = "DevTeam",
      n.range  = "JiraBoard",
      n.notes  = "Dev team's Jira planning board. Local tooling linkage.";
