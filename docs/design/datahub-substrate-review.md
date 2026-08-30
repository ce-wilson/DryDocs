# DataHub substrate review — reading the source behind ADR 0017's other four citations

<!-- anchor: front-matter -->
- **Reviewed at:** commit `cb5d45d8` on `main` (2026-08-29), port base `port-base-20260829`; venue MSI (producer desktop). *The commit is this file's own last revision, which is the tree the reading was done against; absent here reads as not-yet-ported, not as broken (`docs/style/review-provenance.md`, J63).*
- **Scope:** the FOURTH pass, and the companion to `openlineage-substrate-review.md`. That review
  closed by saying "clauses 3, 4 and 5 rest on DataHub, OpenMetadata and Purview and are untouched
  by any of this." This is the pass that touches them. Its question is the same narrow one:
  **ADR 0017 cites DataHub four times — are those citations right?**
- **Status:** DESCRIPTIVE — **Rev 2, 2026-08-30.** This review rules nothing. ADR 0017 is
  PROPOSED and its acceptance is the user's; G125 stays `todo`.
  *Rev 2 adds the three-way overview, and findings 7 and 8: how DataHub actually registers a
  connection and a datasource, and what DryDocs has for database configuration today. The user's
  question that prompted them — "I did not see anything about having database configuration; you
  are creating the YAML files as we go in VS Code, as an application that assumes the user is not
  using a UI" — is answered at `finding-7`, and the answer is that the editor-first posture is
  DataHub's own canonical path, not a degraded substitute for one.*
- **Classification:** External reasoning over Internal-Public context. Every fact about DataHub is
  public and Apache-2.0; every fact about DryDocs is read from `config/source-registry.yaml` and
  `drydocs_core/source_registry.py`, both already committed. No connection coordinate appears here.
- **Companion:** `docs/design/openlineage-substrate-review.md` (the third pass),
  `docs/design/catalog-substrate-review.md` (the survey ADR 0017 rules on),
  `docs/decisions/0017-source-binding-substrate.md`.
- **Verification venue (J18):** this desktop, `C:\coding\projects\datahub`, cloned 2026-08-30
  (`--depth 1 --filter=blob:none`). HEAD `dea0f9c1`, commit date 2026-08-30, licence Apache-2.0.
  The OpenLineage clone at `C:\coding\projects\OpenLineage` HEAD `b995ee00` is re-used for the
  method check below. Counts over DryDocs come from `poetry run python` against the registry at
  `main`, not from reading YAML by eye.
- **Second source:** `ce-wilson/research`, `scratchpad/research/reports/`
  `datahub-datasource-onboarding-model-analysis.md` — a 925-line analysis pinned to DataHub
  `7d5cedd5f8` (2026-08-28), reporting 312 claims of which 229 were confirmed, 47 corrected and 1
  refuted under adversarial re-verification. Its claim ids (`C-nn`, `D-nn`, `R-nn`) are cited
  below. **Seven of its decisive claims were re-derived here against a clone taken two days
  later; all seven reproduced.** Claims not re-derived are marked as such.

<!-- anchor: bottom-line -->
## Bottom line

**Two of ADR 0017's four DataHub citations are corroborated and made stronger. One is right in
shape but incomplete in a way that would re-introduce a defect the repo has already fixed. One is
wrong in the direction that matters most, and it is the clause the whole deferral rests on.**

Clause 1 says DataHub's three-part-key ceiling was fixed with a `dataPlatformInstance` aspect,
and concludes that DryDocs can therefore defer its own instance axis because "the binding table is
where an instance coordinate goes when something needs it, which makes the eventual answer a
configuration change rather than an id migration." **DataHub did not do that.** `platform_instance`
is not a fourth key component; it is concatenated into the URN's `name`, so adding one **changes
the dataset's identity**. DataHub's fix *was* an id migration. The escape hatch clause 1 promises
has no precedent in the product cited for it.

