# FCDO ontology alignment plan

**Classification: Internal-Confidential** (names the internal org and its internal
systems). Drafted 2026-07-31 from the capture in this directory. Scope rule set by the
user: **align our ontology to theirs for what we have planned — do not add what we
won't use.**

## Verdict

FCDO's stack is pure RDF (SKOS+DCMI taxonomies, narrow RDFS/OWL + SHACL ontologies,
PROV-O + OpenLineage provenance, `jpmv:` namespace, Data Publishing Council
governance). DryDocs is **already structurally aligned on everything that matters**:
their Council-approved ETL model (Jobs/Runs = `prov:Activity`, Dataset =
`dcat:Dataset`) is exactly how `relationship_vocabulary.yaml` already classifies
`ControlMJob`, `JobRun`, and the planned `DataAsset`. Alignment work is therefore
**property-name and enum alignment on planned items plus a recorded crosswalk** — not
a remodel. Their standard has **no vocabulary** for scheduling, conditions, folders,
run-state escalation, or sensitivity classification — our local terms have nothing to
conform to and stay as-is. (Their own captured AI review session reached the same
verdict: complementary, not competing — TRANSCRIPT-1 §Part 2.)

## Their frameworks, one line each (what touches us)

| Framework | Status | Core |
|---|---|---|
| Provenance | **Council-approved Feb 2025** | PROV-O required edges; ETL **must** be OpenLineage readable as PROV: Job (`prov:Activity`; `jobname`/`sourceCodeLocation`/`sourceCode`), Run (`prov:Activity`; `runuuid`/`nominalTime`/`parent`/`errorMessage`; events START + COMPLETE/FAIL/ABORT), Dataset (`dcat:Dataset`) |
| Taxonomy | Approved | SKOS profile — every concept: `prefLabel` (lang-tagged), `inScheme`, `dcterms:created/creator/identifier`, `skos:definition`; mapping via `broadMatch/narrowMatch/closeMatch/exactMatch` |
| Data Mapping | Draft Jul 2026 | `MappingSet`/`Mapping` ⊑ `prov:Activity`; `jpmv:mappingConfidence` (0–1, for AI-generated mappings); `adms:status` Proposed→Approved/Rejected→Deprecated→Retired; `jpmv:NoMapping` sentinel; semantic rels Realizes/Represents/WasDerivedFrom |
| Schema Metadata | Approved | SHACL `TableShape`/`ColumnShape` with `precision`/`scale`/`length`/`isNullable`; ANSI SQL datatype vocabulary; `jpmv:mapsToType` datatype crosswalk |
| People & Orgs | v0.1.1 draft | W3C ORG + schema.org; `Employment` ⊑ `org:Membership`; `jpmv:BusinessUnit` ⊑ `org:OrganizationalUnit`; `jpmv:sid`; "ownership is a relationship, never an `owns` predicate" |
| Data Authority | Partial capture | ADS/SOC/SOR designations on `dcat:DataSet` |
| Identifiers (JDI) | Council-approved Mar 2025 | URL identifiers `https://<lob>.data.jpmorgan/path/id?version=x` |
| Ontology Builder (tool) | Agent skill | **Structural** profiler (DDL/CSV/XSD → RDFS/OWL/SHACL/SKOS + `design-decisions.md`); does **no data profiling** (no counts/nulls/grain/joins) |

## Already aligned — no action

- PROV backbone: our 9-row matrix uses their required predicates; every row we use
  appears in their PROV-DM cross-reference appendix.
- W3C ORG: our Membership/Role n-ary = their Employment pattern; CatalogLOB /
  BusinessSegment / DevTeam classing matches their BusinessUnit / FormalOrganization /
  OrganizationalUnit choices.
- Ownership-as-relationship: our `WAS_ATTRIBUTED_TO` discipline is their stated
  architecture principle verbatim.
- SKOS `closeMatch` + `confidence` on `RECONCILES_TO` matches their taxonomy mapping
  properties and `jpmv:mappingConfidence` in spirit.
