# Persona review — Python architect (code-graph Phase 1, U1)

> **Run: 2026-07-28** against the live `drydocs` database, snapshot
> `drydocs-20260728-0754.json` (commit `36866f9`), loaded by
> `drydocs load-code-snapshot` (194 modules, 105 IMPORTS). Plan:
> [`code-graph-review-plan.md`](code-graph-review-plan.md) (baselines probed
> 2026-07-27 at commit `4417d02`). Read-only — zero graph or backlog edits;
> actionable findings routed as IDEAS inbox lines.

## The headline finding first (it reframes four of the six units)

**F1 — the snapshot's IMPORTS edges are intra-root only.** The fresh
snapshot carries 105 edges and **zero** cross between the six scan
roots — while the code carries dozens of top-level cross-root imports
(confirming read: `drydocs/loaders/base.py:37-38` imports
`drydocs_core.cypher_split` and `drydocs_core.run_log` at module top level;
no such edge exists in `edges`). Query that found it: the A6 coupling query
returned `[]`; verification was a direct scan of the snapshot JSON for any
`drydocs_core` target from a `drydocs` source. Consequences, unit by unit:

- **A1 (layering) is VACUOUS as probed.** The plan's baseline "0 — clean"
  was true but unfalsifiable: the graph *cannot see* a core→app import, so
  it would report 0 even if one existed. The real layering guard is
  `tests/unit/test_module_boundary.py` (default-deny COMPONENT_GROUPS) —
  that is where the clean verdict actually comes from.
- **A6 (cross-root coupling vs MODULE_MAP) is empty by construction** —
  the comparison the plan wanted cannot be made from this graph yet.
- **A4's orphan signal has a 100% false-positive rate this run** (24/24 —
  see below): every "orphan" is imported cross-root by tests/, scripts/,
  or lazily by the `cli.py` composition root.
- **A5 (test-coverage shape) is vacuous**: tests→module edges are all
  cross-root, so *every* non-test module reports "no tests importer"
  (39/43 in `drydocs` — contradicted by the 1,054-test suite).

Scored (tech-debt rubric): Impact 5 + Risk 4, Effort 2 →
**(5+4)×(6−2) = 36 — the top item.** IDEAS line filed: extend the snapshot
scanner to resolve cross-root imports (mechanism note: it appears to scan
per root and only resolve targets inside that root's prefix). Until fixed,
treat A1/A5/A6 answers as *not evidence*.

## Unit-by-unit (baseline → current)

| Unit | Baseline (2026-07-27) | Current (2026-07-28) | Verdict |
|---|---|---|---|
| A1 layering | 0 — "clean" | 0 — **vacuous** (F1) | guard lives in test_module_boundary.py, not the graph |
| A2 circular | scanner says 0 | scanner flag 0 AND live `[:IMPORTS*2..6]` cycle probe 0 | **agree — healthy** (the §C3 disagreement-is-a-finding check passes) |
| A3 fan-in top | `loaders/base.py` = 18 | `loaders/base.py` = **19**; `drydocs_lineage/model.py` = 9 | intra-root ranking still valid (see F2/F3) |
| A4 orphans | 24 candidates | 24 candidates — **all 24 dispositioned NOT-dead** | signal unusable until F1 fixed |
| A5 test shape | unprobed | vacuous (F1) | do not publish these numbers |
| A6 coupling map | unprobed | `[]` by construction (F1) | — |

## F2 — `drydocs/loaders/base.py`, fan-in 19 (intra-root alone)

Query: A3. Confirming read: the 19 importers are the loader fleet + `cli.py`
— every loader inherits its lifecycle (JobRun envelope, D7 mark pass,
preflight, run-log). Any edit here is a fleet-wide change. Mitigations that
exist today: `test_base_loader_smoke.py`, the J9 e2e chain, and the fact
that the L17/Q8 guard family subclasses rather than edits it. Score:
Impact 4 + Risk 3, Effort n/a (this is a watch-item, not a defect) — keep
the plan's rule: **read base.py's diff history first in any review**.

## F3 — `drydocs_lineage/model.py`, fan-in 9 — new second hotspot

Wasn't on the baseline top list. Nine intra-root importers (extractors,
writer, tests-of-lineage via their root). Its identity contract
(`process_id`/`asset_id`, kind-scoped tokens) is exactly what the pending
G22 clause-f ruling may reshape — flag: when G22 rules on GUID-vs-URN,
budget for a fan-out edit here. Score: (3+3)×(6−3) = 18.

## A4 — the 24 orphan dispositions (each human-read; grep evidence)

