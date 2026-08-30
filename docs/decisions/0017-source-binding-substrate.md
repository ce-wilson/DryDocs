# ADR 0017 — Source-binding substrate: a declared source binds to a real place through one per-origin table

```yaml
status: PROPOSED          # the drafting session never accepts its own ADR — acceptance is the user's
date: 2026-08-29
amended: 2026-08-30       # Rev 2 — the source passes landed; see "What Rev 2 changed" below
authored_by: G124 (desktop)
deciders: [chad.wilson]
layer: 0-configuration
relates_to:
  - 0009-configuration-substrate.md            # git text is the source of truth — the scope clause this reads
  - 0014-runtime-substrate.md                  # the per-machine exception, and the map-vs-root model reused here
  - 0012-data-named-load-surface.md            # acquisition as a source-entry axis
  - docs/design/catalog-substrate-review.md    # the survey this rules on (Rev 1, 2026-08-28)
  - docs/design/openlineage-substrate-review.md  # third pass — reads the OpenLineage source (Rev 1, 2026-08-30)
  - docs/design/datahub-substrate-review.md      # fourth/fifth pass — reads the DataHub source (Rev 2, 2026-08-30)
  - config/source-registry.yaml                # 15 systems / 30 datasets; the WHAT
  - config/data-zones.yaml                     # G81's declared zones; the mode axis
  - drydocs_core/landing_zones.py              # resolves the manual half today
  - drydocs_api/credentials.py                 # the console credential carrier (O69/O73)
executed_by: G125 (the binding table and the one expansion function)
```

> **Nothing in this record changes code.** G125 implements it and `depends_on` this ADR, so
> nothing implements an unratified ruling — the G104 → G105–G109 shape exactly.

## What Rev 2 changed, and why the ADR is only now ready to rule on

Rev 1 was written from a survey. Three later passes read the cited products' **source** instead,
and one citation did not survive: clause 1 described a DataHub fix that DataHub did not make.
Rev 2 folds every finding into the clauses themselves, so the record can be accepted or rejected
whole rather than read alongside three companions.

| Clause | Rev 1 said | Rev 2 says | Evidence |
|---|---|---|---|
| 1 | the instance axis lands in the binding table, so the fix is a configuration change | the migration is **deferred, not avoided**, and the real ceiling is the derived URN | `datahub-substrate-review.md` findings 1–2 |
| 2 | bind per **origin** | bind per **connection carrier**; the reader is a second, finer grain | `openlineage-substrate-review.md` bottom line |
| 3 | `${VAR}`, one expansion function | plus: refuses defaults, states precedence, and registers the secret for masking | `datahub-substrate-review.md` finding 3, finding 7 |
| 4 | the Purview shape | plus: `dataHubConnection` as the shipped precedent, and the reference direction declared | finding 4 |
| 5 | the demo account | the `ENCRYPTION_KEY` fallback — a sharper instance of the same class | finding 5 |
| 6 | — | **new**: the registered-ids rule recorded as a held property, with its guard | finding 6, finding 7 |
| 7 | — | **new**: the editor-first posture recorded as a design property | finding 7 |

Two things are deliberately still open and named as such: the **grammar** work (un-redacting `[db]`
and `[schema]`, which must move with `SourceEntry.urn`) rides its own SME gate, and **path
multiplicity** (Idea-222) rides N10's.

**One question Rev 2 CREATED, and it is the user's before this is accepted.** Clause 4 as amended
requires the registry row to **name its profile** — which is a new field on
`config/source-registry.yaml`. The drafted, unsigned gate `registry-wiring-readiness` (N10) carries
clause D2: *"THE SCHEMA CHANGES ONLY WHEN THIS PAGE SIGNS. `config/schemas/source-registry.schema.json`,
the registry file, and `require_confirmed()` are untouched until then."* Read literally that fences
this. Read in context it fences the `wired`/`ready` split D2 is about — and **practice supports the
narrow reading**: N12 added the whole `acquisition` block to the same registry and the same schema
file (`a10b0191`) while that sentence stood, and the schema has been modified twice more since.
So either D2 is scoped to its own subject and clause 4's field proceeds, or it is a blanket freeze
and that one field waits for N10's page to sign. Ruling it here is what stops it being
re-litigated per row, the way "established public vocabulary" was.

