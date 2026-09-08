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
    """Render FIRST, then open. The artifact is never opened until there is
    content to put in it.

    THE ORDER IS THE WHOLE FUNCTION. This used to read
    ``with out.open("w") as fh: fh.write(render_schema())`` — and ``open("w")``
    TRUNCATES, so the render ran with the committed file already emptied. Any
    failure inside ``create_app()`` — an unset ``DRYDOCS_DATA_ROOT`` is the one
    that actually happens (G81) — left a zero-byte ``openapi.json`` in the
    working tree. That reads as a corrupt commit rather than as a failed run,
    and ``npm run api:types`` then fails on an empty document one step later
    with nothing pointing back at the cause. Observed 2026-09-06 during Z6.
    """
    return _write(out, render_schema())


def _write(out: Path, text: str) -> Path:
    """The write half, kept separate so the render can be attempted and reported
    on its own (see :func:`main`) without a caller re-implementing this file's
    encoding and newline discipline."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return out


def check_schema(out: Path = DEFAULT_OUT) -> bool:
    """True when the committed file equals a fresh dump. Reads only."""
    return _matches(out, render_schema())


def _matches(out: Path, text: str) -> bool:
    """The comparison, in one place. :func:`main` already holds a rendered schema
    by the time it reaches ``--check`` and must not render a second one — but
    both callers deciding separately what "matches" means is how two answers to
    one question start to disagree."""
    return out.is_file() and out.read_text(encoding="utf-8") == text


def _relative(path: Path) -> str:
    """The path as the repo names it, falling back to the absolute one for an
    ``--out`` outside the tree (a ``tmp_path`` in the tests). ``relative_to``
    RAISES on a path outside the repo, and a crash while REPORTING a failure is
    how the real cause gets lost."""
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit 1 if the committed schema differs from a fresh dump",
    )
    ns = ap.parse_args(argv)
    where = _relative(ns.out)

    # The render is attempted BEFORE anything is opened, and its failure is
    # reported as a failure rather than left as a traceback the next step in the
    # chain inherits. The message says the artifact is untouched because that is
    # now true by construction, and because "did this just corrupt my working
    # tree" is the first question a failed dump raises.
    try:
        text = render_schema()
    except Exception as exc:  # a CLI boundary: report it, never re-raise it
        print(f"openapi dump FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(f"{where} was NOT modified.", file=sys.stderr)
        if isinstance(exc, ImportError):
            print(
                "fastapi lives in the optional api group: poetry install --with api",
                file=sys.stderr,
            )
        return 1

    if ns.check:
        if _matches(ns.out, text):
            print(f"openapi schema up to date: {where}")
            return 0
        print(
            f"openapi schema STALE: {where} differs from create_app().openapi()"
            " — run `poetry run python scripts/dump_openapi.py` then `npm run api:types` in web/",
            file=sys.stderr,
        )
        return 1
    print(f"wrote {_relative(_write(ns.out, text))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
