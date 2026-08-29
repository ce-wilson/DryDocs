# Runbook — operate `drydocs-core`: env roots, schema provisioning, the vocabulary registry, run logs

<!-- anchor: front-matter -->
- **Module:** drydocs-core — this runbook IS the module runbook for drydocs-core
  (V1 coverage rule). The mapping-store runbook covers ONE artifact of this module
  (`var/mapping.db`) and says so; everything else in core lives here.
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 2, 2026-08-04**,
  authored at commit `416d217` (post-S5 fragment directories, post-G51 `ddschema`,
  post-G54 exec-aware provisioning). **Rev 2, same day:** the Verify step listed the
  topology databases inline and named `ddlineage`, which the X1 amendment retired hours
  later — the enumeration is now READ from `config/dev-environment.yaml` instead of
  copied, which is the only version that cannot go stale.
- **Classification:** Internal-Public (mechanism only — env-var NAMES, default paths and
  synthetic values; NO credentials, no company values. The one rule that keeps it that
  way: this runbook names variables, never their contents)
- **Audience:** anyone configuring a DryDocs environment, provisioning the databases, or
  asked "why did that loader see nothing?" — the answer is usually one of the four
  surfaces below
- **Companion:** `drydocs_core/schema/provisioning/README.md` (the provisioning scripts
  this section points at), `docs/design/drydocs-mapping-store-runbook.md` (the SQLite
  materialization), `docs/design/drydocs-startup-refresh-runbook.md` (the SYSTEM-level
  cold start that calls into all of this), `docs/design/drydocs-api-runbook.md` (the
  reader), `docs/RELATIONSHIP_GUIDE.md` (how a vocabulary entry is authored)

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Operate the four surfaces of `drydocs-core` that an SME or operator actually
touches: **where configuration comes from**, **how the databases and schema get
provisioned**, **what the relationship-vocabulary registry guarantees**, and **where the
run logs are** when something needs reviewing.

**Why it reads the way it does.** Core is a library — it has no server to start and no
chain of its own to run. Its failure modes are therefore almost never exceptions; they
are **silence**: a loader that writes nothing, a MATCH that finds nothing, a log that was
written somewhere you did not look. Each section below is organised around the silence it
prevents rather than around the code.

**In scope.** `Neo4jSettings` and the env roots (`DRYDOCS_DATA_ROOT`, `DRYDOCS_LOGDIR`);
the databases + constraints + ontology seed and when to re-apply them; the
relationship-vocabulary registry and its guards; the run-log family; and the YAML
fragment-directory contract that S5 introduced.

**Out of scope.** `var/mapping.db` (its own runbook); the loaders and the CLI load chain
(startup/refresh runbook, `drydocs-load`); serving anything over HTTP (`drydocs-api`);
authoring a NEW relationship type — that is an ontology decision through
`docs/RELATIONSHIP_GUIDE.md` and the HITL gate, not an operation.

<!-- anchor: prerequisites -->
## Prerequisites

- **Python toolchain:** `poetry install` (the default group; the API group is optional and
  belongs to `drydocs-api`).
- **A Neo4j ENTERPRISE DBMS** for anything that provisions. Multi-database and composite
  are Enterprise-only; Community allows exactly one user database and cannot host the
  topology at all.
- **`.env` at the repo root** — NAMES only here:

  | Variable | Default | What it decides |
  |---|---|---|
  | `NEO4J_URI` | `bolt://localhost:7687` | which DBMS |
  | `NEO4J_USER` | `neo4j` | — |
  | `NEO4J_PASSWORD` | (none) | read server-side, never in a request |
  | `NEO4J_DATABASE` | unset | **which database a verb writes to** |
  | `DRYDOCS_DATA_ROOT` | `~/data/DryDocs` | out-of-repo source payloads |
  | `DRYDOCS_LOGDIR` | `~/logs/DryDocs` | where every run log lands |
  | `DRYDOCS_CALLER` | — | the `script:` stamp in a log header |

  `DRYDOCS_LOGDIR` falls back to `SPIDERP_LOGDIR`, and `DRYDOCS_CALLER` to
  `SPIDERP_CALLER` — the Oracle path's original names, kept deliberately so an existing
  scheduled job keeps working. If logs are "missing", check the legacy name before
  concluding nothing ran.
- **`NEO4J_DATABASE` is the one worth double-checking.** Left unset, writes land in the
  EE home database `neo4j`, which is NOT part of the ADR 0002 topology — the load
  succeeds and no query surface ever looks there. `config/dev-environment.yaml` carries
  the warning in the same words.

<!-- anchor: startup -->
## Startup

Core has no process. "Startup" is bringing a fresh DBMS to the point where loaders can run.

1. **Provision the topology** (databases + composite + proxy constraints). This is the
   provisioning README's procedure, not repeated here:
   ```powershell
   .\drydocs_core\schema\provisioning\provision.ps1 -Password <pw>
   ```
   Since G54 the script is exec-aware: no host `cypher-shell` needed, it falls back to
   `docker cp` + `docker exec` and reads the container name from
   `config/dev-environment.yaml`. Success: it prints the transport it chose, then
   `OK  G1 topology provisioned + smoke passed`.

