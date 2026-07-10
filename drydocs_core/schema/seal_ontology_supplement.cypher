// =============================================================================
// seal_ontology_supplement.cypher
//
// Anchor terms specific to the SEAL domain. Idempotent. Apply once after
// the M0 bootstrap; no-op on re-run.
//
// Node classifications:
//   Application  → prov:Agent (SoftwareAgent — a managed software system)
//   Port         → dprod:Port (data product port; local, no PROV-O direct)
//   Membership   → org:Membership
//   Role         → org:Role
//   Employee     → prov:Agent (person)
// =============================================================================


// ----- Local-namespace anchor terms (node types) ----------------------------

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Application"})
  SET n.label = "Application",
      n.notes = "A SEAL-registered software application. Subclass of prov:SoftwareAgent. "
              + "Carries governance metadata (SOX, risk, hosting) from DECO_SEAL_APP_INFO.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Port"})
  SET n.label = "Port",
      n.notes = "A data product port on an Application (EventProcessing or BatchProcessing). "
              + "Modelled after dprod:Port. Kind stored as node property.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Membership"})
  SET n.label = "Membership",
      n.notes = "A timed role-holder record linking an Application to an Employee via a Role. "
              + "Carries valid_from / valid_to for temporal role tracking. "
              + "Maps to org:Membership.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Role"})
  SET n.label = "Role",
      n.notes = "A named responsibility role (e.g., Application Owner, CTO). "
              + "Maps to org:Role.";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Employee"})
  SET n.label = "Employee",
      n.notes = "A person identified by SID. Subclass of prov:Agent (foaf:Person). "
              + "Carries full_name and email; populated from SEAL contact extracts.";


// ----- :SUBCLASS_OF wiring to PROV-O / W3C anchors -------------------------

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Application"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#SoftwareAgent"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.seal_supplement";

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Employee"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Agent"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.seal_supplement";


// ----- :LocalRelationship declarations  —  SEAL relationship → W3C mapping -

// HAS_PORT  —  Application → Port
// Maps to dprod:hasPort pattern; no PROV-O equivalent.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasPort"})
  SET n.label  = "HAS_PORT",
      n.domain = "Application",
      n.range  = "Port",
      n.notes  = "Application exposes a data port (EventProcessing or BatchProcessing). "
               + "Follows dprod:hasPort pattern.";

// HAS_MEMBERSHIP  —  Application → Membership  (org:hasMembership)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasMembership"})
  SET n.label  = "HAS_MEMBERSHIP",
      n.domain = "Application",
      n.range  = "Membership",
      n.notes  = "Application has a timed role-holder membership. Semantics: org:hasMembership.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasMembership"})
MATCH (org:OntologyTerm:OrgProperty         {iri: "http://www.w3.org/ns/org#hasMembership"})
MERGE (local)-[:MAPS_TO]->(org);

// OF_ROLE  —  Membership → Role  (org:role)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#ofRole"})
  SET n.label  = "OF_ROLE",
      n.domain = "Membership",
      n.range  = "Role",
      n.notes  = "Membership is for a specific named role. Semantics: org:role.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#ofRole"})
MATCH (org:OntologyTerm:OrgProperty         {iri: "http://www.w3.org/ns/org#role"})
MERGE (local)-[:MAPS_TO]->(org);

// HELD_BY  —  Membership → Employee  (inverse of org:member)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#heldBy"})
  SET n.label  = "HELD_BY",
      n.domain = "Membership",
      n.range  = "Employee",
      n.notes  = "Membership is held by an employee. Inverse of org:member / org:hasMember. "
               + "Direction chosen so membership is the query start point.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#heldBy"})
MATCH (org:OntologyTerm:OrgProperty         {iri: "http://www.w3.org/ns/org#member"})
MERGE (local)-[:MAPS_TO]->(org);