## Why this is a new ADR and not an edit to 0014

The catalog-substrate review asks for two of these rulings to land **in ADR 0014**. That
request was written against a branch history that did not contain 0014's acceptance
(`b58f3869` does not have `413b9186` as an ancestor — verified, not inferred), so the review
had every reason to believe 0014 was still Proposed. It was accepted, with four amendments,
on 2026-08-25.

That changes the venue question from a preference to a decision, and it is settled here
first because everything below depends on it.

**The ruling: 0017 stands alone, and 0014 gains a cross-reference rather than an
amendment.** Two arguments, one of substance and one of process.

*Substance.* 0014's subject is the **runtime substrate** — log directory, log level,
retention, data root. Its own governing line is that a value belongs there "if and only if
it is a per-machine operational fact — a path, a verbosity, a retention window." A binding
from a declared source to a real connection is not that. It is a **domain** fact with an
owner: which origins exist, which datasets hang off each, and which named profile
authenticates them are things an SME would recognize and argue about. Only the *values*
behind them are per-machine. Filing that under an ADR about verbosity and log rotation would
make 0014's own scope line the first casualty.

*Process.* An accepted ADR is a ruling the user made. Amending one is a new decision that
goes back to them either way, so the only question is whether the amendment arrives as
edits scattered through a ruled document or as a record that can be read, argued with, and
rejected whole. The second is reviewable; the first is not.

**Where this could go the other way**, named rather than buried: if the user reads the
runtime substrate as "everything about where things are on this machine," then the binding
table is 0014's subject after all and this becomes an amendment — 0014 gaining a clause 8
and this file being withdrawn. The `[db]` placeholder in (1) is the argument against, since
it is an identity coordinate rather than a location, but it is a judgement call and it is
the user's.

## Context

**Half the location problem is solved, and solved well.** Fifteen of the thirty datasets in
`config/source-registry.yaml` carry `acquisition.mode: manual` with a `drop_dir` and a
`drop_dir_base`. `drydocs_core/landing_zones.py` resolves them, `drydocs landing-zones`
reports what is in each, and a guard enforces that a zone is either outside the working tree
or made of tracked files. That module exists because a `git clean -fd` destroyed
hand-carried extracts; the control it added is the right one, and G109 widened its read
surface to cover `config/data-zones.yaml` too.

**The other half has no owner.** The remaining fifteen datasets are all
`acquisition.mode: automated` and declare no binding at all. Their system rows carry
`locator.service: ~` with a comment saying the real value lives in `internal-local/`, and
nothing resolves a comment. Alongside them sit seven environment variables read directly in
code and declared nowhere: `DRYDOCS_DATA_ROOT`, `DRYDOCS_LOGDIR` (with a legacy
`SPIDERP_LOGDIR` alias), `DRYDOCS_CONSOLE_CREDENTIALS`, `DRYDOCS_MAPPING_DB`,
`DRYDOCS_MAPPING_READ`, the Control-M adapter's config variable, and the `NEO4J_*` set.

**Why that asymmetry is a defect and not a gap.** `drydocs landing-zones --check` reports a
clean run over the rows it knows about and says nothing about the rows it does not. This is
the same shape G109 already fixed once at a smaller scale, and the finding is worth stating
in the form that makes it actionable: *a check that silently covers half its subject reads
as coverage.* A source nobody can enumerate is a source nobody can audit, back up, or move.

**Evidence the prose is already drifting.** `config/source-registry.yaml` line 201 still
advertises `DRYDOCS_DATA_ROOT (default ~/data/DryDocs)`. G81 removed that default on
2026-08-23; the variable is mandatory and an unset root now fails naming it. The registry
told an operator the opposite of the code for six days, and nothing caught it, because a
`locator:` block is free text no guard reads. That is the whole argument for this ADR in one
line: prose in a locator block is not a declaration.

