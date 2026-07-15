// =============================================================================
// schema_graph.cypher  —  DryDocs schema meta-graph
//
// GENERATED from drydocs/ontology/relationship_vocabulary.yaml on 2026-06-09.
// Regenerate when the vocabulary changes.
//
// Creates ONE exemplar node per node label (real label + :SchemaMeta marker)
// and ONE exemplar relationship per vocabulary entry (real relationship type),
// so the full schema renders in Neo4j Browser via:
//     CALL db.schema.visualization();
// or browse the meta-graph directly:
//     MATCH p = (:SchemaMeta)-[]->(:SchemaMeta) RETURN p;
//
// Node properties:  name, class (CURIE per namespaces.py), prov_type
// Edge properties:  vocab_id, role, prov_maps_to, domain, status
//
// NOTE: node label ControlMFolder was renamed ControlMFolder (2026-06-09); this
// schema uses the new label. Deprecated entries (m3_runs_on RUNS_ON
// ControlMFolder→ControlMServer, renamed SCHEDULED_ON) are excluded.
//
// To remove the meta-graph:  MATCH (n:SchemaMeta) DETACH DELETE n;
// =============================================================================

// ── Node labels ──────────────────────────────────────────────────────────────

// — Control-M (M3, active) —
MERGE (n:SchemaMeta:ControlMJob {name: 'ControlMJob'})
  SET n.class = 'dd:ControlMJob', n.prov_type = 'Activity';
MERGE (n:SchemaMeta:ControlMFolder {name: 'ControlMFolder'})
  SET n.class = 'dd:ControlMFolder', n.prov_type = 'Collection';
MERGE (n:SchemaMeta:ControlMServer {name: 'ControlMServer'})
  SET n.class = 'dd:ControlMServer', n.prov_type = 'n/a';
MERGE (n:SchemaMeta:Condition {name: 'Condition'})
  SET n.class = 'dd:Condition', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:JobRun {name: 'JobRun'})
  SET n.class = 'dd:JobRun', n.prov_type = 'Activity';

// — Control-M phase 2 (planned) —
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
MERGE (n:SchemaMeta:DataSource {name: 'DataSource'})
  SET n.class = 'dcat:Dataset', n.prov_type = 'Entity';
MERGE (n:SchemaMeta:DataTarget {name: 'DataTarget'})
  SET n.class = 'dcat:Dataset', n.prov_type = 'Entity';

// — SEAL (active) —
MERGE (n:SchemaMeta:BusinessApplication {name: 'BusinessApplication'})
  SET n.class = 'prov:SoftwareAgent', n.prov_type = 'Agent';
MERGE (n:SchemaMeta:Employee {name: 'Employee'})
  SET n.class = 'prov:Agent', n.prov_type = 'Agent';
MERGE (n:SchemaMeta:Membership {name: 'Membership'})
  SET n.class = 'org:Membership', n.prov_type = 'n/a';
MERGE (n:SchemaMeta:Role {name: 'Role'})
  SET n.class = 'org:Role', n.prov_type = 'n/a';
MERGE (n:SchemaMeta:Port {name: 'Port'})
  SET n.class = 'dprod:Port', n.prov_type = 'Entity';

// — Catalog (active) —
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

// — Architecture flow (planned) —
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

// ── Relationships ────────────────────────────────────────────────────────────

// — Control-M (M3) —
MATCH (a:SchemaMeta {name: 'ControlMFolder'}), (b:SchemaMeta {name: 'ControlMServer'})
MERGE (a)-[r:SCHEDULED_ON]->(b)
  SET r.vocab_id = 'm3_scheduled_on', r.prov_maps_to = null, r.domain = 'controlm', r.status = 'active';

MATCH (a:SchemaMeta {name: 'ControlMFolder'}), (b:SchemaMeta {name: 'ControlMJob'})
MERGE (a)-[r:CONTAINS_JOB]->(b)
  SET r.vocab_id = 'm3_contains_job', r.prov_maps_to = 'prov:hadMember', r.domain = 'controlm', r.status = 'active';

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

// — Control-M phase 2 —
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

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'Script'})
MERGE (a)-[r:INVOKES]->(b)
  SET r.vocab_id = 'm3_invokes', r.prov_maps_to = 'prov:used', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'Script'}), (b:SchemaMeta {name: 'ETLProcess'})
MERGE (a)-[r:TRIGGERS]->(b)
  SET r.vocab_id = 'm3_triggers', r.prov_maps_to = 'prov:wasStartedBy', r.domain = 'controlm', r.status = 'planned';
// NOTE: prov:wasStartedBy flows ETLProcess→Script; TRIGGERS is its inverse.

MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'ExecutionHost'})
MERGE (a)-[r:RUNS_ON]->(b)
  SET r.vocab_id = 'm3_runs_on_agent_host', r.role = 'agent_host', r.prov_maps_to = null, r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ETLProcess'}), (b:SchemaMeta {name: 'ExecutionHost'})
MERGE (a)-[r:RUNS_ON]->(b)
  SET r.vocab_id = 'm3_runs_on_etl_host', r.role = 'etl_host', r.prov_maps_to = null, r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ETLProcess'}), (b:SchemaMeta {name: 'DataSource'})
MERGE (a)-[r:READS_FROM]->(b)
  SET r.vocab_id = 'm3_reads_from', r.prov_maps_to = 'prov:used', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'ETLProcess'}), (b:SchemaMeta {name: 'DataTarget'})
MERGE (a)-[r:WRITES_TO]->(b)
  SET r.vocab_id = 'm3_writes_to', r.prov_maps_to = 'prov:generated', r.domain = 'controlm', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'AppUser'}), (b:SchemaMeta {name: 'ExecutionHost'})
MERGE (a)-[r:DELEGATES_TO]->(b)
  SET r.vocab_id = 'm3_delegates_to', r.prov_maps_to = 'prov:actedOnBehalfOf', r.domain = 'controlm', r.status = 'planned';

// — SEAL —
MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'Port'})
MERGE (a)-[r:HAS_PORT]->(b)
  SET r.vocab_id = 'seal_has_port', r.prov_maps_to = null, r.domain = 'seal', r.status = 'active';

MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'Membership'})
MERGE (a)-[r:HAS_MEMBERSHIP]->(b)
  SET r.vocab_id = 'seal_has_membership', r.prov_maps_to = null, r.domain = 'seal', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Membership'}), (b:SchemaMeta {name: 'Role'})
MERGE (a)-[r:OF_ROLE]->(b)
  SET r.vocab_id = 'seal_of_role', r.prov_maps_to = null, r.domain = 'seal', r.status = 'active';

MATCH (a:SchemaMeta {name: 'Membership'}), (b:SchemaMeta {name: 'Employee'})
MERGE (a)-[r:HELD_BY]->(b)
  SET r.vocab_id = 'seal_held_by', r.prov_maps_to = null, r.domain = 'seal', r.status = 'active';

// — Catalog —
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

MATCH (a:SchemaMeta {name: 'DevTeam'}), (b:SchemaMeta {name: 'Product'})
MERGE (a)-[r:SUPPORTS]->(b)
  SET r.vocab_id = 'catalog_supports', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'DevTeam'}), (b:SchemaMeta {name: 'AreaProduct'})
MERGE (a)-[r:SUPPORTS]->(b)
  SET r.vocab_id = 'catalog_supports_area_product', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'planned';

MATCH (a:SchemaMeta {name: 'DevTeam'}), (b:SchemaMeta {name: 'Membership'})
MERGE (a)-[r:HAS_MEMBERSHIP]->(b)
  SET r.vocab_id = 'catalog_dev_team_has_membership', r.prov_maps_to = null, r.domain = 'catalog', r.status = 'planned';

// — Architecture flow —
MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'DevTeam'})
MERGE (a)-[r:WAS_ATTRIBUTED_TO]->(b)
  SET r.vocab_id = 'arch_develops', r.role = 'developed_by', r.prov_maps_to = 'prov:wasAttributedTo', r.domain = 'architecture', r.status = 'planned';

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

// — Cross-domain provenance —
// prov_was_generated_by: written by BaseLoader for EVERY node label
// (from_node: "*"). One representative edge per domain keeps the
// visualization readable; in the real graph this edge exists on all nodes.
MATCH (a:SchemaMeta {name: 'ControlMJob'}), (b:SchemaMeta {name: 'JobRun'})
MERGE (a)-[r:WAS_GENERATED_BY]->(b)
  SET r.vocab_id = 'prov_was_generated_by', r.prov_maps_to = 'prov:wasGeneratedBy', r.domain = 'all', r.status = 'active';

MATCH (a:SchemaMeta {name: 'BusinessApplication'}), (b:SchemaMeta {name: 'JobRun'})
MERGE (a)-[r:WAS_GENERATED_BY]->(b)
  SET r.vocab_id = 'prov_was_generated_by', r.prov_maps_to = 'prov:wasGeneratedBy', r.domain = 'all', r.status = 'active';

MATCH (a:SchemaMeta {name: 'CatalogLOB'}), (b:SchemaMeta {name: 'JobRun'})
MERGE (a)-[r:WAS_GENERATED_BY]->(b)
  SET r.vocab_id = 'prov_was_generated_by', r.prov_maps_to = 'prov:wasGeneratedBy', r.domain = 'all', r.status = 'active';
