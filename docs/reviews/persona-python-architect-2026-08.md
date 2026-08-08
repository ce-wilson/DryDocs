# Persona review — Python architect (code-graph Phase 1, Run 2)

> **Run: 2026-08-08** against the live `drydocs` database (desktop,
> `neo4jtest` — J18 venue), snapshot `drydocs-20260808.json` (commit
> `f156cc7`), loaded by `drydocs load-code-snapshot` (whole-tree per U9:
> 391 live `.py` modules / 830 IMPORTS; 273 `.py` in the U14 package scope).
> Plan: [`code-graph-review-plan.md`](code-graph-review-plan.md); canonical
> queries: the tech-debt skill's A1–A6 pack, run verbatim with the U13
> tombstone filter and the U14 `$packages` scope. Read-only — zero graph or
> backlog edits; actionable findings routed as IDEAS inbox lines.
> Prior run: [`persona-python-architect-2026-07.md`](persona-python-architect-2026-07.md)
> (2026-07-28, pre-U9 scope 205/370).

## What changed since Run 1

Run 1's headline (F1: zero cross-root and function-level IMPORTS) is fixed
and stays fixed: this graph carries 62 `drydocs→drydocs_core` edges, and the
A6 map is populated. A1/A4/A5/A6 are answered with real evidence for the
first time in a persona run. The 205/370 baseline in the run prompt is the
pre-U9 six-root scope; the deviation to 391/830 is the documented U9
whole-tree ruling, not drift.

## Unit-by-unit (baseline → current)

| Unit | Baseline (2026-08-04, package scope) | Current (2026-08-08) | Verdict |
|---|---|---|---|
| A1 layering | 0 | **0 — clean, and now falsifiable** (cross-root edges exist, so a violation would show) | healthy; corroborated by A6 (no core→app row) and `test_module_boundary.py` |
| A2 circular | 0 / 0 | scanner flag 0 AND live `[:IMPORTS*2..8]` probe 0 | **agree — healthy** (§C3 check passes) |
| A3 fan-in top | `loaders/base.py` = 29 | `loaders/base.py` = **31**; `drydocs_lineage/model.py` = **24** | see F2/F3 below |
| A4 orphans (package) | 0 | **0 — holds** | healthy |
| A4b first-party queue | 22 | **23 — but mostly FALSE orphans** (F1 of this run, below) | instrument finding |
| A5 untested | 29 | **27** (−2, improving) | list below; two docmeta connectors sit outside the scope (F4) |
| A6 coupling map | unprobed | 20 rows, all consistent with MODULE_MAP boundaries | healthy — and it surfaced `drydocs_docmeta` (F4) |
| Tombstones | — | 7, all non-`.py` (2 yaml re-homes, 5 superseded snapshot JSONs); zero `.py` | D7 working; consistent with the skill's note on the 2026-08-03 re-provision |

## F1 (this run) — residual scanner blind spot: imports rooted off the repo root

The A4b first-party queue (23 candidates in `agents/`, `scripts/`,
`knowledge/`) is mostly false. Mechanism, confirmed by file reads:

- `scripts/render_board.py:56-62` imports SEVEN sibling scripts by bare
  name (`import render_context_types`, `import render_gates`, …) — the
  graph records **zero** `scripts→scripts` edges. The same file's absolute
  `drydocs.plan_board` import IS recorded.
- `agents/` is not a package (no `__init__.py`); its runtime sys.path root
  is `agents/` itself, so modules import `from common import specs_catalog`
  and `from graph_qa.envelope import …` (`agents/graph_qa/pipeline.py:24-36`).
  The graph records **zero** `agents→agents` edges — while the same files'
  absolute imports (`agents/common/llm_ledger.py → drydocs_core/run_log.py`)
  ARE recorded.

So the U6 fix resolved absolute imports against the shared repo-root
namespace, but imports resolved at runtime **relative to a sys.path root
that is not the repo root** are still invisible. Consequence: every
`agents/graph_qa/*` module and four `scripts/render_*` modules read as
orphans when they are not. The genuine standalone candidates in the queue
are the self-contained tools (`scripts/extract_office_text.py`,
`knowledge/depgraph-snapshots/filter_ignored.py` and `probe_instrument.py`,
`knowledge/upgrade-plans/p0-benchmark/benchmark_p0.py`) — and those are
entry points, not dead code. Package-scope metrics (the A3/A4/A5 baselines)
are unaffected: the seven U14 roots all resolve from the repo root.