Disposition key: **[blind-spot]** = imported cross-root (invisible per F1);
**[scripts-entry]** = imported by `scripts/*` (not a scan root);
**[cli-lazy]** = imported inside a `cli.py` command body (composition root).
None are dead code.

| Module | Disposition | Evidence (importer actually read) |
|---|---|---|
| drydocs/design_doc.py | scripts-entry + tests | scripts/render_design_doc.py:18; test_design_doc.py |
| drydocs/doc_outline.py | blind-spot (tests) | test_doc_outline.py:11 |
| drydocs/doc_pdf.py | scripts-entry + tests | scripts/doc_to_pdf.py:18 |
| drydocs/gate_pages.py | blind-spot (tests) + cli-lazy | test_gate_pages.py:6 |
| drydocs/graph_review.py | blind-spot (tests) | test_graph_review.py:4 |
| drydocs/graph_verify.py | blind-spot (tests) + cli-lazy | test_graph_verify.py:12; test_seal_attribution.py:20 |
| drydocs/plan_board.py | scripts-entry + tests | scripts/render_board.py:16 |
| drydocs/review_labels.py | blind-spot (tests) | test_review_labels.py:6 |
| drydocs/sme_notes.py | blind-spot (tests) | test_sme_notes.py:4 |
| drydocs/source_mappings.py | blind-spot (tests) + cli-lazy | test_source_mappings.py:13 |
| drydocs_core/config.py | blind-spot (cross-root) | drydocs/cli.py:60; drydocs_api/app.py:49 |
| drydocs_core/cypher_split.py | blind-spot (cross-root + in-root function-level) | drydocs/loaders/base.py:37 (TOP-LEVEL); neo4j_client.py:74 |
| drydocs_core/data_root.py | blind-spot (cross-root) | drydocs/cmdline_staging.py:59; rua_inventory.py:47 |
| drydocs_core/doc_anchors.py | blind-spot (cross-root) | drydocs/loaders/doc_traceability.py:38; drydocs/doc_outline.py:49 |
| drydocs_core/manual_mappings.py | blind-spot (in-root function-level + cross-root) | mapping_store.py:50; loaders/manual_loads.py:23 |
| drydocs_core/mapping_store.py | blind-spot (cross-root) | drydocs_api/mappings.py:120; loaders/manual_loads.py:62; scripts/build_mapping_db.py |
| drydocs_core/models/doc_traceability.py | blind-spot (cross-root) | drydocs/loaders/doc_traceability.py:32 |
| drydocs_core/ontology/namespaces.py | blind-spot (tests) | test_namespaces.py:6 |
| drydocs_core/ontology/schema_graph.py | scripts-entry + tests | scripts/render_schema_graph.py:18; test_schema_graph.py:16 |
| drydocs_core/precedence.py | blind-spot (cross-root) | drydocs/loaders/catalog.py:22; test_precedence.py |
| drydocs_core/run_log.py | blind-spot (cross-root) | drydocs/loaders/base.py:38 (TOP-LEVEL); cli.py:67 |
| drydocs_core/schema/supplements.py | blind-spot (cross-root + in-root) | drydocs/cli.py:68,71 |
| drydocs_core/source_registry.py | blind-spot (cross-root, cli-lazy) | drydocs/cli.py:152 |
| drydocs_lineage/curation.py | blind-spot (tests) | test_lineage_deepdoc_scaffold.py:17 |

Two entries above also expose a second scanner gap worth one line in the
fix item: `cypher_split` and `manual_mappings` have SAME-root importers
(`neo4j_client.py:74`, `mapping_store.py:50`) that are function-level
imports — also unrecorded. So the blind spot is cross-root **plus**
function-level, which means the gate-§D2 caveat ("IMPORTS cannot
distinguish import kinds") understated it: some import kinds are absent
entirely, not just indistinguishable.

## Ranked findings (Impact+Risk)×(6−Effort)

1. **36 — F1 scanner blind spot** (cross-root + function-level imports
   unrecorded) → IDEAS line (tagged `bug`). Until fixed: layering =
   test_module_boundary.py; orphan/coverage claims = do not publish.
2. **18 — F3 lineage/model.py hotspot** vs the pending G22 clause-f
   identity ruling → no action now; noted on the G22 agenda context.
3. **F2 base.py watch-item** — process rule already in the plan; no new
   action.
4. **A2 healthy** — scanner and live graph agree on zero cycles; no action.

## What this run proves about the method

The graph pointed, the files confirmed, and the biggest finding was about
the *instrument itself* — exactly the §C3 rule (a scanner/graph
disagreement is itself a finding). The next run of this phase is only
worth the session if the F1 fix lands first; A2/A3 remain useful today.
