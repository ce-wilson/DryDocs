"""R16 — the agent verbs: impact, context, trace as names over REVIEWED specs.

The item's clauses, one block each: (a) three verbs at the estate's grain;
(b) each verb IS a registry QuerySpec, so read-only and exposed-Cypher are
inherited, never re-implemented; (c) the generic MCP server is untouched (this
file asserts the package side of that: no new module, route or Cypher surface);
(d) the verbs carry R15's epistemic field with the spec's own wording; (e) the
declared shape is the spec's columns and no operand takes Cypher.

Driven through ``agent_query.main()`` with an injected fake runner, the
drydocs-api offline idiom; stdout is read as JSON because the JSON IS the
contract (J37's one allowed case).
"""

from __future__ import annotations

import json

import pytest

from drydocs_api import agent_query
from drydocs_api.epistemics import CAUSE_PROBES, CAUSE_UNRESOLVED_INVOCATION, CHAIN_WALK
from drydocs_api.exports import execute_spec
from drydocs_api.guard import ensure_no_element_ids, ensure_read_only
from drydocs_api.query_specs import QUERY_SPECS
from drydocs_api.verbs import VERBS, UnknownVerbError, list_verbs, verb

THE_THREE = ("impact", "context", "trace")

# The one operand each verb needs on top of its defaults, at synthetic values.
_ARGS = {
    "impact": ["-p", "job=J70001"],
    "context": ["-p", "job=J70001"],
    "trace": ["-p", "from_job=J70001", "-p", "to_job=J70002"],
}


class ProbeRunner:
    """Answers the R15 cause probes with configured counts and every other
    statement with the configured rows; records the Cypher it was handed."""

    def __init__(self, counts=None, rows=(), keys=("a",)):
        self.counts = counts or {}
        self.rows, self.keys = list(rows), list(keys)
        self.calls: list[tuple[str, dict, str]] = []

    def run(self, cypher, params, database):
        self.calls.append((cypher, dict(params), database))
        for cls, probe in CAUSE_PROBES.items():
            if cypher == probe:
                n = self.counts.get(cls, 0)
                return ["n"], ([] if n is None else [{"n": n}])
        return self.keys, list(self.rows)


def _run(argv, runner, capsys):
    rc = agent_query.main(argv, runner=runner)
    return rc, json.loads(capsys.readouterr().out)


# ---- (a) three verbs, at the estate's grain --------------------------------------------


def test_exactly_the_three_verbs_exist_and_resolve():
    assert tuple(VERBS) == THE_THREE
    for name in THE_THREE:
        assert verb(name).name == name
    with pytest.raises(UnknownVerbError, match="impact, context, trace"):
        verb("cypher")


def test_verbs_take_job_names_not_ids_or_statements():
    """The grain is the estate's: a verb is asked about a JOB by name. Every
    declared param is a job name or the display limit."""
    for v in VERBS.values():
        names = {p.name for p in v.spec.params}
        assert names <= {"job", "from_job", "to_job", "limit"}, (v.name, names)
        assert names & {"job", "from_job"}, f"{v.name} is not asked about a job"


# ---- (b) each verb IS a reviewed registry spec ------------------------------------------


def test_each_verb_binds_a_registry_spec_by_the_verb_id_grammar():
    for v in VERBS.values():
        assert v.spec_id == f"verb.{v.name}.v1"
        assert v.spec_id in QUERY_SPECS
        assert v.spec is QUERY_SPECS[v.spec_id]


def test_each_verb_spec_is_read_only_element_id_free_and_ground_truth_scoped():
    """What the registry guards already enforce, asserted per verb so a verb
    added outside the registry cannot pass by accident."""
    for v in VERBS.values():
        ensure_read_only(v.spec.cypher)
        ensure_no_element_ids(v.spec.cypher, v.spec_id)
        assert "NOT " in v.spec.cypher and ":SchemaMeta" in v.spec.cypher
        assert ":Uncertain" in v.spec.cypher  # the registry rewrite ran on it
        assert v.spec.database == "drydocs"


def test_verb_runs_the_spec_cypher_verbatim_and_nothing_else(capsys):
    """The Cypher the runner receives is the registry row's, byte for byte —
    the verb layer added no statement of its own. Probes are the only other
    statements, and they are R15's declared ones."""
    for name in THE_THREE:
        runner = ProbeRunner()
        rc, _ = _run(["verb", name, *_ARGS[name]], runner, capsys)
        assert rc == agent_query.EXIT_OK
        statements = [c for c, _, _ in runner.calls]
        assert verb(name).spec.cypher in statements
        others = set(statements) - {verb(name).spec.cypher}
        assert others <= set(CAUSE_PROBES.values()), (name, others)


