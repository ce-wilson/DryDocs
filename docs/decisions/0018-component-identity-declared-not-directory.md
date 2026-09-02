# ADR 0018 — Component identity is a declared, exported module map; directories follow only when a trigger fires

```yaml
status: PROPOSED          # awaiting the user's ruling on D1-D5 and the three open questions
date: 2026-09-02
authored_by: the 2026-09-02 tech-debt review, second-reviewed under /architecture (desktop)
deciders: [chad.wilson]
layer: 0-configuration    # the declaration layer; no graph semantics change
relates_to:
  - 0002-a-drydocs-core-extraction-plan.md      # the core/component split and its §7 over-extraction risk
  - 0008-orchestration-module-boundary.md       # S7: folder name vs module name
  - 0013-backlog-sharding.md                    # the module registry the backlog reads
  - 0015-team-edition-template.md               # D2 (module cut) and D4 (file classes by path) — this ADR is the D2 amendment DOC1 carries
  - MODULE_MAP.md                                # the physical routing doc; its components table becomes a render
  - tests/unit/test_module_boundary.py           # today's only machine-readable component declaration
  - docs/restructure/backlog/modules.yaml        # the backlog's module registry (series = module, PLAN1)
  - PORT-MANIFEST.yaml                           # already classifies every path; ownership is what it lacks
  - docs/reviews/tech-debt-pre-restructure-2026-09-02.md   # findings A1, A2, A3, Doc1, Doc2
  - docs/reviews/restructure-design-review-2026-09-02.md   # F5 (the layer note), the two-axis rule
executed_by: TBD — grooms of Idea-244 (the map, the guard, the five directories) and Idea-247 (the routing-doc guard and renders); the DOC1 amendment to 0015 D2
```

> **Nothing in this record moves a file.** It decides what a component IS, where that is
> written down, and what has to be true before any file moves. The move itself (D4) is
> triggered, not scheduled.

- **Reviewed at:** commit `0e3d2945` on `main`, port base `port-base-20260901`; venue MSI.
  *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*

## Context

The tech-debt review found the physical layout and the logical layout disagreeing in three
places, and each one is a place the Team Edition copier (ADR 0015 D4) will read:

1. **Five components are lists of module names inside one package.**
   `tests/unit/test_module_boundary.py:51–200` declares nine component groups. Five of
   them — `load`, `review`, `plan`, `port`, `docgen` — are lists of dotted names inside
   `drydocs/` (70 files, 20k LOC): `drydocs.plan_board` is `plan`, `drydocs.gate_pages`
   is `review`, `drydocs.port_preflight` is `port`, and they sit side by side in one flat
   directory. The other four (`remediation`, `lineage`, `deepdoc`, `docmeta`, `api`, plus
   `agents` and `libs`) ARE directories. The S7 rule (`MODULE_MAP.md:21`) already says
   when a directory must match a module name — "a Python component whose directory
   diverged from its module name" — and it bites only when a directory exists. Here none
   does, so the rule is satisfied vacuously and the five components are invisible to any
   reader that classifies by path.

2. **One component has no module, and no guard joins the two registries.** The `port`
   group (`port_preflight`, `port_backlog_union`, `port_rename_detect` — three of the most
   edited modules of August) has no row in `docs/restructure/backlog/modules.yaml`, so
   under PLAN1 (the series is the module) port work has no id series. Nothing asserts
   `COMPONENT_GROUPS.keys()` against `modules.yaml`; the two lists have drifted once
   already and will again.

3. **Five top-level directories have a port disposition but no owner.** `SDLC-Docs/`,
   `graph-tests/`, `drydocs-icons/`, `libs/`, `knowledge/upgrade-plans/` each have a
   `PORT-MANIFEST.yaml` row (`:344`, `:921`, `:1134`, `:1175`, `:1179`, `:1183` — so the
   port knows what to DO with them) but appear in no routing document — not `CLAUDE.md`,
   not `README.md`, and only `libs/` in `MODULE_MAP.md`. Ownership is what the copier
   needs and the manifest does not carry: which module's ruling covers the file.

