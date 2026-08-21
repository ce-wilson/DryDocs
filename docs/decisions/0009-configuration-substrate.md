# ADR 0009 — Configuration substrate: git YAML stays the source of truth; SQLite is the read model; drafts absorb UI writes

```yaml
status: ACCEPTED        # PROPOSED | ACCEPTED | SUPERSEDED
accepted: 2026-08-01    # ruled at backlog S1 (chad.wilson); as proposed, no amendments
date: 2026-07-25
deciders: [chad.wilson, SME-gate]
layer: 0-configuration
affects:
  - config/taxonomy-ontology-map.yaml            # → config/ontology-map/*.yaml
  - drydocs_core/ontology/relationship_vocabulary.yaml
  - drydocs_core/mapping_store.py                # widened read model + draft table
  - drydocs_core/config.py , source_registry.py , precedence.py
  - drydocs_api/mappings.py                      # draft/promote endpoints
  - tests/unit/test_classification.py , test_mapping_store.py
supersedes: ~
```

> **ACCEPTED 2026-08-01 as proposed** (backlog S1, chad.wilson). No amendments. The headline
> ruling is rule 1: **git text stays the source of truth permanently** — `var/mapping.db`
> remains derived, rebuildable and gitignored, and this is explicitly NOT a stepping stone to
> a database. The draft-table build is backlog **S4**, which this ADR gates.

## Context

The web console is being built. Its admin and mappings surfaces read the configuration layer,
and `O24` already ships a **write** surface (the SEAL-contact override grid). The question
raised in review: *the Python-read configuration files are getting large — is a configuration
store or relational database the better choice, given the DB is already stubbed out?*

### The declarative surface today

| File | Lines | Grows with |
|---|---|---|
| `docs/restructure/backlog.yaml` | 5,651 | work items |
| `drydocs_core/ontology/relationship_vocabulary.yaml` | 2,111 | relationship types |
| `config/taxonomy-ontology-map.yaml` | 1,013 | gated mappings |
| `config/source-mappings/controlm-psgmgr.yaml` | 440 | profiled columns |
| `config/source-registry.yaml` | 296 | registered sources |
| all of `config/` | 5,590 | — |

Readers are thin: `drydocs_core/config.py` (64), `source_registry.py` (96),
`precedence.py` (153). The *code* is not the problem.

### What already exists

`drydocs_core/mapping_store.py` (577 lines) materializes committed YAML/CSV into
`var/mapping.db` (SQLite, gitignored). Its own docstring states the contract:

> *the committed YAML/CSV in git remain the source of truth the HITL gate reviews; the SQLite
> file built here is a derived, rebuildable materialization — deletable at any moment without
> data loss, never the artifact a gate reviews.*

It materializes the ontology map, the relationship vocabulary, node classifications, manual
loads, and the seal-contact overrides; it reuses the loader's own validation chain, so it
cannot accept a row the loader would refuse; it is deterministic (content hashes, no
wall-clock); and `tests/unit/test_mapping_store.py` guards round-trip parity. The
`drydocs-api` `/mappings` routes and DuckDB analytics already read it.

**The "stubbed out" database is not a stub. It is a correct materialized view — the read half
of the answer is built and in production use.** The open question is only whether the *write*
half should move too.

### Four mechanisms that read git text, not rows

1. **The HITL gate reviews diffs.** `docs/restructure/03-hitl-sme-flow.md` and every
   `config/gate-prompts/*.yaml` put a human SME in front of a change. A row-level DB delta is
   not something a domain expert signs off on in a gate session; a YAML hunk is.
2. **The cross-repo port is a commit range.** `git-readme.md` and `docs/port/port-prompt.md` move
   producer → company by applying commits onto a *disjoint* `main`. Database state cannot be
   cherry-picked.
3. **Classification is enforced per file.** `tests/unit/test_classification.py` requires a
   `classification` on every source; `PUBLISH-BOUNDARY.md` gates publication by path. Both
   assume files.
4. **Renders are deterministic from committed text.** The board, the design docs, and the
   gate pages are byte-reproducible — the `CLAUDE.md` §0 stale-render check depends on it.

### What the growth actually costs

