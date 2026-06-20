# DryDocs — repository organization & tuning plan

Authored as a Python-architect + performance pass, on the
`refactor/vendor-internal-separation` fork so it can be tested without touching
`main`. Records what was reorganized, what is **planned but deliberately not yet
executed** (to avoid import churn), and the performance findings.

## 1. The problem

Documentation and ingestion modules for *vendor* vs *internal* material were
intermixed at the repo root (`vendor-bmc/`, `bmc-*.txt`, `internal-standards/`,
`DryDocs_Ontology_Documentation.md`, plus a broad `docs/`). It was not clear which
prose is **captured external vendor reference** vs **DryDocs-owned knowledge that
defines the graph** — a distinction that matters now that an LLM agent will read
this corpus.

## 2. Organizing principle

Three top-level buckets, by *role*:

| Bucket | Role | Examples |
|--------|------|----------|
| **`vendor/`** | External reference that **supports building** the project. Not graph content. | BMC Control-M API/parameter docs |
| **`knowledge/`** | DryDocs-owned unstructured knowledge that **defines** the graph. | ontology doc, naming standards, upgrade plans |
| **`docs/`** | Engineering **process/product** docs — neither vendor reference nor graph-defining. | history, reviews, flows, Product |

Code stays in `drydocs/`; `vendor/` and `knowledge/` are prose only.

## 3. Executed in this fork (safe — `git mv`, no code/imports touched)

- `vendor-bmc/` → **`vendor/bmc-controlm/`**; root `bmc-9-0-22-creating-a-job.txt`
  → `vendor/bmc-controlm/`. Added `vendor/README.md`.
- `internal-standards/` → **`knowledge/standards/`**;
  `DryDocs_Ontology_Documentation.md` → **`knowledge/ontology/`**. Added
  `knowledge/README.md`.
- Saved the GraphRAG upgrade plan → `knowledge/upgrade-plans/graphrag-llm-navigation.md`.
- Added `drydocs/loaders/README.md` documenting the vendor-vs-internal loader split
  **without moving code**.

## 4. Planned — NOT executed (needs an import-aware refactor pass)

These change Python module paths and would break imports if done carelessly; they
belong in a dedicated, test-backed change, not this doc-reorg fork.

### 4a. Group loaders by source/domain
Today `drydocs/loaders/*.py` is a flat mix. Proposed:

```
drydocs/loaders/
  controlm/   # vendor-sourced (BMC Control-M via Oracle psgmgr)
              #   controlm_folders, controlm_jobs, controlm_conditions_in/out,
              #   controlm_dependencies_derived, controlm
  internal/   # internally-sourced
    seal/     #   seal_applications, seal_contacts
    catalog/  #   catalog, business_segments, products, product_lines, ...
```

Migration: move modules, update `cli.py` `LOADER_REGISTRY` + the `from .loaders.*`
imports, keep thin re-export shims for one release, run the test suite. The
`.cypher` and `.sql` siblings (`loaders/cypher/`, `loaders/sql/`) move with their
loaders. **Adapters already separate source** (`csv_adapter`, `oracle_adapter`) —
no change needed there; `oracle_adapter` is the vendor (psgmgr) connector.

### 4b. `docs/patterns/data-catalog/` → `knowledge/ontology/data-catalog/`
Conceptually graph-defining knowledge. Left in place now to avoid breaking inbound
links; move in the same pass that fixes the links.

### 4c. `.claude/skills/` — separate external vs project skills
Most skills there are generic/third-party (`docx`, `pdf`, `pptx`, `canvas-design`,
`code-review`, …); a few are project-specific (`run-drydocs`, `reconcile-port`,
`data-context-extractor`). Proposed grouping `_external/` vs `project/`. Deferred:
skill-resolution path changes need verification against the harness; out of scope
for a doc reorg.

## 5. Performance / tuning findings (architect + perf pass)

The loader core (`loaders/base.py`) is already sound: streaming rows + pydantic
validation + `UNWIND $batch` at `batch_size=1000`, MERGE keys backed by
constraints. Findings below are prioritized; **none were applied blind** (no live
DB / profiling available) — they are recommendations for the fork.

| # | Finding | Action | Priority |
|---|---------|--------|----------|
| T1 | **Embedding writes are one round-trip per node** (P0 `embeddings.py`: `MATCH … SET` per node). | Batch via `UNWIND $rows` + `db.create.setNodeVectorProperty`. (Detailed in the upgrade plan #1–#2.) | **High** |
| T2 | **Oracle extracts**: ensure server-side streaming and set the cursor `arraysize`/`prefetchrows` (~1000, matching `batch_size`) in `oracle_adapter`. A default `arraysize=100` triples round-trips on large pulls; avoid `fetchall()`. | Set `cursor.arraysize`/`prefetchrows`; iterate the cursor. | **High** (large extracts) |
| T3 | **Session per `run()` call** — `neo4j_client.run` opens a new session each call, so a loader run = N+2 sessions. | Offer a session-scoped client (one session per loader run) or reuse a session across `_flush`. | Medium |
| T4 | **Reads use `execute_write`** (`run()` always writes; `server_version`, `verify`). | Add a read path using `execute_read` so reads can route to replicas on clusters/Aura. | Medium |
| T5 | **Multi-statement loader cypher runs via `apoc.cypher.runMany`** (one tx per statement per batch). | Prefer single-statement `UNWIND` templates where feasible (base already fast-paths these via plain `run()`). | Low |
| T6 | **`batch_size` is fixed at 1000.** | Make it per-loader / env-tunable; lower for very wide rows (Application has ~70 props), raise for narrow ones. | Low |
| T7 | **Index write cost during bulk load.** Vector/fulltext indexes add per-write overhead. | Keep embedding population as a **separate post-load `embed` step** (already the design) so bulk MERGE isn't taxed by vector indexing. | Confirmed-good |

### Recommended safe-now changes (small, isolated)
- **T2** (`oracle_adapter` arraysize) and **T1** (batch the embedding writer) are the
  two highest-value, lowest-risk wins. T1 lives on the `feat/llm-nav-p0-vector`
  branch; fold it in there alongside the upgrade-plan refinements.

## 6. Operational entry points (`scripts/`)

Ingestion is invoked through the Python CLI (`poetry run drydocs ...`). For
scheduled go-live (Control-M / cron), `scripts/` adds two thin shell wrappers —
no logic, just the canonical chain, fail-fast:

- `scripts/ingest.sh` — check → bootstrap → ontology supplements → `ingest-controlm`
  → m1/m3-verify. Runnable today; args pass through to `ingest-controlm`.
- `scripts/embed.sh` — vector embedding pass. **Forward-looking**: needs the `embed`
  command from `feat/llm-nav-p0-vector`; guarded to exit cleanly until that lands.

Kept separate so bulk MERGE isn't taxed by vector-index writes (finding **T7**).
NB: distinct from the `.sh`/`.ksh` matched in `drydocs/controlm/commands.py`, which
classify the *job command strings being ingested* — opposite direction. See
`scripts/README.md`.

## 7. Net
- **Now (this fork):** unambiguous top-level `vendor/` vs `knowledge/` split,
  signposted, zero code risk; plus operational `scripts/` wrappers (§6).
- **Next (separate PR):** the loader subpackage split (§4a) with import shims +
  tests; the data-catalog doc move (§4b).
- **Tuning:** apply T1/T2 first; T3–T4 when a perf budget/profiling exists.
