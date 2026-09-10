---
name: neo4j-db
description: "Neo4j guidance for THIS graph — the DryDocs database topology, Cypher execution path, client API, schema/constraint DDL and the failure modes this project has already met. Use when: (1) writing or reviewing Cypher against the DryDocs graph, (2) adding or changing a loader template, a supplement, or constraint DDL, (3) using drydocs_core.neo4j_client.Neo4jClient or the bootstrap / check / apply-* / *-verify CLI verbs, (4) provisioning or troubleshooting the local Enterprise container, or (5) diagnosing an empty result, a hang, an APOC complaint or a 'constraints applied' that applied nothing. THIS SKILL LOADS IN EVERY VENUE (VS Code, Copilot, Claude Code) because it is a filesystem skill; the neo4j-skills plugin loads under Claude Code only and covers version-current VENDOR Neo4j. They are complements: this one is authoritative for this graph's topology, dialect boundary and failure modes, the plugin for general Cypher and modeling practice. Mechanism-only: never emit real credentials, container registry hosts, SIDs or data values."
---

# Neo4j — this graph, not Neo4j in general

The `neo4j-skills` plugin is the vendor reference and it is excellent. It is also
**Claude Code only** — a filesystem skill like this one loads everywhere, and in a
venue with no plugin loader every `neo4j-skills:*` route resolves to nothing with no
error. This file carries what the plugin cannot know: the topology DryDocs runs, the
dialect boundary it sits on, and the ten or so failures it has already paid for.

**Read this first, then reach for the plugin** (under Claude Code) for general Cypher,
modeling, GraphRAG and tuning practice.

---

## 1. The topology — two databases, three retired (ADR 0002)

| Database | Kind | What it holds |
|---|---|---|
| `drydocs` | standard | **Ground truth.** Every loader writes here. Curated lineage lives here too. |
| `ddschema` | standard | The schema meta-graph, written by `drydocs bootstrap-schema-graph`. |

`drydocs_core/schema/provisioning/01_databases.cypher` creates both, run against the
**`system`** database. `tests/unit/test_database_names.py` pins the live set to exactly
those two, so adding a third is a guard failure until the pin moves with it.

**Why `ddschema` is separate and must stay separate.** Its exemplar nodes carry the
REAL label beside `:SchemaMeta` — `MERGE (n:SchemaMeta:ControlMJob {name: 'ControlMJob'})`
— so running `schema_graph.cypher` against `drydocs` violates `controlmjob_key`: a NODE
KEY enforces property existence and the exemplar carries only `name`. It is deliberately
**not aliased** anywhere: federating exemplars with real jobs would present labels as data.
Its single constraint, `schemameta_name`, lives in `schema_graph.cypher` and NOT in
`constraints.cypher` — on purpose, so the pinned constraint census does not move.

**Three names are RETIRED. A document or memory that names them is stale:**

- **`ddlineage`** — retired 2026-08-04 (ADR 0002 X1). Nothing ever wrote it; curated
  lineage writes go to `drydocs`.
- **`ddcontext`** — retired 2026-08-18 (gate `document-content-topology` §A, applied at
  G102, ADR 0011). The trust boundary is no longer the database boundary: uncertain data
  is an `:Uncertain` label plus a mandatory trust property, **inside `drydocs`**.
- **`ddall`** — a COMPOSITE database, retired with its second constituent. A composite
  over one database federates nothing.

**Provisioning never DROPS**, so a container older than either retirement still lists the
dead names after a green run. That gap is where two real defects grew (a module pointing
at a database provisioning never created; four query specs reading one nothing writes).
Drop them per machine behind a zero-node emptiness probe — **a non-empty probe is a defect
report, not a cleanup.**

**Never drop `system`.** And `neo4j`, the Enterprise home database, is not part of the
topology at all — see the trap in §6.

**Enterprise is required**, three times over: multi-database and composite are
Enterprise-only, and `constraints.cypher` declares NODE KEY constraints, which are too.
Community allows exactly one database and is a recorded rejected alternative, not a
fallback.

---

## 2. The version boundary — get this right or you will write the wrong dialect

| | Value | Where |
|---|---|---|
| **Server image** | `neo4j:2026.05.0-enterprise` | `config/dev-environment.yaml` `neo4j.image`, guarded by `tests/unit/test_dev_environment.py` |
| **Python driver** | `neo4j = "^5.20"` → resolves 5.28.4 | `pyproject.toml` |

