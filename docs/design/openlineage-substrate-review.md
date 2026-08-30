# OpenLineage substrate review — reading the source ADR 0017 cites

<!-- anchor: front-matter -->
- **Scope:** a THIRD pass, and the first one that reads a single product's source rather than
  surveying many. Its question is narrow: **ADR 0017 cites OpenLineage twice for its central
  shape — are those citations right?** Everything else here is downstream of that answer.
- **Status:** DESCRIPTIVE — **Rev 1, 2026-08-30.** This review rules nothing. ADR 0017 is
  PROPOSED and its acceptance is the user's; G125 stays `todo`.
- **Classification:** External reasoning over Internal-Public context. Every fact about
  OpenLineage is public and Apache-2.0; every fact about DryDocs is read from
  `config/source-registry.yaml`, which is already committed. No connection coordinate appears
  here.
- **Companion:** `docs/design/catalog-substrate-review.md` (the second pass, the survey ADR 0017
  rules on), `docs/decisions/0017-source-binding-substrate.md`, `config/source-registry.yaml`.
- **Verification venue (J18):** this desktop, `C:\coding\projects\OpenLineage`, cloned
  2026-08-30. HEAD `b995ee00` (commit date 2026-08-28), latest release tag `1.52.0`, licence
  Apache-2.0. Counts over DryDocs come from `poetry run python` against
  `config/source-registry.yaml` at `main`, not from reading the file by eye.
- **Second source:** `ce-wilson/research`, `openlineage-datasource-onboarding/` — a 55-claim
  analysis of the same repo at the same commit, produced independently. Its sampled claims are
  re-derived below rather than accepted.

<!-- anchor: bottom-line -->
## Bottom line

**One of ADR 0017's two OpenLineage citations does not survive contact with the source, and the
registry it governs is the thing that disproves it.**

Clause 2 says DryDocs's grammar is "already isomorphic" to OpenLineage's, with `origin` sitting
where OpenLineage puts the namespace, and concludes that the binding table therefore needs "a row
per origin." OpenLineage's namespace is a **connection** — `oracle://{host}:{port}`. DryDocs's
`origin` is a **provenance label** — who produced the data. The registry field that actually
behaves like a namespace is `system`, and the two are measurably not the same field:
`origin: controlm` spans **three** different systems, so a per-origin row cannot bind to one
connection at all.

Clause 1's citation holds, but is used to support a deferral OpenLineage itself does not make.
Clauses 3, 4 and 5 rest on DataHub, OpenMetadata and Purview and are untouched by any of this.

And OpenLineage does **not** solve the problem ADR 0017 exists to solve. It is a wire format. It
has no binding table, no credential store and no source configuration of any kind. Its
contribution is a grammar and one transferable rule; treating it as a design precedent for the
substrate itself would over-cite it.

<!-- anchor: what-openlineage-implements -->
## What OpenLineage actually implements

Dataset identity is the pair (`namespace`, `name`), both required (`spec/OpenLineage.json`,
`$defs/Dataset`). The naming convention assigns them by platform. Read off
`website/docs/spec/naming.md` at HEAD, unedited:

| Platform | Namespace | Name |
|---|---|---|
| Oracle | `oracle://{host}:{port}` | `{serviceName}.{schema}.{table}` or `{sid}.{schema}.{table}` |
| Snowflake | `snowflake://{org}-{account}` | `{database}.{schema}.{table}` |
| Postgres | `postgres://{host}:{port}` | `{database}.{schema}.{table}` |
| MSSQL | `mssql://{host}:{port}` | `{database}.{schema}.{table}` |
| Redshift | `redshift://{cluster_identifier}.{region_name}:{port}` | `{database}.{schema}.{table}` |
| S3 | `s3://{bucket name}` | `{object key}` |
| Local file | `file` | `{path}` |
| Remote file | `file://{host}` | `{path}` |

Forty-odd rows, one shape. **The namespace is where you connect. The name is what you asked
for.** Not one of the forty carries a username, a password or a URI userinfo component — a fact
the second source calls its load-bearing claim, and which I re-read the full table to confirm.

Two consequences matter here, and they pull in opposite directions:

- The database — `serviceName`, `{database}` — sits in the **name**. It is part of the object's
  stable identity, and it is committed.
- The host and port sit in the **namespace**. They are part of identity too, which is what makes
  two Oracle instances distinct without any extra axis, and also what makes the identifier
  fragile: `naming.md` warns that switching Snowflake namespace formats means "existing lineage
  nodes won't connect to new ones."

<!-- anchor: finding-1 -->
## Finding 1 — clause 2 maps `origin` to the namespace; the registry says the namespace is `system`

ADR 0017 clause 2, verbatim:

