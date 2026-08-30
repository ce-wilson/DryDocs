# Source-registry identity review — the redaction rule is destroying the identifiers the registry exists to carry

<!-- anchor: front-matter -->
- **Scope:** an evaluation, not a runbook and not a decision record. It reads one question: can
  `config/source-registry.yaml` actually identify the things it registers, and can anyone find out
  what it holds? Each finding feeds an existing item or names the one it needs; nothing here mints
  work on its own.
- **Status:** DESCRIPTIVE — **Rev 1, 2026-08-29.**
- **Classification:** Internal-Public — mechanism only. No real database, schema or
  application-id value appears here; every measurement is a count or a shape.
- **Companion:** ADR 0009 (configuration substrate), ADR 0014 (runtime substrate), ADR 0017
  (source-binding substrate, PROPOSED at G124), `docs/design/catalog-substrate-review.md`,
  `config/gate-prompts/registry-wiring-readiness.yaml`

<!-- anchor: why-now -->
## Why now

Two failures in one week, one root cause, and the second is the serious one.

**Registering AWS/Glue metadata as a replica was blocked by the id grammar.** That is not a
workflow annoyance. Source-to-target mapping over registered ids is the core function of a
data-governance product, and an id that resolves to nothing cannot be mapped to anything.

**A generic question cost forty searches and produced a confidently wrong answer.** Asked to
review a loader and report its registry mapping, an agent searched roughly forty times and
returned a review wrong in six places — including quoting a closed defect's error string as
current behavior. The facts were all in importable objects. The surface that hands them over in
one call does not exist, so the search filled the gap with plausible wrongness.

<!-- anchor: what-the-registry-already-has -->
## What the registry already has

Stated first, because two findings below are "this is already right, stop here."

**The two-level split is correct and mature.** Schema v2 (gate signed 2026-07-31) carries 16
systems and 30 datasets: a system row is the thing we connect to, a dataset row is the thing a
loader reads. Retired ids are refused at parse, at lookup, and at overlay binding.

**Loader binding is fully enumerable and needs no search.** Four layers, all importable:
`BaseLoader.source_id` ClassVars, `LOADER_REGISTRY`, the derived `LOADER_SOURCE` projection, and
the per-repo `config/loader-source-overlay.yaml` resolved by
`SourceRegistry.effective_source_id()`. `scripts/render_load_map.py` already inverts them.

**The BDAT layer axis exists** on every system row — human, business, data, technology — ruled at
a gate on 2026-07-31.

<!-- anchor: id-findings -->
## Findings: the identifiers

<!-- anchor: i1 -->
### I1. The grammar calls identifiers "connection coordinates", and they are not

The id grammar states that real db and schema values are **connection coordinates** and belong to
the internal twin only. That premise is wrong. A database or schema *name* is an identifier.
Nobody connects with a schema name; connecting needs a host, a port, a service and credentials.
Redacting the name buys no secrecy and destroys the identity the row exists to carry.

The repo has already ruled it wrong once. **J13 class 3, 2026-08-11:** "schema/table/column ids:
NO SWEEP OWED — already covered by the SIGNED N9 id grammar, which redacts the database and
publishes schema.table." Schema is publishable, by a ruling on record.

**Two live rows ignore that ruling**, and they are the flagship replica rows — the ones the
`catalog` system note calls "exactly the replica case the @ grammar exists for":
`catalog@[db].[schema].datasets_v` and `catalog@[db].[schema].distributions_v`. The only real
token in those ids is the view name. A third instance is a *template* on the `snow` system row,
`snow@[db].[schema].<table>`, which teaches the shape to the next row someone writes.

**Why it keeps recurring: the carve-out is a judgement, not a test.** One schema is published
because someone decided it is "established public vocabulary". Nothing states what qualifies, so
every new source re-litigates it and the safe-looking answer — redact — wins by default and
silently destroys an identifier.

The discriminator that would settle it: *could someone connect with this string alone?* A schema
name fails that test. A service name, host, port or credential passes it.

<!-- anchor: i2 -->
### I2. The db placeholder is carrying two jobs, and ADR 0017 already separates them

The reason the db placeholder felt necessary is that it conflates the **logical database name**
(identity, committable) with **which physical deployment** (the instance coordinate, per-machine).

ADR 0017 clause 1 — drafted at G124, awaiting the user's ruling — already rules that the instance
coordinate lands in the binding table, precisely so the eventual answer is a configuration change
rather than an id migration. Applied here the tension dissolves: the id carries the real logical
name, the binding carries the account, region, service and endpoint, and nothing is redacted to
preserve a distinction the binding table expresses properly.

This is also what makes an AWS/Glue table registrable. `{origin}@{database}.{schema}.{table}` is a
complete identity; the connection stays where connections belong.

<!-- anchor: i3 -->
### I3. The application id is a placeholder on every system row

The application-id field reads the same literal placeholder on **all 16** systems, by the D1
amendment: a standing placeholder on every committed system row, with the real value living only
in the internal twin.

So the Application ID — the identifier through which a governance product maps business ownership
— is absent from every row in the registry. Same category error as I1, a third time: an
application id **identifies**, it does not **connect**.

<!-- anchor: view-findings -->
## Findings: nothing can see what the registry holds

<!-- anchor: v1 -->
### V1. The view is organized by name, so a miscategorization is invisible

`dpl` is registered `layer: technology`. It is a pipeline and dataset taxonomy registry — a
data-layer asset. The registration is wrong, and nothing surfaces it for review.

