// =============================================================================
// schema_graph.cypher  —  DryDocs schema meta-graph  (GENERATED — DO NOT EDIT)
//
// GENERATED deterministically from drydocs_core/ontology/relationship_vocabulary.yaml
// (the confirmed source of truth for edge meaning) by:
//     poetry run python scripts/render_schema_graph.py
// Drift guard: tests/unit/test_schema_graph.py re-renders the vocabulary
// in-memory and fails if this committed file does not match. To change the
// schema picture, edit the vocabulary (via the HITL gate where meaning
// changes), then regenerate. No timestamps — the render is deterministic.
//
// One exemplar node per participating node label (real label + :SchemaMeta
// marker) and one exemplar relationship per vocabulary entry (real
// relationship type), so the full declared schema renders in Neo4j Browser:
//     CALL db.schema.visualization();
// or browse the meta-graph directly:
//     MATCH p = (:SchemaMeta)-[]->(:SchemaMeta) RETURN p;
// Applied MANUALLY only — never part of `drydocs bootstrap`.
// To remove the meta-graph:  MATCH (n:SchemaMeta) DETACH DELETE n;
//
// Inclusion rule (drydocs_core/ontology/schema_graph.py):
//   * entries with status 'active' or 'planned' render (status is carried on
//     each edge as r.status); 'deprecated' and 'removed' entries are excluded.
//   * pipe-union endpoints ("A | B") render one edge per alternative.
//   * wildcard from_node "*" renders representative edges from fixed
//     exemplars (ControlMJob, BusinessApplication, CatalogLOB) — in the real
//     graph BaseLoader writes that edge for every node label.
//   * nodes: only labels referenced by a rendered relationship; class /
//     dual_class / prov_type come from node_classifications (labels without
//     a classification entry render name-only).
//   * entry notes/prose stay in the vocabulary — this file carries structure.
//
// Node properties:  name, class (CURIE per namespaces.py), dual_class, prov_type
// Edge properties:  vocab_id, role, prov_maps_to, sosa_maps_to, domain, status
// =============================================================================

// ── Node labels ─────────────────────────────────────────────────────────────

MERGE (n:SchemaMeta:ControlMJob {name: 'ControlMJob'})
  SET n.class = 'dd:ControlMJob', n.prov_type = 'Activity';
MERGE (n:SchemaMeta:ControlMFolder {name: 'ControlMFolder'})
  SET n.class = 'dd:ControlMFolder', n.prov_type = 'Collection';
MERGE (n:SchemaMeta:ControlMApplication {name: 'ControlMApplication'})
  SET n.class = 'dd:ControlMApplication', n.prov_type = 'Collection';
MERGE (n:SchemaMeta:ControlMServer {name: 'ControlMServer'})
  SET n.class = 'dd:ControlMServer', n.prov_type = 'n/a';
MERGE (n:SchemaMeta:Condition {name: 'Condition'})
  SET n.class = 'dd:Condition', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:JobRun {name: 'JobRun'})
  SET n.class = 'dd:JobRun', n.prov_type = 'Activity';
MERGE (n:SchemaMeta:ControlMJobRun {name: 'ControlMJobRun'})
  SET n.class = 'dd:ControlMJobRun', n.prov_type = 'Activity';
MERGE (n:SchemaMeta:Deployment {name: 'Deployment'})
  SET n.class = 'dd:Deployment', n.prov_type = 'Activity';
MERGE (n:SchemaMeta:Developer {name: 'Developer'})
  SET n.class = 'prov:Person', n.prov_type = 'Agent';
MERGE (n:SchemaMeta:AppUser {name: 'AppUser'})
  SET n.class = 'prov:SoftwareAgent', n.prov_type = 'Agent';
MERGE (n:SchemaMeta:Script {name: 'Script'})
  SET n.class = 'dd:Script', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:ETLProcess {name: 'ETLProcess'})
  SET n.class = 'dd:ETLProcess', n.prov_type = 'Activity';
MERGE (n:SchemaMeta:ExecutionHost {name: 'ExecutionHost'})
  SET n.class = 'prov:SoftwareAgent', n.prov_type = 'Agent';
MERGE (n:SchemaMeta:ControlMHostGroup {name: 'ControlMHostGroup'})
  SET n.class = 'dd:ControlMHostGroup', n.prov_type = 'Collection';
