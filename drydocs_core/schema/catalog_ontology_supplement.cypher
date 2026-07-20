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


// =============================================================================
// PAT ontology additions: AreaProduct, team support relationships, human roles
// Applied after the base catalog supplement; idempotent.
// Source: PAT Product Catalog / product-overview.md / pat.md (2026-06-09)
// =============================================================================


// ----- Local-namespace anchor terms (new node type) -------------------------

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#AreaProduct"})
  SET n.label = "Area Product",
      n.notes = "Area Product Group (Team of Teams). Intermediate organizational level "
              + "between Product and DevTeam in the PAT/Align hierarchy. A group of Teams "
              + "that plan and deliver epics together. Synonymous with Area Product Group.";


// ----- :SUBCLASS_OF wiring  (AreaProduct is a local Entity — no W3C parent) -
// No SUBCLASS_OF needed: dd:AreaProduct is a standalone local entity class.


// ----- :LocalRelationship declarations — PAT relationships ------------------

// HAS_APPLICATION  —  Product → Application
// Local alias; PROV matrix would say WAS_ATTRIBUTED_TO (Entity→Agent).
// Resolves SnapshotWriter references at writer.py:45,67.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasApplication"})
  SET n.label  = "HAS_APPLICATION",
      n.domain = "Product",
      n.range  = "BusinessApplication",
      n.notes  = "Product owns a set of SEAL-registered applications. Local alias; "
               + "matrix equivalent is WAS_ATTRIBUTED_TO (Entity→Agent). "
               + "Written by pat_product_mapping loader.";

// HAS_AREA_PRODUCT  —  Product → AreaProduct
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#hasAreaProduct"})
  SET n.label  = "HAS_AREA_PRODUCT",
      n.domain = "Product",
      n.range  = "AreaProduct",
      n.notes  = "Product contains Area Product Groups (Team of Teams). Local catalog hierarchy.";

// HAS_DEV_TEAM (AreaProduct source)  —  AreaProduct → DevTeam
// Same label as Product→DevTeam (catalog_has_dev_team); from_node type distinguishes.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#areaProductHasDevTeam"})
  SET n.label  = "HAS_DEV_TEAM",
      n.domain = "AreaProduct",
      n.range  = "DevTeam",
      n.notes  = "Area Product Group contains DevTeams. Same relationship label as "
               + "Product→DevTeam; query context (from_node label) distinguishes the two.";

// SUPPORTS  —  DevTeam → AreaProduct   (range resolved by SME 2026-06-21; was "Product or AreaProduct")
// Edge properties: team_type (aligned|flex|dedicated), sponsored (bool).
// Agent→Entity has no PROV-O matrix row; local-only.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#supports"})
  SET n.label  = "SUPPORTS",
      n.domain = "DevTeam",
      n.range  = "AreaProduct",
      n.notes  = "DevTeam is aligned to / supports an AreaProduct (Team-of-Teams). Range resolved "
               + "to AreaProduct (SME 2026-06-21); Product is reached via Product▸AreaProduct▸DevTeam. "
               + "Edge carries team_type (aligned|flex|dedicated) and sponsored (bool); 'aligned to' "
               + "= team_type=aligned. Agent→Entity has no PROV-O matrix row; local-only.";

// WAS_ATTRIBUTED_TO {role: developed_by}  —  BusinessApplication → DevTeam, joined by SEALID
// FLIPPED at K4 (2026-07-15; gate 2026-07-10 §E) from DevTeam-[:DEVELOPS]->BusinessApplication:
// post-reclass, Entity → Agent = prov:wasAttributedTo. Migration:
// drydocs/loaders/cypher/migrate_develops_to_was_attributed_to.cypher.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#develops"})
  SET n.label  = "WAS_ATTRIBUTED_TO",
      n.role   = "developed_by",
      n.domain = "BusinessApplication",
      n.range  = "DevTeam",
      n.notes  = "BusinessApplication was developed by a DevTeam (role=developed_by on the shared "
               + "WAS_ATTRIBUTED_TO label), reconciled by SEALID. prov:wasAttributedTo (Entity->Agent). "
               + "Was DevTeam-[:DEVELOPS]-> pre-K4.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#develops"})
