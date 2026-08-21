// =============================================================================
// ontology.cypher  —  ontology backbone seed
//
// Seeds W3C anchor terms (:OntologyTerm + :<Source>Class | :<Source>Property),
// effective-dated BusinessSegments under :Company JPMC, and a baseline DQV
// catalog (5 dimensions × 10 metrics). (SchedulerKind seeds DEPRECATED
// 2026-07-21 — see the retired block below.)
//
// Role seeds have been removed from this file. The full role vocabulary
// (SEAL + PAT + D&A + CCB Operations) is owned exclusively by
// catalog_ontology_supplement.cypher, which must be applied after bootstrap.
//
// Idempotent. Safe to re-run.
//
// Namespaces (kept in sync with drydocs/ontology/namespaces.py):
//   dprod  https://ekgf.github.io/dprod#
//   dcat   http://www.w3.org/ns/dcat#
//   prov   http://www.w3.org/ns/prov#
//   dqv    http://www.w3.org/ns/dqv#
//   org    http://www.w3.org/ns/org#
//   swo    http://www.ebi.ac.uk/swo/
//   obi    http://purl.obolibrary.org/obo/
//   iao    http://purl.obolibrary.org/obo/
//   dct    http://purl.org/dc/terms/   (property-level envelope bindings, M4;
//          documentation-grade — no dct: OntologyTerm nodes are seeded, the
//          registry of record is relationship_vocabulary.yaml property_terms)
// =============================================================================


// ----- DPROD (data product ontology) -----------------------------------------
MERGE (n:OntologyTerm:DprodClass {iri:"https://ekgf.github.io/dprod#DataProduct"})
  SET n.label = "Data Product",
      n.notes = "A unit of consumable data, governed by ports + agreements.";
MERGE (n:OntologyTerm:DprodClass {iri:"https://ekgf.github.io/dprod#Port"})         SET n.label = "Port";
MERGE (n:OntologyTerm:DprodClass {iri:"https://ekgf.github.io/dprod#InputPort"})    SET n.label = "Input Port";
MERGE (n:OntologyTerm:DprodClass {iri:"https://ekgf.github.io/dprod#OutputPort"})   SET n.label = "Output Port";
MERGE (n:OntologyTerm:DprodClass {iri:"https://ekgf.github.io/dprod#DataContract"}) SET n.label = "Data Contract";
MERGE (n:OntologyTerm:DprodClass {iri:"https://ekgf.github.io/dprod#Agreement"})    SET n.label = "Agreement";
MERGE (n:OntologyTerm:DprodProperty {iri:"https://ekgf.github.io/dprod#hasInputPort"})   SET n.label = "has input port";
MERGE (n:OntologyTerm:DprodProperty {iri:"https://ekgf.github.io/dprod#hasOutputPort"})  SET n.label = "has output port";
MERGE (n:OntologyTerm:DprodProperty {iri:"https://ekgf.github.io/dprod#exposesDataset"}) SET n.label = "exposes dataset";


// ----- DCAT v3 ----------------------------------------------------------------
MERGE (n:OntologyTerm:DcatClass {iri:"http://www.w3.org/ns/dcat#Catalog"})      SET n.label = "Catalog";
MERGE (n:OntologyTerm:DcatClass {iri:"http://www.w3.org/ns/dcat#Dataset"})      SET n.label = "Dataset";
MERGE (n:OntologyTerm:DcatClass {iri:"http://www.w3.org/ns/dcat#Distribution"}) SET n.label = "Distribution";
MERGE (n:OntologyTerm:DcatClass {iri:"http://www.w3.org/ns/dcat#DataService"})  SET n.label = "Data Service";
MERGE (n:OntologyTerm:DcatClass {iri:"http://www.w3.org/ns/dcat#DataProduct"})  SET n.label = "DCAT Data Product (v3)";
MERGE (n:OntologyTerm:DcatProperty {iri:"http://www.w3.org/ns/dcat#theme"})        SET n.label = "theme";
MERGE (n:OntologyTerm:DcatProperty {iri:"http://www.w3.org/ns/dcat#contactPoint"}) SET n.label = "contact point";
MERGE (n:OntologyTerm:DcatProperty {iri:"http://www.w3.org/ns/dcat#distribution"}) SET n.label = "distribution";
MERGE (n:OntologyTerm:DcatProperty {iri:"http://www.w3.org/ns/dcat#accessURL"})    SET n.label = "access URL";
MERGE (n:OntologyTerm:DcatProperty {iri:"http://www.w3.org/ns/dcat#downloadURL"})  SET n.label = "download URL";
MERGE (n:OntologyTerm:DcatProperty {iri:"http://www.w3.org/ns/dcat#mediaType"})    SET n.label = "media type";
MERGE (n:OntologyTerm:DcatProperty {iri:"http://www.w3.org/ns/dcat#keyword"})      SET n.label = "keyword";
MERGE (n:OntologyTerm:DcatProperty {iri:"http://www.w3.org/ns/dcat#endpointURL"})  SET n.label = "endpoint URL";


