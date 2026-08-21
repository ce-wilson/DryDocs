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
  (`drydocs-web`); `UI-WIP/` is a *docs workspace* (mockups, plans — module `docs`), not
  code. S9 owns re-homing it under `docs/design/`.

The backlog `modules:` comments cite this section rather than re-explaining it.

## Core — `drydocs-core` (shared; stable surface)

| Module (physical) | Role |
|---|---|
| `drydocs_core/models/` | typed rows/entities (catalog, controlm, seal, docs, registry) |
| `drydocs_core/adapters/` | source adapters (base, csv, oracle) + the `controlm/` API-call framework (G96 — config-resolved call surface the deploy/pull .sh invokes) — transform, no graph write |
| `drydocs_core/neo4j_client.py` | driver/session lifecycle; caller passes the DB name |
| `drydocs_core/config.py`, `precedence.py`, `source_registry.py` | declarative config layer (CLAUDE.md §4) |
| `drydocs_core/repo_paths.py` | `repo_root(fallback)` — resolves the DryDocs checkout the CALLER is standing in, so repo-CONTENT defaults follow the caller instead of the editable install's main tree (Idea-109). pathlib-only, imports nothing. **The rule every module-level path anchor is judged against: repo content routes through this; package-internal resources (`drydocs_core/schema/*.cypher`, `drydocs/loaders/cypher/`, the bundled sample CSVs) keep their `__file__` anchor.** Default-deny guard: `tests/unit/test_repo_paths.py::test_no_module_anchors_repo_content_on_dunder_file` fails any `Path(__file__)` chain in an installed package that climbs to the repo root without it |
| `drydocs_core/backlog_store.py` | the ONE reader of the sharded backlog `docs/restructure/backlog/` (ADR 0013): assembles plan/modules/epics/items into the monolith's document shape, derives the roll-ups (`derive_summary`), dumps the assembled document for the reconcile-port guard; reuses S5's duplicate-key loader | pure parse; no graph, no component imports |
| `drydocs_core/data_root.py`, `landing_zones.py` | **where source payloads live, and the guarantee that git cannot delete them.** `data_root.py` resolves `DRYDOCS_DATA_ROOT` (default `~/data/DryDocs`) — the out-of-repo home for large/Internal payloads (G19). `landing_zones.py` resolves what `config/source-registry.yaml` DECLARES: every `acquisition.mode: manual` row's `drop_dir` against its `drop_dir_base` (`data_root` = outside the tree; `repo` = in-tree, permitted only when the contents are TRACKED). Pure resolve + read — it never creates, moves or deletes a directory, because a doctor that repairs the tree it inspects hides the damage it exists to surface. Guard: `tests/unit/test_landing_zones.py`; read surface: `drydocs landing-zones [--check|--json]`. **Why it is core:** it is a config fact about a source, consumed by loaders and the CLI alike, and it writes no graph |
| `drydocs_core/ontology/` | namespace / URN vocab + `relationship_vocabulary.yaml`; `concept_scheme.py` (G77) reads the lob-product-team `skos:ConceptScheme` so the Control-M `THEME` token and the docmeta envelope resolve to one set of concept IRIs — pure config read, no graph write |
| `drydocs_core/manual_mappings.py` | pure tier-5 manual-CSV validation/parse (manifest gate, vocab check, K2 shape) — shared by the load component's loader and the mapping store |
| `drydocs_core/mapping_store.py` | SQLite materialization of the mapping layer (plan M0–M4); derived from committed YAML/CSV, consumed by `load` (read seam) and `api` (/mappings) — core placement is WHY both may use it |
| `drydocs_core/schema/` | ground-truth DDL/seed `.cypher` resources (constraints, ontology + supplements) |
| `drydocs_core/schema/supplements.py` | the supplement **chain as data** (G29) — the one ordered registry (base → seal → catalog → registry, SOSA opt-in) plus `declared_terms()`, which parses the `:OntologyTerm` IRIs a `.cypher` MERGEs so the apply can verify it landed. Core, not CLI: the order is a schema fact, the verb is a caller |
| `drydocs_core/orchestration/` | **the vendor-NEUTRAL orchestration surface** (S2, ADR 0008) — `shell.py` (statement split, argv tokenize, wrapper unwrap, LAUNCHER_REGISTRY, file-op verbs; ex `controlm/commands.py`), `paths.py` (the `FileRef` shape + assembly + `PathDialect`, the seam a second vendor supplies instead of forking), `crosswalk.py` (**the first runtime consumer of `config/crosswalks/*.yaml`** — resolves native→baseline and RAISES `NoEquivalent` rather than picking a near-miss). This is the parser **C2 (`drydocs-lineage`) and C3 (`drydocs-deepdoc`) both wrap** |
| `drydocs_core/orchestration/controlm/` | **everything irreducibly Control-M** — AutoEdit `%%NAME\|VALUE` variables + the substitution resolver, folder-name convention, fact routing, `fields.py` (which job fields carry shell text; UCM container-override extraction), and the Control-M `PathDialect` (`?`-run→`{TS16}`/`{Q<n>}`, `{ODATE}` tokens, unresolved-`%%` exclusion, FILEWATCH role). **Direction is one-way**: the vendor may import the neutral level, never the reverse — guarded by `test_module_boundary.py::test_neutral_orchestration_never_imports_a_vendor`. Graph labels are untouched (`:ControlMJob` et al. keep their prefix — ADR 0003 rule 4) |

