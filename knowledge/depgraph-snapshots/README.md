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
- diff the two most recent `.json` files (committed → `git diff`; or any JSON diff tool), or
- watch the summary counts (a jump in `edges` or any `circular_files > 0` is worth a look).

## Housekeeping

- Snapshots are committed so the structural history is diffable. **Prune** old ones periodically
  to keep the repo lean (keep e.g. the last ~10 + one per milestone).
- Baseline: `depgraph.20260621-091057.json` — 49 files, 70 import edges, 0 circular.
