"""Source registration: the descriptor axes turned into catalog assets and
synthetic stand-ins. Pure config in, files out — no graph, no network.

Modules: ``synthetic`` (seeded Matrix-themed CSVs), ``bundle`` (the tracked
``.json.gz`` and its extraction into landing zones), ``duckdb_load`` (optional
project-local DuckDB), ``datahub_emit`` (DataHub MCP file). Driven by
``scripts/build_synthetic_sources.py``.
"""
