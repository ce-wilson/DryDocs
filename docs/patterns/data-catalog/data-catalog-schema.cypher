// =============================================================================
// data-catalog-schema.cypher
//
// Enterprise Data Catalog — Neo4j schema (constraints + meta-graph)
// Standard: LinkedIn DataHub entity model + DCAT v2 + OpenLineage
//
// Usage:
//   1. Run Section 0 (constraints) first; wait for ONLINE before loading.
//   2. Run Section 1 (meta-graph) to create schema documentation nodes.
//   3. Optionally run Section 2 (bridge nodes) to wire to process graph.
//
// Label prefix "Catalog" avoids collision with your existing graph labels.
// Replace <OrgCatalog> in comments with your organization's classifier namespace.
// =============================================================================


// -----------------------------------------------------------------------------
// SECTION 0 — Constraints
// Run first; verify ONLINE with:
//   SHOW CONSTRAINTS YIELD name, state WHERE state <> 'ONLINE' RETURN name, state;
// -----------------------------------------------------------------------------

CREATE CONSTRAINT catalog_dataset_urn IF NOT EXISTS
  FOR (n:CatalogDataset) REQUIRE n.dataset_urn IS UNIQUE;

CREATE CONSTRAINT catalog_distribution_urn IF NOT EXISTS
  FOR (n:CatalogDistribution) REQUIRE n.distribution_urn IS UNIQUE;

CREATE CONSTRAINT catalog_data_product_id IF NOT EXISTS
  FOR (n:CatalogDataProduct) REQUIRE n.data_product_id IS UNIQUE;

CREATE CONSTRAINT catalog_data_domain_id IF NOT EXISTS
  FOR (n:CatalogDataDomain) REQUIRE n.domain_id IS UNIQUE;

CREATE CONSTRAINT catalog_element_id IF NOT EXISTS
  FOR (n:CatalogElement) REQUIRE n.element_id IS UNIQUE;

CREATE CONSTRAINT catalog_field_id IF NOT EXISTS
  FOR (n:CatalogField) REQUIRE n.field_id IS UNIQUE;

CREATE CONSTRAINT catalog_schema_id IF NOT EXISTS
  FOR (n:CatalogSchema) REQUIRE n.schema_id IS UNIQUE;

CREATE CONSTRAINT catalog_tag_name IF NOT EXISTS
  FOR (n:CatalogTag) REQUIRE n.name IS UNIQUE;

CREATE CONSTRAINT catalog_classifier_name IF NOT EXISTS
  FOR (n:CatalogClassifier) REQUIRE n.classifier_name IS UNIQUE;

CREATE CONSTRAINT catalog_policy_id IF NOT EXISTS
  FOR (n:CatalogLifecyclePolicy) REQUIRE n.policy_id IS UNIQUE;

CREATE CONSTRAINT catalog_contract_id IF NOT EXISTS
  FOR (n:CatalogDataContract) REQUIRE n.contract_id IS UNIQUE;

CREATE CONSTRAINT catalog_quality_rule_id IF NOT EXISTS
  FOR (n:CatalogDataQualityRule) REQUIRE n.rule_id IS UNIQUE;

CREATE CONSTRAINT catalog_worker_id IF NOT EXISTS
  FOR (n:CatalogWorker) REQUIRE n.worker_id IS UNIQUE;

CREATE CONSTRAINT catalog_worker_group_id IF NOT EXISTS
  FOR (n:CatalogWorkerGroup) REQUIRE n.group_id IS UNIQUE;

CREATE CONSTRAINT catalog_business_term_id IF NOT EXISTS
  FOR (n:CatalogBusinessTerm) REQUIRE n.term_id IS UNIQUE;

CREATE CONSTRAINT catalog_valid_value_id IF NOT EXISTS
  FOR (n:CatalogValidValue) REQUIRE n.value_id IS UNIQUE;

CREATE CONSTRAINT catalog_encoding_id IF NOT EXISTS
  FOR (n:CatalogEncodingInstance) REQUIRE n.encoding_id IS UNIQUE;

// NOTE: :Application is shared with the process graph.
// Use the existing Application constraint; do NOT create a separate one here.
// CREATE CONSTRAINT application_id IF NOT EXISTS FOR (n:Application) REQUIRE n.app_id IS UNIQUE;

// Performance indexes
CREATE INDEX catalog_dataset_platform_idx IF NOT EXISTS
  FOR (n:CatalogDistribution) ON (n.platform_type);

CREATE INDEX catalog_element_scope_idx IF NOT EXISTS
  FOR (n:CatalogElement) ON (n.scope);

CREATE INDEX catalog_classifier_namespace_idx IF NOT EXISTS
  FOR (n:CatalogClassifier) ON (n.namespace);


// -----------------------------------------------------------------------------
// SECTION 1 — Schema Meta-Graph
// SchemaMeta nodes document the catalog ontology in the graph itself.
// Query with: MATCH (n:SchemaMeta:CatalogNodeType) RETURN n ORDER BY n.domain
// -----------------------------------------------------------------------------

