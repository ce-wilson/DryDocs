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