**The peers.** None of the four open-source catalogs reviewed has an undeclared source. In
DataHub every source is a recipe with a typed `source.config` block; in OpenMetadata every
source is a `ServiceConnection` validated against a published JSON schema; in Amundsen every
extractor reads its connection from a configuration tree keyed by its own scope. The
declaration is mandatory and total in all three, for the reason above.

## Reconciling with ADR 0009 and ADR 0014

ADR 0009 rule 1: *"Source of truth is git text, permanently"*, scoped by its own clause to
anything **an SME gates, a port carries, or a classification test guards**. ADR 0014 carved
out per-machine operational facts as an exception that scope clause already permits.

**This ADR needs no new exception, because it splits along the line 0014 already drew.**
0014's model is `config/data-zones.yaml` and it applies here without modification: the
**map** is committed git text — which zones exist, what mode each has, why — and only the
**root** they hang off is per-machine. The binding table is the same shape one level over.

| Half | Where it lives | Why |
|---|---|---|
| **The table** — which origins exist, which datasets inherit each, which profile authenticates it, which variable holds the secret | **Committed YAML**, ADR 0009 rule 1 | An SME recognizes it, the port carries it (both sides have the same origins), and every row needs a `classification` — it passes all three of 0009's named tests |
| **The values** — host, port, service name, SID, password | **Environment**, ADR 0014's exception | Per-machine operational facts, and secrets besides |

The publish boundary lands on the same line and reinforces it: a host name or SID is
Internal and may never be committed (CLAUDE.md §3), while the *existence* of an origin
called `psgmgr` is already committed and already public in this repo. The split is not a
compromise between the two ADRs — it is the only split that satisfies both.

**Where this could go the other way:** if the user reads a per-origin binding row as itself
a per-machine fact — because the row exists to describe *this* machine's connection — then
the table belongs in the environment too, and 0009 gains a real carve-out rather than
reusing 0014's. The argument against is that the rows are identical on both machines and the
only per-machine part is what the variables resolve to.

## Decision

### 1. The three-part-key ceiling is recorded, and the instance axis is NOT minted

DryDocs derives `urn:drydocs:dataset:({carrier-or-origin},{artifact},prod)` — platform,
name, environment, with environment pinned to `prod`.

DataHub's original dataset URN was the same three parts, and that key cannot represent two
deployments of the same platform in one environment: an organization with two Redshift
instances in production collapses both into one identifier.

**How DataHub actually fixed it, corrected in Rev 2 — this matters, because Rev 1 drew the
wrong conclusion from it.** `platform_instance` is **not** a fourth key component.
`DatasetUrn.createFromUrn` still throws on `key.size() != 3`, and the instance is concatenated
into the URN's `name` (`avro_codegen.py:516`), so **adding a platform instance changes the
dataset's identity**. The aspect that looks like the answer, `DataPlatformInstance`, declares
no relationship at all — it is a search facet. DataHub had a connection-shaped object available
(`dataHubConnection`) and still could not put the instance there, because identity is not
resolvable through configuration: an identifier either distinguishes two things or it does not.

**So the ruling stands and its reason changes. The migration is DEFERRED, not AVOIDED.**
Deferring a migration that buys nothing today is a defensible call on its own terms, and it is
the call made here. What Rev 1 claimed — that the binding table converts the eventual fix into a
configuration change — is not supported by the product it cited, and no longer forms part of the
justification.

**And the ceiling is lower than Rev 1 recorded, in a place it did not look.** Rev 1 pointed at
`[db]` in the committed id string. But `[db]` is a redaction inside a string no code keys on.
The identifier that reaches loaders and the graph is the derived URN, and
`SourceEntry.urn` builds it as `({carrier},{artifact},prod)` — dropping the database **and the
schema**. Measured at `main`: 30 dataset rows, 30 distinct URNs, so nothing is broken today; but
the key is (carrier, bare table name, `prod`), and `psgmgr` already carries three origins while
`snowflake` carries two. DataHub's URN name was always the fully qualified native name, so
DataHub was **one** axis short. DryDocs is **three**: instance, database, schema.

