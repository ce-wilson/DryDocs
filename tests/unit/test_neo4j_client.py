"""CORE11 — the core driver seam: access mode and captured diagnostics.

Offline. A duck-typed fake driver stands in for the real one (the pattern
``test_cypher_split.py`` established), because the two facts under test are
about WHICH driver call a method makes and WHAT it does with the summary — both
observable without a server, and neither observable from a green loader run.

The 2026-09-07 core report is the subject: S2 (every read ran inside a write
transaction — ``execute_read`` appeared nowhere in the first-party tree) and S3
(``run`` dropped the result summary, so a query naming a label that does not
exist returned ``[]`` with no signal, the same value as a query that matched
nothing).
"""

from __future__ import annotations

import logging
import math
import socket
import time

import neo4j
import pytest
from neo4j import Query

from drydocs_core.config import Neo4jDriverBounds
from drydocs_core.neo4j_client import Neo4jClient


class _FakeSummary:
    def __init__(self, notifications: list[dict] | None = None) -> None:
        self.notifications = notifications or []


class _FakeResult:
    def __init__(self, rows: list[dict], summary: _FakeSummary) -> None:
        self._rows = rows
        self._summary = summary
        self.consumed_after_rows: bool | None = None
        self._drained = False

    def __iter__(self):
        self._drained = True
        return iter(self._rows)

    def consume(self) -> _FakeSummary:
        # Records the ORDER, because a summary consumed before the stream is
        # drained is incomplete — that is the bug this fake can catch.
        self.consumed_after_rows = self._drained
        return self._summary


class _FakeTx:
    def __init__(self, log: list, rows: list[dict], summary: _FakeSummary) -> None:
        self._log = log
        self._rows = rows
        self._summary = summary
        self.result: _FakeResult | None = None

    def run(self, cypher: str, bind: dict) -> _FakeResult:
        self._log.append(("tx.run", cypher, dict(bind)))
        self.result = _FakeResult(self._rows, self._summary)
        return self.result


class _FakeSession:
    def __init__(self, log: list, rows: list[dict], summary: _FakeSummary) -> None:
        self._log = log
        self._rows = rows
        self._summary = summary
        self.tx: _FakeTx | None = None

    def __enter__(self) -> _FakeSession:
        return self

    def __exit__(self, *_: object) -> bool:
        return False

    def _apply(self, mode: str, work):
        self._log.append((mode,))
        self.tx = _FakeTx(self._log, self._rows, self._summary)
        return work(self.tx)

    def execute_read(self, work):
        return self._apply("execute_read", work)

    def execute_write(self, work):
        return self._apply("execute_write", work)

    def run(self, statement: str, params: dict) -> _FakeResult:
        self._log.append(("session.run", statement, dict(params)))
        return _FakeResult(self._rows, self._summary)


class _FakeDriver:
    def __init__(self, log: list, rows: list[dict], summary: _FakeSummary) -> None:
        self._log = log
        self._rows = rows
        self._summary = summary
        self.sessions: list[_FakeSession] = []

    def session(self, database: str | None = None) -> _FakeSession:
        session = _FakeSession(self._log, self._rows, self._summary)
        self.sessions.append(session)
        return session


def _client(rows=None, notifications=None):
    log: list = []
    client = Neo4jClient("bolt://fake", "u", "p")
    # `is None`, not `or`: an EMPTY row list is the interesting case for S3 —
    # the point of that finding is that empty and empty-because-mistyped were
    # the same value — and `rows or [...]` would substitute a row under it.
    driver = _FakeDriver(log, [{"v": 1}] if rows is None else rows, _FakeSummary(notifications))
    client._driver = driver
    return client, driver, log


def _modes(log: list) -> list[str]:
    return [entry[0] for entry in log if entry[0] in ("execute_read", "execute_write")]


# ── S2: the access mode is the caller's to choose ────────────────────────────


def test_read_uses_a_read_transaction():
    client, _, log = _client()
    assert client.read("MATCH (n) RETURN n") == [{"v": 1}]
    assert _modes(log) == ["execute_read"]


def test_run_stays_the_write_path():
    """Deliberately unchanged: `run` has ~40 call sites, most of them writes,
    so flipping its default would silently convert them. The migration of the
    read-shaped sites is an ADR action item, not a default change."""
    client, _, log = _client()
    assert client.run("MERGE (n:Thing) RETURN n") == [{"v": 1}]
    assert _modes(log) == ["execute_write"]