MERGE (n:SchemaMeta:DataAsset {name: 'DataAsset'})
  SET n.class = 'dcat:Dataset', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:BusinessApplication {name: 'BusinessApplication'})
  SET n.class = 'prov:Entity', n.dual_class = 'dprod:DataProduct', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:Employee {name: 'Employee'})
  SET n.class = 'prov:Agent', n.prov_type = 'Agent';
MERGE (n:SchemaMeta:Membership {name: 'Membership'})
  SET n.class = 'org:Membership', n.prov_type = 'n/a';
MERGE (n:SchemaMeta:Port {name: 'Port'})
  SET n.class = 'dprod:Port', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:Attribution {name: 'Attribution'})
  SET n.class = 'prov:Attribution', n.prov_type = 'n/a';
MERGE (n:SchemaMeta:TOMRole {name: 'TOMRole'})
  SET n.class = 'skos:Concept', n.prov_type = 'n/a';
MERGE (n:SchemaMeta:ProductRole {name: 'ProductRole'})
  SET n.class = 'skos:Concept', n.prov_type = 'n/a';
MERGE (n:SchemaMeta:CatalogLOB {name: 'CatalogLOB'})
  SET n.class = 'org:OrganizationalUnit', n.prov_type = 'Agent';
MERGE (n:SchemaMeta:BusinessSegment {name: 'BusinessSegment'})
  SET n.class = 'org:FormalOrganization', n.prov_type = 'Agent';
MERGE (n:SchemaMeta:DevTeam {name: 'DevTeam'})
  SET n.class = 'org:OrganizationalUnit', n.prov_type = 'Agent';
MERGE (n:SchemaMeta:ProductLine {name: 'ProductLine'})
  SET n.class = 'dd:ProductLine', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:Product {name: 'Product'})
  SET n.class = 'dd:Product', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:JiraBoard {name: 'JiraBoard'})
  SET n.class = 'dd:JiraBoard', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:AreaProduct {name: 'AreaProduct'})
  SET n.class = 'dd:AreaProduct', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:Code {name: 'Code'})
  SET n.class = 'dd:Code', n.prov_type = 'Collection';
MERGE (n:SchemaMeta:Bitbucket {name: 'Bitbucket'})
  SET n.class = 'dd:CodeRepository', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:PipelineService {name: 'PipelineService'})
  SET n.class = 'dd:PipelineService', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:Batch {name: 'Batch'})
  SET n.class = 'dd:Batch', n.prov_type = 'Collection';
MERGE (n:SchemaMeta:File {name: 'File'})
  SET n.class = 'dd:File', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:Vendor {name: 'Vendor'})
  SET n.class = 'org:Organization', n.prov_type = 'Agent';
MERGE (n:SchemaMeta:SoftwareProduct {name: 'SoftwareProduct'})
  SET n.class = 'dd:SoftwareProduct', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:Document {name: 'Document'})
  SET n.class = 'prov:Entity', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:Chunk {name: 'Chunk'})
  SET n.class = 'prov:Entity', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:DocSource {name: 'DocSource'})
  SET n.class = 'prov:Entity', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:DesignDoc {name: 'DesignDoc'})
  SET n.class = 'dd:DesignDoc', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:DocSection {name: 'DocSection'})
  SET n.class = 'dd:DocSection', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:Requirement {name: 'Requirement'})
  SET n.class = 'dd:Requirement', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:Component {name: 'Component'})
  SET n.class = 'dd:Component', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:TestCase {name: 'TestCase'})
  SET n.class = 'dd:TestCase', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:FeedbackNote {name: 'FeedbackNote'})
  SET n.class = 'dd:FeedbackNote', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:Observation {name: 'Observation'})
  SET n.class = 'sosa:Observation', n.prov_type = 'Activity';
MERGE (n:SchemaMeta:Sensor {name: 'Sensor'})
  SET n.class = 'sosa:Sensor', n.prov_type = 'Agent';
MERGE (n:SchemaMeta:Result {name: 'Result'})
  SET n.class = 'sosa:Result', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:ObservableProperty {name: 'ObservableProperty'})
  SET n.class = 'sosa:ObservableProperty', n.prov_type = 'Entity';
