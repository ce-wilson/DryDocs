// =============================================================================
// seal_ontology_supplement.cypher
//
// Anchor terms specific to the SEAL domain. Idempotent. Apply once after
// the M0 bootstrap; no-op on re-run.
//
// Node classifications (K4 reshape applied 2026-07-15, gate 2026-07-10):
//   BusinessApplication → prov:Entity / dprod:DataProduct (was prov:SoftwareAgent)
//   Port         → dprod:Port (data product port; local, no PROV-O direct)
//   Membership   → org:Membership (DEPRECATED path — see qualified attribution)
//   Role         → org:Role (PAT hierarchy only — distinct from TOMRole)
//   Employee     → prov:Agent (person)
//   Attribution  → prov:Attribution (reified influence node)
//   TOMRole      → skos:Concept (SEAL Technical Operational role vocabulary)
// =============================================================================


// ----- Local-namespace anchor terms (node types) ----------------------------

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#BusinessApplication"})
  SET n.label = "BusinessApplication",
      n.notes = "A SEAL-registered application — a data-product/asset record. "
              + "prov:Entity / dprod:DataProduct (K4 reclass, gate 2026-07-10 §A; was prov:SoftwareAgent). "
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

MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#BusinessApplication"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Entity"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.seal_supplement";
MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#BusinessApplication"})
MATCH (dc:OntologyTerm:DprodClass  {iri: "https://ekgf.github.io/dprod#DataProduct"})
MERGE (lc)-[r:SUBCLASS_OF]->(dc)
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
      n.domain = "BusinessApplication",
      n.range  = "Port",
      n.notes  = "Application exposes a data port (EventProcessing or BatchProcessing). "
               + "Follows dprod:hasPort pattern.";

// DEPRECATED 2026-07-15 (K4, gate 2026-07-10 §C) — SEAL TOM role-holders use the
// qualified-attribution pattern below; org:Membership stays for PAT only.
// HAS_MEMBERSHIP  —  BusinessApplication → Membership  (org:hasMembership)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasMembership"})
  SET n.label  = "HAS_MEMBERSHIP",
      n.domain = "BusinessApplication",
      n.range  = "Membership",
      n.notes  = "Application has a timed role-holder membership. Semantics: org:hasMembership.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasMembership"})
MATCH (org:OntologyTerm:OrgProperty         {iri: "http://www.w3.org/ns/org#hasMembership"})
MERGE (local)-[:MAPS_TO]->(org);

// DEPRECATED 2026-07-15 (K4, gate 2026-07-10 §C) — replacement: HAD_ROLE → TOMRole.
// OF_ROLE  —  Membership → Role  (org:role)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#ofRole"})
  SET n.label  = "OF_ROLE",
      n.domain = "Membership",
      n.range  = "Role",
      n.notes  = "Membership is for a specific named role. Semantics: org:role.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#ofRole"})
MATCH (org:OntologyTerm:OrgProperty         {iri: "http://www.w3.org/ns/org#role"})
MERGE (local)-[:MAPS_TO]->(org);

// DEPRECATED 2026-07-15 (K4, gate 2026-07-10 §C) — replacement: HAS_AGENT → Employee.
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


// ============================================================================
// K4 reshape additions (gate 2026-07-10 §B, applied 2026-07-15) — the
// qualified-attribution pattern + the TOMRole controlled vocabulary.
// ============================================================================

// Migration: retire the pre-K4 SoftwareAgent superclass edge on an
// already-bootstrapped graph (idempotent — no-op when absent).
MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#BusinessApplication"})
      -[r:SUBCLASS_OF]->
      (:OntologyTerm:ProvClass {iri: "http://www.w3.org/ns/prov#SoftwareAgent"})
DELETE r;

// ----- New local classes -----------------------------------------------------

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Attribution"})
  SET n.label = "Attribution",
      n.notes = "Reified PROV influence node for the TOM role-holder pattern: "
              + "BusinessApplication -[:QUALIFIED_ATTRIBUTION]-> Attribution "
              + "-[:HAS_AGENT]-> Employee ; -[:HAD_ROLE]-> TOMRole. prov:Attribution.";
MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Attribution"})
MATCH (pc:OntologyTerm:ProvClass  {iri: "http://www.w3.org/ns/prov#Attribution"})
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.seal_supplement";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#TOMRole"})
  SET n.label = "TOMRole",
      n.notes = "SEAL Technical Operational role concept (skos:Concept semantics). "
              + "DISTINCT from :Role (org:Role — PAT product hierarchy only) and from "
              + ":ProductRole. Fixed 7-concept scheme below; cto is NOT shared with the "
              + "K5 ProductRole scheme (K5 gate 2026-07-20: families independent; rename "
              + "history in config/gate-log.md).";

