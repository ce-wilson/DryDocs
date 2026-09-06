"""R15 — every lineage/impact answer says whether it is EXACT or a LOWER BOUND,
and names the causes that limited the walk.

Three guards, three failure classes:

* GRADING: `grade` is exact when every declared cause measures zero,
  lower-bound per cause class when one fires, and — the clause the item is
  for — zero rows with lower-bound is DISTINGUISHABLE from zero rows with
  exact in the same envelope. An ungraded spec (no walk declaration) answers
  null, never exact: silence is honest, a default is a claim.

* ENVELOPE: `execute_spec` and the export manifest carry `epistemic` and
  `causes`; the declared response model (`SpecRunOut`) models them, so the
  generated client sees typed fields and not `additionalProperties`.

* STATIC (the R20 shape, applied to walks): a `gate_pending` entry a spec
  declares must EXIST in the vocabulary and still be planned-only — the list
  shrinks when the loader lands — and every probe class a walk names must be
  one the module knows how to measure. The probes themselves are read-only
  and exclude the :SchemaMeta and :Uncertain realms by hand, because they
  never pass through the registry's ground-truth rewrite.
"""

from __future__ import annotations

from collections import defaultdict

import pytest

from drydocs_api.ephemeral_specs import EphemeralSpecStore
from drydocs_api.epistemics import (
    CAUSE_CLASSES,
    CAUSE_GATE_PENDING_EDGE,
    CAUSE_PROBES,
    CAUSE_UNPARSED_CMD_LINE,
    CAUSE_UNRESOLVED_INVOCATION,
    EXACT,
    LOWER_BOUND,
    WalkDeclaration,
    grade,
)
from drydocs_api.exports import (
    ExportLedger,
    execute_spec,
    export_spec,
)
from drydocs_api.guard import ensure_read_only
from drydocs_api.query_specs import QUERY_SPECS, ColumnDef, QuerySpec
from drydocs_api.schemas import SpecRunOut
from drydocs_api.sessions import InMemorySessionStore
from drydocs_core.ontology.schema_graph import DEFAULT_VOCAB_PATH
from drydocs_core.yaml_fragments import load_yaml_source

# ---------------------------------------------------------------------------
# fixtures: a runner that answers the probes by cause class and the spec by rows


class ProbeRunner:
    """Answers each probe with the count configured for its cause class, and
    any other Cypher with the configured spec rows. Records what it was asked
    so a test can prove the probes ran against the SPEC's database."""

    def __init__(self, counts: dict[str, int | None] | None = None, rows=(), keys=("a",)):
        self.counts = counts or {}
        self.rows = list(rows)
        self.keys = list(keys)
        self.calls: list[tuple[str, str]] = []

    def run(self, cypher, params, database):
        self.calls.append((cypher, database))
        for cls, probe in CAUSE_PROBES.items():
            if cypher == probe:
                n = self.counts.get(cls, 0)
                return ["n"], ([] if n is None else [{"n": n}])
        return self.keys, list(self.rows)


def _spec(walk: WalkDeclaration | None, spec_id: str = "test.walk.v1") -> QuerySpec:
    return QuerySpec(
        id=spec_id,
        database="drydocs",
        description="R15 fixture",
        cypher="MATCH (n:ControlMJob) WHERE NOT n:SchemaMeta RETURN n.job_name AS a",
        columns=(ColumnDef("a", "string"),),
        classification="internal",
        walk=walk,
    )


MEASURED = WalkDeclaration(probes=(CAUSE_UNPARSED_CMD_LINE, CAUSE_UNRESOLVED_INVOCATION))


# ---------------------------------------------------------------------------
# grading


def test_exact_when_every_declared_cause_measures_zero() -> None:
    runner = ProbeRunner(counts={CAUSE_UNPARSED_CMD_LINE: 0, CAUSE_UNRESOLVED_INVOCATION: 0})
    label, causes = grade(_spec(MEASURED), lambda c, p, d: runner.run(c, p, d)[1])
    assert label == EXACT
    assert causes == []
    # both probes ran, against the spec's own database
    assert [d for _, d in runner.calls] == ["drydocs", "drydocs"]


