# Technical Design — source registration (five-axis descriptors, synthetic stand-ins, DuckDB and DataHub)

<!-- anchor: front-matter -->
**Status:** DESCRIPTIVE — documents the built proof of concept as of **Rev 3, 2026-09-09**,
authored against commit `de0eeb6f`, which was landed onto `main` linearly rather than merged,
together with the two guard fixes described under "QA & tests". Nothing here is prescriptive:
every mechanism described is in the tree and covered by a test. Two of those tests were red while
the work sat on its branch and both are fixed here; "QA & tests" records what each one was, and why
one of them could not fail on the machine that wrote it. ·
**Branch retired 2026-09-09:** `feat/source-registration-poc` (tip `de0eeb6f`) was deleted locally and on origin after the landing; the scoped diff against `main` over the five PoC paths differed only in `tests/unit/test_synthetic_sources.py`, where `main` carries the later guard fix. `fcc3c8bb` is the landing of record. ·
**Classification:** Internal-Public — mechanism only. Every value the generator emits is
synthetic, and no connection coordinate appears in this document or in the files it describes. ·
**Audience:** engineers working on `drydocs_core/source_descriptors.py` or
`drydocs/source_registration/`, and the SME deciding whether the descriptor axes are the right
five and whether a catalog belongs in the picture at all. ·
**Companion:** `docs/decisions/0017-source-binding-substrate.md` (ACCEPTED 2026-08-30; the question this
proof of concept answers a piece of); `docs/design/datahub-substrate-review.md` Rev 2 and
`docs/design/catalog-substrate-review.md` (the reading behind the DataHub choice);
`docs/design/controlm-ingestion-tdd.md` (the pipeline whose landing zones receive the stand-ins);
`config/datahub/README.md` (the operator runbook for the two recipes).

Worked example throughout: the dataset `controlm@[db].psgmgr.cm_def_vtab`. The registry says it
is an automated, database-carried replica in the technology layer. The descriptor turns that into
five axis values; the generator writes `controlm_folders.csv` as its stand-in; the bundle drops
that file into a CSV mirror under the data root; DuckDB loads it as a table; and DataHub registers
it as a dataset carrying those five values as both properties and tags.

> **Read-me-first.** This is a registration surface, not a load. Nothing here writes the graph,
> opens a database connection, or reaches the network. It reads two committed YAML files, writes
> CSV text, and emits one JSON file that an operator-side tool consumes in its own environment.

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Give every registered dataset a machine-readable registration descriptor, and prove
the descriptor is worth having by driving three consumers from it: a synthetic stand-in for each
source, a project-local analytical copy, and a catalog registration.

**The problem it answers.** The source registry says what a source is, and the bindings say how to
reach its carrier. Neither says how a source should be *registered* as a catalog asset, and neither
gives a way to exercise the loaders without a production capture. Both gaps were being filled by
prose a reader had to interpret.

**In scope.**
- `config/source-descriptors.yaml` — the five closed axes, their derivation from the registry, the
  per-dataset overrides, the synthetic plan and the DataHub emission settings.
- `drydocs_core/source_descriptors.py` — the reader that derives, overrides, and refuses.
- `drydocs/source_registration/` — the seeded generator, the tracked bundle and its extraction, the
  optional DuckDB load, and the DataHub emitter.
- `scripts/build_synthetic_sources.py` — the one command that drives all four steps.
- `config/datahub/` — two operator-side recipes for the DataHub command-line tool.

**Out of scope.** Any graph write; any real connection (the bindings own that, ADR 0017); a
production DataHub deployment (the recipes target a local file-backed store); lineage emission of
any kind; and the decision on whether a catalog product is adopted at all, which stays with
ADR 0017 and its gate.

<!-- anchor: context-frame -->
## Where this sits — the four-layer frame

The descriptor is **layer 1, taxonomy**. It classifies a dataset on five closed axes and asserts
no relationship between anything. That placement is deliberate: an axis value says what category
a source falls into, and adding a value to an axis is a classification change, not an ontology
change. Nothing here proposes an edge, so nothing here needs the relationship vocabulary.