**Borderline — RESOLVED at the Phase B move (0002-a §6):**
- `drydocs/staging.py` (was `controlm/staging.py`) — builds the loader staging bundle;
  load-cadence-coupled, so it relocated OUT of core into the `load` component group. Core's
  `controlm/__init__.py` no longer re-exports it.
- `drydocs/snapshots/writer.py` — writes the graph; stays component-side (load).

## Components (import core only)

| Module (today) | Component | Writes |
|---|---|---|
| `drydocs/loaders/**` | `drydocs-load` (main) | `drydocs` ground truth |
| `drydocs/cli.py` | `drydocs-load` (entrypoint) | — (orchestrates loaders) |
| `drydocs/cli_schema.py`, `cli_ingest.py`, `cli_verify.py`, `cli_variables.py`, `cli_docs.py`, `cli_plan.py` | `drydocs-load` (per-domain command modules, S8 2026-08-21) — each holds one domain's Typer verbs and is merged FLAT onto the root, so `drydocs --help` is unchanged. They import shared state FROM the root and are NOT entrypoints: a verb that wires another component (resolve-cmdline-staging, lineage-review → `drydocs_lineage`; fid-census → `drydocs.fid_census`) stays in `cli.py`, the only `ENTRYPOINT_MODULES` exemption. `m1-verify`/`m3-verify` survive as deprecated aliases of `verify-reference`/`verify-controlm` | — (orchestrate loaders) |
| `drydocs/snapshots/` | `drydocs-load` (tooling) | depgraph snapshot |
| `drydocs/staging.py` | `drydocs-load` (staging bundle builder; ex `controlm/staging.py`) | — (builds loader input) |
| `drydocs/cmdline_staging.py` | `drydocs-load` — G39/G40 TEMPORARY cmd-line job-detail staging store + parse (stand-in for the unbuilt psgmgr `CM_DEF_VJOB_DETAIL`; retire when a real table exists) | SQLite under `DRYDOCS_DATA_ROOT` (**no graph write**; G22 gates any load) |
| `drydocs/docs_verify.py` | `drydocs-load` — Q7 doc-corpus reconciliation behind `docs-verify` (registry declared vs graph loaded; re-home to docmeta if Q6 takes over corpus state) | — (reads every database; asserts) |
| `drydocs/pat_projection.py` | `drydocs-load` (input projection, G82) — projects the raw PAT team report into the two files `REFRESH_REFERENCE_CHAIN` reads (`dev_teams__sample.csv`, `pat_product_mapping__sample.csv`); refuses to guess a key header (`--header-map` pins spellings on the first real run); ledger = `config/source-mappings/pat-team-report.yaml`. CLI: `scripts/project_pat_team_report.py` | two CSVs under the caller's `--out-dir` (Internal, under `DRYDOCS_DATA_ROOT`; **no graph write**) |
| `drydocs/seal_samples.py` | `drydocs-load` (fixture generator) — derives the two SEAL sample CSVs `REFRESH_REFERENCE_CHAIN` declares from `config/taxonomy/business-application.yaml`. They are GENERATED per machine, never committed: `drydocs/data/` is gitignored as possibly-sensitive, and this file family leaked real SEALIDs twice. Refuses to emit an app id outside the reserved 70001-70099 block | sample CSVs under `drydocs/data/samples/` (**no graph write**) |
| `drydocs/graph_verify.py` | `drydocs-review` — data-driven Cypher acceptance runner (Epic H) | — (reads graph; asserts) |
| `drydocs/review_labels.py` | `drydocs-review` — the review spine (source→DATA-label map); consumed by review | — (pure config) |
| `drydocs/source_mappings.py` | `drydocs-review` — per-source column ledger accessor (doc 08); projected/filter-only/excluded/deferred disposition per profiled column | — (pure config) |
| `drydocs/graph_review.py` | `drydocs-review` — renders live-graph rows → SME review HTML (H2) | — (reads graph; writes HTML) |
| `drydocs/sme_notes.py` | `drydocs-review` — SME-notes harvester: owner-attributed inline `SME[sid] $FR/$UC/$OQ/$NOTES` comments → requirement buckets (Epic H) | — (scans repo; reports) |
| `drydocs/gate_pages.py` | `drydocs-review` — HITL SME-gate prompt-page generator (load-step spec → self-contained interactive review page; repo stays the system of record) | gate pages (offline HTML) |
| `drydocs/publishing/**` | `drydocs-review` — docs publish pipeline (Confluence push abstracted, H5) | external (docs target) |
| `drydocs/docs_coverage.py` | `drydocs-load` — the Q16 software→documentation coverage report (`drydocs docs-coverage`): per product, what docs are declared, where they live, whether they are loaded, and every blocker. Two layers — a PURE declaration join that decides the cross-DB question with the database off, plus an optional injected graph probe whose fields are `None` (`not-probed`) rather than `0` when it does not run. Reuses `docs_verify.count_query` so the two verbs cannot disagree | — (returns counts + states) |
| `drydocs/fid_census.py` | `drydocs-review` — the doc-09 phase-0 FID directory census (K16): demand-set scope + the registration-vs-attribution disagreement rate the `fid-identity-and-scope` gate cannot sign without. Pure (no file, no DB, no writes; every input injected) and **counts-only by return type** — the method is producer-side, the measured values are Internal and company-side | — (returns counts) |
| `drydocs/plan_board.py` | `drydocs-plan` — backlog/ (sharded, ADR 0013) → HTML project board renderer (Epic I) | `docs/plan/board.html` |
| `drydocs/plan_ideas.py` | `drydocs-plan` — IDEAS.md → HTML idea-inbox read view; reuses `design_doc.render_body` rather than adding a second markdown renderer | `docs/plan/ideas.html` |
| `drydocs/plan_roadmap.py` | `drydocs-plan` — roadmap.yaml (authored stage/estimates) + backlog/ (live counts) → per-module build-out roadmap; the third planning surface | `docs/plan/roadmap.html` |
| `drydocs/port_preflight.py` | `drydocs-port` — J41 the port OPENING sequence: certifies a producer base before a company session starts (tree/renders/suite/ledger-coverage/relay-basis/cited-path-resolution/tag). Pure functions take TEXT, COMMIT LISTS and DOCUMENT MAPS, never a repo, so the guards run without one; only `run_checks` shells out | `port-base-<date>` tag + a pass/fail report |
| `drydocs/doc_outline.py` | `drydocs-docgen` — canonical doc-outline completeness + traceability validator (Epic L) | — (pure; validates docs) |
| `drydocs/design_doc.py` | `drydocs-docgen` — deterministic Markdown→HTML renderer, one surface: screen + @media print (Epic L; L13) | `docs/design/*.html` |
| `drydocs/doc_pdf.py` | `drydocs-docgen` — headless-Chromium html→PDF via the @media print sheet (Brave-first), date-normalized (Epic L) | `docs/design/*.pdf` (build-on-demand) |
| `drydocs_lineage/**` | `drydocs-lineage` (C2) — proactive/curated cmd-line lineage on the shared core parser (G4 scaffold; POPULATED by the depgraph re-home G9/0002-C, DONE 2026-07-11: model/extractor/review/collect/writer) | `drydocs` (curated/CONFIRMED only; `writer.py` is the sole write boundary, gate-bound until the vocab flips active) |
| `drydocs_deepdoc/**` | `drydocs-deepdoc` (C3) — reactive on-failure deep dive on the shared core parser (scaffolded 2026-07-10, G4) | `ddcontext` (reliability/trust stamped; proxy-node keys; `writer.py` sole boundary; promotion = HITL gate, never cross-DB edit) |
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
> **`drydocs-plan` note.** Same default-deny discipline: `drydocs/plan_board.py` is a pure,
> offline renderer (backlog/ → `docs/plan/board.html`, no Neo4j, no imports from other
> components) classified into its own `plan` COMPONENT_GROUP, mirroring how `review` is declared —
> it exists precisely so a future `drydocs-plan` module that isn't added here fails the same guard.
>
> **`drydocs-docgen` note.** Same discipline: `drydocs/doc_outline.py` validates a design doc
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
| `agents/` (Google ADK service) | `drydocs-agents` (Epic R, phase 15) | Own venv; not a Python package of this monorepo, so absent from the boundary test. Its `.py` files still appear in the all-files snapshot as tree nodes. |

## Future, land in core when first written
- `§`-format I/O (`§META …§OQ §SUPPLEMENTS §DOC §LEDGER`) → `drydocs_core.sigfmt`.
- classification helpers (today: `config/classification.yaml` + `tests/unit/test_classification.py`)
  → `drydocs_core.classify`, so every component stamps `classification` identically.