// --- Node type documentation nodes ---

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogDataset'})
  SET n.domain = 'BusinessDataCatalog',
      n.description = 'Logical dataset; primary catalog object',
      n.key_property = 'dataset_urn',
      n.datahub_entity = 'dataset';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogDistribution'})
  SET n.domain = 'BusinessDataCatalog',
      n.description = 'Physical instantiation of a dataset on a platform',
      n.key_property = 'distribution_urn',
      n.datahub_entity = 'dataDistribution';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogDataProduct'})
  SET n.domain = 'BusinessDataCatalog',
      n.description = 'Curated product built from datasets',
      n.key_property = 'data_product_id',
      n.datahub_entity = 'dataProduct';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogDataDomain'})
  SET n.domain = 'BusinessDataCatalog',
      n.description = 'Top-level data subject area',
      n.key_property = 'domain_id',
      n.datahub_entity = 'domain';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogElement'})
  SET n.domain = 'BusinessDataCatalog',
      n.description = 'Logical data element / field-level concept',
      n.key_property = 'element_id',
      n.datahub_entity = 'schemaField';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogField'})
  SET n.domain = 'BusinessDataCatalog',
      n.description = 'Physical field implementing an Element in a Schema',
      n.key_property = 'field_id',
      n.datahub_entity = 'schemaField';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogSchema'})
  SET n.domain = 'BusinessDataCatalog',
      n.description = 'Physical schema grouping Fields',
      n.key_property = 'schema_id',
      n.datahub_entity = 'schema';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogTag'})
  SET n.domain = 'BusinessDataCatalog',
      n.description = 'Free-form or system-controlled tag on any catalog object',
      n.key_property = 'name',
      n.datahub_entity = 'tag';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogClassifier'})
  SET n.domain = 'BusinessDataCatalog',
      n.description = 'Org-namespace controlled-vocabulary attribute (e.g. <OrgCatalog>:)',
      n.key_property = 'classifier_name',
      n.datahub_entity = 'glossaryTerm';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogLifecyclePolicy'})
  SET n.domain = 'BusinessDataCatalog',
      n.description = 'Data lifecycle / retention policy for a Distribution',
      n.key_property = 'policy_id',
      n.datahub_entity = 'dataLifecyclePolicy';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogWorker'})
  SET n.domain = 'Workforce',
      n.description = 'Individual employee; maps to process graph :Employee',
      n.key_property = 'worker_id',
      n.datahub_entity = 'corpUser';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogWorkerGroup'})
  SET n.domain = 'Workforce',
      n.description = 'Team or group; maps to process graph :DevTeam',
      n.key_property = 'group_id',
      n.datahub_entity = 'corpGroup';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogBusinessTerm'})
  SET n.domain = 'BusinessGlossary',
      n.description = 'Canonical business definition',
      n.key_property = 'term_id',
      n.datahub_entity = 'glossaryTerm';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogValidValue'})
  SET n.domain = 'BusinessGlossary',
      n.description = 'Allowed enumeration value for a BusinessTerm',
      n.key_property = 'value_id',
      n.datahub_entity = 'glossaryNode';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogEncodingInstance'})
  SET n.domain = 'BusinessGlossary',
      n.description = 'Code encoding for a BusinessTerm valid value set',
      n.key_property = 'encoding_id',
      n.datahub_entity = 'glossaryNode';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogDataContract'})
  SET n.domain = 'DataQuality',
      n.description = 'Formal data quality contract',
      n.key_property = 'contract_id',
      n.datahub_entity = 'dataContract';

MERGE (n:SchemaMeta:CatalogNodeType {name: 'CatalogDataQualityRule'})
  SET n.domain = 'DataQuality',
      n.description = 'Specific quality rule within a contract',
      n.key_property = 'rule_id',
      n.datahub_entity = 'assertion';

// Shared bridge node
MERGE (n:SchemaMeta:CatalogNodeType {name: 'Application'})
  SET n.domain = 'Application',
      n.description = 'Business application — SHARED with process graph; key = organizational app ID',
      n.key_property = 'app_id',
      n.bridge_to_process_graph = true,
      n.datahub_entity = 'corpGroup';

// --- Relationship type documentation nodes ---

MERGE (r:SchemaMeta:CatalogRelType {name: 'OWNED_BY'})
  SET r.description = 'Ownership: Dataset/Domain/Distribution/Product → Worker/WorkerGroup';

MERGE (r:SchemaMeta:CatalogRelType {name: 'DATASET_OWNED_BY'})
  SET r.description = 'DataDistribution → Application; dataset ownership at platform level';

MERGE (r:SchemaMeta:CatalogRelType {name: 'DATASET_PUBLISHED_BY'})
  SET r.description = 'DataDistribution → Application; publishing responsibility';