// ----- PROV-O / PROV-DM ------------------------------------------------------
MERGE (n:OntologyTerm:ProvClass {iri:"http://www.w3.org/ns/prov#Entity"})         SET n.label = "Entity";
MERGE (n:OntologyTerm:ProvClass {iri:"http://www.w3.org/ns/prov#Activity"})       SET n.label = "Activity";
MERGE (n:OntologyTerm:ProvClass {iri:"http://www.w3.org/ns/prov#Agent"})          SET n.label = "Agent";
MERGE (n:OntologyTerm:ProvClass {iri:"http://www.w3.org/ns/prov#Plan"})           SET n.label = "Plan";
MERGE (n:OntologyTerm:ProvClass {iri:"http://www.w3.org/ns/prov#Collection"})     SET n.label = "Collection";
MERGE (n:OntologyTerm:ProvClass {iri:"http://www.w3.org/ns/prov#SoftwareAgent"})  SET n.label = "Software Agent";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#used"})              SET n.label = "used";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#wasGeneratedBy"})    SET n.label = "was generated by";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#generated"})         SET n.label = "generated";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#hadMember"})         SET n.label = "had member";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#wasAttributedTo"})   SET n.label = "was attributed to";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#wasAssociatedWith"}) SET n.label = "was associated with";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#wasInformedBy"})     SET n.label = "was informed by";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#wasDerivedFrom"})    SET n.label = "was derived from";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#actedOnBehalfOf"})   SET n.label = "acted on behalf of";
// Qualified-attribution family (K4, gate 2026-07-10 §B — the TOM role-holder pattern)
MERGE (n:OntologyTerm:ProvClass {iri:"http://www.w3.org/ns/prov#Attribution"})           SET n.label = "Attribution";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#qualifiedAttribution"}) SET n.label = "qualified attribution";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#agent"})              SET n.label = "agent";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#hadRole"})            SET n.label = "had role";
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#hadPrimarySource"})   SET n.label = "had primary source";
// Occurrence-of-a-logical-entity (gate rua-load-shapes §D2, SIGNED OFF 2026-08-07;
// the term ADR 0001 already cites): a SourceOccurrence specializes its Script.
MERGE (n:OntologyTerm:ProvProperty {iri:"http://www.w3.org/ns/prov#specializationOf"})   SET n.label = "specialization of";


// ----- DQV (data quality vocabulary) -----------------------------------------
MERGE (n:OntologyTerm:DqvClass {iri:"http://www.w3.org/ns/dqv#QualityMeasurement"}) SET n.label = "Quality Measurement";
MERGE (n:OntologyTerm:DqvClass {iri:"http://www.w3.org/ns/dqv#Metric"})             SET n.label = "Metric";
MERGE (n:OntologyTerm:DqvClass {iri:"http://www.w3.org/ns/dqv#Dimension"})          SET n.label = "Dimension";
MERGE (n:OntologyTerm:DqvClass {iri:"http://www.w3.org/ns/dqv#Category"})           SET n.label = "Category";
MERGE (n:OntologyTerm:DqvClass {iri:"http://www.w3.org/ns/dqv#QualityAnnotation"})  SET n.label = "Quality Annotation";
MERGE (n:OntologyTerm:DqvProperty {iri:"http://www.w3.org/ns/dqv#hasQualityMeasurement"}) SET n.label = "has quality measurement";
MERGE (n:OntologyTerm:DqvProperty {iri:"http://www.w3.org/ns/dqv#computedOn"})            SET n.label = "computed on";
MERGE (n:OntologyTerm:DqvProperty {iri:"http://www.w3.org/ns/dqv#isMeasurementOf"})       SET n.label = "is measurement of";
MERGE (n:OntologyTerm:DqvProperty {iri:"http://www.w3.org/ns/dqv#inDimension"})           SET n.label = "in dimension";
MERGE (n:OntologyTerm:DqvProperty {iri:"http://www.w3.org/ns/dqv#value"})                 SET n.label = "value";