2. **Confirm connectivity and APOC:**
   ```powershell
   poetry run drydocs check
   ```
   Success: server version, then `APOC OK.` APOC is load-bearing — `bootstrap` refuses
   without it, and it was silently absent for weeks once (2026-07-28) because the
   plugin was requested by env var instead of mounted.

3. **Apply constraints + the ontology seed:**
   ```powershell
   poetry run drydocs bootstrap
   ```
   Idempotent. Success: constraints applied with a non-zero count — a "Constraints
   applied." with zero constraints is the D8 defect, not a clean run.

4. **Apply the schema meta-graph** (its own database, `ddschema`):
   ```powershell
   poetry run drydocs bootstrap-schema-graph
   ```
   Success: `Schema meta-graph applied to 'ddschema' (N label nodes)`. It guards on zero
   and exits 2, so a silent no-op cannot pass.

5. **Apply the ontology supplements** — ONE ordered chain, never the per-file verbs:
   ```powershell
   poetry run drydocs apply-supplements
   ```
   Success: a table with `Declared terms`, `Verified` and `OK yes` per supplement. The
   order is load-bearing (catalog reuses classes `seal` declares) and lives in one place,
   `drydocs_core/schema/supplements.py`.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

Core is not ingested. What changes underneath it, and what to do:

- **A config or vocabulary edit** — nothing to re-run for core itself. Consumers re-read
  on next use, and `var/mapping.db` rebuilds itself on source-hash drift.
- **A supplement edit** — re-run `apply-supplements`. It is idempotent and it VERIFIES:
  every `:OntologyTerm` IRI a file declares is checked for presence afterwards, so a
  supplement that runs and seeds nothing FAILS the command instead of surfacing later as
  an empty loader MATCH. That verification is the whole reason the chain exists.
- **A constraints edit** — re-run `bootstrap`. Idempotent; a same-name re-declare
  succeeds and does nothing, which is the trap worth knowing: to CHANGE a constraint you
  must DROP it first, or the re-declare silently leaves the old one in place.
- **A schema/label change** — re-run `bootstrap-schema-graph` so the meta-graph matches.
- **The fragment directories (S5).** `relationship_vocabulary/` and
  `config/taxonomy-ontology-map/` are DIRECTORIES merged in lexical filename order
  (`00-header`, `10-node-classifications`, … `4x-local-*`). Adding a domain means adding
  a file, not editing a monolith. A duplicate key ACROSS fragments is a hard error, not
  last-one-wins — `FragmentSourceError` names both files.

<!-- anchor: verify -->
## Verify

**1. Configuration resolves where you think it does** — this answers most "it wrote
nothing" reports:
```powershell
poetry run python -c "from drydocs_core.config import Neo4jSettings; from drydocs_core.data_root import resolve_data_root; from drydocs_core.run_log import resolve_log_dir; s = Neo4jSettings(); print('uri     :', s.uri); print('database:', s.database or '(UNSET -> EE home db neo4j, NOT the topology)'); print('data    :', resolve_data_root()); print('logs    :', resolve_log_dir())"
```
Prints no secret — `password` is a `SecretStr` and is not in the output.

**2. The topology exists and is online:**
```cypher
SHOW DATABASES YIELD name, type, currentStatus;
```
**Do not expect a list from this runbook — read the canonical one**, because the topology
changes and a copy here goes stale (it did: this line named `ddlineage` for a few hours
until the X1 amendment retired it):

```powershell
poetry run python -c "import yaml; print(yaml.safe_load(open('config/dev-environment.yaml'))['neo4j']['databases'])"
```

`config/dev-environment.yaml` is the canonical list, and
`tests/unit/test_dev_environment.py` holds it BIDIRECTIONALLY against
`01_databases.cypher` — a database in one and not the other fails the suite. Every name
it reports should come back `online` from `SHOW DATABASES`. Since the G32/G102 fold
(2026-08-18) that list is `drydocs` + `ddschema`; the composite `ddall` retired with its
second constituent, so a container still showing it predates the fold and owes a drop.

**3. The vocabulary registry is coherent.** These are guards, so run them rather than
reading the file:
```powershell
poetry run pytest tests/unit/test_schema.py -q
```
They pin: every ACTIVE entry is declared in a supplement, the PROV matrix is complete, no
duplicate ids across fragments, and every entry has an inverse label. An `active` entry
with no supplement is the failure that matters — it means a loader can MATCH a term
nothing seeds.

**4. The run logs landed:**
```powershell
Get-ChildItem (poetry run python -c "from drydocs_core.run_log import resolve_log_dir; print(resolve_log_dir())") -Filter *.log | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```
Names are `<kind>.<name>.<YYYYmmdd-HHMMSS>[-N].log` — loader runs use kind `load`. Each
carries a header (date, script, loader, run id, source, target, os user, batch size) and
a summary footer with `rows_processed / rows_rejected / rows_changed / status`.