Upstream neighbors are `config/source-registry.yaml` (the system and dataset rows, ruled at gate
`source-registry-v2`) and `config/source-bindings.yaml`, read only for the presence of a `binding:`
key and never for its contents. Extraction adds one more: the landing-zone accessor, which resolves
the registry's own acquisition rows against the data root. Downstream neighbors are the loaders,
which read the extracted CSVs in SOURCE mode exactly as they would read a real drop, and the
operator's DataHub environment.

Layer 3 is untouched. The graph is neither read nor written at any point in this design.

<!-- anchor: definitions -->
## Definitions, acronyms & references

- **Descriptor** — the five axis values for one dataset, plus the identity facts an emitter needs
  beside them (system, URN, whether the dataset is derived, whether it is confirmed).
- **Axis** — a named, closed list of permitted values. The five are `acquisition`, `format`,
  `authority`, `layer` and `access`.
- **Derivation** — the rule that computes an axis value from the registry rows. Written down so a
  registry edit moves the descriptor without a second edit here.
- **Override** — a per-dataset value that replaces the derivation. The only way to disagree with a
  derivation, and every override is itself checked against its axis.
- **Registry-home dataset** — a dataset whose row lives in the source registry. The document ledger
  shares the registry's identifier space but carries no system row, so its entries have no carrier
  to register against and are excluded here.
- **Stand-in** — a generated CSV that occupies the place of a real capture. Every row carries
  `record_origin` set to `sample`.
- **Bundle** — the single tracked gzip file holding every stand-in as text.
- **Landing zone** — the directory a loader reads a manual drop from, under `DRYDOCS_DATA_ROOT`.
- **Mirror** — the substitute placement for a database-carried dataset, which has no drop directory.
- **MCP file** — the metadata-change-proposal file format, DataHub's documented input to its file
  source and its local import path.
- **DataHub Lite** — DataHub's file-backed local store, itself a DuckDB database. No server is
  involved anywhere in this design.
- **ADR 0017** — "Source binding substrate", ACCEPTED 2026-08-30 (corrected 2026-09-09; Rev 3 read it as PROPOSED). It rules the binding substrate; the catalog question below stays open.

<!-- anchor: design-summary -->
## Design summary

```
 config/source-registry.yaml        config/source-descriptors.yaml
   systems (19) + datasets (30)       axes . authority map . overrides
              |                       synthetic plan . datahub settings
              +-----------+-------------------+
                          v
        drydocs_core/source_descriptors.py   (derive -> override -> refuse)
                          |  30 descriptors, five axis values each
       +------------------+-------------------------------+
       v                  v                               v
  synthetic.py       datahub_emit.py                 (any future reader)
  16 CSV tables      MCP file: 19 containers,
       |             30 datasets, tags, schemas
       v                  |
  bundle.py  -->  drydocs/data/samples/synthetic-sources.json.gz  (tracked, 4076 bytes)
       | extract
       v
  DRYDOCS_DATA_ROOT/<landing zone>/*.csv        --> the loaders, in SOURCE mode
  DRYDOCS_DATA_ROOT/psgmgr-mirror/*.csv
       | duckdb_load.py (optional)
       v
  DRYDOCS_DATA_ROOT/synthetic/drydocs-synthetic.duckdb   --> the DataHub profiler recipe
```

One config file drives everything. The reader turns the registry into 30 descriptors. Three
consumers read those descriptors and nothing else: a generator that writes CSV text, a packer that
puts the text in one tracked file and extracts it where loaders look, and an emitter that writes a
catalog registration. Each output is deterministic, and each has a test that says so.

<!-- anchor: detailed-design -->
## Detailed design

### The five axes and how a value is decided

Each axis is a closed list declared in `config/source-descriptors.yaml`:

| Axis | Values | What it answers |
|---|---|---|
| `acquisition` | `manual`, `automated` | Does a person put the data there, or does a job? |
| `format` | `csv`, `ascii`, `json`, `archive`, `db` | What shape arrives? |
| `authority` | `primary`, `replica` | Is this the system of record, or a copy? |
| `layer` | `human`, `business`, `data`, `technology` | What kind of subject does it describe? |
| `access` | `fid`, `human`, `repo` | Which credential class reads it? |

