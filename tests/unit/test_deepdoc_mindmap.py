"""MM3 — the mind-map state file: a slot cannot move to ``filled`` without an evidence ref.

Every value is a role placeholder (design doc front-matter): ``<folder>``,
``APP_ID-producer``, ``confluence:<page-id>``.
"""

from __future__ import annotations

from datetime import date

import pytest

from drydocs_deepdoc import mindmap as mm
from drydocs_deepdoc.mindmap import (
    SCHEMA,
    Branch,
    MindMap,
    MindMapError,
    Slot,
    new_mindmap,
)

_REF = "confluence:<page-id>"
_DAY = date(2026, 8, 20)


# ---- the default map ------------------------------------------------------------


def test_a_new_map_has_the_six_branches_with_every_record_field_open() -> None:
    m = new_mindmap("<folder>")
    assert m.schema == SCHEMA
    assert [b.name for b in m.branches] == [
        "business",
        "naming",
        "control-m",
        "lineage",
        "ownership",
        "references",
    ]
    assert all(s.is_open for b in m.branches for s in b.slots)
    # the §2 record fields are all present, and nothing is filled
    assert ("ownership", "producer_app") in m.open_slots()
    assert ("business", "business_purpose") in m.open_slots()
    assert len(m.open_slots()) == sum(len(slots) for _, slots in mm.RECORD_SLOTS)


def test_a_map_can_carry_any_layout_not_only_the_record_fields() -> None:
    m = new_mindmap("JOB0001_SAMPLE", "why did it fail?", [("triage", ("signature", "retry"))])
    assert m.open_slots() == (("triage", "signature"), ("triage", "retry"))


# ---- the one rule: filled means evidence ----------------------------------------------


@pytest.mark.parametrize("bad_ref", [None, "", "   ", "<page-id>", "wiki:<page-id>", "confluence:"])
def test_a_slot_cannot_move_to_filled_without_an_evidence_ref(bad_ref) -> None:
    m = new_mindmap("<folder>")
    with pytest.raises(MindMapError):
        m.fill("ownership", "producer_app", evidence_ref=bad_ref)  # type: ignore[arg-type]
    # and the receiver is untouched — nothing half-applied
    assert m.slot("ownership", "producer_app").is_open


def test_fill_with_evidence_flips_the_slot_and_returns_a_new_map() -> None:
    before = new_mindmap("<folder>")
    after = before.fill(
        "ownership", "producer_app", evidence_ref=_REF, filled_on=_DAY, value="APP_ID-producer"
    )
    assert before.slot("ownership", "producer_app").is_open  # immutable
    s = after.slot("ownership", "producer_app")
    assert (s.status, s.evidence_ref, s.filled_on, s.value) == (
        mm.FILLED,
        _REF,
        _DAY,
        "APP_ID-producer",
    )
    assert ("ownership", "producer_app") not in after.open_slots()
    assert len(after.open_slots()) == len(before.open_slots()) - 1


def test_filled_on_defaults_to_today() -> None:
    s = new_mindmap("<folder>").fill("naming", "flow_id", evidence_ref="log:<job>/<run>/1-3")
    assert s.slot("naming", "flow_id").filled_on == date.today()


def test_refilling_replaces_the_evidence_with_the_current_best() -> None:
    m = new_mindmap("<folder>").fill(
        "naming", "flow_id", evidence_ref="jira:<JIRA-1>", filled_on=_DAY
    )
    m2 = m.fill("naming", "flow_id", evidence_ref="commit:<sha>", filled_on=_DAY)
    assert m2.slot("naming", "flow_id").evidence_ref == "commit:<sha>"


def test_filling_an_unknown_target_is_refused_by_name() -> None:
    m = new_mindmap("<folder>")
    with pytest.raises(MindMapError, match="no slot 'nope'"):
        m.fill("naming", "nope", evidence_ref=_REF)
    with pytest.raises(MindMapError, match="no branch 'nope'"):
        m.fill("nope", "flow_id", evidence_ref=_REF)


@pytest.mark.parametrize("kind", mm.EVIDENCE_KINDS)
def test_every_declared_evidence_kind_is_accepted(kind: str) -> None:
    assert mm.validate_evidence_ref(f"{kind}:<ref>") == f"{kind}:<ref>"


