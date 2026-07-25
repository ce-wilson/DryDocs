# Architecture & tech-debt review — directory tree and module structure

**Date:** 2026-07-25 · **Trigger:** pre-UI structural review. The web console is being built;
the API contract and the graph property names it consumes become expensive to change once
routes, demo fixtures, and gate pages depend on them.
**Method:** `/architecture` + `/tech-debt` over the full tree at `aa11fb5`.
**Baseline health:** `poetry run pytest -q` → **900 passed, 6 skipped**. The repo is healthy;
nothing here is a fire.
**Classification:** Internal-Public (mechanism only — no SIDs, app codes, org values).

Resolves to three ADRs, all **PROPOSED** (nothing below is authorized until the HITL gate runs):

| ADR | Question asked | Recommendation |
|---|---|---|
| [0008](../decisions/0008-orchestration-module-boundary.md) | Should `controlm/` folders become `orchestration/`? | **No rename. Add a parent.** `controlm/` is at the wrong *depth*, not the wrong place |
| [0009](../decisions/0009-configuration-substrate.md) | Are the config files too large — move to a relational DB? | **Keep YAML as source of truth.** Split by domain, schema-guard it, widen the existing SQLite read model. Add a *draft* table for UI writes |
| [0010](../decisions/0010-internal-source-term-abstraction.md) | Will SEAL/PAT terms survive an internal port restructure? | **PAT is already safe. SEAL is not** — `seal_id` is the canonical node key in 47 places. Move to `app_id` + `id_authority` |

---

## 1. What is already right — do not "fix" these

A structural review that only lists problems will get the good parts refactored away. Four
things in this repo are better than the industry norm and are load-bearing:

1. **The core/component boundary is real and enforced.** `MODULE_MAP.md` + a *default-deny*
   `tests/unit/test_module_boundary.py` means an unclassified module fails the suite rather
   than silently escaping the rule. Most repos have the diagram and not the test.
2. **Vendor terms are already abstracted at the layer that matters.** Graph labels are
   `:BusinessApplication`, `:Product`, `:AreaProduct`, `:CatalogLOB`, `:SoftwareProduct` —
   not `:SealApp`, not `:PATProduct`. `config/taxonomy/business-application.yaml` says it
   outright: *"GENERIC CONCEPT: BusinessApplication. SEAL is the SOURCE OF RECORD … the
   concept is deliberately decoupled from the vendor system."* That instinct was correct and
   §4 below only asks you to finish applying it.
3. **The orchestrator-neutral seam exists and has been exercised.** `config/crosswalks/`
   holds gate-confirmed AutoSys and Airflow → BMC baseline maps, with honest
   `fidelity: no-equivalent` rows (4 of 14 for Airflow: trigger rules, pools, XCom, dynamic
   task mapping). `:SchedulerKind` was already retired into the software registry at C12.
   The extension path is designed, not hypothetical.
4. **The config/DB split is already the right shape.** `drydocs_core/mapping_store.py`
   materializes committed YAML/CSV into `var/mapping.db` as a *derived, deletable*
   read model, gitignored, with a round-trip parity test. That is a materialized view over a
   git source of truth — which is the correct answer to the question in §3, already built.

The findings below are about **depth, granularity, and naming** — not about the model.

---

## 2. Findings, scored

`Priority = (Impact + Risk) × (6 − Effort)`, per the tech-debt skill. **Pre-UI** flags items
whose cost rises sharply once the console has routes and fixtures depending on them — the
formula deliberately does not encode cost-of-delay, so read the two columns together.

