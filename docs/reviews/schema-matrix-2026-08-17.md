# Schema matrix — ddschema triples × load sources

> **Point-in-time snapshot, preserved verbatim.** Generated 2026-08-17 by a remote-control
> session and recovered from that session's scratchpad. Regenerate with
> `poetry run python scripts/build_schema_matrix.py`.
>
> **Known stale in two ways** as of the commits pulled after it was written:
>
> 1. **Domain names.** The `vocabulary-domains-and-id-policy` gate renamed `controlm` →
>    `scheduler` and `seal` → `business_application`. The `ddschema` database this was
>    queried from still reported the old values, so those two section headings are
>    pre-rename. Tracked vocabulary fragments
>    (`drydocs_core/ontology/relationship_vocabulary/4*.yaml`) are the current authority.
> 2. **Missing `corporate` domain.** G98 (SIGNED 19/19, `faa0bdd8`) added the corporate
>    backbone and `49-local-corporate.yaml`; `1099d68d` registered the domain. Neither is
>    represented below — this snapshot has 9 domains, the vocabulary now has 10.
>
> **Label source is assigned, not queried** — the ddschema exemplars carry `class`/`prov_type`
> only, with no source annotation. Treat that column as the generator's mapping, not as
> graph-resident fact. If it proves useful, adding a `source` property to the exemplars would
> make the next matrix queried rather than reconstructed.

**Basis:** `ddschema` database (desktop, `neo4jtest`, queried 2026-08-17) — 81
relationship exemplars joined to `web/src/generated/load-map.json` (36 registered
sources) plus the `ontology.cypher` seed. **Label source** = what writes nodes of
that label; **Relationship source** = the registered source + loader whose
ontology mapping carries the edge (with its gate status), or `vocab only` when the
edge is registered in the vocabulary but no source mapping is wired yet.
**Backlog** = backlog.yaml item ids whose text cites the vocab id (exact); a `~`
prefix means the match is on the relationship NAME only (noisier); `—` = no item
mentions it.

## domain: all