// (no node_classifications entry)
MERGE (n:SchemaMeta:SchedulerKind {name: 'SchedulerKind'});
// (no node_classifications entry)
MERGE (n:SchemaMeta:OntologyTerm {name: 'OntologyTerm'});

// ── Relationships (one exemplar edge per vocabulary entry) ──────────────────

// ── domain: controlm ────────────────────────────────────────────────────────

MATCH (a:SchemaMeta {name: 'ControlMFolder'}), (b:SchemaMeta {name: 'ControlMServer'})
MERGE (a)-[r:SCHEDULED_ON]->(b)
  SET r.vocab_id = 'm3_scheduled_on', r.prov_maps_to = null, r.domain = 'controlm', r.status = 'active';

MATCH (a:SchemaMeta {name: 'ControlMFolder'}), (b:SchemaMeta {name: 'ControlMJob'})
MERGE (a)-[r:CONTAINS_JOB]->(b)
  SET r.vocab_id = 'm3_contains_job', r.prov_maps_to = 'prov:hadMember', r.domain = 'controlm', r.status = 'active';

MATCH (a:SchemaMeta {name: 'ControlMApplication'}), (b:SchemaMeta {name: 'ControlMFolder'})
MERGE (a)-[r:CONTAINS_FOLDER]->(b)
  SET r.vocab_id = 'm3_contains_folder', r.prov_maps_to = 'prov:hadMember', r.domain = 'controlm', r.status = 'active';

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'Condition'})
MERGE (a)-[r:REQUIRES_IN_CONDITION]->(b)
  SET r.vocab_id = 'm3_requires_in_condition', r.prov_maps_to = 'prov:used', r.domain = 'controlm', r.status = 'active';

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'Condition'})
MERGE (a)-[r:EMITS_OUT_CONDITION]->(b)
  SET r.vocab_id = 'm3_emits_out_condition', r.prov_maps_to = 'prov:generated', r.domain = 'controlm', r.status = 'active';

MATCH (a:SchemaMeta {name: 'ControlMJob'})
MERGE (a)-[r:WAS_INFORMED_BY]->(a)
  SET r.vocab_id = 'm3_was_informed_by', r.prov_maps_to = 'prov:wasInformedBy', r.domain = 'controlm', r.status = 'active';

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'File'})
MERGE (a)-[r:USED]->(b)
  SET r.vocab_id = 'm3_depends_on_file', r.role = 'file_dependency', r.prov_maps_to = 'prov:used', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Deployment'}), (b:SchemaMeta {name: 'Developer'})
MERGE (a)-[r:DEPLOYED_BY]->(b)
  SET r.vocab_id = 'p2_deployed_by', r.prov_maps_to = 'prov:wasAssociatedWith', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Deployment'}), (b:SchemaMeta {name: 'ControlMServer'})
MERGE (a)-[r:DEPLOYED_TO]->(b)
  SET r.vocab_id = 'p2_deployed_to', r.prov_maps_to = null, r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Deployment'}), (b:SchemaMeta {name: 'ControlMFolder'})
MERGE (a)-[r:DEPLOYS_FOLDER]->(b)
  SET r.vocab_id = 'p2_deploys_folder', r.prov_maps_to = 'prov:used', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ControlMFolder'}), (b:SchemaMeta {name: 'Developer'})
MERGE (a)-[r:AUTHORED_BY]->(b)
  SET r.vocab_id = 'p2_authored_by', r.prov_maps_to = 'prov:wasAttributedTo', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ControlMJobRun'}), (b:SchemaMeta {name: 'ControlMJob'})
MERGE (a)-[r:INSTANCE_OF]->(b)
  SET r.vocab_id = 'p2_instance_of', r.prov_maps_to = 'prov:wasInfluencedBy', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ControlMJobRun'}), (b:SchemaMeta {name: 'AppUser'})
MERGE (a)-[r:EXECUTED_BY]->(b)
  SET r.vocab_id = 'm3_executed_by', r.prov_maps_to = 'prov:wasAssociatedWith', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'BusinessApplication'})
