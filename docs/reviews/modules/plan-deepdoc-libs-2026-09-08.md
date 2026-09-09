# drydocs-plan + drydocs-deepdoc + drydocs-libs — module review, 2026-09-08

reviewed_commit: 9389f246
reviewed_branch: review/module-sweep (worktree review-sweep; origin/main merged at the start of this firing — it had moved since slot 7, carrying tests/unit/test_ci_verdict.py and tests/unit/test_port_rename_check.py)
reviewed_port_base: port-base-20260908 — producer-side review
slot: 8 of 10 (slug `plan-deepdoc-libs`)
lenses: system-design, tech-debt (the standing sweep's two; architecture was a one-off on the web slot)
scope: the dotted prefixes of `COMPONENT_GROUPS['plan']`, `['deepdoc']` and `['libs']`, read from
  `drydocs_core/component_map.py` (J37, the importable object) at this firing — 5 prefixes:
  `drydocs.plan`, `drydocs.plan_board`, `drydocs.plan_roadmap`, `drydocs_deepdoc`, `libs`
prior report: first pass

- **Reviewed at:** commit `9389f246` on `review/module-sweep`, port base `port-base-20260908`; venue MSI. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*

Opened before any module code was read (section 4 step 2): this file is the durable
memory for the firing, so a session that compacts mid-review resumes here rather than
starting again. Sections below are filled in order and each is committed as it closes.

**The last module slot. Three components, and `deepdoc` is the one with a stated
epistemic contract to test.** `drydocs_deepdoc` is the REACTIVE, UNCERTAIN half of the D2
split that slot 3 read from the other side: `drydocs_lineage` writes curated ground truth,
and deepdoc's writes carry the `:Uncertain` label since the G102 fold. A component whose
entire job is to hold uncertain material correctly is the natural place to test this
sweep's recurring question one last time before slot 10 generalises it.

**Two inheritances recorded so they are not re-derived.**
1. **ADR 0018 shims.** Two of the eighteen live here (`plan_board`, `plan_roadmap`). Slot 6
   found the removal trigger fired and recommended ONE cross-component grooming; slot 7
   declined to re-report for the same reason. This report counts them and does the same.
2. **The `_git` shape.** Slot 7's candidate 2 asked the next slots to check whether
   `subprocess.run(..., check=False)` returning bare `.stdout` recurs outside
   `drydocs/port/`. That check belongs to this firing and is carried out in Lens 2.

## Measurements

Taken before any module code was read.

| module | lines | files |
|---|---|---|
| `drydocs/plan/` | **985** | 3 — `plan_board` 647, `plan_roadmap` 332 |
| `drydocs_deepdoc/` | **674** | 5 — `mindmap` 352, `search_log` 203, `__init__` 67, `investigate` 33, `writer` 19 |
| `libs/` | **553** | 2 — `oracle_kerberos/spider_login.py` 548 |
| ADR 0018 shims in scope | 24 | 2 × 12 (`plan_board`, `plan_roadmap`) |
| **combined** | **2,236** | against the plan table's 2,188 — **+2%** |

| | |
|---|---|
| tests naming any of the three | **14** files |
| scoped suite | **268 passed, 0 skipped**, 48s |
| `ruff check drydocs/plan/ drydocs_deepdoc/ libs/` | clean |

**The smallest slot, and the second to land on its plan-table size** (+2%, after slot 5's
exact match). Five of eight slots ran over; the two that did not are the two whose last
builds closed.

### Slot 7's carry-over check, answered: the `_git` shape does NOT recur

Slot 7 asked the next slots to find out whether `subprocess.run(..., check=False)`
returning a bare `.stdout` appears outside `drydocs/port/`. Searched across `drydocs/`,
`drydocs_core/`, `drydocs_deepdoc/`, `libs/`, `drydocs_lineage/` and `drydocs_api/`.

**Two sites outside the port component, and both handle failure correctly:**

| site | what it does |
|---|---|
| `drydocs_core/adapters/controlm/api.py:377` | `_default_runner` returns the **`CompletedProcess`** — the caller sees `returncode` and `stderr`. This is precisely the fix slot 7 recommends for `_git`. |
| `drydocs_core/landing_zones.py:171` | catches `OSError`/`SubprocessError` **and** checks `done.returncode != 0`, returning 0 on either |

**Zero occurrences in this slot's own modules.** So `port_preflight._git` is a lone
outlier across the whole repository, not an idiom — which strengthens slot 7's L1-1 and
**narrows its candidate 2 from "sweep for the others" to "there are none; fix the one."**
Recorded here so slot 10 does not re-run the search.

## Lens 1 — system design

**The last module slot answers the sweep's recurring question correctly in both halves
that face a reader** — and that is the finding, because it means the remedy is not rare,
it is unwritten. One modest defect: a docstring at an entry point still describes a
charter the package retired.

### L1-1 — `investigate.py` documents the retired charter, and it is the file a reader opens first

`drydocs_deepdoc/__init__.py` states the current charter, ruled at gate
`document-content-topology` (G32, 2026-08-18) and restated at MM1 (2026-08-21): deepdoc is
a **corpus-driven retriever seeded from the grounded graph**, and — explicitly —
*"the earlier 'reactive on-failure deep dive' into a separate uncertain database is
**retired**."*

`drydocs_deepdoc/investigate.py` opens with:

> *"On-demand deep dive — a failure names the job/folder; this derives context."*

That is the retired model, stated as the module's purpose, in the module that holds the
component's entry point (`investigate_failure(job_name, folder_name)`). The two documents
in one package disagree about what the component is, and the stale one is the one whose
name a reader reaches for.

**Consequence, calibrated honestly.** Nothing can act on it wrongly — `investigate_failure`
raises `NotImplementedError` and has no production caller (only two tests, one asserting
the raise). The cost is orientation: in a repo whose method is *read the code and the
prose beside it*, a reader or an agent seeded from `investigate.py` learns a model that a
signed gate retired three weeks ago. This sweep has twice been slowed by exactly that class
of thing, and both times the report recorded it so the next firing would not pay again.

**Cheapest correction:** rewrite the one docstring to the G32/MM1 charter, or delete
`investigate.py`'s prose down to a pointer at `__init__`. Two lines, no behaviour.

### L1-2 — the scaffold states its own scaffold status, which is the honest version of this sweep's question

`__init__.py` carries, verbatim:

> **Scaffold status:** interfaces + contracts (G4, 2026-07-10); the `investigate` and
> `writer` bodies raise `NotImplementedError` until MM10. `mindmap` and `search_log` (MM3)
> are real.

Checked and true on this tree: `investigate_failure` and `write_findings` both raise on
their first line; `mindmap.py` (352) and `search_log.py` (203) are implemented. **A
component that says which of its own parts are real is the completeness contract this
sweep has been chasing, applied reflexively.** It is why L1-1 above is a docstring nit
rather than a finding about a component pretending to be finished.

### L1-3 — `plan_board` distinguishes "none done" from "nothing to do"

`drydocs/plan/plan_board.py:203-204`:

```python
pct = round(100 * done / total) if total else 0
progress_text = f"{done} / {total}" if total else "no items"
```

A phase with no items renders **"no items"**, not `0 / 0` and not a 0% bar. That is the
third state, in the governed render a human actually reads, on the surface CLAUDE.md
requires to be published verbatim.

**This is the fifth independent in-repo remedy for the pattern this sweep has found in
every slot**, after `equivalence.py`'s **not proven**, `archival.py`'s coverage-on-itself,
`drydocs_api`'s declared `truncated`, and `port_preflight`'s *"SKIPPED — not a
certification"*. Counting deepdoc's scaffold-status paragraph as a sixth. **Six correct
implementations, zero written conventions** — which is the strongest form the argument for
slot 10's rule can take: nobody needs convincing that this is right, and it still does not
travel between components.

### L1-4 — what else is right, recorded so no later firing re-audits it

- **The board is deterministic and says why.** *"Given the same backlog tree,
  `render_board` always produces byte-identical HTML — no build timestamps, no randomness.
  The board is committed to git, so its diffs must reflect real backlog changes, not render
  noise."* The header carries the item count **instead of** a build time (ADR 0013).
- **The board names the system of record and its own status.** *"The repo (`backlog/`) is
  the system of record; the browser is a working aid"* — `localStorage` is convenience
  only, and quick-capture copies a line for a human to paste rather than writing to the
  repo.
- **deepdoc's write boundary is one module and says so.** `writer.py` is *"the ONLY module
  in the component that writes a database"*; every node and edge carries `reliability` and
  `trust` (*"a finding without stamps is a contract violation"*); proxy nodes MERGE on the
  URN business key so ground-truth properties are never copied across the boundary; and
  promotion is explicitly not its job.

## Lens 2 — technical debt

*(step 5)*

## Ranked

*(step 6 — the ranked list; its presence is what marks this report complete)*

## Cross-links

*(step 6 — to the other lens in this firing, and to earlier slots)*

## Candidates for grooming

*(step 6)*
