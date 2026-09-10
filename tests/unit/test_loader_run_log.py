"""LoaderRunLog — the SqlRunLog contract generalized to every loader.

Contract under test (user directive 2026-07-22):
* configurable log path — DRYDOCS_LOGDIR wins, SPIDERP_LOGDIR honored as the
  company-compat fallback, ``~/logs/DryDocs`` default (patched hermetic here);
* shared naming convention — ``load.<loader>.<stamp>[-N].log``;
* header/meta block from the process — date/script/loader/run id/source/
  target/os user + free-form meta lines;
* the WARN stream tees into the file (the description_tokens flood class),
  rejects land uncapped, the footer carries the summary counts;
* best-effort: the log is never the reason a load fails.
"""

from __future__ import annotations

import logging
import re

import pytest

from drydocs_core import run_log as rl
from drydocs_core.run_log import LoaderRunLog, claim_log_path, resolve_log_dir


def _read(path):
    return path.read_text(encoding="utf-8")


# ---- configurable path ------------------------------------------------------


def test_logdir_resolution_order(tmp_path, monkeypatch):
    assert resolve_log_dir() == rl.DEFAULT_LOGDIR  # env cleared by conftest
    monkeypatch.setenv("SPIDERP_LOGDIR", str(tmp_path / "legacy"))
    assert resolve_log_dir() == tmp_path / "legacy"
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "generic"))
    assert resolve_log_dir() == tmp_path / "generic"  # generic name wins


def test_sql_run_log_shares_the_same_knob(tmp_path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "shared"))
    from drydocs_core.adapters.sql_run_log import SqlRunLog

    log = SqlRunLog("stmt", target="dsn", user="u")
    path = log.open()
    log.close()
    assert path.parent == tmp_path / "shared"


# ---- naming convention ------------------------------------------------------


def test_naming_convention_and_collision_suffix(tmp_path, monkeypatch):
    """J46: the clock is FROZEN across the two claims. Before, the test raced the
    wall clock — it passed only when both calls landed inside one second, and
    rode every full-suite run as an occasional -2-suffix failure. What is under
    test is unchanged: the second claim of an existing name gets -2."""
    from datetime import datetime

    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path))
    frozen = datetime(2026, 8, 21, 4, 5, 6)
    first = claim_log_path("load.controlm_jobs.v1", now=lambda: frozen)
    first.touch()
    second = claim_log_path("load.controlm_jobs.v1", now=lambda: frozen)
    assert first.name == "load.controlm_jobs.v1.20260821-040506.log"
    assert second.name == "load.controlm_jobs.v1.20260821-040506-2.log"
    assert re.fullmatch(r"load\.controlm_jobs\.v1\.\d{8}-\d{6}\.log", first.name)
    # and a later second is a fresh name, not a suffix — proof the suffix is the
    # collision logic and not an artefact of the frozen clock
    later = claim_log_path("load.controlm_jobs.v1", now=lambda: datetime(2026, 8, 21, 4, 5, 7))
    assert later.name == "load.controlm_jobs.v1.20260821-040507.log"


# ---- header / meta ----------------------------------------------------------


def test_header_carries_process_meta(tmp_path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path))
    monkeypatch.setenv("DRYDOCS_CALLER", "drydocs ingest-controlm --use-oracle")
    log = LoaderRunLog(
        "controlm_jobs.v1",
        "run-123",
        source="csv (samples/jobs.csv)",
        target="bolt://localhost:7687 db=drydocs",
        meta={"batch size": 1000, "full extract": False},
    )
    path = log.open()
    log.close({"status": "OK"})
    text = _read(path)
    for expected in (
        "script     : drydocs ingest-controlm --use-oracle",
        "loader     : controlm_jobs.v1",
        "run id     : run-123",
        "source     : csv (samples/jobs.csv)",
        "target     : bolt://localhost:7687 db=drydocs",
        "os user    :",
        "batch size : 1000",
        "status               : OK",
    ):
        assert expected in text, f"missing header/meta line: {expected!r}"


# ---- WARN-stream capture ----------------------------------------------------


def test_warn_stream_tees_into_file_and_detaches(tmp_path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path))
    log = LoaderRunLog("x.v1", "r1")
    path = log.open()
    log.attach()
    logging.getLogger("drydocs_core.orchestration.controlm.description_tokens").warning(
        "dropping unknown key %r", "SOME KEY"
    )
    # INFO capture follows the process's logging config (effective logger
    # level), so enable it explicitly — the tee never overrides the process.
    info_logger = logging.getLogger("drydocs.loaders.base")
    old_level = info_logger.level
    info_logger.setLevel(logging.INFO)
    try:
        info_logger.info("Loader x.v1 done")
    finally:
        info_logger.setLevel(old_level)
    log.close({})
    text = _read(path)
    assert "dropping unknown key 'SOME KEY'" in text
    assert "Loader x.v1 done" in text
    assert "warnings captured    : 1" in text
    # after close the handler is gone — further records must not raise or write
    logging.getLogger("drydocs_core.orchestration.controlm.description_tokens").warning("late")
    assert "late" not in _read(path)