MERGE (a)-[r:WAS_ASSOCIATED_WITH]->(b)
  SET r.vocab_id = 'm3_seal_app_ref', r.role = 'seal_app_ref', r.prov_maps_to = 'prov:wasAssociatedWith', r.domain = 'controlm', r.status = 'active';

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'Script'})
MERGE (a)-[r:INVOKES]->(b)
  SET r.vocab_id = 'm3_invokes', r.prov_maps_to = 'prov:used', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Script'}), (b:SchemaMeta {name: 'ETLProcess'})
MERGE (a)-[r:TRIGGERS]->(b)
  SET r.vocab_id = 'm3_triggers', r.prov_maps_to = 'prov:wasStartedBy', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'ExecutionHost'})
MERGE (a)-[r:RUNS_ON]->(b)
  SET r.vocab_id = 'm3_runs_on_agent_host', r.role = 'agent_host', r.prov_maps_to = null, r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ETLProcess'}), (b:SchemaMeta {name: 'ExecutionHost'})
MERGE (a)-[r:RUNS_ON]->(b)
  SET r.vocab_id = 'm3_runs_on_etl_host', r.role = 'etl_host', r.prov_maps_to = null, r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'ControlMHostGroup'})
MERGE (a)-[r:RUNS_ON]->(b)
  SET r.vocab_id = 'm3_runs_on_host_group', r.role = 'host_group', r.prov_maps_to = null, r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ControlMHostGroup'}), (b:SchemaMeta {name: 'ExecutionHost'})
MERGE (a)-[r:CONTAINS_HOST]->(b)
  SET r.vocab_id = 'm3_host_group_contains_host', r.prov_maps_to = 'prov:hadMember', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ControlMHostGroup'}), (b:SchemaMeta {name: 'ControlMServer'})
MERGE (a)-[r:DEFINED_ON]->(b)
  SET r.vocab_id = 'm3_host_group_defined_on', r.prov_maps_to = null, r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ETLProcess'}), (b:SchemaMeta {name: 'DataAsset'})
MERGE (a)-[r:READS_FROM]->(b)
  SET r.vocab_id = 'm3_reads_from', r.prov_maps_to = 'prov:used', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'DataAsset'})
MERGE (a)-[r:READS_FROM]->(b)
  SET r.vocab_id = 'm3_reads_from', r.prov_maps_to = 'prov:used', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ETLProcess'}), (b:SchemaMeta {name: 'DataAsset'})
MERGE (a)-[r:WRITES_TO]->(b)
  SET r.vocab_id = 'm3_writes_to', r.prov_maps_to = 'prov:generated', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'DataAsset'})
MERGE (a)-[r:WRITES_TO]->(b)
  SET r.vocab_id = 'm3_writes_to', r.prov_maps_to = 'prov:generated', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'AppUser'}), (b:SchemaMeta {name: 'ExecutionHost'})
MERGE (a)-[r:DELEGATES_TO]->(b)
  SET r.vocab_id = 'm3_delegates_to', r.prov_maps_to = 'prov:actedOnBehalfOf', r.domain = 'controlm', r.status = 'planned';

// ── domain: seal ────────────────────────────────────────────────────────────

MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'Port'})
MERGE (a)-[r:HAS_PORT]->(b)
  SET r.vocab_id = 'seal_has_port', r.prov_maps_to = null, r.domain = 'seal', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Port'}), (b:SchemaMeta {name: 'SchedulerKind'})
MERGE (a)-[r:REQUIRES_SCHEDULER]->(b)
  SET r.vocab_id = 'seal_requires_scheduler', r.prov_maps_to = null, r.domain = 'seal', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'Document'})
MERGE (a)-[r:HAD_PRIMARY_SOURCE]->(b)
  SET r.vocab_id = 'seal_had_primary_source', r.prov_maps_to = 'prov:hadPrimarySource', r.domain = 'seal', r.status = 'active';

MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'Employee'})
MERGE (a)-[r:WAS_ATTRIBUTED_TO]->(b)
  SET r.vocab_id = 'seal_app_attributed_to_employee', r.role = 'tom_role_holder', r.prov_maps_to = 'prov:wasAttributedTo', r.domain = 'seal', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'Attribution'})
MERGE (a)-[r:QUALIFIED_ATTRIBUTION]->(b)
  SET r.vocab_id = 'seal_qualified_attribution', r.prov_maps_to = 'prov:qualifiedAttribution', r.domain = 'seal', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Attribution'}), (b:SchemaMeta {name: 'Employee'})
