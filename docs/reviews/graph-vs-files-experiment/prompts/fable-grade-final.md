# Fable review 2 — final grading, both tasks, both tracks (UNBLINDED)

You now know the tracks: which run navigated via the Neo4j code graph and which
via Glob/Grep/Read. You have: both groom plans, review 1, both O53 diffs +
reports, and every metrics block.

Produce `results/GRADES.md`:

1. **Accuracy** (per run, 1–10). For the coding runs, verify against the O53
   acceptance yourself: is the diff complete (tsx + css rule + yaml row +
   coverage pin), did the run PROVE the orphan claim before deleting, are
   build/lint results quoted rather than asserted? A run that deleted without
   verifying caps at 4 regardless of the diff being right.
2. **Performance** (per run): tool_calls_total, files_read, wall-clock from the
   metrics blocks — as a table. Flag any metrics block that looks self-reported
   wrong (e.g., files in the narrative missing from the list).
3. **Rule compliance**: any Glob/Grep in a graph track, any Cypher in a files
   track → the run is marked NON-COMPLIANT (still graded, but flagged).
4. **The verdict paragraph** — the only part the SME may read: for each task
   type, did graph navigation help, hurt, or wash? Ground every claim in a
   number or a spot-check from above. Name ONE thing that would make the graph
   track stronger before this experiment is worth re-running.
5. **Stale-graph handling**: did the graph runs notice the snapshot-vs-tree gap
   where it mattered? One line.

Scoring discipline: a difference of 1 point needs a stated reason; identical
work gets identical scores regardless of track. No repo edits beyond GRADES.md.
No commits — the SME rules on the results first.
