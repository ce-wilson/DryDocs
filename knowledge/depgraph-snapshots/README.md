# depgraph snapshots — post-push code-structure comparison

**Run after each push.** Generate a timestamped snapshot of the code dependency graph so
structural drift (added/removed files or import edges) is visible over time — compare each
snapshot to the previous one.

The tool is [`depgraph`](../../../depgraph) (a stdlib-only Python sibling repo that maps a
project to a Neo4j-style dependency model + machine-first JSON).

## Command (after `git push`)

```powershell
.\snapshot.ps1            # -> drydocs-YYYYMMDD.json   (code graph: drydocs/ + tests/)
.\snapshot.ps1 -Tree      # -> drydocs-tree-YYYYMMDD.json  (full repo file tree)
```

[`snapshot.ps1`](snapshot.ps1) runs depgraph and writes `<project>-<date>.json` with a **`meta`
header** so each snapshot is self-identifying:

```jsonc
"meta": {
  "project": "drydocs", "captured_at": "...", "date": "YYYYMMDD",
  "scan": ["drydocs","tests"], "tree": false,
  "git": { "commit": "<short>", "full": "...", "branch": "main",
           "describe": "...", "subject": "...", "dirty": false, "pr": <num|null> }
}
```

`pr` is best-effort (parsed from recent commit subjects/bodies — `pull request #N`, `(#N)`).
The header is **prepended** to depgraph's JSON without reformatting (clean diffs, no BOM), and
`viewer.html` shows `@<commit> (branch) PR#<n>` in its stats. Focused scan = `drydocs/` + `tests/`
(the project's own code); `-Tree` captures the full file tree (noisier; includes `.claude/skills`).

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
- or diff the two `.json` files (`git diff` / any JSON diff tool), or watch the summary counts.

### Seeded comparison — the v1 rewrite (original vs this version)
- `tree-original.json` — full tree at commit `683322c` (pre-rewrite): 494 files / 103 dirs, has `vendor/`.
- `tree-this-version.json` — current v1: 540 files / 124 dirs; adds `reference/ external/ config/ internal/`
  (the four layers), `vendor/` → `external/orchestration/bmc-controlm`.
- Load both in the viewer (A = this-version, B = original, or swap) to see the restructure.

### Live Neo4j connection (viewer.html)
The viewer's **🔌 Live Neo4j** button fetches the graph straight from a Neo4j **Query API v2**
endpoint and renders it as **A** (Dependencies view) — no file load, no build.
- Enter the **Query API URL** (`https://<id>.databases.neo4j.io/db/<db>/query/v2`), **user**, and
  **password**. "Remember" persists only the URL + user in `localStorage`; the **password is never
  stored** and creds are held in memory for the session.
- It runs `MATCH (f:CodeFile) …` + `MATCH (a:CodeFile)-[:DEPENDS_ON]->(b) …`, so the graph must be
  loaded first (below). Aura's Query API sends `access-control-allow-origin: *`, so this works even
  from `file://`; if a different endpoint blocks CORS, serve the folder over http
  (`python -m http.server`) and reopen.

### Loading the graph into Neo4j
```bash
depgraph cypher <project-root> --project drydocs --profile base -o load.cypher
# then run load.cypher's 3 statements (constraint, nodes, edges) against the DB.
```
On **Aura single-instance** you can't `CREATE DATABASE depgraph` — load into the default db
(the instance id) and the `CodeFile`/`DEPENDS_ON` meta-graph coexists with the domain graph
(distinct labels, no overlap). You can also visualize natively in the **Aura Console → Query**
tab: `MATCH p=(:CodeFile)-[:DEPENDS_ON]->(:CodeFile) RETURN p`.

> NVL (`@neo4j-nvl/base`) is the native lib but needs a build and is licensed for Neo4j-backed
> apps — `viewer.html` (cytoscape, MIT) stays the zero-friction option, now with a live mode.

## Housekeeping

- Snapshots are committed so the structural history is diffable. **Prune** old ones periodically
  to keep the repo lean (keep e.g. the last ~10 + one per milestone).
- Baseline: `depgraph.20260621-091057.json` — 49 files, 70 import edges, 0 circular.