**And the ceiling is lower than clause 1 records, in a place the clause does not look.** Clause 1
points at `[db]` in the committed id string. But `[db]` is a redaction inside a string no code
keys on, whereas `SourceEntry.urn` derives `({carrier},{artifact},prod)` — which drops the
database **and the schema**. DataHub's URN name was always the fully qualified native name, so
DataHub was missing exactly one axis. DryDocs's derived URN is missing three.

Clause 3's `${VAR}` shape is correct and worth keeping, but DataHub's expander is bash-style and
supports `${VAR:-default}` — adopting the syntax as cited would re-introduce, at the syntax level,
the exact silent-default behavior G81 clause (d) removed. Clauses 4 and 5 are corroborated, each
with a better example than the one the ADR uses.

<!-- anchor: overview -->
## Overview — ADR 0017 against both peers, one table

The two peers answer different questions, and ADR 0017 borrows from each without saying which
half it is borrowing. Stated plainly:

| | OpenLineage | DataHub | DryDocs today |
|---|---|---|---|
| **What it is** | a wire format | a running catalog service | a git repo with loaders |
| **Identity** | (`namespace`, `name`) — connection + object | URN (`platform`, `name`, `fabric`) — three parts, enforced | dataset id (4 parts) AND a derived URN (3 parts) that drops db + schema |
| **Instance axis** | inside the namespace (`oracle://host:port`) | inside the `name`; adding one changes identity | `[db]`, redacted, absent from the URN entirely |
| **Naming convention** | published for 40+ platforms | none; one delimiter char per platform | one grammar, one page of the registry header |
| **Source configuration** | **none — it has no sources** | a typed `source.config` block per recipe, pydantic-validated | pydantic-settings, but ONE Oracle triple for all sources |
| **Credential** | none | `dataHubSecret` + `dataHubConnection`, AES-256-GCM, standalone | machine-local `.env`, `SecretStr`, gitignored |
| **Reference syntax** | none | `${VAR}` in the recipe, three backends, bash-style | direct env reads in seven resolvers |
| **Connection test** | none | `TestableSource.test_connection()` → a typed report | `landing-zones --check`, manual half only |
| **Normative rule against credentials in ids** | none | none | **yes** — the registered-ids rule, unenforced |
| **Primary authoring surface** | n/a | **a YAML file in an editor**; the UI stores the same recipe as a string | a YAML file in an editor |

**The single most useful line in that table is the last one**, and it is the one ADR 0017 never
states: OpenLineage cannot help with the substrate at all, because it has no sources to configure.
Everything ADR 0017 needs — a typed connection block, a credential object, a reference syntax, a
connection test — exists in DataHub and nowhere in OpenLineage. The ADR cites them as if they were
two comparable precedents. They are a grammar and a product.

<!-- anchor: what-datahub-implements -->
## What DataHub actually implements

Four mechanisms matter here, and they are separate objects by construction rather than by
convention.

| Concern | Mechanism | Shape |
|---|---|---|
| Identity | `datasetKey` → `DatasetUrn(platform, name, origin)` | exactly three components, enforced |
| Instance | `platform_instance` | **concatenated into `name`**, not a fourth component |
| Credential | `dataHubSecret` + `dataHubConnection` | standalone entities, AES-256-GCM, no link to any dataset |
| Reference | `${VAR}` in a recipe | resolved at job time, three backends, bash-style defaults |

The identity/access split is real and structural: no shipped identifier builder in either language
accepts a credential (`C-32`), and the connection entity declares no relationship to anything
(`C-40`).

<!-- anchor: finding-1 -->
## Finding 1 — clause 1 cites DataHub for a deferral DataHub did not make

ADR 0017 clause 1 is right that the ceiling exists and right that DataHub hit it. It is wrong
about the shape of the fix, and the ADR's own conclusion depends on that shape.

Verified at HEAD, not taken from the report:

- `DatasetUrn.createFromUrn` still throws on `key.size() != 3`
  (`li-utils/src/main/javaPegasus/com/linkedin/common/urn/DatasetUrn.java`). The key was never
  widened.
