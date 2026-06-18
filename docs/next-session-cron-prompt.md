# New Session Prompt — Cron Task: feature/oracle-ingestion build-out

Paste this into a new Claude Code session (on branch `feature/oracle-ingestion`) to
pick up where the last session ended.

---

## What was built in the prior session (do not redo)

A resumable hourly cron task named `drydocs-persona-review` completed a full
multi-persona project review:

| Deliverable | File |
|---|---|
| Oracle DBA review (Phase 1) | `docs/reviews/persona-oracle-dba.md` |
| Neo4j Architect review (Phase 2) | `docs/reviews/persona-neo4j-architect.md` |
| Synthesis / recommendations (Phase 3) | `docs/reviews/persona-review-summary.md` |
| Progress state | `docs/reviews/CHECKPOINT.md` — **status: COMPLETE** |

The cron pattern used: hourly poll (not fixed-time, because the daily usage-limit
reset varies). Each wake appended a line to `CHECKPOINT.md ## Run log` — that log
now serves as the empirical record of when the reset actually fires each day.

**That review is done. Do not re-run it.**

---

## Cron pattern — how it was wired (reference for the next task)

```
Task name:   drydocs-persona-review
Frequency:   hourly
Entry point: skill invocation →  docs/reviews/persona-review-plan.md
             EXECUTION PROTOCOL: read CHECKPOINT → load skill → do 1 unit →
             append findings → update CHECKPOINT → repeat until budget ends
Wake log:    docs/reviews/CHECKPOINT.md  ## Run log  (one line per wake-with-budget)
Budget rule: checkpoint after EVERY unit; if near-limit, save checkpoint and stop
Secret rule: architecture-level only — no real SIDs, values, credentials, company GHE org
```

The same pattern applies to the next cron task: create/update a `CHECKPOINT.md`
equivalent, load the relevant skill, work one unit, checkpoint, repeat.

---

## The next goal — build out `feature/oracle-ingestion`

The review produced a full design. The next work is to **implement it**, iteratively,
on branch `feature/oracle-ingestion` (producer side) → ported to company `psgmgr-base`.

### Orientation — read these files first (in order)

1. `docs/reviews/feature-oracle-ingestion-plan.md` — sync contract, minimum components,
   port friction rules, ad-hoc testing approach, local data format guidance
2. `docs/reviews/persona-oracle-dba.md` — full Oracle staging design (§1.3–§1.7 +
   §1.8 addenda from Neo4j review)
3. `docs/reviews/persona-review-summary.md` — 13 prioritized recommendations (P0–P3)
   and 7 open decisions
4. `drydocs/loaders/sql/adhoc/preflight_open_questions.sql` — 5 probes to run in
   SQL Developer on the company side; answers gate the next code unit

### Open questions that gate the build (run in SQL Developer, record conclusions here)

These are in `preflight_open_questions.sql`. Record findings as conclusions only
(never commit real rows):

| # | Question | Gates |
|---|---|---|
| Q1 | Real name of the variable object (≥4 col-match in `ALL_TAB_COLUMNS` for `PSGMGR`) | Variable extract + incremental hash |
| Q2 | Is `CAPTURE_DATE` per-row or uniform per snapshot? | Change-detection strategy choice |
| Q3 | Do `CREATION_USER` / `CHANGE_USERID` exist on `CM_DEF_VJOB`? | Scope binds, `JOB_DEVELOPER_VIEW` |
| Q0.1 | Does `TABLE_ID` collide across DCs? | Composite key assumption in staging |
| Q0.2 | Do `MEMLIB` / `OVERLIB` columns exist? | `controlm_staging_ddl.sql` §0.2 guard |

Once Q1–Q3 are answered, update `docs/reviews/feature-oracle-ingestion-plan.md`
"Open questions" section and begin iteration 1 (below).

### Minimum component file set (fixed — do not add new files mid-stream)

| # | File | Status |
|---|---|---|
| 1 | `drydocs/loaders/sql/ddl/controlm_staging_supplement_ddl.sql` | **EXISTS** (scaffold) |
| 2 | `drydocs/loaders/sql/controlm_*.sql` (add incremental predicates) | **EXISTS** (scope binds in place) |
| 3 | `drydocs/loaders/controlm_incremental.py` | **NOT YET** — iteration 1 |
| 4 | `drydocs/models/controlm_loadcontrol.py` + 1-line `models/__init__.py` import | **NOT YET** |
| 5 | `drydocs/cli.py` — append-only `--incremental` / `load-staging` block | **NOT YET** |
| 6 | `tests/unit/test_oracle_incremental.py` | **NOT YET** |

