# MODULE_MAP — drydocs-core vs component boundary (ADR 0002-a Phase B)

> Authoritative module boundary for the modular split in
> [`docs/decisions/0002-component-database-topology.md`](docs/decisions/0002-component-database-topology.md)
> (ADR 0002) and its extraction plan
> [`docs/decisions/0002-a-drydocs-core-extraction-plan.md`](docs/decisions/0002-a-drydocs-core-extraction-plan.md).
>
> **Status: PHYSICAL (Phase B relocate executed 2026-07-10, thin variant per
> [ADR 0002-a-1](docs/decisions/0002-a-1-phase-b-thin-relocate.md)).** The core modules
> live in [`drydocs_core/`](drydocs_core/__init__.py) for real; the `drydocs` package is the
> component remainder (load / review / plan / docgen) and KEEPS its name until Phase C
> (per-component packaging). The invariant is enforced across **both** packages by
> [`tests/unit/test_module_boundary.py`](tests/unit/test_module_boundary.py).

## Invariant

- **Core imports nothing from any component.** The parse / model / config / driver layer must never
  import the graph-write or run-cadence layer.
- **Components import only core, never each other.**

## The component map (ADR 0018 D1 — the declaration, rendered)

What a module BELONGS to is declared once, in `drydocs_core/component_map.py`, and read three
ways: `tests/unit/test_module_boundary.py` enforces it, this section renders it, and the Team
Edition copier (ADR 0015 D2/D4) derives its file classes from it. Since ADR 0018 D4
(2026-09-02) the four components that were flat name-lists under `drydocs/` are subpackages —
`drydocs/review/`, `drydocs/plan/`, `drydocs/port/`, `drydocs/docgen/` — and each old flat path
is a one-cycle `sys.modules` re-export shim (both prefixes are listed until the shims retire at
the roll after next).

<!-- component-map:begin -->
_Rendered from `drydocs_core/component_map.py` by `scripts/render_module_map.py`; do not edit by hand (ADR 0018 D1). The tables further down carry each row's history._

| Component | Backlog module | Series | Dotted prefixes (the boundary test classifies by these) |
|---|---|---|---|
| core | `drydocs-core` | `CORE` | `drydocs_core` |
| load | `drydocs-load` | `LOAD` | `drydocs.loaders`, `drydocs.cli`, `drydocs.cli_schema`, `drydocs.cli_ingest`, `drydocs.cli_verify`, `drydocs.cli_variables`, `drydocs.cli_docs`, `drydocs.cli_plan`, `drydocs.cli_shared`, `drydocs.cli_consumer`, `drydocs.snapshots`, `drydocs.staging`, `drydocs.cmdline_staging`, `drydocs.seal_samples`, `drydocs.pat_projection`, `drydocs.chain_inputs`, `drydocs.code_graph_freshness`, `drydocs.docs_coverage` |
| review | `drydocs-review` | `REV` | `drydocs.review`, `drydocs.graph_verify`, `drydocs.review_labels`, `drydocs.source_mappings`, `drydocs.graph_review`, `drydocs.sme_notes`, `drydocs.gate_pages`, `drydocs.publishing`, `drydocs.fid_census`, `drydocs.run_as_detect` |
| plan | `drydocs-plan` | `PLAN` | `drydocs.plan`, `drydocs.plan_board`, `drydocs.plan_roadmap` |
| port | `drydocs-port` | `PORT` | `drydocs.port`, `drydocs.port_preflight`, `drydocs.port_backlog_union`, `drydocs.port_rename_detect` |
| docgen | `drydocs-docgen` | `DOCGEN` | `drydocs.docgen`, `drydocs.doc_outline`, `drydocs.design_doc`, `drydocs.doc_pdf`, `drydocs.plan_ideas` |
| remediation | `drydocs-remediation` | `REM` | `drydocs_remediation` |
| lineage | `drydocs-lineage` | `LIN` | `drydocs_lineage` |
| deepdoc | `drydocs-deepdoc` | `DEEP` | `drydocs_deepdoc` |
| docmeta | `drydocs-docmeta` | `META` | `drydocs_docmeta` |
| api | `drydocs-api` | `API` | `drydocs_api` |
| agents | `drydocs-agents` | `AGENT` | `agents` |
| libs | `drydocs-libs` | `LIBS` | `libs` |

| Owned surface (no Python package root) | Owning module |
|---|---|
| `agents/` | `drydocs-agents` |
| `config/` | `config` |
| `docs/` | `docs` |
| `drydocs-icons/` | `drydocs-web` |
| `external/` | `reference` |
| `graph-tests/` | `drydocs-review` |
| `internal/` | `docs` |
| `knowledge/` | `docs` |
| `knowledge/depgraph-snapshots/` | `drydocs-load` |
| `knowledge/upgrade-plans/` | `docs` |
| `libs/` | `drydocs-libs` |
| `reference/` | `reference` |
| `scripts/` | `drydocs-load` |
| `web/` | `drydocs-web` |