**The consequence is a sequencing rule, and it is the operative part of this clause.** The
pending grammar work — un-redacting `[db]` and `[schema]` in committed ids — does **nothing** for
the URN unless `SourceEntry.urn` changes in the same commit. A registry whose ids are precise and
whose URNs are not is the worse of the two states, because the imprecise identifier is the one
that gets written into the graph. That work rides its own SME gate; this ADR only rules that the
two halves move together.

**The counter-case, named rather than buried.** OpenLineage puts the instance *in* the identifier
by construction — its namespace is `oracle://{host}:{port}`, so the host is part of dataset
identity. That is the opposite choice and it has a cost this repo cannot pay: it makes the
identifier a connection coordinate, which the publish boundary forbids committing. The split
adopted in (2) is the reason DryDocs can keep a committable identifier at all.

Naming the ceiling costs a paragraph. Discovering it after the graph is loaded costs what it
cost DataHub.

### 2. The binding is per-CONNECTION CARRIER, and the reader is a second, finer grain

OpenLineage's naming specification gives every dataset two parts: a **namespace** derived
from the datasource (`oracle://{host}:{port}`, `s3://{bucket}`, `file`) and a **name**
identifying the object inside it (`{serviceName}.{schema}.{table}`, `{object key}`,
`{path}`).

The split is the useful part. The namespace is the **connection** — it varies by machine,
carries the host, and can hold a secret. The name is the **object** — stable across every
deployment and safe to commit.

**Rev 1 claimed DryDocs's grammar is already isomorphic to that — origin where OpenLineage puts
the namespace — and concluded the table needs a row per origin. Reading the source disproved it,
and the registry is what disproves it.** OpenLineage's namespace is a **connection**. DryDocs's
`origin` is a **provenance label**: who produced the data. Measured at `main`, they are not the
same field and cannot be made one: `origin: controlm` spans **three** systems (`controlm`,
`drydocs-stg`, `psgmgr`), so a per-origin row cannot bind to one connection at all; and
`system: psgmgr` carries **three** origins (`controlm`, `hr`, `seal`), so keying per origin
re-fragments the very connection this clause exists to share.

**The ruling: one row per CONNECTION CARRIER.** That is the level `system` occupies, and the ten
`psgmgr` datasets then share one row, as intended. Two qualifications ride with it, both
measured rather than assumed:

- **`system` is at the right level while carrying the wrong value.** `psgmgr` names a *schema*;
  the database it sits in is `spiderdb`, which the registry names nowhere. So the binding keys on
  the connection carrier, and `system` is a usable proxy only for as long as one schema happens to
  equal one database. A second schema in `spiderdb`, or a `psgmgr` schema in a second database,
  breaks it silently. (`spiderdb` is a name and not a coordinate — the pronounceable head of the
  TNS alias, ruled publishable 2026-08-30 — so nothing about the redaction was buying secrecy.)
- **The connection is not the only binding.** Which *reader* fetches a datapoint is a separate
  choice at a finer grain: `adapter:` is already dataset-grained and already names the read
  mechanism (`oracle` 10, `csv` 4, `json`/`markdown`/`yaml` 1 each, `~` 13). So the binding is two
  things at two grains — **a connection per carrier, a reader per dataset** — and this ADR rules
  only the first. The reader grain, including whether one datapoint may declare several access
  paths and which wins, is Idea-222's and rides N10's gate.

**One mechanism, not two.** The same shape covers the filesystem sources: a landing zone is a
namespace of `file` with a root, which is what `drop_dir_base` already is, one level less
general. This ADR does **not** require G125 to rewrite the manual half — the existing rows
work and rewriting them buys nothing — but it rules that the two are the same shape, so a
future consolidation is a refactor rather than a redesign, and neither half may grow a
concept the other cannot express.

### 3. Committed YAML REFERENCES environment variables; it never holds a value

DataHub's recipes write `password: ${MSSQL_PASSWORD}` and expand at load, so the file is
committable and the secret never is. That is the shape adopted here.

**Two riders added in Rev 2, both read off DataHub's real expander rather than its documentation
summary.**