A value is decided in three steps, in this order. **Derive** from the registry rows. **Override** if
the dataset names that axis in the override table. **Refuse** if the result is not on its axis, if
the axis is not one of the five, or if an override names a dataset the registry does not have. The
reader never guesses and never falls back to a default it invented.

The derivations are literal. `acquisition` is the dataset's acquisition mode, defaulting to
`automated`. `format` is the declared format for a manual row and the transport for an automated
one, so a database-carried dataset lands on `db`. `authority` maps the registry's own vocabulary
through a small table: a system of record becomes `primary`, an authorized distribution source
becomes `replica`, and a derived store becomes `replica` because it copies. `layer` is the system
row's layer. `access` asks which credential class reads the dataset: a system with a binding is read
by a functional identity, a repository-based zone is read by the checkout itself, an unbound manual
drop is read by a person, and an unbound automated dataset is still read by a service identity
rather than by a person.

Two overrides exist, both on `layer`, both for the same reason: the dataset's subject is people
whatever carrier holds it. One is a phone-number extract that the derivation would otherwise call
`data`, because its carrier is a database. The other is the team report.

The override table is validated when the reader is constructed, not on first use, so a config that
disagrees with the registry fails immediately rather than on whichever dataset happens to be asked
for first.

**The sixth axis, `wired` (added 2026-09-09).** Two gates signed in one sitting
(`registry-wiring-readiness` 18/18, `source-descriptor-axes` 13/13) ruled that whether the pipeline
that reads a dataset is BUILT is a second fact the registry's `confirmed` flag had been carrying in
comments, and that its home is here, as a sixth axis: `wired`, `true` or `false`, DECLARED per
dataset in a `wired:` block keyed by id and never derived - the core package cannot see loader
registration, and a declared value with a written reason is the smaller mechanism. Every
registry-home dataset must answer; a `false` carries a reason of at least forty characters; a
missing entry, a bare false or a short reason is refused when the reader is constructed. The value
is per side at the port (`PORT-MANIFEST.yaml` `per_side_fields`), because what is built on one tree
says nothing about the other. `require_confirmed()` refuses unless both `confirmed` and `wired`
hold and says which failed; the load map's wiring cross and the DataHub emission read the
declaration, and `confirmed` on a catalog asset means the semantic ruling only. The build is CFG13.

### Which datasets get a descriptor

Registry-home datasets only, in registry order. The document ledger's entries share the identifier
space but have no system row, so there is no carrier to register against; they are cataloged by the
document ledger instead. A test pins that exclusion so it stays a decision rather than an accident.

### The synthetic generator

The generator is a pure function of the config and the seed. A single seeded random number generator
decides the few genuine choices; everything else is arithmetic over fixed name lists. It produces 16
tables covering 10 of the 30 datasets, and it returns CSV **text** rather than files, so the same
bytes reach the tracked bundle and the loader's drop directory.

Three fences keep a fixture from ever passing for a capture:

- Every row carries `record_origin` set to `sample`, added by the one helper that builds every
  table, so a new table cannot forget it.
- Application identifiers stay inside the reserved block already used by the existing sample
  generator, and person identifiers are a letter plus six digits in a block that resolves to
  nothing.
- Every mail address ends in the synthetic domain, which cannot be registered.

The theme is the Neo4j Matrix sample graph: crew names as people, ships as product lines, programs
as products and applications. Names are borrowed from a film, and no value describes anything real.
The theme is not decoration. A reviewer who sees a hovercraft in a folder name knows immediately
that the row is generated, which a plausible-looking corporate name would not tell them.

The generator refuses to run past a mismatch. If the config plans a file the generator has no block
for, it raises rather than quietly emitting a short set.

### The bundle and its extraction

Everything is packed into one gzip file at `drydocs/data/samples/synthetic-sources.json.gz`, tracked
in the repository at 4076 bytes. One tracked binary is one publish-boundary decision instead of a
dozen. The JSON inside it is stable by construction: sorted and compact, with a gzip header that
carries a zero timestamp and no filename, so two runs over one config produce the same payload and
any change to it means the generator or the config changed.

