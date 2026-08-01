"""Mapping-store analytics (plan M4) — the dataframe companion path.

Prefers DuckDB (reads the SAME SQLite file via its sqlite extension; from
there pandas/Polars/Parquet are one call away) and falls back to stdlib
sqlite3 when duckdb is not installed — the views answer identically either
way, which is the point: one store, two engines.

    $env:PYTHONPATH = "."; python scripts/mapping_analytics.py [--db var/mapping.db]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from drydocs_core.mapping_store import DEFAULT_DB_PATH, build

QUERIES = {
    "lifecycle (v_status_summary)": "SELECT status, n FROM v_status_summary",
    "active vocabulary terms": "SELECT count(*) AS n FROM v_vocab_active",
    "quintuples with a relationship": (
        "SELECT count(*) AS n FROM v_mapping_quintuple WHERE relationship_type IS NOT NULL"
    ),
    "property-supplement rows (no edge)": (
        "SELECT count(*) AS n FROM v_mapping_quintuple WHERE relationship_type IS NULL"
    ),
    "manual rows": "SELECT count(*) AS n FROM manual_mapping",
    "manual conflicts (v_manual_conflicts)": "SELECT count(*) AS n FROM v_manual_conflicts",
    "PROV coverage of applied+confirmed": (
        "SELECT prov_maps_to, count(*) AS n FROM v_mapping_quintuple "
        "WHERE status IN ('applied','confirmed') GROUP BY prov_maps_to ORDER BY n DESC"
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    args = parser.parse_args()
    db = Path(args.db)
    if not db.exists():
        build(db).close()

    try:
        import duckdb

        conn = duckdb.connect()
        conn.execute(f"ATTACH '{db.as_posix()}' AS m (TYPE sqlite)")
        conn.execute("USE m")
        engine = f"duckdb {duckdb.__version__} (sqlite attach)"
        run = lambda sql: conn.execute(sql).fetchall()  # noqa: E731
    except ImportError:
        import sqlite3

        conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
        engine = "stdlib sqlite3 (duckdb not installed — fallback)"
        run = lambda sql: conn.execute(sql).fetchall()  # noqa: E731

    print(f"engine: {engine}\nstore:  {db}\n")
    for title, sql in QUERIES.items():
        rows = run(sql)
        if len(rows) == 1 and len(rows[0]) == 1:
            print(f"{title}: {rows[0][0]}")
        else:
            print(f"{title}:")
            for r in rows:
                print(f"  {' | '.join(str(v) for v in r)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