Not parse time (milliseconds). Not memory. The cost is that **one file serves many domains**:
an ontology mapping for Control-M lands in the same 1,013-line file as a catalog mapping, so
concurrent sessions collide, and a port conflict is one large hunk instead of one small one.
That is a *granularity* problem, and it has a granularity fix.

## Decision

**Keep committed YAML/CSV as the source of truth. Split it by domain. Schema-guard it. Widen
the derived SQLite read model. Add a draft table so UI writes have somewhere durable to live
before they become a reviewable diff.**

Five rules:

1. **Source of truth is git text, permanently.** Anything an SME gates, a port carries, or a
   classification test guards is a committed file. This is not a stepping stone to a database.
2. **`var/mapping.db` is derived, rebuildable, and never reviewed.** It stays gitignored.
   Widen it — add `source_registry`, `precedence`, `source_mapping` (column ledger),
   `classification`, and `crosswalk` tables — so the console reads **one** SQL surface instead
   of parsing five YAML shapes in TypeScript.
3. **Split monolith YAML by domain; the loader concatenates deterministically.**
   ```
   config/ontology-map/{controlm,catalog,seal,registry,docs,platforms}.yaml
   drydocs_core/ontology/vocabulary/{controlm,catalog,org,docs,registry}.yaml
   ```
   Load order is lexical by filename, entries keep file order within a domain, and a
   duplicate `id` across domains is a test failure. The concatenated result must be
   byte-identical in meaning to today's single file — proven by a migration test that diffs
   old-vs-new parsed output.
4. **JSON Schema per config family, alongside the existing Python tests.** Editors flag a
   malformed entry at typing time; the console's admin surface and the `agents/` runtime can
   validate without importing `drydocs_core`. The Python tests stay — they encode rules JSON
   Schema cannot (cross-file referential integrity, gate status transitions).
5. **UI writes: propose in the DB, land in git.** A `draft` table in `mapping.db` is the
   write-ahead buffer for editing sessions. Promotion **emits a YAML/CSV diff** onto a branch
   for the gate. The console never writes the committed file directly.
   ```
   console edit ─→ mapping.db.draft ─→ (promote) ─→ YAML/CSV diff on a branch ─→ HITL gate ─→ main
                      ▲ durable, multi-session          ▲ reviewable, portable, classified
   ```

Rule 5 is the piece that must be designed **before** the console grows more write surfaces.
Today's `POST /mappings/overrides/draft` returns the *complete updated file*
(commit-by-replace). That is a correct and deliberately minimal M2 design, and it does not
survive a second concurrent editor or a partially-finished edit — both of which arrive with
the console.

## Options considered

### Option A — Move the source of truth into a relational database

| Dimension | Assessment |
|---|---|
| Complexity | High |
| Cost | High — plus migration, backup, and access-control burden |
| Query ergonomics | Excellent |
| Fit with this repo | **Breaks four load-bearing mechanisms** |

**Pros:** real constraints and FKs; concurrent multi-user edits; no parse step; natural
backing for a UI admin surface; ad-hoc SQL over configuration.
**Cons:** the gate loses its diff, the port loses its commit range, the classification tests
lose their file, and the renders lose their deterministic input. It also adds an operational
dependency to a project whose current install story is `poetry install`. **Rejected — the
review specifically asked whether a DB "would be a better choice", and on the merits of
*this* repo's governance model it is not.**

### Option B — Status quo: keep growing the YAML monoliths

| Dimension | Assessment |
|---|---|
| Complexity | None |
| Cost | Zero now, compounding |
| Query ergonomics | Already solved by `mapping.db` |

**Pros:** nothing to build; every guarantee above already holds.
**Cons:** merge and port conflicts concentrate in two files that every workstream touches;
a 2,111-line vocabulary is hard to review; the UI write path stays commit-by-replace.
**Rejected as the final state — but note it is genuinely safe**, which is why the phasing
below can slip without accruing risk.

### Option C — Hybrid: git source of truth + widened derived DB + draft buffer ✅

| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Cost | Low — extends a component that already exists and is tested |
| Query ergonomics | Excellent (SQL for everything the UI reads) |
| Fit with this repo | Preserves all four mechanisms |

