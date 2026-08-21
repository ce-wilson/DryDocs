# Registry redesign plan — system / dataset / replica identity (N7 input)

**Classification: Internal** (names internal systems and carries real SEAL ids in the
worked examples). Drafted 2026-07-31 from the user directive (chat) + the saved samples
in `samples/`. This is the **design input to backlog item N7** (source-registry schema
v2 design session) — nothing here changes a schema, mapping, or loader binding before
the N7 HITL gate rules it (J21's hardening of the current shape is the interim
guarantee).

> **N9 BUILT 2026-07-31 (same day):** the v2 registry SHIPPED — 15 systems / 28
> datasets / 17 retired ids; doc-ledger union; the D2 overlay seam
> (`config/loader-source-overlay.yaml`); derived URNs; all loaders re-bound.
> Per-row sweep finding: the cm_avg_run gate had actually SIGNED 2026-07-14 (P2)
> — the v1 umbrella note was stale. Q6 amendment (old→new id map) appended to
> `config/gate-log.md`. This plan is now the historical design record.

## RULED — N7 gate session 2026-07-31 (gate-log entry `source-registry-v2`)

The in-chat SME session ruled **all** of D1–D4 and Q1–Q6 (transcription:
`config/gate-log.md` 2026-07-31; prompt: `config/gate-prompts/source-registry-v2.yaml`):

- **D1 adopted, amended** — two-level split as designed; **`seal_id` is a standing
  PLACEHOLDER field on every committed system row** (real value internal-twin only).
- **D2 adopted** — the per-side loader→source_id overlay wins over class defaults,
  guarded to resolve to registered dataset ids (extends J21).
- **D3 adopted** — the derived URN handle; **Q2: env segment always `prod`**.
- **D4 adopted** — `replaces:` back-pointers + retired-id refusal list; the loader and
  overlay guard refuse any retired flat id.
- **Q1 @ grammar kept, amended** — replica/derived ids are
  **`{origin}@{db}.{schema}.{table}`**: all dots after `@`, and the qualified segment
  is the **actual carrier locator, replacing the informal system nickname** (SME
  example: `controlm@[db].[schema].cm_def_vjob`); born-here datasets stay
  `{system}:{artifact}`; **lowercase throughout**. Real db/schema values are
  connection coordinates → internal twin only; committed producer ids carry
  `[db].[schema]` placeholders.
- **Q3** — derived stores: @ grammar + `derived: true`; `authority` omitted (SOC
  checked against transcript §H = upstream System of Capture; does not fit).
- **Q4** — **`snow` registers now as a SaaS system**; first dataset
  `snow:cmdb-ci-classes`; doubles as the `cmdb_ci` crosswalk source.
- **Q5** — design-docs pipeline-side only; the doc-registry twin drops.
- **Q6** — signed-off gates **transfer** across renames; one gate-log amendment entry
  maps old→new ids at the build; D4 catches actual meaning changes.
- **T19 naming note** — the catalog feed's replacement name is
  **`pat:product-catalog`** (industry-standard naming; matches neither legacy string);
  the people report splits out as `pat:people-report`. Recorded in the
  `docs/port/port-prompt.md` divergence ledger for the company T19 review.
- **RESIDUAL** — the migration table below is NOT block-confirmed: each row confirms
  individually at the **N9 build** (previously signed rows transfer per Q6; everything
  else lands `confirmed: false`).

## The problem (why the current registry "drifted more than planned")

`config/source-registry.yaml` grew to 18 entries whose flat `id` conflates three
different things, and the generated ids stopped making sense:

- **`kind` proliferated ad hoc** — 10 values (orchestration, internal, reference,
  derived, docs, server-inventory, registry, code-repo, data-platform, staging)
  invented entry-by-entry, not a designed axis.
- **One id spans system AND dataset** — `controlm-psgmgr` is a *connection* (the
  psgmgr replica DB) plus an ever-widening `feeds_taxonomy` list of *datasets*
  (folders, jobs, conditions, dependencies, variables, hosts, runtime_stats).
  `catalog-pat` is one id for two unrelated feeds (catalog hierarchy + PAT team
  report) — exactly how the company-side `catalog-pat ≠ pat-catalog` same-string
  collision (T19) happened.