| Source label | Label source | Relationship | Vocab id | Status | Relationship source | Target label | Target label source | Backlog |
|---|---|---|---|---|---|---|---|---|
| `BusinessApplication` | seal:app-extract · seal_applications.v1 | **WAS_GENERATED_BY** | `prov_was_generated_by` | active | vocab only — no registered source yet (active) | `JobRun` | loader run envelope (every loader stamps WAS_GENERATED_BY) | M1 |
| `CatalogLOB` | pat:product-catalog · catalog_lobs.v1 | **WAS_GENERATED_BY** | `prov_was_generated_by` | active | vocab only — no registered source yet (active) | `JobRun` | loader run envelope (every loader stamps WAS_GENERATED_BY) | M1 |
| `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | **WAS_GENERATED_BY** | `prov_was_generated_by` | active | vocab only — no registered source yet (active) | `JobRun` | loader run envelope (every loader stamps WAS_GENERATED_BY) | M1 |

## domain: architecture

| Source label | Label source | Relationship | Vocab id | Status | Relationship source | Target label | Target label source | Backlog |
|---|---|---|---|---|---|---|---|---|
| `BusinessApplication` | seal:app-extract · seal_applications.v1 | **WAS_ATTRIBUTED_TO** | `arch_develops` | active | `seal:app-extract` · batch_port_orchestrator.v1,seal_applications.v1,seal_contacts.v1 (applied)<br>`pat:people-report` · pat_product_mapping.v1,pat_team_roles.v1 (confirmed) | `DevTeam` | pat:product-catalog · dev_teams.v1 | C3, C4, C9, K3 +1 |
| `Code` | architecture (planned) | **CONTAINS_SERVICE** | `arch_contains_service` | planned | vocab only — no registered source yet (planned) | `PipelineService` | architecture (planned) | — |
| `Code` | architecture (planned) | **STORED_IN** | `arch_stored_in` | planned | vocab only — no registered source yet (planned) | `Bitbucket` | architecture (planned) | — |
| `Code` | architecture (planned) | **WAS_ATTRIBUTED_TO** | `arch_owns_code` | planned | `seal:app-extract` · batch_port_orchestrator.v1,seal_applications.v1,seal_contacts.v1 (applied)<br>`pat:people-report` · pat_product_mapping.v1,pat_team_roles.v1 (confirmed) | `DevTeam` | pat:product-catalog · dev_teams.v1 | G22, G55 |
| `CodeModule` | repo:depgraph-snapshot · code_snapshot.v1 | **IMPORTS** | `u1_imports` | active | vocab only — no registered source yet (active) | `CodeModule` | repo:depgraph-snapshot · code_snapshot.v1 | O42 |
| `CodeModule` | repo:depgraph-snapshot · code_snapshot.v1 | **IS_ENCODED_IN** | `u1_is_encoded_in` | active | vocab only — no registered source yet (active) | `SwoClass` | repo:depgraph-snapshot · code_snapshot.v1 | G55 |
| `Project` | repo:depgraph-snapshot · code_snapshot.v1 | **HAS_MODULE** | `u1_has_module` | active | vocab only — no registered source yet (active) | `CodeModule` | repo:depgraph-snapshot · code_snapshot.v1 | U10 |

## domain: catalog

| Source label | Label source | Relationship | Vocab id | Status | Relationship source | Target label | Target label source | Backlog |
|---|---|---|---|---|---|---|---|---|
| `AreaProduct` | pat:product-catalog · area_products.v1 | **HAS_DEV_TEAM** | `catalog_area_product_has_dev_team` | planned | `pat:product-catalog` · area_products.v1,catalog_lobs.v1,dev_teams.v1,product_lines.v1,products.v1 (confirmed) | `DevTeam` | pat:product-catalog · dev_teams.v1 | G91 |
| `AreaProduct` | pat:product-catalog · area_products.v1 | **QUALIFIED_ATTRIBUTION** | `catalog_cabinet_qualified_attribution` | active | vocab only — no registered source yet (active) | `Attribution` | seal/pat attribution loaders (+ manual_seal_attribution.v1) | — |
| `AreaProduct` | pat:product-catalog · area_products.v1 | **WAS_ATTRIBUTED_TO** | `catalog_cabinet_attributed_to` | active | `pat:people-report` · pat_product_mapping.v1,pat_team_roles.v1 (confirmed) | `Employee` | seal:app-extract seal_contacts.v1 / pat:people-report | K5 |
| `Attribution` | seal/pat attribution loaders (+ manual_seal_attribution.v1) | **HAD_ROLE** | `catalog_cabinet_attribution_had_role` | active | vocab only — no registered source yet (active) | `ProductRole` | pat:people-report · pat_team_roles.v1 | ~O15 |
| `CatalogLOB` | pat:product-catalog · catalog_lobs.v1 | **HAS_PRODUCT_LINE** | `catalog_has_product_line` | active | `pat:product-catalog` · area_products.v1,catalog_lobs.v1,dev_teams.v1,product_lines.v1,products.v1 (confirmed) | `ProductLine` | pat:product-catalog · product_lines.v1 | ~C26, C27 |
| `CatalogLOB` | pat:product-catalog · catalog_lobs.v1 | **RECONCILES_TO** | `catalog_reconciles_to` | active | `pat:product-catalog` · area_products.v1,catalog_lobs.v1,dev_teams.v1,product_lines.v1,products.v1 (confirmed) | `BusinessSegment` | ontology.cypher seed · drydocs bootstrap | ~C24, C26, C34, D2 +1 |
| `DevTeam` | pat:product-catalog · dev_teams.v1 | **HAS_JIRA_BOARD** | `catalog_has_jira_board` | active | vocab only — no registered source yet (active) | `JiraBoard` | pat:product-catalog · dev_teams.v1 | — |
| `DevTeam` | pat:product-catalog · dev_teams.v1 | **HAS_MEMBERSHIP** | `catalog_dev_team_has_membership` | planned | vocab only in this domain (planned) — same rel name mapped elsewhere: `seal:app-extract` | `Membership` | seal:app-extract / pat:people-report | G91 |
| `DevTeam` | pat:product-catalog · dev_teams.v1 | **SUPPORTS** | `catalog_supports_area_product` | active | `pat:people-report` · pat_product_mapping.v1,pat_team_roles.v1 (confirmed) | `AreaProduct` | pat:product-catalog · area_products.v1 | C3, C4 |
| `DevTeam` | pat:product-catalog · dev_teams.v1 | **SUPPORTS** | `catalog_supports` | active | `pat:people-report` · pat_product_mapping.v1,pat_team_roles.v1 (confirmed) | `Product` | pat:product-catalog · products.v1 | C3, C4, C5, C9 |
| `Product` | pat:product-catalog · products.v1 | **HAS_APPLICATION** | `catalog_has_application` | planned | `pat:product-catalog` · area_products.v1,catalog_lobs.v1,dev_teams.v1,product_lines.v1,products.v1 (confirmed) | `BusinessApplication` | seal:app-extract · seal_applications.v1 | C5, C9, K11, K13 |
| `Product` | pat:product-catalog · products.v1 | **HAS_AREA_PRODUCT** | `catalog_has_area_product` | planned | vocab only — no registered source yet (planned) | `AreaProduct` | pat:product-catalog · area_products.v1 | G91, K6 |
| `Product` | pat:product-catalog · products.v1 | **HAS_DEV_TEAM** | `catalog_has_dev_team` | active | `pat:product-catalog` · area_products.v1,catalog_lobs.v1,dev_teams.v1,product_lines.v1,products.v1 (confirmed) | `DevTeam` | pat:product-catalog · dev_teams.v1 | — |
| `Product` | pat:product-catalog · products.v1 | **QUALIFIED_ATTRIBUTION** | `catalog_cabinet_qualified_attribution` | active | vocab only — no registered source yet (active) | `Attribution` | seal/pat attribution loaders (+ manual_seal_attribution.v1) | — |
| `Product` | pat:product-catalog · products.v1 | **WAS_ATTRIBUTED_TO** | `catalog_cabinet_attributed_to` | active | `pat:people-report` · pat_product_mapping.v1,pat_team_roles.v1 (confirmed) | `Employee` | seal:app-extract seal_contacts.v1 / pat:people-report | K5 |
| `ProductLine` | pat:product-catalog · product_lines.v1 | **HAS_PRODUCT** | `catalog_has_product` | active | `pat:product-catalog` · area_products.v1,catalog_lobs.v1,dev_teams.v1,product_lines.v1,products.v1 (confirmed) | `Product` | pat:product-catalog · products.v1 | ~O23 |

## domain: context

| Source label | Label source | Relationship | Vocab id | Status | Relationship source | Target label | Target label source | Backlog |
|---|---|---|---|---|---|---|---|---|
| `Observation` | cm_hist_vw SOSA arm (proposed) | **HAS_RESULT** | `sosa_has_result` | planned | vocab only — no registered source yet (planned) | `Result` | SOSA context (planned) | — |
| `Observation` | cm_hist_vw SOSA arm (proposed) | **MADE_BY_SENSOR** | `sosa_made_by_sensor` | planned | vocab only — no registered source yet (planned) | `Sensor` | SOSA context (planned) | — |
| `Observation` | cm_hist_vw SOSA arm (proposed) | **OBSERVES** | `sosa_observes` | planned | `controlm@[db].psgmgr.cm_hist_vw` · (no loader yet) (proposed) | `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | E1 |
| `Observation` | cm_hist_vw SOSA arm (proposed) | **OF_OBSERVABLE_PROPERTY** | `sosa_observed_property` | planned | vocab only — no registered source yet (planned) | `ObservableProperty` | SOSA context (planned) | — |

