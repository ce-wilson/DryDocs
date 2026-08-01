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
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path))
    first = claim_log_path("load.controlm_jobs.v1")
    first.touch()
    second = claim_log_path("load.controlm_jobs.v1")
    assert re.fullmatch(r"load\.controlm_jobs\.v1\.\d{8}-\d{6}\.log", first.name)
    assert re.fullmatch(r"load\.controlm_jobs\.v1\.\d{8}-\d{6}-2\.log", second.name)


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
    logging.getLogger("drydocs_core.controlm.description_tokens").warning(
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
    logging.getLogger("drydocs_core.controlm.description_tokens").warning("late")
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