**These two are decoupled and conflating them has already produced defects.** `^5.20` is
a DRIVER floor. It is not a server tag, and there is no 5.20 server anywhere in this
project. The store in the `neo4j-testdata` volume was written by 2026.05.0 and **cannot be
downgraded** — provisioning against a 5.x image fails on store format, it does not merely
differ.

**The one dialect rule this tree actively engineers around: Cypher 25 rejects an empty
statement. Neo4j 5.x tolerated it.** That single difference is why §3 exists.

What the tree does **not** enforce: there is no syntax-version linter, no `CYPHER 5` /
`CYPHER 25` prefix in any `.cypher` file, and no ban on deprecated 4.x constructs. The
static checks over Cypher files are semantic (template content, constraint names), not
syntactic. So dialect correctness is on you.

---

## 3. How Cypher actually runs here — client-side splitting, and why

**`apoc.cypher.runMany` is called NOWHERE in this tree.** Every remaining mention is a
comment or docstring explaining the landmine. It was dropped at D5 (2026-07-18).

It was dropped because it failed twice, in two different ways:

1. **Hard error.** `runMany` splits on every `;` it sees — *including one inside a `//`
   comment*. The first Enterprise-container bootstrap on 2026.05.0 / Cypher 25 failed
   `apply-ontology-supplement` because a sheared comment produced an empty fragment and
   the new server rejected it. 5.x had tolerated it.
2. **Silent no-op, which is worse.** `runMany` silently no-ops DDL. Pre-D5 bootstraps
   printed `Constraints applied.` while creating **zero** constraints.

**The fix class is to never let a server-side splitter see the script.**
`drydocs_core/cypher_split.py` is a comment- and string-aware scanner that only honours
semicolons that are really statement terminators. Its public surface:

```python
code_semicolon_positions(cypher: str) -> list[int]   # indexes outside comments/strings
code_semicolons(cypher: str) -> int                  # the dispatch test
has_code(fragment: str) -> bool                      # anything but whitespace/comments?
strip_comments(cypher: str) -> str                   # code untouched, literals verbatim
split_statements(script: str) -> list[str]           # drops code-free fragments
```

Three declared consumers: `Neo4jClient.run_script`, `drydocs.loaders.base` (the dispatch),
and `schema.supplements.declared_terms` (so a commented-out `MERGE` is not read as a term
the graph must hold). Tests use `strip_comments` so negative assertions read CODE, never
prose — the J66 rule.

**The loader dispatch**, in `drydocs/loaders/base.py`:

```python
if _code_semicolons(cypher) > 1:
    self.client.run_script(cypher, params=params)   # multi-statement
else:
    self.client.run(cypher, **params)               # single UNWIND template, faster
```

Counting **code** semicolons is the point: an audit-envelope comment in a folders template
once routed a single-statement load to `runMany`, which sheared it mid-comment and broke
every folders load on stock APOC.

**APOC's entire live surface here is two procedures.** `apoc.text.join` (three call sites,
all in `drydocs/loaders/cypher/vendor_docs.cypher`, building a section identity key from a
TOC ancestry path) and `apoc.version()` (the installation probe). That is all.

---

## 4. The client — `drydocs_core.neo4j_client.Neo4jClient`

```python
Neo4jClient(uri: str, user: str, password: str,
            database: str | None = None,
            bounds: Neo4jDriverBounds | None = None)
```

**Always use it as a context manager** — `__exit__` is the only teardown; there is no
`close()`. `password` is a plain `str`, so a caller holding a `SecretStr` calls
`.get_secret_value()` itself.

**Do not construct it directly in CLI code.** The factory is `drydocs/cli.py::_client`,
which loads settings, refuses an empty password with exit 2, and applies the configured
database. The six S8 command modules each define a thin `_client` that does a
**function-local** `from drydocs import cli as _root` — a module-scope root import is an
import cycle and `tests/unit/test_cli_import_order.py` fails the module by name.

| Method | Transaction | Returns |
|---|---|---|
| `run(cypher, params=None, **kwargs)` | **WRITE** | `list[dict]` |
| `read(cypher, params=None, **kwargs)` | READ | `list[dict]` |
| `run_with_diagnostics(cypher, params=None, *, write=True)` | either | `(rows, notifications)` |
| `run_script(script, params=None)` | auto-commit, per statement | `None` |
| `execute_file(path)` | auto-commit, per statement | `None` |
| `connection_info()` | — | `{uri, user, database}`, no password |
| `server_version()` | READ | `str`, `"unknown"` if no rows |
| `constraint_names()` | READ | `frozenset[str]` |
| `constraints_detail()` | READ | `tuple[dict, ...]`, ordered by name |
| `apoc_available()` | READ | **`CheckOutcome`**, see below |