## domain: controlm

| Source label | Label source | Relationship | Vocab id | Status | Relationship source | Target label | Target label source | Backlog |
|---|---|---|---|---|---|---|---|---|
| `AppUser` | cm run_as (planned) | **DELEGATES_TO** | `m3_delegates_to` | planned | vocab only — no registered source yet (planned) | `ExecutionHost` | psgmgr.cm_hosts · controlm_hosts.v1 | G55 |
| `ControlMApplication` | psgmgr.cm_def_vjob (JOB_ID=1 header row) · controlm_folders.v1 | **CONTAINS_FOLDER** | `m3_contains_folder` | active | `controlm@[db].psgmgr.cm_def_vtab` · controlm_folders.v1 (applied) | `ControlMFolder` | psgmgr.cm_def_vtab · controlm_folders.v1 | K8 |
| `ControlMFolder` | psgmgr.cm_def_vtab · controlm_folders.v1 | **AUTHORED_BY** | `p2_authored_by` | planned | vocab only — no registered source yet (planned) | `Developer` | deployment provenance (p2, planned) | — |
| `ControlMFolder` | psgmgr.cm_def_vtab · controlm_folders.v1 | **BELONGS_TO_APPLICATION** | `m3_belongs_to_application` | active | `controlm@[db].psgmgr.cm_def_vjob` · controlm_jobs.v1 (confirmed) | `Port` | seal:app-extract · batch_port_orchestrator.v1 | K8 |
| `ControlMFolder` | psgmgr.cm_def_vtab · controlm_folders.v1 | **CONTAINS_JOB** | `m3_contains_job` | active | `controlm@[db].psgmgr.cm_def_vjob` · controlm_jobs.v1 (applied) | `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | ~C1, K15, K8, O11 |
| `ControlMFolder` | psgmgr.cm_def_vtab · controlm_folders.v1 | **SCHEDULED_ON** | `m3_scheduled_on` | active | `controlm@[db].psgmgr.cm_def_vtab` · controlm_folders.v1 (confirmed) | `ControlMServer` | psgmgr.cm_def_vtab · controlm_folders.v1 | ~C1, C6, D1, O11 |
| `ControlMHostGroup` | psgmgr.cm_hosts · controlm_hosts.v1 | **CONTAINS_HOST** | `m3_host_group_contains_host` | active | `controlm@[db].psgmgr.cm_hosts` · controlm_hosts.v1 (applied) | `ExecutionHost` | psgmgr.cm_hosts · controlm_hosts.v1 | P3 |
| `ControlMHostGroup` | psgmgr.cm_hosts · controlm_hosts.v1 | **DEFINED_ON** | `m3_host_group_defined_on` | planned | `controlm@[db].psgmgr.cm_hosts` · controlm_hosts.v1 (confirmed) | `ControlMServer` | psgmgr.cm_def_vtab · controlm_folders.v1 | P3 |
| `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | **EMITS_OUT_CONDITION** | `m3_emits_out_condition` | active | `controlm@[db].psgmgr.cm_def_lnko_p_vw` · controlm_conditions_out.v1 (confirmed) | `Condition` | psgmgr.cm_def_lnki/lnko_p_vw · controlm_conditions_in/out.v1 | ~C1, O27 |
| `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | **INVOKES** | `m3_invokes` | planned | vocab only — no registered source yet (planned) | `Script` | cmd_line resolution (m3/m7, planned) | C29, C4, G12, G22 +3 |
| `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | **READS_FROM** | `m3_reads_from` | planned | vocab only — no registered source yet (planned) | `DataAsset` | oracle:schema-inventory (proposed) | G13, G14, G55, G9 +1 |
| `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | **REQUIRES_IN_CONDITION** | `m3_requires_in_condition` | active | `controlm@[db].psgmgr.cm_def_lnki_p_vw` · controlm_conditions_in.v1,controlm_dependencies_derived.v1 (confirmed) | `Condition` | psgmgr.cm_def_lnki/lnko_p_vw · controlm_conditions_in/out.v1 | ~C1, O27 |
| `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | **RUNS_ON** | `m3_runs_on_host_group` | active | `controlm@[db].psgmgr.cm_hosts` · controlm_hosts.v1 (applied) | `ControlMHostGroup` | psgmgr.cm_hosts · controlm_hosts.v1 | G55, P3 |
| `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | **RUNS_ON** | `m3_runs_on_agent_host` | active | `controlm@[db].psgmgr.cm_hosts` · controlm_hosts.v1 (applied) | `ExecutionHost` | psgmgr.cm_hosts · controlm_hosts.v1 | G55 |
| `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | **USED** | `m3_depends_on_file` | planned | `oracle:schema-inventory` · (no loader yet) (proposed) | `File` | file dependency (m3, planned) | G91 |
| `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | **USES_ARTIFACT** | `m7_uses_artifact` | planned | vocab only — no registered source yet (planned) | `Script` | cmd_line resolution (m3/m7, planned) | C29, G16, G40, G55 +1 |
| `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | **WAS_INFORMED_BY** | `m3_was_informed_by` | active | `controlm@[db].psgmgr.cm_def_lnki_p_vw` · controlm_conditions_in.v1,controlm_dependencies_derived.v1 (confirmed) | `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | J2 |
| `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | **WRITES_TO** | `m3_writes_to` | planned | vocab only — no registered source yet (planned) | `DataAsset` | oracle:schema-inventory (proposed) | G13, G14, G55, G9 +1 |
| `ControlMJobRun` | psgmgr.cm_hist_vw (planned) | **EXECUTED_BY** | `m3_executed_by` | planned | vocab only — no registered source yet (planned) | `AppUser` | cm run_as (planned) | G91 |
| `ControlMJobRun` | psgmgr.cm_hist_vw (planned) | **INSTANCE_OF** | `p2_instance_of` | planned | vocab only — no registered source yet (planned) | `ControlMJob` | psgmgr.cm_def_vjob · controlm_jobs.v1 | — |
| `Deployment` | deployment provenance (p2, planned) | **DEPLOYED_BY** | `p2_deployed_by` | planned | vocab only — no registered source yet (planned) | `Developer` | deployment provenance (p2, planned) | — |
| `Deployment` | deployment provenance (p2, planned) | **DEPLOYED_TO** | `p2_deployed_to` | planned | vocab only — no registered source yet (planned) | `ControlMServer` | psgmgr.cm_def_vtab · controlm_folders.v1 | — |
| `Deployment` | deployment provenance (p2, planned) | **DEPLOYS_FOLDER** | `p2_deploys_folder` | planned | vocab only — no registered source yet (planned) | `ControlMFolder` | psgmgr.cm_def_vtab · controlm_folders.v1 | — |
| `ETLProcess` | cmd_line resolution (planned) | **READS_FROM** | `m3_reads_from` | planned | vocab only — no registered source yet (planned) | `DataAsset` | oracle:schema-inventory (proposed) | G13, G14, G55, G9 +1 |
| `ETLProcess` | cmd_line resolution (planned) | **RUNS_ON** | `m3_runs_on_etl_host` | planned | `controlm@[db].psgmgr.cm_hosts` · controlm_hosts.v1 (applied) | `ExecutionHost` | psgmgr.cm_hosts · controlm_hosts.v1 | G55 |
| `ETLProcess` | cmd_line resolution (planned) | **WRITES_TO** | `m3_writes_to` | planned | vocab only — no registered source yet (planned) | `DataAsset` | oracle:schema-inventory (proposed) | G13, G14, G55, G9 +1 |
| `Script` | cmd_line resolution (m3/m7, planned) | **TRIGGERS** | `m3_triggers` | planned | vocab only — no registered source yet (planned) | `ETLProcess` | cmd_line resolution (planned) | G55, G89, G9 |

