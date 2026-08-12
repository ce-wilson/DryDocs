"""changes.py: approved-change compilation, graph anchors, fix-tracking artifact.

The SoD proof lives here too: fix tracking reaches the graph as an ARTIFACT a
write-authorized loader applies — this component's own no-graph-write guards
(the AST scan and the corroborate regex) stay green with zero test changes,
which was the point of the 2026-08-12 ruling.
"""

from __future__ import annotations

import pytest
import yaml

from drydocs_remediation.changes import (
    ApprovedChange,
    FixAnchor,
    FixTrackingChangeset,
    UnanchoredFixError,
    compile_changes,
    fix_tracking_changeset,
    graph_anchors,
)
from drydocs_remediation.corroborate import GraphWriteAttemptError, ReadOnlyGraph
from drydocs_remediation.xml_io import Locator, LocatorNotFound, load_document, write
from tests.unit.fixtures_controlm_xml import F3_RESIDUE


class _FakeClient:
    """Stands in for Neo4jClient behind ReadOnlyGraph; canned rows by match."""

    def __init__(self, rows_by_marker: dict[str, list[dict]]) -> None:
        self._rows = rows_by_marker
        self.queries: list[str] = []

    def run(self, query: str, params: dict | None = None) -> list[dict]:
        self.queries.append(query)
        for marker, rows in self._rows.items():
            if marker in query:
                return rows
        return []


def _graph(job_rows: list[dict] | None = None, folder_rows: list[dict] | None = None):
    return ReadOnlyGraph(
        _FakeClient(
            {
                "CONTAINS_JOB": job_rows if job_rows is not None else [],
                "RETURN f.folder_id AS folder_id, f.sched_table": (
                    folder_rows if folder_rows is not None else []
                ),
            }
        )
    )


# --------------------------------------------------------------------------- #
# compile_changes
# --------------------------------------------------------------------------- #


def test_compile_changes_applies_a_full_approved_set(tmp_path) -> None:
    doc = load_document(F3_RESIDUE)
    changes = [
        ApprovedChange(
            approval_id="gate-x-1",
            kind="rename-variable",
            locator=Locator(folder="PRXYZ3C"),
            detail="SCRIPT_PATH",
            value="LAUNCHER_SCRIPT_PATH",
            evidence="ratified canonical name (cmdline-nfr standard)",
        ),
        ApprovedChange(
            approval_id="gate-x-2",
            kind="add-attribute",
            locator=Locator(folder="PRXYZ3C", subfolder_path="NESTED", job="PRXYZ3C101"),
            detail="DESCRIPTION",
            value="cleanup step | OWNER:synth",
            evidence="description-metadata enrichment",
        ),
    ]
    script, effects = compile_changes(doc, changes)
    assert len(effects) >= 10, "the rename enumerates every site + the set"
    target = tmp_path / "updated.xml"
    report = write(doc, script, target)
    assert report.ok
    out = target.read_bytes()
    assert b"%%LAUNCHER_SCRIPT_PATH/run.sh" in out
    assert b"OWNER:synth" in out


def test_conflicting_approvals_on_one_attribute_are_refused_not_merged(tmp_path) -> None:
    """A rename sweeps DESCRIPTION (it carries the token); a second approval
    setting the SAME attribute is a change-set authoring conflict — refused at
    compile, never silently merged into whichever edit sorts last."""
    from drydocs_remediation.xml_io import XmlIoError

    doc = load_document(F3_RESIDUE)
    script, _ = compile_changes(
        doc,
        [
            ApprovedChange(
                approval_id="gate-x-1",
                kind="rename-variable",
                locator=Locator(folder="PRXYZ3C"),
                detail="SCRIPT_PATH",
                value="LAUNCHER_SCRIPT_PATH",
            ),
            ApprovedChange(
                approval_id="gate-x-2",
                kind="set-attribute",
                locator=Locator(folder="PRXYZ3C", job="PRXYZ3C001"),
                detail="DESCRIPTION",
                value="handwritten replacement",
            ),
        ],
    )
    with pytest.raises(XmlIoError, match="overlapping"):
        write(doc, script, tmp_path / "updated.xml")


def test_compile_changes_rename_is_the_sweep_not_a_field_list(tmp_path) -> None:
    """rename-variable has exactly one compilation target: the whole-scope
    reference sweep. There is no code path back to the field-list shape."""
    doc = load_document(F3_RESIDUE)
    script, _ = compile_changes(
        doc,
        [
            ApprovedChange(
                approval_id="gate-x-1",
                kind="rename-variable",
                locator=Locator(folder="PRXYZ3C"),
                detail="SCRIPT_PATH",
                value="LAUNCHER_SCRIPT_PATH",
            )
        ],
    )
    target = tmp_path / "updated.xml"
    report = write(doc, script, target)
    assert report.ok, "sweep passes the post-conditions on every surface"
    assert b"%%SCRIPT_PATH" not in target.read_bytes().replace(
        b"%%LAUNCHER_SCRIPT_PATH", b""
    )


