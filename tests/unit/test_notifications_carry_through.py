"""R21 — Neo4j notifications are carried, not discarded, at all three points.

The 2026-08-20 incident: a query built on vocabulary the graph did not hold
raised FOUR non-fatal warnings and presented as a clean empty answer. The API
runner discarded the summary, the agent read helper returned rows only, and
:AgentRun had no field for them. These cases pin the carry-through:

* the one shape (drydocs_core.notifications) normalises a driver summary and
  round-trips through the homogeneous string list a Neo4j property can hold;
* a pipeline step keeps its read's notifications, and agent_run_props writes
  ``warnings`` (one JSON string per notification, tagged with the step) and
  ``warning_count`` — a clean run carries ``[]`` / ``0``, never a missing field;
* the API handlers attach ``diagnostics.notifications`` to every response, and
  a plain duck-typed runner yields an empty list rather than breaking;
* LIVE (skips naming the venue, J18): an unknown-label statement produces a
  notification through ``run_read`` and through the live API runner.

The end-user answer is unchanged: a notification is never turned into an error.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common import agent_run_writer  # noqa: E402
from graph_qa.envelope import Envelope, Metrics, StepRecord  # noqa: E402

from drydocs_api import handlers  # noqa: E402
from drydocs_api.credentials import CredentialStore  # noqa: E402
from drydocs_api.query_specs import QUERY_SPECS  # noqa: E402
from drydocs_core.notifications import Neo4jNotification, from_summary, to_payload  # noqa: E402

UNKNOWN_LABEL = {
    "code": "Neo.ClientNotification.Statement.UnknownLabelWarning",
    "title": "The provided label is not in the database.",
    "description": "One of the labels in your query is not available in the database (the missing label name is: NoSuchLabelR21)",
    "severity": "WARNING",
    "category": "UNRECOGNIZED",
    "position": {"offset": 7, "line": 1, "column": 8},
}


# -- the shape ----------------------------------------------------------------------


def test_summary_normalises_to_the_one_shape_and_round_trips() -> None:
    summary = SimpleNamespace(notifications=[UNKNOWN_LABEL])
    (n,) = from_summary(summary)
    assert n.code.endswith("UnknownLabelWarning")
    assert n.severity == "WARNING" and n.position == "1:8" and n.category == "UNRECOGNIZED"
    assert Neo4jNotification.from_json(n.as_json()) == n
    assert to_payload([n])[0]["title"] == UNKNOWN_LABEL["title"]


def test_a_clean_summary_is_an_empty_list_not_a_missing_field() -> None:
    assert from_summary(SimpleNamespace(notifications=[])) == []
    assert from_summary(SimpleNamespace()) == []
    assert from_summary(None) == []


# -- (2) envelope -> :AgentRun ----------------------------------------------------------


def _envelope(steps: list[StepRecord]) -> Envelope:
    env = Envelope(
        run_id="qa-r21",
        session_id="s",
        question_sha256="0" * 64,
        question_chars=12,
        tier="text2cypher",
        answer="",
        model="m",
        provider="p",
    )
    env.steps = steps
    env.metrics = Metrics()
    return env


def test_agent_run_props_persist_the_warnings_payload_tagged_by_step() -> None:
    note = to_payload(from_summary(SimpleNamespace(notifications=[UNKNOWN_LABEL])))
    steps = [
        StepRecord(i=1, kind="router"),
        StepRecord(
            i=2,
            kind="text2cypher",
            cypher="MATCH (n:NoSuchLabelR21) RETURN n",
            rows=0,
            notifications=note,
        ),
        StepRecord(i=3, kind="answer"),
    ]
    props = agent_run_writer.agent_run_props(_envelope(steps))
    assert props["warning_count"] == 1
    (w,) = props["warnings"]
    decoded = json.loads(w)
    assert decoded["step"] == 2
    assert decoded["code"].endswith("UnknownLabelWarning")
    assert decoded["position"] == "1:8"
    # homogeneous strings — what a Neo4j list property can hold
    assert all(isinstance(x, str) for x in props["warnings"])


def test_a_clean_run_carries_an_empty_payload() -> None:
    props = agent_run_writer.agent_run_props(
        _envelope([StepRecord(i=1, kind="spec", cypher="RETURN 1", rows=1)])
    )
    assert props["warnings"] == [] and props["warning_count"] == 0
    # the writer drops None, never [] — the field reaches the node
    kept = {k: v for k, v in props.items() if v is not None}
    assert "warnings" in kept and "warning_count" in kept


def test_admin_spec_exposes_the_payload_and_the_count() -> None:
    spec = QUERY_SPECS["console.agent-runs.v1"]
    names = [c.name for c in spec.columns]
    assert "warning_count" in names and "warnings" in names
    assert "r.warning_count" in spec.cypher and "r.warnings" in spec.cypher


# -- (1) the API path ---------------------------------------------------------------


class _PlainRunner:
    def run(self, cypher, params, database):
        return ["n"], [{"n": 1}]


class _RichRunner(_PlainRunner):
    def run_with_diagnostics(self, cypher, params, database):
        return (
            ["n"],
            [{"n": 1}],
            to_payload(from_summary(SimpleNamespace(notifications=[UNKNOWN_LABEL]))),
        )


def test_handlers_attach_diagnostics_and_tolerate_plain_runners() -> None:
    store = handlers.InMemorySessionStore()
    creds = CredentialStore()
    creds.set("morpheus", "a-test-console-secret")
    token = handlers.login("morpheus", "a-test-console-secret", store, creds)["token"]
    rich = handlers.run_raw(
        "MATCH (n:NoSuchLabelR21) RETURN count(n) AS n", token, store, _RichRunner()
    )
    assert rich["rows"] == [{"n": 1}]  # the answer is untouched — not an error
    assert rich["diagnostics"]["notifications"][0]["code"].endswith("UnknownLabelWarning")
    plain = handlers.run_raw("RETURN 1 AS n", token, store, _PlainRunner())
    assert plain["diagnostics"] == {"notifications": []}


# -- live (J18) -------------------------------------------------------------------------


def _venue() -> str:
    try:
        from drydocs_core.config import load_settings

        cfg, _, _ = load_settings()
        return f"{cfg.uri} / {cfg.database} (host {os.environ.get('COMPUTERNAME') or os.uname().nodename})"
    except Exception:
        return "settings unresolved"


@pytest.fixture(scope="module")
def live_settings():
    try:
        from drydocs_core.config import load_settings
        from drydocs_core.neo4j_client import Neo4jClient

        cfg, _, _ = load_settings()
        pw = cfg.password.get_secret_value()
        if not pw:
            pytest.skip(f"no NEO4J_PASSWORD — live notification check skipped ({_venue()})")
        with Neo4jClient(cfg.uri, cfg.user, pw, cfg.database) as cli:
            cli.run("RETURN 1 AS ok")
    except Exception as exc:
        pytest.skip(
            f"no reachable Neo4j at {_venue()}: {type(exc).__name__} — live notification check skipped"
        )
    return cfg


def test_live_unknown_label_reaches_the_agent_read_result(live_settings, monkeypatch) -> None:
    monkeypatch.setenv("NEO4J_URI", live_settings.uri)
    monkeypatch.setenv("NEO4J_USER", live_settings.user)
    monkeypatch.setenv("NEO4J_PASSWORD", live_settings.password.get_secret_value())
    monkeypatch.setenv("NEO4J_DATABASE", live_settings.database)
    from common import graph_read

    result = graph_read.run_read("MATCH (n:NoSuchLabelR21) RETURN count(n) AS n")
    assert result.records == [{"n": 0}]  # the answer: zero, honestly
    assert result.notifications, f"no notification carried at {_venue()}"
    assert any("NoSuchLabelR21" in n["description"] for n in result.notifications)
    assert all(n["severity"] for n in result.notifications)


def test_live_unknown_label_reaches_the_api_runner(live_settings) -> None:
    from drydocs_api.app import LiveRunner

    runner = LiveRunner(live_settings)
    try:
        keys, rows, notes = runner.run_with_diagnostics(
            "MATCH (n:NoSuchLabelR21) RETURN count(n) AS n", {}, live_settings.database
        )
    finally:
        runner.close()
    assert (keys, rows) == (["n"], [{"n": 0}])
    assert notes and any("NoSuchLabelR21" in n["description"] for n in notes), _venue()
