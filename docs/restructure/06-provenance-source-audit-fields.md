# 06 — Provenance diet + source audit fields (scope, approach, phases)

**Status: PLANNED — captured 2026-07-05, not started.** Groom into `backlog.yaml`
items before building; Phase 0 is an HITL gate session, not a coding task.

## Problem

Two related observations from loading Control-M out of Oracle:

1. **Load provenance out-muscles the domain graph.** Every loader run opens a
   `:JobRun` (PROV Activity, `kind='load'`) and MERGEs
   `(node)-[:WAS_GENERATED_BY {source:'BMC'}]->(run)` from *every touched node* —
   changed or not. A full refresh attaches ~240K edges to one run node, and repeated
   loads mean the generated-by/run-timestamp relationships **outnumber the true
   domain relationships**. This is the persona review's Issue 3
   (`docs/reviews/persona-neo4j-architect.md` — full-load `:JobRun` supernode,
   WARNING) plus a signal-to-noise problem in every exploration view.

2. **The time series is answering the wrong question.** The `:JobRun` chain is
   meant to carry *changes to the record*. A blanket full-refresh edge doesn't say
   "this record changed"; it says "we pulled it" — which is a **property-grade
   fact** (`last_pulled` / `last_seen_at`), not an edge-grade one. Meanwhile the
   fact that *is* worth first-class treatment — **who created and who last changed
   the record in the source system, and when** — is not carried into the graph at
   all: `controlm_jobs.sql` selects `J.AUTHOR` (SME: in this scenario `AUTHOR` is
   the Functional ID of the Control-M team, not an individual editor) but uses
   `CREATION_USER`/`CREATION_DATE`/`CHANGE_USERID`/`CHANGE_DATE` only as filter
   predicates; `controlm_folders.sql` does extract
   `LAST_UPDATED`/`LAST_UPDATED_USER`.

## Direction

- **Demote pull provenance to properties.** `first_seen_at` / `last_seen_at` /
  `last_run_id` already exist on several loaders — standardize them everywhere as
  the record of "when we pulled/updated this node."
- **Promote source authorship to a standard audit envelope.** Per node:
  `source_created_at`, `source_created_by`, `source_updated_at`,
  `source_updated_by` (names to be confirmed at the gate), mapped from each
  source's native columns (CM_ jobs: `CREATION_USER`/`CREATION_DATE`/
  `CHANGE_USERID`/`CHANGE_DATE`; CM_ folders: `LAST_UPDATED`/`LAST_UPDATED_USER`;
  other sources analogous but different).
- **Make `WAS_GENERATED_BY` mean "changed."** Attach the edge only when the
  record was created or actually changed (delta detection — the planned
  incremental loader already gives degree-proportional-to-delta runs). Full
  refreshes record row counts on the `:JobRun` node only, no per-node edges.
- **Each source declares its audit-field mapping in config, HITL-confirmed.**
  Every source carries a *similar but not identical* set of fields; deciding
  which source column means "created by" is an ontology-flavored call per
  dataset → it goes through the SME gate (`03-hitl-sme-flow.md`), exactly like
  taxonomy→ontology mappings. This is why the change is big: it touches the
  config layer, every loader, the vocabulary, and existing graphs.

## Scope

**In:** `drydocs/loaders/` (base + per-loader SQL/cypher), a new
`config/audit-fields.yaml` (per-source mapping, schema-guarded by a unit test the
way `classification.yaml` is), `relationship_vocabulary.yaml` note/status change
for `prov_was_generated_by` (through the gate), a migration for existing sandbox
graphs, `m3-verify` invariants, docs.

**Out:** UI work, the description-field metadata plan (separate, complementary),
calendar projection, company back-flow (gets a port-prompt/git-readme row when
this ships).

## Open use case to work through first (Phase 0 input)

What must the run/change time series actually answer? Candidate queries: "when
did this job last change in the source, and who did it" (audit envelope answers
this), "what did run X change" (delta-only edges answer this), "when did we last
sync" (`:JobRun` node + `last_seen_at` answer this). If nothing needs blanket
membership-of-a-load, the blanket edges have no customer — confirm at the gate
before deleting anything.

## Phases

- **Phase 0 — HITL field inventory + use-case definition (gate session).**
  Enumerate every registered source's audit columns; SME confirms the envelope
  property names and each source's column→envelope mapping; settle the time-series
  use case above. Deliverable: confirmed `config/audit-fields.yaml` (+ schema
  test), gate record. *No graph or loader changes.*
- **Phase 1 — Control-M audit envelope.** Extend `controlm_jobs.sql` /
  `controlm_folders.sql` extracts and their cypher to SET the envelope
  properties (normalize to `datetime()` — fixes the strings-as-dates review issue
  while touching these lines). Standardize `first_seen_at`/`last_seen_at`/
  `last_run_id` on all Control-M loaders. Tests per loader.
- **Phase 2 — provenance-edge diet.** Delta detection in loaders (checksum or
  version compare); `WAS_GENERATED_BY` only on create/change; full-refresh writes
  counts on `:JobRun` only. Vocabulary note updated via the gate.
- **Phase 3 — migration + cleanup.** Batched deletion of blanket
  `WAS_GENERATED_BY` edges on existing sandbox graphs (destructive → HITL
  confirm; `drydocs/migrations/` file like the ControlMFolder rename), backfill
  envelope properties where recoverable, update `m3-verify`.
- **Phase 4 — generalize to remaining sources.** SEAL, catalog, escalation,
  area-products loaders adopt the envelope from their `audit-fields.yaml`
  entries; per-source acceptance tests.
- **Phase 5 — docs + port row.** Loader README, NODE_QUICK_REFERENCE,
  ontology documentation; add the port-prompt/git-readme disposition row.

## Risks

- Edge deletion is destructive and the company copy has the same pattern —
  sequence producer-first, port with its own migration.
- `AUTHOR` vs `CREATION_USER` vs `CHANGE_USERID` semantics differ (author ≠ last
  editor); the gate must define each, per source, not globally.
- Property-only pull tracking loses per-run membership; confirm no consumer needs
  it (Phase 0) before Phase 2 removes it.

## Review record

- **2026-07-06 — Chad Wilson (SME), plan sign-off.** Direction and phasing approved
  for grooming into `backlog.yaml`. One clarification captured inline (Problem §2):
  Control-M `J.AUTHOR` is the Functional ID of the Control-M team, not an individual
  editor — carried forward as an input to the Phase 0 field gate. Envelope property
  names, per-source column→envelope mappings, and the time-series use case remain
  open for Phase 0 (unchanged by this review).