MERGE (a)-[r:HAS_AGENT]->(b)
  SET r.vocab_id = 'seal_attribution_has_agent', r.prov_maps_to = 'prov:agent', r.domain = 'seal', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Attribution'}), (b:SchemaMeta {name: 'TOMRole'})
MERGE (a)-[r:HAD_ROLE]->(b)
  SET r.vocab_id = 'seal_attribution_had_role', r.prov_maps_to = 'prov:hadRole', r.domain = 'seal', r.status = 'active';

// ── domain: catalog ─────────────────────────────────────────────────────────

MATCH (a:SchemaMeta {name: 'CatalogLOB'}), (b:SchemaMeta {name: 'BusinessSegment'})
MERGE (a)-[r:RECONCILES_TO]->(b)
  SET r.vocab_id = 'catalog_reconciles_to', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'CatalogLOB'}), (b:SchemaMeta {name: 'ProductLine'})
MERGE (a)-[r:HAS_PRODUCT_LINE]->(b)
  SET r.vocab_id = 'catalog_has_product_line', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'ProductLine'}), (b:SchemaMeta {name: 'Product'})
MERGE (a)-[r:HAS_PRODUCT]->(b)
  SET r.vocab_id = 'catalog_has_product', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Product'}), (b:SchemaMeta {name: 'DevTeam'})
MERGE (a)-[r:HAS_DEV_TEAM]->(b)
  SET r.vocab_id = 'catalog_has_dev_team', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'DevTeam'}), (b:SchemaMeta {name: 'JiraBoard'})
MERGE (a)-[r:HAS_JIRA_BOARD]->(b)
  SET r.vocab_id = 'catalog_has_jira_board', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Product'}), (b:SchemaMeta {name: 'BusinessApplication'})
MERGE (a)-[r:HAS_APPLICATION]->(b)
  SET r.vocab_id = 'catalog_has_application', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Product'}), (b:SchemaMeta {name: 'AreaProduct'})
MERGE (a)-[r:HAS_AREA_PRODUCT]->(b)
  SET r.vocab_id = 'catalog_has_area_product', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'AreaProduct'}), (b:SchemaMeta {name: 'DevTeam'})
MERGE (a)-[r:HAS_DEV_TEAM]->(b)
  SET r.vocab_id = 'catalog_area_product_has_dev_team', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Product'}), (b:SchemaMeta {name: 'Attribution'})
MERGE (a)-[r:QUALIFIED_ATTRIBUTION]->(b)
  SET r.vocab_id = 'catalog_cabinet_qualified_attribution', r.prov_maps_to = 'prov:qualifiedAttribution', r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'AreaProduct'}), (b:SchemaMeta {name: 'Attribution'})
MERGE (a)-[r:QUALIFIED_ATTRIBUTION]->(b)
  SET r.vocab_id = 'catalog_cabinet_qualified_attribution', r.prov_maps_to = 'prov:qualifiedAttribution', r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Attribution'}), (b:SchemaMeta {name: 'ProductRole'})
MERGE (a)-[r:HAD_ROLE]->(b)
  SET r.vocab_id = 'catalog_cabinet_attribution_had_role', r.prov_maps_to = 'prov:hadRole', r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Product'}), (b:SchemaMeta {name: 'Employee'})
MERGE (a)-[r:WAS_ATTRIBUTED_TO]->(b)
  SET r.vocab_id = 'catalog_cabinet_attributed_to', r.role = 'product_cabinet_role_holder', r.prov_maps_to = 'prov:wasAttributedTo', r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'AreaProduct'}), (b:SchemaMeta {name: 'Employee'})
MERGE (a)-[r:WAS_ATTRIBUTED_TO]->(b)
  SET r.vocab_id = 'catalog_cabinet_attributed_to', r.role = 'product_cabinet_role_holder', r.prov_maps_to = 'prov:wasAttributedTo', r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'DevTeam'}), (b:SchemaMeta {name: 'Product'})
MERGE (a)-[r:SUPPORTS]->(b)
  SET r.vocab_id = 'catalog_supports', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'DevTeam'}), (b:SchemaMeta {name: 'AreaProduct'})
MERGE (a)-[r:SUPPORTS]->(b)
  SET r.vocab_id = 'catalog_supports_area_product', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'active';

