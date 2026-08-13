# depgraph snapshots — post-push code-structure comparison

**Run after each push.** Generate a timestamped snapshot of the code dependency graph so
structural drift (added/removed files or import edges) is visible over time — compare each
snapshot to the previous one.

The tool is [`depgraph`](../../../depgraph) (a stdlib-only Python sibling repo that maps a
project to a Neo4j-style dependency model + machine-first JSON).

## Command (after `git push`)

```powershell
.\snapshot.ps1            # -> drydocs-YYYYMMDD.json      (DEFAULT: the full repo file tree)
.\snapshot.ps1 -CodeOnly  # -> drydocs-code-YYYYMMDD.json (legacy comparison shape: the 7 package roots, .py only)
```

**It reports CI before it writes (Idea-111).** Immediately before the snapshot, the script runs
`gh run list --branch main` and prints the conclusion of the run **for HEAD's own sha** — so
"GREEN" means green at what you just pushed, never green at somebody else's older commit. It is
**warn-only** and never blocks the snapshot; if `gh` is missing or unauthenticated it says so and
carries on. The reason it is a script step rather than a habit: CI blocks on `ruff check` and
`ruff format --check` (J10 stage 5) and ran red for a week (2026-08-05 → 08-12, 100+ consecutive
failing runs) while the unit suite stayed green, so nothing local ever looked wrong.

[`snapshot.ps1`](snapshot.ps1) runs depgraph and writes `<project>-<date>.json` with a **`meta`
header** so each snapshot is self-identifying:

```jsonc
"meta": {
  "project": "drydocs", "captured_at": "...", "date": "YYYYMMDD",
  "scan": ["DryDocs"], "tree": true,        // default: one root = the repo; -CodeOnly lists the 7 package roots, tree: false
  "git": { "commit": "<short>", "full": "...", "branch": "main",
           "describe": "...", "subject": "...",
           "dirty": false, "untracked_present": false, "pr": <num|null> },
  "depgraph": { "commit": "<short>", "full": "...", "branch": "main",
                "dirty": false, "untracked_present": false, "version": "0.1.0",
                "capabilities": { "multi_root": true, "tree": true } }
}
```

**`dirty` counts TRACKED changes only; untracked paths are reported separately** (U15).
The two answer different questions. `dirty` is the provenance one — do tracked files differ
from `HEAD`, i.e. does the commit named in this header actually describe the code that was
measured? `untracked_present` is housekeeping. Until 2026-08-09 a single `git status
--porcelain` covered both, so the 20260805 snapshot recorded `dirty: true` at exactly the
pinned commit with three untracked scratch paths as the entire "dirt" — which states the
opposite of the truth to anyone reading the header. `dirty` keeps its name rather than
becoming `dirty_tracked`: it is loaded onto `:Project` as `git_dirty` and the whole committed
series carries it; what changed is that it now means what its readers already assumed.
On the **instrument** side `untracked_present` is closer to provenance than housekeeping —
`depgraph` runs out of that checkout, so an untracked module there is code that can join the
scan while belonging to no commit. Both the capability refusal and the drift warning print
the two states separately for that reason.

**`git` is what was measured; `depgraph` is what measured it** (U7). Both matter, because the
scan runs in a *sibling repo* whose checked-out revision decides what the snapshot can see —
until 2026-07-28 the header pinned the subject precisely and said nothing about the instrument,
which is how a scanner regression became invisible. Before scanning, `snapshot.ps1` runs
[`probe_instrument.py`](probe_instrument.py) and **refuses** (exit 1, no file written) when the
checkout cannot do what the run needs: multi-root resolution always, `--tree` additionally for
`-Tree`. The probe is **behavioural, never a version string** — depgraph's `0.1.0` spans both
the broken and the fixed resolver, so a version says nothing; only what the code can *do* is
decisive. (depgraph was a fork with two divergent branches until 2026-07-28, when both were
merged into `main` and deleted; `main` is now the only branch and carries every capability.)
Expected
revision and required capabilities live in [`config/dev-environment.yaml`](../../config/dev-environment.yaml);
`tests/unit/test_probe_instrument.py` fails if this machine's instrument has regressed.

