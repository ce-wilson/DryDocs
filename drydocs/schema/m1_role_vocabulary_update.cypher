// =============================================================================
// m1_role_vocabulary_update.cypher
//
// Aligns the :Role vocabulary with the SEAL framework spec
// (seal-overview-with-roles.txt).
//
// Changes from M0 ontology.cypher:
//   * Rename 'App Owner' -> 'Application Owner' (SEAL spec name)
//   * Rename 'Data Owner' -> 'Primary Information Owner' (PIO; SEAL spec)
//   * Add 'Backup Information Owner' (BIO)
//   * Add 'Design Authority' (DA)
//   * Add 'Chief Business Technologist' (CBT)
//   * Add 'L1 Operate Manager'
//   * Add 'Backup Application Owner' (BAO; effective 2026-05-18)
//   * Keep 'L2 Operate Manager', 'CTO', 'Risk Manager' (latter is
//     user-confirmed; not in published SEAL spec but commonly used)
//
// Idempotent. Safe to re-run.  Existing :Membership -> :OF_ROLE edges
// carry over automatically because we rename properties in-place rather
// than creating new nodes.
// =============================================================================

// ---- 1. Rename existing roles to SEAL-spec canonical names -----------------

// 'App Owner' -> 'Application Owner'.  Only fires if the old name is
// still present and the new name doesn't already exist.
MATCH (r:Role {name: 'App Owner'})
WHERE NOT EXISTS { MATCH (:Role {name: 'Application Owner'}) }
SET r.name = 'Application Owner',
    r.deprecated_name = 'App Owner',
    r.spec_source = 'SEAL framework';

// 'Data Owner' -> 'Primary Information Owner'.
MATCH (r:Role {name: 'Data Owner'})
WHERE NOT EXISTS { MATCH (:Role {name: 'Primary Information Owner'}) }
SET r.name = 'Primary Information Owner',
    r.deprecated_name = 'Data Owner',
    r.spec_source = 'SEAL framework';


// ---- 2. Idempotent MERGE for the full SEAL-spec role set -------------------

MERGE (r:Role {name: 'Application Owner'})
  SET r.source = 'SEAL',
      r.description = 'Direct responsibility for the application; maintains records, certifies compliance.',
      r.mandatory = true,
      r.spec_level = 'Application',
      r.spec_source = 'SEAL framework';

MERGE (r:Role {name: 'Primary Information Owner'})
  SET r.source = 'SEAL',
      r.description = 'Primary business leader accountable for data classification, access, risk, regulatory compliance.',
      r.mandatory = true,
      r.spec_level = 'Application',
      r.spec_source = 'SEAL framework';

MERGE (r:Role {name: 'Backup Information Owner'})
  SET r.source = 'SEAL',
      r.description = 'Delegate for the PIO; maintains identical data access rights; cannot be the same individual as the PIO.',
      r.mandatory = true,
      r.spec_level = 'Application',
      r.spec_source = 'SEAL framework';

MERGE (r:Role {name: 'CTO'})
  SET r.source = 'SEAL',
      r.description = 'Chief Technology Officer; accountable to LOB CIO for holistic management of applications within the technology group.',
      r.mandatory = true,
      r.spec_level = 'Application',
      r.spec_source = 'SEAL framework';

MERGE (r:Role {name: 'Design Authority'})
  SET r.source = 'SEAL',
      r.description = 'Responsible for application architecture, alignment with CTO investment strategies, gatekeeping new application risk profiles.',
      r.mandatory = true,
      r.spec_level = 'Application',
      r.spec_source = 'SEAL framework';

MERGE (r:Role {name: 'Chief Business Technologist'})
  SET r.source = 'SEAL',
      r.description = 'Senior management accountable to the CTO for aligning IT/business planning, budgeting, technology services.',
      r.mandatory = true,
      r.spec_level = 'Application',
      r.spec_source = 'SEAL framework';

// Optional operational roles --------------------------------------------------
MERGE (r:Role {name: 'L1 Operate Manager'})
  SET r.source = 'SEAL',
      r.description = 'Leads the business-facing operate team providing front-line application support (e.g., trading-floor support).',
      r.mandatory = false,
      r.spec_level = 'Optional',
      r.spec_source = 'SEAL framework';

MERGE (r:Role {name: 'L2 Operate Manager'})
  SET r.source = 'SEAL',
      r.description = 'Leads the back-end support team managing component infrastructure and technical operations. Drives DryDocs §F.4 support-team derivation.',
      r.mandatory = false,
      r.spec_level = 'Optional',
      r.spec_source = 'SEAL framework';

MERGE (r:Role {name: 'Backup Application Owner'})
  SET r.source = 'SEAL',
      r.description = 'Assists the Application Owner with recertifications, record updates, RLI breaks. Effective 2026-05-18.',
      r.mandatory = false,
      r.spec_level = 'Optional',
      r.spec_source = 'SEAL framework',
      r.effective_from = date('2026-05-18');

MERGE (r:Role {name: 'Risk Manager'})
  SET r.source = 'SEAL',
      r.description = 'Risk owner. Production-support-team convention; NOT in the published SEAL framework spec.',
      r.mandatory = false,
      r.spec_level = 'Production-support convention',
      r.spec_source = 'user-confirmed (not in SEAL framework spec)';


// ---- 3. PAT roles unchanged from M0 (dev-side, not SEAL) --------------------
//   No changes here — the M0 seed for Agility Lead / Software Engineer /
//   Product Contact is correct as-is.