- The instance is folded into the name:
  `name=f"{platform_instance}.{table_name}" if platform_instance else table_name`
  (`metadata-ingestion/scripts/avro_codegen.py:516`, with the same pattern at :460, :560 and :575
  for flows, charts and dashboards).
- The aspect that looks like the answer is not one: `DataPlatformInstance` declares zero
  `@Relationship` annotations (`C-45`, not re-derived here), so instance grouping is a search
  facet and cannot be traversed.

So the sequence was: the key stayed at three, the instance went into the identifier, and every
already-ingested dataset that later gained a platform instance **became a different dataset**.
That is the id migration clause 1 says the binding table lets DryDocs avoid.

**What this changes about the clause.** The ruling — record the ceiling, do not mint the axis —
may well still be right; deferring a migration with no current benefit is defensible on its own
terms. What is not supported is the *reason given*: that a binding table converts the eventual fix
into a configuration change. DataHub had a connection-shaped object available (`dataHubConnection`)
and still could not put the instance there, because identity is not resolvable through
configuration — an identifier either distinguishes two things or it does not. The accurate form of
the clause is that the migration is **deferred**, not **avoided**, and the trigger paragraph at
the end of the ADR already names when it comes due.

<!-- anchor: finding-2 -->
## Finding 2 — the ceiling is in the derived URN, not in `[db]`

DryDocs carries **two** identifiers with different keys, and clause 1 examines only one.

| | Parts | Example |
|---|---|---|
| Committed dataset id | `{origin}@{db}.{schema}.{table}` | `controlm@[db].psgmgr.cm_def_vtab` |
| Derived URN (`source_registry.py:127-135`) | `({carrier},{artifact},prod)` | `urn:drydocs:dataset:(psgmgr,cm_def_vtab,prod)` |

The URN drops the database **and the schema**. Measured live at `main`: 30 dataset rows, 30
distinct URNs — nothing is broken today. But the key is (carrier, bare table name, `prod`), so the
first collision arrives with **a second schema on one carrier holding a same-named table**, and
two carriers are already one table name away from it: `psgmgr` carries three origins (`controlm`,
`hr`, `seal`) and `snowflake` carries two (`catalog`, `snowflake`).

**The comparison the ADR draws is therefore too generous to DryDocs.** DataHub's URN `name` is the
fully qualified native name — verified in the Snowflake connector, which builds it from
`table_name`, `schema_name` and `db_name` together
(`metadata-ingestion/src/datahub/ingestion/source/snowflake/snowflake_utils.py:466-472`). DataHub
before the `platform_instance` work was missing **one** axis. DryDocs's derived URN is missing
**three**: instance, database and schema.

Two consequences worth stating plainly:

1. `[db]` is a redaction inside a string. No code keys on it. The URN is what a loader and the
   graph key on, and the redaction debate has never reached it.
2. The pending grammar work — un-redacting `[db]` and `[schema]` in committed ids — does
   **nothing** for the URN unless `SourceEntry.urn` changes in the same commit. A registry whose
   ids are precise and whose URNs are not is the worse of the two states, because the imprecise
   identifier is the one that gets written into the graph.

<!-- anchor: finding-3 -->
## Finding 3 — clause 3's `${VAR}` is the right shape and the wrong expander

Clause 3 says: "DataHub's recipes write `password: ${MSSQL_PASSWORD}` and expand at load, so the
file is committable and the secret never is. That is the shape adopted here." The shape is right
and the citation is accurate. Two properties of the real expander are not stated, and both matter.

**It resolves from three backends with a precedence order, and the committed file does not say
which one answered.** `docs/secret-resolution.md:53`: *"All backends are checked and values are
merged. If the same secret exists in multiple backends, **DataHub** takes precedence over
**File**, which takes precedence over **Environment**."* DryDocs has one backend today, so this is
a warning rather than a defect: if a second ever arrives, clause 3's "one expansion function, one
error, one enumerable list" needs a fourth item — *one stated precedence* — or the enumerable list
stops telling an operator which value is live.