`pr` is best-effort (parsed from recent commit subjects/bodies — `pull request #N`, `(#N)`).
The header is **prepended** to depgraph's JSON without reformatting (clean diffs, no BOM), and
`viewer.html` shows `@<commit> (branch) PR#<n>` in its stats. **The full tree is the default**
(SME direction, U9): one scan root — the repo — so there is no root list to go stale, and the
`.cypher` a loader executes, the `.sql` an extractor runs and the `.yaml` a module reads are all
visible instead of Python-only. `-CodeOnly` is the retired roots-only shape (the six `drydocs*`
package roots plus `tests/`, one invocation, shared namespace — see the discontinuity note under
**Compare**), kept for comparison against the pre-2026-08-02 series; it writes a different
filename so the two shapes can never collide. The `scan` list in each header is the authority
for what a given snapshot actually covered — read it before comparing two of them.

Three post-processing steps run between scan and write. **U7** — the instrument probe above.
**U8** — machine-absolute `abs_path` is stripped textually before writing (and the script refuses
to write if any survive), so snapshots from different machines or agent worktrees are comparable.
**U9** — git-ignored paths are dropped ([`filter_ignored.py`](filter_ignored.py)): depgraph
excludes `.git`/`.venv` but knows nothing about `.gitignore`, and the first all-files run
collected 384 `.ruff_cache` entries (~18% of the artifact) before the filter existed. The
committed JSON, `viewer.html` and the graph all show the same filtered thing.

## Compare

Each snapshot's summary line reports `files`, `edges`, `circular_files`. To see what changed:
- **Open [`viewer.html`](viewer.html)** in a browser — load a snapshot in **A**, a second in **B**;
  it renders the graph (cytoscape.js, MIT, CDN — no build) and colors the diff
  (green = added in B, red = removed, grey = unchanged). Views: directory **Structure**,
  Structure+files, or **Dependencies** (Python imports). Compares by project-relative path,
  so different projects (e.g. `drydocs-original` vs `drydocs`) align.

