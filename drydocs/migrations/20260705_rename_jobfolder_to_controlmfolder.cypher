// Migration: rename label JobFolder -> ControlMFolder (ADR 0003 follow-up 1)
// Target: existing local Neo4j sandbox graph. Run once. Idempotent.
// New graphs need only drydocs/schema/constraints.cypher — loaders now emit
// :ControlMFolder directly.

// 1) Relabel every node (Neo4j has no in-place label rename).
MATCH (n:JobFolder)
SET n:ControlMFolder
REMOVE n:JobFolder;

// 2) Drop the constraint bound to the OLD label (JobFolder-era name).
DROP CONSTRAINT folder_id IF EXISTS;

// 3) Recreate it against the NEW label (mirrors constraints.cypher post-rename).
CREATE CONSTRAINT controlmfolder_id IF NOT EXISTS
FOR (n:ControlMFolder) REQUIRE n.folder_id IS UNIQUE;

// 4) Sanity checks (run manually; expect old = 0):
// MATCH (n:JobFolder)      RETURN count(n) AS old_label_remaining;
// MATCH (n:ControlMFolder) RETURN count(n) AS new_label_count;