**(a) The expander substitutes and REFUSES defaults.** DataHub's is bash-style, so
`${VAR:-default}` uses the default when `VAR` is unset or empty. Adopting that verbatim would put
silent-default behavior back at the *syntax* level, where the one expansion function cannot see
it — the committed YAML would carry the fallback, not the code. **G81 clause (d) ruled that an
unset data root must FAIL rather than silently relocate**, and this clause exists partly to make
that rule implementable in one place; a default operator would quietly unmake it. An unset
variable is an error naming the variable and the row that wanted it.

**(b) The expansion function is also where the secret is registered.** DataHub states the design
in its own header: config loaders register secrets during `${VAR}` expansion, pydantic models
register `SecretStr` fields during validation, and a logging filter plus an exception hook mask
them everywhere after. This is what "one expansion function" is *for* — the expander is the only
place that can know a resolved value is secret, so it is where the masking obligation is created,
not merely where the lookup happens.

**And if a second backend ever exists, the enumerable list grows a fourth item: one stated
precedence.** DataHub resolves from three backends and merges them, DataHub > File > Environment.
DryDocs has one backend today, so this is a fence rather than a feature: a second one without a
stated precedence stops the list from telling an operator which value is live.

**One expansion function, one error, one enumerable list.** Today seven modules each
implement their own version of "explicit argument, then environment variable, then default",
and they disagree: `resolve_data_root()` treats an empty string as unset,
`resolve_log_dir()` walks two variables before its default, `credentials_path()` takes any
non-empty override verbatim, and `MappingStore.__init__` imports `os` inside the constructor
to read one variable. There is no place to look up which variables exist.

This is also what makes G81 clause (d) — an unset root must FAIL rather than silently
relocate — implementable in one place instead of seven. G81's behavior does not change; its
implementation stops being local to one resolver.

Amundsen's contribution is the *scoping*: keys namespaced by the component that reads them,
composed with declared fallbacks, so a component declares its keys and never re-implements
the lookup. The idea is adopted; the HOCON dependency is not (see rejected alternatives).

### 4. The credential is a named connection PROFILE, referenced by many rows

Two published patterns solve this, and they suit different situations.

OpenMetadata **derives** the secret's location from the row: a MySQL service named
`mysql-test` stores its password at `/openmetadata/database/mysql-test/password`, so the path
cannot drift from the registration. Purview makes the credential a **first-class object**,
created and managed separately, referenced by name from any scan that needs it, so one
credential serves many sources and rotating it is one operation.

**The Purview shape is the ruling, on the facts here:** one Oracle account reads eight
`psgmgr` views. Derived paths suit one-secret-per-source; named objects suit
one-secret-per-many-sources, which is the actual situation. A small set of named profiles,
each referenced by several registry rows, each resolving its secret through an
environment-variable reference per (3). **The registry names the source; a profile names the
connection; neither holds a value.**

This also gives the machine-local credential file a declared peer. That file is gitignored
with no committed source to rebuild from, and the module is right that it must stay that way
— a profile table does not weaken that, because a profile holds variable *names*.

**Rev 2: the shape has a third, closer precedent, and it also shows the shape's cost.** DataHub
ships exactly this — `dataHubConnection` is keyed by an opaque id, carries only its details, and
declares **no relationship to any entity**; its upsert input accepts no dataset URN. Identity and
access are separated by construction in the model rather than by convention, which is the ruling
above, released.

**And nothing links a DataHub connection to the datasets it serves.** A profile that nothing
references is a profile nothing can audit — the defect this ADR opens with. So the reference
direction is part of the ruling, not an implementation detail left to G125: **the registry row
names its profile**, and a guard fails a row naming a profile that does not exist and reports a
profile no row names. DataHub's omission is the argument for writing it down.

### 5. The fresh-clone default is a DECISION, not merely current behavior

DataHub ships a working `datahub:datahub` account in `user.props`, and its own documentation
carries the warning that follows: deleting the user in the UI does **not** disable it, and
the file must be changed before production. Every deployment inherits a credential it did
not choose.