> **Historical note:** every snapshot older than the newest lives in **git history, not the
> working tree** (the ruled retention — see Housekeeping). Snapshots captured before 2026-07-01
> were named `drydocs1-*.json` (the project's original name); the record is preserved in
> history under those names. New snapshots follow the `drydocs-<date>.json` convention.
> The instrument-change markers below cite historical filenames — recover any of them with
> `git log --all --oneline -- knowledge/depgraph-snapshots/<name>` + `git show <commit>:<path>`.

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
> not comparable at all. (Two snapshots were kept for 2026-07-28 rather than the usual
> one-per-day because the fix landed mid-day; the bare-date `drydocs-20260728.json` from that
> morning was **deleted** — it undercounted *and* its commit message asserted "no structural
> drift" on numbers taken from the blind region.)
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

> **⚠ Instrument change — every node gains `"kind"` after 2026-07-28 12:39.** Consolidating the
> depgraph fork onto `main` brought the file-tree branch's `FileNode.kind` with it, so nodes now
> carry `"kind": "file"` (or `"dir"` in a `-Tree` scan). Purely **additive** and verified so: the
> same code scanned before and after the merge produced identical `file_id` sets, byte-identical
> edges, and identical `stats` — the *only* change was the new field. The G33 loader reads
> field-by-field and ignores it. But because it lands on every node at once, the first diff
> across this boundary again shows all nodes changed. Third marker in a day, same lesson: read
> `meta.depgraph` before concluding anything from a node-level diff.

> **⚠ Instrument change — the ALL-FILES tree became the default on 2026-08-02 (U9, `e3f65af`).**
> The ritual snapshot stopped being a Python-roots code graph and became the whole repo: every
> directory, every non-`.py` file, plus `CONTAINS` edges read from the tree instead of guessed
> from path strings. On unchanged code the node count goes **238 → 1457**. That is not growth —
> it is the instrument seeing the `.cypher`, `.sql`, `.yaml`, docs and config that were always
> there and always invisible. The old shape survives as `-CodeOnly` under its own
> `drydocs-code-*` filename; `meta.tree` discriminates the two, and a tree snapshot is **not
> comparable** to a roots-only one at the node level at all — compare `meta.scan`/`meta.tree`
> first, same lesson as the three markers above.

> **⚠ Instrument change — first-party TS/JS import edges appear after 2026-08-06 (O42,
> depgraph `a56d2fc`).** The scanner gained a `ts-imports` extractor (default-on, same
> shape as `python-imports`): relative-specifier resolution over `.ts/.tsx/.js/.jsx`,
> bare specifiers stay third-party, asset imports drop. On unchanged code the edge
> count jumps **549 → ~775** — that is the front end's ~226 import edges becoming
> visible, not growth, and an edge diff across this boundary shows every `web/src`
> dependency as "added". `meta.depgraph.capabilities.ts_imports` discriminates: a
> snapshot without the key (or `false`) was scanned by a TS-blind instrument. Same
> lesson as every marker above — read `meta.depgraph` before concluding anything
> from a cross-boundary diff.

> **⚠ Instrument change — `scripts/` and `agents/` gain internal import edges after
> 2026-08-09 (U19, depgraph `6ee0af6`).** The extractor now resolves bare-name imports
> against the **file's own sys.path root** — the directory Python itself would put on
> the path (walk up while `__init__.py` is present; the first ancestor that is not a
> package is the root). Before it, `scripts/render_board.py`'s `import render_gates` and
> `agents/graph_qa/*`'s `from common import …` resolved to nothing, so both regions
> recorded **zero** internal edges. Measured on this desktop across the bump: **830 → 878**
> edges, of which `scripts→scripts` **0 → 7** and `agents→agents` **0 → 20**. The
> package-scope metrics are unmoved (A3 top-15 identical, A4 0, A5 29) because packages
> already resolved through the repo root — this boundary is visible only outside them.
> What it *does* move is the first-party orphan queue: **22 → 4**, with `agents/` going
> 15 → 0, so roughly four in five of that queue was a scanner artifact rather than dead
> code. The change is additive by construction (the extra root is appended after the
> project roots, pinned by a test), so no edge that already resolved was moved.

- or diff the two `.json` files (`git diff` / any JSON diff tool), or watch the summary counts.

### Seeded comparison — the v1 rewrite (original vs this version)
A pair of tree snapshots once seeded this comparison; **both are history now, recoverable from
git, not files in this directory**: `tree-original.json` (full tree at commit `683322c`,
pre-rewrite — 494 files / 103 dirs, has `vendor/`) and `tree-this-version.json` (v1 —
540 files / 124 dirs; adds `reference/ external/ config/ internal/`, the four layers, with
`vendor/` → `external/orchestration/bmc-controlm`). To re-run the comparison, recover them from
history (see the Historical note above) and load the pair in the viewer.

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

- **Ruled retention (SME 2026-08-02, enforced by `snapshot.ps1` since U12): the newest
  all-files snapshot is the ONLY one in the directory.** The script deletes every older
  `<project>-<date>[-HHmm].json` after a successful write — no human pruning step, because the
  human step is what failed: the ruling was applied by hand four times in the two days after it
  was made, and a 101-file series accumulated once before it. Structural history stays fully
  diffable — every superseded snapshot is in **git history** (see the Historical note under
  Compare for the recovery commands). `-CodeOnly` comparison files (`drydocs-code-*`) are exempt.
- Historical baseline: `drydocs1-20260621.json` — 49 files, 70 import edges, 0 circular — is in
  git history, not this directory. (Filename corrected 2026-07-28: this line once said
  `depgraph.20260621-091057.json`, which never existed; the counts were right. Being pre-U6 it
  undercounts edges like everything before 2026-07-28 08:48 — see the instrument-change note
  above.)