The distribution explains how it happened: **technology 9, data 5, business 2, human 0.**
Technology is the default bucket, `human` is declared in the vocabulary and has never been used,
and no surface anywhere asks anyone to confirm a layer. The rendered load map shows `layer` as one
column of a flat systems table; it never groups by it, never counts it, and never flags a row
nobody has confirmed.

A view organized by BDAT layer, then application, then ontology class would have made this
legible on the day it was registered. A view organized by id string cannot.

<!-- anchor: v2 -->
### V2. The DCAT field cannot be the ontology heading — it is a constant

`asset_type` reads `dcat:Dataset` on **30 of 30** rows. A constant discriminates nothing, and a
constant rendered as a column reads as an answer when it is a default. The genuine class comes
from `config/taxonomy-ontology-map/`, which the generator already joins as `ontology_mappings`. A
row still sitting on the bare default is *unclassified* and should say so rather than borrowing
the appearance of a classification.

<!-- anchor: v3 -->
### V3. Three declared axes have no consumer, and one has none at all

- **`taxonomy_category`** has a full vocabulary — Pipelines 11, Data Asset 5, Software/Apps 4,
  Infrastructure 3, Architecture 2, ITSM/Gov 2, People and Org 2, Product 1 — and **zero readers**
  anywhere outside `config/`. No render, no test, no module.
- **`acquisition`** reaches exactly one surface, `drydocs landing-zones`, and only its manual
  half, because `manual_zones()` filters on it. The automated half is invisible.
- **Replica is computable and computed nowhere.** `origin != system` is the exact predicate, and
  `authority: ADS` (approved copy) versus `SOR` (originating source) corroborates it — all ten
  psgmgr rows are ADS. Neither reaches any surface.

<!-- anchor: twin-findings -->
## Findings: the internal twin is a black hole

<!-- anchor: t1 -->
### T1. The registry names no variable, points at no twin file, and cannot say what is unset

The registry says the real value lives only in the internal twin, and stops. It never says *which*
twin file, *which* variables, or *whether they are set*. `internal/` holds roughly twenty
directories with no index of which one carries which system's settings.

**Measured:** `.env.example` declares 17 keys. First-party code reads **8 more that are declared
nowhere** — the console-credentials path, the Control-M API config pointer, the two mapping-store
variables, the agent registration key, the caller variable, a Neo4j container name, and the legacy
aliases of the log and caller variables.

So a null service locator with an explanatory comment is not merely an empty slot. It is an empty
slot with no way to discover that it is empty, no statement of what would fill it, and no path to
fill it.

<!-- anchor: t2 -->
### T2. The enumeration cannot be a grep, which is how the gap grew unseen

`drydocs_core/config.py` uses pydantic-settings with prefixed groups, so a variable like the Neo4j
URI never appears as a literal string in the source. A text search sees a prefix and misses the
field — and a text search is what anyone reaches for first.

Any list of "every variable the system reads" must therefore be built from the **settings classes
plus the declarations**, never from a search. This is J37 restated one layer over: read the
importable object, never the render — and never the text that happens to spell it.

<!-- anchor: what-changes -->
## What this changes for the existing items

Proposals, not applied. Each names the item that owns it.

| Item | Clause | Proposed amendment |
|---|---|---|
| **ADR 0017** (G124, PROPOSED) | (1) the key ceiling | I2 makes the deferral concrete: the instance coordinate is what the db placeholder stands in for TODAY, not a future need. Worth stating before the ruling. |
| **G125** | (a) the undeclared half | Bind per **SYSTEM** (psgmgr 10, snowflake 3, oracle 1, drydocs-stg 1), not per origin (~6): the `controlm`, `hr` and `seal` origins all resolve to one connection. Also four stale data-root locator strings, not one. |
| **N18** (the wiring gate) | A2 | The SME ruled `cm_escalation_db` a REFERENCE — untrusted for application SEAL, authoritative for the failure to queue to technician mapping, joined to the Control-M job definition table on job name. That confirms clause A2's "third kind". |
| **N18** | D3 | The SME asked for this on a rendered surface. D3 says that gets its own item; V1 to V3 say what it must show. |
| **J13** | class 3 | The ruling stands and is VIOLATED by two live rows plus one template. Enforcement, not a re-ask. |
| **new** | — | The id-grammar ruling (I1 to I3). It changes committed ids and needs the SME, so it is a gate rider, not an edit. |
| **new** | — | The registry read surface (V1 to V3) and the twin leg (T1, T2). |

<!-- anchor: not-taken -->
## What we deliberately do not take

- **A trust vocabulary on pipeline rows.** The SME ruled kind-not-trust: with no adapter, no
  `feeds_taxonomy` and `confirmed: false`, a reference is already derivable. Adding a vocabulary
  would pre-empt a ruling the wiring gate reserves.
- **Any new registry field at all.** Layer, category, authority, acquisition and origin already
  exist; replica and reference are DERIVED predicates over them. Gate clause D2 keeps the schema
  closed until the wiring gate signs, and nothing here needs it open.
- **Publishing a value to make an id resolvable.** The rule is names, never values. If a specific
  database name is itself the confidential material, that is a per-row SME ruling cited on the row
  — an auditable exception, not the ambient default that caused this.
- **A second database.** ADR 0009 already accepts SQLite as the derived read model and
  `var/mapping.db` already implements it, drafts and all. The registry gets tables there or
  nowhere.
- **Rewriting the manual half to match the automated one.** The fifteen manual rows resolve
  correctly today. Ruling the two halves the same SHAPE costs nothing; rewriting working rows to
  prove it buys nothing.
