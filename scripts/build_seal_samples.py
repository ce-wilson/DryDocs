"""build_seal_samples.py — generate the two SEAL loader sample CSVs.

``drydocs/data/`` is gitignored, so these fixtures are GENERATED per machine rather
than committed; run this once before `drydocs refresh-reference` or the chain skips
both SEAL stages and writes no attribution nodes. Logic lives in
``drydocs.seal_samples``; this is the CLI. Stdlib + PyYAML only.

Usage:
    poetry run python scripts/build_seal_samples.py
    poetry run python scripts/build_seal_samples.py --capture path/to/capture.yaml --out-dir path/
"""

from __future__ import annotations

import argparse
from pathlib import Path

from drydocs.seal_samples import DEFAULT_CAPTURE_PATH, DEFAULT_SAMPLES_DIR, write_samples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, default=DEFAULT_CAPTURE_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_SAMPLES_DIR)
    args = parser.parse_args()
    for path in write_samples(args.capture, args.out_dir):
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