// ----- ORG (W3C Organization) ------------------------------------------------
MERGE (n:OntologyTerm:OrgClass {iri:"http://www.w3.org/ns/org#Organization"})       SET n.label = "Organization";
MERGE (n:OntologyTerm:OrgClass {iri:"http://www.w3.org/ns/org#OrganizationalUnit"}) SET n.label = "Organizational Unit";
MERGE (n:OntologyTerm:OrgClass {iri:"http://www.w3.org/ns/org#FormalOrganization"}) SET n.label = "Formal Organization";
MERGE (n:OntologyTerm:OrgClass {iri:"http://www.w3.org/ns/org#Membership"})         SET n.label = "Membership";
MERGE (n:OntologyTerm:OrgClass {iri:"http://www.w3.org/ns/org#Role"})               SET n.label = "Role";
MERGE (n:OntologyTerm:OrgProperty {iri:"http://www.w3.org/ns/org#hasUnit"})       SET n.label = "has unit";
MERGE (n:OntologyTerm:OrgProperty {iri:"http://www.w3.org/ns/org#hasMember"})     SET n.label = "has member";
MERGE (n:OntologyTerm:OrgProperty {iri:"http://www.w3.org/ns/org#member"})        SET n.label = "member";
MERGE (n:OntologyTerm:OrgProperty {iri:"http://www.w3.org/ns/org#memberOf"})      SET n.label = "member of";
MERGE (n:OntologyTerm:OrgProperty {iri:"http://www.w3.org/ns/org#role"})          SET n.label = "role";
MERGE (n:OntologyTerm:OrgProperty {iri:"http://www.w3.org/ns/org#hasMembership"}) SET n.label = "has membership";


// ----- SWO anchor terms (SDLC subset) ---------------------------------------
//   These 13 anchors ARE the seeded SWO set — there is no wider load step.
//   (An earlier revision of this comment said a ~250-term SDLC subset "loads
//   from ontology/reference/swo_sdlc_ontology.cypher"; that file was never
//   created — it existed only in the pre-repo savepoint and was never ported
//   (docs/history/M0-README.md). C19, 2026-07-28.) If the wider subset is
//   ever wanted it would have to be BUILT, and whether it is worth building
//   is an OPEN question — its own decision about loading a public ontology
//   into the operational database (G33 gate §A4 scoped it out).
//   First live consumer (G33, 2026-07-27): the code-snapshot loader binds
//   :CodeModule -IS_ENCODED_IN-> the Python term (SWO_0000118), with the
//   edge mapped to SWO_0000741 in ontology_supplement.cypher; Shell/SQL stay
//   seeded-but-unbound until a scan emits them (G22 rider R1 proposes the
//   :Script binding).
MERGE (n:OntologyTerm:SwoClass {iri:"http://www.ebi.ac.uk/swo/SWO_0000001"})       SET n.label = "software";
MERGE (n:OntologyTerm:SwoClass {iri:"http://purl.obolibrary.org/obo/IAO_0000025"}) SET n.label = "programming language";
MERGE (n:OntologyTerm:SwoClass {iri:"http://www.ebi.ac.uk/swo/SWO_0000118"})       SET n.label = "Python";
MERGE (n:OntologyTerm:SwoClass {iri:"http://www.ebi.ac.uk/swo/SWO_0000124"})       SET n.label = "Shell";
MERGE (n:OntologyTerm:SwoClass {iri:"http://www.ebi.ac.uk/swo/SWO_0000012"})       SET n.label = "Java";
MERGE (n:OntologyTerm:SwoClass {iri:"http://www.ebi.ac.uk/swo/SWO_0000126"})       SET n.label = "SQL";
MERGE (n:OntologyTerm:SwoClass {iri:"http://purl.obolibrary.org/obo/OBI_0200000"}) SET n.label = "data transformation";
MERGE (n:OntologyTerm:SwoProperty {iri:"http://www.ebi.ac.uk/swo/SWO_0040005"}) SET n.label = "is executed in";
MERGE (n:OntologyTerm:SwoProperty {iri:"http://www.ebi.ac.uk/swo/SWO_0000741"}) SET n.label = "is encoded in";
MERGE (n:OntologyTerm:SwoProperty {iri:"http://www.ebi.ac.uk/swo/SWO_0000740"}) SET n.label = "implements";
MERGE (n:OntologyTerm:SwoProperty {iri:"http://www.ebi.ac.uk/swo/SWO_0000086"}) SET n.label = "has specified data input";
MERGE (n:OntologyTerm:SwoProperty {iri:"http://www.ebi.ac.uk/swo/SWO_0000087"}) SET n.label = "has specified data output";
MERGE (n:OntologyTerm:SwoProperty {iri:"http://www.ebi.ac.uk/swo/SWO_0000150"}) SET n.label = "uses platform";


