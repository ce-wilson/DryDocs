# Catalog substrate review — what to take from the data-catalog and lineage products

<!-- anchor: front-matter -->
- **Scope:** an evaluation, not a runbook and not a decision record. It is the SECOND pass over
  two questions the first pass left half-answered: how a console bootstraps its own login, and
  how a declared data source binds to a real location on a real machine. Each adoption feeds an
  existing backlog item; nothing here mints work on its own.
- **Status:** DESCRIPTIVE — **Rev 1, 2026-08-28.**
- **Classification:** External reasoning over Internal-Public context (every product reviewed is
  public; nothing here carries company values, credentials or internal URLs)
- **Reviewed in depth (open source):** DataHub (Apache-2.0), OpenMetadata (Apache-2.0),
  Amundsen (Apache-2.0), OpenLineage / Marquez (Apache-2.0)
- **Reviewed for concepts only (commercial, public documentation):** Microsoft Purview.
  Collibra, Alation and Atlan were checked and dropped as duplicates — see
  [Products reviewed](#products-reviewed).
- **Companion:** `docs/design/web-scaffolding-review.md` (the FIRST pass), ADR 0009
  (configuration substrate), `config/source-registry.yaml`, `drydocs_core/landing_zones.py`

<!-- anchor: why-now -->
## Why a second pass

The first pass read two Python application scaffolds, `full-stack-fastapi-template` and
`ss-python`. That was the right corpus for the question it was asked — how a FastAPI console
does authentication — and it produced O69 through O72 plus J52. O69 and O73 shipped, O74
followed, and the console now has real credentials, a real session and six personas.

It was the wrong corpus for the second question. A SaaS application template has exactly one
data source, its own database, configured by one `DATABASE_URL`. It has nothing to say about a
system that declares thirty datasets across fifteen systems and has to answer, per machine,
"where does this one actually live right now." DryDocs has that problem today: the registry
names WHAT each source is, and the answer to WHERE is spread across seven independent
environment-variable reads in seven modules, each with its own precedence chain and its own
silent default.

The products that solved that problem are the data catalogs and the lineage tools. They are
DryDocs's actual peers: each one holds a registry of sources it does not own, and each one had
to invent a way to bind a registry row to a connection without putting secrets in the registry.
This pass reads what they built.

<!-- anchor: what-drydocs-already-has -->
## What DryDocs already has

Stated first, because two of the findings below are "this is already right, stop here."

**The source registry is mature.** `config/source-registry.yaml` (schema v2, gate signed
2026-07-31) carries 15 systems and 30 datasets on a two-level split: a system row is the thing
we connect to, a dataset row is the thing a loader reads. Identifiers follow a grammar,
`{origin}@{db}.{schema}.{table}` for replicas and `{system}:{artifact}` for born-here data, and
the URN is derived from the row rather than hand-maintained. Retired ids are refused at parse
time.

**Half the location problem is solved, and solved well.** Fifteen of the thirty datasets carry
`acquisition.mode: manual` with a `drop_dir` and a `drop_dir_base`.
`drydocs_core/landing_zones.py` resolves those to real paths, `drydocs landing-zones` reports
what is actually in each one, and `tests/unit/test_landing_zones.py` enforces the rule that a
zone is either outside the working tree or made of tracked files. That module exists because a
`git clean -fd` destroyed hand-carried extracts, and the control it added is the right one.

**The console credential path is sound.** `drydocs_api/credentials.py` hashes with scrypt at
OWASP parameters, stores the parameters beside each hash so the cost can be raised without
invalidating what exists, pays a dummy derivation for unknown identities so response time does
not leak which accounts are real, and reloads on file change (O73) by comparing a stat stamp
rather than polling. The write lives in `scripts/set_console_credential.py`, outside the API
package, enforced by a guard that forbids filesystem writes inside `drydocs_api` — an endpoint
that can rewrite the credential file is an endpoint that can grant itself an account.

**What has no owner.** The other fifteen datasets, every one of them `acquisition.mode:
automated`, declare no binding at all. Their system rows carry `locator.service: ~` with a
comment saying the real value lives in `internal-local/`. Nothing resolves that comment.
Alongside them sit seven environment variables read directly in code, none of them declared
anywhere: `DRYDOCS_DATA_ROOT`, `DRYDOCS_LOGDIR` (with a legacy `SPIDERP_LOGDIR` alias),
`DRYDOCS_CONSOLE_CREDENTIALS`, `DRYDOCS_MAPPING_DB`, `DRYDOCS_MAPPING_READ`, the Control-M
adapter's config variable, and the `NEO4J_*` set.

<!-- anchor: products-reviewed -->
## Products reviewed

| Product | License | Read | What it contributes here |
|---|---|---|---|
| **DataHub** | Apache-2.0 | in depth | The three-part URN and the `platform_instance` retrofit; `${VAR}` expansion in recipes; the `user.props` default-credential lesson |
| **OpenMetadata** | Apache-2.0 | in depth | The secrets-manager abstraction and its DERIVED secret path |
| **Amundsen** | Apache-2.0 | in depth | Scoped configuration keys with declared fallbacks |
| **OpenLineage / Marquez** | Apache-2.0 | in depth | The namespace-and-name naming specification |
| **Microsoft Purview** | commercial | concepts only | Credential as a first-class object, separate from the source it authenticates |
| **Collibra, Alation, Atlan** | commercial | dropped | Each publishes the same connection-plus-vaulted-credential shape Purview and OpenMetadata already show. No distinct contribution; not read further. |

<!-- anchor: binding-findings -->
## Findings: binding a source to a place

<!-- anchor: b1 -->
### B1. The manual half is declared and checked; the automated half is neither

Fifteen manual rows resolve through the registry. Fifteen automated rows resolve through
nothing. That asymmetry is invisible at the surface, because `drydocs landing-zones --check`
reports a clean run over the rows it knows about and says nothing about the rows it does not.

This is the same defect G109 clause (a) already names for the six code zones with no registry
row: a check that silently covers half its subject reads as coverage. The finding here is that
the gap is larger than the six zones. It is every automated source as well, and the fix is the
same declaration.

**What the peers do.** None of the four open-source products has an undeclared source. In
DataHub every source is a recipe with a typed `source.config` block. In OpenMetadata every
source is a `ServiceConnection` validated against a published JSON schema. In Amundsen every
extractor reads its connection from a configuration tree keyed by the extractor's own scope. In
all three the declaration is mandatory and total, and the reason is the same one that applies
here: a source you cannot enumerate is a source you cannot audit, back up, or move.

<!-- anchor: b2 -->
### B2. The URN is the shape DataHub had to retrofit, and the placeholder is the missing axis

DryDocs derives `urn:drydocs:dataset:({carrier-or-origin},{artifact},prod)` — a three-part key
of platform, name, environment, with the environment pinned to `prod`.

DataHub's original dataset URN was `urn:li:dataset:(urn:li:dataPlatform:<platform>,<name>,ENV)`.
The same three parts. Their documentation states the failure plainly: that key cannot represent
two deployments of the same platform in one environment, so an organization with two Redshift
instances in production collapses both into one identifier. Fixing it required adding a
`dataPlatformInstance` aspect and a `platform_instance` recipe parameter, which changes how URNs
are generated across every source — a retrofit that touches everything already ingested.

DryDocs is standing where DataHub stood before that change, and it is not hypothetical. The
committed dataset ids carry `[db]` as a redaction placeholder, and `[db]` is precisely the
instance coordinate: the registry comment says the real value is a connection coordinate that
belongs in the internal twin. Four production Control-M data centers sit behind those ids. Two
machines hold independent graphs. The instance axis exists in the estate and is currently
spelled as a hole in the identifier.

**The recommendation is not to mint the axis now.** It is to record, in ADR 0014, that the
three-part key has a known ceiling and that the binding table introduced below is where an
instance coordinate lands when it is needed — so the eventual answer is a configuration change
rather than an id migration. Naming the ceiling costs a paragraph; discovering it after the
graph is loaded costs what it cost DataHub.

<!-- anchor: b3 -->
### B3. OpenLineage already names the split the binding table should use

OpenLineage's naming specification assigns every dataset two parts: a **namespace** derived from
the datasource, and a **name** identifying the object inside it. The formats are explicit —
`oracle://{host}:{port}` with name `{serviceName}.{schema}.{table}`; `postgres://{host}:{port}`
with `{database}.{schema}.{table}`; `s3://{bucket}` with `{object key}`; `file` with `{path}`;
`kafka://{bootstrap server host}:{port}` with `{topic}`.

The split is the useful part. The namespace is the *connection* — the thing that varies by
machine, carries the host, and can hold a secret. The name is the *object* — the thing that is
stable across every deployment and safe to commit.

DryDocs's grammar is already isomorphic to this. `{origin}@{db}.{schema}.{table}` puts the
origin where OpenLineage puts the namespace and the qualified object where OpenLineage puts the
name. That means the binding table does not need a row per dataset. **It needs a row per
origin**, and every dataset under that origin inherits it. Fifteen automated datasets reduce to
roughly six origins.

The same shape covers the filesystem sources without a second mechanism: a landing zone is a
namespace of `file` with a root, exactly the way OpenLineage models a local path. That is what
`drop_dir_base` already is, one level less general.

<!-- anchor: b4 -->
### B4. Write the resolution precedence once, and reference environment variables rather than reading them

Seven modules each implement their own version of "explicit argument, then environment variable,
then default." They do not agree. `resolve_data_root()` treats an empty string as unset and
falls back silently. `resolve_log_dir()` walks two variables before its default.
`credentials_path()` takes any non-empty override verbatim. `MappingStore.__init__` imports `os`
inside the constructor to read one variable. There is no place to look up which variables exist,
and `.env.example` documents neither of the two roots, which G109 clause (d) already records.

**Amundsen's answer** is a configuration tree where every key is namespaced by the component
that reads it — `{extractor.get_scope()}.{KEY}` — composed with `.with_fallback(defaults)`. One
mechanism supplies the precedence; a component declares its keys and never re-implements the
lookup.

**DataHub's answer** to the secrets half is to let the committed configuration *reference*
environment variables rather than read them: a recipe writes `password: ${MSSQL_PASSWORD}` and
the loader expands it, so the file is committable and the secret never is. DataHub also ships a
`__DATAHUB_TO_FILE_` directive for values that must land on disk as a file.

Together those give the shape for DryDocs: **the binding table is committed YAML that references
environment variables by name and never contains a value that is secret.** One expansion
function, one error message when a referenced variable is unset, one place that enumerates every
variable the system reads. That is also what makes G81 clause (d) — an unset root must fail
rather than silently relocate — implementable in one place instead of seven.

<!-- anchor: b5 -->
### B5. The credential belongs beside the binding, and there are two published ways to put it there

`locator.service: ~` with a comment is the current answer for connection credentials. Both
patterns worth knowing are already public.

**OpenMetadata derives the secret's location from the row.** With a managed secrets manager, a
MySQL service named `mysql-test` stores its password at
`/openmetadata/database/mysql-test/password` — the path is a function of service type and
service name, so it cannot drift from the registration. A non-managed mode leaves the field as a
`secret:{secret_id}` reference the operator writes by hand. Backends are AWS Secrets Manager and
AWS Systems Manager Parameter Store, behind one interface.

**Purview makes the credential a first-class object.** A credential is created and managed
separately from source registration, backed by Key Vault, and referenced by name from any scan
that needs it — so one credential serves many sources and rotating it is one operation.

The difference matters for DryDocs. Derived paths (OpenMetadata) suit the case where each source
has its own secret; named objects (Purview) suit the case where one Oracle account reads eight
`psgmgr` views, which is the actual situation here. **The recommendation is the Purview shape**:
a small set of named connection profiles, each referenced by several registry rows, each
resolving its secret through an environment-variable reference per B4. The registry keeps naming
the source; a profile names the connection; neither holds a value.

This also closes a structural gap from the other direction: the existing credential file is
machine-local, gitignored, and has no committed source to rebuild from — the module says so and
is right to. A named-profile table gives that file a declared peer for connection secrets without
weakening the rule that keeps it out of `var/`.

<!-- anchor: login-findings -->
## Findings: the login tools

<!-- anchor: l1 -->
### L1. The fresh-clone default is already stronger than DataHub's, and should be recorded as deliberate

DataHub ships a working `datahub:datahub` account in a `user.props` file, and its own
documentation carries the warning that follows from that choice: deleting the user in the UI
does **not** disable it, and the file must be changed before production. Every deployment
inherits a credential it did not choose.

DryDocs ships nothing. A fresh clone has no credential file, therefore no accounts, therefore
every login is refused, and the refusal names the bootstrap script. That is the better default
and it is already implemented. No change — the finding is that it is worth stating as a decision
in ADR 0014 rather than leaving it as behavior, because it is the kind of property a later
convenience commit quietly removes.

<!-- anchor: l2 -->
### L2. `--generate` recreates a small piece of the DataHub problem, and the store cannot see it

`admin_demo_login.py --generate` invents a secret and prints it once. The trade is defensible and
the docstring argues it correctly for a synthetic account on localhost. What is missing is that
nothing records it happened. A generated demo secret and a deliberately chosen operator secret
are indistinguishable in the store, so `--list` and `--status` cannot say "this account has been
carrying a printed-to-terminal secret since three weeks ago; rotate it before the demo."

The fix is small and the format already supports it: the credential entry gains non-secret
metadata, `origin: generated|prompted` and `set_at`, and `FORMAT_VERSION` goes to 2. Both
reporting surfaces then say something true that neither can say now. This is the audit that
DataHub's documentation is compensating for in prose.

<!-- anchor: l3 -->
### L3. Removing or rotating a credential does not end that account's live sessions

This is the one defect in the login path.

`InMemorySessionStore.revoke(token)` is token-scoped, driven by logout. `resolve(token)` checks
the store for the token and checks its expiry, and never consults the credential store again.
`ReloadingCredentialStore` refreshes on file change, but only `handlers.login` reads it.

So the sequence is: `morpheus` signs in and receives an eight-hour session; the operator runs
`set_console_credential.py --remove morpheus`, or rotates the secret because it leaked; the
credential file changes; the API notices within one login; and the already-issued token keeps
working, at admin role, for the remainder of its eight hours. The operator has every reason to
believe access was withdrawn.

Both peers tie session validity to the actor rather than to the token alone — it is the reason
DataHub's documentation has to explain that deleting a user in the UI leaves the file-based
account working, and the reason OpenMetadata forces a reset rather than trusting removal.

The fix is proportionate to the store: `revoke_identity(persona_id)` on the session store. The
script cannot call it — it does not share a process with the API, and giving it one would
violate the rule that keeps writes out of `drydocs_api`. The workable shape is the one O73
already established: `resolve` compares the session's `persona_id` against the credential
store's current identities, so a removed account's token stops resolving on the next request
through the same stat-based reload that already runs. Rotation is the harder case, because a
rotated secret leaves the identity present, and it can be deferred with a stated reason;
removal is the one an operator will actually rely on.

<!-- anchor: l4 -->
### L4. The credential file is itself an undeclared environment-to-path binding

`DRYDOCS_CONSOLE_CREDENTIALS` is one of the seven variables in B4, and
`internal-local/console-credentials.json` is a path the system both reads and writes. It is
therefore in scope for G81's declaration, and it is the sharpest test of that item's mode axis:
it is **write** for one script run by a person, **read** for the API, and it must never be
`scratch`. If the declaration G81 lands cannot express that, it is not expressive enough. The
credentials module already argues this boundary in prose; the item is the chance to make it
mechanical.

<!-- anchor: what-changes -->
## What this changes for the existing items

Proposals, not applied. Each names the item that owns it.

| Item | Clause | Proposed amendment |
|---|---|---|
| **G104** (ADR 0014) | (7) data-zone map | Record the three-part-key ceiling from B2 and name the binding table as where an instance coordinate lands later. Record L1 as a decision rather than behavior. |
| **G104** | new | Adopt B3's per-origin binding rather than per-dataset, and B4's reference-not-read rule for environment variables. Name Amundsen, DataHub, OpenMetadata and Purview as the surveyed alternatives, the way the item already requires the sister project's gotcha list to be recorded as rejected alternatives. |
| **G81** | (b) declare every path | Extend the declaration from the three named families to the full origin set, so the fifteen automated datasets are covered and not only the filesystem ones. |
| **G81** | (d) no silent default root | Implement as one expansion function per B4, not per module. Add L4 as the read-and-write test case. |
| **G109** | (a) six undeclared zones | The gap is larger than six: every automated dataset is undeclared too. Either widen the clause or record why the automated half is out of scope for this item. |
| **O epic** | new | L3 (session revocation on credential removal) and L2 (credential provenance metadata) have no item. Raised to `IDEAS.md`. |

<!-- anchor: not-taken -->
## What we deliberately do not take

- **A metastore or a securable-object namespace.** Unity Catalog's shape was already reviewed
  and answers a different question — what things mean, not where they are.
- **A secrets-manager plugin interface.** OpenMetadata supports AWS Secrets Manager and
  Parameter Store behind one abstraction. DryDocs has one machine and one operator; an
  abstraction over one implementation is scaffolding for a scenario that does not exist. The
  environment-variable reference in B4 is the whole requirement.
- **pyhocon.** Amundsen's scoped-key idea is worth taking; its HOCON dependency is not. The repo
  already uses pydantic-settings for this shape, which G104 clause (1) names.
- **A `platform_instance` retrofit now.** B2 recommends recording the ceiling, not minting the
  axis. Adding an instance segment to ids before anything needs it would be an id migration
  bought with no current benefit.
- **Marquez's namespace-per-source at the API layer.** DryDocs has no lineage service taking
  runtime events; the naming specification is useful as a grammar, and the server around it is
  not.
- **DataHub's `__DATAHUB_TO_FILE_` directive.** It solves writing a credential file from a
  configuration value. Here that path runs the other way — a person at a terminal writes the
  file — and the rule that keeps writes out of `drydocs_api` says it should stay that way.

<!-- anchor: sources -->
## Sources

Public documentation, cited rather than reproduced.

- OpenLineage naming conventions — <https://openlineage.io/docs/spec/naming/>
- DataHub platform instances — <https://docs.datahub.com/docs/platform-instances>
- DataHub recipes and environment variables — <https://docs.datahub.com/docs/metadata-ingestion/recipe_overview>
- DataHub changing default credentials — <https://docs.datahub.com/docs/authentication/changing-default-credentials>
- DataHub JaaS authentication — <https://docs.datahub.com/docs/authentication/guides/jaas>
- OpenMetadata secrets manager — <https://docs.open-metadata.org/latest/deployment/secrets-manager>
- Amundsen databuilder — <https://github.com/amundsen-io/amundsen/tree/main/databuilder>
- Microsoft Purview scan credentials — <https://learn.microsoft.com/en-us/purview/data-map-data-scan-credentials>