MATCH (a:SchemaMeta {name: 'DevTeam'}), (b:SchemaMeta {name: 'Membership'})
MERGE (a)-[r:HAS_MEMBERSHIP]->(b)
  SET r.vocab_id = 'catalog_dev_team_has_membership', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'planned';

// ── domain: architecture ────────────────────────────────────────────────────

MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'DevTeam'})
MERGE (a)-[r:WAS_ATTRIBUTED_TO]->(b)
  SET r.vocab_id = 'arch_develops', r.role = 'developed_by', r.prov_maps_to = 'prov:wasAttributedTo', r.domain = 'architecture', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Code'}), (b:SchemaMeta {name: 'DevTeam'})
MERGE (a)-[r:WAS_ATTRIBUTED_TO]->(b)
  SET r.vocab_id = 'arch_owns_code', r.role = 'owner', r.prov_maps_to = 'prov:wasAttributedTo', r.domain = 'architecture', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Code'}), (b:SchemaMeta {name: 'Bitbucket'})
MERGE (a)-[r:STORED_IN]->(b)
  SET r.vocab_id = 'arch_stored_in', r.prov_maps_to = null, r.domain = 'architecture', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Code'}), (b:SchemaMeta {name: 'PipelineService'})
MERGE (a)-[r:CONTAINS_SERVICE]->(b)
  SET r.vocab_id = 'arch_contains_service', r.prov_maps_to = 'prov:hadMember', r.domain = 'architecture', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'Batch'})
MERGE (a)-[r:CONTAINS_BATCH]->(b)
  SET r.vocab_id = 'arch_contains_batch', r.prov_maps_to = null, r.domain = 'architecture', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Batch'}), (b:SchemaMeta {name: 'ControlMFolder'})
MERGE (a)-[r:CONTAINS_FOLDER]->(b)
  SET r.vocab_id = 'arch_contains_folder', r.prov_maps_to = 'prov:hadMember', r.domain = 'architecture', r.status = 'planned';

// ── domain: registry ────────────────────────────────────────────────────────

MATCH (a:SchemaMeta {name: 'SoftwareProduct'}), (b:SchemaMeta {name: 'Vendor'})
MERGE (a)-[r:MADE_BY]->(b)
  SET r.vocab_id = 'reg_made_by', r.prov_maps_to = 'prov:wasAttributedTo', r.domain = 'registry', r.status = 'active';

MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'SoftwareProduct'})
MERGE (a)-[r:USES_SOFTWARE]->(b)
  SET r.vocab_id = 'reg_uses_software', r.prov_maps_to = null, r.domain = 'registry', r.status = 'active';

// ── domain: docs ────────────────────────────────────────────────────────────

MATCH (a:SchemaMeta {name: 'Document'}), (b:SchemaMeta {name: 'SoftwareProduct'})
MERGE (a)-[r:DESCRIBES]->(b)
  SET r.vocab_id = 'docs_describes', r.prov_maps_to = null, r.domain = 'docs', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Chunk'}), (b:SchemaMeta {name: 'Document'})
MERGE (a)-[r:PART_OF]->(b)
  SET r.vocab_id = 'docs_chunk_part_of', r.prov_maps_to = null, r.domain = 'docs', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Document'}), (b:SchemaMeta {name: 'Chunk'})
MERGE (a)-[r:FIRST_CHUNK]->(b)
  SET r.vocab_id = 'docs_first_chunk', r.prov_maps_to = null, r.domain = 'docs', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Chunk'})
MERGE (a)-[r:NEXT_CHUNK]->(a)
  SET r.vocab_id = 'docs_next_chunk', r.prov_maps_to = null, r.domain = 'docs', r.status = 'active';

MATCH (a:SchemaMeta {name: 'DocSource'}), (b:SchemaMeta {name: 'Document'})
MERGE (a)-[r:HAS_DOCUMENT]->(b)
  SET r.vocab_id = 'docs_has_document', r.prov_maps_to = null, r.domain = 'docs', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Document'}), (b:SchemaMeta {name: 'OntologyTerm'})
MERGE (a)-[r:GOVERNED_BY]->(b)
  SET r.vocab_id = 'docs_governed_by', r.prov_maps_to = null, r.domain = 'docs', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'DocSection'}), (b:SchemaMeta {name: 'DesignDoc'})
