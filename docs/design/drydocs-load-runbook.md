# Runbook — operate `drydocs-load`: individual loaders, their envelopes, snapshots and sweeps

<!-- anchor: front-matter -->
- **Module:** drydocs-load — this runbook IS the module runbook for drydocs-load
  (V1 coverage rule; V3 ruled AUTHOR-DISTINCT, see Purpose & scope for the overlap ruling
  against the system-level startup/refresh runbook).
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 2, 2026-08-04**
  (N6 landed: the two operator surfaces are now PROFILES of the declaration rather than
  hand-maintained copies, so the "until N6 lands they can disagree" framing below is
  replaced by what the profiles are; the re-derive one-liner is also fixed — N6 widened
  each step from a 3-tuple to a named `LoadStep`, which broke the unpacking this document
  told readers to run); on top of Rev 1, authored at commit `0b67b66`.
- **Classification:** Internal-Public (mechanism only — bundled sample data, env-var
  NAMES, no credentials, no company values)
- **Audience:** anyone running ONE loader rather than the whole chain, reading a run
  envelope, deciding whether a rejected row matters, or sweeping soft-removed nodes
- **Companion:** `docs/design/drydocs-startup-refresh-runbook.md` (the SYSTEM-level cold
  start that calls this module — **it owns the sequence, this document does not**),
  `docs/plan/load-map.html` (the generated canonical sequence),
  `docs/design/drydocs-core-runbook.md` (schema, env roots, run logs),
  `knowledge/standards/node-status-envelope.md` (the envelope this runbook reads)

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Operate the load module at the grain the cold-start procedure does not:
one loader at a time. Reading its envelope, judging its rejects, re-running it safely,
recomputing snapshots, and sweeping what a source stopped sending.

### The overlap ruling (V3)

The startup/refresh runbook is **SYSTEM-level**: container up → schema bootstrapped →
sample data ingested → invariants green, spanning `graph-infra`, `drydocs-core` and this
module. Declaring it the drydocs-load module runbook would have required either narrowing
it (it covers Docker and provisioning, which are not this module) or widening this module
to own the container (which is not its either). Neither is honest, so **the two are
distinct and cross-reference**.

**THE DIVISION, in one line: the startup/refresh runbook answers "run the chain"; this one
answers "run, read, and repair one loader".**

### And this document deliberately does NOT restate the load sequence

There is exactly one canonical sequence, `cli.CANONICAL_LOAD_SEQUENCE`, published to
`docs/plan/load-map.html` and `web/src/generated/load-map.json`. The two operator surfaces
— `scripts/ingest.sh` and the startup/refresh runbook's Appendix B — are **profiles** of
it since N6, not copies of it. A third copy here would put back exactly what N6 removed,
so there is none. To see the sequence, open the load map or run:

```powershell
poetry run python -c "from drydocs.cli import CANONICAL_LOAD_SEQUENCE as s; print(*[f'{x.mode:9} {x.command}' for x in s], sep='\n')"
```

This is not fastidiousness. On 2026-08-04 the drydocs-core runbook copied the topology
database list inline and it was stale within hours, because a concurrent amendment retired
one of them. A copy is kept current by discipline; a pointer cannot go stale at all.

**In scope.** Running one loader; the run envelope and status items; rejected rows;
idempotency and safe re-runs; soft-delete and `sweep-removed`; snapshots (`snapshot`,
`prune-snapshots`); `docs-verify`; staging (`drydocs.staging`, `drydocs.cmdline_staging`).

**Out of scope.** The cold start and the full chain (startup/refresh runbook); schema,
constraints, supplements and env roots (core runbook); `var/mapping.db` (mapping-store
runbook); serving anything (`drydocs-api`); what a loader's edges MEAN — that is the
ontology and the HITL gate.

<!-- anchor: prerequisites -->
## Prerequisites

- **A provisioned, bootstrapped graph.** Databases exist, constraints applied,
  supplements verified — the core runbook's Startup, or the startup/refresh runbook's
  cold start. A loader against an unbootstrapped graph fails on a missing constraint or,
  worse, MATCHes a term nothing seeded and quietly writes nothing.
- **`NEO4J_DATABASE` set to a topology database** (normally `drydocs`). Unset, writes land
  in the EE home db `neo4j` where no query surface looks. This is the single most common
  cause of "the loader said OK and the graph is empty".
- **`poetry install`** — the default group; no API extras needed.
- **Source data**: the bundled samples need nothing. Oracle-backed and out-of-repo payload
  runs need `ORACLE_*` credentials and/or `DRYDOCS_DATA_ROOT` per the core runbook.
