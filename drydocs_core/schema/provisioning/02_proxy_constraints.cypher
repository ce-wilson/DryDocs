// =============================================================================
// provisioning/02_proxy_constraints.cypher — RETIRED at G31 (2026-08-18).
//
// This file's charter was CROSS-DATABASE joins: the composite joined drydocs and
// ddcontext by business key, so BOTH databases had to carry the same uniqueness
// on the join keys, and this file was run against each. Gate
// document-content-topology (G32, SIGNED 32/32) folded the content topology to
// ONE database (applied at G102), so the charter lost its subject: there is no
// second database to mirror a key into, and no composite to join across.
//
// THE KEYS DID NOT RETIRE — the file did. Both live in constraints.cypher, the
// one home for one-database keys: `controlmjob_key` was always there (this file
// duplicated it), and `dataasset_id` moved there at G31 with the D1 note. The
// D1 discipline (identity is always a business key, never an internal node id)
// survives as tests/unit/test_business_key_spine.py: every label a shipped
// loader MATCHes as a join target must carry a constrained key.
//
// Kept as a tombstone rather than deleted so the provisioning sequence numbers
// stay stable and the retirement is on the record where the file was.
// =============================================================================
