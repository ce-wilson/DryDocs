"""Write drydocs-api's OpenAPI schema to web/src/generated/openapi.json (O70).

The console's TypeScript client is generated from this file (``npm run
api:types`` in ``web/``), so the file is the one place the browser learns the
API's paths, parameter shapes and response types. It follows the same
generated-artifact discipline as gates.json and load-map.json: committed,
deterministic, and guarded — ``--check`` exits 1 when the committed file no
longer matches a fresh dump, and ``tests/unit/test_openapi_client.py`` asserts
the same thing where fastapi is installed.

The schema is read from the importable object (``create_app().openapi()``),
never from ``/openapi.json`` over HTTP (J37). ``create_app()`` builds the intake
store at import and the data root has no default (G81), so ``DRYDOCS_DATA_ROOT``
must be set — the same condition the API itself boots under.

Usage (repo root)::

    poetry run python scripts/dump_openapi.py          # write
    poetry run python scripts/dump_openapi.py --check  # exit 1 on drift
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "web" / "src" / "generated" / "openapi.json"


def render_schema() -> str:
    """The schema as the committed file holds it: sorted keys, two-space
    indent, one trailing newline. Sorting is what makes the dump deterministic
    across pydantic's dict ordering; the app is otherwise built the same way
    every time."""
    from drydocs_api.app import create_app

    schema = create_app().openapi()
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def write_schema(out: Path = DEFAULT_OUT) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_schema())
    return out


def check_schema(out: Path = DEFAULT_OUT) -> bool:
    """True when the committed file equals a fresh dump."""
    if not out.is_file():
        return False
    return out.read_text(encoding="utf-8") == render_schema()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit 1 if the committed schema differs from a fresh dump",
    )
    ns = ap.parse_args(argv)
    if ns.check:
        if check_schema(ns.out):
            print(f"openapi schema up to date: {ns.out.relative_to(REPO).as_posix()}")
            return 0
        print(
            f"openapi schema STALE: {ns.out.relative_to(REPO).as_posix()} differs from create_app().openapi()"
            " — run `poetry run python scripts/dump_openapi.py` then `npm run api:types` in web/",
            file=sys.stderr,
        )
        return 1
    written = write_schema(ns.out)
    print(f"wrote {written.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
