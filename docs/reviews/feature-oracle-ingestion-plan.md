# Feature: Oracle Ingestion — scaffold + sync contract

**Branch mapping:** producer `feature/oracle-ingestion`  →  company `psgmgr-base`.
This feature delivers the supplemental staging + incremental-ingestion work from
[persona-oracle-dba.md](persona-oracle-dba.md), and will iterate. The point of this
scaffold is to make each producer→company sync **smooth** across those iterations.

## Design principle — minimize port friction

Disjoint histories mean every sync is a file-granularity cherry-pick (see the
`reconcile-port` skill). Friction comes almost entirely from **collisions** (files
that exist on both sides and diverge). So the rule for this feature:

1. **Put new work in NEW files** — they port wholesale (`git checkout
   cewilson/feature/oracle-ingestion -- <file>`), zero conflict.
2. **Editing the Canonical-here extract SQL is free** — those files are taken
   wholesale on sync, so adding incremental predicates to `controlm_*.sql` is not a
   collision.
3. **Touch exactly one shared file (`cli.py`), append-only** — one flag/command
   that delegates to the new module; never edit existing command bodies.
4. **Never touch `oracle_adapter.py`** — it's the company's Kerberos divergence
   (keep-company). Depend only on its shared contract: `OracleAdapter(query,
   bind_params)` + `cursor.execute(query, bind_params)`, which both sides have.
5. **Site-specific names stay placeholders** (`DRYDOCS_STG`, `CM_RO_USER`,
   `<PY_NORMALIZER_USER>`, the unverified `CM_DEF_SETVAR`) → producer carries no
   real company values, so syncs need no scrub and the public-repo rule holds.
6. **Idempotent DDL** (`CREATE OR REPLACE` / existence-checked `CREATE` / `GRANT`)
   so every iteration re-applies cleanly and the company can apply deltas.
7. **Fix the file paths now** — later iterations add *content* to this known set,
   never new files mid-stream (new-file churn is what makes ports noisy).

## Minimum necessary components

