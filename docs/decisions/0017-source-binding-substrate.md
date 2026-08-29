# ADR 0017 — Source-binding substrate: a declared source binds to a real place through one per-origin table

```yaml
status: PROPOSED          # the drafting session never accepts its own ADR — acceptance is the user's
date: 2026-08-29
authored_by: G124 (desktop)
deciders: [chad.wilson]
layer: 0-configuration
relates_to:
  - 0009-configuration-substrate.md            # git text is the source of truth — the scope clause this reads
  - 0014-runtime-substrate.md                  # the per-machine exception, and the map-vs-root model reused here
  - 0012-data-named-load-surface.md            # acquisition as a source-entry axis
  - docs/design/catalog-substrate-review.md    # the survey this rules on (Rev 1, 2026-08-28)
  - config/source-registry.yaml                # 15 systems / 30 datasets; the WHAT
  - config/data-zones.yaml                     # G81's declared zones; the mode axis
  - drydocs_core/landing_zones.py              # resolves the manual half today
  - drydocs_api/credentials.py                 # the console credential carrier (O69/O73)
executed_by: G125 (the binding table and the one expansion function)
```

> **Nothing in this record changes code.** G125 implements it and `depends_on` this ADR, so
> nothing implements an unratified ruling — the G104 → G105–G109 shape exactly.

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

DataHub's original dataset URN was the same three parts. Their documentation states the
failure plainly: that key cannot represent two deployments of the same platform in one
environment, so an organization with two Redshift instances in production collapses both
into one identifier. Fixing it required a `dataPlatformInstance` aspect and a
`platform_instance` recipe parameter, changing URN generation across every source — a
retrofit that touches everything already ingested.

**DryDocs is standing where DataHub stood before that change, and it is not hypothetical.**
The committed dataset ids carry `[db]` as a redaction placeholder, and `[db]` is precisely
the instance coordinate — the registry comment says the real value is a connection
coordinate belonging in the internal twin. Four production Control-M data centers sit behind
those ids. Two machines hold independent graphs.

**The decision is to record the ceiling and name where the axis lands, not to add it now.**
The binding table introduced in (2) is where an instance coordinate goes when something
needs it, which makes the eventual answer a configuration change rather than an id
migration. Adding an instance segment to ids today would be a migration bought with no
current benefit.

Naming the ceiling costs a paragraph. Discovering it after the graph is loaded costs what it
cost DataHub.

### 2. The binding is per-ORIGIN, not per-dataset

OpenLineage's naming specification gives every dataset two parts: a **namespace** derived
from the datasource (`oracle://{host}:{port}`, `s3://{bucket}`, `file`) and a **name**
identifying the object inside it (`{serviceName}.{schema}.{table}`, `{object key}`,
`{path}`).

The split is the useful part. The namespace is the **connection** — it varies by machine,
carries the host, and can hold a secret. The name is the **object** — stable across every
deployment and safe to commit.

DryDocs's grammar is already isomorphic: `{origin}@{db}.{schema}.{table}` puts the origin
where OpenLineage puts the namespace and the qualified object where it puts the name. So the
binding table needs **a row per origin**, inherited by every dataset beneath it. Fifteen
automated datasets reduce to roughly six origins.

**One mechanism, not two.** The same shape covers the filesystem sources: a landing zone is a
namespace of `file` with a root, which is what `drop_dir_base` already is, one level less
general. This ADR does **not** require G125 to rewrite the manual half — the existing rows
work and rewriting them buys nothing — but it rules that the two are the same shape, so a
future consolidation is a refactor rather than a redesign, and neither half may grow a
concept the other cannot express.

### 3. Committed YAML REFERENCES environment variables; it never holds a value

DataHub's recipes write `password: ${MSSQL_PASSWORD}` and expand at load, so the file is
committable and the secret never is. That is the shape adopted here.

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

### 5. The fresh-clone default is a DECISION, not merely current behavior

DataHub ships a working `datahub:datahub` account in `user.props`, and its own documentation
carries the warning that follows: deleting the user in the UI does **not** disable it, and
the file must be changed before production. Every deployment inherits a credential it did
not choose.

DryDocs ships nothing. A fresh clone has no credential file, therefore no accounts,
therefore every login is refused, and the refusal names the bootstrap script. That is the
better default and it is already implemented.

It is recorded here as a **property this system holds**, because it is exactly the kind of
thing a later convenience commit quietly removes — "just seed a demo account so the console
works out of the box" is a one-line change that nothing currently forbids. Under this ADR,
removing it requires amending this ADR.

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

**The trigger that would reopen this.** A second instance of any origin — a second
Control-M environment, a second Oracle service behind `psgmgr` — makes (1)'s deferral due.
At that point the instance coordinate lands in the binding table as a field, and only ids
that need to distinguish two instances change.