# ---- the same rule, enforced on the file --------------------------------------------


def test_the_file_round_trips() -> None:
    m = new_mindmap("<folder>").fill(
        "ownership",
        "producer_app",
        evidence_ref=_REF,
        filled_on=_DAY,
        value="APP_ID-producer",
        note="the TDQ producer register",
    )
    text = mm.dumps(m)
    assert text.startswith(f"schema: {SCHEMA}\n")
    assert "filled_on: '2026-08-20'" in text or "filled_on: 2026-08-20" in text
    assert mm.loads(text) == m


def test_save_and_load_through_a_path(tmp_path) -> None:
    m = new_mindmap("<folder>")
    path = mm.save_mindmap(m, tmp_path / "maps" / "folder.yaml")
    assert path.is_file()
    assert mm.load_mindmap(path) == m


def test_a_file_that_says_filled_without_evidence_is_refused_on_load() -> None:
    """The other machine may have written the file; a map that reads as more
    complete than its evidence is refused, not repaired."""
    text = f"""schema: {SCHEMA}
seed: <folder>
root_question: why?
branches:
- name: ownership
  slots:
  - name: producer_app
    status: filled
    filled_on: 2026-08-20
"""
    with pytest.raises(MindMapError, match="evidence ref"):
        mm.loads(text)


def test_a_file_that_says_filled_without_a_date_is_refused_on_load() -> None:
    text = f"""schema: {SCHEMA}
seed: <folder>
root_question: why?
branches:
- name: ownership
  slots:
  - name: producer_app
    status: filled
    evidence_ref: {_REF}
"""
    with pytest.raises(MindMapError, match="filled_on"):
        mm.loads(text)


def test_an_open_slot_carrying_evidence_is_refused_as_inconsistent() -> None:
    with pytest.raises(MindMapError, match="open but carries evidence"):
        Slot(name="x", status=mm.OPEN, evidence_ref=_REF)


@pytest.mark.parametrize(
    ("text", "match"),
    [
        ("schema: drydocs.deepdoc.mindmap.v0\nseed: s\nroot_question: q\n", "schema"),
        (f"schema: {SCHEMA}\nseed: s\nroot_question: q\nextra: 1\n", "unknown top-level keys"),
        (f"schema: {SCHEMA}\nroot_question: q\n", "seed"),
        (f"schema: {SCHEMA}\nseed: s\n", "root question"),
        (
            f"schema: {SCHEMA}\nseed: s\nroot_question: q\nbranches:\n- name: b\n  slots:\n  - name: x\n    status: maybe\n",
            "status 'maybe'",
        ),
        (
            f"schema: {SCHEMA}\nseed: s\nroot_question: q\nbranches:\n- name: b\n  slots:\n  - name: x\n    colour: red\n",
            "unknown keys",
        ),
        (
            f"schema: {SCHEMA}\nseed: s\nroot_question: q\nbranches:\n- name: b\n  slots:\n  - name: x\n  - name: x\n",
            "repeats a slot name",
        ),
        (
            f"schema: {SCHEMA}\nseed: s\nroot_question: q\nbranches:\n- name: b\n- name: b\n",
            "branch names repeat",
        ),
        (
            f"schema: {SCHEMA}\nseed: s\nroot_question: q\nbranches:\n- name: b\n  slots:\n  - name: x\n    status: filled\n    evidence_ref: {_REF}\n    filled_on: not-a-date\n",
            "not a date",
        ),
    ],
)
def test_malformed_files_are_refused_naming_the_fault(text: str, match: str) -> None:
    with pytest.raises(MindMapError, match=match):
        mm.loads(text)


def test_value_objects_are_strict_on_construction_too() -> None:
    with pytest.raises(MindMapError):
        Slot(name="")
    with pytest.raises(MindMapError):
        Branch(name="")
    with pytest.raises(MindMapError):
        MindMap(seed="s", root_question="q", schema="other")
    ok = MindMap(seed="s", root_question="q", branches=(Branch("b", (Slot("x"),)),))
    assert ok.open_slots() == (("b", "x"),)