MATCH (pp:OntologyTerm:ProvProperty         {iri: "http://www.w3.org/ns/prov#wasAttributedTo"})
MERGE (local)-[:MAPS_TO]->(pp);

// HAS_MEMBERSHIP (DevTeam source)  —  DevTeam → Membership
// Reuses org:Membership n-ary pattern from SEAL. Sourced from PAT team-role data.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#devTeamHasMembership"})
  SET n.label  = "HAS_MEMBERSHIP",
      n.domain = "DevTeam",
      n.range  = "Membership",
      n.notes  = "DevTeam has a timed role-holder membership (PAT team staffing). "
               + "Reuses the org:Membership n-ary pattern from SEAL. "
               + "PAT roles: Tech Partner, Area Tech Partner, Software Engineering Manager, "
               + "Software Engineer, SRE Director, Site Reliability Engineer, etc.";


// ----- Role node seeds (SEAL + PAT canonical role vocabulary) ---------------
// MERGE on `name` — this matches the SEAL loader pattern exactly:
//   seal_applications.cypher: MERGE (r:Role {name: 'Application Owner'})
//   seal_contacts.cypher:     MATCH (r:Role {name: row.role_name})
// role_id is a secondary property; role_name constraint (REQUIRE r.name IS UNIQUE)
// is the live uniqueness guarantee. Running this supplement before the SEAL loaders
// guarantees the nodes exist; running it after is also safe (idempotent SET).

// — SEAL embedded roles (seal_applications.cypher) —
MERGE (n:Role {name: 'Application Owner'})
  SET n.role_id = 'application_owner';
MERGE (n:Role {name: 'CTO'})
  SET n.role_id = 'cto';
MERGE (n:Role {name: 'Primary Information Owner'})
  SET n.role_id = 'primary_information_owner';

// — SEAL contact roles (seal_contacts.cypher) —
MERGE (n:Role {name: 'Backup Information Owner'})
  SET n.role_id = 'backup_information_owner';
MERGE (n:Role {name: 'Design Authority'})
  SET n.role_id = 'design_authority';
MERGE (n:Role {name: 'Chief Business Technologist'})
  SET n.role_id = 'chief_business_technologist';
MERGE (n:Role {name: 'L1 Operate Manager'})
  SET n.role_id = 'l1_operate_manager';
MERGE (n:Role {name: 'L2 Operate Manager'})
  SET n.role_id = 'l2_operate_manager';
MERGE (n:Role {name: 'Backup Application Owner'})
  SET n.role_id = 'backup_application_owner';
MERGE (n:Role {name: 'Risk Manager'})
  SET n.role_id = 'risk_manager';

// — PAT Technology roles (team-level; sourced from product-overview.md) —
MERGE (n:Role {name: 'Tech Partner'})
  SET n.role_id = 'tech_partner';
MERGE (n:Role {name: 'Area Tech Partner'})
  SET n.role_id = 'area_tech_partner';
MERGE (n:Role {name: 'Head of Technology'})
  SET n.role_id = 'head_of_technology';
MERGE (n:Role {name: 'Principal Engineer'})
  SET n.role_id = 'principal_engineer';
MERGE (n:Role {name: 'Software Engineering Manager'})
  SET n.role_id = 'sw_engineering_manager';
MERGE (n:Role {name: 'Software Engineer'})
  SET n.role_id = 'software_engineer';
MERGE (n:Role {name: 'Product Architect'})
  SET n.role_id = 'product_architect';
MERGE (n:Role {name: 'SRE Director'})
  SET n.role_id = 'sre_director';