> DryDocs's grammar is already isomorphic: `{origin}@{db}.{schema}.{table}` puts the origin where
> OpenLineage puts the namespace and the qualified object where it puts the name. So the binding
> table needs **a row per origin**, inherited by every dataset beneath it.

The registry disagrees with the first sentence, and it does so in the row the ADR is describing:

```yaml
  - id: "controlm@[db].psgmgr.cm_def_vtab"
    system: psgmgr
    origin: controlm
```

`origin` is `controlm` — the orchestrator whose data this is. `system` is `psgmgr` — the Oracle
service you connect to. It is `system` that behaves like an OpenLineage namespace: one place, one
connection, one set of credentials. `origin` answers a question OpenLineage does not ask in the
identifier at all; its equivalents are the `dataSource` and `ownership` **facets**, which are
metadata hung off identity, never identity itself.

That is not automatically a defect in DryDocs's grammar — it is our grammar, and putting a
provenance token in the identity position is a defensible choice. What it does mean is that the
**isomorphism argument cannot carry the binding conclusion**, because the field the conclusion
keys on is not the field the analogy maps.

**Measured, over `config/source-registry.yaml` at `main` — 16 systems, 30 datasets, 15 automated
and 15 manual:**

| Keyed by | Rows needed for the 15 automated datasets |
|---|---|
| `system` | **4** — psgmgr 10, snowflake 3, oracle 1, drydocs-stg 1 |
| `origin` | **6** — controlm 9, hr 1, seal 1, catalog 2, oracle 1, snowflake 1 |

The ADR's "roughly six origins" is arithmetically correct. The problem is not the count.

**Two structural facts decide it, and the second one is fatal:**

1. `system: psgmgr` carries three origins — `controlm`, `hr`, `seal`. A per-origin key mints three
   binding rows for **one** Oracle service, each repeating the same coordinates. That is precisely
   the duplication clause 4 argues against when it chooses Purview's named-profile shape over
   OpenMetadata's derived paths: *"one Oracle account reads eight `psgmgr` views."* Clause 2
   re-fragments the connection that clause 4 exists to share. The ADR contradicts itself across
   two clauses.
2. `origin: controlm` spans three systems — `controlm`, `drydocs-stg`, `psgmgr`. So the largest
   origin in the registry has **no single connection to bind to**. A per-origin row is not merely
   redundant here; it is unsatisfiable. `origin: seal` spans two systems and fails the same way.

**Recommended amendment**, for the user's ruling rather than applied: clause 2 keys the binding
per **SYSTEM**. The rest of the clause survives unchanged — the inheritance-by-datasets shape, the
"one mechanism, not two" fence with landing zones, and the observation that OpenLineage splits
connection from object are all still right. Only the field name changes, and the OpenLineage
argument gets *stronger* under the correction, because `system` really is the namespace.

