# drydocs-review + drydocs-agents — module review, 2026-09-08

reviewed_commit: 191a71ab
reviewed_branch: review/module-sweep (worktree review-sweep; origin/main merged at the start of this firing — it had moved since slot 5, carrying docs/reviews/company-owed-path-review-2026-09-08.md and a re-stamped depgraph snapshot)
reviewed_port_base: port-base-20260908 — producer-side review. NOTE: this moved during today's sweep; slots 1-5 were stamped `port-base-20260905`.
slot: 6 of 10 (slug `review-agents`)
lenses: system-design, tech-debt (the standing sweep's two; architecture was a one-off on the web slot)
scope: the dotted prefixes of `COMPONENT_GROUPS['review']` and `COMPONENT_GROUPS['agents']`, read from
  `drydocs_core/component_map.py` (J37, the importable object) at this firing — 11 prefixes:
  `agents`, `drydocs.fid_census`, `drydocs.gate_pages`, `drydocs.graph_review`,
  `drydocs.graph_verify`, `drydocs.publishing`, `drydocs.review`, `drydocs.review_labels`,
  `drydocs.run_as_detect`, `drydocs.sme_notes`, `drydocs.source_mappings`
prior report: first pass

- **Reviewed at:** commit `191a71ab` on `review/module-sweep`, port base `port-base-20260908`; venue MSI. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*

Opened before any module code was read (section 4 step 2): this file is the durable
memory for the firing, so a session that compacts mid-review resumes here rather than
starting again. Sections below are filled in order and each is committed as it closes.

**This is the first slot holding TWO modules, and they are unlike each other.**
`drydocs-review` is ten dotted prefixes under `drydocs.` — the HITL surface: graph review
and verify, SME notes, review labels, gate pages, publishing. `drydocs-agents` is the
single prefix `agents`, which is not a `drydocs_*` package at all but the ADK app tree
with its own venv (`agents/.venv`, the one that leaks into this shell as `VIRTUAL_ENV`).
The plan sized them together at 4,851 lines. Where the two halves differ, this report says
which half it is talking about rather than averaging them.

## Measurements

Taken before any module code was read. The two halves are counted separately.

| measure | `drydocs-review` | `drydocs-agents` |
|---|---|---|
| first-party Python | **2,317 lines** | **4,901 lines**, 33 files (excludes `agents/.venv`) |
| shape | `drydocs/review/` package 2,197 + `publishing/` 24 + **8 re-export shims at 12 lines each** | the ADK app tree, own venv |
| largest unit | `review/gate_pages.py` 431 · `source_mappings.py` 382 · `fid_census.py` 366 | — |
| combined | **7,218 lines** against the plan table's 4,851 on 2026-09-05 — **+49%**, the largest gap yet | |

| both halves | |
|---|---|
| tests naming either | **40** files |
| scoped suite | **602 passed, 12 skipped**, 30s |
| `ruff check drydocs/review/ agents/` | clean |
| committed acceptance suites | **6** in `graph-tests/`, **30 assertions**: 28 `empty`, 2 `nonempty` |

**+49% is the widest divergence from the plan table so far** (slot 4 was +36%, slot 3
+16%, slot 5 exactly on). Four of the six slots measured have come in over. That is now a
pattern rather than a slot fact, and belongs to slot 10 rather than to any module: either
the table is stale by design and should say so, or the rotation is being sized against
numbers that no longer hold.

**One skip is a venue fact worth naming (J18):** `test_session_redaction.py:261` skips
because *"google-adk lives in agents/.venv, not this interpreter"*. The `agents` half is
therefore only partly exercised by this worktree's suite by construction — its own venv
is where its dependencies live. That is the same split that made the `api` group matter in
slot 4, and unlike that one it cannot be fixed by installing a group here: the ADK tree is
deliberately a separate environment.

## Lens 1 — system design

**The recurring pattern of this sweep reaches its highest-stakes instance here: the tool
whose job is to certify the graph reports PASS against a graph that is not there.**

### L1-1 — four of six acceptance suites cannot fail on an empty graph

`drydocs/review/graph_verify.py` is the *"data-driven Cypher acceptance runner"*: it loads
`TC-*` YAML suites from `graph-tests/`, runs each case's Cypher against a live graph, and
asserts a result shape — `empty`, `nonempty`, or `equals`. *"A suite fails (non-zero exit)
if any case fails."*

`evaluate` (`:136-148`) is pure and does exactly what it says:

```python
if assertion is Assertion.EMPTY:
    return (len(rows) == 0, ...)
```

There is **no precondition anywhere** — no anchor case, no row-count floor, no "is
anything loaded" check before the assertions are evaluated. So an `empty` case passes
whenever the query returns nothing, including when it returns nothing because the graph
holds nothing.

That would be harmless if suites mixed positive and negative assertions. **They do not.**
Counted across the six committed suites — 30 assertions, **28 `empty` and 2 `nonempty`**:

| suite | `empty` | `nonempty` | |
|---|---|---|---|
| `folder-attribution-coverage.yaml` | **12** | **0** | cannot fail on an empty graph |
| `bmc-docs-lexical.yaml` | **5** | **0** | cannot fail on an empty graph |
| `business-application-identity.yaml` | **5** | **0** | cannot fail on an empty graph |
| `provenance-diet.yaml` | **2** | **0** | cannot fail on an empty graph |
| `bmc-docs-smoke.yaml` | 2 | 1 | anchored |
| `tom-required-contacts.yaml` | 2 | 1 | anchored |

**Four of six suites, and 24 of 30 assertions, are unfalsifiable against an unloaded
graph.** The shape is inherent to what these suites are for — a negative assertion
("no folder lacks attribution", "no document is orphaned") is the natural way to express
a standard — and that is exactly why the runner has to supply the anchor the suite cannot.

**Consequence, and it is the sharpest version of this sweep's recurring finding.** A green
`graph-verify` run means *either* "the estate conforms to every rule in this suite" *or*
"the database was empty and every rule was vacuously satisfied", and the runner cannot
tell the reader which. `folder-attribution-coverage.yaml` is the clearest case: a
**coverage** suite, 12 negative assertions, no anchor — it cannot detect the absence of
the very thing whose coverage it measures. Because this is the acceptance gate, a false
green does not merely mislead; it ends the check.

**Cheapest correction:** a per-suite precondition, asserted by the runner before any case
is evaluated. The suite declares an anchor — a `nonempty` case, or a minimum row count on
a named label — and the runner reports `NOT RUN` rather than `PASS` when it fails. The
loader and evaluator are already pure and offline, so this is testable without Neo4j, and
the vocabulary already exists in the component: slot 3's `equivalence.py` calls the third
state **not proven** and rules that *"no evidence is never evidence."* This is that rule,
applied to the tool that certifies everything else.

### L1-2 — what this slot already gets right, recorded so no later firing re-audits it

- **The verifier writes nothing and says why it needs no gate.** *"The graph is only READ —
  this component writes no meaning edges, so it needs no HITL gate to run"*
  (`graph_verify.py:9-11`). The permission argument is made from the behaviour rather
  than asserted.
- **The classification boundary is stated at the file that would breach it.** The
  committed suite is a vendor-BMC smoke test, Internal-Public; *"real acceptance suites
  (internal counts/IDs) live in a gitignored twin"* (`:13-14`). Which also means the
  `empty`/`nonempty` ratio measured above is of the PUBLIC suites — the twin may be
  anchored differently, and this report cannot see it. **Recorded as a limit on the
  finding, not a hedge:** the four unanchored suites named are the ones that ship.
- **`unknown_targets` ties the suites to the review backbone** (`:151-158`) — a suite
  targeting a label the `review_labels` backbone does not know is reported, and the
  cross-check is kept pure by passing the backbone in rather than importing it.

## Lens 2 — technical debt

Two findings, one per half, and they have opposite characters: the `review` half carries
debt that is **documented, dated, and past its own expiry**; the `agents` half carries
debt that is **undocumented and structural**.

| hatch | `drydocs-review` | `drydocs-agents` |
|---|---|---|
| `# type: ignore` | 0 | 0 |
| `cast(` | 0 | 0 |
| `TODO` / `FIXME` | 0 | 0 |
| `: Any` | 11 | 0 |
| `# pragma: no cover` | 1 | 0 |
| `# noqa` | **0** | **17** |

### L2-1 — eight re-export shims are past the removal trigger they name, and the item that should have retired them was never minted

Eight files in `drydocs/` are 12 lines each and identical in shape
(`fid_census`, `gate_pages`, `graph_review`, `graph_verify`, `review_labels`,
`run_as_detect`, `sme_notes`, `source_mappings`). Each says:

> Re-export shim (ADR 0018 D4, 2026-09-02): this module moved to `drydocs.review.X`.
> Kept for ONE port cycle so every old import path, patch target and citation resolves to
> the SAME module object … **Removed at the roll after next**; new code imports the new path.

The mechanism is careful — `sys.modules[__name__] = _target`, so private names and
monkeypatches work through either path. The problem is the schedule.

| | |
|---|---|
| shims created | 2026-09-02 (LOAD1, `2c128f6e`) |
| rolls since | **two** — `port-base-20260905`, then `port-base-20260908` **today** |
| the stated trigger | "the roll after next" — **fired today** |
| ADR 0018 action item 6 | *"[ ] Shim removal at the roll after next (an item minted when the relay rolls)"* — **unchecked** |
| item or idea for the removal | **none** — no backlog item mentions it, `IDEAS.md` returns zero |

**Consequence.** These shims work perfectly, which is precisely why nothing will ever
signal that they are stale: no test fails, no import breaks, no lint fires. The migration
they exist to smooth is complete on the writing side and open forever on the cleanup side,
and every cycle that passes makes "new code imports the new path" less true — nothing
enforces it, so an old path remains available to any new caller. The ADR anticipated this
exactly and left the enforcement to a minted item that was never minted.

**Scope note.** This slot owns **8** of them. Repo-wide there are **18** carrying the same
ADR 0018 D4 banner, spanning `plan`, `port` and `docgen` — those belong to slots 7 and 8,
which have not run yet. The removal is one action across four components, not four
actions, which is an argument for minting it once now rather than four times later.

**Cheapest correction:** mint the item the ADR says to mint. If the removal should NOT
happen yet, the honest fix is to amend the trigger in ADR 0018 and in the eighteen
docstrings, because a stated expiry that passes silently is worse than a longer one
stated accurately.

### L2-2 — nine copies of a `sys.path` preamble, and the thirteen suppressions that exist only to serve it

All 17 `# noqa` in the `agents` half break into two groups. Four are `F401` and explained
at the site (the ADK app convention exposing `agent.root_agent`; `serve.py`'s import for
its `.env` merge). **The other thirteen are `E402`**, and every one of them follows the
same three lines — here from `common/graph_read.py:27-31`:

```python
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from drydocs_core.notifications import from_summary, to_payload  # noqa: E402
```

**Nine files under `agents/` do this**, because the ADK tree runs from its own venv
(`agents/.venv`) which does not have the repo installed, so anything needing
`drydocs_core` re-derives the repo root and mutates `sys.path` at import time.

**Consequence, and it is fragility rather than ugliness.** `parents[2]` is a hard-coded
depth repeated nine times: move one of these files a directory deeper and it silently
computes the wrong root, and the failure surfaces at the NEXT line as
`ModuleNotFoundError: drydocs_core`, which reads as a missing dependency rather than a
wrong path. It is also import-time mutation of global interpreter state performed by
library modules, so importing any one of them reorders `sys.path` for everything else in
the process.

**Cheapest correction, in order:** install the repo into `agents/.venv` as a path
dependency, after which all nine preambles and all thirteen `E402` suppressions delete
and the imports become ordinary. If the two environments must stay independent — and
there is a real argument that they should, since `serve.py` documents the ADK venv as the
interpreter — then hoist the preamble into **one** module (`agents/common/_bootstrap.py`)
imported first, so the depth constant exists once and moving a file cannot silently break
it.

## Ranked

Three findings. The first is the most consequential thing this sweep has found; the other
two are ordinary debt with unusually clear correction paths.

1. **L1-1 — the acceptance runner cannot fail on an empty graph, in four of six suites.**
   `evaluate` treats `empty` as `len(rows) == 0` with no precondition; 28 of 30 committed
   assertions are negative; `folder-attribution-coverage.yaml` is 12 negative assertions
   with no anchor. A green run means "conforms" or "nothing was loaded" and cannot say
   which. Ranked first without hesitation: this is the gate the other checks report
   through, so a false green here does not mislead a reader, it **ends the inspection**.
   The fix is a per-suite anchor the runner asserts before evaluating, reporting NOT RUN
   rather than PASS — testable offline, because loader and evaluator are already pure.
2. **L2-1 — eighteen shims past a trigger that fired today, and the item that should
   retire them was never minted.** Eight in this slot, ten in slots 7 and 8. Ranked second
   because it is a scheduled action that silently did not happen, and because nothing in
   the repo will ever raise its hand: the shims work.
3. **L2-2 — nine copies of a `sys.path` preamble carrying a hard-coded `parents[2]`,
   and the thirteen `E402` suppressions that exist to serve them.** Ranked third because
   nothing is wrong today; the cost is that moving one file computes a wrong root and
   reports it as a missing dependency.

**Not ranked:** the strengths in L1-2 — the verifier that writes nothing and argues its
own gate-exemption from behaviour, the classification boundary stated at the file that
would breach it, and `unknown_targets` tying suites to the review backbone.

## Cross-links

**Between the lenses.** Lens 1 found a check that cannot fail; Lens 2 found a cleanup that
cannot be noticed. Both are **absences that no instrument in the repo is watching** — the
first because a vacuous pass looks like a pass, the second because a working shim looks
like working code. This slot's character is that its debt is invisible to every tool
pointed at it, which is precisely why a human-read sweep found it.

**To slots 9, 2, 3, 4, 5 — the completeness pattern is now six for six, and this is its
worst case.** Web truncated silently; load records no scope; lineage counts a tier with no
writer; api declares its ceiling and the console reads it; remediation omits its rule
denominator; and here **the tool that certifies the graph reports PASS against a graph
that is not there**. Every previous instance produced a wrong answer to a question someone
asked. This one produces a *right-looking* answer to the question "is the graph correct",
which is the question the others' answers are checked against. If slot 10 ranks the
recurrence anywhere, it ranks here.

**To slot 5 (`remediation`) specifically.** That module's `equivalence.py` was repaired for
this exact defect and named the remedy: three-valued, **not proven**, and *"no evidence is
never evidence."* `graph_verify` needs the same third state and does not have it. The
repo has now written the correct answer down twice (there, and in slot 3's `archival.py`
*"no axis proves absence"*) without either becoming a convention other components adopt.

**To slots 7 and 8, forward.** They own the other ten ADR 0018 shims. If L2-1 is groomed,
it should be groomed once for all eighteen — and those slots should not re-report it.

## Candidates for grooming

Five. None minted — the backlog pen is Lane A's and this firing holds neither it nor an id.

1. **Give `graph_verify` a per-suite precondition.** `drydocs-review`, p1. The suite
   declares an anchor (a `nonempty` case, or a minimum row count on a named label); the
   runner evaluates it FIRST and reports `NOT RUN` rather than `PASS` when it fails.
   Acceptance should require the four unanchored committed suites to gain anchors in the
   same change, or the mechanism ships without covering the cases that motivated it.
2. **Mint the ADR 0018 shim-removal item — once, for all eighteen.** Cross-component
   (`drydocs-review`, `drydocs-plan`, `drydocs-port`, `drydocs-docgen`). The ADR's own
   action item 6 says to mint it when the relay rolls; it rolled twice. If removal should
   wait, amend the trigger in the ADR **and** in the eighteen docstrings rather than
   letting a stated expiry pass silently.
3. **Retire the `agents` path preamble.** `drydocs-agents`, p3. Preferred: a path
   dependency on the repo in `agents/.venv`, which deletes nine preambles and thirteen
   suppressions. Fallback if the venvs must stay independent: one `_bootstrap` module so
   the `parents[2]` depth exists once.
4. **Decide whether "a result states the limits of its own method" is a convention.**
   Cross-module, slot 10's framing — now with six instances and three independent
   in-repo remedies (`equivalence.py`'s third state, `archival.py`'s coverage-on-itself,
   `drydocs_api`'s declared `truncated`). The item is "write the convention down and name
   the instrument", not "fix it again".
5. **Re-measure the rotation's size table.** Slot 10 or the plan's own maintenance. Four
   of six slots have come in over their plan-table size, this one by **+49%**. Either the
   table is a dated snapshot and should say so in the plan, or the rotation is balanced
   against numbers that no longer hold.

## Cross-links

*(step 6 — to the other lens in this firing, and to earlier slots)*

## Candidates for grooming

*(step 6)*