def test_rejects_logged_uncapped(tmp_path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path))
    log = LoaderRunLog("x.v1", "r1")
    path = log.open()
    for i in range(150):
        log.reject(i, [{"msg": "bad"}])
    log.close({})
    text = _read(path)
    assert "REJECT row 0:" in text and "REJECT row 149:" in text
    assert "rejects logged       : 150" in text


# ---- best-effort contract ---------------------------------------------------


def test_methods_are_noops_after_close_and_before_open(tmp_path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path))
    log = LoaderRunLog("x.v1", "r1")
    log.reject(0, "early")  # before open: silent no-op
    log.close({})  # close without open: silent no-op
    path = log.open()
    log.close({"status": "OK"})
    log.reject(1, "late")
    log.close({"status": "AGAIN"})
    assert "AGAIN" not in _read(path)


# ---- BaseLoader wiring ------------------------------------------------------


class _FakeClient:
    _uri = "bolt://localhost:7687"
    _database = "drydocs"

    def run(self, *_a, **_k):
        return []

    def run_script(self, *_a, **_k):
        return []


class _ListAdapter:
    path = "fixture-rows"

    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def rows(self):
        return iter(self._rows)


def _make_loader(rows, tmp_path):
    from pydantic import BaseModel

    from drydocs.loaders.base import BaseLoader

    class Row(BaseModel):
        name: str

    class Loader(BaseLoader):
        name = "unit_probe.v1"
        cypher_path = tmp_path / "probe.cypher"
        row_model = Row

    Loader.cypher_path.write_text("UNWIND $batch AS row RETURN row", encoding="utf-8")
    return Loader(_FakeClient(), _ListAdapter(rows))


def test_baseloader_writes_run_log_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    loader = _make_loader([{"name": "ok"}, {"bad": "row"}], tmp_path)
    summary = loader.load()
    assert summary.rows_processed == 1 and summary.rows_rejected == 1
    logs = list((tmp_path / "logs").glob("load.unit_probe.v1.*.log"))
    assert len(logs) == 1
    text = _read(logs[0])
    assert "run id     : " + loader.run_id in text
    assert "source     : csv (fixture-rows)" in text
    assert "target     : bolt://localhost:7687 db=drydocs" in text
    assert "REJECT row 1:" in text
    assert "status               : OK" in text


def test_baseloader_run_log_opt_out(tmp_path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    loader = _make_loader([{"name": "ok"}], tmp_path)
    loader.run_log = False
    loader.load()
    assert not (tmp_path / "logs").exists()


def test_baseloader_survives_unwritable_logdir(tmp_path, monkeypatch):
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where the log DIR should be", encoding="utf-8")
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(blocker / "nested"))
    loader = _make_loader([{"name": "ok"}], tmp_path)
    summary = loader.load()  # mkdir fails -> WARNING -> load proceeds without log
    assert summary.status == "OK"


