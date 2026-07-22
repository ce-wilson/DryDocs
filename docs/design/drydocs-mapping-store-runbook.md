# Runbook — build, inspect & maintain the mapping store (`var/mapping.db`)

<!-- anchor: front-matter -->
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 1, 2026-07-22**,
  authored at commit `22d1a39` (store per plan M0–M4; O24 override table included).
- **Classification:** Internal-Public (mechanism only — commands and synthetic/empty
  producer-side data; no credentials, no company values)
- **Audience:** anyone operating the mapping-store materialization directly — building,
  inspecting, dumping, or diagnosing it — outside the demo/console surfaces
- **Companion:** `docs/design/drydocs-mapping-store-tdd.md` (the design this operates);
  `docs/design/drydocs-mapping-demo-runbook.md` (the `/demo` site backed by this store);
  `knowledge/upgrade-plans/mapping-store-plan-2026-07-17.md` (the M0–M4 plan)

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Operate the SQLite materialization of the mapping layer: build or rebuild
`var/mapping.db` from the committed YAML/CSV sources, inspect its tables and views,
produce the deterministic CSV dumps, and run the analytics queries.

**The one rule that shapes every step:** the file is DERIVED. The committed sources are
truth; every anomaly means "rebuild", never "investigate the DB". Nothing in this
runbook can lose data, because the store holds none of its own.

**In scope.** `scripts/build_mapping_db.py`, `scripts/mapping_analytics.py`, direct
sqlite3/DuckDB inspection, and the staleness check.

**Out of scope.** Serving the store over HTTP (`drydocs-mapping-demo-runbook.md`);
editing the committed sources themselves (mapping *semantics* — HITL-gated, see
Contacts); Neo4j and the graph loaders (the store touches neither).

<!-- anchor: prerequisites -->
## Prerequisites

```powershell
# From the repo root, on main
poetry install            # core deps only; no api group, no container, no .env needed
```

Optional: `duckdb` (pip/poetry extra) for the analytics path — the script falls back to
stdlib sqlite3 with identical answers when it's absent. No credentials of any kind: the
store connects to nothing.

<!-- anchor: startup -->
## Startup

"Startup" here is a build — the store is a file, not a service.

1. **Build it:**
   ```powershell
   poetry run python scripts/build_mapping_db.py
   ```
   *Success:* `built C:\...\var\mapping.db` followed by a per-table row-count listing
   (producer-side currently: ontology_mapping 33, relationship_vocabulary 75,
   node_classification 52, manual/override tables 0, meta 5).
2. **Confirm freshness:**
   ```powershell
   poetry run python -c "from drydocs_core.mapping_store import DEFAULT_DB_PATH, is_current; print(is_current(DEFAULT_DB_PATH))"
   ```
   *Success:* `True`. (`False` immediately after a build means a source changed mid-build
   — just rebuild.)

<!-- anchor: refresh-ingest -->
## Refresh / ingest

Two refresh paths exist; both are safe to run at any time.

- **Implicit (O14, the normal path):** every `drydocs_api` `/mappings/*` read checks
  `is_current()` and rebuilds on drift — edits to `config/taxonomy-ontology-map.yaml`,
  `drydocs_core/ontology/relationship_vocabulary.yaml`, `config/manual-loads/`, or
  `config/overrides/seal-contact-overrides.csv` are picked up on the next request with
  no restart and no manual step.
