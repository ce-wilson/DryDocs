---
name: run-drydocs
description: Run, start, build, test, or screenshot DryDocs. Use this skill to launch the DryDocs CLI, run the ingest-controlm pipeline, execute m3-verify, or validate the model/adapter layer without Neo4j.
---

DryDocs is a Python CLI (Poetry, Python 3.11+) that loads Control-M job graph data into a Neo4j knowledge graph. The entry point is `poetry run drydocs`. Most integration commands require a live Neo4j instance configured in `.env`. The model and adapter layers — the code most PRs touch — run without Neo4j and are validated by the smoke script.

## Prerequisites

```powershell
# Python 3.11+ required; 3.13 confirmed working.
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
- All five Control-M Pydantic row models against bundled sample CSVs (8 folders, 13 jobs, 10 conditions_in, 10 dependencies)
- Folder name parser (environment/LOB/type decoding)
- Unit test suite (159 pass, 4 skipped — see Gotchas)

## Direct model/adapter invocation (for PRs touching internal code)

Import and exercise specific layers without the CLI:

```powershell
poetry run python 2>&1 << 'EOF'
from drydocs.models.controlm import ControlMFolderRow
from drydocs.adapters.csv_adapter import CsvAdapter
from pathlib import Path

with CsvAdapter(Path("drydocs/data/samples/controlm_folders__sample.csv")) as a:
    rows = [ControlMFolderRow(**r) for r in a.rows()]
print(f"{len(rows)} rows validated")
EOF
```

CsvAdapter is a context manager — `with` is required; direct iteration is not supported.

## Full integration chain (requires Neo4j)

Configure `.env` at repo root:
```
NEO4J_URI=neo4j+s://<instance>.databases.neo4j.io
NEO4J_USER=<user>
NEO4J_PASSWORD=<password>
NEO4J_DATABASE=<database>
```

Then:
```powershell
poetry run drydocs check                       # verify Neo4j + APOC
poetry run drydocs bootstrap                   # apply constraints + ontology seed
poetry run drydocs apply-ontology-supplement   # base ontology (idempotent)
poetry run drydocs apply-m3-supplement         # ControlM anchor terms (idempotent)
poetry run drydocs apply-catalog-supplement    # Catalog ontology (idempotent)
poetry run drydocs apply-seal-supplement       # SEAL ontology (idempotent)
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

## Run (human path)

Same as agent path — DryDocs is pure CLI with no interactive TUI or GUI. Commands complete and return.

## Tests

```powershell
poetry run pytest tests/unit/ -v
```

159 pass, 4 skipped (see Gotchas).

## Gotchas

**4 skipped tests (PyYAML not installed):**
`tests/unit/test_schema.py` has 4 tests that skip with `SKIPPED: PyYAML not installed`. PyYAML is not in `pyproject.toml`. These are expected skips, not failures.

**CsvAdapter is a context manager, not iterable.** `list(adapter)` raises `TypeError: 'CsvAdapter' object is not iterable`. Always use `with CsvAdapter(...) as a: for r in a.rows()`.

**Neo4j Aura requires network access.** `drydocs check` will fail with `gaierror: [Errno 11001] getaddrinfo failed` in any environment without outbound internet (CI sandbox, restricted corporate network). The model/adapter layer and unit tests are the correct validation path in those environments.

**PyYAML not installed** — 4 schema tests are skipped with `SKIPPED: PyYAML not installed`. This is expected; PyYAML is not in `pyproject.toml`.

**Rich output encoding on Windows.** The CLI uses Rich for terminal output with box-drawing characters. Capture output with `| Out-String` in PowerShell before doing string matching, or pipe to Python: `poetry run drydocs --help | python -c "import sys; print(sys.stdin.read())"`.

## Troubleshooting

**`gaierror: getaddrinfo failed`** → Neo4j Aura host not reachable from this network. Run smoke script instead for local validation.

**`NEO4J_PASSWORD is empty`** → `.env` file missing or `NEO4J_PASSWORD=` not set. Copy `.env.example` to `.env` and fill in values.

**`APOC not available`** → Neo4j instance does not have APOC plugin. Required for `bootstrap`. Enable APOC in your Aura instance settings.

**Import errors on `drydocs.*`** → `poetry install` was not run or the venv is not activated. Run `poetry install` from repo root.