**5. Everything at once:** `poetry run pytest -q` — core carries the largest share of the
suite, and it is hermetic (no Neo4j needed).

<!-- anchor: rollback -->
## Rollback

- **Config:** revert the `.env` edit; nothing is cached across a process.
- **Supplements, constraints, the meta-graph:** all idempotent — re-running IS the
  rollback for a partial apply. The exception is a constraint whose DEFINITION changed:
  drop it explicitly first, because a same-name re-declare is a silent no-op.
- **Vocabulary/config edits:** git. They are committed text and that is the point —
  `var/mapping.db` and the graph are both derived from them, so reverting the file and
  re-running is a complete rollback with no migration step.
- **A bad graph load:** not this runbook's — see the startup/refresh runbook and the
  loader's own soft-delete/sweep mechanics. Core provides the schema, not the data.
- **Destructive last resort:** dropping and re-provisioning a database. Blast radius is
  that database's entire contents, and for `drydocs` that is the whole estate load —
  budget a full re-ingest, and check `v_open_drafts` in `var/mapping.db` first if the
  console has unpromoted work.

<!-- anchor: troubleshooting -->
## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| A loader ran, reported OK, and the graph is empty | `NEO4J_DATABASE` unset → wrote to the EE home db `neo4j`, outside the topology | set it to a topology database (normally `drydocs`) and re-run |
| `bootstrap` refuses: "APOC required" | APOC absent — usually requested via `NEO4J_PLUGINS` (a download at startup) instead of mounted from the image | mount the plugins volume per the provisioning header; `drydocs check` confirms |
| "Constraints applied." with zero constraints | the D8 defect — a silent no-op reported as success | check the guard; a real apply reports a count |
| A loader MATCHes nothing and rejects nothing | a supplement did not seed its terms | `apply-supplements` — it verifies declared IRIs and fails loudly; never the per-file verbs, which is how `registry` was omitted for weeks |
| A constraint change did not take effect | same-name re-declare succeeds and does nothing | DROP it first, then create |
| `FragmentSourceError: duplicate key` | the same id in two fragments of one directory (S5) | the message names both files; ids are unique across the whole directory, not per file |
| Logs "missing" | `DRYDOCS_LOGDIR` unset and `SPIDERP_LOGDIR` set, or vice versa | resolve it with the Verify step 1 one-liner rather than guessing |
| `provision.ps1`: cypher-shell not found | pre-G54 script, or `-Container` unresolvable | current script auto-falls back to docker exec; check `neo4j.container` in `config/dev-environment.yaml` |
| Enterprise-only feature refused | Community edition | the topology needs Enterprise; see backlog G53 for the single-DB contingency |

<!-- anchor: contacts-escalation -->
## Contacts & escalation

Mechanism only; no on-call rota. The line that matters: **anything that changes what an
edge MEANS is not an operation.** A new relationship type, a status flip from `planned`
to `active`, a new node classification — all route through `docs/RELATIONSHIP_GUIDE.md`,
the relationship-vocabulary registry, and the HITL gate
(`docs/restructure/03-hitl-sme-flow.md`). Applying a supplement is operational; deciding
what it declares is not. Provisioning topology decisions are ADR-governed (ADR 0002 and
its amendments) — a database is added by amending the ADR and
`01_databases.cypher` together, never by hand on a live DBMS.

<!-- anchor: appendices -->
## Appendices

**A. The four env roots and their fallbacks** — the fallbacks exist so pre-rename
scheduled jobs keep working, and they are the reason a path can look "wrong":

| Resolver | Chain |
|---|---|
| `resolve_data_root()` | `DRYDOCS_DATA_ROOT` → `~/data/DryDocs` |
| `resolve_log_dir()` | `DRYDOCS_LOGDIR` → `SPIDERP_LOGDIR` → `~/logs/DryDocs` |
| `caller_stamp()` | `DRYDOCS_CALLER` → `SPIDERP_CALLER` → derived |
| `Neo4jSettings` | env prefix `NEO4J_`, then the defaults in the Prerequisites table |

**B. The supplement chain**, in its load-bearing order — the single source is
`drydocs_core/schema/supplements.py`, and this table is a copy that can go stale:

`base` → `seal` → `catalog` → `registry`, plus `sosa` (opt-in, `--with-sosa`).

Re-derive rather than trust:
```powershell
poetry run python -c "from drydocs_core.schema.supplements import SUPPLEMENTS; print([(s.name, s.filename) for s in SUPPLEMENTS])"
```

**C. Vocabulary fragment directory** (S5): `drydocs_core/ontology/relationship_vocabulary/`
— `00-header`, `10-node-classifications`, `20-property-terms`, `30-prov-matrix`, then
`4x-local-<domain>`. Merged in lexical filename order; ids unique across the directory.
