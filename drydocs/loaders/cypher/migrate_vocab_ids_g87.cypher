// =============================================================================
// migrate_vocab_ids_g87.cypher  —  G87 (gate vocabulary-domains-and-id-policy §B3)
//
// ONE-TIME, IDEMPOTENT. The epoch-tag vocabulary ids (m3_/p2_/m7_/u1_/u2_/g22_/
// c23_/prov_/sosa_) were migrated to the domain-derived scheme on 2026-08-21 as
// add-new + deprecate-old pairs. Loaders stamp r.vocab_id with the NEW id from
// that date; this script re-stamps edges written before it. Labels, directions
// and every other property are untouched — only the join-key string changes.
// Safe to re-run: once no old value remains it matches nothing.
//
// Run once per environment after deploying the G87 change. Only the ids whose
// old entry was ACTIVE (i.e. could have been loaded) are listed; planned ids
// never reached a graph.
// =============================================================================

UNWIND [
  ['m3_scheduled_on',             'scheduler_scheduled_on'],
  ['m3_contains_job',             'scheduler_contains_job'],
  ['m3_contains_folder',          'scheduler_contains_folder'],
  ['m3_requires_in_condition',    'scheduler_requires_in_condition'],
  ['m3_emits_out_condition',      'scheduler_emits_out_condition'],
  ['m3_was_informed_by',          'scheduler_was_informed_by'],
  ['m3_belongs_to_application',   'scheduler_belongs_to_application'],
  ['m3_invokes',                  'scheduler_invokes'],
  ['m7_uses_artifact',            'scheduler_uses_artifact'],
  ['m3_runs_on_agent_host',       'scheduler_runs_on_agent_host'],
  ['m3_runs_on_host_group',       'scheduler_runs_on_host_group'],
  ['m3_host_group_contains_host', 'scheduler_host_group_contains_host'],
  ['m3_reads_from',               'scheduler_reads_from'],
  ['m3_writes_to',                'scheduler_writes_to'],
  ['u1_has_module',               'arch_has_module'],
  ['u1_imports',                  'arch_imports'],
  ['u2_contains_entry',           'arch_contains_entry'],
  ['u2_has_media_type',           'arch_has_media_type'],
  ['u1_is_encoded_in',            'arch_is_encoded_in'],
  ['g22_occurrence_of',           'arch_occurrence_of'],
  ['prov_was_generated_by',       'all_was_generated_by'],
  ['c23_in_dimension',            'quality_in_dimension']
] AS pair
MATCH ()-[r {vocab_id: pair[0]}]->()
SET r.vocab_id = pair[1];
