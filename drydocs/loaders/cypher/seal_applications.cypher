// =============================================================================
// seal_applications.cypher
//
// Loads PSGMGR.DECO_SEAL_APP_INFO into :Application + two-port pattern,
// and splays the three embedded contacts (Application Owner, CTO,
// Primary Information Owner) directly into Memberships.
//
// Additional roles (BIO, DA, CBT, L1/L2 Operate Manager, BAO, Risk
// Manager) come via the separate SEAL Contact extract loaded by
// seal_contacts.cypher.
//
// Parameters: $batch (validated SealApplicationRow dicts),
//             $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row

// ---- Application upsert -----------------------------------------------------
MERGE (a:Application {seal_id: row.app_id})
  ON CREATE SET a.created_at = datetime($loaded_at),
                a.source     = 'SEAL'
SET a.name                          = row.name,
    a.app_short_name                = row.app_short_name,
    a.description                   = row.description,

    a.status                        = row.app_state,
    a.investment_strategy           = row.investment_strategy,
    a.creation_date                 = row.creation_date,
    a.actual_build_start_date       = row.actual_build_start_date,
    a.actual_operate_date           = row.actual_operate_date,
    a.actual_decom_date             = row.actual_decom_date,
    a.actual_retirement_date        = row.actual_retirement_date,
    a.planned_build_start_date      = row.planned_build_start_date,
    a.planned_operate_date          = row.planned_operate_date,
    a.planned_decom_date            = row.planned_decom_date,
    a.planned_decom_date_chg_reason = row.planned_decom_date_chg_reason,
    a.planned_retirement_date       = row.planned_retirement_date,
    a.replaced_by_app_ids           = row.replaced_by_app_ids,
    a.replacement_app_type          = row.replacement_app_type,
    a.retirement_type               = row.retirement_type,

    a.app_lob                       = row.app_lob,
    a.reporting_cio_lob             = row.reporting_cio_lob,
    a.reporting_cto_group           = row.reporting_cto_group,
    a.tech_group_owner              = row.tech_group_owner,
    a.tech_group_owner_id           = row.tech_group_owner_id,
    a.owning_legal_entity           = row.owning_legal_entity,
    a.using_lob_sub_lobs            = row.using_lob_sub_lobs,

    a.risk_level                    = row.overall_risk_rating,
    a.sox_governed                  = row.sox_reportable,
    a.sox_reportable                = row.sox_reportable,
    a.glba_reportable               = row.glba_reportable,
    a.pci_reportable                = row.pci_reportable,
    a.soc1_reportable               = row.soc1_reportable,
    a.ccar_reportable               = row.ccar_reportable,
    a.global_statutory_audit        = row.global_statutory_audit,
    a.payment_card_industry_category = row.payment_card_industry_category,
    a.info_classification           = row.info_classification,
    a.personal_info                 = row.personal_info,
    a.sensitive_personal_info       = row.sensitive_personal_info,
    a.client_confidential_info      = row.client_confidential_info,
    a.phi                           = row.phi,
    a.mnpi                          = row.mnpi,
    a.strictest_rpo                 = row.strictest_rpo,
    a.strictest_rto                 = row.strictest_rto,

    a.hosting_vendor                = row.hosting_vendor,
    a.overall_hosting_type          = row.overall_hosting_type,
    a.platforms                     = row.platforms,
    a.kapp                          = row.kapp,
    a.provides_platforms            = row.provides_platforms,
    a.programming_languages         = row.programming_languages,
    a.app_dev_responsibility        = row.app_dev_responsibility,
    a.app_dev_vendor_name           = row.app_dev_vendor_name,
    a.firm_owned_source_code        = row.firm_owned_source_code,

    a.authentication_type           = row.authentication_type,
    a.authorization_type            = row.authorization_type,
    a.fine_grain_authorization_type = row.fine_grain_authorization_type,
    a.external_network_connectivity = row.external_network_connectivity,
    a.external_network_exposure     = row.external_network_exposure,
    a.tier_0_1_or_2_network_assets  = row.tier_0_1_or_2_network_assets,
    a.external_api_connectivity     = row.external_api_connectivity,
    a.external_access_control       = row.external_access_control,

    a.certification_status          = row.certification_status,
    a.last_certified_by_sid         = row.last_certified_by_sid,
    a.last_certified_date           = row.last_certified_date,
    a.data_integrity                = row.data_integrity,
    a.capture_date                  = row.capture_date,
    a.last_seen_at                  = datetime($loaded_at),
    a.last_run_id                   = $run_id

