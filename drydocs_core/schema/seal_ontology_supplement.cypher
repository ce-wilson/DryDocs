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

// ----- TOMRole concept scheme — the DECLARED vocabulary (G70) ----------------
// SEEDED FROM config/taxonomy/tom-role-vocabulary.yaml (gate tom-roles-
// enumeration-and-cardinality §F3, signed 2026-08-11) and GUARDED against it:
// tests/unit/test_tom_role_vocabulary.py fails this file when the declaration
// moves, so the two cannot drift the way §A1b measured (the old YAML list
// moved twice inside one gate with the suite green — because no code read it).
// 16 concepts: the §G register's 7 REQUIRED + 9 optional, incl. the §G9
// Operate Manager split (three classes; the old level property retires — see
// migrate_tom_role_split_g70.cypher) and BOTH SRE rows (close-out 2026-08-11:
// which one a team uses is an implementation choice, so a reorganisation
// moves data, not vocabulary). `required` rides the concept (§B3); the
// cardinality rule — one-or-more holders everywhere (§B1) — is recorded ONCE
// on the scheme, never per concept. `active` is the §F6b lifecycle flag:
// retirement is a state, not a deletion. `derived` marks the SRE rows G71's
// completeness report must EXCLUDE.

MERGE (s:SkosConceptScheme {id: "tom_roles"})
  SET s.label = "SEAL Technical Operational Roles",
      s.cardinality = "one-or-more",
      s.source = "gate seal-tom-attribution-reshape (2026-07-10 §B) as amended by tom-roles-enumeration-and-cardinality (2026-08-11 §G), declared in config/taxonomy/tom-role-vocabulary.yaml (G70)";

// -- required (the §G short list) --
MERGE (c1:TOMRole {id: "application_owner"})
  SET c1.pref_label = "Application Owner", c1.required = true, c1.scope = "Individual", c1.active = true;
MERGE (c2:TOMRole {id: "primary_information_owner"})
  SET c2.pref_label = "Primary Information Owner", c2.required = true, c2.scope = "Individual", c2.active = true;
MERGE (c3:TOMRole {id: "backup_information_owner"})
  SET c3.pref_label = "Backup Information Owner", c3.required = true, c3.scope = "Individual", c3.active = true;
// K5 gate 2026-07-20: cto is NOT shared with product_roles (families independent) —
// REMOVE clears the stale shared_with stamp on already-loaded graphs (idempotent).
MERGE (c4:TOMRole {id: "cto"})
  SET c4.pref_label = "CTO", c4.required = true, c4.scope = "Individual", c4.active = true
  REMOVE c4.shared_with;
MERGE (c5:TOMRole {id: "technology_risk_controls"})
  SET c5.pref_label = "Technology Risk & Controls", c5.required = true, c5.scope = "Individual", c5.active = true;
MERGE (c6:TOMRole {id: "design_authority"})
  SET c6.pref_label = "Design Authority", c6.required = true, c6.scope = "Individual", c6.active = true;
MERGE (c16:TOMRole {id: "backup_application_owner"})
  SET c16.pref_label = "Backup Application Owner", c16.required = true, c16.scope = "Individual", c16.active = true;

// -- optional (the extended list) --
// The bare class is defined by RESPONSIBILITY SCOPE (change, problem and
// incident resolution), not a level (§G9) — L1/L2 are levelled coverage tiers.
MERGE (c7:TOMRole {id: "operate_manager"})
  SET c7.pref_label = "Operate Manager", c7.required = false, c7.scope = "Individual", c7.active = true,
      c7.definition = "responsibility scope: change, problem and incident resolution (§G9)";
MERGE (c8:TOMRole {id: "operate_manager_l1"})
  SET c8.pref_label = "L1 Operate Manager", c8.required = false, c8.scope = "Individual", c8.active = true;
MERGE (c9:TOMRole {id: "operate_manager_l2"})
  SET c9.pref_label = "L2 Operate Manager", c9.required = false, c9.scope = "Individual", c9.active = true;
MERGE (c10:TOMRole {id: "chief_business_technologist"})
  SET c10.pref_label = "Chief Business Technologist", c10.required = false, c10.scope = "Individual", c10.active = true;
MERGE (c11:TOMRole {id: "deployment_owner"})
  SET c11.pref_label = "Deployment Owner", c11.required = false, c11.scope = "Individual", c11.active = true;
MERGE (c12:TOMRole {id: "deployment_information_owner"})
  SET c12.pref_label = "Deployment Information Owner", c12.required = false, c12.scope = "Individual", c12.active = true;
MERGE (c13:TOMRole {id: "application_module_owner"})
  SET c13.pref_label = "Application Module Owner", c13.required = false, c13.scope = "Individual", c13.active = true;
MERGE (c14:TOMRole {id: "site_reliability_engineer"})
  SET c14.pref_label = "Site Reliability Engineer", c14.required = false, c14.scope = "Individual", c14.active = true,
      c14.derived = true;
MERGE (c15:TOMRole {id: "sre_devops_incident_resolver_team"})
  SET c15.pref_label = "Incident Resolver – SRE / DevOps Team", c15.required = false, c15.scope = "Group", c15.active = true,
      c15.derived = true;
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