Work-area and non-Python modules (own no package): `config`, `docs`, `drydocs-web`, `graph-infra`, `ontology`, `reference`, `taxonomy`.
<!-- component-map:end -->

## Naming: folder name vs module name (S7, raised at ADR 0008)

A **module name** (`drydocs-<x>`, the backlog's `modules:` registry) names a *component* —
a boundary the guard enforces and the backlog files work against. A **directory** names a
*code root*. They are the same thing only where the guard needs them to be:

- **First-party Python packages MUST match their module name** (underscore for hyphen:
  `drydocs_lineage/` ↔ `drydocs-lineage`). `test_module_boundary.py` classifies modules by
  package root, so a Python component whose directory diverged from its module name would
  make the guard's classification ambiguous — that is the one condition under which a
  rename is required, not stylistic.
- **Non-Python surfaces keep their ecosystem-conventional names.** `web/` is the module
  `drydocs-web` and `agents/` is `drydocs-agents` because a Vite app named `web/` and an
  ADK service named `agents/` are what their own toolchains expect, and no import-boundary
  guard keys on those directory names — the module identity lives only in the ledgers
  (this file, the backlog registry, `config/taxonomy/ui-components.yaml`). Renaming them to
  match would buy nothing and break ecosystem defaults.
- The recurring confusion this rule answers: `web/` is the **real console**
  (`drydocs-web`); `docs/design/ui-exploration/` is a *docs workspace* (mockups, plans — module `docs`), not
  code. S9 owns re-homing it under `docs/design/`.

The backlog `modules:` comments cite this section rather than re-explaining it.

## Core — `drydocs-core` (shared; stable surface)

| Module (physical) | Role |
|---|---|
| `drydocs_core/models/` | typed rows/entities (catalog, controlm, seal, docs, registry) |
| `drydocs_core/adapters/` | source adapters (base, csv, oracle) + the `controlm/` API-call framework (G96 — config-resolved call surface the deploy/pull .sh invokes) — transform, no graph write |
| `drydocs_core/neo4j_client.py` | driver/session lifecycle; caller passes the DB name |
| `drydocs_core/ui_concepts.py` | reads `config/taxonomy/ui-concepts.yaml` — console terms whose source is NOT the graph (Tower first, R22): `match()` a question to a declared term, `answer_for()` the deterministic Tier-0 answer with provenance, `not_graph_concept_lines()` for schema grounding; any graph binding for such a term is the HITL gate's, not this file's |
| `drydocs_core/notifications.py` | `Neo4jNotification` — the one serialisable shape for a driver summary's non-fatal notifications (R21); the API runner, the agents' read helper and the :AgentRun writer all convert to it so an unknown-label warning cannot be dropped at any of the three |
| `drydocs_core/config.py`, `precedence.py`, `source_registry.py` | declarative config layer (CLAUDE.md §4) |
| `drydocs_core/repo_paths.py` | `repo_root(fallback)` — resolves the DryDocs checkout the CALLER is standing in, so repo-CONTENT defaults follow the caller instead of the editable install's main tree (Idea-109). pathlib-only, imports nothing. **The rule every module-level path anchor is judged against: repo content routes through this; package-internal resources (`drydocs_core/schema/*.cypher`, `drydocs/loaders/cypher/`, the bundled sample CSVs) keep their `__file__` anchor.** Default-deny guard: `tests/unit/test_repo_paths.py::test_no_module_anchors_repo_content_on_dunder_file` fails any `Path(__file__)` chain in an installed package that climbs to the repo root without it |
| `drydocs_core/data_zones.py` | the DECLARED path surface (G81): reads `config/data-zones.yaml` (system-owned write/scratch zones + non-dataset read zones) and JOINS it with the source registry's `acquisition.drop_dir` read zones, then enforces the non-overlap invariant — no write path may equal, contain **or be contained by** a read path (both directions; two of the four live findings ran the direction the acceptance did not name). `read_zone_containing()` is the runtime half a write site calls before writing. Since **G109** it also carries the READ SURFACE — `inventory()` reports present/absent/file-count per declared zone, and `drydocs landing-zones` renders it beside the registry half so the command that answers "are my extracts still there" covers BOTH declarations instead of half of them. Pure resolution; creates nothing | pure parse/resolve; no graph, no component imports |
| `drydocs_core/backlog_store.py` | the ONE reader of the sharded backlog `docs/restructure/backlog/` (ADR 0013): assembles plan/modules/epics/items into the monolith's document shape, derives the roll-ups (`derive_summary`), dumps the assembled document for the reconcile-port guard; reuses S5's duplicate-key loader | pure parse; no graph, no component imports |
| `drydocs_core/data_root.py`, `landing_zones.py` | **where source payloads live, and the guarantee that git cannot delete them.** `data_root.py` resolves `DRYDOCS_DATA_ROOT` (default `~/data/DryDocs`) — the out-of-repo home for large/Internal payloads (G19). `landing_zones.py` resolves what `config/source-registry.yaml` DECLARES: every `acquisition.mode: manual` row's `drop_dir` against its `drop_dir_base` (`data_root` = outside the tree; `repo` = in-tree, permitted only when the contents are TRACKED). Pure resolve + read — it never creates, moves or deletes a directory, because a doctor that repairs the tree it inspects hides the damage it exists to surface. Guard: `tests/unit/test_landing_zones.py`; read surface: `drydocs landing-zones [--check|--json]`. **Why it is core:** it is a config fact about a source, consumed by loaders and the CLI alike, and it writes no graph |
| `drydocs_core/env_refs.py`, `source_bindings.py`, `env_doctor.py` | **how a registered source's carrier is REACHED, and the one function that resolves a variable reference** (G125; ADR 0017 ACCEPTED 2026-08-30). `env_refs.py` is the ONE expansion function plus `DECLARED_VARIABLES`, the enumerable list — before it, `.env.example` declared 17 keys and first-party code read 8 more declared nowhere. It REFUSES bash defaults (`${VAR:-x}`), because a default in committed YAML puts G81 (d)'s silent relocation back at the syntax level where one function cannot see it, and it REGISTERS a secret at expansion — the only place that can know a value is secret is where it first exists. `source_bindings.py` reads `config/source-bindings.yaml`: one connection profile per CONNECTION CARRIER (not per origin — `origin: controlm` spans three systems), holding variable NAMES only, referenced by each system row's `binding:` field and guarded in both directions. Its `BindingReport` is TYPED, never a boolean: `not-configured-on-this-machine` and `not-built-yet` are STATES, only `broken` is a failure, and every report names its venue (J18). It opens no socket — reachability here means every referenced variable resolves, which is the strongest claim available without probing side (A). Guard: `tests/unit/test_source_bindings.py`; read surface: `drydocs landing-zones [--check|--json]`. `env_doctor.py` (G129) joins the declared list to the profiles and to the machine-local `.env`, and answers the three questions the twin never did: which variables exist, which are set HERE, and which twin file documents them. It reports TWO CHANNELS because there are two — the settings classes declare `env_file=.env` while `expand()` reads `os.environ` only, so a variable set in the file alone is visible to a loader and invisible to a binding check, and the doctor names that rather than picking one of the two lies. Its record has no field that could hold a value, which is why (f) is structural rather than a masked print site. Guard: `tests/unit/test_env_doctor.py`; read surface: `drydocs env-doctor [--check|--json]`; the write verb is `scripts/set_env_var.py`, a hand-run script nothing imports (G126: the machine-local tree is read-mode for the SYSTEM). **Why it is core:** pure parse/resolve over a config fact about a source; writes no graph |
| `drydocs_core/ontology/` | namespace / URN vocab + `relationship_vocabulary.yaml`; `concept_scheme.py` (G77) reads the lob-product-team `skos:ConceptScheme` so the Control-M `THEME` token and the docmeta envelope resolve to one set of concept IRIs; `tom_role_vocabulary.py` (G70) reads the DECLARED TOM role vocabulary `config/taxonomy/tom-role-vocabulary.yaml` — the one surface the seal model, the loader and the supplement seed defer to (gate §A8) — pure config read, no graph write |
| `drydocs_core/manual_mappings.py` | pure tier-5 manual-CSV validation/parse (manifest gate, vocab check, K2 shape) — shared by the load component's loader and the mapping store |
| `drydocs_core/mapping_store.py` | SQLite materialization of the mapping layer (plan M0–M4); derived from committed YAML/CSV, consumed by `load` (read seam) and `api` (/mappings) — core placement is WHY both may use it |
| `drydocs_core/schema/` | ground-truth DDL/seed `.cypher` resources (constraints, ontology + supplements) |
| `drydocs_core/schema/supplements.py` | the supplement **chain as data** (G29) — the one ordered registry (base → seal → catalog → registry → infrastructure, SOSA opt-in) plus `declared_terms()`, which parses the `:OntologyTerm` IRIs a `.cypher` MERGEs so the apply can verify it landed. Core, not CLI: the order is a schema fact, the verb is a caller |
| `drydocs_core/orchestration/` | **the vendor-NEUTRAL orchestration surface** (S2, ADR 0008) — `shell.py` (statement split, argv tokenize, wrapper unwrap, LAUNCHER_REGISTRY, file-op verbs; ex the pre-S2 `controlm` commands module), `paths.py` (the `FileRef` shape + assembly + `PathDialect`, the seam a second vendor supplies instead of forking), `crosswalk.py` (**the first runtime consumer of `config/crosswalks/*.yaml`** — resolves native→baseline and RAISES `NoEquivalent` rather than picking a near-miss). This is the parser **C2 (`drydocs-lineage`) and C3 (`drydocs-deepdoc`) both wrap** |
| `drydocs_core/orchestration/controlm/` | **everything irreducibly Control-M** — AutoEdit `%%NAME\|VALUE` variables + the substitution resolver, folder-name convention, fact routing, `fields.py` (which job fields carry shell text; UCM container-override extraction), and the Control-M `PathDialect` (`?`-run→`{TS16}`/`{Q<n>}`, `{ODATE}` tokens, unresolved-`%%` exclusion, FILEWATCH role). **`standard_selection.py` (G94) answers WHICH standard a job validates against** — a decision tree over the derived TASKTYPE, the registered `JOB_ROLE` token and `shell.classify_executable`'s `invocation_type`: a file watcher takes the FileWatcher standard, a command job selects on its ETL ENGINE FIRST (DPL / Ab Initio / Informatica), and anything else falls back to a GENERIC standard whose token set is DERIVED from `TOKEN_REGISTRY` + `FOLDER_VARIABLES` so it cannot drift. Selection is separated from validation, so the tree can be re-ruled without touching the parser. Identities are INTERIM per gate `standard-identity-and-carrier` §E2 — it returns an id and invents no carrier, reads no file and stores nothing. The DD grammar digit is absent from its signature, which is how §7.5's "a version never selects a standard" becomes enforceable rather than stated. **Direction is one-way**: the vendor may import the neutral level, never the reverse — guarded by `test_module_boundary.py::test_neutral_orchestration_never_imports_a_vendor`. Graph labels are untouched (`:ControlMJob` et al. keep their prefix — ADR 0003 rule 4) |
| `drydocs_core/entity_extract.py` | the shared entity/ID extractor (MM3) — pure parse over text returning typed matches with spans: `guid`, `folder_name` (decoded through `orchestration.controlm.parse_folder_name`), `issue_key`, `table_name`, `distribution_list`, `application_id` (always reported, `cued` when a `-seal`/`app_id`/landing-prefix cue is present). Pass order IS precedence, because the classes overlap on the same text. Core by the placement test (no I/O, no graph, no config); consumed by `drydocs_deepdoc` (mind-map novelty, the MM4/MM5 connectors' "IDs in → references out" contract). Placement is the `drydocs_core` package prefix (`CORE_PREFIXES` in `test_module_boundary.py`) — the physical package is the whole of core since ADR 0002-a-1 |

**Borderline — RESOLVED at the Phase B move (0002-a §6):**
- `drydocs/staging.py` (was the `controlm` package's staging module) — builds the loader staging bundle;
  load-cadence-coupled, so it relocated OUT of core into the `load` component group. Core's
  the `controlm` package init no longer re-exports it.
- `drydocs/snapshots/writer.py` — writes the graph; stays component-side (load).

## Components (import core only)

| Module (today) | Component | Writes |
|---|---|---|
| `drydocs/loaders/**` | `drydocs-load` (main) | `drydocs` ground truth |
| `drydocs/cli.py` | `drydocs-load` (entrypoint) | — (orchestrates loaders) |
| `drydocs/cli_schema.py`, `cli_ingest.py`, `cli_verify.py`, `cli_variables.py`, `cli_docs.py`, `cli_plan.py` | `drydocs-load` (per-domain command modules, S8 2026-08-21) — each holds one domain's Typer verbs and is merged FLAT onto the root, so `drydocs --help` is unchanged. Since S13 (2026-08-27) they import shared state from `cli_shared.py` (never the root at module scope — that was the S13 cycle) and are NOT entrypoints: a verb that wires another component (resolve-cmdline-staging, lineage-review, lineage-extract → `drydocs_lineage`; fid-census → `drydocs.review.fid_census`) stays in `cli.py`, the only `ENTRYPOINT_MODULES` exemption. `m1-verify`/`m3-verify` survive as deprecated aliases of `verify-reference`/`verify-controlm` | — (orchestrate loaders) |
| `drydocs/cli_shared.py` | `drydocs-load` (hoisted shared CLI state, S13 2026-08-27, the ADR 0002-A shape) — the constants and stateless helpers the command modules and the root both import (loader registry, chains, gate/adapters/opt helpers, `console`). Makes the CLI import graph a DAG so every `cli_*` module works as the FIRST import of a fresh interpreter (guard: `tests/unit/test_cli_import_order.py`, subprocess-per-import). Mutable state stays on the root (`_registry`, `_client` — the tested patch surfaces), reached only at call time | — (pure state; no graph write) |
| `drydocs/cli_consumer.py` | `drydocs-load` — the optional CONSUMER command module (S16, 2026-09-02): the producer ships NONE; a consumer (the company port, a Team Edition instance) adds one on the S8 module shape and the root discovers it (`CONSUMER_COMMAND_MODULE`, `importlib.util.find_spec`, verbs registered LAST, silent when absent). This is the seam that lets `drydocs/cli.py` be canonical-producer: both sides stop editing one file. Guards: `test_cli_registry.py` (both directions, fixture module), `test_cli_import_order.py` (joins the list where it exists) | — (consumer's own verbs) |
| `drydocs/snapshots/` | `drydocs-load` (tooling) | depgraph snapshot |
| `drydocs/staging.py` | `drydocs-load` (staging bundle builder; ex the `controlm` package's staging module) | — (builds loader input) |
| `drydocs/cmdline_staging.py` | `drydocs-load` — G39/G40 TEMPORARY cmd-line job-detail staging store + parse (stand-in for the unbuilt psgmgr `CM_DEF_VJOB_DETAIL`; retire when a real table exists) | SQLite under `DRYDOCS_DATA_ROOT` (**no graph write**; G22 gates any load) |
| `drydocs_core/component_map.py` | `drydocs-core` — THE component declaration (ADR 0018 D1, 2026-09-02): `CORE_PREFIXES`, `COMPONENT_GROUPS`, `COMPONENT_MODULE`, `NON_PYTHON_MODULES`, `SURFACE_OWNERS`, `ENTRYPOINT_MODULES`, `DECLARED_COMPONENT_IMPORTS`. Pure data, imports nothing. `test_module_boundary.py` ENFORCES it and joins it to `docs/restructure/backlog/modules.yaml` by name; this file's component tables are to be RENDERED from it (LOAD1); the Team Edition copier derives its file classes from it (0015 D2/D4). Moved here from the test file because a declaration only pytest could import was the copier's trip hazard | — (pure declaration) |
| `drydocs_core/docs_verify.py` | `drydocs-core` — Q7 doc-corpus reconciliation (registry declared vs graph loaded). PROMOTED from `drydocs/` at O58 (2026-08-31) on the placement test: it imports stdlib only and its single I/O seam is an INJECTED `run(database, cypher, params)` callable, so it is pure resolve logic, not load cadence. The promotion was forced by a second consumer — the console's docs-verify surface needs it in `drydocs_api`, and component-to-component imports are barred; core is the answer the invariant already prescribes, not a workaround. The verb keeps its I/O (driver, `SHOW DATABASES`, the table) in `drydocs/cli_docs.py` | — (pure; callers own the I/O) |
| `drydocs/code_graph_freshness.py` | `drydocs-load` (U22) — `drydocs code-graph-freshness`: max(`:CodeModule.last_seen_at`) vs the newest snapshot's `meta.captured_at`, one verdict line (fresh / stale by N / empty / no snapshot / database-unreachable — never "fresh" when it could not look); warn-only, never refreshes; consumed by the tech-debt skill (step 0) and `snapshot.ps1` | — (**read-only**) |
| `drydocs/chain_inputs.py` | `drydocs-load` (chain input resolver, G78) — resolves every step of a sequenced chain (`refresh-reference`, the `ingest-controlm` fixture pass) BEFORE the first write: explicit `--samples-dir` (fixtures) or `--source <id>` (the registry's declared landing zone), no default; a missing required file fails the chain by name; the closing table says which path each step read | — (pure path resolution, **no graph write**) |
| `drydocs/pat_projection.py` | `drydocs-load` (input projection, G82) — projects the raw PAT team report into the two files the team chain reads (`cli.CHAINS['refresh-teams']`) (`dev_teams__sample.csv`, `pat_product_mapping__sample.csv`); refuses to guess a key header (`--header-map` pins spellings on the first real run); ledger = `config/source-mappings/pat-team-report.yaml`. CLI: `scripts/project_pat_team_report.py` | two CSVs under the caller's `--out-dir` (Internal, under `DRYDOCS_DATA_ROOT`; **no graph write**) |
| `drydocs/seal_samples.py` | `drydocs-load` (fixture generator) — derives the two SEAL sample CSVs the business-application chain declares (`cli.CHAINS['refresh-applications']`) from `config/taxonomy/business-application.yaml`. They are GENERATED per machine, never committed: `drydocs/data/` is gitignored as possibly-sensitive, and this file family leaked real SEALIDs twice. Refuses to emit an app id outside the reserved 70001-70099 block | sample CSVs under `drydocs/data/samples/` (**no graph write**) |
| `drydocs/review/graph_verify.py` | `drydocs-review` — data-driven Cypher acceptance runner (Epic H) | — (reads graph; asserts) |
| `drydocs/review/review_labels.py` | `drydocs-review` — the review backbone (source→DATA-label map); consumed by review | — (pure config) |
| `drydocs/review/source_mappings.py` | `drydocs-review` — per-source column ledger accessor (doc 08); projected/filter-only/excluded/deferred disposition per profiled column | — (pure config) |
| `drydocs/review/graph_review.py` | `drydocs-review` — renders live-graph rows → SME review HTML (H2) | — (reads graph; writes HTML) |
| `drydocs/review/sme_notes.py` | `drydocs-review` — SME-notes harvester: owner-attributed inline `SME[sid] $FR/$UC/$OQ/$NOTES` comments → requirement buckets (Epic H) | — (scans repo; reports) |
| `drydocs/review/gate_pages.py` | `drydocs-review` — HITL SME-gate prompt-page generator (load-step spec → self-contained interactive review page; repo stays the system of record) | gate pages (offline HTML) |
| `drydocs/review/publishing/**` | `drydocs-review` — docs publish pipeline (Confluence push abstracted, H5) | external (docs target) |
| `drydocs/docs_coverage.py` | `drydocs-load` — the Q16 software→documentation coverage report (`drydocs docs-coverage`): per product, what docs are declared, where they live, whether they are loaded, and every blocker. Two layers — a PURE declaration join that decides the cross-DB question with the database off, plus an optional injected graph probe whose fields are `None` (`not-probed`) rather than `0` when it does not run. Reuses `drydocs_core.docs_verify.count_query` so the two verbs cannot disagree | — (returns counts + states) |
| `drydocs/review/fid_census.py` | `drydocs-review` — the doc-09 phase-0 FID directory census (K16): demand-set scope + the registration-vs-attribution disagreement rate the `fid-identity-and-scope` gate cannot sign without. Pure (no file, no DB, no writes; every input injected) and **counts-only by return type** — the method is producer-side, the measured values are Internal and company-side | — (returns counts) |
| `drydocs/review/run_as_detect.py` | K25 — cross-application run_as detection over the census join: per-JOB class (platform_user / application_fid / unresolvable), class x job type, the same/different/unresolvable comparison for application-class jobs, and the §G5 split parked until ruled. Pure and stdlib-only like `fid_census.py`, for the same porting reason; counts only, no graph write | drydocs-review |
| `drydocs/plan/plan_board.py` | `drydocs-plan` — backlog/ (sharded, ADR 0013) → HTML project board renderer (Epic I) | `docs/plan/board.html` |
| `drydocs/docgen/plan_ideas.py` | `drydocs-plan` — IDEAS.md → HTML idea-inbox read view; reuses `design_doc.render_body` rather than adding a second markdown renderer | `docs/plan/ideas.html` |
| `drydocs/plan/plan_roadmap.py` | `drydocs-plan` — roadmap.yaml (authored stage/estimates) + backlog/ (live counts) → per-module build-out roadmap; the third planning surface | `docs/plan/roadmap.html` |
| `drydocs/port/port_preflight.py` | `drydocs-port` — J41 the port OPENING sequence: certifies a producer base before a company session starts (tree/renders/suite/ledger-coverage/relay-basis/cited-path-resolution/tag). Pure functions take TEXT, COMMIT LISTS and DOCUMENT MAPS, never a repo, so the guards run without one; only `run_checks` shells out | `port-base-<date>` tag + a pass/fail report |
| `drydocs/port/port_backlog_union.py` | `drydocs-port` — J42 the port UNION half: diffs the producer base's backlog item-id set (a git ref, materialized with `git archive`) against the APPLIED consumer tree and fails the port report naming every dropped id. Both sides read through `backlog_store.load_items`, so an absent/empty items directory and a filename-vs-inner-id mismatch FAIL LOUD instead of reading as agreement (the tombstone vacuous-green trap). Owns never-drop-an-entry only; the status-regression half is the J16 guard's | a pass/fail union block for the port report |
| `drydocs/port/port_rename_detect.py` | `drydocs-port` — J72 the port RENAME half: a producer path absent consumer-side classifies as a clean-add, which is true of the PATH and blind to the CONTENT — so a renamed file arrives as new. Compares each proposed add against consumer files with a DIFFERENT name, by id-set (a split moves entries; ids survive it) and by normalized text (a rename rewrites the header; the body survives), taking the stronger. Reports, never decides. Pure text/path-map functions, no repo | a stop-and-look list for the apply session |
| `drydocs/docgen/doc_outline.py` | `drydocs-docgen` — canonical doc-outline completeness + traceability validator (Epic L) | — (pure; validates docs) |
| `drydocs/docgen/design_doc.py` | `drydocs-docgen` — deterministic Markdown→HTML renderer, one surface: screen + @media print (Epic L; L13) | `docs/design/*.html` |
| `drydocs/docgen/doc_pdf.py` | `drydocs-docgen` — headless-Chromium html→PDF via the @media print sheet (Brave-first), date-normalized (Epic L) | `docs/design/*.pdf` (build-on-demand) |
| `drydocs_lineage/**` | `drydocs-lineage` (C2) — proactive/curated cmd-line lineage on the shared core parser (G4 scaffold; POPULATED by the depgraph re-home G9/0002-C, DONE 2026-07-11: model/extractor/review/collect/writer) | `drydocs` (curated/CONFIRMED only; `writer.py` is the sole write boundary, gate-bound until the vocab flips active) |
| `drydocs_deepdoc/**` | `drydocs-deepdoc` (C3; charter ruled at gate document-content-topology G32, restated MM1 2026-08-21) — the corpus-driven investigator seeded from the grounded graph: starts from a subject already in `drydocs`, searches the document corpus + SDLC surfaces, creates no relationship whose subject is not already in the graph; the core command-line parser is an INPUT, not a rival. Method + synthesis: `docs/design/deepdoc-data-flow-overview.md` (epic MM) | `drydocs`, every write carrying `:Uncertain` + reliability/trust stamps (the label is the boundary since the G102 fold; proxy-node keys; `writer.py` sole boundary; promotion = HITL gate through the loader path, never a label strip). Real since MM3: `mindmap.py` (the `drydocs.deepdoc.mindmap.v1` state file — branches, slots, and the rule that a slot fills only with an evidence ref, enforced on the transition and on load) and `search_log.py` (the per-search ledger, declared kind `search` in `config/log-kinds.yaml`: `theme` = the slot targeted, required; `novelty` = new ids vs graph + record, with the ids) |
| `drydocs_remediation/**` | `drydocs-remediation` (C1) — detect → transform → prove → Jira (ADR 0002-B; scaffolded 2026-07-10, in-monorepo per 0002-A-1) | — (**no graph write**; Jira = SoR; the `jira.py` module is the only side-effect boundary) |
| `drydocs_docmeta/**` | `drydocs-docmeta` (ADR 0006, Q6) — proactive document-corpus ingestion: acquire (`connectors/` — `web` + `filedrop` here, T4 connectors company-side) → clean → tokenize → manifest, over the `config/doc-source-registry.yaml` ledger. Capture policy (page ceiling, politeness delay, SSRF scheme allow-list) is `config/doc-capture.yaml`, shared with `scripts/external_vendor_scrape.py` so one number governs both doors | — (**no graph write yet**; the load path is P4. Acquisition writes only under `DRYDOCS_DATA_ROOT`) |
| `drydocs_api/**` | `drydocs-api` — thin read API over the graph (ADR 0005; scaffolded 2026-07-14, O5) | — (**read-only**: endpoint guard + `RoutingControl.READ`; per-view DB routing server-side; sessions = in-memory stub; FastAPI = optional `api` group) |
| `agents/**` | `drydocs-agents` (ADR 0007, R2) — tiered read-only Q&A: QuerySpec router → schema-grounded text2cypher → bounded loop. **Not a poetry package**: each ADK app puts `REPO_ROOT` on `sys.path`. Brought under the boundary guard 2026-07-25 | — (**read-only**; `agents/.venv` is its own interpreter and is skipped by the guard) |
| `libs/**` | `libs` — standalone helpers with **no first-party imports at all** (today: `oracle_kerberos`, the Kerberos connection helper). Leaf infrastructure, own bucket so a future lib that starts importing a component fails the guard. Brought under the guard 2026-07-25 | — |

> **`drydocs-review` note.** All review modules own a run cadence or do external I/O, so
> none are core. `review_labels` and `source_mappings` are *pure config accessors* parked in
> the component; promote either to `drydocs_core.config` only if a **non-review** second
> consumer appears. The guard is now
> **default-deny** (`test_every_module_is_classified`): every module must resolve to exactly one
> bucket, so a new review module (graph_review / publishing) that isn't classified here will
> **fail the boundary test** rather than being silently unguarded.
>
> **`drydocs-plan` note.** Same default-deny discipline: `drydocs/plan/plan_board.py` is a pure,
> offline renderer (backlog/ → `docs/plan/board.html`, no Neo4j, no imports from other
> components) classified into its own `plan` COMPONENT_GROUP, mirroring how `review` is declared —
> it exists precisely so a future `drydocs-plan` module that isn't added here fails the same guard.
>
> **`drydocs-docgen` note.** Same discipline: `drydocs/docgen/doc_outline.py` validates a design doc
> against its canonical `*.outline.yaml` (completeness + requirement traceability, Epic L). Pure,
> offline (stdlib + PyYAML), imports no component; classified into its own `docgen` COMPONENT_GROUP.
> The L3 renderer + L5 save-button widget land in this same group.
>
> **Entrypoint exemption (RESOLVED — was the ADR 0002-a TODO).** Wiring `graph-verify` /
> `graph-review` / `sme-notes` / `docs-*` commands into `drydocs/cli.py` makes `cli.py` import the
> `drydocs-review` component. The CLI is the **composition root / top-level orchestrator**, not a peer
> component, so it is **exempt** from the components-don't-import-each-other rule via
> `ENTRYPOINT_MODULES` in [`tests/unit/test_module_boundary.py`](tests/unit/test_module_boundary.py). It
> stays subject to default-deny classification (remains in `load`) and to core-imports-nothing. This is
> the canonical resolution — a company port whose `cli.py` already owns the review commands passes the
> guard **unchanged**; do NOT extract a separate `review_cli.py` sub-app (that creates a company-only
> structure the producer lacks and re-collides on every future port).

> **`drydocs-agents` / `libs` note (2026-07-25).** Both trees sat OUTSIDE the guard entirely —
> neither is a poetry package, so `PKG_ROOTS` never saw them while `drydocs-agents` was a live
> backlog module. They are now scanned and classified. Fixing that surfaced a **hole in the guard
> itself**: the first-party import filter was
> `m == "drydocs" or m.startswith(("drydocs.", "drydocs_core"))` — note the dot, which matched
> `drydocs.x` and `drydocs_core*` but **not** `drydocs_api`, `drydocs_lineage`, `drydocs_deepdoc`,
> or `drydocs_remediation`. Imports *between the standalone component packages were invisible*, so
> `test_components_do_not_import_each_other` could never have caught one (32 first-party imports
> were unseen, incl. `drydocs.cli → drydocs_lineage.*`). The filter now enumerates every
> first-party root.
>
> **`DECLARED_COMPONENT_IMPORTS` — new, and deliberately not an entrypoint exemption.**
> `agents.common.specs_catalog` imports `drydocs_api.query_specs` + `guard`, which is a genuine
> component→component edge. It is *not* a composition root, so stretching `ENTRYPOINT_MODULES` to
> cover it would have blurred what that constant means. Instead it is a **named, reviewed
> exception**: the agent tier's Tier-0 router dispatches to QuerySpecs, so the spec catalog IS the
> agent contract (ADR 0007) — `agents/` consumes in-process the same read surface the console
> consumes over HTTP. **Follow-up, undecided:** the structurally cleaner fix is promoting
> `query_specs` + `guard` into `drydocs_core` (see the list below); the exception records today's
> reality until that is ruled on. A test asserts the exception is load-bearing — remove it and the
> guard fails.

## Non-Python surfaces (outside the import-boundary invariant)

| Surface | Module | Inventory + dependency story |
|---|---|---|
| `web/` (React/TS console) | `drydocs-web` (Epic O, phase 12) | **Not a Python package** — the core/component import invariant and `test_module_boundary.py` do not apply. It is NOT outside the code graph (O42, 2026-08-06): the all-files snapshot carries every `web/` file, and the depgraph `ts-imports` extractor (sibling repo `a56d2fc`; capability `meta.depgraph.capabilities.ts_imports`) emits first-party `.ts/.tsx` import edges — 94 modules, ~226 edges — so blast-radius / orphan / coupling questions are answerable for the front end the same way as for Python. Component-level inventory (the WHAT-exists ledger, area-grouped, reciprocal with the software registry's `react` product) is [`config/taxonomy/ui-components.yaml`](config/taxonomy/ui-components.yaml), drift-guarded by `tests/unit/test_ui_components.py`. Binary assets (images/fonts) are ruled OUT of the graph (2026-08-06 asset ruling). |
| `agents/` (Google ADK service) | `drydocs-agents` (Epic R, phase 15) | Own venv (`agents/.venv`, `agents/requirements.txt` — a PACKAGING fact) **and IN SCOPE for the boundary test** (`tests/unit/test_module_boundary.py` lists `REPO_ROOT / "agents"` in `PKG_ROOTS`, since 2026-07-25; the interpreter under `agents/.venv` is what the guard skips, not the package). G110 (2026-08-21) corrected this row: the old wording "not a Python package of this monorepo, so absent from the boundary test" ran two different facts together — not being a poetry package says nothing about whether the guard scans the directory, and the guard does. Its `.py` files also appear in the all-files snapshot as tree nodes. |

## Future, land in core when first written
- `§`-format I/O (`§META …§OQ §SUPPLEMENTS §DOC §LEDGER`) → `drydocs_core.sigfmt`.
- classification helpers (today: `config/classification.yaml` + `tests/unit/test_classification.py`)
  → `drydocs_core.classify`, so every component stamps `classification` identically.
