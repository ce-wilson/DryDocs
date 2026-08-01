"""Per-run SQL extract log (HITL verification trail) — sql_run_log + adapter wiring.

Ports the company repo's SQL-logging contract onto the producer's
python-oracledb path. Pins:

* ``render_sql`` substitutes binds ONLY in code regions — the company
  hardening ("don't treat :tokens in SQL comments/strings as binds",
  docs/port-prompt.md item 14) must hold from day one, byte-identical on the
  real ``controlm_dependencies_recursive.sql``.
* ``SqlRunLog`` writes one self-contained log per run under SPIDERP_LOGDIR:
  header -> handshake -> statement -> result (csv) -> footer.
* ``OracleAdapter`` tees rows into the log without changing what it yields.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import ClassVar

import pytest

from drydocs_core.adapters.oracle_adapter import OracleAdapter
from drydocs_core.adapters.sql_run_log import SqlRunLog, render_sql, sql_literal

REPO_ROOT = Path(__file__).resolve().parents[2]
RECURSIVE_SQL = REPO_ROOT / "drydocs" / "loaders" / "sql" / "controlm_dependencies_recursive.sql"

SCOPE_BINDS = {
    "folder_filter": "CCB_AUTO_%",
    "run_as": None,
    "developer_sid": None,
    "row_cap": 100,
}


# --- render_sql: literals ----------------------------------------------------


def test_sql_literal_rendering():
    assert sql_literal(None) == "NULL"
    assert sql_literal(100) == "100"
    assert sql_literal(True) == "1"
    assert sql_literal("CCB_AUTO_%") == "'CCB_AUTO_%'"
    assert sql_literal("O'Brien") == "'O''Brien'"


def test_render_sql_substitutes_in_code_regions():
    sql = "SELECT * FROM t WHERE name LIKE :folder_filter AND ROWNUM <= :row_cap"
    rendered = render_sql(sql, SCOPE_BINDS)
    assert rendered == ("SELECT * FROM t WHERE name LIKE 'CCB_AUTO_%' AND ROWNUM <= 100")


def test_render_sql_null_and_unknown_binds():
    sql = "WHERE (:run_as IS NULL OR owner = :run_as) AND x = :not_a_bind"
    rendered = render_sql(sql, SCOPE_BINDS)
    assert "(NULL IS NULL OR owner = NULL)" in rendered
    # a :token not in the bind dict stays untouched (oracledb drops unused binds)
    assert ":not_a_bind" in rendered


# --- render_sql: the company hardening (code regions only) -------------------


def test_render_sql_never_touches_comments_strings_identifiers():
    sql = (
        "-- line comment mentions :folder_filter and :DEPENDS_ON\n"
        "/* block comment :row_cap\n   spans lines :folder_filter */\n"
        "SELECT ':folder_filter' AS lit, \":row_cap\" AS qid, 'it''s :run_as' AS esc\n"
        "FROM t WHERE f LIKE :folder_filter"
    )
    rendered = render_sql(sql, SCOPE_BINDS)
    assert "-- line comment mentions :folder_filter and :DEPENDS_ON" in rendered
    assert "/* block comment :row_cap\n   spans lines :folder_filter */" in rendered
    assert "':folder_filter'" in rendered  # single-quoted string verbatim
    assert '":row_cap"' in rendered  # quoted identifier verbatim
    assert "'it''s :run_as'" in rendered  # escaped quote keeps string open
    assert rendered.endswith("FROM t WHERE f LIKE 'CCB_AUTO_%'")


def test_render_sql_recursive_extract_stays_byte_identical_outside_code():
    """The real file from port-prompt item 14: ':depends_on' literal and the
    :DEPENDS_ON / :BusinessApplication comment tokens must survive rendering."""
    original = RECURSIVE_SQL.read_text(encoding="utf-8")
    rendered = render_sql(original, SCOPE_BINDS)
    assert rendered.count("':depends_on'") == original.count("':depends_on'")
    for line in original.splitlines():
        if line.lstrip().startswith("--"):
            assert line in rendered, f"comment line altered: {line!r}"


# --- SqlRunLog ----------------------------------------------------------------


def _read_only_log(tmp_path: Path) -> str:
    logs = list(tmp_path.glob("*.log"))
    assert len(logs) == 1, f"expected exactly one log, got {logs}"
    return logs[0].read_text(encoding="utf-8")


def test_run_log_shape(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIDERP_LOGDIR", str(tmp_path))
    monkeypatch.setenv("SPIDERP_CALLER", "drydocs ingest-controlm --use-oracle")
    log = SqlRunLog("controlm_folders.sql", target="PSGMGR_ALIAS", user="CM_RO_USER")
    path = log.open()
    assert path.parent == tmp_path
    assert path.name.startswith("controlm_folders.sql.")
    assert path.suffix == ".log"
    log.handshake("Oracle Database 19c")
    log.statement("SELECT 1 FROM dual", {"row_cap": 100})
    log.result_header(["A", "B"])
    log.result_row([1, "x,y"])
    log.result_row([2, None])
    log.close()

    text = _read_only_log(tmp_path)
    assert "script     : drydocs ingest-controlm --use-oracle" in text
    assert "statement  : controlm_folders.sql" in text
    assert "target     : PSGMGR_ALIAS" in text
    assert "connected  : Oracle Database 19c" in text
    assert "-- statement 1 --" in text
    assert "SELECT 1 FROM dual" in text
    assert "row_cap = 100" in text
    assert "-- result (csv) --" in text
    assert '1,"x,y"' in text  # csv quoting on embedded delimiter
    assert "Done. 1 statement(s), 2 row(s) in" in text


def test_run_log_same_second_collision(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIDERP_LOGDIR", str(tmp_path))
    first, second = SqlRunLog("x.sql"), SqlRunLog("x.sql")
    p1, p2 = first.open(), second.open()
    first.close()
    second.close()
    assert p1 != p2 and p1.exists() and p2.exists()


def test_run_log_failure_recorded(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIDERP_LOGDIR", str(tmp_path))
    log = SqlRunLog("y.sql")
    log.open()
    log.statement("SELECT * FROM missing_table", None)
    log.close(error=RuntimeError("ORA-00942: table or view does not exist"))
    text = _read_only_log(tmp_path)
    assert "FAILED: ORA-00942" in text
    assert "0 row(s)" in text


# --- OracleAdapter wiring -----------------------------------------------------


class _FakeCursor:
    # Shared across instances on purpose — it mirrors DB-API's cursor.description,
    # which the adapter only ever reads.
    description: ClassVar[list[tuple[str, None]]] = [("FOLDER_NAME", None), ("JOB_COUNT", None)]
    arraysize = 0

    def __init__(self):
        self.executed: tuple[str, dict] | None = None
        self._rows = [("CCB_AUTO_DAILY", 12), ("CCB_AUTO_EOD", 3)]

    def execute(self, query, binds):
        self.executed = (query, binds)

    def __iter__(self):
        return iter(self._rows)

    def close(self):
        pass


class _FakeConn:
    version = "19.0.0.0.0"

    def __init__(self):
        self.cursor_obj = _FakeCursor()

    def cursor(self):
        return self.cursor_obj

    def close(self):
        pass


@pytest.fixture()
def fake_oracledb(monkeypatch):
    mod = types.ModuleType("oracledb")
    mod.last_conn = None

    def connect(**kwargs):
        mod.last_conn = _FakeConn()
        mod.connect_kwargs = kwargs
        return mod.last_conn

    mod.connect = connect
    monkeypatch.setitem(sys.modules, "oracledb", mod)
    return mod


def test_adapter_tees_run_log(tmp_path, monkeypatch, fake_oracledb):
    monkeypatch.setenv("SPIDERP_LOGDIR", str(tmp_path))
    query = "SELECT folder_name, job_count FROM v WHERE f LIKE :folder_filter"
    adapter = OracleAdapter(
        user="CM_RO_USER",
        password="pw",
        dsn="ALIAS",
        query=query,
        bind_params={"folder_filter": "CCB_AUTO_%"},
        name="controlm_folders.sql",
    )
    with adapter:
        rows = list(adapter.rows())

    # yielded rows unchanged by the tee (regression)
    assert rows == [
        {"folder_name": "CCB_AUTO_DAILY", "job_count": 12},
        {"folder_name": "CCB_AUTO_EOD", "job_count": 3},
    ]
    # execution stayed parameterized — the ORIGINAL query + native binds
    assert fake_oracledb.last_conn.cursor_obj.executed == (query, {"folder_filter": "CCB_AUTO_%"})
    text = _read_only_log(tmp_path)
    assert "connected  : Oracle Database 19.0.0.0.0" in text
    assert "WHERE f LIKE 'CCB_AUTO_%'" in text  # rendered for review
    assert "FOLDER_NAME,JOB_COUNT" in text
    assert "CCB_AUTO_DAILY,12" in text
    assert "Done. 1 statement(s), 2 row(s) in" in text


def test_adapter_run_log_opt_out(tmp_path, monkeypatch, fake_oracledb):
    monkeypatch.setenv("SPIDERP_LOGDIR", str(tmp_path))
    adapter = OracleAdapter(
        user="u",
        password="p",
        dsn="d",
        query="SELECT 1 FROM dual",
        run_log=False,
    )
    with adapter:
        list(adapter.rows())
    assert list(tmp_path.glob("*.log")) == []


def test_adapter_logs_attempted_sql_on_connect_failure(tmp_path, monkeypatch, fake_oracledb):
    """A failed extract still leaves an audit trail (header + FAILED footer)."""
    monkeypatch.setenv("SPIDERP_LOGDIR", str(tmp_path))

    def boom(**kwargs):
        raise RuntimeError("ORA-12154: TNS could not resolve")

    fake_oracledb.connect = boom
    adapter = OracleAdapter(user="u", password="p", dsn="d", query="SELECT 1 FROM dual")
    with pytest.raises(RuntimeError):
        adapter.__enter__()
    text = _read_only_log(tmp_path)
    assert "FAILED: ORA-12154" in text