Scored (tech-debt rubric): Impact 3 + Risk 2, Effort 2 → **(3+2)×(6−2) = 20**.
IDEAS line filed: teach the depgraph extractor per-directory sys.path roots
(or an alias map `scripts/→''`, `agents/→agents/`), so the first-party queue
becomes trustworthy. Until then: treat the A4b queue as candidates only —
the standing rule already says so, and this run shows why.

## F2 — `drydocs/loaders/base.py`, fan-in 29 → 31, still #1

The two new importers track the loader-fleet growth (Epic-scale additions
since 08-04). Watch-item, not a defect; the plan's rule stands — read its
diff history first in any review. The mitigations noted in Run 1
(smoke test, J9 e2e, subclass-not-edit convention) are unchanged.

## F3 — `drydocs_lineage/model.py`, fan-in 24, confirmed second hotspot

Run 1 measured 9 at six-root scope; the all-files scope shows 24 (extractor
fleet + lineage tests + writer). The Run-1 flag still applies and has grown
teeth: the G22 sign-off (carried in the 2026-08-07 port) touched identity
rules, and any follow-on reshape of `process_id`/`asset_id` contracts is a
24-importer fan-out edit. Budget accordingly.

## F4 — `drydocs_docmeta` exists and the U14 allow-list doesn't know it

The A6 map shows `tests→drydocs_docmeta` (10) and `scripts→drydocs_docmeta`
(1). The package was born 2026-08-04 (`d647171`, Q6+Q12) — the same day the
U14 baselines were measured — with 10 modules, healthy test coverage (only
`connectors/filedrop.py` and `connectors/web.py` lack a tests-importer),
and its own MODULE_MAP row and `test_module_boundary.py` entry. But the
`$packages` allow-list in the tech-debt skill and the plan still names
seven roots, so every docmeta module is excluded from A3/A4/A5 metrics —
the same failure shape as Run 1's `drydocs_api` census miss, caught one
package generation later. Scored: Impact 3 + Risk 3, Effort 1 →
**(3+3)×(6−1) = 30 — the top item.** IDEAS line filed: add
`drydocs_docmeta` to the U14 allow-list (skill + plan), re-baseline A3/A5
at the eight-root scope, and note the two untested connectors while doing it.

## A5 — the 27 untested modules (package scope)

`drydocs_core`: `ontology/swo_adapter.py`, `config.py`, `doc_anchors.py`,
`manual_mappings.py`, `models/attribution.py`, `models/controlm.py`,
`orchestration/controlm/variable_report.py`, `orchestration/paths.py`,
`adapters/base.py`, plus 3 `__init__`-style aggregators.
`drydocs`: 5 loaders (`business_segments`, `controlm`,
`controlm_dependencies_derived`, `controlm_hosts`, `seal_contacts`),
`publishing/` ×3 (`assembler`, `preview`, `validator`), `snapshots/` ×2.
`drydocs_lineage`: 5 extractors (`controlm_xml`, `dpl_registry`,
`rua_code_ops`, `rua_inventory`, `snowflake_catalog`).
Direct-import proxy caveat applies (fixture/subprocess coverage invisible) —
the five loaders in particular are exercised through the e2e chain. No new
IDEAS line: the −2 trend is the right direction and the list matches known
debt, not a surprise.

## Ranked findings (Impact+Risk)×(6−Effort)

1. **30 — F4 docmeta missing from the U14 allow-list** → IDEAS line
   (metric blind spot; one-string fix + re-baseline).
2. **20 — F1 sys.path-root scanner blind spot** (`scripts/`, `agents/`
   in-region edges unrecorded; A4b queue untrustworthy) → IDEAS line.
3. **F3 lineage/model.py fan-in 24** — standing G22-reshape budget flag;
   no new action.
4. **F2 base.py 31** — watch-item, process rule already in force.
5. **A1/A2/A4 healthy** — and A1 is finally falsifiable evidence, not a
   vacuous zero.

## Method note

Run 1's biggest finding was the instrument; Run 2's top two findings are
ALSO the instrument (a scope list and a resolver gap) — but this time the
graph itself surfaced both (A6 exposed docmeta; A4b's shape exposed the
resolver gap), which is the §C3 rule working as designed. The structural
verdicts underneath (layering clean, zero cycles, orphan-free packages)
are now backed by falsifiable evidence.
