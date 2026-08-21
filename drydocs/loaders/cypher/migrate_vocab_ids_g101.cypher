// =============================================================================
// migrate_vocab_ids_g101.cypher  —  G101 (the seal_ family §B3's census left out)
//
// ONE-TIME, IDEMPOTENT. Companion to migrate_vocab_ids_g87.cypher: the seal_*
// vocabulary ids migrated 2026-08-21 onto the domain-derived scheme (add-new +
// deprecate-old). Only the join-key string r.vocab_id changes; labels,
// directions and every other property are untouched. Safe to re-run.
// Only ids whose old entry was ACTIVE are listed; the planned appuser pair
// never reached a graph.
// =============================================================================

UNWIND [
  ['seal_has_port',               'business_application_has_port'],
  ['seal_had_primary_source',     'business_application_had_primary_source'],
  ['seal_qualified_attribution',  'human_qualified_attribution'],
  ['seal_attribution_has_agent',  'human_attribution_has_agent'],
  ['seal_attribution_had_role',   'human_attribution_had_role']
] AS pair
MATCH ()-[r {vocab_id: pair[0]}]->()
SET r.vocab_id = pair[1];