**The compressed bytes are a different matter, and this is where the design is currently wrong.**
The parity test compares the committed file's raw bytes against a fresh compression, and gzip output
is not portable: the same input at the same compression level produces a different stream under a
different zlib build. The committed file was written on Windows, whose interpreter links zlib-ng,
and it fails that comparison on the Linux runners. The evidence that this is compression and not
content is in the failure itself — the gzip trailer, which carries the checksum and the uncompressed
size of the payload, is identical on both sides, so both platforms produced the same 20375 bytes of
JSON and disagreed only on how to deflate it.

The fix is to compare the payload rather than the stream: decompress and compare the JSON, or track
the artifact uncompressed. It is a small change and it belongs to whoever holds the branch, so it is
recorded here rather than made. Until then the parity guard is red in CI on every platform that is
not the one that wrote the file, which is every platform CI runs.

Extraction never writes into the repository tree. Each dataset's target is decided from its
placement:

- A dataset with a manual landing zone is written to that zone under the data root.
- A zone declared as repository-based is redirected under a `repo/` prefix inside the data root, so
  a fixture cannot land in a tracked directory.
- A database-carried dataset has no drop directory, so it is written to a CSV mirror under the data
  root instead.

Files are written with newline translation disabled, so the bundled line endings survive on every
platform and the loaders see the same bytes the generator produced.

### The DuckDB load

Optional, and imported lazily. DuckDB is not a repository dependency: the import happens inside the
function, the driving script probes for the package and prints a skip line when it is absent, and
the test skips on the same condition. A tree without the package loses this one step and nothing
else.

Every column is read as text. Type inference is the single thing that would make two loads of one
CSV differ, and saying what the values look like is the profiler's job rather than the loader's.

Two extra tables make the file self-describing. One holds a row per loaded table with that dataset's
five axis values, its identifier, its URN and its placement. The other holds the seed, the theme and
the table count. Both are derived from the descriptors, and neither is typed by hand.

### The DataHub emission

The repository imports nothing from DataHub. The file-sink JSON is a documented, permissively
licensed format, and writing it directly keeps DataHub an operator-side tool installed in its own
environment. That is the whole coupling: one JSON file.

Per system, one container carrying the row's name, layer, classification and binding presence, its
platform, a subtype marking it a source system, and a status. Per dataset, a properties aspect whose
custom properties are the five axis values plus the DryDocs identifier, URN, system, and the
confirmed and derived flags; a pointer to its container; its platform; a subtype chosen from the
format; one tag per axis value plus a synthetic tag when a stand-in exists; a status; and, when a
stand-in exists, a schema built from the generated CSV headers with every field typed as string
because the files are text. Then one tag entity per tag used, each carrying a description that
spells the axis value out.

Determinism again: systems, then datasets, then tags, each in identifier order; a fixed observation
timestamp read from the config rather than from the clock; and the JSON written sorted. Two runs
over one config produce one file.

The container identifier is a hash of a fixed string and the system identifier. The dataset name
replaces every character outside a safe set, because the DryDocs identifier grammar contains
brackets and an at-sign that a URN cannot carry. The true identifier rides in the custom properties,
so nothing is lost.

### The two recipes

Both are operator-side, and both target a local file-backed store, so no server exists in this
design. The first imports the emitted file and registers the systems as containers and the datasets
as assets. The second points DataHub's own profiler at the synthetic DuckDB file and writes row
counts, null and distinct counts, minimum and maximum values, and sample values into the same store.

Every path in a recipe is relative to the data root, and that is a constraint rather than a
preference: DataHub's file source parses its path as a URL, so an absolute Windows path is read as a
one-letter scheme and refused.

The two sets of dataset identifiers differ on purpose. The registration describes the source; the
profile describes the synthetic copy. Collapsing them would claim a profile of production data that
nobody has measured.

<!-- anchor: design-data-mapping -->
### Source → column-level field mapping