## domain: docs

| Source label | Label source | Relationship | Vocab id | Status | Relationship source | Target label | Target label source | Backlog |
|---|---|---|---|---|---|---|---|---|
| `Chunk` | bmc-docs · bmc_docs.v1 | **NEXT_CHUNK** | `docs_next_chunk` | active | `bmc-docs` · bmc_docs.v1 (applied) | `Chunk` | bmc-docs · bmc_docs.v1 | Q2, Q4 |
| `Chunk` | bmc-docs · bmc_docs.v1 | **PART_OF** | `docs_chunk_part_of` | active | `bmc-docs` · bmc_docs.v1 (applied) | `Document` | bmc-docs · bmc_docs.v1 | Q2, Q4 |
| `DocSection` | repo:design-docs · doc_sections.v1 | **PART_OF** | `doc_section_part_of` | active | `bmc-docs` · bmc_docs.v1 (applied) | `DesignDoc` | repo:design-docs · doc_sections.v1 | ~O18, Q13 |
| `DocSource` | doc-source-registry (docmeta, planned) | **HAS_DOCUMENT** | `docs_has_document` | planned | vocab only — no registered source yet (planned) | `Document` | bmc-docs · bmc_docs.v1 | Q4 |
| `Document` | bmc-docs · bmc_docs.v1 | **DESCRIBES** | `docs_describes` | active | `bmc-docs` · bmc_docs.v1 (applied) | `SoftwareProduct` | config/software-registry · registry loader | Q2, Q4 |
| `Document` | bmc-docs · bmc_docs.v1 | **FIRST_CHUNK** | `docs_first_chunk` | active | `bmc-docs` · bmc_docs.v1 (applied) | `Chunk` | bmc-docs · bmc_docs.v1 | Q2, Q4 |
| `Document` | bmc-docs · bmc_docs.v1 | **GOVERNED_BY** | `docs_governed_by` | planned | vocab only — no registered source yet (planned) | `OntologyTerm` | ontology seed (bootstrap) | Q4 |
| `FeedbackNote` | repo:design-docs · doc_feedback.v1 | **ANNOTATES** | `doc_feedback_annotates` | active | vocab only — no registered source yet (active) | `DocSection` | repo:design-docs · doc_sections.v1 | — |
| `FeedbackNote` | repo:design-docs · doc_feedback.v1 | **WAS_ATTRIBUTED_TO** | `doc_feedback_authored_by` | active | vocab only in this domain (active) — same rel name mapped elsewhere: `seal:app-extract`; `pat:people-report` | `Employee` | seal:app-extract seal_contacts.v1 / pat:people-report | ~G22, G55, K13, K3 +1 |
| `Requirement` | repo:design-docs · doc_traceability.v1 | **IMPLEMENTED_BY** | `doc_requirement_implemented_by` | active | vocab only — no registered source yet (active) | `Component` | repo:design-docs · doc_traceability.v1 | — |
| `Requirement` | repo:design-docs · doc_traceability.v1 | **SPECIFIED_IN** | `doc_requirement_specified_in` | active | vocab only — no registered source yet (active) | `DocSection` | repo:design-docs · doc_sections.v1 | — |
| `Requirement` | repo:design-docs · doc_traceability.v1 | **VERIFIED_BY** | `doc_requirement_verified_by` | active | vocab only — no registered source yet (active) | `TestCase` | repo:design-docs · doc_traceability.v1 | — |