// ----- Qualified-attribution relationships (planned -> active at K4) --------

// QUALIFIED_ATTRIBUTION — BusinessApplication → Attribution (prov:qualifiedAttribution)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#qualifiedAttribution"})
  SET n.label  = "QUALIFIED_ATTRIBUTION",
      n.domain = "BusinessApplication",
      n.range  = "Attribution",
      n.notes  = "Entry point to the reified TOM role-holder record. prov:qualifiedAttribution.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#qualifiedAttribution"})
MATCH (pp:OntologyTerm:ProvProperty         {iri: "http://www.w3.org/ns/prov#qualifiedAttribution"})
MERGE (local)-[:MAPS_TO]->(pp);

// HAS_AGENT — Attribution → Employee (prov:agent)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasAgent"})
  SET n.label  = "HAS_AGENT",
      n.domain = "Attribution",
      n.range  = "Employee",
      n.notes  = "Names which Employee the Attribution is about. prov:agent.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasAgent"})
MATCH (pp:OntologyTerm:ProvProperty         {iri: "http://www.w3.org/ns/prov#agent"})
MERGE (local)-[:MAPS_TO]->(pp);

// HAD_ROLE — Attribution → TOMRole (prov:hadRole)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hadRole"})
  SET n.label  = "HAD_ROLE",
      n.domain = "Attribution",
      n.range  = "TOMRole",
      n.notes  = "Names which TOM role the Attribution grants. prov:hadRole.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hadRole"})
MATCH (pp:OntologyTerm:ProvProperty         {iri: "http://www.w3.org/ns/prov#hadRole"})
MERGE (local)-[:MAPS_TO]->(pp);

// ----- TOMRole concept scheme (the fixed 7 — gate §B revised set) -----------
// Multi-person roles load the qualified/reified form; Operate Manager L1/L2 is
// ONE concept — the level (L1|L2) rides the Attribution node as a property
// (gate wording "one or both", 1–3 persons), keeping the scheme at 7 concepts.

MERGE (s:SkosConceptScheme {id: "tom_roles"})
  SET s.label = "SEAL Technical Operational Roles",
      s.source = "gate seal-tom-attribution-reshape (2026-07-10 §B)";
MERGE (c1:TOMRole {id: "application_owner"})          SET c1.pref_label = "Application Owner";
MERGE (c2:TOMRole {id: "primary_information_owner"})  SET c2.pref_label = "Primary Information Owner";
MERGE (c3:TOMRole {id: "backup_information_owner"})   SET c3.pref_label = "Backup Information Owner";
// K5 gate 2026-07-20: cto is NOT shared with product_roles (families independent) —
// REMOVE clears the stale shared_with stamp on already-loaded graphs (idempotent).
MERGE (c4:TOMRole {id: "cto"})                        SET c4.pref_label = "CTO"
                                                      REMOVE c4.shared_with;
MERGE (c5:TOMRole {id: "technology_risk_controls"})   SET c5.pref_label = "Technology Risk & Controls";
MERGE (c6:TOMRole {id: "design_authority"})           SET c6.pref_label = "Design Authority";
MERGE (c7:TOMRole {id: "operate_manager"})            SET c7.pref_label = "Operate Manager",
                                                          c7.levels = "L1,L2";
WITH 1 AS _
MATCH (s:SkosConceptScheme {id: "tom_roles"})
MATCH (c:TOMRole)
MERGE (c)-[:IN_SCHEME]->(s);

// ----- Provenance of the SEAL record itself (gate §D, active at K4) ---------

// HAD_PRIMARY_SOURCE — BusinessApplication → Document (prov:hadPrimarySource)
// Edge-active only: the Document node + loader arrive with drydocs-docmeta.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hadPrimarySource"})
  SET n.label  = "HAD_PRIMARY_SOURCE",
      n.domain = "BusinessApplication",
      n.range  = "Document",
      n.notes  = "The SEAL record was primarily sourced from a scraped Document. "
               + "prov:hadPrimarySource (sub-property of wasDerivedFrom).";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hadPrimarySource"})
MATCH (pp:OntologyTerm:ProvProperty         {iri: "http://www.w3.org/ns/prov#hadPrimarySource"})
MERGE (local)-[:MAPS_TO]->(pp);
