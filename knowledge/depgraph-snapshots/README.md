# depgraph snapshots — post-push code-structure comparison

**Run after each push.** Generate a timestamped snapshot of the code dependency graph so
structural drift (added/removed files or import edges) is visible over time — compare each
snapshot to the previous one.

The tool is [`depgraph`](../../../depgraph) (a stdlib-only Python sibling repo that maps a
project to a Neo4j-style dependency model + machine-first JSON).

## Command (after `git push`)

```powershell
.\snapshot.ps1            # -> drydocs-YYYYMMDD.json   (code graph: the 7 package roots below)
.\snapshot.ps1 -Tree      # -> drydocs-tree-YYYYMMDD.json  (full repo file tree)
```

[`snapshot.ps1`](snapshot.ps1) runs depgraph and writes `<project>-<date>.json` with a **`meta`
header** so each snapshot is self-identifying:

```jsonc
"meta": {
  "project": "drydocs", "captured_at": "...", "date": "YYYYMMDD",
  "scan": ["drydocs","drydocs_core","drydocs_api","drydocs_remediation",
           "drydocs_lineage","drydocs_deepdoc","tests"], "tree": false,
  "git": { "commit": "<short>", "full": "...", "branch": "main",
           "describe": "...", "subject": "...", "dirty": false, "pr": <num|null> },
  "depgraph": { "commit": "<short>", "full": "...", "branch": "feat/controlm-lineage",
                "dirty": false, "version": "0.1.0",
                "capabilities": { "multi_root": true, "tree": false } }
}
```

**`git` is what was measured; `depgraph` is what measured it** (U7). Both matter, because the
scan runs in a *sibling repo* whose checked-out revision decides what the snapshot can see —
until 2026-07-28 the header pinned the subject precisely and said nothing about the instrument,
which is how a scanner regression became invisible. Before scanning, `snapshot.ps1` runs
[`probe_instrument.py`](probe_instrument.py) and **refuses** (exit 1, no file written) when the
checkout cannot do what the run needs: multi-root resolution always, `--tree` additionally for
`-Tree`. The probe is **behavioural, never a version string** — depgraph is a fork whose
branches are not ancestors of each other, so there is no monotonic version to compare. Expected
revision and required capabilities live in [`config/dev-environment.yaml`](../../config/dev-environment.yaml);
`tests/unit/test_probe_instrument.py` fails if this machine's instrument has regressed.

`pr` is best-effort (parsed from recent commit subjects/bodies — `pull request #N`, `(#N)`).
The header is **prepended** to depgraph's JSON without reformatting (clean diffs, no BOM), and
`viewer.html` shows `@<commit> (branch) PR#<n>` in its stats. Focused scan = the project's own
code — the six `drydocs*` package roots plus `tests/`, passed to depgraph in ONE invocation so
they share a namespace (see the discontinuity note under **Compare**); `-Tree` captures the full
file tree instead (noisier; includes `.claude/skills`). The `scan` list in each header is the
authority for what a given snapshot actually covered — read it before comparing two of them.

## Compare

Each snapshot's summary line reports `files`, `edges`, `circular_files`. To see what changed:
- **Open [`viewer.html`](viewer.html)** in a browser — load a snapshot in **A**, a second in **B**;
  it renders the graph (cytoscape.js, MIT, CDN — no build) and colors the diff
  (green = added in B, red = removed, grey = unchanged). Views: directory **Structure**,
  Structure+files, or **Dependencies** (Python imports). Compares by project-relative path,
  so different projects (e.g. `drydocs-original` vs `drydocs`) align.