**N/A — no ingestion.** This design writes no graph and maps no source column to a node or edge
property. The column-level mapping for the datasets involved lives with the loaders that read them,
in the per-source ledgers under `config/source-mappings/` and in
`docs/design/controlm-ingestion-tdd.md`.

What this design does map is a *registry row* to a *descriptor*, and that mapping is the derivation
table in the detailed design above. The one place a column appears is the schema aspect, which is
built from the generated CSV headers rather than authored.

<!-- anchor: classification-security -->
## Classification & security

Everything introduced here is **Internal-Public**. The descriptor config carries a classification
header and holds axis vocabulary, derivation rules and two overrides. No connection coordinate
appears in it: the `access` axis names a credential *class*, never a credential, and the reader
consults the bindings only for the presence of a binding key.

The generated data is synthetic under three enforced fences, described in the detailed design and
pinned by a test: the `record_origin` marker on every row, identifiers confined to the reserved
blocks, and addresses in a domain that cannot be registered. The marker is the important one. It
makes the fixture self-declaring inside any store it reaches, including the DuckDB file and the
catalog, so a row cannot be mistaken for a capture after it leaves this repository.

The tracked bundle sits under an existing never-port row, which is the correct disposition rather
than an oversight: the bundle is generated from a committed config, so a consumer regenerates it
with one command rather than receiving it. Every test that reads the bundle skips when it is absent,
so a tree without it reports "not tested" and never a failure.

Two port-manifest rows were added, both placed above the general configuration default so they win
on first match. The descriptor config is per-entry from day one, because a consumer's own datasets
need their own override and synthetic entries and a wholesale copy would drop them. The recipes are
producer-owned, because a consumer pointing them at a real deployment changes only the destination,
and does that in its own overlay.

<!-- anchor: qa-tests -->
## QA & tests

Two test files, and each one pins a property rather than a snapshot.

**Descriptors.** The config carries its declared schema header. Every registry dataset resolves to a
descriptor and every value is on its axis. Document-ledger entries are excluded. The derivations and
both overrides produce the expected values. Three refusals are exercised: a value off its axis, an
axis that does not exist, and an override for a dataset the registry does not have. The synthetic
plan names only registered datasets. The platform map falls back to its default for an unlisted
system.

**Synthetic sources and emission.** The generator is deterministic across two runs. It covers every
planned file exactly, with no extras and no gaps. Every row carries the sample marker. Every
identifier stays inside its fence. Packing is byte-stable. The committed bundle matches what the
generator produces right now, which is the guard that catches a config change shipped without a
rebuild. Extraction lands each file in the right zone, including the repository redirect and the
mirror. The DuckDB load runs when the package is importable and skips when it is not. Dataset names
are safe for a URN and unique. The emitted file registers every system and every dataset. Emission
is deterministic.

The skip behavior was verified rather than assumed. With the bundle moved aside, the file reports 8
passed and 3 skipped. A consumer tree has no data, and the verdict there must be "not tested".

The two recipes were run once on this desktop, against the local file-backed store. The import
produced 283 events, and the profiler produced 137 events including 18 dataset profiles. That is a
one-time operator verification, not an automated test, and it is recorded as such.

The usual gates apply and were run: the unit suite, the root import, and the module-boundary test,
which is default-deny and so required the new prefix and map rows in the same commit.

**Two guards were red while the work sat on its branch, and both are fixed at landing.** They are
worth recording because one of them is a lesson about where a test can be measured, not about the
code it tests.

The **identity-header guard** rejected both recipe files for the same three missing keys: `schema`,
`classification` and `updated`. The guard was right that they lacked the block and wrong that they
could carry it. DataHub parses a recipe with a model that declares `extra="forbid"`, so the three
keys would not be ignored — the recipe would stop parsing and the file would stop working. That is
the same situation the map already records for the Compose file, and the recipes are now classed the
same way, as somebody else's schema, with the verification written beside the entry. Their
provenance rides in each recipe's header comment and in the directory's README instead.

