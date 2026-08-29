// =============================================================================
// infrastructure_ontology_supplement.cypher — server-location domain supplement
//
// Anchor terms for the infrastructure/server-location domain (Epic Z; gate
// server-location-ontology SIGNED OFF 12/12, 2026-08-19 — config/gate-log.md).
// Idempotent; applied by `drydocs apply-supplements` as chain step 5 (see
// supplements.py).
//
// Declares:  Server (dd:Server), DataCenter (dd:DataCenter, functions as
//            prov:Location), RESOLVES_TO_SERVER (local identity edge, K2
//            evidence discipline), LOCATED_IN (prov:atLocation), and the
//            technology-port RUNS_ON leg (local placement edge, role
//            technology_port — the §C2 SME reshape; HAS_PORT itself is
//            seal's term, reused not redeclared).
//
// THE STANDING CAUTION (§B4): dd:DataCenter is PHYSICAL geography — never
// the Control-M scheduling "data center" (whose name encodes a default run
// time). The two never join by field name.
// =============================================================================


// ----- Local-namespace anchor terms ------------------------------------------

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#Server"})
  SET n.label = "Server",
      n.notes = "Physical/virtual server from the per-application "
              + "infrastructure export — the INVENTORY backbone (gate §A1). "
              + "Distinct from ExecutionHost (Control-M's view, often an LB "
              + "alias), ControlMServer (a scheduler instance) and "
              + "ControlMHostGroup (an LB set); joined to ExecutionHost only "
              + "via RESOLVES_TO_SERVER's evidence-carrying edge. Local "
              + "infrastructure class, no W3C equivalent; carries "
              + "designation (PROD|DR, §A3) and os_product/os_version (§A2).";

MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#DataCenter"})
  SET n.label = "Data Center",
      n.notes = "PHYSICAL data center/building (gate §B1) — functions as the "
              + "prov:Location target of LOCATED_IN. Carries the geography "
              + "ladder as properties (building, city, state, country) plus "
              + "location_grain, the Idea-90 mixed-grain declaration (§B2). "
              + "NEVER the Control-M scheduling DC (§B4).";


// =============================================================================
// :LocalRelationship declarations
// =============================================================================

// RESOLVES_TO_SERVER  —  ExecutionHost → Server  (LOCAL identity edge)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#resolvesToServer"})
  SET n.label  = "RESOLVES_TO_SERVER",
      n.domain = "ExecutionHost",
      n.range  = "Server",
      n.notes  = "The tiered identity join (gate §C1, the K2 precedent): an "
               + "EDGE carrying match_tier (exact|normalized|dns-resolved), "
               + "match_evidence and resolved_at — never a node merge. One "
               + "LB-alias host may resolve to many servers (the Z4 case); "
               + "unmatched hosts get no edge and stay visibly unmatched.";

// LOCATED_IN  —  Server → DataCenter  (prov:atLocation)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#locatedIn"})
  SET n.label  = "LOCATED_IN",
      n.domain = "Server",
      n.range  = "DataCenter",
      n.notes  = "Physical placement (gate §B1); rack rides the edge. Maps "
               + "to prov:atLocation — DataCenter functions as the "
               + "prov:Location. THE Z5 MAP CONTRACT hangs here: 'a located "
               + "label' means reaches-geography-via-LOCATED_IN.";
// prov:atLocation is seeded HERE, not in ontology.cypher: the base PROV seed
// set predates the location domain, and a MATCH against an unseeded term
// would silently no-op the MAPS_TO (the pre-G29 quiet-absence class).
// Idempotent MERGE — harmless if the base seed ever adds it.
MERGE (n:OntologyTerm:ProvProperty {iri: "http://www.w3.org/ns/prov#atLocation"})
  SET n.label = "at location";
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#locatedIn"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#atLocation"})
MERGE (local)-[:MAPS_TO]->(prov);

// RUNS_ON {role: technology_port}  —  Port → Server  (LOCAL placement edge)
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#technologyPortRunsOn"})
  SET n.label  = "RUNS_ON",
      n.domain = "Port",
      n.range  = "Server",
      n.notes  = "The §C2 technology-port leg (the SME reshape): "
               + "(:BusinessApplication)-[:HAS_PORT]->(:Port {kind: "
               + "Technology})-[:RUNS_ON {role: technology_port}]->(:Server). "
               + "Same RUNS_ON label as the scheduler placement family — "
               + "role disambiguates; placement, never attribution. HAS_PORT "
               + "is seal's term (kinds widened by the same ruling), reused "
               + "not redeclared.";
