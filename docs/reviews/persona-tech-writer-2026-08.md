# Persona review — Technical writer (code-graph Phase 3, Run 2)

> **Run: 2026-08-08.** Precondition executed and shown: `drydocs
> load-doc-traceability` against `drydocs` (desktop, `neo4jtest`) — 188
> doc sections, 16 DesignDoc nodes, 51 requirements, 55 components loaded;
> the `doc_feedback.v1` pass **refused again on the L17 :Employee guard**
> (exit 2), the same honest producer-state firing Run 1 recorded. Code
> graph: snapshot `drydocs-20260808.json`, commit `f156cc7`; repo total
> 804 post-squash commits (302 at Run 1). Style: all verdicts and prose
> per `docs/style/us-business-english.md`.
> Prior run: [`persona-tech-writer-2026-07.md`](persona-tech-writer-2026-07.md).

## Run 1 findings re-checked first (the mandate for this run)

| Run 1 finding | Status today | Evidence |
|---|---|---|
| 5 design docs cite pre-squash commits that dangle off main | **OPEN — all five unchanged** | `807e050`, `ac2ea2e`, `97ee81c`, `24d6a4b`, `0e036ff` all still unreachable from main; project-tdd was EDITED 08-06 and still carries `ac2ea2e` |
| startup-refresh runbook cites squash-day `a135a6d` | **OPEN — aggravated** | now Rev 10 (was 3): seven revision bumps since Run 1, last edit 08-06, citation never refreshed |
| mapping-demo runbook has no commit citation | **OPEN** | Rev 3, still the only design doc with no `commit:` at all |
| comma-split shears Component refs | **OPEN** | the same damaged refs verbatim: `DefinitionFormat` … schema-blocked)`, the truncated `K2 loader (…`, the remediation parentheticals, a bare `(planned)` stored as a ref |
| base.py + lineage/model.py cited by no component | **HALF-FIXED** | `base.py` now cited (``loaders `base.py` (`row_checksum`)``); `model.py` — fan-in now 24 — still cited by nothing |
| sdlc-*.md §DEP contradicts the post-G2 tree (3 rows) | **OPEN — all three** | see the §DEP section below |
| drydocs_core is the thinnest-documented root | **FIXED** | `drydocs-core-runbook` Rev 2 exists (env roots, provisioning, vocabulary registry, run logs) — plus three more new runbooks (below) |

The pattern across the open items is one behavior: **revision bumps happen,
citation refreshes don't.** Two docs (startup-refresh, mapping-store-runbook)
have each been re-revised since Run 1 without touching `commit:`; a
re-cite is clearly not part of anyone's edit ritual. The Run-1 IDEAS line
asked for a one-time sweep; this run's line asks for the sweep PLUS the
mechanism — otherwise Run 3 writes this table a third time.

## Doc-status board (all 16 docs/design/*.md)

"Behind" = commits from cite to HEAD (804 total post-squash);
**pre-squash = unreachable from main** (resolves locally only via the
`archive/old-history-2026-07-20` tag; dangles on a fresh clone).

| Doc | Rev | Cited commit | Behind | Last edit | Verdict |
|---|---|---|---|---|---|
| drydocs-load-runbook | 2 | 0b67b66 | 182 | 08-04 | **fresh** (new since Run 1) |
| drydocs-core-runbook | 2 | 416d217 | 187 | 08-04 | **fresh** (new) |
| drydocs-api-runbook | 2 | c28a4d1 | 191 | 08-04 | **fresh** (new) |
| drydocs-cmdline-resolution-runbook | 1 | ba6b83b | 432 | 08-04 | fresh-ish (new) |
| controlm-ingestion-tdd | 5 | c1c3a0a | 608 | 07-27 | aging, content consistent |
| drydocs-lineage-mac-runbook | 3 | 41c4879 | 603 | 07-23 | aging |
| drydocs-mapping-store-tdd | 1 | 22d1a39 | 649 | 07-22 | aging |
| drydocs-mapping-store-runbook | 3 | 22d1a39 | 649 | 08-04 | **stale cite, fresh content** — two rev bumps since Run 1, cite untouched |
| drydocs-startup-refresh-runbook | 10 | a135a6d | 777 | 08-06 | **stale cite, fresh content** — the Run-1 finding, seven revs later |
| drydocs-web-console-runbook | 1 | 6766b4c | 732 | 08-04 | stale-leaning |
| drydocs-mapping-demo-runbook | 3 | **none** | — | 08-04 | **no commit citation** (Run-1 finding, open) |
| drydocs-web-console-tdd | 1 | 807e050 | pre-squash | 07-21 | **citation dangles** |
| drydocs-project-tdd | 2 | ac2ea2e | pre-squash | **08-06** | **citation dangles — and the doc is actively edited** |
| drydocs-project-review | 1 | 97ee81c | pre-squash | 08-04 | citation dangles |
| drydocs-remediation-tdd | 1 | 24d6a4b | pre-squash | 07-20 | citation dangles; still the only PRESCRIPTIVE doc citing a dangling commit |
| graph-retrieval-benchmark-explainer | 2 | 0e036ff | pre-squash | 07-20 | citation dangles |

Re-verify queue (staleness × traffic): 1. project-tdd (edited two days
ago on a dangling cite), 2. web-console-tdd (most active epic),
3. remediation-tdd (prescriptive), 4. startup-refresh + mapping-store-runbook
(content fine — re-cite only), 5. mapping-demo (add the citation).

## Component.ref ↔ CodeModule.file_id — both directions

**Direction 1 (refs → code): one dead citation — a first.** Run 1
verified zero dead refs; today `config/taxonomy-ontology-map.yaml` is a
tombstone: S5 (2026-08-06) split it into the `config/taxonomy-ontology-map/`
fragment directory. The traceability matrix row now cites a file that
existed for every prior run and does not exist today. (The same S5 event
put five backlog `next_ready` items stale — see the U-pm file; one groom
pass fixes both surfaces.) Every other path-like ref verifies on disk or
in the graph, including the `drydocs_api/*` refs, which since U6+U9
verify in the GRAPH, not just on disk — retiring Run 1's census caveat.

**Direction 2 (heavy code → docs):** `base.py` is now cited — the Run-1
gap half-closed. `drydocs_lineage/model.py` (fan-in 24, the #2 hotspot
and the G22-reshape fan-out surface) is still cited by no component. The
new hotspots the all-files graph surfaced (`drydocs_api/query_specs.py`
14, `sessions.py` 12, `guard.py` 11) are partially covered by the
`drydocs_api/*` component refs; `query_specs.py` itself appears only as
the generic `drydocs_api/queries` component.

**Comma-shear (Run 1 bug, open):** the damaged refs are unchanged; the
count holds at 8-of-55-class damage, same examples. The fix options in
the Run-1 line stand (extend `_split_cell` for component cells the way
section-anchor cells already strip qualifiers, or tighten authoring).

## Coverage gaps by subsystem (post-U9 module counts)

| Root | Modules | Doc(s) of record | Verdict |
|---|---|---|---|
| drydocs | 115 | ingestion-tdd + load/startup/mapping runbooks | ok |
| drydocs_core | 71 | **core-runbook (new)** + mapping-store-tdd | **gap closed** (Run 1's thinnest) |
| drydocs_lineage | 19 | lineage-mac-runbook + cmdline-resolution-runbook (new) | ok |
| drydocs_api | 16 | api-runbook (new) + web-console-tdd | ok — and now measurable |
| drydocs_docmeta | 10 | ADR 0006 + MODULE_MAP row; **no design doc/runbook** | **the new thinnest** — same growth stage drydocs_core was at in Run 1 |
| drydocs_remediation | 7 | remediation-tdd | ok (but the doc's cite dangles) |
| drydocs_deepdoc | 3 | none | accept (3 modules) |

## §DEP regeneration check (sdlc-*.md) — all three Run-1 rows still open

| Doc claim (§DEP) | Reality | Status |
|---|---|---|
| `neo4j_client.py` at `drydocs/neo4j_client.py` (line 226) | `drydocs_core/neo4j_client.py` since G2 | **open** |
| `relationship_vocabulary.yaml` in `drydocs/ontology/` (lines 229, 511, 541) | now TWO moves behind: G2 put it in `drydocs_core/ontology/`, S5 (08-06) split it into `relationship_vocabulary/` fragments | **open — aggravated** |
| "OQ-NS-3: APOC availability unconfirmed" (lines 232, 575) | APOC is load-bearing (`run_script` uses `apoc.cypher.runMany`; the J9 e2e container installs it) | **open** |

The telling detail: `sdlc-neo4j-schema.md` line 357 carries a C23 note
added 2026-08-03 — the doc IS receiving edits, but only additive ones;
the stale §DEP rows sit untouched around fresh material. Same disease as
the design-doc cites: edits happen, verification sweeps don't. These two
files live under `docs/reviews/`, outside the design-doc render pipeline,
so no outline sweep will ever catch them — the fix has to be a deliberate
§DEP regeneration from the tree.

## IDEAS lines filed

- `[doc]` re-cite sweep, second filing — now 6 docs (5 pre-squash + the
  never-cited mapping-demo) plus 2 "stale cite, fresh content" cases;
  add the mechanism: a Rev bump must refresh `commit:` (renderer or test
  could enforce commit-reachability, which would catch both classes
  automatically).
- `[doc]` dead component ref: `config/taxonomy-ontology-map.yaml`
  tombstoned by S5 — re-point the matrix row at the fragment directory
  (fold into the same groom pass as U-pm's S5 input cluster).
- `[doc]` `drydocs_lineage/model.py` still uncited by any component
  (second filing; fan-in has since grown 9 → 24).
- `[doc]` sdlc-*.md §DEP rows, second filing — three rows, one of them
  now two moves behind; regenerate from the tree.
- `[doc]` `drydocs_docmeta` (10 modules) has no design doc or runbook —
  the same growth stage that produced the core-runbook after Run 1.