// ----- Media-type terms (file-format layer; SME ruling 2026-08-05) ----------
//   Consumer: the code-snapshot loader's HAS_MEDIA_TYPE edge (arch_has_media_type)
//   — non-.py files in the all-files tree snapshot get a FORMAT binding the way
//   .py gets a LANGUAGE binding (IS_ENCODED_IN). Two provenance tiers, split by
//   `registered`:
//     * registered:true  — IANA-registered media types; the iri IS the IANA
//       registration page (the DCAT convention for dcat:mediaType values).
//       Each was verified against iana.org at seeding (2026-08-05); the two
//       recent ones: application/toml registered 2024-10-21,
//       application/vnd.mermaid registered 2023-09-18.
//     * registered:false — CONVENTIONAL types with no IANA registration
//       (TypeScript, PowerShell, Cypher, Jupyter). Local IRIs — an IANA-shaped
//       iri for an unregistered type would fabricate a registration.
//   Extensions with NEITHER a language nor a media type ('', .example, .lock,
//   .conf) stay unbound and are reported by the CLI, never guessed.
//   BINARY ASSETS (images .png/.svg/.webp/..., fonts .ttf/.woff/...) are NOT
//   loaded at all (SME ruling 2026-08-06, fonts added on same-day revisit) —
//   their terms (image/*, font/ttf) were seeded 2026-08-05 and removed the
//   next day; no asset-class term belongs here while that ruling stands
//   (ASSET_EXTENSIONS_SKIPPED in drydocs/loaders/code_snapshot.py).
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/text/markdown"})   SET n.label = "Markdown",   n.media_type = "text/markdown",   n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/text/html"})       SET n.label = "HTML",       n.media_type = "text/html",       n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/text/css"})        SET n.label = "CSS",        n.media_type = "text/css",        n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/text/javascript"}) SET n.label = "JavaScript", n.media_type = "text/javascript", n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/text/csv"})        SET n.label = "CSV",        n.media_type = "text/csv",        n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/text/plain"})      SET n.label = "Plain text", n.media_type = "text/plain",      n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/application/json"}) SET n.label = "JSON",      n.media_type = "application/json", n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/application/yaml"}) SET n.label = "YAML",      n.media_type = "application/yaml", n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/application/toml"}) SET n.label = "TOML",      n.media_type = "application/toml", n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/application/xml"})  SET n.label = "XML",       n.media_type = "application/xml",  n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/application/pdf"})  SET n.label = "PDF",       n.media_type = "application/pdf",  n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/application/sql"})  SET n.label = "SQL file",  n.media_type = "application/sql",  n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/application/vnd.mermaid"}) SET n.label = "Mermaid", n.media_type = "application/vnd.mermaid", n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://www.iana.org/assignments/media-types/application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}) SET n.label = "Excel workbook (OOXML)", n.media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", n.registered = true;
MERGE (n:OntologyTerm:MediaType {iri:"https://drydocs.local/format#typescript"})       SET n.label = "TypeScript",       n.media_type = "application/typescript",   n.registered = false;
MERGE (n:OntologyTerm:MediaType {iri:"https://drydocs.local/format#powershell"})       SET n.label = "PowerShell",       n.media_type = "application/x-powershell", n.registered = false;
MERGE (n:OntologyTerm:MediaType {iri:"https://drydocs.local/format#cypher"})           SET n.label = "Cypher",           n.media_type = "application/x-cypher-query", n.registered = false;
MERGE (n:OntologyTerm:MediaType {iri:"https://drydocs.local/format#jupyter-notebook"}) SET n.label = "Jupyter notebook", n.media_type = "application/x-ipynb+json", n.registered = false;