**It is bash-style, and bash-style includes defaults.** `${VAR:-default}` uses the default when
`VAR` is unset or empty; `${VAR-default}` when unset (`docs/secret-resolution.md:34-41`). There is
also a documented trap: `${DB-PASSWORD}` parses as *"variable `DB`, with default `PASSWORD`"*
(:25-28) — harmless here, since DryDocs variable names use underscores.

The default operator is not harmless. **G81 clause (d) ruled that an unset data root must FAIL
rather than silently relocate**, and clause 3 names G81 (d) as something it makes implementable in
one place instead of seven. Adopting DataHub's expansion syntax verbatim would put the
silent-default behavior back at the syntax level, where the one expansion function cannot see it —
the committed YAML would carry the fallback, not the code. The rider is one sentence: **the
expander substitutes and refuses defaults**; an unset variable is an error naming the variable and
the row that wanted it.

<!-- anchor: finding-4 -->
## Finding 4 — clause 4 is corroborated by a closer precedent, and DataHub also shows its cost

Clause 4 rules for "the Purview shape" — a credential as a first-class named object referenced by
many rows — over OpenMetadata's derived-path shape. DataHub implements the Purview shape too, and
the ADR does not cite it for this.

Verified: `metadata-models/src/main/pegasus/com/linkedin/connection/` contains exactly
`DataHubConnectionDetails.pdl` and `DataHubJsonConnection.pdl`, and a relationship sweep over that
directory returns nothing. The connection is keyed by an opaque id, carries only its details plus a
platform instance, and its upsert input accepts no dataset URN (`C-40`). Identity and access are
separated **by construction in the model, not by convention** — which is the ruling clause 4 makes,
shipped and released.

**And the cost is visible in the same place.** Nothing links a connection to the datasets it
serves. `DataPlatformInstanceProperties` declares no relationship either (`C-67`, not re-derived),
and the research report's open question 9 records that the secret-resolution documentation never
says whether a recipe can reference a connection by URN at all — recipes reference *secrets* by
`${NAME}`, and the connection entity sits beside that path rather than in it.

A profile that nothing references is a profile nothing can audit. That is the defect ADR 0017
opens with — *"a source nobody can enumerate is a source nobody can audit, back up, or move"* — so
the ADR would be adopting the shape and inheriting the hole. The rider: **clause 4 declares the
reference direction as part of the ruling.** The registry row names its profile; a guard fails a
row naming a profile that does not exist, and reports a profile no row names. DataHub's omission is
the argument for writing it down rather than assuming it.

<!-- anchor: finding-5 -->
## Finding 5 — clause 5 is right, and its stronger example is one line away

Clause 5 records fresh-clone-has-no-credential as a property, citing DataHub's shipped
`datahub:datahub` account. That example is real. The better one is the encryption key.

Verified at HEAD, `metadata-service/configuration/src/main/resources/application.yaml:173`:

```
encryptionKey: "#{systemEnvironment['SECRET_SERVICE_ENCRYPTION_KEY'] ?: 'ENCRYPTION_KEY'}"
```

The fallback is the literal string `ENCRYPTION_KEY`. Per the research report (`R-03`/`C-148`, the
surrounding details not re-derived here): HMAC-derived, no salt, no key id, no rotation tooling —
so an installation that never set the variable has been encrypting every stored secret under a
publicly known key, and *correctly setting* the key later is the action that breaks decryption of
everything already stored.

This is the same class as the demo account and a sharper instance of it: a shipped default that
works, that nothing forces anyone to change, and whose correction is itself a breaking change. It
is worth substituting into clause 5 because it answers the objection the demo account invites —
"we would obviously change that" — with a case where the obvious fix is the destructive one.

Clause 5's ruling is unaffected and holds: DryDocs ships no credential, every login on a fresh
clone is refused, and the refusal names the bootstrap script.

<!-- anchor: finding-6 -->
## Finding 6 — the one place DryDocs leads both peers, and it is unenforced

Across the two source reviews, this is the finding no ADR clause covers.