**`run()` is the WRITE path — this is the thing to get right.** Use `read()` for anything
that only reads: `run()` demands write access a least-privilege credential will not have,
and pins the query to the leader in a clustered topology. `run()` stays write-by-default
deliberately — it has some forty call sites, most of them writes, and flipping the default
would silently convert them. Migrating the read-shaped callers is an open action item, not
a thing to do opportunistically.

Bind values may go in `params`, in `**kwargs`, or both; **kwargs win on collision**.
`run_with_diagnostics` takes binds through `params` only, because any option keyword would
collide with a bind named after it.

**`apoc_available()` returns a `CheckOutcome`, not a bool, and `bool()` on it RAISES**
(ADR 0021). Three states:

- **CHECKED_CLEAN** — the call succeeded.
- **FINDINGS** — the server answered `ProcedureNotFound`. **The only state in which
  "install APOC" is correct advice.**
- **NOT_CHECKED** — auth failure, unreachable, or anything else, with a reason of forty
  characters or more.

Ask by name: `outcome.is_clean`, `outcome.is_not_checked`. `if not client.apoc_available():`
will not compile past the type — deliberately, because that line used to collapse four
worlds into one `False` and told people whose database was merely stopped to install a
plugin.

**Four declared waits** (CORE13), read from `config/dev-environment.yaml` `neo4j.driver`,
falling back per key to `DRIVER_BOUND_DEFAULTS`:

| Bound | Seconds |
|---|---|
| `connection_timeout` | 15.0 |
| `connection_acquisition_timeout` | 30.0 |
| `max_transaction_retry_time` | 30.0 |
| `transaction_timeout` | 120.0 |

Before them, an unreachable server took **102.9 seconds** to produce a verdict; now it is
under five. The transaction ceiling reaches a MANAGED transaction through
`neo4j.unit_of_work(timeout=...)` — measured, that is the only way in driver 5.28, since
`execute_read`/`execute_write` take no timeout argument.

**The fall-back is deliberate, not sloppiness:** `config/dev-environment.yaml` is
canonical-company, so a port does not carry the producer's copy. A loader that raised on
the absent block would turn an optional config addition into a broken tree on the far side
of a port. **A consumer tree needs the `neo4j.driver` block added by hand or it runs on
the defaults.**

`liveness_check_timeout=0` — revalidate always, pay a round trip, never serve a corpse.
Justified by how this client is used: one context manager per CLI verb or loader run,
where a stale first query costs more than the check.

---

## 5. Schema and constraints

- **`drydocs_core/schema/constraints.cypher`** — the constraint set applied by
  `drydocs bootstrap`. The one DDL shape is
  `CREATE CONSTRAINT <name> IF NOT EXISTS FOR (n:L) REQUIRE …`, and an **anonymous
  declaration is refused by regex** in `drydocs_core/schema/constraints.py`.
- **`drydocs_core/schema/schema_graph.cypher`** — `ddschema` only; one constraint.
- **Supplements** are MERGE-only term seeders and carry **zero constraints**. The chain is
  declared as data in `drydocs_core/schema/supplements.py` (`SUPPLEMENTS`), with an
  explicitly empty `CHAIN_EXCLUSIONS` and a guard that fails on any supplement-shaped file
  not in the chain. Their post-apply assertion is on declared `:OntologyTerm` IRIs.
- **A same-name re-declare succeeds and does nothing.** To change a constraint, DROP it
  first, then create.
- **The D8 bootstrap guard**: after applying, bootstrap compares declared names against
  live `SHOW CONSTRAINTS` and refuses with the count if any are absent — because
  `execute_file` raising is not enough when the failure mode is a silent no-op.

**Provisioning** is `drydocs_core/schema/provisioning/provision.ps1`.
`01_databases.cypher` runs against `system`. Note two things the directory records:
`02_proxy_constraints.cypher` is a **tombstone** (retired at G31; the keys moved to
`constraints.cypher`, the file did not retire them), and the federated smoke script was
**deleted 2026-08-19** — it read across `ddall` and the fold left it nothing to federate.
The equivalent check is `SHOW DATABASES` listing `drydocs` and `ddschema` online.