- **Replicas are invisible** — SEAL data landing in psgmgr looks like "a psgmgr
  table", losing that SEAL is the origin and psgmgr only the carrier.
- **Docs corpora are double-entered** — pipeline registry + doc-source registry twins.
- **Four classification tiers** are more publish-boundary machinery than the work
  needs right now.

## The three distinctions (the ruling to encode)

| # | What it is | Ledger | Identity |
|---|-----------|--------|----------|
| 1 | **Software we use or trace in the graph** | `config/taxonomy/software-registry.yaml` (unchanged — Vendor/SoftwareProduct taxonomy ledger, ADR 0004) | product id (`controlm`, `oracle-db`) — **not a source id**. Its own graph load becomes an ordinary dataset row (`repo:software-registry`). |
| 2 | **Ingested data sources** (PAT → Product/ORG, SEAL → Software/Apps, psgmgr → Control-M replica, …) | `config/source-registry.yaml` **v2** | two levels: **system** entry (connection, locator, classification, SDLC/runbook link) + **dataset** entries (gate, crosswalk, feeds_taxonomy, taxonomy category — each with its OWN `confirmed` state). |
| 3 | **Replica datasets** (SEAL data loaded into psgmgr, catalog views in Snowflake) | same v2 file | the dataset id **combines origin + carrier + artifact**: `seal@psgmgr:CM_ESCALATION_DB`. |

**Documents keep their own tracking** — `config/doc-source-registry.yaml` stays the
third ledger (already split; ADR 0006). v2 drops the pipeline-registry twin entries
for pure doc corpora (bmc-docs, essential-graphrag, fcdo-frameworks) — one home each;
design-docs stays pipeline-side only because it feeds graph classes beyond
Document/Chunk (gate question Q5 below).

## The id grammar

```
system  id:   {system}                            e.g.  psgmgr, seal, pat, snow, dpl
dataset id:   {origin}@{db}.{schema}.{table}      replica/derived — the segment after @
                                                  is the ACTUAL qualified carrier
                                                  locator (ruled 2026-07-31: it
                                                  REPLACES the informal nickname)
              {system}:{artifact}                 born-here datasets
e.g.  controlm@[db].[schema].cm_def_vjob          (real db/schema: internal twin only)
      seal@[db].[schema].cm_escalation_db
      pat:product-catalog
```

- **origin** — the system the data is *about* / born in (the SOR side).
- **@{db}.{schema}.{table}** — present only for replica/derived datasets: the fully
  qualified locator of what we actually read, dot-separated like SQL, **lowercase**.
  Real db/schema names stay internal-twin; committed ids carry `[db].[schema]`
  placeholders. The dataset row's `system:` field still joins to the system row.
- **artifact** — the report, file, query, or table: the thing a support person can
  point at. `artifact_kind: table | file | report | query | api`.

This follows the FCDO JDI identifier principles (transcript §A, Council-approved
Mar 2025): self-describing, federated (each system's owner mints its own artifact
segment), **stable** (nothing embedded that changes when data moves — the carrier is
part of the name only because a replica genuinely IS a different dataset), and
reconstructible without a lookup. JDI itself (URL namespaces, `?version=`) stays
company-side per the ALIGNMENT-PLAN skip list; producer keeps a derived **URN
handle** per dataset for cross-repo identity (N7 decision 3), shaped like the DataHub
convention in `samples/DataHubExample.csv`:

```
urn:drydocs:dataset:({carrier-or-origin},{artifact},{env})
e.g. urn:drydocs:dataset:(psgmgr,CM_ESCALATION_DB,prod)
```

lowercase throughout (the DataHub PROD-vs-prod duplicate warning), deterministic from
the row — a render, not a second hand-maintained field.

## Row shape (from `samples/target-partial-start.csv` target-state columns)

**System row** (one per technical system):
`id`, `name`, `seal_id` *(real value — this file/`internal/` twin only)*,
`cmdb_ci` (ServiceNow class, e.g. `cmdb_ci_business_app` — crosswalk hook to
`samples/SNOW-CMDB.csv`), `layer` (`human | business | data | technology` — the
four-value BDAT architecture view, user ruling 2026-07-31; extends the target
sheet's three-value Layer/View column with the explicit Data layer so
data-platform systems like the Snowflake catalog and psgmgr class as `data`
rather than being folded into `business` or `technology`; precedent = the
SDLC-notebook NodeDomain metamodel and the two planes in the user's ER
screenshot), `classification`, `locator`
(connection coordinates — unchanged discipline: service/TNS names stay in
internal-local), `sdlc` (link to the module runbook / SDLC doc — every source is a
participant in the SDLC process), `notes`.

