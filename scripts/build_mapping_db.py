"""Build the mapping-store materialization (plan M0).

    $env:PYTHONPATH = "."; python scripts/build_mapping_db.py
    # options:
    #   --db <path>        output SQLite file (default var/mapping.db)
    #   --dump-dir <path>  also write the deterministic per-table CSV dumps

The output is DERIVED — never commit var/mapping.db; the committed YAML/CSV
sources (and, when adopted, the CSV dumps) are what the gate reviews.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from drydocs_core.mapping_store import DEFAULT_DB_PATH, build, dump_csv, tables


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--dump-dir", default=None)
    args = parser.parse_args()

    conn = build(args.db)
    try:
        counts = {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in tables(conn)}
        print(f"built {args.db}")
        for t, n in counts.items():
            print(f"  {t}: {n}")
        if args.dump_dir:
            for p in dump_csv(conn, args.dump_dir):
                print(f"  dump: {p}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
