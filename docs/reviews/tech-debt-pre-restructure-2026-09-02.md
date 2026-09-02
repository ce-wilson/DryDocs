# Tech-debt review — the whole repo, before the restructure

**Date:** 2026-09-02 · **Trigger:** `/tech-debt` — a detailed review of the current project so
it can be remediated as necessary before the backlog/edition restructure (gate
`ontology-domain-registry-and-edition-grain`, items CFG1 CFG2 PLAN2 DOC1 DOC2 REF1 ONT1 ONT2,
and ADR 0015 Team Edition behind them).
**Method:** the `/tech-debt` framework — six categories, each item scored
`(Impact + Risk) x (6 - Effort)` on 1–5 scales; graph evidence from the A1–A6 query pack on a
FRESH code graph; two parallel surveys (test/dependency/CI and documentation/backlog) whose
sharpest claims were re-verified by hand before they appear here. Every finding cites where it
was read. Findings route through the IDEAS inbox (Idea-243 .. Idea-249), never directly into
the backlog.
**Classification:** Internal-Public (mechanism only; no org values, no edition names).
**House rules carried from the three earlier tech-debt reviews:** rendered `.html` and
generated JSON are deterministic outputs, not duplicated-doc debt; `internal/` exclusions are
the publish boundary working as designed; gate-bound `status: planned` entries are deliberate;
trivial, unambiguous fixes are EXECUTED with the review and marked so.

- **Reviewed at:** commit `7fe46e6b` on `main`, port base `port-base-20260901`; venue MSI.
  *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*

---

## 0. Verdict, in one paragraph

The codebase is in better shape than a 1,885-commit, 54k-LOC-plus-54k-test-LOC repo usually is:
the unit suite is green (3,067 passed / 9 skipped, 4m07s), ruff is clean, the core layer imports
nothing upward (A1 = 0), no component imports another except through the declared entrypoint,
package-scope dead code is 0, measured coverage is 90%, committed renders match their sources,
and CI has been green for the last ten runs. The debt is concentrated in four places, and three
of them bear directly on the restructure: **(1) the self-measurement is untrustworthy** — the
metrics ledger has recorded a STALE graph in 51 of its 52 rows, the A2 baseline moved 0 → 5 on
2026-08-23 and nothing noticed, and running the repo's own coverage tool fails a repo guard;
**(2) the physical layout does not match the logical one** — five components are lists of
module names inside one package, the `port` group has no backlog module, and five top-level
directories are named in no routing document, which matters the moment ADR 0015 assigns every
path a file class; **(3) the routing docs lag the code** — `git-readme.md` names 31 paths that
moved at the 0002-A extraction, and the narrative project plan stops at phase 5 of 18; **(4)
process state has drifted** — five `in_progress` claims from one 08-20/21 burst with no work
behind them, 14 unsigned gate prompts, a Ready strip that lists 85% of the backlog. None of it
blocks the restructure. Items P1, T1, D3, Doc1 and A1's cheap slice should land before it,
because the restructure will rely on exactly the instruments and declarations they repair.

---

## 1. Evidence — the graph (query pack A1–A6)

**Step 0 (U22):** `code graph: STALE by 12.3 day(s) — last loaded 2026-08-21T11:38:06Z`.
Refreshed with `drydocs load-code-snapshot` (run `fd00c314`, snapshot
`drydocs-20260902-1353.json`, captured 2026-09-02T18:53:59Z) and re-checked: **FRESH**. Every
number below is from the fresh graph. Note the `SchemaMeta` label does not exist in this
database (Neo4j warned on every query) — the O33 exemplars are not loaded here, so the guard
is inert but harmless.

**Step 0b (U25):** the ledger delta `@3123eb1 -> @fb310c0` reads "A3 loaders/base.py=37 -> 37;
A4 0 -> 0 / first-party 7 -> 7; A5 31 -> 31; freshness stale -> stale". Those numbers were
measured on the stale graph — see P1. The fresh readings differ:

| # | Category | Baseline (last recorded) | Fresh reading 2026-09-02 | Verdict |
|---|---|---|---|---|
| A1 | Architecture — core importing upward | 0 | **0** | clean |
| A2 | Code — circular imports | 0 (both probes) | **5** by both probes (`drydocs/cli.py`, `drydocs/cli_shared.py`, `drydocs_core/data_root.py`, `drydocs_core/data_zones.py`, `drydocs_core/landing_zones.py`) | finding C1 |
| A3 | Code — fan-in hotspot | `loaders/base.py` = 37 | **`drydocs_core/repo_paths.py` = 43**, `loaders/base.py` = 37, `drydocs_core/__init__.py` = 29, `drydocs_lineage/model.py` = 26, `drydocs_core/models/__init__.py` = 24, `neo4j_client.py` / `cli.py` / `run_log.py` = 23 | the top module changed and the ledger did not see it (P1) |
| A4 | Code — dead-code candidates, package scope | 0 | **0** | clean |
| A4 | first-party queue (`agents`, `scripts`, `knowledge`) | 4 | **7** — the earlier four plus `scripts/doctor_scan.py`, `scripts/render_benchmark_data.py`, `scripts/review_stamp.py`; all subprocess-invoked entry points | zero dead modules |
| A5 | Test — modules no test imports | 31 (stale) | **27** (list in §2 T2) | improving; the CLI modules dominate |
| A6 | Architecture — cross-root coupling | — | component → component edges: **5, all from `drydocs/cli.py`** (to `drydocs_lineage` ×3, `drydocs_remediation` ×2), the declared entrypoint (`test_module_boundary.py:218`); `scripts` → packages 38 edges; `agents` → `drydocs_api` 2 (declared, `:231`) | clean by the declared rules |
| — | tombstones | — | 90 nodes carry `removed_from_source_at` | filters applied |

---

## 2. Findings by category

Scores: I = Impact on the team's speed, R = Risk if left, E = Effort to fix (1 = an hour,
5 = an epic). Priority = (I + R) x (6 - E).

### Code debt

**C1 — Three core modules are a cycle, and the A2 baseline moved without anyone noticing.**
`drydocs_core/data_root.py:142` imports `data_zones` inside a function; `data_zones.py:44`
imports `data_root` at module scope and `landing_zones` at `:237`; `landing_zones.py:46`
imports `data_root`. Introduced at G81 (`701e1d22`, 2026-08-23). The cycle is broken by
function-level imports, which is why nothing fails — and why the skill's A2 baseline of 0 has
read 5 for ten days with no record: the metrics ledger has no A2 column. The other pair
(`cli.py` ↔ `cli_shared.py:736`) is the documented S13 seam and is not debt. I 2 · R 3 · E 2
→ **20**. *Fix:* fold the zone-containment lookup `data_root` needs into a module below both
(or pass it in), and add `a2_circular` to the ledger row so the baseline is a number the ritual
carries.

**C2 — Long functions where the operator-facing surface lives.** 18 functions of 120+ lines;
the largest is `drydocs_api/app.py::create_app` at **625 lines**, then `cli_verify.py::m3_verify`
288, `cli_schema.py::landing_zones_cmd` 265, `scripts/render_load_map.py::build_load_map_html`
265 and `build_load_map` 252, `plan_board.py::render_board` 227, `drydocs_lineage/writer.py::plan_rua`
210. These are also the lowest-covered modules (T2). I 3 · R 2 · E 3 → **15**. *Fix:* split
`create_app` into per-router registration functions (the routers already exist); the CLI
commands into a parse step and a pure step the tests can hit without Typer.

**C3 — Copied helpers that MODULE_MAP already says belong in core.** `_str_or_none` is defined
five times in `drydocs_core/models/` (`attribution.py:41`, `controlm.py:28`, `docs.py:23`,
`doc_traceability.py:37`, `seal.py:34`); `_git(*args)` five times (`drydocs/port_preflight.py:326`,
three `scripts/*`, `validate.py:161`); `as_dict` 31 times across five roots. The seven
`_client()` copies in the CLI modules are NOT this — each is a two-line shim to the root, kept
on purpose as the test-patch seam (S13). I 2 · R 1 · E 1 → **15**. *Fix:* `drydocs_core.coerce`
and `drydocs_core.git_shell`, one commit each, on the "Future, land in core" list at
`MODULE_MAP.md:174`.

