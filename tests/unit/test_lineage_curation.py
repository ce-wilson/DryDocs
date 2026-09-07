"""LIN2 (b) - the decisions file: the ONE shape the review page exports and the load
reads. ``drydocs_lineage.curation`` documents it; this file pins it.

Refusals are total (a half-applied curation is what the gate exists to prevent), the
decision values ARE ``CurationStatus``, and a rel the SME never touched is absent -
never inferred as confirmed. Fixtures are synthetic node ids on the graph's own id
grammar (``proc#<kind>:<key>``).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from drydocs_lineage.curation import (
    DECISIONS_SCHEMA,
    CurationStatus,
    DecisionsError,
    load_decisions,
    parse_decisions,
)
from drydocs_lineage.review import _DECISION_OPTIONS

JOB = "proc#controlm_job:160500.1"
SCRIPT = "proc#shell_script:/opt/scripts/auto/fw.ksh"
PSET = "proc#abinitio:load.pset"


def _doc(*decisions: dict, **extra) -> dict:
    return {
        "schema": DECISIONS_SCHEMA,
        "doc": "synthetic",
        "exported": "2026-09-04T00:00:00Z",
        "decisions": list(decisions),
        **extra,
    }


def _row(src: str, rel: str, dst: str, decision: str) -> dict:
    return {"from": src, "type": rel, "to": dst, "decision": decision}


def test_confirmed_rejected_and_undecided_land_in_their_own_sets() -> None:
    ds = parse_decisions(
        _doc(
            _row(JOB, "INVOKES", SCRIPT, "confirmed"),
            _row(JOB, "INVOKES", PSET, "rejected"),
            _row(JOB, "TRIGGERS", PSET, "proposed"),
            notes=[{"folder": "160500", "note": "looked fine"}],
        )
    )
    assert ds.confirmed == {(JOB, "INVOKES", SCRIPT)}
    assert ds.rejected == {(JOB, "INVOKES", PSET)}
    assert ds.proposed == {(JOB, "TRIGGERS", PSET)}
    assert ds.total == 3
    assert ds.doc == "synthetic" and ds.exported.startswith("2026-09-04")
    assert ds.notes == ({"folder": "160500", "note": "looked fine"},)


def test_an_untouched_rel_is_simply_absent_never_confirmed() -> None:
    """The SME decided nothing: the confirmed set is empty, and the load says so."""
    ds = parse_decisions(_doc())
    assert ds.confirmed == frozenset() and ds.total == 0


def test_prototype_rel_spellings_normalise_to_the_registered_label() -> None:
    """READS -> READS_FROM, the same alias table the graph applies on add_rel, so a
    decision written against an older page still joins."""
    ds = parse_decisions(_doc(_row(JOB, "READS", "data#local_file:/x", "confirmed")))
    assert ds.confirmed == {(JOB, "READS_FROM", "data#local_file:/x")}


@pytest.mark.parametrize(
    ("doc", "match"),
    [
        ({"schema": "something.else", "decisions": []}, "not a lineage decisions file"),
        (_doc(_row(JOB, "INVOKES", SCRIPT, "maybe")), "not one of"),
        (_doc(_row(JOB, "SUMMONS", SCRIPT, "confirmed")), "not a registered label"),
        (_doc({"from": JOB, "type": "INVOKES", "decision": "confirmed"}), "lacks"),
        (
            _doc(
                _row(JOB, "INVOKES", SCRIPT, "confirmed"),
                _row(JOB, "INVOKES", SCRIPT, "rejected"),
            ),
            "decided twice with different answers",
        ),
        ({"schema": DECISIONS_SCHEMA, "decisions": "nope"}, "must be a list"),
    ],
)
def test_a_file_that_cannot_be_trusted_is_refused_whole(doc: dict, match: str) -> None:
    with pytest.raises(DecisionsError, match=match):
        parse_decisions(doc)


def test_the_same_answer_twice_is_not_a_conflict() -> None:
    ds = parse_decisions(
        _doc(_row(JOB, "INVOKES", SCRIPT, "confirmed"), _row(JOB, "INVOKES", SCRIPT, "confirmed"))
    )
    assert ds.confirmed == {(JOB, "INVOKES", SCRIPT)}


def test_missing_from_names_decisions_the_artifact_does_not_carry() -> None:
    """Curation out of sync: the page was rendered from another extract."""
    ds = parse_decisions(
        _doc(_row(JOB, "INVOKES", SCRIPT, "confirmed"), _row(JOB, "INVOKES", PSET, "rejected"))
    )
    assert ds.missing_from({(JOB, "INVOKES", SCRIPT)}) == [(JOB, "INVOKES", PSET)]
    assert ds.missing_from({(JOB, "INVOKES", SCRIPT), (JOB, "INVOKES", PSET)}) == []


def test_load_decisions_reads_a_file_and_names_it(tmp_path: Path) -> None:
    path = tmp_path / "lineage-decisions-synthetic.json"
    path.write_text(json.dumps(_doc(_row(JOB, "INVOKES", SCRIPT, "confirmed"))), encoding="utf-8")
    ds = load_decisions(path)
    assert ds.path == str(path) and ds.confirmed == {(JOB, "INVOKES", SCRIPT)}
    with pytest.raises(DecisionsError, match="not found"):
        load_decisions(tmp_path / "absent.json")
    (tmp_path / "junk.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(DecisionsError, match="cannot read"):
        load_decisions(tmp_path / "junk.json")


def test_the_page_offers_exactly_the_curation_statuses() -> None:
    """The review page's decision control and the reader agree on the vocabulary: every
    non-empty option value is a CurationStatus, and the empty option (undecided) is
    what the page leaves out of the export."""
    values = {v for v, _ in _DECISION_OPTIONS if v}
    assert values <= {s.value for s in CurationStatus}
    assert "confirmed" in values and "rejected" in values
    assert "" in {v for v, _ in _DECISION_OPTIONS}