def test_lower_bound_names_unparsed_cmd_line_with_its_count() -> None:
    runner = ProbeRunner(counts={CAUSE_UNPARSED_CMD_LINE: 7})
    label, causes = grade(_spec(MEASURED), lambda c, p, d: runner.run(c, p, d)[1])
    assert label == LOWER_BOUND
    assert causes == [
        {"cause": CAUSE_UNPARSED_CMD_LINE, "detail": CAUSE_UNPARSED_CMD_LINE, "count": 7}
    ]


def test_lower_bound_names_unresolved_invocation_with_its_count() -> None:
    runner = ProbeRunner(counts={CAUSE_UNRESOLVED_INVOCATION: 3})
    label, causes = grade(_spec(MEASURED), lambda c, p, d: runner.run(c, p, d)[1])
    assert label == LOWER_BOUND
    assert causes == [
        {"cause": CAUSE_UNRESOLVED_INVOCATION, "detail": CAUSE_UNRESOLVED_INVOCATION, "count": 3}
    ]


def test_lower_bound_names_gate_pending_edge_by_vocabulary_entry_id() -> None:
    """A gate-pending cause is static — no probe, no count — and it is keyed by
    the vocabulary ENTRY id, because INVOKES is both an active and a planned
    entry and the label alone could not say which one is missing."""
    walk = WalkDeclaration(gate_pending=("scheduler_invokes_utility",))
    runner = ProbeRunner()
    label, causes = grade(_spec(walk), lambda c, p, d: runner.run(c, p, d)[1])
    assert label == LOWER_BOUND
    assert causes == [
        {"cause": CAUSE_GATE_PENDING_EDGE, "detail": "scheduler_invokes_utility", "count": None}
    ]
    assert runner.calls == []  # nothing to measure


def test_a_probe_that_returns_no_count_is_a_cause_not_a_zero() -> None:
    """J76: an instrument that fails must not fail INTO clean."""
    runner = ProbeRunner(counts={CAUSE_UNPARSED_CMD_LINE: None, CAUSE_UNRESOLVED_INVOCATION: 0})
    label, causes = grade(_spec(MEASURED), lambda c, p, d: runner.run(c, p, d)[1])
    assert label == LOWER_BOUND
    assert [c["cause"] for c in causes] == [CAUSE_UNPARSED_CMD_LINE]
    assert causes[0]["count"] is None


def test_causes_keep_declaration_order_probes_then_gate_pending() -> None:
    walk = WalkDeclaration(
        probes=(CAUSE_UNRESOLVED_INVOCATION, CAUSE_UNPARSED_CMD_LINE),
        gate_pending=("scheduler_depends_on_file",),
    )
    runner = ProbeRunner(counts={CAUSE_UNPARSED_CMD_LINE: 1, CAUSE_UNRESOLVED_INVOCATION: 2})
    _, causes = grade(_spec(walk), lambda c, p, d: runner.run(c, p, d)[1])
    assert [c["detail"] for c in causes] == [
        CAUSE_UNRESOLVED_INVOCATION,
        CAUSE_UNPARSED_CMD_LINE,
        "scheduler_depends_on_file",
    ]


def test_ungraded_spec_answers_null_never_exact() -> None:
    runner = ProbeRunner()
    label, causes = grade(_spec(None), lambda c, p, d: runner.run(c, p, d)[1])
    assert label is None
    assert causes == []
    assert runner.calls == []


def test_unknown_probe_class_is_refused_at_declaration() -> None:
    with pytest.raises(ValueError, match="unknown epistemic probe class"):
        WalkDeclaration(probes=("something-else",))


# ---------------------------------------------------------------------------
# the envelope — the clause the item exists for


def _run(spec: QuerySpec, runner: ProbeRunner) -> dict:
    return execute_spec(spec, {}, runner)


def test_zero_rows_lower_bound_is_distinguishable_from_zero_rows_exact() -> None:
    """Both envelopes have rows == []. Only the label tells them apart, and the
    label is IN the envelope — a consumer never has to infer it."""
    bounded = _run(_spec(MEASURED), ProbeRunner(counts={CAUSE_UNPARSED_CMD_LINE: 5}, rows=[]))
    exact = _run(_spec(MEASURED), ProbeRunner(rows=[]))
    assert bounded["rows"] == [] and exact["rows"] == []
    assert bounded["epistemic"] == LOWER_BOUND and exact["epistemic"] == EXACT
    assert bounded["causes"][0]["cause"] == CAUSE_UNPARSED_CMD_LINE
    assert exact["causes"] == []


