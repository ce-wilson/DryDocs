// =============================================================================
// migrate_payload_invokes_to_uses_artifact_g97.cypher  —  G97 (clause d)
//
// ONE-TIME, IDEMPOTENT. Gate cmdline-nfr-vetting SME-2 (2026-07-21) ruled the
// payload a DISTINCT label, and rua-load-shapes §A4 (2026-08-07) activated
// USES_ARTIFACT alongside INVOKES so payloads would never land in the 1..n
// INVOKES fold in the first place. From G97 the loader routes them correctly on
// write — a payload it can identify NEVER gets an INVOKES edge, so a clean load
// needs nothing from this file.
//
// WHY IT EXISTS ANYWAY. A graph loaded BEFORE G97 has payload artifacts sitting
// on INVOKES, and a re-load cannot fix that on its own: every write in this
// component is a MERGE, and MERGE adds. It has no way to retract an edge a
// previous load asserted. So a re-load alone would leave the payload on INVOKES
// and add USES_ARTIFACT beside it — the DOUBLE REPRESENTATION clause (d) names
// as the one outcome that must be impossible. This script is the other half of
// making that true: it MOVES the edge rather than adding one.
//
// WHAT IT DELIBERATELY DOES NOT TOUCH — :ETLProcess. §B2 chose the union
// endpoint precisely so INVOKES could keep landing on :ETLProcess (G12's
// abioncloud wrapper-payload expansion is working code and was not re-modelled),
// and scheduler_uses_artifact's to_node is `Script`. An Ab Initio pset or a DPL
// pipeline reached through a launcher therefore STAYS on INVOKES: it is not an
// unmigrated leftover, it is where the signed ruling puts it. The MATCH below
// is restricted to :Script for that reason, not by oversight.
//
// IDENTIFYING A PAYLOAD IN AN EXISTING GRAPH: the loader stamps
// s.script_role='payload' before this runs, from the same G16 variable evidence
// the edge routing uses. So the rule is "this Script is a payload AND it still
// carries an INVOKES edge" — never a guess from the path or the extension.
//
// Run once per environment AFTER a G97-era load has stamped script_role.
// Safe to re-run: once no payload carries INVOKES it matches nothing.
//
// Reports what it moved — the counts clause (e) asks for, from the graph rather
// than from the loader's own bookkeeping.
// =============================================================================

MATCH (j:ControlMJob)-[old:INVOKES]->(s:Script)
WHERE s.script_role = 'payload'
MERGE (j)-[new:USES_ARTIFACT]->(s)
  ON CREATE SET new.first_seen_at = coalesce(old.first_seen_at, datetime()),
                new.source        = coalesce(old.source, 'drydocs-lineage'),
                new.vocab_id      = 'scheduler_uses_artifact'
SET new.last_seen_at = coalesce(old.last_seen_at, datetime()),
    new.migrated_from_invokes_at = datetime()
DELETE old
RETURN count(*) AS payload_edges_moved;
