# scripts/ — operational ingestion entry points

Thin shell wrappers for running DryDocs ingestion on a schedule (Control-M / cron).
They add **no logic** — each just runs the canonical `poetry run drydocs ...` chain
and fails fast. The Python CLI remains the source of truth; these exist so an
operator/scheduler has a stable, documented command to invoke.

| Script | Runs | Status |
|--------|------|--------|
| `ingest.sh` | check → bootstrap → ontology supplements → `ingest-controlm` → m1/m3-verify | ✅ all commands present on this branch |
| `embed.sh` | `drydocs embed` (vector embeddings on `:Searchable`) | ⏳ **forward-looking** — needs the `embed` command from `feat/llm-nav-p0-vector`; guarded, exits cleanly if absent |
| `ingest_jpmc_reports.py` | Full ingestion of JPMorgan Chase public annual report PDFs into Neo4j (`ddcontext`) | ✅ runnable — requires `poetry run python scripts/ingest_jpmc_reports.py` |

## Usage

```bash
# Sample mode (bundled CSVs, no Oracle)
scripts/ingest.sh

# Oracle mode, scoped — args pass through to ingest-controlm
scripts/ingest.sh --use-oracle --folder "CCB_AUTO_%"

# Vector pass (after ingest; requires the P0 embed command)
scripts/embed.sh

# Ingest JPMorgan Chase public annual report PDFs into ddcontext
# Requires: PDFs in repo root, Neo4j Enterprise running on bolt://localhost:7687
poetry run python scripts/ingest_jpmc_reports.py
```

`ingest.sh` and `embed.sh` read Neo4j connection settings from the repo-root `.env`
(see `.claude/skills/run-drydocs/SKILL.md` for the full CLI reference and `.env` keys).

`ingest_jpmc_reports.py` connects directly to `bolt://localhost:7687` (credentials:
`neo4j` / `drydocs-dev`) and targets the `ddcontext` database.

## Why two scripts, why separate

The embedding pass is deliberately split from bulk load so the MERGE-heavy ingest
isn't taxed by vector-index writes — see `knowledge/ARCHITECTURE.md` finding **T7**.
Run `ingest.sh` first, then `embed.sh`.

## Naming caveat — these are NOT the `.sh` the loader classifies

Do not confuse these operational wrappers with the `.sh`/`.ksh` references inside
`drydocs/controlm/commands.py`. Those match the **command strings of the Control-M
jobs being ingested** (e.g. `run_data_validation.sh` → `VALIDATION_UTIL`) — i.e.
shell scripts as *graph data going in*. The scripts here run *DryDocs itself*.
Opposite directions; don't conflate them.

> Status: added as operational scaffolding ahead of go-live. `ingest.sh` is runnable
> today against a configured Neo4j; `embed.sh` activates once the P0 vector work lands.
