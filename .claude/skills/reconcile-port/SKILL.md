---
name: reconcile-port
description: Reconcile a producer push (ce-wilson/main) onto the company DryDocs main. Use when applying a new DryDocs port, syncing from the ce-wilson producer repo, resolving disjoint-history cherry-pick collisions, validating Track-1 after a port, or writing a port report.
---

You are on the **company** DryDocs repo. The **producer** is
`https://github.com/ce-wilson/DryDocs.git` (`main`). This repo was `git init`-ed
fresh, so the two histories are **disjoint — no common ancestor**. A port is
therefore a **cherry-pick / `git am`**, not a true rebase, and is **one-way**
(producer → company). Company `main` is canonical here and is *ahead* of the
producer in several areas (see the divergence ledger) — keep the company version
of those.

The authoritative per-port detail lives in the producer's `git-readme.md`
(`git show cewilson/main:git-readme.md`). This skill is the repeatable wrapper +
the accumulated lessons from prior ports. Read both.

## Procedure

1. **Preflight.** Clean tree, on `main`. Set a backup tag:
   `git tag -f pre-cewilson-port`. Add/refresh the remote and fetch:
   `git remote add cewilson https://github.com/ce-wilson/DryDocs.git` (ignore if
   it exists), then `git fetch cewilson main`.
2. **Read the guide:** `git show cewilson/main:git-readme.md`. Follow its
   "Clean-adds", "Canonical-here", and "Collisions" sections.
3. **Apply onto `main`** (skip the optional scratch branch unless asked):
   - **Clean-adds** (path absent here) → apply untouched.
   - **Canonical-here** → take the producer version wholesale, do **not**
     hand-merge: `git checkout cewilson/main -- <path>`. This includes the
     entire `drydocs/controlm/` package, `internal-standards/`, the Control-M
     SQL/DDL, `relationship_vocabulary.yaml`, `catalog_ontology_supplement.cypher`,
     **and the `tests/unit/test_variable_*` files** (taking these wholesale
     avoids re-deriving the skip guards — see ledger note).
   - **Collisions** → hand-merge per the ledger below.
4. **Validate Track-1** (the contract — needs no data file).
5. **Don't push.** Write a port report (template below) and stop.

## Collision ledger (resolve these by keeping the noted side)

