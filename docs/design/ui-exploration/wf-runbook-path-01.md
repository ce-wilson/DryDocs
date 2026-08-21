# wf-runbook-path-01 — app-to-app path runbook, two-layer view (rung 2)

> Captured 2026-07-21 from chat ("a proposed runbook between 2 points source and
> target with a technical layer and a data layer … Business Application (HL-1) →
> Business Application (HL-2) … assume this would be built on the shortest path or
> path cypher"). Modeled on the INTERNAL search-for-file-name use case (Neo4j
> Browser `Shortest 1` from an Application to a file node across team / repo /
> Control-M / managed-transfer nodes — that screenshot lives at the repo ROOT and is
> NEVER committed: real hosts/ids; this wireframe is its mechanism-only twin).
> Rung-3 companion: `wf-runbook-path-01.html`. Groom candidate: extends the O17
> Runbooks module page + the `controlm-runbook-automation` skill's
> failure-driven-batch flow; the path spec would join the QuerySpec registry.
>
> **The shaping rule: the runbook is a PROJECTION of the path.** The user picks two
> anchors; a path query returns one subgraph; the UI partitions it into a TECHNICAL
> lane and a DATA lane by node layer, and every generated runbook step cites the
> path node it came from. Nothing in the runbook is authored free-hand — if a step
> is wrong, the graph (or the path query) is wrong, and THAT gets fixed.

```
+---------------------------------------------------------------------------------+
| TOOLBAR: Source [HL-1 · Origination Workbench v]  →  Target [HL-2 · Servicing   |
|          Core v]   [anchor: file name contains…____] (1)   [Find path]          |
|          EXAMPLE DATA · ILLUSTRATIVE          path: 9 nodes · 2 layers · 1 of 1 |
+---------------------------------------------------------------------------------+
|  TECHNICAL LAYER                    (GitRepo hl-extract-etl) (5)                |
|  (HL-1)--OWNS-->[Folder DEMO-HL-EXTRACT]--CONTAINS_JOB-->[Job hl_daily_extract] |
|      --cond HL-EXTRACT-OK (2)-->[Job hl_core_load]<--CONTAINS_JOB--[Folder      |
|      DEMO-HL-CORE]<--OWNS--(HL-2)                                               |
|  - - - - - - - - - - - - - lane divider (3) - - - - - - - - - - - - - - - - - - |
|  DATA LAYER                                                                     |
|  (TransferRoute NEP-DEMO-rt)--ROUTES-->{File pricing_approval_$DATE.dat}        |
|      --LANDS_IN-->{S3Stage stg_mortgage}--LOADS-->{Dataset app_pipeline}        |
|      --FEEDS-->{View SERVICING_CORE_VW}--READ_BY--^ (to HL-2)                   |
|  cross-lane: Job hl_daily_extract --WRITES--> File   (4)                        |
+------------------------------------------+--------------------------------------+
| CYPHER (the assumed contract) (6)        | INSPECTOR CARDS (7)                  |
|  MATCH p = SHORTEST 1                    |  [File] file_name · provenance_stage |
|   (a:BusinessApplication {seal_id:$src}) |         · transfer route id          |
|   -[]-+                                  |  [TransferRoute] receiver_host ·     |
|   (b:BusinessApplication {seal_id:$tgt}) |         receiver_path · sftp user    |
|  RETURN p                                |  [GitRepo] project · url             |
|  -- file-anchored variant:               |  Node-label legend chips + counts    |
|  … -[]-+(fn:File) WHERE fn.file_name     |                                      |
|      CONTAINS $needle RETURN p           |                                      |
+------------------------------------------+--------------------------------------+
| PROPOSED RUNBOOK — generated from the path (8)                                  |
|  # | layer | node                 | action                    | verify          |
|  1 | data  | File pricing_…​.dat   | confirm arrival at stage  | file watcher OK |
|  2 | tech  | Job hl_daily_extract | check status / rerun      | ended OK        |
|  3 | tech  | cond HL-EXTRACT-OK   | condition posted          | present         |
|  4 | tech  | Job hl_core_load     | check downstream load     | ended OK        |
|  5 | data  | View SERVICING_…_VW  | freshness for HL-2 users  | refreshed today |
+---------------------------------------------------------------------------------+
```

## Annotation key

1. **Anchors.** Default = two `BusinessApplication` pickers (seal-searchable, the O13
   picker pattern). The optional third anchor is the internal use case verbatim: a
   *file-name contains* filter that re-roots the path at a `File` node (the
   search-for-file-name flow). Either way the result is ONE path — `SHORTEST 1`.
2. **Condition edges are first-class hops.** The job→job hop carries its
   `via_condition` label (the O5 dependency-chain payload already returns this);
   a runbook step is generated for the condition itself, not just the jobs.
3. **The lane divider is the layer partition,** not decoration: every path node
   carries `layer` (`technology` | `data`) + `c4_level` (the internal model's
   "C4 — lowest level" annotation generalized). Unknown layer → a visible
   UNPARTITIONED bin above the divider, never silently dropped.
4. **Cross-lane edges (WRITES / READ_BY / ROUTES) are the runbook's joints** — each
   one becomes a verify-handoff step between a technical actor and a data artifact.
5. **Repo/script nodes ride the technical lane** (the internal model's bitbucket
   node): the runbook's "escalate with code link" step cites it. Generic label
   `GitRepo` here; vendor naming is a company-side concern.
6. **Cypher panel = the same honesty rule as SpecGrid's "Copy as Cypher":** the
   panel shows the exact query the view ran. `SHORTEST 1 …-[]-+…` is the modern
   quantified-path form (the internal Browser session used it); classic
   `shortestPath((a)-[*..12]-(b))` is the fallback where that syntax isn't
   available. Both are read-only and would live in the QuerySpec registry
   (`runbooks.app-path.v1`), never in the browser.
7. **Inspector cards mirror the internal screenshot's property panels** (file,
   transfer route, repo) — all values here fictional/`.example`; the real ones are
   exactly what the publish boundary keeps out of this repo.
8. **The generated-runbook grid is the deliverable** — the "proposed runbook
   between 2 points". Each row cites its path node (click → node pulses, the
   O9 linked-selection idiom). Export rides the O11 two-path export + manifest
   once this becomes a QuerySpec-backed view.

## Open items (for grooming)

- Which module owns the view: `/runbooks` (O17) as a "path runbook" tab, or a
  page-level action inside Explorer? Leaning O17 — it IS the runbook generator.
- `layer`/`c4_level` node properties don't exist in the producer graph yet —
  that's a vocabulary/ontology question (HITL gate), not a UI one; until gated,
  the lane partition can derive from label sets (ControlM*/GitRepo = technology;
  File/S3Stage/Dataset/View = data).
- Multi-path ("1 of 1") pager when `SHORTEST k` returns alternatives.