- DataHub has **no normative prohibition** on credentials in an identifier. Two documentation
  sweeps for a rule return nothing prohibitive; the exclusion is *"an accident of API shape, not a
  stated rule"* (`C-33`, not re-derived). The only reserved characters in a dataset name are `(`,
  `)`, `,` and the unit separator — `@ : / = ?` are all legal (`C-35`).
- DataHub has **no shared sanitizer in either language**. The negative sweep re-derived here —
  `grep -rn "removePassword\|stripCredential\|maskPassword\|scrubUrl\|sanitizeUrl\|sanitizeJdbc" --include=*.java .`
  — returns **zero hits** at HEAD. Python has only ad-hoc per-connector helpers.
- OpenLineage, per the third pass, has `JdbcUrlSanitizer` in Java with tests, and nothing in
  Python.

So across both peers there is exactly **one** implementation of the guard and **no** stated rule
anywhere. DryDocs is the inverse: it has the stated rule — the registered-ids rule and the
internal twin, with the discriminator *could someone connect with this string alone?* — and no
enforcement at all.

Two things follow. First, the OpenLineage review's scaffolding item 1 (port those regexes to
Python) is not one option among two; it is the only implementation that exists in either peer, and
the research report says so directly, calling DataHub's side *"net-new code, not a port"*
(`R-09`). Second, the rule itself is worth recording in ADR 0017 the way clause 5 records the
fresh-clone default — as a property this system holds that a later convenience commit could
quietly remove — because it is the one substrate property where the peers are behind.

<!-- anchor: finding-7 -->
## Finding 7 — how DataHub actually registers a connection, and why the editor-first posture is the canonical one

This is the pass the user asked for, and it changes the framing of the whole ADR. **A DataHub
datasource is registered by writing a YAML file in an editor.** The UI is a wrapper over that same
file, not an alternative model.

**The recipe is the registration.** `datahub ingest -c <file>` takes a `.yaml` or `.toml` recipe
with two blocks, `source` (a `type` plus a typed `config`) and `sink` (`docs/cli.md:135-165`). The
shipped Oracle example is exactly a database configuration and nothing more
(`metadata-ingestion/docs/sources/oracle/oracle_recipe.yml`):

```yaml
source:
  type: oracle
  config:
    host_port: localhost:1521
    database: dbname
    username: user
    password: pass
    service_name: svc      # omit database if using this option
```

The Snowflake example alongside it writes `username: "${SNOWFLAKE_USER}"` and
`password: "${SNOWFLAKE_PASS}"` instead. Both shapes are legal; only the second is committable.

**The config block is a pydantic model, and DryDocs already uses the same library.** Every source's
`config` is a `ConfigModel` (`metadata-ingestion/src/datahub/configuration/common.py`) — pydantic
v2, `SecretStr` for credential fields, validation at load. `drydocs_core/config.py` is the same
shape: `Neo4jSettings`, `OracleSettings`, `password: SecretStr`. The difference is not the
technology; it is that DataHub's models are **keyed per source** and DryDocs's are **singletons**
(finding 8).

**The UI does not have its own model.** The entity a UI-created ingestion source writes is
`dataHubIngestionSourceInfo`, and its config record is:

```
config: record DataHubIngestionSourceConfig {
    recipe: string          // "The JSON recipe to use for ingestion"
    version: optional string
    executorId: optional string
    ...
}
```

The recipe is stored as an **opaque string** alongside a schedule and an executor id. So the UI
path is strictly *less* structured than the file path: a committed YAML file gets pydantic
validation, editor tooling and a diff; the UI's copy is a blob in a database. A team that never
opens the UI loses a scheduler and a form, and loses nothing about the model.

**Three mechanisms in that path are worth taking, and one is the enforcement DryDocs is missing.**