`cypher-shell` lives **inside the container**, not on the host PATH; `provision.ps1`
detects that and falls back to `docker cp` + `docker exec`, announcing which transport it
took.

---

## 6. Failure modes this project has already paid for

**A loader ran, reported OK, and the graph is empty.**
`NEO4J_DATABASE` was unset, so writes landed in the Enterprise home database `neo4j`,
which is not in the topology — the load succeeds and no query surface ever looks there.
Set it to a topology database, normally `drydocs`, and re-run. `connection_info()` renders
an unset database as the literal `(home)`, which is the tell. The same defect exists one
layer up in the console, where a fresh clone with no local env file runs correct Cypher
against the wrong database and gets zero rows.

**A query naming a mistyped label returned `[]` with no signal.**
Empty-because-nothing-matched and empty-because-the-label-does-not-exist were the same
value, because the result summary was discarded. The summary is now consumed on every path
(including per-statement inside `run_script`), logged at the driver's own severity, and
retained on `last_notifications` — `[]` means a clean run, never a missing field.

**`Constraints applied.` with zero constraints.** The silent-DDL-no-op class. See the D8
guard in §5.

**`APOC required.` on a database that was merely stopped.** The old probe collapsed four
worlds into one `False`. See `apoc_available()` in §4.

**`drydocs bootstrap` refused with "APOC required" for weeks while APOC looked configured.**
`NEO4J_PLUGINS=[apoc]` asks the entrypoint to DOWNLOAD each plugin at startup; when the
download cannot happen **the container starts anyway and the plugin is simply absent** —
it fails OPEN, so nothing surfaces it until a loader refuses. The fix: plugins are a
mounted named volume populated from the image itself, where both jars already ship and are
version-matched to the server.

**A hang with nothing to read and nothing to cancel.** 102.9 seconds. See the four bounds
in §4.

**`SessionExpired` on a query that never reached the database.** A pooled connection went
stale while idle — container restart, NAT drop, idle socket close. `liveness_check_timeout=0`.

**`Neo.ClientError.Database.DatabaseNotFound`.** Provisioning is a prerequisite, not a
startup step: nothing in the startup sequence creates a database, every verb opens a
session against one that must already exist. Run `provision.ps1`.

**Connection refused though the container is up.** The container was started without `-p`
publishing, or Docker remapped the host ports. **Trust `docker port <container>` over any
template value** — an earlier container landed on non-default ports and cost a session.
The Browser is the 7474-mapped port; `NEO4J_URI` takes the 7687-mapped one. Browsing to
the Bolt port returns raw JSON, which is the tell.

**A graph outage that presented as an application bug.** The API answered 500; the console
treats only 502/503/504 as "down". One handler over `neo4j.exceptions.DriverError` now
answers 503 with the class name only, never the message, so the URI stays off the page.
The line is `DriverError` and **not** `Neo4jError` on purpose: a `DriverError` is the
driver failing to get an answer at all; a `Neo4jError` is the server answering with an
error, and for a query this service wrote that is our bug — calling it "service down"
would hide a real defect behind an outage message.

---

## 7. The CLI surface

55 verbs are registered on `drydocs.cli.app`, flat — there are no sub-command groups.
**Enumerate them from the importable object, never from `--help`** (J37), and note the
`name or callback.__name__` form, because some commands carry `name=None` and a naive sort
raises `TypeError`:

```bash
poetry run python -c "from drydocs.cli import app; print(*sorted(i.name or i.callback.__name__.replace('_','-') for i in app.registered_commands), sep='\n')"
```

The Neo4j-touching core: `bootstrap` (constraints + ontology seed, APOC-gated),
`bootstrap-schema-graph` (`ddschema`), `check` (connection + APOC probe, renders the
outcome's reason), `apply-supplements` and the five per-supplement `apply-*` verbs,
`m1-verify` / `m3-verify` (need a LIVE server plus APOC — the unit suite is the no-database
check), and the `load-*` family.

---

## 8. What this skill will not do

- **Substitute for the vendor plugin.** Under Claude Code, use `neo4j-skills:` for
  general Cypher, modeling, import, GraphRAG, vector and tuning practice. This file is
  about *this* graph.
- **Assert anything about a live database.** Every fact here is read from the tree. A
  live claim names its venue (J18) — the machine, container and database it ran on.
- **Carry credentials, hosts or data.** Connection coordinates live in `.env` (gitignored)
  and `config/dev-environment.yaml`; instance-specific detail belongs in `internal/`.