| # | Finding | Category | I | R | E | **P** | Pre-UI |
|---|---|---|---|---|---|---|---|
| **F4** | `agents/` and `libs/` are outside `pyproject` packages **and** outside the boundary test — *and the guard's own import filter could not see the standalone packages* | Architecture | 3 | **5** | 2 | **32** | — |
| **F1** | No `orchestration/` parent — `controlm/` sits directly in core with no sibling slot | Architecture | 4 | 4 | 3 | **24** | ✅ |
| **F3** | UI write path has no durable draft substrate (commit-by-replace only) | Architecture | 4 | 4 | 3 | **24** | ✅ |
| **F7** | `config/taxonomy-ontology-map.yaml` — 1,013 lines, one file, all domains | Code | 3 | 3 | 2 | **24** | — |
| **F8** | `drydocs_core/ontology/relationship_vocabulary.yaml` — 2,111 lines, same shape | Code | 3 | 3 | 2 | **24** | — |
| **F9** | ~~Stale git worktree — 47 MB shadow repo~~ **CLOSED same day** (auto-removed) | Infrastructure | 2 | 2 | 1 | **20** | — |
| **F2** | `seal_id` is the canonical node key — 47 occurrences across schema/loaders/API/UI | Architecture | 4 | 5 | 4 | **18** | ✅✅ |
| **F14** | Config YAML has test guards but no JSON Schema — errors surface late, only in Python | Test | 3 | 3 | 3 | **18** | — |
| **F12** | Folder names disagree with module names (`web/` ≠ `drydocs-web`, `agents/` ≠ `drydocs-agents`) | Documentation | 2 | 2 | 2 | **16** | ✅ |
| **F6** | `drydocs/cli.py` — 1,519 lines, 27 commands, single composition root | Code | 3 | 2 | 3 | **15** | — |
| **F10** | `UI-WIP/` (40+ files) and `SDLC-Docs/` at repo root; 20 untracked PNGs at root | Documentation | 2 | 1 | 1 | **15** | — |
| **F13** | `docs/` root mixes loose `controlm-*.md` and `port-*.md` with the subdirectory tree | Documentation | 2 | 1 | 1 | **15** | — |
| **F5** | `drydocs/` remainder holds 4 components (load/review/plan/docgen) in one flat namespace | Architecture | 3 | 3 | 4 | **12** | — |
| **F11** | 66 depgraph snapshots / 4.2 MB, several per day, unbounded | Infrastructure | 1 | 2 | 2 | **12** | — |
| **F15** | Two test roots — `tests/` (pytest) and `graph-tests/` (YAML acceptance) | Test | 1 | 1 | 1 | **10** | — |

**F2 is the item to act on first despite scoring 7th.** Its effort is high *today* and rises
every week the console adds a route that reads `seal_id`. It is already in
`web/src/data/mappingsDemo.ts` as `app_seal_id` and in `drydocs_api/query_specs.py`. Formula
priority measures the fix; it does not measure the cost of not fixing.

### Notes on the lower-scored findings

- **F5** is *known and deliberate* — `MODULE_MAP.md` records that `drydocs/` keeps its name
  until Phase C per ADR 0002-a-1. Left as-is; listed only so the next reviewer does not
  rediscover it as a surprise.
- **F9** costs nothing to fix and pollutes every `grep`/`Grep` run in the repo (it shadowed
  results throughout this review). `git worktree remove` when the branch is done.
- **F11** — snapshots are the drift-comparison record and are cheap individually. Consider
  keeping one per day (the `prune-snapshots` command already exists) rather than one per
  session; several 2026-07-20/21 timestamps are minutes apart.
- **F10/F13** are cosmetic but compound: a new contributor cannot tell from the root listing
  which of `UI-WIP/` and `web/` is the real UI.

---

## 3. Configuration: files or a database?

**Short answer: neither move. The architecture is already correct — it is the file
*granularity* that hurts, not the file *format*.**

Current declarative surface (5,590 lines under `config/`, plus 2,111 in the ontology vocab):

| File | Lines | Growth driver |
|---|---|---|
| `config/taxonomy-ontology-map.yaml` | 1,013 | one entry per gated mapping — grows with every gate |
| `drydocs_core/ontology/relationship_vocabulary.yaml` | 2,111 | one entry per relationship type |
| `config/source-mappings/controlm-psgmgr.yaml` | 440 | one entry per profiled column |
| `config/source-registry.yaml` | 296 | one entry per source |
| `docs/restructure/backlog.yaml` | 5,651 | one entry per work item |

### Why YAML must stay the source of truth

Four repo-defining mechanisms read *git text*, not a database. Moving the write path to a DB
breaks all four at once:

1. **The HITL gate reviews diffs.** `docs/restructure/03-hitl-sme-flow.md` and every
   `config/gate-prompts/*.yaml` assume an SME can read what changed. A row-level DB diff is
   not reviewable by a domain expert in a gate session.
2. **The cross-repo port is a commit range.** `git-readme.md` / `docs/port-prompt.md` move
   producer → company by applying commits onto a disjoint `main`. Binary or DB state cannot
   be cherry-picked.
3. **Classification is enforced on files.** `tests/unit/test_classification.py` requires a
   `classification` on every registered source; `PUBLISH-BOUNDARY.md` gates publication by
   path. Both are file-shaped.
4. **Renders are deterministic from text.** The board, the design docs, and the gate pages
   are byte-reproducible from committed sources — the stale-render check in `CLAUDE.md` §0
   depends on it.

