# DryDocs Consolidated Documentation

## 1. Relationship Mapping

DryDocs classifies every relationship by PROV-O source / target type, then picks the Neo4j label. The matrix below is the canonical rule-set.

| Source type   | Target type       | PROV-O term            | Neo4j label         |
|:--------------|:------------------|:-----------------------|:--------------------|
| Activity      | Activity          | prov:wasInformedBy     | WAS_INFORMED_BY     |
| Activity      | Entity            | prov:used              | USED                |
| Activity      | Entity (produces) | prov:generated         | GENERATED           |
| Activity      | Agent             | prov:wasAssociatedWith | WAS_ASSOCIATED_WITH |
| Entity        | Activity          | prov:wasGeneratedBy    | WAS_GENERATED_BY    |
| Entity        | Entity            | prov:wasDerivedFrom    | WAS_DERIVED_FROM    |
| Entity        | Agent             | prov:wasAttributedTo   | WAS_ATTRIBUTED_TO   |
| Agent         | Agent             | prov:actedOnBehalfOf   | ACTED_ON_BEHALF_OF  |
| Collection    | any               | prov:hadMember         | HAD_MEMBER          |

> **USED vs GENERATED:** Activity→Entity. Use USED for reading, GENERATED for producing.

## 2. Node type quick reference

| Node label      | PROV-O / W3C type      | Supplement                         |
|:----------------|:-----------------------|:-----------------------------------|
| ControlMJob     | prov:Activity          | ontology_supplement.cypher      |
| JobFolder       | prov:Collection        | ontology_supplement.cypher      |
| ControlMServer  | local Platform         | ontology_supplement.cypher      |
| Condition       | prov:Entity            | ontology_supplement.cypher      |
| JobRun          | prov:Activity          | base ontology                      |
| Application     | prov:SoftwareAgent     | seal_ontology_supplement.cypher    |
| Employee        | prov:Agent             | seal_ontology_supplement.cypher    |
| Membership      | prov:Membership        | seal_ontology_supplement.cypher    |
| Role            | org:Role               | seal_ontology_supplement.cypher    |
| Port            | dprod:Port             | seal_ontology_supplement.cypher    |
| CatalogLOB      | org:OrganizationalUnit | catalog_ontology_supplement.cypher |
| BusinessSegment | org:FormalOrganization | catalog_ontology_supplement.cypher |
| DevTeam         | org:OrganizationalUnit | catalog_ontology_supplement.cypher |
| ProductLine     | local                  | catalog_ontology_supplement.cypher |
| Product         | local                  | catalog_ontology_supplement.cypher |
| JiraBoard       | local                  | catalog_ontology_supplement.cypher |

## 3. Phase 2 — execution lineage (planned)

Extends Control-M graph from scheduled to actual runtime execution.

| Edge                      | Domain → Range               | PROV-O                 | Required feed                    |
|:--------------------------|:-----------------------------|:-----------------------|:---------------------------------|
| DEPLOYED_BY               | Deployment → Developer       | prov:wasAssociatedWith | Change / CI-CD                   |
| DEPLOYED_TO               | Deployment → ControlMServer  | prov:wasAssociatedWith | Change / CI-CD                   |
| DEPLOYS_FOLDER            | Deployment → JobFolder       | prov:used              | Change / CI-CD                   |
| AUTHORED_BY               | JobFolder → Developer        | prov:wasAttributedTo   | Folder XML / Git blame           |
| INSTANCE_OF               | ControlMJobRun → ControlMJob | prov:wasInfluencedBy   | Control-M history API            |
| EXECUTED_BY               | ControlMJobRun → AppUser     | prov:wasAssociatedWith | Control-M history API            |
| INVOKES                   | ControlMJob → Script         | prov:used              | Folder XML (CMDLINE / MEMNAME)   |
| TRIGGERS                  | Script → ETLProcess          | prov:wasStartedBy      | Informatica / Ab Initio metadata |
| RUNS_ON (role=agent_host) | ControlMJob → ExecutionHost  | infra                  | CMDB / Control-M agent map       |
| RUNS_ON (role=etl_host)   | ETLProcess → ExecutionHost   | infra                  | CMDB / ETL engine config         |
| READS_FROM                | ETLProcess → DataSource      | prov:used              | Informatica / Ab Initio          |
| WRITES_TO                 | ETLProcess → DataTarget      | prov:generated         | Informatica / Ab Initio          |
| DELEGATES_TO              | AppUser → ExecutionHost      | prov:actedOnBehalfOf   | CMDB / IAM                       |

