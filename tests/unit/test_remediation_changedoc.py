"""changedoc.py — the packaging-time diff excerpt renders what was proven.

The excerpt is keyed by the self-check's changed_line_numbers, so it IS the
diff (every changed line proven inside an approved edit span), not a sample.
"""

from __future__ import annotations

from drydocs_remediation.changedoc import ChangeDoc, render_change_doc
from drydocs_remediation.changes import ApprovedChange, FixAnchor, compile_changes
from drydocs_remediation.xml_io import Locator, load_document, render, self_check
from tests.unit.fixtures_controlm_xml import F3_RESIDUE


def _run_fix():
    doc = load_document(F3_RESIDUE)
    changes = [
        ApprovedChange(
            approval_id="gate-x-1",
            kind="rename-variable",
            locator=Locator(folder="PRXYZ3C"),
            detail="SCRIPT_PATH",
            value="LAUNCHER_SCRIPT_PATH",
            evidence="ratified canonical name",
        )
    ]
    script, effects = compile_changes(doc, changes)
    updated = render(doc, script.compile())
    report = self_check(doc, script, updated)
    return doc, changes, effects, updated, report


def test_change_doc_carries_anchors_excerpts_and_approvals() -> None:
    doc, changes, effects, updated, report = _run_fix()
    body = render_change_doc(
        ChangeDoc(
            fix_id="FIX-2026-001",
            original_name="PRXYZ3C.xml",
            updated_name="PRXYZ3C.updated.xml",
            issue="launcher variable off-standard; ratified rename applies",
            changes=changes,
            effects=effects,
            report=report,
            anchors=[
                FixAnchor(
                    labels=("ControlMJob", "Activity"),
                    node_key={"folder_id": 4711, "job_id": 12},
                    display_name="PRXYZ3C001",
                    relationships=("CONTAINS_JOB",),
                )
            ],
        ),
        original=F3_RESIDUE,
        updated=updated,
    )
    assert "# Change doc — FIX-2026-001" in body
    assert "`folder_id=4711, job_id=12`" in body, "anchors cite the NODE KEY, not names"
    assert "gate-x-1" in body
    assert "Verdict: PASS" in body
    # one excerpt block per changed line, and each block shows before+after
    assert body.count("```") == 2 * len(report.changed_line_numbers)
    assert "- " in body and "+ " in body
    assert "%%LAUNCHER_SCRIPT_PATH" in body


def test_change_doc_is_deterministic() -> None:
    doc, changes, effects, updated, report = _run_fix()
    cd = ChangeDoc(
        fix_id="FIX-2026-001",
        original_name="a.xml",
        updated_name="a.updated.xml",
        issue="x",
        changes=changes,
        effects=effects,
        report=report,
    )
    assert render_change_doc(cd, F3_RESIDUE, updated) == render_change_doc(cd, F3_RESIDUE, updated)


def test_failed_self_check_is_shouted_not_hidden() -> None:
    doc, changes, effects, updated, report = _run_fix()
    report.violations.append("synthetic violation")
    body = render_change_doc(
        ChangeDoc(
            fix_id="FIX-2026-001",
            original_name="a.xml",
            updated_name="a.updated.xml",
            issue="x",
            changes=changes,
            effects=effects,
            report=report,
        ),
        original=F3_RESIDUE,
        updated=updated,
    )
    assert "FAILED — this package must not ship" in body
