"""Build, extract, load and register the synthetic source stand-ins.

    python scripts/build_synthetic_sources.py --bundle
    python scripts/build_synthetic_sources.py --extract [--out-root DIR]
    python scripts/build_synthetic_sources.py --extract --duckdb
    python scripts/build_synthetic_sources.py --datahub-json PATH

Every step reads ``config/source-descriptors.yaml``; nothing here is typed by
hand. ``--bundle`` rewrites ``drydocs/data/samples/synthetic-sources.json.gz``
(byte-stable: a diff means the generator or the config changed). ``--extract``
writes the CSVs into the landing zones the loaders read under the data root;
``--duckdb`` then loads them into ``<data_root>/<synthetic.duckdb_file>`` when
the ``duckdb`` package is importable. ``--datahub-json`` writes the DataHub
MCP file for ``datahub lite import --file`` (or any ``file``-source recipe under
``config/datahub/``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from drydocs.source_registration import bundle as bundle_mod
from drydocs.source_registration.datahub_emit import write_mcp_file
from drydocs.source_registration.synthetic import SyntheticSources
from drydocs_core.data_root import resolve_data_root
from drydocs_core.source_descriptors import SourceDescriptors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", action="store_true", help="rewrite the tracked .json.gz")
    ap.add_argument("--extract", action="store_true", help="extract the bundle to the data root")
    ap.add_argument("--out-root", type=Path, help="extraction root (default: DRYDOCS_DATA_ROOT)")
    ap.add_argument("--duckdb", action="store_true", help="load extracted CSVs into DuckDB")
    ap.add_argument("--datahub-json", type=Path, help="write the DataHub MCP file here")
    args = ap.parse_args(argv)
    if not (args.bundle or args.extract or args.datahub_json):
        ap.error("nothing to do: pass --bundle, --extract and/or --datahub-json")

    desc = SourceDescriptors.from_yaml()
    if args.bundle:
        out = bundle_mod.write_bundle(desc)
        print(f"bundle  {out} ({out.stat().st_size} bytes)")

    extracted = ()
    if args.extract:
        root = args.out_root or resolve_data_root()
        extracted = bundle_mod.extract(desc, out_root=root)
        for e in extracted:
            print(f"extract {e.placement:6} {e.source_id:45} {e.path}")
        if args.duckdb:
            try:
                import duckdb  # noqa: F401 - probe only

            except ImportError:
                print("duckdb  SKIPPED: the duckdb package is not importable", file=sys.stderr)
            else:
                from drydocs.source_registration.duckdb_load import load

                db = root / desc.synthetic.get("duckdb_file", "synthetic/drydocs-synthetic.duckdb")
                counts = load(desc, extracted, db)
                for name, n in sorted(counts.items()):
                    print(f"duckdb  {name:32} {n:6} rows")
                print(f"duckdb  {db}")

    if args.datahub_json:
        tables = SyntheticSources(desc).tables()
        out = write_mcp_file(desc, args.datahub_json, tables)
        print(f"datahub {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