The **bundle parity guard** failed only in CI, and could not fail on the machine that wrote the
bundle. It compared compressed bytes, and gzip output is not portable across zlib builds. The fix is
to compare the decompressed payload, which is the thing the test was always about. The gzip artifact
and its size are unchanged. One consequence is worth knowing: two machines can now hold
byte-different bundles that both pass, so a rebuild elsewhere can show as a modified file in `git
status` even when the content is identical. Tracking the payload uncompressed would remove that too,
at a cost of about 16 KB, and remains available if the churn becomes annoying.

This is also the clearest argument in this design for reading a failure before believing a green
local run. The local suite reported one failure and CI reported two, and the extra one was the more
interesting of the pair.

<!-- anchor: hitl-gate -->
## HITL gate & open questions

**No gate is claimed and no gate is due.** Nothing here proposes a relationship type, assigns
meaning to an edge, or writes the graph, so the ontology gate has no subject. The two enforcement
matrix rows added for these surfaces carry no gate reference for the same reason.

Three questions are genuinely open, and they belong to the SME rather than to a later commit.

1. **Are these the right five axes?** They were chosen because each one is already implied by a
   registry field and each one changes what an operator does. A sixth axis, or a different cut of
   `access`, is a reasonable disagreement. It would be cheap to make now and expensive later, once
   values are tagged in a catalog.
2. **Does a catalog get adopted at all?** ADR 0017 is ACCEPTED (2026-08-30) for the BINDING substrate and leaves the catalog product open.
   This proof of concept deliberately proves the *shape* — a descriptor drives a registration — with
   a local file-backed store and no server, so the larger answer stays open.
3. **Should the axis values ever reach the graph?** They are taxonomy, so they could be node
   properties. Nothing here does that, and doing it would be an ontology decision routed through the
   gate in the normal way.

One finding is worth recording because it closes a line of inquiry. OpenLineage was checked for the
profiling job and has no profiler; its run events carry schema and lineage facets only. Profiling
therefore stays with DataHub, and that is a fact about the two products rather than a preference.

<!-- anchor: traceability-matrix -->
## Requirements traceability matrix

| Requirement | Design section | Component | Test / verify | Status |
|---|---|---|---|---|
| Every registry-home dataset carries five axis values, each drawn from a closed list | detailed-design | drydocs-core | `test_source_descriptors.py` — every dataset on axis | done |
| An axis value is derived from the registry, so a registry edit moves it without a second edit | detailed-design | drydocs-core | `test_source_descriptors.py` — derivations and overrides | done |
| An override is the only way to disagree with a derivation, and is itself checked | detailed-design | drydocs-core | `test_source_descriptors.py` — override cases | done |
| An off-axis value, an unknown axis or an unknown dataset is refused, never guessed | detailed-design | drydocs-core | `test_source_descriptors.py` — three refusal cases | done |
| Document-ledger entries are excluded, having no carrier to register against | detailed-design | drydocs-core | `test_source_descriptors.py` — ledger exclusion | done |
| Generated data is a pure function of config and seed | detailed-design | drydocs-load | `test_synthetic_sources.py` — determinism | done |
| Every planned file is generated exactly once, with no extras and no gaps | detailed-design | drydocs-load | `test_synthetic_sources.py` — plan coverage | done |
| A generated row can never pass for a capture | classification-security | drydocs-load | `test_synthetic_sources.py` — sample marker, identifier fences | done |
| The bundle payload is stable, and packing is repeatable within one build | detailed-design | drydocs-load | `test_synthetic_sources.py` — pack stability | done |
| The tracked bundle matches the generator on any platform | detailed-design | drydocs-load | `test_synthetic_sources.py` — bundle parity, compared as decompressed payload | done |
| Extraction lands each file in the zone its loader reads, and never in the repository tree | detailed-design | drydocs-load | `test_synthetic_sources.py` — extraction targets | done |
| A tree without the bundle reports "not tested", never a failure | qa-tests | drydocs-load | measured: 8 passed / 3 skipped with the bundle moved aside | done |
| DuckDB is optional, and its absence costs one step only | detailed-design | drydocs-load | `test_synthetic_sources.py` — load test skips on absence | done |
| Every system and every dataset is registered as a catalog asset carrying the five axes | detailed-design | drydocs-load | `test_synthetic_sources.py` — emission coverage | done |
| A DryDocs identifier survives into the catalog despite a grammar a URN cannot carry | detailed-design | drydocs-load | `test_synthetic_sources.py` — names urn-safe and unique | done |
| Two runs over one config emit one file | detailed-design | drydocs-load | `test_synthetic_sources.py` — emission determinism | done |
| The new module is classified, mapped and port-dispositioned in the same commit | classification-security | drydocs-core, drydocs-load | `test_module_boundary.py`; port-manifest rows; matrix re-render | done |
| The recipes run end to end against a local store | qa-tests | operator-side | one run on this desktop: 283 import events, 137 profile events, 18 profiles | done |
| Every tracked YAML is classified for the identity header, carrying it or exempt with a reason | qa-tests | drydocs-load | `test_config_identity_header.py` — the recipes classed as somebody else's schema | done |
| The five axes are the right five | hitl-gate | — | SME question, open | open |
| A catalog product is adopted | hitl-gate | — | ADR 0017 ACCEPTED 2026-08-30; catalog left open | open |

