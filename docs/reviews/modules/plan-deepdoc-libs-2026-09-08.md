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

*(step 3 — tests, guards, linter, counts; raw numbers recorded as they arrive)*

## Lens 1 — system design

*(step 4)*

## Lens 2 — technical debt

*(step 5)*

## Ranked

*(step 6 — the ranked list; its presence is what marks this report complete)*

## Cross-links

*(step 6 — to the other lens in this firing, and to earlier slots)*

## Candidates for grooming

*(step 6)*