// ----- OpenLineage label vocabulary -----------------------------------------
//   OL doesn't publish OWL; we record canonical names for cross-reference.
MERGE (n:OntologyTerm:OlClass {iri:"https://openlineage.io/spec/Run"})     SET n.label = "OL Run";
MERGE (n:OntologyTerm:OlClass {iri:"https://openlineage.io/spec/Job"})     SET n.label = "OL Job";
MERGE (n:OntologyTerm:OlClass {iri:"https://openlineage.io/spec/Dataset"}) SET n.label = "OL Dataset";


// ----- SchedulerKind — DEPRECATED 2026-07-21 (C12 platforms-taxonomy gate) --
//   RETIRED into the software-registry model: an orchestrator is a
//   :SoftwareProduct {role:"orchestrator"} row (config/taxonomy/
//   software-registry.yaml) reached via USES_SOFTWARE {source:"batch-port"}
//   (vocab reg_uses_software) — role over class, no kind/capability node layer.
//   Seeds kept commented for audit (the company 06-29 precedent, per the K4
//   Membership pattern). The scheduler_kind constraint and the supplement's
//   double-check MERGE were removed 2026-07-23: pre-C13 graphs are wiped and
//   rebuilt from bootstrap, so no graph creates or holds these nodes anymore.
// MERGE (k:SchedulerKind {name:"ControlM"}) SET k.kind_label = "BMC Control-M",  k.phase_supported = 1;
// MERGE (k:SchedulerKind {name:"Autosys"})  SET k.kind_label = "CA Autosys",     k.phase_supported = 2;
// MERGE (k:SchedulerKind {name:"Airflow"})  SET k.kind_label = "Apache Airflow", k.phase_supported = 2;


// ----- Corporate hierarchy: Company + BusinessSegments ----------------------
MERGE (jpmc:Company {name:"JPMC"})
  SET jpmc.legal_name = "JPMorgan Chase & Co.",
      jpmc.source     = "annual report";

// Post-Q2-2024 segments (current).
MERGE (s:BusinessSegment {code:"CCB"})  SET s.name = "Consumer & Community Banking";
MERGE (s:BusinessSegment {code:"CIB"})  SET s.name = "Commercial & Investment Bank";
MERGE (s:BusinessSegment {code:"AWM"})  SET s.name = "Asset & Wealth Management";
MERGE (s:BusinessSegment {code:"Corp"}) SET s.name = "Corporate";

// Pre-Q2-2024 segment retired (CB merged into CIB).
MERGE (s:BusinessSegment {code:"CB"})
  SET s.name    = "Commercial Banking (pre-Q2-2024, merged into CIB)",
      s.retired = true;

// Effective-dated edges Company -> BusinessSegment (post-reorg, open-ended).
MATCH (jpmc:Company {name:"JPMC"})
MATCH (s:BusinessSegment) WHERE s.code IN ['CCB','CIB','AWM','Corp']
MERGE (jpmc)-[r:HAS_BUSINESS_SEGMENT]->(s)
  ON CREATE SET r.effective_from = date('2024-04-01'),
                r.effective_to   = null,
                r.source         = "annual report";

// Pre-reorg snapshot (historical edge).
MATCH (jpmc:Company {name:"JPMC"})
MATCH (s:BusinessSegment) WHERE s.code IN ['CCB','CIB','CB','AWM']
MERGE (jpmc)-[r:HAS_BUSINESS_SEGMENT_HISTORICAL]->(s)
  ON CREATE SET r.effective_from = date('2010-01-01'),
                r.effective_to   = date('2024-03-31'),
                r.source         = "annual report (pre-Q2-2024)";