// ---- Two ports (v3 §C) ------------------------------------------------------
MERGE (ep:Port:EventProcessing {parent_seal_id: row.app_id, kind: 'EventProcessing'})
  ON CREATE SET ep.created_at = datetime($loaded_at), ep.active = false
SET ep.last_seen_at = datetime($loaded_at)

MERGE (bp:Port:BatchProcessing {parent_seal_id: row.app_id, kind: 'BatchProcessing'})
  ON CREATE SET bp.created_at = datetime($loaded_at), bp.active = false
SET bp.last_seen_at = datetime($loaded_at)

MERGE (a)-[:HAS_PORT]->(ep)
MERGE (a)-[:HAS_PORT]->(bp)

// ---- Provenance attribution -------------------------------------------------
WITH a, row
MATCH (run:JobRun {run_id: $run_id})
MERGE (a)-[r:WAS_GENERATED_BY {source: 'SEAL'}]->(run)
  ON CREATE SET r.first_seen_at = datetime($loaded_at)
SET r.last_seen_at = datetime($loaded_at)

// ---- Embedded contact 1: Application Owner ----------------------------------
WITH a, row
FOREACH (_ IN CASE WHEN row.app_owner_sid IS NOT NULL THEN [1] ELSE [] END |
  MERGE (e:Employee {employee_id: row.app_owner_sid})
    ON CREATE SET e.created_at = datetime($loaded_at), e.source = 'SEAL'
  SET e.full_name    = coalesce(row.app_owner_name, e.full_name),
      e.last_seen_at = datetime($loaded_at),
      e.last_run_id  = $run_id
  MERGE (r1:Role {name: 'Application Owner'})
  MERGE (a)-[:HAS_MEMBERSHIP]->(m1:Membership {
      membership_id: row.app_id + '|SEAL|Application Owner|' + row.app_owner_sid
  })
    ON CREATE SET m1.source     = 'SEAL',
                  m1.valid_from = date(),
                  m1.valid_to   = null,
                  m1.created_at = datetime($loaded_at)
  SET m1.last_seen_at = datetime($loaded_at),
      m1.last_run_id  = $run_id
  MERGE (m1)-[:OF_ROLE]->(r1)
  MERGE (m1)-[:HELD_BY]->(e)
)

// ---- Embedded contact 2: CTO ------------------------------------------------
WITH a, row
FOREACH (_ IN CASE WHEN row.chief_tech_officer_sid IS NOT NULL THEN [1] ELSE [] END |
  MERGE (e:Employee {employee_id: row.chief_tech_officer_sid})
    ON CREATE SET e.created_at = datetime($loaded_at), e.source = 'SEAL'
  SET e.full_name    = coalesce(row.chief_tech_officer_name, e.full_name),
      e.last_seen_at = datetime($loaded_at),
      e.last_run_id  = $run_id
  MERGE (r2:Role {name: 'CTO'})
  MERGE (a)-[:HAS_MEMBERSHIP]->(m2:Membership {
      membership_id: row.app_id + '|SEAL|CTO|' + row.chief_tech_officer_sid
  })
    ON CREATE SET m2.source     = 'SEAL',
                  m2.valid_from = date(),
                  m2.valid_to   = null,
                  m2.created_at = datetime($loaded_at)
  SET m2.last_seen_at = datetime($loaded_at),
      m2.last_run_id  = $run_id
  MERGE (m2)-[:OF_ROLE]->(r2)
  MERGE (m2)-[:HELD_BY]->(e)
)

// ---- Embedded contact 3: Primary Information Owner --------------------------
WITH a, row
FOREACH (_ IN CASE WHEN row.info_owner_sid IS NOT NULL THEN [1] ELSE [] END |
  MERGE (e:Employee {employee_id: row.info_owner_sid})
    ON CREATE SET e.created_at = datetime($loaded_at), e.source = 'SEAL'
  SET e.full_name    = coalesce(row.info_owner_name, e.full_name),
      e.last_seen_at = datetime($loaded_at),
      e.last_run_id  = $run_id
  MERGE (r3:Role {name: 'Primary Information Owner'})
  MERGE (a)-[:HAS_MEMBERSHIP]->(m3:Membership {
      membership_id: row.app_id + '|SEAL|Primary Information Owner|' + row.info_owner_sid
  })
    ON CREATE SET m3.source     = 'SEAL',
                  m3.valid_from = date(),
                  m3.valid_to   = null,
                  m3.created_at = datetime($loaded_at)
  SET m3.last_seen_at = datetime($loaded_at),
      m3.last_run_id  = $run_id
  MERGE (m3)-[:OF_ROLE]->(r3)
  MERGE (m3)-[:HELD_BY]->(e)
);
