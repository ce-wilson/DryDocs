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
- Unit test suite (66 pass, 4 pre-existing known failures — see Gotchas)

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
poetry run drydocs check                  # verify Neo4j + APOC
poetry run drydocs bootstrap              # apply constraints + ontology seed
poetry run drydocs apply-m3-supplement    # seed ControlM anchor terms (idempotent)
poetry run drydocs ingest-controlm        # full M3 chain: folders -> jobs -> conditions -> deps
poetry run drydocs m3-verify              # assert 8 invariants; all should be "yes"
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

66 pass, 4 known failures (see Gotchas).

## Gotchas

**4 pre-existing test failures in the suite:**
- `test_conditions_share_composite_key` and `test_dependencies_materializes_derived_edge`: tests assert `:DEPENDS_ON` relationship name, but the Cypher uses `:WAS_INFORMED_BY` (the PROV-O term). The tests are stale; the code is correct.
- `test_real_folder_name_from_recursive_sample` and `test_auto_appcode`: tests expect `"Smart folder"` for type code `G`, but the parser returns `"Group Table/Smart folder"` (the BMC canonical term). Tests are stale.

**CsvAdapter is a context manager, not iterable.** `list(adapter)` raises `TypeError: 'CsvAdapter' object is not iterable`. Always use `with CsvAdapter(...) as a: for r in a.rows()`.

**Neo4j Aura requires network access.** `drydocs check` will fail with `gaierror: [Errno 11001] getaddrinfo failed` in any environment without outbound internet (CI sandbox, restricted corporate network). The model/adapter layer and unit tests are the correct validation path in those environments.

**PyYAML not installed** — 4 schema tests are skipped with `SKIPPED: PyYAML not installed`. This is expected; PyYAML is not in `pyproject.toml`.

**Rich output encoding on Windows.** The CLI uses Rich for terminal output with box-drawing characters. Capture output with `| Out-String` in PowerShell before doing string matching, or pipe to Python: `poetry run drydocs --help | python -c "import sys; print(sys.stdin.read())"`.

## Troubleshooting

**`gaierror: getaddrinfo failed`** → Neo4j Aura host not reachable from this network. Run smoke script instead for local validation.

**`NEO4J_PASSWORD is empty`** → `.env` file missing or `NEO4J_PASSWORD=` not set. Copy `.env.example` to `.env` and fill in values.

**`APOC not available`** → Neo4j instance does not have APOC plugin. Required for `bootstrap`. Enable APOC in your Aura instance settings.

**Import errors on `drydocs.*`** → `poetry install` was not run or the venv is not activated. Run `poetry install` from repo root.