def test_envelope_carries_exactly_the_declared_keys() -> None:
    """SpecRunOut forbids extras, so the dict execute_spec builds must be the
    model's field set — nothing more (a CLI-only key belongs on the CLI side)
    and nothing less (the console reads typed fields)."""
    out = _run(_spec(MEASURED), ProbeRunner(rows=[{"a": "x"}]))
    assert set(out) == set(SpecRunOut.model_fields)
    parsed = SpecRunOut.model_validate(out)
    assert parsed.epistemic == EXACT
    assert parsed.causes == []


def test_ungraded_envelope_is_null_and_validates() -> None:
    out = _run(_spec(None), ProbeRunner(rows=[{"a": "x"}]))
    assert out["epistemic"] is None and out["causes"] == []
    assert SpecRunOut.model_validate(out).epistemic is None


def test_registered_lineage_specs_grade_and_inventories_do_not() -> None:
    graded = {sid for sid, s in QUERY_SPECS.items() if s.walk is not None}
    assert {"lineage.hops.v1", "lineage.data-assets.v1"} <= graded
    for sid in ("explorer.jobs.v2", "docs.documents.v1", "lineage.schema-definition.v1"):
        assert QUERY_SPECS[sid].walk is None, f"{sid} declares a walk it does not have"


def test_ephemeral_spec_is_ungraded() -> None:
    store = EphemeralSpecStore()
    reg = store.register(
        "sess-1",
        cypher="MATCH (n:ControlMJob) WHERE NOT n:SchemaMeta RETURN n.job_name AS a LIMIT 5",
        database="drydocs",
        description="agent",
        params={},
    )
    assert reg.as_query_spec().walk is None


def test_export_manifest_records_the_label_and_causes() -> None:
    store = InMemorySessionStore()
    token = store.issue("mouse").token
    ledger = ExportLedger()
    runner = ProbeRunner(counts={CAUSE_UNRESOLVED_INVOCATION: 2}, rows=[])
    spec = QUERY_SPECS["lineage.hops.v1"]
    job = export_spec(spec.id, {}, "jsonl", token, store, runner, ledger)
    list(job.chunks)  # exhaust: the manifest registers on completion
    manifest = ledger.manifest(job.export_id)
    assert manifest["row_count"] == 0
    assert manifest["epistemic"] == LOWER_BOUND
    assert {c["cause"] for c in manifest["causes"]} == {
        CAUSE_UNRESOLVED_INVOCATION,
        CAUSE_GATE_PENDING_EDGE,
    }


# ---------------------------------------------------------------------------
# static guards (the R20 shape)


def _planned_entries() -> dict[str, list[dict]]:
    doc = load_yaml_source(DEFAULT_VOCAB_PATH)
    by_id: dict[str, list[dict]] = defaultdict(list)
    for r in doc["local_relationships"]:
        by_id[r["id"]].append(r)
    return by_id


def test_declared_gate_pending_entries_exist_and_are_still_planned() -> None:
    """When a listed entry goes active its loader now writes the edge, the walk
    sees it, and the cause is a lie — the list must shrink."""
    entries = _planned_entries()
    problems = []
    for sid, spec in QUERY_SPECS.items():
        if spec.walk is None:
            continue
        for entry_id in spec.walk.gate_pending:
            rows = entries.get(entry_id)
            if not rows:
                problems.append(f"{sid}: gate_pending names {entry_id}, not a vocabulary entry id")
                continue
            statuses = {r.get("status") for r in rows}
            if statuses != {"planned"}:
                problems.append(
                    f"{sid}: gate_pending lists {entry_id} with status {sorted(statuses)} — "
                    "no longer planned-only, remove it"
                )
    assert not problems, "\n".join(problems)


def test_every_probe_class_is_a_known_cause_and_is_read_only() -> None:
    assert set(CAUSE_PROBES) < CAUSE_CLASSES  # gate-pending has no probe, by design
    for cls, cypher in CAUSE_PROBES.items():
        ensure_read_only(cypher)
        assert "NOT j:SchemaMeta AND NOT j:Uncertain" in cypher, cls
        assert cypher.rstrip().endswith("AS n"), cls


def test_walk_probe_classes_on_registered_specs_are_measurable() -> None:
    for sid, spec in QUERY_SPECS.items():
        if spec.walk is not None:
            assert set(spec.walk.probes) <= set(CAUSE_PROBES), sid
