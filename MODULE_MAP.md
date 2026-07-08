# MODULE_MAP — drydocs-core vs component boundary (ADR 0002-a Phase A)

> Authoritative module boundary for the modular split in
> [`docs/decisions/0002-component-database-topology.md`](docs/decisions/0002-component-database-topology.md)
> (ADR 0002) and its extraction plan
> [`docs/decisions/0002-a-drydocs-core-extraction-plan.md`](docs/decisions/0002-a-drydocs-core-extraction-plan.md).
>
> **Status:** the boundary is logical; the physical split is staged. A transitional
> [`drydocs_core/`](drydocs_core/__init__.py) shim package now exists (ADR 0002-a Phase B step 1) — it
> **re-exports** the surface below while the modules still physically live under `drydocs/`. Components
> import `drydocs_core.*`; when the files relocate (Phase B step 2+), only those re-exports flip. The
> invariant is enforced across **both** packages by
> [`tests/unit/test_module_boundary.py`](tests/unit/test_module_boundary.py) and survives the physical
> split unchanged; only the package names update.

## Invariant

- **Core imports nothing from any component.** The parse / model / config / driver layer must never
  import the graph-write or run-cadence layer.
- **Components import only core, never each other.**

## Core — `drydocs-core` (shared; stable surface)

| Module (today) | Becomes | Role |
|---|---|---|
| `drydocs/models/` | `drydocs_core.models` | typed rows/entities (catalog, controlm, seal) |
| `drydocs/adapters/` | `drydocs_core.adapters` | source adapters (base, csv, oracle) — transform, no graph write |
| `drydocs/neo4j_client.py` | `drydocs_core.neo4j` | driver/session lifecycle; caller passes the DB name |
| `drydocs/config.py`, `precedence.py`, `source_registry.py` | `drydocs_core.config` | declarative config layer (CLAUDE.md §4) |
| `drydocs/ontology/` | `drydocs_core.ontology` | namespace / URN vocab |
| `drydocs/controlm/` (whole package) | `drydocs_core.controlm` | **the shared Control-M parser** — `commands.py` (CMD_LINE→invocations/file-ops) + `paths.py` (file-ref canonicalization) are the lineage parser **C2 (`drydocs-lineage`) and C3 (`drydocs-deepdoc`) both wrap** |

**Borderline, parked in core for Phase A** (resolve at the Phase B move, not now):
- `drydocs/controlm/staging.py` — builds the loader staging bundle; the `controlm/__init__.py`
  re-export couples it to the parser package, so it stays inside `drydocs.controlm` (core) for Phase A.
  Candidate to move to `drydocs-load` in Phase B *iff* no second consumer appears.

## Components (import core only)

| Module (today) | Component | Writes |
|---|---|---|
| `drydocs/loaders/**` | `drydocs-load` (main) | `drydocs` ground truth |
| `drydocs/cli.py` | `drydocs-load` (entrypoint) | — (orchestrates loaders) |
| `drydocs/snapshots/` | `drydocs-load` (tooling) | depgraph snapshot |
| `drydocs/graph_verify.py` | `drydocs-review` — data-driven Cypher acceptance runner (Epic H) | — (reads graph; asserts) |
| `drydocs/review_labels.py` | `drydocs-review` — the review spine (source→DATA-label map); consumed by review | — (pure config) |
| *(future H2)* `drydocs/graph_review.py` | `drydocs-review` — renders live-graph rows → SME review HTML | — (reads graph; writes HTML) |
| *(future H5)* `drydocs/publishing/**` | `drydocs-review` — docs publish pipeline (Confluence push abstracted) | external (docs target) |
| `drydocs/plan_board.py` | `drydocs-plan` — backlog.yaml → HTML project board renderer (Epic I) | `docs/plan/board.html` |
| `drydocs/doc_outline.py` | `drydocs-docgen` — canonical doc-outline completeness + traceability validator (Epic L) | — (pure; validates docs) |
| `drydocs/design_doc.py` | `drydocs-docgen` — deterministic Markdown→HTML/print.html renderer (Epic L) | `docs/design/*.{html,print.html}` |
| *(future)* `drydocs-lineage` | C2 — curated cmd-line lineage | `drydocs` |
| *(future)* `drydocs-deepdoc` | C3 — on-demand deep dive | `drydocs_context` |
| *(separate module)* `drydocs-remediation` | C1 — failures → Jira | — (no graph write) |

> **`drydocs-review` note.** All review modules own a run cadence or do external I/O, so
> none are core. `review_labels` is a *pure config accessor* parked in the component; promote
> to `drydocs_core.config` only if a **non-review** second consumer appears. The guard is now
> **default-deny** (`test_every_module_is_classified`): every module must resolve to exactly one
> bucket, so a new review module (graph_review / publishing) that isn't classified here will
> **fail the boundary test** rather than being silently unguarded.
>
> **`drydocs-plan` note.** Same default-deny discipline: `drydocs/plan_board.py` is a pure,
> offline renderer (backlog.yaml → `docs/plan/board.html`, no Neo4j, no imports from other
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

## Future, land in core when first written
- `§`-format I/O (`§META …§OQ §SUPPLEMENTS §DOC §LEDGER`) → `drydocs_core.sigfmt`.
- classification helpers (today: `config/classification.yaml` + `tests/unit/test_classification.py`)
  → `drydocs_core.classify`, so every component stamps `classification` identically.