## domain: quality

| Source label | Label source | Relationship | Vocab id | Status | Relationship source | Target label | Target label source | Backlog |
|---|---|---|---|---|---|---|---|---|
| `Dataset` | quality domain (c23, planned) | **HAS_QUALITY** | `c23_has_quality` | planned | vocab only — no registered source yet (planned) | `QualityMeasurement` | quality domain (c23, planned) | ~C23 |
| `Metric` | ontology.cypher DQV seed | **IN_DIMENSION** | `c23_in_dimension` | active | vocab only — no registered source yet (active) | `Dimension` | ontology.cypher DQV seed | ~C23 |
| `QualityMeasurement` | quality domain (c23, planned) | **COMPUTED_ON** | `c23_computed_on` | planned | vocab only — no registered source yet (planned) | `Dataset` | quality domain (c23, planned) | ~C23 |
| `QualityMeasurement` | quality domain (c23, planned) | **IS_MEASUREMENT_OF** | `c23_is_measurement_of` | planned | vocab only — no registered source yet (planned) | `Metric` | ontology.cypher DQV seed | ~C23 |

## domain: registry

| Source label | Label source | Relationship | Vocab id | Status | Relationship source | Target label | Target label source | Backlog |
|---|---|---|---|---|---|---|---|---|
| `BusinessApplication` | seal:app-extract · seal_applications.v1 | **USES_SOFTWARE** | `reg_uses_software` | active | vocab only — no registered source yet (active) | `SoftwareProduct` | config/software-registry · registry loader | C13, C14, K10, K11 |
| `SoftwareProduct` | config/software-registry · registry loader | **MADE_BY** | `reg_made_by` | active | vocab only — no registered source yet (active) | `Vendor` | config/software-registry · registry loader | ~Q16 |

