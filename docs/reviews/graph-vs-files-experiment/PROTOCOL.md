# Graph-vs-files context experiment (2026-08-10)

**Question.** Does navigating code context through the loaded Neo4j code graph
(G33/Epic U: `:CodeModule` / `IMPORTS` / `CONTAINS_ENTRY`, database `drydocs`,
container `neo4jtest`, desktop) produce more accurate or cheaper work than the
current file-reading process (Glob/Grep/Read over the tree)?

**Design.** Two tasks × two tracks, 2×2. The MODEL is pinned (haiku) so the only
variable per pair is the context-navigation method. The agent TYPE varies by task
(planning → backlog-groomer, coding → general-purpose), never by track.

| | Track A — GRAPH | Track B — FILES |
|---|---|---|
| **Planning** (groom-plan Ideas 96–103) | backlog-groomer, haiku | backlog-groomer, haiku |
| **Coding** (O53 HeroArt orphan) | general-purpose, haiku, worktree | general-purpose, haiku, worktree |

**Track rules.**
- GRAPH: code-context discovery ONLY via Cypher against the code graph, then
  targeted `Read` of specific files it names. No Glob, no Grep. (Task inputs —
  IDEAS.md, backlog conventions, the O53 acceptance — are given in the prompt and
  exempt: the experiment varies *code* navigation, not the task statement.)
- FILES: the normal process — Glob/Grep/Read. No Neo4j.
- Both report the same metrics block (below). Coding runs happen in isolated
  worktrees; each writes its diff into `results/`, commits nothing.

**Why these tasks.** O53 *originated* from the code graph (the HeroArt orphan
finding, Idea-77), so both tracks independently re-verify the same claim by their
own method — the graph track queries the import edges, the files track greps for
importers. The groom-plan exercises multi-item code-context sizing, which is
where graph navigation should help or hurt most.

**Sequence (cron, 03:05 local).**
1. Dispatch planning A and B in parallel (same prompt except the track block).
2. Fable reviews both plans (review 1) — blind to which track is which until
   after scoring; tracks are labeled ALPHA/BETA in what fable sees.
3. Dispatch coding A and B in parallel (fable's review does not gate the coding
   prompts — they are fixed here; it gates only whether the run is VALID, e.g. a
   track broke its navigation rules).
4. Fable grades everything (review 2): accuracy, completeness, efficiency
   (tool calls, files read), speed, rule compliance. Writes `results/GRADES.md`.
5. **No commit, no push.** Everything stays in `results/` for SME review.
   Final commit + push happen only after the SME rules on the results.

**Metrics block every worker must end with (verbatim keys):**
```
METRICS
files_read: <n>  [list]
searches_or_queries: <n>  [each one, verbatim]
tool_calls_total: <n>
started/finished: <ISO timestamps>
blocked_on: <anything the track rules prevented, or "nothing">
```

**Ground truth for grading (fable verifies, not trusts):**
- O53 acceptance: HeroArt.tsx deleted (default) with its index.css hero-net rule
  and its ui-components.yaml row (coverage pin moved, history-line convention);
  orphan query over TS import edges then returns only vite.config.ts; build +
  lint green.
- Groom-plan: every claim about a file, importer, or module in the plan must be
  independently checkable; fable spot-verifies 3 claims per plan by the OPPOSITE
  track's method.

**Fairness notes recorded in advance.**
- The graph was loaded 2026-08-10 from snapshot @ `bd051ab`; the tree has moved
  (~2 commits, docs-only) — a known, shared handicap; grading must not penalize
  either track for it beyond noting whether the track NOTICED.
- Haiku is below the model O53's planning assumed for grooms; both tracks share
  that equally.
- The graph holds structure, not content: the graph track still Reads files; the
  variable is how it FINDS them.
