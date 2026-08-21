# Guide: SQL logging on `drydocs ingest-controlm --use-oracle`

**Audience:** an agent or SME operating/extending the Control-M Oracle ingest path.
**Scope:** what gets logged, where, how, and how to trace a logged query back to its run.
**Classification:** Internal-Public (mechanism only — no real SIDs, servers, or data values).

> **The log family is bigger than SQL now (2026-07-22).** Every loader ALSO writes a
> per-run log with the same anatomy — `load.<loader>.<stamp>.log`: header/meta from the
> process → captured `drydocs*` WARN stream + full reject detail → summary footer
> (`drydocs_core/run_log.py`, wired in `BaseLoader`; `run_log=False` opts out). One knob
> configures the whole family: `DRYDOCS_LOGDIR` (generic, wins) → `SPIDERP_LOGDIR`
> (company-compat fallback) → `~/logs/DryDocs`. The rest of this guide covers the SQL
> extract logs specifically.

## TL;DR

Only the `--use-oracle` path touches Oracle, and **every SQL statement it runs is written
to a per-run, timestamped log outside the repo** (default `~/logs/DryDocs`) so the HITL
can verify exactly what is being extracted. Each log is self-contained: run metadata →
connection handshake → the exact SQL (binds rendered for review) → the CSV result.
The CSV-sample path (no `--use-oracle`) never opens Oracle and writes no SQL log.

```
poetry run drydocs ingest-controlm --use-oracle --folder "CCB_AUTO_%"
```

## The chain (who logs what)

```
drydocs ingest-controlm --use-oracle
      |   (per stage: folders -> jobs -> conditions -> deps)
      v
OracleAdapter                 drydocs_core/adapters/oracle_adapter.py
   * opens the run log BEFORE connecting (a failed extract still leaves a trail)
   * handshake line: connected : Oracle Database <version>
   * logs the statement BEFORE executing — render_sql(query, binds), display-only
   * executes the ORIGINAL parameterized SQL with native oracledb binds
   * rows() tees every fetched row into the log as CSV while yielding dicts
      v
SqlRunLog                     drydocs_core/adapters/sql_run_log.py
   * writes <sql-file-base>.<yyyyMMdd-HHmmss>.log under SPIDERP_LOGDIR
   * header, statement, -- result (csv) --, footer
```

**No JDBC runner in this repo.** The company repo implements the same contract one level
lower (`jdbc_oracle_adapter.py` → `run-sql.cmd` → `SpiderpRunner.openTee()`, where the
`-- result (csv) --` framing is also a parse contract); see `docs/port/port-prompt.md` item 14.
Env-var names and log anatomy match across both repos so inspection snippets and runbooks
work identically. Here the CSV block is log-only — rows flow through the cursor, not stdout.

## Where the logs go

- **Directory:** `SPIDERP_LOGDIR` env var; default `~/logs/DryDocs` (deliberately outside
  the repo — code and logs in separate paths). Created automatically if missing.
- **File name:** `<sql-file-base>.<yyyyMMdd-HHmmss>.log`, e.g.
  `controlm_folders.sql.20260711-084212.log`. The console echoes
  `[sql-log] log: <path>` at the top of each run.
- **One log per statement-batch run** (one per adapter invocation → one per ingest stage
  that queries Oracle; the M3 chain writes up to five).

## What a log contains (in order)

```
==================================================================
date       : 2026-07-11T08:42:12-05:00
script     : drydocs ingest-controlm --use-oracle --folder CCB_AUTO_%   <- SPIDERP_CALLER
statement  : controlm_folders.sql
target     : <dsn / TNS alias>
user       : <oracle user>
bind mode  : native oracledb binds — SQL below rendered for review only
==================================================================
connected  : Oracle Database <version>

------------------------------------------------------------------
-- statement 1 --
<the exact SQL, binds rendered for review>
-- binds (passed natively) --
folder_filter = 'CCB_AUTO_%'
run_as = NULL
...
-- result (csv) --
<CSV header + rows>

Done. 1 statement(s), N row(s) in <ms> ms.
```

A failed extract still leaves the header and attempted SQL, closed with a
`FAILED: <error>` line — that trail is the point.

## Traceability: `SPIDERP_CALLER`

The log's `script:` line stamps the triggering command. If `SPIDERP_CALLER` is unset it
defaults to `drydocs <argv>`, so any logged query is traceable back to its
`ingest-controlm --use-oracle` run and its scope binds
(`--folder`, `--run-as`, `--developer-sid`, `--row-cap`).

## Injection safety (do not "fix" the SQL)

Two layers, both deliberate:

1. **Execution is always parameterized.** The rendered SQL is display-only; binds go to
   Oracle natively through python-oracledb. A rendering bug can corrupt a log line,
   never a query.
2. **`render_sql` substitutes `:binds` only in code regions** — text inside `--` / `/* */`
   comments, `'single-quoted strings'`, and `"quoted identifiers"` is copied verbatim
   (the company hardening, carried here from day one). So `:Application` / `:DEPENDS_ON`
   in comments and the literal `':depends_on'` in `controlm_dependencies_recursive.sql`
   are intentional and stay byte-identical — never de-colonize the `.sql` files.
   Pinned by `tests/unit/test_sql_run_log.py`.

## Environment variables

| Var | Purpose | Default |
|-----|---------|---------|
| `SPIDERP_LOGDIR` | log directory | `~/logs/DryDocs` |
| `SPIDERP_CALLER` | `script:` line stamp | `drydocs <argv>` |
| `ORACLE_USER` / `ORACLE_PASSWORD` / `ORACLE_DSN` | connection (via `.env`, `drydocs_core/config.py`) | unset → `--use-oracle` exits 2 |

(`SPIDERP_DSN` and `ORACLE_JDBC_RUNNER` exist only on the company JDBC path.)

**Logs may contain real DSNs and extracted data values.** They live outside the repo and
are never committed; real connection values stay in the gitignored `.env` /
`oracle_kerberos_connection.txt` — see `PUBLISH-BOUNDARY.md`.

## Inspecting the latest log

```powershell
Get-ChildItem $env:SPIDERP_LOGDIR -Filter *.log |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1 |
  Get-Content
```

(If `SPIDERP_LOGDIR` is unset, look in `~\logs\DryDocs`.)

## Related references

- `drydocs_core/adapters/oracle_adapter.py` — the adapter (tee seam)
- `drydocs_core/adapters/sql_run_log.py` — log writer + display renderer
- `tests/unit/test_sql_run_log.py` — the pinned contract
- `docs/controlm/controlm-staging-ingestion-flow.md` — ingest flow
- `docs/port/port-prompt.md` item 14 — company JDBC path + the bind-renderer back-flow rule
- `.claude/skills/run-drydocs/SKILL.md` — runbook + SQL-logging summary