- **Explicit (this runbook's path):** rerun the build, optionally with the
  deterministic per-table CSV dumps (the gate-reviewable text twin of the binary file):
  ```powershell
  poetry run python scripts/build_mapping_db.py                       # rebuild in place
  poetry run python scripts/build_mapping_db.py --dump-dir var/dumps  # + CSV dumps
  poetry run python scripts/build_mapping_db.py --db <path>           # build elsewhere
  ```

Never commit `var/mapping.db` or the dumps under `var/` — the directory is gitignored
and the file is derived by construction.

<!-- anchor: verify -->
## Verify

```powershell
# Freshness — the whole staleness protocol is this one boolean
poetry run python -c "from drydocs_core.mapping_store import DEFAULT_DB_PATH, is_current; print(is_current(DEFAULT_DB_PATH))"
# -> True

# Lifecycle summary — canonical expected values live in config/taxonomy-ontology-map.yaml
poetry run python -m sqlite3 var/mapping.db "SELECT * FROM v_status_summary"
# -> ('applied', 8) ('confirmed', 22) ('proposed', 2) ('rejected', 1)   [as of Rev 1]

# Schema browse — the SQL-Developer equivalents
poetry run python -m sqlite3 var/mapping.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
poetry run python -m sqlite3 var/mapping.db "PRAGMA table_info(ontology_mapping)"

# Analytics sweep (DuckDB if installed, sqlite3 fallback — answers identical)
poetry run python scripts/mapping_analytics.py
```

Determinism spot-check: two consecutive builds followed by `--dump-dir` into different
directories produce byte-identical CSVs (`fc.exe` / `git diff --no-index` shows nothing).
The unit suite asserts this too: `poetry run pytest tests/unit/test_mapping_store.py -q`.

<!-- anchor: rollback -->
## Rollback

Rollback is deletion — safe by construction:

```powershell
Remove-Item var\mapping.db
```

The next explicit build or API read recreates it from the committed sources. If a bad
*source* edit is the problem, roll back the source in git (`git checkout -- <file>`)
and rebuild; the store follows the sources, always. There is no destructive step in
this runbook — nothing here writes git, graph, or committed config.

<!-- anchor: troubleshooting -->
## Troubleshooting

- **`MappingStoreError: mapping-store source not found: <path>`** → a committed source
  file is missing (usually a wrong repo root or a deleted overrides CSV). Restore the
  file in git; the build refuses loudly rather than building a partial store.
- **`MappingStoreError: ... role_name ... does not canonicalize to a SEAL role`** (or
  missing `rationale` / `authored_by`, bad `status`) → a bad row in
  `config/overrides/seal-contact-overrides.csv`. Fix it at the source; the store never
  guesses around steward-authored data.
- **`MappingStoreError: override equals the captured SEAL value — not a correction`** →
  the override row duplicates the SEAL source value; delete the row or capture the real
  correction.
- **API error `relationship WAS_ASSOCIATED_WITH{role=seal_app_ref} is not registered in
  the vocabulary materialization — rebuild var/mapping.db`** → the store predates a
  vocabulary edit; rebuild (or just re-request — the O14 guard should have done it;
  if it recurs, delete the file, which is always safe).
- **`is_current()` stays `False` after rebuilding** → a source is changing between hash
  and build (concurrent session editing config) — coordinate per the parallel-session
  discipline, then rebuild once the tree is quiet.
- **Query results look wrong** → do not debug the DB. Rebuild, re-query; if still wrong,
  the committed source says what the store says — the discussion belongs at the source
  (and possibly the HITL gate), not in SQLite.

<!-- anchor: contacts-escalation -->
## Contacts & escalation

Role-based, per the repo's standing flow: the repo owner/SME owns this procedure. The
store itself is never the decision surface — anything touching **mapping semantics**
(quintuple entries, vocabulary terms, manual rows, overrides) routes to the HITL gate
(`docs/restructure/03-hitl-sme-flow.md`); the governing sign-offs are K2
`seal-attribution-match-policy` (2026-07-14) and `ui-write-surface` SME-3 (2026-07-21).
Escalation beyond the repo is not applicable (local derived file, no shared
infrastructure).

<!-- anchor: appendices -->
## Appendices

Table/view inventory (schema `drydocs.mapping-store.v1`): tables `meta`,
`node_classification`, `relationship_vocabulary`, `ontology_mapping`,
`manual_load_file`, `manual_mapping`, `seal_contact_override`; views
`v_mapping_quintuple`, `v_status_summary`, `v_vocab_active`, `v_label_options`,
`v_manual_conflicts`, `v_seal_contact_grid`, `v_source_corrections`. Full DDL and
column-level source mapping: the TDD's "Source → column-level field mapping" section.
