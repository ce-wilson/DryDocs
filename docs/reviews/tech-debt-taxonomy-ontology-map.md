# Tech-debt audit — the taxonomy→ontology mapping layer

> **TRACKING (2026-07-11):** findings F1–F4 EXECUTED pre-groom (`c396d75`, `ede0b94`);
> the remaining structured-fields work rides backlog **C7** (vocab_id required +
> capture taxonomy-or-waived at the next gate), `todo`/ready — gate-timed by design.
> This report is the rationale record, not the open-work list.

**Date:** 2026-07-09 · **Scope:** `config/taxonomy-ontology-map.yaml`,
`drydocs/ontology/relationship_vocabulary.yaml`, `config/taxonomy/*`, the schema
supplements, and the guards (`tests/unit/test_schema.py`) · **Method:** `/tech-debt`
framework (Impact + Risk) × (6 − Effort) · **Classification:** Internal-Public.
*Reviewed on `feature/drydocs-remediation` (carries the CM_HOSTS/CM_AVG_RUN map
entries); main's concurrent C6/SchedulerKind commits (`761a201`, `fa7a00c`) reviewed
via `git show` — that same-day churn on both branches is itself evidence below.*

**Headline: the map file that calls itself "THE central artifact of the configuration
layer" is the only ledger in the repo with ZERO test coverage.** Its three siblings all
have typed accessors + guards (`backlog.yaml`→`test_backlog`, `source-mappings`→
`test_source_mappings`, `source-registry`→`test_source_registry`/`test_classification`);
`test_schema.py` guards the *vocabulary*→supplement edge but never opens
`taxonomy-ontology-map.yaml`. Every failure mode below is one the sibling guards
already prevent elsewhere.

---

## Findings

### F1 — The map is unguarded (test debt · the root item)
No test reads `config/taxonomy-ontology-map.yaml`. Nothing asserts: the `schema:` id;
the lifecycle enum (`proposed|confirmed|applied|rejected`); unique entry ids; that
`confirmed` entries carry `confirmed_by`/`confirmed_on`; or the `summary:` counts.
Consequence seen **today**: the hand-bumped summary counts were edited by two sessions
concurrently (this branch's CM_HOSTS gate + main's C6 refine) — the identical
hand-maintained block in `backlog.yaml` produced a real merge conflict this afternoon,
and only survived because `test_backlog` recomputes it. The map has no such net.
Also stale and unnoticed: `updated: 2026-06-20` on a file whose newest entries are
2026-07-09.

### F2 — The `applied` lifecycle stage lives in comments (lifecycle drift)
Census: **23 `confirmed` / 1 `applied`** — yet at least five confirmed mappings have
live loaders, tracked as `# APPLIED 2026-07-07 …` comments (5 occurrences) instead of
`status: applied`. The fourth lifecycle stage exists in the header contract but is
unused in practice, so "what is actually loaded into the graph" cannot be queried from
the map — it must be reverse-engineered from loader code. The one honest `applied`
entry (`job-contains`) proves the stage was meant to be real.

### F3 — `reuses_vocab` is free text with rotting status parentheticals (dual source of truth)
27 distinct formats observed: `m3_scheduled_on (active)`,
`arch_develops (planned -> set active in C4)`, a four-id slash-composite, and one
anchor path into `node_classifications`. The parenthetical status is a **copy** of
`relationship_vocabulary.yaml` state at write time — it rots on every status flip, and
no check confirms the id even exists in the vocabulary. Same class of problem: the
map duplicates `from_node`/`to_node`/`neo4j_label` per entry, and nothing asserts the
two files agree (the RUNS_ON label reassignment precedent shows renames do happen).

### F4 — Duplicate `Document` node classification (code debt, latent bug)
`node_classifications` contains **two** `- label: Document` entries (the SEAL-reshape
proposed one and the docs-corpus active one). Same CURIE today, but which entry a
reader resolves is implementation-dependent, and their `note`/status semantics differ
(proposed-docmeta vs gate-accepted lexical corpus). `test_vocabulary_no_duplicate_ids`
covers relationship ids only — labels are unchecked.

