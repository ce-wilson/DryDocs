"""The fix-tracking loader (G90) — gate remediation-fix-tracking, SIGNED 2026-08-12.

Two halves, tested at the seam the gate drew. The READER
(``drydocs_core.fix_tracking``) is shared with the emitting component and owns
every refusal that can be made without a graph; the LOADER
(``drydocs.loaders.fix_tracking``) owns the write and the one refusal that needs
a graph — a target that is not there.

The client here RECORDS rather than connects: every assertion below is about what
Cypher the loader sends and with which binds, which is exactly the contract a
live run would exercise and the part a live run cannot show you when it passes.
Two behaviours are pinned by inspecting the recorded calls specifically because
they are silent when wrong:

* an unresolved target refuses BEFORE the :JobRun opens — the failure mode being
  guarded is not "it raises" but "it raises having already written";
* reject mode REMOVEs under a fix-id fence — the failure mode is a stale
  rejection quietly stripping a newer fix's marks.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from drydocs.loaders.fix_tracking import (
    APPLY,
    REJECT,
    FixTrackingLoader,
    UnresolvedFixTargetError,
    change_set_rows,
)
from drydocs_core.fix_tracking import (
    FIX_STATUS_ENUM,
    FIX_TRACKING_PROPERTIES,
    FIX_TRACKING_SCHEMA,
    FixTrackingError,
    parse_change_set,
)

# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #

JOB_TARGET = {
    "labels": ["ControlMJob", "Activity"],
    "node_key": {"folder_id": "F-1", "job_id": "J-1"},
    "display_name": "DAILY_EXTRACT",
    "proposed_properties": {
        "remediation_fix_id": "FIX-77",
        "remediation_status": "applied",
        "remediation_status_date": "2026-09-08",
    },
}

FOLDER_TARGET = {
    "labels": ["ControlMFolder", "Collection"],
    "node_key": {"folder_id": "F-1"},
    "display_name": "PAYMENTS_DAILY",
    "proposed_properties": {
        "remediation_fix_id": "FIX-77",
        "remediation_status": "applied",
        "remediation_status_date": "2026-09-08",
    },
}


def _write(tmp_path: Path, **overrides: Any) -> Path:
    payload = {
        "schema": FIX_TRACKING_SCHEMA,
        "fix_id": "FIX-77",
        "gate": {"status": "RATIFIED"},
        "approvals": ["gate-remediation-fix-tracking"],
        "targets": [dict(FOLDER_TARGET), dict(JOB_TARGET)],
    }
    payload.update(overrides)
    path = tmp_path / "fix-tracking.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8", newline="\n")
    return path


class _RecordingClient:
    """Records every statement + bind set; answers the preflight read.

    ``resolves`` names the (kind, folder_id, job_id) triples the graph is
    pretending to hold — anything else comes back ``found: False``, which is how
    a missing target is simulated without a database.
    """

    def __init__(self, resolves: set[tuple] | None = None, *, all_found: bool = True) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.scripts: list[tuple[str, dict]] = []
        self._resolves = resolves or set()
        self._all_found = all_found

    def run(self, cypher: str, params: dict | None = None, **kwargs: Any) -> list[dict]:
        bind = {**(params or {}), **kwargs}
        self.calls.append((cypher, bind))
        if "n IS NOT NULL" in cypher:  # the preflight read
            rows = []
            for row in bind["batch"]:
                identity = (row["kind"], row["folder_id"], row.get("job_id"))
                rows.append(
                    {
                        "kind": row["kind"],
                        "label": row["label"],
                        "folder_id": row["folder_id"],
                        "job_id": row.get("job_id"),
                        "display_name": row["display_name"],
                        "found": self._all_found or identity in self._resolves,
                    }
                )
            return rows
        return []

    def run_script(self, script: str, params: dict | None = None) -> None:
        self.scripts.append((script, dict(params or {})))

    # -- helpers the assertions read through ---------------------------------

    def statements(self) -> list[str]:
        return [cypher for cypher, _ in self.calls] + [script for script, _ in self.scripts]

    def opened_a_run(self) -> bool:
        return any("JobRun" in stmt and "MERGE" in stmt for stmt in self.statements())

    def batch_call(self) -> tuple[str, dict]:
        """The one call carrying the loader's own template."""
        matches = [
            (cypher, bind)
            for cypher, bind in self.calls
            if "UNWIND $batch AS row" in cypher and "$mode" in cypher
        ]
        assert len(matches) == 1, f"expected one template flush, got {len(matches)}"
        return matches[0]


