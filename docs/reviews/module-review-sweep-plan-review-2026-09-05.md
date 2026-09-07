# Secondary review — the module review sweep plan and the slot 9 web findings

- **Reviewed at:** commit `6743ee9d` on `main`, port base `port-base-20260902`; venue MSI. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*
- **Subject:** `docs/reviews/module-review-sweep-plan.md` as first committed at `e44cc5b4` on `review/module-sweep` (the plan behind cron job `55bbce67`, `47 6 */2 * *`, first firing 2026-09-07), the DOC4 item that carries it, and the twenty-four findings of the three-pass web review (A1–A8, S1–S8, T1–T8) that produced it.
- **Scope:** the plan text, `drydocs_core/component_map.py` as the object the plan's scope rule should read, DOC4's `inputs` and clauses, and every headline count in the three passes re-measured on `main`.
- **Method:** read the plan as the firing session would (section 4, step by step, on a clean worktree); walk each derivation and fence rule against what the tree actually holds; re-run every count the passes recorded; classify each finding against the items that already exist. This review decides nothing — a review proposes; a gate rules. Where a plan fix was small and unambiguous it was applied and is marked so.
- **Reviewer pen:** `reviews` (Lane A, desktop). The plan fixes landed on `review/module-sweep` at `5f02599f` and reached `main` by the `--no-ff` merge `6743ee9d`, the first merge of that branch to trunk.

## Part A — the plan

Six findings. R1 is the question the ui-workstream session asked at handoff; R2–R6 came from reading the plan the way a firing would.

### R1 — The sweep is not a trunk session and must not run the trunk's close ritual (applied)

The handoff asked whether `knowledge/depgraph-snapshots/snapshot.ps1` belongs in the cron. It does not, and neither does any other close step of CLAUDE.md section 0 step 3. Those steps — render the board, render the design docs, check CI, snapshot — record the state of TRUNK after a trunk push. A firing pushes no trunk commit: it writes one report under `docs/reviews/modules/` on `review/module-sweep`. There is nothing for the ritual to record, and running the snapshot from a branch venue would write a trunk artifact (a dated JSON keyed to a commit) from a tree that is not trunk. `snapshot` is also a Lane A pen (`lane-handoff` rule 2: the machine holding `backlog` renders once and snapshots once at its close), so a firing that ran it would be writing a surface it does not hold.

The plan at `e44cc5b4` was silent on this — it excluded renders and the backlog but not the snapshot — so a diligent firing could have reached for the session ritual and run it. Applied: section 6 now names all four close steps as excluded, with the reason. The snapshot for this window runs at Lane A's own close, as it should.

### R2 — The derived slot state had no fixed key, and the scope was typed by hand (applied)

Section 2's derivation listed `docs/reviews/modules/` and matched reports "for that family", but a family was named three ways in the plan (`drydocs-review + drydocs-agents`, `review+agents`, the template's `<family>`). Two firings on two machines could spell one family two ways, each conclude the other never ran, and both review the same slot. The state is derived, which is right; a derivation needs a key it cannot misspell.

The scope column, likewise, was a hand-typed list of module names, so a module that moves between components (the S-series did this to a dozen of them) would silently stay in its old slot.

Applied: a `slug` column (`core, load, lineage, api, remediation, review-agents, port-docgen-docmeta, plan-deepdoc-libs, web, seams`) that the filename carries and the derivation matches on; and a scope rule that reads `drydocs_core/component_map.py` — `COMPONENT_GROUPS` joined to `COMPONENT_MODULE` for slots 2–8, `CORE_PREFIXES` for slot 1 — the importable object (J37), with the report's `scope:` line recording what resolved at that firing. Slot 9 is the two `drydocs-web` directories in `MODULE_MAP.md`; slot 10 is `test_module_boundary.py` and `component_map.py` themselves.

### R3 — Step 0 rebased a pushed branch (applied)

Step 0 said `git pull --rebase` and rebase onto `origin/main`. `review/module-sweep` is pushed and both machines may run a firing, so rewriting its history strands the other machine's copy — the J31 shape, from the other direction. Applied: `git pull --ff-only` then `git merge --no-edit origin/main`; never rebase, never `--force`. Only the plan and `docs/reviews/modules/` can conflict, and they resolve on the branch.

### R4 — A half-dead firing was finished by the next one in the acceptance, but not in the derivation (applied)

DOC4 clause (d) says a half-dead firing is finished rather than duplicated. The derivation did not do that: a report opened and stamped at step 2 (before any code is read, per the autocompact protocol) counts as "the most recent report for that family", so the next firing would skip the slot and leave the partial report partial for a full cycle. Applied: a report with no `## Ranked` section is partial and is resumed (section 2 step 3, section 4 step 2), never duplicated.

### R5 — The one report the derivation needed to see was not on disk (applied)

Section 2 placed `drydocs-web` last because it "was reviewed on 2026-09-05", but the three passes lived only in a session scratchpad. `docs/reviews/modules/` was empty, so the derivation would have taken slot 9 as never reviewed, and the second pass would have had nothing to move against. Applied: the three passes landed verbatim as `docs/reviews/modules/web-2026-09-05.md` on the plan's template, headings demoted one level under one H2 per lens, with a `## Measured` section holding the re-verified counts (part B) and a `## Ranked` section across the passes. Its `reviewed_branch` line states what the reviewed tree was: `feat/cyclic-type-test-case` in the ui-workstream worktree, a merge of `origin/main` into that branch, with nine `web/` files differing from `main` at `bcae4d02`, four of them generated JSON and none of them a finding's site.