### F5 — Taxonomy-first rule vs. practice (process drift)
CLAUDE.md §1: capture taxonomy **first**, then map. In practice the newer gate entries
(CM_HOSTS topology, CM_AVG_RUN supplement — this branch; SchedulerKind — main) went
straight to map entries with no `config/taxonomy/` capture; main then had to retrofit
`platforms.yaml` as a "placeholder to reconcile SchedulerKind deprecation"
(`fa7a00c` — the retrofit commit is the smoking gun). Either the rule needs a
lightweight `capture: waived (<reason>)` field on map entries, or gate prep must
include the capture — today the rule silently erodes.

### F6 — Vocabulary monolith with embedded history (documentation debt, low)
`relationship_vocabulary.yaml` is ~1,600 lines mixing four concerns: node classes, the
stable PROV matrix, 60+ relationship entries, and long prose notes that duplicate
gate-log history (gate dates, SME rationale, deprecation sagas). The notes are
valuable but are a *second* audit trail that can disagree with `config/gate-log.md`.
Split-by-domain is tempting but should wait for the ADR 0002 Phase B move (one rename
wave, not two).

### F7 — Accepted debt, already gated (record only)
The `:Application` triple-typing (prov:SoftwareAgent + dprod ports + org memberships;
K1/K2 need Agent while the reshape proposes Entity) is the largest *semantic* debt in
the layer, but it is documented in both files, has a gate spec
(`seal-tom-attribution-reshape`) and a backlog dependency chain (K3 before K2).
Nothing new to do — do not let F1–F3 fixes touch it ahead of the gate.

---

## Scores — (Impact + Risk) × (6 − Effort)

| # | Item | Type | I | R | E | Priority |
|---|------|------|---|---|---|----------|
| F1 | Map unguarded (schema/enum/ids/summary/updated) | test | 4 | 5 | 2 | **36** |
| F4 | Duplicate `Document` label | code | 3 | 4 | 1 | **35** |
| F3 | `reuses_vocab` free text + map↔vocab cross-consistency unchecked | code/dual-truth | 3 | 4 | 2 | **28** |
| F2 | `applied` stage in comments | lifecycle | 3 | 3 | 2 | **24** |
| F5 | Taxonomy-first erosion (retrofit pattern) | process | 2 | 3 | 2 | **20** |
| F6 | Vocabulary monolith / dual history | docs | 2 | 2 | 4 | **8** |
| F7 | Application triple-typing | semantic | — | — | — | gated (K3) |

## Remediation plan

**Phase 1 (one sitting, alongside feature work) — the guard.**
`drydocs/taxonomy_ontology_map.py` (pure accessor, `review`-group per MODULE_MAP
default-deny) + `tests/unit/test_taxonomy_ontology_map.py`, mirroring `test_backlog`:
schema id; lifecycle enum; unique ids; `confirmed`⇒`confirmed_by/on`;
**computed `summary:`** (recount from entries, fail on drift — ends the hand-bump merge
conflicts); `reuses_vocab` referential check (id exists in
`relationship_vocabulary.yaml`; parenthetical status matches or is absent);
`from_node`/`to_node`/`neo4j_label` agreement between map entry and vocabulary entry;
`updated:` ≥ max `confirmed_on`. Covers F1 + F3 + the F2 enum.

**Phase 2 (15 minutes) — the point fixes.**
Dedupe `Document` (one entry, one note covering both uses, or distinct labels if the
docmeta gate wants them distinct — flag at that gate); flip the five comment-`APPLIED`
entries to `status: applied` with an `applied_on:`/`loader:` field; fix `updated:`.

**Phase 3 (with the next gate) — structured fields.**
`reuses_vocab` → `vocab_id:` (machine-checkable, no parenthetical); add
`capture: <taxonomy file> | waived (<reason>)` to new map entries (F5 policy);
gate-prep checklists (add-source-object step 3, ontology-mapper agent) updated to fill
both.

**Deferred.** F6 split rides the ADR 0002 Phase B rename wave; F7 rides gate K3.

## Business justification
The map is the contract that "a taxonomy NEVER becomes graph edges until confirmed" —
the whole HITL value proposition. Today that contract is enforced by attention, not by
tests, while two sessions were editing the file on the same day on different branches.
One unguarded bad merge (the exact conflict `backlog.yaml` hit today) can silently
present wrong summary counts, a rotted `(active)` claim, or a duplicated label to the
SME at the next gate — and gate decisions made on drifted state are governance
failures, not typos.
