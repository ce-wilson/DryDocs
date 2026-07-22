---
name: run-drydocs
description: Run, start, build, test, or screenshot DryDocs. Use this skill to launch the DryDocs CLI, run the ingest-controlm pipeline, execute m3-verify, or validate the model/adapter layer without Neo4j.
---

DryDocs is a Python CLI (Poetry, Python 3.11+) that loads Control-M job graph data into a Neo4j knowledge graph. The entry point is `poetry run drydocs`. Most integration commands require a live Neo4j instance configured in `.env`. The model and adapter layers — the code most PRs touch — run without Neo4j and are validated by the smoke script.

## Prerequisites

```powershell
# Python 3.11+ required; 3.12 confirmed working.
python --version

# Install deps (already done if .venv exists)
poetry install
```

## Agent path — smoke script (no Neo4j needed)

Run from repo root:

```powershell
powershell .claude/skills/run-drydocs/smoke.ps1
```

This verifies:
- CLI entry point (`drydocs --help`, subcommand `--help`)
- All five Control-M Pydantic row models against bundled sample CSVs (8 folders, 17 jobs, 10 conditions_in, 10 dependencies)
- Folder name parser (environment/LOB/type decoding)
- Unit test suite (full suite green; the only expected skips are the gitignored-sample-backed tests — see Gotchas)

## Direct model/adapter invocation (for PRs touching internal code)

Import and exercise specific layers without the CLI:

```powershell
poetry run python 2>&1 << 'EOF'
from drydocs_core.models.controlm import ControlMFolderRow
from drydocs_core.adapters.csv_adapter import CsvAdapter
from pathlib import Path

with CsvAdapter(Path("drydocs/data/samples/controlm_folders__sample.csv")) as a:
    rows = [ControlMFolderRow(**r) for r in a.rows()]
print(f"{len(rows)} rows validated")
EOF
```

CsvAdapter is a context manager — `with` is required; direct iteration is not supported.

## Full integration chain (requires Neo4j)

The target is the **local Docker EE container** — canonical container name, ports,
and database names live in `config/dev-environment.yaml` (Aura was ruled out
2026-07-06). Configure `.env` at repo root — note Docker may remap the host ports
(see `internal/helpmeloginlocalneo4j.md`; check with `docker port <container>`):
```
NEO4J_URI=bolt://localhost:7687     # host-mapped Bolt port — verify, defaults may be remapped
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>           # local secret, never committed
NEO4J_DATABASE=drydocs              # topology db (ADR 0002), not the EE home db
```

Then:
```powershell
poetry run drydocs check                       # verify Neo4j + APOC
poetry run drydocs bootstrap                   # apply constraints + ontology seed
poetry run drydocs apply-ontology-supplement   # base + ControlM anchor terms (idempotent)
poetry run drydocs apply-catalog-supplement    # Catalog ontology (idempotent)
poetry run drydocs apply-seal-supplement       # SEAL ontology (idempotent)
poetry run drydocs apply-registry-supplement   # software-registry ontology (idempotent)
poetry run drydocs ingest-controlm             # full M3 chain: folders -> jobs -> conditions -> deps
poetry run drydocs m1-verify                   # assert M1 invariants
poetry run drydocs m3-verify                   # assert M3 invariants; all should be "yes"
```

Offline (no Neo4j):
```powershell
poetry run drydocs analyze-variables           # variable taxonomy coverage report
poetry run drydocs load --help                 # single-loader: folders/jobs/conditions/deps from CSV or Oracle
```

Sample-mode (bundled CSVs, no Oracle):
```powershell
poetry run drydocs ingest-controlm        # default: uses drydocs/data/samples/
```

Oracle mode:
```powershell
poetry run drydocs ingest-controlm --use-oracle --folder-filter "CCB_AUTO_%"
```

**Run logging (HITL trail):** every `--use-oracle` extract writes a per-run SQL log —
run metadata → handshake → the exact SQL (binds rendered for review; execution stays
parameterized) → the CSV result — and every LOADER run writes a companion
`load.<loader>.<stamp>.log` (header/meta → captured WARN stream + reject detail →
summary footer). Both go to `DRYDOCS_LOGDIR` (fallback `SPIDERP_LOGDIR`, default
`~/logs/DryDocs`, outside the repo, never committed). The console echoes
`[sql-log]`/`[run-log]` paths. Full guide: `docs/oracle-sql-logging.md`.

## Run (human path)

Same as agent path — DryDocs is pure CLI with no interactive TUI or GUI. Commands complete and return.

## Tests

```powershell
poetry run pytest tests/unit/ -v
```

Full suite green; the only expected skips are sample-backed tests (see Gotchas).

End-to-end (opt-in, needs Docker — spins a throwaway Neo4j via testcontainers and
drives bootstrap → supplement → ingest-controlm → invariants through the real CLI):

```powershell
poetry run pytest tests/integration -m integration -q
```

It is deselected from every default run (`-m "not integration"` in pyproject) and
auto-skips when Docker is down. First run pulls the `neo4j:5.26` image.

## Gotchas

**Expected skips (production sample CSV absent):** a few tests in
`test_variable_classifier.py` / `test_variable_staging.py` skip with
`production sample CSV absent (gitignored); regenerate locally via psgmgr`. Expected —
the CSV is deliberately gitignored; regenerate via an Oracle extract if you need them.

**Core imports live in `drydocs_core`.** Since the Phase B relocate (2026-07-10, ADR
0002-A-1), models/adapters/parser/config are `drydocs_core.*`; `drydocs.*` is the
component remainder (loaders/cli/review/plan/docgen). `ModuleNotFoundError: No module
named 'drydocs.models'` means a pre-relocate path.

**CsvAdapter is a context manager, not iterable.** `list(adapter)` raises `TypeError: 'CsvAdapter' object is not iterable`. Always use `with CsvAdapter(...) as a: for r in a.rows()`.

**Docker may remap the Neo4j host ports.** The local EE container's 7474/7687 can land
on different host ports (e.g. 7476/7689). `drydocs check` failing with a connection
refusal usually means the `.env` URI points at the wrong host port — check with
`docker port <container>` (see `internal/helpmeloginlocalneo4j.md`).

**Rich output encoding on Windows.** The CLI uses Rich for terminal output with box-drawing characters. Capture output with `| Out-String` in PowerShell before doing string matching, or pipe to Python: `poetry run drydocs --help | python -c "import sys; print(sys.stdin.read())"`.

## Troubleshooting

**Connection refused / `ServiceUnavailable` on `drydocs check`** → the local Neo4j
container isn't running, or the host port in `.env` is stale (Docker remap — see
Gotchas). Run the smoke script instead for offline validation.

**`NEO4J_PASSWORD is empty`** → `.env` file missing or `NEO4J_PASSWORD=` not set. Copy `.env.example` to `.env` and fill in values.

**`APOC not available`** → the Neo4j container lacks the APOC plugin. Required for `bootstrap`. Start the container with `NEO4J_PLUGINS='["apoc"]'` (or drop the APOC jar into the container's plugins dir).

**Import errors on `drydocs.*` / `drydocs_core.*`** → `poetry install` was not run or the venv is not activated. Run `poetry install` from repo root.