### Port friction rules (critical — do not violate)

- New files → clean-add (wholesale `git checkout cewilson/feature/oracle-ingestion -- <file>`)
- `cli.py` → append-only; the only real merge point
- `oracle_adapter.py` → **NEVER touch** (company Kerberos divergence)
- No real company values, GHE org, credentials in any committed file
- Placeholders: `DRYDOCS_STG`, `CM_RO_USER`, `<PY_NORMALIZER_USER>`, `CM_DEF_SETVAR`

### Iteration 1 work units (each checkpointable)

**Gate: answer Q1–Q3 first (SQL Developer), then:**

1. **Model** — `drydocs/models/controlm_loadcontrol.py`: `LoadControlRow` dataclass +
   `SampleManifestRow`; one-line import in `models/__init__.py`.

2. **DDL** — flesh out `controlm_staging_supplement_ddl.sql`:
   - `STG_LOAD_CONTROL`: existence-checked CREATE, PK `(source_object, data_center)`,
     all watermark columns (see `persona-oracle-dba.md` §1.3-A)
   - `STG_SAMPLE_MANIFEST`: existence-checked CREATE
   - `JOB_DEVELOPER_VIEW`: `CREATE OR REPLACE`, inline SID normalization,
     `CROSS APPLY` / lateral union of the 4 SID-bearing columns
   - Grant placeholders as comments (per §1.6)

3. **Incremental extract predicates** — add watermark `WHERE` clauses to
   `controlm_variables.sql`, `controlm_jobs.sql`, `controlm_folders.sql`:
   ```sql
   AND (:hwm_version_serial IS NULL OR VERSION_SERIAL > :hwm_version_serial)
   AND (:hwm_capture_date   IS NULL OR CAPTURE_DATE   > :hwm_capture_date)
   ```

4. **Incremental loader** — `drydocs/loaders/controlm_incremental.py`:
   - Read HWM from `STG_LOAD_CONTROL` (or default to full-refresh sentinel)
   - Extract changed jobs via watermark-filtered SQL
   - Per-job delete+insert in one transaction (job grain = `(data_center, folder_id, job_id)`)
   - Commit per batch + advance HWM
   - Use existing `OracleAdapter(query, bind_params)` — no adapter changes
   - Write `STG_SAMPLE_MANIFEST` row at end

5. **CLI surface** — append to `drydocs/cli.py`: `load-staging` command (or
   `--incremental` flag on `ingest-controlm`) that calls the new loader; keep tiny,
   delegate entirely to #4.

6. **Tests** — `tests/unit/test_oracle_incremental.py`: unit tests with mock
   `OracleAdapter`; confirm HWM read/write, per-job delete+insert idempotency,
   restart safety (re-apply same batch = same result).

### Cron setup for this next phase (if resumable across days)

If the work spans multiple days, set up a new cron using the same pattern:

```
Task name:   drydocs-oracle-ingestion
Entry point: this file (docs/next-session-cron-prompt.md)
Checkpoint:  docs/reviews/feature-oracle-ingestion-plan.md  (update "Open questions"
             + add a ## Progress log section as iteration units complete)
Frequency:   hourly (same reasoning — reset time varies daily)
Wake log:    append  "- <ISO timestamp> wake"  to the Progress log on each wake
Budget rule: complete + checkpoint one unit before stopping; never hold unsaved work
```

### Branch + remote state (verified end of prior session)

```
Current branch:  feature/oracle-ingestion
main:            synced at a868550
feature/*:       synced at a67d731
Only remote:     origin → https://github.com/ce-wilson/DryDocs.git
Local branches:  main, feature/oracle-ingestion, controlm-spinoff
Sample data:     drydocs/data/samples/controlm_variables__sample.csv  (323 rows, gitignored)
```

---

## Do NOT do on the producer side

- Modify `drydocs/adapters/oracle_adapter.py`
- Commit real company data, SIDs, credentials, or the company GHE org namespace
- Create files outside the fixed minimum-component set without updating the plan
- Use the literal GHE org — always `<company-org>` as placeholder