**Dataset row** (one per extracted artifact):
`id` (the grammar above), `system` (carrier), `origin` (when ≠ carrier),
`artifact` + `artifact_kind`, `taxonomy_category` (controlled scheme below),
`asset_type` (`dcat:Dataset` for Data Asset rows — matches both FCDO's ETL model and
DataHub), `authority` (`SOR | ADS` — see next section), `feeds_taxonomy`
(**scoped per dataset** — this is the drift fix: the list stops widening because each
dataset carries only its own classes), `adapter`, `crosswalk`/`gate_spec`,
`confirmed`, `source_url` / `query_report_source` *(real URLs internal-twin only)*,
`urn` (derived).

**`taxonomy_category` controlled scheme** (from the samples; becomes a SKOS
ConceptScheme when the enum-gate work lands — ALIGNMENT-PLAN Phase 2.2):
`People & Org · Product · Geography · Business Arch · Data Asset · Pipelines ·
Software / Apps · Architecture · ITSM / Gov · Infrastructure`.

## Authority designations — the FCDO transcript references

The replica question is answered by their **Data Authority Metadata Framework**
(CONFLUENCE-TRANSCRIPT §H + the Our Vocabulary page):

- **SOR** — "a single originating source for one or more specific sets of data …
  a system is an SOR *in context of a set of data*" — i.e. authority attaches to the
  **dataset**, not the system. Exactly the two-level split.
- **ADS** — "contains a **copy** of one or more specific sets of data from one or
  more SOR(s) and is approved for redistribution". The SEAL-into-psgmgr replica is
  literally this: origin SEAL = SOR, carrier psgmgr = ADS for that dataset.
- Their `jpmv:designation` property takes literal values `"ADS" / "SOC" / "SOR"`,
  repeatable per asset (§H 5.1.1).

So v2 adopts their **vocabulary as a registry field** (`authority: SOR|ADS` on
dataset rows) — this refines the ALIGNMENT-PLAN skip-list stance: still no Data
Authority *graph classes*, but the field names/values align with the firmwide terms
instead of inventing our own. `config/precedence.yaml` remains the conflict-winner
axis (a different question: which source wins, not which is authoritative for what).

Other transcript anchors used above: JDI Identifiers Specification (§A) for the id
principles; Provenance Framework (Dataset = `dcat:Dataset`) for `asset_type`;
Taxonomy Framework SKOS profile for the category scheme.

## Worked migration sketch (illustrative — the N7 gate rules each row)

