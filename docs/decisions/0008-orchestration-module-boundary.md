# ADR 0008 — Orchestration module boundary: add a parent, do not rename `controlm/`

```yaml
status: ACCEPTED        # PROPOSED | ACCEPTED | SUPERSEDED
date: 2026-07-25
accepted: 2026-08-01    # ruled at backlog S1 (chad.wilson); as proposed, no amendments
deciders: [chad.wilson, SME-gate]
layer: 0-physical-layout
affects:
  - drydocs_core/controlm/               # → drydocs_core/orchestration/controlm/
  - drydocs/loaders/controlm_*.py        # → drydocs/loaders/orchestration/controlm/
  - drydocs/loaders/sql/ , cypher/
  - config/crosswalks/                   # gains a runtime consumer
  - MODULE_MAP.md
  - tests/unit/test_module_boundary.py
supersedes: ~
```

> **ACCEPTED 2026-08-01 as proposed** (backlog S1, chad.wilson). No amendments — the
> boundary this ADR draws is unchanged. The build is backlog **S2**, which this ADR gates.
> Note the ADR authorizes the SHAPE only: `git mv` plus the `commands.py` → `shell.py` /
> `fields.py` split. It writes no graph and needs no ontology gate.

## Context

DryDocs was built against BMC Control-M as the **baseline** orchestrator (`CLAUDE.md` §2
Tier 2, `config/precedence.yaml` authority 1). AutoSys and Airflow are declared placeholders
whose crosswalks to the baseline are already **gate-confirmed**
(`config/crosswalks/autosys-to-bmc.yaml`, `airflow-to-bmc.yaml`, signed off 2026-07-14).

The question raised in review: *`drydocs_core/controlm/` and `drydocs/loaders/controlm_*`
look like they might be in the wrong place — should they be `orchestration/`?*

### What is actually in `drydocs_core/controlm/`

1,725 lines across 8 modules. Auditing each against "would this survive a swap to AutoSys or
Airflow?":

| Module | Lines | Verdict |
|---|---|---|
| `variables.py` | 424 | Control-M only — `%%NAME\|VALUE` AutoEdit definitions, `PRECMD`/`POSTCMD`, `%%\VAR` global/pool scopes |
| `resolver.py` | 346 | Control-M only — reproduces AutoEdit substitution ("Variable Simulation") offline, incl. longest-defined-name matching and the `%%A.%%B` concatenation delimiter |
| `variable_report.py` | 79 | Control-M only — coverage aggregation over classified Control-M variables |
| `facts.py` | 63 | Control-M only — routes `SEMANTIC_FACT` variables into `STG_APP_FACT` / `STG_NOTIFICATION` |
| `folder_name.py` | 134 | Control-M **and company** specific — the folder-naming convention |
| `commands.py` | 486 | **Mixed** — generic statement splitting, shlex/argv tokenization, wrapper unwrapping, launcher registry, file-op verbs; *fed by* Control-M `PRECMD`/`POSTCMD`/`CMD_LINE` fields |
| `paths.py` | 127 | **Mixed** — generic canonicalization and role classification; Control-M `{ODATE}` tokens and FileWatcher `?`-run wildcards |
| `__init__.py` | 66 | re-exports |

Roughly **1,100 of 1,725 lines are irreducibly Control-M semantics.**

### Evidence the model itself generalizes

The crosswalks show the *concepts* hold and the *parsers* do not. Fidelity distribution:

| Orchestrator | exact | approximate | no-equivalent |
|---|---|---|---|
| AutoSys | 3 | 7 | 1 |
| Airflow | 2 | 8 | 4 |

Airflow's four no-equivalents (trigger-rule vocabulary, pools, XCom, dynamic task mapping)
are real gaps that route to `ontology-mapper`, not silent losses. Folder/job/condition — the
graph's spine — maps cleanly for both.

### The real problem

`controlm/` is **not misfiled. It has no parent and no siblings.**

- There is no directory an `autosys/` or `airflow/` module can land in without becoming a
  second top-level peer of `controlm/` inside core.
- The genuinely neutral ~600 lines (shell/argv parsing, path canonicalization) live inside a
  vendor-named package, so a future AutoSys module either duplicates them or imports
  sideways from `controlm`.
