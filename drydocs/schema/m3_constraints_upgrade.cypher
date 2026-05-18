// =============================================================================
// m3_constraints_upgrade.cypher
//
// Locks the NODE KEYs to the natural Control-M identity (folder_id.job_id
// / folder_id.condition_name), per the production support team's
// convention.  We DON'T include VERSION_SERIAL in the keys because:
//
//   * The loaders filter to IS_CURRENT_VERSION = '1' at ingest, so a
//     single (folder_id, job_id) — or (folder_id, name) for conditions —
//     pair always resolves to the current version.
//   * Re-running with a newer VERSION_SERIAL UPDATES the same node
//     (refresh-in-place semantics), keeping a single canonical record
//     per logical entity.
//   * VERSION_SERIAL remains as a PROPERTY for audit / freshness
//     queries, but isn't part of identity.
//
// This script also drops any older versioned keys (from earlier M3 drafts
// that included version_serial in the key).
//
// Apply once, after bootstrap.  Idempotent.
// =============================================================================

DROP CONSTRAINT controlmjob_key IF EXISTS;

CREATE CONSTRAINT controlmjob_key IF NOT EXISTS
  FOR (j:ControlMJob)
  REQUIRE (j.folder_id, j.job_id) IS NODE KEY;

DROP CONSTRAINT condition_key IF EXISTS;

CREATE CONSTRAINT condition_key IF NOT EXISTS
  FOR (c:Condition)
  REQUIRE (c.folder_id, c.name) IS NODE KEY;