- **Know where the logs go** before you start, not after: `DRYDOCS_LOGDIR`, falling back to
  `SPIDERP_LOGDIR`, then `~/logs/DryDocs`.

<!-- anchor: startup -->
## Startup

This module has no service. "Startup" is running a single loader deliberately.

1. **Confirm the graph is ready** (cheap, and it is the check that prevents a silent run):
   ```powershell
   poetry run drydocs check
   ```
   Success: server version and `APOC OK.`

2. **Pick the verb.** Every load verb is listed by `poetry run drydocs --help`; the
   sequence they belong to is the load map, not this page.

3. **Run ONE loader** — most take `--csv` for a specific file, and the Control-M chain
   takes `--use-oracle` and scoping flags:
   ```powershell
   poetry run drydocs load catalog_lobs --csv internal/org/catalog/catalog_lobs.csv
   poetry run drydocs ingest-controlm --use-oracle --folder "PATTERN_%"
   ```
   Success: the run envelope printed at close, with `'status': 'OK'`.

4. **Read the envelope before moving on.** It is the whole point of the run:
   ```
   rows_processed / rows_rejected / rows_changed
   nodes_marked_removed / nodes_reactivated / unresolved_parents
   status
   ```
   `rows_processed: 8, rows_changed: 0` is a healthy no-op re-run. `rows_rejected > 0`
   is a data question, not necessarily a failure — see Troubleshooting.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

**The recurring chain is the startup/refresh runbook's.** What belongs here is what you
do to ONE loader between chain runs.

- **Re-running is safe.** Every loader is idempotent — MERGE on a business key, `ON CREATE`
  for first-seen, unconditional `SET` for enrichment. A second run with the same input
  reports `rows_changed: 0`.
- **A sparse extract is the exception worth knowing.** A partial source can blank an
  enrichment property where a loader still writes `SET x.name = row.name` instead of
  `coalesce(row.name, x.name)`. C22 fixed the three catalog loaders; **C24 is open for
  `dev_teams.cypher` and `catalog_lobs.cypher`**, so on those two prefer a full extract
  until it lands.
- **Soft delete, then sweep.** A row that a source stops sending is MARKED removed, not
  deleted — `nodes_marked_removed` in the envelope. It stays queryable and tombstoned
  until you explicitly:
  ```powershell
  poetry run drydocs sweep-removed
  ```
  Hard-deletes what was soft-marked. Run it deliberately: a source outage looks exactly
  like a deletion to a loader, so sweeping straight after a failed extract removes real
  nodes. Check `nodes_marked_removed` against what you expect BEFORE sweeping.
- **Snapshots** recompute without re-loading source:
  ```powershell
  poetry run drydocs snapshot
  poetry run drydocs prune-snapshots        # deletes older than N years, keeps the newest
  ```
- **Doc corpora** reconcile declared-vs-loaded, and exit non-zero on the wrong database —
  which makes it a useful `NEO4J_DATABASE` check on its own:
  ```powershell
  poetry run drydocs docs-verify
  ```

<!-- anchor: verify -->
## Verify

**1. The envelope said OK** — necessary, not sufficient. `status: OK` with
`rows_processed: 0` means the loader ran and found no input.

**2. The invariants hold:**
```powershell
poetry run drydocs m1-verify
poetry run drydocs m3-verify
```
M1 covers the reference/catalog/SEAL layer, M3 the Control-M chain. These are assertions
about the populated graph, so they are the real proof a load worked — the envelope only
proves the loader ran.

**3. The run log exists and its footer agrees with the console.** Newest first:
```powershell
Get-ChildItem (poetry run python -c "from drydocs_core.run_log import resolve_log_dir; print(resolve_log_dir())") -Filter load.*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 3
```
Header carries date, script, loader, run id, source, target, os user, batch size; the
footer carries the same counts the console printed. If they disagree, trust the log — it
is written at close from the graph.

**4. Status items, for anything that needs review.** They are measurements written to
`:JobRun.status_items` by `BaseLoader._close_run`, never typed by a human. An empty list
on an existing `:JobRun` means **healthy — a producer ran and found nothing to report**,
which is a different statement from "nothing ran". `knowledge/standards/node-status-envelope.md`
is the contract.

**5. The suite**, for the loader contracts themselves: `poetry run pytest -q` (hermetic,
no graph needed).

<!-- anchor: rollback -->
## Rollback

- **A bad run of an idempotent loader:** fix the source and re-run. That IS the rollback —
  MERGE-on-business-key means the second run converges rather than duplicating.