Two adjacent findings ride with these because they are the same disease in prose:
**routing docs lag the code.** `git-readme.md` names 31 paths that moved at the 0002-A
extraction (`drydocs/controlm/*.py`, `drydocs/models/*.py`, `drydocs/schema/*.cypher`,
`drydocs/ontology/*` — all now `drydocs_core/`), and `docs/restructure/01-project-plan.md`
documents 6 of the 18 phases `backlog/plan.yaml` declares. Both are hand-kept copies of
facts the repo holds elsewhere in machine-readable form.

**What ADR 0015 assumes.** D2 cuts the template BY MODULE NAME — "keep, promoted:
`doc_outline`, `sme_notes`, `gate_pages`, `docs_coverage` …", "cut: `plan_board`,
`port_preflight`, `backlog_store` …" — while D4 classifies template files BY PATH GLOB,
transferring the PORT-MANIFEST grammar. Those two clauses are consistent only if some
object maps module names to paths. Today that object is a Python constant inside a test
file, not importable by anything the copier would run. That is the trip hazard: not that
the files are flat, but that the declaration of what they belong to is not a first-class
object.

**Forces.**
- The company port is mid-apply (workplan chunks 2–9 open). A file move now is a rename
  trap on the consumer side — the J72 detector reports it, but reporting 30 renames into
  an apply that has already failed closure three times is a cost, not a courtesy.
- ADR 0002-A §7: "pulling load-only helpers into core to share early recreates the
  tangle the split removed." Over-extraction is the named risk of this exact move.
- Module paths are cited: `MODULE_MAP.md`, the manifest's rows, `config/gate-log.md`,
  85 test files, the port-prompt ledger. A move is add-new + deprecate-old (the G87 shape
  for ids), never a rename — so it costs a shim cycle either way.
- The four non-load groups have ~25 code importers and ~70 test references combined
  (measured 2026-09-02); the move is a half-day of mechanics plus the shim cycle.
- Two registries, two axes: `modules.yaml` is the backlog axis (series = module, PLAN1);
  `COMPONENT_GROUPS` is the import-boundary axis. They must agree by name, and the design
  review's §A2 rule stands: two registries never share a column — they JOIN.

## Decision

**D1 — The component map becomes an importable object, and it is the single declaration.**
`drydocs_core/component_map.py` (pure data; core imports nothing) carries what
`test_module_boundary.py:48–232` carries today: `CORE_PREFIXES`, `COMPONENT_GROUPS`,
`ENTRYPOINT_MODULES`, `DECLARED_COMPONENT_IMPORTS`, plus one new column per group —
`module:` the `modules.yaml` name it belongs to — and one function, `component_of(path)`.
The boundary test imports it (J37: a guard reads the importable object); `MODULE_MAP.md`'s
components table is rendered from it (J43: derived, never carried, with a drift guard on
the pattern of `docs/plan/board.html`); the copier's `_exclude` list and the manifest's
`drydocs/**` rows are derived from it when ADR 0015 builds. One place says what a
component is; three surfaces read it.

**D2 — The two registries join by name and a guard proves it.** Every `COMPONENT_GROUPS`
key names a `modules.yaml` module through its `module:` column; every Python module in
`modules.yaml` is the `module:` of at least one group. `drydocs-port` is added to
`modules.yaml` with series `PORT`, closing the gap PLAN1 left. `agents` → `drydocs-agents`
and `web` (non-Python, no group) → `drydocs-web` follow S7's non-Python clause unchanged.

**D3 — Every top-level directory names an owning module, in `MODULE_MAP.md`'s
"Non-Python surfaces" table, rendered from the same map.** The five:

| Directory | Owner | Ruling |
|---|---|---|
| `graph-tests/` | `drydocs-review` | `drydocs/graph_verify.py` reads it; the TC suites are the review component's acceptance data (manifest: canonical-company, unchanged) |
| `drydocs-icons/` | `drydocs-web` | `scripts/render_software_registry.py` copies them to `web/public/vendor-icons/`; an asset of the console |
| `knowledge/upgrade-plans/` | `docs` | Internal-Public design prose; `knowledge/depgraph-snapshots/` keeps its own rows (drydocs-load, the ritual) |
| `libs/` | open question Q1 | see below |
| `SDLC-Docs/` | `docs`, relocated | the 2018 genesis material (Full Circle Docs) is the project's own history, not external reference: move to `docs/history/genesis/` in lowercase, the six files as they are, and the design review's citation of `FCD-Requirements.md` follows it. Not `reference/` — nothing there has a `source_url` |