**The sharper instance, added in Rev 2, because the demo account invites the answer "we would
obviously change that."** DataHub's secret-encryption key falls back to the literal string
`ENCRYPTION_KEY` (`application.yaml:173`): HMAC-derived, no salt, no key id, no rotation tooling.
An installation that never set the variable has been encrypting every stored secret under a
publicly known key — and *correctly setting* the key later is the action that breaks decryption of
everything already stored. A shipped default that works, that nothing forces anyone to change, and
whose correction is itself the breaking change.

DryDocs ships nothing. A fresh clone has no credential file, therefore no accounts,
therefore every login is refused, and the refusal names the bootstrap script. That is the
better default and it is already implemented.

It is recorded here as a **property this system holds**, because it is exactly the kind of
thing a later convenience commit quietly removes — "just seed a demo account so the console
works out of the box" is a one-line change that nothing currently forbids. Under this ADR,
removing it requires amending this ADR.

### 6. The registered-ids rule is a held PROPERTY, and it gets the guard neither peer has

**Across both peers there is exactly one implementation of a credential guard and no stated rule
anywhere.** DataHub has no normative prohibition on credentials in an identifier — two
documentation sweeps return nothing prohibitive, and `@ : / = ?` are all legal in a dataset name;
the exclusion is an accident of API shape. It has no shared DSN sanitizer in either language (a
Java sweep returns zero hits). OpenLineage has `JdbcUrlSanitizer` in Java, with tests, and nothing
in Python.

DryDocs is the inverse: it **has** the stated rule — an identifier publishes, connection
coordinates go to the internal twin, discriminated by *could someone connect with this string
alone?* — and no enforcement at all. That is the one substrate property where the peers are
behind, which is exactly why a later convenience commit could remove it without anyone noticing.
It is recorded here for the same reason (5) is.

**The enforcement is small and it is named so G125 builds it rather than inferring it.** DataHub's
redaction helper carries the discriminator literally — *"if it is just a variable reference, it is
ok to show as-is"*: a value beginning with `$` is a reference, anything else is a value — over a
credential key list (`password`, `token`, `secret`, `connection_string`, `sqlalchemy_uri`, plus
`_password` / `_token` / `_key` / `_connection_string` suffixes). As a **write guard on committed
YAML** that is one test: a credential-keyed field holds a `$`-prefixed reference or nothing.

### 7. The operator works in an editor, not a UI — and that is the canonical path, not a shortfall

This ADR assumes an operator authoring YAML in an editor with no console for it. Rev 1 never said
so, and because it never said so it never claimed the benefits or admitted the costs. Both are
recorded here so the posture is a decision rather than an accident.

**It is what DataHub does.** A DataHub datasource is registered by writing a recipe file —
`datahub ingest -c <file>` — with a `source.type` and a pydantic-validated `source.config` holding
host, port, database, service name, username and password. And the UI has **no model of its own**:
a UI-created ingestion source stores `recipe: string`, an opaque blob beside a schedule and an
executor id. The file path is therefore *more* structured than the UI path — a committed YAML gets
validation, editor tooling, review and a diff; the UI's copy is a string in a database.

**What the posture gives up, stated plainly:** a scheduler, and a form that validates before you
save. The first is out of scope here. The second is answerable without a UI, and (2)'s connection
binding is what makes it possible: a connection test that returns a typed report — reachable, plus
what it could and could not do, plus what to do about it — rather than a boolean. That is the
shape DataHub's `TestableSource.test_connection` returns, and it is the honest form of the
`landing-zones --check` complaint this ADR opens with.

Whether a further surface — an MCP server, so an agent can read a source's metadata after
configuration — is worth building is **not ruled here**. It is Idea-221, it would be a *reader*
under (2)'s second grain rather than a change to this substrate, and it is named only so that the
posture recorded above is not read as a ruling against it.

## Rejected alternatives

Recorded the way 0014 records the sister project's gotcha list — surveyed, and turned down
with the reason.

- **A metastore or securable-object namespace** (Unity Catalog). Reviewed already, and it
  answers a different question: what things *mean*, not where they *are*. DryDocs has an
  ontology layer for meaning.