def test_every_read_helper_on_the_client_reads():
    """S2 named four: server_version, apoc_available, constraint_names,
    constraints_detail. All four demanded write access before CORE11."""
    client, _, log = _client(rows=[{"v": "2026.05.0", "name": "n"}])
    client.server_version()
    client.apoc_available()
    client.constraint_names()
    client.constraints_detail()
    assert _modes(log) == ["execute_read"] * 4


def test_binds_reach_the_statement_by_either_route():
    client, driver, log = _client()
    client.read("MATCH (n {a: $a, b: $b}) RETURN n", {"a": 1}, b=2)
    (call,) = (e for e in log if e[0] == "tx.run")
    assert call[2] == {"a": 1, "b": 2}


# ── S3: the driver's diagnostics are no longer dropped ───────────────────────


_UNKNOWN_LABEL = {
    "code": "Neo.ClientNotification.Statement.UnknownLabelWarning",
    "title": "The provided label is not in the database.",
    "severity": "WARNING",
    "description": "One of the labels does not exist",
    "position": {"line": 1, "column": 8},
}


def test_a_notification_survives_the_call():
    client, _, _ = _client(rows=[], notifications=[_UNKNOWN_LABEL])
    rows = client.read("MATCH (n:Typo) RETURN n")
    assert rows == []
    # …and the empty answer is no longer the whole story
    (note,) = client.last_notifications
    assert note.code.endswith("UnknownLabelWarning")
    assert note.position == "1:8"


def test_a_clean_run_records_an_empty_list_not_a_missing_field():
    client, _, _ = _client()
    client.run("MERGE (n:Thing)")
    assert client.last_notifications == []


def test_the_previous_statements_notifications_do_not_linger():
    """`last_notifications` describes the MOST RECENT statement. A stale list
    would be worse than none: it would attribute one query's warning to another."""
    client, driver, _ = _client(rows=[], notifications=[_UNKNOWN_LABEL])
    client.read("MATCH (n:Typo) RETURN n")
    assert client.last_notifications
    driver._summary = _FakeSummary([])
    client.read("MATCH (n:Real) RETURN n")
    assert client.last_notifications == []


def test_the_summary_is_consumed_after_the_rows_are_drained():
    client, driver, _ = _client()
    client.read("MATCH (n) RETURN n")
    assert driver.sessions[0].tx.result.consumed_after_rows is True


def test_a_notification_is_logged_at_its_own_severity(caplog):
    """Not flattened to one level. An INFORMATION notice logged as a warning
    teaches readers the channel cries wolf — Idea-111's failure mode."""
    client, _, _ = _client(
        notifications=[
            dict(_UNKNOWN_LABEL, severity="INFORMATION", code="Neo.Info.Thing"),
            _UNKNOWN_LABEL,
        ]
    )
    with caplog.at_level(logging.INFO, logger="drydocs.neo4j_client"):
        client.read("MATCH (n) RETURN n")
    levels = {r.levelno for r in caplog.records}
    assert levels == {logging.INFO, logging.WARNING}


def test_an_unknown_severity_logs_as_a_warning(caplog):
    client, _, _ = _client(notifications=[dict(_UNKNOWN_LABEL, severity="")])
    with caplog.at_level(logging.INFO, logger="drydocs.neo4j_client"):
        client.read("MATCH (n) RETURN n")
    assert [r.levelno for r in caplog.records] == [logging.WARNING]


def test_run_script_records_what_its_statements_carried():
    """`run_script` already called consume() and threw the summary away — the
    same drop as `run`, in the method that runs the bootstrap DDL."""
    client, _, log = _client(notifications=[_UNKNOWN_LABEL])
    client.run_script("MERGE (a:A);\nMERGE (b:B);\n")
    assert len([e for e in log if e[0] == "session.run"]) == 2
    assert client.last_notifications


def test_run_with_diagnostics_returns_rows_and_the_payload():
    client, _, log = _client(rows=[{"v": 1}], notifications=[_UNKNOWN_LABEL])
    rows, notes = client.run_with_diagnostics("MATCH (n) RETURN n", write=False)
    assert rows == [{"v": 1}]
    assert _modes(log) == ["execute_read"]
    # plain dicts, the R21 payload shape the API and the agents already emit
    assert notes[0]["code"].endswith("UnknownLabelWarning")
    assert set(notes[0]) == {
        "code",
        "title",
        "severity",
        "description",
        "position",
        "category",
    }