## domain: seal

| Source label | Label source | Relationship | Vocab id | Status | Relationship source | Target label | Target label source | Backlog |
|---|---|---|---|---|---|---|---|---|
| `Attribution` | seal/pat attribution loaders (+ manual_seal_attribution.v1) | **HAD_ROLE** | `seal_attribution_had_role` | active | vocab only — no registered source yet (active) | `TOMRole` | seal:app-extract · seal_contacts.v1 | K4 |
| `Attribution` | seal/pat attribution loaders (+ manual_seal_attribution.v1) | **HAS_AGENT** | `seal_attribution_has_agent` | active | vocab only — no registered source yet (active) | `Employee` | seal:app-extract seal_contacts.v1 / pat:people-report | K4 |
| `BusinessApplication` | seal:app-extract · seal_applications.v1 | **HAD_PRIMARY_SOURCE** | `seal_had_primary_source` | active | `seal-pat-scrape` · (no loader yet) (confirmed) | `Document` | bmc-docs · bmc_docs.v1 | K4 |
| `BusinessApplication` | seal:app-extract · seal_applications.v1 | **HAS_PORT** | `seal_has_port` | active | `seal:app-extract` · batch_port_orchestrator.v1,seal_applications.v1,seal_contacts.v1 (confirmed) | `Port` | seal:app-extract · batch_port_orchestrator.v1 | K3, K4 |
| `BusinessApplication` | seal:app-extract · seal_applications.v1 | **QUALIFIED_ATTRIBUTION** | `seal_qualified_attribution` | active | vocab only — no registered source yet (active) | `Attribution` | seal/pat attribution loaders (+ manual_seal_attribution.v1) | K4 |
| `BusinessApplication` | seal:app-extract · seal_applications.v1 | **WAS_ATTRIBUTED_TO** | `seal_app_attributed_to_employee` | planned | `seal:app-extract` · batch_port_orchestrator.v1,seal_applications.v1,seal_contacts.v1 (applied) | `Employee` | seal:app-extract seal_contacts.v1 / pat:people-report | ~G22, G55, K13, K3 +1 |