- **A secrets-manager plugin interface** (OpenMetadata supports AWS Secrets Manager and
  Parameter Store behind one abstraction). DryDocs has one machine and one operator. An
  abstraction over one implementation is scaffolding for a scenario that does not exist; the
  environment-variable reference in (3) is the whole requirement.
- **pyhocon** (Amundsen). The scoped-key idea is worth taking, the HOCON dependency is not —
  the repo already uses pydantic-settings for exactly this shape, and 0014 clause 1 names it.
- **A `platform_instance` retrofit now.** Per (1): record the ceiling, do not mint the axis.
  An id migration with no current benefit is the most expensive form of preparedness.
- **Marquez's namespace-per-source at the API layer.** DryDocs has no lineage service taking
  runtime events. The naming specification is useful as a grammar; the server around it is
  not.
- **DataHub's `__DATAHUB_TO_FILE_` directive.** It solves writing a credential file *from* a
  configuration value. Here the path runs the other way — a person at a terminal writes the
  file — and the guard that keeps filesystem writes out of `drydocs_api` says it should stay
  that way. G126 has since declared that file a read zone for the same reason.
- **Collibra, Alation, Atlan.** Checked and dropped: each publishes the same
  connection-plus-vaulted-credential shape Purview and OpenMetadata already show, with no
  distinct contribution.
- **Doing nothing, and letting `internal-local/` hold the answer informally.** This is the
  status quo and it is the alternative most likely to win by default, so it is named. It
  fails on the audit question: fifteen datasets whose location is a comment cannot be
  enumerated, checked, or moved, and the registry's own stale `~/data/DryDocs` prose is what
  that costs in practice.

## Consequences

**What gets better.** Every source is enumerable, so `landing-zones --check` stops reading
as coverage over half its subject. One expansion function means one place where "unset"
means one thing, which is the class G81 (d) fixed for the data root and nothing else.
The instance ceiling is written down before it is expensive.

**What this costs.** A new committed file and a new concept — the origin profile — in a
configuration layer that already has `source-registry.yaml`, `data-zones.yaml` and
`dev-environment.yaml`. That is a real cost and the mitigation is the fence in (2): the
binding table is the same shape as a landing zone, so this is one concept expressed in two
places rather than two concepts, and consolidating later is a refactor.

**What stays out of scope.** Secret rotation, which is the harder case and needs a
per-identity generation stamp the credential file does not carry (O75 clause (f) already
records this). Persisting executed Cypher server-side for ask-search, whose owning surface
is undecided. And any relocation of data: this ADR declares bindings, and a configuration
change that silently moved a source would be the defect class G81 exists to close.

**The trigger that would reopen this, corrected in Rev 2 — it breaks one layer earlier than
Rev 1 said.** A second instance of any origin — a second Control-M environment, a second Oracle
service behind `psgmgr` — was described as making (1)'s deferral due. Measured, the **connection
layer fails before the identifier layer does**: source-side database configuration is a singleton
today. `OracleSettings` is one triple (`ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_DSN`) with
exactly one consumer, `_oracle_adapter` (`drydocs/cli_shared.py:769-782`), which takes a query and
**no source id** — so there is no seam a second Oracle connection could enter, and the ten
`adapter: oracle` rows all share it. A second service is therefore a *connection* problem first,
which is precisely what this ADR's table exists to fix, and only afterwards an identifier problem
per (1).

**And the map/value split this ADR proposes already exists here, for one system.**
`config/dev-environment.yaml` is it: container, image, volumes, ports and plugin list committed,
with its own header stating that it holds names and ports only and that passwords live in
gitignored `.env` files. The context above reaches for `config/data-zones.yaml` as the model,
which is the right precedent for **filesystem** sources; for a **connection**,
`dev-environment.yaml` is the closer analogue and the stronger argument, because it is the same
split already carrying a live database. The binding table is that file generalized from one
destination to N sources — which also means the per-system variable-prefix convention it needs
(`NEO4J_*`, `ORACLE_*`) is established practice, not a new invention. What is missing is only that
no registry row names its prefix.
