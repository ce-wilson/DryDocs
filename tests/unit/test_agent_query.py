"""R9 — the agent query command: read-only, deterministic QuerySpec navigation.

Driven through ``main()`` with an injected fake runner — the drydocs-api
offline idiom (no server, no driver, no FastAPI). The assertions read the
command's stdout as JSON: that output IS the contract under test (the item's
"stable JSON output"), which is J37's one allowed case for reading CLI output.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from drydocs_api import agent_query
from drydocs_api.exports import execute_spec, list_specs
from drydocs_api.query_specs import QUERY_SPECS, QuerySpec


class FakeRunner:
    def __init__(self, keys=None, rows=None, *, raises: Exception | None = None):
        self.calls: list[tuple[str, dict, str]] = []
        self._keys = keys or ["name"]
        self._rows = rows if rows is not None else [{"name": "demo"}]
        self._raises = raises

    def run(self, cypher, params, database):
        self.calls.append((cypher, dict(params), database))
        if self._raises is not None:
            raise self._raises
        return self._keys, self._rows


def _spec_with_optional_int_limit() -> QuerySpec:
    """A registry spec whose only params are optional and include an int
    ``limit`` — the common shape, chosen from the registry rather than named,
    so a renamed spec does not silently retire this test."""
    for spec in QUERY_SPECS.values():
        names = {p.name: p for p in spec.params}
        if (
            "limit" in names
            and names["limit"].type == "int"
            and not any(p.required for p in spec.params)
        ):
            return spec
    raise AssertionError("no registry spec with an optional int limit")


def _spec_with_a_string_param() -> QuerySpec | None:
    for spec in QUERY_SPECS.values():
        if any(p.type == "string" for p in spec.params):
            return spec
    return None


def _run(argv: list[str], runner=None, capsys=None) -> tuple[int, object]:
    rc = agent_query.main(argv, runner=runner)
    out = capsys.readouterr().out
    assert out.endswith("\n") and out.count("\n") == 1 or out.count("\n") > 1  # one document
    return rc, json.loads(out)


# ---- list / describe: the GET /specs rows, not a third shape ------------------------


def test_list_prints_the_specs_rows_the_api_lists(capsys):
    rc, payload = _run(["list"], capsys=capsys)
    assert rc == agent_query.EXIT_OK
    assert payload == json.loads(json.dumps(list_specs(), default=str))
    assert {row["id"] for row in payload} == set(QUERY_SPECS)


def test_describe_prints_one_row_with_its_cypher(capsys):
    spec = _spec_with_optional_int_limit()
    rc, payload = _run(["describe", spec.id], capsys=capsys)
    assert rc == agent_query.EXIT_OK
    assert payload["id"] == spec.id and payload["cypher"] == spec.cypher
    assert payload == json.loads(json.dumps(agent_query.describe_spec(spec), default=str))


# ---- run: one envelope, shared with the API ----------------------------------------


def test_run_prints_exactly_the_api_envelope(capsys):
    spec = _spec_with_optional_int_limit()
    fake = FakeRunner(keys=["a", "b"], rows=[{"a": 1, "b": "x"}])
    rc, payload = _run(["run", spec.id, "-p", "limit=5"], runner=fake, capsys=capsys)
    assert rc == agent_query.EXIT_OK
    expected = execute_spec(
        spec, {"limit": 5}, FakeRunner(keys=["a", "b"], rows=[{"a": 1, "b": "x"}])
    )
    assert payload == json.loads(json.dumps(expected, default=str))
    assert set(payload) == {
        "spec_id",
        "database",
        "classification",
        "columns",
        "cypher",
        "params",
        "keys",
        "rows",
        "watermarked",
        "ephemeral",
    }
    assert "ok" not in payload  # a success IS the envelope; only failures carry ok


def test_run_hands_the_runner_the_spec_verbatim_and_typed_params(capsys):
    spec = _spec_with_optional_int_limit()
    fake = FakeRunner()
    rc, _ = _run(["run", spec.id, "-p", "limit=10"], runner=fake, capsys=capsys)
    assert rc == agent_query.EXIT_OK
    (cypher, params, database), *_ = fake.calls
    assert cypher == spec.cypher and database == spec.database
    assert params["limit"] == 10 and isinstance(params["limit"], int)


def test_run_applies_declared_defaults_when_no_params_are_given(capsys):
    spec = _spec_with_optional_int_limit()
    fake = FakeRunner()
    _run(["run", spec.id], runner=fake, capsys=capsys)
    default = next(p.default for p in spec.params if p.name == "limit")
    assert fake.calls[0][1]["limit"] == default


def test_same_input_yields_identical_bytes(capsys):
    spec = _spec_with_optional_int_limit()
    outs = []
    for _ in range(2):
        agent_query.main(["run", spec.id, "-p", "limit=3"], runner=FakeRunner())
        outs.append(capsys.readouterr().out)
    assert outs[0] == outs[1]
    assert outs[0].endswith("\n") and "\n" not in outs[0][:-1]


def test_pretty_is_the_same_document_indented(capsys):
    spec = _spec_with_optional_int_limit()
    _, compact = _run(["run", spec.id], runner=FakeRunner(), capsys=capsys)
    _, pretty = _run(["--pretty", "run", spec.id], runner=FakeRunner(), capsys=capsys)
    assert compact == pretty


# ---- refusals: by name, on stdout, exit 2 ------------------------------------------


def test_unknown_spec_is_refused_with_the_registry_size(capsys):
    rc, payload = _run(["run", "nope.nothing.v1"], runner=FakeRunner(), capsys=capsys)
    assert rc == agent_query.EXIT_USAGE
    assert payload["ok"] is False and payload["error"] == "unknown-spec"
    assert payload["registry_size"] == len(QUERY_SPECS)
    rc, payload = _run(["describe", "nope.nothing.v1"], capsys=capsys)
    assert rc == agent_query.EXIT_USAGE and payload["error"] == "unknown-spec"


def test_unknown_param_is_refused_by_name_and_the_runner_never_runs(capsys):
    spec = _spec_with_optional_int_limit()
    fake = FakeRunner()
    rc, payload = _run(["run", spec.id, "-p", "bogus=1"], runner=fake, capsys=capsys)
    assert rc == agent_query.EXIT_USAGE
    assert payload["error"] == "bad-param" and "bogus" in payload["message"]
    assert [d["name"] for d in payload["declared"]] == [p.name for p in spec.params]
    assert fake.calls == []


def test_mistyped_param_is_refused_by_name(capsys):
    spec = _spec_with_optional_int_limit()
    rc, payload = _run(["run", spec.id, "-p", "limit=ten"], runner=FakeRunner(), capsys=capsys)
    assert rc == agent_query.EXIT_USAGE
    assert payload["error"] == "bad-param" and "limit" in payload["message"]


def test_param_syntax_is_refused(capsys):
    spec = _spec_with_optional_int_limit()
    rc, payload = _run(["run", spec.id, "-p", "limit"], runner=FakeRunner(), capsys=capsys)
    assert rc == agent_query.EXIT_USAGE and payload["error"] == "bad-param"
    rc, payload = _run(
        ["run", spec.id, "-p", "limit=1", "-p", "limit=2"], runner=FakeRunner(), capsys=capsys
    )
    assert rc == agent_query.EXIT_USAGE and "twice" in payload["message"]


def test_string_params_pass_through_and_split_on_the_first_equals():
    spec = _spec_with_a_string_param()
    if spec is None:
        pytest.skip("no registry spec declares a string param today")
    name = next(p.name for p in spec.params if p.type == "string")
    raw = agent_query.parse_param_operands([f"{name}=a=b"])
    assert raw == {name: "a=b"}
    assert agent_query.coerce_params(spec, raw) == {name: "a=b"}


def test_ephemeral_ids_are_refused_without_a_session(capsys):
    fake = FakeRunner()
    rc, payload = _run(["run", "eph.abc123"], runner=fake, capsys=capsys)
    assert rc == agent_query.EXIT_USAGE and payload["error"] == "ephemeral-spec"
    assert fake.calls == []


def test_no_option_accepts_cypher():
    """Zero write paths, structurally: the parser has no operand that carries a
    query. The only things an agent can name are a spec id and its declared
    params."""
    parser = agent_query.build_parser()
    dests = {
        a.dest
        for sub in parser._subparsers._group_actions
        for a in sub.choices.values()
        for a in a._actions
    }
    assert dests <= {"help", "spec_id", "param"}


# ---- the runner's failure is an outcome, not a traceback ----------------------------


def test_runner_failure_is_exit_1_with_json(capsys):
    spec = _spec_with_optional_int_limit()
    fake = FakeRunner(raises=ConnectionError("bolt refused"))
    rc, payload = _run(["run", spec.id], runner=fake, capsys=capsys)
    assert rc == agent_query.EXIT_RUN_FAILED
    assert payload["ok"] is False and payload["error"] == "run-failed"
    assert payload["message"] == "ConnectionError: bolt refused"
    assert payload["spec_id"] == spec.id and payload["database"] == spec.database


# ---- framework-free on import: the property the agents venv depends on --------------


def test_import_pulls_neither_the_framework_nor_the_wiring_module():
    """Subprocess, because an in-process import proves nothing about what an
    earlier test already imported (S13's lesson). The neo4j PACKAGE is not in
    the list on purpose: drydocs_core.config imports it, so every first-party
    import carries it — what must stay out is fastapi/uvicorn and
    drydocs_api.app, the module that builds the driver and wires the API."""
    code = (
        "import sys; import drydocs_api.agent_query; "
        "print(sorted(m for m in ('fastapi', 'uvicorn', 'drydocs_api.app') if m in sys.modules))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert out == "[]", f"agent_query import dragged in: {out}"