### R6 — The plan was unreachable from `main`, and DOC4 cited it (applied)

DOC4's first `inputs:` entry is the plan, and DOC4 is on `main`; the plan was only on the branch. A reader of the item on `main` — or the docs-coverage guard, had it been asked — would find a dangling input. Applied by the `--no-ff` merge `6743ee9d`, docs-only. The plan's own "no merge to main" rule is a rule for the SWEEP (it merges nothing); a human merging when the findings are wanted in trunk is exactly what the plan provides for, and section 6 now records this merge as the first.

### DOC4

Clauses (a)–(h) hold as written; (i) still waits on the first real firing. The only defect was R6, now closed. One note for the closer: clause (f) says "writing only `docs/reviews/modules/` and the plan", and the secondary review wrote both from outside the sweep — that is within the fence's intent (a human, on the branch, then merging), and the plan's provenance line records it. Nothing else to change on the item.

### Not changed, and why

- **The ten-slot sizing and first-cycle order.** Measured, recorded with exclusions, and re-measured per clause (b). Sound.
- **The scheduler as the weak half.** The plan is honest that a session-only cron cannot carry a twenty-day rotation, and it deliberately declines a CLAUDE.md re-arm step. Agreed; the plan is what a session runs from.
- **Slot 10 (seams).** The web review's strongest conclusion was cross-lens, and no single-module slot can reach it. Keep.

## Part B — the twenty-four web findings

### B1. Verification on `main` at `bcae4d02`

Every count the three passes recorded was re-measured on trunk before grooming. All held; the table is the `## Measured` section of the landed report, and is not repeated here beyond the two that decide item shape:

| finding | measurement on `main` | consequence for grooming |
|---|---|---|
| S1 | `drydocs_api/query_specs.py` `_LIMIT` default 500 shared by ~40 specs; `drydocs_api/exports.py` manifest carries `row_count`, no truncated flag; no `web/` caller passes `limit` | the fix is a READ-CONTRACT change on the API side first (`API1`), with the web rendering as a dependent item (`WEB2`) — one item could not sit in one module |
| A5 / S6 / S8 | eleven demo modules; five routes with five fallback presentations; `/health` uncalled; no fallback counter | one seam item (`WEB1`), because the readiness probe, the provenance union and the activation counter are three views of one decision |

### B2. Grouping into items

Sixteen items, one per decision the builder has to make, so a pull is one coherent change. Titles are FINAL at the stub (the collision guard compares titles). The finding ids each item covers are in its `notes:`; every item cites `docs/reviews/modules/web-2026-09-05.md` in `inputs:`.

| item | covers | rank in the report | prior items touched |
|---|---|---|---|
| `WEB1` | A5, S6, S8 (fallback counter) | 2, 8, 14 | O63 (the probe it should share) |
| `API1` | S1 (server side) | 1 | R15 (the Ask cousin) |
| `WEB2` | S1 (console side); depends on `API1` | 1 | R15 |
| `WEB3` | A1 | 4 | O59 (the shipped bug) |
| `WEB4` | A3 | 5 | O70 |
| `WEB5` | S7 | 9 | — |
| `WEB6` | T5 | 5 | — |
| `WEB7` | A4, S8 (bundle budget) | 10 | O34 (deferred splitting explicitly) |
| `WEB8` | A2, T3 | 12 | O70 (the `unwrapAs` follow-up it left) |
| `WEB9` | S2 | 3 | — (ADR candidate, gate-bound) |
| `WEB10` | S3 | 7 | O72 (Compose stack) |
| `WEB11` | S4 | 6 | O64 (a chosen persistence it must respect) |
| `WEB12` | A6, T6, S5, S6 (dedupe) | 8 | — |
| `WEB13` | T1, T2, T7, T8 | 11, 5, 14 | O43 (the seed suites), O34 (the advisory count) |
| `WEB14` | T4 | 13 | — |
| `WEB15` | A8 | 14 | — |

Three findings are ADR candidates and say so in their items (`WEB3` route authorization, `WEB1` provenance union, `WEB9` credential carrier, `WEB10` delivery shape, `API1` result completeness); the items build nothing that pre-empts the ruling and each names what the ADR must decide.

### B3. What was not groomed

- **A7 as its own item.** It is T1 with a measurement attached; `WEB13` carries the ratchet and O43 already holds the seed suites.
- **T8's font subsets and the two one-file directories.** Deploy weight only, and a directory move with no behavioral change; both noted in `WEB13` as optional residue, not acceptance.
- **S5's "no retry".** The report itself calls no-retry a defensible choice for a read console that should be stated rather than omitted; `WEB12` states it.

### B4. Sequencing the builder should respect

`WEB4` (strict) before `WEB6` (validator) and `WEB8` (typed client) — the compiler has to be on for either to mean anything. `API1` before `WEB2`. `WEB12` (the data-layer hook) before `WEB1`'s seam lands its final shape, or the seam is written twice. Everything else is independent. The three gate-bound items (`WEB9`, `WEB10`, and the ADR halves of `WEB1` / `WEB3`) can be drafted now and built after their ruling.
