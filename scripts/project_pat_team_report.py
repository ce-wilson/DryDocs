"""project_pat_team_report.py — raw PAT team report -> the two dev-team loader files (G82).

Logic lives in ``drydocs.pat_projection``; this is the CLI. The raw report and the
two projected files are Internal and belong under DRYDOCS_DATA_ROOT (the
``pat/`` drop dir the source registry declares), never in the tree.

Usage:
    poetry run python scripts/project_pat_team_report.py <raw.csv> --out-dir <dir>
    poetry run python scripts/project_pat_team_report.py <raw.csv> --out-dir <dir> --header-map headers.yaml
    drydocs refresh-reference --samples-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from drydocs.pat_projection import ProjectionError, load_header_map, project_team_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_csv", type=Path, help="the raw PAT team report export (csv)")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--header-map",
        type=Path,
        default=None,
        help="YAML {logical_field: 'Raw Header'} overriding DEFAULT_HEADER_MAP spellings",
    )
    args = parser.parse_args()
    try:
        report = project_team_report(args.raw_csv, args.out_dir, load_header_map(args.header_map))
    except ProjectionError as exc:
        print(f"projection refused: {exc}", file=sys.stderr)
        return 2
    for line in report.lines():
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