1. **`${VAR}` expansion is also where the secret is registered for masking.**
   `metadata-ingestion/src/datahub/masking/bootstrap.py` states the design in its own header:
   *"Config loaders register secrets during `${VAR}` expansion; Pydantic models register `SecretStr`
   fields during validation"* — so a resolved value is entered into a `SecretRegistry`, and a
   logging filter plus an exception hook mask it everywhere thereafter. This is the answer to
   clause 3's "one expansion function": the expander is not only where the value is read, it is the
   only place that can know a value is secret, so it is where the masking obligation is created.
   *(Note this narrows the research report's `C-36`, which reports no shared framework-level
   sanitizer in either language: at HEAD there is no DSN **sanitizer**, but there IS a shared
   Python masking layer — `datahub/masking/` — that the report's sweep terms would not have
   matched.)*
2. **A committed value that starts with `$` is a reference; anything else is a value.** The
   redaction helper carries the rule literally: *"If it is just a variable reference, it is ok to
   show as-is"* — `if value.startswith("$"): return value`, otherwise `********`, over a key
   allow-list (`password`, `token`, `secret`, `connection_string`, `sqlalchemy_uri`, plus
   `_password` / `_token` / `_key` / `_connection_string` suffixes). That is a **write guard
   DryDocs can implement in one test**: in any committed YAML, a field whose key matches the
   credential list must hold a `$`-prefixed reference or nothing. Finding 6 says DryDocs has the
   stated rule and no enforcement; this is the enforcement, and it is twenty lines.
3. **A connection test is a typed report, not a boolean.** `TestableSource.test_connection(config_dict)`
   returns a `TestConnectionReport` carrying `basic_connectivity` and a per-capability
   `CapabilityReport` with `capable`, `failure_reason` and `mitigation_message`
   (`metadata-ingestion/src/datahub/ingestion/api/source.py:522-528, 800`). ADR 0017's opening
   complaint is that `landing-zones --check` "reports a clean run over the rows it knows about and
   says nothing about the rows it does not." The automated half's check IS a connection test, and
   this is the shape it should return — reachable, plus what it could and could not do, plus what
   to do about it.

**So the posture is right and the ADR should say so.** ADR 0017 never states that DryDocs assumes
an operator working in an editor with no UI, and because it never states it, it also never claims
the benefits: the configuration is diffable, reviewable, portable across the two machines by the
same git sync as everything else, and typed by the same library DataHub uses. Recording it turns
an unexamined assumption into a design property — the same treatment clause 5 gives the
fresh-clone default. It also names the two things the operator gives up, so the choice is real:
no scheduler, and no form that validates before you save.

<!-- anchor: finding-8 -->
## Finding 8 — DryDocs has database configuration; it has exactly one of each, and the ADR never says so

The question behind this pass was whether DryDocs has database configuration at all. It does, and
the precise shape is the finding.

| | Declared where | Consumers | Keyed per source? |
|---|---|---|---|
| Neo4j — the **destination** | `Neo4jSettings` (`NEO4J_*`) + `config/dev-environment.yaml` | 8 modules | n/a, there is one graph |
| Oracle — the **source** | `OracleSettings` (`ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_DSN`) | one: `_oracle_adapter` (`drydocs/cli_shared.py:769-782`) | **no** |
| Everything else | `locator:` prose in `config/source-registry.yaml` | none — free text no guard reads | no |

So the destination is configured well and the **source side is a singleton**: one user, one
password, one DSN, for every Oracle extract in the registry. `_oracle_adapter` takes a query and
optional binds — it never takes a source id, so there is no seam where a second Oracle connection
could enter. That is not a missing feature so much as an unstated ceiling, and it is the same
ceiling clause 1 records for identifiers, one layer down: **a second Oracle service behind
`psgmgr` breaks the connection layer before it breaks the id layer.** The ADR's closing trigger
paragraph names that event and attributes it only to identity.

**The committed-map/machine-local-value split the ADR proposes already exists here, for one
system.** `config/dev-environment.yaml` is exactly it: container name, image, volumes, ports,
plugin list — committed, with its own header saying *"Contains NO company data and NO secrets
(names/ports only; passwords live in gitignored .env files, never in a committed file)."* ADR 0017
reaches for `config/data-zones.yaml` as the model for its map/root split, and data-zones is the
right precedent for **filesystem** sources. For a **connection**, `dev-environment.yaml` is the
closer analogue and the stronger argument, because it is the same split already carrying a live
database. The binding table is that file generalized from one destination to N sources.