| Current flat id | v2 system | v2 dataset id(s) |
|---|---|---|
| `controlm-psgmgr` | `psgmgr` (carrier; SEAL 82507) | `controlm@psgmgr:CM_DEF_JOB`, `…:CM_DEF_SETVAR`, `…:CM_HOSTS`, `…:CM_AVG_RUN` (per the existing column-mapping ledger) — origin `controlm` = SOR, psgmgr = ADS |
| *(new, the user's named case)* | `psgmgr` | `seal@psgmgr:CM_ESCALATION_DB` — origin `seal` |
| `catalog-pat` | `pat` (SEAL 88152) | `pat:catalog-hierarchy` + `pat:people-report` — **the T19 collision dissolves**: the two feeds get distinct dataset ids; system id `pat` matches neither legacy string, so neither repo's wrong value survives |
| `seal-extract` | `seal` (SEAL 32010) | `seal:app-extract` |
| `controlm-xml-export` | `controlm` | `controlm:deftable-xml-export` |
| `autosys-export` / `airflow-mwaa` | `autosys` / `airflow` | `autosys:export` / `airflow:dag-export` (placeholders; crosswalk fields ride the dataset) |
| `dpl-registry` | `dpl` | `dpl:pipeline-registry` + `dpl:dataset-registry` (the two Swagger exports — another forced-split example) |
| `snowflake-data-catalog` | `snowflake` | `catalog@snowflake:DATASETS_V` + `catalog@snowflake:DISTRIBUTIONS_V` (replica grammar again) |
| `rua-inventory` | `exec-hosts` | `exec-hosts:rua-bundle` |
| `code-repo` | `bitbucket` (company) | `bitbucket:repo-objects-manifest` |
| `oracle-schemas` / `snowflake` | per-schema systems | datasets per table group (gate) |
| `stg-app-fact` | `drydocs-stg` (our own derived store) | `controlm@drydocs-stg:STG_APP_FACT` (origin controlm — derived, not replica; gate question Q3) |
| `software-registry` / `depgraph-snapshot` / `design-docs` | `repo` | `repo:software-registry`, `repo:depgraph-snapshot`, `repo:design-docs` |
| `bmc-docs` / `essential-graphrag` / `fcdo-frameworks` | — | move wholly to `doc-source-registry.yaml` (drop pipeline twins) |
| *(future)* | `snow` | `snow:cmdb-ci-classes` — the CMDB class/relationship export sampled in `samples/SNOW-CMDB.csv`; also the crosswalk source for every system row's `cmdb_ci` field |

The ER screenshot (2026-07-31 chat) shows the destination pattern: one model, three
sources color-keyed per node (ServiceNow / SEAL / Verum — Verum Tech Infra SEAL
87674) — per-node source-of-record attribution is what the `origin` + `authority`
fields make loadable.

## Classification simplification (user directive: "for now")

Three levels: **External · Internal-Public · Internal**. Internal-Confidential
collapses into Internal (same publish behavior — never leaves the private repo; the
extra tier bought handling ceremony, not a different boundary). Mechanics, one small
change-set:

1. `config/classification.yaml` — drop the Internal-Confidential level; keep the
   sanitize map + publish rule unchanged (publishable = External, Internal-Public).
2. Relabel the ~8 `Internal-Confidential` entries across `source-registry.yaml` /
   `doc-source-registry.yaml` → `Internal` (comments may keep a "confidential
   handling" note where it matters: rosters, SIDs, SEAL values).
3. `tests/unit/test_classification.py` + `tests/unit/test_doc_registry.py` —
   CURATION_BY_TIER T4 becomes `sme-confirm` (the `+confidential` rider retires with
   the level).
4. README headers in `internal/` capture dirs (fcdo-reference, this dir) restate
   "Internal".
5. `PUBLISH-BOUNDARY.md` note recording the collapse and that a 4th tier can return
   if a real handling difference ever materializes.

## Phasing

- **Phase 0 — done with this commit:** samples re-homed to
  `internal/registry-redesign/samples/` (also clears the J22 fall-through guard
  failure the three root CSVs caused); this plan captured; N7 pointed here.
- **Phase 1 — classification collapse** (the small mechanical change-set above;
  can land ahead of the gate — it removes machinery, adds none).
- **Phase 2 — N7 design session proper:** design doc + gate prompt from this plan;
  full 18-row migration table finalized; SourceRegistry schema v2 drafted; URN
  derivation + reconcile same-id/changed-meaning guard specified.
- **Phase 3 — HITL gate, then build:** schema v2 + loader bindings move to dataset
  ids + renders (load-map, board, enforcement matrix) + the guards. Output feeds the
  company T19 gate review (the catalog-pat ≠ pat-catalog divergence stays recorded in
  the port ledger regardless of the ruling).

## Open questions for the gate — ALL RULED 2026-07-31 (see RULED section above)

- **Q1** `@` carrier notation — **RULED: kept, amended** to
  `{origin}@{db}.{schema}.{table}` (qualified locator replaces the nickname; lowercase).
- **Q2** URN env segment — **RULED: always `prod`**.
- **Q3** Derived stores — **RULED: @ grammar + `derived: true`; authority omitted**.
- **Q4** `snow` — **RULED: registers now as a SaaS system** (`snow:cmdb-ci-classes`).
- **Q5** design-docs — **RULED: pipeline-side only** (doc twin drops).
- **Q6** Per-dataset `confirmed` — **RULED: signed-off gates transfer across renames**
  (one gate-log amendment at the build; D4 catches meaning changes).