# --------------------------------------------------------------------------- #
# the reader — every refusal that needs no graph (core, shared with the emitter)
# --------------------------------------------------------------------------- #


def test_parses_both_target_kinds_into_one_flat_batch(tmp_path: Path) -> None:
    """One batch, one row shape — folder rows carry job_id None so the Cypher
    can UNWIND both kinds together and branch on `kind`."""
    rows = parse_change_set(_write(tmp_path))
    assert [r["kind"] for r in rows] == ["folder", "job"]
    folder, job = rows
    assert folder["folder_id"] == "F-1" and folder["job_id"] is None
    assert job["folder_id"] == "F-1" and job["job_id"] == "J-1"
    for row in rows:
        assert all(name in row for name in FIX_TRACKING_PROPERTIES)
        assert row["remediation_fix_id"] == "FIX-77"


def test_a_foreign_schema_is_refused_by_name(tmp_path: Path) -> None:
    """A v2 artifact read by a v1 loader would apply rulings nobody made."""
    path = _write(tmp_path, schema="drydocs.remediation.fix-tracking.v2")
    with pytest.raises(FixTrackingError) as exc:
        parse_change_set(path)
    assert "v2" in str(exc.value) and FIX_TRACKING_SCHEMA in str(exc.value)


def test_a_status_outside_the_ruled_enum_is_refused(tmp_path: Path) -> None:
    """Refused at emission already; refused again at intake because intake is
    where a hand-edited artifact arrives."""
    target = dict(JOB_TARGET)
    target["proposed_properties"] = {
        **JOB_TARGET["proposed_properties"],
        "remediation_status": "rejected",
    }
    path = _write(tmp_path, targets=[target])
    with pytest.raises(FixTrackingError) as exc:
        parse_change_set(path)
    message = str(exc.value)
    assert "rejected" in message
    assert " | ".join(FIX_STATUS_ENUM) in message
    # and it says WHY 'rejected' in particular is not a status
    assert "REMOVES" in message


def test_a_partial_node_key_is_refused(tmp_path: Path) -> None:
    """§C1 MATCHes on the NODE KEY — folder_id alone would match every job in
    the folder, which is a silent over-application, not a near miss."""
    target = dict(JOB_TARGET)
    target["node_key"] = {"folder_id": "F-1"}
    path = _write(tmp_path, targets=[target])
    with pytest.raises(FixTrackingError, match="NODE KEY"):
        parse_change_set(path)


def test_an_unruled_target_label_is_refused(tmp_path: Path) -> None:
    target = dict(JOB_TARGET)
    target["labels"] = ["BusinessApplication"]
    path = _write(tmp_path, targets=[target])
    with pytest.raises(FixTrackingError, match="no fix-tracking target"):
        parse_change_set(path)


def test_a_target_named_twice_is_refused(tmp_path: Path) -> None:
    """Two rows for one node race to set the same three properties, and which
    one lands is batch order."""
    path = _write(tmp_path, targets=[dict(JOB_TARGET), dict(JOB_TARGET)])
    with pytest.raises(FixTrackingError, match="twice"):
        parse_change_set(path)


def test_a_target_whose_fix_id_disagrees_is_refused(tmp_path: Path) -> None:
    """One change-set carries one fix — §B3 puts ONE last-transition date on a
    node, so two fix ids in one file have no consistent answer."""
    target = dict(JOB_TARGET)
    target["proposed_properties"] = {
        **JOB_TARGET["proposed_properties"],
        "remediation_fix_id": "FIX-99",
    }
    path = _write(tmp_path, targets=[target])
    with pytest.raises(FixTrackingError, match="disagrees"):
        parse_change_set(path)