| Path | Resolution |
|---|---|
| `drydocs/cli.py` | Keep company `m6-verify` (and `ingest-controlm-xml` etc.); **add** producer `analyze-variables` + `normalize-variables`, `m3-verify` (validates the ported M3 structural layer — keep it, it is **not** a stray), the `_scope_binds` / `--folder/--run-as/--developer-sid/--row-cap` options, and the `_oracle_adapter(query, bind_params=None)` change; merge imports. Confirm your `OracleAdapter` accepts `bind_params` and forwards it to `cursor.execute` (company Kerberos adapter already does). |
| `drydocs/models/__init__.py` | Union — keep **all** row models from both sides in imports + `__all__`. |
| `drydocs/models/controlm.py` | Keep company `ControlMQuantitativeRow`; add producer `ControlMVariableRow` (`AliasChoices` import is shared). |
| `tests/unit/test_schema.py` | Keep company `EXPECTED_CONSTRAINTS = 44` (ahead of producer's 35). |
| `tests/unit/test_controlm_cypher.py` | Keep company version (`scope_key` + version_serial-as-property). |
| `tests/unit/test_variable_classifier.py`, `test_variable_staging.py` | **Canonical-here — take producer wholesale.** They already carry `skipif(not SAMPLE.exists())` guards (producer commit `9e9fe1c`). Do not re-write your own guard; that caused redundant divergence in a prior port. |

**Skipped-commit policy:** the early overlap commits where company content is
already richer (prior ports skipped `3bc7adb`, `0eb98a5`, `6c5b7b5`, `0063f07`)
stay skipped — confirm with the operator if a new one appears.

## Divergence ledger (company is ahead — keep company)

- Verify command: company `m6-verify` vs producer `m3-verify`.
- `EXPECTED_CONSTRAINTS = 44` vs producer 35 (local consolidation).
- Condition key: `scope_key` vs producer `folder_id`.
- Suite size: company suite is much larger (scrapers/Confluence). **Do not chase
  the producer's `159 passed` full-suite number** — only zero *new* failures matters.
- `drydocs/adapters/oracle_adapter.py`: company version is **Kerberos-aware**
  (thick via `_init_thick_client` / `externalauth` when `ORACLE_KERBEROS=True`);
  the producer version is thin-only. **Keep company's** — it carries the JPMC
  connection config (`client_path`, `tns_admin`, TNS alias). The producer's
  scope-bind SQL runs under it unchanged.

## Track-1 acceptance (the contract)

Run as a SINGLE line (multi-line `\` continuations break in some agent shells):

```
poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py tests/unit/test_variable_staging.py tests/unit/test_command_parser.py -q
```

(If `poetry` is not on PATH, use `python -m pytest <same files> -q`.) Expect
**86 passed, 3 skipped, 0 failed**. The 3 skips are the sample-backed
tests (`test_sample_classifies_end_to_end`, `test_sample_bundle_smoke`,
`test_sample_end_to_end_counts`) — the production CSV is gitignored and never
transfers, so they skip, not fail. A `FileNotFoundError` instead of a skip means
the skip guard was lost in the port (re-apply the Canonical-here test files).

## Track-2 (optional — real data, or fresh sample)

Bundled exact counts (89 passed; `normalize-variables` → inv=6, file_op=16,
file_ref=92, notif=14, app_fact=66, 86.2%) only hold with the bundled sample
present. For a fresh `psgmgr` pull:

- **Connection mode is environment-specific — check before assuming.** The
  producer's `OracleAdapter` is thin-only (no `init_oracle_client`), but the
  COMPANY adapter is Kerberos-aware and goes THICK when `ORACLE_KERBEROS=True`
  (calls `_init_thick_client` + `connect(externalauth=True)` against a TNS
  alias). In that config a plain `--use-oracle` run uses OCI and WILL hit the
  real Kerberos SPN errors (ORA-12514 / ORA-12638) — that is a DBA / SPN /
  tnsnames issue, NOT a code toggle. Thin mode is only an option if you can set
  `ORACLE_KERBEROS=False` AND supply a real `host:port/service` DSN (a TNS alias
  like `SPIDERP` resolves only via tnsnames and won't work thin).
- Scope binds are **connection-mode agnostic** (NULL-tolerant SQL predicates —
  they work the same under thick/Kerberos once the SQL is ported): `--folder`
  (SCHED_TABLE LIKE), `--run-as` (tenant FID = `OWNER`), `--developer-sid`
  (`AUTHOR`/`CREATION_USER`/`CHANGE_USERID`, or folder `LAST_UPDATED_USER`),
  `--row-cap`. NULL = full population. If your `normalize-variables` lacks these
  flags or the SQL still pulls all ~1.1M rows, you have NOT yet ported the scope
  commits — re-port `controlm_variables.sql` wholesale and merge the cli.py
  scope options (see the collision ledger).
- This run also **verifies the `psgmgr.CM_DEF_SETVAR` source-view name** (still
  flagged unverified). Confirm it and report.
- Judge a fresh pull on *runs clean / no UNKNOWN invocation leakage / plausible
  coverage*, **not** the bundled counts.

## Port report (write this, do not push)

```
Port Report: cewilson/main -> <company>/main
- What applied (clean cherry-picks): <count + the controlm/canonical-here paths>
- What conflicted + resolution: <per collision ledger>
- What was skipped: <commits + why>
- Track-1 result: <N passed, 3 skipped, 0 failed>
- Track-2 status: <ran/blocked + CM_DEF_SETVAR finding>
- State: branch ahead of <company>/main by N; NOT pushed; backup tag pre-cewilson-port
- New divergences observed: <add to the ledger if any>
```
