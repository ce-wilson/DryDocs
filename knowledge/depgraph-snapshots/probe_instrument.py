"""Capability probe for the depgraph instrument (U7).

`snapshot.ps1` shells out to a *sibling repo* (`depgraph`) to produce the code
graph, so the checked-out revision decides what the scan can actually see — and
on 2026-07-28 a checkout without the multi-root resolver wrote a 105-edge
snapshot (vs the truthful 370) that looked completely normal. Nothing in the
artifact recorded which instrument produced it.

This script answers one question — *what can the depgraph on PYTHONPATH
actually do?* — as JSON on stdout::

    {"multi_root": true, "tree": false, "version": "0.1.0", "detail": {...}}

It deliberately reports rather than decides: it exits 0 even when a capability
is missing, and `snapshot.ps1` owns the refusal. That keeps the policy in one
place and makes this script safe to run for diagnosis.

Probes are **behavioural, not version strings**. depgraph's `0.1.0` spans both
the broken and the fixed resolver, so a version comparison would be actively
wrong; only what the code can *do* is decisive. (The fork that made this acute —
`--tree` and the multi-root fix on branches neither of which was an ancestor of
the other — was consolidated onto `main` on 2026-07-28.)
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from collections.abc import Callable
from typing import Any

#: Capability -> why the snapshot needs it. Surfaced in the refusal message.
CAPABILITY_REASONS: dict[str, str] = {
    "multi_root": (
        "cross-root and same-package absolute imports resolve only when every "
        "scan root shares one namespace; without it the edge count silently collapses"
    ),
    "tree": "`scan --tree` walks the full file tree (-Tree snapshots)",
    "ts_imports": (
        "a plain scan emits first-party .ts/.tsx/.js/.jsx import edges (O42); "
        "without it the front-end reads as 94 edge-less nodes and a diff "
        "against a TS-capable snapshot shows a phantom edge collapse"
    ),
}

Importer = Callable[[str], Any]


def _probe_multi_root(import_module: Importer) -> bool:
    """True when the import extractor exposes the shared-namespace entry point.

    This is the U6 fix: `extract_many` takes every root at once, where the old
    `extract` ran each root in isolation.
    """
    try:
        mod = import_module("depgraph.extractors.python_imports")
        return hasattr(mod.PythonImportExtractor, "extract_many")
    except Exception:
        return False


def _probe_tree(import_module: Importer) -> bool:
    """True when the real CLI advertises `--tree` on its `scan` subcommand.

    Driving the actual parser (rather than sniffing for a `file_tree` module)
    keeps this honest: the flag is what `snapshot.ps1` passes, so the flag is
    what gets tested.
    """
    try:
        cli = import_module("depgraph.cli")
    except Exception:
        return False
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            cli.main(["scan", "--help"])
    except SystemExit:
        pass  # --help always exits; the text we want is already in the buffer
    except Exception:
        return False
    return "--tree" in buf.getvalue()


def _probe_ts_imports(import_module: Importer) -> bool:
    """True when a PLAIN scan will emit TS/JS import edges.

    Behavioural like the others: membership in ``default_extractors()`` is the
    thing `scan()` actually consults, so it is the thing probed — an extractor
    that exists but is opt-in would still leave a plain snapshot without
    front-end edges.
    """
    try:
        mod = import_module("depgraph.extractors")
        return any(e.name == "ts-imports" for e in mod.default_extractors())
    except Exception:
        return False


def _version(import_module: Importer) -> str | None:
    try:
        return getattr(import_module("depgraph"), "__version__", None)
    except Exception:
        return None


def probe(import_module: Importer | None = None) -> dict[str, Any]:
    """Report what the importable depgraph can do.

    `import_module` is injectable so the decision logic is testable without a
    depgraph checkout present.
    """
    if import_module is None:
        import importlib

        import_module = importlib.import_module
    importable = True
    try:
        import_module("depgraph")
    except Exception:
        importable = False
    return {
        "multi_root": _probe_multi_root(import_module),
        "tree": _probe_tree(import_module),
        "ts_imports": _probe_ts_imports(import_module),
        "version": _version(import_module),
        "importable": importable,
    }


def missing(caps: dict[str, Any], required: list[str]) -> list[str]:
    """Which of `required` the probed instrument cannot do."""
    return [name for name in required if not caps.get(name)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="probe_instrument",
        description="report depgraph capabilities as JSON (U7)",
    )
    ap.add_argument(
        "--require",
        action="append",
        default=[],
        choices=sorted(CAPABILITY_REASONS),
        help="exit 1 if this capability is absent (default: report only)",
    )
    args = ap.parse_args(argv)
    caps = probe()
    print(json.dumps(caps, sort_keys=True))
    return 1 if missing(caps, args.require) else 0


if __name__ == "__main__":  # pragma: no cover - thin entry point
    sys.exit(main())