def test_baseloader_failure_footer(tmp_path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    loader = _make_loader([{"name": "ok"}], tmp_path)

    def boom(*_a, **_k):
        raise RuntimeError("flush exploded")

    loader._flush = boom
    with pytest.raises(RuntimeError):
        loader.load()
    text = _read(next((tmp_path / "logs").glob("load.unit_probe.v1.*.log")))
    assert "FAILED: flush exploded" in text
    assert "status               : FAILED" in text


# ---- CORE15: the four silent-degradation handlers each say what was lost -----
#
# All four were `except Exception:` with no message. The run log's own docstring
# says it is "best-effort after open: the log is an audit trail, never the reason
# a load fails" - which is right, and was being used to justify saying nothing at
# all. Non-fatal and silent are different things: the coverage report showed all
# four branches untested, so nothing anywhere asserted what happened in them.
#
# Each test asserts the WARNING, not just the fallback, because the fallback
# already worked - the silence was the defect.


def test_an_unreadable_kinds_declaration_says_the_declared_root_is_not_in_use(
    monkeypatch, tmp_path, caplog
):
    def boom(**_k):
        raise RuntimeError("log-kinds.yaml is not valid YAML")

    monkeypatch.setattr("drydocs_core.log_kinds.resolve_root", boom)
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    with caplog.at_level(logging.WARNING, logger="drydocs_core.run_log"):
        assert resolve_log_dir() == tmp_path / "logs"
    (record,) = (r for r in caplog.records if "log-kinds" in r.getMessage())
    assert "DECLARED log root is not in use" in record.getMessage()
    assert "RuntimeError" in record.getMessage()


def test_an_unresolvable_kind_says_rotation_and_format_are_not_in_use(
    monkeypatch, tmp_path, caplog
):
    """What is lost is specific: a per-day kind silently becomes per-run and a
    .jsonl kind silently becomes .log, which look like data problems downstream."""

    def boom(_kind_id):
        raise KeyError("no such kind")

    monkeypatch.setattr("drydocs_core.log_kinds.kind", boom)
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    with caplog.at_level(logging.WARNING, logger="drydocs_core.run_log"):
        path = claim_log_path("nosuchkind.probe")
    assert path.suffix == ".log"  # the fallback still works
    (record,) = (r for r in caplog.records if "could not be resolved" in r.getMessage())
    assert "nosuchkind" in record.getMessage()
    assert "rotation and format are not in use" in record.getMessage()


class _DeadHandle:
    """A file handle whose write() fails the way a full disk does.

    Replacing the HANDLE rather than `_write` is what makes this test honest:
    `_write` is where the OSError is actually caught, so a test that replaced
    `_write` itself would be testing its own stub. That mistake is how the fifth
    handler was found - `close()` calls `_write` directly, so the stub's
    exception escaped through a path the real code swallows.
    """

    def __init__(self) -> None:
        self.attempts = 0

    def write(self, _text: str) -> None:
        self.attempts += 1
        raise OSError("no space left on device")

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


def test_a_run_log_that_stops_accepting_records_says_it_is_incomplete(
    monkeypatch, tmp_path, caplog
):
    """The case the item's title is about, and it flows through `_write`, not
    through the handler the acceptance named - see the comment on `_write`."""
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    log = LoaderRunLog("unit_probe.v1", "core15")
    log.open()
    log.attach()
    try:
        log._fh = _DeadHandle()
        with caplog.at_level(logging.WARNING, logger="drydocs_core.run_log"):
            logging.getLogger("drydocs.loaders.probe").warning("a record that will not land")
        said = [r for r in caplog.records if "INCOMPLETE" in r.getMessage()]
        assert len(said) == 1
        assert str(log.path) in said[0].getMessage()
    finally:
        log.close()


def test_the_incomplete_warning_is_emitted_once_and_does_not_recurse(monkeypatch, tmp_path, caplog):
    """This handler's logger is under CAPTURE_NAMESPACES, so its own warning
    re-enters emit(). The flag is set BEFORE the warning; without that ordering
    this test recurses until Python's stack gives out rather than failing."""
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    log = LoaderRunLog("unit_probe.v1", "core15")
    log.open()
    log.attach()
    try:
        log._fh = _DeadHandle()
        with caplog.at_level(logging.WARNING, logger="drydocs_core.run_log"):
            for i in range(5):
                logging.getLogger("drydocs.loaders.probe").warning("record %d", i)
        assert len([r for r in caplog.records if "INCOMPLETE" in r.getMessage()]) == 1
    finally:
        log.close()


def test_an_undeterminable_os_user_says_the_attribution_is_missing(monkeypatch, tmp_path, caplog):
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))

    def boom():
        raise KeyError("no login name")

    monkeypatch.setattr(rl.getpass, "getuser", boom)
    log = LoaderRunLog("unit_probe.v1", "core15")
    with caplog.at_level(logging.WARNING, logger="drydocs_core.run_log"):
        path = log.open()
    log.close()
    assert "os user" in _read(path).lower()  # the header still rendered
    (record,) = (r for r in caplog.records if "OS user" in r.getMessage())
    assert "missing attribution" in record.getMessage()


def test_a_degraded_run_log_is_still_never_the_reason_a_load_fails(monkeypatch, tmp_path):
    """The contract the warnings must not break. All four handlers stay
    non-fatal - this asserts the load's own exception is the one that surfaces,
    and that a broken log surfaces nothing at all."""
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    log = LoaderRunLog("unit_probe.v1", "core15")
    log.open()
    log.attach()
    handle = _DeadHandle()
    log._fh = handle
    logging.getLogger("drydocs.loaders.probe").warning("nothing raised here")
    log.close()  # close writes the footer through the same dead handle
    assert handle.attempts, "the test did not actually exercise a failing write"