**D4 — Directories follow the map only when a trigger fires, and the triggers are
ADR 0002-A's.** A flat component becomes a subpackage (`drydocs/review/`, `drydocs/plan/`,
`drydocs/port/`, `drydocs/docgen/`; `load` stays the package root) when ONE of:
(a) it gains a second consumer outside `drydocs.cli` (the rule that moved `docs_verify` to
core at O58); (b) it needs its own run cadence or release (0002 rejected polyrepo on
exactly this trigger); (c) the copier is being built and D1's list-driven `_exclude`
proves insufficient in practice — not in anticipation. The move is add-new + re-export-old
for one port cycle, never a rename. **And never during an in-flight company apply**: the
earliest date is after workplan chunk 9 closes the `port-base-20260901` range.

**D5 — Routing docs are rendered or guarded, never hand-copied.** `MODULE_MAP.md`'s two
tables render from D1's map. `docs/restructure/01-project-plan.md`'s phase narrative
renders from `backlog/plan.yaml` (the roadmap already renders the table; the prose is one
field away) or the file is cut to what YAML cannot hold and links the roadmap.
`git-readme.md`, `CLAUDE.md`, `internal/repo-README.md` and whatever remains of the plan
get the L19-pattern guard: every backticked repo-relative path resolves. The 31 dead
paths in `git-readme.md` are swept under that guard, in the same commit that adds it.

## Options considered

### Option A — Declare and export; directories stay flat (D1–D3, D5) — RECOMMENDED NOW

| Dimension | Assessment |
|---|---|
| Complexity | Low — one data module, two guards, two renders, one `modules.yaml` row |
| Cost | Half a day; zero import rewrites; zero citation breakage |
| Scalability | The map scales to any number of components and to the copier's list-driven exclusion (copier `_exclude` is a list, not a glob grammar) |
| Team familiarity | High — the same shape as `modules.yaml`, `FROZEN_SERIES`, the manifest: a committed declaration with an agreement guard |
| Port impact | None; no path changes cross |

**Pros:** closes the copier's trip hazard at the declaration, which is where it actually
is; makes the boundary test, the backlog, MODULE_MAP and the future copier read one object;
lands before the restructure items and during the company apply without touching it.
**Cons:** the flat directory stays, so a human browsing `drydocs/` still sees 30 files
with no visual grouping; classification-by-glob stays impossible for the five groups
(by design — the list is the truth).

### Option B — Subpackages inside `drydocs/` (D4, when triggered)

| Dimension | Assessment |
|---|---|
| Complexity | Medium — ~25 code importers, ~70 test references, four `__init__.py` shims for a cycle |
| Cost | Half a day of moves plus a shim cycle plus the citation sweep (`MODULE_MAP.md`, manifest rows, gate-log mentions) |
| Scalability | Directory = component; glob classification works; S7 satisfied by construction |
| Team familiarity | High (the 0008 orchestration move used exactly this shape) |
| Port impact | High while an apply is in flight: ~30 renames the consumer must adopt; the J72 detector reports them, the company still does the work |

**Pros:** the physical tree finally says what the logical one says; the copier can glob.
**Cons:** every benefit is available from Option A's exported map except browsability;
the cost is real and lands on the company side twice (once at the port, once when their
own surgical merges — `cli.py` — meet moved imports). 0002-A §7 names this move's risk.
**Taken as D4, triggered, not scheduled.**

### Option C — Top-level packages per component (`drydocs_review`, `drydocs_plan`, …) — REJECTED

| Dimension | Assessment |
|---|---|
| Complexity | High — pyproject `packages`, the U14 `$packages` allow-list (twice wrong already), CI, the ledger, MODULE_MAP, every import |
| Cost | Days, and the company port pays it again |
| Scalability | The fullest expression of the invariant, and more than the invariant needs: `plan` and `port` are CUT from the template (0015 D2), so their independence buys nothing |
| Team familiarity | Medium |
| Port impact | Maximal |