One consequence worth stating for whoever builds G125: the `.env.example` template is already
organized by system (`NEO4J_*`, then `ORACLE_*`, then `GITHUB_*`), so the variable naming
convention a binding table would need — one prefix per bound system — is established practice
rather than a new invention. What is missing is only that no registry row names its prefix.

<!-- anchor: method-check -->
## Method check — the report's §0 correction does not travel to the third pass

The research report opens by invalidating its own prescribed maturity test: `git tag --contains`
produces false negatives in DataHub, because releases are cut on long-lived branches that are
never merged back, so `v1.7.0` is not an ancestor of master and `v1.6.0.1` is dated nine days
*after* it.

The third pass (OpenLineage) used exactly that test to grade `LineageDatasetFacet` as merged but
unreleased. So the correction has to be checked against that repo rather than assumed either way.
Re-derived on this desktop: in `C:\coding\projects\OpenLineage`,
`git merge-base --is-ancestor 1.52.0 HEAD` returns **true**. Tags there are ancestors of the
mainline, the test is valid, and the OpenLineage release-status findings stand unchanged.

Recorded because a reader moving between the two documents would reasonably assume a method
correction in one applies to both.

<!-- anchor: replica-note -->
## Outside ADR 0017's scope, but the registry's own case

DataHub's model answers a question DryDocs asks constantly and ADR 0017 does not raise: how to
record that one dataset is a **copy** of another on a different platform. That is
`{origin}@{db}.{schema}.{table}` with `authority: ADS`, ten times over on `psgmgr` alone.