def test_an_envelope_property_smuggled_in_is_refused(tmp_path: Path) -> None:
    """§A1's fence, enforced: the envelope names stay source-system authorship
    and this axis never reuses them."""
    target = dict(JOB_TARGET)
    target["proposed_properties"] = {
        **JOB_TARGET["proposed_properties"],
        "source_updated_by": "someone",
    }
    path = _write(tmp_path, targets=[target])
    with pytest.raises(FixTrackingError, match="unruled source_updated_by"):
        parse_change_set(path)


# --------------------------------------------------------------------------- #
# the loader — the write, and the one refusal that needs a graph
# --------------------------------------------------------------------------- #


def test_apply_sets_the_three_ruled_properties_and_binds_the_mode(tmp_path: Path) -> None:
    rows = change_set_rows(_write(tmp_path))
    client = _RecordingClient()
    FixTrackingLoader(client, rows, mode=APPLY, run_log=False).load()

    cypher, bind = client.batch_call()
    assert bind["mode"] == APPLY
    assert len(bind["batch"]) == 2
    for name in FIX_TRACKING_PROPERTIES:
        assert f"n.{name}" in cypher


def test_the_template_matches_and_never_merges_a_target(tmp_path: Path) -> None:
    """§C1: a fix target that does not exist is an error, not a node to invent.

    Reads the template's CODE, not the prose around it (J66): the comment block
    explaining the rule contains the word MERGE, so a bare substring test over
    the raw file would pass while a MERGE on :ControlMJob sat two lines below.

    The stripper is the Cypher one, IMPORTED rather than re-written.
    ``tests.source_scan.code_only`` is Python's tokenizer and cannot read this
    grammar; ``test_vocabulary_endpoints._code_only`` is the named exemption
    that can (``test_source_scan.py`` pins it). A second copy here would be the
    duplication J66 clause (c) fences, one directory deeper.
    """
    from tests.unit.test_vocabulary_endpoints import _code_only as cypher_code_only

    template = FixTrackingLoader.cypher_path
    assert template is not None
    code = cypher_code_only(template.read_text(encoding="utf-8"))
    for var, label in (("j", "ControlMJob"), ("f", "ControlMFolder")):
        assert f"OPTIONAL MATCH ({var}:{label}" in code
        assert f"MERGE ({var}:{label}" not in code
        assert f"MERGE (:{label}" not in code
    # the only MERGE the template is allowed is the :JobRun provenance edge
    for line in code.splitlines():
        if "MERGE" in line:
            assert "WAS_GENERATED_BY" in line, f"unexpected MERGE: {line.strip()}"


def test_the_template_writes_only_the_three_ruled_properties() -> None:
    """§B1 ruled three names. A fourth remediation_* property would be an unruled
    name in a ruled namespace, and §D1 gives property_terms entries to the ruled
    names — one without an entry is the drift that section exists to prevent.

    "Which run marked this fix, and when" is the :JobRun edge's job, which is why
    the obvious remediation_last_run_id / _loaded_at pair does not belong here.
    """
    from tests.unit.test_vocabulary_endpoints import _code_only as cypher_code_only

    template = FixTrackingLoader.cypher_path
    assert template is not None
    code = cypher_code_only(template.read_text(encoding="utf-8"))
    written = set(re.findall(r"\bn\.(remediation_\w+)", code))
    assert written == set(FIX_TRACKING_PROPERTIES), (
        f"the template touches {sorted(written)}; the gate ruled "
        f"{sorted(FIX_TRACKING_PROPERTIES)} (§B1)"
    )