- HITL machinery: our proposed→confirmed→applied lifecycle is more mature than their
  `adms:status` + design-decisions log (their own session's conclusion).
- Upper-ontology bridging: our `SUBCLASS_OF`/`MAPS_TO` meta-graph is their recommended
  `rdfs:subClassOf`/`subPropertyOf` pattern in property-graph form.

## Phase 0 — housekeeping (DONE with this commit)

1. Transcripts moved from repo root to `internal/fcdo-reference/` (publish-boundary
   fix — they carry employee names + internal URLs).
2. Registered as pipeline source `fcdo-frameworks` (`config/source-registry.yaml`,
   `kind: docs`, `confirmed: false`) and doc corpus (`config/doc-source-registry.yaml`,
   `connector: confluence`, T4, `refresh: on-demand`) so the docmeta pipeline can
   scrape the live pages company-side; page-ID target list in `README.md` here.

## Phase 1 — the FCDO crosswalk (the core deliverable)

Crosswalk entries mapping DryDocs terms ↔ FCDO terms, same mechanism as the
AutoSys/Airflow orchestrator crosswalks, through the normal HITL gate. The committed
crosswalk stays **mechanism-only** (standard terms, no internal URLs/names — the
`jpmv:` CURIEs themselves are the payload). Highest-value rows:

| DryDocs | FCDO | Note |
|---|---|---|
| `ControlMJob` (Activity) | OpenLineage Job (`prov:Activity`) | type-identical today |
| `JobRun`/`ControlMJobRun` (Activity) | OpenLineage Run | + Phase 2 item 1 |
| `DataAsset` (`dcat:Dataset`) | Dataset (`dcat:Dataset`) | identical |
| `READS_FROM`/`WRITES_TO` (planned) | `prov:used` / `prov:wasGeneratedBy` | theirs hang I/O on the *Run*, ours on the definition — record both grains |
| `WAS_GENERATED_BY` loader envelope | their "metadata envelope" pattern | equivalence note |
| vocab/map lifecycle states | `adms:status` concepts | documentation-level only (planned≈Proposed, active≈Approved…); do NOT change our machinery |
| `SUBCLASS_OF`/`MAPS_TO` meta-graph | `rdfs:subClassOf`/`subPropertyOf` bridging | already equivalent |
| `RECONCILES_TO {confidence}` | `skos:closeMatch` + `jpmv:mappingConfidence` | property-name note |

## Phase 2 — targeted updates to *planned* items only

1. **Run modeling** (feeds the temporal-runtime supplement at gate + future history
   loader): when `ControlMJobRun` builds, adopt their required Run property semantics —
   run UUID, `nominalTime` (scheduled time), parent run/job link, `errorMessage` — and
   **START/COMPLETE/FAIL/ABORT** as the run-event value set. Wire the three seeded
   `:OlClass` nodes (OL Run / OL Job / OL Dataset, `ontology.cypher:139-141`, currently
   unconsumed) to `ControlMJobRun`/`ControlMJob`/`DataAsset` via `MAPS_TO` — satisfies
   their "OpenLineage readable as PROV" mandate nearly for free.
2. **Enum gates emit SKOS-compliant schemes**: the open G27 `etlprocess-kind-enum`
   gate and future enums should produce `ConceptScheme`s carrying their required
   concept attributes (prefLabel, definition, identifier, created/creator). Backfill
   `tom_roles`/`product_roles` with the same fields.
3. **Column metadata names at the `oracle-schema-asset` gate**: when Table→DataAsset
   is confirmed, use their `ColumnShape` property names — `precision`, `scale`,
   `length`, `isNullable` — for column facts. Keep `jpmv:mapsToType` as the pattern
   for any future Oracle↔Snowflake datatype crosswalk.
4. **Optional, low priority**: `dcat:accrualPeriodicity` as the property name if the
   calendar-projection work ever derives dataset-level frequency (their only
   scheduling hook).

## Phase 3 — tool adoption (process, not ontology)

`fcdo-ontology-builder` as an **optional Step-3 aid in `add-source-object`** for
flat/denormalized sources (worked example: the PAT-catalog analysis in TRANSCRIPT-1
§Part 3): run on header-only/redacted extracts; reuse its SKOS enum extraction and
HTML data-dictionary render; translate its generic classes through `ontology-mapper`
into matrix terms. It cannot replace our data profiling (structure-only) and doesn't
know PROV/ORG/DPROD, so it never bypasses the gate.

## Explicit skip list (won't use → don't add)

- **Business Processes Framework** — nothing planned models business-process
  hierarchy; `jpmv:technologyAsset` noted as a future join point only.
- **Data Mapping path expressions / ModelElement machinery** — RDF model-to-model
  plumbing; we don't produce RDF mapping files.
- **SHACL shape artifacts** — our validation is pytest + gate tests; borrow property
  *names* only (Phase 2.3).
- **JDI URL identifiers producer-side** — keep the URN scheme; JDI is a company-side
  concern at port time.
- **FIBO / OMG Commons** — see-also references even for them.
- **Data Authority classes** — `precedence.yaml` covers source-of-truth today;
  ADS/SOC/SOR noted as a possible future DataAsset property, gate only when a runbook
  use case demands it.
- **Telemetry framework** — OpenTelemetry field specs; our layer-4 answer is SOSA
  (experimental) and their corpus has no SOSA — neither promote nor drop on their
  account.
- **Naming-convention renames** — `HAS_PORT` etc. is Neo4j idiom; an RDF-export
  mapping note suffices (their own style guide would render it `dprod:hasPort`).

## Evidence caveats

Capture holes that block crosswalk sign-off if hit: Descriptive Metadata Framework
(shared identifier/title/description envelope), Data Quality Framework (can't check
our DQV dimensions/metrics), Data Contracts/DPROD Framework (can't validate our Port
usage), and most of the Taxonomy Framework's normative property tables. **Recapture
via the registered `fcdo-frameworks` scrape before signing rows that depend on them**
— absence from the transcript is not absence from their standard.
