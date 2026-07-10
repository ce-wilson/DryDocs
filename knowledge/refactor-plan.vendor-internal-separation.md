---
schema: drydocs.refactor-plan/architect-output.v1
repo: ce-wilson/DryDocs
branch: refactor/vendor-internal-separation
commit: 683322c970525956ca8cfdaeab94a85a3ea9be76
input_artifacts:
  - knowledge/depgraph.architect.json
  - knowledge/depgraph.json
goal: Separate VENDOR (BMC Control-M) code from INTERNAL/core code
produced_by: Plan-agent architect pass
---

# Implementation Plan: Vendor (Control-M) / Internal Separation

## Design decisions

- **Target namespace:** consolidate ALL vendor code under `drydocs.controlm`. The boundary becomes a single import-path prefix (`drydocs.controlm`) a lint rule can enforce. Rejected `drydocs.loaders.controlm` (keeps vendor inside core `loaders` package + mixed asset dirs).
- **`loaders.base` stays shared, single copy, in core** (fan-in 11, zero vendor knowledge). Vendor→core import is the correct direction, not a violation.
- **Drop `streamlit` + `streamlit-agraph`** — confirmed unused in code. Keep `pandas` unless a grep proves it unused.

## Target layout

```
drydocs_core/controlm/
  __init__.py
  commands.py facts.py folder_name.py paths.py resolver.py
  staging.py variables.py variable_report.py
  models.py              <- from drydocs_core/models/controlm.py
  cli.py                 <- NEW: controlm_app (typer sub-app)
  loaders/
    __init__.py          <- from drydocs/loaders/controlm.py (grouped re-export)
    folders.py jobs.py conditions_in.py conditions_out.py dependencies_derived.py
    cypher/  controlm_*.cypher   <- dir moved, filenames unchanged
    sql/     controlm_*.sql      <- dir moved, filenames unchanged
    registry.py          <- NEW: VENDOR_LOADERS + INGEST_CHAIN seam
drydocs/cli_support.py   <- NEW: core, vendor-free shared CLI helpers
```

## Core↔vendor seam

Replaces today's 9 core→vendor edges with **1 intentional edge** (`cli` → `controlm.cli`):

1. **Loader registry** (`drydocs_core/controlm/loaders/registry.py`): `VENDOR_LOADERS: dict[str, type[BaseLoader]]` (5 entries) + `INGEST_CHAIN: list[IngestStage]`. Core `cli.LOADER_REGISTRY = {**CORE_LOADERS, **VENDOR_LOADERS}`.
2. **Vendor CLI sub-app** (`drydocs_core/controlm/cli.py`, `controlm_app = typer.Typer()`): owns `ingest-controlm`, `analyze-variables`, `normalize-variables`. Core wires with `from .controlm.cli import controlm_app` + `app.add_typer(controlm_app)`.
3. **`drydocs/cli_support.py`**: extract shared helpers (`_client`, `_csv_adapter`, `_oracle_adapter`, `_scope_binds`, scope option factories, `DEFAULT_SAMPLES_DIR`) so both CLIs import without a cycle. Vendor `SQL_DIR` lives in `controlm/cli.py`.

## Phased execution (DAG stays acyclic, tests green each phase)

Per-phase gate: `poetry run pytest -q` + `python -c "import drydocs.cli"` + `drydocs --help`.

- **Phase 0 — Dep cleanup:** delete `streamlit`/`streamlit-agraph` from pyproject.toml; `poetry lock --no-update`. Verify `grep -rn streamlit drydocs tests` empty.
- **Phase 1 — Move vendor row models:** `drydocs_core/models/controlm.py` → `drydocs_core/controlm/models.py`. Strip vendor block from `models/__init__.py` (+`__all__`). Repoint: `controlm/staging.py`, `cli.py` (temp), vendor loaders, tests `test_controlm_models` / `test_variable_classifier` / `test_variable_staging`. Closes boundary-violation #9 (models barrel).
- **Phase 2 — Move vendor loaders + assets:** create `drydocs_core/controlm/loaders/`; move 5 loaders (drop `controlm_` prefix) + `controlm.py`→`__init__.py`; move `cypher/controlm_*.cypher` + `sql/controlm_*.sql` dirs (KEEP filenames). Rewrite imports: `from drydocs.loaders.base import BaseLoader`, `from ..models import ...`, `folders.py` `from .. import parse_folder_name`, fix each `cypher_path` parent. Fix `pyproject` asset packaging globs. **Fix `test_controlm_cypher.py` lines 10–11 hardcoded paths.** Collapse cli.py 5 loader imports → 1 barrel import.
- **Phase 3 — Loader registry:** create `registry.py` (`VENDOR_LOADERS`, `INGEST_CHAIN`, `IngestStage`).
- **Phase 4 — Extract `cli_support.py`** (before vendor CLI needs helpers; pre-empts cycle).
- **Phase 5 — Move 3 vendor commands** into `drydocs_core/controlm/cli.py`; delete them + ALL vendor imports from `cli.py`; merge registries. Boundary check: only `from .controlm.cli import controlm_app` (+ optional registry line) remains in cli.py.
- **Phase 6 — Enforce boundary:** add `tests/unit/test_vendor_boundary.py` — AST guard: no core module imports `drydocs.controlm` except allowlisted `drydocs.cli`.
- **Phase 7 — (Optional) entry-point plugin** discovery to remove the last static vendor import.

## Risks

- **Asset packaging regression (highest):** moved `.cypher`/`.sql` may drop from wheel — verify poetry include globs; add `cypher_path.exists()` runtime test.
- **`test_controlm_cypher.py` path pins** must move in lockstep with Phase 2.
- **`SQL_DIR`** must repoint to vendor sql dir (owned by vendor CLI).
- **Circular import** avoided by Phase 4 before Phase 5 + base stays in core.
- **Stale `__pycache__`** can mask moves — clear if imports misbehave.

## Test impact (10 unit tests)

Need edits: `test_controlm_models`, `test_variable_classifier`, `test_variable_staging` (models repoint, Phase 1); `test_controlm_cypher` (path repoint, Phase 2). Unaffected: tests importing `drydocs.controlm.*` (that namespace's existing modules don't move), `test_base_loader_smoke`, `test_namespaces`, `test_schema`.

## Critical files

- drydocs/cli.py
- drydocs/loaders/__init__.py
- drydocs_core/models/__init__.py
- drydocs/loaders/controlm.py
- tests/unit/test_controlm_cypher.py
