"""Unit-suite fixtures.

Run logs are ON by default for every loader (user directive 2026-07-22), so
without intervention any test that exercises a loader would write real files
under ``~/logs/DryDocs``. Keep the suite hermetic: point the log family's
default at the test's tmp dir and clear the ambient env knobs. Tests that
exercise the env resolution set the variables themselves AFTER this fixture.
"""

from __future__ import annotations

import os

import pytest

# ── J33: a non-terminal console for the whole unit run ──────────────────────
# rich decides "is this a terminal?" ONCE, when a Console is constructed, and
# FORCE_COLOR wins over everything — over NO_COLOR (which only drops colour and
# keeps bold/italic escapes), over CliRunner's non-tty stream, over TERM. The
# CLI's module-level ``console = Console()`` is built the moment a test module
# imports ``drydocs.cli``, i.e. during COLLECTION, so a fixture runs too late:
# the knob has to be cleared at conftest IMPORT time, which precedes every test
# module's import. On a machine that exports FORCE_COLOR (this desktop: 3),
# every plain-substring assertion against CLI output was failing while the CLI
# behaved correctly (Idea-83; three tests from 2026-08-07, one already patched
# by stripping ANSI at e87800f9). The messages themselves are never loosened —
# the stream is made plain instead. TERM=dumb is the belt to the braces: it is
# rich's explicit "not a terminal" answer once FORCE_COLOR is out of the way.
os.environ.pop("FORCE_COLOR", None)
os.environ.setdefault("TERM", "dumb")

import drydocs_core.run_log as run_log  # after the console knob, on purpose


@pytest.fixture(autouse=True)
def _hermetic_run_logs(tmp_path, monkeypatch):
    monkeypatch.setattr(run_log, "DEFAULT_LOGDIR", tmp_path / "run-logs")
    monkeypatch.delenv(run_log.LOGDIR_ENV, raising=False)
    monkeypatch.delenv(run_log.LEGACY_LOGDIR_ENV, raising=False)
    monkeypatch.delenv(run_log.CALLER_ENV, raising=False)
    monkeypatch.delenv(run_log.LEGACY_CALLER_ENV, raising=False)
