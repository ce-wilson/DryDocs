# DryDocs Multi-Persona Review — Synthesis Summary

> **STATUS: Superseded (2026-07-01).** This review/plan is complete; its findings were rolled
> into `docs/decisions/` (ADRs), `MODULE_MAP.md`, and `docs/restructure/backlog.yaml`.
> Kept for historical reference.

**Review scope:** Oracle-side supplemental staging design (Phase 1 / Oracle DBA
persona) + graph/ontology architecture (Phase 2 / Neo4j Architect persona). Both
personas reviewed the same target: the DryDocs incremental-ingestion feature for
`psgmgr` Control-M data.

**Status:** All cross-persona reconciliation complete.

---

## Cross-Persona Reconciliation

The two personas found no fundamental design conflicts. The Oracle staging design
and the graph architecture are compatible and complementary. All five Phase-2
addenda to Phase-1 are additions, not corrections. The two design layers are
coupled at the Python normalizer / incremental loader boundary — the Python code
orchestrates both sides.

| Phase-1 (DBA) decision | Phase-2 (graph architect) verdict |
|---|---|
| Per-job delete+insert in staging | ✓ Correct; requires matching stale-edge delete in Neo4j before re-assert |
| `STG_LOAD_CONTROL` watermark table | ✓ Correct; also annotate `:JobRun` in Neo4j for graph-side audit |
| Inline SID normalization (`UPPER(REGEXP_REPLACE...)`) | ✓ Correct; reuse in Python loader for `WAS_ASSOCIATED_WITH` MATCH |
| `STG_SAMPLE_MANIFEST` provenance | ✓ Correct; annotate `:JobRun` properties; no new node type |
| Variables Oracle-only / semantic facts via `STG_APP_FACT` | ✓ Aligned; do not load raw variables into graph |
| `STG_DEV_SID` dimension deferred | ✓ Aligned; reuse `:Employee` with `developer_sid` MATCH when ready |

---

## Prioritized Recommendations

### P0 — Blockers (do before incremental loader runs against a production graph)

1. **Fix `RUNS_ON` → `SCHEDULED_ON` in `controlm_folders.cypher` + one-time graph
   migration.** The graph currently has `RUNS_ON` edges; the vocabulary says
   `SCHEDULED_ON`; re-using `RUNS_ON` for the planned execution-host edge will
   create a collision. See Neo4j review 2.2 Issue 2 for the migration Cypher.

2. **Add `stale_edge_cleanup.cypher`** (delete condition/invocation edges for
   changed jobs before re-asserting). Without this, removed conditions persist as
   phantom edges in the graph after incremental runs. New file:
   `drydocs/loaders/cypher/stale_edge_cleanup.cypher`. See Neo4j review 2.4.

3. **Wrap date properties with `datetime()` in all M3 loaders.** Bare string date
   values break Neo4j temporal operators. Apply `datetime(row.capture_date)` pattern
   to `capture_date`, `version_timestamp`, `last_updated`, `active_from`,
   `active_till` across `controlm_jobs.cypher` and `controlm_folders.cypher`. See
   Neo4j review 2.2 Issue 4 and Phase-1 Addendum A.

### P1 — Complete for correctness (same sprint as incremental loader)

4. **Complete `:JobFolder` → `:ControlMFolder` label rename migration.** The rename
   is half-applied (vocabulary says `ControlMFolder`; constraints/loaders say
   `JobFolder`). Add the migration Cypher to `constraints.cypher` and update the
   constraint label. See Neo4j review 2.2 Issue 1. Until complete, keep loaders
   emitting both labels (`:JobFolder:Collection`).

5. **Annotate `:JobRun` with `STG_LOAD_CONTROL` metadata** (`load_mode`,
   `hwm_version_serial`, `rows_applied`) after each incremental batch cycle. Adds
   graph-side visibility of the Oracle HWM state. See Neo4j review 2.3 and Phase-1
   Addendum C.

6. **Add a range index on `REQUIRES_IN_CONDITION.last_run_id`** (and
   `EMITS_OUT_CONDITION.last_run_id`) to support the age-out cleanup pass. See Neo4j
   review 2.3 Strategy A.

### P2 — Important for quality and future work

7. **Answer Phase-1 open questions 1–4** before the incremental loader's first
   production run:
   - Q1: Confirm `CM_DEF_SETVAR` object name (blocks variable extract entirely).
   - Q2: Confirm `CAPTURE_DATE` per-row vs per-extract (determines HWM strategy).
   - Q3: Confirm `CREATION_USER`/`CHANGE_USERID` on `CM_DEF_VJOB` (gates dev-SID
     attribution graph edge).
   - Q4: Decide incremental cadence and staging retention (N-run rollback window).

