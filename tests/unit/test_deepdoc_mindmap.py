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


# ---- MM12: the acronym shelf -------------------------------------------------

_DOC = (
    "The load failed overnight. SNOW (ServiceNow) is where the incident lives, "
    "and MFT moved the file."
)
_MM12_REF = "confluence:page-4021"


def _harvested() -> tuple[mm.AcronymCandidate, ...]:
    return mm.harvest_acronyms(_DOC, evidence_ref=_MM12_REF)


def test_harvest_reads_the_shared_extractor_and_carries_the_sentence() -> None:
    """One reading, shared with the connectors and the novelty score (MM3) —
    never a second regex here. The sentence is what makes a candidate judgeable."""
    got = {c.value: c for c in _harvested()}
    assert set(got) == {"SNOW", "MFT"}
    assert got["SNOW"].evidence.startswith("SNOW (ServiceNow) is where")
    assert got["SNOW"].gloss == "ServiceNow"
    assert got["MFT"].gloss is None
    assert all(c.evidence_ref == _MM12_REF for c in got.values())


def test_every_harvested_candidate_is_marked_synthesized() -> None:
    """MM12 clause (d), and the assertion the clause asks for by name. A
    corpus-derived acronym must never be indistinguishable from one an SME
    supplied, and the harvester is INCAPABLE of writing any other trust."""
    assert all(c.trust == mm.HARVESTED_TRUST for c in _harvested())
    assert all(c.is_harvested for c in _harvested())
    assert mm.HARVESTED_TRUST == "SYNTHESIZED"


def test_the_trust_vocabulary_is_the_one_the_doc_rows_already_declare() -> None:
    """The tuple in mindmap.py restates a pydantic Literal rather than importing
    it. This is what stops the two drifting — if the Literal grows a level, the
    restatement fails here rather than quietly disagreeing."""
    from typing import get_args

    from drydocs_core.models.docs import BmcDocChunkRow

    assert mm.TRUST_LEVELS == get_args(BmcDocChunkRow.model_fields["provenance"].annotation)


def test_a_candidate_without_its_sentence_is_refused() -> None:
    with pytest.raises(mm.MindMapError, match="evidence"):
        mm.AcronymCandidate(value="SNOW", evidence="   ", evidence_ref=_MM12_REF)


def test_a_candidate_without_a_breadcrumb_is_refused() -> None:
    """The module's one rule, reached a step earlier: a fact with no breadcrumb
    is not written, and neither is a candidate."""
    with pytest.raises(mm.MindMapError):
        mm.AcronymCandidate(value="SNOW", evidence="SNOW is ServiceNow.", evidence_ref="page-4021")
    with pytest.raises(mm.MindMapError):
        mm.harvest_acronyms(_DOC, evidence_ref="not-a-kind:x")


def test_an_unknown_trust_level_is_refused() -> None:
    with pytest.raises(mm.MindMapError, match="trust"):
        mm.AcronymCandidate(
            value="SNOW", evidence="SNOW is ServiceNow.", evidence_ref=_MM12_REF, trust="TRUSTED"
        )


def test_an_ambiguous_acronym_keeps_both_readings_on_the_shelf() -> None:
    """The acceptance's named case, at the state file rather than the extractor.
    De-duplication is on (value, ref, sentence) precisely so the two readings of
    SNOW survive — collapsing on the value would keep one and destroy the finding.
    """
    incident = mm.harvest_acronyms("SNOW (ServiceNow) holds the ticket.", evidence_ref="jira:INC-1")
    warehouse = mm.harvest_acronyms(
        "SNOW (Snowflake) holds the table.", evidence_ref="confluence:wh-1"
    )
    shelf = mm.new_mindmap("seed-folder").with_acronyms(incident + warehouse)
    snow = [c for c in shelf.acronyms if c.value == "SNOW"]
    assert len(snow) == 2
    assert {c.gloss for c in snow} == {"ServiceNow", "Snowflake"}
    assert len({c.evidence for c in snow}) == 2


def test_re_harvesting_the_same_sentence_adds_nothing() -> None:
    """The other half of the same rule: a repeat of one reading is noise, and a
    second reading is the signal."""
    once = mm.new_mindmap("seed-folder").with_acronyms(_harvested())
    twice = once.with_acronyms(_harvested())
    assert twice.acronyms == once.acronyms
    assert twice is once  # nothing added, nothing rebuilt


def test_the_shelf_round_trips_through_the_file() -> None:
    saved = mm.new_mindmap("seed-folder").with_acronyms(_harvested())
    assert mm.loads(mm.dumps(saved)) == saved


def test_a_map_with_no_candidates_writes_no_acronyms_key() -> None:
    """Additive on v1: every file that exists today round-trips unchanged."""
    doc = mm.to_document(mm.new_mindmap("seed-folder"))
    assert "acronyms" not in doc
    assert mm.loads(mm.dumps(mm.new_mindmap("seed-folder"))).acronyms == ()


def test_a_file_written_before_this_change_still_loads() -> None:
    """The compatibility direction that matters — the state file is machine-local
    and an earlier session's map must not need a migration to be read."""
    older = (
        f"schema: {mm.SCHEMA}\n"
        "seed: seed-folder\n"
        "root_question: what is this flow?\n"
        "branches:\n"
        "- name: ownership\n"
        "  slots:\n"
        "  - name: owner_app\n"
        "    status: open\n"
    )
    loaded = mm.loads(older)
    assert loaded.acronyms == ()
    assert loaded.open_slots() == (("ownership", "owner_app"),)


def test_an_acronym_row_with_an_unknown_key_is_refused_not_repaired() -> None:
    text = mm.dumps(mm.new_mindmap("seed-folder").with_acronyms(_harvested()))
    with pytest.raises(mm.MindMapError, match="unknown keys"):
        mm.loads(text.replace("  trust:", "  confidence: high\n  trust:", 1))


def test_the_shelf_writes_no_graph_and_adds_no_uncertain_writer() -> None:
    """MM12 clause (e), as a check rather than a promise. This module reaches no
    driver and no graph client, and the allowlist that governs :Uncertain writes
    is untouched — drydocs_deepdoc was already on it."""
    from tests.source_scan import absent, code_only, imported_modules, source_text, without_prose
    from tests.unit.test_uncertain_boundary import UNCERTAIN_WRITERS

    assert UNCERTAIN_WRITERS == ("drydocs_deepdoc", "agents/common/agent_run_writer.py")
    sources = {"mindmap.py": source_text(mm.__file__)}
    assert not [m for m in imported_modules(sources["mindmap.py"]) if m.split(".")[0] == "neo4j"]
    # Two scans, two STRIPPERS, and the split is the point (CORE2). A driver
    # handle is CODE, so code_only is right for it. A Cypher clause is only ever
    # a string LITERAL, which code_only deletes — scanning for it there would
    # pass on any tree at all, including one that writes the graph on every line.
    absent(
        "GraphDatabase",
        sources,
        stripper=code_only,
        positive_control="driver = GraphDatabase.driver(uri)",
        because="the mind-map state file reaches no driver",
    )
    for clause in ("MERGE (", "CREATE ("):
        absent(
            clause,
            sources,
            stripper=without_prose,
            positive_control=f'CYPHER = """{clause}n:Acronym) RETURN n"""',
            because="this module writes a YAML shelf, never the graph (MM12 clause e)",
        )