**C4 — The board is 2.5 MB and it has been committed 722 times.** `docs/plan/board.html` is
2,589,944 bytes: 638 cards at ~4 KB each, because every item's full acceptance body is inlined
(`plan_board.py:214`). It has 722 commits out of the repo's 1,885, 399 unique blobs sampled sum
to 653 MB raw, and `.git` is 296 MB. The render is a governed surface (verbatim, deterministic)
and must stay committed; its SIZE is not governed. I 3 · R 2 · E 2 → **20**. *Fix:* render
each body once into a `<template id="body-<id>">` the card opens on demand, or move bodies to
a sibling JSON the page fetches — deterministic either way, and anchors (`data-id`) unchanged.

### Architecture debt

**A1 — The logical components and the physical layout disagree, and the restructure will
assign file classes by PATH.** `test_module_boundary.py:51–200` defines nine component groups;
five of them — `load`, `review`, `plan`, `port`, `docgen` — are lists of module names inside
the single package `drydocs/` (70 files, 20k LOC), and `docs_coverage`, `code_graph_freshness`,
`pat_projection`, `seal_samples` sit as flat files at the package root. Three consequences.
(a) ADR 0015 D4 promotes the manifest's dispositions to copier file classes, and PORT-MANIFEST
classifies by path glob: a component that is a list of files scattered through one directory
cannot be a file class without enumerating every file. (b) `docs/restructure/backlog/modules.yaml`
has no `drydocs-port` module and therefore no series — port work (`port_preflight`,
`port_backlog_union`, `port_rename_detect`, three of the most-edited modules in August) has no
id series under PLAN1, and nothing guards `COMPONENT_GROUPS.keys()` against `modules.yaml`.
(c) The S7 rule (`MODULE_MAP.md:21`) already rules on folder-vs-module naming but only bites
when a directory exists. I 4 · R 4 · E 4 → **16** for the move; the guard slice alone is
I 2 · R 3 · E 1 → **25**. *Fix, in two parts:* NOW, the guard — every `COMPONENT_GROUPS` key
maps to a `modules.yaml` module (add `drydocs-port`, series `PORT`), so the backlog and the
boundary test name the same components. AT THE ADR, the move — rule in ADR 0015 D2 whether
`review/`, `plan/`, `port/`, `docgen/` become subpackages (an add-new + re-export-old shape,
never a rename, because module paths are cited in `MODULE_MAP.md`, the manifest, the gate log
and 85 test files) or whether the copier classifies by an explicit module list the boundary
test exports. Do not move files before that ruling; 0002-A §7 says why.

**A2 — One declared cross-component import with an unruled follow-up.**
`agents.common.specs_catalog` → `drydocs_api` (`test_module_boundary.py:231`) records "today's
reality until that ruling is made": promoting `query_specs.py` (1,576 lines, fan-in 20) and the
read-only guard into `drydocs_core`. Still unruled. I 2 · R 2 · E 3 → **12**. *Fix:* rule it
on the same ADR pass as A1; the module already passes the placement test if its Cypher text is
data.