> **Historical note:** Snapshots captured before 2026-07-01 are named `drydocs1-*.json`
> (the project's original name). Files are intentionally not renamed; the historical record
> is preserved as-is. New snapshots follow the `drydocs-<date>.json` convention.

> **⚠ Instrument change — do not read across 2026-07-28 08:48 as growth.** The scanner had a
> resolution defect: `scan()` ran each root in **isolation**, so an absolute import naming a
> *sibling* root, or the file's own package directory, never resolved — and `drydocs_api` was
> not a scan root at all. Fixed by U6 in two halves: the resolver itself in the **`depgraph`
> sibling repo** (shared-namespace `extract_many`, 7 regression tests), and the scan-root list
> here in `047c319`. Note the consequence of that split — **re-running an old snapshot will not
> reproduce it**, because half the fix lives outside this repo's history. Every snapshot up to
> and including
> `drydocs-20260728-0754.json` undercounts; `drydocs-20260728-0848.json` is the first truthful
> one and the baseline going forward. Across that boundary the counts go **194 files / 105
> edges → 205 / 370** on essentially the same code: the files rose because a root was added,
> but the edges more than **tripled** because they had been silently unresolved all along.
>
> Practical rules: diffs **within** either era are still valid — the instrument was at least
> consistent — but any comparison **straddling** the boundary shows a phantom jump, and an
> import edge absent from a pre-fix snapshot is not evidence it did not exist. When in doubt,
> compare each snapshot's `meta.scan` list first; two snapshots with different scan roots are
> not comparable at all. (Two snapshots exist for 2026-07-28 rather than the usual one-per-day
> because the fix landed mid-day; the bare-date `drydocs-20260728.json` from that morning was
> **deleted** — it undercounted *and* its commit message asserted "no structural drift" on
> numbers taken from the blind region.)
> **⚠ Instrument change — `abs_path` is gone from snapshots written after 2026-07-28 12:00.**
> Nodes used to carry `abs_path`, stamped with the *checkout location*, so the same code read
> `C:/coding/projects/DryDocs/...` on the desktop, `.../sandbox/DryDocs/...` on the laptop, and
> `.claude/worktrees/<name>/...` from an agent worktree. Two snapshots of identical code
> therefore agreed on all 370 edges while **every one of their 205+ nodes read as changed** —
> a 100%-false structural diff. It was not cosmetic: it blocked the session-end ritual twice on
> 2026-07-28 (a cross-machine comparison, then a worktree snapshot deferred at the P5 close,
> leaving real scan-root drift uncaptured). `snapshot.ps1` now strips the field textually before
> writing, the same way it injects the `meta` header, and refuses to write if any survive.
> `file_id` and `rel_path` already carried the stable identity and the G33 loader dropped
> `abs_path` at load anyway (§H4), so **nothing is lost** — but the first diff across this
> boundary shows every node changed by the field's removal alone. That is the marker, not
> growth. After it, snapshots taken on different machines are comparable for the first time:
> the laptop-vs-desktop pair straddling the fix differed by exactly **one** node — the single
> test file genuinely added — where before it would have differed by all of them.

- or diff the two `.json` files (`git diff` / any JSON diff tool), or watch the summary counts.

### Seeded comparison — the v1 rewrite (original vs this version)
- `tree-original.json` — full tree at commit `683322c` (pre-rewrite): 494 files / 103 dirs, has `vendor/`.
- `tree-this-version.json` — current v1: 540 files / 124 dirs; adds `reference/ external/ config/ internal/`
  (the four layers), `vendor/` → `external/orchestration/bmc-controlm`.
- Load both in the viewer (A = this-version, B = original, or swap) to see the restructure.

### Live Neo4j connection (viewer.html)
The viewer's **🔌 Live Neo4j** button fetches the graph straight from a Neo4j **Query API v2**
endpoint and renders it as **A** (Dependencies view) — no file load, no build.
- Enter the **Query API URL** — local EE container:
  `http://localhost:7474/db/<db>/query/v2` (canonical names/ports in
  `config/dev-environment.yaml`; hosted instances use their own
  `/db/<db>/query/v2` URL) — plus **user** and **password**. "Remember" persists
  only the URL + user in `localStorage`; the **password is never stored** and
  creds are held in memory for the session.
- It runs `MATCH (f:CodeFile) …` + `MATCH (a:CodeFile)-[:DEPENDS_ON]->(b) …`, so the graph must be
  loaded first (below). If the endpoint blocks CORS from `file://`, serve the folder over http
  (`python -m http.server`) and reopen.

### Loading the graph into Neo4j
```bash
depgraph cypher <project-root> --project drydocs --profile base -o load.cypher
# then run load.cypher's 3 statements (constraint, nodes, edges) against the DB.
```
On the local **EE container** (`neo4jtest` — Aura was ruled out 2026-07-06) you can
`CREATE DATABASE depgraph` so the `CodeFile`/`DEPENDS_ON` meta-graph gets its own DB; on any
single-database instance, load into the default db instead — the meta-graph coexists with the
domain graph (distinct labels, no overlap). Native visualization:
`MATCH p=(:CodeFile)-[:DEPENDS_ON]->(:CodeFile) RETURN p` in Browser/Query.

> NVL (`@neo4j-nvl/base`) is the native lib but needs a build and is licensed for Neo4j-backed
> apps — `viewer.html` (cytoscape, MIT) stays the zero-friction option, now with a live mode.

## Housekeeping

- Snapshots are committed so the structural history is diffable. **Prune** old ones periodically
  to keep the repo lean (keep e.g. the last ~10 + one per milestone).
- Baseline: [`drydocs1-20260621.json`](drydocs1-20260621.json) — 49 files, 70 import edges, 0
  circular. (Filename corrected 2026-07-28: this line said `depgraph.20260621-091057.json`, which
  has never existed in this directory; the counts were right. Being pre-U6 it undercounts edges
  like everything before 2026-07-28 08:48 — see the instrument-change note above.)