def test_reject_removes_the_properties_under_a_fix_id_fence(tmp_path: Path) -> None:
    """A stale rejection must not strip a NEWER fix's marks — the one way this
    loader could destroy a fact it did not write."""
    rows = change_set_rows(_write(tmp_path))
    client = _RecordingClient()
    FixTrackingLoader(client, rows, mode=REJECT, run_log=False).load()

    cypher, bind = client.batch_call()
    assert bind["mode"] == REJECT
    reject_branch = cypher.split("$mode = 'reject'", 1)[1]
    assert "n.remediation_fix_id = row.remediation_fix_id" in reject_branch
    assert "REMOVE" in reject_branch
    for name in FIX_TRACKING_PROPERTIES:
        assert name in reject_branch


def test_an_unresolved_target_refuses_the_whole_change_set(tmp_path: Path) -> None:
    """All-or-nothing. The resolvable half is NOT applied — a partially marked
    fix is worse than a refused one, because nothing says which half landed."""
    rows = change_set_rows(_write(tmp_path))
    client = _RecordingClient(resolves={("folder", "F-1", None)}, all_found=False)
    with pytest.raises(UnresolvedFixTargetError) as exc:
        FixTrackingLoader(client, rows, mode=APPLY, run_log=False).load()

    message = str(exc.value)
    assert "1 of 2" in message
    assert "DAILY_EXTRACT" in message  # named, so the operator can act on it
    assert "J-1" in message
    assert "PAYMENTS_DAILY" not in message  # the resolvable one is not blamed


def test_the_preflight_probes_the_values_the_write_will_send(tmp_path: Path) -> None:
    """YAML types are not the graph's.

    An unquoted ``folder_id: 123`` parses as an int; ``FixTrackingRow`` coerces
    it to ``"123"`` before the write sees it. If the preflight probed the raw
    value it would compare an int against a string property, call an existing
    target missing, and refuse a change-set that was fine. Both batches must
    carry the same values — which is what makes "the preflight checked it" mean
    "the write will find it".
    """
    target = dict(JOB_TARGET)
    target["node_key"] = {"folder_id": 123, "job_id": 456}
    rows = change_set_rows(_write(tmp_path, targets=[target]))

    client = _RecordingClient()
    FixTrackingLoader(client, rows, mode=APPLY, run_log=False).load()

    probe = next(bind for cypher, bind in client.calls if "n IS NOT NULL" in cypher)
    _, written = client.batch_call()
    assert probe["batch"] == written["batch"]
    assert written["batch"][0]["folder_id"] == "123"
    assert written["batch"][0]["job_id"] == "456"


def test_the_refusal_happens_before_the_run_opens(tmp_path: Path) -> None:
    """The failure mode guarded here is not 'it raises' — it is 'it raises
    having already written'. A refused load leaves no :JobRun behind."""
    rows = change_set_rows(_write(tmp_path))
    client = _RecordingClient(all_found=False)
    with pytest.raises(UnresolvedFixTargetError):
        FixTrackingLoader(client, rows, mode=APPLY, run_log=False).load()

    assert not client.opened_a_run(), "a refused change-set must not open a :JobRun"
    assert all("$mode" not in stmt for stmt in client.statements())


def test_an_unknown_mode_is_refused_at_construction(tmp_path: Path) -> None:
    rows = change_set_rows(_write(tmp_path))
    with pytest.raises(ValueError, match="unknown fix-tracking mode"):
        FixTrackingLoader(_RecordingClient(), rows, mode="rejected", run_log=False)


def test_the_loader_is_sourceless_by_declaration_with_a_written_reason() -> None:
    """N3: the input is an artifact this system emits, not a registry feed —
    so the exemption is named, never silent."""
    from drydocs import cli_shared

    assert FixTrackingLoader.source_id is None
    reason = cli_shared.SOURCELESS_LOADERS[FixTrackingLoader]
    assert "change-set" in reason and len(reason.split()) >= 10


