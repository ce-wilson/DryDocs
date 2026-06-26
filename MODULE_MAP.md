# MODULE_MAP — drydocs-core vs component boundary (ADR 0002-a Phase A)

> Authoritative module boundary for the modular split in
> [`docs/decisions/0002-component-database-topology.md`](docs/decisions/0002-component-database-topology.md)
> (ADR 0002) and its extraction plan
> [`docs/decisions/0002-a-drydocs-core-extraction-plan.md`](docs/decisions/0002-a-drydocs-core-extraction-plan.md).
>
> **Phase A is logical only — no files have moved.** This map is the source of truth for what *will*
> become `drydocs-core` vs the component packages, and it is enforced today by
> [`tests/unit/test_module_boundary.py`](tests/unit/test_module_boundary.py). The invariant survives the
> Phase B physical split unchanged; only the package names update.

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
| *(future)* `drydocs-lineage` | C2 — curated cmd-line lineage | `drydocs` |
| *(future)* `drydocs-deepdoc` | C3 — on-demand deep dive | `drydocs_context` |
| *(separate module)* `drydocs-remediation` | C1 — failures → Jira | — (no graph write) |

## Future, land in core when first written
- `§`-format I/O (`§META …§OQ §SUPPLEMENTS §DOC §LEDGER`) → `drydocs_core.sigfmt`.
- classification helpers (today: `config/classification.yaml` + `tests/unit/test_classification.py`)
  → `drydocs_core.classify`, so every component stamps `classification` identically.