## 4. Architectural Graph Flow

This diagram outlines the refined application hierarchy:

```mermaid
graph TD
    DevTeam((DevTeam)) -- develops --> App((Application))
    DevTeam -- owns --> Code((Code))
    Code -- stored_in --> Bitbucket((Bitbucket))
    Code -- contains --> PS((PipelineService))
    App -- CONTAINS --> Batch((Batch))
    Batch -- CONTAINS --> CTMFolder((Control-M Folders))
    CTMFolder -- CONTAINS --> CTMJob((Control-M Jobs))
    CTMJob -- DEPENDS_ON --> File((Files Delivered via mfts agent fmSubPathId))
```

## 5. Passwords Sheet — workstation fallback

Used when the AWS Glue Plugin runs on a workstation.

| Field       | Description                                                    |
|:------------|:---------------------------------------------------------------|
| FID         | FID name / id.                                                 |
| Domain      | Domain the FID is on. Look up in go/ars, go/arsdev, or go/vst. |
| Environment | DEV, UAT, or PROD.                                             |
| Use Case    | AWS, CCMS, DPL, or CONTROL-M.                                  |

## 6. DryDocs Ingest Notes

| Template sheet / field                                                                                           | Graph projection                                                                                            | Vocabulary id (status)                      |
|:-----------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------|:--------------------------------------------|
| Ingestion · Dataset; Route · datasetGuid/datasetName/datasetVersion                                              | ETLProcess identity (one Placement Job → one ETLProcess activity)                                           | anchors the Script → ETLProcess edge below) |
| Ingestion · Source Zone + Source Glue Database; Route · source side                                              | DataSource node; edge ETLProcess -[:READS_FROM]-> DataSource                                                | m3_reads_from (planned)                     |
| Ingestion · Target Zone + Target Glue Database Name; Glue · Database Name/Dataset/AWS Bucket Name/Partition Keys | DataTarget node; edge ETLProcess -[:WRITES_TO]-> DataTarget                                                 | m3_writes_to (planned)                      |
| Control_M · Jar Path + Task Json Path                                                                            | Script node (the placement JAR + its Task-JSON argument); edge ControlMJob -[:INVOKES]-> Script             | m3_invokes (planned)                        |
| Implicit on the Placement Job                                                                                    | Script -[:TRIGGERS]-> ETLProcess (script launches the AWS-side ingestion workload)                          | m3_triggers (planned)                       |
| Control_M · Host (e.g. PROCO-CDS-UTIL#, 124n8)                                                                   | ExecutionHost; edge ControlMJob -[:RUNS_ON {role:'agent_host'}]-> ExecutionHost                             | m3_runs_on_agent_host (planned)             |
| Connector · Region / Bucket Name (AWS-side cluster entry point)                                                  | ExecutionHost for the ETL engine; edge ETLProcess -[:RUNS_ON {role:'etl_host'}]-> ExecutionHost             | m3_runs_on_etl_host (planned)               |
| Control_M · Run as User; EPV/Passwords · FID rows with Use Case='CONTROL-M'                                      | AppUser (service account); edge ControlMJob -[:EXECUTED_BY]-> AppUser                                       | m3_executed_by (planned)                    |
| EPV · FID rows with Use Case='AWS'/'DPL'/'CCMS' plus Environment                                                 | AppUser -[:DELEGATES_TO]-> ExecutionHost per environment                                                    | m3_delegates_to (planned)                   |
| Control_M · Folder Name (+ Domain fallback), Environment, Server                                                 | JobFolder + JobFolder -[:SCHEDULED_ON]-> ControlMServer (already loaded by M3)                              | m3_scheduled_on (active)                    |
| Control_M · In Conditions                                                                                        | ControlMJob -[:REQUIRES_IN_CONDITION]-> Condition (folder-level, already loaded by M3)                      | m3_requires_in_condition (active)           |
| Connector · Application ID; Glue · Publisher Seal                                                                | Application (SEAL) node; the Data-Delivery SEAL owns the ETLProcess, the Publisher SEAL owns the DataTarget | linked via SEAL loaders (out of M3 scope)   |