# ── CORE13: the waits are declared, reach the driver, and actually bite ──────
#
# S4 of the 2026-09-07 core report: searched across all 74 core files, the only
# `timeout` in drydocs_core was an unrelated `timeout=30` in landing_zones.py.
# No transaction timeout, no retry ceiling, no acquisition timeout, no
# cancellation path - so an unreachable server hung the caller with nothing to
# read and nothing to cancel.


def test_the_declared_block_is_what_the_client_runs_under():
    """The values come from config/dev-environment.yaml, never a literal in the
    client (ADR 0014). This reads the REAL file, so a future edit to the block
    is reflected here rather than pinned to today's numbers."""
    from drydocs_core.config import load_driver_bounds

    declared = load_driver_bounds()
    client = Neo4jClient("bolt://fake", "u", "p")
    assert client.bounds == declared
    # every wait is positive and finite - an unbounded value is the bug
    for value in (
        declared.connection_timeout,
        declared.connection_acquisition_timeout,
        declared.max_transaction_retry_time,
        declared.transaction_timeout,
    ):
        assert 0 < value < math.inf


def test_the_constructor_overrides_the_file():
    bounds = Neo4jDriverBounds(
        connection_timeout=1.0,
        connection_acquisition_timeout=2.0,
        max_transaction_retry_time=3.0,
        transaction_timeout=4.0,
    )
    assert Neo4jClient("bolt://fake", "u", "p", bounds=bounds).bounds is bounds


def test_a_missing_block_falls_back_rather_than_refusing(tmp_path):
    """dev-environment.yaml is canonical-company in PORT-MANIFEST.yaml, so a
    port does NOT carry this block across. A checkout whose file predates it
    must still get bounded waits - raising would turn a missing optional block
    into a broken tree on the far side of a port."""
    from drydocs_core.config import DRIVER_BOUND_DEFAULTS, load_driver_bounds

    empty = tmp_path / "dev-environment.yaml"
    empty.write_text("neo4j:\n  container: x\n", encoding="utf-8")
    assert load_driver_bounds(empty) == Neo4jDriverBounds(**DRIVER_BOUND_DEFAULTS)
    assert load_driver_bounds(tmp_path / "absent.yaml") == Neo4jDriverBounds(
        **DRIVER_BOUND_DEFAULTS
    )


def test_one_bad_value_does_not_take_the_others_with_it(tmp_path):
    from drydocs_core.config import DRIVER_BOUND_DEFAULTS, load_driver_bounds

    path = tmp_path / "dev-environment.yaml"
    path.write_text(
        "neo4j:\n"
        "  driver:\n"
        "    connection_timeout: 2.5\n"
        "    connection_acquisition_timeout: not-a-number\n"
        "    max_transaction_retry_time: 0\n"  # a zero wait is not a wait
        "    transaction_timeout: true\n",  # bool is an int in Python; not a timeout
        encoding="utf-8",
    )
    bounds = load_driver_bounds(path)
    assert bounds.connection_timeout == 2.5
    assert (
        bounds.connection_acquisition_timeout
        == DRIVER_BOUND_DEFAULTS["connection_acquisition_timeout"]
    )
    assert bounds.max_transaction_retry_time == DRIVER_BOUND_DEFAULTS["max_transaction_retry_time"]
    assert bounds.transaction_timeout == DRIVER_BOUND_DEFAULTS["transaction_timeout"]


def test_the_pool_waits_reach_the_real_driver_constructor(monkeypatch):
    """Not "we passed something" - the driver ACCEPTS these three names, so a
    typo here would be a TypeError from the driver rather than a silent no-op."""
    captured: dict = {}
    real = neo4j.GraphDatabase.driver

    def spy(uri, **config):
        captured.update(config)
        return real(uri, **config)  # constructs; no connection is opened yet

    monkeypatch.setattr("drydocs_core.neo4j_client.GraphDatabase.driver", spy)
    bounds = Neo4jDriverBounds(
        connection_timeout=1.0,
        connection_acquisition_timeout=2.0,
        max_transaction_retry_time=3.0,
        transaction_timeout=4.0,
    )
    with Neo4jClient("bolt://localhost:1", "u", "p", bounds=bounds):
        pass
    assert captured["connection_timeout"] == 1.0
    assert captured["connection_acquisition_timeout"] == 2.0
    assert captured["max_transaction_retry_time"] == 3.0
    # the fourth is NOT pool configuration - it rides on the transaction
    assert "transaction_timeout" not in captured