**A3 — Five top-level directories are named in no routing document.** `SDLC-Docs/` (6 files,
untouched since the squash floor, capitalized against the repo's own norm), `graph-tests/` (7),
`drydocs-icons/` (71), `libs/` (4, two MODULE_MAP mentions), `knowledge/upgrade-plans/` (17):
none is referenced from `CLAUDE.md` or `README.md`. PORT-MANIFEST's totality detector keeps
them from falling through silently at a port, but ADR 0015's copier will need a class for
each, and "nobody knows what this is" is the class it will get. I 2 · R 2 · E 1 → **20**.
*Fix:* one MODULE_MAP "Non-Python surfaces" row each, or a retirement — `SDLC-Docs/` (the 2018
genesis document the design review cites) should be either registered under `reference/` with
its classification or moved to `docs/history/`.

### Test debt

**T1 — EXECUTED: `.gitignore` had no `.coverage*` entry, so measuring coverage failed a repo
guard.** With `--cov`, `test_port_reconcile_guards.py::test_no_tracked_path_falls_through_silently`
fails on 34 `.coverage.MSI.pid*` files ("resolve to PORT-MANIFEST default: with nothing written
down"). I 3 · R 2 · E 1 → **25**. Fixed with this review (`.coverage*`, `htmlcov/`).

**T2 — Coverage is 90% overall and 12–28% where operators touch the tool.** `pytest-cov ^5.0`
is a dev dependency with no `[tool.coverage]` block, no `.coveragerc`, and no CI step.
Measured: 19,083 statements, 1,939 missed. The six S8 command modules plus `cli.py` are **42%
of every missed statement**: `cli_variables.py` 12%, `cli_verify.py` 14%, `cli_docs.py` 22%,
`cli.py` 28%, `cli_ingest.py` 43%, `cli_plan.py` / `cli_schema.py` 64%. The A5 list says the
same thing from the graph: 27 modules no test imports, and five of them are the CLI
(`cli_ingest`, `cli_plan`, `cli_shared`, `cli_variables`, `cli_verify`), plus `publishing/*`
(3), `snapshots/*` (2), `drydocs_core/models/{attribution,controlm,infrastructure}.py`,
`orchestration/controlm/{audit_time,conditions,variable_report,xml_vocab}.py`, and three
lineage extractors (`controlm_xml`, `dpl_registry`, `rua_code_ops`). `drydocs --help` is one of
the three CLAUDE.md §6 gates, and it proves the modules import, not that the verbs work.
I 3 · R 3 · E 3 → **18**. *Fix:* a `[tool.coverage.run]` block (`source`, `omit` the vendored
skills), a CI `--cov` step that REPORTS (no threshold yet — a threshold set today is a number
nobody chose), then the C2 split so the CLI's pure halves are testable; re-baseline A5 in the
ledger.

**T3 — `mypy` is declared and has never run.** `pyproject.toml:34` is its only mention: no
config, no CI step, no local invocation, across 54k lines that carry type annotations
everywhere. I 2 · R 2 · E 4 → **8** to wire it fully. *Fix:* decide, do not drift — either
remove the dependency (honest) or add `[tool.mypy]` with `drydocs_core` as the only checked
package and grow outward, because core is the stable surface the components and the company
port both consume.

**T4 — The integration tier never runs in CI.** `addopts = "-ra --strict-markers -m 'not
integration'"` deselects `tests/integration/` (5 testcontainers/Neo4j modules) and
`.github/workflows/ci.yml` runs bare `poetry run pytest -q`. "Testcontainers e2e (J9) live on
main" means live on a developer machine, on demand. I 3 · R 3 · E 3 → **18**. *Fix:* a fourth
CI job, `integration`, on a schedule (nightly) or on `main` only, with Docker; it does not need
to gate PRs to catch a loader regression within a day.

**T5 — EXECUTED (prune): a leaked, LOCKED pytest worktree; and the four slowest tests are
31 s of 247 s.** `git worktree list` carried
`Temp/pytest-of-chade/pytest-2196/test_a_worktree_render_does_no0/wt` at detached `81341df5`,
locked, which `git worktree prune` refuses to drop. Pruned with `--force` here. The
worktree/tree-walk tests (`test_repo_paths.py` 11.3 s + 5.9 s, `test_data_root.py` 8.8 s,
`test_publish_boundary_values.py` 5.6 s) are the cost of testing against the real tree; the
leak says one of them does not always clean up. I 2 · R 1 · E 2 → **12**. *Fix:* a `finally`
that unlocks before removing in the worktree fixture; consider `-p xdist` for the rest.

**T6 — A deprecation past its named trigger.** ADR 0014 clause 1 (`0014-runtime-substrate.md:195`)
keeps `SPIDERP_LOGDIR` one cycle with the drop trigger "the next port after this ADR is
accepted". Two ports have rolled since (2026-08-26, 2026-09-01); the alias still resolves
(`run_log.py:51`, `log_kinds.py:124`) and emits most of the suite's 521 warnings (the rest is
neo4j 5.x's `asyncio.iscoroutinefunction` under Python 3.14, D3). I 1 · R 2 · E 1 → **15**.
*Fix:* drop the alias; the ADR says when and the when has passed.

### Dependency debt

**D1 — Five high-severity npm advisories with no non-breaking fix.** `npm audit --omit=dev`:
`js-cookie <= 3.0.5` (GHSA-qjx8-664m-686j) reached through `@segment/analytics-next` ←
`@neo4j-nvl/base` ← `@neo4j-nvl/react`, in production `dependencies`. `npm audit fix --force`
downgrades `@neo4j-nvl/base` to 1.0.0. Also: both `@neo4j-nvl` packages report `MISSING` in the
local `node_modules` — declared, not installed here. I 2 · R 4 · E 3 → **18**. *Fix:* a
decision — pin an override (`overrides: { "js-cookie": ">=3.0.6" }`) if NVL tolerates it, or
drop the analytics path; then `npm ci` so the local install matches the lockfile.

**D2 — Major-version drift is now a cluster.** `poetry show --outdated`: 36 behind; direct and
major: neo4j 5.28 → 6.3, oracledb 2.5 → 4.0, pandas 2.3 → 3.0, typer 0.12 → 0.27, rich 13 → 15,
pytest 8 → 9, pytest-cov 5 → 7, mypy 1 → 2; `click < 8.2` is a deliberate cap; `ruff = 0.5.7`
is the documented J10 pin (`docs/ruff-format-convergence.md`). Nothing abandoned. I 2 · R 3 ·
E 4 → **10**. *Fix:* stage by blast radius after D3 lands — pytest/pytest-cov first (test-only),
rich/typer together (the CLI, T2 makes this safer), neo4j 6 last and behind an integration run
(T4), oracledb when a live connection exists to prove it.

**D3 — Three Python versions, one tested.** `pyproject.toml:11` says `^3.11`; CI tests 3.12
only; this desktop runs 3.14.6 and produces the neo4j asyncio deprecation warnings CI never
sees. I 3 · R 3 · E 1 → **30**. *Fix:* a `strategy.matrix` of 3.11 / 3.12 / 3.14 on the
`gates` job, fail-fast off — the cheapest high-value change in this review.

**D4 — Poetry metadata on a deprecated schema.** `poetry check --lock` passes with six
deprecation warnings: `[tool.poetry.{name,version,description,readme,authors}]` and
`[tool.poetry.scripts]` should be PEP 621 `[project]`. A future Poetry major turns them into
errors on the company side first (they install last). I 1 · R 2 · E 1 → **15**.

### Documentation debt

**Doc1 — `git-readme.md` is a routing document for the port and it routes to the old
layout.** 31 backticked paths that do not exist: `drydocs/controlm/*.py`, `drydocs/models/*.py`,
`drydocs/schema/*.cypher`, `drydocs/ontology/*` (all moved to `drydocs_core/` at 0002-A),
`config/taxonomy-ontology-map.yaml` and `relationship_vocabulary.yaml` (both now directories),
`config/source-mappings/controlm-psgmgr.yaml`, `graph-tests/vendor-bmc-smoke.yaml`,
`config/gate-prompts/vendor-bmc-example.yaml`. The design review already retires its
`:196–201` sentence through PLAN2; the rest of the file needs the same sweep. I 3 · R 3 · E 2
→ **24**. *Fix:* a path sweep with a guard — `test_docs_paths.py`-style: every backticked
repo-relative path in the four routing docs (`CLAUDE.md`, `MODULE_MAP.md`, `git-readme.md`,
`internal/repo-README.md`) resolves, on the L19 pattern.

**Doc2 — The narrative plan covers 6 of 18 phases.** `docs/restructure/01-project-plan.md`
(last touched 07-22) stops at phase 5 "Orchestrator expansion"; `backlog/plan.yaml` runs to
phase 17 "Mind-map — deepdoc leaves the placeholder". CLAUDE.md's last line still points
readers at it for "the plan". I 3 · R 2 · E 2 → **20**. *Fix:* either render the phase
narrative from `plan.yaml` (the roadmap already does the table; the prose per phase is a
field away) or cut `01-project-plan.md` to the parts `plan.yaml` cannot hold and link the
roadmap.

**Doc3 — 79 broken relative links in 38 files; zero publish-boundary leaks.** 12.7% of the
622 relative links in 596 tracked `.md`. Two clusters: 11 vendor-boilerplate skills each link
`../../CONNECTORS.md`, a file that never existed here; and `internal/` remediation docs (12 in
`internal/repo-README.md`, 11 in `standards-rules-registry.md`). No link from outside
`internal/` points into `internal/` or `internal-local/`. I 2 · R 1 · E 2 → **12**. *Fix:*
the same link guard, warn-only outside the routing docs.

**Doc4 — The always-loaded guidance is ~15k tokens and MODULE_MAP names seven moved paths.**
`CLAUDE.md` 26.7 KB (~6.7k tokens) plus `MODULE_MAP.md` 32.6 KB (~8.1k tokens; 177 lines, so
each row is a paragraph) load before any work starts. MODULE_MAP cites
`relationship_vocabulary.yaml` (now a directory), `controlm/commands.py`, `controlm/staging.py`,
`review_cli.py`. I 2 · R 2 · E 2 → **16**. *Fix:* the Doc1 guard covers the paths; the size
is a `/doctor` question (move the per-row history into `docs/history/`, keep the table).

**Doc5 — `IDEAS.md` is 7,146 lines and half of it is history.** 245 idea lines, 126 under
`## Inbox`; `## Recently groomed` starts at line 3,513. One placeholder-shaped entry
(`Idea-N`, from the capture-format example, dated 07-22) sits in the inbox as if real.
I 2 · R 1 · E 2 → **12**. *Fix:* shard the groomed trail to `ideas/archive-<yyyy-mm>.md` (the
0013 shape the backlog already took); delete the placeholder.

### Infrastructure and process debt

**P1 — The self-measurement instrument records a stale graph 51 times in 52.**
`debt-metrics.jsonl`: 52 rows, 51 `freshness: stale`. `snapshot.ps1` writes a new snapshot,
calls `code-graph-freshness` (warn-only), then `metrics_ledger.py` — which measures the LIVE
graph (`metrics_ledger.py:106–110`) that nothing in the ritual has loaded. So the ledger's A3
top module has read `loaders/base.py = 37` while the fresh graph says `repo_paths.py = 43`, and
its A5 read 31 against a fresh 27. The ledger has no A2 column, so C1's move was invisible
twice over. I 3 · R 3 · E 2 → **24**. *Fix:* compute A3/A4/A5 from the snapshot JSON the
ritual just wrote (the skill's own offline fallback already says how; the snapshot is the live
tree by construction) and keep the live-graph column as the drift comparison it was meant to
be; add `a2_circular` from `stats.circular_files`. Then a row can never be stale about itself.

**P2 — Five `in_progress` claims from one burst, twelve days old, with no work behind them.**
E1, G62, K16, L19, MM7 — claimed 2026-08-20/21, none closed, and `git branch -r --list "*wip/*"`
returns nothing (J31's test). Per the pull rule they hold the pen on five items and keep them
off the Ready strip. I 3 · R 2 · E 1 → **25**. *Fix:* confirm the laptop holds no unpushed
work on them (the K9 case is the one J31 cannot see), then release each to `todo` with a note
naming this review; N14 (5 d) stays.

**P3 — Fourteen gate prompts await sign-off and ~40 prompt files have no schema test.**
`config/gate-prompts/` holds 58; `config/gate-log.md` has 96 records; 14 prompt stems have
zero mentions in the log (`bmc-docs-example`, `business-layer-org-structure`,
`code-graph-package-layer`, `console-auth-boundary`, `controlm-definition-precedence`,
`data-flow-overview`, `dcat-theme-subject-scheme`, `document-supersession`,
`dpl-dataset-identity-zone`, `dpl-dataset-registry-contract`, `dpl-pipeline-registry-contract`,
`registry-wiring-readiness`, `repo-manifest-data-profile`, `script-provenance-gaps`). The
SME's cadence is the SME's; the debt is that a malformed prompt fails at the session, not in
CI: 61 of 104 `config/**/*.y*ml` have no test reference, most of them prompts. I 3 · R 3 · E 2
→ **24**. *Fix:* one shape test over every gate prompt (the fields the gate-page renderer
reads), and the 14 listed on the gate queue page so the count is visible rather than derived
by hand.

**P4 — The Ready strip is 85% of the backlog.** `next_ready = 124` of `todo = 146`. Dependency
edges do almost no sequencing, so "take the next ready item" is "take any item". I 2 · R 2 ·
E 3 → **12**. *Fix:* a grooming pass per epic that declares the real order (the eight
restructure items are the model: a chain, not a bag); five fully-closed epics (`cdo-alignment`,
`ddlineage-retirement`, `orchestrator-expansion`, `provenance-audit`, `taxonomy-capture`)
marked closed so the board stops rendering them open.

**P5 — CI has no timeouts, no pre-commit hook, and a security job that may be a no-op.**
`ci.yml`: no `timeout-minutes` on any of three jobs; ruff runs only on the runner (no
`.pre-commit-config.yaml`), which is the mechanism behind the 100-run red streak Idea-111
records; the `snyk` job skips every step when `SNYK_TOKEN` is unset, and the repo cannot
say whether it is set. I 2 · R 2 · E 1 → **20**. *Fix:* `timeout-minutes: 20` per job; a
pre-commit config with the two ruff hooks; a one-line CI notice when snyk skipped.

**P6 — Merged branch and squash-floor blindness.** `feat/backlog-series-by-module` is merged
(`c24ce720`) and still exists local and remote — checked out in
`.claude/worktrees/ui-workstream`, so deletion is the user's call. And a caveat the surveys
carry: history was squashed to a 2026-07-20 root, so every git-derived "older than N days"
metric is capped at 44 days and proves nothing; staleness has to be measured from content
(Doc1's guard), not dates. I 1 · R 1 · E 1 → **10**.

---

## 3. Prioritized list

| Rank | Id | Item | I | R | E | Priority | Status |
|---|---|---|---|---|---|---|---|
| 1 | D3 | Python version matrix 3.11 / 3.12 / 3.14 in CI | 3 | 3 | 1 | 30 | Idea-245 |
| 2 | T1 | `.coverage*` in `.gitignore` | 3 | 2 | 1 | 25 | **EXECUTED** |
| 2 | A1a | Guard: every boundary component group maps to a `modules.yaml` module; add `drydocs-port` / `PORT` | 2 | 3 | 1 | 25 | Idea-244 |
| 2 | P2 | Release the five dead 08-20/21 claims after the laptop check | 3 | 2 | 1 | 25 | user ruling |
| 5 | P1 | Metrics ledger measures the snapshot it just wrote; add A2 | 3 | 3 | 2 | 24 | Idea-243 |
| 5 | Doc1 | `git-readme.md` path sweep + routing-doc path guard | 3 | 3 | 2 | 24 | Idea-247 |
| 5 | P3 | Gate-prompt shape test + the unsigned-14 on the queue page | 3 | 3 | 2 | 24 | Idea-248 |
| 8 | C1 | Break the `data_root` / `data_zones` / `landing_zones` cycle | 2 | 3 | 2 | 20 | Idea-243 (rides with P1) |
| 8 | C4 | Board bodies rendered once, on demand | 3 | 2 | 2 | 20 | Idea-249 |
| 8 | A3 | Classify or retire the five unrouted top-level dirs | 2 | 2 | 1 | 20 | Idea-244 |
| 8 | Doc2 | Phase narrative from `plan.yaml` | 3 | 2 | 2 | 20 | Idea-247 |
| 8 | P5 | CI timeouts, pre-commit ruff, snyk-skipped notice | 2 | 2 | 1 | 20 | Idea-245 |
| 13 | T2 | Coverage configured + reported; CLI pure halves | 3 | 3 | 3 | 18 | Idea-246 |
| 13 | T4 | Integration tier on a nightly CI job | 3 | 3 | 3 | 18 | Idea-246 |
| 13 | D1 | npm high advisories via `@neo4j-nvl` — decide the override | 2 | 4 | 3 | 18 | Idea-245 |
| 16 | A1b | Subpackages for review / plan / port / docgen — RULE AT ADR 0015, do not move first | 4 | 4 | 4 | 16 | DOC1 (ADR amendment) |
| 16 | Doc4 | MODULE_MAP / CLAUDE.md size and seven moved paths | 2 | 2 | 2 | 16 | Idea-247 |
| 18 | C2 | Split `create_app` and the 120-line CLI commands | 3 | 2 | 3 | 15 | Idea-246 |
| 18 | C3 | `_str_or_none` ×5, `_git` ×5 → core | 2 | 1 | 1 | 15 | Idea-243 |
| 18 | T6 | Drop the `SPIDERP_LOGDIR` alias (trigger passed) | 1 | 2 | 1 | 15 | Idea-243 |
| 18 | D4 | PEP 621 metadata | 1 | 2 | 1 | 15 | Idea-245 |
| 22 | A2 | Rule `query_specs` promotion to core | 2 | 2 | 3 | 12 | DOC1 (ADR amendment) |
| 22 | T5 | Worktree fixture unlock-before-remove | 2 | 1 | 2 | 12 | **prune EXECUTED**; fixture → Idea-246 |
| 22 | Doc3 | 79 broken links (warn-only guard) | 2 | 1 | 2 | 12 | Idea-247 |
| 22 | Doc5 | Shard `IDEAS.md`; drop the `Idea-N` placeholder | 2 | 1 | 2 | 12 | Idea-249 |
| 22 | P4 | Dependency grooming per epic; close five finished epics | 2 | 2 | 3 | 12 | Idea-248 |
| 27 | D2 | Staged major-version upgrades | 2 | 3 | 4 | 10 | Idea-245 |
| 27 | P6 | Delete the merged branch (user's call) | 1 | 1 | 1 | 10 | user |
| 29 | T3 | mypy: remove or scope to core | 2 | 2 | 4 | 8 | Idea-246 |

**Business justification, one line each, for the top of the list.** D3: the daily interpreter
and the declared floor are both untested, so a bad upgrade is found by the company, not by CI.
T1: nobody can measure coverage without turning the suite red. A1a: the restructure mints ids
by module, and one component has no module. P2: five items are invisible to every puller for
no reason. P1: every debt number the ritual has recorded since 08-21 was measured on a graph
the ritual had not loaded. Doc1: the port's own routing doc sends the company to files that
moved in July. P3: a gate prompt that fails at the SME session costs the one hour the SME had.

---

## 4. Phased remediation, alongside feature work

**Phase 0 — with this review (done).** T1 `.gitignore`; T5 prune of the locked worktree; the
code graph reloaded; Ideas 243–249 inboxed for grooming.

**Phase 1 — before the restructure items are pulled (one session, no gate).** D3 matrix +
P5 timeouts/pre-commit (one CI commit); A1a guard + `drydocs-port` module and series (one
backlog-surface commit, renders refreshed); P1 ledger-from-snapshot + `a2_circular` and C1's
cycle (one code commit in `knowledge/depgraph-snapshots/` and `drydocs_core/`); P2 released
after the laptop check; T6 alias drop. Each is a single-purpose commit on `main`.

**Phase 2 — with CFG1/CFG2/PLAN2 (the same sessions, adjacent surfaces).** Doc1 + Doc4 path
guard and sweep (PLAN2 already edits `git-readme.md`); A3 classification of the five
directories (CFG-series, the manifest is open anyway); P3 gate-prompt shape test (the
restructure signs at least one more gate); Doc2 phase narrative (DOC1 touches the plan
surface).

**Phase 3 — at ADR 0015's amendment (DOC1).** A1b and A2 are rulings, not moves: subpackages
or an exported module list; `query_specs` to core or declared for good.

**Phase 4 — steady state, one per port cycle.** T2 coverage report → C2 splits → T4 nightly
integration → D1 override → D2 upgrades in blast-radius order → C4 board size → Doc3/Doc5
hygiene → T3 decision. None gates anything; each is a half-day.

---

## 5. What this review did NOT find

Named so the next review does not re-search it. No core-upward import (A1 = 0). No
component-to-component import outside the declared entrypoint and the one declared allowance
(A6). No dead module in package scope (A4 = 0); the seven first-party hits are all entry
points. No render drift (`render_board.py` then `git status` — clean). No publish-boundary
link leak (0 of 622). No dead dependency chain in the backlog (0). No flaky-test retry
mechanism to hide behind (none installed, by argument at `tests/integration/conftest.py:18`).
No lockfile drift (`poetry check --lock` clean). CI green on the last ten runs.
