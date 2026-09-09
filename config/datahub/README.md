# DataHub recipes for the source registration

Two recipes, both operator-side. DataHub is not a repo dependency: install it in
its own Python environment (`pip install "acryl-datahub[datahub-lite,sqlalchemy]"`,
Python 3.11-3.13) and run the CLI from there. Every path inside a recipe is relative to
`DRYDOCS_DATA_ROOT`, so `cd` there before `datahub ingest`. That is a constraint,
not a style choice: DataHub's `file` source parses its path as a URL, so an
absolute Windows path (`C:/...`) is read as scheme `c` and refused
(`Did not find a registered class for c`); a relative path has no scheme.

| Recipe | Source | Sink | What it does |
|---|---|---|---|
| `lite-import.dhub.yml` | `file` — the MCP file `scripts/build_synthetic_sources.py --datahub-json` writes | `datahub-lite` (DuckDB) | registers the 19 systems as containers and the 30 datasets as assets, tagged on the five descriptor axes |
| `duckdb-profile.dhub.yml` | `sqlalchemy` over `duckdb:///` — the synthetic DuckDB file `--extract --duckdb` loads | `datahub-lite` (same file) | profiles every synthetic table (row counts, null counts, distinct counts, min/max, sample values) — DataHub's own profiler, no Great Expectations |

```
python scripts/build_synthetic_sources.py --bundle
python scripts/build_synthetic_sources.py --extract --duckdb
python scripts/build_synthetic_sources.py --datahub-json "$DRYDOCS_DATA_ROOT/datahub/drydocs-sources.mcp.json"
cd "$DRYDOCS_DATA_ROOT"
datahub ingest -c <repo>/config/datahub/lite-import.dhub.yml
datahub ingest -c <repo>/config/datahub/duckdb-profile.dhub.yml
datahub lite init --type duckdb --file datahub/drydocs-lite.duckdb   # once: point the lite CLI at the sink
datahub lite ls /                                                  # browse what landed
datahub lite get --urn "urn:li:tag:drydocs.access.human"
```

Two things the `datahub lite` CLI needs that `datahub ingest` does not, both
measured on the first run (Windows, Git Bash, 2026-09-09). It reads
`~/.datahubenv`, which `datahub init` writes interactively; a hand-written one
with a `gms:` block (any server, empty token — nothing is contacted) and a
`lite: {type: duckdb, config: {file: <absolute path to the lite file>}}` block is
enough. And under Git Bash the `/` in `datahub lite ls /` is rewritten to the
MSYS root unless `MSYS_NO_PATHCONV=1` is exported first — the symptom is
`Path not found: C:/Program Files/Git/`.

The lite file (`datahub/drydocs-lite.duckdb` under the data root, per
`config/source-descriptors.yaml` `datahub.lite_file`) is itself a DuckDB
database: `metadata_aspect_v2(urn, aspect_name, version, metadata, ...)` answers
"which datasets are `access = fid`" with plain SQL.

OpenLineage was checked for the same job and has no profiler — its run events
carry schema and lineage facets only — so profiling stays with DataHub.
Reference: DataHub source tree at `dea0f9c184b8d413696b6f1992e49528fb30dd76`
(2026-08-30, Apache-2.0), `metadata-ingestion/src/datahub/ingestion/source/sql/`
and `ingestion/sink/datahub_lite.py`; OpenLineage at `b995ee00` (2026-08-28,
Apache-2.0), `spec/facets/`.