def test_the_transaction_timeout_rides_on_the_managed_transaction():
    """`execute_read`/`execute_write` take no timeout argument in driver 5.28
    (measured: their signature is `(transaction_function, *args, **kwargs)` and
    the kwargs go to the function). `unit_of_work` is the driver's own route,
    and it stamps the work function with the metadata the session reads."""
    client, _, _ = _client()
    client._bounds = Neo4jDriverBounds(transaction_timeout=7.5)
    seen: list = []

    class _Recorder(_FakeSession):
        def _apply(self, mode, work):
            seen.append(getattr(work, "timeout", None))
            return super()._apply(mode, work)

    client._driver.session = lambda database=None: _Recorder(
        client._driver._log, [{"v": 1}], _FakeSummary(None)
    )
    client.read("MATCH (n) RETURN n")
    assert seen == [7.5]


def test_run_script_carries_the_same_ceiling_on_its_auto_commit_path():
    client, _, log = _client()
    client._bounds = Neo4jDriverBounds(transaction_timeout=9.0)
    client.run_script("MERGE (a:A);\n")
    (sent,) = (e for e in log if e[0] == "session.run")
    assert isinstance(sent[1], Query)
    assert sent[1].timeout == 9.0


def test_an_unreachable_server_gives_up_within_the_ceiling():
    """The failure CORE13 exists to end, driven rather than described: a socket
    that ACCEPTS and never speaks bolt.

    MEASURED both ways on the laptop, 2026-09-10, against this same silent
    socket. Unbounded - the construction at the CORE11 tip, `liveness_check_
    timeout=0` and nothing else - the driver's own defaults gave a 60s handshake
    deadline and then retried five times with backoff: **102.9 seconds** before
    `ServiceUnavailable`. With the bounds below: **under 5**. That ratio is the
    finding; the assertion is generous against a slow runner, not tuned to it.

    A listening-but-silent socket rather than a closed port on purpose - a
    closed port is refused instantly and would prove nothing about a timeout.
    """
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)  # never accept(): the handshake hangs
    port = listener.getsockname()[1]
    bounds = Neo4jDriverBounds(
        connection_timeout=1.0,
        connection_acquisition_timeout=2.0,
        max_transaction_retry_time=1.0,
        transaction_timeout=1.0,
    )
    started = time.monotonic()
    try:
        # DriverError, not Neo4jError: the server never answered, so there is no
        # server-side error to carry - the driver is the one reporting.
        with pytest.raises(neo4j.exceptions.DriverError) as info:
            with Neo4jClient(f"bolt://127.0.0.1:{port}", "u", "p", bounds=bounds) as client:
                client.read("RETURN 1 AS one")
    finally:
        listener.close()
    elapsed = time.monotonic() - started
    # NAMED, not a bare hang: the driver says what it could not do
    assert type(info.value).__name__ in ("ServiceUnavailable", "SessionExpired")
    # …and it says so within the wait we declared, with slack for a slow runner
    assert elapsed < 20, f"gave up after {elapsed:.1f}s - the ceiling did not hold"


# ── CORE14: four worlds stop being one False ─────────────────────────────────
#
# `apoc_available` was `try: ... except Exception: return False`. APOC absent,
# the server unreachable, the credentials wrong and any unexpected fifth thing
# all produced the same answer, so `drydocs bootstrap` printed "APOC required."
# at people whose database was merely stopped. ADR 0021 was ACCEPTED on
# 2026-09-09, which resolves the item's conditional: this is a probe and it
# returns CheckOutcome.


class _RaisingClient(Neo4jClient):
    """A client whose read() raises whatever the test hands it."""

    def __init__(self, exc: Exception) -> None:
        super().__init__("bolt://fake", "u", "p", bounds=Neo4jDriverBounds())
        self._exc = exc

    def read(self, *a, **k):
        raise self._exc