- **Rows that should not have been written:** they are soft-marked on the next clean run
  when the source no longer sends them; `sweep-removed` then removes them. Prefer this
  over hand-deleting, because it goes through the same tombstone path everything else does.
- **A sweep you regret:** hard delete is not reversible from here. Recovery is a re-load
  from source. This is the reason the two steps are separate verbs.
- **A snapshot:** recompute with `snapshot`; it is derived from the graph.
- **The whole database:** out of scope — the startup/refresh runbook's re-ingest, or the
  core runbook's destructive last resort with its blast radius stated there.

<!-- anchor: troubleshooting -->
## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| `status: OK`, graph empty | `NEO4J_DATABASE` unset → wrote to the EE home db | set it to `drydocs`; `docs-verify` exits non-zero on the wrong db |
| `rows_processed: 0` | the loader found no input rows — path, filter or scope | check the `source:` line in the run-log header, which records what it actually read |
| `rows_rejected > 0` | rows failed the row model (the loader shares the store's validation chain) | the log carries UNCAPPED reject detail; a reject is a data question — decide, do not ignore |
| `unresolved_parents > 0` | a parent id did not resolve; the node was written with an orphan flag and the failing id kept | that is by design (C17/C22) — count them, then fix the source or the load order |
| Constraint violation naming an existing node | a key changed underneath the graph, e.g. the S3 `seal_id` → `app_id` cutover against a graph never re-keyed. Uniqueness IGNORES NULLS, so a MERGE on the new key creates a twin and the old key then collides | backfill the new key on existing nodes BEFORE re-running; see the S3 tracker note |
| Loader MATCHes nothing, rejects nothing | a supplement did not seed its terms | `apply-supplements` (core runbook) — it verifies and fails loudly |
| A name went blank after a refresh | sparse extract + an unconditional `SET` | C22's `coalesce` fix; C24 is open for `dev_teams`/`catalog_lobs` |
| `nodes_marked_removed` unexpectedly large | a source outage looks identical to a deletion | do NOT sweep; re-run against a good extract first |
| No run log | `DRYDOCS_LOGDIR` vs the `SPIDERP_LOGDIR` fallback | resolve it, do not guess (core runbook, Verify step 1) |

<!-- anchor: contacts-escalation -->
## Contacts & escalation

Mechanism only; no on-call rota. The boundary that matters: **running a loader is
operational; changing what it writes is not.** A new relationship type, a status flip from
`planned` to `active`, a new mapping — all route through `docs/RELATIONSHIP_GUIDE.md`, the
relationship-vocabulary registry and the HITL gate
(`docs/restructure/03-hitl-sme-flow.md`). Manual tier-5 mappings carry their own manifest
governance (`config/manual-loads/manifest.yaml`, gate `seal-attribution-match-policy` §F).
**The loader is the only graph writer** — no console, API or agent surface writes the
graph, and that contract is enforced in `drydocs-api`'s own guard rather than assumed.

<!-- anchor: appendices -->
## Appendices

**A. The module's surface**, per `MODULE_MAP` (`tests/unit/test_module_boundary.py` is the
authority and will fail if this drifts): `drydocs.loaders`, `drydocs.cli`,
`drydocs.snapshots`, `drydocs.staging`, `drydocs.cmdline_staging`, `drydocs.docs_verify`.

**B. Where the sequence lives** — deliberately not reproduced here:

| Surface | What it is |
|---|---|
| `cli.CANONICAL_LOAD_SEQUENCE` | the declaration, single source |
| `docs/plan/load-map.html` + `web/src/generated/load-map.json` | the generated view |
| `scripts/ingest.sh` | the `scheduled-ingest` profile — READ at run time, no list of its own |
| startup/refresh runbook, Appendix B | the `cold-start` profile — prose, held to the declaration by `tests/unit/test_load_sequence_surfaces.py` |

Since N6 (2026-08-04) both surfaces derive from the declaration. The scheduled profile is
deliberately the smaller one — a Control-M ingest is not a full refresh — and every
standing step it skips carries its reason in `cli.SCHEDULED_INGEST_EXCLUSIONS`, because
an unexplained subset is indistinguishable from an oversight. That ambiguity was the
actual defect N6 closed; the exhibit was `bootstrap-schema-graph`, which ran in both
operator surfaces while missing from the declaration, so the published load map counted
15 steps where both real paths ran 16.

**C. Reject and envelope reference:** `knowledge/standards/node-status-envelope.md`.
