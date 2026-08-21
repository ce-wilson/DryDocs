"""S12 — the drift comparison over synthetic lock/installed pairs, plus the
live interpreter (which must be drift-free for the suite to be running at all)."""

from __future__ import annotations

from tests import env_drift

LOCK = """
[[package]]
name = "click"
version = "8.1.8"
description = "x"

[[package]]
name = "Ruff"
version = "0.5.7"

[[package]]
name = "extras-only"
version = "1.0.0"
"""


def test_parse_lock_normalises_names() -> None:
    locked = env_drift.parse_lock(LOCK)
    assert locked == {"click": "8.1.8", "ruff": "0.5.7", "extras-only": "1.0.0"}


def test_drift_reports_only_installed_and_differing() -> None:
    locked = env_drift.parse_lock(LOCK)
    installed = {"click": "8.3.2", "ruff": "0.5.7"}  # extras-only absent -> skipped
    assert env_drift.drift(locked, installed) == [("click", "8.1.8", "8.3.2")]
    assert env_drift.drift(locked, {"click": "8.1.8", "ruff": "0.5.7"}) == []


def test_report_names_prefix_count_offenders_cause_and_remedy() -> None:
    text = env_drift.report(
        [("click", "8.1.8", "8.3.2"), ("ruff", "0.5.7", "0.15.11")], 65, "/x/venv"
    )
    assert "2 of 65" in text and "/x/venv" in text
    assert "click locked 8.1.8, installed 8.3.2" in text
    assert "VIRTUAL_ENV" in text and "unset VIRTUAL_ENV" in text and "poetry install --sync" in text
    assert "not twenty broken tests" in text


def test_the_running_interpreter_has_no_drift() -> None:
    """If this fails the session hook already failed first — kept so the check
    is visible in the report, not only in a UsageError."""
    offenders, checked = env_drift.check()
    assert checked >= 20, "too few locked packages found installed — wrong interpreter?"
    assert offenders == [], env_drift.report(offenders, checked)