**Pros:** every governance property is kept; the console gets one SQL read surface; drafts get
a durable home without git churn; the store already has determinism and parity tests to
extend; incremental — each of the five rules ships independently.
**Cons:** two representations to keep in sync (mitigated: one direction only, plus content
hashes and a parity test); the draft→diff promoter is genuinely new code; a stale `mapping.db`
can confuse a developer (mitigate with a hash mismatch warning at read time).

### Option D — Skip files, generate config from the graph

**Pros:** one store; the graph is already the query surface.
**Cons:** inverts the ingestion direction the whole repo is built on — config *governs* what
may be written to the graph. Config that lives in its own output cannot gate it.
**Rejected on principle.**

## Trade-off analysis

The question "files or a database?" assumes they compete. In a repo where an SME signs off on
diffs and a sister repo receives changes as commit ranges, they do not: **git is the
transactional store and the audit log, and SQL is the index over it.** That is already the
implemented architecture — the review's instinct that a DB belongs here is right, and it is
right about the read path, which is done.

The genuine risk the question surfaced is different and sharper: **a UI that edits governed
configuration has nowhere durable to put an unfinished edit.** Commit-by-replace works for one
small override list and one editor. It does not survive two people, or a session interrupted
mid-edit, or a change that needs to sit pending while a gate is scheduled. That is the thing
that gets expensive to retrofit once several write surfaces exist — which is precisely the
"re-configuring later will be costly" concern, correctly located.

Splitting the monoliths is real but second-order: it reduces conflict pain and review load,
and it does not change any contract.

## Consequences

**Easier**
- Console reads one SQL surface; no YAML parsing in TypeScript.
- Port conflicts shrink to the domain file that actually changed.
- Malformed config fails in the editor, not in `pytest`.
- Multi-session and multi-user editing become possible without inventing a git workflow in
  the browser.

**Harder**
- Two representations to keep coherent (one-directional, hash-checked, parity-tested).
- Splitting the ontology map and vocabulary is a wide mechanical diff that must be
  port-sequenced.
- The draft→diff promoter needs its own tests: a promoted draft must produce exactly the file
  a hand-edit would.

**To revisit**
- If `mapping.db` ever needs to be shared across machines, the answer is *rebuild it there*,
  not ship it. Revisit only if rebuild time becomes material (it is currently well under a
  second).
- If a config family ever needs true multi-writer concurrency with locking, that family — and
  only that family — is a candidate for a real database, and it argues for its own ADR.

## Action items

1. [ ] Widen `mapping_store.py`: add `source_registry`, `precedence`, `source_mapping`, `classification`, `crosswalk` tables; extend the parity test to each.
2. [x] **DONE 2026-08-04 (S4).** `draft` table + promote path: `POST /mappings/overrides/draft` and `POST /mappings/app-code/draft` write ROWS and return a receipt; `POST /mappings/drafts/{draft_id}/promote` emits the unified diff; `GET /mappings/drafts` lists what is pending per session; the console downloads a `.patch` instead of a whole file. Both O24 overrides and the K9 defined-mapping domain were retro-fitted together — one module carrying two write models was the confusion this rule set out to remove. `build()` carries draft rows across a rebuild (a rebuild is routine; discarding pending work would defeat the buffer), and deleting `var/mapping.db` still discards unpromoted drafts — the "deletable without data loss" contract holds for everything DERIVED, and an unpromoted draft is by definition work that has not reached git yet.
3. [ ] Add a `mapping.db` staleness check — compare stored source hashes on open, warn loudly on drift.
4. [ ] Split `config/taxonomy-ontology-map.yaml` into `config/ontology-map/*.yaml` with a deterministic concatenating loader + a migration test proving parsed-output equivalence.
5. [ ] Split `relationship_vocabulary.yaml` the same way; duplicate `id` across domains must fail the suite.
6. [ ] Author JSON Schema for source-registry, ontology-map, relationship-vocabulary, crosswalk, and classification; wire into the existing tests; publish for the console and `agents/`.
7. [ ] Port-sequence items 4–5 through `docs/port/port-prompt.md` — they are wide mechanical diffs and must not collide with an in-flight port.