def test_stale_approval_raises_instead_of_best_effort() -> None:
    doc = load_document(F3_RESIDUE)
    with pytest.raises(LocatorNotFound):
        compile_changes(
            doc,
            [
                ApprovedChange(
                    approval_id="gate-x-9",
                    kind="set-attribute",
                    locator=Locator(folder="PRXYZ3C", job="GHOST"),
                    detail="CMDLINE",
                    value="x.sh",
                )
            ],
        )


def test_approval_id_is_unbuildable_without() -> None:
    with pytest.raises(TypeError):
        ApprovedChange(  # type: ignore[call-arg]
            kind="set-attribute", locator=Locator(folder="F"), detail="CMDLINE"
        )


def test_unknown_kind_is_refused() -> None:
    doc = load_document(F3_RESIDUE)
    with pytest.raises(ValueError, match="unknown change kind"):
        compile_changes(
            doc,
            [
                ApprovedChange(
                    approval_id="gate-x-1",
                    kind="mutate-freely",
                    locator=Locator(folder="PRXYZ3C"),
                    detail="X",
                )
            ],
        )


# --------------------------------------------------------------------------- #
# graph anchors
# --------------------------------------------------------------------------- #


def test_anchors_carry_the_node_key_not_names() -> None:
    graph = _graph(
        job_rows=[{"folder_id": 4711, "job_id": 12, "job_name": "PRXYZ3C001"}],
        folder_rows=[{"folder_id": 4711, "sched_table": "PRXYZ3C"}],
    )
    anchors = graph_anchors(graph, "PRXYZ3C", ["PRXYZ3C001"])
    folder, job = anchors
    assert folder.labels == ("ControlMFolder", "Collection")
    assert folder.node_key == {"folder_id": 4711}
    assert job.labels == ("ControlMJob", "Activity")
    assert job.node_key == {"folder_id": 4711, "job_id": 12}
    assert "CONTAINS_JOB" in folder.relationships


def test_unanchored_fix_refuses_invented_identity() -> None:
    graph = _graph(job_rows=[], folder_rows=[])
    with pytest.raises(UnanchoredFixError, match="canonical keys"):
        graph_anchors(graph, "PRXYZ3C", [])


def test_anchor_queries_pass_the_read_only_guard() -> None:
    """The anchor queries run through ReadOnlyGraph — if one ever grew a write
    clause the corroborate regex would refuse it. Prove the guard sees them."""
    graph = _graph(folder_rows=[{"folder_id": 1, "sched_table": "F"}])
    graph_anchors(graph, "F", [])
    with pytest.raises(GraphWriteAttemptError):
        graph.fetch("MATCH (n) SET n.remediation_status = 'x' RETURN n")


# --------------------------------------------------------------------------- #
# fix-tracking change-set
# --------------------------------------------------------------------------- #


def test_fix_tracking_changeset_is_gate_bound_and_key_addressed(tmp_path) -> None:
    changeset = FixTrackingChangeset(
        fix_id="FIX-2026-001",
        status="proposed",
        date="2026-08-12",
        anchors=[
            FixAnchor(
                labels=("ControlMJob", "Activity"),
                node_key={"folder_id": 4711, "job_id": 12},
                display_name="PRXYZ3C001",
            )
        ],
        approvals=["gate-x-1", "gate-x-2"],
    )
    path = fix_tracking_changeset(changeset, tmp_path / "fix-tracking.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["schema"] == "drydocs.remediation.fix-tracking.v1"
    assert data["gate"]["status"] == "GATE-BOUND"
    assert "MUST NOT be reused" in data["gate"]["note"]
    target = data["targets"][0]
    assert target["node_key"] == {"folder_id": 4711, "job_id": 12}
    props = target["proposed_properties"]
    assert props["remediation_fix_id"] == "FIX-2026-001"
    assert props["remediation_status"] == "proposed"
    assert props["remediation_status_date"] == "2026-08-12"
    # the artifact must never smuggle the envelope vocabulary
    assert not any(k.startswith("source_") for k in props)


def test_no_graph_write_guards_still_green_after_this_module() -> None:
    """The SoD proof: this module added graph-adjacent behavior and the two
    structural guards needed ZERO changes. Import them to pin the claim."""
    import tests.unit.test_remediation_no_graph_write as guard  # noqa: F401

    from drydocs_remediation import changes

    assert not hasattr(changes, "write_transaction")
    assert "execute_write" not in open(changes.__file__, encoding="utf-8").read()