8. **Add `:Script(executable_path)` and `:File(canonical_path, date_token)`
   constraints** before activating the `STG_INVOCATION` and `STG_FILE_REF` loaders.
   Without constraints, MERGE will silently create duplicate nodes. See Neo4j
   review 2.3.

9. **Drop the `m3_constraints_upgrade.cypher` reference** in `controlm_jobs.cypher`
   comment, or create the file. The comment says "Run `m3_constraints_upgrade.cypher`
   to lock this on existing graphs" but the file does not exist. The correct NODE KEY
   is already in `constraints.cypher` with a DROP guard — the migration is handled
   there. Remove the stale reference or create the file as an alias. See Neo4j
   review 2.1.

### P3 — Technical debt and future capabilities

10. **`AreaProduct` `SUBCLASS_OF` wiring** (add `prov:Entity` parent). Enables
    `AreaProduct` edges to eventually map to PROV-O terms rather than being
    local-only forever. See Neo4j review 2.2 Issue 6.

11. **Add `queries/` library** (`queries/queries.cypher`) with the five most common
    graph traversals: folder→job→condition chain, job→SEAL application attribution,
    dev-SID attribution, incremental run provenance, sample coverage query. Enables
    developer and analyst self-service without writing Cypher from scratch.

12. **`controlm_staging_supplement_ddl.sql` section 4 — indexes.** Placeholder
    comment reads "none required yet." Add an index on `STG_SAMPLE_MANIFEST.run_id`
    and `STG_LOAD_CONTROL.updated_at` once access patterns are confirmed.

13. **Consider `STG_DEV_SID` dimension promotion.** Phase 1 deferred this;
    Phase 2 confirms `:Employee` reuse is the right long-term pattern. Revisit
    once Q3 (column existence) and Q4 (retention) are answered — the dimension
    materializes as a graph edge, not an Oracle table.

---

## Open Decisions for the User

| # | Decision | Blocker for |
|---|---|---|
| D1 | `CM_DEF_SETVAR` object name (verify or replace with real name) | Variable extract + incremental variable hash |
| D2 | Is `CAPTURE_DATE` per-row or per-extract-uniform? | HWM strategy selection |
| D3 | Do `CREATION_USER`/`CHANGE_USERID` exist on `CM_DEF_VJOB`? | Dev-SID graph attribution edge (`JOB_DEVELOPER_VIEW`) |
| D4 | Incremental cadence + staging retention (how many runs to keep)? | `STG_LOAD_CONTROL` rollback window; full-refresh schedule |
| D5 | Run `RUNS_ON`→`SCHEDULED_ON` migration before or during incremental deploy? | Must be before to avoid edge-type collision |
| D6 | Is APOC available on the Neo4j instance? | Determines age-out cleanup tool (`apoc.periodic.iterate` vs `CALL IN TRANSACTIONS`) |
| D7 | Is the full-load `:JobRun` supernode (300K+ edges) causing observable query latency? | Prioritization of provenance restructuring |

---

## File Inventory — What Exists vs. What is Needed

### Exists and correct
- `drydocs/schema/constraints.cypher` — NODE KEYs, uniqueness constraints
- `drydocs/schema/ontology_supplement.cypher` + `seal_`, `catalog_` — PROV-O supplement
- `drydocs/ontology/relationship_vocabulary.yaml` — single registry with drift guard
- `drydocs/loaders/sql/ddl/controlm_staging_ddl.sql` — base STG_ DDL
- `drydocs/loaders/sql/ddl/controlm_staging_supplement_ddl.sql` — Phase-1 additions
- `drydocs/loaders/cypher/controlm_jobs.cypher` — job MERGE (correct pattern, needs date fix)
- `drydocs/loaders/cypher/controlm_folders.cypher` — folder+server MERGE (needs SCHEDULED_ON)
- `drydocs/loaders/cypher/controlm_conditions_in.cypher` / `_out.cypher` — condition edges

### New files needed (incremental feature)
- `drydocs/loaders/cypher/stale_edge_cleanup.cypher` — delete stale edges before re-assert **[P0]**
- `drydocs/loaders/incremental_controlm.py` — `IncrementalControlMLoader` orchestrator
- `drydocs/loaders/sql/incremental_changed_jobs.sql` — changed-job extract (VERSION_SERIAL > HWM)

### Existing files needing updates (incremental feature)
- `drydocs/loaders/cypher/controlm_folders.cypher` — RUNS_ON → SCHEDULED_ON **[P0]**
- `drydocs/loaders/cypher/controlm_jobs.cypher` — datetime() wrapping on date props **[P0]**
- `drydocs/schema/constraints.cypher` — `:ControlMFolder` rename migration block **[P1]**

---

*Review by: Oracle DBA persona (Phase 1) + Neo4j Architect persona (Phase 2).
Completed: 2026-06-18. Full findings in `persona-oracle-dba.md` (§1.1–1.8) and
`persona-neo4j-architect.md` (§2.1–2.6).*
