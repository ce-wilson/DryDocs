# ADR 0002-A-1 — Phase B physical relocate: thin core extraction (amends 0002-A §6 step 4)

```yaml
status: ACCEPTED          # user-ratified 2026-07-10 (session decision, option A)
date: 2026-07-10
amends: docs/decisions/0002-a-drydocs-core-extraction-plan.md   # §6 step 4 + §5 packaging
deciders: Chad Wilson
principle: 0002-A "thin = define the boundary and move with zero behavior change; do not redesign"
```

## Context

ADR 0002-A (2026-06-26) planned the physical split as: move core modules out, then
**"rename the remainder to `drydocs-load`"** with per-package Poetry path dependencies.
That step was written when the remainder ≈ load only. By 2026-07-10 the remainder had
grown **four** component groups — load, review (Epic H), plan (Epic I), docgen (Epic L) —
all formalized in `tests/unit/test_module_boundary.py`'s default-deny tables. Executing
step 4 literally today would misname three components as "load", rewire the CLAUDE.md §6
gates (`import drydocs.cli`, the `drydocs` console script), split Poetry packaging on a
freshly-stabilized toolchain, and re-path **all 18** `drydocs/*` PORT-MANIFEST rows —
including the canonical-company back-flow paths (graph_review, publishing/**, gate_pages…),
the highest-friction collision class the manifest defines.

Measured blast radius (2026-07-10, both options move the same ~36 core files and rewrite
the same ~52 import lines):

| Additional surface under the literal split | Cost |
|---|---|
| Remainder move (~37 .py + sql/cypher/data dirs) | every company-side wired file replayed into new paths |
| 27 test + 3 script import lines → `drydocs_load` | churn with no boundary gain |
| 3 pyprojects + path deps | new risk on the Store-Python/Poetry setup |
| Gates + console script identity | CLAUDE.md, memories, company runbooks all edit |
| PORT-MANIFEST | all 18 rows re-pathed vs ~5 |

## Decision

**Thin extraction.** Move the 0002-A §2 core-marked modules physically into the existing
`drydocs_core/` package (the step-1 shim becomes the real package). The remainder **keeps
the `drydocs` package name**, hosting the four component groups; one Poetry distribution
as today; `drydocs` console script and the §6 gates unchanged. The borderline modules
resolve as 0002-A §6 already decided: `controlm/staging.py` relocates to the load side as
`drydocs/staging.py`; `snapshots/writer.py` stays load-side in place.

The remainder rename / per-component packaging is **deferred to Phase C**, where the
correct split is four packages (not one "load") — and where PORT-MANIFEST's sequencing
note already plans for it as a path-column diff. Packaging is separable from file
placement: making `drydocs-core` independently installable later is a packaging-only
commit with zero file moves.

## Consequences

- The core boundary is physically real: `drydocs_core` imports nothing from any component
  (boundary test now enforces it on real files, not a shim).
- The relocate ports as renames + import-line diffs; canonical-company paths untouched.
- G3 (spinoff rebase onto drydocs-core) is unblocked.
- 0002-A §6 step 4 and the §5 multi-package mechanics are NOT executed in Phase B; they
  move to Phase C's charter. 0002-A's done criteria are read accordingly: "drydocs-load
  runs the existing pipeline unchanged" = the `drydocs` remainder package, unchanged.
- Revisit at Phase C: 4-way component split, per-component pyprojects, load's final name.