### What the growth actually costs

The real pain is not size, it is **that one file serves many domains**. Editing an ontology
mapping for the Control-M domain touches the same 1,013-line file as a catalog mapping, so
two concurrent sessions collide, and a port conflict in that file is one big hunk instead of
one small one. That is a *granularity* problem with a granularity fix.

### Recommendation (detail in [ADR 0009](../decisions/0009-configuration-substrate.md))

1. **Split by domain, keep the format.** `config/taxonomy-ontology-map.yaml` →
   `config/ontology-map/{controlm,catalog,seal,registry,docs}.yaml` with a loader that
   concatenates in deterministic order. Same for `relationship_vocabulary.yaml`. Port
   conflicts shrink to the domain that changed.
2. **Add JSON Schema alongside the Python tests** (F14) so an editor flags a malformed entry
   before `pytest` does, and so non-Python tools (the UI's admin surface, agents) can
   validate without importing `drydocs_core`.
3. **Widen `mapping.db`, do not promote it.** It already materializes the ontology map, the
   vocabulary, manual loads, and the seal-contact overrides. Add the source registry,
   precedence, and source-mappings tables so the console reads *one* SQL surface. It stays
   derived, gitignored, rebuildable — never the artifact a gate reviews.
4. **For UI writes: propose in the DB, land in git.** Today `POST /mappings/overrides/draft`
   returns the *complete updated file* (commit-by-replace). That is correct and does not
   scale past a small override list. Add a `draft` table to `mapping.db` as the write-ahead
   buffer: the console writes drafts freely, a draft is promoted by *emitting the YAML/CSV
   diff* into a branch for the gate. Git stays the system of record; the DB absorbs the
   editing session. This is the one piece to design **before** the console grows write
   surfaces.

---

## 4. Where the structure will bend: Control-M and SEAL

### 4.1 `controlm/` — right place, wrong depth

`drydocs_core/controlm/` (1,725 lines, 8 modules) is not misfiled. Renaming it to
`orchestration/` would be actively wrong, because most of it *is* Control-M:

| Module | Lines | Vendor-specific? |
|---|---|---|
| `variables.py` | 424 | **Yes** — `%%NAME\|VALUE` AutoEdit syntax, PRECMD/POSTCMD, `%%\VAR` pools |
| `resolver.py` | 346 | **Yes** — reproduces AutoEdit substitution / "Variable Simulation" offline |
| `variable_report.py` | 79 | **Yes** — aggregates Control-M variable classifications |
| `facts.py` | 63 | **Yes** — routes `SEMANTIC_FACT` variables to Control-M staging tables |
| `folder_name.py` | 134 | **Yes**, and company-specific — Control-M folder naming convention |
| `commands.py` | 486 | **Mixed** — generic shell/argv parsing + launcher registry, fed by Control-M fields |
| `paths.py` | 127 | **Mixed** — generic path canonicalization, Control-M `{ODATE}` and FileWatcher wildcard vocab |
| `__init__.py` | 66 | re-exports |

Roughly 1,100 of 1,725 lines are irreducibly Control-M. Calling that directory
`orchestration/` would make the *most* vendor-coupled code in the repo look neutral — the
exact failure ADR 0004 was written to prevent ("one meaning per word").

**The actual gap is that `controlm/` has no parent and no siblings.** There is nowhere for
an AutoSys or Airflow module to land, and nowhere for the genuinely neutral parts to live.
When Airflow arrives, the only available move is a second top-level `airflow/` beside
`controlm/` — and the shared shell/path parsing gets duplicated or imported sideways.

Recommended shape (details and the migration in [ADR 0008](../decisions/0008-orchestration-module-boundary.md)):

```
drydocs_core/orchestration/
├── __init__.py          # the neutral surface components import
├── shell.py             # ← from controlm/commands.py: argv/statement parsing, launcher registry
├── paths.py             # ← from controlm/paths.py: canonicalization, role classification
├── crosswalk.py         # reads config/crosswalks/*.yaml; the gate-confirmed native→baseline map
└── controlm/            # ← today's controlm/, unchanged in content
    ├── variables.py  resolver.py  variable_report.py  facts.py  folder_name.py
    └── fields.py        # the Control-M-specific half of commands.py (PRECMD/POSTCMD/CMD_LINE routing)
```

This is **additive**: one `git mv`, one new package, two file splits. Nothing is renamed away
from an accurate name. The same treatment applies one level out to
`drydocs/loaders/controlm_*.py` → `drydocs/loaders/orchestration/controlm/`, and to the
`sql/` and `cypher/` asset directories.

**Do the core move before the UI ships**, because the API's query specs are where an
orchestrator assumption would first become a public contract. The loader/SQL reshuffle is
internal and can follow.

> **Graph labels stay as they are.** `:ControlMJob` / `:ControlMFolder` / `:ControlMServer`
> are correct under ADR 0003 rule 4 — source-system labels take the vendor prefix. An
> AutoSys job becomes `:ControlMJob` only if the crosswalk says `fidelity: exact`; otherwise
> it goes through `ontology-mapper`. Nothing in this section changes the graph.

### 4.2 SEAL and PAT

These two are in very different shape, and the difference is instructive.

**PAT is already safe.** It appears in prose, gate specs, and comments — and essentially
nowhere in code, schema, or property names. Its concepts landed as `:Product`,
`:AreaProduct`, `:ProductLine`, `:CatalogLOB`, `:BusinessSegment`, `:Role`, `:ProductRole`.
A rename of the internal tool would cost a documentation sweep. **No action needed.**

**SEAL is not.** `seal_id` is the *canonical key* on `:BusinessApplication` — 47 occurrences
in schema and loader Cypher alone, plus `seal_app_ref` (15), `seal_ids` (13), `seal_sid`,
`seal_holder_sid`. It has already crossed into the API (`drydocs_api/query_specs.py`) and the
console (`web/src/data/mappingsDemo.ts` as `app_seal_id`, and `match_method: 'seal_var'`).

This contradicts the repo's own rule. ADR 0003 rule 1 is *"source-system fields stay verbatim
on **source-labeled** nodes."* `:BusinessApplication` is the canonical node, not a
source-labeled one — so a vendor-named key on it is precisely the case the rule excludes.
`config/taxonomy/business-application.yaml` gets this right at the taxonomy layer
(`concept: BusinessApplication`, `source_of_record: SEAL`, `identifier: SEALID`); the graph
and the API layers did not inherit it.

**Recommendation** (detail in [ADR 0010](../decisions/0010-internal-source-term-abstraction.md)):
carry identity as a **qualified reference**, not a vendor-named scalar —

```
(:BusinessApplication {
   app_id: "82507",            # the value, neutral name
   id_authority: "SEAL",       # WHICH registry issued it  ← survives the rename
   app_urn: "urn:dd:businessapplication:seal:82507"   # optional canonical form
})
```

Migrate additively: write `app_id`/`id_authority` alongside `seal_id`, flip readers, then
retire `seal_id` at a gate. **The API and console must expose `app_id` + `id_authority` from
day one** — that costs nothing today and is the whole point of doing this before the UI
hardens.

This is the Unity Catalog lesson from `reference/research/databricks-unity-catalog.md`
applied inward: the value of a governed namespace is that *the identifier itself carries its
authority*. And where "SEAL", "PAT", and "AIS" need to be **defined** rather than encoded,
the home is a `CatalogBusinessTerm`-shaped glossary
(`docs/patterns/data-catalog/enterprise-data-catalog-ontology.md`) — which is the same
conclusion the reopened Q6 acronym question is circling.

---

## 5. Phased plan

Each phase is independently shippable and leaves the suite green. Nothing here is a
big-bang refactor.

### Phase 1 — free wins, this week (no gate needed)

**Execution note, 2026-07-25 (same day).** Phase 1 was attempted immediately. Two items
were mis-assessed in the table above and are corrected here — the corrections are kept
visible rather than silently edited, because both were effort estimates that did not
survive contact.

| Item | Action | Outcome |
|---|---|---|
| F9 | Remove the stale worktree | ✅ **Already closed** — auto-removed by the harness between the audit and the attempt. Nothing to do |
| F4 | Add `agents/` and `libs/` to `tests/unit/test_module_boundary.py` | ✅ **Done** (`432ea43`) — and it was **bigger than scored**. See below |
| F10/F13 | Move `UI-WIP/`, group loose `docs/*.md` | ❌ **Not a free win — effort mis-scored (1, should be 3–4).** Deferred |
| F11 | "Run `drydocs prune-snapshots`" | ❌ **Wrong mechanism.** Deferred |
| F10 (part) | Gitignore root `*.png` scratch | ✅ **Done** — 20 untracked screenshots, zero references, nothing tracked affected |

**F4 was larger than the finding described.** Bringing `agents/` and `libs/` under the guard
surfaced a hole *in the guard itself*: the first-party import filter was
`m == "drydocs" or m.startswith(("drydocs.", "drydocs_core"))` — the dot means it matched
`drydocs.x` and `drydocs_core*` but **not** `drydocs_api`, `drydocs_lineage`,
`drydocs_deepdoc`, or `drydocs_remediation`. Imports *between the standalone component
packages were invisible*, so `test_components_do_not_import_each_other` could never have
caught one. Measured before the fix: **32 first-party imports unseen**, including
`drydocs.cli → drydocs_lineage.*` — meaning the `ENTRYPOINT_MODULES` exemption written to
permit that import had been doing nothing, because the import was never visible in the first
place. A new `DECLARED_COMPONENT_IMPORTS` table records the one genuine
component→component edge (`agents.common.specs_catalog → drydocs_api`), with a test that
fails if an entry goes stale.

**Why F10/F13 are not free.** `UI-WIP` is referenced by **31 tracked files** — including
`backlog.yaml` (45 hits), the *generated* `docs/plan/board.html`, `PORT-MANIFEST.yaml`, two
gate-prompt specs, two governed `docs/design/*` renders, and `drydocs_api/app.py`. The loose
`docs/*.md` files carry 3–10 references each. That is a wide mechanical rename touching
governed renders and port machinery, so it belongs on a **branch, port-sequenced through
`docs/port-prompt.md`** — not in a tidy-up commit. The original Effort=1 scored the `git mv`
and ignored the reference sweep.

**Why F11 was wrong.** `drydocs prune-snapshots` prunes `:ApplicationSnapshot`-style
snapshots **inside Neo4j** (via `SnapshotWriter`), and needs a live connection. It has
nothing to do with `knowledge/depgraph-snapshots/*.json`, which is what the finding was
about. Those JSON files are a deliberate per-push structural-drift record with a documented
A/B compare workflow in their README — thinning them is a call about how much audit history
to keep, not a cleanup. **Left for the user to decide.**

### Phase 2 — before the console grows write surfaces (**pre-UI**)

| Item | Action | ADR |
|---|---|---|
| F2 | Add `app_id` + `id_authority` beside `seal_id`; **API and web emit the neutral pair only** | 0010 |
| F3 | Design the `draft` table in `mapping.db`; keep git as the commit target | 0009 |
| F1 | Create `drydocs_core/orchestration/`; move `controlm/` under it; split `shell.py`/`paths.py` out | 0008 |
| F12 | Decide folder-vs-module naming once (`web/` ↔ `drydocs-web`, `agents/` ↔ `drydocs-agents`) and record it in `MODULE_MAP.md` | 0008 |

### Phase 3 — granularity, alongside feature work

| Item | Action | ADR |
|---|---|---|
| F7/F8 | Split the two monolith YAMLs by domain; deterministic concatenating loader | 0009 |
| F14 | JSON Schema for each config family, wired into the existing tests | 0009 |
| F1b | Reshuffle `drydocs/loaders/controlm_*` + `sql/` + `cypher/` under `loaders/orchestration/controlm/` | 0008 |
| F6 | Split `cli.py` into a thin root + per-component command modules (still one composition root, still exempt under `ENTRYPOINT_MODULES`) | — |

### Phase 4 — when a second orchestrator is real

Retire `seal_id`. Populate `orchestration/autosys/` or `airflow/` against the confirmed
crosswalk. Revisit `drydocs/` Phase C packaging (F5).

---

## 6. What NOT to do

Recorded so a future session does not rediscover these as good ideas:

1. **Do not rename `drydocs_core/controlm/` to `orchestration/`.** ~1,100 of its 1,725 lines
   are AutoEdit/Control-M semantics. A neutral name on vendor-specific code is worse than a
   vendor name on vendor-specific code, and it is the failure mode ADR 0004 already ruled on.
2. **Do not move the config source of truth into a database.** It breaks the HITL diff
   review, the commit-range port, the classification tests, and deterministic renders — four
   mechanisms this repo is built on. The derived SQLite read model already delivers the
   query ergonomics the question was really after.
3. **Do not rename the `:ControlM*` graph labels.** ADR 0003 rule 4 is correct: source-system
   labels take the vendor prefix precisely so the canonical labels can stay neutral.
4. **Do not touch PAT terminology.** It never leaked into code. Effort with no return.
5. **Do not restructure `drydocs/` (F5) now.** ADR 0002-a-1 deferred it deliberately to Phase C;
   doing it mid-UI-build spends the largest refactor budget on the smallest risk in this list.
