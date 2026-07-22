"""Unit-suite fixtures.

Run logs are ON by default for every loader (user directive 2026-07-22), so
without intervention any test that exercises a loader would write real files
under ``~/logs/DryDocs``. Keep the suite hermetic: point the log family's
default at the test's tmp dir and clear the ambient env knobs. Tests that
exercise the env resolution set the variables themselves AFTER this fixture.
"""
from __future__ import annotations

import pytest

import drydocs_core.run_log as run_log


@pytest.fixture(autouse=True)
def _hermetic_run_logs(tmp_path, monkeypatch):
    monkeypatch.setattr(run_log, "DEFAULT_LOGDIR", tmp_path / "run-logs")
    monkeypatch.delenv(run_log.LOGDIR_ENV, raising=False)
    monkeypatch.delenv(run_log.LEGACY_LOGDIR_ENV, raising=False)
    monkeypatch.delenv(run_log.CALLER_ENV, raising=False)
    monkeypatch.delenv(run_log.LEGACY_CALLER_ENV, raising=False)