**Rejected** for the reason 0002 rejected polyrepo: stronger isolation than any current
consumer needs, priced in version and dependency management, for a team of one plus
agents. Re-proposing this means arguing against that reason, not rediscovering it.

### Option D — Do nothing until the copier is built — REJECTED

The copier will be built against 0015 D2's module lists, and D2 already names modules by
dotted name. Without D1 the copier author hand-types the list a fourth time (after
`COMPONENT_GROUPS`, `MODULE_MAP.md`, `modules.yaml`), and the tech-debt review counted
what hand-typed lists cost: `$packages` was wrong from the hour it was written, twice.

## Trade-off analysis

The real question is not "flat or nested" but "where is the declaration, and can a
machine read it." Option A answers that for one afternoon and zero port cost, and leaves
the directory question to a trigger that has fired before (O58) and has a known shape
(0008). The cost of A is browsability, and browsability is exactly what the rendered
`MODULE_MAP.md` table provides — a reader who wants to know what `gate_pages.py` belongs
to reads the table, which is rendered from the same object the guard reads. The cost of B
now is paid by the consumer mid-apply; the cost of B later is paid once, by the producer,
with a shim. The order A → (trigger) → B is the 0002-A staging discipline applied one
layer down: extract when a consumer exists, never to share early.

## Consequences

- **Easier:** the copier's file classes have an object to read; the backlog can file port
  work (`PORT1`); `MODULE_MAP.md` cannot lag the boundary test; a new module fails ONE
  guard with ONE message naming the map; every top-level directory has an owner to ask.
- **Harder:** adding a component now touches `component_map.py` AND `modules.yaml` (the
  guard says so, with the row to add); `MODULE_MAP.md`'s tables are no longer hand-edited
  (the prose around them still is — the S7 section, the placement test, the history).
- **Revisit:** D4's triggers, at the copier build (0015 Phase 0 gate) and at any second
  consumer. And Q1–Q3 below.

## Open questions for the ruling

- **Q1 — `libs/` ownership.** It is Python (`libs/oracle_kerberos/`, port-frozen, its own
  `evaluate` manifest row) and it is in `COMPONENT_GROUPS` as `libs`, but it is not a
  package and no `modules.yaml` module claims it. Options: (i) `drydocs-core` owns it for
  backlog purposes and the group's `module:` says so — items about the kerberos helper are
  core items; (ii) a new module `drydocs-libs` / `LIBS` for two files. Recommend (i).
- **Q2 — `01-project-plan.md`: render or cut.** Rendering the phase narrative from
  `plan.yaml` keeps one document; cutting it to the parts YAML cannot hold (the
  conceptual argument, the audience strategy) and linking `roadmap.html` keeps the prose
  honest. Recommend cut-and-link: the roadmap already IS the phase narrative, rendered.
- **Q3 — `SDLC-Docs/` destination.** `docs/history/genesis/` (recommended: it is this
  project's own 2018 material) or `reference/research/` (only if the SME wants it read as
  an external method source, in which case it needs a `source_url` it may not have).

## Action items

1. [ ] Ruling on D1–D5 and Q1–Q3 (user).
2. [ ] Groom Idea-244 into two items: CFG/CORE — `drydocs_core/component_map.py` + the
   boundary test importing it + the join guard + `drydocs-port`/`PORT` in `modules.yaml`;
   DOC — the five ownership rows and the `SDLC-Docs/` relocation.
3. [ ] Groom Idea-247: the routing-doc path guard, the `git-readme.md` sweep in the same
   commit, `MODULE_MAP.md` tables rendered from the map, `01-project-plan.md` per Q2.
4. [ ] DOC1 (already minted): amend ADR 0015 D2 to cite this ADR's map as the object the
   cut reads, and D4 to say the `drydocs/**` file classes derive from it.
5. [ ] Record D4's triggers on the copier's Phase 0 gate so the move is decided there,
   with the company apply closed.
