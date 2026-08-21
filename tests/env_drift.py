"""S12 — environment-drift guard: the interpreter's packages vs poetry.lock.

THE FAILURE THIS REPLACES. An inherited VIRTUAL_ENV (this desktop's shell
pre-sets it to agents/.venv) takes precedence over the in-project venv, so the
suite ran on a sibling interpreter whose click/ruff/... versions disagreed with
the lock — and it presented as twenty broken tests, not as one wrong
environment. The guard compares, for every locked package that is ALSO
installed, the installed version to the locked one; packages absent from the
interpreter are skipped (the lock carries groups and extras a given install
legitimately does not select). It guards on DRIFT, never on the venv PATH: a
path assertion would fail Docker, tox and system-python runs that are correctly
provisioned, and miss a wrong-version install inside the right directory.

The comparison is a pure function so the negative case is reproducible off this
machine (tests/unit/test_env_drift.py); the session hook runs it ONCE before
any test.
"""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
#: DRYDOCS_LOCK_PATH lets a test point the hook at a synthetic lock to prove it
#: FAILS (the negative case), without touching the real one.
LOCK = Path(os.environ.get("DRYDOCS_LOCK_PATH") or REPO / "poetry.lock")


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_lock(text: str) -> dict[str, str]:
    """{normalised name: locked version} from a poetry.lock (TOML-lite parse:
    every [[package]] block's name/version — no tomllib dependency on the hook
    path, so the guard itself cannot be the thing that drifts)."""
    out: dict[str, str] = {}
    name = version = None
    for line in text.splitlines():
        if line.strip() == "[[package]]":
            name = version = None
            continue
        m = re.match(r'^name\s*=\s*"([^"]+)"', line)
        if m:
            name = m.group(1)
        m = re.match(r'^version\s*=\s*"([^"]+)"', line)
        if m:
            version = m.group(1)
        if name and version:
            out[_norm(name)] = version
            name = version = None
    return out


def installed_versions(names: Iterable[str]) -> dict[str, str]:
    from importlib import metadata

    found: dict[str, str] = {}
    for name in names:
        try:
            found[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return found


def drift(locked: Mapping[str, str], installed: Mapping[str, str]) -> list[tuple[str, str, str]]:
    """(name, locked, installed) for every package present in BOTH and differing.
    Absent from the interpreter = skipped, by design."""
    return sorted(
        (name, locked[name], installed[name])
        for name in locked
        if name in installed and installed[name] != locked[name]
    )


def report(offenders: list[tuple[str, str, str]], checked: int, prefix: str = sys.prefix) -> str:
    shown = ", ".join(f"{n} locked {lk}, installed {ins}" for n, lk, ins in offenders[:6])
    more = f" (+{len(offenders) - 6} more)" if len(offenders) > 6 else ""
    return (
        f"ENVIRONMENT DRIFT: {len(offenders)} of {checked} installed locked package(s) disagree "
        f"with poetry.lock in {prefix}: {shown}{more}. Usual cause: an inherited VIRTUAL_ENV "
        "taking precedence over the in-project venv (this desktop's shell pre-sets it to "
        "agents/.venv). Remedy: `unset VIRTUAL_ENV` (PowerShell: `$env:VIRTUAL_ENV=$null`) and "
        "re-run under `poetry run`, or `poetry install --sync` in the venv you meant. This is one "
        "wrong environment, not twenty broken tests."
    )


def check(lock_path: Path | None = None) -> tuple[list[tuple[str, str, str]], int]:
    locked = parse_lock((lock_path or LOCK).read_text(encoding="utf-8"))
    installed = installed_versions(locked)
    return drift(locked, installed), len(installed)