DataHub's ruling (`D-04`) is to use the typed lineage edge `Upstream{type=COPY}` — released
2020-05-21, patchable one edge at a time — and never the aliasing mechanism. Its reason is worth
carrying: `Siblings` asserts *"these are the same thing"*, and `SiblingGraphService` **actively
deletes any lineage relationship between two siblings** from the merged read path, which is the
default (`C-58`/`C-59`, the report's own highest-value verification item; not re-derived here).
Using the aliasing mechanism destroys the fact being recorded.

DryDocs today records replica-ness three ways and as no edge: the id shape (`origin != system`),
the `authority: ADS` field, and prose in `notes`. All three are attributes; none is traversable.
Minting a derivation edge is an ontology decision that goes through `docs/RELATIONSHIP_GUIDE.md`
and the HITL gate, so nothing here proposes one. It is inboxed rather than ruled.

<!-- anchor: what-changes -->
## What would change, if the user rules this way

Nothing in this document changes code, and nothing in it has been applied.

| # | Where | Change |
|---|---|---|
| 1 | ADR 0017 clause 1 | Correct the mechanism: `platform_instance` is concatenated into the URN name, not a fourth key part, so DataHub's fix WAS an id migration. Restate the ruling as deferral, not avoidance. |
| 2 | ADR 0017 clause 1 | Name the real ceiling — the derived URN drops db and schema, so DryDocs is three axes short where DataHub was one. Pair any id un-redaction with `SourceEntry.urn`. |
| 3 | ADR 0017 clause 3 | Add the rider: the expander substitutes and REFUSES defaults (G81 (d) at the syntax level), and if a second backend ever exists, one stated precedence. |
| 4 | ADR 0017 clause 4 | Cite `dataHubConnection` as the shipped precedent, and declare the reference direction plus its guard, which DataHub omits. |
| 5 | ADR 0017 clause 5 | Substitute the `ENCRYPTION_KEY` fallback for the demo account as the worked example. |
| 6 | ADR 0017 | Record the registered-ids rule as a held property: both peers lack a normative prohibition, and only one has any implementation. |
| 7 | ADR 0017 | Record the editor-first posture as a design property: no UI, YAML authored in an editor, which is DataHub's own canonical path — with the two things it gives up (a scheduler, a validating form) named. |
| 8 | ADR 0017 | State that source-side database configuration is a SINGLETON today (one Oracle triple, one consumer, no source id) and that the trigger paragraph's "second Oracle service" breaks the connection layer before the id layer. |
| 9 | ADR 0017 clause 2 / G125 | Cite `config/dev-environment.yaml`, not only `config/data-zones.yaml`, as the map/value precedent — it is the same split already carrying a live database. |
| 10 | A guard | The `$`-prefix rule as a committed-YAML write guard: a credential-keyed field holds a reference or nothing. This is the enforcement finding 6 says is missing. |
| 11 | IDEAS | The replica-edge question, for the relationship guide and the HITL gate. |

<!-- anchor: verification -->
## Verification checklist

Each item is a command, so a reader can disagree with evidence rather than with me.

1. `cd C:\coding\projects\datahub && git log -1 --format=%H` — expect `dea0f9c1`, 2026-08-30.
2. `sed -n '46,56p' li-utils/src/main/javaPegasus/com/linkedin/common/urn/DatasetUrn.java` —
   expect `key.size() != 3`.
3. `grep -n 'platform_instance}\.' metadata-ingestion/scripts/avro_codegen.py` — expect the name
   concatenation at :516 (and :460, :560, :575).
4. `grep -n 'def get_dataset_identifier' -A6 metadata-ingestion/src/datahub/ingestion/source/snowflake/snowflake_utils.py`
   — expect `table_name`, `schema_name` and `db_name` combined.
5. `grep -rn "removePassword\|stripCredential\|maskPassword\|scrubUrl\|sanitizeUrl\|sanitizeJdbc" --include=*.java .`
   — expect zero hits.
6. `grep -n encryptionKey metadata-service/configuration/src/main/resources/application.yaml` —
   expect the `?: 'ENCRYPTION_KEY'` fallback at :173.
7. `sed -n '25,55p' docs/secret-resolution.md` — expect the hyphen caution, the bash default table
   and the DataHub > File > Environment precedence line.
8. `ls metadata-models/src/main/pegasus/com/linkedin/connection/` — expect two files, and a
   relationship sweep of that directory to return nothing.
9. `cd C:\coding\projects\OpenLineage && git merge-base --is-ancestor 1.52.0 HEAD` — expect exit 0,
   which is what keeps the third pass's release grades valid.
10. In DryDocs at `main`: build a `SourceRegistry.from_yaml()`, take `.urn` over every
    `source-registry` row, and expect 30 rows, 30 distinct URNs, none carrying a database or
    schema segment.
11. `cat metadata-ingestion/docs/sources/oracle/oracle_recipe.yml` — expect `host_port`,
    `database`, `username`, `password`, `service_name` under a typed `source.config` block, and
    the Snowflake recipe beside it to use `${SNOWFLAKE_USER}` / `${SNOWFLAKE_PASS}` instead.
12. `cat metadata-models/src/main/pegasus/com/linkedin/ingestion/DataHubIngestionSourceInfo.pdl` —
    expect `recipe: string`, the UI's copy of the same document.
13. `sed -n '1,15p' metadata-ingestion/src/datahub/masking/bootstrap.py` — expect the two-line
    architecture note: config loaders register secrets during `${VAR}` expansion, pydantic models
    register `SecretStr` fields during validation.
14. `grep -n 'startswith("\$")' -B4 metadata-ingestion/src/datahub/configuration/common.py` —
    expect the reference-vs-value rule, above `REDACT_KEYS` / `REDACT_SUFFIXES`.
15. `sed -n '520,528p;798,802p' metadata-ingestion/src/datahub/ingestion/api/source.py` — expect
    `TestConnectionReport` and `TestableSource.test_connection`.
16. In DryDocs: `grep -rn "load_settings" --include=*.py .` — expect exactly one consumer of the
    Oracle half, `_oracle_adapter` at `drydocs/cli_shared.py:769-782`, taking a query and no
    source id.