def _server_error(code: str, message: str) -> neo4j.exceptions.ClientError:
    """A ClientError carrying a server code, by the one route driver 5.28 does
    not deprecate. Assigning `.code` on an instance warns ("Altering the code of
    a Neo4jError is deprecated") and `Neo4jError.hydrate` warns that it is
    internal - so the code is declared as a CLASS attribute on a throwaway
    subclass, which shadows the property for reads and touches no internals.
    What the probe reads is `exc.code`, and that is what this provides."""
    subclass = type("_ServerSaid", (neo4j.exceptions.ClientError,), {"code": code})
    return subclass(message)


def _procedure_not_found() -> neo4j.exceptions.ClientError:
    return _server_error(
        "Neo.ClientError.Procedure.ProcedureNotFound",
        "There is no procedure with the name `apoc.version`",
    )


def test_apoc_present_is_checked_clean():
    client, _, _ = _client(rows=[{"v": "5.28.0"}])
    outcome = client.apoc_available()
    assert outcome.is_clean
    assert "apoc.version()" in (outcome.subject or "")


def test_apoc_absent_is_a_finding_not_a_silence():
    """The ONE state in which 'install APOC' is the right advice. The server
    answered; what it said is that the procedure does not exist."""
    outcome = _RaisingClient(_procedure_not_found()).apoc_available()
    assert not outcome.is_clean
    assert not outcome.is_not_checked, "a server that ANSWERED did not fail to check"
    assert outcome.count == 1
    assert "not installed" in outcome.findings[0]


def test_an_unreachable_server_is_not_checked_and_says_so():
    outcome = _RaisingClient(
        neo4j.exceptions.ServiceUnavailable("Couldn't connect to 127.0.0.1:7687")
    ).apoc_available()
    assert outcome.is_not_checked
    assert "could not be reached" in outcome.reason
    assert "ServiceUnavailable" in outcome.reason
    # the reason must not claim anything about APOC itself
    assert "not installed" not in outcome.reason


def test_bad_credentials_are_not_checked_and_are_their_own_class():
    outcome = _RaisingClient(
        neo4j.exceptions.AuthError("The client is unauthorized due to authentication failure.")
    ).apoc_available()
    assert outcome.is_not_checked
    assert "authentication" in outcome.reason


def test_a_server_side_refusal_that_is_not_a_missing_procedure_is_not_checked():
    """A ClientError that is NOT ProcedureNotFound - a forbidden procedure on a
    locked-down server, say. The server answered, but not about APOC's presence."""
    exc = _server_error(
        "Neo.ClientError.Security.Forbidden",
        "Executing procedure is not allowed for user 'reader'.",
    )
    outcome = _RaisingClient(exc).apoc_available()
    assert outcome.is_not_checked
    assert "Forbidden" in outcome.reason


def test_an_unexpected_class_is_reported_as_unknown_rather_than_negative():
    outcome = _RaisingClient(RuntimeError("something nobody predicted")).apoc_available()
    assert outcome.is_not_checked
    assert "RuntimeError" in outcome.reason


def test_the_four_classes_are_actually_distinguishable():
    """The point of the item in one assertion, and MEASURED both ways on the
    laptop, 2026-09-10, by driving the old body over these same four worlds:

        OLD  apoc present           -> True
        OLD  apoc NOT installed     -> False
        OLD  server unreachable     -> False
        OLD  bad credentials        -> False       2 distinct answers of 4

    Three worlds shared one answer, and the two that shared it needed opposite
    actions from the operator: install a plugin, or start a database. Now: 4.
    """
    answers = [
        _client(rows=[{"v": "5.28.0"}])[0].apoc_available(),
        _RaisingClient(_procedure_not_found()).apoc_available(),
        _RaisingClient(neo4j.exceptions.ServiceUnavailable("x")).apoc_available(),
        _RaisingClient(neo4j.exceptions.AuthError("x")).apoc_available(),
    ]
    assert len({a.render() for a in answers}) == 4


def test_the_probe_never_raises_and_never_coerces():
    outcome = _RaisingClient(neo4j.exceptions.ServiceUnavailable("x")).apoc_available()
    # ADR 0021 D1: `if not client.apoc_available()` must fail LOUDLY rather than
    # read not-checked as either clean or failed. That is what protects a caller
    # this change did not reach.
    with pytest.raises(TypeError, match="three states"):
        bool(outcome)