- `config/crosswalks/*.yaml` is gate-confirmed data with **no runtime consumer** — nothing in
  `drydocs_core` reads it. It is currently documentation that a test could enforce.

## Decision

**Add `drydocs_core/orchestration/` as the parent. Move `controlm/` under it unchanged.
Lift the two vendor-neutral modules to the parent. Do not rename anything to a name less
accurate than the one it has.**

```
drydocs_core/orchestration/
├── __init__.py          # the neutral surface; what components import
├── shell.py             # ← commands.py: statement split, argv tokenize, wrapper unwrap,
│                        #   interpreter inference, LAUNCHER_REGISTRY, file-op verbs
├── paths.py             # ← paths.py: canonicalize_path, classify_role, build_file_ref
├── crosswalk.py         # NEW — loads config/crosswalks/*.yaml; resolve(native, orchestrator)
│                        #   → baseline concept + node label + fidelity; raises on
│                        #   no-equivalent so an unmapped concept cannot be silently invented
└── controlm/
    ├── __init__.py
    ├── variables.py  resolver.py  variable_report.py  facts.py  folder_name.py
    └── fields.py        # ← the Control-M half of commands.py: PRECMD/POSTCMD/CMD_LINE and
                         #   EMBEDDED_SHELL/UCM field routing into shell.py
```

Four rules this ADR codifies:

1. **A vendor-named directory holds vendor-specific semantics — nothing else.** If a module
   would work unchanged against a different orchestrator, it belongs at the
   `orchestration/` level, not under a vendor.
2. **Neutrality is earned by a second implementation, not asserted by a name.**
   `orchestration/__init__.py` exports only what `controlm/` and the confirmed crosswalks
   *both* justify today. It does not become a speculative plugin framework.
3. **`config/crosswalks/` gains exactly one runtime consumer** — `orchestration/crosswalk.py`
   — so a `fidelity: no-equivalent` row is enforced in code rather than only in prose. This
   is the guardrail against the drift `external/orchestration/autosys/README.md` warns about.
4. **Graph labels are out of scope and do not change.** `:ControlMJob`, `:ControlMFolder`,
   `:ControlMServer`, `:ControlMApplication` remain correct under ADR 0003 rule 4 —
   source-system labels take the vendor prefix precisely so the canonical labels
   (`:BusinessApplication`, `:Product`) can stay neutral. An AutoSys job becomes
   `:ControlMJob` only where the crosswalk says `fidelity: exact`; anything else routes to
   `ontology-mapper` and the HITL gate.

The same parent goes one level out, in a later phase:

```
drydocs/loaders/orchestration/controlm/{loaders}.py + sql/ + cypher/
```

## Options considered

### Option A — Rename `controlm/` → `orchestration/` (the review's opening hypothesis)

| Dimension | Assessment |
|---|---|
| Complexity | Low (one `git mv`) |
| Cost | Low now, **high later** |
| Extensibility | Negative — no place left for the *next* vendor |
| Accuracy | **Poor** |

**Pros:** one command; the tree instantly "looks" vendor-neutral.
**Cons:** puts a neutral name on ~1,100 lines of AutoEdit-specific parsing. When Airflow
arrives, its DAG parsing must either go in the same directory (now genuinely mixed and
un-untanglable) or in a new `airflow/` beside a package called `orchestration` that is
secretly Control-M. It is the exact "one word, five meanings" failure ADR 0004 was written
to end. **Rejected.**

### Option B — Leave it entirely alone

| Dimension | Assessment |
|---|---|
| Complexity | None |
| Cost | Zero now |
| Extensibility | Deferred, not solved |
| Accuracy | Fine today |

**Pros:** no churn; the names are honest; 900 tests stay green with no work.
**Cons:** the second orchestrator arrives with no landing site and duplicates the shell/path
parser, or imports `drydocs_core.controlm.paths` from an `airflow` module — a sideways
dependency the boundary test does not currently catch (it guards component-to-component, not
vendor-to-vendor inside core). `config/crosswalks/` stays enforced only by prose.
**Rejected as the final state, but it is the correct fallback if capacity is short** — this
ADR is additive and can wait without accruing interest.

### Option C — Full plugin architecture (orchestrator ABC, entry-point registry, per-vendor adapters)

| Dimension | Assessment |
|---|---|
| Complexity | High |
| Cost | High |
| Extensibility | Maximal |
| Team familiarity | Fine, but unwarranted |