MERGE (n:Role {name: 'Site Reliability Engineer'})
  SET n.role_id = 'site_reliability_engineer';

// — PAT Product / Portfolio roles —
MERGE (n:Role {name: 'Product Manager'})
  SET n.role_id = 'product_manager';
MERGE (n:Role {name: 'Product Delivery Manager'})
  SET n.role_id = 'product_delivery_manager';
MERGE (n:Role {name: 'Portfolio Operations'})
  SET n.role_id = 'portfolio_operations';

// — D&A roles —
MERGE (n:Role {name: 'LOB Head of D&A'})
  SET n.role_id = 'lob_head_of_da';
MERGE (n:Role {name: 'Portfolio Lead Data Owner'})
  SET n.role_id = 'portfolio_lead_data_owner';
MERGE (n:Role {name: 'Data Owner'})
  SET n.role_id = 'data_owner';
MERGE (n:Role {name: 'Area Data Owner'})
  SET n.role_id = 'area_data_owner';
MERGE (n:Role {name: 'Analytic Lead'})
  SET n.role_id = 'analytic_lead';
MERGE (n:Role {name: 'Information Owner'})
  SET n.role_id = 'information_owner';

// — CCB Operations roles (product-overview.md §CCB Operations) —
// These roles govern cross-product readiness, change management, and employee
// readiness. They are not in SEAL — will be loaded via PAT contacts.
MERGE (n:Role {name: 'CCB Operations Strategy Lead'})
  SET n.role_id = 'ccb_operations_strategy_lead';
MERGE (n:Role {name: 'Operations Delivery Project Manager'})
  SET n.role_id = 'odpm';
MERGE (n:Role {name: 'Agile Employee Readiness Manager'})
  SET n.role_id = 'erm';


// =============================================================================
// Product Cabinet additions (K6; gate product-cabinet-attribution SIGNED OFF
// 2026-07-20 — config/gate-log.md). Applied after the PAT additions; idempotent.
// Registration only — NO attribution loader exists (blocked company-side until a
// person-level PAT cabinet extract lands). The reified pattern reuses the seal
// supplement's Attribution LocalClass and its #hasAgent term as family-agnostic
// infrastructure (the C8 duplicate-triple guard — the (Attribution, HAS_AGENT,
// Employee) triple is registered exactly once).
// =============================================================================


// ----- Local-namespace anchor terms ------------------------------------------

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#ProductRole"})
  SET n.label = "ProductRole",
      n.notes = "Product Cabinet role concept (skos:Concept semantics), scheme product_roles. "
              + "EXACTLY the fixed 7 — no cto: the K5 gate (2026-07-20) decided the "
              + "ProductRole and TOMRole families are INDEPENDENT (supersedes the 2026-07-10 "
              + "§B shared-cto record; rename history on the tech_partner concept). DISTINCT "
              + "from :Role (org:Role — PAT hierarchy membership) and from :TOMRole. Scope: "
              + ":Product / :AreaProduct only, never :BusinessApplication.";


// ----- :LocalRelationship declarations — Product Cabinet attribution ---------
// Catalog-domain twins of the seal qualified-attribution terms (their triples
// differ — the HAS_DEV_TEAM dual-registration precedent). The Attribution
// -[:HAS_AGENT]-> Employee hop is NOT re-declared here: it reuses the seal
// supplement's #hasAgent term (rescoped family-agnostic at the K5 sign-off).

// QUALIFIED_ATTRIBUTION — Product|AreaProduct → Attribution (prov:qualifiedAttribution)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#cabinetQualifiedAttribution"})
  SET n.label  = "QUALIFIED_ATTRIBUTION",
      n.domain = "Product|AreaProduct",
      n.range  = "Attribution",
      n.notes  = "Entry point to the reified Product Cabinet role-holder record. One "
               + "Attribution per (scope-node, ProductRole) pair; area_product_owner and "
               + "tech_partner attributions attach only to :AreaProduct. "
               + "prov:qualifiedAttribution.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#cabinetQualifiedAttribution"})