<!-- anchor: decisions-discussions -->
## Decisions & discussions

**Why closed axes rather than a description field.** A prose field is read by a person and
interpreted differently each time. A closed axis is read by a consumer and refused when wrong. The
emitter, the generator and the tests all read axis values, and none of them contains a rule for
interpreting English.

**Why derivation first and override second.** The alternative is to write all 150 values by hand,
which would be correct once and stale after the first registry edit. Derivation makes the registry
the single place a fact is stated. The override table is short enough to read in one screen, and
each entry says why it disagrees.

**Why one tracked bundle rather than loose fixture files.** The samples directory is ignored, and
its tracked fixtures are grandfathered. Adding a dozen tracked CSVs would be a dozen
publish-boundary decisions; one file is one. It also makes the parity test possible, because a
single artifact can be compared against a fresh generation in one line.

**Why DataHub is not a dependency.** The file format is documented and permissively licensed, and
the tool is an operator's, installed in its own environment. Importing the package would put a large
dependency tree behind a step that writes one JSON file. The cost of the choice is that the format
is a contract this repository restates rather than imports, and the emission tests are what hold it.

**Why a local file-backed store rather than a server.** The question this proof of concept answers
is whether the descriptor is worth having, and a server would not change that answer. It would only
change the cost of reaching it.

**Alternative weighed and rejected: emit lineage instead.** OpenLineage was read for the profiling
job and carries no profiler. Registration and profiling are what a source needs first. Lineage is a
separate question, and it belongs with the ingestion pipeline that already knows the edges.

<!-- anchor: appendices -->
## Appendices

**A. The command.** One script drives every step, and reads the config for all of them.

```
python scripts/build_synthetic_sources.py --bundle
python scripts/build_synthetic_sources.py --extract [--out-root DIR]
python scripts/build_synthetic_sources.py --extract --duckdb
python scripts/build_synthetic_sources.py --datahub-json PATH
```

**B. What the branch changed.** One commit, nineteen files.

| Area | Files |
|---|---|
| Config | `config/source-descriptors.yaml`; `config/datahub/` (two recipes and a README) |
| Core | `drydocs_core/source_descriptors.py`; `drydocs_core/component_map.py` |
| Load | `drydocs/source_registration/` (generator, bundle, DuckDB load, emitter); `scripts/build_synthetic_sources.py` |
| Data | `drydocs/data/samples/synthetic-sources.json.gz` |
| Tests | `tests/unit/test_source_descriptors.py`; `tests/unit/test_synthetic_sources.py` |
| Governance | `MODULE_MAP.md`; `PORT-MANIFEST.yaml`; `scripts/render_enforcement_matrix.py` and the re-rendered matrix |

**C. Counts.**

| Thing | Count |
|---|---|
| Systems in the registry | 19 |
| Datasets in the registry | 30 |
| Datasets with a stand-in | 10 |
| Generated tables | 16 |
| Bundle size, bytes | 4076 |
