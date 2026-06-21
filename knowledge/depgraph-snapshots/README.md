# depgraph snapshots — post-push code-structure comparison

**Run after each push.** Generate a timestamped snapshot of the code dependency graph so
structural drift (added/removed files or import edges) is visible over time — compare each
snapshot to the previous one.

The tool is [`depgraph`](../../../depgraph) (a stdlib-only Python sibling repo that maps a
project to a Neo4j-style dependency model + machine-first JSON).

## Command (after `git push`)

```powershell
$ts  = Get-Date -Format "yyyyMMdd-HHmmss"
$out = "C:\coding\projects\sandbox\DRYDOCS\knowledge\depgraph-snapshots\depgraph.$ts.json"
Set-Location C:\coding\projects\sandbox\depgraph
$env:PYTHONPATH = "."
python -m depgraph.cli scan `
  C:\coding\projects\sandbox\DRYDOCS\drydocs `
  C:\coding\projects\sandbox\DRYDOCS\tests `
  --project drydocs1 -o $out
```

Focused scan = `drydocs/` (the package) + `tests/` — the project's own code. For a full
file-tree snapshot (noisier; includes `.claude/skills`), scan the repo root with `--tree`.

## Compare

Each snapshot's summary line reports `files`, `edges`, `circular_files`. To see what changed:
- **Open [`viewer.html`](viewer.html)** in a browser — load a snapshot in **A**, a second in **B**;
  it renders the graph (cytoscape.js, MIT, CDN — no build) and colors the diff
  (green = added in B, red = removed, grey = unchanged). Views: directory **Structure**,
  Structure+files, or **Dependencies** (Python imports). Compares by project-relative path,
  so different projects (e.g. `drydocs-original` vs `drydocs1`) align.
- or diff the two `.json` files (`git diff` / any JSON diff tool), or watch the summary counts.

### Seeded comparison — the v1 rewrite (original vs this version)
- `tree-original.json` — full tree at commit `683322c` (pre-rewrite): 494 files / 103 dirs, has `vendor/`.
- `tree-this-version.json` — current v1: 540 files / 124 dirs; adds `reference/ external/ config/ internal/`
  (the four layers), `vendor/` → `external/orchestration/bmc-controlm`.
- Load both in the viewer (A = this-version, B = original, or swap) to see the restructure.

> Neo4j path (alternative): `depgraph cypher --from <snapshot>.json -o load.cypher`, load into Neo4j,
> and visualize in Neo4j Browser / Bloom. NVL (`@neo4j-nvl/base`) is the native lib but needs a
> build and is licensed for Neo4j-backed apps — `viewer.html` is the zero-friction option.

## Housekeeping

- Snapshots are committed so the structural history is diffable. **Prune** old ones periodically
  to keep the repo lean (keep e.g. the last ~10 + one per milestone).
- Baseline: `depgraph.20260621-091057.json` — 49 files, 70 import edges, 0 circular.