MATCH (pp:OntologyTerm:ProvProperty         {iri: "http://www.w3.org/ns/prov#qualifiedAttribution"})
MERGE (local)-[:MAPS_TO]->(pp);

// HAD_ROLE — Attribution → ProductRole (prov:hadRole)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#cabinetHadRole"})
  SET n.label  = "HAD_ROLE",
      n.domain = "Attribution",
      n.range  = "ProductRole",
      n.notes  = "Names which Product Cabinet role the Attribution grants (the fixed 7, "
               + "no cto). prov:hadRole.";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#cabinetHadRole"})
MATCH (pp:OntologyTerm:ProvProperty         {iri: "http://www.w3.org/ns/prov#hadRole"})
MERGE (local)-[:MAPS_TO]->(pp);

// WAS_ATTRIBUTED_TO {role: product_cabinet_role_holder} — Product|AreaProduct → Employee
// The collapsed simple form (gate §C: BOTH forms load — a deliberate deviation from
// the K4 TOM qualified-only resolution; the reified form remains the multi-person
// carrier). role distinguishes this instance on the shared WAS_ATTRIBUTED_TO label.
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#cabinetAttributedTo"})
  SET n.label  = "WAS_ATTRIBUTED_TO",
      n.role   = "product_cabinet_role_holder",
      n.domain = "Product|AreaProduct",
      n.range  = "Employee",
      n.notes  = "Collapsed Product Cabinet attribution (catalog twin of the seal simple "
               + "form; same :AreaProduct-only scope rules as the reified chain). "
               + "prov:wasAttributedTo (Entity->Agent).";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#cabinetAttributedTo"})
MATCH (pp:OntologyTerm:ProvProperty         {iri: "http://www.w3.org/ns/prov#wasAttributedTo"})
MERGE (local)-[:MAPS_TO]->(pp);


// ----- ProductRole concept scheme (the fixed 7 — K5 gate; scheme FIXED) -------
// New Product Cabinet roles require a new gate (the tom_roles precedent).
// area_product_owner and tech_partner attach ONLY to :AreaProduct (scope
// property); the other five attach to :Product or :AreaProduct.

MERGE (s:SkosConceptScheme {id: "product_roles"})
  SET s.label = "Product Cabinet Roles",
      s.source = "gate product-cabinet-attribution (signed off 2026-07-20, config/gate-log.md)",
      s.fixed = true;
MERGE (p1:ProductRole {id: "area_product_owner"})  SET p1.pref_label = "Area Product Owner",
                                                       p1.scope = "AreaProduct";
MERGE (p2:ProductRole {id: "product_owner"})       SET p2.pref_label = "Product Owner";
MERGE (p3:ProductRole {id: "product_architect"})   SET p3.pref_label = "Product Architect";
MERGE (p4:ProductRole {id: "tech_partner"})        SET p4.pref_label = "Tech Partner",
                                                       p4.scope = "AreaProduct",
                                                       p4.change_note = "skos:changeNote — in PAT the mapping "
                                                         + "changed slightly: this area-product role was formerly "
                                                         + "named 'CTO' in SEAL; SEAL's CTO now denotes the "
                                                         + "product-level role. Recorded at the K5 gate "
                                                         + "(2026-07-20); supersedes the 2026-07-10 §B "
                                                         + "'CTO in both families' record.";
MERGE (p5:ProductRole {id: "data_owner"})          SET p5.pref_label = "Data Owner";
MERGE (p6:ProductRole {id: "data_certifier"})      SET p6.pref_label = "Data Certifier";
MERGE (p7:ProductRole {id: "analytics_lead"})      SET p7.pref_label = "Analytics Lead";
WITH 1 AS _
MATCH (s:SkosConceptScheme {id: "product_roles"})
MATCH (c:ProductRole)
MERGE (c)-[:IN_SCHEME]->(s);