MERGE (r:SchemaMeta:CatalogRelType {name: 'PUBLISHED_BY'})
  SET r.description = 'DataDistribution → Application; distribution publishing';

MERGE (r:SchemaMeta:CatalogRelType {name: 'HAS_MEMBER'})
  SET r.description = 'WorkerGroup → Worker; group membership';

MERGE (r:SchemaMeta:CatalogRelType {name: 'BELONGS_TO'})
  SET r.description = 'Dataset → DataDomain; subject-area assignment';

MERGE (r:SchemaMeta:CatalogRelType {name: 'IS_PART_OF'})
  SET r.description = 'Dataset → DataProduct; product contribution';

MERGE (r:SchemaMeta:CatalogRelType {name: 'IMPLEMENTED_ON'})
  SET r.description = 'Dataset → DataDistribution; logical→physical platform mapping';

MERGE (r:SchemaMeta:CatalogRelType {name: 'HAS'})
  SET r.description = 'Schema → Field; Dataset → Element; containment';

MERGE (r:SchemaMeta:CatalogRelType {name: 'IS_IMPLEMENTED_AS'})
  SET r.description = 'Element → Field; logical→physical field mapping';

MERGE (r:SchemaMeta:CatalogRelType {name: 'IS_TAGGED_WITH'})
  SET r.description = 'Any catalog object → Tag; metadata tagging';

MERGE (r:SchemaMeta:CatalogRelType {name: 'IS_ASSOCIATED_WITH'})
  SET r.description = 'Dataset → Classifier | Distribution → LifecyclePolicy; association';

MERGE (r:SchemaMeta:CatalogRelType {name: 'CLASSIFIED_BY'})
  SET r.description = 'Dataset/Element → Classifier; classification';

MERGE (r:SchemaMeta:CatalogRelType {name: 'HAS_LIFECYCLE_POLICY'})
  SET r.description = 'DataDistribution → LifecyclePolicy; policy attachment';

MERGE (r:SchemaMeta:CatalogRelType {name: 'POLICY_CONFINES_TO'})
  SET r.description = 'LifecyclePolicy → Application; policy scope binding';

MERGE (r:SchemaMeta:CatalogRelType {name: 'HAS_QUALITY_RULE'})
  SET r.description = 'DataContract → DataQualityRule; rule membership';

MERGE (r:SchemaMeta:CatalogRelType {name: 'IS_REPRESENTED_AS'})
  SET r.description = 'Element → BusinessTerm; glossary linkage';

MERGE (r:SchemaMeta:CatalogRelType {name: 'HAS_ALLOWED_VALUES'})
  SET r.description = 'ValidValue → BusinessTerm; enumeration linkage';

MERGE (r:SchemaMeta:CatalogRelType {name: 'DEFINED_FOR'})
  SET r.description = 'BusinessTerm/ValidValue → EncodingInstance; code encoding linkage';


// -----------------------------------------------------------------------------
// SECTION 2 — Process Graph Bridge
// Adds meta-nodes for the process-plane nodes that bridge to the catalog.
// These are the DryDocs / Control-M nodes that join the two planes.
// -----------------------------------------------------------------------------

MERGE (n:SchemaMeta:ProcessNodeType {name: 'AppDataFlow'})
  SET n.domain = 'ProcessOrchestration',
      n.description = '3rd Application child; maps to DataHub dataFlow entity',
      n.key_property = 'dataflowUrn',
      n.datahub_entity = 'dataFlow',
      n.openlineage_entity = 'Job';

MERGE (n:SchemaMeta:ProcessNodeType {name: 'ControlMJob'})
  SET n.domain = 'ProcessOrchestration',
      n.description = 'Individual orchestration task; maps to DataHub dataJob / OpenLineage Job',
      n.key_property = 'jobId',
      n.datahub_entity = 'dataJob',
      n.openlineage_entity = 'Job';

MERGE (n:SchemaMeta:ProcessNodeType {name: 'DataAsset'})
  SET n.domain = 'ProcessOrchestration',
      n.description = 'Named data object seen by the orchestration layer; bridges to CatalogDataset',
      n.key_property = 'assetId',
      n.datahub_entity = 'dataset',
      n.openlineage_entity = 'Dataset';

MERGE (r:SchemaMeta:ProcessRelType {name: 'USED'})
  SET r.description = 'ControlMJob consumes a DataAsset (input); PROV-O prov:used';

MERGE (r:SchemaMeta:ProcessRelType {name: 'GENERATED'})
  SET r.description = 'ControlMJob produces a DataAsset (output); PROV-O prov:wasGeneratedBy';

MERGE (r:SchemaMeta:ProcessRelType {name: 'ORCHESTRATES'})
  SET r.description = 'AppDataFlow → ControlMJob; pipeline→task containment';

MERGE (r:SchemaMeta:ProcessRelType {name: 'REPRESENTS_CATALOG_DATASET'})
  SET r.description = 'DataAsset → CatalogDataset; optional join to catalog when URN is known';