MERGE (a)-[r:PART_OF]->(b)
  SET r.vocab_id = 'doc_section_part_of', r.prov_maps_to = null, r.domain = 'docs', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Requirement'}), (b:SchemaMeta {name: 'DocSection'})
MERGE (a)-[r:SPECIFIED_IN]->(b)
  SET r.vocab_id = 'doc_requirement_specified_in', r.prov_maps_to = 'prov:hadPrimarySource', r.domain = 'docs', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Requirement'}), (b:SchemaMeta {name: 'Component'})
MERGE (a)-[r:IMPLEMENTED_BY]->(b)
  SET r.vocab_id = 'doc_requirement_implemented_by', r.prov_maps_to = null, r.domain = 'docs', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Requirement'}), (b:SchemaMeta {name: 'TestCase'})
MERGE (a)-[r:VERIFIED_BY]->(b)
  SET r.vocab_id = 'doc_requirement_verified_by', r.prov_maps_to = null, r.domain = 'docs', r.status = 'active';

MATCH (a:SchemaMeta {name: 'FeedbackNote'}), (b:SchemaMeta {name: 'DocSection'})
MERGE (a)-[r:ANNOTATES]->(b)
  SET r.vocab_id = 'doc_feedback_annotates', r.prov_maps_to = null, r.domain = 'docs', r.status = 'active';

MATCH (a:SchemaMeta {name: 'FeedbackNote'}), (b:SchemaMeta {name: 'Employee'})
MERGE (a)-[r:WAS_ATTRIBUTED_TO]->(b)
  SET r.vocab_id = 'doc_feedback_authored_by', r.role = 'feedback_author', r.prov_maps_to = 'prov:wasAttributedTo', r.domain = 'docs', r.status = 'active';

// ── domain: all ─────────────────────────────────────────────────────────────

// prov_was_generated_by: from_node "*" — representative exemplar edges;
// in the real graph this edge exists on every node label.

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'JobRun'})
MERGE (a)-[r:WAS_GENERATED_BY]->(b)
  SET r.vocab_id = 'prov_was_generated_by', r.prov_maps_to = 'prov:wasGeneratedBy', r.domain = 'all', r.status = 'active';

MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'JobRun'})
MERGE (a)-[r:WAS_GENERATED_BY]->(b)
  SET r.vocab_id = 'prov_was_generated_by', r.prov_maps_to = 'prov:wasGeneratedBy', r.domain = 'all', r.status = 'active';

MATCH (a:SchemaMeta {name: 'CatalogLOB'}), (b:SchemaMeta {name: 'JobRun'})
MERGE (a)-[r:WAS_GENERATED_BY]->(b)
  SET r.vocab_id = 'prov_was_generated_by', r.prov_maps_to = 'prov:wasGeneratedBy', r.domain = 'all', r.status = 'active';

// ── domain: context ─────────────────────────────────────────────────────────

MATCH (a:SchemaMeta {name: 'Observation'}), (b:SchemaMeta {name: 'ControlMJob'})
MERGE (a)-[r:OBSERVES]->(b)
  SET r.vocab_id = 'sosa_observes', r.prov_maps_to = null, r.sosa_maps_to = 'sosa:hasFeatureOfInterest', r.domain = 'context', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Observation'}), (b:SchemaMeta {name: 'Result'})
MERGE (a)-[r:HAS_RESULT]->(b)
  SET r.vocab_id = 'sosa_has_result', r.prov_maps_to = null, r.sosa_maps_to = 'sosa:hasResult', r.domain = 'context', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Observation'}), (b:SchemaMeta {name: 'Sensor'})
MERGE (a)-[r:MADE_BY_SENSOR]->(b)
  SET r.vocab_id = 'sosa_made_by_sensor', r.prov_maps_to = null, r.sosa_maps_to = 'sosa:madeBySensor', r.domain = 'context', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Observation'}), (b:SchemaMeta {name: 'ObservableProperty'})
MERGE (a)-[r:OF_OBSERVABLE_PROPERTY]->(b)
  SET r.vocab_id = 'sosa_observed_property', r.prov_maps_to = null, r.sosa_maps_to = 'sosa:observedProperty', r.domain = 'context', r.status = 'planned';
