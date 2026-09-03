"""S13/S15 — every CLI module imports cleanly as the FIRST import of a fresh
interpreter, and importing a command module does not drag in the root.

WHY SUBPROCESSES. The defect this guards against is import-ORDER dependent:
whichever module the test session touches first primes ``sys.modules`` and the
failure vanishes — which is precisely the mechanism that hid the S8 cycle for
two days (J26: a check that looks where the failure cannot happen proves
nothing). Each import therefore runs in its OWN interpreter. In-process
imports of these modules anywhere else in the suite say nothing about this
property.

WHY THE NO-ROOT ASSERTION. The fix's shape (S13's hoist option) is a DAG:
command modules import ``drydocs.cli_shared``; the composition root imports
both. "The cycle is removed rather than reordered" is only true while a
command module's import does NOT execute the root's body — so the guard
asserts ``drydocs.cli`` never lands in ``sys.modules`` when a command module
is imported first. A module that quietly regains a module-scope root import
fails here BY NAME, not two splits later.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys

import pytest

#: The composition root plus every module the S8 split produced, plus the
#: shared-state module the S13 fix introduced. A new `cli_*` module joins this
#: list in the same commit that creates it.
CLI_MODULES: tuple[str, ...] = (
    "drydocs.cli",
    "drydocs.cli_shared",
    "drydocs.cli_schema",
    "drydocs.cli_ingest",
    "drydocs.cli_verify",
    "drydocs.cli_variables",
    "drydocs.cli_docs",
    "drydocs.cli_plan",
)
# S16: the optional CONSUMER module joins the list wherever it exists (never producer-side;
# test_cli_registry.py proves the seam with a fixture). Subprocess-per-import, like the rest.
if importlib.util.find_spec("drydocs.cli_consumer") is not None:
    CLI_MODULES = (*CLI_MODULES, "drydocs.cli_consumer")

#: Everything except the root itself must be importable WITHOUT executing the
#: root's module body (the root imports THEM, never the reverse at import time).
NON_ROOT = tuple(m for m in CLI_MODULES if m != "drydocs.cli")


def _probe(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize("module", CLI_MODULES)
def test_module_imports_first_in_a_fresh_interpreter(module: str) -> None:
    result = _probe(f"import {module}")
    assert result.returncode == 0, (
        f"`import {module}` as the first import of a fresh interpreter failed:\n" f"{result.stderr}"
    )


@pytest.mark.parametrize("module", NON_ROOT)
def test_importing_a_command_module_does_not_execute_the_root(module: str) -> None:
    result = _probe(
        f"import sys; import {module}; "
        "assert 'drydocs.cli' not in sys.modules, "
        "'importing a command module executed the composition root'"
    )
    assert result.returncode == 0, (
        f"`import {module}` pulled in drydocs.cli — the S13 cycle is back "
        f"(reordered, not removed):\n{result.stderr}"
    )