This is the same conclusion the standing plan already reached for G125 ("bind per **SYSTEM**
(psgmgr 10, snowflake 3, oracle 1, drydocs-stg 1), not per origin"). Two independent routes to
one answer, and the ADR text is the piece that was never updated to match.

<!-- anchor: finding-2 -->
## Finding 2 — the `[db]` redaction is backwards, and OpenLineage puts it more sharply than the ADR uses it

Committed dataset ids carry `[db]` as a redaction placeholder because the registry grammar calls
the database a connection coordinate. Measured against the naming table, that is exactly inverted:

| Half | OpenLineage | Carries | DryDocs today |
|---|---|---|---|
| Name | `{serviceName}.{schema}.{table}` | database, schema, table | `[db].psgmgr.cm_def_vtab` — **database redacted** |
| Namespace | `oracle://{host}:{port}` | host, port | undeclared — `locator.service: ~` plus a comment |

DryDocs redacts the half OpenLineage treats as safe by construction, and leaves undeclared the
half OpenLineage treats as the connection. Note what is left in `controlm@[db].psgmgr.cm_def_vtab`
after the redaction: `psgmgr` is the **schema** and publishes fine; the single redacted token is
the database. So the boundary is already being drawn in the right *place* for schema and table,
and only the database is on the wrong side of it.

This corroborates §0 of the standing plan with a citation rather than an argument, and it
strengthens the user's standing test — *could someone connect with this string alone?* — by
showing a 40-platform convention that answers it the same way for every platform.

**The caveat that keeps this honest:** the guarantee is convention plus tested implementation, not
a normative prohibition. Nothing in `spec/OpenLineage.json` forbids a namespace containing
userinfo. What exists is a uniform table, 28 Java `Naming` classes whose constructors take no
credential parameter, and a sanitizer that strips credentials when a URL arrives anyway. That is
strong evidence about the intended boundary and weak evidence about enforcement — do not cite it
as a rule the spec imposes.

<!-- anchor: finding-3 -->
## Finding 3 — clause 1 defers an axis OpenLineage never defers, and the trade is real

Clause 1 records the three-part-key ceiling and declines to mint the instance axis, on DataHub's
`platform_instance` retrofit as the cautionary case. The reasoning is sound and the DataHub facts
are as described.

OpenLineage is the counter-example, and the ADR does not mention it: **there is no instance axis
to add, because the host is already in the namespace.** Two Oracle services, two namespaces, two
distinct datasets, no retrofit — ever.

It is not free. Identity that contains the connection is identity that breaks when the connection
moves, which is exactly the Snowflake warning quoted above: change the namespace format and old
nodes never join new ones. DataHub's separate `dataPlatformInstance` aspect exists to avoid that
coupling; it pays for the decoupling with a retrofit.

So the two products bracket the choice rather than agreeing, and ADR 0017's deferral sits between
them defensibly. The recommendation is only that clause 1 **name the trade** instead of implying
a settled direction: OpenLineage shows the axis can live in the identifier, and shows what that
costs when the identifier has to change. The ADR's own escape hatch — the instance coordinate
lands in the binding table when a second instance appears — is the DataHub side of that bracket,
and is better argued once the OpenLineage side is stated.

<!-- anchor: finding-4 -->
## Finding 4 — OpenLineage does not solve the problem ADR 0017 is about

Stated plainly because the risk here is over-citation, not under-citation.

OpenLineage is an **event format**. Searched at HEAD: it has no source configuration, no
connection registry, no credential store, no secret reference, no binding of a declared source to
a real place. Its credential separation is achieved by *never putting a credential in the
identifier* — a property of the grammar, not a mechanism. There is nothing to adopt for the
substrate itself.

Concretely: clause 3 (committed YAML references environment variables), clause 4 (named
connection profiles) and clause 5 (the fresh-clone default) rest entirely on DataHub,
OpenMetadata and Purview. Nothing in this review touches them, and no OpenLineage citation should
be added to them.

**One exception, and it is a good one.** The OpenLineage *Python client* configures itself the way
clause 3 wants DryDocs to: a YAML file found at `OPENLINEAGE_CONFIG`, then the working directory,
then `$HOME/.openlineage`, deep-merged with environment variables under an `OPENLINEAGE__` prefix
where `__` is a path separator into the nested config
(`client/python/src/openlineage/client/client.py:213-241, 406-446`). That is **structural**
override — a variable addresses a node in the config tree — where DataHub's `${MSSQL_PASSWORD}`
is string interpolation into a value slot. Structural override is the better fit for clause 3's
"one expansion function, one error, one enumerable list," because the set of legal variables is
derivable from the config schema instead of from scanning files for `${...}`.

<!-- anchor: second-source -->
## Finding 5 — the second source checks out, and its central rule lands on `system`

Sampled claims from `ce-wilson/research`, re-derived here rather than accepted:

| Claim | Re-derivation | Result |
|---|---|---|
| Sourced at `b995ee00c`, release `1.52.0` | `git rev-parse HEAD` → `b995ee00`; `git describe --tags --abbrev=0` → `1.52.0` | confirmed |
| `C-46` — the `lineage` facet is unreleased | `git tag --contains 2cfa2594b` → **empty** | confirmed, still true today |
| `C-10`/`C-11`/`C-12`/`C-14` — namespace forms, no userinfo anywhere | full `naming.md` table read | confirmed |
| `C-51`/`C-52` — Java ships `JdbcUrlSanitizer`, five regex passes, Python has none | file read; `grep -rniE "sanitiz\|dropSensitive" client/python/src/` returns nothing relevant | confirmed |
| Apache-2.0 | `LICENSE` | confirmed |

Its `D-05` — *"the vault key is derived from the OpenLineage namespace, not the reverse; credential
rotation never changes the namespace, so no lineage node is ever orphaned by a password change"* —
is the single most transferable idea in the document for our purposes. Applied to DryDocs it says
the credential profile is keyed by the thing that identifies the **connection**, and Finding 1
already established which field that is: `system`. Two documents, two routes, one correction.

**Where its framing has to be adjusted before reuse.** It answers a *datasource onboarding*
question — how to emit incremental curation as OpenLineage events — which is not ADR 0017's
question. Its `D-01` through `D-04` and its whole risk table are about producing events against a
lineage backend. DryDocs produces no OpenLineage events and has no lineage backend, so those
sections are reference material for a different decision, not input to this one. Read `D-05`,
`C-10`–`C-14` and `C-51`–`C-52`; leave the rest for whenever the emission question is actually
asked.

<!-- anchor: scaffolding -->
## What can be scaffolded

Apache-2.0 throughout, so vendoring with attribution is legally clean. Ranked by value per unit of
cost, and honest about what is a dependency versus a pattern.

| # | Take | From | Cost | What it buys |
|---|---|---|---|---|
| 1 | **The five credential-stripping regexes**, ported to Python | `client/java/.../jdbc/JdbcUrlSanitizer.java` | ~15 lines plus tests | The Python client has **no equivalent** — verified. This is the guard behind the plan's fence that no connection string reaches a committed file. Note it drops the entire query string rather than allow-listing; adopt that stricter posture. |
| 2 | **The default-redact posture with an explicit allow-list** | `client/python/.../utils.py` `RedactMixin`; `client/python/redact_fields.yml` | pattern, no code | The plan's `registry env` surface must print `set`/`unset` and never a value. Default-deny with a named exemption list is the same shape as `test_module_boundary.py`'s UNCLASSIFIED rule, and it is how a new field fails closed instead of leaking. |
| 3 | **Structural env override of a config tree** | `client.py:213-241, 406-446` (`OPENLINEAGE__A__B__C` → `config["a"]["b"]["c"]`, deep-merged, JSON-parsed values) | pattern, ~40 lines | Clause 3's one expansion function. Better than `${VAR}` interpolation because the legal variable set is derivable from the schema — which is exactly what makes the plan's generated `.env.example` and its "one enumerable list" possible. |
| 4 | **The `DatasetNaming` protocol shape** — `get_namespace()` / `get_name()`, one small validated class per platform | `client/python/src/openlineage/client/naming/dataset.py` (512 lines, `attrs` only) | copy the shape, not the file | A typed, per-platform locator builder for the binding table, replacing free-text `locator:` prose that no guard reads — the ADR's own one-line argument for itself. Do **not** vendor the module: it builds OpenLineage identifiers, which DryDocs does not emit. |
| 5 | **The 40-platform namespace vocabulary** | `website/docs/spec/naming.md` | copy as data | A ready-made controlled vocabulary for whatever field ends up holding the connection form, and a published answer to "what shape does an S3 / Glue / Snowflake / file source take" that we would otherwise invent per source. |
| 6 | **The 38 facet JSON schemas** | `spec/facets/*.json` | none to read | Relevant to the *ontology* layer, not to ADR 0017. Two worth knowing: `TagsDatasetFacet.field` gives column-level classification inside a dataset-level facet, and `HierarchyDatasetFacet` is an ordered database→schema→table array — the credential-free display projection the plan's §2 view needs. |

**Do not take:** the `lineage` facet (unreleased — `git tag --contains 2cfa2594b` is empty as of
today, re-check before relying on it), the transport layer, the event model, `SymlinksDatasetFacet`
(it asserts two names for **one** entity and would collapse a replica into its origin — the exact
fact a replica registration exists to record), and the OpenLineage client as a runtime dependency.
DryDocs has no lineage service and no reason to acquire one here.

<!-- anchor: what-changes -->
## What this changes, and what it does not

**Changes proposed, none applied:**

1. **ADR 0017 clause 2** — key the binding per `system`, not per `origin`. Four rows, not six, and
   `controlm` becomes bindable. This is a ruling; it goes to the user.
2. **ADR 0017 clause 1** — name OpenLineage as the counter-case that puts the instance in the
   identifier, and state the cost it pays. Strengthens the existing deferral; does not reverse it.
3. **G125 acceptance** — already needs the per-system rewrite. This review is the evidence for it.

**Unchanged:** clauses 3, 4 and 5, whose sources are elsewhere. The `[db]` question, which is
corroborated here but was already the standing plan's §0 and is still a sensitivity ruling the SME
owns. And the scope fence — no new registry field, no ADR 0017 implementation.

<!-- anchor: verification -->
## Verification checklist for a reviewing agent

Ordered by value, each independently checkable.

1. **Re-run the cardinality measurement.** Load `config/source-registry.yaml`, group the automated
   datasets by `system` and by `origin`, and list any origin spanning more than one system. If
   `controlm` no longer spans three, Finding 1's fatal half is stale — the rest of it is not.
2. Read `website/docs/spec/naming.md` end to end and look for one namespace form containing
   userinfo. A single counterexample weakens Finding 2.
3. `git tag --contains 2cfa2594b` in the clone. Empty today; a tag means the `lineage` facet
   shipped and the "do not take" list needs revisiting.
4. Confirm `origin` has no OpenLineage counterpart in the identifier by searching the spec for any
   identity component describing data *provenance* rather than *location*. If one exists, Finding
   1's framing needs adjusting.
5. Check that `JdbcUrlSanitizer`'s regexes still number five and that no Python equivalent has
   landed, before spending effort on scaffold item 1.
6. Re-derive the facet `$id` versions before using anything in scaffold item 6. They drift between
   releases and this review pins none of them.