| # | Component | File | Port disposition |
|---|---|---|---|
| 1 | Supplement DDL (STG_LOAD_CONTROL, STG_SAMPLE_MANIFEST, view extensions, grants) | `drydocs/loaders/sql/ddl/controlm_staging_supplement_ddl.sql` **(new)** | **Clean-add** — wholesale |
| 2 | Incremental extract predicates (watermark filters) | extend existing `drydocs/loaders/sql/controlm_*.sql` | **Canonical-here** — wholesale |
| 3 | Incremental loader (watermark read/advance + per-job delete+insert) | `drydocs/loaders/controlm_incremental.py` **(new)** | **Clean-add** — wholesale |
| 4 | Load-control row model (only if dict rows won't do) | `drydocs/models/controlm_loadcontrol.py` **(new)** + 1 import line in `models/__init__.py` | new file clean-add; **`__init__.py` = isolated 1-line collision** |
| 5 | CLI surface | one append-only block in `drydocs/cli.py` (`--incremental` flag / `load-staging`) | **Collision — the only real merge point**; keep tiny, delegate to #3 |
| 6 | Tests | `tests/unit/test_oracle_incremental.py` **(new)** | **Clean-add** |
| 7 | This plan / sync contract | `docs/reviews/feature-oracle-ingestion-plan.md` **(new)** | **Clean-add** |
| 8 | Ad-hoc / investigation queries (kept, sanitized; NOT loaded) | `drydocs/loaders/sql/adhoc/` **(new dir)** | **Clean-add** |

Everything is a clean-add or wholesale-take **except** the `cli.py` block (and,
only if needed, one line in `models/__init__.py`). That is the entire collision
surface for the feature — by design.

**Deferred (not in scope, keeps the surface minimal):** the `STG_DEV_SID`
dimension — handled inline via `UPPER(REGEXP_REPLACE(sid,'p$',''))`; partitioning
(volumes don't need it); any `oracle_adapter.py` change.

## How the company syncs this branch onto `psgmgr-base`

```
git fetch cewilson feature/oracle-ingestion
# clean-adds + Canonical-here extract SQL — take wholesale:
git checkout cewilson/feature/oracle-ingestion -- drydocs/loaders/sql/ddl/controlm_staging_supplement_ddl.sql drydocs/loaders/sql/ drydocs/loaders/controlm_incremental.py drydocs/models/controlm_loadcontrol.py tests/unit/test_oracle_incremental.py docs/reviews/feature-oracle-ingestion-plan.md
# then ONE hand-merge: append the cli.py flag/command block (keep company m6-verify etc.)
# leave drydocs/adapters/oracle_adapter.py untouched (company Kerberos version)
```
Follow the `reconcile-port` skill, substituting `feature/oracle-ingestion` →
`psgmgr-base`. Grant deltas needed company-side: `UPDATE` on `STG_LOAD_CONTROL`;
confirm `CM_DEF_SETVAR` SELECT.

## Iteration discipline

Each iteration fills content into the **fixed file set** above and commits on
`feature/oracle-ingestion`; nothing new appears at sync time except more content in
files the company already knows to take. Open questions that gate the work live in
[persona-oracle-dba.md](persona-oracle-dba.md) §1.7 (confirm `CM_DEF_SETVAR`;
`CAPTURE_DATE` semantics; `CREATION_USER`/`CHANGE_USERID` existence; retention).

## Ad-hoc testing approach (decided)

Split by purpose — don't force everything through one tool:

- **Explore / discover → SQL Developer.** Fast, GUI, already connected via
  thin-JDBC, real data stays local. Use it for the §1.7 open questions (confirm the
  `CM_DEF_SETVAR` object, whether `CAPTURE_DATE` is per-row or per-snapshot, whether
  `CREATION_USER`/`CHANGE_USERID` exist), eyeballing data, and prototyping a WHERE
  clause. The project-via-VS-Code overhead is **not** worth it for one-off pokes.
- **Validate / land → the project (VS Code, company-side checkout).** Once a query
  or DDL is a keeper, move it into the repo SQL file and run it through the real
  ship path — `drydocs … --use-oracle` + the `OracleAdapter` + `pytest`. That is the
  only way to exercise what actually ships: bind variables, the Kerberos adapter,
  idempotent re-runs. SQL Developer can't prove those.

- **Keep / version → `drydocs/loaders/sql/adhoc/`.** The third bucket: a
  worth-keeping investigation/profiling/QA query that isn't ship-path loader SQL.
  Save it there (sanitized) so the discovery work is versioned, portable, and
  rerunnable — without polluting the pipeline (`adhoc/` is not loaded). Seeded with
  `preflight_open_questions.sql` (the §1.7 probes). Promote to
  `drydocs/loaders/sql/` only if it becomes part of ingestion.

Why it benefits the project: the repo stays the source of truth and gets tested as
it ships; SQL-Developer-only work is invisible, untested on the real path, and never
ports. **Data discipline:** commit only sanitized SQL *structure* — never paste real
result rows into the (public) repo. Optional middle ground: SQLcl runs the committed
`.sql` from the command line in thin mode if you want CLI without full plumbing.

## Saving data locally (real result/sample data)

Real data **never** goes in the repo (public producer). It lives **only** under
`drydocs/data/` — which is gitignored — so the model can use it while it stays off
GitHub.

**Status check (the planned sample test case): present.** The sampling case from
the prior iteration is saved locally at
`drydocs/data/samples/controlm_variables__sample.csv` — **323 rows**, gitignored.
The full `drydocs/data/samples/` set (folders, jobs, conditions, dependencies, SEAL,
catalog) is also present. The four sample-backed tests run against it locally and
skip elsewhere — exactly as designed.

**Where it goes:**
- **Inputs / samples** → `drydocs/data/samples/` (gitignored).
- **Run output** → `drydocs/data/stg_out/` (gitignored). Note: `normalize-variables`
  defaults to `stg_out/` at the repo root, which is **not** under `drydocs/data/`;
  `.gitignore` now guards `stg_out/` and `/stg_*/`, but prefer
  `--out-dir drydocs/data/stg_out` so output persists in the data area (and isn't
  left in `/tmp`, where prior runs landed and were lost).

**Format — what works best for the model:**
- **CSV is the default** for tabular sample/extract/staging data. It's the
  pipeline-native format (`CsvAdapter`, the `STG_*` outputs), the most
  **token-efficient** for flat rows (no per-row key repetition), and the model reads
  it directly. Use header rows.
- **JSON only for nested / metadata** — run manifests, scope-bind records, the
  scenario-coverage / `tree_*` snapshots, or columns that are themselves structured
  (`args_json`). For flat rows JSON wastes tokens (repeated keys), so don't default
  to it.
- **Not Parquet** for model consumption — it's binary; the model can't read it
  without a tool. Fine for archival/scale, not for handing to the model.

Rule of thumb: **tabular → CSV; nested/metadata → JSON**; keep slices the model
reads small, and never let real rows leave `drydocs/data/`.