// ----- DQV catalog: Dimensions + Metrics (TDQ baseline, v2 §11.6) -----------
// C23 RULING (SME, 2026-08-03): DEFERRED, kept as a REFERENCE catalog. These
// rows deliberately have no upstream today — the designed measurement leg
// (:QualityMeasurement -IS_MEASUREMENT_OF->, COMPUTED_ON, HAS_QUALITY;
// LoadPlanV2 §4.4) has no writer because no measurement feed exists yet.
// REVIVAL TRIGGER: the first measurement feed — expected to be the
// temporal-runtime freshness observations (cm_avg_run / freshness_sla), whose
// vocabulary notes already reference dqv:QualityMeasurement. When that feed
// lands, groom the writer items and flip quality_is_measurement_of /
// quality_computed_on / quality_has_quality from planned. All four DQV edges are
// registered in relationship_vocabulary.yaml (c23_* ids); IN_DIMENSION below
// is active — it is written right here at bootstrap.
MERGE (d:Dimension {name:"Completeness"}) SET d.description = "Whether all required data is present.";
MERGE (d:Dimension {name:"Accuracy"})     SET d.description = "Whether values match a trusted source.";
MERGE (d:Dimension {name:"Consistency"})  SET d.description = "Whether values are consistent across structures and over time.";
MERGE (d:Dimension {name:"Timeliness"})   SET d.description = "Whether data arrives within the agreed SLA.";
MERGE (d:Dimension {name:"Integrity"})    SET d.description = "Whether structural / referential rules hold.";

// Metrics keyed by name; each links into one dimension.
MERGE (m:Metric {name:"rowcount_match"})        SET m.description = "Data file row count matches control file claim.";
MERGE (m:Metric {name:"null_rate"})             SET m.description = "Per-column null rate vs threshold.";
MERGE (m:Metric {name:"hash_match"})            SET m.description = "File SHA-256 matches control file hash.";
MERGE (m:Metric {name:"value_range"})           SET m.description = "Numeric values within configured min/max.";
MERGE (m:Metric {name:"schema_conformance"})    SET m.description = "Columns and types match the expected schema.";
MERGE (m:Metric {name:"referential_integrity"}) SET m.description = "Foreign keys resolve to existing rows.";
MERGE (m:Metric {name:"freshness_sla"})         SET m.description = "Arrival timestamp meets the dataset SLA.";
MERGE (m:Metric {name:"arrival_latency"})       SET m.description = "Time between expected and actual arrival.";
MERGE (m:Metric {name:"pkey_uniqueness"})       SET m.description = "Primary keys are unique.";
MERGE (m:Metric {name:"fkey_validity"})         SET m.description = "Foreign keys present in parent dataset.";

// Wire metrics to dimensions.
MATCH (m:Metric {name:"rowcount_match"}),        (d:Dimension {name:"Completeness"}) MERGE (m)-[:IN_DIMENSION]->(d);
MATCH (m:Metric {name:"null_rate"}),             (d:Dimension {name:"Completeness"}) MERGE (m)-[:IN_DIMENSION]->(d);
MATCH (m:Metric {name:"hash_match"}),            (d:Dimension {name:"Accuracy"})     MERGE (m)-[:IN_DIMENSION]->(d);
MATCH (m:Metric {name:"value_range"}),           (d:Dimension {name:"Accuracy"})     MERGE (m)-[:IN_DIMENSION]->(d);
MATCH (m:Metric {name:"schema_conformance"}),    (d:Dimension {name:"Consistency"})  MERGE (m)-[:IN_DIMENSION]->(d);
MATCH (m:Metric {name:"referential_integrity"}), (d:Dimension {name:"Consistency"})  MERGE (m)-[:IN_DIMENSION]->(d);
MATCH (m:Metric {name:"freshness_sla"}),         (d:Dimension {name:"Timeliness"})   MERGE (m)-[:IN_DIMENSION]->(d);
MATCH (m:Metric {name:"arrival_latency"}),       (d:Dimension {name:"Timeliness"})   MERGE (m)-[:IN_DIMENSION]->(d);
MATCH (m:Metric {name:"pkey_uniqueness"}),       (d:Dimension {name:"Integrity"})    MERGE (m)-[:IN_DIMENSION]->(d);
MATCH (m:Metric {name:"fkey_validity"}),         (d:Dimension {name:"Integrity"})    MERGE (m)-[:IN_DIMENSION]->(d);


// ----- Loader Agent (PROV) --------------------------------------------------
MERGE (a:Agent:SoftwareAgent {id:"drydocs.loader.v1"})
  SET a.label = "DryDocs Loader v1",
      a.kind  = "loader";