def test_the_command_is_ad_hoc_by_ruling_not_a_sequence_member() -> None:
    """§C2 (a pass inside an existing Control-M loader) was declined so a fix is
    markable the hour its package ships. A refresh cadence would re-create the
    coupling the gate refused."""
    from drydocs import cli_shared

    assert cli_shared.COMMAND_LOADERS["load-fix-tracking"] == (FixTrackingLoader,)
    assert "load-fix-tracking" in cli_shared.AD_HOC_COMMANDS


def test_the_emitter_and_the_loader_share_one_enum_object() -> None:
    """§E1's drift guard, structurally: there is no second copy to drift.

    Identity, not equality — two equal tuples is exactly the state this build
    replaced, and it is the state that goes stale silently.
    """
    from drydocs_remediation import changes

    assert changes.FIX_STATUS_ENUM is FIX_STATUS_ENUM
    assert changes.FIX_TRACKING_SCHEMA is FIX_TRACKING_SCHEMA


def test_a_change_set_the_real_emitter_wrote_loads_without_a_hand_written_fixture(
    tmp_path: Path,
) -> None:
    """The seam the gate drew, closed end to end.

    Every other test here feeds the reader a fixture THIS FILE wrote, which
    proves the reader reads what the test author believes the emitter emits.
    That is the assumption worth checking directly: emit with
    ``fix_tracking_changeset``, read with ``parse_change_set``, load. If the two
    halves ever disagree about the artifact shape — a renamed key, a moved
    node_key — this fails and the hand-written fixtures above do not.
    """
    from drydocs_remediation.changes import (
        FixAnchor,
        FixTrackingChangeset,
        fix_tracking_changeset,
    )

    changeset = FixTrackingChangeset(
        fix_id="FIX-77",
        status="verified",
        date="2026-09-08",
        anchors=[
            FixAnchor(
                labels=("ControlMFolder", "Collection"),
                node_key={"folder_id": "F-1"},
                display_name="PAYMENTS_DAILY",
            ),
            FixAnchor(
                labels=("ControlMJob", "Activity"),
                node_key={"folder_id": "F-1", "job_id": "J-1"},
                display_name="DAILY_EXTRACT",
            ),
        ],
        approvals=["gate-remediation-fix-tracking"],
    )
    emitted = fix_tracking_changeset(changeset, tmp_path / "emitted.yaml")

    rows = change_set_rows(emitted)
    assert [r["kind"] for r in rows] == ["folder", "job"]
    assert {r["remediation_status"] for r in rows} == {"verified"}

    client = _RecordingClient()
    summary = FixTrackingLoader(client, rows, mode=APPLY, run_log=False).load()
    assert summary.rows_processed == 2
    assert summary.rows_rejected == 0
    _, bind = client.batch_call()
    assert bind["mode"] == APPLY


def test_the_ruled_property_names_are_the_ones_the_gate_named() -> None:
    """The names are frozen by §B1; a rename here is a gate change, not a
    refactor. Spelled out rather than derived so the test states the ruling."""
    assert FIX_TRACKING_PROPERTIES == (
        "remediation_fix_id",
        "remediation_status",
        "remediation_status_date",
    )
    assert FIX_STATUS_ENUM == ("proposed", "in_progress", "applied", "verified")
    assert "rejected" not in FIX_STATUS_ENUM


def test_the_property_terms_carry_the_three_dd_local_entries() -> None:
    """§D1 lands with the build: dd: local terms with prose definitions, the
    standard-term binding revisited at RDF export. dct: is the envelope's."""
    from drydocs_core.ontology.schema_graph import DEFAULT_VOCAB_PATH
    from drydocs_core.yaml_fragments import load_yaml_source

    registry = load_yaml_source(DEFAULT_VOCAB_PATH)
    terms = {e["property"]: e for e in registry["property_terms"]}
    for name in FIX_TRACKING_PROPERTIES:
        assert name in terms, f"{name} has no property_terms entry (gate §D1)"
        entry = terms[name]
        assert entry["term"].startswith("dd:"), "§D1 ruled dd: local terms"
        assert entry["decided_by"] == "remediation-fix-tracking"
        assert len(entry["note"].split()) >= 10, "§D1 asked for prose definitions"