def test_verb_prints_exactly_the_run_envelope_for_its_spec(capsys):
    """``verb impact`` and ``run verb.impact.v1`` are one path: same fourteen
    keys, same values, ``spec_id`` naming the spec the verb is."""
    for name in THE_THREE:
        v = verb(name)
        rows = [{c: "x" for c in v.shape}]
        rc, payload = _run(
            ["verb", name, *_ARGS[name]], ProbeRunner(rows=rows, keys=v.shape), capsys
        )
        assert rc == agent_query.EXIT_OK
        bound = {k: v_ for k, v_ in (a.split("=", 1) for a in _ARGS[name][1::2])}
        expected = execute_spec(
            v.spec, {**bound, "limit": 500}, ProbeRunner(rows=rows, keys=v.shape)
        )
        assert payload == json.loads(json.dumps(expected, default=str))
        assert payload["spec_id"] == v.spec_id
        assert len(payload) == 14 and "ok" not in payload


# ---- (c) the generic MCP server stays beside it, unchanged ------------------------------


def test_the_verb_layer_adds_no_route_and_no_component():
    """The verbs are a module in drydocs_api plus two sub-commands. The API's
    route table is untouched — a verb is reached as ``/specs/verb.<name>.v1/run``
    — and nothing under ``agents/`` or a new package is needed for them."""
    pytest.importorskip("fastapi", reason="fastapi is an optional dep (the api group)")
    from drydocs_api.app import create_app

    paths = {r.path for r in create_app().routes}
    assert not any("verb" in p for p in paths), sorted(p for p in paths if "verb" in p)


# ---- (d) R15's epistemic field, one wording -------------------------------------------


def test_every_verb_declares_the_chain_walk():
    for v in VERBS.values():
        assert v.spec.walk is CHAIN_WALK, f"{v.name} is ungraded"
    assert CHAIN_WALK.gate_pending == ("scheduler_depends_on_file",)


def test_verb_envelope_carries_the_spec_grade_unchanged(capsys):
    """An unresolved invocation in the estate makes every chain answer a lower
    bound; zero causes make it exact. The verb prints the label the spec
    graded, with the causes as they arrived - no second wording."""
    rc, bounded = _run(
        ["verb", "impact", *_ARGS["impact"]],
        ProbeRunner(counts={CAUSE_UNRESOLVED_INVOCATION: 3}),
        capsys,
    )
    assert rc == agent_query.EXIT_OK
    assert bounded["epistemic"] == "lower-bound"
    assert {c["cause"] for c in bounded["causes"]} >= {
        CAUSE_UNRESOLVED_INVOCATION,
        "gate-pending-edge",
    }
    # gate_pending alone keeps the label at lower-bound: a planned edge is a
    # cause with no count, and the graph cannot measure what it has no loader for.
    _, unmeasured = _run(["verb", "impact", *_ARGS["impact"]], ProbeRunner(), capsys)
    assert unmeasured["epistemic"] == "lower-bound"
    assert [c["detail"] for c in unmeasured["causes"]] == ["scheduler_depends_on_file"]


# ---- (e) shape, and no Cypher operand ----------------------------------------------------


def test_declared_shape_is_the_spec_columns_and_verbs_lists_it(capsys):
    rc, rows = _run(["verbs"], None, capsys)
    assert rc == agent_query.EXIT_OK
    assert [r["name"] for r in rows] == list(THE_THREE)
    for r in rows:
        v = verb(r["name"])
        assert r["columns"] == list(v.shape) == [c.name for c in v.spec.columns]
        assert r["spec_id"] == v.spec_id
        assert {p["name"] for p in r["params"]} == {p.name for p in v.spec.params}
    assert rows == json.loads(json.dumps(list_verbs(), default=str))


def test_every_verb_returns_the_folder_beside_the_job_name():
    """job_name is indexed, not unique - (folder_id, job_id) is the key. An
    ambiguous name must be visible in the rows, never silently merged."""
    assert "folder" in verb("impact").shape
    assert "folder" in verb("context").shape
    assert {"from_folder", "to_folder"} <= set(verb("trace").shape)


def test_unknown_verb_is_json_exit_2_naming_the_valid_set(capsys):
    rc, payload = _run(["verb", "nuke", "-p", "job=J70001"], ProbeRunner(), capsys)
    assert rc == agent_query.EXIT_USAGE
    assert payload["ok"] is False and payload["error"] == "unknown-verb"
    assert payload["verbs"] == sorted(THE_THREE)


def test_verb_params_are_validated_before_the_runner_runs(capsys):
    runner = ProbeRunner()
    rc, payload = _run(["verb", "trace", "-p", "from_job=J70001"], runner, capsys)
    assert rc == agent_query.EXIT_USAGE and payload["error"] == "bad-param"
    assert "to_job" in payload["message"]
    assert runner.calls == []
    rc, payload = _run(["verb", "impact", "-p", "cypher=MATCH (n) RETURN n"], runner, capsys)
    assert rc == agent_query.EXIT_USAGE and payload["error"] == "bad-param"
    assert runner.calls == []


def test_no_verb_operand_accepts_cypher():
    """The parser's verb sub-command names a verb and its declared params;
    there is no operand a statement could ride in on."""
    parser = agent_query.build_parser()
    vb = parser._subparsers._group_actions[0].choices["verb"]
    dests = {a.dest for a in vb._actions}
    assert dests == {"help", "verb_name", "param"}