**Pros:** a third-party orchestrator could be added without touching core.
**Cons:** designing an abstraction from one implementation. The crosswalks already show the
vendors do not align cleanly (4 no-equivalents for Airflow) — an ABC would either force
lossy uniformity or be so loose it carries no meaning. Correct answer to a problem that does
not exist yet. **Rejected; revisit if a second orchestrator actually loads.**

### Option D — Add the parent, move `controlm/` under it, lift the neutral modules ✅

| Dimension | Assessment |
|---|---|
| Complexity | Low-medium (one `git mv`, one new package, two file splits) |
| Cost | Low |
| Extensibility | Solved — the slot exists and is named |
| Accuracy | **Every directory name stays true** |

**Pros:** additive, not a rename; nothing acquires a name less accurate than today's; the
neutral ~600 lines become reusable without a sideways import; crosswalks get an enforcement
point; the diff is mechanical and testable.
**Cons:** import churn across loaders, tests, and `MODULE_MAP.md` (mechanical — the
`ControlMFolder` rename playbook applies: baseline-grep → move → re-grep → tests); one
genuine judgment call in splitting `commands.py`; a company-side port must apply the same
move (coordinate via `docs/port-prompt.md`).

## Trade-off analysis

The decision turns on **when accuracy is cheapest to buy.** Option A trades permanent
accuracy for a one-command tidy-up. Option C buys extensibility that has no consumer.
Option B is free and honest but leaves a known collision on the path.

Option D is the only one where **no name gets less true**. That matters more than usual in
this repo, because agents route by directory name — `CLAUDE.md` §5 dispatches sub-agents by
layer, and the documented failure mode in §2 is agents "seeing" only BMC because it was the
only vendor with files on disk. A directory called `orchestration/` that contains only
Control-M semantics would re-create that failure with worse odds of being noticed.

Splitting `commands.py` is the one place reasonable people differ. The split line is clean:
statement/argv/launcher logic is generic (an Airflow `BashOperator` command needs exactly
this); knowing that `PRECMD` and `POSTCMD` are where shell text hides is Control-M
knowledge. If the split proves contentious in review, ship the parent + `git mv` first and
defer the split — the value is mostly in the parent.

## Consequences

**Easier**
- Onboarding AutoSys or Airflow has a named destination and a reusable parser.
- `fidelity: no-equivalent` becomes a runtime error instead of a comment.
- The tree answers "which parts are vendor-locked?" by shape rather than by reading code.
- Neutral parsing gets tested once, not once per vendor.

**Harder**
- One more level of nesting; imports get longer.
- The company port must apply the same move or diverge structurally (this is exactly the
  kind of change `docs/port-prompt.md` exists to sequence).
- `commands.py` briefly has two homes during the split.

**To revisit**
- If a second orchestrator ever loads for real, re-evaluate Option C with two implementations
  in hand — that is the point at which an abstraction can be derived rather than guessed.
- Whether `folder_name.py` (Control-M **and** company specific) belongs in core at all, or
  in a company-side overlay.

## Action items

1. [ ] Create `drydocs_core/orchestration/__init__.py`; `git mv drydocs_core/controlm drydocs_core/orchestration/controlm`.
2. [ ] Lift `paths.py` to `orchestration/paths.py`; split `commands.py` → `orchestration/shell.py` (generic) + `orchestration/controlm/fields.py` (Control-M field routing).
3. [ ] Write `orchestration/crosswalk.py` reading `config/crosswalks/*.yaml`; raise on `fidelity: no-equivalent`; add unit tests over both confirmed crosswalks.
4. [ ] Update `MODULE_MAP.md` (core table) and re-run `tests/unit/test_module_boundary.py`; add a guard that nothing outside `orchestration/controlm/` imports Control-M-specific modules.
5. [ ] Resolve the folder-vs-module naming inconsistency in the same pass and record it in `MODULE_MAP.md`: `web/` ↔ `drydocs-web`, `agents/` ↔ `drydocs-agents`, `libs/` — decide whether the directory or the backlog `module:` value moves.
6. [ ] Phase 3: `drydocs/loaders/orchestration/controlm/` for the loaders, `sql/`, and `cypher/` assets.
7. [ ] Sequence the company-side application through `docs/port-prompt.md` before any other structural port lands.
