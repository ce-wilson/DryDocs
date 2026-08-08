# Persona review — Project manager (code-graph Phase 2, Run 2)

> **Run: 2026-08-08** against the live `drydocs` code graph (desktop,
> `neo4jtest`; snapshot `drydocs-20260808.json`, commit `f156cc7`) and
> `backlog.yaml` at the same commit (367 items: todo 84 / done 278 /
> in_progress 4 / blocked 1 — matches the test-enforced summary block).
> Plan: [`code-graph-review-plan.md`](code-graph-review-plan.md).
> ZERO backlog edits — mismatches route through IDEAS.
> Prior run: [`persona-project-manager-2026-07.md`](persona-project-manager-2026-07.md).

## Verdict up front

**Done-claims still hold: 271 path claims audited, zero false done-claims.**
The drift this run is in the OTHER ledger surface: **9 of the 62
`next_ready` items carry stale `inputs:` paths**, and seven of the nine
trace to a single event — S5's re-home of two ontology/config yaml files
into per-domain fragment directories closed without sweeping the items
that cite the old single-file paths. Run 1 found the instrument blind
(drydocs_api unscanned); Run 2's instrument is fixed (docmeta is visible,
closing that census class) and the findings moved to where a PM wants
them: grooming hygiene.

## Unit 1 — done-claims spot check

Method: every `done` item whose notes/acceptance carry a 2026-07-09..08-08
date (226 items), every `path/like.ext` claim extracted (271), verified
against the graph (`.py` → `:CodeModule.file_id`, tombstone-aware) and the
filesystem. 37 flagged by the mechanical pass; each human-read:

- **Relative-prose matcher artifacts (18)** — claims like
  `models/controlm.py`, `connectors/base.py`, `lineage/model.py`,
  `graph_qa/control.py`, `provisioning/01_databases.cypher`,
  `cypher/patch_window.cypher`, and the `web/src`-relative TS paths
  (`lib/auth.ts`, `components/Shell.tsx`, …): the full paths all exist.
  Claim TRUE in every case.
- **Leading-dot regex drops (4)** — `claude/skills/...`,
  `github/workflows/ci.yml`: the real `.claude/`/`.github/` paths exist.
- **Recorded moves (3)** — `drydocs_core/controlm/resolver.py` →
  `drydocs_core/orchestration/controlm/` (G2 Phase B, its own done item);
  `docs/runbook-mapping-demo.md` → relocated by L14; `docs/controlm-loader-flow.md`
  → `docs/history/` (J11 WAS the mv item). Self-consistent history.
- **Recorded deletions (4)** — C18 (deletion was the acceptance), C19
  (never-ported path quoted deliberately), J6's `scripts/ingest_jpmc_reports.py`
  (removed `5eb68bc`, registry records it), U13's
  `drydocs_core/controlm/__init__.py` (the tombstone proof case, quoted).
- **Tombstone hits (6, the new disposition class)** —
  `config/taxonomy-ontology-map.yaml` (cited by C6/K12/N4/S5) and
  `drydocs_core/ontology/relationship_vocabulary.yaml` (S5): both
  tombstoned 2026-08-06 when S5 split them into fragment DIRECTORIES
  (`config/taxonomy-ontology-map/`, `…/relationship_vocabulary/` — both
  verified on disk). Existed-then-removed, exactly the disposition the
  plan said tombstones would enable. Historical claims TRUE.
- **Remaining (2)** — regex artifacts of prose punctuation (O42's
  `MODULE_MAP.md/test_module_boundary.py`, U9's doubled `drydocs/drydocs/`).

**Zero real drift in the done ledger.**

## Unit 2 — module-registry census

Graph regions (25 live) vs the 18-module registry: every Python package
root is registry-claimable, including **`drydocs_docmeta` (10 modules) —
the census gap class Run 1 found with `drydocs_api` is closed**; the graph
now sees every package the registry names. `web` (118 files) belongs to
drydocs-web (TS — file nodes only, no IMPORTS, by design). Regions with no
registry module, all explainable but worth their one-line dispositions:
`.claude` 454 (vendored, U14's exclusion rationale), `UI-WIP` 34 (working
area, two-track plan), `internal` 53 / `external` 33 (classification
homes), `libs` 4 (the oracle_kerberos utility — no module row),
`SDLC-Docs` 6, `graph-tests` 6, `drydocs-icons` 3. None of these is a
zombie; the only borderline row is `libs/` — a shipped, tested utility
that no module in the registry claims. Noted for the next groom, not
filed as a defect.

## Unit 3 — todo reality check (the finding this run)

62 `next_ready` items; **9 carry inputs that no longer resolve**:

| Item(s) | Stale input | Cause |
|---|---|---|
| Q14, G34, U10, U11 | `drydocs_core/ontology/relationship_vocabulary.yaml` | S5 split it into `relationship_vocabulary/` fragments (2026-08-06) |
| G34, U10 | `config/taxonomy-ontology-map.yaml` | same S5 event — now the `config/taxonomy-ontology-map/` directory |
| Q15, R11, R12 | `web/src/routes/ask/` | ask module lives at `web/src/ask/` + `routes/AskRoute.tsx` — no `routes/ask/` subdir |
| U10 | `knowledge/depgraph-snapshots/drydocs-20260802.json` | newest-only retention deleted it — any dated-snapshot input goes stale BY DESIGN; should say "newest snapshot" |
| R9 | `docs/reviews/persona-architect-2026-07.md` | filename typo — actual file is `persona-python-architect-2026-07.md` |
| V4 | `drydocs/review/` | no such directory — review modules are flat files (`drydocs/graph_review.py`, `review_labels.py`, `sme_notes.py`) |

Per the plan's rule, these items need a re-groom before an agent burns a
session on them — the S5 cluster especially, since five sits high in the
pull order. One IDEAS line filed covering all nine (single groom pass),
plus the structural half-line: items should cite the snapshot DIRECTORY,
never a dated snapshot file, because retention makes dated cites
self-staling.

Status hygiene, same unit: the four `in_progress` items are E1 (since
2026-06-22 — a deferred gate wearing an active status; the others are
G32/G35 gate sessions and Y1's sharding design, all legitimately open).
E1's status reads as work-in-flight to any pull-rule agent when it is
actually waiting-on-gate-scheduling; half a line in the same IDEAS entry
suggests re-statusing it `blocked` at the next groom. K16 `blocked` is
correctly labeled.

## Unit 4 — per-epic code footprint (recent closes)

18 epics with recent closes; roots touched match charters everywhere it
matters: component-topology spans packages by design; web-console touches
`web`+`drydocs_api`+generated surfaces; docmeta touches `drydocs_docmeta`
+registry+config; release-infrastructure touches CI/scripts/skills;
fcdo-alignment stayed inside `config`+vocabulary fragments. No epic's
footprint contradicts its charter. The Run-1 caveat (the two most active
epics under-measured because the graph couldn't see `drydocs_api`) is
retired — the graph sees all their roots now.

## IDEAS lines filed

- `[chore]` next_ready input re-groom: 9 items, 6 causes (S5 fragment
  split ×5-item cluster, ask-route path ×3, retention-deleted snapshot
  cite, persona filename typo, `drydocs/review/` flat-file reality);
  plus rule-of-thumb "cite the snapshot dir, not a dated file" and the
  E1 status question.

Nothing else actionable: the done ledger, roll-ups, census, and epic
footprints all verified true.
